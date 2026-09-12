#!/usr/bin/env python3
# @steered SNARE-1 2026-09-12
"""
Pass to Production Migration Tool
==================================

Migrates finished components from dev branch to v3.0 production branch.

Production branch (v3.0) contains only the minimum files needed to run:
- components/     -- Hardware interface layer
- manual_control/ -- Manual operation (keyboard, REST API, color tracking)
- self_aware/     -- Autonomous navigation + data logging
- picrawler/      -- Factory core (untouched)
- examples/       -- Factory examples (untouched)
- README.md       -- Architecture overview

Dev-only files (ML notebooks, test iterations, diagnostics) stay on dev.

Features:
- Interactive file/folder selection
- Automatic filtering of dev-only files
- Git integration (commits to v3.0)
- Dry-run mode to preview changes
- Validation mode to check prod is clean

Usage:
    python3 tools/pass_to_prod.py                    # Interactive mode
    python3 tools/pass_to_prod.py --dry-run          # Preview only
    python3 tools/pass_to_prod.py --file path/to/file.py  # Migrate specific file
    python3 tools/pass_to_prod.py --file f1.py --file f2.py  # Multiple files (single commit)
    python3 tools/pass_to_prod.py --file f1.py -m "Fix bug in config"  # Custom commit message
    python3 tools/pass_to_prod.py --file f1.py --yes  # Skip confirm prompt (non-interactive)
    python3 tools/pass_to_prod.py --module components/sensors  # Migrate module
    python3 tools/pass_to_prod.py --all              # Migrate all production files
    python3 tools/pass_to_prod.py --validate         # Check v3.0 is clean

Author: PiCrawler dev tools
Updated: March 27, 2026
"""

import os
import sys
import subprocess
import argparse
from fnmatch import fnmatch
from pathlib import Path
from typing import List, Tuple

# Import encoding fixer (sibling module)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fix_encoding import fix_encoding as _fix_encoding_file

# ============================================================================
# PRODUCTION FILE POLICY
# ============================================================================

# Modules that belong in production
PRODUCTION_MODULES = [
    'components',
    'manual_control',
    'self_aware',
]

# Top-level files that belong in production (in addition to factory files)
PRODUCTION_TOP_LEVEL = [
    'README.md',
    'setup.py',
    'LICENSE',
    'DESCRIPTION.rst',
    'show',
    'i2samp.sh',
    '.gitignore',
]

# Filename patterns to ALWAYS exclude from production
EXCLUDE_PATTERNS = [
    # Build / cache artifacts
    '__pycache__',
    '*.pyc',
    '*.pyo',
    '.DS_Store',
    '.env',

    # Dev artifacts
    '*diagnostic*.py',
    'test_*.py',
    '*_test.py',
    '*.backup',
    '*.bak',
    '*.tmp',
]

# Specific files/paths that exist on dev but must NOT go to production.
# These are checked against the full relative path (from project root).
DEV_ONLY_FILES = [
    # ML scaffolding -- dev only (training infrastructure, not runtime)
    'self_aware/create_ml_notebook.py',
    'self_aware/dataset_utils.py',
    'self_aware/ml_next_move_prediction.ipynb',
    'self_aware/QUICKSTART_ML.md',
    'self_aware/AUTONOMOUS_NAVIGATION.md',
    'self_aware/README_ML.md',
    'self_aware/README_PHOTO_DATASETS.md',

    # NOTE: photo_logger.py and data_logger_with_photos.py are PRODUCTION files
    # They enable full sensor + photo capture during autonomous navigation

    # Tracking test iterations -- superseded by tracking.py (consolidated from tracking6.py)
    'manual_control/scripts/tracking2.py',
    'manual_control/scripts/tracking5.py',
    'manual_control/scripts/tracking6.py',

    # Broken / incomplete tests
    'manual_control/scripts/nohat/tracking_nohat2.py',

    # Raw prototype -- superseded by flaskirapi.py using components layer
    'manual_control/scripts/camera_trigger/irflask.py',

    # Diagnostics infrastructure -- dev only (base classes for diagnostic tools)
    'components/diagnostics/',

    # Top-level docs that are dev-only
    'CUSTOM_MODULES_MANIFEST.md',
    'V4_MIGRATION_GUIDE.md',
    'PRODUCTION_SETUP_V3.md',
    'DEV_WORKFLOW.md',
    'DIAGNOSTIC_TOOLS.md',
    'DIAGNOSTIC_TODO.md',
    'AI_CODING_GUIDELINES.md',

    # Tools directory itself is dev-only
    'tools/pass_to_prod.py',
    'tools/fix_encoding.py',
]

# Files that need renaming when migrated to prod
# Format: { 'dev_path': 'prod_path' }
RENAME_MAP = {
    # tracking6.py is the tested result -> becomes tracking.py in prod
    # (Only needed if dev still has the numbered version)
}


# ============================================================================
# TERMINAL COLORS
# ============================================================================

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 70}{Colors.END}\n")


def print_success(text: str):
    print(f"{Colors.GREEN}[EMOJI] {text}{Colors.END}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}[EMOJI] {text}{Colors.END}")


def print_error(text: str):
    print(f"{Colors.RED}[EMOJI] {text}{Colors.END}")


def print_info(text: str):
    print(f"{Colors.CYAN}[i] {text}{Colors.END}")


# ============================================================================
# GIT HELPERS
# ============================================================================

def run_command(cmd: List[str], check: bool = True) -> Tuple[int, str]:
    """Run shell command and return (returncode, stdout)"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return result.returncode, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stderr.strip()


def get_current_branch() -> str:
    code, branch = run_command(['git', 'branch', '--show-current'])
    if code != 0:
        print_error("Failed to get current branch")
        sys.exit(1)
    return branch


def check_git_clean() -> bool:
    code, status = run_command(['git', 'status', '--short'])
    return code == 0 and len(status) == 0


# ============================================================================
# FILE FILTERING
# ============================================================================

def is_dev_only(filepath: str) -> bool:
    """Return True if this file should NOT be in production."""
    # Normalize path separators
    filepath = filepath.replace('\\', '/')

    # Check explicit dev-only list
    if filepath in DEV_ONLY_FILES:
        return True

    # Check dev-only directories
    for dev_file in DEV_ONLY_FILES:
        # If a directory is listed (e.g. tools/), exclude everything under it
        if dev_file.endswith('/') and filepath.startswith(dev_file):
            return True

    # Check filename patterns
    filename = os.path.basename(filepath)
    for pattern in EXCLUDE_PATTERNS:
        if fnmatch(filename, pattern):
            return True

    return False


def get_production_files(module_path: str) -> List[str]:
    """Get list of production-ready files in a module."""
    production_files = []

    for root, dirs, files in os.walk(module_path):
        # Skip __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']

        for file in files:
            filepath = os.path.join(root, file)
            if not is_dev_only(filepath):
                production_files.append(filepath)

    return sorted(production_files)


def get_all_production_files() -> List[str]:
    """Get all files that should exist in production."""
    all_files = []
    for module in PRODUCTION_MODULES:
        if os.path.exists(module):
            all_files.extend(get_production_files(module))
    return all_files


# ============================================================================
# VALIDATION
# ============================================================================

def validate_production(dry_run: bool = True) -> bool:
    """
    Check v3.0 branch for files that shouldn't be there, or missing files.
    Can be run from any branch (reads v3.0 tree via git).
    """
    print_header("Validating v3.0 Production Branch")

    # Get file list from v3.0 branch
    code, output = run_command(['git', 'ls-tree', '-r', 'v3.0', '--name-only'], check=False)
    if code != 0:
        print_error("Failed to read v3.0 branch (does it exist?)")
        return False

    prod_files = set(output.split('\n')) if output else set()

    issues = []

    # Check for dev-only files that leaked into production
    for f in sorted(prod_files):
        if is_dev_only(f):
            issues.append(('UNWANTED', f))

    # Check that key production files exist
    key_files = [
        'self_aware/autonomous_navigator.py',
        'self_aware/autonomous_navigator_with_logging.py',
        'self_aware/data_logger.py',
        'manual_control/startup.py',
        'manual_control/scripts/tracking.py',
        'manual_control/scripts/keyboard_control.py',
        'manual_control/scripts/restapi3.py',
        'components/sensors/sensor_fusion.py',
        'components/navigation/motion_controller.py',
        'components/utils/config.py',
        'README.md',
    ]
    for f in key_files:
        if f not in prod_files:
            issues.append(('MISSING', f))

    # Report
    if not issues:
        print_success("v3.0 is clean -- no dev-only files, all key files present")
        print_info(f"Total files in v3.0: {len(prod_files)}")
        return True

    print_warning(f"Found {len(issues)} issue(s):\n")
    for issue_type, filepath in issues:
        if issue_type == 'UNWANTED':
            print(f"  {Colors.RED}UNWANTED{Colors.END}  {filepath}")
        else:
            print(f"  {Colors.YELLOW}MISSING {Colors.END}  {filepath}")

    return False


# ============================================================================
# MIGRATION
# ============================================================================

def preview_migration(files: List[str]):
    """Preview files to be migrated"""
    print_header("Migration Preview")

    if not files:
        print_warning("No files to migrate")
        return

    print(f"Files to migrate: {len(files)}\n")

    # Group by module
    by_module = {}
    for f in files:
        module = f.split(os.sep)[0]
        if module not in by_module:
            by_module[module] = []
        by_module[module].append(f)

    for module, module_files in sorted(by_module.items()):
        print(f"{Colors.BOLD}{module}/{Colors.END} ({len(module_files)} files)")
        for f in module_files:
            print(f"  -> {f}")
        print()


def migrate_files(files: List[str], dry_run: bool = False, commit_message: str = None,
                  assume_yes: bool = False) -> bool:
    """
    Migrate files from dev to v3.0 production branch.

    assume_yes skips the interactive confirmation, for scripted/CI use and for
    agents that cannot answer a prompt. Interactive mode never sets it.
    """
    if not files:
        print_warning("No files to migrate")
        return False

    current_branch = get_current_branch()
    if current_branch != 'dev':
        print_error(f"Must be on 'dev' branch (currently on '{current_branch}')")
        return False

    # Filter out dev-only files
    original_count = len(files)
    files = [f for f in files if not is_dev_only(f)]
    skipped = original_count - len(files)
    if skipped > 0:
        print_info(f"Filtered out {skipped} dev-only file(s)")

    if not files:
        print_warning("No production files to migrate after filtering")
        return False

    # Preview
    preview_migration(files)

    if dry_run:
        print_info("Dry-run mode -- no changes will be made")
        return True

    # Confirm
    if assume_yes:
        print_info(f"--yes given, migrating {len(files)} file(s) without confirmation")
    else:
        print(f"\n{Colors.YELLOW}Migrate {len(files)} files to v3.0 production branch?{Colors.END}")
        response = input("Type 'yes' to continue: ")
        if response.lower() != 'yes':
            print_warning("Migration cancelled")
            return False

    # Check v3.0 exists
    code, branches = run_command(['git', 'branch', '--list', 'v3.0'])
    if 'v3.0' not in branches:
        print_error("v3.0 branch does not exist")
        return False

    print_header("Migrating Files")

    # Stash uncommitted dev changes
    print_info("Stashing current changes on dev...")
    run_command(['git', 'stash', 'push', '-m', 'pass_to_prod temporary stash'], check=False)

    try:
        # Switch to v3.0
        print_info("Switching to v3.0 branch...")
        code, output = run_command(['git', 'checkout', 'v3.0'])
        if code != 0:
            print_error(f"Failed to checkout v3.0: {output}")
            return False

        # Checkout each file from dev
        migrated = 0
        for filepath in files:
            # Apply rename if needed
            prod_path = RENAME_MAP.get(filepath, filepath)

            print(f"  Migrating: {filepath}", end='')
            if prod_path != filepath:
                print(f" -> {prod_path}", end='')
            print()

            code, output = run_command(['git', 'checkout', 'dev', '--', filepath])
            if code != 0:
                print_error(f"  Failed: {output}")
                continue

            # Handle rename
            if prod_path != filepath:
                os.makedirs(os.path.dirname(prod_path), exist_ok=True)
                os.rename(filepath, prod_path)
                # Remove the old path from git index
                run_command(['git', 'rm', '--cached', filepath], check=False)

            migrated += 1

        if migrated == 0:
            print_warning("No files were migrated")
            return False

        print_success(f"Migrated {migrated} files")

        # Fix encoding on all migrated .py files (prevents charmap codec errors on Pi)
        print_info("Fixing encoding (emoji -> ASCII) for production...")
        encoding_fixed = 0
        for filepath in files:
            prod_path = RENAME_MAP.get(filepath, filepath)
            if prod_path.endswith('.py') and os.path.exists(prod_path):
                success, changes, message = _fix_encoding_file(
                    Path(prod_path), backup=False, dry_run=False
                )
                if success and changes > 0:
                    encoding_fixed += 1
                    print(f"    Fixed encoding: {prod_path} ({changes} replacements)")
        if encoding_fixed > 0:
            print_success(f"Fixed encoding in {encoding_fixed} file(s)")
            # Re-stage files after encoding fixes
            prod_paths_py = [RENAME_MAP.get(f, f) for f in files if RENAME_MAP.get(f, f).endswith('.py')]
            if prod_paths_py:
                run_command(['git', 'add'] + prod_paths_py)
        else:
            print_info("No encoding issues found")

        # Commit - use custom message if provided, otherwise generate default
        if commit_message:
            commit_msg = commit_message + "\n\nFiles updated:\n"
        else:
            commit_msg = f"Production update: Migrated {migrated} file(s) from dev\n\nFiles updated:\n"
        for f in files[:15]:
            prod_path = RENAME_MAP.get(f, f)
            commit_msg += f"- {prod_path}\n"
        if len(files) > 15:
            commit_msg += f"... and {len(files) - 15} more files\n"

        # Stage all production files (including renames)
        prod_paths = [RENAME_MAP.get(f, f) for f in files]
        run_command(['git', 'add'] + prod_paths)

        print_info("Committing changes...")
        code, output = run_command(['git', 'commit', '-m', commit_msg], check=False)

        if code == 0:
            print_success("Changes committed to v3.0")
        else:
            print_warning("No changes to commit (files already up to date)")

        print_header("Migration Complete")
        print_success(f"Successfully migrated {migrated} files to v3.0")
        print_info("Remember to push: git push origin v3.0")

        return True

    finally:
        # Return to dev
        print_info("\nReturning to dev branch...")
        run_command(['git', 'checkout', 'dev'])

        # Restore stash
        code, stash_list = run_command(['git', 'stash', 'list'], check=False)
        if 'pass_to_prod temporary stash' in stash_list:
            run_command(['git', 'stash', 'pop'], check=False)


# ============================================================================
# INTERACTIVE MODE
# ============================================================================

def interactive_mode():
    """Interactive file selection"""
    print_header("Pass to Production -- Interactive Mode")

    print("Select what to migrate:\n")
    print("  1. Specific file")
    print("  2. Entire module (e.g., components/sensors)")
    print("  3. All production files")
    print("  4. Validate v3.0 (check for unwanted files)")
    print("  5. Exit\n")

    choice = input("Enter choice (1-5): ").strip()

    if choice == '1':
        filepath = input("Enter file path: ").strip()
        if not os.path.exists(filepath):
            print_error(f"File not found: {filepath}")
            return
        if is_dev_only(filepath):
            print_warning(f"'{filepath}' is marked as dev-only")
            response = input("Migrate anyway? (yes/no): ")
            if response.lower() != 'yes':
                return
        migrate_files([filepath])

    elif choice == '2':
        module_path = input("Enter module path (e.g., components/sensors): ").strip()
        if not os.path.exists(module_path):
            print_error(f"Module not found: {module_path}")
            return
        files = get_production_files(module_path)
        migrate_files(files)

    elif choice == '3':
        files = get_all_production_files()
        migrate_files(files)

    elif choice == '4':
        validate_production()

    elif choice == '5':
        print_info("Exiting")

    else:
        print_error("Invalid choice")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Migrate files from dev to v3.0 production branch',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 tools/pass_to_prod.py                           # Interactive mode
  python3 tools/pass_to_prod.py --dry-run                 # Preview all prod files
  python3 tools/pass_to_prod.py --validate                # Check v3.0 is clean
  python3 tools/pass_to_prod.py --file self_aware/data_logger.py
  python3 tools/pass_to_prod.py --file f1.py --file f2.py # Multiple files (single commit)
  python3 tools/pass_to_prod.py --file f1.py -m "Fix config bug"  # Custom message
  python3 tools/pass_to_prod.py --file f1.py --yes         # Skip the confirm prompt
  python3 tools/pass_to_prod.py --module components/sensors
  python3 tools/pass_to_prod.py --all                     # Migrate everything
        """
    )

    parser.add_argument('--file', action='append', dest='files', help='Migrate specific file(s) - can be used multiple times')
    parser.add_argument('--module', help='Migrate entire module')
    parser.add_argument('--all', action='store_true', help='Migrate all production files')
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    parser.add_argument('--validate', action='store_true', help='Validate v3.0 branch is clean')
    parser.add_argument('-m', '--message', help='Custom commit message for the migration')
    parser.add_argument('-y', '--yes', action='store_true',
                        help='Skip the confirmation prompt (non-interactive use)')

    args = parser.parse_args()

    # Validate can run from any branch
    if args.validate:
        validate_production()
        return

    # Check we're in project root
    if not os.path.exists('picrawler') or not os.path.exists('components'):
        print_error("Must run from project root directory")
        sys.exit(1)

    # Must be on dev for migration
    current_branch = get_current_branch()
    if current_branch != 'dev':
        print_error(f"Must be on 'dev' branch (currently on '{current_branch}')")
        sys.exit(1)

    if args.files:
        # Verify all files exist
        for filepath in args.files:
            if not os.path.exists(filepath):
                print_error(f"File not found: {filepath}")
                sys.exit(1)
        migrate_files(args.files, dry_run=args.dry_run, commit_message=args.message,
                      assume_yes=args.yes)

    elif args.module:
        if not os.path.exists(args.module):
            print_error(f"Module not found: {args.module}")
            sys.exit(1)
        files = get_production_files(args.module)
        migrate_files(files, dry_run=args.dry_run, commit_message=args.message,
                      assume_yes=args.yes)

    elif args.all:
        files = get_all_production_files()
        migrate_files(files, dry_run=args.dry_run, commit_message=args.message,
                      assume_yes=args.yes)

    else:
        interactive_mode()


if __name__ == '__main__':
    main()

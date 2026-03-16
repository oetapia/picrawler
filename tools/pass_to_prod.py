#!/usr/bin/env python3
"""
Pass to Production Migration Tool
==================================

Migrates finished components from dev branch to v3.0 production branch.

Features:
- Interactive file/folder selection
- Automatic cleaning (removes diagnostics, tests, backups)
- Git integration (commits to v3.0)
- Dry-run mode to preview changes
- Validation checks

Usage:
    python3 tools/pass_to_prod.py                    # Interactive mode
    python3 tools/pass_to_prod.py --dry-run          # Preview only
    python3 tools/pass_to_prod.py --file path/to/file.py  # Migrate specific file
    python3 tools/pass_to_prod.py --module components/sensors  # Migrate module
    python3 tools/pass_to_prod.py --all              # Migrate all production files

Author: Automated packaging system
Date: March 17, 2026
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path
from typing import List, Set, Tuple

# Files to exclude from production
EXCLUDE_PATTERNS = [
    '*diagnostic*.py',
    'test_*.py',
    '*.backup',
    '*_GUIDE.md',
    '*_TROUBLESHOOTING.md',
    '*_FIX*.md',
    '*_API*.md',
    'README_*.md',
    '__pycache__',
    '*.pyc',
    '*.pyo',
    '.DS_Store',
]

# Production modules
PRODUCTION_MODULES = [
    'components',
    'manual_control',
    'self_aware',
]

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 70}{Colors.END}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")

def run_command(cmd: List[str], check: bool = True) -> Tuple[int, str]:
    """Run shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check
        )
        return result.returncode, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stderr.strip()

def get_current_branch() -> str:
    """Get current git branch"""
    code, branch = run_command(['git', 'branch', '--show-current'])
    if code != 0:
        print_error("Failed to get current branch")
        sys.exit(1)
    return branch

def check_git_status() -> bool:
    """Check if git working directory is clean"""
    code, status = run_command(['git', 'status', '--short'])
    if code != 0:
        print_error("Failed to check git status")
        return False
    return len(status) == 0

def should_exclude(filepath: str) -> bool:
    """Check if file should be excluded from production"""
    from fnmatch import fnmatch
    filename = os.path.basename(filepath)
    
    for pattern in EXCLUDE_PATTERNS:
        if fnmatch(filename, pattern):
            return True
    
    return False

def get_production_files(module_path: str) -> List[str]:
    """Get list of production files in module (excluding diagnostics)"""
    production_files = []
    
    for root, dirs, files in os.walk(module_path):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            filepath = os.path.join(root, file)
            if not should_exclude(filepath):
                production_files.append(filepath)
    
    return sorted(production_files)

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
        for f in module_files[:5]:  # Show first 5
            print(f"  → {f}")
        if len(module_files) > 5:
            print(f"  ... and {len(module_files) - 5} more")
        print()

def migrate_files(files: List[str], dry_run: bool = False) -> bool:
    """Migrate files to production branch"""
    if not files:
        print_warning("No files to migrate")
        return False
    
    current_branch = get_current_branch()
    
    if current_branch != 'dev':
        print_error(f"Must be on 'dev' branch (currently on '{current_branch}')")
        return False
    
    # Preview migration
    preview_migration(files)
    
    if dry_run:
        print_info("Dry-run mode - no changes will be made")
        return True
    
    # Confirm migration
    print(f"\n{Colors.YELLOW}Migrate {len(files)} files to v3.0 production branch?{Colors.END}")
    response = input("Type 'yes' to continue: ")
    
    if response.lower() != 'yes':
        print_warning("Migration cancelled")
        return False
    
    # Check if v3.0 branch exists
    code, branches = run_command(['git', 'branch', '--list', 'v3.0'])
    if 'v3.0' not in branches:
        print_error("v3.0 branch does not exist")
        return False
    
    print_header("Migrating Files")
    
    # Stash any uncommitted changes on dev
    print_info("Stashing current changes on dev...")
    run_command(['git', 'stash', 'push', '-m', 'pass_to_prod temporary stash'], check=False)
    
    try:
        # Switch to v3.0
        print_info("Switching to v3.0 branch...")
        code, output = run_command(['git', 'checkout', 'v3.0'])
        if code != 0:
            print_error(f"Failed to checkout v3.0: {output}")
            return False
        
        # Copy files from dev
        print_info(f"Copying {len(files)} files...")
        for filepath in files:
            src = os.path.join('..', 'dev_backup', filepath)
            
            # Create backup of dev files
            backup_dir = '../dev_backup'
            os.makedirs(backup_dir, exist_ok=True)
            
        # Checkout files from dev branch
        for filepath in files:
            print(f"  Migrating: {filepath}")
            code, output = run_command(['git', 'checkout', 'dev', '--', filepath])
            if code != 0:
                print_error(f"Failed to migrate {filepath}: {output}")
                continue
        
        print_success(f"Migrated {len(files)} files")
        
        # Commit changes
        commit_msg = f"Production update: Migrated {len(files)} files from dev\n\nFiles updated:\n"
        for f in files[:10]:  # List first 10 files
            commit_msg += f"- {f}\n"
        if len(files) > 10:
            commit_msg += f"... and {len(files) - 10} more files\n"
        
        print_info("Committing changes...")
        run_command(['git', 'add'] + files)
        code, output = run_command(['git', 'commit', '-m', commit_msg], check=False)
        
        if code == 0:
            print_success("Changes committed to v3.0")
        else:
            print_warning("No changes to commit (files already up to date)")
        
        print_header("Migration Complete")
        print_success(f"Successfully migrated {len(files)} files to v3.0")
        print_info("Remember to push changes: git push origin v3.0")
        
        return True
        
    finally:
        # Return to dev branch
        print_info("\nReturning to dev branch...")
        run_command(['git', 'checkout', 'dev'])
        
        # Restore stashed changes
        code, stash_list = run_command(['git', 'stash', 'list'], check=False)
        if 'pass_to_prod temporary stash' in stash_list:
            run_command(['git', 'stash', 'pop'], check=False)

def interactive_mode():
    """Interactive file selection mode"""
    print_header("Pass to Production - Interactive Mode")
    
    print("Select what to migrate:\n")
    print("1. Specific file")
    print("2. Entire module (e.g., components/sensors)")
    print("3. All production files")
    print("4. Exit\n")
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == '1':
        filepath = input("Enter file path: ").strip()
        if not os.path.exists(filepath):
            print_error(f"File not found: {filepath}")
            return
        if should_exclude(filepath):
            print_warning(f"File matches exclusion pattern: {filepath}")
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
        all_files = []
        for module in PRODUCTION_MODULES:
            if os.path.exists(module):
                all_files.extend(get_production_files(module))
        migrate_files(all_files)
        
    elif choice == '4':
        print_info("Exiting")
        return
        
    else:
        print_error("Invalid choice")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Migrate files from dev to v3.0 production branch',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 tools/pass_to_prod.py                           # Interactive mode
  python3 tools/pass_to_prod.py --dry-run                 # Preview changes
  python3 tools/pass_to_prod.py --file components/sensors/accelerometer.py
  python3 tools/pass_to_prod.py --module components/sensors
  python3 tools/pass_to_prod.py --all                     # Migrate everything
        """
    )
    
    parser.add_argument('--file', help='Migrate specific file')
    parser.add_argument('--module', help='Migrate entire module')
    parser.add_argument('--all', action='store_true', help='Migrate all production files')
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    
    args = parser.parse_args()
    
    # Check we're in project root
    if not os.path.exists('picrawler') or not os.path.exists('components'):
        print_error("Must run from project root directory")
        sys.exit(1)
    
    # Check current branch
    current_branch = get_current_branch()
    if current_branch != 'dev':
        print_error(f"Must be on 'dev' branch (currently on '{current_branch}')")
        sys.exit(1)
    
    # Process arguments
    if args.file:
        if not os.path.exists(args.file):
            print_error(f"File not found: {args.file}")
            sys.exit(1)
        migrate_files([args.file], dry_run=args.dry_run)
        
    elif args.module:
        if not os.path.exists(args.module):
            print_error(f"Module not found: {args.module}")
            sys.exit(1)
        files = get_production_files(args.module)
        migrate_files(files, dry_run=args.dry_run)
        
    elif args.all:
        all_files = []
        for module in PRODUCTION_MODULES:
            if os.path.exists(module):
                all_files.extend(get_production_files(module))
        migrate_files(all_files, dry_run=args.dry_run)
        
    else:
        interactive_mode()

if __name__ == '__main__':
    main()

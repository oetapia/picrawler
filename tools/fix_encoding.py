#!/usr/bin/env python3
# @steered SNARE-1 2026-09-12
"""
Encoding Fix Script

Replaces Unicode special characters with ASCII equivalents to prevent charmap codec errors.
Creates backups and can process single files or directories.

Usage:
    python fix_encoding.py <file_or_directory> [--no-backup] [--dry-run]
"""

import os
import sys
import shutil
import argparse
import re
from pathlib import Path


# Emoji Unicode ranges (comprehensive)
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F700-\U0001F77F"  # alchemical symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "\U000024C2-\U0001F251" 
    "]+"
)


# Character replacement mappings (Unicode -> ASCII)
CHAR_REPLACEMENTS = {
    # Checkmarks and crosses
    '✓': '[OK]',
    '✗': '[X]',
    '☑': '[X]',
    '☒': '[ ]',
    
    # Arrows
    '→': '->',
    '←': '<-',
    '↑': '^',
    '↓': 'v',
    '⇒': '=>',
    '⇐': '<=',
    
    # Warning and info symbols
    '⚠': '[!]',
    '⚡': '[!]',
    '⛔': '[!]',
    'ℹ': '[i]',
    
    # Quotation marks
    # Do NOT run this script on its own source: doing so rewrites the keys
    # below to plain ASCII, turning each entry into a no-op that then "fixes"
    # every ordinary quote in every file. fix_encoding() refuses to process
    # this file for that reason.
    '“': '"',
    '”': '"',
    '‘': "'",
    '’': "'",
    '„': '"',
    '‚': "'",
    
    # Dashes
    '–': '-',
    '—': '--',
    '−': '-',
    
    # Other common symbols
    '…': '...',
    '•': '*',
    '◦': '-',
    '▪': '*',
    '▫': '-',
    '°': ' deg',
    '±': '+/-',
    '×': 'x',
    '÷': '/',
    '≈': '~=',
    '≠': '!=',
    '≤': '<=',
    '≥': '>=',
}


def fix_encoding(file_path: Path, backup: bool = True, dry_run: bool = False) -> tuple:
    """
    Fix encoding issues in a file by replacing Unicode characters with ASCII equivalents.
    
    Args:
        file_path: Path to the file to fix
        backup: Whether to create a backup before modifying
        dry_run: If True, only report what would be changed without modifying
        
    Returns:
        tuple: (success: bool, changes_made: int, message: str)
    """
    if not file_path.exists():
        return False, 0, f"File not found: {file_path}"
    
    if not file_path.is_file():
        return False, 0, f"Not a file: {file_path}"

    # Refuse to fix this script. Its CHAR_REPLACEMENTS keys ARE the Unicode
    # characters it strips, so processing itself rewrites every key to its own
    # ASCII value. The table becomes a set of no-ops that then "fix" every
    # plain quote and hyphen in every file, and the mangled quote keys break
    # this file's syntax outright. This has happened twice already.
    try:
        if file_path.resolve() == Path(__file__).resolve():
            return True, 0, f"Skipped {file_path.name} (cannot fix its own mapping table)"
    except OSError:
        pass


    try:
        # Read the file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with latin-1 encoding as fallback
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        original_content = content
        changes_made = 0
        changes_detail = []
        
        # First, remove all emojis
        emoji_matches = EMOJI_PATTERN.findall(content)
        if emoji_matches:
            emoji_count = len(emoji_matches)
            content = EMOJI_PATTERN.sub('[EMOJI]', content)
            changes_made += emoji_count
            changes_detail.append(f"  - Removed {emoji_count} emoji(s) -> '[EMOJI]'")
        
        # Apply replacements
        for unicode_char, ascii_equiv in CHAR_REPLACEMENTS.items():
            count = content.count(unicode_char)
            if count > 0:
                content = content.replace(unicode_char, ascii_equiv)
                changes_made += count
                changes_detail.append(f"  - '{unicode_char}' -> '{ascii_equiv}' ({count} occurrences)")
        
        if changes_made == 0:
            return True, 0, "No Unicode characters found to replace"
        
        # Dry run - just report
        if dry_run:
            message = f"Would make {changes_made} changes:\n" + "\n".join(changes_detail)
            return True, changes_made, message
        
        # Create backup if requested
        if backup:
            backup_path = file_path.with_suffix(file_path.suffix + '.backup')
            shutil.copy2(file_path, backup_path)
        
        # Write the fixed content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        message = f"Fixed {changes_made} Unicode characters:\n" + "\n".join(changes_detail)
        if backup:
            message += f"\n  Backup saved: {backup_path.name}"
        
        return True, changes_made, message
        
    except Exception as e:
        return False, 0, f"Error processing file: {str(e)}"


def process_directory(directory: Path, backup: bool = True, dry_run: bool = False):
    """
    Process all Python files in a directory recursively.
    
    Args:
        directory: Path to directory
        backup: Whether to create backups
        dry_run: If True, only report what would be changed
    """
    python_files = list(directory.rglob('*.py'))

    if not python_files:
        print(f"No Python files found in {directory}")
        return
    
    print(f"Found {len(python_files)} Python file(s) to process\n")
    
    total_changes = 0
    files_modified = 0
    
    for file_path in python_files:
        print(f"Processing: {file_path.relative_to(directory)}")
        success, changes, message = fix_encoding(file_path, backup, dry_run)
        
        if success and changes > 0:
            print(f"  ✓ {message}\n")
            total_changes += changes
            files_modified += 1
        elif success:
            print(f"  - {message}\n")
        else:
            print(f"  ✗ {message}\n")
    
    print("="*60)
    if dry_run:
        print(f"DRY RUN: Would modify {files_modified} file(s) with {total_changes} total changes")
    else:
        print(f"Modified {files_modified} file(s) with {total_changes} total changes")


def main():
    parser = argparse.ArgumentParser(
        description='Fix encoding issues by replacing Unicode characters with ASCII equivalents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fix_encoding.py components/camera/camera_diagnostic.py
  python fix_encoding.py components/ --dry-run
  python fix_encoding.py myfile.py --no-backup
        """
    )
    
    parser.add_argument(
        'path',
        help='File or directory to process'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Do not create backup files'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    
    args = parser.parse_args()
    
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: Path not found: {path}")
        sys.exit(1)
    
    backup = not args.no_backup
    
    if path.is_file():
        print(f"Processing file: {path}\n")
        success, changes, message = fix_encoding(path, backup, args.dry_run)
        print(message)
        
        if success and changes > 0:
            print("\n✓ File processed successfully!")
        elif success:
            print("\n- No changes needed")
        else:
            print("\n✗ Processing failed")
            sys.exit(1)
    
    elif path.is_dir():
        print(f"Processing directory: {path}\n")
        process_directory(path, backup, args.dry_run)
    
    else:
        print(f"Error: Invalid path: {path}")
        sys.exit(1)


if __name__ == '__main__':
    main()

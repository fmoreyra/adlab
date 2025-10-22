#!/usr/bin/env python3
"""
Update Image Placeholder Paths in Documentation

This script updates all image placeholders in the documentation from the format:
    _[Espacio para captura de pantalla: Description]_

To the MkDocs format:
    ![Description](assets/images/section/filename.png)

It extracts descriptions, generates appropriate filenames, and updates all markdown files.
"""

import re
import os
from pathlib import Path
from typing import List, Tuple, Dict

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def colorize(text: str, color: str) -> str:
    """Add color to terminal output"""
    return f"{color}{text}{Colors.END}"

def slugify(text: str) -> str:
    """Convert Spanish text to a valid filename"""
    # Convert to lowercase
    text = text.lower()

    # Replace Spanish characters
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', 'ü': 'u',
        ' ': '-', '_': '-',
        '"': '', "'": '', '¿': '', '?': '', '¡': '', '!': '',
        '(': '', ')': '', '[': '', ']': '', '{': '', '}': '',
        ',': '', '.': '', ':': '', ';': '',
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove any remaining non-alphanumeric characters except hyphens
    text = re.sub(r'[^a-z0-9-]', '', text)

    # Remove multiple consecutive hyphens
    text = re.sub(r'-+', '-', text)

    # Remove leading/trailing hyphens
    text = text.strip('-')

    return text

def get_image_section(file_path: Path) -> str:
    """Determine the image subdirectory based on file path"""
    parts = file_path.parts
    docs_index = parts.index('docs')
    relative_parts = parts[docs_index + 1:-1]  # Exclude 'docs' and filename

    # Map to image directories
    if 'getting-started' in relative_parts:
        return 'getting-started'
    elif 'user-guides' in relative_parts:
        if 'veterinarians' in relative_parts:
            return 'user-guides/veterinarians'
        elif 'histopathologists' in relative_parts:
            return 'user-guides/histopathologists'
        elif 'lab-staff' in relative_parts:
            return 'user-guides/lab-staff'
        elif 'administrators' in relative_parts:
            return 'user-guides/administrators'
    elif 'workflows' in relative_parts:
        return 'workflows'
    elif 'common-tasks' in relative_parts:
        return 'common-tasks'
    elif 'troubleshooting' in relative_parts:
        return 'troubleshooting'

    return 'general'

def extract_placeholders(content: str, file_path: Path) -> List[Tuple[str, str, str]]:
    """Extract all image placeholders from content

    Returns: List of (full_placeholder, description, proposed_filename)
    """
    pattern = r'_\[Espacio para captura de pantalla:\s*([^\]]+)\]_'
    matches = re.finditer(pattern, content)

    section = get_image_section(file_path)
    placeholders = []

    for match in matches:
        full_match = match.group(0)
        description = match.group(1).strip()
        filename = slugify(description) + '.png'
        image_path = f"assets/images/{section}/{filename}"

        placeholders.append((full_match, description, image_path))

    return placeholders

def update_file(file_path: Path, dry_run: bool = True) -> Dict:
    """Update a single markdown file with proper image paths

    Returns: Dictionary with update statistics
    """
    content = file_path.read_text(encoding='utf-8')
    placeholders = extract_placeholders(content, file_path)

    if not placeholders:
        return {'file': str(file_path), 'placeholders': 0, 'updated': False}

    # Create new content with replacements
    new_content = content
    for full_placeholder, description, image_path in placeholders:
        replacement = f"![{description}]({image_path})"
        new_content = new_content.replace(full_placeholder, replacement)

    # Write if not dry run
    if not dry_run:
        file_path.write_text(new_content, encoding='utf-8')

    return {
        'file': str(file_path),
        'placeholders': len(placeholders),
        'updated': not dry_run,
        'changes': placeholders
    }

def find_markdown_files(docs_dir: Path) -> List[Path]:
    """Find all markdown files in the docs directory"""
    markdown_files = []

    # Exclude internal/archive directories
    exclude_dirs = {'internal', 'archive', 'node_modules', '.git'}

    for md_file in docs_dir.rglob('*.md'):
        # Check if any excluded directory is in the path
        if not any(excluded in md_file.parts for excluded in exclude_dirs):
            markdown_files.append(md_file)

    return sorted(markdown_files)

def main():
    """Main execution"""
    print(colorize("\n" + "="*70, Colors.HEADER))
    print(colorize("  Image Placeholder Updater", Colors.HEADER + Colors.BOLD))
    print(colorize("="*70 + "\n", Colors.HEADER))

    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    docs_dir = project_root / 'docs'

    if not docs_dir.exists():
        print(colorize("❌ Error: docs directory not found!", Colors.RED))
        return 1

    print(colorize(f"📁 Documentation directory: {docs_dir}\n", Colors.BLUE))

    # Find all markdown files
    print(colorize("🔍 Finding markdown files...", Colors.CYAN))
    markdown_files = find_markdown_files(docs_dir)
    print(colorize(f"   Found {len(markdown_files)} files\n", Colors.GREEN))

    # Ask for mode
    print(colorize("Choose mode:", Colors.YELLOW))
    print("  1. Dry run (preview changes)")
    print("  2. Update files")
    choice = input("\nEnter choice (1-2): ").strip()

    dry_run = choice != '2'
    mode = "DRY RUN (preview only)" if dry_run else "UPDATE MODE (will modify files)"

    print(colorize(f"\n📝 Mode: {mode}\n", Colors.YELLOW + Colors.BOLD))

    if not dry_run:
        confirm = input(colorize("⚠️  This will modify files. Continue? (yes/no): ", Colors.RED))
        if confirm.lower() != 'yes':
            print(colorize("\n❌ Cancelled by user\n", Colors.YELLOW))
            return 0
        print()

    # Process files
    total_placeholders = 0
    updated_files = 0
    all_changes = []

    for file_path in markdown_files:
        result = update_file(file_path, dry_run)

        if result['placeholders'] > 0:
            updated_files += 1
            total_placeholders += result['placeholders']

            rel_path = file_path.relative_to(docs_dir)
            print(colorize(f"📄 {rel_path}", Colors.CYAN))
            print(colorize(f"   {result['placeholders']} placeholder(s) found", Colors.YELLOW))

            for full_placeholder, description, image_path in result['changes']:
                print(colorize(f"   → {image_path}", Colors.GREEN))
                all_changes.append({
                    'file': str(rel_path),
                    'description': description,
                    'path': image_path
                })

            print()

    # Summary
    print(colorize("="*70, Colors.HEADER))
    print(colorize("  Summary", Colors.HEADER + Colors.BOLD))
    print(colorize("="*70, Colors.HEADER))
    print(colorize(f"\n📊 Files processed: {len(markdown_files)}", Colors.BLUE))
    print(colorize(f"📊 Files with placeholders: {updated_files}", Colors.BLUE))
    print(colorize(f"📊 Total placeholders: {total_placeholders}", Colors.BLUE))

    if dry_run:
        print(colorize(f"\n✅ Preview complete! No files were modified.", Colors.GREEN))
        print(colorize(f"   Run with option 2 to actually update files.", Colors.YELLOW))
    else:
        print(colorize(f"\n✅ Files updated successfully!", Colors.GREEN))
        print(colorize(f"   Remember to add screenshots to the image paths!", Colors.YELLOW))

    # Generate image checklist
    if all_changes:
        checklist_file = docs_dir / 'IMAGE_PATHS_GENERATED.md'
        with open(checklist_file, 'w', encoding='utf-8') as f:
            f.write("# Generated Image Paths\n\n")
            f.write("This file lists all image paths referenced in the documentation.\n\n")
            f.write("## Images Needed\n\n")

            for change in all_changes:
                f.write(f"- [ ] `{change['path']}` - {change['description']}\n")
                f.write(f"      File: {change['file']}\n\n")

        print(colorize(f"\n📝 Image list saved to: {checklist_file.name}", Colors.CYAN))

    print()
    return 0

if __name__ == '__main__':
    try:
        exit(main())
    except KeyboardInterrupt:
        print(colorize("\n\n❌ Interrupted by user\n", Colors.RED))
        exit(1)
    except Exception as e:
        print(colorize(f"\n\n❌ Error: {e}\n", Colors.RED))
        import traceback
        traceback.print_exc()
        exit(1)

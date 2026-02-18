#!/usr/bin/env python3
"""
Fix all broken inter-page links in the Astro/Starlight content files.

Handles the following link patterns:
  A) Bare markdown links:   [Text](r_foo)         → [Text](../r_foo)         (same category)
                             [Text](r_foo)         → [Text](../rules/r_foo)   (cross category)
  B) Absolute HTML links:   <a href="/rules/r_foo">Text</a> → [Text](../r_foo)
  C) Bare HTML links:       <a href="R_mechs">text</a>     → [text](../rules/r_mechs)
  D) Existing cross-cat relative links: normalize slug case to lowercase

All link targets are normalized to lowercase.
Stray HTML tags (e.g. </sub>) in converted link text are cleaned up.

Usage:
  python fix_all_links.py              # Apply fixes
  python fix_all_links.py --dry-run    # Preview changes without writing
  python fix_all_links.py --validate   # Check that all link targets resolve to real files
"""

import os
import re
import sys
from pathlib import Path

DOCS_ROOT = Path(__file__).parent / "src" / "content" / "docs"

# Map slug prefix → content directory
PREFIX_TO_DIR = {
    "r_": "rules",
    "f_": "factions",
    "c_": "components",
}


def get_category(filepath: Path) -> str | None:
    """Get the category directory of a file (rules, factions, components)."""
    rel = filepath.relative_to(DOCS_ROOT)
    parts = rel.parts
    if len(parts) >= 2:
        return parts[0]  # e.g., 'rules', 'factions', 'components'
    return None


def slug_to_category(slug: str) -> str | None:
    """Determine the target category directory from a slug's prefix."""
    slug_lower = slug.lower()
    for prefix, category in PREFIX_TO_DIR.items():
        if slug_lower.startswith(prefix):
            return category
    return None


def build_valid_slugs() -> set[str]:
    """Build a set of valid lowercase slugs from actual content files."""
    slugs = set()
    for category_dir in ["rules", "factions", "components"]:
        dir_path = DOCS_ROOT / category_dir
        if dir_path.exists():
            for f in dir_path.iterdir():
                if f.suffix == ".md":
                    slugs.add(f.stem.lower())
    return slugs


def compute_relative_path(source_category: str, target_category: str, target_slug: str) -> str:
    """
    Compute the relative markdown link path from a source file to a target.

    Each page lives at /<category>/<slug>/ (directory-style), so we always
    need ../ to escape the current page's directory, then either land in
    a sibling (same category) or navigate to another category directory.
    """
    target_slug = target_slug.lower()
    if source_category == target_category:
        # Same directory: ../r_foo
        return f"../{target_slug}"
    else:
        # Cross directory: ../rules/r_foo
        return f"../{target_category}/{target_slug}"


def clean_inner_html(text: str) -> str:
    """Clean up stray HTML tags from converted link text."""
    # Remove stray </sub> tags (present in some technology links)
    text = re.sub(r"</sub>", "", text)
    # Strip leading/trailing whitespace
    return text.strip()


def fix_file(filepath: Path, valid_slugs: set[str], dry_run: bool = False) -> list[str]:
    """Fix all links in a single file. Returns list of change descriptions."""
    changes = []
    source_category = get_category(filepath)

    if source_category is None:
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    new_content = content

    # ──────────────────────────────────────────────────────────────
    # Pattern A: Bare markdown links — [Text](r_foo) or [Text](R_foo)
    # Matches slug-only targets (no ../, no /, no http)
    # ──────────────────────────────────────────────────────────────
    def fix_bare_md_link(match):
        full_match = match.group(0)
        text = match.group(1)
        target = match.group(2)
        target_lower = target.lower()
        target_cat = slug_to_category(target_lower)
        if target_cat and target_lower in valid_slugs:
            new_path = compute_relative_path(source_category, target_cat, target_lower)
            changes.append(f"  MD bare:  [{text}]({target}) → [{text}]({new_path})")
            return f"[{text}]({new_path})"
        return full_match

    bare_md_pattern = re.compile(r"\[([^\]]+)\]\(([RrFfCc]_[A-Za-z0-9_]+)\)")
    new_content = bare_md_pattern.sub(fix_bare_md_link, new_content)

    # ──────────────────────────────────────────────────────────────
    # Pattern B: Absolute HTML links — <a href="/rules/r_foo">Text</a>
    # Converts to markdown link with correct relative path
    # ──────────────────────────────────────────────────────────────
    def fix_absolute_html_link(match):
        full_match = match.group(0)
        abs_path = match.group(1)       # e.g., /rules/r_technology_sc
        inner_text = match.group(2)     # may contain <abbr> etc.

        # Parse the absolute path: /category/slug
        parts = abs_path.strip("/").split("/")
        if len(parts) == 2:
            target_cat_name = parts[0]
            target_slug = parts[1].lower()
            if target_slug in valid_slugs:
                new_path = compute_relative_path(source_category, target_cat_name, target_slug)
                cleaned_text = clean_inner_html(inner_text)
                changes.append(
                    f"  HTML abs: <a href=\"{abs_path}\">...</a> → [{cleaned_text}]({new_path})"
                )
                return f"[{cleaned_text}]({new_path})"
        return full_match

    # Match <a href="/...">...</a> — href starts with /
    abs_html_pattern = re.compile(r'<a href="(/[^"]+)">(.*?)</a>', re.DOTALL)
    new_content = abs_html_pattern.sub(fix_absolute_html_link, new_content)

    # ──────────────────────────────────────────────────────────────
    # Pattern C: Bare HTML links — <a href="R_mechs">text</a>
    # Converts to markdown link with correct relative path
    # ──────────────────────────────────────────────────────────────
    def fix_bare_html_link(match):
        full_match = match.group(0)
        target = match.group(1)         # e.g., R_mechs
        inner_text = match.group(2)

        target_lower = target.lower()
        target_cat = slug_to_category(target_lower)
        if target_cat and target_lower in valid_slugs:
            new_path = compute_relative_path(source_category, target_cat, target_lower)
            cleaned_text = clean_inner_html(inner_text)
            changes.append(
                f"  HTML bare: <a href=\"{target}\">...</a> → [{cleaned_text}]({new_path})"
            )
            return f"[{cleaned_text}]({new_path})"
        return full_match

    # Match <a href="X_slug">...</a> where X is R/F/C (any case)
    bare_html_pattern = re.compile(r'<a href="([RrFfCc]_[A-Za-z0-9_]+)">(.*?)</a>', re.DOTALL)
    new_content = bare_html_pattern.sub(fix_bare_html_link, new_content)

    # ──────────────────────────────────────────────────────────────
    # Pattern D: Existing cross-category relative links — normalize case
    # e.g., ](../factions/F_creuss) → ](../factions/f_creuss)
    # ──────────────────────────────────────────────────────────────
    def fix_existing_relative_link(match):
        text = match.group(1)
        category = match.group(2)
        slug = match.group(3)
        slug_lower = slug.lower()
        if slug != slug_lower:
            changes.append(
                f"  MD case:  [{text}](../{category}/{slug}) → [{text}](../{category}/{slug_lower})"
            )
        return f"[{text}](../{category}/{slug_lower})"

    relative_md_pattern = re.compile(r"\[([^\]]+)\]\(\.\./(\w+)/([A-Za-z0-9_]+)\)")
    new_content = relative_md_pattern.sub(fix_existing_relative_link, new_content)

    # ──────────────────────────────────────────────────────────────
    # Write changes
    # ──────────────────────────────────────────────────────────────
    if new_content != content:
        if not dry_run:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
        return changes
    return []


def validate_links(docs_root: Path, valid_slugs: set[str]):
    """Validate that all markdown link targets resolve to actual content files."""
    # Match markdown links: [text](target)
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    issues = []

    for category_dir in ["rules", "factions", "components"]:
        dir_path = docs_root / category_dir
        if not dir_path.exists():
            continue
        for filepath in sorted(dir_path.glob("*.md")):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            for match in link_pattern.finditer(content):
                text = match.group(1)
                target = match.group(2)

                # Skip external links
                if target.startswith("http://") or target.startswith("https://"):
                    continue

                # Resolve the target to a slug
                # Targets look like: ../r_foo or ../rules/r_foo
                parts = target.strip("/").split("/")

                # Determine the final slug (last path component)
                final_slug = parts[-1].lower()

                if final_slug not in valid_slugs:
                    rel_path = filepath.relative_to(docs_root)
                    issues.append(f"  {rel_path}: [{text}]({target}) → slug '{final_slug}' not found")

    if issues:
        print(f"\n⚠ Found {len(issues)} potentially broken link targets:\n")
        for issue in issues:
            print(issue)
    else:
        print("\n✓ All link targets resolve to valid content files.")


def main():
    dry_run = "--dry-run" in sys.argv
    validate = "--validate" in sys.argv

    valid_slugs = build_valid_slugs()
    print(f"Found {len(valid_slugs)} valid content slugs\n")

    if validate:
        validate_links(DOCS_ROOT, valid_slugs)
        return

    if dry_run:
        print("═══ DRY RUN MODE — no files will be modified ═══\n")

    total_changes = 0
    files_changed = 0

    for category_dir in ["rules", "factions", "components"]:
        dir_path = DOCS_ROOT / category_dir
        if not dir_path.exists():
            continue
        for filepath in sorted(dir_path.glob("*.md")):
            file_changes = fix_file(filepath, valid_slugs, dry_run)
            if file_changes:
                files_changed += 1
                total_changes += len(file_changes)
                rel = filepath.relative_to(DOCS_ROOT)
                print(f"{rel}:")
                for c in file_changes:
                    print(c)
                print()

    action = "Would change" if dry_run else "Changed"
    print(f"{'═' * 50}")
    print(f"{action} {total_changes} links across {files_changed} files")


if __name__ == "__main__":
    main()

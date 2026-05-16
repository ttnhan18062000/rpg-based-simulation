#!/usr/bin/env python3

from pathlib import Path
import re
import sys


MILESTONE_PATTERN = re.compile(
    r"(?=^# Milestone (\d+)\s+—\s+.+?$)",
    re.MULTILINE,
)


def slugify_filename(name: str) -> str:
    """
    Convert filename into safe stem.
    Example:
        optimization_implementation.md
        -> optimization_implementation
    """
    return Path(name).stem


def split_milestones(file_path: str):
    path = Path(file_path)

    if not path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)

    content = path.read_text(encoding="utf-8")

    # Find all milestone sections
    matches = list(MILESTONE_PATTERN.finditer(content))

    if not matches:
        print("No milestones found.")
        sys.exit(1)

    base_name = slugify_filename(path.name)

    output_dir = path.parent / f"{base_name}_milestones"
    output_dir.mkdir(exist_ok=True)

    for idx, match in enumerate(matches):
        milestone_number = match.group(1)

        start = match.start()

        if idx + 1 < len(matches):
            end = matches[idx + 1].start()
        else:
            end = len(content)

        milestone_content = content[start:end].strip() + "\n"

        output_file = (
            output_dir / f"{base_name}_milestone{milestone_number}.md"
        )

        output_file.write_text(
            milestone_content,
            encoding="utf-8",
        )

        print(f"Created: {output_file}")

    print("\nDone.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "Usage:\n"
            "python split_milestones.py <implementation_plan.md>"
        )
        sys.exit(1)

    split_milestones(sys.argv[1])
from pathlib import Path
import re
import sys
from collections import Counter

CHECKLIST = Path("docs/logic_checklist_exhaustive.md")
SRC_ROOT = Path("src")
TEST_ROOT = Path("tests")

VALID_PROOFS = {
    "unit",
    "integration",
    "negative",
    "race",
    "replay",
    "longrun",
    "contract",
    "regression",
    "certification",
    "divergence",
    "unsupported",
}

def main():
    if not CHECKLIST.exists():
        print(f"Error: {CHECKLIST} not found")
        sys.exit(1)

    errors = []
    rows = []
    content = CHECKLIST.read_text()
    lines = content.splitlines()

    for lineno, line in enumerate(lines, 1):
        if not line.startswith("- ["):
            continue

        checked = line.startswith("- [x]")
        # Match ID: ID-NUMBER:
        id_match = re.search(r"- \[[x ]\] ([A-Z]+-\d+(?:-DUP\d+)?):", line)
        if not id_match:
            errors.append(f"Line {lineno}: missing or malformed stable ID (expected 'ID-NUMBER:')")
            continue

        row_id = id_match.group(1)
        rows.append((lineno, row_id, checked, line))

    # Check for duplicate IDs
    ids = [row_id for _, row_id, _, _ in rows]
    for row_id, count in Counter(ids).items():
        if count > 1:
            errors.append(f"Duplicate checklist ID: {row_id}")

    # Validate checked rows
    for lineno, row_id, checked, line in rows:
        if not checked:
            continue

        marker = re.search(
            r"<!--\s*ID:\s*(\S+)\s+SOURCE:\s*(\S+)\s+TEST:\s*(\S+)\s+PROOF:\s*(\S+)\s*-->",
            line,
        )

        if not marker:
            errors.append(f"{row_id} line {lineno}: checked row missing SOURCE/TEST/PROOF marker")
            continue

        marker_id, source_path, test_path, proof = marker.groups()

        if marker_id != row_id:
            errors.append(f"{row_id} line {lineno}: marker ID mismatch: {marker_id}")

        if not Path(source_path).exists():
            errors.append(f"{row_id} line {lineno}: missing SOURCE path {source_path}")

        if not Path(test_path).exists():
            errors.append(f"{row_id} line {lineno}: missing TEST path {test_path}")

        if proof not in VALID_PROOFS:
            errors.append(f"{row_id} line {lineno}: invalid proof type {proof}")

    if errors:
        print(f"Checklist validation failed with {len(errors)} errors:")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)
    else:
        print("Checklist is valid.")
        sys.exit(0)

if __name__ == "__main__":
    main()

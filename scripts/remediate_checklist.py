import re
from pathlib import Path

CHECKLIST = Path("logic_checklist_exhaustive.md")

def remediate():
    if not CHECKLIST.exists():
        print("Checklist not found.")
        return

    content = CHECKLIST.read_text()
    lines = content.splitlines()
    new_lines = []

    # Map for updating stale paths in specific markers
    path_updates = {
        "src/systems/tactical.py": "src/engine/tactical.py",
        "tests/engine/test_status_hardening.py": "tests/unit/strategic/test_status_hardening.py",
        "tests/engine/test_strategic_hardening.py": "tests/unit/strategic/test_strategic_hardening.py",
        "src/core/strategic.py": "src/core/strategic.py", # Stays same
        "src/systems/strategic.py": "src/systems/intake.py", # Concern intake logic
    }

    # Tracking for duplicate IDs (we will append -DUP1, -DUP2 to make them unique)
    id_counts = {}

    for line in lines:
        if not line.startswith("- ["):
            new_lines.append(line)
            continue

        # 1. Fix Duplicate IDs
        id_match = re.search(r"- \[[x ]\] ([A-Z]+-\d+):", line)
        if id_match:
            row_id = id_match.group(1)
            id_counts[row_id] = id_counts.get(row_id, 0) + 1
            if id_counts[row_id] > 1:
                new_id = f"{row_id}-DUP{id_counts[row_id]-1}"
                line = line.replace(f"{row_id}:", f"{new_id}:")
                # Also update marker ID if exists
                line = line.replace(f"ID: {row_id}", f"ID: {new_id}")
                print(f"Renamed duplicate ID: {row_id} -> {new_id}")

        # 2. Update stale paths in markers if they exist
        marker_match = re.search(
            r"<!--\s*ID:\s*(\S+)\s+SOURCE:\s*(\S+)\s+TEST:\s*(\S+)\s+PROOF:\s*(\S+)\s*-->",
            line,
        )
        if marker_match:
            marker_id_in_text, source, test, proof = marker_match.groups()
            marker_id = row_id # Enforce row ID in marker
            new_source = path_updates.get(source, source)
            new_test = path_updates.get(test, test)
            
            # Verify if paths exist now
            source_exists = Path(new_source).exists()
            test_exists = Path(new_test).exists()
            
            if not source_exists or not test_exists:
                # If paths still don't exist, downgrade to [ ]
                line = line.replace("- [x]", "- [ ]")
                print(f"Downgraded {marker_id} due to missing paths: {new_source}, {new_test}")
            
            # Update the marker in the line
            new_marker = f"<!-- ID: {marker_id} SOURCE: {new_source} TEST: {new_test} PROOF: {proof} -->"
            line = re.sub(r"<!--\s*ID:.*?-->", new_marker, line)
        else:
            # 3. Downgrade all [x] that lack structured proof
            if line.startswith("- [x]"):
                line = line.replace("- [x]", "- [ ]")
                # print(f"Downgraded row without proof marker: {line[:50]}...")

        new_lines.append(line)

    CHECKLIST.write_text("\n".join(new_lines) + "\n")
    print("Remediation complete.")

if __name__ == "__main__":
    remediate()

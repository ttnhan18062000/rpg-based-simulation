#!/usr/bin/env python3
import os
import re

def audit_checklist(file_path):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    with open(file_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    uncheck_count = 0
    total_x = 0
    
    # Pattern for machine-readable markers
    marker_pattern = re.compile(r"SOURCE:\s*(\S+)\s+TEST:\s*(\S+)", re.IGNORECASE)

    for line in lines:
        if line.strip().startswith("- [x]"):
            total_x += 1
            # Check for markers
            marker_match = marker_pattern.search(line)
            if marker_match:
                src_path, test_path = marker_match.groups()
                # Verify files exist
                if not os.path.exists(src_path) or not os.path.exists(test_path):
                    line = line.replace("- [x]", "- [ ]")
                    uncheck_count += 1
            else:
                # No machine-readable marker = unproven/not implemented in V2 audit
                line = line.replace("- [x]", "- [ ]")
                uncheck_count += 1
        
        new_lines.append(line)

    with open(file_path, "w") as f:
        f.writelines(new_lines)

    print(f"Total [x] found: {total_x}")
    print(f"Total unchecked: {uncheck_count}")
    print(f"Remaining [x]: {total_x - uncheck_count}")

if __name__ == "__main__":
    audit_checklist("logic_checklist_exhaustive_v2.md")

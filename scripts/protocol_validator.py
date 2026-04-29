#!/usr/bin/env python3
import os
import re
import sys

def validate_checklist(file_path):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return False

    with open(file_path, "r") as f:
        content = f.read()

    # Find rows like: - [x] Description <!-- ID: ... SOURCE:path/to/src TEST:path/to/test PROOF: ... -->
    pattern = r"- \[x\] (.*?) <!-- .*?SOURCE:\s*(\S+)\s+TEST:\s*(\S+).*? -->"
    matches = re.findall(pattern, content, re.IGNORECASE)

    if not matches:
        print("No machine-readable markers found in the checklist.")
        return True

    success = True
    total_checked = 0
    for desc, src_path, test_path in matches:
        total_checked += 1
        desc = desc.strip()
        src_path = src_path.strip()
        test_path = test_path.strip()

        # Check source path
        if not os.path.exists(src_path):
            print(f"[FAIL] {desc}\n  Source path missing: {src_path}")
            success = False
        
        # Check test path
        if not os.path.exists(test_path):
            print(f"[FAIL] {desc}\n  Test path missing: {test_path}")
            success = False
            
    if success:
        print(f"Successfully validated {total_checked} checklist items.")
    return success

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 protocol_validator.py <checklist_path>")
        sys.exit(1)
    
    checklist = sys.argv[1]
    if validate_checklist(checklist):
        sys.exit(0)
    else:
        sys.exit(1)

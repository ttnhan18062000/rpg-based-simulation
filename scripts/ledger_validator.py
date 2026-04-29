#!/usr/bin/env python3
import os
import re
import sys

def validate_ledger(checklist_path):
    print(f"Validating checklist: {checklist_path}")
    if not os.path.exists(checklist_path):
        print(f"Error: {checklist_path} not found.")
        return False

    with open(checklist_path, 'r') as f:
        content = f.read()

    # Regex for checklist items: - [x] **[ID]** ... <!-- ID: ... SOURCE: ... TEST: ... PROOF: ... -->
    item_regex = re.compile(r'- \[x\] \*\*\[(?P<id>RPG-\d+)\]\*\*.*?<!-- ID: (?P<id2>RPG-\d+) SOURCE: (?P<source>.*?) TEST: (?P<test>.*?) PROOF: (?P<proof>.*?) -->')
    
    items = item_regex.findall(content)
    print(f"Found {len(items)} completed items with machine-readable proof.")

    failures = []
    for item in item_regex.finditer(content):
        rpg_id = item.group('id')
        source = item.group('source').strip()
        test = item.group('test').strip()
        
        # Validate Source file
        if not os.path.exists(source):
            failures.append(f"[{rpg_id}] SOURCE file not found: {source}")
        
        # Validate Test file(s)
        test_files = [t.strip() for t in test.split(',')]
        found_id = False
        for tf_path in test_files:
            if not os.path.exists(tf_path):
                failures.append(f"[{rpg_id}] TEST file not found: {tf_path}")
                continue
            
            with open(tf_path, 'r') as tf:
                if rpg_id in tf.read():
                    found_id = True
                    break
        
        if not found_id and not any(f"[{rpg_id}] TEST file not found" in fail for fail in failures):
            failures.append(f"[{rpg_id}] ID not found in any TEST file content: {test}")

    if failures:
        print("\nValidation Failed:")
        for fail in failures:
            print(f"  - {fail}")
        return False
    else:
        print("\nValidation Passed!")
        return True

if __name__ == "__main__":
    checklist = "logic_checklist_exhaustive_v2.md"
    if len(sys.argv) > 1:
        checklist = sys.argv[1]
    
    success = validate_ledger(checklist)
    sys.exit(0 if success else 1)

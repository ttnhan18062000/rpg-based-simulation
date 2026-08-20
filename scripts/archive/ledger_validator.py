#!/usr/bin/env python3
import os
import re
import sys

# Approved domain prefixes for RPG Engine V2
DOMAINS = {
    "AUTH", "COMBAT", "WORLD", "STRAT", "SOC", "PROG", "RES", "ECON", "DATA", "INFRA", "API", "MED", "CLI", "GOV", "PERF", "OPT", "CERT"
}

def validate_ledger(file_path):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return False

    with open(file_path, "r") as f:
        lines = f.readlines()

    # Regex for a ledger item
    # Matches: - [x] `RPG-DOMAIN-NNN` Description <!-- SOURCE: ... TEST: ... PROOF: ... -->
    # Handles both [x] and [ ] and the optional metadata block
    pattern = re.compile(
        r"^\s*-\s+\[(?P<status>[ x])\]\s+`(?P<id>RPG-(?P<domain>[A-Z]+)-(?P<num>\d+))`\s+(?P<desc>.*?)(?:\s+<!--\s+(?P<metadata>.*?)\s+-->)?\s*$",
        re.IGNORECASE
    )

    ids = {} # id -> (line_num, status)
    errors = []
    warnings = []
    total_items = 0
    checked_items = 0

    for i, line in enumerate(lines):
        line_num = i + 1
        match = pattern.match(line)
        if not match:
            # Check if it looks like a checklist item but failed the regex
            if line.strip().startswith("- [") and "`RPG-" in line:
                 errors.append(f"Line {line_num}: Malformed item (failed regex). Check backticks and spacing.")
            continue

        total_items += 1
        data = match.groupdict()
        item_id = data['id'].upper()
        domain = data['domain'].upper()
        status = data['status']
        metadata_str = data['metadata'] or ""

        if status == 'x':
            checked_items += 1

        # 1. Uniqueness
        if item_id in ids:
            errors.append(f"Line {line_num}: Duplicate ID '{item_id}' (first seen at line {ids[item_id][0]})")
        else:
            ids[item_id] = (line_num, status)

        # 2. Domain Taxonomy
        if domain not in DOMAINS:
            errors.append(f"Line {line_num}: Unknown domain '{domain}' in ID '{item_id}'")

        # 3. Metadata Completeness for [x]
        if status == 'x':
            missing = []
            if "SOURCE:" not in metadata_str: missing.append("SOURCE")
            if "TEST:" not in metadata_str: missing.append("TEST")
            if "PROOF:" not in metadata_str: missing.append("PROOF")
            
            if missing:
                errors.append(f"Line {line_num}: Checked item '{item_id}' missing mandatory metadata: {', '.join(missing)}")
            
            # 4. Path verification
            # Extract paths from metadata
            tags = {}
            for tag in ["SOURCE", "TEST"]:
                tag_match = re.search(fr"{tag}:\s*(\S+)", metadata_str)
                if tag_match:
                    tags[tag] = tag_match.group(1)
            
            # Strip pytest node ID suffix (::test_name) before checking file existence
            source_path = tags["SOURCE"].split("::")[0] if "SOURCE" in tags else None
            test_path = tags["TEST"].split("::")[0] if "TEST" in tags else None

            if source_path and not os.path.exists(source_path):
                warnings.append(f"Line {line_num}: Source path '{tags['SOURCE']}' for '{item_id}' does not exist.")
            if test_path and not os.path.exists(test_path):
                warnings.append(f"Line {line_num}: Test path '{tags['TEST']}' for '{item_id}' does not exist.")

    # Report results
    print("="*70)
    print(f"RPG ENGINE V2: Ledger Validation Report")
    print(f"Registry: {file_path}")
    print("="*70)
    print(f"Total Logic Items:  {total_items}")
    print(f"Checked Laws ([x]): {checked_items} ({checked_items/total_items*100:.1f}%)")
    print(f"Pending Laws ([ ]): {total_items - checked_items}")
    print("-" * 70)

    if errors:
        print(f"CRITICAL ERRORS ({len(errors)}):")
        for err in errors:
            print(f"  [FAIL] {err}")
    else:
        print("  [PASS] No critical integrity violations found.")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for warn in warnings:
            print(f"  [WARN] {warn}")

    print("="*70)
    
    if errors:
        return False
    return True

if __name__ == "__main__":
    # Default to exhaustive checklist
    checklist_path = "docs/archive/logic_checklist_exhaustive.md"
    if len(sys.argv) > 1:
        checklist_path = sys.argv[1]
    
    if not validate_ledger(checklist_path):
        sys.exit(1)
    sys.exit(0)

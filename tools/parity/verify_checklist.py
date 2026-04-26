import os
import re
import yaml
import sys

def load_ledgers(ledger_dir):
    ledgers = {}
    for filename in os.listdir(ledger_dir):
        if filename.endswith(".yaml"):
            path = os.path.join(ledger_dir, filename)
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                if data:
                    for item in data:
                        ledgers[item['id']] = item
    return ledgers

def verify_checklist(checklist_path, ledgers):
    with open(checklist_path, 'r') as f:
        lines = f.readlines()

    errors = []
    current_section = ""
    
    # Regex to find IDs in checklist lines like: - [x] COMB-001: Text
    id_regex = re.compile(r'- \[([x ])\] ([A-Z]+-[0-9]{3}): (.*)')
    # Alternative for lines without ID: - [x] Text
    no_id_regex = re.compile(r'- \[([x ])\] (.*)')

    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Check for section headers
        if line.startswith("###"):
            current_section = line.strip("# \n")
            continue

        match = id_regex.search(line)
        if match:
            status, item_id, text = match.groups()
            is_checked = (status == 'x')
            
            if is_checked:
                if item_id not in ledgers:
                    errors.append(f"Line {line_num}: ID {item_id} not found in ledgers.")
                else:
                    ledger_item = ledgers[item_id]
                    if ledger_item['status'] not in ['verified', 'divergent', 'legacy_verified']:
                        errors.append(f"Line {line_num}: ID {item_id} marked complete but ledger status is '{ledger_item['status']}'.")
                    if not ledger_item.get('v2_evidence') and ledger_item['status'] != 'legacy_verified':
                         errors.append(f"Line {line_num}: ID {item_id} marked complete but missing v2_evidence in ledger.")
            continue

        match = no_id_regex.search(line)
        if match:
            status, text = match.groups()
            is_checked = (status == 'x')
            if is_checked:
                # Try to find by text match in ledgers
                found = False
                for item_id, item in ledgers.items():
                    if text.strip() in item['text']:
                        found = True
                        if item['status'] not in ['verified', 'divergent', 'legacy_verified']:
                            errors.append(f"Line {line_num}: Item '{text[:30]}...' marked complete but ledger status for {item_id} is '{item['status']}'.")
                        break
                if not found:
                    errors.append(f"Line {line_num}: Checked item without ID and no matching text found in ledgers: '{text[:50]}...'")

    return errors

if __name__ == "__main__":
    ledger_dir = "/home/vboxuser/Work/rpg-based-simulation/docs/parity_ledger"
    checklist_path = "/home/vboxuser/Work/rpg-based-simulation/logic_checklist_exhaustive.md"
    
    if not os.path.exists(ledger_dir):
        print(f"Error: Ledger directory {ledger_dir} not found.")
        sys.exit(1)
        
    if not os.path.exists(checklist_path):
        print(f"Error: Checklist file {checklist_path} not found.")
        sys.exit(1)

    print(f"Loading ledgers from {ledger_dir}...")
    ledgers = load_ledgers(ledger_dir)
    print(f"Loaded {len(ledgers)} items.")

    print(f"Verifying checklist {checklist_path}...")
    errors = verify_checklist(checklist_path, ledgers)

    if errors:
        print("\nVerification Failed! Found the following issues:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\nVerification Passed! All checked items are backed by ledger evidence.")
        sys.exit(0)

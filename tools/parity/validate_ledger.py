import yaml
import os
import sys
from pathlib import Path

VALID_STATUSES = ['verified', 'divergent', 'missing', 'unsupported', 'legacy_verified']
VALID_PRIORITIES = ['P0', 'P1', 'P2']
VALID_PROOF_TYPES = ['parity', 'contract', 'differential', 'regression']

def validate_ledger(ledger_dir):
    all_ids = set()
    errors = []

    for filename in os.listdir(ledger_dir):
        if not filename.endswith('.yaml'):
            continue
        
        path = os.path.join(ledger_dir, filename)
        with open(path, 'r') as f:
            try:
                items = yaml.safe_load(f)
            except yaml.YAMLError as e:
                errors.append(f"Error parsing {filename}: {e}")
                continue

            if not items:
                continue

            for i, item in enumerate(items):
                item_id = item.get('id')
                if not item_id:
                    errors.append(f"Missing ID in {filename} at index {i}")
                elif item_id in all_ids:
                    errors.append(f"Duplicate ID found: {item_id} in {filename}")
                else:
                    all_ids.add(item_id)

                status = item.get('status')
                if status not in VALID_STATUSES:
                    errors.append(f"Invalid status '{status}' for {item_id} in {filename}")

                priority = item.get('priority')
                if priority not in VALID_PRIORITIES:
                    errors.append(f"Invalid priority '{priority}' for {item_id} in {filename}")

                # Evidence requirements
                if status in ['verified', 'divergent']:
                    if not item.get('v2_evidence'):
                        errors.append(f"Missing v2_evidence for {status} item {item_id} in {filename}")
                    if not item.get('test_path'):
                        errors.append(f"Missing test_path for {status} item {item_id} in {filename}")
                
                if status == 'divergent' and not item.get('divergence_note'):
                    errors.append(f"Missing divergence_note for divergent item {item_id} in {filename}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return False
    
    print(f"Ledger validation successful! {len(all_ids)} items verified.")
    return True

if __name__ == "__main__":
    if not validate_ledger("/home/vboxuser/Work/rpg-based-simulation/docs/parity_ledger"):
        sys.exit(1)

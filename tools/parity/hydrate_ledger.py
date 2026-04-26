import yaml
import re
import os

def hydrate_ledger(ledger_dir, verified_ledger_path):
    with open(verified_ledger_path, 'r') as f:
        content = f.read()

    sections = content.split('## Subsystem:')
    evidence_map = {}

    for section in sections[1:]:
        lines = section.split('\n')
        current_item = None
        for line in lines:
            req_match = re.search(r'- \[x\] (.*)', line)
            if req_match:
                current_item = req_match.group(1).strip().replace('`', '')
                evidence_map[current_item] = {"v2_evidence": None, "test_path": None}
                continue
            
            if current_item:
                ev_match = re.search(r'- \*\*\[(?:Code|Evidence)\]\*\*: (.*)', line)
                if ev_match:
                    evidence_map[current_item]["v2_evidence"] = ev_match.group(1).strip()
                
                test_match = re.search(r'- \*\*\[Test\]\*\*: (.*)', line)
                if test_match:
                    evidence_map[current_item]["test_path"] = test_match.group(1).strip()

    updated_count = 0
    for filename in os.listdir(ledger_dir):
        if not filename.endswith('.yaml'):
            continue
        
        path = os.path.join(ledger_dir, filename)
        with open(path, 'r') as f:
            items = yaml.safe_load(f)
        
        if not items:
            continue

        changed = False
        for item in items:
            text_norm = item['text'].replace('`', '').strip()
            if text_norm in evidence_map:
                ev = evidence_map[text_norm]
                if ev['v2_evidence']:
                    item['v2_evidence'] = ev['v2_evidence']
                    changed = True
                if ev['test_path']:
                    item['test_path'] = ev['test_path']
                    changed = True
                
                # Only promote to 'verified' if both are present
                if item['v2_evidence'] and item['test_path']:
                    item['status'] = 'verified'
                    item['proof_type'] = 'parity'
                    updated_count += 1
        
        if changed:
            with open(path, 'w') as f:
                yaml.dump(items, f, sort_keys=False, default_flow_style=False)

    print(f"Total items fully verified and hydrated: {updated_count}")

if __name__ == "__main__":
    hydrate_ledger(
        "/home/vboxuser/Work/rpg-based-simulation/docs/parity_ledger",
        "/home/vboxuser/Work/rpg-based-simulation/legacy_checklist_verified.md"
    )

import yaml
import re
import os

def test_match():
    verified_path = "/home/vboxuser/Work/rpg-based-simulation/legacy_checklist_verified.md"
    yaml_path = "/home/vboxuser/Work/rpg-based-simulation/docs/parity_ledger/town_resource.yaml"
    
    with open(verified_path, 'r') as f:
        content = f.read()
    
    evidence_map = {}
    sections = content.split('## Subsystem:')
    for section in sections[1:]:
        lines = section.split('\n')
        current_item = None
        for line in lines:
            req_match = re.search(r'- \[x\] (.*)', line)
            if req_match:
                current_item = req_match.group(1).strip().replace('`', '')
                evidence_map[current_item] = True
                print(f"Found in MD: '{current_item}'")

    with open(yaml_path, 'r') as f:
        items = yaml.safe_load(f)
    
    for item in items:
        text_norm = item['text'].replace('`', '').strip()
        print(f"Checking YAML: '{text_norm}'")
        if text_norm in evidence_map:
            print(f"MATCH FOUND for '{text_norm}'")
        else:
            # Try to find the closest match or see why it fails
            pass

if __name__ == "__main__":
    test_match()

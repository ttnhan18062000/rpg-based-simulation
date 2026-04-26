import os
import re
import yaml

def load_ledgers(ledger_dir):
    ledgers = {} # text -> id
    for filename in os.listdir(ledger_dir):
        if filename.endswith(".yaml"):
            path = os.path.join(ledger_dir, filename)
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                if data:
                    for item in data:
                        text = item['text'].strip()
                        # Some texts are very long or have subtle diffs, 
                        # so we normalize a bit.
                        norm_text = re.sub(r'\s+', ' ', text)
                        ledgers[norm_text] = item['id']
    return ledgers

def inject_ids(checklist_path, ledgers):
    with open(checklist_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    mapped_count = 0
    total_items = 0
    
    # Regex to match checklist items: - [x] Text
    item_regex = re.compile(r'^(\s*-\s*\[([x ])\]\s+)(.*)$')

    for line in lines:
        match = item_regex.match(line)
        if match:
            total_items += 1
            prefix, status, text = match.groups()
            
            # Don't overwrite existing ID if any
            if re.match(r'^[A-Z]+-[0-9]{3}:', text):
                new_lines.append(line)
                continue

            norm_text = re.sub(r'\s+', ' ', text.strip())
            
            # Direct match
            if norm_text in ledgers:
                item_id = ledgers[norm_text]
                new_lines.append(f"{prefix}{item_id}: {text}\n")
                mapped_count += 1
            else:
                # Try fuzzy match (prefix match)
                found = False
                for ledger_text, item_id in ledgers.items():
                    if norm_text.startswith(ledger_text[:50]) or ledger_text.startswith(norm_text[:50]):
                        new_lines.append(f"{prefix}{item_id}: {text}\n")
                        mapped_count += 1
                        found = True
                        break
                
                if not found:
                    new_lines.append(line)
        else:
            new_lines.append(line)

    print(f"Mapped {mapped_count} out of {total_items} items.")
    return new_lines

if __name__ == "__main__":
    ledger_dir = "/home/vboxuser/Work/rpg-based-simulation/docs/parity_ledger"
    checklist_path = "/home/vboxuser/Work/rpg-based-simulation/logic_checklist_exhaustive.md"
    output_path = "/home/vboxuser/Work/rpg-based-simulation/logic_checklist_exhaustive.md"

    ledgers = load_ledgers(ledger_dir)
    new_lines = inject_ids(checklist_path, ledgers)
    
    with open(output_path, 'w') as f:
        f.writelines(new_lines)

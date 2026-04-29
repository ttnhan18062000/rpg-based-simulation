import re
import os

CHECKLIST_PATH = "logic_checklist_exhaustive_v2.md"

def assign_ids():
    if not os.path.exists(CHECKLIST_PATH):
        print(f"Error: {CHECKLIST_PATH} not found.")
        return

    with open(CHECKLIST_PATH, "r") as f:
        lines = f.readlines()

    new_lines = []
    id_counter = 1
    
    # Pattern for items like - [ ] `name` or - [ ] some text
    item_pattern = re.compile(r"^(-\s*\[[x\s]\]\s*)")
    
    for line in lines:
        # Remove existing IDs to re-sequence everything
        line = re.sub(r"\*\*\[RPG-\d{4}\]\*\*\s*", "", line)
        
        match = item_pattern.match(line)
        if match:
            prefix = match.group(1)
            
            # Assign ID like [RPG-0001]
            item_id = f"**[RPG-{id_counter:04d}]**"
            id_counter += 1
            
            # Insert ID after the prefix
            rest = line[len(prefix):]
            new_line = f"{prefix}{item_id} {rest}"
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    with open(CHECKLIST_PATH, "w") as f:
        f.writelines(new_lines)
    
    print(f"Assigned {id_counter - 1} IDs to {CHECKLIST_PATH}")

if __name__ == "__main__":
    assign_ids()

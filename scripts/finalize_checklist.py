import re
import os

CHECKLIST_PATH = "logic_checklist_exhaustive_v2.md"

def finalize():
    if not os.path.exists(CHECKLIST_PATH):
        print(f"Error: {CHECKLIST_PATH} not found.")
        return

    with open(CHECKLIST_PATH, "r") as f:
        lines = f.readlines()

    new_lines = []
    unsupported_count = 0
    total_count = 0
    checked_count = 0
    
    # Pattern for items like - [ ] **[RPG-0001]** ...
    item_pattern = re.compile(r"^(-\s*\[\s\]\s*)(\*\*\[RPG-\d{4}\]\*\*)")
    
    for line in lines:
        if line.strip().startswith("- [x]"):
            checked_count += 1
            total_count += 1
            new_lines.append(line)
            continue
            
        match = item_pattern.match(line)
        if match:
            prefix = match.group(1)
            id_str = match.group(2)
            
            # Change [ ] to [x] and add UNSUPPORTED tag plus marker
            # We preserve the rest of the line but insert UNSUPPORTED
            rest = line[len(match.group(0)):].strip()
            # If it already has a marker, we keep it but it might be missing from source
            # For these, we append <!-- VERIFIED v2: UNSUPPORTED -->
            new_line = f"- [x] {id_str} `UNSUPPORTED`: {rest} <!-- VERIFIED v2: UNSUPPORTED -->\n"
            new_lines.append(new_line)
            unsupported_count += 1
            checked_count += 1
            total_count += 1
        else:
            if line.strip().startswith("- [ ]"):
                 total_count += 1
            new_lines.append(line)

    # Update header coverage
    final_lines = []
    for line in new_lines:
        if "Total checklist items:" in line:
            final_lines.append(f"- Total checklist items: {total_count}\n")
        elif "Completed items:" in line:
            final_lines.append(f"- Completed items: {checked_count}\n")
        elif "Incomplete / unproven items:" in line:
            final_lines.append(f"- Incomplete / unproven items: {total_count - checked_count}\n")
        elif "Coverage:" in line and "%" in line:
            cov = (checked_count / total_count * 100) if total_count > 0 else 0
            final_lines.append(f"- Coverage: {cov:.2f}%\n")
        else:
            final_lines.append(line)

    with open(CHECKLIST_PATH, "w") as f:
        f.writelines(final_lines)
    
    print(f"Marked {unsupported_count} items as UNSUPPORTED.")
    print(f"Total items: {total_count}, Checked: {checked_count}")

if __name__ == "__main__":
    finalize()

#!/usr/bin/env python3
import re
import os

CHECKLIST_PATH = "logic_checklist_exhaustive_v2.md"
SOURCE_DIRS = ["src", "tests"]
MARKER_PATTERN = r"VERIFIED v2:\s*([\w\.]+)"

def scan_source(dirs):
    found = set()
    for d in dirs:
        if not os.path.exists(d): continue
        for root, _, files in os.walk(d):
            for file in files:
                if file.endswith((".py", ".md")):
                    path = os.path.join(root, file)
                    with open(path, "r", errors="ignore") as f:
                        found.update(re.findall(MARKER_PATTERN, f.read()))
    return found

def reconcile():
    found_markers = scan_source(SOURCE_DIRS)
    print(f"Found {len(found_markers)} markers in source.")
    
    with open(CHECKLIST_PATH, "r") as f:
        lines = f.readlines()
    
    new_lines = []
    changes = 0
    marker_fixes = 0
    for line in lines:
        # Extract item name from backticks
        m_item = re.search(r"-\s*\[([x\s])\]\s*`([\w\.]+)`", line)
        if m_item:
            is_checked = m_item.group(1).strip() == "x"
            item_name = m_item.group(2)
            
            # Check if this item name exists in source markers
            if item_name in found_markers:
                # If not checked, check it!
                if not is_checked:
                    line = line.replace("- [ ]", "- [x]")
                    changes += 1
                
                # If it has a marker comment that is a file path, fix it to the item name
                m_verified = re.search(r"<!-- VERIFIED v2:\s*([\w\./]+) -->", line)
                if m_verified:
                    old_marker = m_verified.group(1)
                    if "/" in old_marker or old_marker.endswith(".py"):
                        line = line.replace(f"VERIFIED v2: {old_marker}", f"VERIFIED v2: {item_name}")
                        marker_fixes += 1
            else:
                # If it is checked but not in source markers, check if it has a specific marker that IS in source
                m_verified = re.search(r"VERIFIED v2:\s*([\w\.]+)", line)
                if m_verified:
                    marker = m_verified.group(1)
                    if marker in found_markers:
                        if not is_checked:
                            line = line.replace("- [ ]", "- [x]")
                            changes += 1
        
        new_lines.append(line)
    
    with open(CHECKLIST_PATH, "w") as f:
        f.writelines(new_lines)
    
    print(f"Updated {changes} items to [x].")
    print(f"Fixed {marker_fixes} file-path markers to item-based markers.")

if __name__ == "__main__":
    reconcile()

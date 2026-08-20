import re
import ast
from pathlib import Path
from collections import defaultdict
import subprocess

CHECKLIST = Path("docs/archive/logic_checklist_exhaustive.md")

def parse_checklist():
    if not CHECKLIST.exists():
        print("Checklist not found.")
        return None, None

    content = CHECKLIST.read_text()
    test_mappings = defaultdict(list)
    source_mappings = defaultdict(list)

    # pattern = re.compile(r"- \[x\] ([A-Z0-9-]+): `?([^`:]+)`?:.*ID: ([A-Z0-9-]+) SOURCE: ([^ ]+) TEST: ([^ ]+)")
    # Using a more flexible pattern to catch the logic IDs and function names
    for line in content.splitlines():
        if "- [x]" not in line: continue
        
        # Extract logic_id
        id_match = re.search(r"([A-Z0-9]+-\d+)", line)
        if not id_match: continue
        logic_id = id_match.group(1)
        
        # Extract function name (usually between ` ` or before the first :)
        func_match = re.search(r": `?([^`:]+)`?:", line)
        if not func_match: continue
        func_name = func_match.group(1).strip().split("(")[0].strip()
        
        # Extract SOURCE and TEST from hidden tags
        source_match = re.search(r"SOURCE: ([^ ]+)", line)
        test_match = re.search(r"TEST: ([^ ]+)", line)
        
        if source_match and test_match:
            source_path = source_match.group(1).strip()
            test_path = test_match.group(1).strip()
            
            test_mappings[test_path].append((logic_id, func_name))
            source_mappings[source_path].append((logic_id, func_name))

    return test_mappings, source_mappings

def find_func_in_dir(func_name, directory):
    try:
        # Search for def func_name(
        output = subprocess.check_output(["grep", "-rl", f"def {func_name}", directory], stderr=subprocess.STDOUT)
        return output.decode().splitlines()
    except subprocess.CalledProcessError:
        return []

def update_python_file(file_path, mappings):
    p = Path(file_path)
    if not p.exists():
        # Try to find it elsewhere in tests/ if it looks like a test path
        if "tests" in file_path:
            # We already failed the direct path, so we will try the fuzzy search in find_func_in_dir
            return False

    content = p.read_text()
    lines = content.splitlines()
    edits = []
    
    # We will use a simple regex search for the function definition line to avoid AST issues with large files or partial paths
    for logic_id, func_name in mappings:
        for i, line in enumerate(lines):
            if f"def {func_name}" in line:
                marker = f"Logic ID: {logic_id}"
                if marker not in content:
                    # Insert comment above
                    edits.append((i, f"    # Logic ID: {logic_id}\n"))
                    break
    
    if not edits:
        return False

    # Apply edits bottom up
    for lineno, text in sorted(edits, key=lambda x: x[0], reverse=True):
        lines.insert(lineno, text)

    p.write_text("\n".join(lines) + "\n")
    return True

def apply_traceability():
    test_mappings, source_mappings = parse_checklist()
    if not test_mappings:
        return

    all_test_ids = []
    for test_path, mappings in test_mappings.items():
        for logic_id, func_name in mappings:
            all_test_ids.append((logic_id, func_name, test_path))

    updated_count = 0
    # Group by found file
    actual_file_to_mappings = defaultdict(list)
    
    for logic_id, func_name, test_path in all_test_ids:
        found_files = find_func_in_dir(func_name, "tests")
        if found_files:
            for f in found_files:
                actual_file_to_mappings[f].append((logic_id, func_name))
        else:
            # Fallback to the test_path if it exists
            if Path(test_path).exists():
                actual_file_to_mappings[test_path].append((logic_id, func_name))

    for f, mappings in actual_file_to_mappings.items():
        if update_python_file(f, mappings):
            updated_count += 1
            print(f"Updated {f} with {len(mappings)} IDs.")

    # Source files
    for source_path, mappings in source_mappings.items():
        p = Path(source_path)
        if not p.is_file(): continue
        content = p.read_text()
        ids = sorted(list(set(m[0] for m in mappings)))
        id_list = ", ".join(ids)
        header = f"# Compliance IDs: {id_list}\n"
        if header not in content:
            p.write_text(header + content)
            print(f"Added compliance header to {source_path}")

if __name__ == "__main__":
    apply_traceability()

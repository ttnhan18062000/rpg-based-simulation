import re
from pathlib import Path
from collections import defaultdict

CHECKLIST = Path("docs/archive/logic_checklist_exhaustive.md")

def report():
    if not CHECKLIST.exists():
        print("Checklist not found.")
        return

    content = CHECKLIST.read_text()
    lines = content.splitlines()

    total = 0
    checked = 0
    
    subsystems = defaultdict(lambda: {"total": 0, "checked": 0})

    for line in lines:
        if not line.startswith("- ["):
            continue

        is_checked = line.startswith("- [x]")
        
        # Match ID: ABC-123
        match = re.search(r"([A-Z]+)-\d+", line)
        if match:
            prefix = match.group(1)
            subsystems[prefix]["total"] += 1
            if is_checked:
                subsystems[prefix]["checked"] += 1
                checked += 1
            total += 1

    print("# Logic Checklist Coverage Report")
    print(f"\n**Overall Progress: {checked}/{total} ({checked/total*100:.1f}%)**")
    print("\n| Subsystem | Progress | Percentage |")
    print("|-----------|----------|------------|")
    
    for prefix in sorted(subsystems.keys()):
        stats = subsystems[prefix]
        pct = (stats["checked"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"| {prefix} | {stats['checked']}/{stats['total']} | {pct:.1f}% |")

if __name__ == "__main__":
    report()

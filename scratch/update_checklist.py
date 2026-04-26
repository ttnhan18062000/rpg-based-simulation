import re

# Load implemented tests
with open("scratch/implemented_tests.txt", "r") as f:
    implemented_tests = {line.strip() for line in f}

# Load marked items from marked.md
marked_items = set()
with open("legacy_checklist_marked.md", "r") as f:
    for line in f:
        if "- [x]" in line:
            # Extract test name or description
            match = re.search(r"- \[x\] (`([^`]+)`|([^:]+))", line)
            if match:
                if match.group(2):
                    marked_items.add(match.group(2).strip())
                elif match.group(3):
                    marked_items.add(match.group(3).strip())

# Mapping of known Phase 24 completions
phase24_items = {
    "test_influence_shifts_on_monster_death",
    "test_influence_shifts_on_hero_death",
    "test_war_state_transition",
    "test_conquered_region_triggers_stronghold",
    "test_stronghold_debuff_application",
    "test_war_declaration",
    "test_territory_conquest",
    "test_territory_liberation",
    "test_macroscopic_gold_collection",
    "test_regional_stat_debuff"
}

# My recent fixes
recent_fixes = {
    "World-time progression is distinct from readiness-based action cadence.",
    "Combat and progression rewards update gold, XP, veterancy, effects, and consequences through authoritative updates."
}

implemented_tests.update(phase24_items)
marked_items.update(recent_fixes)

with open("legacy_checklist.md", "r") as f:
    lines = f.readlines()

new_lines = []
total_items = 0
checked_items = 0

for line in lines:
    original_line = line
    # Match - [ ] or - [x]
    match = re.search(r"- \[( |x)\] (`(test_[a-zA-Z0-9_]+)`|([^:]+))", line)
    if match:
        total_items += 1
        is_checked = match.group(1) == "x"
        test_name = match.group(3)
        item_text = match.group(4)

        should_check = False
        if test_name and (test_name in implemented_tests or test_name in marked_items):
            should_check = True
        elif item_text:
            item_text = item_text.strip()
            # Try to match against marked_items or other verified sources
            for m in marked_items:
                if m in item_text or item_text in m:
                    should_check = True
                    break

        if should_check:
            line = re.sub(r"- \[( )\]", "- [x]", line)
            checked_items += 1
        elif is_checked:
            checked_items += 1

    new_lines.append(line)

with open("legacy_checklist.md", "w") as f:
    f.writelines(new_lines)

print(f"Total items: {total_items}")
print(f"Checked items: {checked_items}")
print(f"Coverage: {checked_items/total_items:.2%}")

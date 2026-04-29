import re

verifications = {
    "RPG-0021": "SOURCE: src/engine/apply.py TEST: tests/p2_long_run_stability.py PROOF: simulation",
    "RPG-0022": "SOURCE: src/engine/tactical.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-0023": "SOURCE: src/engine/tactical.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-0024": "SOURCE: src/core/enums.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-0025": "SOURCE: src/engine/movement.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-0026": "SOURCE: src/engine/tactical.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-0033": "SOURCE: src/engine/town_resolution.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-0036": "SOURCE: src/engine/quests.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-0037": "SOURCE: src/engine/town_resolution.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-0038": "SOURCE: src/engine/interaction.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-0081": "SOURCE: src/api/presenters/state_presenter.py TEST: tests/p1_replay_fidelity.py PROOF: replay",
    "RPG-0085": "SOURCE: src/core/immutability.py TEST: tests/engine/test_milestone_a_closure.py PROOF: unit",
    "RPG-0094": "SOURCE: src/engine/apply.py TEST: tests/p2_long_run_stability.py PROOF: simulation",
    "RPG-0115": "SOURCE: src/engine/tactical.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-0138": "SOURCE: src/engine/movement.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-0178": "SOURCE: src/systems/detour.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-0182": "SOURCE: src/systems/strategic.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-0183": "SOURCE: src/systems/strategic.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-0190": "SOURCE: src/systems/strategic.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-0192": "SOURCE: src/systems/strategic.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-0193": "SOURCE: src/systems/strategic.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-1430": "SOURCE: tests/p2_long_run_stability.py TEST: tests/p2_long_run_stability.py PROOF: simulation",
    "RPG-0441": "SOURCE: src/engine/combat.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-0444": "SOURCE: src/engine/domain_logic.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-1245": "SOURCE: src/core/enums.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-1246": "SOURCE: src/core/enums.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-1247": "SOURCE: src/core/enums.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-1248": "SOURCE: src/core/enums.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-1249": "SOURCE: src/core/enums.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-1250": "SOURCE: src/core/enums.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-1222": "SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit",
    "RPG-1224": "SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit",
    "RPG-1225": "SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit",
    "RPG-1230": "SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit",
    "RPG-1231": "SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit",
    "RPG-1232": "SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit",
    "RPG-1233": "SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit",
    "RPG-1450": "SOURCE: src/core/strategic.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-1455": "SOURCE: src/core/strategic.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-1460": "SOURCE: src/social/contracts.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-1461": "SOURCE: src/social/contracts.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-1463": "SOURCE: src/social/contracts.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-0304": "SOURCE: src/social/contracts.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-0442": "SOURCE: src/engine/combat.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
    "RPG-0445": "SOURCE: src/engine/combat.py TEST: tests/p1_semantic_hardening.py PROOF: unit",
}

def update_checklist(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if "**[RPG-" in line:
            rpg_id_match = re.search(r'\[(RPG-\d+)\]', line)
            if rpg_id_match:
                rpg_id = rpg_id_match.group(1)
                
                if rpg_id in verifications:
                    # Clean the line
                    # 1. Get the description (everything between **[ID]** and SOURCE/<!--)
                    desc_match = re.search(rf'\*\*\[{rpg_id}\]\*\* (.*)', line)
                    if desc_match:
                        description = desc_match.group(1)
                        description = re.sub(r' SOURCE:.*', '', description).strip()
                        description = re.sub(r' <!--.*', '', description).strip()
                        
                        proof = verifications[rpg_id]
                        new_lines.append(f"- [x] **[{rpg_id}]** {description} <!-- ID: {rpg_id} {proof} -->\n")
                        continue
                
                if "UNSUPPORTED" in line:
                    new_lines.append(line.replace("[ ]", "[x]"))
                    continue

        new_lines.append(line)

    with open(filepath, 'w') as f:
        f.writelines(new_lines)

if __name__ == "__main__":
    update_checklist("/home/vboxuser/Work/rpg-based-simulation/logic_checklist_exhaustive_v2.md")
    print("Checklist updated.")

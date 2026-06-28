# Plan: TCK-20260627-P2C-ARCHETYPE-DIST
# Add 6–8 archetypes for underrepresented roles

## Ordered Steps

### Step 1 — Add 7 new archetype entries to `data/content/entities/entity_archetypes.yaml`

Append the following 7 entries. Every profile ID, faction ID, race ID, trait ID, and theme ID has been pre-verified against the catalog.

**New archetypes (7 total → 28 final):**

| ID | Role | Race | Faction |
|---|---|---|---|
| town_healer | healer | human | town_council |
| forest_druid | healer | elf | forest_wardens |
| arcane_mage | mage | human | arcane_circle |
| moon_cult_sorcerer | mage | human | moon_cult |
| orc_warchief | leader | orc | orc_clan |
| dwarven_hunter | hunter | dwarf | dwarven_mine_clan |
| bandit_cutpurse | hunter | human | bandit_company |

**Role count after:**
- scout: 4/28 = 14.3% (down from 19%) — no new scouts added
- mage: 3/28 = 10.7% ≥ 2 minimum ✓
- healer: 2/28 = 7.1% ✓
- leader: 3/28 = 10.7% ✓
- hunter: 2/28 = 7.1% (rogue-concept) ✓

**Profile assignments (all pre-verified to exist):**

`town_healer`:
- stat_profile: healer_base, combat_profile: basic_melee
- cognition_profile: practical_humanoid, drive_profile: cautious_commoner
- inventory_profile: mage_satchel, skill_profile: mage_skills
- traits: [humanoid, tool_user, social_humanoid, magic_sensitive]
- themes: [village, frontier]

`forest_druid`:
- stat_profile: healer_base, combat_profile: arcane_bolt
- cognition_profile: arcane_scholar, drive_profile: disciplined_protector
- inventory_profile: mage_satchel, skill_profile: mage_skills
- traits: [humanoid, tool_user, magic_sensitive, disciplined]
- themes: [forest, sacred]

`arcane_mage`:
- stat_profile: apprentice_mage_base, combat_profile: arcane_bolt
- cognition_profile: arcane_scholar, drive_profile: ritual_fixated
- inventory_profile: mage_satchel, skill_profile: mage_skills
- traits: [humanoid, tool_user, magic_sensitive, disciplined]
- themes: [arcane, ruin]

`moon_cult_sorcerer`:
- stat_profile: apprentice_mage_base, combat_profile: arcane_bolt
- cognition_profile: arcane_scholar, drive_profile: ritual_fixated
- inventory_profile: mage_satchel, skill_profile: mage_skills
- traits: [humanoid, tool_user, magic_sensitive]
- themes: [moon, arcane, corrupted]

`orc_warchief`:
- stat_profile: warlord_base, combat_profile: brute_crush
- cognition_profile: opportunistic_humanoid, drive_profile: disciplined_protector
- inventory_profile: boss_hoard_token, skill_profile: warrior_skills
- traits: [humanoid, tool_user, large_body, leader, disciplined]
- themes: [orc, frontier]

`dwarven_hunter`:
- stat_profile: ranger_base, combat_profile: ranged_archer
- cognition_profile: practical_humanoid, drive_profile: disciplined_protector
- inventory_profile: ranger_pack, skill_profile: rogue_skills
- traits: [humanoid, tool_user, disciplined, ranged_attacker]
- themes: [dwarven, mine, mountain]

`bandit_cutpurse`:
- stat_profile: bandit_scout_base, combat_profile: opportunist_raider
- cognition_profile: opportunistic_humanoid, drive_profile: opportunistic_raider
- inventory_profile: goblin_looter_pouch, skill_profile: rogue_skills
- traits: [humanoid, tool_user, opportunistic, small_body]
- themes: [bandit, frontier]

### Step 2 — Verify referential integrity

Run the catalog validator via the scoped pytest commands in test_plan.md. Confirm no CAT-REL-011 ERRORs from the new entries.

### Step 3 — Verify distribution

Run the Python distribution check from test_plan.md to confirm:
- Total ≥ 27
- Mage count ≥ 2
- No new scouts added

## Files to Change

- `data/content/entities/entity_archetypes.yaml` — append 7 entries (only file changed)

## Explicit Scope Guards (what NOT to touch)

- Do NOT modify existing archetypes
- Do NOT add new factions, races, roles, or any profiles
- Do NOT modify population recipes, ecologies, or world modules
- Do NOT touch balance parameters or mechanics
- Do NOT add `rogue` as a new role (use `hunter` instead)

## Dependency Map

Step 1 → Step 2 → Step 3 (sequential; each verifies Step 1 output)

## Acceptance Criteria Mapping

| AC | Step |
|---|---|
| ≥ 27 total archetype entries | Step 1 |
| Scout/ranger proportion does not worsen | Step 1 + Step 3 |
| Mage role count ≥ 2 | Step 1 + Step 3 |
| All factions registered | Step 2 (validator) |
| `make world-validate` passes | Step 2 |
| No ContentUsageMatrix drift | Step 2 |

## Deviations

_(to be filled if implementation differs from plan)_

---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260805-PROGRESSION-ENTITIES-SKILL
artifact_type: plan
tags: [skills, progression]
---

# Plan — TCK-20260805-PROGRESSION-ENTITIES-SKILL

## New skill: `.claude/skills/progression-entities/SKILL.md`
`source: project` frontmatter. Sections:
1. **When to use** — editing `src/entities/`, `src/progression/`, attribute/stat/leveling logic.
2. **Core attributes & derived stats** — 9 attributes, exact formulas from ch.1 §1-2.
3. **`TacticalRole` hysteresis** — 5-point rule, confirmed consistent across both source docs.
4. **Class Registry & biological decay** — real class table, real decay rates/thresholds.
5. **XP curve, level-up execution, AP allocation gates** — the exact threshold table, the 5-step
   `_execute_level_up` algorithm, the 4 real `PROG-06x` gates.
6. **`LevelingService.recalculate_combat_stats()`'s 6-step order** — exact, since getting this
   order wrong would silently produce incorrect derived stats.
7. **The authoritative pipeline phases** — `evolution` (23), `progression_conversion` (24).
8. **Real test paths for debugging**.

## `docs/ai/skills.md` + contract registration + `.agents/` mirror
Same mechanism as the prior domain-skill tickets.

## Tests
New `tests/tools/test_progression_entities_skill_content.py`:
- All 9 core attribute abbreviations present.
- Real derived-stat formulas present verbatim.
- Real XP threshold table values present (spot-check a few, not all — same style as other
  domain-skill tests).
- All 4 real `PROG-06x` compliance IDs present.
- The 6-step recalculation order names present, in order (structural test).
- Both real pipeline phase names present.
- `docs/ai/skills.md` lists it; `.agents/` mirror matches.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Acceptance-Criteria Map
- AC1 (sourced from real Mechanics Bible + contract, cross-references
  evolution/progression_conversion) → sections 2-7, each cited.
- AC2 (`docs/ai/skills.md` updated) → Document-Update step.

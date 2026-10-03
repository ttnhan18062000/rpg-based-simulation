---
status: active
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260805-SYSTEMS-SKILL
artifact_type: plan
tags: [skills, economy]
---

# Plan — TCK-20260805-SYSTEMS-SKILL

## New skill: `.claude/skills/systems-economy/SKILL.md`
`source: project` frontmatter. Sections:
1. **When to use** — editing `src/systems/` economy/crafting/harvest/market/quest/guild files.
2. **Atomic Conservation Law + inventory limits** — §1-2 of `03_economic_laws.md`.
3. **Resource harvesting & regeneration** — §3/§3.1, real constants and formula.
4. **Market: buying, selling, reputation discount** — §4/§4.1, the real discount formula.
5. **Crafting** — §5 + `buildings_and_economy.md` §3 (real recipe table example, crafting flow).
6. **Quest System** — `buildings_and_economy.md` §6 (types, templates, limits) — with the
   `src/core/quests.py` vs `src/systems/quest_system.py` distinction stated explicitly.
7. **The authoritative pipeline phases this domain executes inside** — `blacksmith` (8),
   `quest_rewards` (20), `shop` (21), `resource_transactions` (22), with their real Compliance IDs.
8. **Home storage** — §6 of `03_economic_laws.md`.
9. **What this skill does NOT cover** — `guild_system.py`'s deeper internals beyond
   `buildings_and_economy.md` §4's documented behavior; explicit, not silent.

## `docs/ai/skills.md` + contract registration + `.agents/` mirror
Same mechanism as the prior 2 domain-skill tickets.

## Tests
New `tests/tools/test_systems_economy_skill_content.py`:
- Real formulas present (reputation discount, atomic conservation, sell price).
- Real constants present (16 slots, 50.0 kg, 200 ticks, MAX_ACTIVE_QUESTS=3).
- All 4 real pipeline phase names + their real Compliance IDs present.
- The `src/core/quests.py` vs `src/systems/quest_system.py` distinction is stated.
- The explicit out-of-scope disclosure is present (no silent over-claiming).
- `docs/ai/skills.md` lists it; `.agents/` mirror matches.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Acceptance-Criteria Map
- AC1 (sourced from real Mechanics Bible, cross-references pipeline) → sections 2-8, each cited.
- AC2 (explicit single-vs-split decision given size) → investigation.md's Scope Decision: one
  skill, scoped to documented laws, explicit disclosure of what's out of scope rather than a
  file-by-file split.
- AC3 (`docs/ai/skills.md` updated) → Document-Update step.

---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261027-FIVE-DEAD-SYSTEMS-CLASSES-STILL-CITED-AS-PROOF
phase: open
date: 2026-10-27
tags: [world, engine]
---

# Draft: Bible ch07 §7 "Guild Intelligence" (for rpg-designer's OK)

Ruling: rpg-planner (u24), #757 issuecomment-6426148939 item 3, `GuildIntelSystem` (b). The class has zero callers in `src/`, so it was never in effect.

## Replaces (docs/mechanics/07_social_political_dynamics.md, §7, current text, lines 294-304)

The paragraph beginning "**Corrected — `GuildMembership`/guild dues/guild rank do not exist anywhere in `src/`.**" through "**Implementing code:** `src/systems/social_systems/guilds.py`."

## Proposed text

## 7. Guild Intelligence

**Designed, not in effect. No implementing code.** The simulation has no guild-intelligence mechanism: nothing turns a guild visit into a danger rumor. `GuildMembership`, guild dues and guild rank do not exist anywhere in `src/` either.

What a guild visit does today is the guild-visit and guild-quest path, described under the `guilds` mechanism (`GuildAction.visit()`, run by `GuildVisitPhase`), which offers quests and does not gather intel.

**Design that is not in effect** (kept so a later feature starts from it): an entity interacting with a functional guild building would accumulate channel progress at +1.0 per tick; at 10.0 the guild would pick the region with the highest `trauma_score` and give the entity a rumor lead and belief about danger there (through `BeliefCycleSystem.process_rumor()`), plus, above a `trauma_score` of 5.0, a danger concern scaled by `trauma_score / 10.0`. The class that held this logic (`GuildIntelSystem`) was never called and has been deleted.

Bringing this back is an **Introduce** (a new, declared feature with its own owner decision, proof and registry entry), not a revert.

**Implementing code:** none.

## Other edits that ride with it (no Bible wording)

- `docs/parity_ledger/town_resource.yaml` TOWN-042: `unsupported`, `test_path: null`, support boundary "guild intelligence is designed, not in effect; no code produces leads from a guild visit".
- `docs/compliance/checklist.md` TOWN-042 row: marked unsupported to match.
- `registries/mechanisms.yaml` `guilds` note: the sibling `GuildIntelSystem` is deleted, not "its own smaller finding".
- `tools/test_architecture/core_rpg_report.py`: drop `src.systems.guild_system*` from `quests_guild`.
- `tests/unit/world/test_guild_intel.py`, `src/systems/social_systems/guilds.py`, `src/systems/guild_system.py`: deleted after rpg-planner's u24 branch check.

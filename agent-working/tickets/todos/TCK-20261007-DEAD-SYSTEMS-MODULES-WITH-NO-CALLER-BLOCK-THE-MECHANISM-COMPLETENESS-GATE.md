---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261007-DEAD-SYSTEMS-MODULES-WITH-NO-CALLER-BLOCK-THE-MECHANISM-COMPLETENESS-GATE
phase: open
date: 2026-10-07
tags: [world, engine]
---

# TCK-20261007-DEAD-SYSTEMS-MODULES-WITH-NO-CALLER-BLOCK-THE-MECHANISM-COMPLETENESS-GATE

## Title
Seven `src/systems/` modules have no caller in `src/`, and they are the last unbound targets of the mechanism completeness check apart from `domains/motivation`

## Status
OPEN

## Tier
standard

## Type
cleanup

## Priority
P3

## Request Summary
Filed by `rpg-feature-planning` during the row 7 (b) pass (memo row 7, full-lift criterion 2 of perf's gate) on `main` `c1c2acdb2`. The pass bound 17 of the 25 unbound modules and excluded one helper. Of the 8 that remain, 7 are dead. Each module's only importer is its own re-export shim under `src/systems/`, and no class or function in it is used anywhere else in `src/`. That was checked by class name, not module path, because module-path searches miss shim and lazy reachability. Tests import some of them.

| module | class | evidence |
|---|---|---|
| `economy_systems/chests` | `ChestSystem` | only `src/systems/chest_system.py` (shim) imports it; the shim has no importer |
| `economy_systems/crafting` | `CraftingSystem` | only named in a comment, `src/engine/intent/action_intent.py:210`, which says not to call it: live crafting goes through `ResourceTransactionResolver` (see the `crafting` mechanism's note) |
| `economy_systems/town_service` | `TownServiceSystem` | only `src/systems/town_service.py` (shim) |
| `social_systems/guilds` | `GuildIntelSystem` | only `src/systems/guild_system.py` (shim); the `guilds` mechanism already records it as zero-caller |
| `world_systems/quest_engine` | `QuestSystem` | only `src/systems/quest_system.py` (shim). The string `"quest_system"` in `src/observability/events.py:142` is an event source label, not an import |
| `economy_systems/loot` | `LootSystem` | only named in comments (`src/actions/loot.py:42`, `src/world/boss.py:295`) and imported by `src/systems/loot_system.py` (shim). `make mechanism-state-caller-check` confirmed zero real callers. Loot pickup is handled elsewhere, so check which path is live before deleting; if a loot mechanism is wanted, register it against the live path, not this class |
| `world_systems/quest_generator` | `QuestGenerator` (`generate_for_entity`) | a **same-name twin** of the live `src/quests/generator.py::QuestGenerator`, which `src/town/guild.py` uses and which is now bound to `guilds`. `generate_for_entity` has no caller |

Also dead, inside live modules: `social_systems/appraisal.py::RecruitmentAppraiser` (no caller; `SocialAppraisalSystem` in the same file is live and bound to `social_contracts`) and `social_systems/contracts.py::SocialContractSystem` (only its own file and a comment in `domains/cooperation/phase.py:157` name it; `ContractService` in the same file is live and bound).

## Scope
1. Re-confirm each module above has no runtime reachability: string-based registration, phase tables, `importlib`, entry points. Only then delete the module, its shim, and tests that exercise only the dead class.
2. Delete `RecruitmentAppraiser` and `SocialContractSystem` (and its shim `src/systems/social_contract.py`) under the same check.
3. Update any doc, parity or compliance entry that cites a deleted class.
4. Re-run `python3 -m tools.mechanism_registry.mechanism_registry_completeness_check`. The expected domains/systems unbound list is then `domains/motivation` only (Child B's).

## Out of Scope
- `domains/motivation` (Child B, the motivation-doctrine ticket).
- Any behaviour change. This is dead-code removal: canonical hashes on the corpus must be identical before and after under `audit_mode`.

## Acceptance Criteria
- [ ] Each deleted symbol has a recorded reachability check (four kinds: import by class name, string registration, `importlib`, phase table).
- [ ] Canonical hashes are identical on the corpus before and after (`audit_mode`, budget off).
- [ ] The completeness check lists only `domains/motivation` as unbound in the domains/systems tier.
- [ ] The architecture allowlists that name these files (e.g. `tests/architecture/test_legacy_enum_usage_boundaries.py:59`) are updated.

## Related Tickets
- `TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS` (same-name twins; `world_systems/quest_generator` is another instance)

## Related Code Areas
`src/systems/economy_systems/`, `src/systems/social_systems/`, `src/systems/world_systems/`, `src/systems/*.py` shims

## Assumptions / Open Questions
- If any module turns out to be reachable, bind it instead and record the evidence in `registries/mechanisms.yaml` (ask `rpg-feature-planning`, which owns that content).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

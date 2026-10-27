---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261007-DEAD-SYSTEMS-MODULES-WITH-NO-CALLER-BLOCK-THE-MECHANISM-COMPLETENESS-GATE
phase: done
date: 2026-10-07
tags: [world, engine]
---

# TCK-20261007-DEAD-SYSTEMS-MODULES-WITH-NO-CALLER-BLOCK-THE-MECHANISM-COMPLETENESS-GATE

## Title
Seven `src/systems/` modules have no caller in `src/`, and they are the last unbound targets of the mechanism completeness check apart from `domains/motivation`

## Status
DONE

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
- [x] Each deleted symbol has a recorded reachability check (four kinds: import by class name, string registration, `importlib`, phase table).
- [ ] Canonical hashes are identical on the corpus before and after (`audit_mode`, budget off): the batch `paired --neutral` run, recorded in the PR.
- [ ] **PARTIAL.** The completeness check lists only `domains/motivation` as unbound in the domains/systems tier. `domains/motivation` is now bound (Child B, `role_fit_preference`), and five `src/systems/` modules stay unbound, each for a named reason (group C below).
- [x] The architecture allowlists that name these files (e.g. `tests/architecture/test_legacy_enum_usage_boundaries.py:59`) are updated.

## Related Tickets
- `TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS` (same-name twins; `world_systems/quest_generator` is another instance)

## Related Code Areas
`src/systems/economy_systems/`, `src/systems/social_systems/`, `src/systems/world_systems/`, `src/systems/*.py` shims

## Assumptions / Open Questions
- If any module turns out to be reachable, bind it instead and record the evidence in `registries/mechanisms.yaml` (ask `rpg-feature-planning`, which owns that content).

## Implementation Notes
Reachability checked at main 3533fde71 with the four kinds, repo-wide and per symbol: see the stored `investigation.md`. rpg-planner (u24) confirmed on #593 (issuecomment-6420602655, relayed by rpg-planner-ubuntu) that none of its local branches touches these files, and rpg-planner-ubuntu gave the go for the deletions that pass.
**Premise corrected: `SocialContractSystem` is live, so it is KEPT.** `ContractService.accept_contract` (contracts.py:177) and `resolve_contract_outcome` (:203) call `SocialContractSystem.transition_contract`, and `accept_contract` is called from `src/domains/cooperation/phase.py:179`; tests import it through its shim. The ticket said only its own file and a comment name it. It is now cited in `social_contracts`' `implemented_by`, with a dated note.
**Deleted (passed all four checks):** `src/systems/world_systems/quest_generator.py` and its shim `src/systems/quest_generator.py` (the live same-name class is `src/quests/generator.py`), `RecruitmentAppraiser` in `social_systems/appraisal.py` (its body only forwarded to `SocialAppraisalSystem._appraise_recruitment`, which stays), `ChestSystem` (`economy_systems/chests.py`, shim `chest_system.py`, and `tests/unit/world/test_chest_lifecycle.py`, 3 tests that exercised only this class). Updated with them: the allowlist line at `tests/architecture/test_legacy_enum_usage_boundaries.py` (a testing-owned path, edited per this ticket's AC and rpg-planner-ubuntu's dispatch), two registry-tool tests that used the chests shim as their example (moved to the live `market` shim), the completeness-check pins (targets 65 to 63, unbound 7 to 5), and one row of `docs/mechanics/resource_conservation_contract.md`. **Code-health ratchet registry (the correction rpg-planner-ubuntu made):** `codebase/baselines/code_health_exceptions.jsonl` validates that each row's file exists (`tests/codebase/test_code_health_ratchet_registry.py`), so the 13 rows for the four deleted files (`chest_system.py` 2, `economy_systems/chests.py` 6, `quest_generator.py` shim 2, `world_systems/quest_generator.py` 3) were removed with the registry's own tool, `python3 -m codebase.health delete FILE TOOL RULE [--symbol S]`; `python3 -m codebase.health validate` is back to 0 problems, and `python3 -m codebase.health check` reports 0 new, 0 worse (4 improved, 3 gone; the `appraisal.py [ruff D102]` row went "gone" because the class was removed, left for `tighten`). `codebase/**` is codebase-planner's and `tests/architecture/**` testing-planner's: listed for the PR's Review notes. `import_layers_baseline.txt` and `package_registry.jsonl` name none of the deleted modules; `make lint-imports` 17 kept, 0 broken; `tests/codebase/test_code_health_ratchet_registry.py` 37, `test_package_registry.py` 32 and `test_import_contracts.py` 34 passed. `mypy_baseline.txt` and `pyrefly_baseline.json` keep entries for the deleted files: both gates report only errors NOT in the baseline (the pyrefly report is advisory), so stale entries are harmless and were not hand-edited.
Not hand-edited: the mutation baseline `tests/mutation/baselines/src_systems_social_appraisal_v1.json` (a dated observation that quotes diffs mentioning the deleted class; nothing regenerates it), and the generated `docs/audits/unreachable_code_inventory.*`.
**Group C, kept, no deletion, no ledger or Bible edit in this PR (ruling by rpg-planner-ubuntu, 2026-10-26; rpg-planner owns the parity and Bible semantics).** Each class has no caller in `src/`, but each is cited as proof or as implementing code by a live-looking claim:
| class (module, shim) | tests that run it | claims that cite it |
|---|---|---|
| `LootSystem` (economy_systems/loot.py, loot_system.py) | tests/unit/resource/test_loot_channeling.py (9 tests); tests/integration/kernel/test_resource_conservation.py (2 loot tests) | parity **TOWN-009** (P0 `verified`, "Looting is a channeled state...", test_path `tests/unit/resource/test_loot_channeling.py`; v2_evidence names the live path `InteractionSystem.enforce`) and **TOWN-076** (P0 `verified`, test_path `...::test_loot_corpse_completion_transfers_all_item_stacks`); `tests/tools/test_parity_index_baseline.py:165` comment; docs/compliance/checklist.md TOWN-009 and TOWN-076 |
| `TownServiceSystem` (economy_systems/town_service.py, town_service.py) | tests/unit/world/test_town_services.py (4 tests) | parity **TOWN-020** (P0 `verified`) cites 2 of them (`test_guild_service_routes_via_interaction_kind`, `test_unrelated_interaction_kind_not_routed`) beside a live test |
| `GuildIntelSystem` (social_systems/guilds.py, guild_system.py) | tests/unit/world/test_guild_intel.py (2 tests) | **Mechanics Bible docs/mechanics/07_social_political_dynamics.md §7 "Guild Intelligence"** names `GuildIntelSystem.update()` as the real mechanism and `social_systems/guilds.py` as its implementing code; parity **TOWN-042** (P0 `verified`, null test_path; the checklist row cites a different test); registry `guilds` notes; `tools/test_architecture/core_rpg_report.py` maps `src.systems.guild_system*` |
| `QuestSystem` (world_systems/quest_engine.py, quest_system.py) | tests/unit/quest/test_quest_system.py (3 tests); tests/integration/kernel/test_resource_conservation.py (1 quest test) | parity **WORLD-116** (P2 `verified`) cites `test_quest_kind_escort_enum_value_is_new_member_only`, an enum test that sits in that file |
| `CraftingSystem` (economy_systems/crafting.py, crafting.py) | tests/unit/quest/test_progression_lifecycle.py (2 crafting tests) | parity **PROG-097 to PROG-101 and PROG-107** (all P0 `verified`, null test_path) and the compliance checklist rows of the same ids, which cite those tests; `docs/mechanics/resource_conservation_contract.md` already says the class is not live; `tools/test_architecture/core_rpg_report.py` maps `src.systems.crafting*` |
**The TOWN-009 and TOWN-076 point, explicitly:** these are P0 `verified` claims about looting, and the test that proves them exercises the dead `LootSystem`, not the live `InteractionSystem.enforce` that their own `v2_evidence` names. The live path's P0 claim is therefore currently unproven by the cited test. Deleting `LootSystem` without first deciding how to re-prove (or re-grade) these claims would erase the only test. Open for rpg-planner (parity and Bible semantics); if it rules before the batch's final SHA the follow-up folds into this PR, otherwise a ticket is filed from this table.
**Completeness check after the deletions** (`python3 -m tools.mechanism_registry.mechanism_registry_completeness_check`): 63 targets, 54 bound, 4 excluded, **5 unbound**: `systems/economy_systems/crafting`, `systems/economy_systems/loot`, `systems/economy_systems/town_service`, `systems/social_systems/guilds`, `systems/world_systems/quest_engine`. `domains/motivation` is bound.
## Test Summary
`tests/unit/tools/test_mechanism_registry_completeness_check.py` 14 passed, `test_mechanism_state_caller_check.py` 11 passed, `tests/architecture/test_legacy_enum_usage_boundaries.py` 6 passed, `tests/unit/social/test_appraisal_logic.py` 15 passed, `tests/refactor/test_import_compatibility.py` 3 passed, `tests/refactor/test_public_facades.py` 3 passed. `make mechanism-registry-validate` passes; html `--check` up to date. Hash neutrality is the batch `paired --neutral` run.

## Files Changed
- Deleted: src/systems/world_systems/quest_generator.py, src/systems/quest_generator.py, src/systems/economy_systems/chests.py, src/systems/chest_system.py, tests/unit/world/test_chest_lifecycle.py
- src/systems/social_systems/appraisal.py (RecruitmentAppraiser removed)
- registries/mechanisms.yaml (SocialContractSystem cited under social_contracts); regenerated docs/brainstorm/mechanism_verification_view.md
- docs/mechanics/resource_conservation_contract.md (one row)
- codebase/baselines/code_health_exceptions.jsonl (13 rows for the deleted files, removed with `codebase.health delete`; a codebase-planner path)
- tests/architecture/test_legacy_enum_usage_boundaries.py (allowlist line), tests/unit/tools/test_mechanism_registry_completeness_check.py, tests/unit/tools/test_mechanism_state_caller_check.py
- agent-working/stored_artifacts/TCK-20261007-DEAD-SYSTEMS-MODULES-WITH-NO-CALLER-BLOCK-THE-MECHANISM-COMPLETENESS-GATE/{plan,investigation,test_plan}.md

## Completion Summary
Three dead symbols deleted (the `quest_generator` twin, `RecruitmentAppraiser`, `ChestSystem`), one ticket premise corrected (`SocialContractSystem` is live and now cited), five modules kept because parity, Bible and compliance claims cite them (group C, awaiting rpg-planner's ruling). The third acceptance criterion is partial: five `src/systems/` modules remain unbound.

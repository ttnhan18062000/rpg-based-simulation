---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261027-FIVE-DEAD-SYSTEMS-CLASSES-STILL-CITED-AS-PROOF
phase: open
date: 2026-10-27
tags: [world, engine, economy]
---

# TCK-20261027-FIVE-DEAD-SYSTEMS-CLASSES-STILL-CITED-AS-PROOF

## Title
Five dead `src/systems/` classes are still the proof or the named implementation of parity, Bible and compliance claims: re-prove each claim on the live path or re-grade it, then delete the class

## Status
INPROGRESS

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Follow-up to `TCK-20261007-DEAD-SYSTEMS-MODULES-WITH-NO-CALLER-BLOCK-THE-MECHANISM-COMPLETENESS-GATE` (PR #757), whose acceptance criterion 3 closed PARTIAL. Five classes have no caller in `src/`, but live-looking claims cite each one as proof or as implementing code, so they were held, not deleted. The full table (tests that run each class, claims that cite it) is in that ticket's Implementation Notes.

rpg-planner (u24) ruled on #593 (the ruling is #757 issuecomment-6426148939, item 3, answering #593 issuecomment-6421250141). That ruling is the authority for this ticket. Summary:

| class (module, shim) | claims | ruling |
|---|---|---|
| `LootSystem` (`economy_systems/loot.py`, `loot_system.py`) | TOWN-009, TOWN-076 (P0 `verified`) | **(a)** re-prove on the live path `InteractionSystem.enforce`, repoint `tests/integration/kernel/test_resource_conservation.py`'s loot use, then delete |
| `TownServiceSystem` (`economy_systems/town_service.py`, `town_service.py`) | TOWN-020 (P0 `verified`) | **(a)**, same terms |
| `GuildIntelSystem` (`social_systems/guilds.py`, `guild_system.py`) | Bible `docs/mechanics/07_social_political_dynamics.md` §7 "Guild Intelligence"; TOWN-042 (P0 `verified`, null test_path) | **(b)** §7 becomes "designed, not in effect, no implementing code" (the parked-`perception` precedent); parity entry `unsupported` with a support boundary; delete. Restoring it later is an Introduce, not a revert |
| `QuestSystem` (`world_systems/quest_engine.py`, `quest_system.py`) | WORLD-116 (P2 `verified`, cites `test_quest_kind_escort_enum_value_is_new_member_only`) | move the enum test out of `tests/unit/quest/test_quest_system.py`, repoint WORLD-116, delete |
| `CraftingSystem` (`economy_systems/crafting.py`, `crafting.py`) | PROG-097..101, PROG-107 (P0 `verified`, null test_path); compliance checklist rows | a **reachability check decides**. If a live crafting path exists: (a), repoint the tests there. If not: (b), entries go `unsupported` with a support boundary and the checklist rows are corrected. Delete either way |

## Scope
1. **First commit, before anything else:** add a `divergence_note` to TOWN-009 and TOWN-076 (through `tools/parity_ledger_writer.py`), reading: "the cited proof exercises the dead LootSystem; live-path proof pending, TCK-20261027-FIVE-DEAD-SYSTEMS-CLASSES-STILL-CITED-AS-PROOF". Add the same kind of interim note to TOWN-020 for `TownServiceSystem`.
2. `LootSystem`: write or repoint tests so that TOWN-009 (looting is a channeled state) and TOWN-076 (corpse loot completion transfers all item stacks) are proven through `InteractionSystem.enforce`. Repoint the loot tests in `tests/integration/kernel/test_resource_conservation.py`. Update both entries' `test_path` and `v2_evidence`, then delete the class, its shim and the tests that exercise only it.
3. `TownServiceSystem`: same as step 2 for TOWN-020. Two of its cited tests (`test_guild_service_routes_via_interaction_kind`, `test_unrelated_interaction_kind_not_routed`) run the dead class.
4. `GuildIntelSystem`: rewrite Bible ch07 §7 as designed, not in effect, no implementing code. **rpg-designer must OK the wording before it lands.** Set TOWN-042 to `unsupported` with a support boundary. Fix the `guilds` mechanism note and `tools/test_architecture/core_rpg_report.py`'s `src.systems.guild_system*` mapping. Then delete the class, its shim and `tests/unit/world/test_guild_intel.py`.
5. `QuestSystem`: move `test_quest_kind_escort_enum_value_is_new_member_only` to a test file that does not depend on the dead class, repoint WORLD-116, repoint or delete the quest test in `test_resource_conservation.py`, then delete the class, its shim and the remaining dead-only tests.
6. `CraftingSystem`: run the four-kind reachability check (import by class name, string registration, `importlib`, phase table) for a live crafting path (`ResourceTransactionResolver`, the `crafting` mechanism). Record the result, apply (a) or (b) as in the table, correct the compliance checklist rows, fix the `core_rpg_report.py` mapping, then delete the class and shim.
7. Bind or exclude each deleted module's target as the completeness check requires. Re-run `python3 -m tools.mechanism_registry.mechanism_registry_completeness_check`: the domains/systems tier must have **0 unbound**.
8. Record each divergence or re-grade in `docs/guidelines/intentional_divergences.md` where the rationale classes require it. Update `docs/compliance/checklist.md` rows that cite deleted tests.

## Out of Scope
- Any behaviour change on a live path. If re-proving a claim on the live path shows the live code does not meet it, record the claim as `divergent` or `unsupported` with a support boundary. Fixing the live code is a separate ticket, so stop and report.
- Wiring any dead class into the simulation.
- `mypy_baseline.txt` and `pyrefly_baseline.json` stale entries (only-new gates; same as the parent ticket).

## Acceptance Criteria
- [ ] The first commit on the branch adds the interim `divergence_note` to TOWN-009 and TOWN-076 (and TOWN-020).
- [ ] TOWN-009, TOWN-076 and TOWN-020 are each either `verified` with a `test_path` that runs the live path, or `unsupported`/`divergent` with a support boundary. None is left `verified` on a test that runs a deleted class.
- [ ] **Deadline:** if the live re-proof of TOWN-009/076 fails, or has not landed when the M1 record ticket is dispatched, those entries go to `unsupported` with a support boundary. Tell lead-planner and rpg-planner (u24) at that point. Until then, the M1 record does not cite them as verified.
- [ ] Bible ch07 §7 is marked designed, not in effect, and rpg-designer's OK on the wording is linked in the ticket. TOWN-042 is `unsupported` with a support boundary.
- [ ] The ESCORT enum test lives in a file that does not import `QuestSystem`, and WORLD-116 cites it there.
- [ ] The CraftingSystem reachability result is recorded with evidence. PROG-097..101 and PROG-107 and their checklist rows match that result.
- [ ] All five classes and their shims are deleted, each after a recorded four-kind reachability check. The completeness check reports 0 unbound in the domains/systems tier.
- [ ] Hash-neutral: `paired --neutral` IDENTICAL on the 3-world corpus. 1000t is accepted for this ticket **only if** no live runtime path changes (rpg-planner's ruling, item 2 and item 3 "Proof"). If any live path changes, 5000t applies.
- [ ] Before any deletion, the u24 branch check is re-run, as in #593 issuecomment-6420602655 (no u24 local branch touches these files).
- [ ] Parity ledger edits go through `tools/parity_ledger_writer.py`, or the diff stays narrow where the writer refuses. Full `tests/unit/tools/` is green, as is the registry/territory/cross-domain view regeneration.

## Related Tickets
- `TCK-20261007-DEAD-SYSTEMS-MODULES-WITH-NO-CALLER-BLOCK-THE-MECHANISM-COMPLETENESS-GATE` (parent; the group C table is in its Implementation Notes)
- `TCK-20261002-EPIC-SEMANTIC-FOUNDATION-COMPLETION` (epic)
- `TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS`

## Related Docs
- `docs/parity_ledger/town_resource.yaml` (TOWN-009, TOWN-020, TOWN-042, TOWN-076), `progression.yaml` (PROG-097..101, PROG-107), `world_dynamics.yaml` (WORLD-116)
- `docs/mechanics/07_social_political_dynamics.md` §7
- `docs/mechanics/resource_conservation_contract.md` (already says CraftingSystem is not live)
- `docs/compliance/checklist.md`
- `docs/guidelines/intentional_divergences.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261007-DEAD-SYSTEMS-MODULES-WITH-NO-CALLER-BLOCK-THE-MECHANISM-COMPLETENESS-GATE/investigation.md` (reachability method and per-symbol results)

## Related Code Areas
`src/systems/economy_systems/{loot,town_service,crafting}.py`, `src/systems/social_systems/guilds.py`, `src/systems/world_systems/quest_engine.py`, the shims `src/systems/{loot_system,town_service,guild_system,quest_system,crafting}.py`, `src/engine/interaction.py` (`InteractionSystem`), `tests/unit/resource/test_loot_channeling.py`, `tests/integration/kernel/test_resource_conservation.py`, `tests/unit/world/test_town_services.py`, `tests/unit/world/test_guild_intel.py`, `tests/unit/quest/test_quest_system.py`, `tests/unit/quest/test_progression_lifecycle.py`, `tools/test_architecture/core_rpg_report.py`, `registries/mechanisms.yaml`

## Assumptions / Open Questions
- Ubuntu U2 stays the sole `mechanisms.yaml` editor for this ticket, under the same rule as batch 1.
- This builds on #757's state (the parent ticket in done/, the deletions already made). Branch from #757's head until it merges, then from `origin/main`.
- The three non-blocking text points from rpg-planner's #757 review ride #757's REGISTRY re-sync push. If they have not landed on main by the time this branch starts, fold them in here.

## Implementation Notes
Done so far (deletions, §7, checklist rows, completeness check and proof still to do):
- Commit 1 (bf6e813ec): interim `divergence_note` on TOWN-009, TOWN-076, TOWN-020, through `parity_ledger_writer`.
- Loot: `tests/unit/resource/test_loot_live_path.py` (6 tests through `AuthoritativeApplyPipeline.refine` and `InteractionSystem.enforce`); the loot cases in `test_resource_conservation.py` now propose channel progress instead of calling `LootSystem`. Positive control: with room in the inventory the repointed tests fail. TOWN-009 and TOWN-076 are `verified` on live tests; TOWN-009's `v2_evidence` cited a non-existent `node.kind == "LOOT"` and was corrected.
- TownService: TOWN-020 stays `verified`, proved by the live inn REST test and a new negative test. `visited_guild_tick` and kind-based service routing existed only in the dead class; recorded in TOWN-020's `divergence_note`. rpg-planner owns the final grading.
- Crafting reachability: `CraftingSystem.craft()` has zero callers; the live path is `ActionIntentAdapter.execute` (REQUEST_CRAFT) then the `ResourceTransactionResolver` CRAFTING branch. Result (a): `tests/integration/economy/test_crafting_live_path.py` (6 tests, each gate positive-controlled). PROG-098..101 and PROG-107 `verified` on it.
- **Known gap, PROG-097 graded `divergent`:** live REQUEST_CRAFT with a recipe id absent from `RecipeRegistry` builds no requirements and then raises `KeyError` at `src/engine/intent/action_intent.py:212` (`RecipeRegistry.get`); the retired class returned `UNKNOWN_RECIPE`. No live producer of such an id was observed (not measured). Live code untouched; no follow-up ticket while the owner's stop direction stands. Goes into the PR's Known gaps.
- Quest: the ESCORT enum test moved to `tests/unit/quest/test_quest_kind.py`; WORLD-116 repointed. The quest full-inventory case in `test_resource_conservation.py` is covered live by `test_transaction_completion.py::test_quest_reward_with_item_rejected_on_full_inventory` and goes with the class.
- GuildIntel: Bible ch07 §7 draft in `agent-working/staging_artifacts/<ticket>/bible_ch07_s7_draft.md`, posted on #593 for rpg-designer; not applied until its OK.


## Test Summary

## Files Changed

## Completion Summary

---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260902-HARVEST-LOOT-TEST-COVERAGE
phase: done
date: 2026-09-02
tags: [testing, economy]
---

# TCK-20260902-HARVEST-LOOT-TEST-COVERAGE

## Title
Close remaining branch-coverage gaps in HarvestSystem/LootSystem dedicated unit tests

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Two M2-batch tickets (`TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION` and
`TCK-20260831-TRUST-GATED-TEACHING`) both flagged, during their independent Test phases, that
`src/systems/world_systems/harvesting.py` (`HarvestSystem`) and
`src/systems/economy_systems/loot.py` (`LootSystem`) have "no dedicated unit test module of their
own, only indirect integration coverage" via `tests/integration/kernel/test_resource_conservation.py`
and `test_resource_conservation_v2.py`. Both flagged it as pre-existing, out-of-scope debt, not
something either ticket introduced, and asked for a follow-up ticket.

**Correction found during this scoping pass**: that premise is only partially accurate. Dedicated
unit test files already exist — `tests/unit/resource/test_harvest_channeling.py` and
`tests/unit/resource/test_loot_channeling.py` (added 2026-05-18, commit `5621168`, well before
both referenced tickets) — and they do directly unit-test `HarvestSystem.update()` /
`LootSystem.update()` (imported via the thin re-export shims `src/systems/harvest_system.py` /
`src/systems/loot_system.py`, which both referenced tickets' Test-phase sweeps also ran against,
per their own `tests/unit/resource/` inclusion note). What both prior Test phases actually missed
is that these files exist; what genuinely remains missing is **specific branch coverage within
them** — several real code paths in `harvesting.py`/`loot.py` are exercised only indirectly (or
not at all) by the existing dedicated tests or by the two integration files. This ticket is
rescoped accordingly: extend the two existing dedicated files with the missing branches, per this
project's no-duplication test policy (`docs/testing/no_duplication_test_policy.md`: "if the
behavior already has an owning file, extend that file rather than creating a new one"), rather than
author a net-new test module.

## Scope
Add test cases to `tests/unit/resource/test_harvest_channeling.py` and
`tests/unit/resource/test_loot_channeling.py` covering the following branches in
`HarvestSystem.update()` (`src/systems/world_systems/harvesting.py`) and `LootSystem.update()`
(`src/systems/economy_systems/loot.py`) that are currently untested at the unit level:

- **`harvesting.py`**:
  - Entity has no `interaction` component, or `interaction.target_node_id is None` → skipped
    (no-op) by the entity loop.
  - Entity's `interaction.kind != "harvest"` → skipped by the entity loop (e.g. an entity mid-loot
    should not be touched by `HarvestSystem`).
  - Entity is interacting with a harvest target whose node is missing or has
    `remaining_charges <= 0` → interaction reset (lines 26-31; currently only the no-interaction
    cooldown-decrement path is tested, not this reset-on-depleted-target path).
  - Entity is too far (`dist > 1.5`) from its harvest target → interaction reset (currently only
    tested for `LootSystem`, not `HarvestSystem`).
  - Node cooldown-decrement branch when the same node already has a pending `node_updates` entry
    in the same tick (the `if current_upd:` merge branch, lines 68-74) — currently only the
    no-existing-update branch (75-79) is exercised.
- **`loot.py`**:
  - Entity has no `interaction` component, or `interaction.target_node_id is None` → skipped.
  - Entity's `interaction.kind` is neither `"ground_item"` nor `"corpse"` → skipped.
  - **Corpse looting is entirely untested** — only `ground_item` looting is covered today. Add a
    completion-path test for `interaction_kind == "corpse"` (`items_add = target.items`,
    `source_kind = "CORPSE"`), including verifying multiple item stacks transfer correctly.
  - Target gone (`ground_items`/`corpses` lookup returns `None`, so `target_pos` stays `None`) →
    interaction reset (lines 35-41).
  - Distance-interruption for the `corpse` variant specifically (currently only `ground_item`
    distance-interruption is tested).

Bonus (only if low-effort once the above tests exist): repair the two P0 parity ledger entries
`TOWN-009` and `TOWN-010` in `docs/parity_ledger/town_resource.yaml`, both `status: verified` but
citing a stale `test_path` (`` `tests_v2/parity/test_resource_interaction_parity.py` ``) that does
not exist anywhere in this repo (the `tests_v2/` tree does not exist; this repo uses `tests/`).
Point `test_path` at the real, passing dedicated test(s) added by this ticket instead. This is a
genuine, separately-discovered gap (per the Mechanics Bible rule that P0 entries require a passing
`test_path`), not required for this ticket's core acceptance criteria — do it only if it doesn't
expand scope meaningfully.

## Out of Scope
- Do not modify the actual behavior of `harvesting.py` or `loot.py` — this is test-only work. If a
  new test reveals a real bug (e.g. an unhandled exception in an untested branch), stop and report
  it rather than silently patching the source file; file a separate ticket for any fix.
- Do not touch `tests/integration/kernel/test_resource_conservation.py` or
  `test_resource_conservation_v2.py` unless a newly-added unit test creates a genuine, verified
  duplicate of an existing integration case (per `no_duplication_test_policy.md`) — trimming, if
  any, should be minimal and justified in Test Summary, not a rewrite.
- Do not create a brand-new test file/module for these two systems — the no-duplication policy
  requires extending the existing owning files (`test_harvest_channeling.py`,
  `test_loot_channeling.py`) instead.
- Do not attempt full parity-ledger reconciliation for the `town_resource.yaml` file beyond the two
  specific stale-`test_path` entries (`TOWN-009`, `TOWN-010`) called out above; `TOWN-073`/`TOWN-074`
  (also P0, also `test_path: null`) are noted as a related-but-separate gap, not in scope here.
- Do not migrate the shim import paths (`src.systems.harvest_system`, `src.systems.loot_system`) to
  the canonical `src.systems.world_systems.harvesting` / `src.systems.economy_systems.loot` paths in
  either existing or new tests — that is an unrelated refactor, out of scope for a coverage-only
  ticket.

## Acceptance Criteria
- [x] `tests/unit/resource/test_harvest_channeling.py` has new test function(s) covering: (a)
      no-interaction/no-target skip, (b) non-"harvest" interaction kind skip, (c) reset-on-missing-
      or-depleted node target, (d) reset-on-distance for harvest, (e) the node-cooldown merge
      branch (existing pending `node_updates` entry in the same tick).
- [x] `tests/unit/resource/test_loot_channeling.py` has new test function(s) covering: (a)
      no-interaction/no-target skip, (b) non-"ground_item"/"corpse" interaction kind skip, (c) a
      full corpse-looting completion path (multi-item-stack `target.items` transfer,
      `source_kind == "CORPSE"`), (d) reset-on-target-gone, (e) distance-interruption for the
      corpse variant.
- [x] All new and existing tests in both files pass:
      `pytest tests/unit/resource/test_harvest_channeling.py tests/unit/resource/test_loot_channeling.py -v`.
- [x] No existing test in `tests/integration/kernel/test_resource_conservation.py` or
      `test_resource_conservation_v2.py` is broken by this change.
- [x] `harvesting.py` and `loot.py` are byte-for-byte unmodified (test-only ticket).
- [ ] If the `TOWN-009`/`TOWN-010` bonus is done: both entries' `test_path` in
      `docs/parity_ledger/town_resource.yaml` cite a real file path that exists in the repo and
      whose named test(s) pass. (Bonus explicitly declined this ticket — see Implementation Notes.)

## Related Tickets
- TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION (done) — flagged this gap during its Test phase
  (see line 340-341 of the ticket body); premise corrected during this scoping pass.
- TCK-20260831-TRUST-GATED-TEACHING (done) — independently re-confirmed the same flagged gap during
  its own Test phase.
- TCK-20260425-PH6-M3-HARVEST (done, per `stored_artifacts/`) — original Harvest V2 implementation
  ticket; likely origin of `test_harvest_channeling.py`.
- TCK-20260425-PH6-M2-LOOT (done, per `stored_artifacts/`) — original Loot V2 implementation
  ticket; likely origin of `test_loot_channeling.py`.
- TCK-20260427-PHASE3-RESOURCE-CONSERVATION (done, per `stored_artifacts/`) — likely origin of the
  `tests/integration/kernel/test_resource_conservation*.py` indirect-coverage files.

## Related Docs
- `docs/testing/no_duplication_test_policy.md` — governs the "extend, don't duplicate" rule this
  ticket's Scope follows.
- `docs/testing/test_taxonomy.md` — `v2_contract` marker convention already used by both existing
  test files (`@pytest.mark.v2_contract`); new tests should follow the same marker.
- `docs/mechanics/03_economic_laws.md` — harvesting/crafting/atomic-conservation laws chapter
  (Mechanics Bible authority for these two systems).
- `docs/parity_ledger/town_resource.yaml` — `TOWN-009` (looting channeled-state law), `TOWN-010`
  (harvesting channeled-state law), `TOWN-073`/`TOWN-074` (hidden discovery / loot recovery,
  related-but-separate `test_path: null` gap, not in scope here).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260425-PH6-M3-HARVEST/` (plan.md, investigation.md)
- `stored_artifacts/TCK-20260425-PH6-M2-LOOT/` (plan.md, investigation.md)
- `stored_artifacts/TCK-20260427-PHASE3-RESOURCE-CONSERVATION/` (plan.md, investigation.md)
- `stored_artifacts/TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION/` (investigation.md, test_plan.md)
  — where the gap was originally flagged.

## Related Code Areas
- `src/systems/world_systems/harvesting.py` (`HarvestSystem.update`) — no behavior change.
- `src/systems/economy_systems/loot.py` (`LootSystem.update`) — no behavior change.
- `src/systems/harvest_system.py`, `src/systems/loot_system.py` — thin re-export shims used as the
  existing tests' import path; kept as-is.
- `tests/unit/resource/test_harvest_channeling.py` — extend.
- `tests/unit/resource/test_loot_channeling.py` — extend.
- `tests/integration/kernel/test_resource_conservation.py`,
  `tests/integration/kernel/test_resource_conservation_v2.py` — read-only reference, do not modify
  unless a genuine duplicate is found.
- `docs/parity_ledger/town_resource.yaml` — only if the bonus `TOWN-009`/`TOWN-010` `test_path`
  repair is done.

## Assumptions / Open Questions
- `layer: testing` was chosen over `layer: economy`/`systems` because the ticket's actual unit of
  work is test authoring/coverage, not a behavior or economy-law change; `testing` is the
  registered layer whose note ("Test infrastructure, fixtures, and testing-strategy tickets/docs")
  matches most directly. `economy` was added as a secondary tag (not layer) since the systems under
  test are economy/harvest subsystems.
- Assumes no hidden behavior exists in the untested branches that would fail once exercised (e.g.
  the corpse-looting completion path, which is structurally symmetric with the tested
  ground-item path but has never actually been run by any existing test). If a new test uncovers a
  real bug, Out of Scope requires stopping and filing a separate ticket rather than silently fixing
  it here — this could invalidate the "test-only, no behavior change" scope if it happens.
  Confidence is moderate-high (the code is straightforward and structurally mirrors the
  ground-item path) but not certain, since it has literally never been executed by any test.
- Assumes the `TOWN-009`/`TOWN-010` stale `test_path` values were never valid in this repo's
  history under the current `tests/` layout (grep found no `tests_v2/` directory anywhere) rather
  than a recent rename that broke a previously-valid path — if that assumption is wrong, the
  correct fix might be restoring/renaming a moved file instead of just repointing the citation,
  which would be a slightly different (but still small) fix.
- Tier is `standard` (not `hotfix`) because the real scope, once corrected, spans ~9-10 net-new
  test functions across two files covering distinct failure/edge modes, plus optional parity-ledger
  repair — judged as substantive rather than a self-evident one-liner, even though it is low-risk
  (test-only, P3).

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260902-HARVEST-LOOT-TEST-COVERAGE/plan.md` Steps 1-7 (Step
8/bonus explicitly declined, per plan.md's own "Bonus Scope Item ... DECLINED" section).

- **Step 1-2 (`test_harvest_channeling.py`)**: added
  `test_harvest_no_interaction_or_no_target_is_skipped`,
  `test_harvest_skips_non_harvest_interaction_kind`, `test_harvest_resets_on_missing_node`,
  `test_harvest_resets_on_depleted_node`, `test_harvest_resets_on_distance`. Plan Step 2 suggested
  either one parametrized function or two functions for the missing/depleted case; two separate
  functions were used (`test_harvest_resets_on_missing_node` /
  `test_harvest_resets_on_depleted_node`) — both names differ from the single suggested name
  `test_harvest_resets_on_missing_or_depleted_node` but the plan explicitly allowed this shape. Same
  pattern applied to loot's Step 6 (see below). Logged in `plan.md`'s Deviations section.
- **Step 3 (dead-code documentation)**: added
  `test_harvest_node_cooldown_merge_branch_is_unreachable`, marked both `@pytest.mark.v2_contract`
  and `@pytest.mark.skip(reason=...)`. The skip reason cites `harvesting.py:69-74` and states the
  reachability finding (node_updates is a call-local dict, keyed 1:1 by node.id via
  `Dict[int, ResourceNodeState]`, so `current_upd` can never be truthy on first encounter within one
  `HarvestSystem.update()` call). Confirmed `pytest -v` shows it as `SKIPPED` with the reason
  visible in output, not silently absent.
  - **Separate tangential finding, not fixed here (flag-don't-chase, matching this session's
    established pattern)**: `harvesting.py:69-74` (the node-cooldown `if current_upd:` merge
    branch) is genuinely unreachable dead code within a single `HarvestSystem.update()` call, as
    verified independently by both the investigation and planning passes and confirmed again during
    implementation. Worth a small future ticket to evaluate simplifying/removing it — not attempted
    here since that would be a behavior change to `harvesting.py`, out of scope for this test-only
    ticket.
- **Step 4-7 (`test_loot_channeling.py`)**: added
  `test_loot_no_interaction_or_no_target_is_skipped`, `test_loot_skips_non_lootable_interaction_kind`,
  `test_loot_corpse_completion_transfers_all_item_stacks` (constructs `CorpseState` inline with two
  distinct `ItemStack` entries, asserts both on the raw `sys_upd` resource_transfer and on the
  post-`refine()`/post-`apply_generation()` state — inventory contents and `corpses_remove`
  membership), `test_loot_resets_on_ground_item_gone`, `test_loot_resets_on_corpse_gone` (two
  functions instead of the plan's single suggested `test_loot_resets_on_target_gone` name, same
  plan-permitted shape as harvesting Step 2), and `test_loot_corpse_interruption_by_distance`
  (mirrors the existing `test_loot_interruption_by_distance` structure with a `CorpseState` target).
- **Step 8 / Bonus (TOWN-009/TOWN-010 parity-ledger `test_path` repair)**: declined, per plan.md's
  own analysis. `docs/parity_ledger/town_resource.yaml` was not touched. Re-verified independently
  during implementation against `src/engine/interaction.py` and `harvesting.py`/`loot.py`'s
  Compliance-ID headers: TOWN-010's cited mechanism (`InteractionSystem.enforce`'s
  `node.required_ticks` check) is materially different from `harvesting.py`'s own completion check
  (`entity.identity.properties.get("harvest_duration", 10.0)`), so repointing `test_path` to this
  ticket's new `HarvestSystem` tests would misattribute evidence. TOWN-009 is only partially covered
  by `LootSystem`-only unit tests (the ledger text also depends on `InteractionSystem.enforce`'s
  interruption/capacity logic, untouched by this ticket's tests). Recommend a separate future ticket
  scoped to properly resolving both entries (either new `InteractionSystem.enforce`-targeted tests
  or a ledger text/evidence revision).
- No source-file changes: `src/systems/world_systems/harvesting.py` and
  `src/systems/economy_systems/loot.py` remain byte-for-byte unmodified (`git diff --stat` on both
  shows no output).
- No integration-test trimming was needed or performed:
  `tests/integration/kernel/test_resource_conservation.py` and `test_resource_conservation_v2.py`
  were left untouched, confirmed still passing.

## Test Summary

`pytest tests/unit/resource/test_harvest_channeling.py tests/unit/resource/test_loot_channeling.py -v`
— 15 passed, 1 skipped (the documented-unreachable-branch test), 0 failed.

`pytest tests/integration/kernel/test_resource_conservation.py tests/integration/kernel/test_resource_conservation_v2.py -v`
— 6 passed, 0 failed (no regression from this ticket's additions).

`git diff --stat src/systems/world_systems/harvesting.py src/systems/economy_systems/loot.py`
— no output (byte-for-byte unmodified, confirmed).

## Files Changed
- `tests/unit/resource/test_harvest_channeling.py` — added 6 new test functions (5 passing, 1
  skip-documented) covering entity-loop skip branches, reset-on-missing/depleted-node,
  reset-on-distance, and the node-cooldown merge-branch dead-code finding.
- `tests/unit/resource/test_loot_channeling.py` — added 6 new test functions covering entity-loop
  skip branches, the corpse-completion headline gap, reset-on-target-gone (both ground_item and
  corpse variants), and corpse distance-interruption.
- `staging_artifacts/TCK-20260902-HARVEST-LOOT-TEST-COVERAGE/investigation.md` — created during this
  run's Investigate phase.
- `staging_artifacts/TCK-20260902-HARVEST-LOOT-TEST-COVERAGE/plan.md` — created during this run's
  Plan phase; Deviations section added during Implement (see below).
- `staging_artifacts/TCK-20260902-HARVEST-LOOT-TEST-COVERAGE/test_plan.md` — created during this
  run's Investigate/Plan phase.
- `tickets/inprogress/TCK-20260902-HARVEST-LOOT-TEST-COVERAGE.md` — this file (Implementation Notes,
  Test Summary, Files Changed, Completion Summary, Acceptance Criteria, Status).

No changes to `src/systems/world_systems/harvesting.py`, `src/systems/economy_systems/loot.py`, or
`docs/parity_ledger/town_resource.yaml`.

## Completion Summary

Extended the two existing dedicated unit test files for `HarvestSystem`/`LootSystem`
(`tests/unit/resource/test_harvest_channeling.py`, `tests/unit/resource/test_loot_channeling.py`)
with 12 new test functions closing the branch-coverage gaps identified in the investigation: entity-
loop skip branches, reset-on-missing/depleted-target and reset-on-distance for both systems, the
corpse-looting completion path (previously entirely untested at the unit level), reset-on-target-gone
and distance-interruption for the corpse variant, and one `@pytest.mark.skip`-documented test proving
the `harvesting.py` node-cooldown merge branch is unreachable dead code rather than silently omitting
it. No source file (`harvesting.py`, `loot.py`) was modified, and the optional TOWN-009/TOWN-010
parity-ledger bonus repair was explicitly declined with cited evidence. All 15 active tests pass (1
correctly skipped), and both integration conservation test files remain green with no regression.


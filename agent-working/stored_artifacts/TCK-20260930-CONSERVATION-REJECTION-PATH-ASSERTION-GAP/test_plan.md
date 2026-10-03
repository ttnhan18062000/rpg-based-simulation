---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP
artifact_type: test_plan
tags: [testing, economy, resource]
---

# Test Plan — TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP

Tests only; `src/` unchanged. This is a coverage gap, not a live defect.

## Regression Surface

Unit:
- `tests/unit/resource/test_resource_conservation_regression.py`
- `tests/unit/resource/test_transaction_grouping.py`
- `tests/unit/resource/test_node_charge_accounting.py`
- `tests/unit/resource/test_resource_conflicts.py` (existing TARGET_LOCKED end-to-end, line 76)
- `tests/unit/resource/test_durability_repair.py`
- `tests/unit/economy/test_gold_sink.py`
- `tests/unit/quest/test_quest_rewards.py`
- `tests/unit/combat/test_combat_matrix.py`, `tests/unit/content/test_resolvers.py`, `tests/unit/domains/adventure/test_craft_upgrade_execution.py`
- `tests/unit/tools/test_mutation_baseline_records.py` and `tests/unit/tools/test_core_rpg_report.py` (read `tests/mutation/baselines/*.json` only; the re-run record lives in `tests/mutation/reruns/` and must not be picked up by either)
Integration:
- `tests/integration/pipeline/test_transaction_completion.py`
- `tests/integration/domains/adventure/test_harvest_to_event.py`
- `tests/integration/kernel/test_phase10_replay.py` (determinism)
- `tests/integration/kernel/test_race_conditions_v2.py` (existing TARGET_LOCKED end-to-end, lines 89 and 113)
Arena-combat: none affected.

## New Tests Required

New file `tests/unit/resource/test_conservation_rejection_paths.py` (resolver level), plus
`tests/unit/resource/test_rejected_transfer_apply_path.py` (apply path). Identifiers carry no ticket or phase labels.

1. `test_resolver_rejection_table` — unit. One explicit case id per rejection path in the investigation table (29 returns: `:59`; `:74/77/89`;
   `:101/104/108`; `:118/121/125`; `:136/139/144`; `:158/162/169/174`; `:198/201/206`; `:228`; `:240/244`; `:257`; `:277/280`; `:309/314/320`; `:334`).
   Asserts `result.accepted is False`, exact `result.reason`, and no update fields set. This kills all 22 flag-flip survivors (owner decision 1).
2. `test_target_locked_per_source_kind` — unit. TARGET_LOCKED for GROUND_ITEM, CORPSE, QUEST, RECRUIT, CHEST via direct
   `resolve(..., reservations={(kind, id): 1})`, with negative controls (reservation absent / `0` / empty dict -> accepted) and a different-kind key not locking.
   Resolver level per owner decision 2. Docstring records that **no building reservation guard exists**; no building test is written.
3. `test_resolver_source_kind_coverage_guard` — architecture guard. Fails if a source kind handled by `resolve()` is missing from the table; a new kind
   must fail loudly, never be skipped.
4. `test_idempotency_violation_resolver_level` — unit. id in `state.processed_transaction_ids` -> `accepted is False`, IDEMPOTENCY_VIOLATION (kills `:59`).
5. `test_rejected_transfer_does_not_burn_transaction_id` — integration (apply path). Via `AuthoritativeApplyPipeline.refine` + `ApplyPath.apply_generation`:
   two entities, same tick, same GROUND_ITEM (and CORPSE), distinct transaction ids; loser gets TARGET_LOCKED; loser id absent from the refined and
   post-apply `processed_transaction_ids`, winner id present; a later-tick retry of the loser id is not IDEMPOTENCY_VIOLATION. Plus one non-reservation
   rejection (INVENTORY_FULL) with the same assertions. (AC-2)
6. `test_rejected_transfer_zero_durable_change` — architecture test. Pre/post state compare: inventories (items, gold), node charges, ground items,
   corpses, building/home-storage inventory, `processed_transaction_ids`; refined removals and node updates empty. (AC-3)
7. `test_grouped_rejection_rolls_back_without_burning_ids` — integration. Group where a later intent rejects: no inventory delta, no ids in the processed list.
8. Mutation re-run record (not a pytest test): `tests/mutation/reruns/src_core_conservation_rerun.json`, see Proof Plan AC6.

## Proof Plan

| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| AC1 | unit | regression / mutation-kill | `docs/mechanics/resource_conservation_contract.md` failure-code table + `docs/mechanics/03_economic_laws.md` section 1; parity TOWN-103 / TOWN-011 | every rejection path returns `accepted is False` and the exact ReasonCode | `pytest tests/unit/resource/test_conservation_rejection_paths.py -q` |
| AC2 | integration | invariant | `docs/engine/authoritative_mutation_pipeline_contract.md`, `docs/core/state.md`; parity TOWN-014 | rejected id absent from durable `processed_transaction_ids`; retry not IDEMPOTENCY_VIOLATION | `pytest tests/unit/resource/test_rejected_transfer_apply_path.py -q` |
| AC3 | integration | architecture guard | `resource_conservation_contract.md` ("world state is unchanged" on rejection); parity TOWN-014 | zero delta across inventory, node charges, ground items, corpses, processed ids | `pytest tests/unit/resource/test_rejected_transfer_apply_path.py -q -k zero_durable` |
| AC4 | unit (resolver level for QUEST/RECRUIT/CHEST; also apply-path for GROUND_ITEM/CORPSE via AC2 tests) | regression | `resource_conservation_contract.md` Concurrent Actor Protection; parity TOWN-121/123 | TARGET_LOCKED for GROUND_ITEM, CORPSE, QUEST, RECRUIT, CHEST; "building: no such guard exists" recorded, not tested | `pytest tests/unit/resource/test_conservation_rejection_paths.py -q -k target_locked` |
| AC5 | n/a | scope guard | ticket Out of Scope | `git diff --stat origin/main -- src/` is empty | `git diff --stat origin/main -- src/` |
| AC6 | tooling | mutation measurement with positive control | baseline `tests/mutation/baselines/src_core_conservation.json` (177/60/117); owner decisions 1 and 5; parity: none | Pass 1 (baseline selection only, 8 files) reproduces 177/60/117 with mutmut 2.5.1, else stop-and-report. Pass 2 (8 files + 2 new files) records after-counts and each of the 22 flag-flip ids killed or alive; `:82-91` kills excluded; record states selections differ, names the existing TARGET_LOCKED end-to-end tests outside the selection, states the core-RPG report cannot see it and the baseline is not refreshed (stale 2026-10-30). If mutmut 2.5.1 cannot run: AC-6 stop-and-report, no substitute | mutmut 2.5.1 in scratch copy (see below) |
| AC7 | n/a | review | ticket AC-7 | no artifact claims a live defect | grep new tests/records/docs for wording implying a live defect |

Negative cases: reservation absent -> accepted; `0` reservation; empty reservations dict; sufficient gold/stock control per kind.
Fixtures: `make_actor` pattern from `test_resource_conservation_regression.py`; `_entity`/state pattern from `test_gold_sink.py`; `_make_state`/`_make_intent` from `test_quest_rewards.py`; two-actor shape from `test_resource_conflicts.py`.
Non-functional risk: mutmut run ~6 min (baseline 341 s) in a scratch copy at a real path, not `/tmp`, not in the repo.

AC6 record requirements (decided, owner decision 5): file `tests/mutation/reruns/src_core_conservation_rerun.json` (outside the baselines glob). Contents: exact mutmut 2.5.1 command for each pass; version; full test file list and count per pass (pass 2 = baseline's 8 files + `tests/unit/resource/test_conservation_rejection_paths.py` + `tests/unit/resource/test_rejected_transfer_apply_path.py`); source commit sha and target sha256; runtime; statement that before and after test sets differ; before counts 177 / 60 / 117 and the positive-control result; after counts; the 22 flag-flip ids (22, 32, 54, 57, 63, 67, 76, 80, 82, 86, 91, 96, 100, 111, 113, 117, 132, 153, 155, 169, 171, 175) each killed or alive, `:82-91` kills (PR #265) excluded; the three existing TARGET_LOCKED end-to-end assertions named as outside the selection (`tests/unit/resource/test_resource_conflicts.py:76`, `tests/integration/kernel/test_race_conditions_v2.py:89,113`); statement that the core-RPG report reads only `baselines/*.json` and cannot see this record; statement that the baseline is not refreshed and goes stale 2026-10-30; `equivalent: not-classified`; no kill-rate claim and no wording implying a live defect. The baseline JSON is not rewritten.

## Scoped Pytest Commands

```
export PATH=/home/u24desktop/Working/rpg-based-simulation/.venv/bin:$PATH
pytest tests/unit/resource tests/unit/economy/test_gold_sink.py tests/unit/quest/test_quest_rewards.py tests/integration/pipeline/test_transaction_completion.py tests/integration/kernel/test_phase10_replay.py tests/integration/kernel/test_race_conditions_v2.py -q
pytest tests/unit/tools/test_mutation_baseline_records.py tests/unit/tools/test_core_rpg_report.py -q
git diff --stat origin/main -- src/
```
Mutation re-run (scratch copy at a real path, mutmut 2.5.1 private install), two passes, in this order:
1. Positive control: `mutmut run --paths-to-mutate src/core/conservation.py --runner "python -m pytest -x -q <baseline 8 files>"` must give 177 / 60 / 117; otherwise stop-and-report.
2. Delta: same command with the baseline 8 files + the 2 new files.
The test phase records the actual command it used. Never `pytest tests/`.

## Anti-Drift Test Guards

- Coverage-guard test (item 3) fails on any new source kind lacking a rejection case.
- `git diff --stat origin/main -- src/` must be empty.
- `tests/integration/kernel/test_phase10_replay.py` confirms determinism is unaffected.
- `tests/unit/tools/test_mutation_baseline_records.py` and `tests/unit/tools/test_core_rpg_report.py` must keep passing; the re-run record lives outside the baselines glob.
- Positive-control pass must reproduce 177/60/117 before any delta is reported.
- Verify the new tests would fail on a real regression: locally flip one `accepted=False` in a scratch copy (never in the repo) and confirm a failure.

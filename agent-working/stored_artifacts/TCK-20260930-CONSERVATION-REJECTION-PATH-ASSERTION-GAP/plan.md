---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP
artifact_type: plan
tags: [testing, economy, resource]
---

# Implementation Plan — TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP

## Summary

Test-coverage gap, not a live defect: `src/` is unchanged and nothing in any artifact may say otherwise (AC-7). The plan adds two new test files (resolver level; apply-path level), then measures them with a two-pass mutmut 2.5.1 re-run (positive control first, then delta) recorded in a new file outside the baselines glob, then makes the authorized prose-only doc fix. All five owner decisions of 2026-10-01 are applied as settled; none is reopened.

Facts verified by reading source in this planning run:
- `ResourceTransactionResolver.resolve()` source kinds are plain string literals, not an enum (`src/core/conservation.py:72,99,116,133,155,192,224,237,255,274,297`; no `SourceKind` enum exists in `src/core`). The coverage guard (Step 1) therefore must derive the handled-kind set from the source text (AST scan of `resolve()` for string constants compared to `intent.source_kind`), not import an enum.
- `economy.py:89` in-tick idempotency check; `:103` `if result.accepted:`; `:142` id add inside the accepted block; `:324/:346/:350` reservations populated for NODE, GROUND_ITEM, CORPSE only (`:346`/`:350` set `= 1`).
- `docs/mechanics/resource_conservation_contract.md:226` is the reservation sentence naming "NODE, GROUND_ITEM, CORPSE, QUEST, CHEST, or RECRUIT"; its Regression Tests table (`:282-289`) cites `tests_v2/...` paths.
- Baseline `tests/mutation/baselines/src_core_conservation.json`: `tests.files` = 8 files, `tests.count` = 165, tool mutmut 2.5.1, counts 177/60/117, `target.sha256` prefix `bb5484ebbed8`.
- Only `tests/unit/tools/test_mutation_baseline_records.py` / `test_core_rpg_report.py` read `tests/mutation/baselines/*.json` (per investigation); `tests/mutation/reruns/` is outside that glob. No test or tool under `tests/` or `tools/` references `resource_conservation_contract.md` (grep this run), so the prose edit is not pinned by a test.

## Steps

### Step 1 — Resolver-level rejection table, idempotency case, and coverage guard
**Files:** new `tests/unit/resource/test_conservation_rejection_paths.py`.
**Change:** Add `test_resolver_rejection_table` (explicit case ids, one per rejection return: `:59`; `:74/77/89`; `:101/104/108`; `:118/121/125`; `:136/139/144`; `:158/162/169/174`; `:198/201/206`; `:228`; `:240/244`; `:257`; `:277/280`; `:309/314/320`; `:334` = 29 cases). Each calls `ResourceTransactionResolver.resolve()` directly and asserts `result.accepted is False`, exact `result.reason` (a `ReasonCode` member, `src/core/enums.py:66`), and no update fields set (inventory/node/ground_item_remove/corpse_remove/building/home_storage updates empty). Add `test_idempotency_violation_resolver_level` (id in `state.processed_transaction_ids` -> `accepted is False`, `IDEMPOTENCY_VIOLATION`; this is the only way to reach `:59`, because `economy.py:89` pre-empts it on the apply path). Add `test_resolver_source_kind_coverage_guard`: AST-scan `resolve()` in `src/core/conservation.py` (read-only) for string constants compared to `intent.source_kind`, and fail loudly if any kind is absent from the table (including the unknown-kind `:334` case). Fixture patterns: `make_actor` from `test_resource_conservation_regression.py`; `_entity`/state from `test_gold_sink.py`; `_make_state`/`_make_intent` from `test_quest_rewards.py`. Identifiers carry no ticket or phase labels. Docstrings state "coverage gap, not a live defect". No other writer exists for this new file.
**Do NOT touch:** `src/`; existing test files; no `not accepted`-only assertions; do not parametrize over a list that silently skips new kinds.
**Verify:** `pytest tests/unit/resource/test_conservation_rejection_paths.py -q`.

### Step 2 — TARGET_LOCKED per source kind (resolver level)
**Files:** same file `tests/unit/resource/test_conservation_rejection_paths.py`.
**Change:** Add `test_target_locked_per_source_kind`: GROUND_ITEM (`:108`), CORPSE (`:125`), QUEST (`:240`), RECRUIT and CHEST (`:277`) via direct `resolve(..., reservations={(kind, id): 1})` asserting `accepted is False` and `ReasonCode.TARGET_LOCKED`. Negative controls: reservation absent, value `0`, empty dict -> accepted; a reservation keyed by a different kind (or different id) does not lock. Docstring records: "building: no such reservation guard exists in `resolve()`; no building test is written and no `src/` guard is added" (owner decision 2; `economy.py` only populates NODE/GROUND_ITEM/CORPSE at `:324/:346/:350`). Owner decision 2 applies to QUEST/RECRUIT/CHEST: hand-built dict only.
**Do NOT touch:** no building test; no `src/` guard; do not add NODE reservation cases beyond what Step 1's table requires (NODE lock is charge accounting at `:82-91`, killed by PR #265 tests).
**Verify:** `pytest tests/unit/resource/test_conservation_rejection_paths.py -q -k target_locked`.

### Step 3 — Rejected transfer does not burn the transaction id (apply path)
**Files:** new `tests/unit/resource/test_rejected_transfer_apply_path.py`.
**Change:** Add `test_rejected_transfer_does_not_burn_transaction_id`. Drive via `AuthoritativeApplyPipeline.refine` then `ApplyPath.apply_generation` (read the exact signatures from `src/engine/economy.py` / `src/engine/apply.py` and the two-actor shape in `tests/unit/resource/test_resource_conflicts.py` before writing). Two entities, same tick, same GROUND_ITEM (and a second case for CORPSE), distinct transaction ids; loser gets `TARGET_LOCKED`; assert loser id absent from the refined update's `processed_transaction_ids` (`economy.py:289`) and from post-apply `AuthoritativeState.processed_transaction_ids` (`apply.py:307-308,487`), winner id present; a later-tick retry of the loser id is not `IDEMPOTENCY_VIOLATION`. Add one non-reservation rejection (INVENTORY_FULL) with identical assertions. Writers to `processed_transaction_ids`, all production and read-only to this test: `economy.py:142` and `:229` (add), `:289` (union into the update), `apply.py:307-308` (extend into durable state); the test only observes outputs and never writes the field, so there is no ordering or double-count interaction.
**Do NOT touch:** `src/engine/economy.py`, `src/engine/apply.py`; do not modify `test_resource_conflicts.py` / `test_race_conditions_v2.py` (existing coverage, outside the mutation selection by decision). If the test cannot pass without a production change, STOP and report.
**Verify:** `pytest tests/unit/resource/test_rejected_transfer_apply_path.py -q -k burn`.

### Step 4 — Rejected transfer causes zero durable change (architecture test)
**Files:** `tests/unit/resource/test_rejected_transfer_apply_path.py`.
**Change:** Add `test_rejected_transfer_zero_durable_change`: pre/post state compare over entity inventories (items, gold), node charges, ground items, corpses, building and home-storage inventories, and `processed_transaction_ids`; assert refined removals and node updates are empty. Use the GROUND_ITEM/CORPSE lock loser and the INVENTORY_FULL case from Step 3 (reuse a shared helper in the file).
**Do NOT touch:** production state-comparison helpers; do not add snapshot helpers under `src/`.
**Verify:** `pytest tests/unit/resource/test_rejected_transfer_apply_path.py -q -k zero_durable`.

### Step 5 — Grouped rejection rolls back without burning ids
**Files:** `tests/unit/resource/test_rejected_transfer_apply_path.py`.
**Change:** Add `test_grouped_rejection_rolls_back_without_burning_ids`: a transaction group where a later intent rejects; assert no inventory delta and no group ids in the processed list (grouped path adds ids at `economy.py:229` only on full acceptance; read `economy.py` grouped block before writing).
**Do NOT touch:** `src/engine/economy.py`; transaction-grouping tests.
**Verify:** `pytest tests/unit/resource/test_rejected_transfer_apply_path.py -q -k grouped`.

### Step 6 — Scoped regression and scope-guard run
**Files:** none changed.
**Change:** Run the scoped commands from `test_plan.md` (never `pytest tests/`): `pytest tests/unit/resource tests/unit/economy/test_gold_sink.py tests/unit/quest/test_quest_rewards.py tests/integration/pipeline/test_transaction_completion.py tests/integration/kernel/test_phase10_replay.py tests/integration/kernel/test_race_conditions_v2.py -q`; `pytest tests/unit/tools/test_mutation_baseline_records.py tests/unit/tools/test_core_rpg_report.py -q`; `git diff --stat origin/main -- src/` (must be empty; use `origin/main`, never local `main`). Also run a throwaway real-regression check in a scratch copy only: flip one `accepted=False` to `True` and confirm a new test fails.
**Do NOT touch:** the repo's `src/` for the flip check; scratch copy only (a real path, not `/tmp`, not in the repo).
**Verify:** all green; src diff empty.

### Step 7 — Mutation pass 1: baseline selection only (positive control)
**Files:** none in the repo; scratch copy at a real path with mutmut 2.5.1 in a private `pip --target` install (not a project dependency; never mutmut 3.x).
**Change:** Confirm `sha256(src/core/conservation.py)` prefix `bb5484ebbed8` in the scratch copy. Run `mutmut run --paths-to-mutate src/core/conservation.py --runner "python -m pytest -x -q <the baseline's 8 files>"`. Must reproduce 177 / 60 / 117. If mutmut 2.5.1 cannot run (owner decision 4) or counts differ (decision 5): STOP and report; no substitute measurement (no hand mutation, no AST flipper, no 3.x), and do not report any delta. Note runtime (~341 s baseline). Scratch-copy mutmut cache is a private writer; it does not touch the repo's `.mutmut-cache` (confirm none is tracked in the repo).
**Do NOT touch:** the baseline JSON; project dependencies; the repo's `src/`.
**Verify:** pass-1 counts equal 177 / 60 / 117.

### Step 8 — Mutation pass 2 (delta) and the re-run record
**Files:** new `tests/mutation/reruns/src_core_conservation_rerun.json` (new directory).
**Change:** Fresh scratch copy (or cleared mutmut cache) with the new tests present; same command as pass 1 with the 8 baseline files plus `tests/unit/resource/test_conservation_rejection_paths.py` and `tests/unit/resource/test_rejected_transfer_apply_path.py`. Do NOT add `tests/unit/resource/test_resource_conflicts.py` or `tests/integration/kernel/test_race_conditions_v2.py`. Write the record with: exact command for each pass; mutmut version 2.5.1; full test file list and count per pass; source commit sha and target sha256; runtime per pass; before counts 177/60/117 and the positive-control result; after counts; a statement that the before and after test sets differ; each of the 22 flag-flip ids (22, 32, 54, 57, 63, 67, 76, 80, 82, 86, 91, 96, 100, 111, 113, 117, 132, 153, 155, 169, 171, 175) marked killed or alive, with the `:82-91` kills (PR #265, `test_node_charge_accounting.py`) excluded from this ticket's delta and not re-counted as survivors (ids 82, 86, 91 are in the 22 list at lines 82-91: record them under the exclusion note, do not credit them to this ticket and do not count them as survivors); the three existing TARGET_LOCKED end-to-end assertions named as outside the selection (`tests/unit/resource/test_resource_conflicts.py:76`, `tests/integration/kernel/test_race_conditions_v2.py:89,113`); statement that the core-RPG report's mutation layer reads only `baselines/*.json` and cannot see this record; statement that the baseline is not refreshed and goes stale on 2026-10-30; `"equivalent": "not-classified"`; no kill-rate claim; no wording implying a live defect. Any of the 22 still alive is reported honestly as alive (do not edit tests or the record to pass; if any remain alive, add a targeted test in Steps 1-2 and re-run, or report). Writers to `tests/mutation/`: the baseline writer (PR #259, historical) writes only `baselines/`; this step writes only `reruns/`; `test_mutation_baseline_records.py` and `test_core_rpg_report.py` glob `baselines/*.json`, so no collision. Re-run Step 6's second pytest command afterwards to confirm both still pass.
**Do NOT touch:** `tests/mutation/baselines/src_core_conservation.json`; the mutation readers/report tools.
**Verify:** record JSON parses; 22 ids each carry killed/alive; `pytest tests/unit/tools/test_mutation_baseline_records.py tests/unit/tools/test_core_rpg_report.py -q` green.

### Step 9 — Prose-only doc fix (owner decision 3)
**Files:** `docs/mechanics/resource_conservation_contract.md`.
**Change:** (a) At `:226` correct the reservation sentence: the resolver honours reservations for GROUND_ITEM, CORPSE, QUEST, RECRUIT and CHEST (NODE's lock is charge accounting, `conservation.py:82-91`); the apply path populates reservations only for NODE, GROUND_ITEM and CORPSE (`economy.py:324,346,350`); no building reservation guard exists. (b) In the Regression Tests table (`:282-289`) replace the non-existent `tests_v2/...` paths with real paths verified to exist (including the two new test files and `test_resource_conflicts.py`, `test_race_conditions_v2.py`); verify each cited path with `ls` before writing. Other writers to this doc: parity-ledger entries cite it by reference (`docs/parity_ledger/town_resource.yaml` TOWN-121..125) but do not write it. Update the frontmatter/date only if the repo's doc conventions require it. If any docs file is modified, run `make knowledge-index-update` at close. Parity-ledger `test_path`/`v2_evidence` enrichment of TOWN-014/103/121/123 is conditional and left to the parity-updater; no status change is forced (TOWN-011/012 unchanged).
**Do NOT touch:** `docs/mechanics/03_economic_laws.md`, `docs/guidelines/intentional_divergences.md` (no divergence; doc-only fix of existing behaviour), `docs/core/state.md`, `docs/engine/*`, any `src/` file.
**Verify:** `git diff` of the doc is prose-only; every cited test path exists; wording claims no live defect.

### Step 10 — Final guard sweep
**Files:** none changed.
**Change:** Re-run `git diff --stat origin/main -- src/` (empty), grep new tests/record/doc for wording implying a live defect (AC-7), confirm no ticket/phase labels in new test identifiers, confirm no stray scratch/mutmut artifacts in the repo (`git status`).
**Verify:** all clean.

## Unresolved Questions

None. All five owner decisions are settled and applied. (The investigation lists no open questions; the choice between explicit cases vs parametrisation is resolved in Step 1 by an explicit case table plus a coverage guard.)

## Scope Guards

- No edit under `src/` (AC-5); any test that needs one means stop and report.
- The other 110 survivors, equivalent-mutant classification, kill-rate targets: out of scope.
- `src/core/inventory.py` untouched (owned by `TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS`); mutmut not added as a dependency.
- No building reservation test or `src/` guard; record "no such guard exists" only.
- Baseline JSON not rewritten or refreshed; record lives only in `tests/mutation/reruns/`.
- Existing TARGET_LOCKED end-to-end tests not added to the mutation selection and not edited.
- No substitute measurement if mutmut 2.5.1 cannot run; no delta reported before the positive control reproduces 177/60/117.
- No ticket IDs or phase labels in test identifiers.

## Dependency Map

- Steps 1-2 (one file) are independent of 3-5 (second file); 4 and 5 reuse helpers from 3.
- Step 6 depends on 1-5. Step 7 is independent of code steps but must precede 8. Step 8 depends on 1-5 and 7.
- Step 9 depends on 1-5 (cites the new test paths); independent of 7-8. Step 10 last.

## Acceptance Criteria Map

| AC | Implemented by step(s) | Verified by test |
|---|---|---|
| AC-1 every rejection path, `accepted is False` + exact ReasonCode | 1, 2 | `pytest tests/unit/resource/test_conservation_rejection_paths.py -q` |
| AC-2 rejected id absent from `processed_transaction_ids` after apply | 3 | `test_rejected_transfer_does_not_burn_transaction_id` |
| AC-3 zero durable change | 4, 5 | `test_rejected_transfer_zero_durable_change`, `test_grouped_rejection_rolls_back_without_burning_ids` |
| AC-4 TARGET_LOCKED per kind (GROUND_ITEM, CORPSE apply-path; QUEST/RECRUIT/CHEST resolver-level; building recorded as no guard) | 2, 3, 9 | `-k target_locked`, Step 3 test |
| AC-5 `src/` unchanged | 6, 10 | `git diff --stat origin/main -- src/` empty |
| AC-6 re-run recorded; 22 flag-flip ids named killed/alive; `:82-91` excluded | 7, 8 | positive control 177/60/117; `src_core_conservation_rerun.json` |
| AC-7 no live-defect claim | 1-2 docstrings, 8, 9, 10 | grep sweep in Step 10 |

AC wording cross-check: ticket AC-6 says "seven named survivors" and a record in `baselines/` "or a sibling record"; owner decisions 1 and 5 supersede with the 22 ids and `tests/mutation/reruns/`. The plan follows the owner decisions.

## Anti-Drift Notes

- Production is correct on every path; wording must say "coverage gap".
- `economy.py:89` pre-empts resolver idempotency on the apply path; `:59` is killable only by a direct resolver call (Step 1).
- QUEST/RECRUIT/CHEST locks are unreachable end to end (reservations populated only for NODE/GROUND_ITEM/CORPSE); resolver-level only.
- Baseline survivor ids 45-49 (line 91) predate PR #265; compute the delta excluding `:82-91`.
- Verify scope guards against `origin/main`, never local `main`.
- Side-effect observation only: reservation-condition mutants at `:104-125` may also die; report as an observation, not a requirement.
- Mutmut 3.x rejects `src.` import paths; use 2.5.1 in a scratch copy at a real path.

## Deviations

- Step 8: the plan said mutant ids 82, 86 and 91 fall under the `:82-91` exclusion. Those are mutmut mutant ids on source lines 139, 144 and 158 (CRAFTING and SHOP_BUY flag-flips), not source lines 82-91. No flip mutant lies on lines 82-91. The three are killed in pass 2 and credited to this change; the real `:82-91` mutants (12 survivors in both passes) are excluded and unchanged. Recorded in `id_vs_line_note` of the re-run record.
- Step 1: the rejection table has 38 cases rather than 29 (the shared service-fee kinds, RECRUIT and CHEST, and building missing / not functional are separate cases); the coverage guard is as planned.
- Step 9: the Regression Tests table also cites `test_node_charge_accounting.py`, `test_transaction_grouping.py`, `test_resource_v2_boundary.py`, `test_domain_8_economy.py`, `test_economy_hardening.py` and `test_equipment_chests_storage.py`, each verified to exist; `last_verified` was bumped to 2026-10-01.
- Step 10 and mutation passes: pass 1 reproduced 177 / 60 / 117; pass 2 gave 177 / 143 / 34.


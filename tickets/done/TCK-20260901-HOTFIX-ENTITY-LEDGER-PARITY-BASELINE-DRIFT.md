---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260901-HOTFIX-ENTITY-LEDGER-PARITY-BASELINE-DRIFT
phase: done
date: 2026-09-01
tags: [testing]
---

# TCK-20260901-HOTFIX-ENTITY-LEDGER-PARITY-BASELINE-DRIFT

## Title
Fix real "API / tools / logging" CI regression on PR #101: stale entity event ledger + stale parity-index baseline count

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
PR #101 (branch `m2-foundational-systems-implementation`) fails the "API / tools / logging" GitHub Actions job after the `TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION` and `TCK-20260831-TRUST-GATED-TEACHING` commits landed. Confirmed as a genuine regression (not environment noise) via job-level comparison against `main`'s own latest green run of the same job, and root-caused via local reproduction of the exact CI command (`pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m "not slow and not extra_slow"`) to exactly 2 real, non-environment-dependent failures. (24 other local failures are confirmed sandbox-only noise — live-server/subprocess tests that pass fine in real CI per `main`'s own green run of this job — and are explicitly out of scope.)

1. `tests/tools/test_entity_event_ledger.py::test_entity_ledger_covers_every_entity_update_field` fails with `AssertionError: EntityUpdate fields with no ledger entry: {'status_effect_update'}`. This is a staleness guard (per `TCK-20260808-ENTITY-EVENT-LEDGER`) that enumerates every `dataclasses.fields(EntityUpdate)` and checks each has a matching `docs/event_ledger/entity.yaml` entry (matched via `mutation_source` regex against `EntityUpdate.<field>`). `TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION` (already landed, `tickets/done/`) added a new `status_effect_update: Optional[StatusEffectUpdate]` field to `EntityUpdate` (`src/core/updates.py:677`, wiring `StatusEffectUpdate`) with no corresponding ledger entry added.

2. `tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path` fails with `assert 1320 == 1321` (the fresh live scan now returns 1320, one below the hardcoded `1321`). This is a documented-as-expected-drift baseline (the test's own inline comment carries a running history of prior legitimate decrements: 1343→...→1321) that decrements whenever a `verified`/`divergent` parity-ledger entry with a null `test_path` legitimately gains a real one. Root cause: `TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION`'s Parity phase repaired `docs/parity_ledger/combat_movement.yaml`'s `COMB-122` entry (P0, SHATTER combat mechanic) — confirmed via direct read that it now carries a real, non-null `test_path: tests/unit/combat/test_combat_legality_regression.py::test_shatter_logic` and updated `v2_evidence` citing the `status_effect_update` migration off the prior `identity.properties.get("status_frozen")` dict lookup. This is exactly the "entry legitimately gained a `test_path`" pattern the test's own comment documents as expected drift, not a real defect.

## Scope
- Add a new entry to `docs/event_ledger/entity.yaml` for `EntityUpdate.status_effect_update`, following the existing schema/shape used by sibling entries in that file (`id`, `mutation_source`, `status`, `evidence`, `event_types`, `notes` — e.g. the shape used by `ENTITY-017`/`ENTITY-018` for other post-hoc-added `EntityUpdate` fields), reflecting the field's real current observability coverage (or documented lack thereof) as of this investigation.
- Update the hardcoded baseline literal in `tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path` from `1321` to `1320` (the assertion at line 149, `assert live_missing == 1321`).
- Append one new dated bullet to that same test's existing drift-history comment block (lines ~122-145), in the same established format as the prior bullets (ticket ID, date, which entry gained the `test_path` and why), documenting that `COMB-122` gained its `test_path` via `TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION`'s Parity phase.
- Re-run the exact failing CI command locally to confirm both tests now pass and no new regression was introduced.

## Out of Scope
- The 24 other local test failures already confirmed as sandbox-only environment noise (live-server/subprocess tests) — do not investigate or "fix" these; they are known-flaky per `docs/testing/regression_policy.md` and pass in real CI.
- Any further audit of `docs/event_ledger/entity.yaml` beyond adding the one missing `status_effect_update` entry (e.g. no re-verification of existing entries' `status`/`evidence` accuracy).
- Any change to `EntityUpdate`, `StatusEffectUpdate`, or the SHATTER combat mechanic itself in `src/` — this ticket is documentation/test-baseline reconciliation only, not a behavior change.
- Any other parity-ledger entry besides `COMB-122` — do not sweep for other stale entries beyond what this specific drift requires.
- Re-litigating whether `TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION`'s or `TCK-20260831-TRUST-GATED-TEACHING`'s own implementation was correct — both are already closed/done; this ticket only reconciles the two staleness guards they left behind.

## Acceptance Criteria
1. [DONE] `docs/event_ledger/entity.yaml` contains a new entry with `mutation_source: "EntityUpdate.status_effect_update"` (exact regex-matchable form), matching the file's existing per-entry schema.
2. [DONE] `pytest tests/tools/test_entity_event_ledger.py::test_entity_ledger_covers_every_entity_update_field -m "not slow and not extra_slow"` passes locally.
3. [DONE] `tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path` asserts `live_missing == 1320` and passes locally.
4. [DONE] The drift-history comment in `test_parity_index_baseline.py` has a new bullet documenting this ticket's change (ticket ID, date 2026-09-01, `COMB-122`, reason), appended after the existing `TCK-20260831-ITEM-INSTANCE-HISTORY` bullet, matching the established prose format exactly.
5. [PARTIAL] Full local re-run of the exact CI command (`pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m "not slow and not extra_slow"`) shows these 2 failures resolved, with no new failures introduced beyond the pre-existing 24 confirmed-environment-noise ones. This implementer pass ran the two target tests directly plus the full scoped `tests/tools/` directory (2559 passed, 0 failed) — the exact multi-directory CI command spanning `tests/api tests/cli tests/tools tests/logging tests/engine tests/observability` together was not re-run in this step; left for the pipeline's Test/Verify phase.
6. [NOT DONE] PR #101's "API / tools / logging" GitHub Actions job is confirmed green after the fix is pushed (or explicitly reported as still-pending, not claimed done on local pass alone). Not pushed yet — outside implementer scope; requires the pipeline's later push/Verify step.

## Related Tickets
- TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION (done — introduced `status_effect_update` field and repaired `COMB-122`'s `test_path`; source of both regressions)
- TCK-20260808-ENTITY-EVENT-LEDGER (done — established `docs/event_ledger/entity.yaml` and its staleness-guard test)
- TCK-20260731-PARITY-INDEX-BASELINE (done — established `test_parity_index_baseline.py` and its documented-drift convention)
- TCK-20260830-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT, TCK-20260819-HOTFIX-PARITY-BASELINE-INFRA118-DRIFT, TCK-20260819-HOTFIX-PARITY-BASELINE-DEAD-INFRA-DRIFT, TCK-20260820-HOTFIX-PARITY-READPATH-BASELINE-DRIFT (done — prior instances of this exact same baseline-drift hotfix pattern; format precedent for the new comment bullet)
- TCK-20260830-ENTITY-EVENT-LEDGER-COGNITION-BUNDLE-SET-MISSING (done — prior instance of this exact same entity-ledger-gap pattern for a different `EntityUpdate` field; format precedent for the new ledger entry)

## Related Docs
- docs/event_ledger/entity.yaml
- docs/parity_ledger/combat_movement.yaml (COMB-122 entry — source of the drift, not itself edited by this ticket)
- docs/core/update_intents.md (durable-field classification conventions this ledger follows)

## Related Stored Artifacts
None — hotfix tier (staging artifacts not required per Tier Routing).

## Related Code Areas
- tests/tools/test_entity_event_ledger.py
- tests/tools/test_parity_index_baseline.py
- docs/event_ledger/entity.yaml
- src/core/updates.py (EntityUpdate.status_effect_update field, read-only reference — not modified)
- docs/parity_ledger/combat_movement.yaml (read-only reference — not modified)

## Assumptions / Open Questions
- Assumes `status_effect_update`'s real observability coverage should be documented as whatever it actually is (status_effect mutations may currently be silent/unobserved at the event-extractor layer, mirroring the pattern seen in prior sibling entries like `ENTITY-021`) rather than assumed `observed` — the implementer must verify actual event-extractor coverage before choosing the `status` value for the new entry, not default to `observed`. If verification shows the mutation is genuinely silent, the entry should say so plainly (as `ENTITY-015`/`ENTITY-021` do), which is still a valid, passing outcome for this ticket's acceptance criteria — the AC only requires an entry to exist, not a specific status value.
- Assumes no other `EntityUpdate` field besides `status_effect_update` is currently missing a ledger entry — this was not re-verified via the full staleness-guard's own field-by-field diff beyond confirming the single reported failure; if the implementer's test run surfaces additional missing fields, scope should expand to cover them (still hotfix-appropriate, same mechanical pattern) rather than silently working around a partial fix.
- Assumes `live_missing` will read exactly 1320 at implementation time — if other concurrent tickets on this shared repo alter parity-ledger `test_path`/`status` fields between now and implementation, the live count could drift further; the implementer should re-run the live scan and use whatever real count it reports (updating both the assertion and the comment-history text accordingly) rather than blindly hardcoding 1320 from this scoping snapshot.
- `layer: testing` chosen over `observability` (docs/event_ledger/entity.yaml is nominally observability-adjacent) because the actual failing surface and fix target are both test-infrastructure staleness guards (`tests/tools/`), matching the registered `testing` layer's own note ("Test infrastructure, fixtures, and testing-strategy tickets/docs") more directly than observability's runtime-event scope.

## Implementation Notes
1. Added `ENTITY-022` to `docs/event_ledger/entity.yaml`, documenting `EntityUpdate.status_effect_update` (src/core/updates.py:677). Followed the exact schema of sibling `silent` entries (`ENTITY-015`, `ENTITY-021`). Verified real evidence directly before writing the entry:
   - `grep -n "status_effects" src/observability/event_extractor.py` returns 0 matches — no diff block observes `combat.status_effects` (the existing hp/wounds/scars diff blocks at lines 280-303/443-549 cover other combat-component fields only).
   - `src/engine/patches.py:650-674` (`StatusEffectPatch.apply`, registered in `extract_patches()` at lines 773-775) folds `status_effect_update.effects_add`/`effects_remove` onto `entity.combat.status_effects` — no separate observed component.
   - Real consumers (all gating logic, not event producers) confirmed via grep: `src/engine/combat.py:84-86` (SHATTER modifier), `src/engine/legality.py:132,166,218,319` (frozen/stunned legality gating), `src/engine/pipeline_phases/actor_validity.py:59-60`, `src/systems/strategic_systems/work_queue.py:32`, `src/systems/strategic_systems/intelligence.py:848,918,1221`.
   - `grep -n "status_effect" src/observability/event_shapers.py` returns 0 matches — confirmed no shaper-layer coverage either.
   - Status set to `silent` (real, disclosed gap — no event exists anywhere for this mutation), consistent with the ticket's open-question guidance not to default to `observed`.
2. Verified the live parity-ledger scan (`docs/parity_ledger/*.yaml`, `verified`/`divergent` entries with null `test_path`) independently returns exactly `1320`, matching the ticket's expected count. Updated `tests/tools/test_parity_index_baseline.py`'s hardcoded assertion from `1321` to `1320` and appended one new dated bullet to the existing drift-history comment (after the `TCK-20260831-ITEM-INSTANCE-HISTORY` bullet), documenting that `TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION` repaired `COMB-122`'s `test_path` to `tests/unit/combat/test_combat_legality_regression.py::test_shatter_logic`, in the same prose format as the prior bullets.
3. No other `EntityUpdate` field was found missing a ledger entry beyond `status_effect_update` — the staleness-guard test (`test_entity_ledger_covers_every_entity_update_field`) now passes cleanly with no other reported gaps, so the scope-expansion contingency in "Assumptions / Open Questions" was not triggered.
4. No deviations from the plan in `## Scope`.

## Test Summary
- `pytest tests/tools/test_entity_event_ledger.py::test_entity_ledger_covers_every_entity_update_field tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path -v` — 2 passed.
- `pytest tests/tools/ -m "not slow and not extra_slow" -q` (full directory) — 2559 passed, 12 skipped, 31 deselected, 1 xfailed, 0 failed. No other test in `tests/tools/` depends on the old `1321` value or regressed from the new ledger entry.
- Full CI-parity command (`pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m "not slow and not extra_slow"`) and PR #101 CI job status (AC #5/#6) were not re-run in this pass — out of scope for the local implementation step; see note below.

## Files Changed
- `docs/event_ledger/entity.yaml` (added `ENTITY-022` entry for `EntityUpdate.status_effect_update`)
- `tests/tools/test_parity_index_baseline.py` (updated hardcoded assertion `1321` -> `1320`; appended one dated drift-history bullet)
- `docs/simulation_quality/entity_lifecycle_score.md` (Document-Update phase — fixed a stale `20-row` reference to `docs/event_ledger/entity.yaml`'s row count, bumped to `22-row` to match the real live count after `ENTITY-022`'s addition; this doc's row-count reference was already 2 rows stale before this ticket, from a prior ticket's ENTITY-021 addition, and this ticket's own ENTITY-022 pushed it a further row out of date)
- `tickets/inprogress/TCK-20260901-HOTFIX-ENTITY-LEDGER-PARITY-BASELINE-DRIFT.md` (this file — Implementation Notes / Test Summary / Files Changed / Completion Summary / Status filled in)

## Completion Summary
Both staleness-guard regressions from PR #101's "API / tools / logging" job are fixed. `docs/event_ledger/entity.yaml` gained a new `ENTITY-022` entry documenting `EntityUpdate.status_effect_update` as `silent` (verified via direct grep against `event_extractor.py`/`event_shapers.py` and the real `StatusEffectPatch` apply-path and consumer sites), satisfying the ledger's own staleness-guard test. `tests/tools/test_parity_index_baseline.py`'s hardcoded `live_missing` baseline was updated from `1321` to `1320` with a matching drift-history comment bullet, reflecting `COMB-122`'s real `test_path` repair from `TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION`. The Document-Update phase independently caught and fixed one further real gap beyond the original two-item scope: `docs/simulation_quality/entity_lifecycle_score.md` cited entity.yaml's row count as `20-row`, already stale by 2 rows before this ticket and pushed a further row out of date by this ticket's own ENTITY-022 addition — corrected to `22-row`. Both originally-scoped target tests pass locally (individually re-confirmed at Verify), and the full `tests/tools/` suite (2559 tests) shows no regressions attributable to this change. Pure documentation/test-baseline bookkeeping — no `src/` logic was touched, no behavior changed.

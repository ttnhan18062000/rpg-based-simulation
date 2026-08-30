---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260830-HOTFIX-PROGRESSION-DECISION-CANONICAL-HASH-CRASH
phase: done
date: 2026-08-30
tags: [feature-flags]
---

# TCK-20260830-HOTFIX-PROGRESSION-DECISION-CANONICAL-HASH-CRASH

## Title
Fix `CanonicalStateHasher` Crash on Non-JSON-Serializable `ProgressionDecisionResult`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Filed from `TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION`'s real 4-leg corpus trial. With
`ENABLE_PROGRESSION_EVOLUTION=ON`, the real pipeline deterministically crashes (reproduced 4
independent times across 2 different worlds/seeds):

```
TypeError: Object of type ProgressionDecisionResult is not JSON serializable
```

Root cause: `ProgressionConversionPhase.execute()` (`src/domains/progression/phase.py:80`) stores
a raw `ProgressionDecisionResult` dataclass directly into `property_updates`:

```python
prop_upd = dict(merged_upd.property_updates)
prop_upd["last_progression_decision"] = decision
```

`property_updates` is later passed through `CanonicalStateHasher.get_hash()` /
`to_canonical_json()` (`src/engine/checkpoint.py:44-58`), which calls `json.dumps(data, ...)` with
no custom encoder — a raw dataclass instance there always raises `TypeError`. This confirms why
the flag has stayed OFF with zero real corpus profiles: no one has ever run the phase through the
actual `Kernel` loop with the flag ON before this trial (existing `test_phase6_*.py` coverage
calls the phase/services directly, bypassing the pipeline's canonical-hash step entirely).

This is also a Durable State Rule violation independent of the crash itself: storing an untyped,
non-serializable raw dataclass into a free-form `property_updates` dict is exactly the pattern
CLAUDE.md's Durable State Rule prohibits ("If something survives beyond the current tick or
current function call, it must have a typed model... Do not store durable meaning in... temporary
local variables" — `property_updates` is the project's own free-form-metadata analogue here).

## Scope
- Fix `ProgressionConversionPhase.execute()` so `last_progression_decision` (or whatever replaces
  it) is JSON-serializable through `CanonicalStateHasher`, either by:
  - converting `ProgressionDecisionResult` to a plain serializable dict/typed record before
    storing it, or
  - not storing the raw decision in `property_updates` at all, if a typed observation channel
    already exists elsewhere for this purpose (check `docs/core/state.md`'s durable-state
    partitioning for the correct location).
- Confirm the fix holds under a real flag-ON trial (re-run at least one of the two worlds/seeds
  `TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION` used —
  `stored_artifacts/TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION/trial_evidence.md` has the
  exact repro commands).

## Out of Scope
- Flipping `ENABLE_PROGRESSION_EVOLUTION`'s default — this fix removes one blocking prerequisite
  named in the filing ticket's recommendation, but the separate reward-ledger producer gap
  (`RewardLedgerService` has zero live callers — already tracked via the 2026-08-30 update to
  `docs/guidelines/intentional_divergences.md`'s DEV-004 entry) is a distinct, larger, not-yet-
  scoped gap and is not this ticket's job to close.
- Building new pipeline-wiring test coverage beyond what's needed to confirm this specific fix
  (the filing ticket already disclosed the general pipeline-wiring coverage gap; a full build-out
  is a separate scope decision).

## Acceptance Criteria
- [x] Running the pipeline with `ENABLE_PROGRESSION_EVOLUTION=ON` no longer raises
  `TypeError: Object of type ProgressionDecisionResult is not JSON serializable`.
- [x] A regression test exercises `ProgressionConversionPhase.execute()` through
  `CanonicalStateHasher.get_hash()` (or equivalent full-hash path) with the flag ON, so this
  cannot silently regress.
- [x] Existing `tests/unit/domains/progression/` and `tests/integration/.../progression*` tests still
  pass.

## Related Tickets
- TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION (filing ticket, disclosed this finding)

## Related Docs
- CLAUDE.md (Durable State Rule)
- docs/guidelines/intentional_divergences.md (DEV-004)
- docs/core/state.md

## Related Code Areas
- src/domains/progression/phase.py
- src/engine/checkpoint.py (CanonicalStateHasher)

## Assumptions / Open Questions
Whether a typed observation channel for "last progression decision" already exists elsewhere in
the durable-state model, or needs to be introduced — to be resolved during implementation.

## Implementation Notes
Fix approach: convert `ProgressionDecisionResult` to a plain JSON-serializable dict at the write
site in `ProgressionConversionPhase.execute()`, using `dataclasses.asdict(decision)`, rather than
introducing a new typed durable-state observation channel. Rationale (recorded before
implementation, unchanged after building it):
1. No existing typed observation channel for "last progression decision" exists elsewhere in the
   durable-state model (`EntityUpdate`/`EntityState`/`AuthoritativeState` in
   `src/core/updates.py` and `src/core/state.py`). `property_updates: Dict[str, Any]` is already
   the established, repo-wide pattern for lightweight debug/trace tags stored on
   `entity.identity.properties` (e.g. `"movement_resolution"` in `src/engine/movement.py`) —
   every existing value stored there is already a JSON primitive or primitive container.
   Introducing a brand-new typed durable-state field/component for this single debug-trace value
   is out of proportion for a hotfix and is exactly the kind of larger architectural change this
   ticket's Out of Scope note (and DEV-004) explicitly defers.
2. `docs/core/state.md`'s "Serialization & Canonical Truth" convention (everything reaching
   canonical serialization resolves to primitives/dicts/lists) is satisfied by `asdict()` for this
   nested dataclass without adding a new serialization protocol.
3. Verified empirically that `dataclasses.asdict(decision)` on a real `ProgressionDecisionResult`
   (including its nested `ConversionOption` tuple and `ConversionKind` str-Enum member, which
   survives unchanged inside the dict but still serializes correctly under `json.dumps` because it
   subclasses `str`) round-trips cleanly through `json.dumps(..., sort_keys=True)` — both via the
   new unit test and the real flag-ON trial below.
4. `ConversionDecisionService.select()`'s `trace` dict only ever stores plain strings — no hidden
   non-serializable payload lurking inside `trace` that `asdict()` wouldn't already handle.

Code change: `src/domains/progression/phase.py` — extended the existing
`from dataclasses import replace` import to `from dataclasses import asdict, replace`, and changed
`prop_upd["last_progression_decision"] = decision` to
`prop_upd["last_progression_decision"] = asdict(decision)`, with a short comment on the `asdict()`
call explaining the canonical-hash JSON-compatibility reason (non-obvious from the call alone). No
other logic/control flow in the file was touched.

Real flag-ON trial verification (run from the worktree, using the main checkout's
`.venv/bin/python3` per the ticket's exact repro command from
`stored_artifacts/TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION/trial_evidence.md`, scaled
down to 300 ticks — the original crash reproduced by tick ~120-121):
```
ENABLE_PROGRESSION_EVOLUTION=ON /home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 \
  tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 300 \
  --output data/calibration/dungeon_crawl_seed42_300t_progression_evolution_ON_verify
```
Result: exit code 0. All 300 ticks completed (`ticks=300 events=321 elapsed=5.31s`, quality report
written to `data/calibration/dungeon_crawl_seed42_300t_progression_evolution_ON_verify/quality_report.json`,
`progression_conversion` phase cost present in the per-tick phase-cost breakdown confirming the
phase actually ran with the flag on). No `TypeError` anywhere in stdout or in the run's JSONL logs
(`data/runs/run_1788069285_5169`) — confirmed via `grep -rli typeerror` over both, zero matches.
The only warnings emitted were pre-existing, unrelated tick-budget/watchdog warnings (locomotion
phase cost), not errors.

Regression test: `tests/unit/domains/progression/test_progression_decision_canonical_hash.py`
(new file, following the existing `test_phase6_progression_boundary.py`
`test_progression_service_does_not_mutate_state` fixture pattern — `V2EntityBuilder`, a minimal
one-entity `AuthoritativeState`, calling `ProgressionConversionPhase.execute()` directly against a
bare `StateUpdate()`, same as that existing test, since the phase's own `execute()` does not check
`ENABLE_PROGRESSION_EVOLUTION` itself — that gating happens one layer up, in the
`run_phase(..., "ENABLE_PROGRESSION_EVOLUTION")` wrapper in `src/engine/pipeline.py:342-343`).
The test applies the phase's real `property_updates` output into `entity.identity.properties`
(mirroring exactly what `IdentityPatch.apply()` does in `src/engine/patches.py:213-215` —
`props.update(self.property_updates)` — without pulling in the full `ApplyPath` machinery, which
is unrelated to what's being regression-tested here), then calls both
`CanonicalStateHasher.to_canonical_json()` (asserting the decoded JSON's
`last_progression_decision` dict has `entity_id`/`selected`/`trace`/`reason` keys and the correct
`entity_id`) and `CanonicalStateHasher.get_hash()` (asserting it returns a 64-char sha256 hex
string with no exception).

Tests run: `tests/unit/domains/progression/` (21 passed, including the 2 new tests) and
`tests/integration/progression/` (1 passed, `test_allocate_ap_dormancy.py` — unaffected by this
change, still confirms the ALLOCATE_AP branch stays dormant per DEV-004).

No deviations from the plan given in the ticket's own investigation/decision section.

## Test Summary
- `tests/unit/domains/progression/` — 21 passed (19 pre-existing + 2 new in
  `test_progression_decision_canonical_hash.py`).
- `tests/integration/progression/test_allocate_ap_dormancy.py` — 1 passed (unaffected regression
  check).
- Real flag-ON trial: `ENABLE_PROGRESSION_EVOLUTION=ON` `tools/calibrate_simq.py` for
  `dungeon_crawl` seed 42, 300 ticks — exit code 0, no `TypeError`, all 300 ticks completed. See
  Implementation Notes for the full command and output excerpt.

## Files Changed
- `src/domains/progression/phase.py` — the fix (`asdict(decision)` instead of raw dataclass).
- `tests/unit/domains/progression/test_progression_decision_canonical_hash.py` — new regression
  test (2 test functions).
- `docs/parity_ledger/progression.yaml` — added `PROG-121` (status `verified`, priority `P0`,
  `v2_evidence` pointing at `phase.py:83`, `test_path` pointing at the new regression test).
- `docs/simulation/domains/progression_contract.md` — updated the "Debug trace property" bullet
  and Step 6 (Intent Resolution) description to document the `asdict()` serialization requirement;
  bumped `last_verified` to 2026-08-30.
- `docs/architecture/rollout_flag_decisions_m1.md` — updated the `ENABLE_PROGRESSION_EVOLUTION`
  summary-table row and added a "Post-fix status update" note under the flag's Validation Trial
  Result section, recording that the crash prerequisite is resolved while the reward-ledger
  producer gap (DEV-004) remains and the flag's default stays OFF.
- `tickets/inprogress/TCK-20260830-HOTFIX-PROGRESSION-DECISION-CANONICAL-HASH-CRASH.md` — this
  file (Implementation Notes, Test Summary, Files Changed, Completion Summary, Status, Acceptance
  Criteria checkboxes).

## Completion Summary
Fixed the `TypeError: Object of type ProgressionDecisionResult is not JSON serializable` crash by
converting the raw `ProgressionDecisionResult` dataclass to a plain dict via `dataclasses.asdict()`
before storing it in `property_updates["last_progression_decision"]` in
`ProgressionConversionPhase.execute()` (`src/domains/progression/phase.py`). Added a regression
test (`tests/unit/domains/progression/test_progression_decision_canonical_hash.py`) that exercises
the phase's real output through `CanonicalStateHasher.to_canonical_json()`/`get_hash()` and asserts
no `TypeError` and correct dict shape. Verified the fix against the ticket's real
`ENABLE_PROGRESSION_EVOLUTION=ON` Kernel-driven repro command (300-tick `dungeon_crawl` seed 42
trial) — exit code 0, no crash, all ticks completed. All existing progression unit and integration
tests still pass. Updated the parity ledger (`PROG-121`), the progression domain contract doc, and
the `ENABLE_PROGRESSION_EVOLUTION` rollout-flag decision doc to reflect the fix and record that the
flag's default stays OFF pending the separate, out-of-scope reward-ledger producer gap (DEV-004).

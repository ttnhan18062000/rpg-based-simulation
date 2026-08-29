---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260830-HOTFIX-PROGRESSION-DECISION-CANONICAL-HASH-CRASH
phase: open
date: 2026-08-30
tags: [feature-flags]
---

# TCK-20260830-HOTFIX-PROGRESSION-DECISION-CANONICAL-HASH-CRASH

## Title
Fix `CanonicalStateHasher` Crash on Non-JSON-Serializable `ProgressionDecisionResult`

## Status
OPEN

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
- Running the pipeline with `ENABLE_PROGRESSION_EVOLUTION=ON` no longer raises
  `TypeError: Object of type ProgressionDecisionResult is not JSON serializable`.
- A regression test exercises `ProgressionConversionPhase.execute()` through
  `CanonicalStateHasher.get_hash()` (or equivalent full-hash path) with the flag ON, so this
  cannot silently regress.
- Existing `tests/unit/domains/progression/` and `tests/integration/.../progression*` tests still
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
(Not yet implemented — filed and deferred, per session's "verify follow-up tickets, then SimQ" sequencing.)

## Test Summary
(Not yet implemented.)

## Files Changed
(Not yet implemented.)

## Completion Summary
(Not yet implemented.)

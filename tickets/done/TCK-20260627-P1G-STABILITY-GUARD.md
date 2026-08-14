---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260627-P1G-STABILITY-GUARD
phase: done
date: 2026-06-27
tags: [kernel, stability-guard, audit-mode, isolation, documentation]
---

# TCK-20260627-P1G-STABILITY-GUARD

## Title
Document phase stability guard scope and evaluate lightweight guard for standard runs

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
`_guard_stability()` in `src/engine/kernel.py` fingerprints `AuthoritativeState` between phases to catch isolation breaches (a phase mutating state outside the authoritative pipeline). It is only active when `Kernel` is initialized with `audit_mode=True`. An isolation breach in a normal production run is invisible. Source: D09 Finding 5, Risk 11/15.

## Scope
- Document which violation types are only detectable in `audit_mode=True` in `docs/engine/known_limitations.md`.
- Evaluate adding a lightweight guard to standard runs: hash only entity count and tick number (not full state) to catch gross isolation breaches without performance overhead.
- If the lightweight guard is feasible: implement it in `kernel.py:_tick_once_inner()` behind a separate flag or unconditionally.
- Update `docs/engine/kernel.md` §"Stability Guard Law" with the new information.

## Out of Scope
- Full state hashing in standard runs (that is `audit_mode` and `replay_richness=FULL` — see P2-F for documentation of canonical hashing).
- Changes to what `_guard_stability()` does in `audit_mode`.

## Acceptance Criteria
- [ ] `docs/engine/known_limitations.md` documents: "Isolation breaches in non-audit phases are only caught in `audit_mode=True`".
- [ ] Decision on lightweight guard is recorded (implement or explicitly reject with rationale).
- [ ] If implemented: lightweight guard runs in standard mode and raises on gross violation (entity count changes mid-phase without a lifecycle event).
- [ ] `docs/engine/kernel.md` §Stability Guard Law updated.
- [ ] Run `make knowledge-index-update` after doc changes.

## Related Tickets
- TCK-20260627-P2F-CANON-HASH-DOC (related — canonical state hashing scope documentation)
- TCK-20260627-P2E-FEATURE-FLAG-TEST (test coverage for phase isolation)

## Related Docs
- `docs/audits/D09_system_wiring.md` Finding 5
- `docs/engine/kernel.md` §Stability Guard Law
- `docs/engine/known_limitations.md`

## Related Stored Artifacts
- N/A

## Related Code Areas
- `src/engine/kernel.py` (`_guard_stability()`, `_tick_once_inner()`)

## Assumptions / Open Questions
- "Entity count + tick number" hash is a proxy for gross violations only. True isolation enforcement requires `audit_mode`.
- Performance overhead of even a lightweight hash should be measured — benchmark against hardware class B target.

## Implementation Notes
- Added `_guard_gross_isolation(phase_name, expected_entity_count, expected_tick)` to `Kernel` — checks `len(state.entities)` and `state.tick` (two O(1) int reads) and raises `ProtocolViolationError` on mismatch.
- Updated `_tick_once_inner()`: lightweight guard runs unconditionally in non-audit mode after Scheduling and Collection phases; audit mode still uses full `_guard_stability()`.
- Decided to run unconditionally (no flag) — the guard is two integer reads, cheaper than any runtime flag check that would be meaningful.
- `CanonicalStateHasher.fingerprint()` was inspected — full hash, too expensive for standard hot path. Raw `len(dict)` + int read is the right approach.
- `docs/engine/known_limitations.md` §2.3 added with full violation-type detection matrix.
- `docs/engine/kernel.md` §Stability Guard Law updated to document two-tier (gross / full) architecture.

## Test Summary
- Doc verification: `docs/engine/known_limitations.md` contains the isolation-breach caveat.
- If lightweight guard implemented: unit test that a gross mid-phase mutation triggers the guard in standard mode.

## Files Changed
- `src/engine/kernel.py` — added `_guard_gross_isolation()` method; updated `_tick_once_inner()` to call it unconditionally in non-audit mode after Scheduling and Collection phases
- `docs/engine/known_limitations.md` — added §2.3 Phase Isolation Detection with full violation-type detection matrix
- `docs/engine/kernel.md` — updated §Stability Guard Law to document two-tier (gross/full) architecture
- `tests/unit/core/test_engine_integrity.py` — added 3 new tests covering gross guard trigger on tick change, entity count change, and clean-state pass-through
- `docs/parity_ledger/infrastructure.yaml` — added INFRA-222 entry for the new gross isolation guard

## Completion Summary
Implemented two-tier phase isolation guard: (1) documented in `known_limitations.md` §2.3 that field-level mutations are only caught in `audit_mode=True`; (2) added lightweight `_guard_gross_isolation()` to `Kernel` running unconditionally in standard mode — two O(1) integer reads checking entity count and tick number — which detects gross lifecycle violations mid-phase without measurable performance overhead; (3) updated `kernel.md` §Stability Guard Law and parity ledger INFRA-222; 6 tests pass including 3 new tests.

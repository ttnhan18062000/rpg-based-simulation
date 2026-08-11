---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG
phase: open
date: 2026-08-11
tags: [cognition, strategy]
---

# TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG

## Title
`evaluate_project_switch()`'s normalized lock-bypass gate structurally cannot ever let a
System-B candidate interrupt a locked System-A current project

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION` (C2) generalized
`StrategicIntelligenceSystem.evaluate_project_switch()`'s lock-bypass gate from a hardcoded
`"danger"/"detour"` allowlist to a normalized score/urgency-floor rule:

```python
candidate_max = _score_scale_max(candidate_project.kind)
current_max = _score_scale_max(current.kind)
candidate_pct = candidate_project.score / candidate_max
normalized_effective_current_pct = (current.score / current_max) + (retention_margin / current_max)
if not (candidate_pct > normalized_effective_current_pct and candidate_pct > _INTERRUPTION_URGENCY_FLOOR_PCT):
    return None
```
(`src/systems/strategic_systems/intelligence.py:988-993`)

`TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`'s post-batch re-investigation
(`stored_artifacts/TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION/investigation.md`'s
"Post-Batch Re-Investigation" section) found, via a live monkeypatched trace of 1365 real
`evaluate_project_switch()` calls (SEED=42, 400 ticks): **0 of 24** calls made while
`current.lock_until_tick > current_tick` ever resulted in a switch, for any kind, anywhere in the
run. The specific, confirmed mechanism: `retention_margin` (default `interruption_resistance(0.3) *
resistance_multiplier(30.0) = 9.0`, `src/core/strategic.py:320-321`) is divided by `current_max`
rather than normalized to any shared scale. When `current` is a System-A (`ProjectKind`) project,
`current_max = _ADVENTURE_ROUTE_SCORE_MAX = 2.9`, so `retention_margin / current_max ≈ 3.10` —
**a percentage-point value alone exceeding 310%** — before even adding `current.score/current_max`.
Since no real System-B `CombatEngageScorer` candidate observed in the trace ever produced
`candidate_pct` above ~1.0–1.33, a System-B candidate can never mathematically clear
`normalized_effective_current_pct` while `current` is System-A-typed, for any value either
system's scorers can realistically produce today.

This contradicts `STRAT-186`'s own documented intent ("Strategic project switching requires margin
or explicit emergency" — implying a genuine emergency-equivalent candidate should still be able to
get through) and makes `STRAT-187`'s "current project has reservation priority" absolute/
un-interruptible in this direction rather than merely favored, a stronger guarantee than the
Mechanics Bible documents.

This did not block `TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`'s own fix from
working, because System-A locks in that scenario are short (10 ticks, capped at 50) and the
*unlocked* raw-score comparison path (`if candidate_project.score > effective_current_score:`,
C2-untouched) rescues stuck heroes once the lock naturally expires. A scenario with longer
System-A locks, or any future tightening of `_threat_resolved()`/`AdventureDecisionPhase`'s own
per-hero lock gate, would re-expose full starvation with no escape path at all.

## Scope
- Fix the normalization so `retention_margin` does not structurally dominate the comparison when
  `current` belongs to a small-max system (System A, `~2.9`) — the exact mechanism is an Implement-
  time design decision (see Assumptions/Open Questions below), not decided by this ticket's Scope
- Add a regression test exercising the specific direction C2's own test suite never covered: a
  locked System-A `current` (small max) challenged by a System-B `candidate` (large max) whose
  score represents a genuine emergency/high-urgency case — must be able to bypass under the fixed
  formula, while a low-urgency System-B candidate must still correctly fail to bypass
- Update `docs/parity_ledger/strategic_cognition.yaml`'s STRAT-186/187 entries to reflect the fix
  (their current `v2_evidence`, written by C2, describes the pre-fix behavior)
- Update `docs/mechanics/04_strategic_cognition.md` §2 if the normalization basis changes materially
  from what C3 already documented there

## Out of Scope
- `TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`'s own test/statistical fix — that
  ticket does not depend on this fix landing (confirmed: the specific heroes it compares never hit
  the locked path)
- Any change to `CombatEngageScorer`'s bravery weighting or other scoring formulas
- Reviving `RouteFamily.HUNT_WEAK_ENEMY` or unifying `GoalKind`/`ProjectKind` — unrelated, tracked
  under D22

## Acceptance Criteria
- [ ] A locked System-A `current` project CAN be interrupted by a genuinely high-urgency System-B
      candidate under the fixed formula — verified via a new test using real, realistic score values
      (not synthetic values chosen just to pass)
- [ ] A locked System-A `current` project is still NOT interrupted by a low-urgency System-B
      candidate — the fix must not overcorrect into "any candidate can always interrupt"
- [ ] All existing tests in `tests/unit/strategic/test_interruption_resistance.py`,
      `test_project_continuity.py`, `test_score_normalization.py` still pass (with any that encoded
      the buggy behavior updated, not just left green by accident)
- [ ] STRAT-186/187 parity-ledger entries updated to describe the fixed mechanism

## Related Tickets
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION (C2 — landed the buggy normalization this
  ticket fixes)
- TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION (the ticket whose re-investigation
  discovered this bug as a byproduct)

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
- stored_artifacts/TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION/ (the plan/investigation that
  landed the current formula)
- stored_artifacts/TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION/investigation.md (the
  "Post-Batch Re-Investigation" section — the direct evidence and real trace numbers for this bug)

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (`evaluate_project_switch`, `_score_scale_max`,
  module constants)
- src/core/strategic.py (`CognitionProfile` defaults)

## Assumptions / Open Questions
- The exact fix mechanism is not decided: options include (a) normalizing `retention_margin` itself
  as a percentage of `current_max` at its point of origin rather than treating it as a raw-scale
  constant, (b) capping `retention_margin`'s contribution to the normalized comparison at some
  fraction, (c) computing `normalized_effective_current_pct` differently (e.g., percentage of
  `current_max` for the raw score, but comparing `retention_margin` against a fixed absolute
  floor instead of dividing it by `current_max`), or (d) something else — Investigate/Plan must
  determine the right approach with real evidence, not guess
- Whether this bug is severe enough to warrant a `hotfix`-tier minimal patch or a `standard`-tier
  redesign is also an Implement-time judgment call, informed by how many real corpus scenarios are
  actually affected (currently only 2 of 20 corpus worlds have `ENABLE_ADVENTURE_ROUTING=ON`)

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

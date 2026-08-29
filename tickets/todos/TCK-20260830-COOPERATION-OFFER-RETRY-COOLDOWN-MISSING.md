---
status: active
layer: social
authority: P2
audience: agent
ticket_id: TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING
phase: open
date: 2026-08-30
tags: [social, simulation-quality]
---

# TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING

## Title
Cooperation Offers Have No Retry Cooldown — Same Entity Re-Offers Every Tick After Expiry

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Filed from `TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE`'s due-diligence check on
`highland_traverse_seed42_200t`'s SOCIAL-pillar score decrease. That ticket's own investigation
confirmed (via direct code read of the entire `src/domains/cooperation/` package plus real
event-trace evidence) a genuine tuning gap: `src/domains/cooperation/phase.py`/`services.py` has
no cooldown or backoff after a cooperation offer expires unaccepted — the same entity fires
`contract_expired_offer` on **20-23 literally consecutive ticks**, immediately re-proposing a new
offer every tick right after the previous one lapses.

This linear accumulation of `offer_dead`-weighted `contract_expired_offer` events
(`src/simulation_quality/scorers/social.py:28,99-100`) is what drags `highland_traverse_seed42_200t`'s
SOCIAL score down enough to fail its grade-anchor band check even after the corpus-wide
re-baseline — it was deliberately left un-rebaselined and disclosed rather than silently
re-anchored, since a rapidly-repeating identical rejection is a real behavioral gap (missing
retry throttling), not a one-time legitimate signal like the rest of the corpus's SOCIAL drift.

## Scope
- Add a retry cooldown/backoff to cooperation-offer proposal logic so the same entity does not
  immediately re-propose a cooperation offer to the same (or any) target on the tick right after
  a prior offer expired unaccepted.
- Confirm the fix actually reduces `contract_expired_offer` event density for
  `highland_traverse_seed42_200t` (re-run the real corpus trial, don't assume).
- Once the fix holds, re-baseline `highland_traverse_seed42_200t`'s SOCIAL anchor entry in
  `tests/simulation_quality/fixtures/grade_anchors.json` to reflect the corrected (real) score —
  this ticket both fixes the behavior and closes out the one anchor entry the rebaseline ticket
  deliberately left open.

## Out of Scope
- Any other SOCIAL/cooperation scoring or weighting change — this is specifically about the
  missing retry cooldown, not a broader cooperation-system tuning pass.
- Re-litigating any other run_key's anchor value — only `highland_traverse_seed42_200t` is in
  scope here.

## Acceptance Criteria
- Cooperation offers have a real cooldown/backoff after expiry (implementer's judgment on the
  right mechanism — a per-entity or per-pair tick-based cooldown consistent with how other
  proposal-throttling exists elsewhere in the codebase, if any precedent exists).
- `test_grade_within_anchor_band[highland_traverse_seed42_200t]` passes after the anchor is
  updated to reflect the fixed behavior.
- A regression test confirms an entity does not re-propose a cooperation offer on the tick
  immediately following a prior expiry.

## Related Tickets
- TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE (filing ticket, disclosed this finding)

## Related Docs
- docs/testing/regression_policy.md

## Related Code Areas
- src/domains/cooperation/phase.py
- src/domains/cooperation/services.py
- src/domains/cooperation/postures.py
- src/simulation_quality/scorers/social.py
- tests/simulation_quality/fixtures/grade_anchors.json

## Assumptions / Open Questions
Exact cooldown duration/mechanism (fixed tick count vs. relationship-state-based) to be decided
during implementation, informed by whatever precedent exists elsewhere in the cooperation/social
domain for similar throttling.

## Implementation Notes
(Not yet implemented — filed and deferred.)

## Test Summary
(Not yet implemented.)

## Files Changed
(Not yet implemented.)

## Completion Summary
(Not yet implemented.)

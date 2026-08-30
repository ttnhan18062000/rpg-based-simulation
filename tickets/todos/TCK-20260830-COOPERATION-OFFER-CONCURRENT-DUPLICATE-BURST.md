---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260830-COOPERATION-OFFER-CONCURRENT-DUPLICATE-BURST
phase: open
date: 2026-08-30
tags: [simulation-quality, social]
---

# TCK-20260830-COOPERATION-OFFER-CONCURRENT-DUPLICATE-BURST

## Title
Cooperation-Offer Creation Not Gated on an Already-Pending Offer (Multi-Offer Burst Before First
Expiry)

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Filed from `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING`'s implementation. That ticket
added a post-expiry retry cooldown (`COOPERATION_OFFER_COOLDOWN_TICKS = 15`,
`src/systems/social_systems/contracts.py`) that correctly bounds the previously-unbounded
re-offer loop. However, real trial evidence from that ticket's own corpus run
(`highland_traverse_seed42_200t`) showed an initial multi-tick burst of several simultaneous
un-expired offers from the same entity BEFORE the first offer ever expires — offer *creation* in
`CooperationDecisionService.select()` (`src/domains/cooperation/services.py`) is not gated on
whether the entity already has a pending (`ContractStatus.OFFERED`) `RECRUITMENT` contract, only
post-expiry retry is now throttled.

This is a smaller, secondary gap than the one already fixed — the unbounded indefinite retry loop
is gone — but it's still a real duplicate-offer burst worth closing for correctness.

## Scope
- Gate cooperation-offer creation in `CooperationDecisionService.select()` on whether the entity
  already has a pending `OFFERED`/`RECRUITMENT` contract to the same (or any) candidate, similar
  in spirit to the cooldown check `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING` added.
- Confirm via a real corpus trial that the initial-burst pattern is gone.
- Add a regression test.

## Out of Scope
- Any change to the post-expiry retry cooldown itself (already correctly fixed).
- Any other SOCIAL/cooperation scoring or weighting change.
- Re-anchoring any `grade_anchors.json` entries unless this fix measurably changes a real trial's
  score enough to require it (check before assuming).

## Acceptance Criteria
- An entity does not create a second simultaneous `RECRUITMENT` offer while one is already
  `OFFERED` and unexpired.
- A regression test confirms this.
- Existing cooperation/contract tests still pass.

## Related Tickets
- TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING (filing ticket, disclosed this finding)

## Related Code Areas
- src/domains/cooperation/services.py
- src/systems/social_systems/contracts.py

## Assumptions / Open Questions
None yet.

## Implementation Notes
(Not yet implemented — filed and deferred.)

## Test Summary
(Not yet implemented.)

## Files Changed
(Not yet implemented.)

## Completion Summary
(Not yet implemented.)

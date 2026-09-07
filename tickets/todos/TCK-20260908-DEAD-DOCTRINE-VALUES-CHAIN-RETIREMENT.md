---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT
phase: open
date: 2026-09-08
tags: [architecture, strategy]
---

# TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT

## Title
Decide the disposition of the confirmed-dead Doctrine/Values motivation chain — delete or formally retire in place

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Follow-up from the Dormant Mechanism Closure epic (`TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE`,
merged via PR #144). `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE` confirmed 4 modules/classes are
dead in production — not merely under-used — and disclosed this in
`docs/guidelines/intentional_divergences.md` §2.53, but deliberately did not delete or formally retire
them (out of that ticket's own narrow scope), leaving a "CONFIRMED DEAD LEGACY CODE" docstring as the
only in-code signal:
- `MotivationBiasService.compute_bias_multiplier()` (`src/domains/motivation/service.py`) — zero real
  callers anywhere in `src/`.
- `DoctrineResolver.resolve()` (`src/domains/motivation/resolver.py`) — zero real (non-test) callers;
  the only two `identity(class_id=...)` construction sites in the codebase
  (`src/testing/scenario_runner.py`, `src/domains/campaigns/runner.py`) are test/analysis utilities,
  not the real corpus-world entity population path.
- `IdentityDoctrine`, `ValuePreferenceProfile` (`src/core/cognition.py`) — `ValuePreferenceProfile`'s
  fields all default to exactly `0.5`, so `compute_bias_multiplier()`'s own `(value - 0.5) * 0.5` terms
  are mathematically guaranteed to evaluate to `0.0` for every real entity even if the service were
  called.

§2.53 itself flagged this as a real, disclosed gap needing a future decision, not resolved there.

## Scope
- Re-confirm during Investigate that all 4 are still genuinely dead (re-grep for real callers) — do
  not assume the 2026-09-07 finding is still accurate without re-checking.
- Present the real decision (see Assumptions/Open Questions) to the user/roadmap owner: delete the 4
  modules/classes outright, or formally document them as permanently-retired-in-place if deletion
  carries real risk (e.g. external tooling or a future roadmap idea referencing these module paths by
  name).
- Whichever is chosen, update `docs/guidelines/intentional_divergences.md` §2.53 to record the final
  disposition (not leave it as a standing "not actioned" note indefinitely).

## Out of Scope
- Reviving the chain — already ruled out by `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`'s own
  decision (bypass legacy, extend `personality_bias`); not re-litigated here.
- Any other item from the Dormant Mechanism Closure epic's scope.

## Acceptance Criteria
- [ ] A real, evidenced decision (delete vs. formally retire-in-place) is made and recorded.
- [ ] If deleted: no regression in the touched-area test suite; the 4 "CONFIRMED DEAD LEGACY CODE"
      docstring cross-references in `personality_bias`'s own §2.53/§2.55 branches are updated to stop
      pointing at now-nonexistent code.
- [ ] `docs/guidelines/intentional_divergences.md` §2.53 updated to reflect the final disposition.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (`tickets/done/` — parent epic)
- `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE` (`tickets/done/` — original dead-chain finding)

## Related Docs
- `docs/guidelines/intentional_divergences.md` §2.53

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/domains/motivation/service.py`, `src/domains/motivation/resolver.py`
- `src/core/cognition.py` (`IdentityDoctrine`, `ValuePreferenceProfile`)

## Assumptions / Open Questions
- **Decided 2026-09-08 (real user decision)**: **delete the 4 modules/classes outright.** Investigate
  should still check for any reference to these exact module/class paths outside `src/` (docs,
  external tooling, roadmap docs) before deleting — the decision to delete stands regardless, but if
  a real external reference is found, update it rather than silently leaving a dangling reference.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

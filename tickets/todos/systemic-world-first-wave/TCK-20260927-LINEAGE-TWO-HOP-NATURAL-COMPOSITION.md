---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260927-LINEAGE-TWO-HOP-NATURAL-COMPOSITION
phase: open
date: 2026-09-27
tags: [lifecycle, engine]
---

# TCK-20260927-LINEAGE-TWO-HOP-NATURAL-COMPOSITION

## Title
Verify a bounded two-hop lineage sequence through ordinary ticks: predecessor → heir → next heir

## Status
OPEN — brief only, not started. First-wave milestone M4a. Gated **only** on
TCK-20260927-NATURAL-AGING-OLD-AGE-DISPATCH-RACE (M1) meeting its acceptance criteria. It is not
gated on any observer/player-side result (M2). Starts only after the owner reviews the first-wave
scope.

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
**Semantic contract.** History causes later world state: a death's lineage consequences must
persist and themselves be carried forward when the heir later dies (roadmap §3.2, §3.4). Only the
world side is in scope; legibility to any observer is a separate question (M2).

**Observed problem.**
- Each single death→heir transition is verified today, but only with staged starting state:
  - `tests/simulation_quality/test_heir_inventory_transfer_corpus.py`;
  - `tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py`.
- A second hop through ordinary aging could not be composed. M1's defect prevents natural-aging
  succession entirely (roadmap §7.1).
- Mid-run state staging is refused by the engine (`ReadOnlyError`, `src/core/state.py:44`), so a
  demonstration cannot fake the passage of time.

## Scope
- Once M1 is resolved, one bounded, reproducible run through ordinary ticks:
  - predecessor dies;
  - the heir inherits;
  - the heir later dies;
  - the next heir inherits.
- Record the seed, starting state, relevant ticks/events, stable identities, authoritative state
  changes, and the provenance of each causal link.
- State the minimum run length and why it is causally sufficient for this claim.

## Out of Scope
- Claims about natural frequency, population-wide emergence, multi-generation arcs, player
  legibility, or a changed opportunity/decision (the closed-loop proof).
- Any change to the observer or evidence path.
- Fixing a newly found blocker beyond a small directly related defect permitted by repository risk
  rules. Anything larger becomes a follow-up ticket.

## Acceptance Criteria
1. A real two-hop run through ordinary ticks, with no mid-run staging, shows:
   - an authoritative OLD_AGE death (cause and tick) at each hop;
   - the correct heir at each hop;
   - chronological order;
   - identity continuity.
2. At least one effect of the first transition is carried into the second. For example, something
   the heir inherited is passed on again. The report states exactly which effect.
3. The report says precisely what this one run proves and what it does not.
4. If a new blocker appears, the ticket closes `BLOCKED_WITH_REASON`, with a reproducible failure
   and its narrowest known cause. It does not silently widen scope.

## Related Tickets
- TCK-20260927-NATURAL-AGING-OLD-AGE-DISPATCH-RACE (M1, hard dependency)
- TCK-20260904-LINEAGE-DEATH-DISPATCH

## Related Docs
- `docs/plans/systemic_world/roadmap.md` §7.1, §7.3 (gate questions 1 and 3)
- `docs/plans/systemic_world/first_wave_plan.md` M4a

## Related Stored Artifacts
None.

## Related Code Areas
`src/systems/lifecycle_systems/lifecycle.py` (succession dispatch). Evidence location only.

## Assumptions / Open Questions
- Inherited effects beyond inventory (feud blocker, dying wish) are internal cognition/strategic
  state. The run can verify they transfer, but they have no observable consequence today (roadmap
  §7.2). Do not present them as behavior changes.
- Untried alternative: a combat-caused second death. It may compose without M1, but that is
  unverified, and it would not satisfy the natural-aging claim.

## Implementation Notes
_Not started — owned by the implementation agent._

## Test Summary
_Not started._

## Files Changed
_Not started._

## Completion Summary
_Not started._

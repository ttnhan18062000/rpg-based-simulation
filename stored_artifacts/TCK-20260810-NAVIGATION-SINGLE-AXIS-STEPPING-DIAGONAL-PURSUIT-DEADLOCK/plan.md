---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260810-NAVIGATION-SINGLE-AXIS-STEPPING-DIAGONAL-PURSUIT-DEADLOCK
artifact_type: plan
tags: [combat, engine]
---

# Plan: TCK-20260810-NAVIGATION-SINGLE-AXIS-STEPPING-DIAGONAL-PURSUIT-DEADLOCK

## Approach
1. Confirm the mechanism analytically before touching the live kernel — cheaper and faster to
   validate a hypothesis against a standalone re-implementation of the exact tie-break rule.
2. Measure real corpus prevalence via a live, non-mocked kernel loop across multiple
   seeds/worlds BEFORE deciding whether to fix or document — per the ticket's own explicit
   two-branch scope (fix if non-trivial prevalence, document-and-defer if rare).
3. Based on the measured result, execute the appropriate branch (this ticket ended up on the
   document-and-defer branch).
4. Add direct test coverage for `get_next_step()` regardless of which branch — it had zero
   coverage before this ticket, a real, independent gap worth closing either way.

## Rejected Alternatives (would have applied only if prevalence had been non-trivial)
- **True 8-directional stepping** (move both axes when the offset is diagonal) — would have
  been the most direct fix, but not implemented given the real, measured low prevalence; noted
  here for a future ticket if prevalence is ever re-measured and found higher.
- **Anti-stalemate STALEMATE_BREAK detection** — the existing mechanic only fires on exact
  position-repeat (`entity.navigation.position` in `recent_positions`), not the
  oscillating-but-never-repeating pattern this deadlock produces (each entity DOES move every
  tick, just never converges) — would have needed its own extension, not a reuse, if pursued.

## Verification Plan
- 5 new direct unit tests for `get_next_step()`, covering normal-case convergence (both axes),
  the exact diagonal tie-break, single-sided-pursuit convergence (regression guard), and the
  confirmed mutual-diagonal deadlock (a characterization test).
- Full regression sweep across movement/world/combat/tactical/kernel/core/engine test suites.
- Real corpus prevalence measurement across 3 seeds × up to 8 worlds, 2000 ticks each — this
  measurement itself IS the primary deliverable of this ticket, not a secondary check.

---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260915-FACTION-IMPORTANCE-SIGNAL-INITIATIVE
phase: open
date: 2026-09-15
tags: [faction, cognition]
---

# TCK-20260915-FACTION-IMPORTANCE-SIGNAL-INITIATIVE

## Title
No real signal exists anywhere in this codebase for "how much does this entity matter to their
faction" — the faction-sentiment design (`TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION`)
wanted to weight sentiment by an acting entity's importance and found nothing strong enough to
carry it; this ticket scopes a real one, as its own initiative, not folded into sentiment

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The faction-sentiment design (`docs/mechanics/faction_war_drivers_proposal.md` §3.2) wanted a
leader's action to move faction relations categorically differently from a peasant's — good
realistic-fantasy politics, and a real, stated part of the user's own design intent. Every real
candidate signal was checked empirically and found unsupported:

- `public_reputation` (`SocialComponent.public_reputation`, range 0.0–2.0) is real and
  non-degenerate, but its spread is structurally a 2× ceiling-to-floor ratio and **confirmed not to
  widen with more play** — measured flat (`spread = max−min = 1.000` exactly) across ten checkpoints
  over a real 5000-tick run (`urban_political`, seed=42). Too weak to express categorical
  difference.
- `veterancy_rank` (`EntityState.identity.veterancy_rank`) has a real, live producer
  (`VeterancyService.process_points()`) but is **confirmed degenerate** in the same real run —
  every one of 49 alive entities at rank 0. The same "everyone is level 1" failure shape already
  found once this arc (the perceived-power draft's entity-level assumption).
- **No faction-leadership concept exists at all.** `FactionState` has no leader field.
  `ClanState.leader_entity_id` exists but is schema-only with zero real producers, and is a
  *different* concept (Clan, not Faction) besides. `EntityRole` has no `LEADER` tier.

**Decision**: rather than ship a near-invisible 2× multiplier as importance weighting, cut it from
the sentiment build and scope a real signal here, separately — genuine new design (who holds
standing in a faction, who speaks for it, how that's acquired), not a reuse of anything that exists
today.

## Scope
- **Scoping and design only in this ticket — no implementation.** Produce a real design for what
  "importance to a faction" means and how an entity acquires/loses it, checking first whether any
  further real signal exists that this investigation didn't already rule out (this ticket's own
  Request Summary already checked `public_reputation`, `veterancy_rank`, `EntityRole`,
  `ClanState.leader_entity_id` — start from "none of these work," not from scratch).
- Candidate shapes to weigh, not decided here: a formal leadership designation per faction (who is
  "the" leader, how selected/succeeded — mirrors `ClanState.leader_entity_id`'s own unbuilt intent,
  possibly the right place to finally wire it rather than inventing a parallel field); a continuous
  standing/rank score with real, wider range than `public_reputation`'s 2×; or a hybrid (a small
  number of named offices/ranks, each carrying a real weight).
- Explicitly check reuse-before-invention one more time before proposing new state: does any
  existing but not-yet-considered field (entity age/tenure, faction-territory-count per entity,
  wealth) have real, non-degenerate spread that could serve, before inventing a wholly new stat?
- Once a design direction exists, define exactly how it feeds
  `FactionSentimentDerivationPhase`'s `FACTION_SCALE_FACTOR` (`docs/mechanics/
  faction_war_drivers_proposal.md` §3.2.3) — a small, later wiring change once this initiative has
  its own real answer, not a redesign of sentiment itself.

## Out of Scope
- Building anything — this ticket produces a design/spec, matching the same "spec first, peer
  review, then code" sequencing already established for the sentiment design itself.
- The sentiment mechanism itself (`TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION`) — ships
  independently, with a uniform (unweighted) `FACTION_SCALE_FACTOR`, not blocked on this ticket.
- Loop #1 (`military_strength`) — a separate, unrelated open question, tracked on its own.

## Acceptance Criteria
- [ ] A real, evidence-backed design for an importance/leadership signal, checked against real
      corpus data for non-degenerate spread before being proposed (per the rule this whole
      investigation established: measure spread before leaning on any discriminator).
- [ ] Explicit reuse-before-invention check against any candidate not already ruled out by this
      ticket's own Request Summary.
- [ ] A concrete integration point into `FactionSentimentDerivationPhase`'s scale factor, described
      but not built.
- [ ] Findings brought to peer/user review before any implementation, matching this arc's
      established pattern for genuine new game design.

## Related Tickets
- `TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION` (the sentiment design that surfaced this
  gap and ships without it)

## Related Docs
- `docs/mechanics/faction_war_drivers_proposal.md` §3.2.4 (the investigation and decision to cut
  importance weighting from the sentiment build)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/core/state.py` (`FactionState`, `ClanState.leader_entity_id`)
- `src/core/models/social.py` (`SocialComponent.public_reputation`)
- `src/systems/lifecycle_systems/` (`VeterancyService`, for reference on why `veterancy_rank` is
  degenerate — a real producer with no real accrual pressure yet in the corpus)

## Assumptions / Open Questions
- Whether a real faction-leadership concept should be built from scratch or should finally wire
  `ClanState.leader_entity_id`'s own already-declared-but-unused intent is the central open
  question — not assumed either way here.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_

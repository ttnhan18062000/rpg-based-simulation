---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE
phase: open
date: 2026-09-15
tags: [combat, faction]
---

# TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE

## Title
The real ~58% combat-volume reduction from
`TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION`'s gate further starves two
already-thin downstream systems — faction pairwise tension accumulation and regional-trauma feeding
the world-boss maturity gate — neither of which this ticket fixes; filed to make the risk visible

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION` made a real, measured change: in
the reference scenario, only risk-accepted combat postures may now attack, cutting real
`execute_attack()` volume by 57.3% overall and 58.1% in the cross-faction subset specifically
(1960 -> 822 cross-faction attacks over 25 sample ticks). This is the correct, intended behavior —
"an entity assessing a threat and committing or withdrawing" per
`docs/mechanics/04_strategic_cognition.md` §13 — not a bug. But real combat is the sole fuel source
for two other systems this arc has already found to be thinly fed even at the pre-gate volume:

1. **Faction pairwise tension** (`FactionState.pairwise_tension`, built and fixed this same arc —
   see `TCK-20260915-SENTIMENT-HOSTILE-THRESHOLD-REACHABILITY`, closed, and
   `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`, still open). That investigation already
   found real cross-faction interaction volume in `frontier_living_world` to be a "lottery" (0.0 to
   0.65 across 5 seeds) even before this gate existed — HOSTILE was already found unreachable in
   realistic runs for reasons independent of this gate (see that ticket). A further ~58% cut to the
   cross-faction attack population that seeds `pairwise_tension` makes an already-thin fuel supply
   thinner, on top of an already-open reachability question.
2. **Regional trauma feeding the world-boss maturity gate**
   (`TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`, closed 2026-09-14). That
   investigation's own resolution already characterized the gate's real-world trigger rate as thin;
   a real cut to combat volume reduces the trauma-accumulating events that gate depends on further.

**The honest framing, not assumed to be a regression**: this gate did not create a new problem —
it made an existing one (both systems were always thinly fed relative to how often the design
intends them to trigger) more visible by removing volume that was previously masking it. "Put
combat back" is very unlikely to be the right fix for either system; the more likely honest
diagnosis is that both systems' own trigger conditions/thresholds were tuned against an inflated
combat baseline that included attacks the attacker's own risk assessment had already rejected.

## Scope
- **Faction chain — DONE, 2026-09-17, see `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`'s
  own 2026-09-17 addendum for the full measurement (not duplicated here — that ticket owns the
  fact, this one cites it).** Summary: the gate has no measurable effect on cross-faction interaction
  volume in `crowded_frontier`, `quest_dense_frontier`, or `hero_guild_routing` — not because its
  effect is small relative to an already-thin baseline, but because these worlds' real combat runs
  almost entirely through `CombatResolutionSystem.resolve_multi_attack()` (movement.py's incidental
  opportunity-attack mechanic), which never routes through `ActionRouter.execute_action()` and so is
  structurally ungated by this policy. The gate only measurably affects worlds like `metropolis`
  where the decision-driven `ATTACK`-intent path (which it does gate) is actually exercised.
- **Boss-gate chain**: re-check `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`'s own
  real trigger-rate measurement with this gate active, to see whether the gate's already-thin
  trigger rate drops further into practical unreachability. Still open — not touched by the
  faction-chain work above, per this ticket's own scope split.
- For whichever chain (or both) shows a real, material drop: propose a concrete fix scoped to that
  chain specifically (e.g., re-tuning that system's own threshold/window against the new baseline,
  not reverting this gate) — a design decision, not assumed here.
- **Do not revert or weaken `TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION`'s
  gate** as a "fix" for this ticket — that gate is confirmed-correct behavior on its own merits;
  this ticket is about whether two of its downstream consumers need re-tuning, not about undoing it.

## Out of Scope
- `TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION`'s own gate logic/placement —
  closed, not reopened by this ticket.
- Any other downstream consumer of real combat volume not named above — this ticket is scoped to
  the two specific chains peer flagged as already-known-thin before this gate existed.

## Acceptance Criteria
- Real, current post-gate measurement for both chains (cross-faction interaction volume;
  boss-gate trigger rate), not assumed from a single fixed-seed number.
  - Faction chain: DONE — see `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`'s own
    2026-09-17 addendum. No material drop (there was nothing left to drop — the gate doesn't apply
    to this world class's real combat mechanism at all).
- If either chain shows a material further drop: a scoped, evidence-backed proposal for that
  chain's own fix, filed as its own follow-up if it's more than a small tuning change.
- If neither chain shows a material further drop beyond what was already known: report that
  honestly and close without a code change. (Faction chain: reported, per above — no code change
  warranted for the gate/faction-chain relationship specifically.)

## Related Tickets
- `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` — groups this ticket (boss-gate half only, still
  open) with 4 others measuring the same broader causal chain
- `TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION` (created the volume reduction
  this ticket investigates the downstream effect of)
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (still open — the faction-chain half of
  this ticket's scope belongs here)
- `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY` (closed — the boss-gate half of this
  ticket's scope is a re-check of that ticket's own conclusion under the new baseline)
- `TCK-20260915-SENTIMENT-HOSTILE-THRESHOLD-REACHABILITY` (closed — established the pre-gate
  cross-faction volume was already a "lottery" across seeds)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` §13 (the spec this gate implements)
- `docs/plans/rpg_design_roadmap/faction_war_drivers_proposal.md` (carries the reachability
  investigation's own banner section)

## Related Stored Artifacts
_(none yet — filed as a finding, not yet investigated)_

## Related Code Areas
- `src/domains/faction/diplomatic_state_machine.py` (`pairwise_tension` consumer)
- `src/domains/faction/sentiment.py`
- Whatever module implements the world-boss maturity gate's own trauma-accumulation check (not yet
  re-identified in this ticket — see the boss-gate ticket's own Related Code Areas)

## Assumptions / Open Questions
- Not yet known whether either chain's post-gate volume is materially worse than its already-known
  pre-gate thinness, or whether the existing thinness already accounted for most of the practical
  unreachability regardless of this gate's further cut. Measure before concluding either way.

## Implementation Notes
**2026-09-17, faction chain resolved (half of this ticket).** See
`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`'s own 2026-09-17 addendum for the full
measurement. Boss-gate chain (the other half) not touched — still open.

## Test Summary
_(none yet — no code changed for the faction-chain half; boss-gate half not started)_

## Files Changed
_(none yet)_

## Completion Summary
_(not started)_

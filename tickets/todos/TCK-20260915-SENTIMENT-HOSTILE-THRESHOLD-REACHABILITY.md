---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260915-SENTIMENT-HOSTILE-THRESHOLD-REACHABILITY
phase: open
date: 2026-09-15
tags: [world, faction]
---

# TCK-20260915-SENTIMENT-HOSTILE-THRESHOLD-REACHABILITY

## Title
Post-fix, faction sentiment reliably reaches `TENSE` but has not been shown to reach `HOSTILE`
organically — a real 9000-tick run plateaus well short of the threshold; same reachability shape
as the maturity-gate and D-05 findings this week

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION` built `FactionSentimentService`, proved it
end-to-end, and in the process found and fixed a real defect: `DiplomaticStateMachine.compute_transitions()`
was reading `FactionState.tension_level` (an ambient, per-faction scalar) as a stand-in for
pairwise tension, so one faction's real fight with a single rival cascaded into blanket `HOSTILE`
with every faction in the world. That was fixed by introducing `FactionState.pairwise_tension`
(directed, per-rival) and re-scoping `compute_transitions()` to read it.

**Re-running the same acceptance scenario after the fix surfaced a new, honest finding**: the one
real interacting pair in a real 9000-tick `frontier_living_world` run (`bandit_company` <->
`wild_beast_pack`) reached `TENSE` and then **plateaued at `pairwise_tension = 0.418`**, never
approaching the `0.7` `HOSTILE` threshold, across the full run. A pre-fix run had reached `HOSTILE`
for this same pair, but that observation depended on the now-removed cascade (the aggregate scalar
being fed by more than just this one relationship) and is not representative of current, correct
behaviour. As of this ticket, **`HOSTILE` has not been demonstrated to be reachable through
ordinary play with the cascade fixed.**

This is explicitly the same shape as `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`
and the original D-05 finding in this ticket's own parent: a mechanism that is real, wired, and
documented as working, but that real play does not actually reach.

## Scope
- **Investigation first — do not assume the answer.** Determine, with real evidence (not
  extrapolation from the one 9000-tick run already done), whether the sentiment -> pairwise_tension
  escalation curve genuinely plateaus below `0.7` by design, or whether it is blocked by a further,
  as-yet-unidentified reachability gate (the same "not one big number, several small compounding
  gaps" shape found in the parent ticket's original investigation).
- Concretely check at minimum:
  1. Whether the plateau at `0.418` reflects the real rival pair's combat simply stopping (e.g. one
     side dispersing, moving apart, or being reduced in number) rather than a mechanical ceiling —
     i.e. is this an interaction-volume problem, not a formula problem?
  2. Whether `FACTION_SCALE_FACTOR` (`0.1`, provisional per the spec's own §3.2.3 note) is simply
     too small for realistic interaction volumes to cross `0.7` within a normal simulation horizon,
     and if so, what scale factor (or decay interval) would make `HOSTILE` reachable without making
     it trivial.
  3. Whether `decay_stale_sentiments()`'s periodic decay (`DECAY_FACTOR=0.9` every `DECAY_INTERVAL=500`
     ticks once stale) is actively working against sustained escalation for pairs whose combat comes
     in bursts rather than continuously — i.e. does the mechanism's own decay undercut its own
     escalation before a threshold can be crossed.
  4. Run across more than one corpus world/seed before concluding a general answer — this ticket's
     parent found world-specific behavior (`urban_political` vs `frontier_living_world`) earlier in
     the same investigation; don't generalize from a single world again.
- Out of scope: re-opening the cascade fix itself, re-litigating the additive-field-vs-rename
  decision, or building loop #1 (`military_strength`) / `WAR` reachability — those remain separately
  scoped.

## Out of Scope
- The `military_strength` / `WAR`-reachability gap (loop #1) — already explicitly deferred by the
  parent ticket's own acceptance bar; not this ticket's concern.
- Re-deriving or redesigning the sentiment formula from scratch — this is a reachability
  investigation into the *existing* built mechanism, not a request to re-propose it.
- The importance-weighting cut (`TCK-20260915-FACTION-IMPORTANCE-SIGNAL-INITIATIVE`) — separate,
  already filed.

## Acceptance Criteria
- A real, evidence-backed answer (not assumption) to: is `HOSTILE` reachable through ordinary play
  post-fix, and if not yet observed, what specifically blocks it (interaction volume, scale factor,
  decay working against escalation, or something else)?
- If a genuine gap is found and a fix is proposed, it must be reviewed before being built — same
  sequencing discipline as the parent ticket (design/tuning changes go to peer first).
- If the honest answer is "the mechanism is correct and `HOSTILE` requires sustained real conflict
  this world's content doesn't produce, and that's fine" — that is an acceptable, valid outcome,
  as long as it's stated plainly rather than left ambiguous.

## Related Tickets
- `TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION` (parent — built sentiment, found and fixed
  the tension_level cascade defect, surfaced this finding)
- `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY` (same reachability-gap shape, done)
- `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` (sibling reachability gap in the same faction
  subsystem, still open)
- `TCK-20260915-FACTION-IMPORTANCE-SIGNAL-INITIATIVE` (separate, scoping-only)

## Related Docs
- `docs/plans/rpg_design_roadmap/faction_war_drivers_proposal.md` (§3.2, §4 — the sentiment spec
  and its acceptance bar; carries the post-build finding banner this ticket was filed from)

## Related Stored Artifacts
_(none yet — filed as a finding from the parent ticket's own build/verification, not yet
investigated)_

## Related Code Areas
- `src/domains/faction/sentiment.py` (`FactionSentimentService` — `FACTION_SCALE_FACTOR`,
  `DECAY_INTERVAL`, `DECAY_STALENESS_THRESHOLD`, `DECAY_FACTOR`)
- `src/domains/faction/diplomatic_state_machine.py` (`compute_transitions()` — the `0.7` `HOSTILE`
  threshold read against `pairwise_tension`)
- `src/core/state.py` (`FactionState.pairwise_tension`)

## Assumptions / Open Questions
- Not yet known whether this is a tuning problem (raise `FACTION_SCALE_FACTOR` or lower the
  threshold) or a genuine second reachability gate. Do not assume either before measuring.

## Implementation Notes
_(none — filed as a finding, not yet investigated)_

## Test Summary
_(none yet)_

## Files Changed
_(none yet)_

## Completion Summary
_(not started)_

---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260914-REGION-DANGER-SEEN-COLOCATION-SCAR-CONJUNCTION-UNPROVEN
phase: open
date: 2026-09-14
tags: [cognition, investigation]
---

# TCK-20260914-REGION-DANGER-SEEN-COLOCATION-SCAR-CONJUNCTION-UNPROVEN

## Title
Does `region_danger_seen`'s full synthesis (actor co-located with an active scar in the same region a location lead resolves to) ever complete under realistic conditions? Not yet known.

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING` fixed the dead `region_id`-string
comparison in `src/domains/information/phase.py`'s `region_danger_seen` synthesis and
`src/domains/information/contradiction.py`'s `BeliefContradictionService.detect()`, replacing it
with a real coordinate-to-region resolution (`resolve_location_lead_region_id()`). A real 500-tick
`frontier_living_world` corpus measurement (seed 42, 49 entities) run as part of closing that ticket
proved the fix's own machinery is genuinely live in the production pipeline:

- `GuildAction.visit()` produced 4 visits / 8 location leads (matches independently-known evidence).
- Every one of the 300 untested VAGUE/APPROXIMATE location leads encountered across the run
  resolved its coordinate `detail` to a real region: **300/300**, zero resolution failures.

But the *full* `region_danger_seen` synthesis needs one more thing beyond a resolved region: the
**observing actor's own current region must equal the lead's resolved region, at a tick where that
region also has an active local scar** (`InformationBeliefPhase.apply()`'s `has_active_scar` check,
`src/domains/information/phase.py` around the `region_danger_seen` branch). That specific
conjunction — actor co-located with an actively-scarred region matching one of its own untested
leads — **never occurred once** in the 500-tick/49-entity run.

This ticket exists because that gap was left as an open, unresolved question when the prior ticket
closed — not because a fix has already been chosen. **The components are proven; the conjunction is
not.** Three genuinely different explanations are all still plausible, and they call for different
responses:

1. **The precondition is real and simply rare** — nothing is wrong, this branch just fires
   infrequently in practice, and that's an acceptable, working design.
2. **The tick budget/entity count in the measurement run was too short to observe it** — a longer
   run, or a run against a world with more scars/denser guild-visit traffic, might show it firing
   normally.
3. **The conjunction is effectively unreachable given how scars and leads are actually produced in
   real corpus worlds** (e.g. scars and a given actor's own unresolved location leads may almost
   never land in the same region by construction) — in which case this is another dormant code path
   in the same family as the ones already found and fixed this cycle (raid mobs, guild quest
   generation, the region_id convention itself), just one level deeper.

Nobody knows which of these is true yet. This ticket is the investigation, not a fix.

## Scope
- Determine, with real evidence (not assumption), which of the three explanations above actually
  holds — or narrow to a more precise one if the real answer doesn't cleanly match any of them.
- Candidate approaches (not mandated, to be chosen based on what's cheapest/most conclusive):
  - Run longer and/or across more/varied corpus worlds, instrumenting the same three counters used
    in the prior ticket's measurement (`candidate_location_leads`, `detail_resolved_to_a_region`,
    and a new `region_match_condition_true` / `has_active_scar` pair), to see if the conjunction
    ever fires given enough ticks/worlds.
  - Independently examine how local scars are actually created (`state.local_scars`'s real
    producers) and how a given entity's own location leads' resolved regions relate to where that
    same entity tends to be positioned, to reason about whether the conjunction is structurally
    rare vs. structurally near-impossible, without needing an arbitrarily long simulation run.
- Report the real answer, with evidence, as this ticket's own Completion Summary — whichever of the
  three (or other) explanations it turns out to be.

## Out of Scope
- Choosing or building a fix. If the investigation concludes explanation 3 (effectively
  unreachable), a *separate* follow-up ticket should propose what to do about it — not decided here.
- Re-litigating whether `resolve_location_lead_region_id()` itself works — already proven (300/300)
  by the prior ticket's own measurement and is not in question here.
- The broader Convention-1-vs-3 (`LeadState.detail` typed-shape) design question from
  `TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING`'s own Out of Scope — unrelated to this
  ticket's own narrower conjunction question.

## Acceptance Criteria
- [ ] A real, evidence-backed answer to which of the three explanations (rare-but-real,
      budget-too-short, effectively-unreachable) actually holds, or a more precise fourth
      explanation if the real evidence doesn't fit any of the three.
- [ ] The answer is backed by real measurement or real code-path analysis, not restated assumption.
- [ ] If the answer is "effectively unreachable," a follow-up ticket is filed (not built here).
- [ ] If the answer is "rare but real" or "budget too short," that's recorded as the resolution —
      no code change required in either case.

## Related Tickets
- `TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING` (done — the fix that made this
  conjunction's own components reachable and produced the measurement that surfaced this gap)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` § "Leads (Knowledge)" (declares the `detail` coordinate
  contract this conjunction's own inputs depend on)
- `docs/parity_ledger/strategic_cognition.yaml` `STRAT-230` (the parity entry covering the
  `lead_contradiction`/`region_danger_seen` mechanism this ticket investigates)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/domains/information/phase.py` (`InformationBeliefPhase.apply()`'s `region_danger_seen`
  synthesis branch — the `has_active_scar` / region-match conjunction under investigation)
- `src/domains/information/lead_location.py` (`resolve_location_lead_region_id()` — already proven
  correct, not itself in question)
- `src/town/guild.py` (`GuildAction.visit()` — the real producer of the location leads that feed
  this conjunction)
- `state.local_scars` real producers (not yet enumerated in this ticket — first investigation step)

## Assumptions / Open Questions
- This entire ticket *is* the open question. No assumption about which of the three explanations is
  correct should be carried into the investigation.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_

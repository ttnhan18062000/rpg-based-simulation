---
status: active
layer: simulation
authority: P1
audience: agent
tags: [content, architecture]
---

# Epic Plan — RPG Design Roadmap, Milestone 7: Simulation Quality Pillar Integration

**Tracking ticket:** `TCK-20260823-EPIC-RPG-M7-SIMQ-INTEGRATION` (not yet created — scope-only, per
`docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`)
**Source:** `docs/simulation_quality/quality_scoring_contract.md` §1 (Purpose &amp; Scope, 3 stated goals
including regression detection) and §5 (the 10 real pillars), cross-referenced against
`docs/brainstorm/design_merit_scorecard.html`'s Pillar Reach axis for all 65 ideas.
**Gate:** M1 through M6. Deliberately a follow-up epic, not per-milestone acceptance criteria — see
Problem below for why.

## Problem

SimQ scores a *running* simulation's health per pillar by counting real event types
(`belief_updated`, `route_selected`, `commitment_complete`, etc.) against data-driven signal rules. One of
its three stated goals is regression detection — catching when a code change silently kills a subsystem. If
Milestones 1 through 6 ship 65 ideas' worth of new mechanisms and new event types without any of them ever
being registered into SimQ's per-pillar signal rules, that goal fails silently for all of it: SimQ would
have no rules telling it to even look, so a new subsystem quietly breaking later would go completely
undetected by the one system built specifically to catch exactly that.

**Why this is a follow-up epic and not 6 sets of per-milestone acceptance criteria:** designing exact
signal rules before an idea's event types exist would be speculating against code that hasn't been written.
Distributing "also register this with SimQ" across 6 separate epics also risks it being quietly skipped in
whichever epic is under the most time pressure — a single, consolidated sweep after the mechanisms actually
exist is both more honest about sequencing and harder to accidentally miss piece by piece.

## Scope (not yet broken into child tickets)

1. **Expand Pillar Reach from a count into named pillars, per idea.** The Merit Scorecard's Pillar Reach
   axis currently records how many of the 10 real pillars an idea affects (e.g. "5/10") but not which ones
   by name. This epic's first real task is going back through all 65 ideas and naming the specific pillar(s)
   each one should register with — the count alone isn't enough to drive an actual audit.
2. **For each shipped idea, confirm its real event types exist and are named.** Once M1-M6 tickets have
   landed, this is a direct read of what got built — not a redesign, an inventory.
3. **Cross-check every named event type against SimQ's existing per-pillar signal tables**
   (`quality_scoring_contract.md` §5). For each event type with no existing rule, author one: a signal, a
   delta, and a tag, following the exact shape already used for the 10 pillars' existing rules — reuse the
   pattern, don't invent a new one.
4. **Re-run SimQ's own calibration workflow** (the real precedent: `TCK-20260628-SIMQ-E7-CALIBRATE`) against
   at least one corpus profile exercising the new content, to confirm the new signal rules produce a
   meaningful grade signal rather than a flat, uninformative score.
5. **Explicit completeness check, not just a best-effort sweep.** Cross-reference the final rule set against
   step 1's named-pillar list for all 65 ideas — every idea Pillar Reach says should touch a pillar needs a
   traceable rule or an explicit, written reason it doesn't (e.g. a pure governance/investigation idea like
   9 or 15-19 legitimately has nothing to register). This is the "make sure we don't miss any" step; it's a
   checklist against a known-complete list, not a scan for whatever happens to be found.

## Out of Scope

- Designing any signal rule before the event type it covers actually exists in shipped code.
- The metamorphic-lab balance-testing work (idea 37's pilot, M2/M3's acceptance gates in their own epics) —
  a different system, testing content/balance decisions before they ship, not runtime health after.
- Anything from Milestones 1 through 6's own functional scope — this epic only touches SimQ's scoring
  rules, never the mechanisms themselves.

## Acceptance Signal

- All 65 ideas have a named-pillar mapping (step 1), not just a count.
- Every real event type introduced by M1-M6 either has a traceable SimQ signal rule or an explicit,
  written reason it's intentionally excluded — no silent gaps.
- A real calibration run (step 4) exists and its results are recorded, not just "rules were written."

## Open Questions

- Should this epic run once, after all of M1-M6 ships, or could it reasonably split into two passes (after
  M1+M2+M3, then again after M4+M5+M6) to catch regressions earlier rather than waiting for the whole
  roadmap? Not decided here — leaning toward one pass for now, per the "don't miss any" instruction driving
  this epic's existence, but worth revisiting once M1-M3 actually ship and there's a real sense of how long
  that takes.

## References

- `docs/simulation_quality/quality_scoring_contract.md` — §1 Purpose &amp; Scope, §5 The 10 Pillars, §4.8
  Data-Driven Scoring Weights
- `docs/brainstorm/design_merit_scorecard.html` — Pillar Reach axis, all 65 ideas
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`

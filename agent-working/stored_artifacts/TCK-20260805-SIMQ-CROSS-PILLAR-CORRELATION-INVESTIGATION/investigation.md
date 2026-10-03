---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-CROSS-PILLAR-CORRELATION-INVESTIGATION
artifact_type: investigation
tags: [simulation-quality, calibration]
---

# investigation.md — TCK-20260805-SIMQ-CROSS-PILLAR-CORRELATION-INVESTIGATION

## Method

Analyzed all 76 real `data/calibration/*/quality_report.json` reports from this session's earlier
full-corpus run. For every report, extracted each pillar's `worst_events` (negative-delta entries
only, real tick values — not estimated). For every pillar pair present in the same report, checked
whether any of their negative-event ticks fell within a 10-tick window of each other (a plausible
"something broke around the same moment" signal). Computed the overlap rate per pillar pair across
all reports where both pillars had at least one negative event.

## Finding: no real cross-pillar correlation exists in the current corpus

**51 of 76 reports (67%) have 2+ pillars showing negative worst_events** — correlated degradation
is at least structurally possible to observe. But of all pillar pairs with enough sample size (≥3
reports) to be meaningful, only one showed a high overlap rate:

| Pillar pair | Reports with overlap | Reports with both negative | Rate |
|---|---|---|---|
| PROGRESSION ↔ SOCIAL | 13 | 16 | **81%** |
| COMBAT ↔ WORLD | 1 | 4 | 25% (too small a sample to mean anything) |
| COMBAT ↔ NARRATIVE | 1 | 10 | 10% |
| COMBAT ↔ PROGRESSION | 0 | 25 | 0% |
| PROGRESSION ↔ WORLD | 0 | 21 | 0% |
| (4 more pairs, all 0%) | | | |

**The 81% PROGRESSION↔SOCIAL rate is a methodological artifact, not a real signal — verified by
tracing the actual events, not accepted at face value:**

1. `progression_plateau_detected` (PROGRESSION's negative signal) fires at **exactly tick 51 in
   every single report it appears in, corpus-wide** — confirmed by collecting the distinct tick
   values across all 76 reports: `{51}`. This is a fixed scoring-rule tick-gate ("XP gain rate
   dropped to zero after tick gate"), not an emergent world-state event. It cannot meaningfully
   "correlate" with anything since it never varies.
2. `contract_expired_offer` (SOCIAL's negative signal, in the affected worlds) fires on **nearly
   every tick of the run** — one sampled report (`frontier_living_world_seed42_200t`) shows 99
   negative events spanning ticks 14–152 with almost no gaps. Any pillar with even one negative
   event anywhere in a ~140-tick window would register a false "overlap" against this density,
   regardless of any causal relationship.

Together, a fixed constant (tick 51) colliding with a near-continuous event stream produces a
spurious 81% co-occurrence rate that has nothing to do with compound failure — it is guaranteed by
the density of one signal, not evidence of the two pillars breaking together.

**No other pillar pair shows a rate above 25%, and all pairs above 0% have samples too small (≤10
reports) to distinguish from chance.**

## Conclusion (AC1)

**No meaningful cross-pillar correlation exists in the current 76-scenario corpus.** This is a
real, evidenced negative result, not an absence of looking. Building a cross-pillar correlation
detection layer today would have nothing real to detect — it would either surface artifacts like
the PROGRESSION↔SOCIAL false positive above, or stay silent. Per the ticket's own AC1, this
finding is conclusive enough to close as "investigated, no build" (option (b) in the ticket's
Out of Scope framing) — not because correlation is impossible in principle, but because this
corpus's actual failure modes (documented across this session's other 5 tickets: WORLD anchor
staleness, ECONOMY's zero-harvest chain, cognition-graph capture gating) don't currently produce
compound, temporally-clustered signatures worth detecting.

**Revisit if:** the corpus composition changes substantially (e.g. a new stress-tier world
deliberately designed to produce cascading failures across pillars), or if a future incident is
observed where a developer manually notices correlated degradation the current tooling missed.

## Docs Requiring Update
- `docs/simulation_quality/extension_points.md`: axis 11 needs this finding recorded (currently
  says "investigation tracked in this ticket").

## Parity Ledger Overlap
None — this is a SimQ analysis-layer question, not a Mechanics-Bible-tracked behavior.

## Prior Work
None — first investigation on this axis.

## Risks and Open Questions
None outstanding. The negative finding is well-evidenced (root-caused the one apparent signal down
to specific event mechanics, not just a low p-value).

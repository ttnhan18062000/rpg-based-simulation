---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-SIMQ-LONG-RUN-LIFECYCLE-OBSERVATION-TIER
phase: done
date: 2026-08-08
tags: [simulation-quality, calibration]
---

# TCK-20260808-SIMQ-LONG-RUN-LIFECYCLE-OBSERVATION-TIER

## Title
62.5% of the real SimQ calibration corpus (`grade_anchors.json`) runs only 200 ticks — a window
this session's own real data shows is too short to observe real entity lifecycle; establish a
first-class long-run (1000-5000 tick) observation tier rather than treating length as incidental

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Per the user's own explicit concern: lifecycle observation needs to run "long enough... at least
1000 to 5000 [ticks]... to observe the real lifecycle, not a slightly start and end soon." This
is not a vague preference — this session's own real, measured data confirms it directly.

**Real, current corpus composition** (`tests/simulation_quality/fixtures/grade_anchors.json`, 80
total run_keys): **50 (62.5%) use 200 ticks**, 12 use 500, 12 use 1000, 6 use 2000. The large
majority of the "official" calibration corpus — the numbers `grade_anchors.json`/`eval_matrix_
results.md` and every SimQ pillar grade are drawn from — uses the shortest available window.

**Real evidence this window is too short for lifecycle-quality signals specifically**
(`TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION`'s own real tick-length sweep,
`sandbox_world`/seed 42):

| Ticks | `dominant_shape_share` | `phase_coverage` mean |
|---|---|---|
| 200 | 0.500 | 0.239 |
| 500 | 0.611 | 0.378 |
| 1000 | 0.190 | 0.533 |
| 2000 | 0.179 | 0.557 |

`dominant_shape_share` (the population-diversity signal) is **artificially inflated by more than
3x** at 200-500 ticks compared to its own stabilized value at 1000+ — a short run doesn't just
give less data, it gives a **systematically wrong** answer to "is this population diverse."
`phase_coverage` more than doubles from 200 to 2000 ticks and is still rising at 2000 — meaning
even the *longest* tick-length already in real use in this corpus (2000, only 6/80 run_keys)
hasn't necessarily plateaued. Separately, `capability_growth_stalled` (a real PROGRESSION
detector) structurally cannot fire below its own 300-tick window — meaning **50/80 real
calibration run_keys (200 ticks) cannot ever produce this signal at all**, not because nothing is
wrong, but because the detector is mathematically unreachable at that length.

**This is not a call to lengthen every existing calibration run** — 200-tick runs likely still
serve their own original purpose (fast regression/smoke checks against `grade_anchors.json`'s own
existing baselines) and re-lengthening them would be a large, disruptive recalibration with its
own real cost. The proposal is additive: establish long-run observation (1000-5000 ticks) as a
**first-class, separately-tracked SimQ corpus tier**, specifically for lifecycle/diversity
questions that are provably unreliable at the corpus's current default length — not a fix to the
whole corpus, a new, explicit lane alongside it.

## Scope
1. **Investigate**:
   - Confirm exactly which SimQ signals/detectors (beyond `capability_growth_stalled`'s 300-tick
     window and the lifecycle-score tool's own `clustering_reliable_tick_threshold: 1000`) have a
     real, structural minimum-tick requirement — survey `quality_scoring_contract.md`'s own §4.7
     loop-detection window (200 events, not ticks — a related but distinct concept, don't
     conflate) and any other tick-gated detector.
   - Confirm the real cost of a 5000-tick run — this session's own tick-length sweep only tested
     up to 2000 ticks (59.1s for `sandbox_world`, a small world); estimate/measure real runtime
     for a representative sample of larger corpus worlds (e.g. `frontier_extended`,
     `simq_scale_stress_seed42`) at 5000 ticks before committing to that as a real target, not an
     assumed-safe number.
   - Decide whether this tier should be its own new `corpus_registry.yaml` tier value (alongside
     `unit`/`end_to_end`/`stress`/`regression_baseline`, per `docs/simulation_quality/
     corpus_tier_taxonomy.md`) or a cross-cutting run-length dimension independent of tier.
2. **Plan**: design the exact new tier — which worlds get long-run anchors (likely a subset, not
   all 20 — probably the same worlds already used for cross-world comparison, e.g. the density-
   correlation sample from `TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION`), and whether these
   new anchors feed `grade_anchors.json` directly or a separate, lifecycle-specific fixture.
3. **Implement**: author the new long-run anchors/fixtures, wire them into whatever repeatable
   check (likely `tools/entity_lifecycle_score.py` runs, not full SimQ pillar re-scoring) makes
   this tier a standing, re-runnable observation point rather than a one-off.

## Out of Scope
- Re-running or re-lengthening the existing 50 short-tick `grade_anchors.json` entries — those
  serve a different, already-working purpose (fast regression checks); not touched here.
- Any change to the SimQ pillar scoring formulas themselves (`quality_scoring_contract.md`'s own
  weights/deltas) — this ticket is about observation *length*, not the metrics computed at that
  length.
- Resolving any of the substantive findings the full-corpus 1000-tick run already surfaced
  (growth-economy flatness, HERO underperformance, wilderness_survival) — those are tracked in
  their own sibling tickets; this ticket is about making long-run observation a standing,
  repeatable practice, not re-investigating what one long run already found.

## Acceptance Criteria
- [ ] investigation.md surveys all real tick-gated detectors, not just the 2 already known
- [ ] investigation.md reports real, measured runtime cost at 5000 ticks for at least 2
      representative real corpus worlds
- [ ] plan.md specifies the exact new tier/fixture shape and which worlds it covers
- [ ] A real, repeatable long-run observation mechanism exists (not a one-off script run) —
      re-runnable via a documented command, producing durable output
- [ ] `docs/simulation_quality/corpus_tier_taxonomy.md` updated if a new tier value is added
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS, TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION
  (the tool and the real tick-length sweep data this ticket is grounded in — both DONE)
- TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE,
  TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF,
  TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS (sibling findings from the same
  full-corpus run this tier would make more routinely observable going forward)

## Related Docs
- `docs/simulation_quality/corpus_tier_taxonomy.md` (existing tier definitions to extend or
  cross-reference)
- `docs/simulation_quality/quality_scoring_contract.md` §4.7 (a related but distinct
  window/threshold concept — loop-detection window is measured in scored events, not ticks; don't
  conflate the two when writing this ticket's own investigation)
- `docs/simulation_quality/entity_lifecycle_score.md` (the real tick-length findings this ticket
  formalizes into a standing practice)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tests/simulation_quality/fixtures/grade_anchors.json` (the real corpus composition this
  ticket's own investigation quantified — 62.5% at 200 ticks)
- `tools/entity_lifecycle_score.py`, `tools/calibrate_simq.py` (the real tools this new tier would
  run through)
- `config/simulation_quality/entity_lifecycle_weights.yaml`
  (`clustering_reliable_tick_threshold: 1000` — the real, measured basis for this ticket's own
  minimum-length reasoning)

## Assumptions / Open Questions
- Whether 5000 ticks is actually achievable in reasonable wall-clock time for the corpus's
  larger worlds — not assumed; Investigate must measure, not extrapolate from the 2000-tick data
  already on hand.

## Implementation Notes
Subagent spawning unavailable this session (200/200 cap) — self-performed throughout.

Real, corpus-wide survey (`docs/simulation_quality/quality_scoring_contract.md`, not assumed)
found 7 tick-gated SimQ scorer rules beyond the 2 already known — real max 500 ticks
(`gold_frozen`, `emergence_dormant`), below `entity_lifecycle_score.py`'s own 1000-tick
`clustering_reliable` threshold, which remains the real binding constraint. §4.7's own
200-scored-event loop window is a distinct, related concept (confirmed via direct doc read, not
conflated as the ticket's own Related Docs note warned against).

Real 5000-tick runtime measured (not assumed) on the corpus's 2 largest worlds:
`frontier_extended` (59 entities) and `simq_scale_stress_seed42` (68 entities), both ~250s,
`dropped_count=0`. Confirmed 5000 ticks is real, achievable cost for a periodic (not CI) tier.

Decided run length is a cross-cutting dimension, not a new `corpus_registry.yaml` tier value —
same relationship the immediately-preceding sibling ticket's own `archetype` field has to `tier`.
Built `tools/simq_long_run_observation.py` reusing `entity_lifecycle_score.py`'s own lean,
non-fragile run-driver (not `calibrate_simq.py`'s `_run_engine()`) so the Kernel runs exactly once
per world, deriving both the real SimQ pillar report and the entity-lifecycle score from the same
run — never touching `grade_anchors.json` or any pillar-scoring formula.

## Test Summary
`pytest tests/tools/test_simq_long_run_observation.py tests/tools/test_entity_lifecycle_score.py
tests/tools/test_corpus_registry.py -q` — 39/39 passed (5 new tests, including a spy-based check
confirming the engine drives exactly once per world, not twice).

## Files Changed
- `tools/simq_long_run_observation.py` — new
- `tests/tools/test_simq_long_run_observation.py` — new
- `Makefile` — new `simq-long-run-lifecycle-observation` target
- `docs/simulation_quality/corpus_tier_taxonomy.md`, `docs/simulation_quality/
  entity_lifecycle_score.md` — updated

## Completion Summary
Established the long-run observation tier as a real, standing, re-runnable mechanism grounded in
measured data at every decision point — the tick-gated-detector survey, the 5000-tick cost
measurement, and the tier-vs-cross-cutting-dimension design choice. All 5 of the ticket's own
Acceptance Criteria items satisfied. Per the user's own explicit follow-up instruction, the actual
6-world observation run (and the deep investigation + epic scoping that follows it) is the next
concrete action after this ticket's own close, not folded into it.

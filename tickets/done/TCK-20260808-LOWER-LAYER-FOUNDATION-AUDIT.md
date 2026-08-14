---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260808-LOWER-LAYER-FOUNDATION-AUDIT
phase: open
date: 2026-08-08
tags: [simulation-quality, documentation]
---

# TCK-20260808-LOWER-LAYER-FOUNDATION-AUDIT

## Title
Audit the real state of the "lower layer" entity lifecycle foundation (VITALS, EXPLORATION,
GROWTH_PROGRESSION, COMBAT, baseline STRATEGY_COGNITION, CONCLUSION_DEMOGRAPHIC) — logic, SimQ
scorers, lifecycle metrics, and events — before any ECONOMY/SOCIAL/NARRATIVE_QUEST work, per the
user's own explicit design priority

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Per the user's own explicit direction: the simulation's core design intent is goal-driven,
cognition-based entities exploring a non-hardcoded, personality/RNG-biased route toward power —
but ECONOMY and SOCIAL are inherently complex and should only be built up once the lower layers
(vitals, exploration, growth, combat, baseline cognition, and the demographic
birth/death/conclusion cycle) are confirmed solid. This ticket audits the real, current state of
those lower layers — code, SimQ scorers, `entity_lifecycle_score.py` metrics, and real event
coverage — and documents the findings, rather than assuming the foundation is fine and building
upward.

## Scope
1. **Investigate**: for each lower-layer `lifecycle_phase_bucket` (VITALS, GROWTH_PROGRESSION,
   EXPLORATION, COMBAT, STRATEGY_COGNITION's flag-free baseline, CONCLUSION_DEMOGRAPHIC), trace:
   - the real trigger events (`config/simulation_quality/entity_lifecycle_weights.yaml`) and their
     real emission code paths
   - the corresponding SimQ scorer(s) and scoring weights
     (`config/simulation_quality/scoring_weights.yaml`, `docs/simulation_quality/
     quality_scoring_contract.md`)
   - real, observed reachability this session's own kernel-level investigations already
     established (not re-deriving from scratch — citing the real evidence already gathered)
   - known real bugs/gaps: fixed this session vs. still open, disclosed
2. **Document**: write a real audit doc capturing the above, following the existing
   `docs/audits/D0N_*.md` convention, so this becomes the durable reference for future
   lower-layer work before any ECONOMY/SOCIAL push.

## Out of Scope
- Fixing the still-open `growth_trajectory` pacing gap (already filed:
  `TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE`) — this ticket documents it, doesn't fix it.
- Any ECONOMY/SOCIAL/NARRATIVE_QUEST work — explicitly deferred by the user's own stated priority
  until the lower layers are confirmed solid.
- Re-running new kernel probes — this audit is grounded in real evidence already gathered this
  session (cited with its own ticket provenance), not fresh instrumentation.

## Acceptance Criteria
- [x] Real trigger events and emission code traced for every lower-layer bucket
- [x] Real SimQ scorer/weight behavior documented per bucket
- [x] Known real gaps (fixed and open) disclosed honestly, not glossed over
- [x] Audit doc written and added to `docs/REGISTRY.yaml` via the standard doc-registry regen

## Related Tickets
- TCK-20260808-ENTITY-LIFECYCLE-IMPROVEMENT-EPIC (parent context — this audit synthesizes that
  epic's own real findings into a durable foundation reference)
- TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE (the real, still-open lower-layer gap this
  audit documents but does not fix)
- TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD, TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION,
  TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-ATTACK-CREDIT-GAP, TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP,
  TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING (real evidence sources this audit cites)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md`
- `docs/simulation_quality/event_type_coverage.md`
- `docs/simulation_quality/entity_lifecycle_score.md`, `docs/guides/entity_lifecycle_score.md`
- `docs/audits/D06_longrun_health.md`, `D07_content_depth.md`, `D20_simq_quality_status_review.md`
  (existing audit convention this doc follows)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `config/simulation_quality/entity_lifecycle_weights.yaml`
- `config/simulation_quality/scoring_weights.yaml`
- `src/simulation_quality/scorers/`
- `src/observability/event_extractor.py`, `event_shapers.py`

## Assumptions / Open Questions
None — this is a synthesis of real evidence already gathered this session, not new investigation
requiring open questions.

## Implementation Notes
Subagent spawning unavailable this session (200/200 cap) — self-performed throughout.

Pulled the real, authoritative `lifecycle_phase_buckets` event mapping directly from
`entity_lifecycle_weights.yaml` (not assumed/recalled), the real `event_type_coverage.md` state
(84 scored events, 0 real emission/translation gaps at the "does it reach a scorer" level —
Certified Level 1, last verified 2026-07-04+incremental updates through 2026-08-08), and the real
`COMBAT`/`PROGRESSION` scoring weights directly from `scoring_weights.yaml`. Combined with this
session's own already-established real kernel-level findings (opportunity-attack dominance, growth
stall ratios, rebirth unreachability, IDENTITY hard ceiling, mid-run metadata gap fix) to write
`docs/audits/D21_entity_lifecycle_foundation_layers.md`.

Key finding structure: distinguishes "is the event wired to a scorer" (SimQ's own event-coverage
audit — this is in excellent shape, 0 real gaps) from "does the event actually fire in real
gameplay at meaningful volume" (this session's own kernel-level finding — several lower-layer
events are wired correctly but never/rarely fire in practice, most notably 5 of 6 GROWTH_PROGRESSION
sub-events). This distinction is the audit's own central contribution — the two prior audits
answer different questions and neither alone tells you whether the foundation is solid.

## Test Summary
Documentation-only ticket — no code changed, no tests applicable. Verified the audit doc's own
citations (event names, weight values, bucket membership) against the real source files it quotes
(`entity_lifecycle_weights.yaml`, `scoring_weights.yaml`, `event_type_coverage.md`) rather than
recalled from memory.

## Files Changed
- `docs/audits/D21_entity_lifecycle_foundation_layers.md` (new)

## Completion Summary
Real, evidence-grounded audit of the lifecycle foundation layers written and committed, directly
serving the user's own stated priority: confirm/document the lower-layer state before any
ECONOMY/SOCIAL work. Central finding: SimQ's own event-to-scorer wiring is essentially complete
(0 real gaps), but real in-game reachability of several GROWTH_PROGRESSION sub-events remains the
one significant open lower-layer gap — already filed as its own follow-up
(`TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE`), not fixed here.

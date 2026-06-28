---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-E-PERSONALITY-CALIBRATION
phase: open
date: 2026-06-28
tags: [epic, personality, ocean, calibration, long-run, p3, deferred, blocked]
---

# TCK-20260628-E-PERSONALITY-CALIBRATION

## Title
Epic: Personality → Long-Run Behavior Calibration at 1,000+ ticks

## Status
BLOCKED

## Tier
epic

## Type
feature

## Priority
P3

## Request Summary
OCEAN traits, mood, and grudges are all implemented locally. Per-entity personality
snapshots are now captured in LIGHT observability mode (P2O — done). No metric yet
proves personality produces distinct long-run life arcs vs. one-off route nudges.

**Gate conditions:**
- P0-A fix: DONE ✓ (adventure pipeline now active by default)
- D05-style audit run at 1,000+ ticks: NOT YET DONE ⛔ — requires running a
  behavioral audit with personality observability enabled.

**Status: BLOCKED pending D05-style 1,000+ tick audit run.**

## Block Resolution

Run a D05-style behavioral audit with P2O personality observability (LIGHT mode):
```
make sim-run TICKS=1000 SEED=42 OBS_MODE=LIGHT
```
Analyze per-entity personality snapshots vs. behavioral route diversity:
- Do high-Openness entities select more varied route families?
- Do high-Conscientiousness entities abandon projects less?
- Do high-Neuroticism entities show elevated threat urgency responses?

Once audit data is available, identify calibration gaps and scope child tickets.

## Scope (preliminary)
1. Run D05-style audit at 1,000 ticks with LIGHT observability.
2. Define personality-behavior correlation metrics.
3. Tune OCEAN weight constants in adventure decision scoring if personality
   is not producing statistically distinct behavioral clusters at scale.
4. Add a `make personality-audit` target for reproducible calibration runs.

## Out of Scope
- Re-implementing OCEAN trait system or mood system.
- Changing the OCEAN score initialization (F1 resolution is confirmed done).
- Embedding-based clustering (deferred per project memory — no runtime embeddings).

## Acceptance Criteria
- [ ] 1,000-tick audit shows ≥ 3 statistically distinct behavioral clusters
      correlated with OCEAN trait bands (e.g., Openness quartiles).
- [ ] High-Conscientiousness entities show ≤ 50% abandonment rate vs. high-Neuroticism.
- [ ] `make personality-audit` produces a reproducible audit report.
- [ ] Any OCEAN constant changes are recorded in the parity ledger under
      `strategic_cognition.yaml`.

## Related Tickets
- Parent: TCK-20260627-P3A-DEFERRED-EPICS
- Gate: TCK-20260627-P0A-ADVENTURE-FLAG (DONE)
- Observability enabler: TCK-20260627-P2O-ENTITY-PERSONALITY-OBS (DONE)

## Related Docs
- `docs/audits/D01_rpg_feature_impact.md` §Personality → Long-Run Behavior Calibration
- `docs/audits/D05_entity_differentiation.md` — D05 audit methodology
- `docs/mechanics/04_strategic_cognition.md` — OCEAN weight application

## Related Stored Artifacts
- N/A (will populate after calibration audit run)

## Related Code Areas
- `src/domains/adventure/phase.py` — adventure decision scoring with OCEAN bias
- `src/core/personality.py` (if exists) — OCEAN trait storage
- `src/observability/` — per-entity personality snapshot output
- `data/content/entities/entity_archetypes.yaml` — archetype trait distributions

## Assumptions / Open Questions
- Calibration methodology: use route-family distribution per personality quartile as
  the primary metric. If personality has near-zero correlation with route diversity
  at 1k ticks, the OCEAN weight constants need upward adjustment.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

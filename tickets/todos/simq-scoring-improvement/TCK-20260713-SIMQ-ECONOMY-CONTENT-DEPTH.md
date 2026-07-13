---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH
phase: open
date: 2026-07-13
tags: [simulation-quality, calibration, corpus]
---

# TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH

## Title
Author ECONOMY-rich content into 2-3 more archetype worlds

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`EconomyScorer` (`src/simulation_quality/scorers/economy.py`) listens for 10 distinct event types
(harvesting, crafting, trading, gold flow, scarcity, inflation control, conservation checks,
paid-info transactions, quest rewards) — not a thin, single-signal pillar. The corpus-wide C-heavy
grade distribution (60/72 committed anchors) is partly a genuine content gap: most worlds simply
don't have sustained harvest/craft/trade content authored into them. This pillar was never
addressed by the archived `docs/plans/archive/simq_development_roadmap.md` (explicitly out of
scope there — a Gini-threshold/archetype-composition question, not the `FeatureMode`-gating
question that roadmap's 4 pillars shared).

**This must land after `TCK-20260713-SIMQ-SCORE-CEILING-FIX`, not before or in parallel.**
Authoring more content into a formula that currently caps at 1/3-of-A regardless of volume
(confirmed empirically — the single richest observed ECONOMY run in the whole corpus, 69 events,
only reached a normalized score of 0.16 against a 0.5 A-threshold) risks spending real
content-authoring effort for a result that still reads as C/B corpus-wide.

## Scope
- Investigation-tier first: confirm which worlds already have a merchant NPC or crafting-capable
  population (per `data/worlds/*/world.yaml`) before authoring anything new — mirrors how the
  archived roadmap's Phase 3 investigation found FACTION/INFORMATION already more covered than
  assumed. ECONOMY's real gap size should be verified the same way, not assumed from the raw grade
  count alone.
- Author harvest/craft/trade content into 2-3 confirmed candidate worlds with a plausible
  in-fiction merchant/crafting economy (e.g. a trade-hub or settlement-heavy archetype).
- Recalibrate against the corrected formula from `TCK-20260713-SIMQ-SCORE-CEILING-FIX`, verify
  ECONOMY signal actually moves, full regression sweep given the cross-pillar side-effect history
  documented elsewhere in this corpus (e.g. INFORMATION activation once surfaced COGNITION
  side-effects).

## Out of Scope
- The weight/threshold recalibration itself — this ticket depends on
  `TCK-20260713-SIMQ-SCORE-CEILING-FIX`, it does not perform that work.
- Any world outside the 2-3 confirmed candidates from this ticket's own investigation.
- Re-opening FACTION/INFORMATION/SOCIAL/AGENCY depth — all declared complete by the archived
  roadmap's Phase 5 gate.
- ECONOMY's Gini-threshold mechanism (`EconomyHealthMonitor.INFLATION_SPIRAL_GINI_THRESHOLD`,
  `src/economy/health_monitor.py`) — content authoring only, no engine change expected.

## Acceptance Criteria
- [ ] ECONOMY grade moves measurably off C in ≥2 additional worlds, with calibration evidence in
      `docs/simulation_quality/eval_matrix_results.md`.
- [ ] 0 regressions on a full `evaluate_simq.py` sweep.
- [ ] If investigation finds fewer than 2-3 legitimate candidate worlds remain (mirroring the
      archived roadmap's FACTION/INFORMATION "zero new worlds, already adequate" outcome), that is
      an equally valid, documented closure — this ticket does not require finding candidates if
      honest investigation finds none remain.

## Related Tickets
- `TCK-20260713-SIMQ-SCORE-CEILING-FIX` — **hard dependency, must land first.**
- `TCK-20260710-SIMQ-DEPTH-SOCIAL`, `TCK-20260710-SIMQ-DEPTH-FACTION`,
  `TCK-20260710-SIMQ-DEPTH-INFORMATION` (all done) — the playbook precedent this ticket mirrors.

## Related Docs
- `docs/simulation_quality/current_state.md` — Recommendation 2, the finding this ticket addresses.
- `docs/plans/simq_scoring_improvement_roadmap.md` — Phase 2, this ticket's source.
- `docs/simulation_quality/corpus_tier_taxonomy.md` — tier structure; candidate worlds must respect
  tier-purity (Stress/Unit/Regression-tier worlds are supposed to stay content-inert).
- `docs/guidelines/design_patterns.md` Pattern 6 — the compile-time pillar activation pattern used
  for FACTION/INFORMATION; investigate whether it applies here or whether ECONOMY's mechanism
  (event-driven, not compiler-constructed field) means content authoring alone suffices without any
  Pattern 6-style plumbing.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/simulation_quality/scorers/economy.py`
- `data/worlds/*/world.yaml` (candidate world content)
- `config/simulation_quality/profiles/*.yaml` (calibration profiles for candidate worlds)

## Assumptions / Open Questions
- Candidate worlds are not pre-selected — deliberately left to this ticket's own Investigate step,
  working from live corpus content, per the same discipline the archived roadmap's depth waves
  followed.
- Whether ECONOMY's mechanism needs any Pattern 6-style compiler plumbing (like FACTION/
  INFORMATION did) or is purely content-authoring (since `EconomyScorer` is event-driven, reading
  `AuthoritativeState` fields not at all — confirmed during this session's investigation) is a real
  open question for the investigation step, not assumed here.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

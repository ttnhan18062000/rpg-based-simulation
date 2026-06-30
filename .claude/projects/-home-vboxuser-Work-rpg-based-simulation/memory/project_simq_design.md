---
name: simq-design
description: Simulation Quality Scoring Module — 10-pillar design completed, investigation ticket open, feature plan at docs/plans/sim_quality_scoring_module.md
metadata:
  type: project
---

Major new module designed (TCK-20260628-SIMQ-INVESTIGATION, status: inprogress).

Feature plan at `docs/plans/sim_quality_scoring_module.md`.

**Why:** No automated way to measure simulation health per-run per-subsystem. Audit dimensions are manual, behavior scorecards are post-run episode aggregates, hard_law_monitor is correctness not quality.

**The 10 pillars (source: D19 pipeline phases + D01 RPG tiers):**
1. Cognition — belief system, knowledge divergence, subjective decision-making (PP-03, PP-04, PP-30)
2. Agency & Action — purposeful action, anti-stasis, loop detection (PP-12, PP-13, PP-14, PP-15)
3. Combat — entity combat balance, attrition rates, resolution health (PP-16, PP-31, PP-33)
4. Faction & Military — diplomacy, alliance, military conflict, territory (PP-08, PP-09, PP-10, PP-11)
5. Economy — resource loop, crafting, trade, gold flow, ecology (PP-07, PP-24–27, WD-05, WD-10)
6. Progression — XP, level-up, skill unlock, trait expression (PP-24, PP-28, PP-29)
7. Social — cooperation, contracts, groups, reputation (PP-05, PP-34, PP-35, PP-36)
8. Information & Belief — paid info, lead certainty, decision divergence (PP-04, PP-26, PP-30)
9. World Dynamics — ecology, calamity, spawn, boss, trauma, demographics (PP-22, WD-01–15)
10. Narrative — quests, chronicle, world emergence, scenario objectives (PP-23, PP-24, PP-33)

**Architecture position:** New `src/simulation_quality/` module — subscribes to ObservabilityEventEnvelope, never imports domain internals, never mutates simulation state. Score records written to `data/runs/{run_id}/quality_scores.jsonl`.

**Score model:** ScoreRecord (immutable, typed) → PillarAccumulator (running totals + 100-tick window) → normalized_score = raw/ticks → health grade S/A/B/C/D/F.

**Does NOT overlap with:** RunBehaviorScorecard (post-run episode aggregates), CampaignScorecard (semantic arc verdict), AnalyzerQualityReporter (analyzer accuracy), hard_law_monitor (correctness).

**Implementation sequencing:** 10 phases: typed models → accumulators → scorers → hub wiring → persistence → report → API → tests → calibration.

**How to apply:** When implementing this feature, start from `docs/plans/sim_quality_scoring_module.md` — all pillar scoring tables, data flow, traceability paths, and API surface are defined there. Do not start implementation until user reviews and approves the design.

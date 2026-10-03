---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF
artifact_type: plan
phase: plan
date: 2026-08-08
tags: [feature-flags, progression, world]
---

# Plan — TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF

## Fix — REVISED after Implement found a real, blocking regression

Original plan (steps 1-4 below) was implemented and then reverted. See investigation.md's "Real
fix decision" section for the full evidence: enabling `ENABLE_ADVENTURE_ROUTING` for
`frontier_marches` correctly activates AGENCY (C→A on all 3 seeds, no stuck-hero failure) but also
silently collapses FACTION (S→C) and INFORMATION (B→C) via an apparent RNG-consumption side
effect unrelated to HERO routing itself. This is a real regression, not shipped.

**Final decision: no flag change ships in this ticket.** The ticket closes with:
1. The real root cause of HERO underperformance identified: mostly archetype-correct per a
   ratified Design Authority ruling (`TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`), not a wiring gap.
2. The one well-evidenced per-world opt-in candidate (`frontier_marches`) is blocked by a newly
   discovered, real regression — filed as its own follow-up ticket,
   `TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING`.
3. `config/simulation_quality/profiles/frontier_marches.yaml` reverted to its original state
   (`ENABLE_BELIEF_ASSIMILATION: "ON"` only).
4. `grade_anchors.json` recovered to its correct, real, current state (restoring the accidental
   over-broad `git checkout` from cached `data/calibration/` reports — see investigation.md's
   Operational note) — not left at either the stale 2026-08-05 state or the (now-reverted)
   frontier_marches-with-routing state.

Original steps (not executed — kept for record):
1. ~~Add `ENABLE_ADVENTURE_ROUTING: "ON"` to `frontier_marches.yaml`~~
2. ~~Recalibrate 3 seeds via `calibrate_simq.py`~~
3. ~~Update `grade_anchors.json`'s 3 `frontier_marches_seed*_200t` entries~~
4. ~~Update `eval_matrix_results.md`'s `frontier_marches` row~~

## Explicitly not doing

- Not flipping `ENABLE_ADVENTURE_ROUTING`'s own default in `feature_flags.py` — would break the
  sentinel test and violate the ratified per-world-archetype DA ruling.
- Not enabling routing for `crowded_frontier` or any other world — insufficient self-evident
  authored intent found in Investigate; a future ticket can revisit with stronger evidence.
- Not touching `urban_political` — already explicitly, deliberately settled OFF by prior ticket.

## Acceptance-criteria map

| Criterion | Satisfied by |
|---|---|
| Real HERO-entity-by-world distribution reported | investigation.md (3 heroes in `frontier_marches`, cross-world module/description survey) |
| Real routing-on vs routing-off comparison with data | investigation.md's live 800-tick probe (72 route_selected/action_executed per hero, healthy) |
| Real reason for OFF default reported | investigation.md (`TCK-20260627-P0A-ADVENTURE-FLAG`'s own deliberate-gated-rollout rationale + sentinel test) |
| Real rollout decision made and implemented | This plan: narrow per-world opt-in for `frontier_marches` only, not a corpus-wide flip |
| `grade_anchors.json` recalibrated | Step 3 above, with real `calibrate_simq.py` output |
| Scoped pytest passes | test_plan.md |

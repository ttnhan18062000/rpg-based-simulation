---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP
phase: plan
date: 2026-08-10
tags: [simulation-quality, calibration, corpus]
---

# Plan — TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP

No source code change (no `kernel.py` edit — out of scope, same guard as D06 F6). Pure
recalibration + provenance-classification ticket.

## Steps

1. Recalibrate `grade_anchors.json` for the 12 confirmed-cause fields (Finding 1) — same
   established methodology as the precursor SUB-384 tickets.
2. Recalibrate `hero_guild_routing_seed456_500t`'s COGNITION/ECONOMY (confirmed stable via 3x
   re-run, ordinary stale drift, same methodology).
3. Add 6 new `watchdog_variance` entries to `tests/simulation_quality/fixtures/score_ceilings.json`
   for the confirmed-unstable (run_key, pillar) pairs (Finding 2) — no code change, uses the
   existing `tools/simq_ceiling.py` content-threshold lookup mechanism.
4. Re-verify via the authoritative `_within_band`/`_format_score_failures` functions (not the
   coarser `evaluate_simq.py` grade-only diff) that every remaining fast-tier pytest failure
   carries a `[known ...]` annotation — zero unexplained.
5. Update `docs/audits/D06_longrun_health.md` F6 (extend to note the FAST-tier finding).
6. Finalize per standard tier.

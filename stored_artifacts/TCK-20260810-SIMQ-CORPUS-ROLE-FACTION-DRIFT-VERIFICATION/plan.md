---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION
phase: plan
date: 2026-08-10
tags: [simulation-quality, calibration, corpus]
---

# Plan — TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION

No source code change — this ticket's root cause (SUB-384) is already fixed
(`TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION`). This is a pure recalibration ticket:
update `tests/simulation_quality/fixtures/grade_anchors.json` for every field whose drift is
confirmed attributable to SUB-384's cascading effect (see investigation.md §1), leave every
pre-existing `[known tick_budget: ...]`-annotated field untouched.

## Steps

1. Batch-update `grade_anchors.json` for the 15 run_keys / 27 fields identified via the
   authoritative `_within_band`/`_format_score_failures` scan (SOCIAL/ECONOMY/PROGRESSION/
   COGNITION/AGENCY pillars).
2. Re-run `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q`; fix any
   further genuinely-new, unannotated failures surfaced (found: 2 guard-test-only run_keys —
   `urban_political_selfmodel_execution_probe_seed42_200t`,
   `urban_political_selfmodel_probe_seed42_200t` — needed a regenerated `quality_report.json`
   plus their own COMBAT/SOCIAL anchor updates, same confirmed cause).
3. Confirm the sweep's remaining failures are all pre-existing `[known tick_budget: ...]`
   annotated noise (zero unexplained failures).
4. Update `docs/simulation_quality/eval_matrix_results.md` and `docs/audits/D20_simq_integration.md`
   to record this ticket's own findings, distinct from the precursor audit's COMBAT-only note.
5. Update `docs/parity_ledger/substrate.yaml` SUB-384 entry to note the confirmed broader blast
   radius (PROGRESSION via `CombatRewardClassificationService`, cascading SOCIAL/ECONOMY/
   COGNITION/AGENCY/COMBAT via changed entity population dynamics).
6. Finalize per standard tier: move ticket to done, migrate staging artifacts, working_log,
   monitoring records, commit.

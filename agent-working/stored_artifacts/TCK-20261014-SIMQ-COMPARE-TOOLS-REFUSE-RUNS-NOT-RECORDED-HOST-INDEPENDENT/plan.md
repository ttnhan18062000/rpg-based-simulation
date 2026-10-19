---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261014-SIMQ-COMPARE-TOOLS-REFUSE-RUNS-NOT-RECORDED-HOST-INDEPENDENT
phase: done
date: 2026-10-19
tags: [testing, regression, simulation-quality]
---

# Plan

1. `tools/test_architecture/simq_run_record.py`: `read_run_determinism(run_dir)`, `write_sidecar(cal_dir, run_dir)`, `load_sidecar(cal_dir)`. Manifest path from `RunArtifactRepository.resolve_path`; a non-boolean or absent field is `None`.
2. `tools/calibrate_simq.py`: after `persistence.write_report`, write the sidecar from the same run's directory (reviewed separately by agent-working: see the PR).
3. `tools/test_architecture/simq_audit_rows.py`: the committed rows producer (`collect_row` reads the manifest, then deletes the run by exact id via `done_checker_static.delete_data_run_paths`).
4. `simq_reanchor.audit_values`: refuse unless both rows record `audit_mode` True, then `require_host_independent_runs` (rpg's helper) on `signals_zeroed`; `ReanchorRefused` names key and run.
5. `simq_pillar_compare`: `HostIndependenceRefused`, `require_host_independent(run_key, live_manifest)`, `compare_report(..., live_manifest=...)` with no default.
6. Callers: `test_grade_regression` (`_load_calibration_manifest`, `_pillar_failures(..., manifest)`), `evaluate_simq` (refusal is exit 2), `test_score_ceilings`.
7. `baseline_change_policy.md` rule 7 states both halves.

Rulings (testing-planner, 2026-10-19): commit the producer; the anchor side of a compare is not checked by manifest; sidecar shape and the calibrate_simq diff accepted (agent-working-planner: no objection); a campaign-mode run records `None` and refuses.

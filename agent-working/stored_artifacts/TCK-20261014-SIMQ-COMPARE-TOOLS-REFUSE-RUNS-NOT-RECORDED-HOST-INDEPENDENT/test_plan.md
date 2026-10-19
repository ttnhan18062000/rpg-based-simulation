---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261014-SIMQ-COMPARE-TOOLS-REFUSE-RUNS-NOT-RECORDED-HOST-INDEPENDENT
phase: done
date: 2026-10-19
tags: [testing, regression, simulation-quality]
---

# Test plan

## Proof Plan
| criterion | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| AC1: the producer copies the manifest's fields verbatim, None when absent | unit | fake run dir (manifest with both fields, one field, nulls, non-boolean, none) | the ticket AC and rpg's `RunManifest` fields | the row's `audit_mode` / `signals_zeroed` equal the manifest's or None; the run dir is gone, another run untouched | `pytest tests/unit/tools/test_simq_audit_rows.py` |
| AC1: a real run records them | integration | two-run smoke of one key | the run's own manifest | `audit_mode` True, `signals_zeroed` True, dirs deleted; rows accepted by `simq_reanchor` | `python -m tools.test_architecture.simq_audit_rows --key sandbox_world_seed42_200t` |
| AC2: reanchor refuses a pair not recorded audit_mode | unit | negative cases | the ticket AC | both audit accepted; one live, one pinned (signals_zeroed True, audit_mode False), one nulls, an old row with no fields: `ReanchorRefused` naming key and run; no CLI override | `pytest tests/unit/tools/test_simq_reanchor.py` |
| AC3: the live side must be host-independent | unit + integration | negative cases incl. sidecar with nulls and a missing sidecar | testing-planner ruling 2026-10-19 | `HostIndependenceRefused` with `__cause__`; `compare_report` has no default for `live_manifest`; `evaluate_simq` exits 2 | `pytest tests/unit/tools/test_simq_pillar_compare.py tests/simulation_quality/test_grade_regression.py tests/simulation_quality/test_anchors_audit_mode.py` |
| AC4: existing tests keep their assertions | regression | scoped suites | the ticket AC | only fixtures gained the fields | `pytest tests/unit/tools tests/simulation_quality tests/tools/test_score_ceilings.py tests/architecture tests/static -m "not slow"` |
| AC5: the policy line | review | doc check | the ticket AC | rule 7 states both halves | read `baseline_change_policy.md` |

---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-TEST-DECISIONS-RECORD-AND-SCENARIO-LANE
artifact_type: investigation
tags: [testing]
---

# Investigation

## Scenario-lane dependency evidence (D-R2, reviewer condition 2)

Method: ran `pytest tests/mechanic_scenarios -m "not slow and not extra_slow"` (53 passed) with a Python audit hook (`sys.addaudithook`, event `open`) recording every file opened under the repo root. 1,447 paths opened (ignoring caches). Non-`src/` paths by prefix:

| Opened path (count) | Read by | Classified |
|---|---|---|
| `data/content/**` (36 files in compatibility, entities, foundation, living, social, world) | world compile via `src.worldbuilding.compiler` / content resolver | trigger |
| `data/worlds/{mechanic_scenario_combat_judgement_withdrawal,unit_selfmodel_pilot,crowded_frontier}/**` (9) | `tests/helpers/scenario.py::compile_world` | trigger |
| `config/simulation_quality/*.yaml` (4) | SimQ profile loaded by the engine profiles | trigger |
| `tests/helpers/*.py` (8), `tests/tools/memory_probe.py`, `tests/conftest.py`, `tests/__init__.py` | imports | trigger |
| `tests/mechanic_scenarios/**` (23) | the tests | trigger (the old `PERF_RE` omitted this) |
| `data/runs/**` (145) | outputs written by the runs | not a dependency (written, not read); not a trigger |

Static evidence added: `tests/helpers` imports `tests.integration.kernel.test_determinism_suite` (trigger, one file). `requirements.txt`, `pyproject.toml`, `uv.lock`, `Makefile` and `.github/workflows/test.yml` are triggers by convention (the environment and the job definition), not by file-open evidence.

Known-irrelevant entries: `docs/`, `tickets/`, `agent-monitoring/`, `agent-orchestration/`, `stored_artifacts/`, `staging_artifacts/`, `frontend/`, `dashboard-frontend/`, `website/`, `grafana/`, `reviews/`, `experiments/`, `registries/`, `tools/`, `pilot_requests/`, root `*.md`, `skills-lock.json`. Evidence: none of these prefixes appears in the audit-hook list (the scenario docstrings mention `registries/mechanisms.yaml` but no file under `registries/` or `tools/` was opened). Everything else (e.g. `tests/unit/**`, other workflows, `.claude/**`, `config/` outside `simulation_quality`) is **unknown** and fails open.

Limit: the audit covers the non-slow scenario run at this SHA. A dependency only reached by a slow test or a code path not taken is not seen; such a path is either under `src/` (trigger) or unknown (fail open), never irrelevant unless listed above.

## Other findings
- `perf-cert-arena` already runs `tests/mechanic_scenarios` when `PERF_RE` matches, so the new job runs only when it does not (once per PR).
- `main` has no branch protection (reviewer verified: 404 "disabled"); "non-required" is by convention.
- Old `PERF_RE` omitted `tests/mechanic_scenarios/`: a scenario-test-only PR ran no scenario test.
- `impact_report.py:268-270` `executed: not-run` meant "no supplied evidence"; renamed. The mutation layer's `not-run` is accurate and stays.

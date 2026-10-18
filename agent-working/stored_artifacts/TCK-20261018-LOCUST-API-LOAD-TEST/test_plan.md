---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-LOCUST-API-LOAD-TEST
artifact_type: test_plan
tags: [platform, observability]
---

# Test plan: TCK-20261018-LOCUST-API-LOAD-TEST

**Written retrospectively at ticket close (2026-10-18).** The plan was given in platform-planner's dispatch messages and the ticket Scope; this file records it after the fact.

## Test plan (what was run)

## Proof Plan
| criterion | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| AC1: 2-step smoke run completes, writes CSVs, manifest and summary, 429s in their own category | runtime, local | smoke run | none: platform runtime, criterion from the ticket AC and ADR `docs/architecture/devops_baseline_adr.md` | CSVs, manifest.json, summary.json written; `admission_429` counted separately | `python3 -m tools.loadtest.run --users 5,10 --duration 30 --repeats 1 --warmup 5 --smoke` (and a `--single-key` step) |
| AC2: pool shows no 429 at 10 users; a single shared key does | runtime, local | differential | none: platform runtime, criterion from the ticket AC and ADR `docs/architecture/devops_baseline_adr.md` | pool 10 users: 0 of 5283; single key 10 users: 9237 of 11616 | same runner, with and without `--single-key` |
| AC3: unit tests for the summary maths with fixed CSV fixtures | unit | regression | none: platform runtime, criterion from the ticket AC and ADR `docs/architecture/devops_baseline_adr.md` | spread, knee rule, attribution, ceiling, baseline, flags, status-key hashing, engine reading and ticks/s all asserted | `pytest tests/tools/test_loadtest_summary.py` |
| AC4: CI pin tests and tests/tools pass after the uv.lock change | static and tools | regression | none: platform runtime, criterion from the ticket AC and ADR `docs/architecture/devops_baseline_adr.md` | green | `pytest tests/static` and `pytest tests/tools` under a memory cap |
| AC5: `tools/sessions/validate.py` passes with the new owns glob | static | validator | `registries/session_roles.yaml` | 0 findings | `PYTHONPATH=. python3 tools/sessions/validate.py` |

## Results (from the ticket's Test Summary)
- `tests/tools/test_loadtest_summary.py`: 44 passed together with the platform-domain and repo-root tests at the last run (33 in the summary file itself).
- Cleared run 2026-10-18: `tests/static` 96 passed; `tests/tools` 4994 passed, 56 skipped, 1 xfailed; `tests/api` 148 passed, 2 failed (live-server websocket timing).
- ws comparison and `requests` 2.34.2 evidence: 6 of 6 ws runs and the full `tests/api` (150 passed) on a scratch venv with requests 2.34.2 had no failures; the two earlier failures did not recur and were not shown to be pre-existing.
- Smoke run (labelled not a measurement): pool 5 users 167.6 req/s, 9 of 4875 429; pool 10 users 182.0 req/s, 0 429; single key 10 users 399.4 req/s, 79.5 % 429.
- `tools/sessions/validate.py`: 0 findings after the cards were regenerated.
- Not run: `tests/tools` again after the latest commits (the 44 tests above were run).

---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-API-LOAD-TEST-MEASURED-RUN
artifact_type: test_plan
tags: [platform, observability]
---

# Test plan: TCK-20261018-API-LOAD-TEST-MEASURED-RUN

**Written retrospectively at ticket close (2026-10-18).** The plan was given in platform-planner's dispatch messages and the ticket Scope; this file records it after the fact.

## Test plan (what was run)

## Proof Plan
| criterion | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| AC1: record holds the #541 items (USE and first saturated resource, p50/p95/p99 with spread, hardware, fleet, commit, profiled run labelled separately) | runtime, local | measurement | none: platform runtime, criterion from the ticket AC and ADR `docs/architecture/devops_baseline_adr.md` | all items present in the record | `python3 -m tools.loadtest.run --users 10,25,50,100,200 --duration 60 --repeats 3 --label baseline`; `--users 25 --duration 120 --repeats 1 --warmup 15 --baseline-seconds 0 --label profiled` with py-spy; `--users 50,100 --duration 60 --repeats 1 --label obs-on` |
| AC2: every figure traces to a CSV in the stored artifacts | static | traceability | none: platform runtime, criterion from the ticket AC and ADR `docs/architecture/devops_baseline_adr.md` | each run dir copied to staging with `manifest.json`, `summary.json` and per-step CSVs | `agent-working/staging_artifacts/TCK-20261018-API-LOAD-TEST-MEASURED-RUN/run-*` |
| AC3: proposed SLO threshold and its derivation stated | doc | review | none: platform runtime, criterion from the ticket AC and ADR `docs/architecture/devops_baseline_adr.md` | record section 7, accepted by lead-planner as proposed; the owner approves at PR time | `docs/runbooks/records/2026-10-18-api-load-test.md` |
| AC4: run data cleaned by run id; `data/runs` ownership checked | runtime, local | live check | none: platform runtime, criterion from the ticket AC and ADR `docs/architecture/devops_baseline_adr.md` | new dirs 1000:1000; only own dirs removed | `ls -ln data/runs`; `done_checker_static.py --clean-data-runs --path <run_id>` |

## Results
- Throughput runs completed with the abort guard never firing (available memory about 5.1-5.9 GB, swap about 2.4-2.5 GB).
- Age soak, fresh curve (10-200 users, one fresh backend per step), pre-age and aged curve (10-100 users): tables in the record, sections 2, 3, 5 and 6.
- Checks in the same window: Grafana whitespace guard PASS; watchdog `id` uid 1000 on the rebuilt image; Grafana fresh-volume check NOT run (needs the owner's direct yes to remove `platform_grafana_data`).
- `tools/loadtest` tests, platform domain and repo-root tests: 44 passed at the last run.
- Not run: `make knowledge-index-update` (on hold by planner until lead gives a slot); a py-spy run on any step other than 25 users.

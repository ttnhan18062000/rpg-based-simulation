---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK
artifact_type: test_plan
tags: [platform, observability]
---

# Test plan: TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK

Written by platform-planner at dispatch (2026-10-19); the implementer updates it as the work changes.

## Proof Plan
| criterion | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| rules provisioned | running locally | provisioning API | Grafana | group `slo` with 2 rules, provenance file | `GET /api/v1/provisioning/alert-rules` |
| 0.3 bucket present | running locally | metrics query | Prometheus | `le="0.3"` series exist | query `http_request_duration_seconds_bucket{le="0.3"}` |
| server-side numbers per step | measured | histogram_quantile per step vs Locust CSV | Prometheus + Locust | table p50/p95/p99 both sides per step | PromQL at step end; Locust stats CSV |
| fire and resolve | running locally | Locust step above knee | Grafana state + ntfy | pending, firing, ntfy message with route and runbook link, resolved after load stops | Grafana alert API; ntfy poll |
| error rule evaluates | running locally | rule state | Grafana | Normal under normal load, no exec error | Grafana alert API |
| docs valid | static | frontmatter | docs schema | OK | `validate_frontmatter.py` |

## Live row added at planner review (2026-10-19)
| # | check | oracle | expected |
|---|---|---|---|
| L-N | while the SLO is NOT violated the rules show Normal | `GET /api/prometheus/grafana/api/v1/rules` (state/health of `ApiLatencyP95High` and `ApiErrorRateHigh`) before the fire step | state Normal (NoData mapped to OK), health ok; never NoData or Error |

## Results (2026-10-19)
- L-N passed (Normal, health ok, never NoData/Error as a state). Server-side vs Locust per step recorded; the 25-user step did not fire (server p95 0.222 to 0.239 s), the 50-user step fired (ntfy `[firing]` 17:33:05Z, `[resolved]` 17:43:05Z); thresholds never edited. Record: `docs/runbooks/records/2026-10-19-api-slo-alert-fire-test.md`; run files in `run-2026-10-19/`.

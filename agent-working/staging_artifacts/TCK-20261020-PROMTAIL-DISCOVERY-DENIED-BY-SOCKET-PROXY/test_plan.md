---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261020-PROMTAIL-DISCOVERY-DENIED-BY-SOCKET-PROXY
artifact_type: test_plan
tags: [platform, observability]
---

# Test plan: TCK-20261020-PROMTAIL-DISCOVERY-DENIED-BY-SOCKET-PROXY

## Static (no stack)
- `docker compose config -q` for the default and observability profiles.
- `promtool check config docker/prometheus.yml`, and `promtool check rules` on the rule's PromQL if it applies (Grafana rules: YAML parse plus a provisioning load in the live run).
- Frontmatter validator on the changed docs and tickets. `tests/static`, `tests/architecture/test_docker_compose_dependency_hygiene.py`, `tests/logging/test_loki_cardinality.py`, `tests/tools/test_session_platform_domain.py`. Scoped runs only, at load < 3.

## A/B (light slot 1)
| state | action | expected |
|---|---|---|
| A | fresh up, no NETWORKS | promtail targets 0/0; 403 every refresh; Loki labels empty; sent_entries 0 |
| B | proxy NETWORKS=1 (throwaway override), recreate proxy + promtail | targets > 0; Loki `container` has the project's running containers, no loki or promtail; backend line queryable |
| B-surface | probes through the proxy | GET /networks 200; GET /networks/<id> 200; POST /networks/create 403; DELETE /networks/<id> 403; POST /containers/x/stop still 403 |
| C | recreate proxy without NETWORKS, promtail untouched | targets persist; sent_entries keeps rising; 403 logged (reproduces 10-18) |
| C' | restart promtail | targets 0/0 |

## Live proof after the fix (light slot 2, or merged with slot 1)
- A fresh up from main + fix: targets > 0, labels, a backend log line, sent_entries rising.
- `LogShippingStalled` provisioned, Normal while shipping.
- Induced failure (i): `docker compose stop promtail`, then TargetDown{job=promtail} and `LogShippingStalled` (noData → Alerting) fire and reach ntfy (record pending and firing times and the ntfy timestamps); `start promtail`, then both resolved arrive.
- Induced failure (ii), the real one: a fresh promtail against the 403 (state A override), then `LogShippingStalled` fires on targets_active == 0; restore and see it resolved.
- Quiet-stack check: with no load for > 10 m, `LogShippingStalled` stays Normal (targets > 0 even when no lines are sent).
- Thresholds are not edited.
- The runbook's Loki first checks (target-down, api-latency-slo, redis-down) each run once and return lines.
- docker stats and the cgroup peaks for promtail and the proxy (sample_stats.sh): within limits on anon + active_file.

## Regression-prone paths
- Project filter: no other stack's containers in Loki.
- loki and promtail self-logs still dropped.
- Secrets: no token or topic in any captured file (scan by counts).

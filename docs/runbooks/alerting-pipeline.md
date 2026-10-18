---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, observability]
---

# Runbook: alerting pipeline (PrometheusUnreachable, GrafanaAlertingFailures)

## PrometheusUnreachable
Rule: the query `vector(1)` against the `prometheus` datasource, for 2m. `execErrState: Alerting` on purpose: when Grafana cannot query Prometheus the query errors, and that error is the signal. `noDataState: OK`. Severity critical.
1. `docker compose --profile observability ps prometheus` and its logs.
2. Grafana, Connections, Data sources, Prometheus, Test.
3. `http://127.0.0.1:9090/-/healthy`.

Fix: restart Prometheus (`docker compose --profile observability up -d prometheus`); check its `mem_limit` and the `prometheus_data` volume.

## GrafanaAlertingFailures
Rule: `increase(grafana_alerting_rule_evaluation_failures_total[5m]) + increase(grafana_alerting_notifications_failed_total[5m]) > 0`, for 0s (a failure is rare and worth a message at once). `noDataState: OK`, `execErrState: OK`. Severity warning. Scraped from Grafana's own `/metrics` (job `grafana`).
1. Grafana, Alerting, Alert rules: which rule shows an Error state, and its error text.
2. Grafana, Alerting, Contact points: the ntfy contact point's last delivery error.
3. `docker compose --profile observability logs --tail=100 grafana ntfy`.

## Known limit
If the notifier itself is broken (ntfy down or the token invalid), `GrafanaAlertingFailures` cannot reach ntfy; the Grafana alert state is the only trace. Check the Alerting UI (`http://127.0.0.1:3000/alerting`) when you suspect silence. `TargetDown` for `ntfy` goes through the same broken path.

## Silence and escalate
See the README. Escalate to the owner if ntfy delivery stays broken after a restart and a token check (`docker compose exec ntfy ntfy token list`).

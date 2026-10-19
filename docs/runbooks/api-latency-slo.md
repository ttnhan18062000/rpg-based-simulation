---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, observability, performance]
---

# Runbook: API SLO (ApiLatencyP95High, ApiErrorRateHigh)

The SLO text is owner-approved (#627): **API p95 <= 300 ms over 5 minutes and 5xx < 1 percent**, measured server-side on rpg's histogram `http_request_duration_seconds{method, route, status_class}` scraped from `backend:9109` (job `rpg-backend`). Both rules are in `docker/grafana/provisioning/alerting/rules-slo.yaml`, group `slo`; that file is the single source of the PromQL. Alerts go to the local ntfy through the S4 contact point and policy.

| Rule | Expression (comparison included) | `for` | `noDataState` / `execErrState` |
|---|---|---|---|
| `ApiLatencyP95High` | `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{status_class="2xx",route!~"/health\|unmatched"}[5m]))) > 0.3` | 2m | OK / OK |
| `ApiErrorRateHigh` | `sum(rate(http_request_duration_seconds_count{status_class="5xx"}[5m])) / sum(rate(http_request_duration_seconds_count[5m])) > 0.01` | 2m | OK / OK |

The rules are evaluated every minute. The rate windows are 5 minutes, so a short spike does not fire; `for: 2m` keeps a single noisy evaluation from paging. No data means no traffic or a backend that is down, which is `TargetDown`'s job (see [target-down.md](target-down.md)); a failing Prometheus is `PrometheusUnreachable` (see [alerting-pipeline.md](alerting-pipeline.md)). That is why neither rule alerts on no data or an error.

## What the SLI covers, and what it does not
- **Latency SLI (lead decision D-B, 2026-10-19):** only `status_class="2xx"` responses, excluding `route="/health"` and `route="unmatched"` (unmatched is every URL no route claims, so it would let a scanner move the number). 429 cannot be separated from other 4xx in this histogram, so **4xx is not in the latency SLI**: an admission-pressure 429 storm does not fire the latency alert.
- **Error SLI:** all 5xx over all requests, every route.
- The 0.3 s threshold needs a histogram bucket edge at 0.3 (owner decision 2026-10-19, requested on #622). Without that edge `histogram_quantile` interpolates inside the 0.25 to 0.5 bucket and the 300 ms line is approximate.
- **Availability SLO without an alert:** `/health` at least 99 percent over 1 hour (ADR D5). Step 3 asks for one alert, so this one is written down and not alerted on.

## What it means
`ApiLatencyP95High`: the 95th percentile of successful API responses was above 300 ms over the last 5 minutes. `ApiErrorRateHigh`: more than 1 percent of responses were 5xx over the last 5 minutes. The API is slow or failing for real callers.

## First three checks
1. Grafana Explore on the `prometheus` datasource: the latency expression without the `> 0.3`, by route (`sum by (le, route)`), to see which route is slow. On the load-test mix the slow route is `/api/v1/entities` once the world has aged: its response grows with the world's age to about 690 to 745 KB (see the [2026-10-18 load-test record](records/2026-10-18-api-load-test.md) and the [2026-10-19 fire-test record](records/2026-10-19-api-slo-alert-fire-test.md)).
2. The Loki query on backend logs (`{container=~".*backend.*"}`): errors, tracebacks, admission pressure messages.
3. Tempo search for slow traces: tracing is wired in compose but the spans arrive only after rpg's R3 (OpenTelemetry) lands; until then this step finds nothing.

## Known causes
- **Engine tick contention in the same process:** the API and the engine share one Python process; a slow tick delays requests.
- **Admission pressure mode** (the governor): sustained load puts the server in a restrictive mode; check the governor state in `/api/v1/status`.
- **Host saturation:** this is a VM host with the whole stack and other sessions on it; check `docker stats` and the host load.
- **Payload growth with world age:** `GET /api/v1/entities` is the dominant cost in the measured mix. What grows it: on 2026-10-19 the response went from about 12 KB to a plateau of about 691 KB within a few minutes of 50-user load while the world held only 12 entities (about 57 KB per entity), so the per-entity payload grows with age; the 2026-10-18 world had 100 entities at about 7.4 KB each. The cause of the per-entity growth was not investigated.

## Mitigations
Reduce the load (stop the load test or the client), restart the backend only if it is stuck (`docker compose restart backend`; this resets the world age), and check that the metrics port `backend:9109` is still scraped (job `rpg-backend`, [target-down.md](target-down.md)). Do not raise the threshold to make the alert go away: the thresholds are the SLO and are not edited, not even for a test.

## Silence and escalate
See the [index](README.md) for the silence steps. Escalate to the owner if the SLO stays violated after the load is gone.

## Risks and notes
- **The numbers are one host's:** the SLO is "on this host spec, at the `/entities` page cap, load-test route mix, concurrency of at most 10 clients (about 145 requests per second ceiling)". It is not a capacity claim for anything else.
- **Trivy baseline note (#561):** the image scans in `publish-images.yml` are report-only (ADR D3) and the HIGH/CRITICAL baseline counts are recorded only after the first published run; flipping Trivy to blocking needs its own owner decision. This alert says nothing about image vulnerabilities.
- The fire test (a Locust step above the knee) is recorded in the drill record for this alert; it never edits the committed thresholds.

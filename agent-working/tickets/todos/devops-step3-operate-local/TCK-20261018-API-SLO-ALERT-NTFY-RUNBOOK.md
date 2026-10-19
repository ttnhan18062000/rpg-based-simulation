---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK
phase: open
date: 2026-10-18
tags: [platform, observability]
---

# TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK

## Title
One API SLO alert as a provisioned Grafana alert rule, a local ntfy container as its contact point, and the runbook it links to

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
ADR D5 as amended: one SLO alert, Grafana alerting, ntfy. The owner hasn't picked a public ntfy topic, so the contact
point is a local ntfy container for now; switching to ntfy.sh later is a one-line URL change. Every alert links to a
runbook in `docs/runbooks/`.

## Scope
- **SLO (owner-approved text at #627; amended 2026-10-19 after R1/R2 landed):** "API p95 ≤ 300 ms over 5 min and 5xx < 1%",
  measured server-side on rpg's R2 histogram `http_request_duration_seconds{method, route, status_class}` scraped from
  `backend:9109`.
  - **Threshold 0.3 s exactly:** owner decision 2026-10-19 (D-A option 1): rpg adds a 0.3 bucket to R2's `_BUCKETS`
    (requested on #622). The stack run waits until that is on main.
  - **Latency SLI (lead D-B, 2026-10-19):** `status_class="2xx"` only, excluding `route="/health"` and `route="unmatched"`:
    `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{status_class="2xx",route!~"/health|unmatched"}[5m]))) > 0.3`.
    429 cannot be separated from other 4xx, so 4xx is out of the latency SLI; the runbook says so.
  - **Error SLI:** `sum(rate(http_request_duration_seconds_count{status_class="5xx"}[5m])) / sum(rate(http_request_duration_seconds_count[5m])) > 0.01`.
  - Two rules in one rule group `slo` (latency and errors: both are the approved SLO text). `for:` windows chosen
    and stated in the runbook.
  - **The rule file is the single source of the PromQL.** No `tests/**` comparison test (tests/** is rpg's; lead D-4,
    confirmed 2026-10-19). The dashboard ticket copies the expressions and checks equality in its own test plan.
  - D5's availability SLO (/health ≥ 99 % over 1 h) is written into the runbook as an SLO without an alert. Step 3
    asks for one alert.
- **Provisioning files** under `docker/grafana/provisioning/alerting/`: the rule group, the contact point, and the
  notification policy. Datasources are referenced by uid. `noDataState` and `execErrState` are chosen and stated in
  the runbook.
- **ntfy, contact point and policy: reuse S4's** (amended 2026-10-18 at S4 filing). `TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES`
  builds the `ntfy` service, the ntfy contact point (topic from a gitignored secret file, never committed) and the
  notification policy. This ticket adds only its rule group (with `runbook_url`) under
  `docker/grafana/provisioning/alerting/` and routes through that policy.
- **`docs/runbooks/api-latency-slo.md`** (frontmatter per the docs schema):
  - what the alert means;
  - the first three checks (the PromQL in Grafana Explore by route, the Loki query on backend logs, and a Tempo search
    for slow traces once R3 lands; until then say so);
  - known causes (engine tick contention in the same process, admission pressure mode, host saturation);
  - mitigations;
  - how to silence it;
  - escalation (the owner);
  - the Trivy baseline note from #561 under risks.

  Add its row to `docs/runbooks/README.md` (the index is created by S4's `TCK-20261018-BASE-ALERTS-RUNBOOKS-AND-DRILL`).
- `docs/runbooks/**` is already platform-owned (registered with #627).
- The knowledge index is refreshed by lead-planner in the main checkout after merge (not in the worktree).

## Out of Scope
- The Redis-down cause alert (`TCK-20261018-REDIS-DOWN-CAUSE-ALERT`), the ai_worker lag alert (blocked ticket).
- A public ntfy.sh topic or Telegram: an owner choice, later.
- Prometheus-side alerting rules or Alertmanager (D5 says Grafana alert rules).

## Acceptance Criteria
- After a fresh `--profile observability` start, the rule, contact point and policy appear as provisioned (read-only)
  in Grafana (**running locally**).
- **Server-side numbers:** on an aged world at the `/entities` page cap (the #627 method), Locust steps record
  server-side p50/p95/p99 from the histogram next to Locust's client-side numbers, per step (**measured**).
- **Fire test:** a Locust step above the knee (aged curve: p95 ≈ 410 ms at 25 users on 2026-10-18) makes the latency
  alert fire. No env-override threshold (lead {D}: provisioning `$VAR` has no default, so an override would be a
  required variable); the committed 0.3 is never edited. The ntfy topic receives it with the runbook link, and it resolves after
  the load stops. Timestamps are recorded.
- `docker compose --profile observability config -q` passes. ntfy is bound to `127.0.0.1` only.
- The new docs pass frontmatter validation.

## Related Tickets
Epic `TCK-20261018-EPIC-DEVOPS-STEP3-OPERATE-LOCAL`. Needs `TCK-20261018-API-LOAD-TEST-MEASURED-RUN` (done, #627),
`TCK-20261018-SCRAPE-BACKEND-METRICS-PORT` (the 9109 scrape), S4's `TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES` (done, #640), rpg R2 (#654) and
rpg's 0.3 bucket (#622). The dashboard ticket `TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF` now follows this one and copies its PromQL.

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D5), `docs/runbooks/` (new)

## Related Stored Artifacts
None.

## Related Code Areas
`docker/grafana/provisioning/alerting/rules-slo.yaml` (new), `docs/runbooks/api-latency-slo.md` (new), `docs/runbooks/README.md`

## Assumptions / Open Questions
- If Grafana 13's file provisioning for alerting differs from the documented schema, follow the 13.x docs and
  record the version used.

## Implementation Notes
(open)

## Test Summary
(open)

## Files Changed
(open)

## Completion Summary
(open)

---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK
artifact_type: investigation
tags: [platform, observability]
---

# Investigation: TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK

Written by platform-planner at dispatch (2026-10-19); the implementer updates it as the work changes.

## Findings at dispatch
- Owner-approved SLO text (#627 merge): "API p95 ≤ 300 ms over 5 min and 5xx < 1%, at the /entities page cap (100
  entities, ~745 KB), on this host spec, load-test route mix, concurrency ≤ 10 clients (~145 req/s ceiling)".
- R2 buckets at #654: 0.005 ... 0.25, 0.5 ...; 0.3 is not a boundary. Owner decision 2026-10-19: rpg adds 0.3 (#622
  comment 6260505031). Until then the quantile at 0.3 would be interpolated between 0.25 and 0.5.
- Lead D-B (2026-10-19): latency SLI on 2xx only, excluding /health and unmatched; errors 5xx over all.
- S4 lessons: `$$` is not an escape in Grafana 13.2.4 provisioning; use single `$labels`. Env-override thresholds are
  ruled out (provisioning `$VAR` has no default).
- Aged curve (2026-10-18 record): p95 200/410/680/1400 ms at 10/25/50/100 users, so 25 users should breach 300 ms.

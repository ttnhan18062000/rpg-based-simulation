---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261020-PROMTAIL-DISCOVERY-DENIED-BY-SOCKET-PROXY
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-PROMTAIL-DISCOVERY-DENIED-BY-SOCKET-PROXY

## Title
Loki receives no logs: promtail's docker discovery is denied by the socket proxy (GET /networks returns 403)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
In the 2026-10-19 SLO run, the Redis drill and the re-measure, Loki held no data: no labels, `loki_ingester_chunks_created_total` 0, promtail sent 0 entries. Promtail `/targets` shows `docker/tcp://docker-socket-proxy:2375 (0/0 ready)`. Every 5 s it logs `Unable to refresh target groups ... error while computing network labels: ... 403 Forbidden`. `docker-socket-proxy` (tecnativa v0.4.1) allows `CONTAINERS=1`, `POST=0` only. A probe from inside promtail: `GET /containers/json` returns 200, `GET /networks` returns 403. So every runbook first check that starts with Loki finds nothing; `docker compose logs` is the working fallback. Evidence: `docs/runbooks/records/2026-10-19-redis-stop-drill-under-load.md` §7 and its `remeasure-2026-10-19/loki/` files (stored_artifacts of TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD).

## Scope
- Establish when it broke. The first hypothesis was the promtail bump 3.0.0 → 3.6.8 (#562/#604, merged 2026-10-16), but counter-evidence weakens it. TCK-20261018-OBSERVABILITY-PROFILE-HARDENING's runtime check on 2026-10-18, already on promtail 3.6.8 with the same proxy (CONTAINERS=1, POST=0), recorded "NETWORKS=1: not needed. Without it the proxy returns 403 on GET /networks (logged every refresh), GET /containers/json works and backend logs keep arriving", plus Loki `container` values for the 9 project containers. So the 403 alone did not stop discovery on 10-18. Find what changed between that run and 2026-10-19. Candidates:
  - the service set (S4 added node-exporter and ntfy; R1/R2 added redis-exporter), and whether any container now carries more than one network, or a network-mode, that makes the network-label lookup mandatory;
  - promtail-config edits after HARDENING;
  - the proxy image;
  - whether the 10-18 check ran a different promtail config.
  Read promtail 3.6.8's docker_sd network-label code path to see when a /networks failure aborts the whole refresh.
  - Leading hypothesis (planner, 2026-10-20): the 10-18 observation is explained by stale targets, not by the 403 being harmless. `NETWORKS` never appears in compose.yaml's git history (`git log -S NETWORKS`), so NETWORKS=1 was set only ad hoc during the 10-18 check and then dropped. Prometheus-style discovery keeps the last successful target groups when a refresh fails. If promtail discovered its targets while NETWORKS=1 was set, and the proxy was then recreated without it, the targets would stay in memory and logs would keep arriving, with the 403 logged on every refresh. A fresh promtail start against a 403 never gets targets, which matches 2026-10-19 (0/0). The A/B run must test exactly this: fresh start, 403 → 0 targets; fresh start with NETWORKS=1 → targets; then recreate the proxy without NETWORKS and check the targets stay (stale).
- Choose a fix, preferring the narrowest read surface:
  (a) `NETWORKS=1` on the proxy (GET-only, since POST=0 stays). This widens what the proxy exposes: network names, subnets and attached containers. Security decision: lead reviews, and the decision is recorded in compose.yaml beside the proxy's existing risk comment.
  (b) a promtail/discovery setting that skips network labels, if one exists in the pinned version.
  (c) fold into the Promtail → Alloy migration follow-up, if that lands first. Alloy's discovery.docker has the same networks call, so (a) or (b) is still needed.
- Prove it live: promtail targets > 0 and ready; Loki labels include `container`; a backend log line is queryable; `promtail_sent_entries_total` > 0. Re-run the runbook's Loki first check from target-down.md / api-latency-slo.md / redis-down.md.
- Update the runbooks: remove the "docker compose logs fallback" note once Loki works.

- Fold in two stale compose.yaml comments (lead review of the R1/R2 batch, 2026-10-20):
  - redis-exporter `mem_limit: 32m # placeholder until the measured peak is recorded`: replace it with the measured figure (re-measure 2026-10-19: docker stats 12 MiB, anon 10 MiB, anon + active_file 12 MiB, 36 %).
  - grafana "Slot (c) verifies the new headroom": replace it with the result (re-measure anon 23 % of 1024m; the long-run slot (b) figure of 654 MiB is 64 %).
- Runbook pass, same PR (lead, 2026-10-20): #686 made `GET /api/v1/entities` a bounded summary (target ≤ 1 KB per row). In api-latency-slo.md, update the "payload growth with world age" cause and first check: say the 2026-10-19 plateau (~691.5 KB, 12 entities) predates #686, and confirm the new size with one measured request if a stack is up. Do not edit the 2026-10-19 records.

## Out of Scope
- Promtail → Alloy migration itself (separate follow-up).
- Loki retention or limits.
- Any other proxy section beyond what discovery needs.

## Acceptance Criteria
- Root cause (version or config) stated, with evidence.
- Loki receives backend, ai_worker and grafana logs in a live run; the queries are recorded.
- The proxy allow-list change, if any, is the minimum needed, is GET-only, and its risk is written next to it in compose.yaml with the reviewer's decision.
- A guard against silent regression: the runbook's alerting-pipeline or target checks include "promtail targets > 0". Optional: a base alert on `promtail_targets_active_total == 0`, or on the sent-entries rate being 0 with the stack up. Decide in the plan.

## Related Tickets
- TCK-20261015-LOKI-37-READINESS-VIA-PROMTAIL (promtail 3.6.8 bump)
- TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD (found it)
- Promtail → Alloy follow-up (to be filed)

## Related Docs
- docs/runbooks/records/2026-10-19-redis-stop-drill-under-load.md
- docs/runbooks/target-down.md, docs/runbooks/api-latency-slo.md, docs/runbooks/redis-down.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD/ (remeasure-2026-10-19/loki/)

## Related Code Areas
- compose.yaml (docker-socket-proxy, promtail)
- docker/promtail config

## Assumptions / Open Questions
- Did Loki ever receive docker logs in this stack? Unknown. Check older records first.

## Implementation Notes
Not started.
- Plan requirements (lead, 2026-10-20). The plan must state:
  - the exact proxy env change and every endpoint it opens;
  - whether `docker_sd` can avoid `/networks` (a config option, or a file-based log path such as /var/lib/docker/containers), so we can compare against not widening the proxy;
  - the promtail release-notes line (or code reference) that proves or disproves the 3.6.8 hypothesis;
  - the targets > 0 guard (in scope).
  The `NETWORKS=1` decision goes to the owner through lead, with platform-planner's recommendation.
 Standard tier: plan.md, investigation.md and test_plan.md at dispatch.

## Test Summary
Not started.

## Files Changed
None yet.

## Completion Summary
Not started.

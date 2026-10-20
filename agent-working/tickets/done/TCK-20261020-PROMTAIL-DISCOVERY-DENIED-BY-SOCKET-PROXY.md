---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261020-PROMTAIL-DISCOVERY-DENIED-BY-SOCKET-PROXY
phase: done
date: 2026-10-20
tags: []
---

# TCK-20261020-PROMTAIL-DISCOVERY-DENIED-BY-SOCKET-PROXY

## Title
Loki receives no logs: promtail's docker discovery is denied by the socket proxy (GET /networks returns 403)

## Status
DONE

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
- A guard against silent regression: a Prometheus job `promtail` and a base alert `LogShippingErrors` on promtail's own error-level log counter (`sum(rate(loki_internal_log_messages_total{job="promtail",level="error"}[5m])) > 0` for 10m, noData → Alerting), with a runbook section whose first check is `docker compose logs promtail` (discovery 403 = the proxy allow-list; push errors = Loki); promtail down is TargetDown{job="promtail"}. Not zero sent entries (an idle stack fires). The original `promtail_targets_active_total` design was dropped: that metric is not exported for docker discovery in 3.6.8. Proven by a stopped promtail, by a fresh promtail against the 403, and by a quiet stack.

## Related Tickets
- TCK-20261015-LOKI-37-READINESS-VIA-PROMTAIL (promtail 3.6.8 bump)
- TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD (found it)
- Promtail → Alloy follow-up (to be filed)

## Related Docs
- docs/runbooks/records/2026-10-19-redis-stop-drill-under-load.md
- docs/runbooks/target-down.md, docs/runbooks/api-latency-slo.md, docs/runbooks/redis-down.md

## Related Stored Artifacts
- agent-working/staging_artifacts/TCK-20261020-PROMTAIL-DISCOVERY-DENIED-BY-SOCKET-PROXY/ (plan.md, investigation.md, test_plan.md; filed up front)
- agent-working/stored_artifacts/TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD/ (remeasure-2026-10-19/loki/)

## Related Code Areas
- compose.yaml (docker-socket-proxy, promtail)
- docker/promtail config

## Assumptions / Open Questions
- Did Loki ever receive docker logs in this stack? Unknown. Check older records first.

## Implementation Notes
- **Decision (2026-10-20):** NETWORKS=1 on docker-socket-proxy, POST=0 unchanged: owner via lead-planner, 2026-10-20. The compose comment documents what it opens (GET/HEAD /networks and /networks/{id} only), what it exposes, why, and the rejected options (log-file mount, Loki Docker driver). A/B evidence: investigation.md and ab-2026-10-20/.
- **Guard:** Prometheus job promtail (promtail:9080) and base rule LogShippingErrors (error-level log counter, for 10m, noData Alerting, no comparison in the PromQL), runbook docs/runbooks/log-shipping.md. Live proof pending its own slot.
- **Ride-alongs:** the redis-exporter and Grafana compose comments updated to measured figures; api-latency-slo.md carries the #686 note.
Not started.
- Plan requirements (lead, 2026-10-20). The plan must state:
  - the exact proxy env change and every endpoint it opens;
  - whether `docker_sd` can avoid `/networks` (a config option, or a file-based log path such as /var/lib/docker/containers), so we can compare against not widening the proxy;
  - the promtail release-notes line (or code reference) that proves or disproves the 3.6.8 hypothesis;
  - the targets > 0 guard (in scope).
  The `NETWORKS=1` decision goes to the owner through lead, with platform-planner's recommendation.
 Standard tier: plan.md, investigation.md and test_plan.md at dispatch.

## Test Summary
- **validated:** compose config -q (both profiles), promtool check config, YAML parse of the rules, frontmatter, tests/static, the compose hygiene, loki cardinality, platform-domain, allowlist and registry tests (203 passed); done_checker_static PASS.
- **running locally:** the A/B and the live proof of 2026-10-20 (summarised in the Completion Summary; full timelines in `docs/runbooks/records/2026-10-20-log-shipping-fix.md`; evidence in the ticket's stored artifacts: `ab-2026-10-20/`, `proof-2026-10-20/`, `fresh-volume-2026-10-20/`).

## Files Changed
`compose.yaml` (docker-socket-proxy `NETWORKS=1`, comments), `docker/prometheus.yml` (job `promtail`), `docker/grafana/provisioning/alerting/rules-base.yaml` (`LogShippingErrors`), `docs/runbooks/log-shipping.md` (new), `docs/runbooks/{README,target-down,api-latency-slo}.md`, `tools/loadtest/stack_guard.sh` (new), `docs/runbooks/records/2026-10-20-log-shipping-fix.md` (new), this ticket, its stored artifacts and the HARDENING ticket's notes.

## Completion Summary
Loki had no data because promtail's Docker discovery calls the networks API on every refresh and the socket proxy (CONTAINERS=1 only) answered 403, so every refresh failed (code path cited at the loki v3.6.8 and proxy v0.4.1 tags). Fixed with `NETWORKS=1` on the proxy, `POST=0` unchanged (owner via lead-planner, 2026-10-20); the widening is `/networks` only (probes: `GET /networks` and `/networks/<id>` 200; `POST /networks/create`, `DELETE /networks/<id>`, `POST /containers/x/stop`, `GET /volumes`, `GET /images/json`, `GET /info` 403). A guard was added: a Prometheus job `promtail` and the base rule `LogShippingErrors` on promtail's own error-level log counter, with `docs/runbooks/log-shipping.md`. Running locally on 2026-10-20 (record `docs/runbooks/records/2026-10-20-log-shipping-fix.md`): a fresh start with the committed config shipped logs (11/11 targets, a new backend line after `up`) and the rule was Normal with its query at 0; a quiet stack stayed Normal for 11 minutes; a fresh promtail against the 403 fired the alert (Pending 15:21:56Z, Alerting 15:31:59Z, ntfy 15:32:14Z) and it resolved after the restore (ntfy 15:42:14Z); a stopped promtail fired `TargetDown` (ntfy 15:46:17Z) and `LogShippingErrors` through noData (ntfy 15:59:14Z) and both resolved (16:01:17Z and 16:04:14Z). Findings and gaps: (1) the stale-target hypothesis is NOT supported: after a proxy recreation without `NETWORKS` the per-container log streams died and shipping stopped; the 10-18 observation was most likely Loki holding older lines (a hypothesis, not reproduced); (2) lead's original guard on `promtail_targets_active_total` was dropped because promtail 3.6.8 does not export that metric for docker discovery; (3) a comparison inside the PromQL would have turned the healthy case into NoData and fired under noData Alerting, so the threshold lives in Grafana's step; (4) the rule fires on errors that recur at least every 5 minutes for 10 minutes, not on isolated ones; (5) ntfy reached 61 of 64 MiB on the docker stats basis and 58 MiB on anon + active_file (91 percent; 26 MiB anon), so its limit was raised from 64m to 96m in this PR (platform-planner's decision; the new limit was not re-run); (6) one run per failure case. Staging artifacts were written by platform-planner at dispatch and updated at close. Knowledge index refreshed by lead-planner in the main checkout after merge.

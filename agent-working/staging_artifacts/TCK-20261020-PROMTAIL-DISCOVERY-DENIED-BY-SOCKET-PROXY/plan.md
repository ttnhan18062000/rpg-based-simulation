---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261020-PROMTAIL-DISCOVERY-DENIED-BY-SOCKET-PROXY
artifact_type: plan
tags: [platform, observability]
---

# Plan: TCK-20261020-PROMTAIL-DISCOVERY-DENIED-BY-SOCKET-PROXY

Tier standard. Domain platform. Branch platform-implementer-local-promtail-discovery from origin/main. The A/B run happens first: the fix choice depends on it.

## Steps
1. **Code-path proof (read-only).** Cite the promtail 3.6.8 vendored docker discovery refresh: the NetworkList call and the error wrap "error while computing network labels", and what the discovery manager does with targets on a refresh error. Use the GitHub source at the tag, with file and line. Record it in investigation.md.
2. **A/B run** (one light slot that lead clears; observability profile with grafana, loki, promtail, docker-socket-proxy and backend only; memory re-checked; abort if MemAvailable < 1.5 GB or swap > 7.5 GB; a proven watcher before start; down with no -v). States:
   - A: main as is (no NETWORKS), fresh `up`. Expect promtail targets 0/0, the 403 logged, Loki labels empty.
   - B: NETWORKS=1 through a throwaway override file under tools/loadtest/runs/<ts>/ (not committed), `up -d --force-recreate docker-socket-proxy promtail`. Expect targets > 0, Loki `container` labels for the running project containers, and backend lines queryable.
   - C: recreate only the proxy, back without NETWORKS, and leave promtail running. Expect the targets to persist (stale), sent_entries to keep rising, and the 403 to be logged: the 10-18 observation reproduced. Then restart promtail. Expect 0 targets.
   - Proxy surface under B: `GET /networks` 200, `GET /networks/<id>` 200, `POST /networks/create` 403, `DELETE /networks/<id>` 403. Probe from inside promtail, using curl or wget as available in that image, the same way as the 10-19 probe.
   - Outputs go under tools/loadtest/runs/<ts>-promtail-ab/: targets JSON, promtail metrics, logs, Loki labels and query results, the probe codes. Evidence copied into stored_artifacts and scanned for secrets before staging.
3. **Decision gate.** The implementer reports A/B/C. If the stale-target hypothesis holds, the planner sends the recommendation (option 1, NETWORKS=1 GET-only) to lead, and lead takes it to the owner. Nothing is committed in compose.yaml before the owner's yes. If the A/B shows something else, the planner re-plans.
4. **Fix** (after the yes): compose.yaml docker-socket-proxy `NETWORKS=1`. Extend the comment: what it opens (GET /networks and /networks/{id}; POST stays 0), what it exposes, the decision reference (owner via lead, date), and why options 2 and 3 were rejected. Correct the HARDENING ticket's 10-18 "NETWORKS=1 not needed" with a dated note in its Test Summary (do not rewrite history).
5. **Guard**: docker/prometheus.yml job `promtail` (promtail:9080); rules-base.yaml `LogShippingStalled`: noData → Alerting, for 10m, `runbook_url` set; runbook section in target-down.md (or a new log-shipping.md listed in runbooks/README.md); "promtail targets > 0" in the first checks.
6. **Ride-alongs (from the R1/R2 review):**
   - compose comments: the redis-exporter "placeholder" line → "measured 12 MiB peak (anon 10), 2026-10-19 re-measure"; Grafana "Slot (c) verifies" → "re-measure anon 23 % of 1024m; long-run 654 MiB = 64 %".
   - api-latency-slo.md: the #686 note (the entity list is now a bounded summary; the 10-19 plateau predates it), and one measured `/api/v1/entities` size if the stack is up in the A/B. The 10-19 records are not edited.
   - Runbooks: remove the "docker compose logs fallback until Loki works" lines once Loki is proven.
7. **Live proof** after the fix (it can be the same slot as B if the owner's yes comes first; otherwise a second light slot): fresh `up`, then targets > 0, Loki labels, a backend line, sent_entries rising, `LogShippingStalled` Normal. Then stop promtail and see `LogShippingStalled` fire to ntfy (`for` 10m, plus the group wait), then start it again and see it resolved. Down with no -v.

## Scope guards
- No src/** or tests/** edits. No Alloy. No Loki retention or limit changes. No proxy section other than NETWORKS.
- The A/B override file is never committed. NETWORKS goes into compose.yaml only after the owner's yes.
- Each slot is cleared by lead and runs alone.

## AC map
- Root cause with evidence: steps 1-2.
- Logs flow live: step 7.
- Minimum GET-only proxy change, documented: steps 2 (surface probe) and 4.
- Guard: step 5, proven in step 7.
- Runbooks updated: steps 5-6.

---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, observability]
---

# Target-down drill (2026-10-18): stop Loki, the alert reaches ntfy, recover

**Label: running locally** (VM host ubuntu, the 8-service observability subset). Tickets: `TCK-20261018-BASE-ALERT-SCRAPES-AND-NODE-EXPORTER`, `TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES`, `TCK-20261018-BASE-ALERTS-RUNBOOKS-AND-DRILL`. Runbook: [target-down.md](../target-down.md).

## 1. Method and host
- Host: the same VM as `2026-10-18-api-load-test.md` (6 vCPU, 9.7 GiB, swap 8 GiB). Load average about 1.6 and 4.5 GB available at the start; the fleet was running other sessions.
- Code under test: branch `platform-implementer-local-base-alerts`, commit `87eebdbe2` (config of C1, C2 and the runbooks), plus the two local secret files' mode (see section 7).
- Started with `docker compose --profile observability up -d --no-deps` for exactly: ntfy first (alone, to create its user and token), then prometheus, loki, tempo, node-exporter, docker-socket-proxy, promtail, grafana. **Not started:** backend, redis, ai_worker, frontend, watchdog (Prometheus and Grafana depend on a healthy backend, and the drill needs none of them). The existing Grafana volume was reused.
- ntfy: `auth-default-access: deny-all`; user `grafana` (write-only on the one topic) with a token for Grafana; a temporary read-only user `drillreader` to read the topic during the drill. The topic and both tokens are in gitignored or scratch files and appear nowhere below (the captured messages have the topic redacted).
- Drill: stop Loki (T0), poll Grafana's rule state and the ntfy topic every 10 s, start Loki again (T4), poll until the resolved message.

## 2. Configured timings
Rule evaluation 1 m, `for` 2 m, group_wait 30 s, group_interval 5 m, repeat_interval 4 h. Expected detection about 3 to 4 minutes.

## 3. Timeline (UTC, 2026-10-18)
| mark | time | event |
|---|---|---|
| T0 | 12:47:19 | `docker compose stop loki` |
| T1 | 12:48:33 | `TargetDown` for `job=loki` is Pending |
| T2 | 12:50:36 | state Alerting (firing) |
| T3 | 12:50:58 | ntfy "firing" message published (the poll saw it at 12:51:16) |
| T4 | 12:51:16 | `docker compose start loki` |
| - | 12:52:28 | rule state Normal for every job |
| T5 | 12:55:58 | ntfy "resolved" message published (the poll saw it at 12:56:06) |

Detection (T3 - T0): about 3 m 39 s. Recovery (T5 - T4): about 4 m 42 s, which is the group_interval wait for the resolved message, not Loki's start time.

## 4. ntfy messages (topic redacted)
- 12:50:58: title `[firing] TargetDown`, priority 4, tags `bell`, message `Scrape target {{ $$labels.job }} is down` plus `Runbook: docs/runbooks/target-down.md`.
- 12:55:58: title `[resolved] TargetDown`, same message and tags.
- Valid ntfy JSON reached a deny-all server through the write-only token, so the webhook template (`coll.Dict ... | data.ToJSON`) and the bearer auth work.
- **The message text is wrong:** `$$labels` was delivered literally. In Grafana 13.2.4 the provisioning loader does not treat `$$` as an escape and the annotation template did not render. See section 8.

## 5. Checks for the other tickets (same run)
- Targets: `prometheus`, `grafana`, `loki`, `tempo`, `node-exporter`, `ntfy` all `up`.
- node-exporter series: `node_filesystem_avail_bytes` has `mountpoint="/"` (device `/dev/sda2`) and `mountpoint="/data"` (`/dev/sdb1`), with no `/host` prefix, so the rule regex `^(/|/data)$` matches both. It also reports `/etc/hostname`, `/etc/hosts` and `/etc/resolv.conf` bind mounts, which the regex excludes.
- Grafana `/metrics` answers without auth.
- Provisioning: the log shows `starting to provision alerting` and `finished to provision alerting` with no error. Five rules (`for` 2m, 2m, 0s, 10m, 30m), the contact point `ntfy` and the policy read back as provenance `file`. The contact point's credential reads `[REDACTED]` and no `$__file` text remains in its settings.
- **Disk rule, query only (the committed threshold stays 15 percent):** the free-percent expression with a threshold above the current value (`< 40`) returned `/` = 29.24 and `/data` = 26.01; `predict_linear(... [6h], 86400) < 1e12` returned both mounts; at the committed 15 percent the expression returns no series, as it should.
- The test-notification API was not used: the old `receivers/test` endpoint is removed in 13.x and the new one rejected my request body. The real firing and resolved messages prove delivery.

## 6. docker stats (measured on the 8-service subset)
Peak seen over the run and the `mem_limit`:

| service | peak MiB | mem_limit | note |
|---|---|---|---|
| grafana | 559 | 768 m (73 %) | watch when the SLO rules are added; not raised |
| loki | 180 | 512 m | after the restart replay; 71 before |
| prometheus | 88 | 512 m | |
| tempo | 44 | 512 m | |
| promtail | 42 | 128 m | |
| ntfy | 26 | 128 m | placeholder limit, measured 26 |
| docker-socket-proxy | 19 | 64 m | |
| node-exporter | 11 | 64 m | placeholder limit, measured 11 |

Sum of peaks about 970 MiB, above the 500 to 700 MiB estimate; Grafana is the driver. **Full profile:** this subset omits backend, redis, ai_worker, frontend and watchdog. The earlier full-profile idle total was about 710 MiB (hardening and Tempo tickets); the full figure is that plus the new containers' measured peaks (node-exporter 11, ntfy 26) and Grafana's higher peak with alerting loaded, not a new measurement of the full profile.

## 7. Host and secret notes
- The ntfy secret files must be readable by Grafana's container user (uid 472). With mode 0600 the Grafana guard looped on "Permission denied"; they are 0644, accepted for this single-user host. On a multi-user host that is a known limit: use a group-readable mode or a compose-managed secret.
- No root-owned files under this worktree's `data/runs` afterwards. The stack was taken down without `-v`; volumes were kept.

## 8. What the runbook and rules got wrong
- The `$$labels` text in the summary (above). Fixed in the source to a single `$labels`; re-check below.
- The compose header told the user to create the secrets with `umask 077`, which breaks Grafana. Fixed to `chmod 644` with the reason.
- `grafana_alerting_notifications_failed_total` does not appear in `/metrics` at zero (Grafana skips zero-valued series); the name is right and the series appears after a first failure. Failure detection is validated by source only.

## 9. Re-check (pending)
To be filled after the short re-check run: the rendered summary in ntfy, the fixed rule evaluating without error, the deletion of the temporary `drillreader` user, and the time `down` ran.

## 10. Limits
One local host, no on-call; the stack subset, not the full profile; one drill run; the resolved message is delayed by group_interval; no failure of the notifier itself was induced.

---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, observability]
---

# Runbook: disk space (DiskSpaceLow, DiskWillFillIn24h)

Rules in group `base`, from node-exporter (`node_filesystem_*`) for the mounts `/` and `/data`, which are separate mounts on the local host. Both use `noDataState: OK` and `execErrState: OK` (a missing exporter is `TargetDown`).

| Rule | Condition | `for` | Why |
|---|---|---|---|
| `DiskSpaceLow` | free space below 15 percent of the mount | 10m | 15 percent leaves time to react on a disk that is about 70 percent used; 10m ignores short build or image-pull spikes |
| `DiskWillFillIn24h` | `predict_linear` over 6h of free bytes is below 0 at +24h | 30m | catches a steady fill that the percentage rule would only see late; 30m filters transient growth |

## Heavy local work can trip DiskWillFillIn24h
`predict_linear` over 6 hours projects the recent slope forward, so heavy local work (image builds, CI artifact downloads, load tests) can fire `DiskWillFillIn24h` while the disk is still far from full. This was seen on 2026-10-19 for `/` from 17:14:51 to 17:29:51 UTC, during an image build and a 50-user soak (see the [2026-10-19 record](records/2026-10-19-api-slo-alert-fire-test.md)). It resolved by itself. The tuning follow-up is `TCK-20261020-DISK-FILL-ALERT-TUNING`; the rule was not changed. If it fires during such work, check `df -h` first: a large free percentage and a recent build or download mean the alert is the slope, not the level.

## First three checks
1. `df -h / /data`: which mount, and how full.
2. `docker system df`: images, containers, volumes and build cache.
3. `du -xh --max-depth=1 /data | sort -h | tail` (or `/`): what grew. `data/runs` and the Docker data root are the usual suspects.

## Known causes
Docker images and build cache; `data/runs` from simulation runs; the Prometheus, Loki and Tempo volumes (retention is short, 24h for Tempo); a runaway log file.

## Mitigation
`docker builder prune` and `docker image prune` for build and image space. Remove only your own run directories by run id, with `python3 tools/gate_checks/done_checker_static.py --clean-data-runs --path <run_id>`; never `rm -rf data/runs/*`. Root-owned run directories are the owner's to remove. Do not delete the Grafana, Prometheus, Loki or Tempo volumes to free space without the owner.

## Proof without filling a disk
The committed threshold stays 15 percent and there is no override. The expression is proven by query: run it in Explore or the Prometheus API with a threshold above the current free percent and record the output (see the drill record).

## Silence and escalate
See the README. Escalate to the owner if free space keeps falling after the mitigations.

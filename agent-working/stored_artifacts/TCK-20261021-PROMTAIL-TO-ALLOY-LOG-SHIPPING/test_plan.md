---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261021-PROMTAIL-TO-ALLOY-LOG-SHIPPING
phase: test_plan
date: 2026-10-28
tags: [observability, platform]
---

# Test plan: TCK-20261021-PROMTAIL-TO-ALLOY-LOG-SHIPPING

Static (no stack): `docker compose --profile observability config` lists alloy and no promtail; `alloy validate` (or `alloy fmt --verbose`) on docker/alloy/config.alloy in the pinned image; promtool/yaml load of prometheus.yml and the alert provisioning; the label-guard draft test passes against the Alloy config (draft only, not committed without OK).
Live (one heavy slot, lead-cleared, abort watcher proven first): fresh `up` of the observability profile; Alloy targets show this project's containers only with another project's container running; a new backend line queryable with labels container, job=varlogs, level, component and no tick/message label; LogShippingErrors Normal on a quiet stack (>= 10 samples); 403 case (fresh Alloy, throwaway NETWORKS=0 override) fires; stopped Alloy fires (TargetDown and NoData path); recreate Alloy and check duplicate/replay behaviour; memory sampled for anon + active_file.

## Added by platform-planner (2026-10-28)
- Case 4, Loki unreachable: stop loki with alloy running; record the rate terms (retries, dropped), rule state and ntfy; restart loki and confirm resolve.
- Memory: sample alloy anon + active_file (sample_stats.sh) under normal shipping for the whole run; justify mem_limit 192m from it in the record.
- Recreate check: with a known marker line per second before and after `up -d --force-recreate alloy`, count in Loki what is replayed (duplicates) or missing (gap); record both numbers.
- Dated record: docs/runbooks/records/2026-10-28-alloy-log-shipping.md.

## Proof Plan
- Level: live stack (observability profile) plus static checks.
- Proof kind: measured behaviour on the running stack, and a unit-level guard test.
- Oracle source: Grafana rule state API, Prometheus query, Loki label and query API, cgroup memory files.
- Expected effect: Normal on a quiet stack; Alerting on the 403, stopped and Loki-unreachable cases; labels container, job, level, component and no tick or message.
- Selected commands: `pytest tests/logging/test_loki_cardinality.py`; `docker compose --profile observability config`; `alloy validate`; the case script `proof-2026-10-28/cases.sh`.

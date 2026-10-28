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

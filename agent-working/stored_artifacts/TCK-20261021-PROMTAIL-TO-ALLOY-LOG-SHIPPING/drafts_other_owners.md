---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261021-PROMTAIL-TO-ALLOY-LOG-SHIPPING
phase: drafts
date: 2026-10-28
tags: [observability, platform]
---

# Exact before/after text for files platform does not own

Platform-planner routes each block to its owner. Not applied in this branch. The architecture-doc lines at `devops_baseline_adr.md` L24 and L29 describe the dated baseline and are left as written (listed so lead can decide).

## docs/architecture/devops_baseline_adr.md (lead-planner), L41, row D1
Before: `... `prometheus`, `grafana`, `loki`, `promtail` (and `tempo`, D4) get `profiles: [observability]` ...`
After:  `... `prometheus`, `grafana`, `loki`, `alloy` (and `tempo`, D4) get `profiles: [observability]` ...`
Add at the end of the D1 rationale cell: ` Promtail (end of life 2026-03-02) was replaced by Grafana Alloy on 2026-10-28 (TCK-20261021-PROMTAIL-TO-ALLOY-LOG-SHIPPING); log shipping only, no metrics or traces.`

## docs/architecture/system_overview.md (lead-planner)
L36 before: `    PT["Promtail"] -- "container logs" --> L["Loki"]`
L36 after:  `    PT["Alloy"] -- "container logs" --> L["Loki"]`
L70 before: `| Metrics, dashboards and logs | Prometheus, Grafana, Loki, Promtail | running locally |`
L70 after:  `| Metrics, dashboards and logs | Prometheus, Grafana, Loki, Alloy | running locally |`

## docs/engine/contracts/infrastructure_overview.md (rpg-planner)
L36 before: `    Container["Container stdout"] -->|Promtail| Loki["Loki"]`
L36 after:  `    Container["Container stdout"] -->|Alloy| Loki["Loki"]`
L155 before: `... `prometheus.yml`, `promtail-config.yml` and `grafana/` live under `docker/`):`
L155 after:  `... `prometheus.yml`, `alloy/config.alloy` and `grafana/` live under `docker/`):`
L163 before: `*   **`loki` & `promtail`**: Multi-container centralized log aggregator.`
L163 after:  `*   **`loki` & `alloy`**: Multi-container centralized log aggregator (Alloy ships container logs to Loki).`

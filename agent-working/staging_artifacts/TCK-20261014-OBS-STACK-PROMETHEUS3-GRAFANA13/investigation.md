---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261014-OBS-STACK-PROMETHEUS3-GRAFANA13
artifact_type: investigation
tags: [platform]
---

# investigation — TCK-20261014-OBS-STACK-PROMETHEUS3-GRAFANA13

Current state (main @ 7fa1fc7bc):
- `compose.yaml`: `prom/prometheus:v2.50.0@sha256:042258e3…`, command flags `--config.file`, `--storage.tsdb.path`; healthcheck `wget --spider http://localhost:9090/-/healthy`. `grafana/grafana:10.3.3@sha256:8640e503…`; healthcheck `/api/health`; env `GF_SECURITY_ADMIN_PASSWORD`; mounts `docker/grafana/provisioning` and `docker/grafana/dashboards`.
- `docker/prometheus.yml`: global 5s scrape/eval, one job `rpg-backend` → `backend:8000`. No rules, no remote_write, no feature flags.
- Provisioning: `docker/grafana/provisioning/datasources/datasource.yml`, `dashboards/dashboard.yml`; one dashboard `docker/grafana/dashboards/simulation.json`.
Risks to check:
- Prometheus v3: removed feature flags (none used here), the new UI, stricter scrape content-type negotiation (`fallback_scrape_protocol` may be needed if the backend's `/metrics` Content-Type is unusual), changed `/-/healthy` response body (the healthcheck uses status only), and the TSDB volume `prometheus_data` written by v2 (v3 reads v2 blocks; downgrade is not supported).
- Grafana 11-13: AngularJS panel plugins removed (any `graph`/`table-old`/`singlestat` panels in simulation.json must be migrated to `timeseries`/`table`/`stat`); provisioning schema `apiVersion: 1` unchanged; `grafana_data` volume migrates forward on start (one way).
Dependabot #563/#564 carry only the tag changes and none of these checks.

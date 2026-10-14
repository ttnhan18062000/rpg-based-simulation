---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261014-OBS-STACK-PROMETHEUS3-GRAFANA13
artifact_type: test_plan
tags: [platform]
---

# test_plan — TCK-20261014-OBS-STACK-PROMETHEUS3-GRAFANA13

- Check `compose config -q` with and without the profile.
- Run the stack on fresh volumes: all profile services reach healthy within 2 minutes.
- Prometheus `/api/v1/targets`: `rpg-backend` health `up`.
- Grafana `/api/datasources/uid/<uid>/health` (or the datasource test) returns OK; `/api/dashboards/uid/<uid>` loads, and the dashboard renders with no "panel plugin not found" (screenshot or API output).
- Existing-volume upgrade: start v3/13 on the v2/10 volumes left by the previous run; both start healthy (records the one-way migration).
- Regression: the default profile (4 services) is unchanged and healthy; publish-images PR build stays green.
Evidence labels: running locally, validated.

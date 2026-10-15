---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261014-OBS-STACK-PROMETHEUS3-GRAFANA13
artifact_type: plan
tags: [platform]
---

# plan — TCK-20261014-OBS-STACK-PROMETHEUS3-GRAFANA13

1. Resolve the current Prometheus 3.x and Grafana 13.x exact tags and their multi-arch index digests (`docker buildx imagetools inspect`); update both `image:` lines in the existing comment style.
2. Check the prometheus.yml and compose flags against the v3 migration guide; add `fallback_scrape_protocol` only if the backend scrape fails.
3. Open `simulation.json` and replace any Angular panel types with their current equivalents; keep queries and layout.
4. Run `docker compose --profile observability up -d` on fresh volumes (`down -v` for the obs volumes only, never redis_data), then on existing volumes, and collect the evidence in the test plan.
5. Record each change and the evidence in the ticket.

## Plan outcome (2026-10-14, platform-implementer)
Implemented as planned, plus two changes found while running the stack: Grafana `mem_limit` raised to 768m and a 120s `start_period` on its health check (Grafana 13 hit 256m and restarted once, and its first start migrates the 10.x data volume slowly). Prometheus v3 needed no config change.

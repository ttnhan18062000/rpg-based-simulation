---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-OBSERVABILITY-PROFILE-HARDENING
artifact_type: investigation
tags: [platform, observability, security]
---

# Investigation: TCK-20261018-OBSERVABILITY-PROFILE-HARDENING

**Written retrospectively at ticket close (2026-10-20).** Findings recorded in the ticket's Implementation Notes and Test Summary: Grafana started with admin/admin on an empty secret file (fixed by the entrypoint guard); the `grafana_data` volume from that test kept the old password until the volume was replaced; the 2026-10-18 conclusion that `NETWORKS=1` was not needed was wrong: promtail's discovery calls `GET /networks` on every refresh and fails with a 403 without it (`TCK-20261020-PROMTAIL-DISCOVERY-DENIED-BY-SOCKET-PROXY`, whose A/B showed a fresh promtail ships nothing without `NETWORKS=1`); the 10-18 observation of logs arriving was most likely Loki holding older lines. The fresh-volume check of 2026-10-20 (owner removed `platform_grafana_data`): real password 200, admin/admin 401.

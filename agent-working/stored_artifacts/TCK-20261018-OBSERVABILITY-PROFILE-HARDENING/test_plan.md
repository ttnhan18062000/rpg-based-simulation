---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-OBSERVABILITY-PROFILE-HARDENING
artifact_type: test_plan
tags: [platform, observability, security]
---

# Test plan: TCK-20261018-OBSERVABILITY-PROFILE-HARDENING

**Written retrospectively at ticket close (2026-10-20).**

## Proof Plan
| criterion | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| compose config valid with and without the secret file | static | config validation | none: criterion from the ticket AC | exit 0 for both profiles | `docker compose config -q`; `docker compose --profile observability config -q` |
| missing secret file fails Grafana's start; empty file exits with a message | runtime, local | live service check | none: criterion from the ticket AC | bind-mount error; entrypoint guard message | `docker compose --profile observability up -d grafana` (2026-10-18) |
| real password logs in, admin/admin refused, on a fresh volume | runtime, local | live service check | none: criterion from the ticket AC | 200 and 401 | `curl -K -` with the secret on stdin (2026-10-20) |
| ports bound to 127.0.0.1; socket mounted only by the proxy; POST through the proxy refused | runtime, local | live checks | none: criterion from the ticket AC | `ss -ltnH`; `docker inspect`; 403 on POST | 2026-10-18 and the 2026-10-20 probes |
| backend logs reach Loki | runtime, local | end-to-end check | none: criterion from the ticket AC | a new line after `up`, sent entries rising | the 2026-10-20 proof in the promtail ticket (the 10-18 check was not reliable: it could not tell old lines from new) |
| compose hygiene and platform-domain tests | static | test run | none: criterion from the ticket AC | pass | `pytest tests/architecture/test_docker_compose_dependency_hygiene.py tests/tools/test_session_platform_domain.py tests/logging/test_loki_cardinality.py` |

---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-AI-WORKER-SCRAPE-AND-LAG-ALERT
artifact_type: test_plan
tags: [platform, observability]
---

# Test plan: TCK-20261018-AI-WORKER-SCRAPE-AND-LAG-ALERT

## Proof Plan
- Static: YAML parses; no `$` in rule files; tests/static and the platform/registry tests pass.
- Live: ai_worker target up and container healthy; observation of lag and pending under engine load sets thresholds; idle worker still serves lag; `--scale ai_worker=2` shows two targets up; stopping ai_worker while the engine publishes fires `AiWorkerLagHigh` to ntfy and it resolves after restart, with timestamps; a fresh start is Normal.

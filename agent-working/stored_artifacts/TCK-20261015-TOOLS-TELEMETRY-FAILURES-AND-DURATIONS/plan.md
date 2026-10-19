---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261015-TOOLS-TELEMETRY-FAILURES-AND-DURATIONS
artifact_type: plan
tags: [agent-monitoring, hooks, data-quality]
---

# plan — TCK-20261015-TOOLS-TELEMETRY-FAILURES-AND-DURATIONS

1. PostToolUseFailure handling in the post hook with a closed error-class set. 2. Per-call start stamps keyed by session_id + tool_use_id, payload duration first, null when unpaired. 3. Retro: pre-field zero hand closures are unknown. 4. Measure the missing tools shards and file the follow-up. 5. Owner applies the settings.json diff (not edited here).

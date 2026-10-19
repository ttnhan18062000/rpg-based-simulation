---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261015-TOOLS-TELEMETRY-FAILURES-AND-DURATIONS
artifact_type: investigation
tags: [agent-monitoring, hooks, data-quality]
---

# investigation — TCK-20261015-TOOLS-TELEMETRY-FAILURES-AND-DURATIONS

Source: RETRO-2026-W41 final note finding 3. All 6,957 W41+W42 tool rows had `status: ok` because no PostToolUseFailure hook was wired and `tool_response.is_error` is not what a failing Bash call carries. `duration_ms` came from one shared `.claude/.tool_start` overwritten by every concurrent session (a `cat` at 8.6 h). Coverage numbers: see the implementation notes of the ticket.

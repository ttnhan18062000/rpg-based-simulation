"""Codex `PostToolUse` monitoring adapter (TCK-20260730-CODEX-POSTTOOL-ADAPTER).

Parses and validates a captured Codex `PostToolUse` hook stdin payload into the shared
`tools.jsonl` record shape (`provider="codex"`, a redacted summary of `tool_input`, a derived
`status` flag never carrying `tool_response` content, and a validated execution identity), and
delegates the actual append to `tools/agent-monitoring/writer.py`'s `write_line` — never a second
append mechanism.

This package never invokes `codex exec` (that is `tools/agent_replay_codex/`'s responsibility)
and never governs pilot ticket-selection/rollback/signoff (that is
`tools/agent_codex_pilot_guardrails/`'s responsibility). It is real, tested, importable code that
stays operationally inert: nothing in the committed `.codex/config.toml` invokes it, and its own
live-append gate (`live_gate.require_live_append`) defaults closed — proven mechanically by
`tests/agent_codex_posttool_adapter/test_no_subprocess_and_no_live_wiring.py`.
"""

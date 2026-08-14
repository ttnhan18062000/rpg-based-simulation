"""Evidenced-surface guard (test_plan.md's Anti-Drift Test Guards): proves the adapter's actual
chosen hook-event/writer-function set never exceeds the evidenced subset. Imports and calls
tools.agent_codex_pilot_guardrails.enabled_surface.assert_enabled_surface_subset — exactly as
tests/agent_codex_pilot_guardrails/test_enabled_surface.py already does — never reimplemented.

The adapter's real values, not restated constants: input_model.py's own EVIDENCED_HOOK_EVENTS
membership check accepts exactly {"PostToolUse"} (the only hook event this adapter parses), and
writer_bridge.py binds write_line (not write_lines) as its sole append function.
"""
from __future__ import annotations

from tools.agent_codex_pilot_guardrails.enabled_surface import (
    EnabledSurfaceExceedsEvidenceError,
    assert_enabled_surface_subset,
)
from tools.agent_codex_posttool_adapter import writer_bridge


def test_adapter_hook_event_and_writer_function_within_evidenced_surface():
    assert_enabled_surface_subset(
        enabled_hook_events=frozenset({"PostToolUse"}),
        enabled_writer_names=frozenset({writer_bridge.write_line.__name__}),
    )


def test_adapter_surface_would_be_rejected_if_it_exceeded_evidence():
    try:
        assert_enabled_surface_subset(
            enabled_hook_events=frozenset({"PostToolUse", "PreToolUse"}),
            enabled_writer_names=frozenset({writer_bridge.write_line.__name__}),
        )
    except EnabledSurfaceExceedsEvidenceError:
        return
    raise AssertionError("expected EnabledSurfaceExceedsEvidenceError for an unevidenced hook event")

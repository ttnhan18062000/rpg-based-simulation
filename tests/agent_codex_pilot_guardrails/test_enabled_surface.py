"""Tests for tools/agent_codex_pilot_guardrails/enabled_surface.py
(TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS, Step 3)."""
from __future__ import annotations

import pytest

from tools.agent_codex_pilot_guardrails.enabled_surface import (
    EVIDENCED_HOOK_EVENTS,
    EVIDENCED_WRITER_FUNCTIONS,
    assert_enabled_surface_subset,
    assert_evidenced_events_are_schema_valid,
)
from tools.agent_codex_pilot_guardrails.errors import EnabledSurfaceExceedsEvidenceError


def test_evidenced_hook_events_is_exactly_post_tool_use():
    assert EVIDENCED_HOOK_EVENTS == frozenset({"PostToolUse"})


def test_evidenced_writer_functions_is_exactly_write_line_and_write_lines():
    assert EVIDENCED_WRITER_FUNCTIONS == frozenset({"write_line", "write_lines"})


def test_evidenced_events_are_schema_valid_against_real_contract():
    assert_evidenced_events_are_schema_valid()  # must not raise


def test_subset_input_passes():
    assert_enabled_surface_subset(frozenset({"PostToolUse"}), frozenset({"write_line"}))


def test_schema_valid_but_not_evidenced_hook_event_is_rejected():
    # PreToolUse is schema-valid (agent-orchestration/hook-events.yaml declares it) but never
    # fixture-captured for Codex — proves this is a real subset assertion, not a hardcoded
    # equality check that trivially passes.
    with pytest.raises(EnabledSurfaceExceedsEvidenceError):
        assert_enabled_surface_subset(frozenset({"PreToolUse"}), frozenset())


def test_unevidenced_writer_function_is_rejected():
    with pytest.raises(EnabledSurfaceExceedsEvidenceError):
        assert_enabled_surface_subset(frozenset(), frozenset({"raw_open_append"}))

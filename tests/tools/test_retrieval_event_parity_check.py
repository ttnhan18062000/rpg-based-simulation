"""Tests for tools/retrieval_event_parity_check.py (TCK-20260729-RETRIEVAL-EVENT-PARITY-CHECK).

This test module exercises structural/field-shape parity only, not live cross-provider parity —
no real Codex or Claude Code execution occurs anywhere in these tests, and no
CODEX_REPLAY_PARITY_LIVE_CONSENT gate is touched.
"""
from __future__ import annotations

import inspect

import pytest

import tools.retrieval_event_parity_check as parity_check_mod
from tools import retrieval_events as re_mod
from tools.retrieval_event_parity_check import (
    ProviderFieldViolationError,
    assert_no_provider_specific_fields,
)


def test_field_set_contains_no_provider_specific_field():
    assert_no_provider_specific_fields(re_mod.RETRIEVAL_EVENT_FIELDS)


def test_execution_id_and_provider_absent_from_retrieval_event_fields():
    assert "execution_id" not in re_mod.RETRIEVAL_EVENT_FIELDS
    assert "provider" not in re_mod.RETRIEVAL_EVENT_FIELDS

    assert_no_provider_specific_fields(re_mod.RETRIEVAL_EVENT_FIELDS)


def test_negative_control_raises_when_provider_specific_field_injected():
    codex_injected = frozenset(re_mod.RETRIEVAL_EVENT_FIELDS | {"codex_latency_ms"})
    with pytest.raises(ProviderFieldViolationError) as exc_info:
        assert_no_provider_specific_fields(codex_injected)
    assert type(exc_info.value) is ProviderFieldViolationError

    claude_injected = frozenset(re_mod.RETRIEVAL_EVENT_FIELDS | {"claude_cache_status"})
    with pytest.raises(ProviderFieldViolationError) as exc_info:
        assert_no_provider_specific_fields(claude_injected)
    assert type(exc_info.value) is ProviderFieldViolationError


def test_negative_control_raises_on_execution_id_or_provider_injection():
    with pytest.raises(ProviderFieldViolationError):
        assert_no_provider_specific_fields(
            frozenset(re_mod.RETRIEVAL_EVENT_FIELDS | {"execution_id"})
        )
    with pytest.raises(ProviderFieldViolationError):
        assert_no_provider_specific_fields(
            frozenset(re_mod.RETRIEVAL_EVENT_FIELDS | {"provider"})
        )


def test_docstring_and_test_names_state_structural_only_not_live_parity():
    module_doc = parity_check_mod.__doc__.lower()
    assert "structural" in module_doc
    assert "live" in module_doc
    assert "not live cross-provider parity" in module_doc

    fn_name = assert_no_provider_specific_fields.__name__
    assert "live" not in fn_name
    assert "output" not in fn_name
    assert "execution" not in fn_name


def test_check_is_read_only_and_never_touches_real_monitoring_files():
    source = inspect.getsource(parity_check_mod)
    assert "open(" not in source
    assert "Path(" not in source
    assert "agent-monitoring" not in source
    for forbidden in (
        "CODEX_REPLAY_PARITY_LIVE_CONSENT",
        "consent_gate",
        "invoker",
        "shadow_mode",
    ):
        assert forbidden not in source

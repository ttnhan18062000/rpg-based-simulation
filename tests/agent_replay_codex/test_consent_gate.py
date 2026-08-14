"""Tests for tools/agent_replay_codex/consent_gate.py (TCK-20260721-CODEX-REPLAY-PARITY, Step 2)."""
from __future__ import annotations

import pytest

from tools.agent_replay_codex.consent_gate import CONSENT_ENV_VAR, require_live_consent
from tools.agent_replay_codex.errors import ConsentNotGrantedError


def test_require_live_consent_raises_when_env_var_unset():
    with pytest.raises(ConsentNotGrantedError):
        require_live_consent(env={})


def test_require_live_consent_raises_on_truthy_but_not_exact_value():
    with pytest.raises(ConsentNotGrantedError):
        require_live_consent(env={CONSENT_ENV_VAR: "true"})


def test_require_live_consent_raises_on_zero_value():
    with pytest.raises(ConsentNotGrantedError):
        require_live_consent(env={CONSENT_ENV_VAR: "0"})


def test_require_live_consent_passes_on_exact_string_one():
    require_live_consent(env={CONSENT_ENV_VAR: "1"})


def test_consent_gate_module_never_imports_subprocess():
    import sys

    import tools.agent_replay_codex.consent_gate as mod

    assert "subprocess" not in vars(mod)
    assert "subprocess" not in getattr(sys.modules[mod.__name__], "__dict__", {})

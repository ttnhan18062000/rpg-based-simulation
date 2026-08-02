from __future__ import annotations

from types import SimpleNamespace

from tools.agent_codex_live_transport.invoker import _hook_environment


def test_hook_environment_threads_identity_only_and_preserves_all_human_gates(monkeypatch):
    monkeypatch.setenv("CODEX_LIVE_PILOT_HUMAN_SIGNOFF", "1")
    monkeypatch.setenv("CODEX_REALREPO_PILOT_LIVE_CONSENT", "1")
    monkeypatch.setenv("CODEX_POSTTOOL_ADAPTER_LIVE_APPEND", "1")
    monkeypatch.setenv("CODEX_HOOK_EXECUTION_ID", "ambient-wrong-value")
    context = SimpleNamespace(
        execution_id="codex-TCK-20260801-MONITORING-WRITER-STATUS-STALE-1-deadbeef",
        ticket_id="TCK-20260801-MONITORING-WRITER-STATUS-STALE",
    )

    env = _hook_environment(SimpleNamespace(context=context))

    assert env["CODEX_HOOK_EXECUTION_ID"] == context.execution_id
    assert env["CODEX_HOOK_TICKET_ID"] == context.ticket_id
    assert env["CODEX_HOOK_RUN_ID"] == context.ticket_id
    assert env["CODEX_HOOK_SEQ_START"] == "1"
    assert env["CODEX_HOOK_PHASE"] == "PostToolUse"
    assert env["CODEX_HOOK_AGENT"] == "codex-posttool-hook"
    assert env["CODEX_LIVE_PILOT_HUMAN_SIGNOFF"] == "1"
    assert env["CODEX_REALREPO_PILOT_LIVE_CONSENT"] == "1"
    assert env["CODEX_POSTTOOL_ADAPTER_LIVE_APPEND"] == "1"

"""Guardrail, rollback, and sign-off *mechanisms only* for a future live Codex pilot
(TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS).

This package has no live-execution entry point. It builds: a typed human-owner/rollback-plan
pilot-request manifest and loader; ticket-selection rejection rules (missing owner/rollback-plan,
concurrent same-work provider claim); an evidenced-subset guard restricting the enabled
hook-event/writer-function surface; a pre/post baseline-monitoring-manifest fail-closed gate; a
scratch-only Codex-adapter config enable/disable toggle with a zero-byte-diff rollback proof; and
a human sign-off gate distinct from and later than ticket selection. None of these mechanisms
invokes `codex exec`, enables a hook in the real committed .codex/config.toml, or writes Codex
output to any real ticket file — proven mechanically by
tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py.
"""

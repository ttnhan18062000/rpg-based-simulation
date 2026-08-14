"""Divergence-registration test (TCK-20260721-CODEX-REPLAY-PARITY, Step 10, AC #4's registration
half). Proves the reuse path (Step 8's fail-safe branch) actually works, independent of whether a
real divergence is ever found. Uses tools.agent_orchestration_claude_adapter.divergence_log
unmodified.
"""
from __future__ import annotations

from tools.agent_orchestration_claude_adapter.divergence_log import is_approved, load_divergences

_RATIFIED_ENTRY = """\
## codex_parity:FAKE-TICKET
Axis: codex_parity
Contract-value: final_status=ok
Live-value: final_status=TIMEOUT
Rationale: synthetic test entry
Approved-by: test-operator
Approved-date: 2026-07-27
Status: RATIFIED
"""

_DEFERRED_ENTRY = """\
## codex_parity:FAKE-TICKET-DEFERRED
Axis: codex_parity
Contract-value: final_status=ok
Live-value: final_status=TIMEOUT
Rationale: synthetic test entry
Approved-by: test-operator
Approved-date: 2026-07-27
Status: DEFERRED
"""


def test_is_approved_recognizes_a_ratified_codex_parity_entry(tmp_path):
    doc_path = tmp_path / "intentional-divergences.md"
    doc_path.write_text(_RATIFIED_ENTRY, encoding="utf-8")

    divergences = load_divergences(doc_path)
    assert is_approved(divergences, "codex_parity", "FAKE-TICKET") is True


def test_is_approved_rejects_a_deferred_codex_parity_entry(tmp_path):
    doc_path = tmp_path / "intentional-divergences.md"
    doc_path.write_text(_DEFERRED_ENTRY, encoding="utf-8")

    divergences = load_divergences(doc_path)
    assert is_approved(divergences, "codex_parity", "FAKE-TICKET-DEFERRED") is False

"""Phase-order conformance test: rendered Claude adapter representation vs. LIVE
`.claude/workflows/implement-ticket.js` (TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER, AC #2).

Reuses `tools.gate_checks.workflow_meta_conformance.extract_meta_phases` directly — no
reimplementation of its bracket-depth-scan/regex technique. Runs `render_claude_adapter()` against
a `tmp_path` target (not the committed file), so this test is self-contained and does not depend
on the committed `agent-orchestration/rendered/claude-adapter.yaml` being fresh — freshness is
Step 8's (test_claude_containment.py's) concern.

Any mismatch is checked against `divergence_log.is_approved()` before the test hard-fails — see
`agent-orchestration/intentional-divergences.md` for the human-approval mechanism. As of this
ticket's own build, phase order matches exactly, so nothing needs approval.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from tools.agent_orchestration_claude_adapter.divergence_log import is_approved, load_divergences
from tools.agent_orchestration_claude_adapter.generator import render_claude_adapter
from tools.gate_checks.workflow_meta_conformance import extract_meta_phases

_REPO_ROOT = Path(__file__).parent.parent.parent
_WORKFLOW_JS_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"
_DIVERGENCE_LOG_PATH = _REPO_ROOT / "agent-orchestration" / "intentional-divergences.md"


def test_phase_order_conformance_byte_identical_to_live_meta_phases(tmp_path):
    live_phase_order = extract_meta_phases(_WORKFLOW_JS_PATH)

    output_path = render_claude_adapter(_REPO_ROOT, tmp_path, allow_outside_contract=True)
    rendered = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    rendered_phase_order = rendered["phase_order"]

    if live_phase_order == rendered_phase_order:
        return

    divergences = load_divergences(_DIVERGENCE_LOG_PATH)
    assert is_approved(divergences, axis="phase_order", value="phase_order"), (
        f"phase order mismatch: live={live_phase_order!r} vs rendered={rendered_phase_order!r}, "
        f"and no matching human-approved entry found in {_DIVERGENCE_LOG_PATH}"
    )


def test_live_phase_order_has_the_expected_12_phases():
    live_phase_order = extract_meta_phases(_WORKFLOW_JS_PATH)
    assert live_phase_order == [
        "Scope",
        "Investigate",
        "Plan",
        "Review",
        "Implement",
        "Document-Update",
        "Architecture-Verify",
        "Test",
        "Parity",
        "Security-Review",
        "Verify",
        "Finalize",
    ]

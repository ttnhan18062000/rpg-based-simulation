"""One-time bootstrap-correctness check for workflows/implement-ticket.yaml's phase/agent
vocabulary (TCK-20260721-ORCHESTRATION-CONTRACT-CORE).

IMPORTANT FRAMING — read before touching this file: this test is a ONE-TIME bootstrap
correctness check, run while `.claude/workflows/implement-ticket.js` remains the live
production workflow and `tools/agent-monitoring/vocabulary.py` remains the legacy, operative
source of truth for its phase/agent names. It is NOT an ongoing single-source-of-truth
guarantee the way tests/tools/test_validate_agent_monitoring.py's
test_canonical_vocabulary_single_sourced identity check is (that test asserts two live modules
share the same Python object; this test asserts a value-equality snapshot between YAML data and
vocabulary.py, taken once at bootstrap time). Do not "fix" a future failure of this test by
re-syncing the YAML to vocabulary.py forever — once provider adapters exist, this contract is
meant to become the upstream authority and vocabulary.py becomes generated/validated FROM it,
not the reverse (see agent-orchestration/README.md). Rewording this docstring to claim a
permanent two-way binding would reintroduce the reversed-ownership bug this ticket's own history
records being corrected once already.
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import vocabulary  # noqa: E402

from agent_orchestration.loader import load_contract  # noqa: E402


def test_bootstrap_phase_agent_vocabulary_matches_vocabulary_py():
    """One-time bootstrap-correctness check — see module docstring. Not an ongoing sync
    guarantee: vocabulary.py remains the legacy source of truth today; the contract does not
    stay generated-from-or-equal-to it forever."""
    bundle = load_contract(_REPO_ROOT)

    contract_phase_names = {phase["name"] for phase in bundle.workflow["phases"]}
    assert contract_phase_names == vocabulary.WORKFLOW_PHASES["implement-ticket"]

    contract_agent_ids = set(bundle.workflow["agents"])
    expected_agents = vocabulary.WORKFLOW_AGENTS["implement-ticket"] - {"implement-ticket-orchestrator"}
    assert contract_agent_ids == expected_agents


def test_bootstrap_equality_test_docstring_states_one_time_not_permanent():
    """Meta-test: forces the correct one-time-bootstrap framing to exist in this module's
    docstring, guarding against silently reverting to a permanent two-way sync claim — the exact
    reversed-ownership bug this ticket's own history (Codex review correction #1) already fixed
    once."""
    doc = inspect.getdoc(sys.modules[__name__]) or ""
    lowered = doc.lower()
    assert "one-time" in lowered or "bootstrap" in lowered
    assert "legacy" in lowered and "source of truth" in lowered
    assert "reversed-ownership" in lowered or "not an ongoing" in lowered

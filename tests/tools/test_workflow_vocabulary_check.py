"""Tests for tools/gate_checks/workflow_vocabulary_check.py
(TCK-20260924-WORKFLOW-AGENT-LITERAL-VOCABULARY-CHECK)."""
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "gate_checks"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "agent-monitoring"))

import workflow_vocabulary_check  # noqa: E402
import vocabulary  # noqa: E402
from workflow_vocabulary_check import (  # noqa: E402
    check_workflow_vocabulary,
    extract_literals_from_workflow_file,
)
from vocabulary import WORKFLOW_AGENTS, WORKFLOW_PHASES  # noqa: E402


def _patch_registries(monkeypatch, agents: dict, phases: dict) -> None:
    """Patch both this module's own imported names AND vocabulary.py's module globals.

    `check_workflow_vocabulary()`'s own "is this file keyed" test reads
    `workflow_vocabulary_check.WORKFLOW_AGENTS`/`WORKFLOW_PHASES` (imported names in that module's
    namespace), but `is_known_agent()`/`is_known_phase()` are DEFINED in vocabulary.py and read
    its module globals directly -- patching only one half would leave literal resolution reading
    real, unpatched production registries while the keyed-file check reads the fixture ones.
    """
    monkeypatch.setattr(workflow_vocabulary_check, "WORKFLOW_AGENTS", agents, raising=False)
    monkeypatch.setattr(workflow_vocabulary_check, "WORKFLOW_PHASES", phases, raising=False)
    monkeypatch.setattr(vocabulary, "WORKFLOW_AGENTS", agents, raising=False)
    monkeypatch.setattr(vocabulary, "WORKFLOW_PHASES", phases, raising=False)

REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_WORKFLOWS_DIR = REPO_ROOT / ".claude" / "workflows"

# The exact 6 agent / 23 phase literals confirmed unregistered by this ticket's own
# investigation.md re-derivation, BEFORE the vocabulary.py registry change this ticket also makes.
# Recorded here as a frozen snapshot (not re-derived from git history) so AC2 stays a pinned,
# reproducible assertion independent of vocabulary.py's current (post-fix) state.
_PRE_FIX_WORKFLOW_AGENTS = {
    "implement-ticket": WORKFLOW_AGENTS["implement-ticket"],
    "create-tickets": {"create-tickets", "structure", "ticket-scoper", "link-epic",
                        "concern-investigator", "orchestrator", "write-sequence"},
    "implement-epic": {"implement-ticket", "implement-epic"},
    "simq-audit": WORKFLOW_AGENTS["simq-audit"],
}
_PRE_FIX_WORKFLOW_PHASES = {
    "implement-ticket": WORKFLOW_PHASES["implement-ticket"],
    "create-tickets": {"Comprehend", "Investigate", "Structure", "Write", "Link"},
    "implement-epic": {"Implement"},
    "simq-audit": WORKFLOW_PHASES["simq-audit"],
}


def _write_workflow_file(tmp_path: Path, name: str, body: str) -> Path:
    path = tmp_path / f"{name}.js"
    path.write_text(body, encoding="utf-8")
    return path


def test_unkeyed_workflow_file_is_a_loud_failure(tmp_path, monkeypatch):
    """AC1: a workflow file present in neither registry is a named FAIL, never a silent skip."""
    _write_workflow_file(tmp_path, "totally-unkeyed-workflow", "phase('Whatever')\n")
    _patch_registries(monkeypatch, agents={}, phases={})
    results = check_workflow_vocabulary(tmp_path)
    unkeyed_fails = [r for r in results if r["family"] == "unkeyed_workflow"]
    assert len(unkeyed_fails) == 1
    assert unkeyed_fails[0]["status"] == "FAIL"
    assert "totally-unkeyed-workflow" in unkeyed_fails[0]["evidence"]
    # The file-level flag does not suppress literal-level reporting: the one phase literal it
    # contains is also reported, trivially unregistered since the workflow has no registry key.
    phase_fails = [r for r in results if r["family"] == "phase"]
    assert len(phase_fails) == 1
    assert "Whatever" in phase_fails[0]["evidence"]


def test_real_corpus_pre_fix_snapshot_reports_exactly_6_agent_and_23_phase_findings(monkeypatch):
    """AC2: against the real .claude/workflows/*.js corpus with pre-fix registries, the check
    reports exactly 6 agent findings and 23 phase findings, counted separately."""
    _patch_registries(monkeypatch, agents=_PRE_FIX_WORKFLOW_AGENTS, phases=_PRE_FIX_WORKFLOW_PHASES)
    results = check_workflow_vocabulary(REAL_WORKFLOWS_DIR)
    agent_fails = [r for r in results if r["status"] == "FAIL" and r["family"] == "agent"]
    phase_fails = [r for r in results if r["status"] == "FAIL" and r["family"] == "phase"]
    unkeyed_fails = [r for r in results if r["family"] == "unkeyed_workflow"]

    assert len(agent_fails) == 6, agent_fails
    assert len(phase_fails) == 23, phase_fails
    assert len(unkeyed_fails) == 7, unkeyed_fails


def test_real_corpus_current_state_reports_zero_findings():
    """AC3: after the registry change, the check reports zero findings against the real corpus,
    and all 11 workflow files are keyed in WORKFLOW_PHASES."""
    results = check_workflow_vocabulary(REAL_WORKFLOWS_DIR)
    fails = [r for r in results if r["status"] == "FAIL"]
    assert fails == []
    assert len(results) == 11
    js_files = sorted(p.stem for p in REAL_WORKFLOWS_DIR.glob("*.js"))
    assert set(js_files) <= set(WORKFLOW_PHASES.keys())


def test_commented_out_literals_produce_no_finding(tmp_path, monkeypatch):
    """AC4: a literal appearing only inside a comment produces no finding."""
    body = (
        "// await writeSidecar(1, 'CommentedPhase', 'commented-agent')\n"
        "// phase('CommentedPhase2')\n"
        "// agent: 'commented-agent-2'\n"
        "/* agent: 'block-commented-agent'\n"
        "   phase('BlockCommentedPhase') */\n"
    )
    _write_workflow_file(tmp_path, "comment-only", body)
    _patch_registries(
        monkeypatch,
        agents={"comment-only": set()},
        phases={"comment-only": set()},
    )
    results = check_workflow_vocabulary(tmp_path)
    assert len(results) == 1
    assert results[0]["status"] == "PASS"


def test_write_sidecar_argument_positions_read_independently(tmp_path):
    """AC5: writeSidecar's 2nd arg is read as phase, 3rd as agent -- distinguishable strings so a
    position swap fails loudly rather than silently reporting a plausible wrong number."""
    path = _write_workflow_file(
        tmp_path, "position-check",
        "await writeSidecar(1, 'ThePhaseLiteral', 'the-agent-literal')\n",
    )
    agent_literals, phase_literals = extract_literals_from_workflow_file(path)
    assert phase_literals == {"ThePhaseLiteral"}
    assert agent_literals == {"the-agent-literal"}


def test_literal_registered_under_different_workflow_still_reported(tmp_path, monkeypatch):
    """AC6: a literal registered under workflow A but used in workflow B is a finding, for both
    families."""
    _write_workflow_file(
        tmp_path, "workflow-b",
        "agent: 'agent-only-in-a'\nphase('Phase-Only-In-A')\n",
    )
    _patch_registries(
        monkeypatch,
        agents={"workflow-a": {"agent-only-in-a"}, "workflow-b": set()},
        phases={"workflow-a": {"Phase-Only-In-A"}, "workflow-b": set()},
    )
    results = check_workflow_vocabulary(tmp_path)
    fails = [r for r in results if r["status"] == "FAIL"]
    assert any(r["family"] == "agent" for r in fails)
    assert any(r["family"] == "phase" for r in fails)


def test_create_tickets_investigate_prefix_family_not_reported(tmp_path, monkeypatch):
    """AC7: a create-tickets agent literal matching the investigate: prefix family is not
    reported -- proves resolution goes through is_known_agent(), not raw set membership."""
    _write_workflow_file(
        tmp_path, "create-tickets",
        "pushEvent('Investigate', `investigate:${inv.concern_id}`, {})\n"
        "agent: 'investigate:some-concern-id'\n",
    )
    _patch_registries(
        monkeypatch,
        agents={"create-tickets": set()},
        phases={"create-tickets": {"Investigate"}},
    )
    results = check_workflow_vocabulary(tmp_path)
    fails = [r for r in results if r["status"] == "FAIL"]
    assert fails == []


def test_exit_code_zero_even_with_findings():
    """AC8: exit code is zero even with findings."""
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "gate_checks" / "workflow_vocabulary_check.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert proc.stdout.startswith("MARKER:")


def test_vocabulary_py_additions_are_additive_only():
    """AC9: every pre-existing WORKFLOW_AGENTS/WORKFLOW_PHASES entry is still present as a subset
    of the current registries -- catches an accidental removal (not a same-shape rename, which
    needs a human diff read at Verify, noted in test_plan.md)."""
    for workflow, agents in _PRE_FIX_WORKFLOW_AGENTS.items():
        assert agents <= WORKFLOW_AGENTS.get(workflow, set())
    for workflow, phases in _PRE_FIX_WORKFLOW_PHASES.items():
        assert phases <= WORKFLOW_PHASES.get(workflow, set())


@pytest.mark.parametrize("workflow_name", sorted(p.stem for p in REAL_WORKFLOWS_DIR.glob("*.js")))
def test_every_real_workflow_file_is_keyed_in_workflow_phases(workflow_name):
    """AC3 (explicit per-file form): all 11 workflow files are keyed in WORKFLOW_PHASES."""
    assert workflow_name in WORKFLOW_PHASES

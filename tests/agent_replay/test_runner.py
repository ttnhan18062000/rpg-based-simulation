"""Tests for tools/agent_replay/runner.py (TCK-20260721-CODEX-REPLAY-PROOF, AC #2).

Proves the replay runner actually re-executes the Scope -> Investigate -> Plan -> Review slice
against the real fixture and completes, reproducing the real recorded outcome
(agent-monitoring/events.jsonl seq 1-4 for run_id TCK-20260721-ORCHESTRATION-CONTRACT-ADR are all
status="ok").
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from agent_replay.fixture_envelope import load_fixture  # noqa: E402
from agent_replay.runner import ReplayOutcome, replay_slice  # noqa: E402

_REAL_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "fixtures" / "agent_replay" / "TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml"
)


def test_replay_runner_completes_against_real_fixture():
    fixture = load_fixture(_REAL_FIXTURE_PATH)

    outcome = replay_slice(fixture)

    assert isinstance(outcome, ReplayOutcome)
    assert outcome.final_status == "ok"
    assert outcome.phases_completed == ["Scope", "Investigate", "Plan", "Review"]


def test_scope_conflicts_present_short_circuits_at_scope():
    fixture = load_fixture(_REAL_FIXTURE_PATH)
    fixture.phases[0].input["conflicts"] = ["duplicate work found"]

    outcome = replay_slice(fixture)

    assert outcome.final_status == "CONFLICTS_DETECTED"
    assert outcome.phases_completed == []


def test_scope_unregistered_tag_short_circuits_at_scope():
    fixture = load_fixture(_REAL_FIXTURE_PATH)
    fixture.phases[0].input["tags"] = ["this-tag-is-definitely-not-registered-xyz"]

    outcome = replay_slice(fixture)

    assert outcome.final_status == "TAGS_NOT_REGISTERED"
    assert outcome.phases_completed == []


def test_plan_unresolved_questions_short_circuits_at_plan(tmp_path):
    fixture = load_fixture(_REAL_FIXTURE_PATH)
    plan_with_open_question = tmp_path / "plan.md"
    plan_with_open_question.write_text("## Steps\n\n## Unresolved Questions\n\n- What now?\n")
    fixture.phases[2].input["plan_path"] = str(plan_with_open_question)

    outcome = replay_slice(fixture)

    assert outcome.final_status == "NEEDS_HUMAN_INPUT"
    assert outcome.phases_completed == ["Scope", "Investigate"]


def test_review_non_approved_verdict_short_circuits_at_review():
    fixture = load_fixture(_REAL_FIXTURE_PATH)
    fixture.phases[3].output["verdict"] = "NEEDS_CHANGES"

    outcome = replay_slice(fixture)

    assert outcome.final_status == "NEEDS_CHANGES"
    assert outcome.phases_completed == ["Scope", "Investigate", "Plan"]

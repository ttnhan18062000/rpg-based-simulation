"""Tests for tools/agent_replay/fixture_envelope.py (TCK-20260721-CODEX-REPLAY-PROOF).

Covers AC #1 (real fixture loads and validates, and is not a synthetic stub masquerading as a
real fixture) and AC #4 (fail-closed on any missing required envelope field, parametrized over
several distinct fields — not just the first one a lazy validator might check).
"""
import json
import sys
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from agent_replay.fixture_envelope import (  # noqa: E402
    FixtureEnvelope,
    FixtureValidationError,
    PhaseEntry,
    load_fixture,
)

_REAL_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "fixtures" / "agent_replay" / "TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml"
)


def _well_formed_fixture_dict() -> dict:
    return {
        "version": 1,
        "source": {
            "ticket_id": "TCK-EXAMPLE",
            "ticket_path": "tickets/done/TCK-EXAMPLE.md",
            "events_run_id": "TCK-EXAMPLE",
        },
        "phases": [
            {
                "phase": "Scope",
                "agent": "ticket-scoper",
                "input": {"tags": [], "conflicts": []},
                "output": {"summary": "ok"},
                "transition": "ok",
            },
            {
                "phase": "Investigate",
                "agent": "investigator",
                "input": {},
                "output": {"summary": "ok"},
                "transition": "ok",
            },
        ],
    }


# ---------------------------------------------------------------------------
# Schema validation — well-formed fixture
# ---------------------------------------------------------------------------


def test_fixture_envelope_schema_validates_required_fields(tmp_path):
    fixture_path = tmp_path / "well_formed.yaml"
    fixture_path.write_text(yaml.safe_dump(_well_formed_fixture_dict()))

    envelope = load_fixture(fixture_path)

    assert isinstance(envelope, FixtureEnvelope)
    assert envelope.version == 1
    assert envelope.source["ticket_id"] == "TCK-EXAMPLE"
    assert len(envelope.phases) == 2
    assert isinstance(envelope.phases[0], PhaseEntry)
    assert envelope.phases[0].phase == "Scope"
    assert envelope.phases[1].phase == "Investigate"


def test_empty_dict_input_output_is_a_valid_recorded_value(tmp_path):
    data = _well_formed_fixture_dict()
    # Investigate's input/output are already {} above — assert this loads without error, since an
    # empty dict is a legitimate recorded value, distinct from the key being absent/null.
    fixture_path = tmp_path / "empty_dict_ok.yaml"
    fixture_path.write_text(yaml.safe_dump(data))
    envelope = load_fixture(fixture_path)
    assert envelope.phases[1].input == {}


# ---------------------------------------------------------------------------
# Real fixture — AC #1, anti-drift guard against a synthetic stub
# ---------------------------------------------------------------------------


def test_real_fixture_set_loads_and_validates():
    envelope = load_fixture(_REAL_FIXTURE_PATH)

    assert envelope.version == 1
    assert envelope.source["ticket_id"] == "TCK-20260721-ORCHESTRATION-CONTRACT-ADR"
    assert [p.phase for p in envelope.phases] == ["Scope", "Investigate", "Plan", "Review"]

    # Anti-drift guard: the fixture's ticket_id must correspond to a real, permanent record — not
    # invented example data.
    done_ticket_path = _REPO_ROOT / "tickets" / "done" / "TCK-20260721-ORCHESTRATION-CONTRACT-ADR.md"
    assert done_ticket_path.exists(), "fixture's source ticket_id has no matching tickets/done/ file"

    runs_jsonl = _REPO_ROOT / "agent-monitoring" / "runs.jsonl"
    matching_run_ids = set()
    for line in runs_jsonl.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        matching_run_ids.add(row.get("run_id"))
    assert envelope.source["ticket_id"] in matching_run_ids, (
        "fixture's source ticket_id has no matching row in agent-monitoring/runs.jsonl"
    )


# ---------------------------------------------------------------------------
# Fail-closed behavior — AC #4
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda d: d.pop("version"), id="missing-version"),
        pytest.param(lambda d: d["phases"][0].pop("output"), id="missing-phase-output"),
        pytest.param(lambda d: d["phases"][0].pop("transition"), id="missing-phase-transition"),
        pytest.param(lambda d: d.__setitem__("source", None), id="null-source"),
        pytest.param(lambda d: d["phases"][0].__setitem__("agent", None), id="null-phase-agent"),
    ],
)
def test_replay_runner_fails_clearly_on_missing_required_fixture_field(tmp_path, mutate):
    data = _well_formed_fixture_dict()
    mutate(data)
    fixture_path = tmp_path / "broken.yaml"
    fixture_path.write_text(yaml.safe_dump(data))

    with pytest.raises(FixtureValidationError):
        load_fixture(fixture_path)

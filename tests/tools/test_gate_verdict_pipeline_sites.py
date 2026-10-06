"""Tests for TCK-20261006-GATE-VERDICT-PIPELINE-SITES: every gate in gate-policy.yaml has an emit site in implement-ticket.js."""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from tools.agent_working_paths import AGENT_MONITORING, AGENT_ORCHESTRATION

_REPO = Path(__file__).parent.parent.parent
_MONITORING_DIR = _REPO / "tools" / "agent-monitoring"
if str(_MONITORING_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_DIR))

import gate_verdicts  # noqa: E402

_SOURCE = (_REPO / ".claude" / "workflows" / "implement-ticket.js").read_text(encoding="utf-8")
_GATES = yaml.safe_load((_REPO / AGENT_ORCHESTRATION / "gate-policy.yaml").read_text(encoding="utf-8"))["gates"]


def emit_site(gate: dict, source: str) -> re.Match | None:
    """The pushGate/pushStaticGate call that records `gate`, or None when the source has no such call."""
    helper = "pushStaticGate" if gate["gate_type"] == "static_check" else "pushGate"
    return re.search(rf"\b{helper}\('{re.escape(gate_verdicts.policy_gate_id(gate))}', '{gate['gate_type']}', '{gate['phase']}'", source)


def test_policy_gate_ids_are_unique():
    ids = [gate_verdicts.policy_gate_id(g) for g in _GATES]
    assert len(ids) == len(set(ids)) == len(_GATES)


@pytest.mark.parametrize("gate", _GATES, ids=gate_verdicts.policy_gate_id)
def test_every_policy_gate_has_an_emit_site(gate):
    assert emit_site(gate, _SOURCE), f"no emit site for {gate_verdicts.policy_gate_id(gate)}"


def test_conformance_fails_when_a_gate_has_no_emit_site():
    gate = _GATES[0]
    stripped = _SOURCE.replace(f"'{gate_verdicts.policy_gate_id(gate)}'", "'removed'")
    assert emit_site(gate, stripped) is None


@pytest.mark.parametrize("gate", _GATES, ids=gate_verdicts.policy_gate_id)
def test_a_gate_is_recorded_before_the_run_stops_on_it(gate):
    """A blocked run still flushes its rows in writeMonitoring, so the gate row must be pushed before the call that stops
    the run on it (the last writeMonitoring of that status: Finalize also stops earlier, on unparseable output, before the gate ran)."""
    site = emit_site(gate, _SOURCE)
    for status in gate["on_fail_status"]:
        stop = _SOURCE.rfind(f"writeMonitoring('{status}')")
        if stop != -1:
            assert site.start() < stop, f"{status} stops the run before {gate['phase']} records its verdict"


def test_write_failure_cannot_change_the_run():
    """Rows ride writeMonitoring's own fail-open step; pushGate never throws."""
    assert "try {\n    gateRows.push" in _SOURCE
    assert "A failure here is only a warning" in _SOURCE


def _batch(*rows):
    return [{"gate_id": g, "gate_type": "agent_verdict", "phase": "Review", "verdict": v, "blocking": b,
             "inputs_ref": {"phase": "Review"}, "run_id": "TCK-X", "execution_id": "claude-TCK-X-1",
             "ticket_id": "TCK-X", "execution_mode": "pipeline"} for g, v, b in rows]


def test_a_passing_run_writes_one_non_blocking_row_per_gate(tmp_path, monkeypatch):
    monkeypatch.delenv(gate_verdicts.ENV_NO_RECORD, raising=False)
    target = tmp_path / "g.jsonl"
    assert gate_verdicts.record_batch(_batch(("Review:verdict", "APPROVED", False), ("Verify:verdict", "READY_TO_CLOSE", False)), target=target) == 2
    rows = [json.loads(line) for line in target.read_text().splitlines()]
    assert [r["blocking"] for r in rows] == [False, False] and rows[0]["verdict"] == "APPROVED" and rows[0]["run_id"] == "TCK-X"
    assert all(gate_verdicts.validate_record(r) == [] for r in rows)


def test_a_run_blocked_at_review_writes_only_the_gates_it_reached(tmp_path, monkeypatch):
    monkeypatch.delenv(gate_verdicts.ENV_NO_RECORD, raising=False)
    target = tmp_path / "g.jsonl"
    gate_verdicts.record_batch(_batch(("Scope:conflicts", "PASS", False), ("Review:verdict", "NEEDS_CHANGES", True)), target=target)
    rows = [json.loads(line) for line in target.read_text().splitlines()]
    assert [(r["gate_id"], r["verdict"], r["blocking"]) for r in rows] == [
        ("Scope:conflicts", "PASS", False), ("Review:verdict", "NEEDS_CHANGES", True)]


def test_one_bad_row_does_not_stop_the_others(tmp_path, monkeypatch):
    monkeypatch.delenv(gate_verdicts.ENV_NO_RECORD, raising=False)
    target = tmp_path / "g.jsonl"
    bad = {"gate_id": "Review:verdict"}
    good = _batch(("Verify:verdict", "READY_TO_CLOSE", False))[0]
    assert gate_verdicts.record_batch([bad, "junk", good], target=target) == 1


def test_cli_records_rows_and_never_fails_the_run(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "checkout", "-q", "-b", "b"], check=True)
    env = {k: v for k, v in os.environ.items() if k != gate_verdicts.ENV_NO_RECORD}
    run = lambda data: subprocess.run([sys.executable, str(_MONITORING_DIR / "gate_verdicts.py"), "record-batch", "--data", data],
                                      capture_output=True, text=True, cwd=tmp_path, env=env)
    ok = run(json.dumps(_batch(("Review:verdict", "APPROVED", False))))
    assert ok.returncode == 0 and "recorded 1" in ok.stdout
    week = datetime.now(timezone.utc).strftime("%G-W%V")
    assert len(list((tmp_path / AGENT_MONITORING / "data" / week).glob("*.gate_verdicts.jsonl"))) == 1
    broken = run("{not json")
    assert broken.returncode == 0 and "WARNING" in broken.stderr


def test_static_gate_row_is_written_natively_too_and_carries_the_attested_stdout_sha():
    """TCK-20261006-GATE-LEDGER-NATIVE-ATTESTED-ROWS-DOUBLE-COUNT: the attested_command row is evidence; this row is the verdict."""
    source = (_REPO / ".claude/workflows/implement-ticket.js").read_text(encoding="utf-8")
    assert "const pushStaticGate = (...gateArgs) => pushGate(...gateArgs, legacyBash ? null : lastAttestedStdoutSha)" in source
    assert "stdout_sha: linkedStdoutSha" in source
    assert "lastAttestedStdoutSha = JSON.parse(" in source

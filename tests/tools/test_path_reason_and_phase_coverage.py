"""Tests for TCK-20261006-PATH-REASON-AND-PHASE-COVERAGE-RECORD: run `path_reason`/`phases_omitted`, event `skip_reason`."""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from tools.agent_working_paths import AGENT_MONITORING

_MONITORING_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_DIR))

import path_record  # noqa: E402
from record_events import validate_record as validate_event  # noqa: E402
from record_hand_orchestrated_closure import build_records  # noqa: E402
from record_run import validate_record as validate_run  # noqa: E402
from vocabulary import PATH_REASONS, SKIP_REASONS  # noqa: E402

_REPO = Path(__file__).parent.parent.parent
_CLOSURE = _MONITORING_DIR / "record_hand_orchestrated_closure.py"
_TITLE = ["--title", "T", "--log-summary", "S."]

_STANDARD_EVENTS = [
    {"phase": "Scope", "status": "ok", "summary": "s"},
    {"phase": "Implement", "status": "ok", "summary": "s"},
    {"phase": "Test", "status": "ok", "summary": "s"},
    {"phase": "Parity", "status": "skipped", "summary": "s", "skip_reason": "condition_false"},
    {"phase": "Verify", "status": "ok", "summary": "s"},
    {"phase": "Finalize", "status": "ok", "summary": "s"},
]
_HOTFIX_EVENTS = [
    {"phase": p, "status": "skipped" if p in ("Investigate", "Plan", "Review", "Architecture-Verify") else "ok", "summary": "s",
     **({"skip_reason": "tier_plan"} if p in ("Investigate", "Plan", "Review", "Architecture-Verify") else {})}
    for p in ("Scope", "Investigate", "Plan", "Review", "Implement", "Document-Update", "Architecture-Verify", "Test", "Verify", "Finalize")
]


def _build(tier, events, **kw):
    return build_records("TCK-FAKE", tier, "DONE", events, None, None, "implement-ticket", "claude", "claude", **kw)


def _plan(tmp_path, standard_arch="full"):
    plan = {"phases": [
        {"name": "Scope", "tiers": {"standard": "full", "hotfix": "full"}},
        {"name": "Architecture-Verify", "tiers": {"standard": standard_arch, "hotfix": "skipped_event"}},
        {"name": "Parity", "tiers": {"standard": "conditional", "hotfix": "conditional"}},
    ]}
    path = tmp_path / "plan.yaml"
    path.write_text(yaml.safe_dump(plan), encoding="utf-8")
    return path


def test_standard_closure_records_omitted_phases_reason_and_skip_reason():
    run, events = _build("standard", _STANDARD_EVENTS, path_reason="small_change")
    assert run["phases_omitted"] == ["Investigate", "Plan", "Review", "Document-Update", "Architecture-Verify"]
    assert run["path_reason"] == "small_change"
    assert next(e for e in events if e["phase"] == "Parity")["skip_reason"] == "condition_false"
    assert validate_run(run) == []
    assert all(validate_event(e) == [] for e in events)


def test_hotfix_with_every_planned_phase_recorded_omits_nothing():
    run, _ = _build("hotfix", _HOTFIX_EVENTS)
    assert run["phases_omitted"] == []


def test_epic_and_unlisted_tiers_record_empty_omitted():
    assert _build("epic", _STANDARD_EVENTS)[0]["phases_omitted"] == []


def test_skipped_event_without_a_reason_is_unstated_and_other_events_carry_none():
    _, events = _build("standard", [
        {"phase": "Scope", "status": "ok", "summary": "s"}, {"phase": "Parity", "status": "skipped", "summary": "s"}])
    assert events[1]["skip_reason"] == "unstated" and "skip_reason" not in events[0]


def test_plan_edit_changes_omitted_with_no_code_change(tmp_path):
    recorded = ["Scope", "Parity"]
    assert path_record.phases_omitted("standard", recorded, _plan(tmp_path)) == ["Architecture-Verify"]
    assert path_record.phases_omitted("standard", recorded, _plan(tmp_path, standard_arch="skipped_event")) == []


def test_unreadable_plan_gives_none_not_a_false_empty_list(tmp_path):
    assert path_record.phases_omitted("standard", [], tmp_path / "missing.yaml") is None


def test_real_plan_never_counts_conditional_phases():
    assert "Parity" not in path_record.full_phases("standard") and "Security-Review" not in path_record.full_phases("hotfix")


@pytest.mark.parametrize("reason", PATH_REASONS)
def test_every_path_reason_validates_except_other_without_note(reason):
    run, _ = _build("hotfix", _HOTFIX_EVENTS, path_reason=reason, path_note="why" if reason == "other" else None)
    assert validate_run(run) == []


def test_validators_reject_unknown_values():
    run, events = _build("hotfix", _HOTFIX_EVENTS)
    assert validate_run({**run, "path_reason": "because"}) != []
    assert validate_run({**run, "path_reason": "other"}) != []
    assert validate_run({**run, "phases_omitted": "Plan"}) != []
    skipped = next(e for e in events if e["status"] == "skipped")
    assert validate_event({**skipped, "skip_reason": "because"}) != []
    assert validate_event({**next(e for e in events if e["status"] == "ok"), "skip_reason": "tier_plan"}) != []
    assert set(SKIP_REASONS) >= {"tier_plan", "condition_false", "unstated"}


class TestCli:
    def _run(self, tmp_path, *args):
        subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
        subprocess.run(["git", "-C", str(tmp_path), "checkout", "-q", "-b", "b"], check=True)
        return subprocess.run([sys.executable, str(_CLOSURE), "--ticket-id", "TCK-FAKE-PR", "--tier", "standard",
                               "--events", json.dumps(_STANDARD_EVENTS), *_TITLE, *args],
                              capture_output=True, text=True, cwd=tmp_path)

    def _runs(self, tmp_path):
        week = datetime.now(timezone.utc).strftime("%G-W%V")
        return list((tmp_path / AGENT_MONITORING / "data" / week).glob("*.runs.jsonl"))

    def test_path_reason_is_written_and_no_hint(self, tmp_path):
        result = self._run(tmp_path, "--path-reason", "owner_directed")
        assert result.returncode == 0, result.stderr
        assert "HINT" not in result.stderr
        row = json.loads(self._runs(tmp_path)[0].read_text().strip())
        assert row["path_reason"] == "owner_directed" and "Investigate" in row["phases_omitted"]

    def test_missing_flag_is_unstated_with_one_hint_and_same_exit_code(self, tmp_path):
        result = self._run(tmp_path)
        assert result.returncode == 0 and result.stderr.count("HINT") == 1
        assert json.loads(self._runs(tmp_path)[0].read_text().strip())["path_reason"] == "unstated"

    @pytest.mark.parametrize("args", [["--path-reason", "nope"], ["--path-reason", "other"]])
    def test_bad_value_exits_nonzero_and_writes_nothing(self, tmp_path, args):
        result = self._run(tmp_path, *args)
        assert result.returncode != 0 and self._runs(tmp_path) == []


def test_pipeline_sets_path_reason_and_tier_plan_skip_reasons():
    """The pipeline's own run write and skip sites carry the new fields (source-level fixture: the script cannot run here)."""
    src = (_REPO / ".claude" / "workflows" / "implement-ticket.js").read_text(encoding="utf-8")
    assert '"path_reason":"pipeline_default"' in src and "path_record.py --tier" in src
    hotfix_skips = re.findall(r"pushEvent\('([\w-]+)', '[\w-]+', 'skipped', '[^']*', null, null, null, null, null, '(\w+)'\)", src)
    assert {p for p, _ in hotfix_skips if _ == "tier_plan"} == {"Investigate", "Plan", "Review", "Architecture-Verify"}
    assert ("Parity", "condition_false") in [(p, r) for p, r in re.findall(
        r"pushEvent\('([\w-]+)', '[\w-]+', 'skipped', '[^']*', null, null, null, null, null, '(\w+)'\)", src)]
    assert len(re.findall(r"pushEvent\([^\n]*'skipped'", src)) == len(re.findall(r"pushEvent\([^\n]*'skipped'[^\n]*'(?:tier_plan|condition_false)'\)", src))


def test_validate_flags_unknown_enum_values_and_accepts_absent_ones():
    from validate import check_path_record
    assert check_path_record([{"run_id": "R", "path_reason": "small_change"}, {"run_id": "OLD"}],
                             [{"run_id": "R", "seq": 1, "skip_reason": "tier_plan"}, {"run_id": "OLD", "seq": 1}]) == []
    errors = check_path_record([{"run_id": "R", "path_reason": "bad"}], [{"run_id": "R", "seq": 2, "skip_reason": "bad"}])
    assert len(errors) == 2 and "R#2" in errors[1]

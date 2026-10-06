"""Tests for TCK-20261006-PATH-AND-PHASE-REPORT-AND-RETRO: path_report.py and the retro's Paths section."""
import sys
from pathlib import Path

_MONITORING_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_DIR))

import generate_retro  # noqa: E402
import path_report  # noqa: E402

_PLANNED = ["Scope", "Investigate", "Plan", "Review", "Implement", "Document-Update", "Architecture-Verify", "Test", "Verify", "Finalize"]
_RAN = {"Scope", "Implement", "Test", "Verify", "Finalize"}


def _hand_standard(i: int, reason: str, plan_omitted: bool = True):
    """One standard hand run that ran Scope/Implement/Test/Verify/Finalize and skipped Parity; Plan omitted when asked."""
    run_id = f"TCK-FAKE-{i}"
    omitted = [p for p in _PLANNED if p not in _RAN and not (p == "Plan" and not plan_omitted)]
    run = {"run_id": run_id, "execution_id": f"x-{i}", "workflow": "implement-ticket", "tier": "standard", "execution_mode": "hand",
           "path_reason": reason, "phases_omitted": omitted}
    phases = [p for p in _PLANNED if p in _RAN or (p == "Plan" and not plan_omitted)]
    events = [{"run_id": run_id, "execution_id": f"x-{i}", "phase": p, "status": "ok"} for p in phases]
    events.append({"run_id": run_id, "execution_id": f"x-{i}", "phase": "Parity", "status": "skipped", "skip_reason": "condition_false"})
    return run, events


def _week(stated: int, plan_present: int = 1):
    runs, events = [], []
    for i in range(12):
        run, evs = _hand_standard(i, "small_change" if i < stated else "unstated", plan_omitted=i >= plan_present)
        runs.append(run)
        events += evs
    return runs, events


def _group(runs, events):
    (group,) = path_report.analyze(runs, events)
    return group


def test_twelve_runs_with_plan_omitted_in_eleven_and_reason_stated_in_ten_flags_plan():
    runs, events = _week(stated=10)
    group = _group(runs, events)
    assert group["phases"]["Plan"]["omitted"] == 11 and group["path_reasons"]["unstated"] == 2
    assert group["phases"]["Parity"]["skipped"] == 12 and group["phases"]["Parity"]["skip_reasons"] == {"condition_false": 12}
    candidates, held = path_report.routing(group)
    assert "Plan" in candidates and held == []
    line = next(l for l in path_report.render_section(runs, events, 12).splitlines() if l.startswith("Routing candidates:"))
    assert "`Plan`" in line


def test_only_four_reasons_stated_does_not_flag_plan_and_names_the_unstated_share():
    runs, events = _week(stated=4)
    candidates, held = path_report.routing(_group(runs, events))
    assert "Plan" not in candidates
    assert any("`Plan`" in h and "`unstated` is 67%" in h for h in held)
    assert "No routing candidate." in path_report.render_section(runs, events, 12)


def test_fewer_than_ten_runs_never_flags_a_phase():
    runs, events = _week(stated=12)
    runs, events = runs[:9], [e for e in events if int(e["run_id"].rsplit("-", 1)[1]) < 9]
    candidates, held = path_report.routing(_group(runs, events))
    assert candidates == [] and any("fewer than 10" in h for h in held)


def test_runs_from_before_the_fields_are_predates_never_unstated():
    old = {"run_id": "TCK-OLD", "execution_id": "o", "workflow": "implement-ticket", "tier": "standard", "execution_mode": "hand"}
    runs, events = _week(stated=10)
    group = _group(runs + [old], events)
    assert group["predates"] == 1 and group["with_fields"] == 12 and group["path_reasons"]["unstated"] == 2


def test_a_period_of_only_old_runs_shows_predates_rows_and_no_candidate():
    old = [{"run_id": f"TCK-OLD-{i}", "workflow": "implement-ticket", "tier": "hotfix", "execution_mode": "hand"} for i in range(3)]
    section = path_report.render_section(old, [], total_field_runs=0)
    assert "Instrument not running" in section and "| hotfix | hand | 3 | 3 |" in section
    assert "No routing candidate: no run carries the fields yet." in section and "Routing candidates:" not in section


def test_no_runs_in_the_period_says_so_without_zero_tables():
    assert "No implement-ticket runs this period" in path_report.render_section([], [], total_field_runs=5)
    assert "5 runs outside this period" in path_report.render_section([], [], total_field_runs=5)


def test_other_workflows_are_ignored():
    runs, events = _week(stated=10)
    runs.append({"run_id": "EPIC-1", "workflow": "implement-epic", "tier": "n/a", "path_reason": "other"})
    assert [(g["tier"], g["execution_mode"]) for g in path_report.analyze(runs, events)] == [("standard", "hand")]


def test_conditional_phase_without_an_event_is_conditional_absent_not_omitted():
    run = {"run_id": "R", "execution_id": "e", "workflow": "implement-ticket", "tier": "standard", "execution_mode": "pipeline",
           "path_reason": "pipeline_default", "phases_omitted": []}
    group = _group([run], [{"run_id": "R", "execution_id": "e", "phase": "Scope", "status": "ok"}])
    assert group["phases"]["Security-Review"]["conditional_absent"] == 1 and group["phases"]["Security-Review"]["omitted"] == 0


def test_retro_renders_the_paths_section_and_keeps_notes_without_force(tmp_path):
    runs, events = _week(stated=10)
    section = path_report.render_section(runs, events, 12)
    report = generate_retro.generate(runs, events, "2026-W41", "2026-W41", paths=section)
    assert "## Paths" in report and report.index("## Paths") < report.index("## Notes")
    out = tmp_path / "RETRO-2026-W41.md"
    generate_retro._write_report_preserving_notes(report, out, False)
    out.write_text(out.read_text().replace("_Fill in after reviewing the report above. What patterns stand out? What to improve?_", "HAND NOTE"))
    generate_retro._write_report_preserving_notes(report, out, False)
    assert "HAND NOTE" in out.read_text()


def test_retro_without_the_section_is_unchanged():
    assert "## Paths" not in generate_retro.generate([], [], "2026-W41", "2026-W41")

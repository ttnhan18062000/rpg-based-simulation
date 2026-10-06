"""TCK-20261006-CREATE-TICKETS-FAILED-INVESTIGATIONS-REPORTED-AS-COVERED.

Static, source-text tests like this repo's other `.claude/workflows/*.js` tests (no JS runner exists here): they pin the
orchestrator's exit logic. The runtime behaviour has a manual reproduction: run /create-tickets from the parent directory
of the repo, where `concern-investigator` is not registered, and expect `INVESTIGATION_FAILED`, not `NOTHING_TO_CREATE`."""
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
_JS = (_ROOT / ".claude" / "workflows" / "create-tickets.js").read_text(encoding="utf-8")


def _investigate_exit_region() -> str:
    start = _JS.index("const validInvestigations")
    return _JS[start:_JS.index("phase('Structure')", start)]


def test_failed_concerns_are_found_by_id_not_position():
    region = _investigate_exit_region()
    assert "investigatedIds = new Set(validInvestigations.map(i => i.concern_id))" in region
    assert "failedConcerns = comprehension.concerns.filter(c => !investigatedIds.has(c.id)).map(c => c.id)" in region


def test_total_failure_returns_a_distinct_status_before_the_covered_exit():
    region = _investigate_exit_region()
    failed = region.index("status: 'INVESTIGATION_FAILED'")
    covered = region.index("status: 'NOTHING_TO_CREATE'")
    assert failed < covered, "the failure exit must come first so a failed run can never reach the 'covered' exit"
    guard = region[:failed]
    assert "activeInvestigations.length === 0 && failedConcerns.length > 0" in guard
    assert "writeMonitoring('INVESTIGATION_FAILED')" in region
    assert "failed_concerns: failedConcerns" in region[failed:covered] and "failed_count" in region[failed:covered]


def test_the_already_covered_message_is_only_reachable_with_no_failed_concern():
    region = _investigate_exit_region()
    covered_exit = region[region.index("if (activeInvestigations.length === 0) {"):]
    assert "All concerns are already covered by existing tickets." in covered_exit
    # the only branch that can reach it comes after the failure branch returned for failedConcerns.length > 0
    assert region.count("All concerns are already covered by existing tickets.") == 1


def test_partial_failure_lists_the_failed_concerns_in_the_final_return():
    final = _JS[_JS.rindex("return {\n  status: 'DONE'"):]
    assert "failed_concerns: failedConcerns" in final


def test_a_failed_concern_is_never_listed_as_a_duplicate():
    # duplicates come only from validInvestigations (those that returned), failures come from the id difference
    assert "const duplicates = validInvestigations.filter(i => i.is_duplicate)" in _JS


def test_the_skill_text_and_schema_describe_the_new_status():
    skill = (_ROOT / ".claude" / "skills" / "create-tickets" / "SKILL.md").read_text(encoding="utf-8")
    schema = (_ROOT / "docs" / "agent-monitoring" / "schema.md").read_text(encoding="utf-8")
    assert "INVESTIGATION_FAILED" in skill and "failed_concerns" in skill
    assert "| `INVESTIGATION_FAILED` |" in schema

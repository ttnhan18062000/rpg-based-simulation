"""Tests for TCK-20260927-PHASE-PROMPTS-OMIT-GATE-PRECONDITIONS.

Static, raw-source-text-parsing tests against `.claude/workflows/implement-ticket.js` and
`.claude/agents/done-checker.md` — reuses the established pattern from
tests/tools/test_scope_orphan_fix.py and tests/tools/test_step0_ts_orchestrator.py (the workflow
file is never executed; no JS test runner exists in this repo for `.claude/workflows/*.js`).

Covers: the Test phase now computes the required test-directory floor via
`expected_test_dirs_for()` BEFORE the test-scoper agent() call (AC1/AC2), the Verify phase now
declares `todos_source_path` to done-checker when non-empty (AC3), and `done-checker.md` states
the declared-vs-undeclared rule (AC4).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools" / "gate_checks"))

from test_scope_coverage_static import (  # noqa: E402
    check_test_scope_coverage,
    expected_test_dirs_for,
)

_REPO_ROOT = Path(__file__).parent.parent.parent
_IMPLEMENT_TICKET_JS = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"
_DONE_CHECKER_MD = _REPO_ROOT / ".claude" / "agents" / "done-checker.md"


def _read_implement_ticket() -> str:
    return _IMPLEMENT_TICKET_JS.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# AC1 — Test phase prompt contains the pre-computed directory list; no JS mapping copy.
# ---------------------------------------------------------------------------

def test_expected_test_dirs_computed_via_bash_before_agent_call():
    source = _read_implement_ticket()
    bash_call_index = source.index("from gate_checks.test_scope_coverage_static import expected_test_dirs_for")
    agent_call_index = source.index("const testResult = await agent(")
    assert bash_call_index < agent_call_index, (
        "expected_test_dirs_for() must be computed before the test-scoper agent() call, not after"
    )


def test_test_phase_placement_precedes_capturets_like_orphan_call():
    """Mirrors test_scope_orphan_fix.py's test_step1c_orphan_bash_precedes_capturets: the new
    bash() call must precede captureTs()/writeSidecar(), never sit between them and agent() --
    that placement is what keeps test_step0_ts_orchestrator.py's exact literal-adjacency
    assertion for the Test phase intact."""
    source = _read_implement_ticket()
    adjacency = (
        "const testTs = await captureTs()\n"
        "await writeSidecar(events.length + 1 + seqOffset, 'Test', 'test-scoper')\n"
        "const testResult = await agent("
    )
    assert adjacency in source

    expected_dirs_call_index = source.index("EXPECTED_TEST_DIRS_JSON:")
    capture_ts_index = source.index(adjacency)
    assert expected_dirs_call_index < capture_ts_index, (
        "the expected-test-dirs bash() call must be resolved before captureTs()/writeSidecar(), "
        "never inserted between them and agent()"
    )


def test_no_js_reimplementation_of_the_src_subsystem_mapping():
    """AC1's grep-verifiable half: none of expected_test_dirs_for()'s Python-side subsystem names
    are duplicated as a JS array/object literal in the workflow file — the orchestrator must call
    the Python function via bash(), never port its mapping."""
    source = _read_implement_ticket()
    # A few subsystem names distinctive enough that their co-occurrence as a JS literal would
    # indicate a ported copy of _SRC_UNIT_SUBSYSTEMS, rather than incidental unrelated mentions.
    suspicious_js_set_literal = "'campaigns', 'cognition'"
    assert suspicious_js_set_literal not in source
    assert "_SRC_UNIT_SUBSYSTEMS" not in source


def test_prompt_states_the_computed_floor_when_dirs_exist():
    source = _read_implement_ticket()
    assert "Computed floor" in source
    assert "expected_test_dirs_for()" in source
    assert "the exact function the post-agent gate re-checks this command against" in source


def test_step1_and_step3_reworded_to_mean_directory_not_file():
    source = _read_implement_ticket()
    assert "counterpart DIRECTORY (not a specific file inside it)" in source
    assert "including every directory from the computed floor above (never individual files" in source


# ---------------------------------------------------------------------------
# AC2 — the injected directories are exactly what the post-agent gate then requires.
# ---------------------------------------------------------------------------

def test_injected_dirs_alone_satisfy_the_post_agent_gate():
    files_changed = [
        "src/combat/damage.py",
        "src/core/state.py",
        "tools/gate_checks/test_scope_coverage_static.py",
    ]
    computed_dirs = sorted({d for d in (expected_test_dirs_for(p) for p in files_changed) if d})
    assert computed_dirs == ["tests/tools/", "tests/unit/combat/", "tests/unit/core/"]

    # A command built ONLY from the injected bare directories -- no cherry-picked files.
    command = "pytest " + " ".join(computed_dirs) + " -m 'not slow'"
    results = check_test_scope_coverage(files_changed, command)
    assert results, "expected at least one condition checked"
    assert all(r["status"] == "PASS" for r in results), results


def test_injected_dirs_empty_for_files_with_no_known_mapping():
    files_changed = ["docs/guides/delivery_process.md", "tickets/done/TCK-1.md"]
    computed_dirs = sorted({d for d in (expected_test_dirs_for(p) for p in files_changed) if d})
    assert computed_dirs == []


# ---------------------------------------------------------------------------
# AC3 — Verify prompt declares todos_source_path when non-empty; says nothing when empty.
# ---------------------------------------------------------------------------

def test_verify_prompt_declares_todos_source_path_conditionally():
    source = _read_implement_ticket()
    assert "${ticketInfo.todos_source_path ? `" in source
    assert 'Condition 9 (repo state is consistent) note:' in source
    assert 'Finalize step 3 deletes it AFTER this check passes' in source
    assert 'Do not flag this\ndeclared path' in source


def test_todos_declaration_is_inside_the_verify_prompt_not_test_phase():
    source = _read_implement_ticket()
    done_check_agent_index = source.index("const doneCheck = await agent(")
    verify_prompt_start = source.index("Definition-of-Done check for ticket")
    declaration_index = source.index("Condition 9 (repo state is consistent) note:")
    # The prompt text is the argument passed to agent(), so the call opens first, then the
    # prompt's own opening line, then (further into that same string) this ticket's declaration.
    assert done_check_agent_index < verify_prompt_start < declaration_index


# ---------------------------------------------------------------------------
# AC4 — done-checker.md states the declared-vs-undeclared rule once.
# ---------------------------------------------------------------------------

def test_done_checker_md_states_declared_vs_undeclared_rule():
    text = _DONE_CHECKER_MD.read_text(encoding="utf-8")
    assert "is a failure only when the caller did" in text
    assert "not declare it" in text
    assert "todos_source_path" in text
    # Stated once, under condition 9 -- not duplicated as a second standalone rule elsewhere.
    assert text.count("A `tickets/todos/` copy of the ticket under check") == 1


def test_done_checker_md_still_reports_an_undeclared_duplicate():
    text = _DONE_CHECKER_MD.read_text(encoding="utf-8")
    assert "any other `tickets/todos/` duplicate is still a real finding" in text.lower() or (
        "duplicate is still a real finding" in text
    )

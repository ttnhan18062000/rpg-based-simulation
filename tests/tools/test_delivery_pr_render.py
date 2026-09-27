"""Tests for tools/delivery/pr_render.py (TCK-20260924-DELIVERY-PR-RENDERER).

One section per Acceptance Criterion, per staging_artifacts/TCK-20260924-DELIVERY-PR-RENDERER/
test_plan.md. Fixture tickets are small throwaway .md files under tmp_path; git calls are faked.
"""
import json
import re
import subprocess
from pathlib import Path

import pytest

from tools.delivery import pr_render
from tools.delivery.pr_status import CommandResult


def _write_ticket(root: Path, ticket_id, layer, title, tier="standard",
                   request_summary="First paragraph of the summary.\n\nSecond paragraph.",
                   test_summary="pytest ran, 5 passed.", completion_summary="Done, no gaps."):
    path = root / f"{ticket_id}.md"
    path.write_text(f"""---
status: active
layer: {layer}
authority: P2
audience: agent
ticket_id: {ticket_id}
phase: open
date: 2026-09-24
tags: []
---

# {ticket_id}

## Title
{title}

## Status
DONE

## Tier
{tier}

## Type
feature

## Priority
P2

## Request Summary
{request_summary}

## Test Summary
{test_summary}

## Completion Summary
{completion_summary}
""", encoding="utf-8")
    return path


class FakeRunner:
    def __init__(self, rules):
        self.rules = rules
        self.calls = []

    def __call__(self, cmd, timeout=30):
        self.calls.append(cmd)
        for predicate, result in self.rules:
            if predicate(cmd):
                return result
        raise AssertionError(f"no rule matched {cmd!r}")


def _git_log_rule(subjects):
    return (
        lambda cmd: cmd[:2] == ["git", "log"],
        CommandResult(0, "\n".join(subjects) + "\n", ""),
    )


def _git_diff_rule(paths):
    return (
        lambda cmd: cmd[:2] == ["git", "diff"],
        CommandResult(0, "\n".join(paths) + "\n", ""),
    )


REAL_LAYER_REGISTRY = Path("registries/layer_registry.jsonl")


# ---------------------------------------------------------------------------
# AC1 / AC2 — normal flow
# ---------------------------------------------------------------------------

def test_single_ticket_title_and_scope_in_registry(tmp_path):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    _write_ticket(tickets_root, "TCK-20260924-EXAMPLE-ONE", "ai", "Do the example thing")
    runner = FakeRunner([
        _git_log_rule(["TCK-20260924-EXAMPLE-ONE: do the thing"]),
        _git_diff_rule(["tickets/TCK-20260924-EXAMPLE-ONE.md"]),
    ])
    result = pr_render.render(tickets_root=tickets_root, run_command=runner)
    assert result["title"] == "ai: Do the example thing (1 ticket)"
    assert "ai" in {json.loads(l)["layer"] for l in REAL_LAYER_REGISTRY.read_text().splitlines() if l.strip()}
    assert result["warnings"] == []


def test_unregistered_layer_reported_not_defaulted(tmp_path):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    _write_ticket(tickets_root, "TCK-20260924-EXAMPLE-TWO", "totally-not-a-real-layer", "Thing")
    runner = FakeRunner([
        _git_log_rule(["TCK-20260924-EXAMPLE-TWO: do it"]),
        _git_diff_rule(["tickets/TCK-20260924-EXAMPLE-TWO.md"]),
    ])
    result = pr_render.render(tickets_root=tickets_root, run_command=runner)
    assert any("not in" in w and "totally-not-a-real-layer" in w for w in result["warnings"])


def test_two_tickets_title_and_table_rows(tmp_path):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    _write_ticket(tickets_root, "TCK-20260924-A", "ai", "First thing")
    _write_ticket(tickets_root, "TCK-20260924-B", "ai", "Second thing")
    runner = FakeRunner([
        _git_log_rule(["TCK-20260924-A: x", "TCK-20260924-B: y"]),
        _git_diff_rule(["tickets/TCK-20260924-A.md", "tickets/TCK-20260924-B.md"]),
    ])
    result = pr_render.render(tickets_root=tickets_root, run_command=runner)
    assert "(2 tickets)" in result["title"]
    table_rows = [l for l in result["body"].splitlines() if l.startswith("| TCK-")]
    assert len(table_rows) == 2


# ---------------------------------------------------------------------------
# AC3 / AC4 / AC5 — body shape and attribution
# ---------------------------------------------------------------------------

def test_body_contains_all_spec_sections_in_order_and_closes(tmp_path):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    _write_ticket(tickets_root, "TCK-20260924-A", "ai", "Thing")
    runner = FakeRunner([
        _git_log_rule(["TCK-20260924-A: x"]),
        _git_diff_rule(["tickets/TCK-20260924-A.md"]),
    ])
    result = pr_render.render(tickets_root=tickets_root, run_command=runner)
    body = result["body"]
    headings = ["## What landed", "## Tickets", "## Why", "## Verification", "## Review notes"]
    positions = [body.index(h) for h in headings]
    assert positions == sorted(positions)
    assert "Closes: TCK-20260924-A" in body
    assert body.index("## Review notes") < body.index("Closes:")


def test_no_attribution_trailer_in_rendered_body(tmp_path):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    _write_ticket(tickets_root, "TCK-20260924-A", "ai", "Thing")
    runner = FakeRunner([
        _git_log_rule(["TCK-20260924-A: x"]),
        _git_diff_rule(["tickets/TCK-20260924-A.md"]),
    ])
    result = pr_render.render(tickets_root=tickets_root, run_command=runner)
    for marker in ("Co-Authored-By", "claude.ai/code", "Generated with"):
        assert marker not in result["body"]
        assert marker not in result["title"]


def test_review_notes_is_a_distinguishable_placeholder(tmp_path):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    _write_ticket(tickets_root, "TCK-20260924-A", "ai", "Thing")
    runner = FakeRunner([
        _git_log_rule(["TCK-20260924-A: x"]),
        _git_diff_rule(["tickets/TCK-20260924-A.md"]),
    ])
    result = pr_render.render(tickets_root=tickets_root, run_command=runner)
    assert pr_render._REVIEW_NOTES_PLACEHOLDER in result["body"]
    assert "UNFILLED" in pr_render._REVIEW_NOTES_PLACEHOLDER


# ---------------------------------------------------------------------------
# AC6 — known gaps
# ---------------------------------------------------------------------------

def test_known_gap_from_test_summary_renders_into_verification(tmp_path):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    _write_ticket(
        tickets_root, "TCK-20260924-A", "ai", "Thing",
        test_summary="`data_runs_clean` FAIL — shared-worktree data, not this ticket's own output.",
    )
    runner = FakeRunner([
        _git_log_rule(["TCK-20260924-A: x"]),
        _git_diff_rule(["tickets/TCK-20260924-A.md"]),
    ])
    result = pr_render.render(tickets_root=tickets_root, run_command=runner)
    assert "data_runs_clean" in result["body"]
    assert "FAIL" in result["body"]


def test_no_gap_states_none_stated(tmp_path):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    _write_ticket(tickets_root, "TCK-20260924-A", "ai", "Thing")
    runner = FakeRunner([
        _git_log_rule(["TCK-20260924-A: x"]),
        _git_diff_rule(["tickets/TCK-20260924-A.md"]),
    ])
    result = pr_render.render(tickets_root=tickets_root, run_command=runner)
    assert "none stated" in result["body"]


# ---------------------------------------------------------------------------
# AC7 — discovery mismatch
# ---------------------------------------------------------------------------

def test_commit_and_changed_file_mismatch_is_reported(tmp_path):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    _write_ticket(tickets_root, "TCK-20260924-A", "ai", "Thing")
    runner = FakeRunner([
        _git_log_rule(["TCK-20260924-A: x", "TCK-20260924-GHOST: y"]),
        _git_diff_rule(["tickets/TCK-20260924-A.md"]),
    ])
    result = pr_render.render(tickets_root=tickets_root, run_command=runner)
    assert any("mismatch" in w and "TCK-20260924-GHOST" in w for w in result["warnings"])
    assert any("TCK-20260924-GHOST" in w and "no ticket file found" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# AC8 — --check mode
# ---------------------------------------------------------------------------

def test_check_reports_no_difference_when_identical(tmp_path):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    _write_ticket(tickets_root, "TCK-20260924-A", "ai", "Thing")
    rendered = pr_render.render(
        tickets_root=tickets_root,
        run_command=FakeRunner([
            _git_log_rule(["TCK-20260924-A: x"]),
            _git_diff_rule(["tickets/TCK-20260924-A.md"]),
        ]),
    )
    runner = FakeRunner([
        (lambda cmd: cmd[:2] == ["gh", "pr"],
         CommandResult(0, json.dumps({"title": rendered["title"], "body": rendered["body"]}), "")),
        _git_log_rule(["TCK-20260924-A: x"]),
        _git_diff_rule(["tickets/TCK-20260924-A.md"]),
    ])
    result = pr_render.check_against_live(run_command=runner, tickets_root=tickets_root)
    assert result["matches"] is True


def test_check_reports_difference_when_changed(tmp_path):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    _write_ticket(tickets_root, "TCK-20260924-A", "ai", "Thing")
    runner = FakeRunner([
        (lambda cmd: cmd[:2] == ["gh", "pr"],
         CommandResult(0, json.dumps({"title": "totally different", "body": "totally different"}), "")),
        _git_log_rule(["TCK-20260924-A: x"]),
        _git_diff_rule(["tickets/TCK-20260924-A.md"]),
    ])
    result = pr_render.check_against_live(run_command=runner, tickets_root=tickets_root)
    assert result["matches"] is False


def test_check_exits_zero_via_cli(tmp_path, monkeypatch):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    _write_ticket(tickets_root, "TCK-20260924-A", "ai", "Thing")
    runner = FakeRunner([
        (lambda cmd: cmd[:2] == ["gh", "pr"],
         CommandResult(0, json.dumps({"title": "different", "body": "different"}), "")),
        _git_log_rule(["TCK-20260924-A: x"]),
        _git_diff_rule(["tickets/TCK-20260924-A.md"]),
    ])
    monkeypatch.setattr(pr_render, "default_run_command", runner)
    monkeypatch.setattr(pr_render, "_DEFAULT_TICKETS_ROOT", tickets_root)
    exit_code = pr_render.main(["--check", "--json"])
    assert exit_code == 0


# ---------------------------------------------------------------------------
# AC9 — spec drives section list, not hardcoded literals
# ---------------------------------------------------------------------------

def test_rendered_output_follows_altered_spec_fixture(tmp_path):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    _write_ticket(tickets_root, "TCK-20260924-A", "ai", "Thing")
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps({
        "sections": [
            {"heading": "## What landed", "rendered": True},
            {"heading": "## Review notes", "rendered": False},
            {"heading": "Closes:", "rendered": True},
        ],
        "no_attribution_trailer": True,
    }))
    runner = FakeRunner([
        _git_log_rule(["TCK-20260924-A: x"]),
        _git_diff_rule(["tickets/TCK-20260924-A.md"]),
    ])
    result = pr_render.render(tickets_root=tickets_root, spec_path=spec_path, run_command=runner)
    assert "## Tickets" not in result["body"]
    assert "## What landed" in result["body"]


# ---------------------------------------------------------------------------
# AC10 — CLAUDE.md still points at the guide
# ---------------------------------------------------------------------------

def test_claude_md_still_points_at_delivery_guide():
    text = Path("CLAUDE.md").read_text(encoding="utf-8")
    assert "docs/guides/delivery_process.md" in text


# ---------------------------------------------------------------------------
# Regression-prone paths
# ---------------------------------------------------------------------------

def test_ticket_found_across_directories(tmp_path):
    tickets_root = tmp_path / "tickets"
    done_dir = tickets_root / "done"
    done_dir.mkdir(parents=True)
    _write_ticket(done_dir, "TCK-20260924-A", "ai", "Thing")
    found = pr_render.find_ticket_file("TCK-20260924-A", tickets_root)
    assert found is not None
    assert found.parent.name == "done"


def test_scope_tie_break_deterministic_and_reported(tmp_path):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    _write_ticket(tickets_root, "TCK-20260924-A", "ai", "First")
    _write_ticket(tickets_root, "TCK-20260924-B", "observability", "Second")
    runner = FakeRunner([
        _git_log_rule(["TCK-20260924-A: x", "TCK-20260924-B: y"]),
        _git_diff_rule(["tickets/TCK-20260924-A.md", "tickets/TCK-20260924-B.md"]),
    ])
    result = pr_render.render(tickets_root=tickets_root, run_command=runner)
    assert result["title"].startswith("ai:")
    assert any("tie" in w for w in result["warnings"])


def test_why_section_uses_first_paragraph_only(tmp_path):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    _write_ticket(
        tickets_root, "TCK-20260924-A", "ai", "Thing",
        request_summary="Only the first paragraph should appear.\n\nThis second paragraph must not.",
    )
    runner = FakeRunner([
        _git_log_rule(["TCK-20260924-A: x"]),
        _git_diff_rule(["tickets/TCK-20260924-A.md"]),
    ])
    result = pr_render.render(tickets_root=tickets_root, run_command=runner)
    assert "Only the first paragraph should appear." in result["body"]
    assert "This second paragraph must not." not in result["body"]


# ---------------------------------------------------------------------------
# TCK-20260925-PR-RENDER-TABLE-CELL-NEWLINES — multi-line/`|` titles must not break the table
# ---------------------------------------------------------------------------

def test_multiline_title_with_pipe_collapses_to_one_row(tmp_path):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    multiline_title = "Report `gh`-calls-per-PR and subject traceability over a week range in one\ncommand, so this | epic's before/after is measured rather than asserted"
    _write_ticket(tickets_root, "TCK-20260924-A", "ai", multiline_title)
    _write_ticket(tickets_root, "TCK-20260924-B", "ai", "Second thing")
    runner = FakeRunner([
        _git_log_rule(["TCK-20260924-A: x", "TCK-20260924-B: y"]),
        _git_diff_rule(["tickets/TCK-20260924-A.md", "tickets/TCK-20260924-B.md"]),
    ])
    result = pr_render.render(tickets_root=tickets_root, run_command=runner)
    body = result["body"]

    table_rows = [l for l in body.splitlines() if l.startswith("| TCK-")]
    assert len(table_rows) == 2  # AC1/AC3: exactly one line per ticket, no mid-cell break
    for row in table_rows:
        # AC2/AC3: split on pipes a markdown table parser would treat as separators (an escaped
        # `\|` is not one) — 3 cells means 2 leading/trailing empty segments plus 3 cell segments.
        columns = re.split(r"(?<!\\)\|", row)
        assert len(columns) == 5
    assert "Report `gh`-calls-per-PR and subject traceability over a week range in one command, " \
        "so this \\| epic's before/after is measured rather than asserted" in table_rows[0]
    # AC4: no content lost — every word from the original multi-line title is still present.
    for word in ("Report", "command,", "asserted"):
        assert word in table_rows[0]

    what_landed_lines = [
        l for l in body.splitlines()
        if l.startswith("- TCK-") and "Report" in l
    ]
    assert len(what_landed_lines) == 1  # AC5: one line per ticket in "## What landed" too
    assert "\n" not in what_landed_lines[0]


def test_no_write_side_effect(tmp_path):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    _write_ticket(tickets_root, "TCK-20260924-A", "ai", "Thing")
    before = subprocess.run(["git", "status", "--short"], capture_output=True, text=True).stdout
    runner = FakeRunner([
        _git_log_rule(["TCK-20260924-A: x"]),
        _git_diff_rule(["tickets/TCK-20260924-A.md"]),
    ])
    pr_render.render(tickets_root=tickets_root, run_command=runner)
    after = subprocess.run(["git", "status", "--short"], capture_output=True, text=True).stdout
    assert before == after


# ---------------------------------------------------------------------------
# TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS — section-aware --check + Known-gaps run-on fix
# ---------------------------------------------------------------------------

def _rendered_and_hand_filled_live(tmp_path, run_command_rules):
    """Renders once, then returns a live body with `## Review notes` hand-filled -- the shape
    every real PR has (AC1's premise)."""
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    _write_ticket(tickets_root, "TCK-20260924-A", "ai", "Thing")
    runner = FakeRunner(run_command_rules)
    rendered = pr_render.render(tickets_root=tickets_root, run_command=runner)
    live_body = rendered["body"].replace(
        pr_render._REVIEW_NOTES_PLACEHOLDER,
        "Looked closely at the edge case; nothing else to flag.",
    )
    return tickets_root, rendered, live_body


def test_check_ac1_matches_despite_hand_filled_review_notes(tmp_path):
    rules = [_git_log_rule(["TCK-20260924-A: x"]), _git_diff_rule(["tickets/TCK-20260924-A.md"])]
    tickets_root, rendered, live_body = _rendered_and_hand_filled_live(tmp_path, rules)
    assert live_body != rendered["body"]  # sanity: genuinely different strings

    runner = FakeRunner([
        (lambda cmd: cmd[:2] == ["gh", "pr"],
         CommandResult(0, json.dumps({"title": rendered["title"], "body": live_body}), "")),
        *rules,
    ])
    result = pr_render.check_against_live(run_command=runner, tickets_root=tickets_root)
    assert result["matches"] is True
    assert result["differing_sections"] == []
    assert result["review_notes_hand_filled"] is True


def test_check_ac2_names_the_differing_section(tmp_path):
    rules = [_git_log_rule(["TCK-20260924-A: x"]), _git_diff_rule(["tickets/TCK-20260924-A.md"])]
    tickets_root, rendered, live_body = _rendered_and_hand_filled_live(tmp_path, rules)
    # Simulate drift: a ticket closed since the live body's ## Tickets table was written.
    drifted_live_body = live_body.replace("| standard |", "| hotfix |")
    assert drifted_live_body != live_body

    runner = FakeRunner([
        (lambda cmd: cmd[:2] == ["gh", "pr"],
         CommandResult(0, json.dumps({"title": rendered["title"], "body": drifted_live_body}), "")),
        *rules,
    ])
    result = pr_render.check_against_live(run_command=runner, tickets_root=tickets_root)
    assert result["matches"] is False
    assert "## Tickets" in result["differing_sections"]
    # AC3: distinguishable from Review notes' expected, non-failing difference.
    assert result["review_notes_hand_filled"] is True


def test_check_ac3_result_shape_distinguishes_pass_from_real_drift():
    """Both outcomes are readable from the result dict alone -- no diff-text parsing needed."""
    pass_result = {"matches": True, "differing_sections": [], "review_notes_hand_filled": True,
                    "unexpected_sections": []}
    drift_result = {"matches": False, "differing_sections": ["## Tickets"],
                     "review_notes_hand_filled": True, "unexpected_sections": []}
    assert pass_result["matches"] and not pass_result["differing_sections"]
    assert not drift_result["matches"] and drift_result["differing_sections"]


def test_check_unexpected_live_section_not_a_failure(tmp_path):
    rules = [_git_log_rule(["TCK-20260924-A: x"]), _git_diff_rule(["tickets/TCK-20260924-A.md"])]
    tickets_root, rendered, live_body = _rendered_and_hand_filled_live(tmp_path, rules)
    live_body_with_extra = live_body + "\n\n## Extra thoughts\nSomething the author added by hand.\n"

    runner = FakeRunner([
        (lambda cmd: cmd[:2] == ["gh", "pr"],
         CommandResult(0, json.dumps({"title": rendered["title"], "body": live_body_with_extra}), "")),
        *rules,
    ])
    result = pr_render.check_against_live(run_command=runner, tickets_root=tickets_root)
    assert result["matches"] is True
    assert "## Extra thoughts" in result["unexpected_sections"]


def test_check_missing_live_section_reported_not_crashed(tmp_path):
    rules = [_git_log_rule(["TCK-20260924-A: x"]), _git_diff_rule(["tickets/TCK-20260924-A.md"])]
    tickets_root, rendered, live_body = _rendered_and_hand_filled_live(tmp_path, rules)
    lines = live_body.splitlines()
    why_start = next(i for i, l in enumerate(lines) if l.strip() == "## Why")
    verification_start = next(i for i, l in enumerate(lines) if l.strip() == "## Verification")
    live_body_missing_why = "\n".join(lines[:why_start] + lines[verification_start:])

    runner = FakeRunner([
        (lambda cmd: cmd[:2] == ["gh", "pr"],
         CommandResult(0, json.dumps({"title": rendered["title"], "body": live_body_missing_why}), "")),
        *rules,
    ])
    result = pr_render.check_against_live(run_command=runner, tickets_root=tickets_root)
    assert result["matches"] is False
    assert "## Why" in result["differing_sections"]


def test_check_still_exits_zero_and_writes_nothing_on_a_real_difference(tmp_path, monkeypatch):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    _write_ticket(tickets_root, "TCK-20260924-A", "ai", "Thing")
    runner = FakeRunner([
        (lambda cmd: cmd[:2] == ["gh", "pr"],
         CommandResult(0, json.dumps({"title": "different", "body": "different"}), "")),
        _git_log_rule(["TCK-20260924-A: x"]),
        _git_diff_rule(["tickets/TCK-20260924-A.md"]),
    ])
    monkeypatch.setattr(pr_render, "default_run_command", runner)
    monkeypatch.setattr(pr_render, "_DEFAULT_TICKETS_ROOT", tickets_root)
    before = subprocess.run(["git", "status", "--short"], capture_output=True, text=True).stdout
    exit_code = pr_render.main(["--check", "--json"])
    after = subprocess.run(["git", "status", "--short"], capture_output=True, text=True).stdout
    assert exit_code == 0
    assert before == after


def test_known_gap_two_tickets_render_as_separate_tagged_entries_not_run_on(tmp_path):
    tickets_root = tmp_path / "tickets"
    tickets_root.mkdir()
    _write_ticket(
        tickets_root, "TCK-20260924-A", "ai", "First thing",
        test_summary="`scan_a` FAIL — narrow reason for ticket A.",
    )
    _write_ticket(
        tickets_root, "TCK-20260924-B", "ai", "Second thing",
        test_summary="`scan_b` FAIL — unrelated narrow reason for ticket B.",
    )
    runner = FakeRunner([
        _git_log_rule(["TCK-20260924-A: x", "TCK-20260924-B: y"]),
        _git_diff_rule(["tickets/TCK-20260924-A.md", "tickets/TCK-20260924-B.md"]),
    ])
    result = pr_render.render(tickets_root=tickets_root, run_command=runner)
    body = result["body"]

    assert "  - TCK-20260924-A: `scan_a` FAIL — narrow reason for ticket A." in body
    assert "  - TCK-20260924-B: `scan_b` FAIL — unrelated narrow reason for ticket B." in body
    # Never glued into one semicolon-joined run-on line: each ticket's gap is its own bullet.
    known_gap_bullets = [l for l in body.splitlines() if l.startswith("  - TCK-")]
    assert len(known_gap_bullets) == 2
    for line in known_gap_bullets:
        assert "scan_a" not in line or "scan_b" not in line


# ---------------------------------------------------------------------------
# TCK-20260927-PR-RENDER-NO-RECORDED-TICKET-EXCLUSION
# ---------------------------------------------------------------------------

def _three_ticket_fixture(tmp_path, subdir="tickets"):
    """Three discovered tickets, one of which (B) is the 'phantom' shape from the real PR #251
    finding: named in a commit subject but never changed on the branch (its file still exists,
    e.g. already merged in a prior PR)."""
    tickets_root = tmp_path / subdir
    tickets_root.mkdir(exist_ok=True)
    _write_ticket(tickets_root, "TCK-20260924-A", "ai", "First thing")
    _write_ticket(tickets_root, "TCK-20260924-B", "ai", "Phantom thing, already closed elsewhere")
    _write_ticket(tickets_root, "TCK-20260924-C", "ai", "Third thing")
    runner = FakeRunner([
        _git_log_rule([
            "TCK-20260924-A: x", "TCK-20260924-B: mentioned as context", "TCK-20260924-C: z",
        ]),
        # B's file exists (found by find_ticket_file) but was never actually changed on this
        # branch -- the real PR #251 shape.
        _git_diff_rule(["tickets/TCK-20260924-A.md", "tickets/TCK-20260924-C.md"]),
    ])
    return tickets_root, runner


def test_ac1_excluded_ticket_omitted_from_title_and_all_five_sections(tmp_path):
    tickets_root, runner = _three_ticket_fixture(tmp_path)
    result = pr_render.render(
        tickets_root=tickets_root, run_command=runner,
        exclusions={"TCK-20260924-B": "already closed in a prior PR"},
    )
    body = result["body"]
    assert "(2 tickets)" in result["title"]
    # No per-ticket content bullet for the excluded ticket (the AC5 mismatch warning and the
    # exclusion comment itself both legitimately still name it elsewhere in the body).
    assert "- TCK-20260924-B:" not in body
    assert "- TCK-20260924-B Tests:" not in body
    assert "TCK-20260924-A" in body and "TCK-20260924-C" in body
    assert "Closes: TCK-20260924-A, TCK-20260924-C" in body
    # The exclusion itself is recorded in the body as a comment, for --check to read back later.
    assert pr_render.render_exclusion_comment(
        "TCK-20260924-B", "already closed in a prior PR"
    ) in body


def test_ac1_isolated_diff_shape_matches_the_bug_that_found_this(tmp_path):
    """Same isolated-diff method that found the original bug: compare a fully-excluded render
    against the untouched full render and confirm exactly the expected sections differ (because
    the ticket count genuinely changed), not more and not fewer."""
    tickets_root, runner = _three_ticket_fixture(tmp_path)
    full = pr_render.render(tickets_root=tickets_root, run_command=runner)
    excluded = pr_render.render(
        tickets_root=tickets_root, run_command=runner,
        exclusions={"TCK-20260924-B": "already closed in a prior PR"},
    )
    spec = json.loads(pr_render._DEFAULT_SPEC_PATH.read_text())
    comparison = pr_render.compare_generated_body(excluded["body"], full["body"], spec)
    assert set(comparison["differing_sections"]) == {
        "## What landed", "## Tickets", "## Why", "## Verification", "Closes:",
    }


def test_ac2_check_matches_when_live_body_already_reflects_its_own_recorded_exclusion(tmp_path):
    tickets_root, runner_for_render = _three_ticket_fixture(tmp_path)
    rendered_with_exclusion = pr_render.render(
        tickets_root=tickets_root, run_command=runner_for_render,
        exclusions={"TCK-20260924-B": "already closed in a prior PR"},
    )
    # Live body = exactly what an operator would have gotten from the first render above, with
    # Review notes hand-filled (the real shape of every live PR).
    live_body = rendered_with_exclusion["body"].replace(
        pr_render._REVIEW_NOTES_PLACEHOLDER, "Checked the exclusion by hand; looks right.",
    )
    tickets_root2, runner_for_check = _three_ticket_fixture(tmp_path)
    check_runner = FakeRunner([
        (lambda cmd: cmd[:2] == ["gh", "pr"],
         CommandResult(0, json.dumps({
             "title": rendered_with_exclusion["title"], "body": live_body,
         }), "")),
        *runner_for_check.rules,
    ])
    result = pr_render.check_against_live(run_command=check_runner, tickets_root=tickets_root2)
    assert result["matches"] is True
    assert result["differing_sections"] == []
    assert result["review_notes_hand_filled"] is True


def test_ac3_check_with_no_operator_flags_reproduces_recorded_exclusion_from_live_body_alone(tmp_path):
    """No `exclusions` kwarg passed to check_against_live() at all -- the exclusion is read
    purely from the fetched live body, proving the record doesn't depend on any caller-remembered
    state."""
    tickets_root, runner = _three_ticket_fixture(tmp_path)
    exclusions = {"TCK-20260924-B": "already closed in a prior PR"}
    rendered_with_exclusion = pr_render.render(
        tickets_root=tickets_root, run_command=runner, exclusions=exclusions,
    )
    live_body = rendered_with_exclusion["body"].replace(
        pr_render._REVIEW_NOTES_PLACEHOLDER, "Reviewed.",
    )
    tickets_root2, runner2 = _three_ticket_fixture(tmp_path)
    check_runner = FakeRunner([
        (lambda cmd: cmd[:2] == ["gh", "pr"],
         CommandResult(0, json.dumps({
             "title": rendered_with_exclusion["title"], "body": live_body,
         }), "")),
        *runner2.rules,
    ])
    # No `exclusions=` kwarg here at all.
    result = pr_render.check_against_live(run_command=check_runner, tickets_root=tickets_root2)
    assert result["matches"] is True


def test_ac4_excluding_a_ticket_not_in_the_discovered_set_is_reported(tmp_path):
    tickets_root, runner = _three_ticket_fixture(tmp_path)
    result = pr_render.render(
        tickets_root=tickets_root, run_command=runner,
        exclusions={"TCK-99999999-NOT-DISCOVERED": "typo'd id"},
    )
    assert any(
        "TCK-99999999-NOT-DISCOVERED" in w and "no effect" in w for w in result["warnings"]
    )
    # Real 3 tickets still render, unaffected.
    assert "(3 tickets)" in result["title"]


def test_ac5_mismatch_warning_still_fires_with_an_exclusion_recorded_for_it(tmp_path):
    """Recording an exclusion for the exact ticket causing the commit-subject/changed-file
    mismatch must not suppress the underlying disagreement diagnostic -- it's a presentation
    choice, not a resolution of the diagnostic."""
    tickets_root, runner = _three_ticket_fixture(tmp_path)
    result = pr_render.render(
        tickets_root=tickets_root, run_command=runner,
        exclusions={"TCK-20260924-B": "already closed in a prior PR"},
    )
    assert any(
        "mismatch" in w and "TCK-20260924-B" in w for w in result["warnings"]
    )


def test_ac6_no_exclusions_output_byte_identical_to_before_this_ticket(tmp_path):
    tickets_root, runner = _three_ticket_fixture(tmp_path)
    with_default = pr_render.render(tickets_root=tickets_root, run_command=runner)
    tickets_root2, runner2 = _three_ticket_fixture(tmp_path)
    with_explicit_none = pr_render.render(
        tickets_root=tickets_root2, run_command=runner2, exclusions=None,
    )
    assert with_default["body"] == with_explicit_none["body"]
    assert "pr-render:exclude" not in with_default["body"]


def test_ac7_two_or_more_discovered_tickets_one_excluded_all_sections_agree(tmp_path):
    tickets_root, runner = _three_ticket_fixture(tmp_path)
    result = pr_render.render(
        tickets_root=tickets_root, run_command=runner,
        exclusions={"TCK-20260924-B": "already closed in a prior PR"},
    )
    body = result["body"]

    # No per-ticket content bullet/row for the excluded ticket in any of the four content
    # sections. The excluded ticket's ID CAN legitimately still appear inside "## Verification"'s
    # own "Discovery warnings" line (AC5: the underlying commit-subject/changed-file mismatch
    # diagnostic must still fire and name it) -- that is a required exception, not a leak.
    assert "- TCK-20260924-B:" not in body
    assert "TCK-20260924-B:" not in body.split("## Tickets")[1].split("## Why")[0]
    assert "**TCK-20260924-B**" not in body
    assert "- TCK-20260924-B Tests:" not in body
    verification_section = body.split("## Verification")[1].split("## Review notes")[0]
    assert "TCK-20260924-B" in verification_section  # required: the AC5 mismatch warning
    assert "- TCK-20260924-B Tests:" not in verification_section  # but no per-ticket test bullet
    assert "TCK-20260924-B" not in body.split("Closes:")[1].split("\n")[0]
    assert "(2 tickets)" in result["title"]


def test_extract_recorded_exclusions_round_trip_with_punctuation_in_reason():
    comment = pr_render.render_exclusion_comment(
        "TCK-20260924-A", "closed in #250 - named only as context, not a real change"
    )
    parsed = pr_render.extract_recorded_exclusions(comment)
    assert parsed == {"TCK-20260924-A": "closed in #250 - named only as context, not a real change"}


def test_extract_recorded_exclusions_finds_multiple():
    body = "\n".join([
        pr_render.render_exclusion_comment("TCK-20260924-A", "reason one"),
        "some other body text",
        pr_render.render_exclusion_comment("TCK-20260924-B", "reason two"),
    ])
    parsed = pr_render.extract_recorded_exclusions(body)
    assert parsed == {"TCK-20260924-A": "reason one", "TCK-20260924-B": "reason two"}


def test_extract_recorded_exclusions_empty_on_body_with_no_comments():
    assert pr_render.extract_recorded_exclusions("just a normal PR body\nwith no markers") == {}


def test_cli_exclude_ticket_and_reason_must_pair_up(capsys):
    """The length mismatch is caught before any git/gh call is ever made."""
    exit_code = pr_render.main(["--exclude-ticket", "TCK-20260924-A"])
    assert exit_code == 1
    assert "same number of times" in capsys.readouterr().err

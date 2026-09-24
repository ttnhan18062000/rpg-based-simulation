"""Tests for tools/delivery/pr_render.py (TCK-20260924-DELIVERY-PR-RENDERER).

One section per Acceptance Criterion, per staging_artifacts/TCK-20260924-DELIVERY-PR-RENDERER/
test_plan.md. Fixture tickets are small throwaway .md files under tmp_path; git calls are faked.
"""
import json
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

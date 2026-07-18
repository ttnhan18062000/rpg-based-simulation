"""Tests for src/api/agent_ops_dashboard/ingest.py.

Covers TCK-20260716-AGENTOPS-DASHBOARD-BACKEND's AC #2, #3, #6, #7, #8, and the
files_touched/legacy-schema/non-ticket-markdown scope bullets.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.api.agent_ops_dashboard import ingest

import validate  # tools/agent-monitoring/validate.py — importable once ingest.py has run
import validate_frontmatter  # tools/validate_frontmatter.py — same

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_ticket_raw(
    tmp_path: Path,
    lifecycle: str,
    ticket_id: str,
    *,
    subfolder: str | None = None,
    body: str | None = None,
) -> Path:
    rel_dir = tmp_path / "tickets" / lifecycle
    if subfolder:
        rel_dir = rel_dir / subfolder
    rel_dir.mkdir(parents=True, exist_ok=True)
    p = rel_dir / f"{ticket_id}.md"
    frontmatter = (
        "status: active\nlayer: observability\nauthority: P1\naudience: agent\n"
        f"ticket_id: {ticket_id}\nphase: open\ndate: 2026-07-16\ntags: []"
    )
    if body is None:
        body = (
            f"# {ticket_id}\n\n## Tier\nstandard\n\n## Type\nfeature\n\n"
            "## Priority\nP2\n\n## Status\nOPEN\n"
        )
    p.write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")
    return p


def _init_repo_skeleton(tmp_path: Path) -> None:
    (tmp_path / "agent-monitoring").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "inprogress").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "done").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "todos").mkdir(parents=True, exist_ok=True)


def _bump_mtime(path: Path) -> None:
    """Force a distinguishable mtime after a same-tick write, so DashboardCache's
    mtime-based rebuild trigger fires deterministically in fast test runs."""
    future = time.time() + 5
    os.utime(path, (future, future))


# ---------------------------------------------------------------------------
# AC #3 — reuse, not reimplementation
# ---------------------------------------------------------------------------


def test_ingest_reuses_extract_frontmatter_and_validate_allowlists():
    assert ingest.extract_frontmatter is validate_frontmatter.extract_frontmatter
    assert ingest.load_jsonl is validate.load_jsonl
    assert ingest.validate.LEGACY_COMPLETION_FIELDS is validate.LEGACY_COMPLETION_FIELDS
    assert ingest.validate.LEGACY_TERMINAL_STATUS_VALUES is validate.LEGACY_TERMINAL_STATUS_VALUES


def test_ingest_never_imports_query_module():
    import inspect

    source = inspect.getsource(ingest)
    assert "import query" not in source
    assert "from query import" not in source


# ---------------------------------------------------------------------------
# AC #2 — ticket-to-run join returns all matches, sorted start_ts descending
# ---------------------------------------------------------------------------


def test_ticket_run_join_returns_all_matches_sorted_desc():
    runs_all = [
        {"run_id": "TCK-X", "start_ts": "2026-07-01T00:00:00Z", "end_ts": "2026-07-01T01:00:00Z", "final_status": "TESTS_FAILED"},
        {"run_id": "TCK-X", "start_ts": "2026-07-03T00:00:00Z", "end_ts": "2026-07-03T01:00:00Z", "final_status": "DONE"},
        {"run_id": "TCK-X", "start_ts": "2026-07-02T00:00:00Z", "end_ts": None, "final_status": "CRASHED"},
        {"run_id": "TCK-OTHER", "start_ts": "2026-07-05T00:00:00Z", "final_status": "DONE"},
    ]
    matches = ingest.build_matching_runs("TCK-X", runs_all)
    assert len(matches) == 3
    assert [m.start_ts for m in matches] == [
        "2026-07-03T00:00:00Z",
        "2026-07-02T00:00:00Z",
        "2026-07-01T00:00:00Z",
    ]
    assert matches[0].final_status == "DONE"


def test_ticket_run_join_none_start_ts_sorts_last_not_first():
    runs_all = [
        {"run_id": "TCK-Y", "start_ts": None, "final_status": "DONE"},
        {"run_id": "TCK-Y", "start_ts": "2026-07-01T00:00:00Z", "final_status": "DONE"},
    ]
    matches = ingest.build_matching_runs("TCK-Y", runs_all)
    assert matches[0].start_ts == "2026-07-01T00:00:00Z"
    assert matches[1].start_ts is None


def test_ticket_run_join_no_matches_returns_empty_list():
    assert ingest.build_matching_runs("TCK-NOPE", [{"run_id": "TCK-OTHER", "start_ts": "2026-07-01T00:00:00Z"}]) == []


# ---------------------------------------------------------------------------
# TCK-20260717-TICKET-TITLE-PARSE-FIX — title comes from the ## Title body
# section, not the H1 heading (H1 is mandated to equal ticket_id, so
# parse_h1_title would silently degrade title to the ticket_id for every
# ticket in the corpus).
# ---------------------------------------------------------------------------


def test_ticket_title_reads_body_section_not_h1_heading(tmp_path):
    p = _write_ticket_raw(
        tmp_path,
        "inprogress",
        "TCK-20260101-TITLED",
        body=(
            "# TCK-20260101-TITLED\n\n## Title\nFix the frobnicator overheating bug\n\n"
            "## Tier\nstandard\n\n## Type\nbug\n\n## Priority\nP2\n\n## Status\nOPEN\n"
        ),
    )
    record = ingest.parse_ticket_file(p, "inprogress")
    assert record is not None
    assert record["title"] == "Fix the frobnicator overheating bug"
    assert record["title"] != record["ticket_id"]


def test_ticket_title_missing_section_surfaces_empty_string_not_h1(tmp_path):
    p = _write_ticket_raw(
        tmp_path,
        "inprogress",
        "TCK-20260101-NOTITLE",
        body="# TCK-20260101-NOTITLE\n\n## Tier\nstandard\n\n## Type\nbug\n\n## Priority\nP2\n\n## Status\nOPEN\n",
    )
    record = ingest.parse_ticket_file(p, "inprogress")
    assert record is not None
    assert record["title"] == ""


# ---------------------------------------------------------------------------
# AC #6 — missing body sections surface as null, not error/placeholder
# ---------------------------------------------------------------------------


def test_ticket_missing_body_sections_surfaces_null_not_error(tmp_path):
    p = _write_ticket_raw(
        tmp_path,
        "inprogress",
        "TCK-20260101-NOBODY",
        body="# TCK-20260101-NOBODY\n\nJust prose, no ## Tier/## Type/## Priority sections.\n",
    )
    record = ingest.parse_ticket_file(p, "inprogress")
    assert record is not None
    assert record["tier"] is None
    assert record["ticket_type"] is None
    assert record["priority"] is None
    assert record["workflow_status"] is None


def test_ticket_file_without_frontmatter_returns_none(tmp_path):
    p = tmp_path / "tickets" / "todos" / "x"
    p.mkdir(parents=True)
    f = p / "TCK-20260101-NOFRONTMATTER.md"
    f.write_text("# No frontmatter here\n", encoding="utf-8")
    assert ingest.parse_ticket_file(f, "todos") is None


# ---------------------------------------------------------------------------
# Non-ticket markdown in tickets/todos/{folder}/ must not crash the walk
# ---------------------------------------------------------------------------


def test_non_ticket_markdown_in_tickets_dirs_does_not_crash_ingest(tmp_path):
    todos_dir = tmp_path / "tickets" / "todos" / "some-folder"
    todos_dir.mkdir(parents=True)
    (todos_dir / "SEQUENCE.md").write_text("# Sequence\n\nNot a ticket.\n", encoding="utf-8")
    _write_ticket_raw(tmp_path, "todos", "TCK-20260101-REAL", subfolder="some-folder")

    files = ingest.walk_ticket_dirs(tmp_path / "tickets")
    names = {f.name for f in files}
    assert "SEQUENCE.md" not in names
    assert "TCK-20260101-REAL.md" in names


def test_walk_ticket_dirs_covers_all_three_lifecycle_states(tmp_path):
    _write_ticket_raw(tmp_path, "inprogress", "TCK-20260101-A")
    _write_ticket_raw(tmp_path, "done", "TCK-20260101-B", subfolder="some-epic")
    _write_ticket_raw(tmp_path, "todos", "TCK-20260101-C", subfolder="some-folder")

    files = ingest.walk_ticket_dirs(tmp_path / "tickets")
    stems = {f.stem for f in files}
    assert stems == {"TCK-20260101-A", "TCK-20260101-B", "TCK-20260101-C"}


# ---------------------------------------------------------------------------
# AC #7 — is_inferred_active from tools.jsonl tail, ACTIVE_WINDOW_MINUTES=10
# ---------------------------------------------------------------------------


def test_inferred_active_run_from_tools_jsonl_tail():
    now = datetime(2026, 7, 16, 12, 0, 0, tzinfo=timezone.utc)
    tools_by_run_recent = {
        "TCK-LIVE": [
            {"ts": "2026-07-16T11:55:00Z"},
            {"ts": "2026-07-16T11:58:00Z"},
        ],
    }
    result = ingest.compute_inferred_active(tools_by_run_recent, {}, now)
    assert "TCK-LIVE" in result
    assert result["TCK-LIVE"]["inferred_start_ts"] == "2026-07-16T11:55:00Z"


def test_inferred_active_boundary_exactly_at_window_is_included():
    now = datetime(2026, 7, 16, 12, 0, 0, tzinfo=timezone.utc)
    tools_by_run_recent = {"TCK-EDGE": [{"ts": "2026-07-16T11:50:00Z"}]}  # exactly 10:00 ago
    result = ingest.compute_inferred_active(tools_by_run_recent, {}, now)
    assert "TCK-EDGE" in result


def test_inferred_active_boundary_just_past_window_is_excluded():
    now = datetime(2026, 7, 16, 12, 0, 0, tzinfo=timezone.utc)
    tools_by_run_recent = {"TCK-STALE": [{"ts": "2026-07-16T11:49:59Z"}]}  # 10:01 ago
    result = ingest.compute_inferred_active(tools_by_run_recent, {}, now)
    assert "TCK-STALE" not in result


def test_inferred_active_excludes_run_ids_present_in_runs_by_id():
    now = datetime(2026, 7, 16, 12, 0, 0, tzinfo=timezone.utc)
    tools_by_run_recent = {"TCK-DONE": [{"ts": "2026-07-16T11:59:00Z"}]}
    result = ingest.compute_inferred_active(tools_by_run_recent, {"TCK-DONE": {}}, now)
    assert "TCK-DONE" not in result


# ---------------------------------------------------------------------------
# AC #8 — completion flips is_inferred_active true -> false atomically
# ---------------------------------------------------------------------------


def test_active_run_completion_flips_inferred_flag_and_timestamps(tmp_path):
    _init_repo_skeleton(tmp_path)
    now = datetime.now(timezone.utc)
    live_ts = (now - timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ")

    tools_file = tmp_path / "agent-monitoring" / "tools.jsonl"
    tools_file.write_text(
        json.dumps(
            {
                "run_id": "TCK-LIVE-1",
                "seq": 1,
                "ts": live_ts,
                "tool": "Read",
                "input_summary": "/x.py",
                "status": "ok",
                "duration_ms": 10,
            }
        )
        + "\n"
    )

    cache = ingest.DashboardCache(repo_root=tmp_path)
    run = cache.get_run("TCK-LIVE-1")
    assert run is not None
    assert run.is_inferred_active is True
    assert run.end_ts is None

    runs_file = tmp_path / "agent-monitoring" / "runs.jsonl"
    end_ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    runs_file.write_text(
        json.dumps(
            {
                "run_id": "TCK-LIVE-1",
                "start_ts": live_ts,
                "end_ts": end_ts,
                "workflow": "implement-ticket",
                "tier": "hotfix",
                "final_status": "DONE",
                "agent_count": 1,
                "duration_s": 120,
            }
        )
        + "\n"
    )
    _bump_mtime(runs_file)

    run_after = cache.get_run("TCK-LIVE-1")
    assert run_after is not None
    assert run_after.is_inferred_active is False
    assert run_after.end_ts == end_ts
    assert run_after.final_status == "DONE"

    # No intermediate state may show both is_inferred_active=True and a populated end_ts.
    assert not (run_after.is_inferred_active and run_after.end_ts)


# ---------------------------------------------------------------------------
# files_touched: deduped by path, restricted to Read/Edit/Write/MultiEdit
# ---------------------------------------------------------------------------


def test_files_touched_dedup_by_path_restricted_to_edit_tools():
    entries = [
        {
            "tool_calls": [
                {"tool": "Read", "input_summary": "/a.py", "ts": "2026-07-16T10:00:00Z"},
                {"tool": "Bash", "input_summary": "pytest", "ts": "2026-07-16T10:00:01Z"},
            ],
        },
        {
            "tool_calls": [
                {"tool": "Edit", "input_summary": "/a.py", "ts": "2026-07-16T10:05:00Z"},
                {"tool": "Write", "input_summary": "/b.py", "ts": "2026-07-16T10:06:00Z"},
            ],
        },
    ]
    live_tail = [
        {"tool": "Agent", "input_summary": "spawn subagent", "ts": "2026-07-16T10:07:00Z"},
        {"tool": "MultiEdit", "input_summary": "/c.py", "ts": "2026-07-16T10:08:00Z"},
    ]

    touched = ingest.extract_files_touched(entries, live_tail)
    by_path = {f.path: f for f in touched}

    assert set(by_path) == {"/a.py", "/b.py", "/c.py"}
    # First-seen ts+tool wins for /a.py (Read at 10:00:00), not the later Edit.
    assert by_path["/a.py"].tool == "Read"
    assert by_path["/a.py"].ts == "2026-07-16T10:00:00Z"


# ---------------------------------------------------------------------------
# Legacy runs.jsonl schema generations must not crash the join
# ---------------------------------------------------------------------------


def test_legacy_runs_jsonl_schema_generations_do_not_crash_ingest(tmp_path):
    _init_repo_skeleton(tmp_path)
    runs_file = tmp_path / "agent-monitoring" / "runs.jsonl"
    rows = [
        {"run_id": "TCK-LEGACY-A", "started_at": "2026-07-01T00:00:00Z", "finished_at": "2026-07-01T01:00:00Z", "status": "done"},
        {"run_id": "TCK-LEGACY-B", "ts_start": "2026-07-02T00:00:00Z", "ts_end": "2026-07-02T01:00:00Z", "result": "success"},
        {"run_id": "FOLDER-batch-x", "start_ts": "2026-07-03T00:00:00Z", "status": "DONE"},
    ]
    runs_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    cache = ingest.DashboardCache(repo_root=tmp_path)
    runs = cache.get_runs(limit=100)
    assert len(runs) == 3
    by_id = {r.run_id: r for r in runs}
    assert by_id["TCK-LEGACY-A"].final_status == "done"
    assert by_id["TCK-LEGACY-B"].final_status == "DONE"  # resolved via ts_end completion field
    assert by_id["FOLDER-batch-x"].final_status == "DONE"


# ---------------------------------------------------------------------------
# TCK-20260716-AGENTOPS-TICKETS-VIEW — get_tickets AND-across-dimensions,
# OR-within-tag filter semantics (closes a coverage gap left by this file's
# original scope, which never exercised get_tickets's own filter logic).
# ---------------------------------------------------------------------------


def _write_filter_fixture_tickets(tmp_path: Path) -> None:
    _init_repo_skeleton(tmp_path)

    _matched_path = tmp_path / "tickets" / "inprogress" / "TCK-20260101-MATCH.md"
    frontmatter_matched = (
        "status: active\nlayer: observability\nauthority: P1\naudience: agent\n"
        "ticket_id: TCK-20260101-MATCH\nphase: open\ndate: 2026-07-16\n"
        "tags: [observability, infra]"
    )
    _matched_path.write_text(
        f"---\n{frontmatter_matched}\n---\n\n"
        "# TCK-20260101-MATCH\n\n## Tier\nstandard\n\n## Type\nfeature\n\n"
        "## Priority\nP1\n\n## Status\nOPEN\n",
        encoding="utf-8",
    )

    other_layer_path = tmp_path / "tickets" / "inprogress" / "TCK-20260101-OTHERLAYER.md"
    frontmatter_other_layer = (
        "status: active\nlayer: combat\nauthority: P1\naudience: agent\n"
        "ticket_id: TCK-20260101-OTHERLAYER\nphase: open\ndate: 2026-07-16\n"
        "tags: [observability]"
    )
    other_layer_path.write_text(
        f"---\n{frontmatter_other_layer}\n---\n\n"
        "# TCK-20260101-OTHERLAYER\n\n## Tier\nstandard\n\n## Type\nfeature\n\n"
        "## Priority\nP1\n\n## Status\nOPEN\n",
        encoding="utf-8",
    )

    other_tier_path = tmp_path / "tickets" / "inprogress" / "TCK-20260101-OTHERTIER.md"
    frontmatter_other_tier = (
        "status: active\nlayer: observability\nauthority: P1\naudience: agent\n"
        "ticket_id: TCK-20260101-OTHERTIER\nphase: open\ndate: 2026-07-16\n"
        "tags: [infra]"
    )
    other_tier_path.write_text(
        f"---\n{frontmatter_other_tier}\n---\n\n"
        "# TCK-20260101-OTHERTIER\n\n## Tier\nhotfix\n\n## Type\nbug\n\n"
        "## Priority\nP2\n\n## Status\nDONE\n",
        encoding="utf-8",
    )

    no_tag_path = tmp_path / "tickets" / "inprogress" / "TCK-20260101-NOTAGMATCH.md"
    frontmatter_no_tag = (
        "status: active\nlayer: observability\nauthority: P1\naudience: agent\n"
        "ticket_id: TCK-20260101-NOTAGMATCH\nphase: open\ndate: 2026-07-16\n"
        "tags: [unrelated]"
    )
    no_tag_path.write_text(
        f"---\n{frontmatter_no_tag}\n---\n\n"
        "# TCK-20260101-NOTAGMATCH\n\n## Tier\nstandard\n\n## Type\nfeature\n\n"
        "## Priority\nP1\n\n## Status\nOPEN\n",
        encoding="utf-8",
    )


def test_get_tickets_and_across_dimensions_filters_tier_and_layer(tmp_path):
    _write_filter_fixture_tickets(tmp_path)

    cache = ingest.DashboardCache(repo_root=tmp_path)
    results = cache.get_tickets(tier="standard", layer="observability")

    ids = {r.ticket_id for r in results}
    assert ids == {"TCK-20260101-MATCH", "TCK-20260101-NOTAGMATCH"}


def test_get_tickets_or_within_tag(tmp_path):
    _write_filter_fixture_tickets(tmp_path)

    cache = ingest.DashboardCache(repo_root=tmp_path)
    results = cache.get_tickets(tags=["observability", "infra"])

    ids = {r.ticket_id for r in results}
    assert ids == {
        "TCK-20260101-MATCH",
        "TCK-20260101-OTHERLAYER",
        "TCK-20260101-OTHERTIER",
    }
    assert "TCK-20260101-NOTAGMATCH" not in ids


def test_get_tickets_dimension_filter_and_tag_filter_combine_with_and(tmp_path):
    _write_filter_fixture_tickets(tmp_path)

    cache = ingest.DashboardCache(repo_root=tmp_path)
    results = cache.get_tickets(layer="observability", tags=["infra"])

    ids = {r.ticket_id for r in results}
    # TCK-20260101-MATCH (layer=observability, tags include infra) and
    # TCK-20260101-OTHERTIER (layer=observability, tags=[infra]) both satisfy
    # AND(layer=observability, tag in {infra}); TCK-20260101-OTHERLAYER is
    # excluded (wrong layer) even though it has tag "observability" not
    # "infra"; TCK-20260101-NOTAGMATCH is excluded (no "infra" tag).
    assert ids == {"TCK-20260101-MATCH", "TCK-20260101-OTHERTIER"}


# ---------------------------------------------------------------------------
# TCK-20260717-TICKETS-TABLE-PAGINATION — get_tickets limit/offset slicing,
# default-preserves-full-set behavior, and facets computed pre-slice.
# ---------------------------------------------------------------------------


def _write_pagination_fixture_tickets(tmp_path: Path) -> None:
    _init_repo_skeleton(tmp_path)

    fixtures = [
        # (ticket_id, date, tier, layer, workflow_status, priority, tags)
        ("TCK-20260101-PAGE1", "2026-07-15", "epic", "ai", "BLOCKED", "P0", ["ai", "onpage"]),
        ("TCK-20260101-PAGE2", "2026-07-14", "standard", "engine", "INPROGRESS", "P1", ["engine"]),
        ("TCK-20260101-PAGE3", "2026-07-13", "hotfix", "combat", "OPEN", "P2", ["combat", "offpage"]),
        ("TCK-20260101-PAGE4", "2026-07-12", "standard", "world", "DONE", "P1", ["world"]),
        ("TCK-20260101-PAGE5", "2026-07-11", "standard", "world", "OPEN", "P2", ["world"]),
    ]
    for ticket_id, date, tier, layer, status, priority, tags in fixtures:
        path = tmp_path / "tickets" / "inprogress" / f"{ticket_id}.md"
        tags_yaml = "[" + ", ".join(tags) + "]"
        frontmatter = (
            f"status: active\nlayer: {layer}\nauthority: P1\naudience: agent\n"
            f"ticket_id: {ticket_id}\nphase: open\ndate: {date}\ntags: {tags_yaml}"
        )
        path.write_text(
            f"---\n{frontmatter}\n---\n\n"
            f"# {ticket_id}\n\n## Tier\n{tier}\n\n## Type\nfeature\n\n"
            f"## Priority\n{priority}\n\n## Status\n{status}\n",
            encoding="utf-8",
        )


def test_get_tickets_slices_to_requested_page(tmp_path):
    _write_pagination_fixture_tickets(tmp_path)

    cache = ingest.DashboardCache(repo_root=tmp_path)
    results = cache.get_tickets(limit=2, offset=1)

    # Default sort is date_desc, so the full order is PAGE1..PAGE5; offset=1,
    # limit=2 must return exactly [PAGE2, PAGE3].
    assert [r.ticket_id for r in results] == ["TCK-20260101-PAGE2", "TCK-20260101-PAGE3"]
    assert results.total_count == 5


def test_get_tickets_limit_offset_default_preserves_existing_behavior(tmp_path):
    _write_pagination_fixture_tickets(tmp_path)

    cache = ingest.DashboardCache(repo_root=tmp_path)
    results = cache.get_tickets()

    assert len(results) == 5
    assert results.total_count == 5
    assert {r.ticket_id for r in results} == {
        "TCK-20260101-PAGE1",
        "TCK-20260101-PAGE2",
        "TCK-20260101-PAGE3",
        "TCK-20260101-PAGE4",
        "TCK-20260101-PAGE5",
    }


def test_facets_source_reflects_full_filtered_corpus_not_just_current_page(tmp_path):
    _write_pagination_fixture_tickets(tmp_path)

    cache = ingest.DashboardCache(repo_root=tmp_path)
    results = cache.get_tickets(limit=1, offset=0)

    # Only PAGE1 (tier=epic, layer=ai, tags=[ai, onpage]) comes back as items,
    # but facets must still carry values that only exist on later pages.
    assert [r.ticket_id for r in results] == ["TCK-20260101-PAGE1"]
    assert results.facets["tiers"] == ["epic", "hotfix", "standard"]
    assert results.facets["layers"] == ["ai", "combat", "engine", "world"]
    # statuses is the fixed canonical list (see test_statuses_facet_is_canonical_full_set_below),
    # not corpus-derived like every other facet here — EPIC_SCOPED shows even though this fixture
    # has zero epic-tier tickets.
    assert results.facets["statuses"] == ["BLOCKED", "DONE", "EPIC_SCOPED", "INPROGRESS", "OPEN"]
    assert results.facets["priorities"] == ["P0", "P1", "P2"]
    assert "offpage" in results.facets["tags"]
    assert "world" in results.facets["tags"]


def test_statuses_facet_is_canonical_full_set_regardless_of_corpus_content(tmp_path):
    # A ticket corpus with only OPEN and DONE tickets — no INPROGRESS, BLOCKED, or EPIC_SCOPED
    # ticket exists anywhere. The statuses facet must still list all 5 canonical values, so a user
    # can select e.g. BLOCKED and see it's a valid (if currently empty) filter option, matching
    # every other facet's contract of "never hide a legitimate value" but going further: unlike
    # tiers/layers/priorities/tags, statuses doesn't even require the value to exist once anywhere
    # in the corpus.
    _init_repo_skeleton(tmp_path)
    for ticket_id, status in [("TCK-20260101-ONLY-OPEN", "OPEN"), ("TCK-20260101-ONLY-DONE", "DONE")]:
        path = tmp_path / "tickets" / "inprogress" / f"{ticket_id}.md"
        path.write_text(
            f"---\nstatus: active\nlayer: engine\nauthority: P1\naudience: agent\n"
            f"ticket_id: {ticket_id}\nphase: open\ndate: 2026-07-15\ntags: []\n---\n\n"
            f"# {ticket_id}\n\n## Tier\nstandard\n\n## Type\nfeature\n\n"
            f"## Priority\nP1\n\n## Status\n{status}\n",
            encoding="utf-8",
        )

    cache = ingest.DashboardCache(repo_root=tmp_path)
    results = cache.get_tickets()

    assert {r.ticket_id for r in results} == {"TCK-20260101-ONLY-OPEN", "TCK-20260101-ONLY-DONE"}
    assert results.facets["statuses"] == ["BLOCKED", "DONE", "EPIC_SCOPED", "INPROGRESS", "OPEN"]


def test_statuses_facet_unaffected_by_status_query_param(tmp_path):
    # Filtering BY status=DONE must not shrink the statuses facet down to just ["DONE"] — the
    # facet is the canonical list independent of any active filter, same as it's independent of
    # pagination.
    _write_pagination_fixture_tickets(tmp_path)
    cache = ingest.DashboardCache(repo_root=tmp_path)
    results = cache.get_tickets(status="DONE")

    assert [r.ticket_id for r in results] == ["TCK-20260101-PAGE4"]
    assert results.facets["statuses"] == ["BLOCKED", "DONE", "EPIC_SCOPED", "INPROGRESS", "OPEN"]


def test_malformed_jsonl_line_is_skipped_and_counted():
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "runs.jsonl"
        p.write_text(
            '{"run_id": "TCK-OK", "start_ts": "2026-07-01T00:00:00Z", "final_status": "DONE"}\n'
            "not valid json at all\n"
        )
        records, unparsed = ingest.load_jsonl_counted(p)
        assert len(records) == 1
        assert unparsed == 1

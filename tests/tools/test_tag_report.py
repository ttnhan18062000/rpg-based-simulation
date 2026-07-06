"""Tests for tools/tag_report.py."""

import sys
from pathlib import Path

# Ensure tools/ is importable.
_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from tag_report import (  # noqa: E402
    build_tag_rows,
    categorize_tag,
    collect_completed_tickets,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ticket(root: Path, rel: str, frontmatter: str, body: str = "# Ticket\n") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")
    return path


_VALID_FM = """\
status: active
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260705-EXAMPLE
phase: done
date: 2026-07-05
tags: [faction, phase-5, debugging, hardening, some-oneoff-tag]"""

# ---------------------------------------------------------------------------
# categorize_tag — a pure registry lookup now, tested against a small in-memory registry rather
# than the live docs/guidelines/tag_registry.jsonl (mirrors this file's existing tmp_path style).
# ---------------------------------------------------------------------------

_SAMPLE_REGISTRY = {
    "faction": {"tag": "faction", "category": "subsystem-topic", "added_date": "2026-07-06", "note": ""},
    "debugging": {"tag": "debugging", "category": "process-skill-signal", "added_date": "2026-07-06", "note": ""},
    "hardening": {"tag": "hardening", "category": "quality-attribute", "added_date": "2026-07-06", "note": ""},
}


def test_categorize_tag_looks_up_registry_category():
    assert categorize_tag("faction", _SAMPLE_REGISTRY) == "subsystem-topic"
    assert categorize_tag("debugging", _SAMPLE_REGISTRY) == "process-skill-signal"
    assert categorize_tag("hardening", _SAMPLE_REGISTRY) == "quality-attribute"


def test_categorize_tag_phase_milestone_bypasses_registry():
    assert categorize_tag("phase-5", {}) == "phase-milestone"
    # Non-canonical "phase5" (no hyphen) is not recognized as phase-milestone by this classifier —
    # it is a data-quality issue the non-canonical-hit diagnostic surfaces separately.
    assert categorize_tag("phase5", {}) == "unclassified"


def test_categorize_tag_unclassified_when_not_in_registry():
    assert categorize_tag("some-unregistered-tag", _SAMPLE_REGISTRY) == "unclassified"


# ---------------------------------------------------------------------------
# collect_completed_tickets — skip rules
# ---------------------------------------------------------------------------


def test_collect_includes_valid_post_taxonomy_tagged_ticket(tmp_path):
    _make_ticket(tmp_path, "tickets/done/TCK-20260705-EXAMPLE.md", _VALID_FM)

    included, skip_reasons, _skipped_paths = collect_completed_tickets(tmp_path)

    assert len(included) == 1
    ticket_id, tags, path = included[0]
    assert ticket_id == "TCK-20260705-EXAMPLE"
    assert tags == ["faction", "phase-5", "debugging", "hardening", "some-oneoff-tag"]
    assert path == "tickets/done/TCK-20260705-EXAMPLE.md"
    assert sum(skip_reasons.values()) == 0


def test_collect_skips_ticket_with_no_frontmatter(tmp_path):
    path = tmp_path / "tickets/done/legacy-no-frontmatter.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Old ticket\nNo frontmatter block here.\n", encoding="utf-8")

    included, skip_reasons, skipped_paths = collect_completed_tickets(tmp_path)

    assert included == []
    assert skip_reasons["no_frontmatter_legacy_format"] == 1
    assert skipped_paths["no_frontmatter_legacy_format"] == ["tickets/done/legacy-no-frontmatter.md"]


def test_collect_skips_ticket_predating_taxonomy_cutoff(tmp_path):
    fm = _VALID_FM.replace("TCK-20260705-EXAMPLE", "TCK-20260101-OLD").replace(
        "date: 2026-07-05", "date: 2026-01-01"
    )
    _make_ticket(tmp_path, "tickets/done/TCK-20260101-OLD.md", fm)

    included, skip_reasons, _skipped_paths = collect_completed_tickets(tmp_path)

    assert included == []
    assert skip_reasons["pre_taxonomy_or_legacy_ticket_id"] == 1


def test_collect_skips_ticket_with_unparseable_ticket_id(tmp_path):
    fm = _VALID_FM.replace("ticket_id: TCK-20260705-EXAMPLE", "ticket_id: legacy-freeform-id")
    _make_ticket(tmp_path, "tickets/done/legacy-freeform-id.md", fm)

    included, skip_reasons, _skipped_paths = collect_completed_tickets(tmp_path)

    assert included == []
    assert skip_reasons["pre_taxonomy_or_legacy_ticket_id"] == 1


def test_collect_skips_ticket_with_no_tags(tmp_path):
    fm = _VALID_FM.rsplit("\n", 1)[0].replace(
        "tags: [faction, phase-5, debugging, hardening, some-oneoff-tag]", "tags: []"
    )
    _make_ticket(tmp_path, "tickets/done/TCK-20260705-EXAMPLE.md", fm)

    included, skip_reasons, _skipped_paths = collect_completed_tickets(tmp_path)

    assert included == []
    assert skip_reasons["no_tags"] == 1


def test_collect_skips_sequence_md_index_files(tmp_path):
    path = tmp_path / "tickets/done/some-folder/SEQUENCE.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Sequence index\n", encoding="utf-8")

    included, skip_reasons, _skipped_paths = collect_completed_tickets(tmp_path)

    assert included == []
    assert skip_reasons["sequence_index_file"] == 1


def test_collect_recurses_into_done_subfolders(tmp_path):
    _make_ticket(
        tmp_path, "tickets/done/some-folder/TCK-20260705-NESTED.md",
        _VALID_FM.replace("TCK-20260705-EXAMPLE", "TCK-20260705-NESTED"),
    )

    included, _skip_reasons, _skipped_paths = collect_completed_tickets(tmp_path)

    assert len(included) == 1
    assert included[0][0] == "TCK-20260705-NESTED"


def test_collect_missing_done_dir_returns_empty(tmp_path):
    included, skip_reasons, skipped_paths = collect_completed_tickets(tmp_path)

    assert included == []
    assert sum(skip_reasons.values()) == 0
    assert skipped_paths == {}


# ---------------------------------------------------------------------------
# build_tag_rows
# ---------------------------------------------------------------------------


def test_build_tag_rows_counts_and_sorts_by_count_desc():
    included = [
        ("TCK-A", ["faction", "debugging"], "a.md"),
        ("TCK-B", ["faction", "hardening"], "b.md"),
        ("TCK-C", ["faction"], "c.md"),
    ]

    rows, non_canonical_hits = build_tag_rows(included, _SAMPLE_REGISTRY)

    assert rows[0]["tag"] == "faction"
    assert rows[0]["count"] == 3
    assert rows[0]["category"] == "subsystem-topic"
    assert rows[0]["tickets"] == ["TCK-A", "TCK-B", "TCK-C"]
    assert non_canonical_hits == []


def test_build_tag_rows_flags_non_canonical_tags():
    included = [
        ("TCK-A", ["Combat"], "a.md"),  # uppercase — non-canonical
        ("TCK-B", ["simulation_quality"], "b.md"),  # underscore — non-canonical
        ("TCK-C", ["p0"], "c.md"),  # forbidden priority tag
        ("TCK-D", ["sim"], "d.md"),  # known non-canonical synonym
    ]

    _rows, non_canonical_hits = build_tag_rows(included, {})

    flagged_tags = {hit["tag"] for hit in non_canonical_hits}
    assert flagged_tags == {"Combat", "simulation_quality", "p0", "sim"}

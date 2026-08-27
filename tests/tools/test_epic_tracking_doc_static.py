"""Tests for tools/gate_checks/epic_tracking_doc_static.py (TCK-20260826-IMPLEMENT-EPIC-ROADMAP-
DOC-STALENESS-GAP). Doubles as the real, deterministic demonstration this ticket's AC4 asks for
("a real batch run... demonstrates the status block updating correctly after Implement") -- these
tests exercise the exact Python functions implement-epic.js's Discover/Report phases call.
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from gate_checks.epic_tracking_doc_static import (  # noqa: E402
    MARKER_BEGIN,
    MARKER_END,
    parse_tracking_doc_from_sequence,
    render_status_line,
    update_tracking_doc_status_block,
)


class TestParseTrackingDocFromSequence:
    def test_finds_declaration_mid_file(self):
        text = (
            "# Implementation Sequence — my-batch\n\n"
            "tracking_doc: docs/plans/my_roadmap.md\n\n"
            "## Order\n1. TCK-20260101-A\n"
        )
        assert parse_tracking_doc_from_sequence(text) == "docs/plans/my_roadmap.md"

    def test_finds_declaration_on_first_line(self):
        text = "tracking_doc: docs/plans/my_roadmap.md\n# Sequence\n"
        assert parse_tracking_doc_from_sequence(text) == "docs/plans/my_roadmap.md"

    def test_returns_none_when_absent(self):
        text = "# Implementation Sequence — my-batch\n\n## Order\n1. TCK-20260101-A\n"
        assert parse_tracking_doc_from_sequence(text) is None

    def test_returns_none_for_empty_declaration(self):
        text = "tracking_doc:   \n# Sequence\n"
        assert parse_tracking_doc_from_sequence(text) is None

    def test_first_of_multiple_declarations_wins(self):
        text = "tracking_doc: docs/plans/a.md\ntracking_doc: docs/plans/b.md\n"
        assert parse_tracking_doc_from_sequence(text) == "docs/plans/a.md"

    def test_trims_surrounding_whitespace(self):
        text = "tracking_doc:   docs/plans/my_roadmap.md   \n"
        assert parse_tracking_doc_from_sequence(text) == "docs/plans/my_roadmap.md"


class TestRenderStatusLine:
    def test_renders_expected_shape(self):
        line = render_status_line(4, 21, 17, "folder-based batch at `tickets/todos/m1-quick-wins/`", "2026-08-26T10:00:00Z")
        assert "4/21 tickets done, 17 remaining" in line
        assert "2026-08-26T10:00:00Z" in line
        assert "folder-based batch at `tickets/todos/m1-quick-wins/`" in line


class TestUpdateTrackingDocStatusBlock:
    def test_doc_not_found(self, tmp_path):
        result = update_tracking_doc_status_block(
            tmp_path / "nonexistent.md", done_count=1, total_count=2, remaining_count=1,
            description="x", ts="2026-08-26T00:00:00Z",
        )
        assert result == {"status": "doc_not_found", "doc_path": str(tmp_path / "nonexistent.md")}

    def test_markers_missing_when_absent(self, tmp_path):
        doc = tmp_path / "roadmap.md"
        doc.write_text("# Roadmap\n\nSome content.\n")
        result = update_tracking_doc_status_block(
            doc, done_count=1, total_count=2, remaining_count=1, description="x",
            ts="2026-08-26T00:00:00Z",
        )
        assert result["status"] == "markers_missing"
        # No write attempted -- content must be byte-identical to before.
        assert doc.read_text() == "# Roadmap\n\nSome content.\n"

    def test_markers_missing_when_only_begin_present(self, tmp_path):
        doc = tmp_path / "roadmap.md"
        doc.write_text(f"# Roadmap\n\n{MARKER_BEGIN}\nold content\n")
        result = update_tracking_doc_status_block(
            doc, done_count=1, total_count=2, remaining_count=1, description="x",
            ts="2026-08-26T00:00:00Z",
        )
        assert result["status"] == "markers_missing"

    def test_markers_missing_when_reversed(self, tmp_path):
        doc = tmp_path / "roadmap.md"
        doc.write_text(f"# Roadmap\n\n{MARKER_END}\nold content\n{MARKER_BEGIN}\n")
        result = update_tracking_doc_status_block(
            doc, done_count=1, total_count=2, remaining_count=1, description="x",
            ts="2026-08-26T00:00:00Z",
        )
        assert result["status"] == "markers_missing"

    def test_replaces_content_between_markers_and_preserves_surrounding_text(self, tmp_path):
        doc = tmp_path / "roadmap.md"
        doc.write_text(
            f"# Roadmap\n\n### M1 — Quick Wins (IN PROGRESS)\n\n"
            f"{MARKER_BEGIN}\n"
            f"stale old line\n"
            f"{MARKER_END}\n\n"
            f"No dependencies on anything else.\n"
        )
        result = update_tracking_doc_status_block(
            doc, done_count=4, total_count=21, remaining_count=17,
            description="folder-based batch at `tickets/todos/m1-quick-wins/`",
            ts="2026-08-26T10:00:00Z",
        )
        assert result["status"] == "updated"
        new_text = doc.read_text()
        assert "# Roadmap" in new_text
        assert "### M1 — Quick Wins (IN PROGRESS)" in new_text
        assert "No dependencies on anything else." in new_text
        assert "stale old line" not in new_text
        assert "4/21 tickets done, 17 remaining" in new_text
        assert new_text.count(MARKER_BEGIN) == 1
        assert new_text.count(MARKER_END) == 1

    def test_idempotent_on_second_call_no_duplication(self, tmp_path):
        doc = tmp_path / "roadmap.md"
        doc.write_text(f"# Roadmap\n\n{MARKER_BEGIN}\nfirst\n{MARKER_END}\n")

        update_tracking_doc_status_block(
            doc, done_count=1, total_count=21, remaining_count=20, description="x",
            ts="2026-08-26T09:00:00Z",
        )
        result2 = update_tracking_doc_status_block(
            doc, done_count=2, total_count=21, remaining_count=19, description="x",
            ts="2026-08-26T10:00:00Z",
        )
        assert result2["status"] == "updated"
        final_text = doc.read_text()
        assert final_text.count(MARKER_BEGIN) == 1
        assert final_text.count(MARKER_END) == 1
        assert "2/21 tickets done, 19 remaining" in final_text
        assert "1/21 tickets done, 20 remaining" not in final_text

"""Tests for tools/generate_registry.py."""

import sys
from pathlib import Path

import pytest

# Ensure tools/ is importable.
_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from generate_registry import (  # noqa: E402
    collect_docs,
    collect_tickets,
    generate_registry,
    join_artifact_files,
    parse_body_section,
    parse_h1_title,
    parse_related_code_areas,
    sort_entries,
    _invert_date,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_doc(tmp_path: Path, rel: str, frontmatter: str, body: str = "") -> Path:
    """Create a doc file under tmp_path/docs/<rel> with given frontmatter and body."""
    p = tmp_path / "docs" / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")
    return p


def _make_ticket(tmp_path: Path, name: str, frontmatter: str, body: str = "") -> Path:
    """Create a ticket file under tmp_path/tickets/done/<name> with given frontmatter and body."""
    p = tmp_path / "tickets" / "done" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Group 1: Doc entry generation
# ---------------------------------------------------------------------------


class TestDocEntryGeneration:
    def test_doc_entry_has_correct_type(self, tmp_path):
        _make_doc(tmp_path, "mechanics/ch01.md",
                  "status: authoritative\nlayer: mechanics\nauthority: P0\naudience: developer\n"
                  "last_verified: 2026-06-01\ntags: [combat]",
                  "# Combat Laws\n")
        entries, errors = collect_docs(tmp_path)
        assert errors == []
        assert len(entries) == 1
        assert entries[0]["type"] == "doc"

    def test_doc_entry_fields_from_frontmatter(self, tmp_path):
        _make_doc(tmp_path, "mechanics/ch01.md",
                  "status: authoritative\nlayer: mechanics\nauthority: P0\naudience: developer\n"
                  "last_verified: 2026-06-01\ntags: [combat, damage]",
                  "# Combat Laws\n")
        entries, errors = collect_docs(tmp_path)
        assert errors == []
        e = entries[0]
        assert e["status"] == "authoritative"
        assert e["layer"] == "mechanics"
        assert e["authority"] == "P0"
        assert e["audience"] == "developer"
        assert e["last_verified"] == "2026-06-01"
        assert e["tags"] == ["combat", "damage"]

    def test_doc_entry_path_is_relative_to_root(self, tmp_path):
        _make_doc(tmp_path, "mechanics/ch01.md",
                  "status: active\nlayer: mechanics\nauthority: P1\naudience: developer\ntags: []",
                  "# Foo\n")
        entries, errors = collect_docs(tmp_path)
        assert errors == []
        assert entries[0]["path"] == "docs/mechanics/ch01.md"

    def test_doc_entry_skips_archive_subdir(self, tmp_path):
        _make_doc(tmp_path, "archive/old.md",
                  "status: archive\nlayer: misc\nauthority: P2\naudience: developer\n"
                  "original_date: 2024-01-01\ntags: []",
                  "# Old doc\n")
        _make_doc(tmp_path, "mechanics/ch01.md",
                  "status: active\nlayer: mechanics\nauthority: P1\naudience: developer\ntags: []",
                  "# New doc\n")
        entries, errors = collect_docs(tmp_path)
        assert errors == []
        assert len(entries) == 1
        assert "archive" not in entries[0]["path"]

    def test_doc_entry_skips_parity_ledger_subdir(self, tmp_path):
        _make_doc(tmp_path, "parity_ledger/combat.md",
                  "status: active\nlayer: combat\nauthority: P1\naudience: developer\ntags: []",
                  "# Parity\n")
        entries, errors = collect_docs(tmp_path)
        assert errors == []
        assert entries == []

    def test_doc_entry_missing_frontmatter_is_error(self, tmp_path):
        p = tmp_path / "docs" / "engine" / "nofm.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# No frontmatter\n\nJust body.\n", encoding="utf-8")
        entries, errors = collect_docs(tmp_path)
        assert len(errors) == 1
        assert "nofm.md" in errors[0]

    def test_doc_entry_tags_empty_list(self, tmp_path):
        _make_doc(tmp_path, "engine/foo.md",
                  "status: active\nlayer: engine\nauthority: P1\naudience: developer\ntags: []",
                  "# Foo\n")
        entries, errors = collect_docs(tmp_path)
        assert errors == []
        assert entries[0]["tags"] == []


# ---------------------------------------------------------------------------
# Group 2: Ticket entry generation
# ---------------------------------------------------------------------------


class TestTicketEntryGeneration:
    def test_ticket_entry_has_correct_type(self, tmp_path):
        _make_ticket(tmp_path, "TCK-20260601-FOO.md",
                     "status: historical\nlayer: engine\nauthority: P1\naudience: agent\n"
                     "ticket_id: TCK-20260601-FOO\nphase: done\ndate: 2026-06-01\ntags: []",
                     "## Title\nFoo\n\n## Tier\nhotfix\n\n## Type\nbug\n")
        entries = collect_tickets(tmp_path)
        assert len(entries) == 1
        assert entries[0]["type"] == "ticket"

    def test_ticket_entry_ticket_id_from_frontmatter(self, tmp_path):
        _make_ticket(tmp_path, "TCK-20260601-FOO.md",
                     "status: historical\nlayer: engine\nauthority: P1\naudience: agent\n"
                     "ticket_id: TCK-20260601-FOO\nphase: done\ndate: 2026-06-01\ntags: []",
                     "## Title\nFoo\n")
        entries = collect_tickets(tmp_path)
        assert entries[0]["ticket_id"] == "TCK-20260601-FOO"

    def test_ticket_entry_ticket_id_fallback_to_stem(self, tmp_path):
        p = tmp_path / "tickets" / "done" / "OLD-TICKET.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# No frontmatter\n\n## Title\nOld\n", encoding="utf-8")
        entries = collect_tickets(tmp_path)
        assert len(entries) == 1
        assert entries[0]["ticket_id"] == "OLD-TICKET"

    def test_ticket_entry_date_from_frontmatter(self, tmp_path):
        _make_ticket(tmp_path, "TCK-20260601-FOO.md",
                     "status: historical\nlayer: engine\nauthority: P1\naudience: agent\n"
                     "ticket_id: TCK-20260601-FOO\nphase: done\ndate: 2026-06-01\ntags: []",
                     "## Title\nFoo\n")
        entries = collect_tickets(tmp_path)
        assert entries[0]["date"] == "2026-06-01"

    def test_ticket_entry_tags_list(self, tmp_path):
        _make_ticket(tmp_path, "TCK-20260601-FOO.md",
                     "status: historical\nlayer: engine\nauthority: P1\naudience: agent\n"
                     "ticket_id: TCK-20260601-FOO\nphase: done\ndate: 2026-06-01\ntags: [foo, bar]",
                     "## Title\nFoo\n")
        entries = collect_tickets(tmp_path)
        assert entries[0]["tags"] == ["foo", "bar"]

    def test_ticket_missing_frontmatter_emits_warning_not_error(self, tmp_path, capsys):
        p = tmp_path / "tickets" / "done" / "OLD.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# No frontmatter\n", encoding="utf-8")
        entries = collect_tickets(tmp_path)
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert len(entries) == 1  # Still emitted.


# ---------------------------------------------------------------------------
# Group 3: Artifact join
# ---------------------------------------------------------------------------


class TestArtifactJoin:
    def test_artifact_files_present(self, tmp_path):
        art_dir = tmp_path / "stored_artifacts" / "TCK-20260601-FOO"
        art_dir.mkdir(parents=True)
        (art_dir / "investigation.md").write_text("---\n---\n# Investigation\n")
        (art_dir / "plan.md").write_text("---\n---\n# Plan\n")
        files = join_artifact_files(tmp_path, "TCK-20260601-FOO")
        assert sorted(files) == [
            "stored_artifacts/TCK-20260601-FOO/investigation.md",
            "stored_artifacts/TCK-20260601-FOO/plan.md",
        ]

    def test_artifact_files_empty_when_no_folder(self, tmp_path):
        files = join_artifact_files(tmp_path, "TCK-DOES-NOT-EXIST")
        assert files == []

    def test_artifact_files_only_md(self, tmp_path):
        art_dir = tmp_path / "stored_artifacts" / "TCK-20260601-FOO"
        art_dir.mkdir(parents=True)
        (art_dir / "plan.md").write_text("---\n---\n# Plan\n")
        (art_dir / "notes.txt").write_text("not markdown")
        files = join_artifact_files(tmp_path, "TCK-20260601-FOO")
        assert files == ["stored_artifacts/TCK-20260601-FOO/plan.md"]

    def test_artifact_files_joined_into_ticket_entry(self, tmp_path):
        _make_ticket(tmp_path, "TCK-20260601-FOO.md",
                     "status: historical\nlayer: engine\nauthority: P1\naudience: agent\n"
                     "ticket_id: TCK-20260601-FOO\nphase: done\ndate: 2026-06-01\ntags: []",
                     "## Title\nFoo\n")
        art_dir = tmp_path / "stored_artifacts" / "TCK-20260601-FOO"
        art_dir.mkdir(parents=True)
        (art_dir / "plan.md").write_text("---\n---\n# Plan\n")
        entries = collect_tickets(tmp_path)
        assert entries[0]["artifact_files"] == ["stored_artifacts/TCK-20260601-FOO/plan.md"]


# ---------------------------------------------------------------------------
# Group 4: Sort order
# ---------------------------------------------------------------------------


class TestSortOrder:
    def test_docs_before_tickets(self, tmp_path):
        doc_entry = {"type": "doc", "path": "docs/a.md", "authority": "P2"}
        ticket_entry = {"type": "ticket", "path": "tickets/done/t.md", "date": "2026-06-01"}
        sorted_entries = sort_entries([ticket_entry, doc_entry])
        assert sorted_entries[0]["type"] == "doc"
        assert sorted_entries[1]["type"] == "ticket"

    def test_docs_sorted_by_authority(self, tmp_path):
        e_p2 = {"type": "doc", "path": "docs/b.md", "authority": "P2"}
        e_p0 = {"type": "doc", "path": "docs/a.md", "authority": "P0"}
        e_p1 = {"type": "doc", "path": "docs/c.md", "authority": "P1"}
        result = sort_entries([e_p2, e_p0, e_p1])
        assert [e["authority"] for e in result] == ["P0", "P1", "P2"]

    def test_docs_same_authority_sorted_by_path(self, tmp_path):
        e1 = {"type": "doc", "path": "docs/z.md", "authority": "P1"}
        e2 = {"type": "doc", "path": "docs/a.md", "authority": "P1"}
        result = sort_entries([e1, e2])
        assert result[0]["path"] == "docs/a.md"
        assert result[1]["path"] == "docs/z.md"

    def test_tickets_sorted_by_date_descending(self, tmp_path):
        t1 = {"type": "ticket", "path": "tickets/done/a.md", "date": "2026-01-01"}
        t2 = {"type": "ticket", "path": "tickets/done/b.md", "date": "2026-06-01"}
        t3 = {"type": "ticket", "path": "tickets/done/c.md", "date": "2025-12-01"}
        result = sort_entries([t1, t2, t3])
        dates = [e["date"] for e in result]
        assert dates == ["2026-06-01", "2026-01-01", "2025-12-01"]

    def test_tickets_empty_date_sorts_last(self, tmp_path):
        t_no_date = {"type": "ticket", "path": "tickets/done/old.md", "date": ""}
        t_with_date = {"type": "ticket", "path": "tickets/done/new.md", "date": "2026-06-01"}
        result = sort_entries([t_no_date, t_with_date])
        assert result[0]["date"] == "2026-06-01"
        assert result[1]["date"] == ""


# ---------------------------------------------------------------------------
# Group 5: Title extraction
# ---------------------------------------------------------------------------


class TestTitleExtraction:
    def test_h1_title_from_body(self):
        body = "\n# Combat Laws\n\nSome content.\n"
        assert parse_h1_title(body) == "Combat Laws"

    def test_h1_title_ignores_h2(self):
        body = "## Not H1\n# Actual Title\n"
        assert parse_h1_title(body) == "Actual Title"

    def test_h1_title_empty_when_absent(self):
        body = "## Only H2\nContent\n"
        assert parse_h1_title(body) == ""

    def test_ticket_title_from_body_section(self):
        body = "## Title\nDo the thing\n\n## Status\nDONE\n"
        assert parse_body_section(body, "Title") == "Do the thing"

    def test_ticket_title_empty_when_absent(self):
        body = "## Status\nDONE\n"
        assert parse_body_section(body, "Title") == ""


# ---------------------------------------------------------------------------
# Group 6: related_code_areas extraction
# ---------------------------------------------------------------------------


class TestRelatedCodeAreas:
    def test_extracts_backtick_paths(self):
        section = "- `src/core/foo.py` (new)\n- `src/core/bar.py` (modified)\n"
        areas = parse_related_code_areas(section)
        assert areas == ["src/core/foo.py", "src/core/bar.py"]

    def test_skips_lines_without_backticks(self):
        section = "- plain text line\n- `src/core/foo.py`\n"
        areas = parse_related_code_areas(section)
        assert areas == ["src/core/foo.py"]

    def test_empty_section_returns_empty_list(self):
        areas = parse_related_code_areas("")
        assert areas == []

    def test_ticket_with_related_code_areas(self, tmp_path):
        body = (
            "## Title\nFoo\n\n"
            "## Related Code Areas\n"
            "- `src/core/engine.py` (new)\n"
            "- `src/systems/registry.py` (modified)\n\n"
            "## Status\nDONE\n"
        )
        _make_ticket(tmp_path, "TCK-20260601-FOO.md",
                     "status: historical\nlayer: engine\nauthority: P1\naudience: agent\n"
                     "ticket_id: TCK-20260601-FOO\nphase: done\ndate: 2026-06-01\ntags: []",
                     body)
        entries = collect_tickets(tmp_path)
        assert entries[0]["related_code_areas"] == ["src/core/engine.py", "src/systems/registry.py"]

    def test_ticket_no_related_code_areas_section(self, tmp_path):
        _make_ticket(tmp_path, "TCK-20260601-BAR.md",
                     "status: historical\nlayer: engine\nauthority: P1\naudience: agent\n"
                     "ticket_id: TCK-20260601-BAR\nphase: done\ndate: 2026-06-01\ntags: []",
                     "## Title\nBar\n")
        entries = collect_tickets(tmp_path)
        assert entries[0]["related_code_areas"] == []


# ---------------------------------------------------------------------------
# Group 7: YAML output and file written to correct path
# ---------------------------------------------------------------------------


class TestYAMLOutput:
    def test_registry_yaml_written(self, tmp_path):
        _make_doc(tmp_path, "engine/foo.md",
                  "status: active\nlayer: engine\nauthority: P1\naudience: developer\ntags: []",
                  "# Foo\n")
        output = tmp_path / "docs" / "REGISTRY.yaml"
        rc = generate_registry(tmp_path, output)
        assert rc == 0
        assert output.exists()

    def test_registry_yaml_is_valid(self, tmp_path):
        import yaml
        _make_doc(tmp_path, "engine/foo.md",
                  "status: active\nlayer: engine\nauthority: P1\naudience: developer\ntags: []",
                  "# Foo\n")
        _make_ticket(tmp_path, "TCK-20260601-BAR.md",
                     "status: historical\nlayer: engine\nauthority: P1\naudience: agent\n"
                     "ticket_id: TCK-20260601-BAR\nphase: done\ndate: 2026-06-01\ntags: []",
                     "## Title\nBar\n")
        output = tmp_path / "docs" / "REGISTRY.yaml"
        generate_registry(tmp_path, output)
        data = yaml.safe_load(output.read_text())
        assert isinstance(data, list)
        assert len(data) == 2

    def test_registry_exits_nonzero_on_missing_doc_frontmatter(self, tmp_path):
        p = tmp_path / "docs" / "engine" / "nofm.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# No frontmatter\n\nBody.\n", encoding="utf-8")
        output = tmp_path / "docs" / "REGISTRY.yaml"
        rc = generate_registry(tmp_path, output)
        assert rc == 1

    def test_registry_header_comment_present(self, tmp_path):
        _make_doc(tmp_path, "engine/foo.md",
                  "status: active\nlayer: engine\nauthority: P1\naudience: developer\ntags: []",
                  "# Foo\n")
        output = tmp_path / "docs" / "REGISTRY.yaml"
        generate_registry(tmp_path, output)
        content = output.read_text()
        assert "# docs/REGISTRY.yaml" in content
        assert "make docs-registry" in content


# ---------------------------------------------------------------------------
# Group 8: Regression / edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_invert_date_newest_sorts_first(self):
        dates = ["2026-06-01", "2025-01-15", "2026-01-01"]
        inverted = sorted(dates, key=_invert_date)
        # After sorting by inverted key ascending, newest should be first.
        assert inverted[0] == "2026-06-01"
        assert inverted[2] == "2025-01-15"

    def test_invert_date_empty_sorts_last(self):
        dates = ["2026-06-01", "", "2025-01-01"]
        inverted = sorted(dates, key=_invert_date)
        assert inverted[-1] == ""

    def test_docs_and_tickets_both_present(self, tmp_path):
        _make_doc(tmp_path, "mechanics/ch01.md",
                  "status: authoritative\nlayer: mechanics\nauthority: P0\naudience: developer\n"
                  "last_verified: 2026-06-01\ntags: []",
                  "# Chapter 1\n")
        _make_ticket(tmp_path, "TCK-20260601-FOO.md",
                     "status: historical\nlayer: engine\nauthority: P1\naudience: agent\n"
                     "ticket_id: TCK-20260601-FOO\nphase: done\ndate: 2026-06-01\ntags: []",
                     "## Title\nFoo\n")
        output = tmp_path / "docs" / "REGISTRY.yaml"
        rc = generate_registry(tmp_path, output)
        assert rc == 0
        import yaml
        data = yaml.safe_load(output.read_text())
        types = [e["type"] for e in data]
        # doc before ticket
        assert types.index("doc") < types.index("ticket")

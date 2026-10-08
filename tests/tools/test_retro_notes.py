"""The retro Notes convention (TCK-20261007-RETRO-NOTES-ACCUMULATION-COLLAPSE); the older notes tests stay in test_generate_retro.py."""
from __future__ import annotations

import sys
from pathlib import Path

_MON = Path(__file__).resolve().parents[2] / "tools" / "agent-monitoring"
if str(_MON) not in sys.path:
    sys.path.insert(0, str(_MON))

import generate_retro  # noqa: E402
import retro_notes  # noqa: E402

FRESH = "# Report\n\n## Run Summary\n\nnew data\n\n## Notes\n\n_placeholder_\n"
HEAD = "# Report\n\n## Run Summary\n\nold data\n\n"
UNMARKED = "Hand-written opening note, no marker.\n\n- A bullet that must survive byte-for-byte.\n"
OLD18 = "<!-- retro-note runs=18 -->\n**Addendum (2026-09-29, 18 runs):** the first look.\n\n- detail one\n- detail two\n"
OLD38 = "<!-- retro-note runs=38 -->\n**Addendum (2026-09-30, 38 runs):** the second look.\n"
FINAL = "<!-- retro-note runs=251 final -->\n**Final (2026-10-07, 251 runs):** the current statement.\n\n```\nverbatim block   with   odd spacing\n```\n"


def _existing(*parts):
    return HEAD + "## Notes\n\n" + "\n".join(parts)


def _write(tmp_path, existing, run_count=None, force=False):
    out = tmp_path / "RETRO-TEST.md"
    out.write_text(existing)
    status = generate_retro._write_report_preserving_notes(FRESH, out, force, run_count=run_count)
    return out, status


def test_earlier_stamped_addenda_collapse_to_one_line_and_the_final_block_is_byte_for_byte(tmp_path):
    out, status = _write(tmp_path, _existing(UNMARKED, OLD18, OLD38, FINAL), run_count=251)
    text = out.read_text()
    assert FINAL in text and UNMARKED in text
    assert "detail one" not in text and "detail two" not in text  # the bodies are gone; only headlines remain
    lines = [l for l in text.splitlines() if l.startswith("<!-- retro-note-collapsed")]
    assert len(lines) == 2 and "runs=18 -->" in lines[0] and "runs=38 -->" in lines[1]
    assert "the first look" in lines[0] and "archive/RETRO-TEST-notes-history.md" in lines[0]
    assert "collapsed the note stamped at 18 runs" in status
    assert "new data" in text and "old data" not in text  # above Notes is the fresh report


def test_the_full_text_is_archived_before_collapsing(tmp_path):
    out, _ = _write(tmp_path, _existing(OLD18, FINAL), run_count=251)
    archive = (tmp_path / "archive" / "RETRO-TEST-notes-history.md").read_text()
    assert OLD18.rstrip("\n") in archive and "detail two" in archive


def test_unmarked_text_survives_byte_for_byte_even_when_nothing_is_marked(tmp_path):
    existing = _existing(UNMARKED)
    out, _ = _write(tmp_path, existing, run_count=999)
    assert out.read_text() == FRESH.split("## Notes")[0] + "## Notes\n\n" + UNMARKED
    assert not (tmp_path / "archive").exists()


def test_a_note_stamped_at_18_runs_is_flagged_stale_against_251(tmp_path):
    out, status = _write(tmp_path, _existing(OLD18), run_count=251)
    text = out.read_text()
    assert "Notes may be stale" in text and "written at 18 runs" in text and "251 runs" in text
    assert OLD18 in text  # flagged, not touched
    assert "older than the data" in status


def test_a_current_final_note_is_not_flagged(tmp_path):
    out, _ = _write(tmp_path, _existing(FINAL), run_count=251)
    assert "stale" not in out.read_text()
    out2, _ = _write(tmp_path, _existing(FINAL), run_count=100)
    assert "stale" not in out2.read_text()


def test_regenerating_twice_gives_identical_output_and_a_stable_archive(tmp_path):
    out, _ = _write(tmp_path, _existing(UNMARKED, OLD18, OLD38, FINAL), run_count=300)
    first = out.read_text()
    archive = tmp_path / "archive" / "RETRO-TEST-notes-history.md"
    first_archive = archive.read_text()
    generate_retro._write_report_preserving_notes(FRESH, out, False, run_count=300)
    assert out.read_text() == first and archive.read_text() == first_archive
    assert first.count("Notes may be stale") == 1  # the status line does not accumulate


def test_force_still_discards_notes_without_collapsing_or_archiving(tmp_path):
    out, status = _write(tmp_path, _existing(OLD18, FINAL), run_count=251, force=True)
    assert out.read_text() == FRESH and "--force" in status
    assert not (tmp_path / "archive").exists()


def test_a_malformed_marker_is_unmarked_text_and_is_never_collapsed(tmp_path):
    bad = "<!-- retro-note runs=lots -->\nnot a real stamp\n"
    out, _ = _write(tmp_path, _existing(bad, FINAL), run_count=251)
    text = out.read_text()
    assert bad in text and "retro-note-collapsed" not in text


def test_nothing_collapses_without_a_final_entry(tmp_path):
    out, _ = _write(tmp_path, _existing(OLD18, OLD38), run_count=38)
    text = out.read_text()
    assert OLD18 in text and OLD38 in text and "retro-note-collapsed" not in text


def test_a_failing_archive_write_collapses_nothing_and_says_so(tmp_path, monkeypatch):
    monkeypatch.setattr(retro_notes, "_archive", lambda *a, **k: (_ for _ in ()).throw(OSError("disk full")))
    out, status = _write(tmp_path, _existing(OLD18, FINAL), run_count=251)
    text = out.read_text()
    assert OLD18 in text and FINAL in text and "retro-note-collapsed" not in text
    assert "WARNING: notes not collapsed: disk full" in status


def test_a_crash_in_the_convention_keeps_the_notes_verbatim(tmp_path, monkeypatch):
    monkeypatch.setattr(retro_notes, "process_notes", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    existing = _existing(UNMARKED, OLD18, FINAL)
    out, status = _write(tmp_path, existing, run_count=251)
    assert out.read_text().endswith("## Notes\n\n" + "\n".join([UNMARKED, OLD18, FINAL]))
    assert "convention not applied" in status


def test_output_above_notes_is_the_fresh_report_regardless_of_the_convention(tmp_path):
    out, _ = _write(tmp_path, _existing(OLD18, FINAL), run_count=251)
    assert out.read_text().split("## Notes")[0] == FRESH.split("## Notes")[0]


def test_a_collapsed_line_is_never_collapsed_again_and_a_later_final_collapses_the_old_final(tmp_path):
    out, _ = _write(tmp_path, _existing(OLD18, FINAL), run_count=251)
    newer = "<!-- retro-note runs=400 final -->\n**Final (2026-10-20, 400 runs):** newer.\n"
    out.write_text(out.read_text().rstrip("\n") + "\n\n" + newer)
    generate_retro._write_report_preserving_notes(FRESH, out, False, run_count=400)
    text = out.read_text()
    assert newer in text and "verbatim block" not in text.split("retro-note-collapsed runs=251")[0]
    assert text.count("retro-note-collapsed") == 2
    assert "verbatim block   with   odd spacing" in (tmp_path / "archive" / "RETRO-TEST-notes-history.md").read_text()

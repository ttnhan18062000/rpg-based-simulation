"""The CI job-summary line that states how many real-Aseprite tests were skipped (ADR D10)."""

from __future__ import annotations

from pathlib import Path

from tools import ci_aseprite_skip_line as skip_line

XML = """<testsuites><testsuite tests="3" skipped="2">
<testcase classname="a" name="x"><skipped message="requires aseprite and bwrap (real Aseprite runs locally only, ADR D10)"/></testcase>
<testcase classname="a" name="y"><skipped message="requires aseprite and bwrap (real Aseprite runs locally only, ADR D10)"/></testcase>
<testcase classname="a" name="z"><skipped message="some other reason"/></testcase>
</testsuite></testsuites>"""


def test_counts_only_aseprite_skips(tmp_path: Path):
    path = tmp_path / "j.xml"
    path.write_text(XML)
    assert skip_line.count_aseprite_skips(path) == 2
    line = skip_line.render_line(2)
    assert "2" in line and "ADR D10" in line


def test_missing_or_bad_file_never_raises(tmp_path: Path):
    assert skip_line.count_aseprite_skips(tmp_path / "none.xml") is None
    bad = tmp_path / "bad.xml"
    bad.write_text("<<")
    assert skip_line.count_aseprite_skips(bad) is None
    assert "no JUnit" in skip_line.render_line(None)
    assert skip_line.main([str(tmp_path / "none.xml")]) == 0

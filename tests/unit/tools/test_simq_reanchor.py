"""TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE: the re-anchor tool needs an identical pair, honours exclusions and keeps the fixture layout."""
from __future__ import annotations

import copy
import json

import pytest

from tests.simulation_quality import test_grade_regression as gr
from tools.test_architecture import simq_reanchor as ra

FIXTURE = {
    "_note": "meta",
    "w_seed1_200t": {"FACTION": {"grade": "S", "score": 2.9}, "ECONOMY": {"grade": "B", "score": 0.18}},
    "w_seed2_200t": {"FACTION": {"grade": "A", "score": 1.0}},
}


def _pillars(faction=(0.0, "C"), economy=(3.58, "S")):
    return {"ECONOMY": {"grade": economy[1], "norm": economy[0], "raw": 1.0, "events": 80}, "FACTION": {"grade": faction[1], "norm": faction[0], "raw": 0.0, "events": 0}}


def _pair(key, **kw):
    row = {"key": key, "exit": 0, "pillars": _pillars(**kw), "overall": ["B", 1.0]}
    return {1: {**copy.deepcopy(row), "rep": 1}, 2: {**copy.deepcopy(row), "rep": 2}}


def _rows(**kw):
    return {"w_seed1_200t": _pair("w_seed1_200t", **kw), "w_seed2_200t": _pair("w_seed2_200t", faction=(1.02, "A"))}


def test_the_tool_agrees_with_the_regression_tests_constants():
    assert (ra.SCORE_ABS_FLOOR, ra.SCORE_REL_PCT, ra.GRADE_ORDER) == (gr.SCORE_TOLERANCE_ABS_FLOOR, gr.SCORE_TOLERANCE_REL_PCT, tuple(gr.GRADE_ORDER))


def test_a_moved_row_takes_the_audit_value_and_an_in_band_row_is_not_moved():
    new, table = ra.reanchor(FIXTURE, _rows())
    assert new["w_seed1_200t"]["FACTION"] == {"grade": "C", "score": 0.0} and new["w_seed1_200t"]["ECONOMY"] == {"grade": "S", "score": 3.58}
    by = {(r["run_key"], r["pillar"]): r for r in table}
    assert by[("w_seed1_200t", "FACTION")]["moved"] and not by[("w_seed1_200t", "FACTION")]["in_band_before"] and by[("w_seed1_200t", "FACTION")]["in_band_after"]
    assert not by[("w_seed2_200t", "FACTION")]["moved"] and new["_note"] == "meta"  # 1.0 -> 1.02 is inside max(0.05, 20%)
    assert new["w_seed2_200t"]["FACTION"] == {"grade": "A", "score": 1.02}  # an in-band row still takes the audit value (policy: one measured value per row)


def test_an_excluded_row_keeps_its_committed_anchor_and_stays_out_of_band():
    new, table = ra.reanchor(FIXTURE, _rows(), excluded={("w_seed1_200t", "FACTION")})
    assert new["w_seed1_200t"]["FACTION"] == {"grade": "S", "score": 2.9} and new["w_seed1_200t"]["ECONOMY"]["grade"] == "S"
    row = next(r for r in table if (r["run_key"], r["pillar"]) == ("w_seed1_200t", "FACTION"))
    assert row["excluded"] and row["moved"] and not row["in_band_after"]


def test_a_non_identical_pair_a_missing_key_and_an_incomplete_run_refuse():
    rows = _rows()
    rows["w_seed2_200t"][2]["pillars"]["FACTION"]["events"] = 3
    with pytest.raises(ra.ReanchorRefused, match=r"w_seed2_200t.*NOT identical.*FACTION"):
        ra.reanchor(FIXTURE, rows)
    with pytest.raises(ra.ReanchorRefused, match="needs 2 isolated"):
        ra.reanchor(FIXTURE, {"w_seed1_200t": _pair("w_seed1_200t")})
    bad = _rows()
    bad["w_seed1_200t"][1]["exit"] = 1
    with pytest.raises(ra.ReanchorRefused, match="did not complete"):
        ra.reanchor(FIXTURE, bad)
    with pytest.raises(ra.ReanchorRefused, match="not in the fixture"):
        ra.reanchor(FIXTURE, _rows(), excluded={("nope", "FACTION")})


def test_the_committed_fixture_round_trips_byte_exact_and_the_cli_writes_files(tmp_path, monkeypatch):
    real = gr.FIXTURE_PATH
    assert ra.dump_fixture(json.loads(real.read_text())) == real.read_text()  # the layout the tool writes is the committed one
    fixture = tmp_path / "f.json"
    fixture.write_text(ra.dump_fixture(FIXTURE))
    rows = tmp_path / "rows.jsonl"
    rows.write_text("".join(json.dumps(r) + "\n" for pair in _rows().values() for r in pair.values()))
    exclude = tmp_path / "x.tsv"
    exclude.write_text("# rpg ruled this a regression\nw_seed1_200t\tFACTION\n")
    out, table = tmp_path / "new.json", tmp_path / "t.tsv"
    monkeypatch.chdir(gr.FIXTURE_PATH.parents[3])
    assert ra.main(["--rows", str(rows), "--fixture", str(fixture), "--out", str(out), "--table", str(table), "--exclude", str(exclude)]) == 0
    assert json.loads(out.read_text())["w_seed1_200t"]["FACTION"]["grade"] == "S" and "excluded" in table.read_text().splitlines()[0]

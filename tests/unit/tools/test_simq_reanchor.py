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


def test_a_prior_measurement_adds_the_three_column_comparison_and_flags_what_changed_since_the_ruling():
    prior = _rows()  # FACTION (0.0, C) and ECONOMY (3.58, S) for w_seed1; FACTION (1.02, A) for w_seed2
    now = _rows(faction=(0.0, "C"), economy=(3.0, "A"))
    new, table = ra.reanchor(FIXTURE, now, prior_rows=prior)
    by = {(r["run_key"], r["pillar"]): r for r in table}
    eco = by[("w_seed1_200t", "ECONOMY")]
    assert (eco["prior_grade"], eco["prior_score"], eco["audit_grade"], eco["audit_score"]) == ("S", 3.58, "A", 3.0)
    assert eco["grade_changed"] and eco["changed_since_ruling"]
    fac = by[("w_seed1_200t", "FACTION")]
    assert not fac["grade_changed"] and not fac["changed_since_ruling"]
    text = ra.table_tsv(table)
    assert text.splitlines()[0].split("\t")[4:6] == ["prior_grade", "prior_score"] and "changed_since_ruling" in text.splitlines()[0]
    plain = ra.table_tsv(ra.reanchor(FIXTURE, now)[1])
    assert "prior_grade" not in plain


def test_a_prior_measurement_that_is_not_an_identical_pair_refuses():
    bad = _rows()
    bad["w_seed1_200t"][2]["pillars"]["FACTION"]["norm"] = 0.5
    with pytest.raises(ra.ReanchorRefused, match="NOT identical"):
        ra.reanchor(FIXTURE, _rows(), prior_rows=bad)


def test_the_ruling_table_groups_rows_by_value_comparison_only():
    fixture = {"w_seed1_200t": {"FACTION": {"grade": "S", "score": 2.9}, "ECONOMY": {"grade": "B", "score": 0.18}}, "w_seed2_200t": {"FACTION": {"grade": "C", "score": 0.0}}}
    prior = _rows()  # w_seed1: FACTION C/0.0, ECONOMY S/3.58; w_seed2: FACTION A/1.02
    now = {"w_seed1_200t": _pair("w_seed1_200t", faction=(0.0, "C"), economy=(3.0, "A")), "w_seed2_200t": _pair("w_seed2_200t", faction=(1.02, "A"))}
    _, table = ra.reanchor(fixture, now, prior_rows=prior)
    rows = {(r["run_key"], r["pillar"]): r for r in ra.ruling_rows(table)}
    assert rows[("w_seed1_200t", "ECONOMY")]["group"] == ra.GROUP_CHANGED and rows[("w_seed1_200t", "ECONOMY")]["direction"] == "down"
    assert (rows[("w_seed1_200t", "ECONOMY")]["pre_536"], rows[("w_seed1_200t", "ECONOMY")]["post_536"]) == ("S/3.58", "A/3")
    assert rows[("w_seed1_200t", "FACTION")]["group"] == ra.GROUP_UNCHANGED  # same as ruled, differs from committed: a FACTION row by value, not by name
    assert rows[("w_seed2_200t", "FACTION")]["group"] == ra.GROUP_UNCHANGED and rows[("w_seed2_200t", "FACTION")]["direction"] == "up"
    equal = ra.ruling_rows(ra.reanchor({"w_seed1_200t": {"FACTION": {"grade": "C", "score": 0.0}}}, {"w_seed1_200t": _pair("w_seed1_200t")}, prior_rows={"w_seed1_200t": _pair("w_seed1_200t")})[1])
    assert equal == []
    assert ra.ruling_tsv(rows.values()).splitlines()[0] == "run_key\tpillar\tcommitted\tpre_536\tpost_536\tdirection\tgroup"


def test_the_ruling_table_cli_needs_the_prior_rows(tmp_path):
    with pytest.raises(SystemExit):
        ra.main(["--rows", "x", "--fixture", "y", "--out", "z", "--table", "t", "--ruling-table", str(tmp_path / "r.tsv")])

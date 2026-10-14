"""TCK-20261013-SIMQ-NO-DATA-PILLAR-IN-GRADE-REGRESSION: the pillar reading and the four-way comparison, on synthetic pillars (AC1-AC3, AC5, AC6)."""

import pytest

from tools.test_architecture import simq_pillar_compare as spc
from tools.test_architecture.simq_pillar_compare import (
    PillarContractError as Bad, compare_pillar, compare_report, no_data_sets_equal, parse_anchor, parse_overall, parse_report_pillar, parse_row_pillar,
)

OK_ANCHOR = {"grade": "B", "score": 1.0}
ND_ANCHOR = {"status": "no-data", "reason": "below_min_events", "min_events": 3}
OK_LIVE = {"grade": "B", "normalized_score": 1.0, "event_count": 9}
ND_LIVE = {"status": "no-data", "grade": None, "normalized_score": None, "event_count": 1, "min_events": 3, "reason": "below_min_events"}


def _cmp(anchor, live, **kw):
    return compare_pillar("X", parse_anchor("X", anchor), None if live is None else parse_report_pillar("X", live), **kw)


def test_constants_agree_with_the_regression_tests():
    from tests.simulation_quality import test_grade_regression as tgr

    assert spc.GRADE_ORDER == tuple(tgr.GRADE_ORDER)
    assert (spc.SCORE_ABS_FLOOR, spc.SCORE_REL_PCT) == (tgr.SCORE_TOLERANCE_ABS_FLOOR, tgr.SCORE_TOLERANCE_REL_PCT)


# AC6: a report from before the status field
def test_a_pillar_without_status_is_ok_only_with_a_letter_and_a_number():
    p = parse_report_pillar("X", {"grade": "S", "normalized_score": 2.5, "raw_score": 9})
    assert (p.status, p.grade, p.score) == ("ok", "S", 2.5)
    for bad in ({}, {"grade": "C"}, {"normalized_score": 1.0}, {"grade": "Z", "normalized_score": 1.0}, {"grade": "C", "normalized_score": "1"},
                {"grade": "C", "normalized_score": True}, {"grade": None, "normalized_score": None}, None, "C"):
        with pytest.raises(Bad):
            parse_report_pillar("X", bad)


def test_explicit_ok_and_unknown_status():
    assert parse_report_pillar("X", {"status": "ok", "grade": "A", "normalized_score": 0.0}).grade == "A"
    with pytest.raises(Bad, match="unknown status"):
        parse_report_pillar("X", {"status": "maybe", "grade": "A", "normalized_score": 1.0})


# AC2: both malformed shapes are contract failures
def test_no_data_pillar_with_a_grade_or_score_is_a_contract_failure():
    for bad in ({**ND_LIVE, "grade": "C"}, {**ND_LIVE, "normalized_score": 0.0}, {**ND_LIVE, "min_events": None}, {**ND_LIVE, "min_events": 0}):
        with pytest.raises(Bad):
            parse_report_pillar("X", bad)


def test_ok_pillar_with_a_null_grade_or_score_is_a_contract_failure():
    for bad in ({"status": "ok", "grade": None, "normalized_score": 1.0}, {"status": "ok", "grade": "B", "normalized_score": None}):
        with pytest.raises(Bad):
            parse_report_pillar("X", bad)


# AC2: the four cells
def test_ok_ok_is_the_band_and_score_check_unchanged():
    assert _cmp(OK_ANCHOR, OK_LIVE).ok
    assert _cmp(OK_ANCHOR, {**OK_LIVE, "grade": "A"}).ok  # +1 band
    v = _cmp(OK_ANCHOR, {**OK_LIVE, "grade": "S"})
    assert (v.ok, v.code) == (False, spc.BAND) and "outside" in v.message
    v = _cmp(OK_ANCHOR, {**OK_LIVE, "normalized_score": 1.5})
    assert (v.ok, v.code) == (False, spc.SCORE)
    assert _cmp(OK_ANCHOR, {**OK_LIVE, "normalized_score": 1.04}).ok  # inside the 0.05 floor / 20%
    assert _cmp({"grade": "B", "score": 1.0}, {**OK_LIVE, "grade": "S"}, band=2).ok  # a per-row override widens the band only when passed


def test_no_data_no_data_passes_only_with_the_same_min_events():
    v = _cmp(ND_ANCHOR, ND_LIVE)
    assert (v.ok, v.code) == (True, spc.STILL_NO_DATA) and "still no-data" in v.message
    v = _cmp(ND_ANCHOR, {**ND_LIVE, "min_events": 5})
    assert (v.ok, v.code) == (False, spc.THRESHOLD_CHANGED) and "threshold changed" in v.message and "re-anchor under a ruling" in v.message


def test_anchor_ok_live_no_data_is_lost_data():
    v = _cmp(OK_ANCHOR, ND_LIVE)
    assert (v.ok, v.code) == (False, spc.LOST_DATA) and "lost its data" in v.message


def test_anchor_no_data_live_ok_is_gained_data():
    v = _cmp(ND_ANCHOR, OK_LIVE)
    assert (v.ok, v.code) == (False, spc.GAINED_DATA) and "gained data" in v.message and "re-anchor under a ruling" in v.message


# AC1: a missing pillar fails and names itself; nothing defaults it
def test_a_pillar_missing_from_the_report_fails_naming_it():
    v = _cmp(OK_ANCHOR, None)
    assert (v.ok, v.code) == (False, spc.MISSING) and v.message.startswith("X:")
    verdicts, _ = compare_report("k", {"COMBAT": OK_ANCHOR, "FACTION": ND_ANCHOR}, {"pillars": {"COMBAT": OK_LIVE}})
    assert [v.code for v in verdicts] == [spc.PASS, spc.MISSING] and "FACTION" in verdicts[1].message


def test_a_missing_pillar_that_would_have_read_as_c_no_longer_passes():
    verdicts, _ = compare_report("k", {"COMBAT": {"grade": "C", "score": 0.0}}, {"pillars": {}})
    assert [v.ok for v in verdicts] == [False]


def test_compare_report_turns_malformed_pillars_into_contract_verdicts_and_lists_no_data():
    report = {"pillars": {"A": OK_LIVE, "B": ND_LIVE, "C": {**ND_LIVE, "grade": "C"}, "D": {"grade": "B"}}}
    anchors = {"A": OK_ANCHOR, "B": ND_ANCHOR, "C": ND_ANCHOR, "D": OK_ANCHOR, "E": {"grade": "B"}}
    verdicts, sets = compare_report("k", anchors, report)
    assert [v.code for v in verdicts] == [spc.PASS, spc.STILL_NO_DATA, spc.CONTRACT, spc.CONTRACT, spc.CONTRACT]
    assert sets == {"anchor_no_data": ["B", "C"], "live_no_data": ["B"]}
    assert not compare_report("k", anchors, {})[0][0].ok  # no pillars object at all


# AC5: the anchor shapes
def test_anchor_shapes_accept_two_and_reject_everything_else():
    assert parse_anchor("X", OK_ANCHOR).status == "ok"
    assert parse_anchor("X", {"status": "ok", "grade": "A", "score": 2.0}).grade == "A"
    assert parse_anchor("X", ND_ANCHOR).min_events == 3
    for bad in (
        {**ND_ANCHOR, "grade": "C"}, {**ND_ANCHOR, "score": 0.0}, {**ND_ANCHOR, "grade": None}, {"status": "no-data", "min_events": 3},
        {**ND_ANCHOR, "reason": "other"}, {**ND_ANCHOR, "min_events": 0}, {"grade": "B"}, {"grade": "B", "score": 1.0, "extra": 1},
        {"status": "maybe", "grade": "B", "score": 1.0}, {"grade": "Z", "score": 1.0}, {"grade": "B", "score": "1"}, [], None,
    ):
        with pytest.raises(Bad):
            parse_anchor("X", bad)


# AC3: the overall
def test_overall_is_comparable_only_on_equal_no_data_sets():
    ok, nd = parse_anchor("o", OK_ANCHOR), parse_anchor("o", ND_ANCHOR)
    assert no_data_sets_equal({"A": ok, "B": nd}, {"A": ok, "B": nd})
    assert not no_data_sets_equal({"A": ok, "B": nd}, {"A": ok, "B": ok})
    assert not no_data_sets_equal({"A": ok, "B": ok}, {"A": nd, "B": ok})
    assert no_data_sets_equal({}, {})


def test_overall_no_data_follows_the_four_way_rule():
    live_nd = {"status": "no-data", "grade": None, "score": None, "reason": "too_few_pillars_scored", "min_events": 3}
    anchor_ok, anchor_nd = parse_overall(OK_ANCHOR, anchor=True), parse_overall(ND_ANCHOR, anchor=True)
    assert compare_pillar("overall", anchor_nd, parse_overall(live_nd)).code == spc.STILL_NO_DATA
    assert compare_pillar("overall", anchor_ok, parse_overall(live_nd)).code == spc.LOST_DATA
    assert compare_pillar("overall", anchor_nd, parse_overall({"grade": "B", "score": 1.0})).code == spc.GAINED_DATA
    assert compare_pillar("overall", anchor_ok, parse_overall({"grade": "B", "score": 1.0})).ok


def test_row_pillars_use_norm_and_labels():
    assert parse_row_pillar("X", {"grade": "B", "norm": 1.5, "raw": 3, "events": 4}).score == 1.5
    assert parse_row_pillar("X", {"status": "no-data", "grade": None, "norm": None, "events": 1, "min_events": 3}).status == "no-data"
    assert spc.grade_label("X", OK_LIVE) == "B" and spc.grade_label("X", ND_LIVE) == "no-data"
    assert spc.anchor_grade_label("X", ND_ANCHOR) == "no-data" and spc.anchor_grade_label("X", OK_ANCHOR) == "B"
    with pytest.raises(Bad):
        spc.grade_label("X", {})


def test_the_committed_fixture_is_all_ok_anchors_today():
    import json
    from pathlib import Path

    fixture = json.loads((Path(__file__).resolve().parents[2] / "simulation_quality" / "fixtures" / "grade_anchors.json").read_text(encoding="utf-8"))
    for run_key, pillars in fixture.items():
        if not run_key.startswith("_"):
            assert all(parse_anchor(f"{run_key}/{p}", a).status == "ok" for p, a in pillars.items())

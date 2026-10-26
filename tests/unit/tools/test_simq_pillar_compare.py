"""TCK-20261013-SIMQ-NO-DATA-PILLAR-IN-GRADE-REGRESSION: the pillar reading and the four-way comparison, on synthetic pillars (AC1-AC3, AC5, AC6)."""

import pytest

from tools.test_architecture import simq_pillar_compare as spc
from tools.test_architecture.simq_pillar_compare import (
    HostIndependenceRefused, PillarContractError as Bad, compare_pillar, compare_report, no_data_sets_equal, parse_anchor, parse_report_overall, parse_report_pillar, parse_row_pillar,
)

OK_ANCHOR = {"grade": "B", "score": 1.0}
ND_ANCHOR = {"status": "no-data", "reason": "below_min_events", "min_events": 3}
OK_LIVE = {"grade": "B", "normalized_score": 1.0, "event_count": 9}
ND_LIVE = {"status": "no-data", "grade": None, "normalized_score": None, "event_count": 1, "min_events": 3, "reason": "below_min_events"}


AUDIT_MANIFEST = {"run_id": "r", "audit_mode": True, "signals_zeroed": True}


def _report(run_key, anchors, report, **kw):
    """compare_report on a host-independent live run (the host-independence refusal has its own tests below)."""
    return compare_report(run_key, anchors, report, live_manifest=AUDIT_MANIFEST, **kw)


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
    verdicts, _ = _report("k", {"COMBAT": OK_ANCHOR, "FACTION": ND_ANCHOR}, {"pillars": {"COMBAT": OK_LIVE}})
    assert [v.code for v in verdicts] == [spc.PASS, spc.MISSING] and "FACTION" in verdicts[1].message


def test_a_missing_pillar_that_would_have_read_as_c_no_longer_passes():
    verdicts, _ = _report("k", {"COMBAT": {"grade": "C", "score": 0.0}}, {"pillars": {}})
    assert [v.ok for v in verdicts] == [False]


def test_compare_report_turns_malformed_pillars_into_contract_verdicts_and_lists_no_data():
    report = {"pillars": {"A": OK_LIVE, "B": ND_LIVE, "C": {**ND_LIVE, "grade": "C"}, "D": {"grade": "B"}}}
    anchors = {"A": OK_ANCHOR, "B": ND_ANCHOR, "C": ND_ANCHOR, "D": OK_ANCHOR, "E": {"grade": "B"}}
    verdicts, sets = _report("k", anchors, report)
    assert [v.code for v in verdicts] == [spc.PASS, spc.STILL_NO_DATA, spc.CONTRACT, spc.CONTRACT, spc.CONTRACT]
    assert sets == {"anchor_no_data": ["B", "C"], "live_no_data": ["B"]}
    assert not _report("k", anchors, {})[0][0].ok  # no pillars object at all


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


def test_overall_is_read_from_the_flat_report_keys():
    ok = parse_report_overall({"overall_grade": "B", "overall_score": 1.2})  # no overall_status: a report from before the field (AC6)
    assert (ok.status, ok.grade, ok.score) == ("ok", "B", 1.2)
    assert parse_report_overall({"overall_status": "ok", "overall_grade": "S", "overall_score": 0.0}).grade == "S"
    nd = parse_report_overall({"overall_status": "no-data", "overall_grade": None, "overall_score": None, "overall_reason": "too_few_pillars_scored"})
    assert (nd.status, nd.grade, nd.score, nd.min_events) == ("no-data", None, None, None)  # no min_events on an overall
    for bad in ({}, {"overall_grade": "B"}, {"overall_score": 1.0}, {"overall_grade": "Z", "overall_score": 1.0}, {"overall_status": "maybe", "overall_grade": "B", "overall_score": 1.0},
                {"overall_status": "no-data", "overall_grade": "B", "overall_score": None, "overall_reason": "too_few_pillars_scored"},
                {"overall_status": "no-data", "overall_grade": None, "overall_score": 0.0, "overall_reason": "too_few_pillars_scored"},
                {"overall_status": "no-data", "overall_grade": None, "overall_score": None, "overall_reason": "other"},
                {"overall_status": "no-data", "overall_grade": None, "overall_score": None}, None):
        with pytest.raises(Bad):
            parse_report_overall(bad)


def test_overall_counts_must_match_the_pillars_statuses():
    pillars = {"A": OK_LIVE, "B": ND_LIVE, "C": ND_LIVE}
    base = {"overall_grade": "B", "overall_score": 1.0, "pillars": pillars}
    assert parse_report_overall({**base, "pillars_scored": 1, "pillars_no_data": 2}).status == "ok"
    assert parse_report_overall(base).status == "ok"  # counts absent: nothing to check
    for bad in ({"pillars_no_data": 1}, {"pillars_scored": 2}, {"pillars_scored": 1, "pillars_no_data": 0}):
        with pytest.raises(Bad, match="pillars give"):
            parse_report_overall({**base, **bad})


def test_overall_no_data_follows_the_four_way_rule():
    ok_overall = parse_report_overall({"overall_grade": "B", "overall_score": 1.0})
    nd_overall = parse_report_overall({"overall_status": "no-data", "overall_grade": None, "overall_score": None, "overall_reason": "too_few_pillars_scored"})
    assert compare_pillar("overall", nd_overall, nd_overall).code == spc.STILL_NO_DATA
    assert compare_pillar("overall", ok_overall, nd_overall).code == spc.LOST_DATA
    assert compare_pillar("overall", nd_overall, ok_overall).code == spc.GAINED_DATA
    assert compare_pillar("overall", ok_overall, ok_overall).ok


def test_row_pillars_use_norm_and_labels():
    assert parse_row_pillar("X", {"grade": "B", "norm": 1.5, "raw": 3, "events": 4}).score == 1.5
    assert parse_row_pillar("X", {"status": "no-data", "grade": None, "norm": None, "events": 1, "min_events": 3}).status == "no-data"
    assert spc.grade_label("X", OK_LIVE) == "B" and spc.grade_label("X", ND_LIVE) == "no-data"
    assert spc.anchor_grade_label("X", ND_ANCHOR) == "no-data" and spc.anchor_grade_label("X", OK_ANCHOR) == "B"
    with pytest.raises(Bad):
        spc.grade_label("X", {})


def test_every_committed_anchor_is_a_well_formed_ok_or_no_data_anchor():
    import json
    from pathlib import Path

    fixture = json.loads((Path(__file__).resolve().parents[2] / "simulation_quality" / "fixtures" / "grade_anchors.json").read_text(encoding="utf-8"))
    for run_key, pillars in fixture.items():
        if not run_key.startswith("_"):
            for p, a in pillars.items():
                anchor = parse_anchor(f"{run_key}/{p}", a)  # strict: one of the two shapes
                assert anchor.status in ("ok", "no-data")
                if anchor.status == "no-data":
                    assert a.get("reason") == "below_min_events" and isinstance(a.get("min_events"), int)  # the only no-data anchor reason today (baseline v1 re-anchor)


def test_a_verdict_names_its_pillar_without_parsing_the_message():
    verdicts, _ = _report("k", {"A": OK_ANCHOR, "B": ND_ANCHOR, "C": OK_ANCHOR, "D": OK_ANCHOR},
                                 {"pillars": {"A": {**OK_LIVE, "normalized_score": 9.0}, "B": OK_LIVE, "D": {"grade": "B"}}})
    assert {v.pillar: v.code for v in verdicts} == {"A": spc.SCORE, "B": spc.GAINED_DATA, "C": spc.MISSING, "D": spc.CONTRACT}


def test_a_no_data_pillar_whose_event_count_reaches_min_events_contradicts_itself():
    with pytest.raises(Bad, match="contradicts itself"):
        parse_report_pillar("X", {**ND_LIVE, "event_count": 3})
    with pytest.raises(Bad, match="contradicts itself"):
        parse_row_pillar("X", {"status": "no-data", "grade": None, "norm": None, "events": 7, "min_events": 3})
    assert parse_report_pillar("X", {**ND_LIVE, "event_count": 2}).status == "no-data"
    assert parse_report_pillar("X", {k: v for k, v in ND_LIVE.items() if k != "event_count"}).status == "no-data"  # no count to contradict


# TCK-20261014-SIMQ-COMPARE-TOOLS-REFUSE-RUNS-NOT-RECORDED-HOST-INDEPENDENT (AC3): the live side must be recorded host-independent; the anchor side is covered by simq_reanchor.
_LIVE_RUN = {"pillars": {"COMBAT": OK_LIVE}}


def test_compare_report_accepts_a_live_run_recorded_host_independent():
    verdicts, _ = compare_report("k", {"COMBAT": OK_ANCHOR}, _LIVE_RUN, live_manifest={"audit_mode": True, "signals_zeroed": True})
    assert [v.ok for v in verdicts] == [True]


def test_compare_report_accepts_a_pinned_governor_run_for_the_live_side():
    verdicts, _ = compare_report("k", {"COMBAT": OK_ANCHOR}, _LIVE_RUN, live_manifest={"audit_mode": False, "signals_zeroed": True})
    assert [v.ok for v in verdicts] == [True]


@pytest.mark.parametrize(
    "manifest",
    [
        {"audit_mode": False, "signals_zeroed": False},  # a live run
        {"run_id": "r"},  # an older manifest with no field
        {"audit_mode": None, "signals_zeroed": None},  # a sidecar with nulls
        {"audit_mode": True, "signals_zeroed": "yes"},  # not a boolean
        {},
        None,  # no manifest to hand: a refusal, not a skip
    ],
)
def test_compare_report_refuses_a_live_run_not_recorded_host_independent(manifest):
    with pytest.raises(HostIndependenceRefused, match="re-run it under audit_mode") as caught:
        compare_report("k", {"COMBAT": OK_ANCHOR}, _LIVE_RUN, live_manifest=manifest)
    assert "k:" in str(caught.value) and caught.value.__cause__ is not None  # names the run; keeps rpg's NonAuditRunError as the cause


def test_compare_report_has_no_default_for_the_live_manifest():
    with pytest.raises(TypeError):
        compare_report("k", {"COMBAT": OK_ANCHOR}, _LIVE_RUN)  # type: ignore[call-arg]

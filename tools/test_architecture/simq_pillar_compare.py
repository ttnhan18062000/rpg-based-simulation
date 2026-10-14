"""One reading of a SimQ pillar (report, anchor or proof row) and one comparison of an anchor against a live pillar.

TCK-20261013-SIMQ-NO-DATA-PILLAR-IN-GRADE-REGRESSION. The grade regression tests, the corpus-diversity guards, ``simq_reanchor`` and ``evaluate_simq`` all read pillars
through this module, so the status handling cannot drift between them.

A pillar has a status: ``ok`` (a grade and a score) or ``no-data`` (fewer than ``min_events`` events: no grade, no score). Three shapes read into :class:`Pillar`:

* a live report pillar ``{"status"?, "grade", "normalized_score", "event_count"?, "min_events"?}``  (:func:`parse_report_pillar`)
* a committed anchor ``{"grade", "score"}`` / ``{"status": "ok", "grade", "score"}`` / ``{"status": "no-data", "reason": "below_min_events", "min_events": k}``  (:func:`parse_anchor`)
* a re-anchor proof row ``{"grade", "norm", ...}`` plus the same status fields  (:func:`parse_row_pillar`)

A pillar with no ``status`` field (every report before rpg's scorer change) is ``ok`` only when its grade is a letter and its score a number. Anything else is a
:class:`PillarContractError`; there is no default, so a missing or malformed pillar is never read as a grade.

:func:`compare_pillar` is the four-way verdict (anchor ok/no-data against live ok/no-data); :func:`no_data_sets_equal` is the overall's comparability rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

GRADE_ORDER = ("F", "D", "C", "B", "A", "S")
SCORE_ABS_FLOOR, SCORE_REL_PCT = 0.05, 0.20  # mirrors test_grade_regression; a test pins that they agree

OK, NO_DATA = "ok", "no-data"
BELOW_MIN_EVENTS = "below_min_events"

ANCHOR_OK_KEYS = ({"grade", "score"}, {"status", "grade", "score"})
ANCHOR_NO_DATA_KEYS = {"status", "reason", "min_events"}

# verdict codes
PASS, STILL_NO_DATA = "pass", "still-no-data"
BAND, SCORE = "band", "score"
MISSING, LOST_DATA, GAINED_DATA, THRESHOLD_CHANGED, CONTRACT = "missing", "lost-data", "gained-data", "threshold-changed", "contract"


class PillarContractError(ValueError):
    """A pillar (report, anchor or row) is malformed; the message names what is wrong."""


@dataclass(frozen=True)
class Pillar:
    status: str  # OK or NO_DATA
    grade: Optional[str] = None
    score: Optional[float] = None
    min_events: Optional[int] = None


@dataclass(frozen=True)
class Verdict:
    ok: bool
    code: str
    message: str


def within_band(actual: str, anchor: str, tolerance: int = 1) -> bool:
    return actual in GRADE_ORDER and anchor in GRADE_ORDER and abs(GRADE_ORDER.index(actual) - GRADE_ORDER.index(anchor)) <= tolerance


def within_score(actual: float, anchor: float, abs_floor: float = SCORE_ABS_FLOOR, rel_pct: float = SCORE_REL_PCT) -> bool:
    return abs(actual - anchor) <= max(abs_floor, rel_pct * abs(anchor))


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _parse(name: str, data: Any, score_key: str) -> Pillar:
    if not isinstance(data, Mapping):
        raise PillarContractError(f"{name}: expected a pillar object, got {data!r}")
    status = data.get("status")
    grade, score = data.get("grade"), data.get(score_key)
    if status in (None, OK):
        if grade not in GRADE_ORDER:
            raise PillarContractError(f"{name}: status {status or '(absent)'!s} needs a grade in {list(GRADE_ORDER)}, got {grade!r}")
        if not _number(score):
            raise PillarContractError(f"{name}: status {status or '(absent)'!s} needs a numeric {score_key}, got {score!r}")
        return Pillar(OK, grade, float(score))
    if status == NO_DATA:
        if grade is not None or score is not None:
            raise PillarContractError(f"{name}: status no-data must carry no grade or score, got grade={grade!r} {score_key}={score!r}")
        min_events = data.get("min_events")
        if isinstance(min_events, bool) or not isinstance(min_events, int) or min_events < 1:
            raise PillarContractError(f"{name}: status no-data needs an integer min_events >= 1, got {min_events!r}")
        return Pillar(NO_DATA, None, None, min_events)
    raise PillarContractError(f"{name}: unknown status {status!r} (expected 'ok' or 'no-data')")


def parse_report_pillar(name: str, data: Any) -> Pillar:
    """A pillar of ``quality_report.json`` (score key ``normalized_score``)."""
    return _parse(name, data, "normalized_score")


def parse_row_pillar(name: str, data: Any) -> Pillar:
    """A pillar of a re-anchor proof row (score key ``norm``)."""
    return _parse(name, data, "norm")


def parse_anchor(name: str, data: Any) -> Pillar:
    """A committed anchor, strictly: exactly one of the two shapes, no other keys (so a no-data anchor can not carry a grade)."""
    if not isinstance(data, Mapping):
        raise PillarContractError(f"{name}: expected an anchor object, got {data!r}")
    keys = set(data)
    if data.get("status") == NO_DATA:
        if keys != ANCHOR_NO_DATA_KEYS or data.get("reason") != BELOW_MIN_EVENTS:
            raise PillarContractError(
                f"{name}: a no-data anchor is exactly {{status: no-data, reason: {BELOW_MIN_EVENTS}, min_events: k}}, got {dict(data)!r}"
            )
    elif keys not in ANCHOR_OK_KEYS or ("status" in data and data["status"] != OK):
        raise PillarContractError(f"{name}: an ok anchor is exactly {{grade, score}} (status 'ok' optional), got {dict(data)!r}")
    return _parse(name, data, "score")


def parse_overall(data: Any, *, anchor: bool = False) -> Pillar:
    """An overall (``{"status"?, "grade", "score", ...}``); the overall's own no-data follows the same four-way rule."""
    return parse_anchor("overall", data) if anchor else _parse("overall", data, "score")


def compare_pillar(
    name: str, anchor: Pillar, live: Optional[Pillar], *, band: int = 1, abs_floor: float = SCORE_ABS_FLOOR, check_score: bool = True,
) -> Verdict:
    """The four-way verdict of one pillar. ``live`` is None when the report has no such pillar (a failure naming it).

    ``check_score=False`` leaves the score tolerance to the caller (a guard that averages trials), for the ok/ok cell only; the other cells are unchanged."""
    if live is None:
        return Verdict(False, MISSING, f"{name}: pillar missing from the report")
    if anchor.status == OK and live.status == OK:
        if not within_band(live.grade, anchor.grade, band):
            return Verdict(False, BAND, f"{name}: actual={live.grade!r} is outside ±{band} band of anchor={anchor.grade!r}")
        if check_score and not within_score(live.score, anchor.score, abs_floor):
            return Verdict(False, SCORE, f"{name}: actual_score={live.score!r} outside tolerance of anchor_score={anchor.score!r}")
        return Verdict(True, PASS, f"{name}: ok")
    if anchor.status == NO_DATA and live.status == NO_DATA:
        if anchor.min_events != live.min_events:
            return Verdict(False, THRESHOLD_CHANGED,
                           f"{name}: threshold changed (min_events anchor={anchor.min_events} live={live.min_events}): re-anchor under a ruling")
        return Verdict(True, STILL_NO_DATA, f"{name}: still no-data (min_events={live.min_events})")
    if anchor.status == OK:
        return Verdict(False, LOST_DATA, f"{name}: pillar lost its data (anchor={anchor.grade!r}, live has fewer than min_events={live.min_events} events)")
    return Verdict(False, GAINED_DATA, f"{name}: pillar gained data (anchor is no-data, live={live.grade!r}): re-anchor under a ruling")


def no_data_pillars(pillars: Mapping[str, Pillar]) -> list[str]:
    return sorted(name for name, p in pillars.items() if p.status == NO_DATA)


def no_data_sets_equal(anchor: Mapping[str, Pillar], live: Mapping[str, Pillar]) -> bool:
    """The overall is comparable only when the anchor's and the live report's no-data pillar sets are equal."""
    return no_data_pillars(anchor) == no_data_pillars(live)


def compare_report(
    run_key: str, anchors: Mapping[str, Any], report: Mapping[str, Any], *,
    band_overrides: Optional[Mapping[tuple, int]] = None, floor_overrides: Optional[Mapping[tuple, float]] = None,
) -> tuple[list[Verdict], dict[str, list[str]]]:
    """Every anchored pillar of ``run_key`` against ``report`` -> ``(verdicts, {"anchor_no_data": [...], "live_no_data": [...]})``.

    A malformed anchor or live pillar is a contract verdict, not an exception. ``report["pillars"]`` is read without any default per pillar."""
    band_overrides, floor_overrides = band_overrides or {}, floor_overrides or {}
    live_raw = report.get("pillars")
    verdicts: list[Verdict] = []
    anchor_parsed: dict[str, Pillar] = {}
    live_parsed: dict[str, Pillar] = {}
    if not isinstance(live_raw, Mapping):
        return [Verdict(False, CONTRACT, f"{run_key}: the report has no pillars object")], {"anchor_no_data": [], "live_no_data": []}
    for pillar, raw in anchors.items():
        label = f"{run_key}/{pillar}"
        try:
            anchor = anchor_parsed[pillar] = parse_anchor(label, raw)
        except PillarContractError as exc:
            verdicts.append(Verdict(False, CONTRACT, f"contract (anchor) {exc}"))
            continue
        live = None
        if pillar in live_raw:
            try:
                live = live_parsed[pillar] = parse_report_pillar(label, live_raw[pillar])
            except PillarContractError as exc:
                verdicts.append(Verdict(False, CONTRACT, f"contract (report) {exc}"))
                continue
        verdicts.append(compare_pillar(
            pillar, anchor, live, band=band_overrides.get((run_key, pillar), 1), abs_floor=floor_overrides.get((run_key, pillar), SCORE_ABS_FLOOR),
        ))
    return verdicts, {"anchor_no_data": no_data_pillars(anchor_parsed), "live_no_data": no_data_pillars(live_parsed)}


def grade_label(name: str, data: Any) -> str:
    """The grade letter of a report pillar, or the literal ``no-data`` (for a one-column grade table); a malformed pillar raises."""
    pillar = parse_report_pillar(name, data)
    return pillar.grade if pillar.status == OK else NO_DATA


def anchor_grade_label(name: str, data: Any) -> str:
    pillar = parse_anchor(name, data)
    return pillar.grade if pillar.status == OK else NO_DATA

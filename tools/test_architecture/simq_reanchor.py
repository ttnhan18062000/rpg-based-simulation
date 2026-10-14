"""Re-anchor ``grade_anchors.json`` from audit_mode proof runs, with an exclusion list and a provenance table.

TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE. The anchors are measured under ``audit_mode`` (a run that does not depend on host speed). Before an
anchor moves, each run key needs TWO isolated runs that are identical on every pillar (grade, normalized score, raw score, event count) and overall; a key whose
pair differs is never re-anchored (it is a determinism finding for rpg, not a value). A ``(run_key, pillar)`` row on the exclusion list keeps its committed
anchor (for example a FACTION=0 that rpg rules a regression the stale anchor had hidden; that row gets an rpg-owned known-red instead).

Input rows (``rows.jsonl``, one per run): ``{"key", "rep", "exit", "pillars": {PILLAR: {"grade", "norm", "raw", "events"}}, "overall": [grade, score]}``, the
shape the proof driver writes. A pillar the scorer reports as no-data is ``{"status": "no-data", "grade": null, "norm": null, "events": n, "min_events": k}``
(TCK-20261013-SIMQ-NO-DATA-PILLAR-IN-GRADE-REGRESSION): it is written as the no-data anchor ``{"status": "no-data", "reason": "below_min_events", "min_events": k}``, a
change of status (ok to no-data or back) is always a moved row, and the pair-identity check compares status and ``min_events`` with everything else. A pillar that is
neither a letter and a number nor a well-formed no-data pillar refuses the re-anchor. Output: the new fixture (same layout as the committed one: ``indent=2`` and a final newline, metadata keys first and untouched,
run keys and pillars in their existing order) and a provenance table with one line per (run_key, pillar)::

    run_key  pillar  committed_grade  committed_score  audit_grade  audit_score  in_band_before  in_band_after  moved  excluded  committed_status  audit_status

``in_band_before`` is the committed anchor's own check applied to the audit value (grade within the band and score within the tolerance, including the
per-(run_key, pillar) overrides in ``test_grade_regression``); ``in_band_after`` is the same check against the new anchor (true unless the row is excluded);
``moved`` is ``not in_band_before`` (the four-way comparison of ``simq_pillar_compare``, so a status change is moved). A no-data pillar has an empty grade and score cell.

CLI::

    python -m tools.test_architecture.simq_reanchor --rows rows.jsonl --fixture grade_anchors.json --out new.json --table table.tsv [--exclude exclude.tsv] [--prior-rows earlier_rows.jsonl]

``exclude.tsv`` has one ``run_key<TAB>pillar`` per line (``#`` comments allowed). Exit 2 when a key is missing, incomplete or not identical (nothing written).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple

from tools.test_architecture.simq_pillar_compare import (  # noqa: E402  (one reading of a pillar and one comparison, shared with the regression tests)
    BELOW_MIN_EVENTS, GRADE_ORDER, NO_DATA, OK, SCORE_ABS_FLOOR, SCORE_REL_PCT, Pillar, PillarContractError, compare_pillar, parse_anchor, parse_row_pillar,
    within_band, within_score,
)


class ReanchorRefused(ValueError):
    """The proof rows can not re-anchor; the message names the run key and the rule."""


def load_rows(path: Path) -> Dict[str, Dict[int, dict]]:
    by_key: Dict[str, Dict[int, dict]] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            by_key.setdefault(row["key"], {})[row["rep"]] = row
    return by_key


def load_exclusions(path: Optional[Path]) -> Set[Tuple[str, str]]:
    if path is None:
        return set()
    out: Set[Tuple[str, str]] = set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            run_key, pillar = line.split("\t")[:2]
            out.add((run_key, pillar))
    return out


def audit_values(run_key: str, runs: Mapping[int, dict]) -> Dict[str, dict]:
    """The pillar values of ``run_key`` when two isolated runs are complete and identical, else :class:`ReanchorRefused`."""
    a, b = runs.get(1), runs.get(2)
    if not a or not b:
        raise ReanchorRefused(f"{run_key}: needs 2 isolated audit_mode runs, has {sorted(runs)}")
    for rep, row in ((1, a), (2, b)):
        if row.get("exit") != 0 or not row.get("pillars"):
            raise ReanchorRefused(f"{run_key}: run {rep} did not complete (exit {row.get('exit')}); no report to anchor on")
    if a["pillars"] != b["pillars"] or a.get("overall") != b.get("overall"):
        differing = sorted(p for p in a["pillars"] if a["pillars"][p] != b["pillars"].get(p))
        raise ReanchorRefused(f"{run_key}: the two audit_mode runs are NOT identical (pillars {differing or 'overall'}); a determinism finding, not an anchor")
    return a["pillars"]


def _row_pillar(run_key: str, pillar: str, data: Mapping[str, Any]) -> Pillar:
    try:
        return parse_row_pillar(f"{run_key}/{pillar}", data)
    except PillarContractError as exc:
        raise ReanchorRefused(f"{run_key}: the audit_mode pillar is neither a graded nor a well-formed no-data pillar: {exc}") from exc


def _anchor_pillar(run_key: str, pillar: str, data: Mapping[str, Any]) -> Pillar:
    try:
        return parse_anchor(f"{run_key}/{pillar}", data)
    except PillarContractError as exc:
        raise ReanchorRefused(f"{run_key}: the committed anchor is malformed: {exc}") from exc


def _new_anchor(actual: Pillar) -> Dict[str, Any]:
    """The anchor an audit value writes: ``{grade, score}`` for an ok pillar, the no-data shape otherwise (never a grade or score on a no-data pillar)."""
    if actual.status == NO_DATA:
        return {"status": NO_DATA, "reason": BELOW_MIN_EVENTS, "min_events": actual.min_events}
    return {"grade": actual.grade, "score": actual.score}


def _identity(p: Pillar) -> tuple:
    return (p.status, p.grade, p.score, p.min_events)


def reanchor(
    fixture: Mapping[str, Any],
    rows: Mapping[str, Mapping[int, dict]],
    excluded: Iterable[Tuple[str, str]] = (),
    score_overrides: Optional[Mapping[Tuple[str, str], float]] = None,
    band_overrides: Optional[Mapping[Tuple[str, str], int]] = None,
    prior_rows: Optional[Mapping[str, Mapping[int, dict]]] = None,
) -> Tuple[Dict[str, Any], List[dict]]:
    """``(new fixture, provenance rows)``. Every run key of the fixture must have an identical pair; excluded rows keep their committed anchor.

    ``prior_rows`` (an earlier measurement, for example the one an owner ruled on before the code moved again) adds ``prior_grade``, ``prior_score``,
    ``grade_changed`` and ``changed_since_ruling`` to every table row, so a value that differs from what was ruled can be put back to the owner (rule 5)."""
    excluded = set(excluded)
    score_overrides, band_overrides = score_overrides or {}, band_overrides or {}
    new: Dict[str, Any] = {}
    table: List[dict] = []
    for run_key, pillars in fixture.items():
        if run_key.startswith("_"):
            new[run_key] = pillars
            continue
        audit = audit_values(run_key, rows.get(run_key, {}))
        prior = audit_values(run_key, prior_rows.get(run_key, {})) if prior_rows is not None else None
        new[run_key] = {}
        for pillar, anchor in pillars.items():
            actual_raw = audit.get(pillar)
            if actual_raw is None:
                raise ReanchorRefused(f"{run_key}: the audit_mode runs have no {pillar} pillar to anchor on")
            actual = _row_pillar(run_key, pillar, actual_raw)
            committed = _anchor_pillar(run_key, pillar, anchor)
            floor = score_overrides.get((run_key, pillar), SCORE_ABS_FLOOR)
            before = compare_pillar(pillar, committed, actual, band=band_overrides.get((run_key, pillar), 1), abs_floor=floor).ok
            skip = (run_key, pillar) in excluded
            new[run_key][pillar] = dict(anchor) if skip else _new_anchor(actual)
            extra = {}
            if prior is not None:
                before_raw = prior.get(pillar)
                if before_raw is None:
                    raise ReanchorRefused(f"{run_key}: the prior measurement has no {pillar} pillar")
                before_value = _row_pillar(run_key, pillar, before_raw)
                extra = {"prior_grade": before_value.grade, "prior_score": before_value.score, "prior_status": before_value.status,
                         "grade_changed": before_value.grade != actual.grade,
                         "changed_since_ruling": _identity(before_value) != _identity(actual)}
            table.append({
                **extra, "run_key": run_key, "pillar": pillar, "committed_grade": committed.grade, "committed_score": committed.score,
                "audit_grade": actual.grade, "audit_score": actual.score, "in_band_before": before,
                "in_band_after": before if skip else True, "moved": not before, "excluded": skip,
                "committed_status": committed.status, "audit_status": actual.status, "committed_min_events": committed.min_events, "audit_min_events": actual.min_events,
            })
    unknown = sorted(f"{k}:{p}" for k, p in excluded if k not in fixture or p not in fixture[k])
    if unknown:
        raise ReanchorRefused(f"exclusion(s) not in the fixture: {unknown}")
    return new, table


def dump_fixture(fixture: Mapping[str, Any]) -> str:
    return json.dumps(fixture, indent=2) + "\n"


def table_tsv(table: Iterable[Mapping[str, Any]]) -> str:
    table = list(table)
    cols = ["run_key", "pillar", "committed_grade", "committed_score"]
    if table and "prior_grade" in table[0]:
        cols += ["prior_grade", "prior_score"]
    cols += ["audit_grade", "audit_score"]
    if table and "prior_grade" in table[0]:
        cols += ["grade_changed", "changed_since_ruling"]
    cols += ["in_band_before", "in_band_after", "moved", "excluded", "committed_status"]
    if table and "prior_grade" in table[0]:
        cols += ["prior_status"]
    cols += ["audit_status"]
    return "\t".join(cols) + "\n" + "".join("\t".join("" if row.get(c) is None else str(row[c]) for c in cols) + "\n" for row in table)


GROUP_CHANGED = "#536, cause not isolated by measurement"
GROUP_UNCHANGED = "unchanged since the 2026-10-12 ruling"
GROUP_HELD = "held as a finding: kept at the committed anchor (excluded)"


def _same_value(a: tuple, b: tuple) -> bool:
    """Whether two ``(status, grade, score, min_events)`` readings are the same value; ``min_events`` counts only when both sides know it."""
    if a[:3] != b[:3]:
        return False
    return a[3] is None or b[3] is None or a[3] == b[3]


def _fmt(v: tuple) -> str:
    return f"no-data(min_events={v[3]})" if v[0] == NO_DATA and v[3] is not None else "no-data" if v[0] == NO_DATA else f"{v[1]}/{v[2]:.4g}"


def ruling_rows(table: Iterable[Mapping[str, Any]]) -> List[dict]:
    """The rows an owner rules on after the code moved again, grouped by value comparison only (never by pillar name or a guessed cause).

    Needs the ``prior_*`` columns (an earlier measurement the owner ruled on). A row whose post value differs from the prior (ruled) value is
    :data:`GROUP_CHANGED` (the code change that moved it is not isolated by measurement); an excluded row (held by the owner as a finding) is :data:`GROUP_HELD`; a row whose post value equals the prior one but differs from the
    committed anchor is :data:`GROUP_UNCHANGED` (already covered by the earlier ruling). A row equal to its committed anchor is not listed."""
    out: List[dict] = []
    for row in table:
        committed = (row.get("committed_status", OK), row["committed_grade"], row["committed_score"], row.get("committed_min_events"))
        before = (row.get("prior_status", OK), row["prior_grade"], row["prior_score"], None)
        after = (row.get("audit_status", OK), row["audit_grade"], row["audit_score"], row.get("audit_min_events"))
        if row.get("excluded"):
            group = GROUP_HELD
        elif not _same_value(before, after):
            group = GROUP_CHANGED
        elif not _same_value(after, committed):
            group = GROUP_UNCHANGED
        else:
            continue
        reference = before if group in (GROUP_CHANGED, GROUP_HELD) else committed
        if reference[0] != after[0]:
            direction = "to-no-data" if after[0] == NO_DATA else "from-no-data"  # a status transition is shown as one, never as a grade step
        else:
            step = GRADE_ORDER.index(after[1]) - GRADE_ORDER.index(reference[1]) if after[1] in GRADE_ORDER and reference[1] in GRADE_ORDER else 0
            direction = "up" if step > 0 or (step == 0 and (after[2] or 0) > (reference[2] or 0)) else "down"
        out.append({"run_key": row["run_key"], "pillar": row["pillar"], "committed": _fmt(committed), "pre_536": _fmt(before),
                    "post_536": _fmt(after), "direction": direction, "group": group})
    order = (GROUP_HELD, GROUP_CHANGED, GROUP_UNCHANGED)
    return sorted(out, key=lambda r: (order.index(r["group"]), r["run_key"], r["pillar"]))


def ruling_tsv(rows: Iterable[Mapping[str, Any]]) -> str:
    cols = ("run_key", "pillar", "committed", "pre_536", "post_536", "direction", "group")
    return "\t".join(cols) + "\n" + "".join("\t".join(str(r[c]) for c in cols) + "\n" for r in rows)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--table", type=Path, required=True)
    parser.add_argument("--exclude", type=Path)
    parser.add_argument("--prior-rows", type=Path, help="rows.jsonl of an earlier measurement (the one an owner ruled on); adds the prior columns and the changed-since-ruling flags")
    parser.add_argument("--score-overrides", type=Path, help="JSON [[run_key, pillar, abs_floor], ...]: the COMMITTED per-row tolerance widenings, so in_band_before is judged the way the committed anchor was")
    parser.add_argument("--ruling-table", type=Path, help="write the table for the owner's ruling (needs --prior-rows): the rows the owner rules on, in two groups (changed since the ruling, unchanged since it)")
    args = parser.parse_args(argv)
    if args.ruling_table and not args.prior_rows:
        parser.error("--ruling-table needs --prior-rows")
    overrides = {(k, p): float(f) for k, p, f in json.loads(args.score_overrides.read_text(encoding="utf-8"))} if args.score_overrides else {}
    try:
        new, table = reanchor(
            json.loads(args.fixture.read_text(encoding="utf-8")), load_rows(args.rows), load_exclusions(args.exclude), overrides,
            {("urban_political_seed123_500t", "COGNITION"): 2}, load_rows(args.prior_rows) if args.prior_rows else None,
        )
    except ReanchorRefused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    args.out.write_text(dump_fixture(new), encoding="utf-8")
    args.table.write_text(table_tsv(table), encoding="utf-8")
    if args.ruling_table:
        args.ruling_table.write_text(ruling_tsv(ruling_rows(table)), encoding="utf-8")
    moved = sum(1 for r in table if r["moved"])
    print(f"wrote {args.out} ({len(table)} pillar rows, {moved} moved, {sum(1 for r in table if r['excluded'])} excluded)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

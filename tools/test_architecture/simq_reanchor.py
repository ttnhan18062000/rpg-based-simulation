"""Re-anchor ``grade_anchors.json`` from audit_mode proof runs, with an exclusion list and a provenance table.

TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE. The anchors are measured under ``audit_mode`` (a run that does not depend on host speed). Before an
anchor moves, each run key needs TWO isolated runs that are identical on every pillar (grade, normalized score, raw score, event count) and overall; a key whose
pair differs is never re-anchored (it is a determinism finding for rpg, not a value). A ``(run_key, pillar)`` row on the exclusion list keeps its committed
anchor (for example a FACTION=0 that rpg rules a regression the stale anchor had hidden; that row gets an rpg-owned known-red instead).

Input rows (``rows.jsonl``, one per run): ``{"key", "rep", "exit", "pillars": {PILLAR: {"grade", "norm", "raw", "events"}}, "overall": [grade, score]}``, the
shape the proof driver writes. Output: the new fixture (same layout as the committed one: ``indent=2`` and a final newline, metadata keys first and untouched,
run keys and pillars in their existing order) and a provenance table with one line per (run_key, pillar)::

    run_key  pillar  committed_grade  committed_score  audit_grade  audit_score  in_band_before  in_band_after  moved  excluded

``in_band_before`` is the committed anchor's own check applied to the audit value (grade within the band and score within the tolerance, including the
per-(run_key, pillar) overrides in ``test_grade_regression``); ``in_band_after`` is the same check against the new anchor (true unless the row is excluded);
``moved`` is ``not in_band_before``.

CLI::

    python -m tools.test_architecture.simq_reanchor --rows rows.jsonl --fixture grade_anchors.json --out new.json --table table.tsv [--exclude exclude.tsv]

``exclude.tsv`` has one ``run_key<TAB>pillar`` per line (``#`` comments allowed). Exit 2 when a key is missing, incomplete or not identical (nothing written).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple

GRADE_ORDER = ("F", "D", "C", "B", "A", "S")
SCORE_ABS_FLOOR, SCORE_REL_PCT = 0.05, 0.20  # mirrors test_grade_regression; a test pins that they agree


class ReanchorRefused(ValueError):
    """The proof rows can not re-anchor; the message names the run key and the rule."""


def within_band(actual: str, anchor: str, tolerance: int = 1) -> bool:
    return actual in GRADE_ORDER and anchor in GRADE_ORDER and abs(GRADE_ORDER.index(actual) - GRADE_ORDER.index(anchor)) <= tolerance


def within_score(actual: float, anchor: float, abs_floor: float = SCORE_ABS_FLOOR) -> bool:
    return abs(actual - anchor) <= max(abs_floor, SCORE_REL_PCT * abs(anchor))


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


def reanchor(
    fixture: Mapping[str, Any],
    rows: Mapping[str, Mapping[int, dict]],
    excluded: Iterable[Tuple[str, str]] = (),
    score_overrides: Optional[Mapping[Tuple[str, str], float]] = None,
    band_overrides: Optional[Mapping[Tuple[str, str], int]] = None,
) -> Tuple[Dict[str, Any], List[dict]]:
    """``(new fixture, provenance rows)``. Every run key of the fixture must have an identical pair; excluded rows keep their committed anchor."""
    excluded = set(excluded)
    score_overrides, band_overrides = score_overrides or {}, band_overrides or {}
    new: Dict[str, Any] = {}
    table: List[dict] = []
    for run_key, pillars in fixture.items():
        if run_key.startswith("_"):
            new[run_key] = pillars
            continue
        audit = audit_values(run_key, rows.get(run_key, {}))
        new[run_key] = {}
        for pillar, anchor in pillars.items():
            actual = audit.get(pillar)
            if actual is None:
                raise ReanchorRefused(f"{run_key}: the audit_mode runs have no {pillar} pillar to anchor on")
            floor = score_overrides.get((run_key, pillar), SCORE_ABS_FLOOR)
            before = within_band(actual["grade"], anchor["grade"], band_overrides.get((run_key, pillar), 1)) and within_score(actual["norm"], anchor["score"], floor)
            skip = (run_key, pillar) in excluded
            new[run_key][pillar] = dict(anchor) if skip else {"grade": actual["grade"], "score": actual["norm"]}
            table.append({
                "run_key": run_key, "pillar": pillar, "committed_grade": anchor["grade"], "committed_score": anchor["score"],
                "audit_grade": actual["grade"], "audit_score": actual["norm"], "in_band_before": before,
                "in_band_after": before if skip else True, "moved": not before, "excluded": skip,
            })
    unknown = sorted(f"{k}:{p}" for k, p in excluded if k not in fixture or p not in fixture[k])
    if unknown:
        raise ReanchorRefused(f"exclusion(s) not in the fixture: {unknown}")
    return new, table


def dump_fixture(fixture: Mapping[str, Any]) -> str:
    return json.dumps(fixture, indent=2) + "\n"


def table_tsv(table: Iterable[Mapping[str, Any]]) -> str:
    cols = ("run_key", "pillar", "committed_grade", "committed_score", "audit_grade", "audit_score", "in_band_before", "in_band_after", "moved", "excluded")
    return "\t".join(cols) + "\n" + "".join("\t".join(str(row[c]) for c in cols) + "\n" for row in table)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--table", type=Path, required=True)
    parser.add_argument("--exclude", type=Path)
    parser.add_argument("--score-overrides", type=Path, help="JSON [[run_key, pillar, abs_floor], ...]: the COMMITTED per-row tolerance widenings, so in_band_before is judged the way the committed anchor was")
    args = parser.parse_args(argv)
    overrides = {(k, p): float(f) for k, p, f in json.loads(args.score_overrides.read_text(encoding="utf-8"))} if args.score_overrides else {}
    try:
        new, table = reanchor(
            json.loads(args.fixture.read_text(encoding="utf-8")), load_rows(args.rows), load_exclusions(args.exclude), overrides,
            {("urban_political_seed123_500t", "COGNITION"): 2},
        )
    except ReanchorRefused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    args.out.write_text(dump_fixture(new), encoding="utf-8")
    args.table.write_text(table_tsv(table), encoding="utf-8")
    moved = sum(1 for r in table if r["moved"])
    print(f"wrote {args.out} ({len(table)} pillar rows, {moved} moved, {sum(1 for r in table if r['excluded'])} excluded)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

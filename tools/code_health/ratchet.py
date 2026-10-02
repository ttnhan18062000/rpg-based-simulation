"""The ratchet: fail only on a violation that is new, or worse than its baseline row.

`compare` matches each current `Finding` to a registry `Row` by `(file, symbol, tool, rule)`
(never a line number; see `tools/code_health/findings.py` for the key each tool produces):

- no row                         -> NEW      (fails)
- value above the row's ceiling  -> WORSE    (fails)
- value below the row's ceiling  -> IMPROVED (reported, never fails)
- row with no current finding    -> GONE     (reported, never fails)
- otherwise                      -> unchanged

The two non-failing outcomes are how paid-off debt shows up: `tighten` (or `delete`) in
`tools.code_health.registry` then lowers or removes the row. Frozen historical debt and a live
regression are different lists in the report, which is what an earlier single-number ratchet in
this repo (TCK-20260915-RATCHET-CONFLATES-HISTORICAL-DEBT-WITH-LIVE-REGRESSION) could not say.

Report-only for now: nothing in CI or any hook runs this (roadmap M4 gates it).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from tools.code_health.findings import Finding
from tools.code_health.registry import Row

DEFAULT_REPORT_LIMIT = 25


@dataclass(frozen=True)
class RatchetResult:
    """The outcome of comparing one scan with the registry."""

    new: tuple[Finding, ...] = ()
    worse: tuple[tuple[Finding, Row], ...] = ()
    improved: tuple[tuple[Finding, Row], ...] = ()
    gone: tuple[Row, ...] = ()
    unchanged: int = 0

    @property
    def failed(self) -> bool:
        """True if any violation is new or above its ceiling."""
        return bool(self.new or self.worse)


def compare(findings: Iterable[Finding], rows: Sequence[Row]) -> RatchetResult:
    """Compare a scan with the registry. Both are matched by key, so line moves never matter."""
    baseline = {row.key: row for row in rows}
    seen: set[tuple] = set()
    new: list[Finding] = []
    worse: list[tuple[Finding, Row]] = []
    improved: list[tuple[Finding, Row]] = []
    unchanged = 0
    for finding in findings:
        seen.add(finding.key)
        row = baseline.get(finding.key)
        if row is None:
            new.append(finding)
        elif finding.value > row.ceiling:
            worse.append((finding, row))
        elif finding.value < row.ceiling:
            improved.append((finding, row))
        else:
            unchanged += 1
    gone = [row for row in rows if row.key not in seen]
    return RatchetResult(tuple(new), tuple(worse), tuple(improved), tuple(gone), unchanged)


def _where(finding: Finding) -> str:
    place = f"{finding.file}:{finding.line}" if finding.line else finding.file
    return f"{place} {finding.symbol}" if finding.symbol else place


def _section(title: str, lines: list[str], limit: int) -> list[str]:
    if not lines:
        return []
    shown = lines[:limit]
    more = [f"  ... and {len(lines) - limit} more"] if len(lines) > limit else []
    return [f"{title} ({len(lines)}):", *shown, *more]


def format_report(result: RatchetResult, limit: int = DEFAULT_REPORT_LIMIT) -> str:
    """A plain-text report: failures first, then the non-failing changes, then a one-line verdict."""
    lines: list[str] = []
    lines += _section(
        "NEW violations (no baseline row)",
        [f"  {_where(f)} [{f.tool} {f.rule}] value={f.value}" for f in result.new],
        limit,
    )
    lines += _section(
        "WORSE than baseline",
        [f"  {_where(f)} [{f.tool} {f.rule}] {f.value} > ceiling {r.ceiling}" for f, r in result.worse],
        limit,
    )
    lines += _section(
        "improved (not a failure; run `tighten` to lower the ceiling)",
        [f"  {_where(f)} [{f.tool} {f.rule}] {f.value} < ceiling {r.ceiling}" for f, r in result.improved],
        limit,
    )
    lines += _section(
        "gone (not a failure; run `tighten` or `delete` to remove the row)",
        [f"  {r.file} {r.symbol or ''} [{r.tool} {r.rule}]" for r in result.gone],
        limit,
    )
    verdict = "FAIL" if result.failed else "OK"
    lines.append(
        f"{verdict}: {len(result.new)} new, {len(result.worse)} worse, {len(result.improved)} improved, "
        f"{len(result.gone)} gone, {result.unchanged} unchanged"
    )
    return "\n".join(lines)

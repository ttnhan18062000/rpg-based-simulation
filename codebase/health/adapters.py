"""One adapter per adopted tool: raw JSON output in, normalised `Finding` records out.

Each adapter is a pure function of the tool's own JSON, so it can be tested against a captured
real output (tests/fixtures/code_health/). The match key each adapter produces is documented in
`codebase/health/findings.py`.

complexipy is handled by an adapter, not by its native snapshot file. Roadmap section 6.3 allowed
either; the adapter keeps one ratchet, one registry and symbol-level keys for every tool, and
complexipy's JSON already names the function. Switching to the native baseline later only means
dropping `adapt_complexipy` and recording the snapshot file in the registry.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, Mapping, Sequence

from codebase.health.findings import (
    TOOL_COMPLEXIPY,
    TOOL_JSCPD,
    TOOL_LINE_COUNT,
    TOOL_RUFF,
    Finding,
    aggregate,
)

RULE_COGNITIVE = "cognitive-complexity"
RULE_DUPLICATE = "duplicate-block"
RULE_SYNTAX_ERROR = "syntax-error"
_LENGTH_RULES = {"function": "function-length", "class": "class-length", "module": "module-length"}
_OVER_LIMIT_LEVELS = {"fail", "flag"}


def _relative(path: str, root: str | None) -> str:
    posix = PurePosixPath(path.replace("\\", "/"))
    if root is not None:
        try:
            return posix.relative_to(PurePosixPath(root.replace("\\", "/"))).as_posix()
        except ValueError:
            pass
    return posix.as_posix()


def adapt_ruff(records: Sequence[Mapping[str, Any]], root: str | None = None) -> list[Finding]:
    """`ruff check --output-format json` -> one count per (file, rule).

    Ruff reports absolute paths; `root` (the repository root) is stripped to make them relative.
    """
    findings = [
        Finding(
            file=_relative(str(record["filename"]), root),
            symbol=None,
            tool=TOOL_RUFF,
            rule=str(record.get("code") or RULE_SYNTAX_ERROR),
            value=1,
            line=(record.get("location") or {}).get("row"),
        )
        for record in records
    ]
    return aggregate(findings, "sum")


def adapt_complexipy(records: Sequence[Mapping[str, Any]], max_allowed: int) -> list[Finding]:
    """complexipy JSON (`--output-format json`) -> functions over `max_allowed`, by qualified name."""
    findings = [
        Finding(
            file=_relative(str(record["path"]), None),
            symbol=str(record["function_name"]).replace("::", "."),
            tool=TOOL_COMPLEXIPY,
            rule=RULE_COGNITIVE,
            value=int(record["complexity"]),
        )
        for record in records
        if int(record["complexity"]) > max_allowed
    ]
    return aggregate(findings, "max")


def adapt_jscpd(report: Mapping[str, Any], scan_root: str) -> list[Finding]:
    """jscpd's `jscpd-report.json` -> total duplicated lines per ordered pair of files.

    jscpd names files relative to the scanned directory, so `scan_root` (for example `src`) is put
    back in front of each name.
    """
    findings = []
    for clone in report.get("duplicates", []):
        first = f"{scan_root}/{clone['firstFile']['name']}"
        second = f"{scan_root}/{clone['secondFile']['name']}"
        low, high = sorted((first, second))
        findings.append(
            Finding(
                file=low,
                symbol=f"dup:{high}",
                tool=TOOL_JSCPD,
                rule=RULE_DUPLICATE,
                value=int(clone["lines"]),
                line=clone["firstFile"].get("start") if low == first else clone["secondFile"].get("start"),
            )
        )
    return aggregate(findings, "sum")


def adapt_line_count(report: Mapping[str, Any]) -> list[Finding]:
    """`line_count --format json` -> functions over the fail limit, classes and modules over theirs."""
    findings = [
        Finding(
            file=record["path"],
            symbol=None if record["kind"] == "module" else record["symbol"],
            tool=TOOL_LINE_COUNT,
            rule=_LENGTH_RULES[record["kind"]],
            value=int(record["lines"]),
            line=record["start_line"],
        )
        for record in report.get("records", [])
        if record["level"] in _OVER_LIMIT_LEVELS
    ]
    return aggregate(findings, "max")

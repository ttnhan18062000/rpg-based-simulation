"""Render a JUnit XML file (produced by pytest's built-in `--junit-xml`) as a markdown
pass/fail/skip/error/duration summary table, for piping into `$GITHUB_STEP_SUMMARY`.

Built for TCK-20260823-CI-STEP-SUMMARY-REPORTING. Invoked from `.github/workflows/test.yml`
as an `if: always()` step immediately after each fast-lane job's `pytest` step, so it must run
even when the job crashed before pytest could write a complete (or any) XML file -- `main()`
therefore always returns 0 and never raises, regardless of parse outcome. That guarantee lives
in this module (not a workflow-level `continue-on-error:`) specifically so it stays independently
unit-testable.

Deliberately placed in `tools/`, not `tools/gate_checks/` -- that package's own test suite
(`tests/tools/test_ci_workflow_test_coverage.py::test_module_has_no_argparse_entry_point`)
enforces a no-CLI/argparse-entry-point convention for its modules; this one needs a `python3`-
invocable CLI entry point by design.

pytest's default `xunit2` JUnit writer (confirmed: no `junit_family` override in
`pyproject.toml`) emits `tests`/`failures`/`errors`/`skipped`/`time` as attributes on the
`<testsuite>` element, optionally wrapped in a `<testsuites>` root when there is more than one
suite. `passed` has no XML attribute of its own -- it is derived as
`total - failed - errors - skipped`.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class JUnitSummary:
    total: int
    passed: int
    failed: int
    errors: int
    skipped: int
    duration_seconds: float
    parse_ok: bool


_EMPTY_SUMMARY = JUnitSummary(
    total=0, passed=0, failed=0, errors=0, skipped=0, duration_seconds=0.0, parse_ok=False
)


def _int_attr(elem: ET.Element, name: str) -> int:
    return int(elem.get(name, "0"))


def _float_attr(elem: ET.Element, name: str) -> float:
    return float(elem.get(name, "0"))


def _summarize_testsuite_elements(elements: list[ET.Element]) -> JUnitSummary:
    total = failed = errors = skipped = 0
    duration = 0.0
    for suite in elements:
        total += _int_attr(suite, "tests")
        failed += _int_attr(suite, "failures")
        errors += _int_attr(suite, "errors")
        skipped += _int_attr(suite, "skipped")
        duration += _float_attr(suite, "time")
    passed = total - failed - errors - skipped
    return JUnitSummary(
        total=total,
        passed=passed,
        failed=failed,
        errors=errors,
        skipped=skipped,
        duration_seconds=duration,
        parse_ok=True,
    )


def parse_junit_xml(path: Path) -> JUnitSummary:
    """Parse a pytest-emitted JUnit XML file into a `JUnitSummary`. Never raises -- any
    missing file, malformed XML, or unexpected attribute shape resolves to the all-zero
    `parse_ok=False` sentinel instead."""
    try:
        tree = ET.parse(path)
    except (ET.ParseError, FileNotFoundError, OSError):
        return _EMPTY_SUMMARY

    root = tree.getroot()
    try:
        if root.tag == "testsuites":
            suites = root.findall("testsuite")
        elif root.tag == "testsuite":
            suites = [root]
        else:
            return _EMPTY_SUMMARY
        if not suites:
            return _EMPTY_SUMMARY
        return _summarize_testsuite_elements(suites)
    except (KeyError, ValueError):
        return _EMPTY_SUMMARY


@dataclass(frozen=True)
class TestCaseRecord:
    test_id: str
    status: str  # "passed" | "failed" | "error" | "skipped"


def _testcase_status(testcase: ET.Element) -> str:
    if testcase.find("failure") is not None:
        return "failed"
    if testcase.find("error") is not None:
        return "error"
    if testcase.find("skipped") is not None:
        return "skipped"
    return "passed"


def parse_testcase_records(path: Path) -> list[TestCaseRecord]:
    """Parse per-testcase (classname+name, status) pairs out of a pytest-emitted JUnit XML
    file. Never raises -- mirrors `parse_junit_xml`'s defensive shape, but returns an empty
    list instead of a sentinel dataclass since there is no meaningful "parse_ok" concept for
    a list of records."""
    try:
        tree = ET.parse(path)
    except (ET.ParseError, FileNotFoundError, OSError):
        return []

    root = tree.getroot()
    if root.tag == "testsuites":
        suites = root.findall("testsuite")
    elif root.tag == "testsuite":
        suites = [root]
    else:
        return []

    records: list[TestCaseRecord] = []
    for suite in suites:
        for testcase in suite.findall("testcase"):
            test_id = f"{testcase.get('classname', '')}::{testcase.get('name', '')}"
            records.append(TestCaseRecord(test_id=test_id, status=_testcase_status(testcase)))
    return records


def _normalize_collect_only_node_id(node_id: str) -> str:
    """`pytest --collect-only -q` prints slash-form file paths with `.py` intact
    (`path/to/test_file.py::TestClass::test_name`); JUnit XML's `classname` attribute is a
    dotted module path with `.py` stripped. Normalize only the leading file-path segment so
    both sides land on the same `classname::name` canonical form."""
    segments = node_id.split("::")
    file_segment = segments[0].replace("/", ".")
    if file_segment.endswith(".py"):
        file_segment = file_segment[: -len(".py")]
    segments[0] = file_segment
    return "::".join(segments)


def parse_collect_only_ids(text: str) -> set[str]:
    """Parse a `pytest --collect-only -q` text listing into a set of canonical test IDs.
    Lines without `::` (e.g. a trailing "N tests collected in Ys" summary line, or blank
    lines) are silently skipped -- never raises, and garbage/empty input resolves to an
    empty set rather than an exception."""
    ids: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if "::" not in stripped:
            continue
        ids.add(_normalize_collect_only_node_id(stripped))
    return ids


@dataclass(frozen=True)
class NewExistingBreakdown:
    new_total: int
    new_passed: int
    new_failed: int
    new_errors: int
    new_skipped: int
    existing_total: int
    existing_passed: int
    existing_failed: int
    existing_errors: int
    existing_skipped: int


def classify_new_vs_existing(
    head_records: list[TestCaseRecord], base_ids: set[str] | None
) -> NewExistingBreakdown | None:
    """Split head-branch test IDs into new-vs-existing buckets against a base-branch
    collect-only ID set. `base_ids=None` means "no base data available" (non-PR run, or a
    fetch/collection failure upstream) and skips the breakdown entirely rather than computing
    a degenerate result. `base_ids=set()` (e.g. malformed/empty base listing) is a normal,
    safe input -- every head record is classified `new`, since nothing was found in the base."""
    if base_ids is None:
        return None

    counts = {
        "new": {"total": 0, "passed": 0, "failed": 0, "error": 0, "skipped": 0},
        "existing": {"total": 0, "passed": 0, "failed": 0, "error": 0, "skipped": 0},
    }
    for record in head_records:
        bucket = counts["existing"] if record.test_id in base_ids else counts["new"]
        bucket["total"] += 1
        bucket[record.status] += 1

    return NewExistingBreakdown(
        new_total=counts["new"]["total"],
        new_passed=counts["new"]["passed"],
        new_failed=counts["new"]["failed"],
        new_errors=counts["new"]["error"],
        new_skipped=counts["new"]["skipped"],
        existing_total=counts["existing"]["total"],
        existing_passed=counts["existing"]["passed"],
        existing_failed=counts["existing"]["failed"],
        existing_errors=counts["existing"]["error"],
        existing_skipped=counts["existing"]["skipped"],
    )


def render_markdown_table(
    summary: JUnitSummary,
    job_name: str,
    breakdown: NewExistingBreakdown | None = None,
) -> str:
    header = f"### CI job summary — {job_name}\n\n"
    if not summary.parse_ok:
        return (
            header
            + "| Result |\n"
            + "| --- |\n"
            + "| No JUnit results available (missing or unparseable report) |\n"
        )
    table = (
        header
        + "| Passed | Failed | Errors | Skipped | Duration (s) |\n"
        + "| --- | --- | --- | --- | --- |\n"
        + f"| {summary.passed} | {summary.failed} | {summary.errors} | {summary.skipped} "
        + f"| {summary.duration_seconds:.2f} |\n"
    )
    if breakdown is None:
        return table
    return (
        table
        + "\n#### New vs. existing tests (diffed against PR base branch)\n\n"
        + "| Category | Total | Passed | Failed | Errors | Skipped |\n"
        + "| --- | --- | --- | --- | --- | --- |\n"
        + f"| New | {breakdown.new_total} | {breakdown.new_passed} | {breakdown.new_failed} "
        + f"| {breakdown.new_errors} | {breakdown.new_skipped} |\n"
        + f"| Existing | {breakdown.existing_total} | {breakdown.existing_passed} "
        + f"| {breakdown.existing_failed} | {breakdown.existing_errors} "
        + f"| {breakdown.existing_skipped} |\n"
    )


def main(argv: list[str]) -> int:
    try:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("junit_xml_path", help="Path to the pytest --junit-xml output file")
        parser.add_argument("job_name", help="CI job name/key, used as the summary table title")
        parser.add_argument(
            "base_collect_only_path",
            nargs="?",
            default=None,
            help=(
                "Path to a pytest --collect-only -q text listing computed against the PR's "
                "base branch. Omitted, missing, or empty on non-PR runs -- resolves to no "
                "new/existing breakdown rather than an error."
            ),
        )
        args = parser.parse_args(argv)

        summary = parse_junit_xml(Path(args.junit_xml_path))
        head_records = parse_testcase_records(Path(args.junit_xml_path))

        base_ids: set[str] | None = None
        if args.base_collect_only_path:
            base_path = Path(args.base_collect_only_path)
            if base_path.is_file() and base_path.stat().st_size > 0:
                base_ids = parse_collect_only_ids(base_path.read_text())

        breakdown = classify_new_vs_existing(head_records, base_ids)
        print(render_markdown_table(summary, args.job_name, breakdown))
    except Exception as exc:  # never let an unexpected error become a second CI failure gate
        print(f"### CI job summary\n\nFailed to render job summary: {exc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

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


def render_markdown_table(summary: JUnitSummary, job_name: str) -> str:
    header = f"### CI job summary — {job_name}\n\n"
    if not summary.parse_ok:
        return (
            header
            + "| Result |\n"
            + "| --- |\n"
            + "| No JUnit results available (missing or unparseable report) |\n"
        )
    return (
        header
        + "| Passed | Failed | Errors | Skipped | Duration (s) |\n"
        + "| --- | --- | --- | --- | --- |\n"
        + f"| {summary.passed} | {summary.failed} | {summary.errors} | {summary.skipped} "
        + f"| {summary.duration_seconds:.2f} |\n"
    )


def main(argv: list[str]) -> int:
    try:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("junit_xml_path", help="Path to the pytest --junit-xml output file")
        parser.add_argument("job_name", help="CI job name/key, used as the summary table title")
        args = parser.parse_args(argv)

        summary = parse_junit_xml(Path(args.junit_xml_path))
        print(render_markdown_table(summary, args.job_name))
    except Exception as exc:  # never let an unexpected error become a second CI failure gate
        print(f"### CI job summary\n\nFailed to render job summary: {exc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Unit tests for tools/ci_junit_summary.py.

Built for TCK-20260823-CI-STEP-SUMMARY-REPORTING. Exercises the parser against fixture JUnit
XML files under tests/tools/fixtures/ci_junit_summary/ covering all-pass, failure, error, skip,
empty-testsuite, malformed, and missing-file outcome shapes, plus the markdown renderer and the
`main()` entry point's "always exits 0" guarantee -- the concrete evidence that the new
`if: always()` CI step can never become a second failure gate.
"""

from __future__ import annotations

from pathlib import Path

from tools.ci_junit_summary import main, parse_junit_xml, render_markdown_table

_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ci_junit_summary"


def test_parse_junit_xml_all_passing() -> None:
    summary = parse_junit_xml(_FIXTURES / "all_pass.xml")
    assert summary.parse_ok is True
    assert summary.total == 5
    assert summary.passed == 5
    assert summary.failed == 0
    assert summary.errors == 0
    assert summary.skipped == 0
    assert summary.duration_seconds == 1.234


def test_parse_junit_xml_with_failure() -> None:
    summary = parse_junit_xml(_FIXTURES / "has_failure.xml")
    assert summary.parse_ok is True
    assert summary.total == 4
    assert summary.failed == 1
    assert summary.errors == 0
    assert summary.skipped == 0
    assert summary.passed == 3
    assert summary.duration_seconds == 2.5


def test_parse_junit_xml_with_error() -> None:
    summary = parse_junit_xml(_FIXTURES / "has_error.xml")
    assert summary.parse_ok is True
    assert summary.total == 3
    assert summary.errors == 1
    assert summary.failed == 0
    assert summary.skipped == 0
    assert summary.passed == 2
    assert summary.duration_seconds == 0.75


def test_parse_junit_xml_with_skip() -> None:
    summary = parse_junit_xml(_FIXTURES / "has_skip.xml")
    assert summary.parse_ok is True
    assert summary.total == 3
    assert summary.skipped == 1
    assert summary.failed == 0
    assert summary.errors == 0
    assert summary.passed == 2
    assert summary.duration_seconds == 0.6


def test_parse_junit_xml_empty_testsuite_produces_correct_zero_counts() -> None:
    summary = parse_junit_xml(_FIXTURES / "empty.xml")
    assert summary.parse_ok is True
    assert summary.total == 0
    assert summary.passed == 0
    assert summary.failed == 0
    assert summary.errors == 0
    assert summary.skipped == 0
    assert summary.duration_seconds == 0.0


def test_parse_junit_xml_malformed_produces_safe_fallback() -> None:
    summary = parse_junit_xml(_FIXTURES / "malformed.xml")
    assert summary.parse_ok is False
    assert summary.total == 0
    assert summary.passed == 0
    assert summary.failed == 0
    assert summary.errors == 0
    assert summary.skipped == 0


def test_parse_junit_xml_missing_file_produces_safe_fallback() -> None:
    summary = parse_junit_xml(_FIXTURES / "does_not_exist.xml")
    assert summary.parse_ok is False
    assert summary.total == 0
    assert summary.passed == 0
    assert summary.failed == 0
    assert summary.errors == 0
    assert summary.skipped == 0


def test_markdown_table_output_shape() -> None:
    summary = parse_junit_xml(_FIXTURES / "has_failure.xml")
    table = render_markdown_table(summary, "unit-core-world")
    assert "unit-core-world" in table
    assert "| Passed | Failed | Errors | Skipped | Duration (s) |" in table
    assert "| 3 | 1 | 0 | 0 | 2.50 |" in table


def test_markdown_table_output_shape_for_parse_failure() -> None:
    summary = parse_junit_xml(_FIXTURES / "does_not_exist.xml")
    table = render_markdown_table(summary, "unit-core-world")
    assert "unit-core-world" in table
    assert "No JUnit results available" in table


def test_parser_exit_code_independent_of_test_outcome() -> None:
    assert main([str(_FIXTURES / "all_pass.xml"), "unit-core-world"]) == 0
    assert main([str(_FIXTURES / "has_failure.xml"), "unit-core-world"]) == 0
    assert main([str(_FIXTURES / "has_error.xml"), "unit-core-world"]) == 0
    assert main([str(_FIXTURES / "malformed.xml"), "unit-core-world"]) == 0
    assert main([str(_FIXTURES / "does_not_exist.xml"), "unit-core-world"]) == 0

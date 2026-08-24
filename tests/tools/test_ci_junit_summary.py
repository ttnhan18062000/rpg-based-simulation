"""Unit tests for tools/ci_junit_summary.py.

Built for TCK-20260823-CI-STEP-SUMMARY-REPORTING. Exercises the parser against fixture JUnit
XML files under tests/tools/fixtures/ci_junit_summary/ covering all-pass, failure, error, skip,
empty-testsuite, malformed, and missing-file outcome shapes, plus the markdown renderer and the
`main()` entry point's "always exits 0" guarantee -- the concrete evidence that the new
`if: always()` CI step can never become a second failure gate.
"""

from __future__ import annotations

from pathlib import Path

from tools.ci_junit_summary import (
    _normalize_collect_only_node_id,
    classify_new_vs_existing,
    main,
    parse_collect_only_ids,
    parse_junit_xml,
    parse_testcase_records,
    render_markdown_table,
)

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


def test_parse_testcase_records_extracts_all_states() -> None:
    records = parse_testcase_records(_FIXTURES / "head_with_testcases.xml")
    by_id = {r.test_id: r.status for r in records}
    assert by_id["tests.unit.core.test_new::test_new_passed"] == "passed"
    assert by_id["tests.unit.core.test_new::test_new_failed"] == "failed"
    assert by_id["tests.unit.core.test_new::test_new_skipped"] == "skipped"
    assert by_id["tests.unit.core.test_new::test_new_error"] == "error"
    assert by_id["tests.unit.core.test_a::test_one"] == "passed"
    assert by_id["tests.unit.core.test_a::test_two"] == "failed"
    assert by_id["tests.unit.core.test_b::test_three"] == "skipped"
    assert by_id["tests.unit.core.test_b::test_four"] == "passed"
    assert len(records) == 8


def test_parse_testcase_records_missing_file_returns_empty_list() -> None:
    assert parse_testcase_records(_FIXTURES / "does_not_exist.xml") == []


def test_parse_testcase_records_malformed_returns_empty_list() -> None:
    assert parse_testcase_records(_FIXTURES / "malformed.xml") == []


def test_id_normalization_reconciles_collect_only_nodeid_with_junit_classname() -> None:
    assert (
        _normalize_collect_only_node_id("tests/unit/core/test_a.py::test_one")
        == "tests.unit.core.test_a::test_one"
    )
    assert (
        _normalize_collect_only_node_id("tests/unit/core/test_b.py::TestFoo::test_bar")
        == "tests.unit.core.test_b.TestFoo::test_bar"
    )


def test_id_normalization_dot_joins_nested_class_segments() -> None:
    assert (
        _normalize_collect_only_node_id(
            "tests/unit/core/test_b.py::Outer::Inner::test_method"
        )
        == "tests.unit.core.test_b.Outer.Inner::test_method"
    )


def test_parse_collect_only_ids_skips_non_nodeid_lines() -> None:
    text = "tests/unit/core/test_a.py::test_one\n\n12 tests collected in 0.34s\n"
    assert parse_collect_only_ids(text) == {"tests.unit.core.test_a::test_one"}


def test_parse_collect_only_ids_garbage_input_resolves_to_empty_set() -> None:
    assert parse_collect_only_ids("") == set()
    assert parse_collect_only_ids("not a node id\nneither is this\n") == set()


def test_parse_collect_only_ids_dot_joins_nested_class_segments() -> None:
    text = "tests/unit/core/test_b.py::Outer::Inner::test_method\n\n1 tests collected in 0.01s\n"
    assert parse_collect_only_ids(text) == {"tests.unit.core.test_b.Outer.Inner::test_method"}


def test_classify_new_vs_existing_matches_class_based_tests_as_existing() -> None:
    head_records = parse_testcase_records(_FIXTURES / "head_with_class_testcases.xml")
    base_ids = parse_collect_only_ids(
        (_FIXTURES / "base_collect_only_with_classes.txt").read_text()
    )
    breakdown = classify_new_vs_existing(head_records, base_ids)

    assert breakdown is not None
    # tests.tools.test_x.TestFoo::test_bar (single-level class) and
    # tests.tools.test_y.Outer.Inner::test_method (nested class) both appear in the base
    # collect-only listing and must classify as existing, not new.
    assert breakdown.existing_total == 2
    # tests.tools.test_z.TestBrandNew::test_never_seen_before has no base-branch match.
    assert breakdown.new_total == 1


def test_classify_new_vs_existing_splits_by_base_collect_only_ids() -> None:
    head_records = parse_testcase_records(_FIXTURES / "head_with_testcases.xml")
    base_ids = parse_collect_only_ids((_FIXTURES / "base_collect_only.txt").read_text())
    breakdown = classify_new_vs_existing(head_records, base_ids)
    assert breakdown is not None
    assert breakdown.existing_total == 4
    assert breakdown.new_total == 4


def test_classify_new_vs_existing_all_six_states() -> None:
    head_records = parse_testcase_records(_FIXTURES / "head_with_testcases.xml")
    base_ids = parse_collect_only_ids((_FIXTURES / "base_collect_only.txt").read_text())
    breakdown = classify_new_vs_existing(head_records, base_ids)
    assert breakdown is not None
    # new: test_new_passed, test_new_failed, test_new_skipped, test_new_error
    assert breakdown.new_passed == 1
    assert breakdown.new_failed == 1
    assert breakdown.new_skipped == 1
    assert breakdown.new_errors == 1
    # existing: test_one (passed), test_two (failed), test_three (skipped), test_four (passed)
    assert breakdown.existing_passed == 2
    assert breakdown.existing_failed == 1
    assert breakdown.existing_skipped == 1
    assert breakdown.existing_errors == 0


def test_classify_malformed_or_missing_base_listing_resolves_to_safe_fallback() -> None:
    head_records = parse_testcase_records(_FIXTURES / "head_with_testcases.xml")

    assert classify_new_vs_existing(head_records, None) is None

    breakdown = classify_new_vs_existing(head_records, set())
    assert breakdown is not None
    assert breakdown.new_total == len(head_records)
    assert breakdown.existing_total == 0


def test_render_markdown_table_includes_new_existing_breakdown() -> None:
    summary = parse_junit_xml(_FIXTURES / "has_failure.xml")
    head_records = parse_testcase_records(_FIXTURES / "head_with_testcases.xml")
    base_ids = parse_collect_only_ids((_FIXTURES / "base_collect_only.txt").read_text())
    breakdown = classify_new_vs_existing(head_records, base_ids)

    table = render_markdown_table(summary, "unit-core-world", breakdown)

    assert "| Passed | Failed | Errors | Skipped | Duration (s) |" in table
    assert "| 3 | 1 | 0 | 0 | 2.50 |" in table
    assert "New vs. existing tests" in table
    assert "| New | 4 | 1 | 1 | 1 | 1 |" in table
    assert "| Existing | 4 | 2 | 1 | 0 | 1 |" in table


def test_render_markdown_table_omits_breakdown_when_no_base_data() -> None:
    summary = parse_junit_xml(_FIXTURES / "has_failure.xml")
    table_without_breakdown_arg = render_markdown_table(summary, "unit-core-world")
    table_with_none_breakdown = render_markdown_table(summary, "unit-core-world", None)

    assert table_without_breakdown_arg == table_with_none_breakdown
    assert "New vs. existing tests" not in table_without_breakdown_arg
    assert table_without_breakdown_arg == (
        "### CI job summary — unit-core-world\n\n"
        "| Passed | Failed | Errors | Skipped | Duration (s) |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| 3 | 1 | 0 | 0 | 2.50 |\n"
    )


def test_main_with_base_collect_only_arg_still_exits_zero_and_shows_breakdown(capsys) -> None:
    exit_code = main(
        [
            str(_FIXTURES / "head_with_testcases.xml"),
            "unit-core-world",
            str(_FIXTURES / "base_collect_only.txt"),
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "New vs. existing tests" in captured.out


def test_main_with_missing_base_collect_only_path_falls_back_gracefully(capsys) -> None:
    exit_code = main(
        [
            str(_FIXTURES / "head_with_testcases.xml"),
            "unit-core-world",
            str(_FIXTURES / "does_not_exist_base.txt"),
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "New vs. existing tests" not in captured.out

"""Unit tests for tools/ci_junit_merge.py.

Built for TCK-20260916-CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS, after review found the original
inline-YAML merge step silently dropped a shard's results on parse failure with nothing anywhere
noticing (`grep` found zero prior tests covering the merge step at all). Plants a corrupt/missing
shard and confirms the merge both surfaces it (`missing_paths`) and, via the CLI, fails loudly
(`::warning::`/`::error::` plus a non-zero exit) rather than quietly producing a smaller report.
"""

from __future__ import annotations

from pathlib import Path

from tools.ci_junit_merge import main, merge_junit_shards

_VALID_SHARD = """<?xml version="1.0"?>
<testsuite name="pytest" tests="2" failures="0" errors="0" skipped="0" time="1.0">
  <testcase classname="tests.unit.domains.test_a" name="test_one" time="0.1"/>
  <testcase classname="tests.unit.domains.test_a" name="test_two" time="0.1"/>
</testsuite>
"""

_OTHER_VALID_SHARD = """<?xml version="1.0"?>
<testsuite name="pytest" tests="1" failures="1" errors="0" skipped="0" time="0.5">
  <testcase classname="tests.unit.observability.test_b" name="test_three" time="0.5">
    <failure message="boom">AssertionError</failure>
  </testcase>
</testsuite>
"""


def _write(path: Path, content: str) -> str:
    path.write_text(content, encoding="utf-8")
    return str(path)


def test_merge_all_shards_present_and_valid(tmp_path: Path) -> None:
    shard_a = _write(tmp_path / "a.xml", _VALID_SHARD)
    shard_b = _write(tmp_path / "b.xml", _OTHER_VALID_SHARD)
    out = tmp_path / "merged.xml"

    result = merge_junit_shards([shard_a, shard_b], out)

    assert result.all_merged is True
    assert result.missing_paths == []
    assert result.expected_count == 2
    merged_text = out.read_text()
    assert "test_one" in merged_text
    assert "test_three" in merged_text


def test_merge_records_a_missing_shard_rather_than_dropping_it_silently(tmp_path: Path) -> None:
    shard_a = _write(tmp_path / "a.xml", _VALID_SHARD)
    missing_shard = str(tmp_path / "does-not-exist.xml")
    out = tmp_path / "merged.xml"

    result = merge_junit_shards([shard_a, missing_shard], out)

    assert result.all_merged is False
    assert result.missing_paths == [missing_shard]
    assert result.merged_paths == [shard_a]
    # The merged file is still written -- a lost shard must not also lose everything else.
    assert "test_one" in out.read_text()


def test_merge_records_a_corrupt_shard_rather_than_dropping_it_silently(tmp_path: Path) -> None:
    shard_a = _write(tmp_path / "a.xml", _VALID_SHARD)
    corrupt_shard = _write(tmp_path / "corrupt.xml", "not valid xml at all <<<")
    out = tmp_path / "merged.xml"

    result = merge_junit_shards([shard_a, corrupt_shard], out)

    assert result.all_merged is False
    assert result.missing_paths == [corrupt_shard]


def test_cli_exits_zero_when_all_shards_merge(tmp_path: Path, capsys) -> None:
    shard_a = _write(tmp_path / "a.xml", _VALID_SHARD)
    out = tmp_path / "merged.xml"

    exit_code = main(["--out", str(out), shard_a])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "::error::" not in captured.out


def test_cli_fails_loudly_when_a_shard_is_missing_not_a_smaller_silent_report(
    tmp_path: Path, capsys,
) -> None:
    shard_a = _write(tmp_path / "a.xml", _VALID_SHARD)
    missing_shard = str(tmp_path / "does-not-exist.xml")
    out = tmp_path / "merged.xml"

    exit_code = main(["--out", str(out), shard_a, missing_shard])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "::warning::" in captured.out
    assert missing_shard in captured.out
    assert "::error::" in captured.out
    # The merged file still exists and still has the one real shard's data -- this is a
    # visibility failure, not a data-destruction one.
    assert "test_one" in out.read_text()


def test_real_shard_path_list_and_merged_output_path_match_the_workflow() -> None:
    from tools.ci_junit_merge import UNIT_INFRA_MERGED_PATH, UNIT_INFRA_SHARD_PATHS

    workflow_text = Path(".github/workflows/test.yml").read_text(encoding="utf-8")
    for shard_path in UNIT_INFRA_SHARD_PATHS:
        assert shard_path in workflow_text, (
            f"{shard_path!r} from UNIT_INFRA_SHARD_PATHS not found in test.yml -- the module's "
            "own expected-shard list has drifted from the workflow's real --junit-xml= paths"
        )
    assert UNIT_INFRA_MERGED_PATH in workflow_text
    assert "tools/ci_junit_merge.py" in workflow_text

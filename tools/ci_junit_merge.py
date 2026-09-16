"""Merge several per-directory JUnit XML shards (produced by `unit-infra`'s per-directory
`Run: <path>` steps, TCK-20260916-CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS) into one combined
file at the path the existing "Job summary" step already reads (`ci_junit_summary.py`), so
splitting a job's Run step into N steps for diagnostic purposes doesn't require any downstream
change.

**Why this exists as a real module, not inline YAML** (found during review, TCK-20260916-
CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS): a first version lived entirely inside the workflow
file as a `python3 -c "..."` block, globbed for `unit-infra-*.xml`, and silently `continue`d
past any shard that was missing or failed to parse. That is a reporting-fidelity gap, not a
green-when-red gap -- every split step still carries `if: always()` with no
`continue-on-error:`, so a real test failure still fails the job independently of this merge --
but a lost shard produced a merged report with `parse_ok=True` and a smaller, entirely
plausible total, with nothing anywhere noticing. Extracted here so the "did every expected
shard actually merge" invariant is a real, independently testable function instead of an
un-covered inline script (`grep` before this fix found zero tests touching the merge step at
all).

Deliberately placed in `tools/`, not `tools/gate_checks/` -- same reasoning as
`ci_junit_summary.py`'s own docstring: this needs a `python3`-invocable CLI entry point, and
that package's own test suite enforces a no-CLI convention for its modules.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MergeResult:
    merged_paths: list[str]
    missing_paths: list[str]

    @property
    def expected_count(self) -> int:
        return len(self.merged_paths) + len(self.missing_paths)

    @property
    def all_merged(self) -> bool:
        return not self.missing_paths


def merge_junit_shards(expected_paths: list[str], out_path: Path) -> MergeResult:
    """Merge each file in `expected_paths` (a pytest `--junit-xml` output) into a single
    `<testsuites>` document written to `out_path`. A shard that is missing or fails to parse
    is skipped -- its path is recorded in the returned `MergeResult.missing_paths` rather than
    silently dropped, so the caller (the CLI below, or a test) can decide whether that is
    acceptable. Always writes `out_path`, even when every shard is missing (an empty
    `<testsuites>` root) -- the downstream summary step must never be left with no file at all."""
    root = ET.Element("testsuites")
    merged_paths: list[str] = []
    missing_paths: list[str] = []

    for path_str in expected_paths:
        path = Path(path_str)
        try:
            parsed = ET.parse(path).getroot()
        except (ET.ParseError, OSError, FileNotFoundError):
            missing_paths.append(path_str)
            continue
        if parsed.tag == "testsuites":
            root.extend(parsed.findall("testsuite"))
        elif parsed.tag == "testsuite":
            root.append(parsed)
        merged_paths.append(path_str)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(out_path)
    return MergeResult(merged_paths=merged_paths, missing_paths=missing_paths)


# The 17 per-directory shard paths written by unit-infra's own "Run: <path>" steps
# (.github/workflows/test.yml) -- kept as an explicit list, not a glob, so a step that crashed
# before pytest could write ANY output file is caught the same way as a corrupt one (a glob
# would simply not see a missing file at all).
UNIT_INFRA_SHARD_PATHS = [
    "reports/junit/unit-infra-domains.xml",
    "reports/junit/unit-infra-observability.xml",
    "reports/junit/unit-infra-rendering.xml",
    "reports/junit/unit-infra-lab.xml",
    "reports/junit/unit-infra-lab_agent.xml",
    "reports/junit/unit-infra-api.xml",
    "reports/junit/unit-infra-cli.xml",
    "reports/junit/unit-infra-views.xml",
    "reports/junit/unit-infra-perf.xml",
    "reports/junit/unit-infra-entity.xml",
    "reports/junit/unit-infra-entities.xml",
    "reports/junit/unit-infra-cognition.xml",
    "reports/junit/unit-infra-docs.xml",
    "reports/junit/unit-infra-certification.xml",
    "reports/junit/unit-infra-tools.xml",
    "reports/junit/unit-infra-test_memory_probe.xml",
    "reports/junit/unit-infra-test_queue_worker_singleton.xml",
]

UNIT_INFRA_MERGED_PATH = "reports/junit/unit-infra.xml"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", default=UNIT_INFRA_MERGED_PATH, help="Path to write the merged JUnit XML to",
    )
    parser.add_argument(
        "shard_paths", nargs="*", default=None,
        help="Shard paths to merge; defaults to UNIT_INFRA_SHARD_PATHS if omitted",
    )
    args = parser.parse_args(argv)

    expected = args.shard_paths if args.shard_paths else UNIT_INFRA_SHARD_PATHS
    result = merge_junit_shards(expected, Path(args.out))

    for missing in result.missing_paths:
        print(f"::warning::Merge JUnit XML: shard {missing} missing or unparseable -- its results are absent from the merged report")

    if not result.all_merged:
        print(
            f"::error::Merge JUnit XML: only {len(result.merged_paths)}/{result.expected_count} "
            "shards merged -- see ::warning:: lines above for which ones are missing"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

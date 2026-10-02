"""Craft metrics for the codebase health snapshot: per-dimension counts, never a combined score.

`compute_craft_metrics` is a pure function of the tool findings and the registry rows. The
snapshot (`tools/codebase_health_snapshot.py`) merges its result into each record as a second
metric source next to `codebase_health_baseline.build_report()`; the snapshot only persists these
numbers and does not recompute them.

Two kinds of key, told apart by name:

- live keys (`craft_<thing>`): measured now from ruff, complexipy and the line-count report. These
  are the offline Python tools; a snapshot never needs the network.
- registry-derived keys (`craft_baseline_<thing>`): read from `registries/code_health_exceptions.jsonl`,
  so they describe the baselined state at the last seed or `tighten`, not a live measurement. Duplication
  is reported this way because jscpd needs `npx`; it can become a live key once jscpd has a lockfile.

Every key is a plain integer. There is deliberately no aggregate: each dimension trends on its own
(docs/audits/D24_codebase_health_observatory.md sections J and M).
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Iterable, Sequence

from tools.code_health import registry, scan
from tools.code_health.adapters import RULE_DUPLICATE
from tools.code_health.findings import (
    TOOL_COMPLEXIPY,
    TOOL_JSCPD,
    TOOL_LINE_COUNT,
    TOOL_RUFF,
    Finding,
)
from tools.code_health.registry import Row

LIVE_KEYS = (
    "craft_ruff_findings",
    "craft_correctness_findings",
    "craft_missing_public_docstrings",
    "craft_missing_annotations",
    "craft_functions_over_cognitive_limit",
    "craft_functions_over_length_limit",
    "craft_classes_over_length_limit",
    "craft_modules_over_length_limit",
    "craft_longest_function_lines",
    "craft_highest_cognitive_complexity",
)
REGISTRY_KEYS = (
    "craft_baseline_rows",
    "craft_baseline_unreviewed_rows",
    "craft_baseline_duplicate_file_pairs",
    "craft_baseline_duplicated_lines",
)
CRAFT_METRIC_KEYS = LIVE_KEYS + REGISTRY_KEYS

CRAFT_LABELS = {
    "craft_ruff_findings": "Craft: ruff findings (standard's rules)",
    "craft_correctness_findings": "Craft: pyflakes/syntax findings",
    "craft_missing_public_docstrings": "Craft: public items without a docstring",
    "craft_missing_annotations": "Craft: missing type annotations",
    "craft_functions_over_cognitive_limit": "Craft: functions over cognitive limit",
    "craft_functions_over_length_limit": "Craft: functions over length limit",
    "craft_classes_over_length_limit": "Craft: classes over length limit",
    "craft_modules_over_length_limit": "Craft: modules over length limit",
    "craft_longest_function_lines": "Craft: longest function (lines)",
    "craft_highest_cognitive_complexity": "Craft: highest cognitive complexity",
    "craft_baseline_rows": "Craft: baseline rows (registry)",
    "craft_baseline_unreviewed_rows": "Craft: baseline rows not reviewed (registry)",
    "craft_baseline_duplicate_file_pairs": "Craft: duplicated file pairs (registry)",
    "craft_baseline_duplicated_lines": "Craft: duplicated lines (registry)",
}

_DOCSTRING_RULES = ("D100", "D101", "D102", "D103", "D104")


def _ruff_total(findings: Iterable[Finding], prefixes: tuple[str, ...] = ("",)) -> int:
    """The number of ruff findings whose rule code starts with any of `prefixes` (default: all)."""
    return sum(f.value for f in findings if f.tool == TOOL_RUFF and f.rule.startswith(prefixes))


def _count(findings: Iterable[Finding], tool: str, rule: str) -> int:
    return sum(1 for f in findings if f.tool == tool and f.rule == rule)


def _largest(findings: Iterable[Finding], tool: str, rule: str) -> int:
    return max((f.value for f in findings if f.tool == tool and f.rule == rule), default=0)


def compute_craft_metrics(findings: Sequence[Finding], rows: Sequence[Row]) -> dict[str, int]:
    """One integer per key in `CRAFT_METRIC_KEYS`, from live `findings` and the registry `rows`."""
    duplicates = [row for row in rows if row.tool == TOOL_JSCPD and row.rule == RULE_DUPLICATE]
    return {
        "craft_ruff_findings": _ruff_total(findings),
        "craft_correctness_findings": _ruff_total(findings, ("F", "E9")),
        "craft_missing_public_docstrings": _ruff_total(findings, _DOCSTRING_RULES),
        "craft_missing_annotations": _ruff_total(findings, ("ANN",)),
        "craft_functions_over_cognitive_limit": _count(findings, TOOL_COMPLEXIPY, "cognitive-complexity"),
        "craft_functions_over_length_limit": _count(findings, TOOL_LINE_COUNT, "function-length"),
        "craft_classes_over_length_limit": _count(findings, TOOL_LINE_COUNT, "class-length"),
        "craft_modules_over_length_limit": _count(findings, TOOL_LINE_COUNT, "module-length"),
        "craft_longest_function_lines": _largest(findings, TOOL_LINE_COUNT, "function-length"),
        "craft_highest_cognitive_complexity": _largest(findings, TOOL_COMPLEXIPY, "cognitive-complexity"),
        "craft_baseline_rows": len(rows),
        "craft_baseline_unreviewed_rows": sum(1 for row in rows if not row.reviewed),
        "craft_baseline_duplicate_file_pairs": len(duplicates),
        "craft_baseline_duplicated_lines": sum(row.value for row in duplicates),
    }


def measure_craft_metrics(root: Path) -> dict[str, int]:
    """Run the offline tools over `root`'s `src/` and read its registry (a missing registry is empty)."""
    with tempfile.TemporaryDirectory() as scratch:
        out_dir = Path(scratch)
        scan.run_scan(root, out_dir, tools=scan.OFFLINE_TOOLS)
        findings = scan.collect_findings(out_dir, root, tools=scan.OFFLINE_TOOLS)
    rows = registry.load_rows(registry.registry_path(root), root, check_files=False)
    return compute_craft_metrics(findings, rows)

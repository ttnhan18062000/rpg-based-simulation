"""
Architecture report: categorise all remaining direct Faction.*/EntityRole.* enum usage in src/.

Categories:
  forbidden_new         — in FORBIDDEN_MODULES; must be empty (CI gate)
  compatibility_projection — in compat adapter modules; intentional bridge code
  allowed_legacy_fallback  — in runtime modules with data-model-layer enum assignments
  allowed_test_only        — in test harness / perf / certification modules
  migration_target         — all other allowed runtime modules; should be cleaned over time

Each entry carries: file, line, enum symbol, category, suggested replacement, migration status.

This test:
  - FAILS if forbidden_new is non-empty (hard gate)
  - PASSES with a printed report for all other categories
  - PASSES if report can be generated at all
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

import pytest

pytestmark = pytest.mark.architecture

_SRC_ROOT = Path("src")
_TESTS_ROOT = Path("tests")

_ENUM_USAGE_PATTERN = re.compile(
    r'\b(Faction|EntityRole)\.[A-Z_][A-Z_0-9]*\b'
)

# ---------------------------------------------------------------------------
# Category maps — relative paths from src/
# ---------------------------------------------------------------------------

_FORBIDDEN = frozenset({
    "content_semantics/relation.py",
    "content/repository.py",
    "content/paths.py",
    "content/pack_manifest.py",
    "content/validator.py",
    "content/schema.py",
    "content/resolver.py",
})

_COMPAT_ADAPTERS = frozenset({
    "content_semantics/faction.py",
    "content_semantics/role.py",
    "entities/identity_resolver.py",
})

_LEGACY_FALLBACK_RUNTIME = frozenset({
    # Data-model-layer enum assignments (owner_faction_id_set is Optional[int])
    "world/influence.py",
    "engine/world_dynamics.py",
    # Legacy fallback path inside classifier
    "world/region_threat_classifier.py",
})

_TEST_HARNESSES = frozenset({
    "perf/scenarios.py",
    "perf/governance_scenarios.py",
    "certification/scenarios.py",
})

_REPLACEMENT_MAP = {
    "Faction": "EntityIdentityResolver.resolve(entity).faction_id + FactionSemanticsService.is_invader()/is_protector()",
    "EntityRole": "EntityIdentityResolver.resolve(entity).role_id",
}


class EnumUsageEntry(NamedTuple):
    file: str
    line: int
    enum_symbol: str
    category: str
    suggested_replacement: str
    migration_status: str


def _categorise(rel: str) -> str:
    if rel in _FORBIDDEN:
        return "forbidden_new"
    if rel in _COMPAT_ADAPTERS:
        return "compatibility_projection"
    if rel in _LEGACY_FALLBACK_RUNTIME:
        return "allowed_legacy_fallback"
    if rel in _TEST_HARNESSES:
        return "allowed_test_only"
    # Skip enum definition file
    if rel == "core/enums.py":
        return "skip"
    return "migration_target"


def _migration_status(category: str) -> str:
    return {
        "forbidden_new": "VIOLATION",
        "compatibility_projection": "intentional_bridge",
        "allowed_legacy_fallback": "data_model_constraint",
        "allowed_test_only": "test_harness_only",
        "migration_target": "pending",
    }.get(category, "unknown")


def _build_report() -> list[EnumUsageEntry]:
    entries = []
    for root, label in [(_SRC_ROOT, "src"), (_TESTS_ROOT, "tests")]:
        for py_file in sorted(root.rglob("*.py")):
            if "__pycache__" in py_file.parts:
                continue
            try:
                rel = str(py_file.relative_to(_SRC_ROOT))
                is_test_file = False
            except ValueError:
                rel = str(py_file.relative_to(_TESTS_ROOT))
                is_test_file = True

            text = py_file.read_text(encoding="utf-8")
            for line_no, line in enumerate(text.splitlines(), start=1):
                stripped = line.strip()
                if stripped.startswith("from ") or stripped.startswith("import "):
                    continue
                for m in _ENUM_USAGE_PATTERN.finditer(line):
                    enum_class = m.group(1)
                    symbol = m.group(0)
                    if is_test_file:
                        category = "allowed_test_only"
                    else:
                        category = _categorise(rel)
                    if category == "skip":
                        continue
                    entries.append(EnumUsageEntry(
                        file=f"{'tests/' if is_test_file else 'src/'}{rel}",
                        line=line_no,
                        enum_symbol=symbol,
                        category=category,
                        suggested_replacement=_REPLACEMENT_MAP.get(enum_class, "use catalog semantics"),
                        migration_status=_migration_status(category),
                    ))
    return entries


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_report_can_be_generated():
    """Smoke: report generation must not raise."""
    report = _build_report()
    assert isinstance(report, list)


def test_forbidden_category_is_empty():
    """Hard gate: no direct enum usage is allowed in FORBIDDEN_MODULES.

    If this fails:
      Use EntityIdentityResolver or FactionSemanticsService instead.
    """
    report = _build_report()
    violations = [e for e in report if e.category == "forbidden_new"]
    assert not violations, (
        f"{len(violations)} enum usage(s) in FORBIDDEN modules:\n"
        + "\n".join(f"  {e.file}:{e.line} — {e.enum_symbol}" for e in violations)
    )


def test_allowed_categories_are_non_empty():
    """Allowed categories must be explicitly represented (proves scan is working)."""
    report = _build_report()
    categories_found = {e.category for e in report}
    # compatibility_projection and migration_target must always be present during migration
    assert "compatibility_projection" in categories_found, (
        "No compatibility_projection entries found — scan may be broken."
    )
    assert "migration_target" in categories_found, (
        "No migration_target entries found — either migration is complete (update this test) "
        "or the scan is broken."
    )


def test_report_distinguishes_test_from_runtime(capsys):
    """Report must cover both src/ and tests/ entries, and they must be distinguishable."""
    report = _build_report()
    src_entries = [e for e in report if e.file.startswith("src/")]
    test_entries = [e for e in report if e.file.startswith("tests/")]
    assert src_entries, "Report found no src/ entries — scan is broken."
    assert test_entries, "Report found no tests/ entries — scan is broken or tests use no enums."


def test_print_migration_report(capsys):
    """Prints the full categorised migration report. Non-failing informational output."""
    report = _build_report()

    from collections import defaultdict
    by_category: dict[str, list[EnumUsageEntry]] = defaultdict(list)
    for e in report:
        by_category[e.category].append(e)

    order = [
        "forbidden_new",
        "migration_target",
        "allowed_legacy_fallback",
        "compatibility_projection",
        "allowed_test_only",
    ]

    lines = ["\n=== Enum Migration Backlog Report ==="]
    for cat in order:
        entries = by_category.get(cat, [])
        lines.append(f"\n[{cat.upper()}] ({len(entries)} occurrences)")
        for e in entries[:10]:
            lines.append(f"  {e.file}:{e.line}  {e.enum_symbol}  status={e.migration_status}")
        if len(entries) > 10:
            lines.append(f"  ... and {len(entries) - 10} more")

    total = len(report)
    forbidden_count = len(by_category.get("forbidden_new", []))
    lines.append(f"\nTotal: {total} usages across {len(by_category)} categories")
    lines.append(f"Forbidden violations: {forbidden_count} (must be 0)")
    print("\n".join(lines))

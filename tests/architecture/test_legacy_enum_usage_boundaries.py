"""
Architecture guard: prevent direct Faction.* / EntityRole.* enum usage from spreading into
clean catalog-driven modules while migration is ongoing.

Strategy:
  - Scan src/ for files containing direct Faction.<MEMBER> or EntityRole.<MEMBER> references
  - FORBIDDEN_MODULES must have zero occurrences — any hit is an architecture violation
  - ALLOWED_MODULES may have occurrences (allowlisted during migration)
  - Any src/ module with violations that is in NEITHER list is an untracked migration target
    (reported but does NOT fail CI — added here to force explicit categorisation over time)

When removing an enum from an allowed module (migration complete):
  - Remove it from ALLOWED_MODULES
  - The test will automatically enforce it stays clean

When a forbidden module gains a violation:
  - The test fails with a message naming the file and suggesting the replacement path
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import FrozenSet

import pytest

pytestmark = pytest.mark.architecture

_SRC_ROOT = Path("src")

# Matches direct member access: Faction.SOMETHING or EntityRole.SOMETHING
# Does not match import statements or type annotations that only mention the class name.
_ENUM_USAGE_PATTERN = re.compile(
    r'\b(Faction|EntityRole)\.[A-Z_][A-Z_0-9]*\b'
)

# ---------------------------------------------------------------------------
# Allowlist — enum usage PERMITTED during migration
# Comment each entry with why it legitimately uses the enum.
# ---------------------------------------------------------------------------
ALLOWED_MODULES: FrozenSet[str] = frozenset({
    # Enum definitions — source of truth
    "core/enums.py",
    # Compatibility adapters — exist to bridge old enum world to clean catalog world
    "content_semantics/faction.py",
    "content_semantics/role.py",
    "entities/identity_resolver.py",          # compatibility projection map tables
    # Legacy world assembly — builds entities using enum factions during migration
    "worldbuilding/compiler.py",
    "worldassembly/resolver.py",
    # Performance / certification scenario harnesses — run in legacy_fallback mode
    "perf/scenarios.py",
    "perf/governance_scenarios.py",
    "certification/scenarios.py",
    # World systems — still use enum for entity spawning (migration target, not yet cleaned)
    "systems/world_systems/generator.py",
    "systems/world_systems/routine.py",
    "systems/world_systems/quest_generator.py",
    # World domain — legacy classification or data-model-layer enum assignments
    "world/influence.py",                      # owner_faction_id_set is Optional[int] (data model)
    "world/spawn.py",
    "world/environment.py",
    "world/camp.py",
    "world/regional_sovereignty.py",
    "world/region_threat_classifier.py",       # legacy fallback path inside classifier
    # Engine — active migration targets or data-model-layer assignments
    "engine/world_dynamics.py",               # owner_faction_id_set assignments (data model)
    "engine/combat_rewards.py",
    "engine/combat.py",
    "engine/legality.py",
    "engine/occupancy_snapshot.py",
    "engine/evolution.py",
    # TCK-20260824-OCCUPATION-CHANGE-TRIGGER — reads EntityRole.CITIZEN/SHOPKEEPER/WORKER/GUARD
    # directly to gate and pick the occupation-change destination role.
    "ai/goals/occupation_change_scorer.py",
})

# ---------------------------------------------------------------------------
# Forbidden list — must have ZERO direct enum usage
# These modules are clean catalog-driven code; enum coupling must never appear here.
# ---------------------------------------------------------------------------
FORBIDDEN_MODULES: FrozenSet[str] = frozenset({
    # Clean relation projection — uses string faction IDs only
    "content_semantics/relation.py",
    # Catalog / content pack infrastructure — purely data-loading, no enum logic
    "content/repository.py",
    "content/paths.py",
    "content/pack_manifest.py",
    "content/validator.py",
    "content/schema.py",
    "content/resolver.py",
})


def _relative_src_path(path: Path) -> str:
    return str(path.relative_to(_SRC_ROOT))


def _scan_enum_usages():
    """Yield (relative_path, line_no, line_text) for each Faction./EntityRole. hit in src/."""
    for py_file in sorted(_SRC_ROOT.rglob("*.py")):
        if "__pycache__" in py_file.parts:
            continue
        rel = _relative_src_path(py_file)
        text = py_file.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            # Skip import lines — we only care about usage sites
            stripped = line.strip()
            if stripped.startswith("from ") or stripped.startswith("import "):
                continue
            if _ENUM_USAGE_PATTERN.search(line):
                yield rel, line_no, line.rstrip()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_forbidden_modules_have_no_direct_enum_usage():
    """Modules in FORBIDDEN_MODULES must contain zero direct Faction.*/EntityRole.* references.

    If this test fails:
      - Remove the direct enum comparison
      - Use EntityIdentityResolver + FactionSemanticsService.is_invader()/is_protector() instead
      - Or use get_faction_id_str(entity) as a compat bridge for runtime entity lookups
    """
    violations: list[str] = []
    for rel, line_no, line_text in _scan_enum_usages():
        if rel in FORBIDDEN_MODULES:
            violations.append(
                f"  {rel}:{line_no}: {line_text.strip()}\n"
                f"    → Use EntityIdentityResolver or FactionSemanticsService instead of direct enum"
            )

    assert not violations, (
        f"Found {len(violations)} direct enum usage(s) in FORBIDDEN modules:\n"
        + "\n".join(violations)
    )


def test_allowed_list_is_not_empty():
    """Smoke test: allowlist must be non-empty (proves the test is actually enforcing something)."""
    assert len(ALLOWED_MODULES) > 0


def test_forbidden_list_is_not_empty():
    """Smoke test: forbidden list must be non-empty (proves the guard covers real modules)."""
    assert len(FORBIDDEN_MODULES) > 0


def test_forbidden_modules_exist_as_files():
    """Every FORBIDDEN_MODULES entry must exist as a real file (detects stale path entries)."""
    missing = [
        mod for mod in FORBIDDEN_MODULES
        if not (_SRC_ROOT / mod).is_file()
    ]
    # Only flag modules that exist — new modules added to forbidden list before their file
    # is created is an ordering issue, not a violation. But stale paths ARE violations.
    stale = [mod for mod in missing if not (_SRC_ROOT / mod).exists()]
    assert not stale, (
        f"FORBIDDEN_MODULES entries no longer exist as files: {stale}\n"
        "Remove them from FORBIDDEN_MODULES."
    )


def test_scan_finds_enum_usages_in_known_allowed_module():
    """Smoke test: scan must find at least one usage in a known allowed module.

    Fails if the regex is broken or all allowed modules have already been cleaned.
    """
    found_in_allowed = {
        rel
        for rel, _, _ in _scan_enum_usages()
        if rel in ALLOWED_MODULES
    }
    assert found_in_allowed, (
        "Scan found zero Faction./EntityRole. usages in ALLOWED_MODULES. "
        "Either the regex is broken or the allowlist is stale (all modules cleaned — update it)."
    )


def test_report_untracked_migration_targets(capsys):
    """Non-failing report: prints src/ modules with enum usage that are in neither list.

    These are untracked migration targets. Each should eventually be moved to
    ALLOWED_MODULES (if legitimate legacy use) or cleaned (if new code that slipped in).
    This test never fails — it only prints a warning.
    """
    untracked: dict[str, list[tuple[int, str]]] = {}
    for rel, line_no, line_text in _scan_enum_usages():
        if rel not in ALLOWED_MODULES and rel not in FORBIDDEN_MODULES:
            untracked.setdefault(rel, []).append((line_no, line_text.strip()))

    if untracked:
        print(
            f"\nWARNING: {len(untracked)} untracked migration target(s) "
            f"with direct enum usage (not in ALLOWED or FORBIDDEN list):\n"
        )
        for rel, hits in sorted(untracked.items()):
            print(f"  {rel}:")
            for line_no, text in hits[:3]:
                print(f"    line {line_no}: {text}")
            if len(hits) > 3:
                print(f"    ... and {len(hits) - 3} more")

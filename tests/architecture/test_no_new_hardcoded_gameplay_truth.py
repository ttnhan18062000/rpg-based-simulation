"""
Architecture guard: no new gameplay content IDs may be added to hardcoded Python fallback maps
without a corresponding entry in data/content/compatibility/migration_map.yaml.

Scan strategy:
  - Look for dict-literal-style gameplay ID definitions in src/**/*.py
    Pattern: "id_string": XxxDef( where Xxx is Item/Resource/Enemy/Recipe/Service/Region
  - Cross-reference against migration_map.yaml (authoritative allow list)
  - Remaining IDs must appear in KNOWN_HARDCODED_BASELINE (pre-existing, grandfathered content)
  - Any ID in neither set is a new violation

KNOWN_HARDCODED_BASELINE documents pre-existing content that predates the migration map
and is not yet tracked there. Adding an ID to KNOWN_HARDCODED_BASELINE requires a comment
explaining why it is not in the migration map. Prefer migration_map entries for new
tracking rather than growing this baseline.
"""

import re
from pathlib import Path
from typing import FrozenSet, Tuple

import pytest
import yaml

pytestmark = pytest.mark.architecture

_MIGRATION_MAP_PATH = Path("data/content/compatibility/migration_map.yaml")
_SRC_ROOT = Path("src")

# Regex matches dict-literal-style gameplay IDs (not variable-keyed assignments).
# Example match: `    "rusted_sword": ItemDef(` — captured: ("rusted_sword", "Item")
# Non-match: `    items[item_id] = ItemDef(` — variable key, not a literal
_DICT_LITERAL_PATTERN = re.compile(
    r'^\s+"([\w_]+)"\s*:\s*(Item|Resource|Enemy|Recipe|Service|Region)Def\s*\(',
    re.MULTILINE,
)

_DEF_TO_LEGACY_FAMILY = {
    "Item": "item",
    "Resource": "resource",
    "Enemy": "enemy",
    "Recipe": "recipe",
    "Service": "service",
    "Region": "region",
}

# Pre-existing hardcoded IDs that predate the migration map and are grandfathered in.
# Do NOT add new IDs here without a comment explaining why they are not in migration_map.yaml.
# Prefer adding to migration_map.yaml instead.
KNOWN_HARDCODED_BASELINE: FrozenSet[Tuple[str, str]] = frozenset({
    # Items — material/loot drops; catalog-backed but also in legacy fallback for redundancy
    ("wood", "item"),
    ("iron_ore", "item"),
    ("beast_fang", "item"),
    ("wolf_pelt", "item"),
    ("moon_resin", "item"),
    ("crystal_shard", "item"),
    ("goblin_token", "item"),
    ("ancient_fragment", "item"),
    ("healing_flower", "item"),
    # Items — craftable equipment not yet deprecated-tracked in migration_map
    ("iron_sword", "item"),
    ("hunter_blade", "item"),
    ("small_potion", "item"),    # migration_map tracks (small_potion, recipe); this is the item entry
    ("travel_ration", "item"),
    ("repair_kit", "item"),
    # Enemies — base world creatures; entries below now tracked via migration_map.yaml
})


def _load_migration_map_allowed() -> FrozenSet[Tuple[str, str]]:
    """Returns frozenset of (legacy_id, legacy_family) from migration_map.yaml."""
    with open(_MIGRATION_MAP_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return frozenset(
        (e["legacy_id"], e["legacy_family"])
        for e in data.get("entries", [])
    )


def _scan_src_dict_literal_ids():
    """Yields (file_path, id_string, legacy_family) for each dict-literal gameplay ID in src/."""
    for py_file in sorted(_SRC_ROOT.rglob("*.py")):
        if "__pycache__" in py_file.parts:
            continue
        text = py_file.read_text(encoding="utf-8")
        for m in _DICT_LITERAL_PATTERN.finditer(text):
            yield py_file, m.group(1), _DEF_TO_LEGACY_FAMILY[m.group(2)]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_migration_map_exists():
    assert _MIGRATION_MAP_PATH.is_file(), (
        f"migration_map.yaml not found at {_MIGRATION_MAP_PATH}. "
        "Create it via TCK-20260609-MIGRATION-MAP-YAML."
    )


def test_no_new_hardcoded_gameplay_ids_without_migration_map_entry():
    """New dict-literal gameplay IDs in src/ must appear in migration_map.yaml.

    If an existing ID is not in migration_map.yaml it must be in KNOWN_HARDCODED_BASELINE.
    Any ID in NEITHER set is an architecture violation.
    """
    migration_allowed = _load_migration_map_allowed()
    violations = []

    for file_path, legacy_id, legacy_family in _scan_src_dict_literal_ids():
        key = (legacy_id, legacy_family)
        if key not in migration_allowed and key not in KNOWN_HARDCODED_BASELINE:
            violations.append(
                f"  {file_path}:{legacy_id!r} ({legacy_family}) — "
                f"add to data/content/compatibility/migration_map.yaml "
                f"with legacy_family={legacy_family!r}"
            )

    assert not violations, (
        f"Found {len(violations)} hardcoded gameplay ID(s) not in migration_map.yaml "
        f"or KNOWN_HARDCODED_BASELINE:\n" + "\n".join(violations)
    )


def test_scan_finds_expected_fallback_families():
    """Smoke test: scan must detect IDs in all six expected families.

    Fails if the regex is broken or the fallback maps were removed.
    """
    found_families = {family for _, _, family in _scan_src_dict_literal_ids()}
    required = {"item", "resource", "enemy", "recipe", "service", "region"}
    missing = required - found_families
    assert not missing, (
        f"Scan found no hardcoded IDs for families: {sorted(missing)}. "
        "Either fallback maps were removed or the regex is broken."
    )


def test_scan_finds_known_fallback_ids():
    """Smoke test: specific known IDs must be detected by the scan."""
    found = {(id_, fam) for _, id_, fam in _scan_src_dict_literal_ids()}
    expected = {
        ("rusted_sword", "item"),
        ("node_wood", "resource"),
        ("wolf", "enemy"),
        ("small_potion", "recipe"),
        ("shop_hometown", "service"),
        ("hometown", "region"),
    }
    missing = expected - found
    assert not missing, (
        f"Scan did not detect expected fallback IDs: {sorted(missing)}. "
        "Regex may be broken or fallback maps were restructured."
    )


def test_known_baseline_stale_guard():
    """If a KNOWN_HARDCODED_BASELINE entry gains a migration_map entry, remove it from baseline.

    This prevents the baseline from growing stale over time. A KNOWN_HARDCODED_BASELINE
    entry that is now tracked in migration_map.yaml should be removed from this file.
    """
    migration_allowed = _load_migration_map_allowed()
    stale = [
        key for key in KNOWN_HARDCODED_BASELINE if key in migration_allowed
    ]
    assert not stale, (
        f"{len(stale)} KNOWN_HARDCODED_BASELINE entries are now in migration_map.yaml. "
        "Remove them from KNOWN_HARDCODED_BASELINE:\n"
        + "\n".join(f"  {id_!r} ({fam})" for id_, fam in sorted(stale))
    )

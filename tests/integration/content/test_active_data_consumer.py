"""
Active data consumer gate.

Scans content YAML files for STATE markers and asserts that every record
marked EXISTING-LOGIC, LEGACY-EXPORT, or REDESIGNED-CORE has at least one
consumer path (an incoming edge in the content reference graph, or an explicit
exemption for families whose consumers are not tracked in the graph).

Records marked ADDITIONAL or FUTURE-EXTENSION are allowed to be inactive.

Failure messages include: family, record ID, and which consumer path is missing.

Known pre-existing gaps (content with no current consumer) are captured in
KNOWN_INACTIVE_CONTENT so the gate turns red only on NEW violations.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest

pytestmark = pytest.mark.content_graph

from src.content.reference_graph import ContentReferenceGraph, FAMILY_TO_SHORT
from src.content.repository import CatalogRepository, CANONICAL_FAMILIES
from src.worldmodules.repository import WorldModuleRepository

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONTENT_BASE = Path("data/content")

ACTIVE_STATES = frozenset({"EXISTING-LOGIC", "LEGACY-EXPORT", "REDESIGNED-CORE"})
INACTIVE_STATES = frozenset({"ADDITIONAL", "FUTURE-EXTENSION"})

# Families consumed via implicit runtime mechanisms, not reference graph edges.
# attribute / element: foundation types used by the attribute/combat system at
#   runtime but never explicitly cited in catalog cross-references.
# perspective: referenced via compositions' default_perspectives string field,
#   which the reference graph does not convert to typed edges.
# projection: compatibility projections consumed implicitly by catalog seeding.
FAMILIES_WITH_IMPLICIT_CONSUMERS = frozenset({
    "attribute",
    "element",
    "perspective",
    "projection",
})

# Pre-existing content orphans — records that are active (EXISTING-LOGIC /
# LEGACY-EXPORT / REDESIGNED-CORE) but currently have no proven consumer path.
# These are documented gaps, not exemptions: the intent is that they will be
# connected or reclassified in a future ticket. The gate turns red for any
# violation NOT in this set.
KNOWN_INACTIVE_CONTENT: frozenset[Tuple[str, str]] = frozenset({
    ("faction", "neutral"),              # EXISTING-LOGIC faction; no module or archetype references it
    ("role", "shopkeeper"),              # no archetype or module references this role
    ("stat_profile", "monster_base"),    # legacy profile; no archetype uses it
    ("item", "apprentice_staff"),        # LEGACY-EXPORT item; no inventory profile references it
    ("item", "basic_bow"),
    ("item", "herb"),
    ("item", "leather_armor"),
    ("item", "rusted_sword"),
    ("item", "wooden_staff"),
    ("recipe", "craft_small_potion"),    # LEGACY-EXPORT recipe; no consumer path
    ("skill_profile", "warrior_skills"), # LEGACY-EXPORT; no archetype uses this profile
})

# ---------------------------------------------------------------------------
# Helpers: path → family mapping
# ---------------------------------------------------------------------------

def _build_path_to_short_family(content_base: Path = CONTENT_BASE) -> Dict[Path, str]:
    """Map catalog YAML file paths to their reference-graph short family names."""
    mapping: Dict[Path, str] = {}
    for spec in CANONICAL_FAMILIES:
        short = FAMILY_TO_SHORT.get(spec.family)
        if not short:
            continue
        parts = spec.family.split(".")
        if len(parts) == 2:
            yaml_path = content_base / parts[0] / f"{parts[1]}.yaml"
        elif len(parts) == 1:
            yaml_path = content_base / f"{parts[0]}.yaml"
        else:
            continue
        mapping[yaml_path] = short
    return mapping


# ---------------------------------------------------------------------------
# Helpers: STATE marker parsing
# ---------------------------------------------------------------------------

def _parse_state_markers_from_file(path: Path) -> List[Tuple[str, str]]:
    """
    Parse (record_id, state_marker) pairs from a YAML file.

    Uses a sticky-state approach: a `# STATE: X` comment sets the current state
    and applies to all following `id:` fields until the next `# STATE:` comment.
    Handles both file-level markers (at the top, applying to all records) and
    per-record markers (before each list entry).
    """
    results: List[Tuple[str, str]] = []
    current_state: Optional[str] = None

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            state_match = re.match(r"#\s*STATE:\s*(\S+)", stripped)
            if state_match:
                current_state = state_match.group(1)
                continue
            if current_state:
                id_match = re.match(
                    r"^-?\s*id:\s*[\"']?([^\"':\s#]+)[\"']?\s*(?:#.*)?$", stripped
                )
                if id_match:
                    results.append((id_match.group(1).strip(), current_state))
    return results


def scan_state_marked_records(content_base: Path = CONTENT_BASE) -> List[Tuple[str, str, str]]:
    """
    Scan all catalog YAML files and return a list of
    (short_family, record_id, state_marker) for every STATE-marked record.
    """
    path_to_family = _build_path_to_short_family(content_base)
    results: List[Tuple[str, str, str]] = []
    for yaml_path, short_family in path_to_family.items():
        if not yaml_path.is_file():
            continue
        for record_id, state in _parse_state_markers_from_file(yaml_path):
            results.append((short_family, record_id, state))
    return results


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def catalog() -> CatalogRepository:
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


@pytest.fixture(scope="module")
def module_repo() -> WorldModuleRepository:
    repo = WorldModuleRepository()
    repo.load_all()
    return repo


@pytest.fixture(scope="module")
def ref_graph(catalog, module_repo) -> ContentReferenceGraph:
    modules = list(module_repo.modules.values())
    return ContentReferenceGraph(repo=catalog, modules=modules)


@pytest.fixture(scope="module")
def state_marked_records() -> List[Tuple[str, str, str]]:
    return scan_state_marked_records()


# ---------------------------------------------------------------------------
# Gate tests
# ---------------------------------------------------------------------------

def test_active_records_have_consumer_paths(ref_graph, state_marked_records):
    """
    Every record with state EXISTING-LOGIC, LEGACY-EXPORT, or REDESIGNED-CORE
    must have at least one consumer path tracked in the reference graph — unless
    it is in KNOWN_INACTIVE_CONTENT (pre-existing documented gap) or its family
    is in FAMILIES_WITH_IMPLICIT_CONSUMERS.

    This gate turns red for any NEW violation not in the known-gaps baseline.
    """
    new_violations: List[str] = []

    for short_family, record_id, state in state_marked_records:
        if state not in ACTIVE_STATES:
            continue
        if short_family in FAMILIES_WITH_IMPLICIT_CONSUMERS:
            continue
        if (short_family, record_id) in KNOWN_INACTIVE_CONTENT:
            continue  # documented pre-existing gap

        node_id = f"{short_family}:{record_id}"
        if not ref_graph.has_node(node_id):
            continue  # not indexed by reference graph; skip

        if not ref_graph.is_record_used(node_id):
            new_violations.append(
                f"  [{state}] {short_family}:{record_id} — "
                f"no incoming reference edges (no resolver/compile/composition/module consumer)"
            )

    assert not new_violations, (
        f"{len(new_violations)} active content record(s) have no consumer path "
        f"(beyond known pre-existing gaps):\n"
        + "\n".join(sorted(new_violations))
    )


def test_known_gaps_are_genuinely_inactive(ref_graph):
    """
    Verify that records in KNOWN_INACTIVE_CONTENT actually have no consumer path.
    If a known gap gains a consumer, remove it from KNOWN_INACTIVE_CONTENT.
    """
    stale_entries: List[str] = []

    for short_family, record_id in KNOWN_INACTIVE_CONTENT:
        node_id = f"{short_family}:{record_id}"
        if not ref_graph.has_node(node_id):
            continue
        if ref_graph.is_record_used(node_id):
            stale_entries.append(
                f"  {short_family}:{record_id} now HAS a consumer — "
                f"remove it from KNOWN_INACTIVE_CONTENT"
            )

    assert not stale_entries, (
        f"{len(stale_entries)} known-gap entry/entries are now consumed and should be removed:\n"
        + "\n".join(stale_entries)
    )


def test_inactive_state_records_not_confused_with_active(state_marked_records):
    """
    Records with ADDITIONAL or FUTURE-EXTENSION state must NOT overlap with
    active-state records (same family + id cannot have two conflicting states).
    """
    active_ids = {(fam, rid) for fam, rid, state in state_marked_records if state in ACTIVE_STATES}
    inactive_ids = {(fam, rid) for fam, rid, state in state_marked_records if state in INACTIVE_STATES}
    overlap = active_ids & inactive_ids
    assert not overlap, (
        f"These records have conflicting state markers (both active and inactive):\n"
        + "\n".join(f"  {fam}:{rid}" for fam, rid in sorted(overlap))
    )


def test_state_marked_records_are_parsed(state_marked_records):
    """Sanity check: the scanner must find a non-trivial number of active records."""
    active = [r for r in state_marked_records if r[2] in ACTIVE_STATES]
    assert len(active) > 10, (
        f"Expected >10 active state-marked records; found {len(active)}. "
        "State marker scanner may be broken."
    )


def test_implicit_consumer_families_are_scanned(state_marked_records):
    """
    Families in FAMILIES_WITH_IMPLICIT_CONSUMERS should appear in scan results
    to confirm the exemption is not vacuous. Perspectives.yaml has REDESIGNED-CORE.
    """
    exempt_found = {
        fam
        for fam, _, state in state_marked_records
        if fam in FAMILIES_WITH_IMPLICIT_CONSUMERS and state in ACTIVE_STATES
    }
    assert "perspective" in exempt_found, (
        "No perspective records found with active state — check scanner or perspectives.yaml"
    )

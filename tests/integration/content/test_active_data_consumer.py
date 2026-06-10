"""
Active data consumer gate.

Validates that every active content family (as defined in ContentUsageMatrix)
has registered consumer components and at least one consumed record in the
content reference graph.

Uses ContentUsageMatrix as the authoritative source of family-level implementation
status. Does NOT scan YAML comment markers — per Option A (Phase 20-28 repair):
YAML comments are human planning notes only.

Run standalone:
    pytest tests/integration/content/test_active_data_consumer.py -v
"""

from __future__ import annotations

from typing import List, Tuple

import pytest

pytestmark = pytest.mark.content_graph

from src.content.matrix import CONTENT_USAGE_MATRIX
from src.content.reference_graph import ContentReferenceGraph, FAMILY_TO_SHORT
from src.content.repository import CatalogRepository, CANONICAL_FAMILIES
from src.worldmodules.repository import WorldModuleRepository

# ---------------------------------------------------------------------------
# Active states by ContentUsageMatrix definition
# ---------------------------------------------------------------------------

_ACTIVE_IMPL_STATES = frozenset({"RESOLVED_PARTIALLY", "RUNTIME_AUTHORITATIVE"})

# Families whose records are consumed via implicit runtime mechanisms that do
# not produce reference graph edges, or are graph entry points (no inbound edges
# by design). These are exempted from graph-coverage checks.
_GRAPH_EXEMPT_SHORTS = frozenset({
    "attribute", "element", "perspective", "projection",  # implicit runtime consumers
    "defaults",         # entry point: consumers read from it, nothing points to it
    "spawn_table",      # entry point
    "composition",      # entry point
    "scenario",         # entry point
})


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


# ---------------------------------------------------------------------------
# Gate tests
# ---------------------------------------------------------------------------

def test_active_families_have_documented_consumers():
    """
    Every content family with an active implementation_state must have at least
    one documented consumer registered in ContentUsageMatrix
    (resolver_component or compile_runtime_consumer).

    This validates the matrix is properly maintained, not that code is correct.
    """
    violations: List[str] = []

    for family_key, entry in CONTENT_USAGE_MATRIX.items():
        if entry.implementation_state not in _ACTIVE_IMPL_STATES:
            continue
        if not entry.resolver_component and not entry.compile_runtime_consumer:
            violations.append(
                f"  {family_key}: state={entry.implementation_state} "
                f"but no resolver_component or compile_runtime_consumer documented"
            )

    assert not violations, (
        f"{len(violations)} active content families have no documented consumer in ContentUsageMatrix:\n"
        + "\n".join(violations)
    )


def test_active_families_have_graph_coverage(ref_graph):
    """
    For each active content family that appears in the reference graph, at least
    one record in that family must have at least one incoming edge (be consumed
    by something in the reference graph).

    Families in _GRAPH_EXEMPT_SHORTS have implicit consumers outside the graph
    and are exempted from this check.
    """
    violations: List[str] = []

    for family_key, entry in CONTENT_USAGE_MATRIX.items():
        if entry.implementation_state not in _ACTIVE_IMPL_STATES:
            continue

        short = FAMILY_TO_SHORT.get(family_key.replace("/", "."))
        if not short or short in _GRAPH_EXEMPT_SHORTS:
            continue

        family_nodes = [nid for nid in ref_graph.nodes if nid.startswith(f"{short}:")]
        if not family_nodes:
            continue  # family not indexed in this graph build; skip

        consumed = [nid for nid in family_nodes if ref_graph.is_record_used(nid)]
        if not consumed:
            violations.append(
                f"  {family_key} ({short}): {len(family_nodes)} records loaded, "
                f"none have any incoming reference graph edge"
            )

    assert not violations, (
        f"{len(violations)} active content families have no consumed records in the reference graph:\n"
        + "\n".join(violations)
    )


def test_content_usage_matrix_covers_active_catalog_families(catalog):
    """
    ContentUsageMatrix must have an entry for every canonical family loaded by
    CatalogRepository. Matched by file_path to handle cases where the matrix key
    differs from the canonical family's dot-notation name.

    Families missing from the matrix cannot have their implementation state tracked.
    """
    # Build a set of file_paths registered in ContentUsageMatrix
    matrix_paths = {entry.file_path for entry in CONTENT_USAGE_MATRIX.values()}

    missing: List[str] = []
    for spec in CANONICAL_FAMILIES:
        if spec.path not in matrix_paths:
            missing.append(f"  {spec.family} (path: {spec.path})")

    assert not missing, (
        f"{len(missing)} canonical families are missing from ContentUsageMatrix (matched by file_path):\n"
        + "\n".join(missing)
    )

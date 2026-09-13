"""
Tests for TCK-20260627-P2N-DEGRADED-FALLBACK.

Verifies:
  1. Module-level default of runtime_content_source is not "legacy_hardcoded".
  2. CatalogRepository.get_lowest_cost_for_type returns items cheapest-first.

TCK-20260912-OPTIMIZATION-ORPHANED-CAPABILITY-DETERMINATION: `GracefulDegradationManager` (and
`resolve_content_source()`, the "prefer catalog under pressure" capability this file originally
also covered) was deleted -- confirmed to have zero real callers, and the catalog-preference
behavior under pressure was never wired anywhere else in production. `CatalogRepository.
get_lowest_cost_for_type()` itself is real, live, kept code (`src/content/repository.py`) and gets
its own real coverage here independent of the deleted wrapper -- those tests are unaffected by
that deletion and stay.
"""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# 1. Module-level default
# ---------------------------------------------------------------------------

def test_runtime_content_source_module_default_is_not_legacy_hardcoded():
    """The declared module-level default for runtime_content_source must not be 'legacy_hardcoded'.

    This guards against re-introducing the pre-boot default that caused D02 §6.6.
    We parse the source AST so the test is immune to the post-import seeded value.
    """
    src_path = Path("src/core/registries.py")
    source = src_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    # Find module-level assignment: runtime_content_source = <value>
    for node in ast.walk(tree):
        if not isinstance(node, (ast.AnnAssign, ast.Assign)):
            continue
        # AnnAssign covers `runtime_content_source: Optional[str] = None`
        if isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and target.id == "runtime_content_source":
                if node.value is not None:
                    # Must NOT be the string literal "legacy_hardcoded"
                    assert not (
                        isinstance(node.value, ast.Constant)
                        and node.value.value == "legacy_hardcoded"
                    ), (
                        "runtime_content_source module-level default must not be 'legacy_hardcoded'. "
                        "D02 §6.6 fix: change to None."
                    )
                return  # found the declaration, assertion passed
        # Plain Assign covers `runtime_content_source = "legacy_hardcoded"` (old form)
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "runtime_content_source":
                    assert not (
                        isinstance(node.value, ast.Constant)
                        and node.value.value == "legacy_hardcoded"
                    ), (
                        "runtime_content_source module-level default must not be 'legacy_hardcoded'. "
                        "D02 §6.6 fix: change to None."
                    )
                    return

    pytest.fail("Could not find runtime_content_source declaration in src/core/registries.py")


# ---------------------------------------------------------------------------
# 2. CatalogRepository.get_lowest_cost_for_type
# ---------------------------------------------------------------------------

def _make_item_def(base_value: float):
    """Build a minimal ItemDefinition-like mock with the given base_value."""
    obj = MagicMock()
    obj.base_value = base_value
    return obj


def _make_resource_def(required_tool):
    """Build a minimal ResourceDefinition-like mock."""
    obj = MagicMock()
    obj.required_tool = required_tool
    return obj


def test_get_lowest_cost_items_sorted_by_base_value():
    """get_lowest_cost_for_type('items') returns items ordered cheapest-first by base_value."""
    from src.content.repository import CatalogRepository

    repo = CatalogRepository.__new__(CatalogRepository)
    repo.items = {
        "expensive": _make_item_def(100.0),
        "cheap": _make_item_def(1.0),
        "mid": _make_item_def(50.0),
    }
    repo.resources = {}

    result = repo.get_lowest_cost_for_type("items")
    keys = list(result.keys())

    assert keys == ["cheap", "mid", "expensive"], (
        f"Expected cheapest-first order, got: {keys}"
    )


def test_get_lowest_cost_resources_no_tool_first():
    """get_lowest_cost_for_type('resources') returns tool-free entries before tool-required."""
    from src.content.repository import CatalogRepository

    repo = CatalogRepository.__new__(CatalogRepository)
    repo.items = {}
    repo.resources = {
        "node_iron": _make_resource_def("pickaxe"),
        "node_herb": _make_resource_def(None),
        "node_wood": _make_resource_def(None),
    }

    result = repo.get_lowest_cost_for_type("resources")
    keys = list(result.keys())

    # Tool-free first (sorted alphabetically within that group), then tool-required
    assert keys[0] in ("node_herb", "node_wood")
    assert keys[1] in ("node_herb", "node_wood")
    assert keys[2] == "node_iron"


def test_get_lowest_cost_unknown_type_returns_empty():
    """get_lowest_cost_for_type with an unrecognised type returns an empty dict."""
    from src.content.repository import CatalogRepository

    repo = CatalogRepository.__new__(CatalogRepository)
    repo.items = {}
    repo.resources = {}

    result = repo.get_lowest_cost_for_type("nonexistent_type")

    assert result == {}

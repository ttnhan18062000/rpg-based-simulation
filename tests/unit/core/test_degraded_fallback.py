"""
Tests for TCK-20260627-P2N-DEGRADED-FALLBACK.

Verifies:
  1. Module-level default of runtime_content_source is not "legacy_hardcoded".
  2. GracefulDegradationManager.resolve_content_source uses catalog in degraded mode.
  3. GracefulDegradationManager.resolve_content_source raises CatalogMissError in strict mode
     when catalog is absent.
  4. GracefulDegradationManager.resolve_content_source returns {} in non-strict mode when
     catalog is absent.
  5. CatalogRepository.get_lowest_cost_for_type returns items cheapest-first.
"""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.domains.optimization.degradation import (
    CatalogMissError,
    GracefulDegradationManager,
)


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
# 2–4. GracefulDegradationManager.resolve_content_source
# ---------------------------------------------------------------------------

def test_resolve_content_source_degraded_uses_catalog():
    """In degraded mode, resolve_content_source delegates to catalog.get_lowest_cost_for_type."""
    manager = GracefulDegradationManager()
    manager.update_pressure(0.96, 1.0)  # ratio=0.96 → DEGRADED

    catalog = MagicMock()
    catalog.get_lowest_cost_for_type.return_value = {"mock_item": object()}

    result = manager.resolve_content_source(catalog, "items")

    catalog.get_lowest_cost_for_type.assert_called_once_with("items")
    assert "mock_item" in result


def test_resolve_content_source_normal_mode_uses_catalog():
    """In normal mode, resolve_content_source also delegates to catalog (no restriction)."""
    manager = GracefulDegradationManager()
    # default level is NORMAL

    catalog = MagicMock()
    catalog.get_lowest_cost_for_type.return_value = {"item_x": object()}

    result = manager.resolve_content_source(catalog, "resources")

    catalog.get_lowest_cost_for_type.assert_called_once_with("resources")
    assert "item_x" in result


def test_resolve_content_source_strict_raises_on_missing_catalog():
    """strict=True with no catalog must raise CatalogMissError."""
    manager = GracefulDegradationManager()

    with pytest.raises(CatalogMissError, match="strict mode"):
        manager.resolve_content_source(None, "items", strict=True)


def test_resolve_content_source_strict_error_names_content_type():
    """CatalogMissError message must include the requested content_type for traceability."""
    manager = GracefulDegradationManager()

    with pytest.raises(CatalogMissError, match="resources"):
        manager.resolve_content_source(None, "resources", strict=True)


def test_resolve_content_source_non_strict_returns_empty_dict_on_missing_catalog():
    """strict=False with no catalog must return {} (not raise, not use hardcoded path)."""
    manager = GracefulDegradationManager()

    result = manager.resolve_content_source(None, "items", strict=False)

    assert result == {}


def test_resolve_content_source_non_strict_default_is_false():
    """Default for strict parameter is False — missing catalog must not raise by default."""
    manager = GracefulDegradationManager()
    result = manager.resolve_content_source(None, "items")
    assert result == {}


# ---------------------------------------------------------------------------
# 5. CatalogRepository.get_lowest_cost_for_type
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

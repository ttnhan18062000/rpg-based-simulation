"""Checks on a composition's ``module_refs`` that run before the modules are merged."""
from __future__ import annotations

from typing import Any, Dict, List


def require_one_ref_per_module(composition: Any) -> Any:
    """Return ``composition``, or raise if one module id is listed twice in its ``module_refs``.

    The assembly graph and its per-ref lookups are keyed by module id, so a second ref would
    silently replace the first. The error names the world, the module id and both refs.
    """
    first_ref_of: Dict[str, Any] = {}
    for index, ref in enumerate(composition.module_refs):
        if ref.module_id in first_ref_of:
            first_index, first = first_ref_of[ref.module_id]
            raise ValueError(
                f"Composition '{composition.world_id}' lists module '{ref.module_id}' twice: "
                f"module_refs[{first_index}] (namespace={first.namespace!r}, enabled={first.enabled}, order={first.order}) and "
                f"module_refs[{index}] (namespace={ref.namespace!r}, enabled={ref.enabled}, order={ref.order}). "
                f"A module can be composed once per world; to use its content twice, author a second module."
            )
        first_ref_of[ref.module_id] = (index, ref)
    return composition


def missing_module_issues(composition: Any, graph_map: Dict[str, Any]) -> List[Dict[str, Any]]:
    """ASM-COMP-001 issues for enabled refs whose module is not in ``graph_map``.

    ``graph_map`` holds only the enabled refs, so exactly those are checked: a disabled ref is
    left out of the assembly and is not a missing module.
    """
    return [
        {
            "severity": "ERROR",
            "rule_id": "ASM-COMP-001",
            "message": f"Referenced module '{ref.module_id}' not found in repository.",
            "path": f"module_refs.{ref.module_id}",
        }
        for ref in composition.module_refs
        if ref.enabled and ref.module_id not in graph_map
    ]

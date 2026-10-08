"""
Advisory need-path integrity report (SURV-06, SURV-05).

For each kind populated in a compiled world, reports whether the kind's declared needs have a path:
- hunger (a level other than ``none``): a meal place, i.e. at least one ``inn`` building, and how far
  the farthest subject of the kind is from the nearest one. Eating carried food needs no building, so
  the meal place is the declared PLACE path.
- hunger, forage: a food node, i.e. a resource node whose yield is food (``hunger_recovery`` above zero),
  harvested through the ordinary harvest path and eaten as carried food. It counts as a path for every
  hungering kind in a world that has one (the harvest path is open to every subject; which kinds are
  declared to forage is prose in SURV-06, not data, so the report does not narrow it).
- rest: rough sleep in place needs no building (SURV-06), so every kind with a sleep need always has a
  path; the report records it for completeness.

This is advisory: it never raises and never blocks assembly (the row-11 precedent). The report is a
pure read of the compiled state.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from src.core.items import food_hunger_recovery
from src.engine.biological_needs import PERSON_FALLBACK_PROFILE_ID, profile_id_for

_HUNGERLESS = ("none", "undeclared")


def _nearest_inn_distance(state: Any, position: Tuple[float, float]) -> Optional[float]:
    distances = [abs(b.position[0] - position[0]) + abs(b.position[1] - position[1])
                 for b in state.buildings.values() if b.kind == "inn"]
    return min(distances) if distances else None


def _is_food_node(node: Any) -> bool:
    return food_hunger_recovery(node.yields_item) > 0.0


def _nearest_food_node_distance(food_nodes: List[Any], position: Tuple[float, float]) -> Optional[float]:
    distances = [abs(n.position[0] - position[0]) + abs(n.position[1] - position[1]) for n in food_nodes]
    return min(distances) if distances else None


def _kind_of(props: Dict[str, Any], profile_id: Optional[str]) -> str:
    return props.get("species_id") or ("person" if profile_id == PERSON_FALLBACK_PROFILE_ID else "undeclared")


def _new_row(kind: str, profile_id: Optional[str], profile: Any) -> Dict[str, Any]:
    needs = profile.needs if profile else {}
    level = (lambda key: needs.get(key, "none")) if profile else (lambda key: "undeclared")
    return {"kind": kind, "subjects": 0, "need_profile": profile_id, "hunger": level("hunger"),
            "sleep": level("sleep"), "max_inn_distance": None, "max_food_node_distance": None}


def _finish_row(row: Dict[str, Any], inns: int, food_nodes: int) -> Dict[str, Any]:
    hungers = row["hunger"] not in _HUNGERLESS
    row["inns_in_world"] = inns
    row["food_nodes_in_world"] = food_nodes
    row["hunger_path"] = (inns > 0 or food_nodes > 0) if hungers else "not_needed"
    row["rest_path"] = "rough_sleep" if row["sleep"] not in _HUNGERLESS else "not_needed"
    row["advisory"] = (
        "undeclared kind: content defect (SURV-05)" if row["kind"] == "undeclared"
        else "hungers but the world has no inn and no food node" if hungers and inns == 0 and food_nodes == 0 else ""
    )
    return row


def _widen(row: Dict[str, Any], key: str, distance: Optional[float]) -> None:
    """Keep the largest distance seen for `key` on the row."""
    if distance is not None and (row[key] is None or distance > row[key]):
        row[key] = distance


def need_path_report(state: Any, catalog: Any) -> List[Dict[str, Any]]:
    """One row per kind (species id, or ``person`` for a species-less civil role) populated in `state`."""
    groups: Dict[str, Dict[str, Any]] = {}
    food_nodes = [n for n in state.resource_nodes.values() if _is_food_node(n)]
    for entity in state.entities.values():
        props = entity.identity.properties or {}
        profile_id = profile_id_for(props, entity.identity.role, catalog)
        kind = _kind_of(props, profile_id)
        profile = catalog.get_need_profile(profile_id) if profile_id else None
        row = groups.setdefault(kind, _new_row(kind, profile_id, profile))
        row["subjects"] += 1
        if row["hunger"] not in _HUNGERLESS:
            _widen(row, "max_inn_distance", _nearest_inn_distance(state, entity.navigation.position))
            _widen(row, "max_food_node_distance", _nearest_food_node_distance(food_nodes, entity.navigation.position))
    inns = sum(1 for b in state.buildings.values() if b.kind == "inn")
    return [_finish_row(groups[kind], inns, len(food_nodes)) for kind in sorted(groups)]

"""
Advisory need-path integrity report (SURV-06, SURV-05).

For each kind populated in a compiled world, reports whether the kind's declared needs have a path:
- hunger (a level other than ``none``): a meal place, i.e. at least one ``inn`` building, and how far
  the farthest subject of the kind is from the nearest one. Eating carried food needs no building, so
  the meal place is the declared PLACE path.
- rest: rough sleep in place needs no building (SURV-06), so every kind with a sleep need always has a
  path; the report records it for completeness.

This is advisory: it never raises and never blocks assembly (the row-11 precedent). The report is a
pure read of the compiled state.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from src.engine.biological_needs import PERSON_FALLBACK_PROFILE_ID, profile_id_for

_HUNGERLESS = ("none", "undeclared")


def _nearest_inn_distance(state: Any, position: Tuple[float, float]) -> Optional[float]:
    distances = [abs(b.position[0] - position[0]) + abs(b.position[1] - position[1])
                 for b in state.buildings.values() if b.kind == "inn"]
    return min(distances) if distances else None


def _kind_of(props: Dict[str, Any], profile_id: Optional[str]) -> str:
    return props.get("species_id") or ("person" if profile_id == PERSON_FALLBACK_PROFILE_ID else "undeclared")


def _new_row(kind: str, profile_id: Optional[str], profile: Any) -> Dict[str, Any]:
    needs = profile.needs if profile else {}
    level = (lambda key: needs.get(key, "none")) if profile else (lambda key: "undeclared")
    return {"kind": kind, "subjects": 0, "need_profile": profile_id, "hunger": level("hunger"),
            "sleep": level("sleep"), "max_inn_distance": None}


def _finish_row(row: Dict[str, Any], inns: int) -> Dict[str, Any]:
    hungers = row["hunger"] not in _HUNGERLESS
    row["inns_in_world"] = inns
    row["hunger_path"] = (inns > 0) if hungers else "not_needed"
    row["rest_path"] = "rough_sleep" if row["sleep"] not in _HUNGERLESS else "not_needed"
    row["advisory"] = (
        "undeclared kind: content defect (SURV-05)" if row["kind"] == "undeclared"
        else "hungers but the world has no inn" if hungers and inns == 0 else ""
    )
    return row


def need_path_report(state: Any, catalog: Any) -> List[Dict[str, Any]]:
    """One row per kind (species id, or ``person`` for a species-less civil role) populated in `state`."""
    groups: Dict[str, Dict[str, Any]] = {}
    for entity in state.entities.values():
        props = entity.identity.properties or {}
        profile_id = profile_id_for(props, entity.identity.role, catalog)
        kind = _kind_of(props, profile_id)
        profile = catalog.get_need_profile(profile_id) if profile_id else None
        row = groups.setdefault(kind, _new_row(kind, profile_id, profile))
        row["subjects"] += 1
        d = _nearest_inn_distance(state, entity.navigation.position) if row["hunger"] not in _HUNGERLESS else None
        if d is not None and (row["max_inn_distance"] is None or d > row["max_inn_distance"]):
            row["max_inn_distance"] = d
    inns = sum(1 for b in state.buildings.values() if b.kind == "inn")
    return [_finish_row(groups[kind], inns) for kind in sorted(groups)]

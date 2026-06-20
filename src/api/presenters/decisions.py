"""
src/api/presenters/decisions.py
───────────────────────────────────────────────────────────────────────────────
Presenter layer for Decision Explanation REST endpoints (Epic 2.2C).

Shapes raw JSONL dicts from DecisionTraceIndex.lookup() into the authoritative
response schema. No domain types, no I/O, no side effects.

Architecture constraints:
- Do NOT import AuthoritativeState, EntityState, AdventureRouteOption,
  RouteFamily, or any src.core.* / src.engine.* symbol.
- All inputs are plain dicts and primitives.
- All outputs are plain dicts (no Pydantic models here — consistent with the
  existing StatePresenter pattern).
"""
from __future__ import annotations

from typing import List


class DecisionPresenter:
    """Shapes decision trace data into authoritative REST response models."""

    @staticmethod
    def present_tick_response(entity_id: int, tick: int, entries: List[dict]) -> dict:
        """
        Filter entries to the given entity_id and return the tick response shape.

        Args:
            entity_id: Integer entity ID (matches the path parameter).
            tick:      Tick number from query parameter.
            entries:   List of raw dicts from DecisionTraceIndex.lookup(tick).
                       Each entry has keys: entity_id, tick, routes (list of dicts).

        Returns:
            {"entity_id": int, "tick": int, "routes": [...]}
        """
        routes: List[dict] = []
        for entry in entries:
            if entry.get("entity_id") != entity_id:
                continue
            routes.extend(entry.get("routes", []))
        return {
            "entity_id": entity_id,
            "tick": tick,
            "routes": routes,
        }

    @staticmethod
    def present_range_response(entity_id: int, entries_by_tick: List[dict]) -> List[dict]:
        """
        Filter a flat list of raw entries to the given entity_id, grouped by tick.

        Args:
            entity_id:      Integer entity ID.
            entries_by_tick: Flat list of raw entry dicts (each has entity_id, tick, routes).
                             All ticks in the requested range are mixed together.

        Returns:
            List of {"entity_id": int, "tick": int, "routes": [...]} objects,
            one per tick that has at least one route after entity filtering.
            Ticks with no matching data are omitted.
        """
        # Group filtered routes by tick, preserving insertion order
        tick_routes: dict[int, List[dict]] = {}
        for entry in entries_by_tick:
            if entry.get("entity_id") != entity_id:
                continue
            tick = entry.get("tick")
            if tick is None:
                continue
            if tick not in tick_routes:
                tick_routes[tick] = []
            tick_routes[tick].extend(entry.get("routes", []))

        result: List[dict] = []
        for tick in sorted(tick_routes.keys()):
            routes = tick_routes[tick]
            if not routes:
                continue  # omit ticks with no routes after filtering
            result.append({
                "entity_id": entity_id,
                "tick": tick,
                "routes": routes,
            })
        return result

    @staticmethod
    def present_summary_response(
        entity_id: int,
        tick_count: int,
        distribution: dict,
    ) -> dict:
        """
        Shape the summary response.

        Args:
            entity_id:    Integer entity ID.
            tick_count:   Number of ticks that had at least one matching entry.
            distribution: route_kind → fractional proportion (pre-computed by handler).

        Returns:
            {"entity_id": int, "tick_count": int, "route_kind_distribution": {...}}
        """
        return {
            "entity_id": entity_id,
            "tick_count": tick_count,
            "route_kind_distribution": distribution,
        }

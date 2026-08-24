# Compliance IDs: API-001, API-009, API-013, API-018, API-019, API-020, API-021, API-022, API-023, API-024, DATA-023, DATA-041, DATA-045, DATA-129, DATA-130, DATA-131, DATA-132, DATA-133, DATA-134, DATA-135, INFRA-019, INFRA-056, INFRA-057, INFRA-167, INFRA-180, RES-021, STRAT-035, STRAT-044, STRAT-060, STRAT-068, WORLD-015
from __future__ import annotations
from typing import Dict, Any, List
from src.core.state import AuthoritativeState, EntityState, RegionState

class StatePresenter:
    """
    Transforms authoritative state into read-only API models.
    M12 Law: API presenters MUST NOT mutate authoritative state.
    VERIFIED v2: observability_from_results
    """

    @staticmethod
    def present_minimal(state: AuthoritativeState) -> Dict[str, Any]:
        """Summarized world view."""
        return {
            "tick": state.tick,
            "world_time": state.world_time,
            "entities_count": len(state.entities),
            "maturity": state.maturity,
            "seed": state.seed
        }

    @staticmethod
    def present_full(state: AuthoritativeState) -> Dict[str, Any]:
        """Complete inspectable world view."""
        return {
            "tick": state.tick,
            "world_time": state.world_time,
            "maturity": state.maturity,
            "entities": [StatePresenter.present_entity(e) for e in state.entities.values()],
            "regions": [StatePresenter.present_region(r) for r in state.regions.values()],
            "global_resources": state.global_resources,
            "transaction_trace": state.transaction_trace,
            "status": "ACTIVE"
        }

    @staticmethod
    def present_entity(entity: EntityState) -> Dict[str, Any]:
        """Detailed entity model."""
        from src.core.quests import QuestState
        
        return {
            "id": entity.id,
            "kind": entity.kind,
            "position": entity.position,
            "readiness": entity.readiness,
            "combat": {
                "hp": entity.combat.hp,
                "max_hp": entity.combat.max_hp,
                "atk": entity.combat.atk,
                "def": entity.combat.def_stat,
                "alive": entity.combat.alive,
                "tactical_role": entity.combat.tactical_role,
                "last_legality_result": entity.combat.latest_result.reason if entity.combat.latest_result else None,
                "damage_trace": {} # Trace removed in V2 to save memory
            },
            "inventory": {
                "gold": entity.inventory.gold,
                "item_count": len(entity.inventory.items),
                "items": [
                    {"id": i.item_id, "quantity": i.quantity, "metadata": i.metadata}
                    for i in entity.inventory.items
                ]
            },
            "strategic": {
                "current_project": entity.strategic.current_project_id,
                "current_objective": entity.strategic.current_objective_id,
                "project_count": len(entity.strategic.projects),
                "boredom": entity.strategic.boredom,
                "primary_overload": entity.strategic.primary_overload_source,
                "blockers": [
                    {"id": b.id, "kind": b.kind, "subject": b.subject, "severity": b.severity, "resolved": b.resolved}
                    for b in entity.strategic.blockers.values()
                ],
                "leads": [
                    {"id": l.id, "kind": l.kind, "subject": l.subject, "certainty": l.certainty.value if hasattr(l.certainty, 'value') else l.certainty, "tested": l.tested}
                    for l in entity.strategic.leads.values()
                ],
                "contracts": [
                    {"id": c.id, "kind": c.kind.value if hasattr(c.kind, 'value') else c.kind, "status": c.status.value if hasattr(c.status, 'value') else c.status, "target_id": c.target_id}
                    for c in entity.strategic.contracts.values()
                ]
            },
            "quests": [
                {
                    "id": q.id,
                    "name": q.name,
                    "kind": q.quest_kind.name if hasattr(q.quest_kind, 'name') else str(q.quest_kind),
                    "status": q.quest_status.name if hasattr(q.quest_status, 'name') else str(q.quest_status),
                    "progress": q.progress_ratio,
                    "reward": {"xp": q.reward.xp, "gold": q.reward.gold, "items": q.reward.items}
                }
                for q in entity.strategic.projects.values() if isinstance(q, QuestState)
            ],
            "social": {
                "trust": {str(k): v for k, v in entity.social.trust_history.items()},
                "public_reputation": entity.social.public_reputation,
                "heroism": entity.social.heroism_score,
                "notoriety": entity.social.notoriety_score,
                "betrayals": entity.social.betrayal_count
            },
            "navigation": {
                "target": entity.navigation.target,
                "moved_recently": entity.navigation.moved_recently,
                "wait_count": entity.navigation.wait_count,
                "oscillation_count": entity.navigation.oscillation_count,
                "last_failure": entity.navigation.last_failure_reason,
                "mode": entity.navigation.movement_mode.name if hasattr(entity.navigation.movement_mode, 'name') else str(entity.navigation.movement_mode)
            },
            "biological": {
                "sleep_debt": entity.biological.sleep_debt,
                "hunger": entity.biological.hunger
            },
            "identity": {
                "faction": entity.identity.faction,
                "role": entity.identity.role,
                "level": entity.identity.evolution_level,
                "class": entity.identity.class_id
            },
            "intent_results": [
                {
                    "accepted": r.accepted,
                    "reason": r.reason,
                    "source": f"{r.source_kind}:{r.source_id}",
                    "transaction_id": r.transaction_id
                } for r in entity.identity.latest_intent_results
            ]
        }

    @staticmethod
    def present_region(region: RegionState) -> Dict[str, Any]:
        """Detailed regional model."""
        return {
            "id": region.id,
            "name": region.name,
            "owner": region.owner_faction_id,
            "influence": region.influence,
            "hazard": region.hazard_level,
            "kind": region.kind,
            "weather": region.weather
        }

    @staticmethod
    def terrain_code_map(state: AuthoritativeState) -> Dict[str, int]:
        """Deterministic terrain-type-string -> int code, for the live map's RLE grid.

        No terrain-type enum exists in this codebase (recipe-declared free-form strings). Codes are
        assigned 0..n-1 over the alphabetically-sorted distinct values actually present in
        state.terrain, so the same terrain-type set always maps to the same codes regardless of dict
        insertion order. Computed fresh per call (never cached/stored) since terrain can change
        between calls.
        """
        return {t: i for i, t in enumerate(sorted(set(state.terrain.values())))}

    @staticmethod
    def present_map(state: AuthoritativeState) -> Dict[str, Any]:
        """Terrain grid as an RLE-encoded payload: {width, height, grid}.

        AuthoritativeState has no stored width/height; state.terrain is populated densely over the
        full world topology at compile time, so the populated extent (max key + 1) is the real
        width/height. RLE walk matches src_legacy's ported _idx(x,y)=y*width+x row-major order.
        """
        if not state.terrain:
            return {"width": 0, "height": 0, "grid": []}

        width = max(x for x, _ in state.terrain.keys()) + 1
        height = max(y for _, y in state.terrain.keys()) + 1
        code_map = StatePresenter.terrain_code_map(state)

        grid: List[int] = []
        cur_val = None
        cur_count = 0
        for y in range(height):
            for x in range(width):
                v = code_map.get(state.terrain.get((x, y)), 0)
                if v == cur_val:
                    cur_count += 1
                else:
                    if cur_val is not None:
                        grid.append(cur_val)
                        grid.append(cur_count)
                    cur_val = v
                    cur_count = 1
        if cur_val is not None:
            grid.append(cur_val)
            grid.append(cur_count)

        return {"width": width, "height": height, "grid": grid}

    @staticmethod
    def present_static(state: AuthoritativeState) -> Dict[str, Any]:
        """Static world objects (buildings, resource nodes, treasure chests, regions).

        See staging_artifacts/TCK-20260821-PRESENT-MAP-STATIC/investigation.md for the field-level
        drop-vs-derive decisions (building name/owner, resource-node name/terrain, chest
        guard/tier/looted, region terrain/difficulty/locations) — none are stored on the
        corresponding state class, so each is either derived from an existing field or dropped.
        """
        code_map = StatePresenter.terrain_code_map(state)

        buildings = [
            {
                "building_id": str(b.id),
                "name": b.kind.title(),
                "x": b.position[0],
                "y": b.position[1],
                "building_type": b.kind,
                "owner_entity_id": None,
            }
            for b in state.buildings.values()
        ]

        resource_nodes = [
            {
                "node_id": n.id,
                "resource_type": n.kind,
                "name": n.kind.title(),
                "x": n.position[0],
                "y": n.position[1],
                "terrain": code_map.get(state.terrain.get((int(n.position[0]), int(n.position[1]))), 0),
                "yields_item": n.yields_item,
                "max_harvests": n.max_charges,
                "respawn_cooldown": n.respawn_cooldown,
                "harvest_ticks": n.required_ticks,
            }
            for n in state.resource_nodes.values()
        ]

        treasure_chests = [
            {
                "chest_id": c.id,
                "x": c.position[0],
                "y": c.position[1],
                "tier": 1,
                "looted": len(c.items) == 0,
                "guard_entity_id": None,
            }
            for c in state.chests.values()
        ]

        regions = []
        for region in state.regions.values():
            min_x, min_y, max_x, max_y = region.bounds
            regions.append({
                "region_id": region.id,
                "name": region.name,
                "terrain": code_map.get(region.kind, 0),
                "center_x": (min_x + max_x) / 2,
                "center_y": (min_y + max_y) / 2,
                "radius": max(max_x - min_x, max_y - min_y) / 2,
                "difficulty": region.hazard_level,
                "locations": [],
            })

        return {
            "buildings": buildings,
            "resource_nodes": resource_nodes,
            "treasure_chests": treasure_chests,
            "regions": regions,
        }

    @staticmethod
    def present_stats(
        state: AuthoritativeState,
        total_spawned: int,
        total_deaths: int,
        running: bool,
        paused: bool,
    ) -> Dict[str, Any]:
        """Live simulation counters: {tick, world_day, alive_count, total_spawned, total_deaths, running, paused}.

        world_day = tick // 2400 per docs/mechanics/05_world_evolution.md:15-22 ("1 Day = 2400 ticks",
        Certified Level 1) -- NOT V1's legacy tick // 100, NOT src/world/raid.py's unrelated
        RaidService.TICKS_PER_DAY=100 (see staging_artifacts/TCK-20260821-REST-MAP-STATIC-STATS/plan.md
        Design Decisions).
        alive_count filters state.entities by combat.alive, ported from V1's exact semantics and
        matching the in-repo precedent at src/api/presenters/economy.py's EconomyPresenter
        .present_health filter -- not len(state.entities) (see plan.md Design Decisions for the
        revisit condition).
        total_spawned/total_deaths/running/paused are V2EngineManager-level telemetry, passed through
        unchanged -- this keeps the method a pure function of its arguments, consistent with the M12
        Law docstring at the top of this file: "API presenters MUST NOT mutate authoritative state."
        """
        alive_count = sum(1 for e in state.entities.values() if e.combat.alive)
        return {
            "tick": state.tick,
            "world_day": state.tick // 2400,
            "alive_count": alive_count,
            "total_spawned": total_spawned,
            "total_deaths": total_deaths,
            "running": running,
            "paused": paused,
        }

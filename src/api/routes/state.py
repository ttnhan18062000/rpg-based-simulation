"""GET /api/v1/state — dynamic entity & event data (polled by UI)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_engine_manager
from src.api.engine_manager import EngineManager
from src.api.schemas import (
    AttributeCapSchema,
    AttributeSchema,
    BuildingSchema,
    EffectSchema,
    EntitySchema,
    EventSchema,
    GroundItemSchema,
    QuestSchema,
    ResourceNodeSchema,
    SimulationStats,
    SkillSchema,
    WorldStateResponse,
)

router = APIRouter()


def _serialize_attrs(e) -> AttributeSchema | None:
    if e.attributes is None:
        return None
    a = e.attributes
    return AttributeSchema(
        str_=a.str_, agi=a.agi, vit=a.vit,
        int_=a.int_, spi=a.spi, wis=a.wis,
        end=a.end, per=a.per, cha=a.cha,
        str_frac=a._str_frac, agi_frac=a._agi_frac, vit_frac=a._vit_frac,
        int_frac=a._int_frac, spi_frac=a._spi_frac, wis_frac=a._wis_frac,
        end_frac=a._end_frac, per_frac=a._per_frac, cha_frac=a._cha_frac,
    )


def _serialize_caps(e) -> AttributeCapSchema | None:
    if e.attribute_caps is None:
        return None
    c = e.attribute_caps
    return AttributeCapSchema(
        str_cap=c.str_cap, agi_cap=c.agi_cap, vit_cap=c.vit_cap,
        int_cap=c.int_cap, spi_cap=c.spi_cap, wis_cap=c.wis_cap,
        end_cap=c.end_cap, per_cap=c.per_cap, cha_cap=c.cha_cap,
    )


def _serialize_hero_class(e) -> str:
    from src.core.classes import HeroClass
    try:
        return HeroClass(e.hero_class).name.lower()
    except (ValueError, KeyError):
        return "none"


def _serialize_skills(e) -> list[SkillSchema]:
    from src.core.classes import SKILL_DEFS
    result = []
    for si in e.skills:
        sdef = SKILL_DEFS.get(si.skill_id)
        result.append(SkillSchema(
            skill_id=si.skill_id,
            name=sdef.name if sdef else si.skill_id,
            cooldown_remaining=si.cooldown_remaining,
            mastery=si.mastery,
            times_used=si.times_used,
            skill_type=sdef.skill_type.name.lower() if sdef else "active",
            target=sdef.target.name.lower() if sdef else "self",
            stamina_cost=si.effective_stamina_cost(sdef.stamina_cost) if sdef else 0,
            cooldown=si.effective_cooldown(sdef.cooldown) if sdef else 0,
            power=si.effective_power(sdef.power) if sdef else 1.0,
            description=sdef.description if sdef else "",
        ))
    return result


@router.get("/state", response_model=WorldStateResponse)
def get_state(
    since_tick: int = Query(0, ge=0, description="Only return events since this tick"),
    manager: EngineManager = Depends(get_engine_manager),
) -> WorldStateResponse:
    snapshot = manager.get_snapshot()
    if snapshot is None:
        raise HTTPException(status_code=503, detail="No snapshot available yet.")

    entities = [
        EntitySchema(
            id=e.id,
            kind=e.kind,
            x=e.pos.x,
            y=e.pos.y,
            hp=e.stats.hp,
            max_hp=e.stats.max_hp,
            atk=e.effective_atk(),
            def_=e.effective_def(),
            spd=e.effective_spd(),
            luck=e.stats.luck,
            crit_rate=e.effective_crit_rate(),
            evasion=e.effective_evasion(),
            matk=e.effective_matk(),
            mdef=e.effective_mdef(),
            level=e.stats.level,
            xp=e.stats.xp,
            xp_to_next=e.stats.xp_to_next,
            gold=e.stats.gold,
            tier=e.tier,
            faction=e.faction.name.lower(),
            state=e.ai_state.name,
            weapon=e.inventory.weapon if e.inventory else None,
            armor=e.inventory.armor if e.inventory else None,
            accessory=e.inventory.accessory if e.inventory else None,
            inventory_count=e.inventory.used_slots if e.inventory else 0,
            inventory_items=list(e.inventory.items) if e.inventory else [],
            vision_range=manager.config.vision_range,
            terrain_memory={f"{k[0]},{k[1]}": v for k, v in e.terrain_memory.items()},
            entity_memory=list(e.entity_memory),
            goals=list(e.goals),
            loot_progress=e.loot_progress,
            loot_duration=manager.config.loot_duration,
            known_recipes=list(e.known_recipes),
            craft_target=e.craft_target,
            stamina=e.stats.stamina,
            max_stamina=e.stats.max_stamina,
            attributes=_serialize_attrs(e),
            attribute_caps=_serialize_caps(e),
            hero_class=_serialize_hero_class(e),
            skills=_serialize_skills(e),
            class_mastery=e.class_mastery,
            active_effects=[
                EffectSchema(
                    effect_type=eff.effect_type.name,
                    source=eff.source,
                    remaining_ticks=eff.remaining_ticks,
                    atk_mult=eff.atk_mult,
                    def_mult=eff.def_mult,
                    spd_mult=eff.spd_mult,
                )
                for eff in e.effects
                if not eff.expired
            ],
            traits=list(e.traits),
            quests=[
                QuestSchema(
                    quest_id=q.quest_id,
                    quest_type=q.quest_type.name,
                    title=q.title,
                    description=q.description,
                    target_kind=q.target_kind,
                    target_x=q.target_pos.x if q.target_pos else None,
                    target_y=q.target_pos.y if q.target_pos else None,
                    target_count=q.target_count,
                    progress=q.progress,
                    completed=q.completed,
                    gold_reward=q.gold_reward,
                    xp_reward=q.xp_reward,
                )
                for q in e.quests
            ],
        )
        for e in snapshot.entities.values()
        if e.alive
    ]

    events = [
        EventSchema(tick=ev.tick, category=ev.category, message=ev.message)
        for ev in manager.event_log.since_tick(since_tick)
    ]

    ground_items = [
        GroundItemSchema(x=x, y=y, items=list(items))
        for (x, y), items in snapshot.ground_items.items()
        if items
    ]

    buildings = [
        BuildingSchema(
            building_id=b.building_id, name=b.name,
            x=b.pos.x, y=b.pos.y, building_type=b.building_type,
        )
        for b in snapshot.buildings
    ]

    resource_nodes = [
        ResourceNodeSchema(
            node_id=n.node_id, resource_type=n.resource_type, name=n.name,
            x=n.pos.x, y=n.pos.y, terrain=int(n.terrain),
            yields_item=n.yields_item, remaining=n.remaining,
            max_harvests=n.max_harvests, is_available=n.is_available,
            harvest_ticks=n.harvest_ticks,
        )
        for n in snapshot.resource_nodes
    ]

    alive_count = len(entities)
    return WorldStateResponse(
        tick=snapshot.tick,
        alive_count=alive_count,
        entities=entities,
        events=events,
        ground_items=ground_items,
        buildings=buildings,
        resource_nodes=resource_nodes,
    )


@router.get("/stats", response_model=SimulationStats)
def get_stats(
    manager: EngineManager = Depends(get_engine_manager),
) -> SimulationStats:
    snapshot = manager.get_snapshot()
    tick = snapshot.tick if snapshot else 0
    alive = sum(1 for e in snapshot.entities.values() if e.alive) if snapshot else 0

    return SimulationStats(
        tick=tick,
        alive_count=alive,
        total_spawned=manager.total_spawned,
        total_deaths=manager.total_deaths,
        running=manager.running,
        paused=manager.paused,
    )

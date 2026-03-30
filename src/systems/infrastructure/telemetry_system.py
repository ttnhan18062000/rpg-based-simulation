"""TelemetrySystem handles metrics collection and Prometheus exposure."""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.systems.infrastructure.base import System, SystemContext

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.platform.rng import DeterministicRNG

logger = logging.getLogger(__name__)

class TelemetrySystem(System):
    """System for collecting and publishing simulation metrics."""

    def on_tick(self, ctx: SystemContext, tick: int) -> None:
        """Collect rich simulation metrics for Prometheus/Grafana."""
        from src.utils.metrics import (
            SIM_FACTION_POPULATION,
            SIM_ENTITY_LEVEL_DISTRIBUTION,
            SIM_HERO_CLASS_TOTAL,
            SIM_GOLD_CIRCULATION_TOTAL,
            SIM_BUILDING_DURABILITY_PERCENT,
            SIM_CALAMITY_ACTIVE,
            # SIM_ACTION_QUEUE_DEPTH, # Handled by WorldLoop since it owns the queue
            ACTIVE_ENTITIES,
            SIM_TOP_HERO_LEVEL,
            SIM_TOP_HERO_GOLD
        )
        from src.core.models.enums import Faction, HeroClass
        
        world = ctx.world
        
        # 1. Populations & Gold
        pop_counts = {f: 0 for f in Faction}
        gold_counts = {f: 0 for f in Faction}
        level_dist = {} # (kind, bracket) -> count
        class_dist = {} # (hc_name, tier) -> count
        
        total_alive = 0
        max_level = 0
        max_gold = 0
        for entity in world.entities.values():
            if not entity.combat.alive or entity.kind == "generator":
                continue
            
            total_alive += 1
            f = entity.identity.faction
            pop_counts[f] += 1
            gold_counts[f] += entity.progression.gold
            
            if f == Faction.HERO_GUILD:
                max_level = max(max_level, entity.progression.level)
                max_gold = max(max_gold, entity.progression.gold)
            
            # Level distribution
            lvl = entity.progression.level
            bracket = f"{(lvl-1)//10*10+1}-{(lvl-1)//10*10+10}"
            key = (entity.kind, bracket)
            level_dist[key] = level_dist.get(key, 0) + 1
            
            # Hero Class distribution
            if f == Faction.HERO_GUILD:
                hc_val = entity.identity.hero_class
                try:
                    hc = HeroClass(hc_val)
                except ValueError:
                    hc = HeroClass.NONE
                tier = 1
                if lvl >= 20: tier = 3
                elif lvl >= 10: tier = 2
                ckey = (hc.name.lower(), str(tier))
                class_dist[ckey] = class_dist.get(ckey, 0) + 1
                
        ACTIVE_ENTITIES.set(total_alive)
        SIM_TOP_HERO_LEVEL.set(max_level)
        SIM_TOP_HERO_GOLD.set(max_gold)
        for f, count in pop_counts.items():
            SIM_FACTION_POPULATION.labels(faction=f.name.lower()).set(count)
            SIM_GOLD_CIRCULATION_TOTAL.labels(faction=f.name.lower()).set(gold_counts[f])
            
        for (kind, bracket), count in level_dist.items():
            SIM_ENTITY_LEVEL_DISTRIBUTION.labels(kind=kind, level_bracket=bracket).set(count)
            
        for (hc_name, tier), count in class_dist.items():
            SIM_HERO_CLASS_TOTAL.labels(hero_class=hc_name, tier=tier).set(count)
            
        # 2. Buildings
        for b in world.buildings:
            pct = (b.durability / b.max_durability) * 100.0 if b.max_durability > 0 else 0
            SIM_BUILDING_DURABILITY_PERCENT.labels(building_id=b.building_id).set(pct)
            
        # 3. Calamity
        calamity_active = 0
        for entity in world.entities.values():
            if entity.combat.alive and "calamity" in entity.kind.lower():
                calamity_active = 1
                SIM_CALAMITY_ACTIVE.labels(region_id=entity.region_id).set(1)
                break
        if not calamity_active:
            SIM_CALAMITY_ACTIVE.labels(region_id="none").set(0)

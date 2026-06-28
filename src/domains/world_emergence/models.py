"""
src/domains/world_emergence/models.py
───────────────────────────────────────────────────────────────────────────────
Phase 8 — Pressures and Scarcity Models.
"""

from __future__ import annotations
from typing import Tuple, Sequence, Dict, List
from src.core.state import AuthoritativeState, RegionState
from src.domains.world_emergence.schema import (
    WorldEventAggregate, RegionalPressure, ResourceScarcitySignal, ServicePressure, WorldEventCategory
)
from src.domains.demographics.cohort import compute_population_density

class RegionalPressureModel:
    """
    Evaluates macro regional pressures based on aggregates.
    Limits pressures to 0.0 - 1.0.
    """

    @staticmethod
    def evaluate(
        state: AuthoritativeState,
        aggregates: Tuple[WorldEventAggregate, ...],
    ) -> Tuple[RegionalPressure, ...]:
        pressures = []
        
        # Calculate regional death aggregates
        death_counts: Dict[str, Tuple[int, float]] = {}
        failure_counts: Dict[str, Tuple[int, float]] = {}
        camp_clears: Dict[str, Tuple[int, float]] = {}
        camp_raids: Dict[str, Tuple[int, float]] = {}

        for agg in aggregates:
            if not agg.region_id:
                continue
            r_id = agg.region_id
            if agg.category == WorldEventCategory.ENTITY_DEATH:
                death_counts[r_id] = (agg.count, agg.severity_sum)
            elif agg.category == WorldEventCategory.QUEST_FAILED:
                failure_counts[r_id] = (agg.count, agg.severity_sum)
            elif agg.category == WorldEventCategory.CAMP_CLEARED:
                camp_clears[r_id] = (agg.count, agg.severity_sum)
            elif agg.category == WorldEventCategory.CAMP_RAID:
                camp_raids[r_id] = (agg.count, agg.severity_sum)

        # We evaluate regions present in aggregates or all active regions to ensure updates propagate
        for r_id in state.regions.keys():
            # 1. Danger Pressure: influenced by death counts & quest failures, decreased by camp clears
            base_danger = 0.0
            sources = []
            reasons = []

            if r_id in death_counts:
                cnt, sev = death_counts[r_id]
                base_danger += cnt * 0.15 + sev * 0.05
                sources.append(f"death:{cnt}")
                reasons.append(f"{cnt} entity deaths")
            if r_id in failure_counts:
                cnt, sev = failure_counts[r_id]
                base_danger += cnt * 0.08 + sev * 0.02
                sources.append(f"failure:{cnt}")
                reasons.append(f"{cnt} quest failures")
            if r_id in camp_raids:
                cnt, sev = camp_raids[r_id]
                base_danger += cnt * 0.25 + sev * 0.05
                sources.append(f"raid:{cnt}")
                reasons.append(f"{cnt} camp raids")
            if r_id in camp_clears:
                cnt, sev = camp_clears[r_id]
                base_danger -= cnt * 0.20 + sev * 0.05
                sources.append(f"clear:{cnt}")
                reasons.append(f"{cnt} camps cleared")

            # Check existing trauma to scale danger
            reg_state = state.regions[r_id]
            trauma_factor = min(0.4, reg_state.trauma_score / 100.0)
            hazard_factor = reg_state.hazard_level * 0.2
            
            intensity = min(1.0, max(0.0, base_danger + trauma_factor + hazard_factor))
            
            if intensity > 0.0 or sources:
                pressures.append(RegionalPressure(
                    region_id=r_id,
                    pressure_kind="danger",
                    intensity=intensity,
                    confidence=0.85,
                    source_aggregates=tuple(sources),
                    reason=", ".join(reasons) if reasons else "baseline environmental status"
                ))

            # 2. Resource Pressure: harvesting volume
            harv_cnt = 0
            harv_sev = 0.0
            dep_cnt = 0
            for agg in aggregates:
                if agg.region_id == r_id:
                    if agg.category == WorldEventCategory.RESOURCE_HARVESTED:
                        harv_cnt += agg.count
                        harv_sev += agg.severity_sum
                    elif agg.category == WorldEventCategory.RESOURCE_DEPLETED:
                        dep_cnt += agg.count

            if harv_cnt > 0 or dep_cnt > 0:
                # E52D: population density demand signal — high-population regions
                # consume more resources, amplifying base resource pressure.
                # demand_multiplier = 1.0 + (population_density * 0.5)
                # (spec: TCK-20260619-E52D-DENSITY-SIGNAL §Scope)
                demand_multiplier = 1.0 + (compute_population_density(reg_state) * 0.5)
                res_intensity = min(1.0, (harv_cnt * 0.05 + dep_cnt * 0.15) * demand_multiplier)
                pressures.append(RegionalPressure(
                    region_id=r_id,
                    pressure_kind="resource",
                    intensity=res_intensity,
                    confidence=0.9,
                    source_aggregates=(f"harvested:{harv_cnt}", f"depleted:{dep_cnt}", f"density_mult:{demand_multiplier:.3f}"),
                    reason=f"{harv_cnt} harvests, {dep_cnt} depleted nodes (demand_multiplier={demand_multiplier:.3f})"
                ))

            # 3. Camp pressure
            if r_id in camp_raids or r_id in camp_clears:
                base_camp = 0.0
                camp_reasons = []
                camp_sources = []
                if r_id in camp_raids:
                    cnt, sev = camp_raids[r_id]
                    base_camp += cnt * 0.3
                    camp_sources.append(f"raid:{cnt}")
                    camp_reasons.append(f"{cnt} camp raids matured")
                if r_id in camp_clears:
                    cnt, sev = camp_clears[r_id]
                    base_camp -= cnt * 0.25
                    camp_sources.append(f"clear:{cnt}")
                    camp_reasons.append(f"{cnt} camps cleared")
                
                camp_intensity = min(1.0, max(0.0, base_camp))
                pressures.append(RegionalPressure(
                    region_id=r_id,
                    pressure_kind="camp",
                    intensity=camp_intensity,
                    confidence=0.8,
                    source_aggregates=tuple(camp_sources),
                    reason=", ".join(camp_reasons)
                ))

        return tuple(pressures)

    # E21E constants
    ADJACENCY_GAP: float = 50.0      # regions within 50 units are considered adjacent
    PROPAGATION_FACTOR: float = 0.30  # fraction of neighbor resource pressure that bleeds across

    @staticmethod
    def _are_adjacent(r1: RegionState, r2: RegionState) -> bool:
        """True if the two regions' bounding boxes are within ADJACENCY_GAP units of each other."""
        gap = RegionalPressureModel.ADJACENCY_GAP
        x1min, y1min, x1max, y1max = r1.bounds
        x2min, y2min, x2max, y2max = r2.bounds
        hdist = max(0.0, max(x1min, x2min) - min(x1max, x2max))
        vdist = max(0.0, max(y1min, y2min) - min(y1max, y2max))
        return hdist <= gap and vdist <= gap

    @staticmethod
    def propagate_cross_region(
        pressures: Tuple[RegionalPressure, ...],
        state: AuthoritativeState,
    ) -> Tuple[RegionalPressure, ...]:
        """
        Propagate resource scarcity pressure between adjacent regions (E21E).

        Each region with nonzero resource pressure bleeds PROPAGATION_FACTOR × its
        intensity to every adjacent region, creating a scarcity gradient that drives
        entity migration away from resource-depleted areas.
        """
        factor = RegionalPressureModel.PROPAGATION_FACTOR

        # Partition: resource pressure entries vs everything else
        resource_by_region: Dict[str, RegionalPressure] = {}
        other: List[RegionalPressure] = []
        for p in pressures:
            if p.pressure_kind == "resource":
                resource_by_region[p.region_id] = p
            else:
                other.append(p)

        if not resource_by_region or len(state.regions) < 2:
            return pressures

        # Accumulate spread: how much each region receives from neighbours
        spread_in: Dict[str, float] = {r_id: 0.0 for r_id in state.regions}
        region_list = list(state.regions.values())
        for i, r1 in enumerate(region_list):
            for r2 in region_list[i + 1:]:
                if RegionalPressureModel._are_adjacent(r1, r2):
                    p1 = resource_by_region[r1.id].intensity if r1.id in resource_by_region else 0.0
                    p2 = resource_by_region[r2.id].intensity if r2.id in resource_by_region else 0.0
                    spread_in[r2.id] += p1 * factor
                    spread_in[r1.id] += p2 * factor

        # Rebuild resource pressure entries with propagated component merged in
        all_affected = set(resource_by_region.keys()) | {
            r_id for r_id, v in spread_in.items() if v > 0.0
        }
        updated_resource: List[RegionalPressure] = []
        for r_id in sorted(all_affected):
            spread = min(1.0, spread_in.get(r_id, 0.0))
            orig = resource_by_region.get(r_id)
            if orig:
                new_intensity = min(1.0, orig.intensity + spread)
                src = list(orig.source_aggregates)
                if spread > 0.0:
                    src.append(f"cross_region_spread:{spread:.3f}")
                reason = orig.reason
                if spread > 0.0:
                    reason += f"; +{spread:.3f} from adjacent-region scarcity"
                updated_resource.append(RegionalPressure(
                    region_id=r_id,
                    pressure_kind="resource",
                    intensity=new_intensity,
                    confidence=min(orig.confidence, 0.75) if spread > 0.0 else orig.confidence,
                    source_aggregates=tuple(src),
                    reason=reason,
                ))
            else:
                # Region got pressure purely through propagation from neighbours
                if spread > 0.0:
                    updated_resource.append(RegionalPressure(
                        region_id=r_id,
                        pressure_kind="resource",
                        intensity=spread,
                        confidence=0.65,
                        source_aggregates=(f"cross_region_spread:{spread:.3f}",),
                        reason=f"{spread:.3f} resource pressure propagated from adjacent regions",
                    ))

        return tuple(other + updated_resource)


class ScarcityModel:
    """
    Evaluates dynamic resource scarcity signals.
    """

    @staticmethod
    def evaluate(
        state: AuthoritativeState,
        aggregates: Tuple[WorldEventAggregate, ...],
    ) -> Tuple[ResourceScarcitySignal, ...]:
        signals = []
        
        # Scarcity maps
        harvested_count: Dict[Tuple[str, str], int] = {}
        depleted_count: Dict[Tuple[str, str], int] = {}
        
        for agg in aggregates:
            if agg.region_id and agg.subject:
                key = (agg.region_id, agg.subject)
                if agg.category == WorldEventCategory.RESOURCE_HARVESTED:
                    harvested_count[key] = harvested_count.get(key, 0) + agg.count
                elif agg.category == WorldEventCategory.RESOURCE_DEPLETED:
                    depleted_count[key] = depleted_count.get(key, 0) + agg.count

        # Evaluate based on active resource aggregates
        keys = set(harvested_count.keys()) | set(depleted_count.keys())
        for r_id, r_type in sorted(list(keys), key=lambda x: (x[0], x[1])):
            harv = harvested_count.get((r_id, r_type), 0)
            depl = depleted_count.get((r_id, r_type), 0)
            
            # Scarcity formula: depletion heavy
            scarcity = min(1.0, harv * 0.08 + depl * 0.25)
            availability = max(0.0, 1.0 - scarcity)
            trend = "INCREASING" if depl > 0 or harv > 3 else "STABLE"
            
            signals.append(ResourceScarcitySignal(
                region_id=r_id,
                resource_type=r_type,
                availability=availability,
                scarcity_level=scarcity,
                trend=trend,
                confidence=0.95,
                reason=f"Harvested count: {harv}, Depletion count: {depl}"
            ))
            
        return tuple(signals)


class ServiceStatePressureModel:
    """
    Translates scarcity and regional pressures into town service constraints.
    """

    @staticmethod
    def evaluate(
        pressures: Tuple[RegionalPressure, ...],
        scarcity: Tuple[ResourceScarcitySignal, ...],
        state: AuthoritativeState,
    ) -> Tuple[ServicePressure, ...]:
        s_pressures = []
        
        # Map regional scarcity/danger
        danger_by_region = {p.region_id: p.intensity for p in pressures if p.pressure_kind == "danger"}
        iron_scarcity = sum(s.scarcity_level for s in scarcity if s.resource_type == "iron_ore")
        herb_scarcity = sum(s.scarcity_level for s in scarcity if s.resource_type == "herb")
        deaths = sum(p.intensity * 5 for p in pressures if p.pressure_kind == "danger") # casualties representation
        
        # Blacksmith material pressure
        if iron_scarcity > 0.1:
            intensity = min(1.0, iron_scarcity * 0.8)
            s_pressures.append(ServicePressure(
                service_id="blacksmith",
                pressure_kind="material_shortage",
                intensity=intensity,
                effect_tags=("price_pressure", "stock_pressure"),
                reason=f"Iron scarcity in surrounding region: {iron_scarcity:.2f}"
            ))
            
        # Healer demand pressure
        if deaths > 0.5:
            intensity = min(1.0, deaths * 0.1)
            s_pressures.append(ServicePressure(
                service_id="healer",
                pressure_kind="healing_demand",
                intensity=intensity,
                effect_tags=("service_delay", "healing_demand"),
                reason=f"High casualty level in surrounding wilderness: {deaths:.2f}"
            ))

        # Guild threat pressure
        max_danger = max(danger_by_region.values()) if danger_by_region else 0.0
        if max_danger > 0.2:
            s_pressures.append(ServicePressure(
                service_id="guild",
                pressure_kind="threat_pressure",
                intensity=max_danger,
                effect_tags=("quest_pressure", "information_demand"),
                reason=f"Severe threat danger reported in wilderness: {max_danger:.2f}"
            ))
            
        # Shop stock pressure from travel danger
        if max_danger > 0.4:
            s_pressures.append(ServicePressure(
                service_id="shop",
                pressure_kind="supply_chain_disruption",
                intensity=max_danger * 0.7,
                effect_tags=("stock_pressure", "price_pressure"),
                reason=f"Danger pressure {max_danger:.2f} causing supply wagon delays"
            ))

        return tuple(s_pressures)

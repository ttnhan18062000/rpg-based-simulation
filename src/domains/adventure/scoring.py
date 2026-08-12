"""
src/domains/adventure/scoring.py
───────────────────────────────────────────────────────────────────────────────
Phase 3 — AdventureRouteScorer

Implements subjective route scoring with imperfect decision personality bias.
Reads only subjective self-model, cognition/memory, and (for
GATHER_RESOURCE/CRAFT_UPGRADE routes with a resolvable capability key) entity-owned
combat/stamina/inventory/equipment aspects via an ad-hoc
CapabilityEstimateService.estimate() call — never omniscient world truth, and never
entity.self_model.capabilities itself, which remains unpopulated in production (see
TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING) — to protect information
opacity.
"""

from __future__ import annotations
import dataclasses
from typing import TYPE_CHECKING, Any, Dict, Optional

from src.cognition.capability_estimate import CapabilityContext, CapabilityEstimateService
from src.core.state import EntityState, ResourceNodeState
from src.domains.adventure.schema import RouteFamily, AdventureRouteOption
from src.engine.faction_constants import DEFEND_BORDER, TRADE_ROUTE, COMMISSION_QUEST
from src.core.enums import DiplomaticState

if TYPE_CHECKING:
    from src.core.models.quests import QuestOpportunity
    from src.core.state import GroupRecord
    from src.domains.campaigns.progression_plan import ProgressionPlan
    from src.engine.faction_decision import FactionDirective


class AdventureRouteScorer:
    """
    Evaluates suitability scores of AdventureRouteOptions.
    Incorporates personality traits bias and survival priorities.
    """

    @staticmethod
    def score(
        entity: EntityState,
        route: AdventureRouteOption,
        resource_nodes: Optional[Dict[int, ResourceNodeState]] = None,
        quest_registry: Optional[Dict[str, "QuestOpportunity"]] = None,
        group: Optional["GroupRecord"] = None,
        faction_directives: Optional[list] = None,
        factions: Optional[Any] = None,
        progression_plan: Optional["ProgressionPlan"] = None,
    ) -> AdventureRouteOption:
        """
        Calculate subjective score for the route option and return updated option.
        Formula:
            score = urgency + benefit + personality_bias + plan_advance_bonus + memory_adjustment + confidence_bonus - risk_penalty - blocker_penalty

        Optional group context enables class-synergy multipliers (SOC-229):
          - WARRIOR + MAGE both present in group.roles → HUNT_WEAK_ENEMY score ×1.15
          - Entity is EntityRole.HERO                 → QUEST_OPPORTUNITY score ×1.10

        For GATHER_RESOURCE/CRAFT_UPGRADE routes with a resolvable capability key,
        confidence_bonus is computed from CapabilityEstimateService.estimate() instead
        of route.confidence (TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING); all
        other routes, and mapped routes whose key cannot be resolved, keep the flat
        route.confidence × 0.15 term.
        """
        # ── 1. Fetch Personality Traits (Robust Range Normalisation) ─────────
        def get_trait(trait_name: str) -> float:
            traits = getattr(entity.identity, "personality", None)
            if traits is None:
                if trait_name == "caution":
                    return 0.5
                if trait_name == "curiosity":
                    return 0.5
                return 0.5
            
            # Map caution and curiosity as they are not on PersonalityComponent
            if trait_name == "caution":
                # derived from 1.0 - bravery
                b_val = getattr(traits, "bravery", 0.0)
                if b_val > 1.0:
                    b_val /= 100.0
                return max(0.0, min(1.0, 1.0 - b_val))
            if trait_name == "curiosity":
                # Check entity.identity.properties for curiosity or intelligence
                props = getattr(entity.identity, "properties", {}) or {}
                if "curiosity" in props:
                    val = props["curiosity"]
                else:
                    # derived from intelligence on entity.attributes
                    attrs = getattr(entity, "attributes", None)
                    intel = getattr(attrs, "intelligence", 5.0)
                    val = intel / 10.0 if intel > 1.0 else intel
                
                if val > 1.0:
                    val /= 100.0
                return val
            
            val = getattr(traits, trait_name, 0.5)
            if val is None:
                return 0.5
            if val > 1.0:
                return val / 100.0
            return val

        bravery = get_trait("bravery")
        caution = get_trait("caution")
        greed = get_trait("greed")
        curiosity = get_trait("curiosity")
        industry = get_trait("industry")
        sociability = get_trait("sociability")

        # ── 2. Calculate Active Need Urgency ─────────────────────────────────
        needs = getattr(entity.self_model.needs, "active_needs", {}) or {}
        urgency = 0.0

        # Map RouteFamily to matching InterpretedNeed keys
        family_needs = {
            RouteFamily.RECOVER: ["healing", "rest", "stamina_recovery", "equipment_repair"],
            RouteFamily.BUY_UPGRADE: ["equipment_improvement"],
            RouteFamily.CRAFT_UPGRADE: ["equipment_improvement"],
            RouteFamily.GATHER_RESOURCE: ["gold", "inventory_space"],
            RouteFamily.SELL_LOOT_FOR_GOLD: ["gold"],
            RouteFamily.TAKE_EASY_QUEST: ["gold"],
            RouteFamily.ASK_INFORMATION: ["information"],
            RouteFamily.SCOUT_LOCATION: ["information"],
            RouteFamily.FORM_PARTY: ["social"],
            RouteFamily.QUEST_OPPORTUNITY: ["gold"],
        }

        matching_keys = family_needs.get(route.family, [])
        for key in matching_keys:
            if key in needs:
                urgency = max(urgency, needs[key].urgency)

        # ── 2b. Faction Directive Urgency Adjustments ─────────────────────────
        # Additive boosts applied when directives are provided (None = no boost).
        if faction_directives is not None:
            from src.core.enums import EntityRole as _ER
            # GUARD + patrol (HUNT_WEAK_ENEMY): boost when any DEFEND_BORDER active
            if entity.identity.role == _ER.GUARD and route.family == RouteFamily.HUNT_WEAK_ENEMY:
                if any(d.directive_kind == DEFEND_BORDER for d in faction_directives):
                    urgency += 2.0
            # SHOPKEEPER + trade routes: boost when any faction has allied relations
            if (
                entity.identity.role == _ER.SHOPKEEPER
                and route.family in (RouteFamily.GATHER_RESOURCE, RouteFamily.SELL_LOOT_FOR_GOLD)
                and factions is not None
                and any(DiplomaticState.ALLIED in fs.diplomatic_relations.values() for fs in factions.values())
            ):
                urgency += 1.5
            # HERO + quest: boost when any COMMISSION_QUEST directive active
            if entity.identity.role == _ER.HERO and route.family == RouteFamily.QUEST_OPPORTUNITY:
                if any(d.directive_kind == COMMISSION_QUEST for d in faction_directives):
                    urgency += 3.0

        # ── 3. Expected Benefit & Risk Calculations ─────────────────────────
        benefit = route.expected_benefit

        # Depletion-aware scaling for GATHER_RESOURCE routes:
        # benefit × (remaining_charges / max_charges) reduces attractiveness
        # of partially-depleted nodes linearly toward 0 as charges approach 0.
        if route.family == RouteFamily.GATHER_RESOURCE and resource_nodes is not None:
            node_id = route.target_node_id
            if node_id is not None:
                target_node = resource_nodes.get(node_id)
                if target_node is not None and target_node.max_charges > 0:
                    depletion_fraction = target_node.remaining_charges / target_node.max_charges
                    benefit = benefit * depletion_fraction

        # ── QUEST_OPPORTUNITY capability matching ─────────────────────────────
        # HERO entities score quests proportional to their capability match.
        # Non-HERO entities find quests half as attractive as generic harvesting.
        if route.family == RouteFamily.QUEST_OPPORTUNITY:
            from src.core.enums import EntityRole
            is_hero = entity.identity.role == EntityRole.HERO

            if is_hero:
                capability_match = 0.0
                opportunity = None
                if quest_registry is not None and route.quest_id is not None:
                    opportunity = quest_registry.get(route.quest_id)
                if opportunity is not None and opportunity.objective_chain:
                    entity_traits = {
                        t.split(":")[0].lower()
                        for t in (entity.identity.traits or set())
                    }
                    required_verbs = {
                        token.split(":")[0].lower()
                        for token in opportunity.objective_chain
                    }
                    if required_verbs:
                        matched_count = len(entity_traits & required_verbs)
                        ratio = matched_count / len(required_verbs)
                        if ratio >= 1.0:
                            capability_match = 1.0
                        elif ratio > 0.0:
                            capability_match = 0.5
                benefit = benefit * (1.0 + capability_match)
            else:
                # Non-HERO entities find quest opportunities less attractive
                benefit = benefit * 0.5

        # Risk penalty deflated by bravery, inflated by caution
        risk_multiplier = max(0.1, (1.0 + caution * 0.8) - bravery * 0.6)
        risk_penalty = route.expected_risk * risk_multiplier * 0.5

        # ── 4. Personality Biases ───────────────────────────────────────────
        personality_bias = 0.0

        # Weight calibration (E11C, 2026-06-28): greed and sociability raised from
        # 0.25 to 0.50/0.40 after E11B audit showed Δ<0.05 at uniform 0.25.
        # Bravery already exerts strong influence via risk_multiplier (multiplicative).
        if route.family == RouteFamily.RECOVER:
            personality_bias += caution * 0.25
        elif route.family in (RouteFamily.GATHER_RESOURCE, RouteFamily.SELL_LOOT_FOR_GOLD, RouteFamily.TAKE_EASY_QUEST):
            personality_bias += greed * 0.50
        elif route.family in (RouteFamily.ASK_INFORMATION, RouteFamily.SCOUT_LOCATION):
            personality_bias += curiosity * 0.25
        elif route.family in (RouteFamily.CRAFT_UPGRADE, RouteFamily.GATHER_RESOURCE):
            personality_bias += industry * 0.25
        elif route.family == RouteFamily.FORM_PARTY:
            personality_bias += sociability * 0.40
        elif route.family == RouteFamily.QUEST_OPPORTUNITY:
            personality_bias += greed * 0.50

        # ── 4b. Plan-Advance Bonus ──────────────────────────────────────────
        # +1.5 flat bonus when this route's family matches the head BuildGoal's
        # target_route_family and that goal is pending or in_progress.
        plan_advance_bonus = 0.0
        if progression_plan is not None and progression_plan.goal_queue:
            head_goal = progression_plan.goal_queue[0]
            if head_goal.status in ("pending", "in_progress"):
                if route.family.value == head_goal.target_route_family:
                    plan_advance_bonus = 1.5
        plan_advance_bonus = min(plan_advance_bonus, 3.0)

        # ── 4c. Memory-Informed Advice Adjustment (TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING) ──
        # Reads only the entity's own subjective causal-memory beliefs (never state/world truth).
        # Fixed ±1.0 magnitude, boolean-gated per advice string (not accumulated per matching
        # entry) so a full 30-entry causal-memory buffer with many matching entries still produces
        # exactly one adjustment per mapped family, never a growing stack.
        memory_adjustment = 0.0
        causal_entries = entity.cognition.memory.causal.entries
        if causal_entries:
            has_avoid_enemy = any(
                "avoid_enemy" in e.future_advice for e in causal_entries
            )
            has_boost_party_trust = any(
                "boost_party_trust" in e.future_advice for e in causal_entries
            )
            if has_avoid_enemy and route.family == RouteFamily.HUNT_WEAK_ENEMY:
                memory_adjustment -= 1.0
            if has_boost_party_trust and route.family == RouteFamily.FORM_PARTY:
                memory_adjustment += 1.0

        # ── 5. Confidence Bonus (TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING) ──────
        # For GATHER_RESOURCE/CRAFT_UPGRADE routes with a resolvable capability key,
        # confidence_bonus is fed by an ad-hoc CapabilityEstimateService.estimate() call
        # (entity-owned combat/stamina/inventory/equipment only) instead of the flat
        # generation-time route.confidence constant. Replacement of the term's input
        # source, not a new additive term -- weight stays 0.15. Never touches
        # entity.self_model.capabilities (stays empty in production); this is a
        # scorer-local, throwaway read, never written back to durable entity state.
        confidence_bonus = route.confidence * 0.15
        capability_estimate_value = None

        if (
            route.family == RouteFamily.GATHER_RESOURCE
            and resource_nodes is not None
            and route.target_node_id is not None
        ):
            gather_node = resource_nodes.get(route.target_node_id)
            if gather_node is not None:
                resource_kind = gather_node.kind
                required_tool = None
                for req in route.requirements:
                    if req.kind == "has_item" and req.subject:
                        required_tool = req.subject
                        break
                # Review round-1 fix: only take the capability-estimate path when a real tool
                # requirement exists. Without this gate, resource_data={} for tool-less resources
                # makes CapabilityEstimateService.estimate() default has_tool=True
                # (capability_estimate.py:179), always returning a non-None estimate and silently
                # switching off the flat term for every resolvable GATHER_RESOURCE route --
                # including the common case where no tool is required at all. There is nothing
                # capability-relevant to estimate when no tool requirement exists, so the flat
                # term is correctly kept in that case.
                if required_tool is not None:
                    resource_data = {resource_kind: {"required_tool": required_tool}}
                    cap_component = CapabilityEstimateService.estimate(
                        entity,
                        context=CapabilityContext(
                            gather_resources=(resource_kind,), resource_data=resource_data
                        ),
                    )
                    cap_estimate = cap_component.estimates.get(f"gather.resource.{resource_kind}")
                    if cap_estimate is not None:
                        capability_estimate_value = cap_estimate.estimate

        elif route.family == RouteFamily.CRAFT_UPGRADE:
            recipe_id = None
            gold_cost = 0
            requires_items: Dict[str, int] = {}
            for req in route.requirements:
                if req.kind == "recipe_known" and req.subject:
                    recipe_id = req.subject
                elif req.kind == "has_gold":
                    gold_cost = req.quantity
                elif req.kind == "has_item" and req.subject:
                    requires_items[req.subject] = req.quantity
            if recipe_id is not None:
                cap_component = CapabilityEstimateService.estimate(
                    entity,
                    context=CapabilityContext(
                        craft_recipes=(recipe_id,),
                        recipe_data={
                            recipe_id: {"requires_items": requires_items, "gold_cost": gold_cost}
                        },
                    ),
                )
                cap_estimate = cap_component.estimates.get(f"craft.recipe.{recipe_id}")
                if cap_estimate is not None:
                    capability_estimate_value = cap_estimate.estimate

        if capability_estimate_value is not None:
            confidence_bonus = capability_estimate_value * 0.15

        # ── 6. Blocker Penalty ───────────────────────────────────────────────
        blocker_penalty = 0.0
        if route.blockers:
            blocker_penalty = 2.0  # massive penalty for blocked routes

        # ── 7. Calculate Final Score ─────────────────────────────────────────
        final_score = urgency + benefit + personality_bias + plan_advance_bonus + memory_adjustment + confidence_bonus - risk_penalty - blocker_penalty
        final_score = round(max(0.0, final_score), 4)

        # ── 8. Class-Synergy Multipliers (SOC-229) ───────────────────────────
        # Applied only when group context is provided.  Read-only — no mutation.
        if group is not None:
            from src.core.enums import EntityRole
            roles_set = set(group.roles.values())

            # WARRIOR + MAGE pair: boost combat (HUNT_WEAK_ENEMY) routes by 15 %
            if (
                route.family == RouteFamily.HUNT_WEAK_ENEMY
                and "WARRIOR" in roles_set
                and "MAGE" in roles_set
            ):
                final_score = round(final_score * 1.15, 4)

            # HERO entity: boost quest-opportunity routes by 10 %
            if (
                route.family == RouteFamily.QUEST_OPPORTUNITY
                and entity.identity.role == EntityRole.HERO
            ):
                final_score = round(final_score * 1.10, 4)

        # ── 9. Escort Scoring (SOC-230) ──────────────────────────────────────────
        # Applies when: group context present, group has an escort_target_id set,
        # and this entity is NOT the escort target (targets don't protect themselves).
        if (
            group is not None
            and group.escort_target_id is not None
            and entity.id != group.escort_target_id
        ):
            if route.family == RouteFamily.PROTECT_TARGET:
                final_score = round(final_score + 3.0, 4)
            elif route.family == RouteFamily.OWN_SURVIVAL:
                final_score = round(max(0.0, final_score - 1.0), 4)

        return dataclasses.replace(
            route,
            score=final_score,
            urgency=round(urgency, 4),
            benefit_score=round(benefit, 4),
            personality_bias=round(personality_bias, 4),
            plan_advance_bonus=round(plan_advance_bonus, 4),
            memory_adjustment=round(memory_adjustment, 4),
            confidence_bonus=round(confidence_bonus, 4),
            risk_penalty=round(risk_penalty, 4),
            blocker_penalty=round(blocker_penalty, 4),
        )

"""
src/domains/adventure/scoring.py
───────────────────────────────────────────────────────────────────────────────
Phase 3 — AdventureRouteScorer

Implements subjective route scoring with imperfect decision personality bias.
Reads only subjective self-model aspects to protect information opacity.
"""

from __future__ import annotations
import dataclasses
from typing import TYPE_CHECKING, Any, Dict, Optional

from src.core.state import EntityState, ResourceNodeState
from src.domains.adventure.schema import RouteFamily, AdventureRouteOption

if TYPE_CHECKING:
    from src.core.models.quests import QuestOpportunity


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
    ) -> AdventureRouteOption:
        """
        Calculate subjective score for the route option and return updated option.
        Formula:
            score = urgency + benefit + personality_bias + confidence_bonus - risk_penalty - blocker_penalty
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

        if route.family == RouteFamily.RECOVER:
            # Cautious entities prefer recovery
            personality_bias += caution * 0.25
        elif route.family in (RouteFamily.GATHER_RESOURCE, RouteFamily.SELL_LOOT_FOR_GOLD, RouteFamily.TAKE_EASY_QUEST):
            # Greedy entities prefer gold/loot routes
            personality_bias += greed * 0.25
        elif route.family in (RouteFamily.ASK_INFORMATION, RouteFamily.SCOUT_LOCATION):
            # Curious entities prefer information/scouting
            personality_bias += curiosity * 0.25
        elif route.family in (RouteFamily.CRAFT_UPGRADE, RouteFamily.GATHER_RESOURCE):
            # Industrious entities prefer craft/gather
            personality_bias += industry * 0.25
        elif route.family == RouteFamily.FORM_PARTY:
            # Sociable entities prefer parties
            personality_bias += sociability * 0.25
        elif route.family == RouteFamily.QUEST_OPPORTUNITY:
            # Greedy entities are drawn to quest rewards (gold, loot)
            personality_bias += greed * 0.25

        # ── 5. Confidence Bonus ─────────────────────────────────────────────
        confidence_bonus = route.confidence * 0.15

        # ── 6. Blocker Penalty ───────────────────────────────────────────────
        blocker_penalty = 0.0
        if route.blockers:
            blocker_penalty = 2.0  # massive penalty for blocked routes

        # ── 7. Calculate Final Score ─────────────────────────────────────────
        final_score = urgency + benefit + personality_bias + confidence_bonus - risk_penalty - blocker_penalty
        final_score = round(max(0.0, final_score), 4)

        return dataclasses.replace(
            route,
            score=final_score,
            urgency=round(urgency, 4),
            benefit_score=round(benefit, 4),
            personality_bias=round(personality_bias, 4),
            confidence_bonus=round(confidence_bonus, 4),
            risk_penalty=round(risk_penalty, 4),
            blocker_penalty=round(blocker_penalty, 4),
        )

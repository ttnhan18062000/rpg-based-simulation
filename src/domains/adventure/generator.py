"""
src/domains/adventure/generator.py
───────────────────────────────────────────────────────────────────────────────
Phase 3 — AdventureRouteGenerator

Translates entity self-model aspects and visible world opportunities
into candidate AdventureRouteOption records.
"""

from __future__ import annotations
from typing import Any, List, Sequence, Optional, Dict, Tuple

from src.core.state import EntityState
from src.world.providers.resources import Opportunity
from src.domains.adventure.schema import RouteFamily, AdventureRouteOption


class AdventureRouteGenerator:
    """
    State-free generator producing subjective candidate route options.
    Does not score or select, only compiles what is available or blocked.
    """

    @staticmethod
    def generate(
        entity: EntityState,
        state: Any = None,
        opportunities: Sequence[Opportunity] = (),
    ) -> Tuple[AdventureRouteOption, ...]:
        """
        Generate candidate RouteOption instances for the given entity.
        Capped to prevent performance bloat.
        """
        opts: List[AdventureRouteOption] = []
        seen_families = set()

        # Map dynamic opportunity kinds to strategic route families
        kind_map = {
            "gather_resource": RouteFamily.GATHER_RESOURCE,
            "buy_item": RouteFamily.BUY_UPGRADE,
            "craft_item": RouteFamily.CRAFT_UPGRADE,
            "repair_gear": RouteFamily.RECOVER,
            "ask_information": RouteFamily.ASK_INFORMATION,
            "rest_inn": RouteFamily.RECOVER,
        }

        # 1. Process visible opportunities
        for opp in opportunities:
            family = kind_map.get(opp.kind)
            if not family:
                continue

            # Check if any blocker requirement fails
            blockers: List[str] = []
            for req in getattr(opp, "requirements", ()):
                # If quantity gold needed > gold held, add a blocker reason
                if req.kind == "has_gold":
                    gold_held = getattr(entity.inventory, "gold", 0)
                    if gold_held < req.quantity:
                        blockers.append(f"insufficient_gold:{req.quantity - gold_held}")
                elif req.kind == "has_item":
                    # Check items in inventory
                    item_count = 0
                    for stack in getattr(entity.inventory, "items", []):
                        if getattr(stack, "item_id", None) == req.subject:
                            item_count += getattr(stack, "quantity", 1)
                    if item_count < req.quantity:
                        blockers.append(f"missing_item:{req.subject}:{req.quantity - item_count}")

            # Extract integer node ID for GATHER_RESOURCE routes (used by depletion scorer)
            target_node_id = None
            if opp.kind == "gather_resource":
                try:
                    target_node_id = int(opp.target_id)
                except (ValueError, TypeError):
                    target_node_id = None

            opts.append(
                AdventureRouteOption(
                    family=family,
                    score=0.0,  # scored by scoring service
                    confidence=opp.confidence,
                    expected_benefit=opp.estimated_reward / 100.0,
                    expected_risk=opp.estimated_risk,
                    requirements=opp.requirements,
                    blockers=tuple(blockers),
                    source_opportunity_ids=(opp.id,),
                    reason=f"Backed by opportunity {opp.id} ({opp.subject})",
                    target_node_id=target_node_id,
                )
            )

        # 2. Add structural default routes based on needs
        weaknesses = getattr(entity.self_model.self_awareness, "perceived_weaknesses", ())
        needs = getattr(entity.self_model.needs, "active_needs", {})

        if "low_health" in weaknesses or "healing" in needs:
            if RouteFamily.RECOVER not in seen_families:
                opts.append(
                    AdventureRouteOption(
                        family=RouteFamily.RECOVER,
                        score=0.0,
                        confidence=0.9,
                        expected_benefit=0.8,
                        expected_risk=0.0,
                        reason="Forced recovery due to perceived low health weakness"
                    )
                )

        if "weak_weapon" in weaknesses or "equipment_improvement" in needs:
            # If blacksmith craft or shop buy option isn't already present, suggest exploring or seeking info
            if not any(o.family in (RouteFamily.BUY_UPGRADE, RouteFamily.CRAFT_UPGRADE) for o in opts):
                opts.append(
                    AdventureRouteOption(
                        family=RouteFamily.ASK_INFORMATION,
                        score=0.0,
                        confidence=0.8,
                        expected_benefit=0.6,
                        expected_risk=0.1,
                        reason="Explore upgrades via information gathering"
                    )
                )

        # 3. Add default Defer route if empty or fallback is needed
        if not opts:
            opts.append(
                AdventureRouteOption(
                    family=RouteFamily.DEFER_WITH_REASON,
                    score=0.01,
                    confidence=1.0,
                    expected_benefit=0.0,
                    expected_risk=0.0,
                    reason="no active opportunities or structural needs identified; deferring."
                )
            )

        # Ensure result count is strictly capped to prevent O(N) evaluation blowup
        capped_opts = opts[:25]

        return tuple(capped_opts)

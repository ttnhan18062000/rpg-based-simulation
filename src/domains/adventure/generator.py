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

            # Extract integer node/building ref id when the backing opportunity's
            # target_id resolves to one (used by the depletion scorer for
            # GATHER_RESOURCE, and by tactical.py's position resolution for any
            # opportunity-backed objective).
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

        # 3. Party formation route when entity is sociable and allied candidates exist (SOC-231)
        if state is not None and hasattr(state, "entities") and RouteFamily.FORM_PARTY not in seen_families:
            personality = getattr(entity.identity, "personality", None)
            sociability = getattr(personality, "sociability", 0.0) if personality else 0.0
            if sociability >= 0.2:
                from src.core.enums import EntityRole
                from src.systems.social_systems.party_composition import PartyCompositionScorer
                candidates = [
                    e for e in state.entities.values()
                    if e.id != entity.id
                    and getattr(e.identity, "role", EntityRole.MONSTER) != EntityRole.MONSTER
                    and getattr(e, "is_alive", True)
                ]
                if candidates:
                    trust_term = PartyCompositionScorer.score_trust_bonds(entity, candidates[:8])
                    comp_score = PartyCompositionScorer.score(candidates[:8], actor=entity)
                    # E43G: block FORM_PARTY if any candidate is a nemesis.
                    # TCK-20260904-SOCIAL-NEMESIS-ROLE-PRECEDENCE: also check the canonical
                    # SocialComponent.nemesis_ids field, not just the strategic-blocker proxy --
                    # a candidate promoted to nemesis via real grudge_history (>= 3.0) was
                    # previously not blocked here at all unless a separate, unrelated SOCIAL
                    # strategic blocker happened to also exist for the same target.
                    from src.core.strategic import BlockerKind
                    blocker_nemesis_ids = {
                        int(b.subject)
                        for b in entity.strategic.blockers.values()
                        if b.kind == BlockerKind.SOCIAL and b.subject.isdigit()
                    }
                    all_nemesis_ids = blocker_nemesis_ids | entity.social.nemesis_ids
                    nemesis_in_candidates = any(c.id in all_nemesis_ids for c in candidates)
                    route_blockers = ("nemesis_block",) if nemesis_in_candidates else ()
                    opts.append(
                        AdventureRouteOption(
                            family=RouteFamily.FORM_PARTY,
                            score=0.0,
                            confidence=min(
                                1.0,
                                max(
                                    0.0,
                                    sociability + 0.3
                                    + PartyCompositionScorer.TRUST_BONUS_WEIGHT * trust_term,
                                ),
                            ),
                            expected_benefit=max(0.3, comp_score),
                            expected_risk=0.1,
                            blockers=route_blockers,
                            reason=(
                                f"Party formation: {len(candidates)} candidates, "
                                f"comp_score={comp_score:.2f}, trust_term={trust_term:.2f}"
                                + (" [nemesis block]" if route_blockers else "")
                            ),
                        )
                    )

        # 4. Add default Defer route if empty or fallback is needed
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

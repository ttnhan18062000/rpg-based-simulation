from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from src.core.state import EntityState
from src.core.strategic import LeadState, LeadCertainty
from src.core.registries import ResourceRegistry, RecipeRegistry, ItemRegistry


@dataclass(frozen=True, slots=True)
class KnowledgeFact:
    subject: str
    fact_type: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InformationQuery:
    kind: str
    subject: str
    actor_id: int


@dataclass(frozen=True, slots=True)
class InformationResponse:
    answer_kind: str  # "known" | "partial" | "unknown" | "insufficient_gold"
    facts: Tuple[KnowledgeFact, ...] = field(default_factory=tuple)
    unknowns: Tuple[str, ...] = field(default_factory=tuple)
    suggested_leads: Tuple[LeadState, ...] = field(default_factory=tuple)
    certainty: float = 0.0
    source_id: Optional[str] = None
    cost_gold: int = 0


class GuideInformationProvider:
    """
    Exposes environmental and resource information.
    decidedly state-free.
    """

    @staticmethod
    def query(
        entity: EntityState,
        query: InformationQuery
    ) -> InformationResponse:
        cost = 10 if query.subject == "moon_resin" else 0
        gold_held = getattr(entity.inventory, "gold", 0)
        
        if gold_held < cost:
            return InformationResponse(
                answer_kind="insufficient_gold",
                cost_gold=cost
            )

        if query.kind == "material_source":
            # Direct interception for the rare/secret Phase 1 material "moon_resin"
            if query.subject == "moon_resin":
                lead = LeadState(
                    id="lead_moon_resin_north_ruin",
                    kind="location",
                    subject="material.moon_resin.source",
                    detail="north_ruin",
                    certainty=LeadCertainty.APPROXIMATE,
                    source_entity_id=None,
                    discovered_tick=0
                )
                return InformationResponse(
                    answer_kind="partial",
                    unknowns=("material.moon_resin.source",),
                    suggested_leads=(lead,),
                    certainty=0.55,
                    source_id="guide_hometown",
                    cost_gold=cost
                )

            # Normal resource query
            # Search resource node definitions for matching yield item
            matched_res = None
            for res in ResourceRegistry.all().values():
                if res.yield_item == query.subject:
                    matched_res = res
                    break

            if matched_res:
                fact = KnowledgeFact(
                    subject=query.subject,
                    fact_type="resource_source",
                    details={
                        "yield_item": matched_res.yield_item,
                        "source_regions": list(matched_res.source_region_tags),
                        "required_tool": matched_res.required_tool
                    }
                )
                return InformationResponse(
                    answer_kind="known",
                    facts=(fact,),
                    certainty=1.0,
                    source_id="guide_hometown",
                    cost_gold=cost
                )

        return InformationResponse(
            answer_kind="unknown",
            unknowns=(query.subject,),
            cost_gold=cost
        )


class BlacksmithInformationProvider:
    """
    Exposes crafting recipe costs and item requirements.
    """

    @staticmethod
    def query(
        entity: EntityState,
        query: InformationQuery
    ) -> InformationResponse:
        if query.kind == "recipe_requirements":
            recipe_id = query.subject
            if RecipeRegistry.contains(recipe_id):
                recipe = RecipeRegistry.get(recipe_id)
                fact = KnowledgeFact(
                    subject=recipe_id,
                    fact_type="recipe_definition",
                    details={
                        "requires_items": recipe.requires_items,
                        "gold_cost": recipe.gold_cost,
                        "output_item_id": recipe.output_item_id
                    }
                )
                return InformationResponse(
                    answer_kind="known",
                    facts=(fact,),
                    certainty=1.0,
                    source_id="blacksmith_hometown"
                )

        return InformationResponse(
            answer_kind="unknown",
            unknowns=(query.subject,)
        )


class GuildInformationProvider:
    """
    Exposes active quest boards and regional danger metrics.
    """

    @staticmethod
    def query(
        entity: EntityState,
        query: InformationQuery
    ) -> InformationResponse:
        # Mock / simple guild intelligence mapping for Phase 1
        if query.kind == "regional_danger":
            fact = KnowledgeFact(
                subject=query.subject,
                fact_type="danger_rating",
                details={
                    "region_id": query.subject,
                    "danger_rating": 2.0,
                    "enemy_archetypes": ["wolf", "goblin"]
                }
            )
            return InformationResponse(
                answer_kind="known",
                facts=(fact,),
                certainty=0.8,
                source_id="guild_hometown"
            )

        return InformationResponse(
            answer_kind="unknown",
            unknowns=(query.subject,)
        )

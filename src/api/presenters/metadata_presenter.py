"""Metadata presenter -- shapes CatalogRepository content into the /api/v1/metadata/* response
contract frontend/src/types/metadata.ts already defines (TCK-20260825-METADATA-API-BACKEND-MISSING).

Investigation found the frontend contract was written speculatively, ahead of any backend
implementation: several of its sub-fields have zero corresponding data anywhere in this
codebase (`ai_states`, `tiers`, `damage_types`, `skill_targets`, and nearly all of `classes`'
richer fields -- skills, race_skills, scaling_grades, mastery_tiers, and most of ClassEntry
itself). Per explicit user decision: return real data everywhere it genuinely exists, and
correctly-shaped empty/default data (never fabricated content) everywhere it doesn't -- each
documented inline below, not silently guessed.

Generic enum entries (EnumEntry{id: number, ...}) need a numeric id, but every real catalog
definition's own id is a string. Mirrors the existing stable-index convention this codebase
already uses for exactly this situation (StatePresenter.terrain_code_map: `sorted()`-order
0..n-1 assignment over the real distinct values, not an arbitrary/random one).
"""
from __future__ import annotations

from typing import Any, Dict, List

from src.content.repository import CatalogRepository
from src.core.classes import CLASS_REGISTRY
from src.core.enums import EntityRole


def _enum_entries(ids_and_texts: List[tuple]) -> List[Dict[str, Any]]:
    """Builds a stable-sorted list of {id, name, description} from (id_str, name, description)
    triples, assigning the numeric `id` field by sorted-id order (see module docstring)."""
    return [
        {"id": i, "name": name, "description": description}
        for i, (_orig_id, name, description) in enumerate(sorted(ids_and_texts, key=lambda t: t[0]))
    ]


class MetadataPresenter:
    @staticmethod
    def present_enums(catalog: CatalogRepository) -> Dict[str, Any]:
        # materials: mapped to real catalog.materials (crafting materials) for id/name -- the
        # richest real data available for this domain. `walkable` has no corresponding concept
        # anywhere for crafting materials (that's a terrain/occupancy property, computed
        # per-tile by LegalityServiceV2.verify_occupancy, never a static per-material flag) --
        # defaulted False for every entry, not fabricated per-material.
        materials = [
            {"id": i, "name": (m.display_name or m.id), "walkable": False}
            for i, m in enumerate(sorted(catalog.materials.values(), key=lambda d: d.id))
        ]

        # ai_states, tiers, damage_types, skill_targets: zero backing data anywhere in this
        # codebase (confirmed via repo-wide grep during investigation) -- correctly-shaped empty,
        # not fabricated.
        ai_states: List[Dict[str, Any]] = []
        tiers: List[Dict[str, Any]] = []
        damage_types: List[Dict[str, Any]] = []

        # rarities: no described-enum registry exists, but ItemDefinition.rarity is a real
        # free-string field on every real item -- derived from the distinct values actually used
        # across catalog.items (real, not fabricated), each with an empty description (no
        # authoritative description text exists for any rarity tier).
        rarity_values = sorted({it.rarity for it in catalog.items.values()})
        rarities = _enum_entries([(v, v, "") for v in rarity_values])

        # item_types: ItemDefinition has no discrete "item_type" field, only a `categories` tag
        # list (e.g. ["weapon", "melee"]) -- the first category is the primary type tag per its
        # own field docstring ("e.g. weapon, melee, material"). Derived from the distinct
        # first-categories actually used across catalog.items (real, not fabricated).
        item_type_values = sorted({
            it.categories[0] for it in catalog.items.values() if it.categories
        })
        item_types = _enum_entries([(v, v, "") for v in item_type_values])

        elements = _enum_entries([
            (e.id, (e.display_name or e.id), (e.description or "")) for e in catalog.elements.values()
        ])

        entity_roles = [
            {"id": int(role), "name": role.name.title(), "description": ""}
            for role in EntityRole
        ]

        factions = [
            {"id": i, "name": (f.display_name or f.id)}
            for i, f in enumerate(sorted(catalog.factions.values(), key=lambda d: d.id))
        ]
        faction_index = {f.id: i for i, f in enumerate(sorted(catalog.factions.values(), key=lambda d: d.id))}
        faction_relations = [
            {
                "faction_a": faction_index.get(r.source_faction, -1),
                "faction_b": faction_index.get(r.target_faction, -1),
                "relation": r.relationship_model,
            }
            for r in catalog.faction_relationships.values()
            if r.source_faction in faction_index and r.target_faction in faction_index
        ]

        # entity_kinds: same real source ManifestPresenter.present_manifest already uses for its
        # own entity_kinds field (catalog.entity_archetypes), reshaped from that route's
        # {def_id: display_name} dict into this route's {kind, faction} list contract.
        entity_kinds = [
            {"kind": a.id, "faction": a.faction}
            for a in catalog.entity_archetypes.values()
        ]

        return {
            "materials": materials,
            "ai_states": ai_states,
            "tiers": tiers,
            "rarities": rarities,
            "item_types": item_types,
            "damage_types": damage_types,
            "elements": elements,
            "entity_roles": entity_roles,
            "factions": factions,
            "faction_relations": faction_relations,
            "entity_kinds": entity_kinds,
        }

    @staticmethod
    def present_items(catalog: CatalogRepository) -> Dict[str, Any]:
        # Real: item_id, name, item_type (see item_types derivation above), rarity, gold_value.
        # Unbacked (no corresponding ItemDefinition field exists anywhere): weight and every
        # combat-stat bonus field, damage_type, element, heal_amount, mana_restore -- all
        # defaulted to 0/"" , never fabricated per-item values. sell_value reuses base_value
        # (documented assumption: no separate sell-price concept exists in the catalog).
        items = [
            {
                "item_id": it.id,
                "name": (it.display_name or it.id),
                "item_type": (it.categories[0] if it.categories else "misc"),
                "rarity": it.rarity,
                "weight": 0.0,
                "atk_bonus": 0.0, "def_bonus": 0.0, "spd_bonus": 0.0, "max_hp_bonus": 0.0,
                "crit_rate_bonus": 0.0, "evasion_bonus": 0.0, "luck_bonus": 0.0,
                "matk_bonus": 0.0, "mdef_bonus": 0.0,
                "damage_type": "", "element": "",
                "heal_amount": 0.0, "mana_restore": 0.0,
                "gold_value": it.base_value,
                "sell_value": it.base_value,
            }
            for it in catalog.items.values()
        ]
        return {"items": items}

    @staticmethod
    def present_classes() -> Dict[str, Any]:
        # Real: id, name (from the legacy 4-entry CLASS_REGISTRY -- confirmed the only class
        # registry in this codebase; no richer class content source exists anywhere).
        # Everything else ClassEntry/SkillDefEntry/etc. expects (description, tier, role, lore,
        # playstyle, attr_bonuses, cap_bonuses, scaling, skill_ids, breakthrough, skills,
        # race_skills, scaling_grades, mastery_tiers, skill_targets) has zero backing data
        # anywhere -- correctly-shaped empty/default, not fabricated.
        zero_attrs = {"str": 0, "agi": 0, "vit": 0, "int": 0, "spi": 0, "wis": 0, "end": 0, "per": 0, "cha": 0}
        empty_scaling = {"str": "", "agi": "", "vit": "", "int": "", "spi": "", "wis": "", "end": "", "per": "", "cha": ""}
        classes = [
            {
                "id": c.id,
                "name": c.name,
                "description": "",
                "tier": 1,
                "role": "",
                "lore": "",
                "playstyle": "",
                "attr_bonuses": dict(zero_attrs),
                "cap_bonuses": dict(zero_attrs),
                "scaling": dict(empty_scaling),
                "skill_ids": list(c.starting_skills),
                "breakthrough": None,
            }
            for c in CLASS_REGISTRY.values()
        ]
        return {
            "classes": classes,
            "skills": [],
            "race_skills": {},
            "scaling_grades": [],
            "mastery_tiers": [],
            "skill_targets": [],
        }

    @staticmethod
    def present_traits(catalog: CatalogRepository) -> Dict[str, Any]:
        traits = [
            {"trait_type": i, "name": (t.display_name or t.id), "description": (t.description or "")}
            for i, t in enumerate(sorted(catalog.traits.values(), key=lambda d: d.id))
        ]
        return {"traits": traits}

    @staticmethod
    def present_attributes(catalog: CatalogRepository) -> Dict[str, Any]:
        attributes = [
            {"key": a.id, "label": (a.display_name or a.id), "description": (a.description or "")}
            for a in catalog.attributes.values()
        ]
        return {"attributes": attributes}

    @staticmethod
    def present_buildings(catalog: CatalogRepository) -> Dict[str, Any]:
        building_types = [
            {"building_type": b.id, "name": (b.display_name or b.id), "description": (b.description or "")}
            for b in catalog.buildings.values()
        ]
        return {"building_types": building_types}

    @staticmethod
    def present_resources(catalog: CatalogRepository) -> Dict[str, Any]:
        # respawn_cooldown: no such concept exists on ResourceDefinition (only a fixed
        # default_charges count) -- defaulted 0, not fabricated.
        resource_types = [
            {
                "resource_type": (r.resource_type or r.id),
                "name": (r.display_name or r.id),
                "terrain": (r.preferred_biomes[0] if r.preferred_biomes else ""),
                "yields_item": (r.material or ""),
                "max_harvests": r.default_charges,
                "respawn_cooldown": 0,
                "harvest_ticks": r.required_ticks,
            }
            for r in catalog.resources.values()
        ]
        return {"resource_types": resource_types}

    @staticmethod
    def present_recipes(catalog: CatalogRepository) -> Dict[str, Any]:
        # catalog.recipes is the real, content-catalog-loaded recipe source (confirmed during
        # TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE's own investigation to be what
        # src/core/registries.py::RecipeRegistry bootstraps from -- the actually-live
        # crafting-execution path, not either of the 2 other disjoint/unreachable recipe
        # registries that ticket found).
        recipes = []
        for r in catalog.recipes.values():
            output_item = next(iter(r.outputs), "") if r.outputs else ""
            output_def = catalog.items.get(output_item)
            recipes.append({
                "recipe_id": r.id,
                "output_item": output_item,
                "output_name": (output_def.display_name if output_def else output_item),
                "gold_cost": r.gold_cost,
                "materials": dict(r.ingredients),
            })
        return {"recipes": recipes}

from typing import Dict, List, Set, Tuple, Any, Optional
from src.content.repository import CatalogRepository, CANONICAL_FAMILIES
from src.worldmodules.schema import WorldModuleSpec
from src.worldassembly.schema import WorldCompositionSpec

FAMILY_TO_SHORT = {
    "foundation.materials": "material",
    "foundation.traits": "trait",
    "foundation.themes": "theme",
    "foundation.relationship_axes": "relationship_axis",
    "foundation.attributes": "attribute",
    "foundation.elements": "element",
    "living.species": "species",
    "living.need_profiles": "need_profile",
    "living.sense_profiles": "sense_profile",
    "living.body_models": "body_model",
    "living.drive_profiles": "drive_profile",
    "living.cognition_profiles": "cognition_profile",
    "social.roles": "role",
    "social.factions": "faction",
    "social.perspectives": "perspective",
    "social.faction_relationships": "faction_relationship",
    "entities.stat_profiles": "stat_profile",
    "entities.combat_profiles": "combat_profile",
    "entities.inventory_profiles": "inventory_profile",
    "entities.skill_profiles": "skill_profile",
    "entities.populations": "population",
    "entities.entity_archetypes": "archetype",
    "world.buildings": "building",
    "world.terrain": "terrain",
    "world.services": "service",
    "world.regions": "region",
    "world.recipes": "recipe",
    "world.resources": "resource",
    "world.items": "item",
    "world.biomes": "biome",
    "world.ecologies": "ecology",
    "defaults": "defaults",
    "spawn_tables": "spawn_table",
    "compatibility.legacy_enemy_projection": "projection",
    "world_modules": "module",
    "world_compositions": "composition",
}

FIELD_TO_TARGET = {
    "species": "species",
    "body_model": "body_model",
    "need_profile": "need_profile",
    "sense_profile": "sense_profile",
    "cognition_profile": "cognition_profile",
    "default_cognition_profile": "cognition_profile",
    "drive_profile": "drive_profile",
    "stat_profile": "stat_profile",
    "default_stats_profile": "stat_profile",
    "combat_profile": "combat_profile",
    "inventory_profile": "inventory_profile",
    "default_inventory_profile": "inventory_profile",
    "skill_profile": "skill_profile",
    "role": "role",
    "compatible_roles": "role",
    "faction": "faction",
    "chosen_faction": "faction",
    "source_faction": "faction",
    "target_faction": "faction",
    "controlling_faction": "faction",
    "traits": "trait",
    "natural_traits": "trait",
    "compatible_traits": "trait",
    "themes": "theme",
    "biomes": "biome",
    "dominant_factions": "faction",
    "default_factions": "faction",
    "populations": "population",
    "resources": "resource",
    "services": "service",
    "required_service": "service",
    "service_profile_id": "service",
    "materials": "material",
    "common_materials": "material",
    "material": "material",
    "allowed_enemy_ids": "projection",
    "provided_items": "item",
    "ingredients": "item",
    "outputs": "item",
    "provided_recipes": "recipe",
    "archetype_id": "archetype",
    "members": "archetype",
    "spawn_regions": "region",
    "axes": "relationship_axis",
    "terrain_mix": "terrain",
    "biome": "biome",
    "spawn_weights": "role",
    "loot_table": "item",
    "requires": "module",
    "resource_bias": "item",
}


def extract_references_from_field(k: str, v: Any) -> List[Tuple[str, str]]:
    """Returns list of (target_concept, referenced_id)."""
    target = FIELD_TO_TARGET.get(k)
    if not target:
        if k == "projected_labels" and isinstance(v, dict):
            refs = []
            for sublist in v.values():
                if isinstance(sublist, list):
                    for item in sublist:
                        if isinstance(item, str):
                            refs.append(("faction", item))
            return refs
        return []

    # Case-insensitive terrain mapping
    if target == "terrain":
        if isinstance(v, str) and v:
            return [(target, v.lower())]
        elif isinstance(v, list):
            return [(target, x.lower()) for x in v if isinstance(x, str)]

    # Spawn table roles vs legacy enum values
    if k == "spawn_weights" and isinstance(v, dict):
        refs = []
        legacy_roles = {"hero", "shopkeeper", "monster", "citizen", "worker", "guard"}
        for key in v.keys():
            if isinstance(key, str):
                if key.lower() not in legacy_roles:
                    refs.append((target, key))
        return refs

    if isinstance(v, str):
        if v:
            return [(target, v)]
    elif isinstance(v, list):
        refs = []
        for item in v:
            if isinstance(item, str):
                refs.append((target, item))
        return refs
    elif isinstance(v, dict):
        refs = []
        for key in v.keys():
            if isinstance(key, str):
                refs.append((target, key))
        return refs
    return []


def find_references_recursive(data: Any) -> List[Tuple[str, str]]:
    """Recursively scans data structures for fields referencing other concepts."""
    refs = []
    if isinstance(data, dict):
        for k, v in data.items():
            extracted = extract_references_from_field(k, v)
            refs.extend(extracted)
            refs.extend(find_references_recursive(v))
    elif isinstance(data, list):
        for item in data:
            refs.extend(find_references_recursive(item))
    return refs


class ContentReferenceGraph:
    """Generic directed graph representing content definitions and their relationships."""

    def __init__(
        self,
        repo: CatalogRepository,
        modules: Optional[List[WorldModuleSpec]] = None,
        compositions: Optional[List[WorldCompositionSpec]] = None,
    ):
        self.nodes: Dict[str, Any] = {}  # node_id -> record object or metadata dict
        self.edges: Set[Tuple[str, str]] = set()  # source_id -> target_id
        self.adj: Dict[str, Set[str]] = {}  # source -> targets
        self.reverse_adj: Dict[str, Set[str]] = {}  # target -> sources
        self.edge_metadata: Dict[Tuple[str, str], Dict[str, Any]] = {}

        self._build_graph(repo, modules or [], compositions or [])

    def add_node(self, node_id: str, obj: Any) -> None:
        self.nodes[node_id] = obj
        if node_id not in self.adj:
            self.adj[node_id] = set()
        if node_id not in self.reverse_adj:
            self.reverse_adj[node_id] = set()

    def add_edge(self, source: str, target: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if source not in self.adj:
            self.adj[source] = set()
        if target not in self.reverse_adj:
            self.reverse_adj[target] = set()

        self.edges.add((source, target))
        self.adj[source].add(target)
        self.reverse_adj[target].add(source)
        if metadata:
            self.edge_metadata[(source, target)] = metadata

    def has_node(self, node_id: str) -> bool:
        return node_id in self.nodes

    def get_incoming_neighbors(self, node_id: str) -> Set[str]:
        return self.reverse_adj.get(node_id, set())

    def get_outgoing_neighbors(self, node_id: str) -> Set[str]:
        return self.adj.get(node_id, set())

    def is_record_used(self, node_id: str) -> bool:
        """Returns True if the record has at least one incoming edge."""
        return len(self.get_incoming_neighbors(node_id)) > 0

    def add_module_edges(self, normalized_module: "NormalizedWorldModule") -> None:
        """Add edges from a normalized module into the reference graph."""
        from src.worldmodules.normalizer import NormalizedWorldModule  # local import to avoid circular
        module_node = f"module:{normalized_module.module_id}"
        for b_id in normalized_module.biome_refs:
            self.add_edge(module_node, f"biome:{b_id}")
        for e_id in normalized_module.ecology_refs:
            self.add_edge(module_node, f"ecology:{e_id}")
        for p_id in normalized_module.population_refs:
            self.add_edge(module_node, f"population:{p_id}")
        for rel_id in normalized_module.relationship_refs:
            self.add_edge(module_node, f"faction_relationship:{rel_id}")
        for res_id, count in normalized_module.resources.items():
            self.add_edge(module_node, f"resource:{res_id}", {"count": count})
        for bld_id, count in normalized_module.buildings.items():
            self.add_edge(module_node, f"building:{bld_id}", {"count": count})
        for svc_id, count in normalized_module.services.items():
            self.add_edge(module_node, f"service:{svc_id}", {"count": count})

    def _build_graph(
        self,
        repo: CatalogRepository,
        modules: List[WorldModuleSpec],
        compositions: List[WorldCompositionSpec],
    ) -> None:
        # Add engine-supported terrains that may not be explicitly defined in catalog yaml files
        for t in {"grass", "floor", "hill", "sand"}:
            self.add_node(f"terrain:{t}", {"id": t, "display_name": t.capitalize(), "built_in": True})

        # 1. Add catalog records
        for spec in CANONICAL_FAMILIES:
            short_family = FAMILY_TO_SHORT.get(spec.family)
            if not short_family:
                continue

            records_dict = getattr(repo, spec.repository_index, {})
            for record_id, record in records_dict.items():
                node_id = f"{short_family}:{record_id}"
                self.add_node(node_id, record)

                # Scan model fields
                if hasattr(record, "model_dump"):
                    dump = record.model_dump()
                else:
                    dump = record.__dict__

                for k, v in dump.items():
                    # Skip administrative/metadata fields
                    if k in ("id", "display_name", "description", "tags", "schema_version", "deprecated", "metadata", "extension", "design_notes"):
                        continue
                    for target_concept, target_id in extract_references_from_field(k, v):
                        self.add_edge(node_id, f"{target_concept}:{target_id}")

        # 2. Add modules
        for module in modules:
            module_node = f"module:{module.module_id}"
            self.add_node(module_node, module)

            # Mapped dependencies
            for req in module.requires:
                self.add_edge(module_node, f"module:{req}")

            # Scan regions defined
            for reg in module.regions:
                reg_node = f"region:{reg.id}"
                self.add_node(reg_node, reg)
                self.add_edge(module_node, reg_node)
                # Scan region fields (terrain)
                if reg.terrain:
                    self.add_edge(reg_node, f"terrain:{reg.terrain.lower()}")

            # Scan recipes/V1 lists
            for pop in module.population_recipes:
                # Populations are defined by the module but reference other types
                # Add references from module to target roles/factions/profiles
                self.add_edge(module_node, f"role:{pop.role}")
                self.add_edge(module_node, f"faction:{pop.faction}")
                if pop.spawn_region:
                    self.add_edge(module_node, f"region:{pop.spawn_region}")
                if pop.stats_profile:
                    self.add_edge(module_node, f"stat_profile:{pop.stats_profile}")
                if pop.inventory_profile:
                    self.add_edge(module_node, f"inventory_profile:{pop.inventory_profile}")
                if pop.cognition_profile:
                    self.add_edge(module_node, f"cognition_profile:{pop.cognition_profile}")

            for res in module.resource_recipes:
                self.add_edge(module_node, f"resource:{res.resource_type}")
                self.add_edge(module_node, f"region:{res.region}")

            for bld in module.building_recipes:
                self.add_edge(module_node, f"building:{bld.building_type}")
                self.add_edge(module_node, f"region:{bld.region}")
                if bld.service_profile:
                    self.add_edge(module_node, f"service:{bld.service_profile}")

            # Scan V2 layout lists and dict refs via normalized module
            from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
            normalized = WorldModuleAuthoringNormalizer.normalize(module)
            for faction in module.factions:
                self.add_edge(module_node, f"faction:{faction}")
            self.add_module_edges(normalized)

        # 3. Add compositions
        for comp in compositions:
            comp_node = f"composition:{comp.world_id}"
            self.add_node(comp_node, comp)

            # Check module_refs
            if comp.module_refs:
                for ref in comp.module_refs:
                    self.add_edge(comp_node, f"module:{ref.module_id}")
            # Check modules list shorthand if not normalized
            if hasattr(comp, "modules") and comp.modules:
                for mod_id in comp.modules:
                    self.add_edge(comp_node, f"module:{mod_id}")

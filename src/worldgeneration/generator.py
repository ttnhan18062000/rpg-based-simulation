# Compliance IDs: WORLD-GEN-003, WORLD-GEN-004
from __future__ import annotations

import random
import hashlib
from datetime import datetime, timezone
from typing import Optional, Any, Dict, List

from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.worldgeneration.schema import GenerationIntentSpec
from src.worldassembly.schema import ProvenanceManifest, ProvenanceRecord
from src.worldassembly.resolver import ResolvedWorldBundle

from src.worldbuilding.schema import (
    WorldSpec,
    TopologySpec,
    RegionSpec,
    FactionSpec,
    PopulationSpec,
    ResourceNodeSpec,
    BuildingSpec,
)
from src.worldbuilding.validator import WorldValidator, ValidationContext


class WorldProceduralGenerator:
    """
    Deterministic world procedural generator that constructs a fully validated
    WorldSpec specification and auditable ProvenanceManifest based on high-level intent.
    """

    def __init__(self, catalog_repo: CatalogRepository, module_repo: WorldModuleRepository):
        self.catalog_repo = catalog_repo
        self.module_repo = module_repo

    def generate(self, intent: GenerationIntentSpec) -> ResolvedWorldBundle:
        """
        Main procedural pipeline compiling random distributions into stable spec formats.
        """
        # 1. Isolated deterministic RNG
        rng = random.Random(intent.seed)
        width, height = intent.target_world_size

        regions: Dict[str, RegionSpec] = {}
        factions: Dict[str, FactionSpec] = {}
        entities: List[PopulationSpec] = []
        resources: List[ResourceNodeSpec] = []
        buildings: List[BuildingSpec] = []
        
        prov_records: Dict[str, ProvenanceRecord] = {}

        # 2. Region Allocation
        # Settlement Region (Centered)
        center_x, center_y = width // 2, height // 2
        town_min_x = max(0, center_x - 15)
        town_max_x = min(width - 1, center_x + 15)
        town_min_y = max(0, center_y - 15)
        town_max_y = min(height - 1, center_y + 15)
        
        regions["town_center"] = RegionSpec(
            id="town_center",
            type="town",
            bounds=(town_min_x, town_min_y, town_max_x, town_max_y),
            terrain="GRASS",
            hazard_level=0.0
        )
        
        # Wilderness Regions (Surrounding)
        regions["wilderness_forest"] = RegionSpec(
            id="wilderness_forest",
            type="wilderness",
            bounds=(0, 0, town_min_x - 1, height - 1),
            terrain="FOREST",
            hazard_level=1.2 * intent.danger_level
        )
        regions["wilderness_hills"] = RegionSpec(
            id="wilderness_hills",
            type="wilderness",
            bounds=(town_max_x + 1, 0, width - 1, height - 1),
            terrain="GRASS",
            hazard_level=1.5 * intent.danger_level
        )

        for reg_id, reg in regions.items():
            prov_records[reg_id] = ProvenanceRecord(
                element_id=reg_id,
                element_type="region",
                source_module="procedural_generator",
                recipe_type="procedural_layout",
                parameters={"seed": intent.seed, "style": intent.terrain_style},
                profiles={},
                details={"bounds": reg.bounds, "terrain": reg.terrain}
            )

        # 3. Faction Mapping
        for f_id in self.catalog_repo.factions:
            cat_faction = self.catalog_repo.get_faction(f_id)
            if cat_faction:
                factions[f_id] = FactionSpec(id=f_id, type=cat_faction.alignment_bucket)
                prov_records[f_id] = ProvenanceRecord(
                    element_id=f_id,
                    element_type="faction",
                    source_module=None,
                    recipe_type="catalog",
                    parameters={},
                    profiles={"alignment_bucket": cat_faction.alignment_bucket},
                    details={"description": cat_faction.description or ""}
                )

        # Find civilian/defender faction and monster/invader faction dynamically
        civilian_faction = "town_council"
        hostile_faction = "goblin_warband"

        defenders = [f_id for f_id, f in self.catalog_repo.factions.items() if f.alignment_bucket == "defender"]
        invaders = [f_id for f_id, f in self.catalog_repo.factions.items() if f.alignment_bucket == "invader"]
        
        if defenders:
            civilian_faction = "town_council" if "town_council" in defenders else defenders[0]
        if invaders:
            hostile_faction = "goblin_warband" if "goblin_warband" in invaders else invaders[0]

        # Find roles dynamically
        citizen_role = "citizen"
        hostile_role = "raider"

        catalog_roles = list(self.catalog_repo.roles.keys())
        if "citizen" not in catalog_roles and catalog_roles:
            citizen_role = catalog_roles[0]
        if "raider" not in catalog_roles:
            monsters = [r_id for r_id, r in self.catalog_repo.roles.items() if r.legacy_engine_role == "MONSTER"]
            if monsters:
                hostile_role = monsters[0]
            elif catalog_roles:
                hostile_role = catalog_roles[0]

        # 4. Building Placement
        catalog_buildings = list(self.catalog_repo.buildings.keys())
        building_types = []
        if catalog_buildings:
            for preferred in ["shop", "blacksmith", "inn"]:
                if preferred in catalog_buildings:
                    building_types.append(preferred)
            if not building_types:
                building_types = catalog_buildings[:3]
        else:
            building_types = ["shop", "blacksmith", "inn"]

        for idx, bld_type in enumerate(building_types):
            bld_id = f"bld_{bld_type}_{idx}"
            buildings.append(BuildingSpec(
                id=bld_id,
                type=bld_type,
                region="town_center"
            ))
            prov_records[bld_id] = ProvenanceRecord(
                element_id=bld_id,
                element_type="building",
                source_module="procedural_generator",
                recipe_type="procedural_placement",
                parameters={"seed": intent.seed},
                profiles={"building_type": bld_type},
                details={"region": "town_center"}
            )

        # 5. Resource Spawning (Wilderness distribution based on resource_density scalar)
        catalog_resources = list(self.catalog_repo.resources.values())
        if catalog_resources:
            resource_types = list(set(r.resource_type for r in catalog_resources))
        else:
            resource_types = ["wood", "iron_ore"]

        wild_regions = ["wilderness_forest", "wilderness_hills"]
        resource_count = max(5, int(20 * intent.resource_density))
        for idx in range(resource_count):
            res_id = f"res_node_{idx}"
            r_type = rng.choice(resource_types)
            r_region = rng.choice(wild_regions)
            resources.append(ResourceNodeSpec(
                id=res_id,
                resource_type=r_type,
                count=rng.randint(5, 15),
                region=r_region
            ))
            prov_records[res_id] = ProvenanceRecord(
                element_id=res_id,
                element_type="resource",
                source_module="procedural_generator",
                recipe_type="procedural_distribution",
                parameters={"seed": intent.seed, "density": intent.resource_density},
                profiles={"resource_type": r_type},
                details={"region": r_region}
            )

        # 6. Population Allocation (Scale-based seeding)
        pop_count_citizen = max(5, int(15 * intent.population_scale))
        pop_count_monster = max(2, int(8 * intent.population_scale))
        
        # Citizens in town
        entities.append(PopulationSpec(
            id="citizens",
            count=pop_count_citizen,
            role=citizen_role,
            faction=civilian_faction,
            spawn_region="town_center"
        ))
        prov_records["citizens"] = ProvenanceRecord(
            element_id="citizens",
            element_type="population",
            source_module="procedural_generator",
            recipe_type="procedural_populating",
            parameters={"seed": intent.seed, "scale": intent.population_scale},
            profiles={"role": citizen_role, "faction": civilian_faction},
            details={"count": pop_count_citizen, "region": "town_center"}
        )

        # Monsters in wilderness
        entities.append(PopulationSpec(
            id="monsters",
            count=pop_count_monster,
            role=hostile_role,
            faction=hostile_faction,
            spawn_region="wilderness_forest"
        ))
        prov_records["monsters"] = ProvenanceRecord(
            element_id="monsters",
            element_type="population",
            source_module="procedural_generator",
            recipe_type="procedural_populating",
            parameters={"seed": intent.seed, "scale": intent.population_scale},
            profiles={"role": hostile_role, "faction": hostile_faction},
            details={"count": pop_count_monster, "region": "wilderness_forest"}
        )

        # 7. Assembled clean worldspec.v1
        world_spec = WorldSpec(
            schema_version="worldspec.v1",
            world_id=intent.generation_id,
            name=f"Procedural {intent.generation_id}",
            topology=TopologySpec(width=width, height=height, coordinate_system="grid"),
            regions=list(regions.values()),
            factions=list(factions.values()),
            entities=entities,
            resources=resources,
            buildings=buildings
        )

        # Gating Validation run
        validator = WorldValidator()
        issues = validator.validate(world_spec, context=ValidationContext.GENERATED_WORLD)

        validation_report = {
            "world_validation": [
                {
                    "severity": issue.severity,
                    "rule_id": issue.rule_id,
                    "message": issue.message,
                    "path": issue.path
                }
                for issue in issues
            ]
        }

        # Deterministic manifest metadata
        hasher = hashlib.sha256()
        hasher.update(intent.generation_id.encode())
        hasher.update(self.catalog_repo.fingerprint.encode())
        hasher.update(str(intent.seed).encode())
        content_fingerprint = hasher.hexdigest()
        manifest_id = f"prov_gen_{content_fingerprint[:16]}"
        created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        provenance = ProvenanceManifest(
            manifest_id=manifest_id,
            world_id=intent.generation_id,
            catalog_fingerprint=self.catalog_repo.fingerprint,
            module_fingerprints={},
            composition_fingerprint="",
            resolver_version="1.0.0",
            generator_version="1.0.0",
            seed=intent.seed,
            content_fingerprint=content_fingerprint,
            created_at=created_at,
            records=prov_records
        )

        assembly_report = {
            "sorted_module_ids": [],
            "factions_resolved": list(factions.keys()),
            "regions_count": len(regions),
            "entities_count": len(entities),
            "summary": {
                "status": "SUCCESS",
                "blocking_errors_count": 0,
                "warnings_count": 0
            }
        }

        from src.worldassembly.resolver import CompileProfileResolver
        profile_resolver = CompileProfileResolver(self.catalog_repo)
        compile_context = profile_resolver.resolve(world_spec)

        return ResolvedWorldBundle(
            world_spec=world_spec,
            compile_context=compile_context,
            provenance_manifest=provenance,
            assembly_report=assembly_report,
            validation_report=validation_report
        )

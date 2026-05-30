# Compliance IDs: WORLD-CAT-006, WORLD-CAT-007
from __future__ import annotations

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from src.content.repository import CatalogRepository


class CatalogValidationError(Exception):
    """Exception raised when catalog validation discovers errors."""
    pass


class ValidationIssue(BaseModel):
    """Represents a specific semantic warning or error inside the catalog files."""
    severity: str = Field(..., description="Either 'ERROR' or 'WARNING'")
    rule_id: str = Field(..., description="Unique validation rule code")
    message: str = Field(..., description="Informative explanation of the validation constraint violation")
    target_id: Optional[str] = Field(None, description="Optional definition ID causing the violation")
    filename: Optional[str] = Field(None, description="Filename where the issue resides")


class CatalogValidator:
    """
    Independent validator for the static Content Catalog. 
    Catches relational, schema, mapping, and range errors across definition directories.
    """

    def __init__(self, repo: CatalogRepository):
        self.repo = repo

    def validate(self) -> List[ValidationIssue]:
        """
        Runs validation sweeps and returns a complete list of structured warnings and errors.
        """
        issues: List[ValidationIssue] = []

        # Validate relational linkages
        self._validate_role_relations(issues)
        self._validate_building_relations(issues)
        self._validate_archetype_relations(issues)
        self._validate_relationship_relations(issues)
        self._validate_perspective_relations(issues)
        self._validate_legacy_projection_relations(issues)
        self._validate_recipe_relations(issues)
        self._validate_region_relations(issues)
        self._validate_race_relations(issues)
        self._validate_biome_relations(issues)
        self._validate_ecology_relations(issues)
        self._validate_defaults(issues)
        
        return issues

    def _validate_role_relations(self, issues: List[ValidationIssue]) -> None:
        """Verify referenced stats, inventory, and cognition profiles exist."""
        for role_id, role in self.repo.roles.items():
            if role.default_stats_profile:
                if not self.repo.get_stats_profile(role.default_stats_profile):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-001",
                        message=f"Role '{role_id}' references non-existent stats profile '{role.default_stats_profile}'",
                        target_id=role_id,
                        filename="social/roles.yaml"
                    ))
            
            if role.default_inventory_profile:
                if not self.repo.get_inventory_profile(role.default_inventory_profile):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-002",
                        message=f"Role '{role_id}' references non-existent inventory profile '{role.default_inventory_profile}'",
                        target_id=role_id,
                        filename="social/roles.yaml"
                    ))

            if role.default_cognition_profile:
                if not self.repo.get_cognition_profile(role.default_cognition_profile):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-003",
                        message=f"Role '{role_id}' references non-existent cognition profile '{role.default_cognition_profile}'",
                        target_id=role_id,
                        filename="social/roles.yaml"
                    ))

            for trait_id in role.compatible_traits:
                if not self.repo.get_trait(trait_id):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-001",
                        message=f"Role '{role_id}' references non-existent trait '{trait_id}'",
                        target_id=role_id,
                        filename="social/roles.yaml"
                    ))

    def _validate_building_relations(self, issues: List[ValidationIssue]) -> None:
        """Verify referenced service profiles inside buildings exist."""
        for bld_id, bld in self.repo.buildings.items():
            if bld.service_profile_id:
                if not self.repo.get_service_profile(bld.service_profile_id):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-004",
                        message=f"Building '{bld_id}' references non-existent service profile '{bld.service_profile_id}'",
                        target_id=bld_id,
                        filename="world/buildings.yaml"
                    ))

    def _validate_archetype_relations(self, issues: List[ValidationIssue]) -> None:
        """Verify archetype components exist."""
        for arch_id, arch in self.repo.entity_archetypes.items():
            # Check race
            if not self.repo.get_race(arch.race):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    rule_id="CAT-REL-011",
                    message=f"Archetype '{arch_id}' references non-existent race '{arch.race}'",
                    target_id=arch_id,
                    filename="entities/entity_archetypes.yaml"
                ))
            # Check faction
            if not self.repo.get_faction(arch.faction):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    rule_id="CAT-REL-011",
                    message=f"Archetype '{arch_id}' references non-existent faction '{arch.faction}'",
                    target_id=arch_id,
                    filename="entities/entity_archetypes.yaml"
                ))
            # Check role
            if not self.repo.get_role(arch.role):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    rule_id="CAT-REL-011",
                    message=f"Archetype '{arch_id}' references non-existent role '{arch.role}'",
                    target_id=arch_id,
                    filename="entities/entity_archetypes.yaml"
                ))
            # Check stats profile
            if not self.repo.get_stats_profile(arch.stat_profile):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    rule_id="CAT-REL-011",
                    message=f"Archetype '{arch_id}' references non-existent stats profile '{arch.stat_profile}'",
                    target_id=arch_id,
                    filename="entities/entity_archetypes.yaml"
                ))
            # Check combat profile
            if not self.repo.get_combat_profile(arch.combat_profile):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    rule_id="CAT-REL-011",
                    message=f"Archetype '{arch_id}' references non-existent combat profile '{arch.combat_profile}'",
                    target_id=arch_id,
                    filename="entities/entity_archetypes.yaml"
                ))
            # Check cognition profile
            if not self.repo.get_cognition_profile(arch.cognition_profile):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    rule_id="CAT-REL-011",
                    message=f"Archetype '{arch_id}' references non-existent cognition profile '{arch.cognition_profile}'",
                    target_id=arch_id,
                    filename="entities/entity_archetypes.yaml"
                ))
            # Check drive profile
            if not self.repo.get_drive_profile(arch.drive_profile):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    rule_id="CAT-REL-011",
                    message=f"Archetype '{arch_id}' references non-existent drive profile '{arch.drive_profile}'",
                    target_id=arch_id,
                    filename="entities/entity_archetypes.yaml"
                ))
            # Check inventory profile
            if not self.repo.get_inventory_profile(arch.inventory_profile):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    rule_id="CAT-REL-011",
                    message=f"Archetype '{arch_id}' references non-existent inventory profile '{arch.inventory_profile}'",
                    target_id=arch_id,
                    filename="entities/entity_archetypes.yaml"
                ))
            # Check skill profile
            if arch.skill_profile:
                if not self.repo.get_skill_profile(arch.skill_profile):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-011",
                        message=f"Archetype '{arch_id}' references non-existent skill profile '{arch.skill_profile}'",
                        target_id=arch_id,
                        filename="entities/entity_archetypes.yaml"
                    ))

            # Check traits
            for trait_id in arch.traits:
                if not self.repo.get_trait(trait_id):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-011",
                        message=f"Archetype '{arch_id}' references non-existent trait '{trait_id}'",
                        target_id=arch_id,
                        filename="entities/entity_archetypes.yaml"
                    ))

            # Check themes
            for theme_id in arch.themes:
                if not self.repo.get_theme(theme_id):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-011",
                        message=f"Archetype '{arch_id}' references non-existent theme '{theme_id}'",
                        target_id=arch_id,
                        filename="entities/entity_archetypes.yaml"
                    ))

    def _validate_relationship_relations(self, issues: List[ValidationIssue]) -> None:
        """Verify relationship source, target, and axes exist."""
        for rel_id, rel in self.repo.faction_relationships.items():
            if not self.repo.get_faction(rel.source_faction):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    rule_id="CAT-REL-012",
                    message=f"Relationship '{rel_id}' references non-existent source faction '{rel.source_faction}'",
                    target_id=rel_id,
                    filename="social/faction_relationships.yaml"
                ))
            if not self.repo.get_faction(rel.target_faction):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    rule_id="CAT-REL-012",
                    message=f"Relationship '{rel_id}' references non-existent target faction '{rel.target_faction}'",
                    target_id=rel_id,
                    filename="social/faction_relationships.yaml"
                ))
            for axis_id in rel.axes:
                if not self.repo.get_relationship_axis(axis_id):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-012",
                        message=f"Relationship '{rel_id}' references non-existent axis '{axis_id}'",
                        target_id=rel_id,
                        filename="social/faction_relationships.yaml"
                    ))

    def _validate_perspective_relations(self, issues: List[ValidationIssue]) -> None:
        """Verify perspective chosen faction and labels exist."""
        for pers_id, pers in self.repo.perspectives.items():
            if not self.repo.get_faction(pers.chosen_faction):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    rule_id="CAT-REL-013",
                    message=f"Perspective '{pers_id}' references non-existent chosen faction '{pers.chosen_faction}'",
                    target_id=pers_id,
                    filename="social/perspectives.yaml"
                ))
            for group, factions in pers.projected_labels.items():
                for f_id in factions:
                    # Let it pass if it is also a race (like prey_or_threat_by_context contains 'human', etc.)
                    if not self.repo.get_faction(f_id) and not self.repo.get_race(f_id):
                        issues.append(ValidationIssue(
                            severity="ERROR",
                            rule_id="CAT-REL-013",
                            message=f"Perspective '{pers_id}' projected label group '{group}' references non-existent faction/race '{f_id}'",
                            target_id=pers_id,
                            filename="social/perspectives.yaml"
                        ))

    def _validate_legacy_projection_relations(self, issues: List[ValidationIssue]) -> None:
        """Verify legacy projections map valid archetypes, items, and regions."""
        for proj_id, proj in self.repo.legacy_enemy_projections.items():
            if not self.repo.get_entity_archetype(proj.archetype_id):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    rule_id="CAT-REL-014",
                    message=f"Legacy projection '{proj_id}' references non-existent archetype '{proj.archetype_id}'",
                    target_id=proj_id,
                    filename="compatibility/legacy_enemy_projection.yaml"
                ))
            for item_id in proj.loot_table:
                if not self.repo.get_item(item_id):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-014",
                        message=f"Legacy projection '{proj_id}' loot table references non-existent item '{item_id}'",
                        target_id=proj_id,
                        filename="compatibility/legacy_enemy_projection.yaml"
                    ))
            for region_id in proj.spawn_regions:
                if not self.repo.get_region(region_id):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-014",
                        message=f"Legacy projection '{proj_id}' references non-existent spawn region '{region_id}'",
                        target_id=proj_id,
                        filename="compatibility/legacy_enemy_projection.yaml"
                    ))

    def _validate_recipe_relations(self, issues: List[ValidationIssue]) -> None:
        """Verify recipe items and services exist."""
        for recipe_id, recipe in self.repo.recipes.items():
            for item_id in recipe.ingredients:
                if not self.repo.get_item(item_id):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-015",
                        message=f"Recipe '{recipe_id}' ingredient references non-existent item '{item_id}'",
                        target_id=recipe_id,
                        filename="world/recipes.yaml"
                    ))
            for item_id in recipe.outputs:
                if not self.repo.get_item(item_id):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-015",
                        message=f"Recipe '{recipe_id}' output references non-existent item '{item_id}'",
                        target_id=recipe_id,
                        filename="world/recipes.yaml"
                    ))
            if recipe.required_service:
                # We can check either ServiceProfile or building service reference
                if not self.repo.get_service_profile(recipe.required_service) and not any(recipe.required_service in b.id for b in self.repo.buildings.values()):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-015",
                        message=f"Recipe '{recipe_id}' references non-existent service '{recipe.required_service}'",
                        target_id=recipe_id,
                        filename="world/recipes.yaml"
                    ))

    def _validate_region_relations(self, issues: List[ValidationIssue]) -> None:
        """Verify region allowed enemy list reference valid archetypes."""
        for region_id, region in self.repo.regions.items():
            for enemy_id in region.allowed_enemy_ids:
                if not self.repo.get_entity_archetype(enemy_id) and not self.repo.get_legacy_enemy_projection(enemy_id):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-016",
                        message=f"Region '{region_id}' references non-existent archetype/projection '{enemy_id}'",
                        target_id=region_id,
                        filename="world/runtime_regions.yaml"
                    ))

    def _validate_race_relations(self, issues: List[ValidationIssue]) -> None:
        """Verify race body models, needs, senses, cognition, drives, traits, and roles exist."""
        for race_id, race in self.repo.races.items():
            if not self.repo.get_body_model(race.body_model):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    rule_id="CAT-REL-017",
                    message=f"Race '{race_id}' references non-existent body model '{race.body_model}'",
                    target_id=race_id,
                    filename="living/races.yaml"
                ))
            if not self.repo.get_need_profile(race.need_profile):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    rule_id="CAT-REL-017",
                    message=f"Race '{race_id}' references non-existent need profile '{race.need_profile}'",
                    target_id=race_id,
                    filename="living/races.yaml"
                ))
            if not self.repo.get_sense_profile(race.sense_profile):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    rule_id="CAT-REL-017",
                    message=f"Race '{race_id}' references non-existent sense profile '{race.sense_profile}'",
                    target_id=race_id,
                    filename="living/races.yaml"
                ))
            if not self.repo.get_cognition_profile(race.cognition_profile):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    rule_id="CAT-REL-017",
                    message=f"Race '{race_id}' references non-existent cognition profile '{race.cognition_profile}'",
                    target_id=race_id,
                    filename="living/races.yaml"
                ))
            if not self.repo.get_drive_profile(race.drive_profile):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    rule_id="CAT-REL-017",
                    message=f"Race '{race_id}' references non-existent drive profile '{race.drive_profile}'",
                    target_id=race_id,
                    filename="living/races.yaml"
                ))
            for trait_id in race.natural_traits:
                if not self.repo.get_trait(trait_id):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-017",
                        message=f"Race '{race_id}' references non-existent trait '{trait_id}'",
                        target_id=race_id,
                        filename="living/races.yaml"
                    ))
            for role_id in race.compatible_roles:
                if not self.repo.get_role(role_id):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-017",
                        message=f"Race '{race_id}' references non-existent role '{role_id}'",
                        target_id=race_id,
                        filename="living/races.yaml"
                    ))

    def _validate_biome_relations(self, issues: List[ValidationIssue]) -> None:
        """Verify biomes reference existing themes, materials, and factions."""
        for biome_id, biome in self.repo.biomes.items():
            for theme_id in biome.themes:
                if not self.repo.get_theme(theme_id):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-018",
                        message=f"Biome '{biome_id}' references non-existent theme '{theme_id}'",
                        target_id=biome_id,
                        filename="world/biomes.yaml"
                    ))
            for mat_id in biome.common_materials:
                if not self.repo.get_material(mat_id):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-018",
                        message=f"Biome '{biome_id}' references non-existent material '{mat_id}'",
                        target_id=biome_id,
                        filename="world/biomes.yaml"
                    ))
            for f_id in biome.default_factions:
                if not self.repo.get_faction(f_id):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-018",
                        message=f"Biome '{biome_id}' references non-existent faction '{f_id}'",
                        target_id=biome_id,
                        filename="world/biomes.yaml"
                    ))

    def _validate_ecology_relations(self, issues: List[ValidationIssue]) -> None:
        """Verify ecology biomes, factions, populations, and resources exist."""
        for eco_id, eco in self.repo.ecologies.items():
            for biome_id in eco.biomes:
                if not self.repo.get_biome(biome_id):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-019",
                        message=f"Ecology '{eco_id}' references non-existent biome '{biome_id}'",
                        target_id=eco_id,
                        filename="world/ecologies.yaml"
                    ))
            for f_id in eco.dominant_factions:
                if not self.repo.get_faction(f_id):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-019",
                        message=f"Ecology '{eco_id}' references non-existent faction '{f_id}'",
                        target_id=eco_id,
                        filename="world/ecologies.yaml"
                    ))
            for pop_id in eco.populations:
                if not self.repo.get_population_recipe(pop_id):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-019",
                        message=f"Ecology '{eco_id}' references non-existent population recipe '{pop_id}'",
                        target_id=eco_id,
                        filename="world/ecologies.yaml"
                    ))
            for res_id in eco.resources:
                if not self.repo.get_resource(res_id) and not any(res_id in r.id for r in self.repo.resources.values()):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-019",
                        message=f"Ecology '{eco_id}' references non-existent resource '{res_id}'",
                        target_id=eco_id,
                        filename="world/ecologies.yaml"
                    ))

    def _validate_defaults(self, issues: List[ValidationIssue]) -> None:
        """Verify that at least one global default compile profile exists."""
        if not self.repo.defaults:
            issues.append(ValidationIssue(
                severity="WARNING",
                rule_id="CAT-DEF-001",
                message="No global default compile profiles are configured inside the catalog.",
                filename="defaults.yaml"
            ))

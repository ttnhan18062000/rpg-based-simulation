# Compliance IDs: WORLD-CAT-TEST-PHASE14
import os
import pytest
import tempfile
import yaml
from src.content.repository import CatalogRepository
from src.content.validator import CatalogValidator


def test_layered_catalog_validation_errors():
    """Verify that CatalogValidator catches relational violations CAT-REL-011 through CAT-REL-019."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create all required subdirectories
        for folder in ["foundation", "living", "social", "entities", "world", "compatibility"]:
            os.makedirs(os.path.join(tmp_dir, folder), exist_ok=True)

        # 1. Create a broken Archetype (CAT-REL-011)
        archetypes_data = [
            {
                "id": "broken_archetype",
                "race": "missing_race",
                "faction": "missing_faction",
                "role": "missing_role",
                "stat_profile": "missing_stats",
                "combat_profile": "missing_combat",
                "cognition_profile": "missing_cognition",
                "drive_profile": "missing_drive",
                "inventory_profile": "missing_inventory",
                "skill_profile": "missing_skill",
                "traits": ["missing_trait"],
                "themes": ["missing_theme"]
            }
        ]
        with open(os.path.join(tmp_dir, "entities", "entity_archetypes.yaml"), "w") as f:
            yaml.dump(archetypes_data, f)

        # 2. Create a broken Faction Relationship (CAT-REL-012)
        relationships_data = [
            {
                "id": "broken_relation",
                "source_faction": "missing_source",
                "target_faction": "missing_target",
                "relationship_model": "hostile",
                "axes": {"missing_axis": "negative"}
            }
        ]
        with open(os.path.join(tmp_dir, "social", "faction_relationships.yaml"), "w") as f:
            yaml.dump(relationships_data, f)

        # 3. Create a broken Perspective (CAT-REL-013)
        perspectives_data = [
            {
                "id": "broken_perspective",
                "chosen_faction": "missing_faction",
                "default_focus": "survival",
                "projected_labels": {
                    "threats": ["missing_threat_faction"]
                }
            }
        ]
        with open(os.path.join(tmp_dir, "social", "perspectives.yaml"), "w") as f:
            yaml.dump(perspectives_data, f)

        # 4. Create a broken Legacy Projection (CAT-REL-014)
        projections_data = [
            {
                "id": "broken_projection",
                "archetype_id": "missing_archetype",
                "legacy_enemy_id": "goblin",
                "danger_hint": "MEDIUM",
                "loot_table": {"missing_loot_item": 0.5},
                "spawn_regions": ["missing_region"]
            }
        ]
        with open(os.path.join(tmp_dir, "compatibility", "legacy_enemy_projection.yaml"), "w") as f:
            yaml.dump(projections_data, f)

        # 5. Create a broken Recipe (CAT-REL-015)
        recipes_data = [
            {
                "id": "broken_recipe",
                "ingredients": {"missing_ingredient": 1},
                "outputs": {"missing_output": 1},
                "required_service": "missing_service",
                "gold_cost": 10.0,
                "required_level": 1
            }
        ]
        with open(os.path.join(tmp_dir, "world", "recipes.yaml"), "w") as f:
            yaml.dump(recipes_data, f)

        # 6. Create a broken Region (CAT-REL-016)
        regions_data = [
            {
                "id": "broken_region",
                "danger_level": 1,
                "allowed_enemy_ids": ["missing_enemy"]
            }
        ]
        with open(os.path.join(tmp_dir, "world", "runtime_regions.yaml"), "w") as f:
            yaml.dump(regions_data, f)

        # 7. Create a broken Race (CAT-REL-017)
        races_data = [
            {
                "id": "broken_race",
                "body_model": "missing_body",
                "need_profile": "missing_need",
                "sense_profile": "missing_sense",
                "cognition_profile": "missing_cognition",
                "drive_profile": "missing_drive",
                "natural_traits": ["missing_trait"],
                "compatible_roles": ["missing_role"]
            }
        ]
        with open(os.path.join(tmp_dir, "living", "races.yaml"), "w") as f:
            yaml.dump(races_data, f)

        # 8. Create a broken Biome (CAT-REL-018)
        biomes_data = [
            {
                "id": "broken_biome",
                "themes": ["missing_theme"],
                "terrain_mix": ["grass"],
                "common_materials": ["missing_material"],
                "default_factions": ["missing_faction"],
                "danger_level": 1
            }
        ]
        with open(os.path.join(tmp_dir, "world", "biomes.yaml"), "w") as f:
            yaml.dump(biomes_data, f)

        # 9. Create a broken Ecology (CAT-REL-019)
        ecologies_data = [
            {
                "id": "broken_ecology",
                "biomes": ["missing_biome"],
                "dominant_factions": ["missing_faction"],
                "populations": ["missing_population"],
                "resources": ["missing_resource"],
                "relationship_models": [],
                "services": []
            }
        ]
        with open(os.path.join(tmp_dir, "world", "ecologies.yaml"), "w") as f:
            yaml.dump(ecologies_data, f)

        repo = CatalogRepository(tmp_dir)
        repo.load_all()

        validator = CatalogValidator(repo)
        issues = validator.validate()
        
        errors = [i for i in issues if i.severity == "ERROR"]
        rule_ids = {i.rule_id for i in errors}

        assert "CAT-REL-011" in rule_ids
        assert "CAT-REL-012" in rule_ids
        assert "CAT-REL-013" in rule_ids
        assert "CAT-REL-014" in rule_ids
        assert "CAT-REL-015" in rule_ids
        assert "CAT-REL-016" in rule_ids
        assert "CAT-REL-017" in rule_ids
        assert "CAT-REL-018" in rule_ids
        assert "CAT-REL-019" in rule_ids

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
                "species": "missing_species",
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

        # 7. Create a broken Species (CAT-REL-017)
        species_data = [
            {
                "id": "broken_species",
                "body_model": "missing_body",
                "need_profile": "missing_need",
                "sense_profile": "missing_sense",
                "cognition_profile": "missing_cognition",
                "intelligence_tier": "low",
                "drive_profile": "missing_drive",
                "natural_traits": ["missing_trait"],
                "compatible_roles": ["missing_role"]
            }
        ]
        with open(os.path.join(tmp_dir, "living", "species.yaml"), "w") as f:
            yaml.dump(species_data, f)

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


def test_phase23_reference_graph_and_dead_active_data():
    """Verify ContentReferenceGraph construction, reverse lookups, and dead active data validation."""
    from src.content.reference_graph import ContentReferenceGraph
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create all required subdirectories
        for folder in ["foundation", "living", "social", "entities", "world", "compatibility"]:
            os.makedirs(os.path.join(tmp_dir, folder), exist_ok=True)

        # Create Faction (source)
        factions_data = [{"id": "town_council", "display_name": "Town Council", "alignment_bucket": "defender", "influence_role": "sovereign", "legacy_engine_bucket": "TOWN_COUNCIL", "common_races": [], "themes": []}]
        with open(os.path.join(tmp_dir, "social", "factions.yaml"), "w") as f:
            yaml.dump(factions_data, f)

        # Create Species (source)
        species_data = [{
            "id": "human", "display_name": "Human",
            "body_model": "humanoid", "need_profile": "human_needs",
            "sense_profile": "human_senses", "cognition_profile": "practical_human",
            "intelligence_tier": "high",
            "drive_profile": "human_drives", "natural_traits": [], "compatible_roles": []
        }]
        with open(os.path.join(tmp_dir, "living", "species.yaml"), "w") as f:
            yaml.dump(species_data, f)

        # Add profiles to prevent errors
        with open(os.path.join(tmp_dir, "living", "body_models.yaml"), "w") as f:
            yaml.dump([{"id": "humanoid", "display_name": "Humanoid"}], f)
        with open(os.path.join(tmp_dir, "living", "need_profiles.yaml"), "w") as f:
            yaml.dump([{"id": "human_needs", "display_name": "Needs"}], f)
        with open(os.path.join(tmp_dir, "living", "sense_profiles.yaml"), "w") as f:
            yaml.dump([{"id": "human_senses", "display_name": "Senses"}], f)
        with open(os.path.join(tmp_dir, "living", "cognition_profiles.yaml"), "w") as f:
            yaml.dump([{"id": "practical_human", "display_name": "Cognition"}], f)
        with open(os.path.join(tmp_dir, "living", "drive_profiles.yaml"), "w") as f:
            yaml.dump([{"id": "human_drives", "display_name": "Drives"}], f)

        # Stat, combat, drive, cognition, need, sense, body profiles, roles, inventory
        with open(os.path.join(tmp_dir, "entities", "stat_profiles.yaml"), "w") as f:
            yaml.dump([{"id": "guard_stats", "display_name": "Guard Stats"}], f)
        with open(os.path.join(tmp_dir, "entities", "combat_profiles.yaml"), "w") as f:
            yaml.dump([{"id": "guard_combat", "display_name": "Guard Combat"}], f)
        with open(os.path.join(tmp_dir, "entities", "inventory_profiles.yaml"), "w") as f:
            yaml.dump([{"id": "guard_inv", "display_name": "Guard Inv"}], f)
        with open(os.path.join(tmp_dir, "social", "roles.yaml"), "w") as f:
            yaml.dump([{"id": "guard_role", "display_name": "Guard Role", "role_family": "defender", "legacy_engine_role": "GUARD", "default_stats_profile": "guard_stats", "default_cognition_profile": "practical_human"}], f)

        # Active archetype (Existing Logic / Redesigned Core maturity)
        archetypes_data = [{
            "id": "active_guard",
            "species": "human",
            "faction": "town_council",
            "role": "guard_role",
            "stat_profile": "guard_stats",
            "combat_profile": "guard_combat",
            "cognition_profile": "practical_human",
            "drive_profile": "human_drives",
            "inventory_profile": "guard_inv",
            "traits": [], "themes": []
        }]
        with open(os.path.join(tmp_dir, "entities", "entity_archetypes.yaml"), "w") as f:
            yaml.dump(archetypes_data, f)

        repo = CatalogRepository(tmp_dir)
        repo.load_all()

        # Build reference graph
        graph = ContentReferenceGraph(repo)

        # Assert nodes exist
        assert graph.has_node("species:human")
        assert graph.has_node("faction:town_council")
        assert graph.has_node("archetype:active_guard")

        # Assert outgoing neighbors (archetype references species, faction, role)
        outgoing = graph.get_outgoing_neighbors("archetype:active_guard")
        assert "species:human" in outgoing
        assert "faction:town_council" in outgoing
        assert "role:guard_role" in outgoing

        # Assert incoming neighbors (reverse lookup)
        incoming = graph.get_incoming_neighbors("species:human")
        assert "archetype:active_guard" in incoming

        # Test dead data warning
        validator = CatalogValidator(repo)
        issues = validator.validate()

        # Since active_guard is active (under entities/entity_archetypes) and has 0 incoming references (it is not used by any population/projection), it should trigger a warning
        dead_warnings = [i for i in issues if i.rule_id == "CAT-DEAD-001" and i.target_id == "active_guard"]
        assert len(dead_warnings) == 1
        assert dead_warnings[0].severity == "WARNING"
        assert "is active but never consumed" in dead_warnings[0].message


def test_graph_module_count_maps_and_metadata():
    """Verify that module count map fields (resources, buildings, services) resolve to typed edges and preserve counts."""
    from src.worldmodules.schema import WorldModuleSpec
    from src.content.reference_graph import ContentReferenceGraph
    from src.content.repository import CatalogRepository

    # Create dummy catalog repository
    with tempfile.TemporaryDirectory() as tmp_dir:
        for folder in ["foundation", "living", "social", "entities", "world", "compatibility"]:
            os.makedirs(os.path.join(tmp_dir, folder), exist_ok=True)
        repo = CatalogRepository(tmp_dir)
        repo.load_all()

    # Create a custom module with dict and list count maps
    m = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="test_count_module",
        module_type="settlement",
        display_name="Test Count Module",
        resources={
            "wood_node": 3
        },
        buildings={
            "inn": 1
        },
        services=["healer_service"]
    )

    graph = ContentReferenceGraph(repo, modules=[m])

    # Assert edges are created
    assert ("module:test_count_module", "resource:wood_node") in graph.edges
    assert ("module:test_count_module", "building:inn") in graph.edges
    assert ("module:test_count_module", "service:healer_service") in graph.edges

    # Assert counts are preserved in edge metadata
    assert graph.edge_metadata.get(("module:test_count_module", "resource:wood_node")) == {"count": 3}
    assert graph.edge_metadata.get(("module:test_count_module", "building:inn")) == {"count": 1}
    assert graph.edge_metadata.get(("module:test_count_module", "service:healer_service")) == {"count": 1}



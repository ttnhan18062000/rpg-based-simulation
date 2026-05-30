# Compliance IDs: WORLD-CAT-TEST
import os
import pytest
import tempfile
import yaml
from src.content.repository import CatalogRepository
from src.content.schema import FactionDefinition, RoleDefinition
from src.content.validator import CatalogValidator


def test_base_catalog_loading():
    """Verify that the repository successfully loads our baseline catalog files."""
    repo = CatalogRepository("data/content")
    repo.load_all()

    # Assert that minimal mappings are correctly loaded
    assert "villagers" in repo.factions
    assert "monsters" in repo.factions
    assert "town_council" in repo.factions

    assert "hero" in repo.roles
    assert "worker" in repo.roles
    assert "monster" in repo.roles

    # Verify attributes parsed correctly
    hero_role = repo.get_role("hero")
    assert hero_role is not None
    assert hero_role.legacy_engine_role == "HERO"
    assert hero_role.default_stats_profile == "hero_base"

    assert repo.fingerprint != ""


def test_catalog_relational_validator():
    """Verify that catalog validation successfully flags broken relational dependencies."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create custom roles and defaults
        roles_data = [
            {
                "id": "broken_hero",
                "display_name": "Broken Hero",
                "schema_version": "roledefinition.v1",
                "role_family": "combatant",
                "legacy_engine_role": "HERO",
                "default_stats_profile": "missing_profile",
                "default_inventory_profile": "missing_inventory"
            }
        ]
        
        with open(os.path.join(tmp_dir, "roles.yaml"), "w") as f:
            yaml.dump(roles_data, f)

        repo = CatalogRepository(tmp_dir)
        repo.load_all()

        validator = CatalogValidator(repo)
        issues = validator.validate()

        errors = [i for i in issues if i.severity == "ERROR"]
        error_ids = {i.rule_id for i in errors}

        assert "CAT-REL-001" in error_ids
        assert "CAT-REL-002" in error_ids

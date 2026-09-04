import os
import tempfile
import yaml
import pytest

from src.content.repository import CatalogRepository
from src.content.validator import CatalogValidationError
from src.core.registries import seed_phase1_content, runtime_content_source, catalog_fingerprint
from src.core.modes import RuntimeContentMode


@pytest.fixture(autouse=True)
def cleanup_registries():
    """Automatically reset registries to default hardcoded fallback state after each test."""
    yield
    seed_phase1_content(None, mode=RuntimeContentMode.LEGACY_FALLBACK)


def test_optional_fallback_mode():
    """Verify optional mode (required=False) falls back cleanly when catalog_repo is None."""
    seed_phase1_content(catalog_repo=None, required=False, mode=RuntimeContentMode.LEGACY_FALLBACK)
    
    from src.core.registries import runtime_content_source, catalog_fingerprint
    assert runtime_content_source == "legacy_hardcoded"
    assert catalog_fingerprint is None


def test_strict_required_mode_missing():
    """Verify required mode (required=True) raises ValueError when catalog_repo is None."""
    with pytest.raises(ValueError, match="Catalog repository is required in strict mode"):
        seed_phase1_content(catalog_repo=None, required=True)


def test_strict_required_mode_invalid_catalog():
    """Verify required mode raises CatalogValidationError when catalog contains validation errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create entities directory
        os.makedirs(os.path.join(tmp_dir, "entities"), exist_ok=True)
        
        # Create an archetype with invalid references
        archetypes_data = [
            {
                "id": "invalid_archetype",
                "species": "non_existent_species",
                "faction": "non_existent_faction",
                "role": "non_existent_role",
                "stat_profile": "non_existent_stats",
                "combat_profile": "non_existent_combat",
                "cognition_profile": "non_existent_cognition",
                "drive_profile": "non_existent_drive",
                "inventory_profile": "non_existent_inventory"
            }
        ]
        with open(os.path.join(tmp_dir, "entities", "entity_archetypes.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(archetypes_data, f)

        repo = CatalogRepository(tmp_dir)
        repo.load_all()
        
        with pytest.raises(CatalogValidationError, match="Catalog has validation errors"):
            seed_phase1_content(repo, required=True)

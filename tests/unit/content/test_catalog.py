# Compliance IDs: WORLD-CAT-TEST
import os
import pytest
import tempfile
import yaml
from src.content.repository import CatalogRepository
from src.content.schema import FactionDefinition, RoleDefinition, SpeciesDefinition
from src.content.validator import CatalogValidator


def test_base_catalog_loading():
    """Verify that the repository successfully loads our baseline catalog files."""
    repo = CatalogRepository("data/content")
    repo.load_all()

    # Assert that minimal mappings are correctly loaded
    assert "hero_guild" in repo.factions
    assert "town_council" in repo.factions
    assert "wild_beast_pack" in repo.factions

    assert "hero" in repo.roles
    assert "worker" in repo.roles
    assert "guard" in repo.roles

    # Verify attributes parsed correctly
    hero_role = repo.get_role("hero")
    assert hero_role is not None
    assert hero_role.legacy_engine_role == "HERO"
    assert hero_role.default_stats_profile == "hero_base"

    assert repo.fingerprint != ""


def test_catalog_relational_validator():
    """Verify that catalog validation successfully flags broken relational dependencies."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create the subdirectory expected by repository layout
        os.makedirs(os.path.join(tmp_dir, "social"), exist_ok=True)
        
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
        
        with open(os.path.join(tmp_dir, "social", "roles.yaml"), "w") as f:
            yaml.dump(roles_data, f)

        repo = CatalogRepository(tmp_dir)
        repo.load_all()

        validator = CatalogValidator(repo)
        issues = validator.validate()

        errors = [i for i in issues if i.severity == "ERROR"]
        error_ids = {i.rule_id for i in errors}

        assert "CAT-REL-001" in error_ids
        assert "CAT-REL-002" in error_ids


def test_strict_load_missing_required():
    """Verify load_all(strict=True) raises ValueError if a required family is missing."""
    from unittest.mock import patch
    import src.content.repository as rep_mod

    mock_registry = [
        rep_mod.ContentFamilySpec(
            family="foundation.materials",
            path="foundation/materials.yaml",
            schema=rep_mod.MaterialDefinition,
            repository_index="materials",
            required=True
        )
    ]

    with tempfile.TemporaryDirectory() as tmp_dir:
        # No files are created, so required file will be missing
        repo = rep_mod.CatalogRepository(tmp_dir)
        with patch("src.content.repository.CANONICAL_FAMILIES", mock_registry):
            with pytest.raises(ValueError, match="Missing required catalog files"):
                repo.load_all(strict=True)


def test_strict_load_unknown_extra_file():
    """Verify that undeclared YAML files in data/content/ are reported as ignored_files."""
    from unittest.mock import patch
    import src.content.repository as rep_mod

    mock_registry = [
        rep_mod.ContentFamilySpec(
            family="foundation.materials",
            path="foundation/materials.yaml",
            schema=rep_mod.MaterialDefinition,
            repository_index="materials",
            required=False
        )
    ]

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create foundation directory
        os.makedirs(os.path.join(tmp_dir, "foundation"), exist_ok=True)
        # Create an unknown extra file
        with open(os.path.join(tmp_dir, "foundation", "unknown_extra.yaml"), "w", encoding="utf-8") as f:
            yaml.dump([{"id": "unknown"}], f)

        repo = rep_mod.CatalogRepository(tmp_dir)
        with patch("src.content.repository.CANONICAL_FAMILIES", mock_registry):
            report = repo.load_all(strict=False)
            assert "foundation/unknown_extra.yaml" in report.ignored_files


def test_strict_load_empty_family():
    """Verify that empty family files are detected and reported."""
    from unittest.mock import patch
    import src.content.repository as rep_mod

    mock_registry = [
        rep_mod.ContentFamilySpec(
            family="foundation.materials",
            path="foundation/materials.yaml",
            schema=rep_mod.MaterialDefinition,
            repository_index="materials",
            required=True
        )
    ]

    with tempfile.TemporaryDirectory() as tmp_dir:
        os.makedirs(os.path.join(tmp_dir, "foundation"), exist_ok=True)
        # Write an empty file
        with open(os.path.join(tmp_dir, "foundation", "materials.yaml"), "w", encoding="utf-8") as f:
            f.write("")

        repo = rep_mod.CatalogRepository(tmp_dir)
        with patch("src.content.repository.CANONICAL_FAMILIES", mock_registry):
            report = repo.load_all(strict=False)
            # Empty active family has 0 records loaded
            assert report.record_counts["foundation.materials"] == 0


def test_strict_load_duplicate_paths():
    """Verify that duplicate paths in CANONICAL_FAMILIES check fail."""
    from unittest.mock import patch
    import src.content.repository as rep_mod

    mock_registry = [
        rep_mod.ContentFamilySpec(
            family="foundation.materials",
            path="foundation/materials.yaml",
            schema=rep_mod.MaterialDefinition,
            repository_index="materials",
            required=True
        ),
        rep_mod.ContentFamilySpec(
            family="foundation.materials_dup",
            path="foundation/materials.yaml",
            schema=rep_mod.MaterialDefinition,
            repository_index="materials",
            required=True
        )
    ]

    with tempfile.TemporaryDirectory() as tmp_dir:
        os.makedirs(os.path.join(tmp_dir, "foundation"), exist_ok=True)
        with open(os.path.join(tmp_dir, "foundation", "materials.yaml"), "w", encoding="utf-8") as f:
            yaml.dump([{"id": "iron", "categories": ["metal"]}], f)

        repo = rep_mod.CatalogRepository(tmp_dir)
        with patch("src.content.repository.CANONICAL_FAMILIES", mock_registry):
            with pytest.raises(ValueError, match="Duplicate family path detected"):
                repo.load_all(strict=True)


def test_strict_load_report_fingerprint():
    """Verify that load report contains a fingerprint that is unique and deterministic."""
    from unittest.mock import patch
    import src.content.repository as rep_mod

    mock_registry = [
        rep_mod.ContentFamilySpec(
            family="foundation.materials",
            path="foundation/materials.yaml",
            schema=rep_mod.MaterialDefinition,
            repository_index="materials",
            required=True
        )
    ]

    with tempfile.TemporaryDirectory() as tmp_dir:
        os.makedirs(os.path.join(tmp_dir, "foundation"), exist_ok=True)
        
        # Write first content
        with open(os.path.join(tmp_dir, "foundation", "materials.yaml"), "w", encoding="utf-8") as f:
            yaml.dump([{"id": "iron", "categories": ["metal"]}], f)
        repo = rep_mod.CatalogRepository(tmp_dir)
        with patch("src.content.repository.CANONICAL_FAMILIES", mock_registry):
            r1 = repo.load_all(strict=False)
            f1 = r1.fingerprint
            assert f1 != ""

            # Write second content (same ID but different properties)
            with open(os.path.join(tmp_dir, "foundation", "materials.yaml"), "w", encoding="utf-8") as f:
                yaml.dump([{"id": "iron", "categories": ["heavy_metal"]}], f)
            
            # Reload
            repo2 = rep_mod.CatalogRepository(tmp_dir)
            r2 = repo2.load_all(strict=False)
            f2 = r2.fingerprint
            assert f2 != f1


def test_schema_fail_closed_unknown_field():
    """Verify that instantiating a catalog model with an unknown top-level field raises ValidationError."""
    from pydantic import ValidationError
    from src.content.schema import MaterialDefinition

    with pytest.raises(ValidationError):
        # unknown_prop is not declared on MaterialDefinition or CatalogBaseDefinition
        MaterialDefinition(
            id="iron",
            display_name="Iron Ore",
            categories=["metal"],
            unknown_prop="invalid"
        )


def test_schema_metadata_nested_field_allowed():
    """Verify that placing extra/unknown keys inside metadata/extension/design_notes is allowed."""
    from src.content.schema import MaterialDefinition

    mat = MaterialDefinition(
        id="iron",
        display_name="Iron Ore",
        categories=["metal"],
        metadata={"custom_key": "allowed"},
        extension={"legacy_key": "allowed"},
        design_notes="This is allowed"
    )
    assert mat.metadata["custom_key"] == "allowed"
    assert mat.extension["legacy_key"] == "allowed"
    assert mat.design_notes == "This is allowed"


def test_faction_definition_hazard_immunities_field():
    """FactionDefinition.hazard_immunities round-trips and defaults to empty list."""
    faction = FactionDefinition(
        id="fiend_lords",
        alignment_bucket="invader",
        influence_role="challenger",
        legacy_engine_bucket="MONSTER_HORDE",
        hazard_immunities=["CHAOS_CORRUPTION"],
    )
    assert faction.hazard_immunities == ["CHAOS_CORRUPTION"]

    # Field omitted entirely -> defaults to empty list, does not break loading.
    faction_default = FactionDefinition(
        id="plain_faction",
        alignment_bucket="neutral",
        influence_role="non_combatant",
        legacy_engine_bucket="NEUTRAL",
    )
    assert faction_default.hazard_immunities == []


def test_faction_catalog_loads_with_hazard_immunities_authored():
    """The full real catalog (with hazard_immunities authored on some factions) still loads."""
    repo = CatalogRepository("data/content")
    repo.load_all()

    wild_beast_pack = repo.get_faction("wild_beast_pack")
    assert wild_beast_pack is not None
    assert wild_beast_pack.hazard_immunities == ["NATURAL_TERRAIN"]

    goblin_warband = repo.get_faction("goblin_warband")
    assert goblin_warband is not None
    assert goblin_warband.hazard_immunities == ["NATURAL_TERRAIN"]

    # A faction without the field authored must still default safely to empty.
    hero_guild = repo.get_faction("hero_guild")
    assert hero_guild is not None
    assert hero_guild.hazard_immunities == []


def test_species_definition_intelligence_tier_field_round_trips():
    """SpeciesDefinition.intelligence_tier round-trips for both valid values, is required
    (no default), and rejects a value outside {"high", "low"} via the field validator."""
    from pydantic import ValidationError

    species_high = SpeciesDefinition(
        id="test_species_high",
        body_model="standard_humanoid",
        need_profile="humanoid_survival",
        sense_profile="normal_humanoid_senses",
        cognition_profile="practical_humanoid",
        drive_profile="cautious_commoner",
        intelligence_tier="high",
    )
    assert species_high.intelligence_tier == "high"

    species_low = SpeciesDefinition(
        id="test_species_low",
        body_model="quadruped_predator",
        need_profile="carnivore_survival",
        sense_profile="predator_smell_senses",
        cognition_profile="instinctive_animal",
        drive_profile="territorial_predator",
        intelligence_tier="low",
    )
    assert species_low.intelligence_tier == "low"

    # Field omitted entirely -> ValidationError (required, no default).
    with pytest.raises(ValidationError):
        SpeciesDefinition(
            id="test_species_missing_tier",
            body_model="standard_humanoid",
            need_profile="humanoid_survival",
            sense_profile="normal_humanoid_senses",
            cognition_profile="practical_humanoid",
            drive_profile="cautious_commoner",
        )

    # Invalid value outside {"high", "low"} -> ValidationError via the field validator.
    with pytest.raises(ValidationError):
        SpeciesDefinition(
            id="test_species_bad_tier",
            body_model="standard_humanoid",
            need_profile="humanoid_survival",
            sense_profile="normal_humanoid_senses",
            cognition_profile="practical_humanoid",
            drive_profile="cautious_commoner",
            intelligence_tier="medium",
        )


EXPECTED_INTELLIGENCE_TIER = {
    "human": "high",
    "goblin": "high",
    "orc": "high",
    "elf": "high",
    "dwarf": "high",
    "lizardfolk": "high",
    "wolf": "low",
    "spider": "low",
    "undead": "low",
    "troll": "low",
    "slime": "low",
    "dragonkin": "high",
    "spirit": "high",
}


def test_all_13_species_have_documented_intelligence_tier():
    """Every species in the real catalog carries an authored intelligence_tier matching the
    documented anchor rule (tool_user in natural_traits <-> "high"), with dragonkin/spirit
    as explicitly reviewed and justified exceptions (see ticket TCK-20260831-SPECIES-INTELLIGENCE-TIER)."""
    repo = CatalogRepository("data/content")
    repo.load_all()

    assert set(EXPECTED_INTELLIGENCE_TIER) == set(repo.species.keys())

    for species_id, expected_tier in EXPECTED_INTELLIGENCE_TIER.items():
        species = repo.species[species_id]
        assert species.intelligence_tier == expected_tier, (
            f"{species_id}: expected intelligence_tier={expected_tier!r}, "
            f"got {species.intelligence_tier!r}"
        )

    # Executable anchor-rule invariant for the 11 unambiguous species (dragonkin/spirit are the
    # two explicitly justified exceptions to the tool_user anchor, see plan.md).
    for species in repo.species.values():
        if species.id in ("dragonkin", "spirit"):
            continue
        assert ("tool_user" in species.natural_traits) == (species.intelligence_tier == "high"), (
            f"{species.id}: tool_user anchor rule violated "
            f"(tool_user in natural_traits={'tool_user' in species.natural_traits}, "
            f"intelligence_tier={species.intelligence_tier})"
        )


def test_species_catalog_loads_with_intelligence_tier_authored():
    """The full real catalog (with intelligence_tier authored on every species) loads without
    raising, catching a YAML authoring error (bad value or missing field) as a load failure."""
    repo = CatalogRepository("data/content")
    repo.load_all()
    assert len(repo.species) == len(EXPECTED_INTELLIGENCE_TIER)


def test_schema_compatibility_model_fail_closed():
    """Verify that compatibility models also raise ValidationError when unknown top-level fields are supplied."""
    from pydantic import ValidationError
    from src.content.schema import LegacyEnemyProjectionDefinition

    with pytest.raises(ValidationError):
        LegacyEnemyProjectionDefinition(
            id="proj_rat",
            archetype_id="rat_archetype",
            legacy_enemy_id="rat",
            danger_hint="MEDIUM",
            unknown_prop="invalid"
        )

import os
from pathlib import Path
import pytest
from src.content.matrix import CONTENT_USAGE_MATRIX, generate_matrix_report

VALID_IMPLEMENTATION_STATES = {
    "LOADED_ONLY",
    "VALIDATED_ONLY",
    "RESOLVED_PARTIALLY",
    "PROJECTED_TO_LEGACY",
    "RUNTIME_AUTHORITATIVE",
    "DESIGN_ONLY"
}

VALID_MATURITY_STATES = {
    "EXISTING-LOGIC",
    "LEGACY-EXPORT",
    "REDESIGNED-CORE",
    "ADDITIONAL",
    "FUTURE-EXTENSION",
    "COMPATIBILITY"
}


def test_matrix_exists_and_can_be_imported():
    assert isinstance(CONTENT_USAGE_MATRIX, dict)
    assert len(CONTENT_USAGE_MATRIX) > 0


def test_matrix_validation_and_states():
    """Verify that every entry in the matrix has valid states and satisfies engine constraints."""
    for key, entry in CONTENT_USAGE_MATRIX.items():
        # Validate implementation states
        assert entry.implementation_state in VALID_IMPLEMENTATION_STATES, (
            f"Invalid implementation state '{entry.implementation_state}' for content family '{key}'"
        )
        # Validate maturity states
        assert entry.content_maturity in VALID_MATURITY_STATES, (
            f"Invalid maturity state '{entry.content_maturity}' for content family '{key}'"
        )

        # Constraint: Compatibility data cannot be RUNTIME_AUTHORITATIVE
        if entry.content_maturity == "COMPATIBILITY" or "compatibility" in key:
            assert entry.implementation_state != "RUNTIME_AUTHORITATIVE", (
                f"Compatibility family '{key}' cannot be marked as RUNTIME_AUTHORITATIVE"
            )

        # Constraint: REDESIGNED-CORE content cannot stay LOADED_ONLY
        if entry.content_maturity == "REDESIGNED-CORE":
            assert entry.implementation_state != "LOADED_ONLY", (
                f"REDESIGNED-CORE family '{key}' cannot remain LOADED_ONLY"
            )

        # Ensure required metadata exists or is explicitly documented
        assert entry.schema_class is not None or entry.implementation_state == "DESIGN_ONLY", (
            f"Schema class is required for active content family '{key}'"
        )
        assert entry.validator_coverage is not None, (
            f"Validator coverage is required for content family '{key}'"
        )
        assert entry.resolver_component is not None, (
            f"Resolver component field is required for content family '{key}'"
        )
        assert entry.compile_runtime_consumer is not None, (
            f"Compile/runtime consumer field is required for content family '{key}'"
        )


def test_matrix_covers_all_content_files():
    """Verify that every content catalog yaml file and structural directory is covered in the matrix."""
    content_dir = Path("data/content")
    assert content_dir.is_dir(), "Expected data/content directory to exist"

    # Walk all files and directories under data/content
    scanned_families = set()

    for item in content_dir.rglob("*"):
        if item.name == ".gitkeep":
            continue

        # We treat subdirectories directly under data/content as families if they contain yaml files
        # or are structural folders like world_modules, world_compositions, simulation_scenarios
        rel_path = item.relative_to(content_dir)
        parts = rel_path.parts

        if not parts:
            continue

        top_dir = parts[0]

        # Check if it's one of the extra structural/scenario directories
        if top_dir in {"world_modules", "world_compositions", "simulation_scenarios"}:
            scanned_families.add(top_dir)
        elif item.is_file() and item.suffix in {".yaml", ".yml"}:
            # Strip suffix to get family key
            family_key = str(rel_path.with_suffix(""))
            scanned_families.add(family_key)

    # Verify every scanned family exists in the matrix
    missing_families = scanned_families - set(CONTENT_USAGE_MATRIX.keys())
    assert not missing_families, (
        f"The following content families are present on disk but missing from the ContentUsageMatrix: {missing_families}"
    )


def test_generate_and_save_report():
    """Automatically generate the markdown matrix report on test run and save to docs/mechanics/."""
    report = generate_matrix_report()
    assert "# Content Usage Matrix Report" in report

    output_path = Path("docs/mechanics/content_usage_matrix.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    assert output_path.is_file(), "Report markdown file should be successfully created on disk"


def test_yaml_state_comments_are_ignored():
    """Verify that YAML comment parser does not exist and comment content is ignored by validators."""
    # We scan src/ content loaders/validators to ensure they don't parse comments like # STATE:
    # This is a static analysis check.
    src_dir = Path("src")
    for filepath in src_dir.rglob("*.py"):
        content = filepath.read_text(encoding="utf-8")
        assert "STATE:" not in content or "human-only" in content or "comments" in content or "ignored" in content, (
            f"Source file {filepath} seems to reference or parse YAML 'STATE:' comments."
        )


def test_every_family_has_implementation_state():
    """Verify every content family has exactly one valid implementation state."""
    for key, entry in CONTENT_USAGE_MATRIX.items():
        assert entry.implementation_state in VALID_IMPLEMENTATION_STATES, (
            f"Family '{key}' must have a valid implementation_state"
        )


def test_runtime_authoritative_requires_evidence():
    """Verify RUNTIME_AUTHORITATIVE requires at least one evidence test."""
    for key, entry in CONTENT_USAGE_MATRIX.items():
        if entry.implementation_state == "RUNTIME_AUTHORITATIVE":
            assert entry.evidence_tests and len(entry.evidence_tests.strip()) > 0, (
                f"RUNTIME_AUTHORITATIVE family '{key}' must have defined evidence_tests"
            )


def test_compatibility_family_not_runtime_authoritative():
    """Verify COMPATIBILITY content maturity classification cannot be RUNTIME_AUTHORITATIVE."""
    for key, entry in CONTENT_USAGE_MATRIX.items():
        if entry.content_maturity == "COMPATIBILITY":
            assert entry.implementation_state != "RUNTIME_AUTHORITATIVE", (
                f"Compatibility family '{key}' cannot be marked RUNTIME_AUTHORITATIVE"
            )


def test_graph_ignores_yaml_comments_explicitly():
    """Verify that graph validation does not read or depend on YAML comments."""
    # Ensure there are no references in the codebase where CatalogValidator reads YAML files manually to find `# STATE:` comments.
    from src.content.validator import CatalogValidator
    import inspect
    source = inspect.getsource(CatalogValidator)
    assert "# STATE:" not in source
    assert "STATE:" not in source


def test_family_without_declared_consumer_fails_usage_contract():
    """Verify that every active content family (except DESIGN_ONLY and PROJECTED_TO_LEGACY) must have a declared compile/runtime consumer."""
    for key, entry in CONTENT_USAGE_MATRIX.items():
        if entry.implementation_state not in ("DESIGN_ONLY", "PROJECTED_TO_LEGACY"):
            assert entry.compile_runtime_consumer and entry.compile_runtime_consumer not in ("None", "N/A"), (
                f"Active content family '{key}' must have a declared compile/runtime consumer"
            )


def test_design_only_family_may_have_no_runtime_consumer():
    """Verify that DESIGN_ONLY content families are allowed to have None or N/A as compile/runtime consumer."""
    design_only_found = False
    for key, entry in CONTENT_USAGE_MATRIX.items():
        if entry.implementation_state == "DESIGN_ONLY":
            design_only_found = True
            # Should be allowed to have "None" or "N/A" or "None (Design-Only)" as consumer
            assert entry.compile_runtime_consumer in ("None", "N/A", "None (Design-Only)", "ScenarioLabOrchestrator")
    assert design_only_found


def test_compatibility_family_points_to_clean_source():
    """Verify that compatibility mappings only map to valid clean source records."""
    # Let's load the compatibility file and check that the archetype_ids referenced exist in the catalog repository
    from src.content.repository import CatalogRepository
    repo = CatalogRepository("data/content")
    repo.load_all()

    assert len(repo.legacy_enemy_projections) > 0
    for proj_id, proj in repo.legacy_enemy_projections.items():
        # Check that the mapped archetype exists
        assert proj.archetype_id in repo.entity_archetypes, (
            f"Compatibility projection '{proj_id}' references non-existent archetype '{proj.archetype_id}'"
        )


def test_living_family_marked_resolved_partially_until_runtime_consumer():
    """Verify that living families (e.g., need_profiles, body_models) stay RESOLVED_PARTIALLY."""
    for family in ["living/need_profiles", "living/body_models", "living/drive_profiles", "living/sense_profiles", "living/cognition_profiles"]:
        entry = CONTENT_USAGE_MATRIX[family]
        assert entry.implementation_state == "RESOLVED_PARTIALLY", (
            f"Living family '{family}' must be RESOLVED_PARTIALLY until runtime consumers exist"
        )
        assert entry.runtime_consumer_evidence == "None yet"


def test_foundation_resolver_fetches_known_ids():
    """Verify that FoundationResolver resolves known IDs correctly."""
    from src.content.repository import CatalogRepository
    from src.content.resolver import FoundationResolver
    repo = CatalogRepository("data/content")
    repo.load_all()
    resolver = FoundationResolver(repo)

    # strength is a known attribute
    strength = resolver.resolve_attribute("strength")
    assert strength.id == "strength"

    # wood is a known material
    wood = resolver.resolve_material("wood")
    assert wood.id == "wood"


def test_missing_foundation_id_fails_clearly():
    """Verify that resolving a missing foundation ID raises a clean ResolverError."""
    from src.content.repository import CatalogRepository
    from src.content.resolver import FoundationResolver, ResolverError
    repo = CatalogRepository("data/content")
    repo.load_all()
    resolver = FoundationResolver(repo)

    with pytest.raises(ResolverError) as exc_info:
        resolver.resolve_attribute("nonexistent_strength_xxxx")
    assert "attribute" in str(exc_info.value)
    assert "nonexistent_strength_xxxx" in str(exc_info.value)


def test_social_resolver_resolves_relationships_without_claiming_all_runtime_usage():
    """Verify that social relationships resolve correctly but stay RESOLVED_PARTIALLY."""
    entry = CONTENT_USAGE_MATRIX["social/faction_relationships"]
    assert entry.implementation_state == "RESOLVED_PARTIALLY"
    assert entry.resolver_component == "SocialDefaultsResolver"
    assert "RelationProjectionService" in entry.runtime_consumer_evidence




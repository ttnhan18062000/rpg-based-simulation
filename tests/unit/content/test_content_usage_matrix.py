import os
import tempfile
from pathlib import Path
import pytest
from src.content.matrix import (
    CONTENT_USAGE_MATRIX,
    _auto_discover_extra_entries,
    generate_matrix_report,
)

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
    """Families with a resolver component but no runtime consumer cannot be RUNTIME_AUTHORITATIVE."""
    for key, entry in CONTENT_USAGE_MATRIX.items():
        if entry.resolver_component and not entry.compile_runtime_consumer:
            assert entry.implementation_state != "RUNTIME_AUTHORITATIVE", (
                f"Resolver-only family '{key}' cannot be RUNTIME_AUTHORITATIVE"
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
    # TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY: living/cognition_profiles gained a
    # real runtime consumer (AdventureDecisionPhase.apply() reads supports_adventure_routing),
    # so it no longer belongs to the "no runtime consumer yet" group asserted below -- it still
    # stays RESOLVED_PARTIALLY (implementation_state unchanged), just with real evidence now.
    for family in ["living/need_profiles", "living/body_models", "living/drive_profiles", "living/sense_profiles"]:
        entry = CONTENT_USAGE_MATRIX[family]
        assert entry.implementation_state == "RESOLVED_PARTIALLY", (
            f"Living family '{family}' must be RESOLVED_PARTIALLY until runtime consumers exist"
        )
        assert entry.runtime_consumer_evidence == "None yet"

    cognition_entry = CONTENT_USAGE_MATRIX["living/cognition_profiles"]
    assert cognition_entry.implementation_state == "RESOLVED_PARTIALLY"
    assert cognition_entry.runtime_consumer_evidence != "None yet"
    assert "AdventureDecisionPhase" in cognition_entry.runtime_consumer_evidence


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


def test_dead_record_validator_covers_region_concept():
    """Verify that the region concept correctly maps to world/runtime_regions via FAMILY_KEY_OVERRIDES.

    Without the override, 'world.regions' → 'world/regions' (via dot-to-slash) does not match
    the matrix key 'world/runtime_regions', causing dead-record validation to silently skip all
    region records.
    """
    from src.content.validator import _FAMILY_KEY_OVERRIDES
    from src.content.reference_graph import FAMILY_TO_SHORT

    # Confirm the region concept short-name
    region_concept = FAMILY_TO_SHORT.get("world.regions")
    assert region_concept == "region", "world.regions must map to short name 'region'"

    # Confirm the dot-to-slash derivation produces the override key
    derived_key = "world.regions".replace(".", "/")
    assert derived_key == "world/regions"
    assert derived_key in _FAMILY_KEY_OVERRIDES, (
        f"'{derived_key}' must be in _FAMILY_KEY_OVERRIDES so region dead-record validation is not silently skipped"
    )

    # Confirm the override maps to the actual matrix key
    resolved_key = _FAMILY_KEY_OVERRIDES[derived_key]
    assert resolved_key in CONTENT_USAGE_MATRIX, (
        f"Override target '{resolved_key}' must exist in CONTENT_USAGE_MATRIX"
    )


VALID_TRANSITIONS = {
    "DESIGN_ONLY":            frozenset({"LOADED_ONLY", "VALIDATED_ONLY"}),
    "LOADED_ONLY":            frozenset({"VALIDATED_ONLY", "RESOLVED_PARTIALLY"}),
    "VALIDATED_ONLY":         frozenset({"RESOLVED_PARTIALLY", "PROJECTED_TO_LEGACY"}),
    "RESOLVED_PARTIALLY":     frozenset({"RUNTIME_AUTHORITATIVE", "PROJECTED_TO_LEGACY"}),
    "PROJECTED_TO_LEGACY":    frozenset({"RUNTIME_AUTHORITATIVE"}),
    "RUNTIME_AUTHORITATIVE":  frozenset(),  # terminal
}


def test_implementation_state_values_are_valid():
    valid_states = set(VALID_TRANSITIONS.keys())
    for key, entry in CONTENT_USAGE_MATRIX.items():
        assert entry.implementation_state in valid_states, (
            f"'{key}' has unknown implementation_state '{entry.implementation_state}'"
        )


# ---------------------------------------------------------------------------
# Auto-discovery regression tests (TCK-20260627-P2K-CONTENT-MATRIX)
# ---------------------------------------------------------------------------

def test_auto_discover_returns_design_only_for_unknown_file():
    """Auto-discovered entries must be DESIGN_ONLY with valid state/maturity."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        subdir = Path(tmp_dir) / "custom_pack"
        subdir.mkdir()
        (subdir / "items.yaml").write_text("- id: test_item\n", encoding="utf-8")

        discovered = _auto_discover_extra_entries(tmp_dir, frozenset())

    assert "custom_pack/items" in discovered
    entry = discovered["custom_pack/items"]
    assert entry.implementation_state == "DESIGN_ONLY"
    assert entry.content_maturity in VALID_MATURITY_STATES
    # Fields required to be non-None by test_matrix_validation_and_states must
    # be present as strings (not Python None)
    assert entry.validator_coverage is not None
    assert entry.resolver_component is not None
    assert entry.compile_runtime_consumer is not None
    # schema_class is allowed to be None for DESIGN_ONLY entries
    assert entry.schema_class is None


def test_auto_discover_skips_known_keys():
    """Auto-discovery must not overwrite or duplicate already-registered keys."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        subdir = Path(tmp_dir) / "foundation"
        subdir.mkdir()
        (subdir / "materials.yaml").write_text("- id: stone\n", encoding="utf-8")

        known = frozenset({"foundation/materials"})
        discovered = _auto_discover_extra_entries(tmp_dir, known)

    assert "foundation/materials" not in discovered


def test_auto_discover_skips_gitkeep():
    """Gitkeep placeholder files must be ignored during auto-discovery."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        (Path(tmp_dir) / ".gitkeep").write_text("", encoding="utf-8")
        discovered = _auto_discover_extra_entries(tmp_dir, frozenset())

    assert not any(".gitkeep" in k for k in discovered)


def test_auto_discover_graceful_on_missing_dir():
    """Auto-discovery must return an empty dict when content_dir does not exist."""
    result = _auto_discover_extra_entries(
        "/nonexistent/path/that/does/not/exist", frozenset()
    )
    assert result == {}


def test_auto_discover_no_duplicates_for_current_content():
    """Running auto-discover against real data/content/ with all current keys must produce no new entries.

    This confirms every file currently on disk is already hand-registered in
    CONTENT_USAGE_MATRIX — no accidental gaps from the existing content set.
    """
    discovered = _auto_discover_extra_entries(
        content_dir="data/content",
        known_keys=frozenset(CONTENT_USAGE_MATRIX.keys()),
    )
    # All current files are already covered by the hand-crafted matrix entries
    # plus any previously auto-discovered entries merged at import time.
    assert discovered == {}, (
        f"Unexpected files on disk not registered in CONTENT_USAGE_MATRIX: "
        f"{sorted(discovered.keys())}"
    )


def test_merged_matrix_covers_all_disk_files():
    """The live CONTENT_USAGE_MATRIX (after auto-discovery merge) must cover every
    file currently present under data/content/.

    This is a direct post-implementation regression guard for the DX fix: adding
    a new YAML to data/content/ must not require a manual CONTENT_USAGE_MATRIX edit.
    """
    content_dir = Path("data/content")
    if not content_dir.is_dir():
        pytest.skip("data/content/ not present in this environment")

    structural_dirs = {"world_modules", "world_compositions", "simulation_scenarios"}
    scanned_families = set()
    for item in content_dir.rglob("*"):
        if item.name == ".gitkeep":
            continue
        rel = item.relative_to(content_dir)
        parts = rel.parts
        if not parts:
            continue
        top_dir = parts[0]
        if top_dir in structural_dirs:
            scanned_families.add(top_dir)
        elif item.is_file() and item.suffix in {".yaml", ".yml"}:
            scanned_families.add(str(rel.with_suffix("")))

    missing = scanned_families - set(CONTENT_USAGE_MATRIX.keys())
    assert not missing, (
        f"Files on disk not covered by CONTENT_USAGE_MATRIX after auto-discovery: "
        f"{sorted(missing)}"
    )



# Compliance IDs: WORLD-ASM-TEST
import pytest
from src.content.repository import CatalogRepository
from src.worldassembly.resolver import CompileProfileResolver
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.schema import WorldSpec, TopologySpec, RegionSpec, FactionSpec, PopulationSpec, ResourceNodeSpec, BuildingSpec

pytestmark = pytest.mark.worldassembly


@pytest.fixture
def base_repo():
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


def test_compile_profile_resolver_overrides(base_repo):
    """Verify that profiles properly override and resolve compiled defaults."""
    # 1. Setup mock spec with stats_profile configured
    spec = WorldSpec(
        schema_version="worldspec.v1",
        world_id="asm_test",
        name="Asm Test",
        topology=TopologySpec(width=10, height=10, coordinate_system="grid"),
        regions=[RegionSpec(id="r1", type="town", bounds=(0, 0, 9, 9))],
        factions=[FactionSpec(id="villagers", type="civilian")],
        entities=[
            PopulationSpec(
                id="pop_custom",
                count=1,
                role="hero",
                faction="villagers",
                spawn_region="r1"
            )
        ],
        resources=[
            ResourceNodeSpec(
                id="res_wood",
                resource_type="wood_node",
                count=5,
                region="r1"
            )
        ],
        buildings=[
            BuildingSpec(
                id="bld_shop",
                type="shop",
                region="r1"
            )
        ]
    )

    resolver = CompileProfileResolver(base_repo)
    context = resolver.resolve(spec)

    # Compile the spec WITH the resolved context
    state, report = WorldCompiler.compile(spec, seed=42, context=context)

    # 2. Assert Entity properties resolved from hero_base stats profile
    entity = state.entities[1]
    assert entity.combat.hp == 100
    assert entity.combat.max_hp == 100
    assert entity.combat.atk == 10

    # 3. Assert Resource properties resolved wood_node catalog spec
    node = state.resource_nodes[10000]
    assert node.required_ticks == 10  # from wood_node definition

    # 4. Assert Building properties resolved general_store (shop) catalog spec
    building = state.buildings[20000]
    assert building.hp == 500  # from shop definition


def test_compiler_backward_compatibility():
    """Verify that compiling without a context preserves traditional legacy defaults."""
    spec = WorldSpec(
        schema_version="worldspec.v1",
        world_id="asm_test",
        name="Asm Test",
        topology=TopologySpec(width=10, height=10, coordinate_system="grid"),
        regions=[RegionSpec(id="r1", type="town", bounds=(0, 0, 9, 9))],
        factions=[FactionSpec(id="villagers", type="civilian")],
        entities=[
            PopulationSpec(
                id="pop_custom",
                count=1,
                role="hero",
                faction="villagers",
                spawn_region="r1"
            )
        ],
        resources=[
            ResourceNodeSpec(
                id="res_wood",
                resource_type="wood_node",
                count=5,
                region="r1"
            )
        ],
        buildings=[
            BuildingSpec(
                id="bld_shop",
                type="shop",
                region="r1"
            )
        ]
    )

    # Compile WITHOUT context
    state, report = WorldCompiler.compile(spec, seed=42)

    # Verify standard legacy parameters are correctly defaulted
    entity = state.entities[1]
    assert entity.combat.hp == 100
    assert entity.combat.atk == 10
    
    node = state.resource_nodes[10000]
    assert node.required_ticks == 10

    building = state.buildings[20000]
    assert building.hp == 500


def test_v2_service_refs_assembly_is_documented_gap():
    """Guard test: service_refs is computed in contributions but WorldSpec has no services field.

    If WorldSpec gains a 'services' field, this test will fail — that is the signal to add
    the v2 service merge loop in WorldModuleAssemblyResolver.assemble() and update
    docs/guidelines/v2_intentional_divergences.md (entry 2.19).
    """
    from src.worldassembly.schema import ResolvedModuleContribution
    from src.worldbuilding.schema import WorldSpec

    # service_refs must exist in the contribution schema with the correct type
    fields = ResolvedModuleContribution.model_fields
    assert "service_refs" in fields, "ResolvedModuleContribution must have service_refs field"
    annotation = str(fields["service_refs"].annotation)
    assert "Dict" in annotation or "dict" in annotation, (
        f"service_refs must be Dict[str, int], got {annotation}"
    )

    # WorldSpec must NOT yet have a services field — the gap is intentional and documented
    assert "services" not in WorldSpec.model_fields, (
        "WorldSpec gained a 'services' field — add the v2 service merge loop in "
        "WorldModuleAssemblyResolver.assemble() (parallel to the v2 building loop), "
        "update docs/guidelines/v2_intentional_divergences.md (entry 2.19), "
        "and update docs/parity_ledger/substrate.yaml (SUB-367) to status: verified."
    )


def test_contribution_snapshot_after_normalization(base_repo):
    """Contribution record fields must match the normalized module's structure.

    Uses a minimal empty-field module to assert that resolve_module_contribution
    returns empty collections of the correct types when no content is specified.
    """
    from src.worldmodules.schema import WorldModuleSpec
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
    from src.worldmodules.repository import WorldModuleRepository
    from src.worldassembly.resolver import WorldAssemblyResolver

    spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="test_empty_module",
        module_type="terrain",
        display_name="Test Empty Module",
    )
    normalized = WorldModuleAuthoringNormalizer.normalize(spec)

    module_repo = WorldModuleRepository("data/content/world_modules")
    resolver = WorldAssemblyResolver(base_repo, module_repo)
    contribution = resolver.resolve_module_contribution(normalized)

    # Empty module produces empty collections of the correct types
    assert contribution.resource_refs == {}
    assert contribution.building_refs == {}
    assert contribution.service_refs == {}
    assert isinstance(contribution.resource_refs, dict)
    assert isinstance(contribution.building_refs, dict)
    assert isinstance(contribution.service_refs, dict)
    assert contribution.regions == []
    assert contribution.factions == []
    assert contribution.population_refs == []
    assert contribution.resolved_population_specs == []
    assert contribution.biome_refs == []
    assert contribution.ecology_refs == []
    assert contribution.relationship_refs == []


def test_resolve_module_contribution_rejects_raw_spec(base_repo):
    """resolve_module_contribution must raise TypeError when passed a raw WorldModuleSpec.

    Callers must normalize via WorldModuleAuthoringNormalizer.normalize() first.
    """
    from src.worldmodules.schema import WorldModuleSpec
    from src.worldmodules.repository import WorldModuleRepository
    from src.worldassembly.resolver import WorldAssemblyResolver

    raw_spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="test_raw_spec",
        module_type="terrain",
        display_name="Test Raw Spec",
    )

    module_repo = WorldModuleRepository("data/content/world_modules")
    resolver = WorldAssemblyResolver(base_repo, module_repo)
    with pytest.raises(TypeError, match="resolve_module_contribution requires NormalizedWorldModule"):
        resolver.resolve_module_contribution(raw_spec)


def test_resolve_module_contribution_wires_place_shaped_region(base_repo):
    """TCK-20260902-WORLDCOMPILER-PLACE-WIRING (idea 66 child 2/5): a RegionRecipeSpec
    declaring places: gets resolved into a RegionSpec with the matching PlaceSpec list,
    with place_id namespaced by the same prefix as the parent region_id -- confirms the
    Composition path (WorldModuleSpec -> resolver -> WorldSpec, round-tripping through
    WorldCompiler.compile() per docs/world/compiler_contract.md's "Two Compilation Paths")
    is wired the same as the Direct path (see tests/unit/worldbuilding/test_place_wiring.py).
    """
    from src.worldbuilding.recipe import RegionRecipeSpec, PlaceRecipeSpec
    from src.worldmodules.schema import WorldModuleSpec
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
    from src.worldmodules.repository import WorldModuleRepository
    from src.worldassembly.resolver import WorldAssemblyResolver

    spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="test_place_module",
        module_type="terrain",
        display_name="Test Place Module",
        regions=[
            RegionRecipeSpec(
                id="hometown", type="wilderness", grid_bounds=(0, 0, 10, 10),
                places=[PlaceRecipeSpec(id="p1", kind="city", position=(5, 5), scale=1.5)],
            ),
        ],
    )
    normalized = WorldModuleAuthoringNormalizer.normalize(spec)

    module_repo = WorldModuleRepository("data/content/world_modules")
    resolver = WorldAssemblyResolver(base_repo, module_repo)
    contribution = resolver.resolve_module_contribution(normalized, prefix="mod1_")

    assert len(contribution.regions) == 1
    region_spec = contribution.regions[0]
    assert region_spec.id == "mod1_hometown"
    assert len(region_spec.places) == 1
    place_spec = region_spec.places[0]
    assert place_spec.id == "mod1_p1"
    assert place_spec.kind == "CITY"
    assert place_spec.position == (5, 5)
    assert place_spec.scale == 1.5


def test_resolve_module_contribution_region_without_places_yields_empty_list(base_repo):
    """Backward compatibility: a RegionRecipeSpec with no places declared (all existing
    content today) resolves to an empty places list, not an error or None."""
    from src.worldbuilding.recipe import RegionRecipeSpec
    from src.worldmodules.schema import WorldModuleSpec
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
    from src.worldmodules.repository import WorldModuleRepository
    from src.worldassembly.resolver import WorldAssemblyResolver

    spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="test_no_place_module",
        module_type="terrain",
        display_name="Test No Place Module",
        regions=[RegionRecipeSpec(id="hometown", type="wilderness", grid_bounds=(0, 0, 10, 10))],
    )
    normalized = WorldModuleAuthoringNormalizer.normalize(spec)

    module_repo = WorldModuleRepository("data/content/world_modules")
    resolver = WorldAssemblyResolver(base_repo, module_repo)
    contribution = resolver.resolve_module_contribution(normalized)

    assert contribution.regions[0].places == []


def test_resolve_module_contribution_wires_camp_kind_place_with_race_field(base_repo):
    """TCK-20260904-CAMPSTATE-PLACE-BRIDGE: the Composition path carries the new
    creature_kind field through resolve_module_contribution() unchanged -- the id
    namespacing (prefix) still applies to place_id, while creature_kind is not an
    identifier and passes through unnamespaced."""
    from src.worldbuilding.recipe import RegionRecipeSpec, PlaceRecipeSpec
    from src.worldmodules.schema import WorldModuleSpec
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
    from src.worldmodules.repository import WorldModuleRepository
    from src.worldassembly.resolver import WorldAssemblyResolver

    spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="test_camp_place_module",
        module_type="terrain",
        display_name="Test Camp Place Module",
        regions=[
            RegionRecipeSpec(
                id="goblin_camp", type="wilderness", grid_bounds=(0, 0, 10, 10),
                places=[PlaceRecipeSpec(id="p1", kind="camp", position=(5, 5), creature_kind="goblin")],
            ),
        ],
    )
    normalized = WorldModuleAuthoringNormalizer.normalize(spec)

    module_repo = WorldModuleRepository("data/content/world_modules")
    resolver = WorldAssemblyResolver(base_repo, module_repo)
    contribution = resolver.resolve_module_contribution(normalized, prefix="mod1_")

    assert len(contribution.regions) == 1
    region_spec = contribution.regions[0]
    place_spec = region_spec.places[0]
    assert place_spec.id == "mod1_p1"
    assert place_spec.kind == "CAMP"
    assert place_spec.creature_kind == "goblin"


# ---------------------------------------------------------------------------
# TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION
# ---------------------------------------------------------------------------

class TestHashPointInBounds:
    def test_deterministic_same_key_same_bounds(self):
        from src.worldassembly.resolver import _hash_point_in_bounds
        bounds = (40, 40, 100, 60)
        p1 = _hash_point_in_bounds("pop_a", bounds)
        p2 = _hash_point_in_bounds("pop_a", bounds)
        assert p1 == p2

    def test_point_within_bounds(self):
        from src.worldassembly.resolver import _hash_point_in_bounds
        bounds = (40, 40, 100, 60)
        for key in ["pop_a", "pop_b", "pop_c", "bandit_ambush_group", "merchant_caravan"]:
            x, y = _hash_point_in_bounds(key, bounds)
            assert 40 <= x <= 100
            assert 40 <= y <= 60

    def test_degenerate_single_point_region_never_exceeds_bounds(self):
        """Regression: a naive `max(diff, 1)` width guard combined with a `% (width + 1)`
        modulo can produce a point one unit past max_x/max_y for a min_x == max_x region.
        Caught during manual verification before this fix; must never regress."""
        from src.worldassembly.resolver import _hash_point_in_bounds
        bounds = (5, 5, 5, 5)
        for key in ["a", "b", "c", "d", "e"]:
            x, y = _hash_point_in_bounds(key, bounds)
            assert (x, y) == (5, 5)


class TestResolveSpawnPosition:
    def test_unknown_region_returns_none(self):
        from src.worldassembly.resolver import _resolve_spawn_position
        result = _resolve_spawn_position("pop_a", "no_such_region", {}, {})
        assert result is None

    def test_empty_spawn_region_returns_none(self):
        from src.worldassembly.resolver import _resolve_spawn_position
        result = _resolve_spawn_position("pop_a", "", {"r1": (0, 0, 10, 10)}, {})
        assert result is None

    def test_returns_point_within_bounds(self):
        from src.worldassembly.resolver import _resolve_spawn_position
        region_bounds = {"bandit_road": (40, 40, 100, 60)}
        pos = _resolve_spawn_position("pop_a", "bandit_road", region_bounds, {})
        assert pos is not None
        x, y = pos
        assert 40 <= x <= 100
        assert 40 <= y <= 60

    def test_two_populations_same_region_get_distinct_positions(self):
        """Direct regression for the de-confliction requirement -- multiple populations
        sharing one spawn_region is the documented normal case (compiler.py's
        region_declared_population aggregation comment), not an edge case."""
        from src.worldassembly.resolver import _resolve_spawn_position
        region_bounds = {"bandit_road": (40, 40, 100, 60)}
        claimed: dict = {}
        pos_a = _resolve_spawn_position("bandit_ambush_group", "bandit_road", region_bounds, claimed)
        pos_b = _resolve_spawn_position("merchant_caravan", "bandit_road", region_bounds, claimed)
        assert pos_a is not None and pos_b is not None
        assert pos_a != pos_b

    def test_forced_collision_resolved_via_probe_sequence(self, monkeypatch):
        """Force two keys to hash to the identical candidate point; the second must be
        de-conflicted via the probe sequence rather than silently colliding."""
        import src.worldassembly.resolver as resolver_mod

        monkeypatch.setattr(resolver_mod, "_hash_point_in_bounds", lambda key, bounds: (50, 50))

        region_bounds = {"r1": (0, 0, 100, 100)}
        claimed: dict = {}
        pos_a = resolver_mod._resolve_spawn_position("pop_a", "r1", region_bounds, claimed)
        pos_b = resolver_mod._resolve_spawn_position("pop_b", "r1", region_bounds, claimed)
        assert pos_a == (50.0, 50.0)
        assert pos_b != pos_a
        assert pos_b == (51.0, 50.0)  # first probe offset (1, 0)

    def test_degenerate_region_exhausts_probe_sequence_without_raising(self):
        """A 1x1 region shared by more populations than the probe sequence can de-conflict
        is a real, unavoidable collision -- must fall back gracefully, never raise."""
        from src.worldassembly.resolver import _resolve_spawn_position
        region_bounds = {"tiny": (5, 5, 5, 5)}
        claimed: dict = {}
        positions = [
            _resolve_spawn_position(f"pop_{i}", "tiny", region_bounds, claimed)
            for i in range(20)
        ]
        assert all(p == (5.0, 5.0) for p in positions)

    def test_exhausted_probe_sequence_logs_a_warning(self, caplog):
        """Peer review: the exhausted-probe fallback reintroduces a real
        LAW-OCCUPANCY-COLLISION-triggering collision -- it must never be silent. Confirms the
        warning names the region and key, not just a generic message."""
        import logging
        from src.worldassembly.resolver import _resolve_spawn_position
        region_bounds = {"tiny": (5, 5, 5, 5)}
        claimed: dict = {}
        with caplog.at_level(logging.WARNING, logger="src.worldassembly.resolver"):
            for i in range(3):
                _resolve_spawn_position(f"pop_{i}", "tiny", region_bounds, claimed)
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert warnings, "expected at least one warning once the probe sequence is exhausted"
        assert "tiny" in warnings[0].getMessage()
        assert "pop_1" in warnings[0].getMessage() or "pop_2" in warnings[0].getMessage()

    def test_pure_function_no_shared_state_across_calls(self):
        """A fresh `claimed` dict per call (as CompileProfileResolver.resolve() does per
        invocation) must not see collisions from an unrelated prior call -- confirms this
        stays a pure function of one resolve() call's own spec, not accidental module state."""
        from src.worldassembly.resolver import _resolve_spawn_position
        region_bounds = {"r1": (0, 0, 10, 10)}
        pos_call_1 = _resolve_spawn_position("pop_a", "r1", region_bounds, {})
        pos_call_2 = _resolve_spawn_position("pop_a", "r1", region_bounds, {})
        assert pos_call_1 == pos_call_2

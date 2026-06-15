# Compliance IDs: WORLD-ASM-003, WORLD-ASM-009
import pytest
from src.content.repository import CatalogRepository
from src.content.resolver import ResolverError, SocialDefaultsResolver
from src.worldmodules.repository import WorldModuleRepository
from src.worldassembly.context import CompileContext
from src.worldassembly.resolver import WorldAssemblyResolver
from src.worldassembly.schema import WorldCompositionSpec, ModuleRefSpec

pytestmark = pytest.mark.worldassembly


@pytest.fixture
def repos():
    cat = CatalogRepository("data/content")
    cat.load_all()
    mod = WorldModuleRepository("data/world_modules")
    mod.load_all()
    return cat, mod


def _minimal_composition(perspectives=None):
    return WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="persp_test_world",
        name="Perspective Test World",
        module_refs=[
            ModuleRefSpec(module_id="plains_layout", enabled=True, order=0),
            ModuleRefSpec(module_id="standard_villagers", enabled=True, order=1),
        ],
        default_perspectives=perspectives if perspectives is not None else [],
    )


def test_known_perspective_resolves(repos):
    cat, mod = repos
    composition = _minimal_composition(["hero_guild_perspective"])
    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(composition)
    perspectives = bundle.compile_context.perspectives
    assert "hero_guild_perspective" in perspectives
    data = perspectives["hero_guild_perspective"]
    assert isinstance(data, dict)
    assert data["chosen_faction"] == "hero_guild"
    assert "default_focus" in data
    assert "projected_labels" in data


def test_unknown_perspective_raises_resolver_error(repos):
    cat, mod = repos
    composition = _minimal_composition(["unknown_xyz"])
    resolver = WorldAssemblyResolver(cat, mod)
    with pytest.raises(ResolverError) as exc_info:
        resolver.assemble(composition)
    assert "unknown_xyz" in str(exc_info.value)


def test_empty_perspectives_assembles_cleanly(repos):
    cat, mod = repos
    composition = _minimal_composition([])
    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(composition)
    assert bundle.compile_context.perspectives == {}


def test_multiple_perspectives_all_resolved(repos):
    cat, mod = repos
    composition = _minimal_composition(["hero_guild_perspective", "goblin_warband_perspective"])
    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(composition)
    perspectives = bundle.compile_context.perspectives
    assert "hero_guild_perspective" in perspectives
    assert "goblin_warband_perspective" in perspectives
    assert perspectives["hero_guild_perspective"]["chosen_faction"] == "hero_guild"
    assert perspectives["goblin_warband_perspective"]["chosen_faction"] == "goblin_warband"


def test_perspectives_in_to_dict(repos):
    cat, mod = repos
    composition = _minimal_composition(["hero_guild_perspective"])
    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(composition)
    ctx_dict = bundle.compile_context.to_dict()
    assert "perspectives" in ctx_dict
    assert "hero_guild_perspective" in ctx_dict["perspectives"]
    assert ctx_dict["perspectives"]["hero_guild_perspective"]["chosen_faction"] == "hero_guild"


def test_perspectives_from_dict_backward_compat():
    raw = {
        "entities": {},
        "buildings": {},
        "resources": {},
        "factions": {},
        "region_ownership": {},
        "legacy_factions": {},
        "legacy_roles": {},
    }
    ctx = CompileContext.from_dict(raw)
    assert ctx.perspectives == {}


def test_register_perspective_stores_dict(repos):
    cat, _ = repos
    social_resolver = SocialDefaultsResolver(cat)
    persp_def = social_resolver.resolve_perspective("merchant_league_perspective")
    ctx = CompileContext()
    ctx.register_perspective("merchant_league_perspective", persp_def)
    assert "merchant_league_perspective" in ctx.perspectives
    stored = ctx.perspectives["merchant_league_perspective"]
    assert isinstance(stored, dict)
    assert stored["chosen_faction"] == "merchant_league"

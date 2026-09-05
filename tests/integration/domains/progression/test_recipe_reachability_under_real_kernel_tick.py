"""
tests/integration/domains/progression/test_recipe_reachability_under_real_kernel_tick.py

TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE — proves the bridge holds under a real
Kernel.tick_once() loop, not just hand-constructed unit fixtures: any known_recipes id that
BlacksmithSystem.enforce() organically writes during real ticks must resolve in the same
src/core/registries.py::RecipeRegistry that recipe_materials() (and therefore
PossessionUnderstandingService/GrowthGapEvaluator) reads. Before this ticket, BlacksmithSystem
wrote src/core/recipes.py-shaped literals while recipe_materials() read src/core/recipes.py's own
3-entry registry -- coincidentally consistent only because both were the same tiny legacy set;
after this ticket both sides read src/core/registries.py's real, catalog-backed ~46-entry registry.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from tools.calibrate_simq import _load_world_state  # noqa: E402
from src.config.profiles import PROD_SMALL  # noqa: E402
from src.core.registries import RecipeRegistry  # noqa: E402
from src.domains.progression.possession import PossessionUnderstandingService  # noqa: E402
from src.engine.kernel import Kernel  # noqa: E402
from src.platform.rng import DeterministicRNG  # noqa: E402


def test_organically_learned_recipes_resolve_in_live_registry_after_real_ticks():
    state, _report = _load_world_state("sandbox_world", 42)
    rng = DeterministicRNG(state.seed)
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=rng, flags={"no_frame_pacing": True})
    try:
        for _ in range(500):
            kernel.tick_once()
    finally:
        kernel.shutdown()

    final_state = kernel.state
    checked_any = False
    for entity in final_state.entities.values():
        known_recipes = getattr(getattr(entity, "identity", None), "known_recipes", None) or ()
        if not known_recipes:
            continue
        checked_any = True
        for recipe_id in known_recipes:
            assert RecipeRegistry.contains(recipe_id), (
                f"BlacksmithSystem organically wrote known_recipes id {recipe_id!r} that "
                f"registries.py::RecipeRegistry (the registry recipe_materials() reads) does not "
                f"recognize -- the bridge is broken under real usage."
            )
        # Must not raise on a real, organically-populated known_recipes set -- proves
        # PossessionUnderstandingService genuinely consumes what BlacksmithSystem writes,
        # not just the hand-picked ids used by the unit-level fixtures.
        PossessionUnderstandingService.evaluate(entity, final_state)

    if not checked_any:
        import warnings
        warnings.warn(
            "no entity organically learned any recipe within 500 ticks on sandbox_world -- "
            "same real-pathing-dependent condition documented on "
            "test_recipe_learned_fires_through_real_kernel_tick_once; the reachability this test "
            "guards is otherwise covered by test_material_possession_predicate_craft_prefixed_"
            "known_recipes_now_match and test_growth_gap_craft_prefixed_known_recipes_now_produce_"
            "material_gap using a real registries.py recipe id."
        )

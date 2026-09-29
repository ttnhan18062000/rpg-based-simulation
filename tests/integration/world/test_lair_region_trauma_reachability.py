"""
Integration regression guard for TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING (Card
J, J2 -- `regional_trauma`, adopting TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES).

Pins the ticket's Level-1/Level-2 finding: `generated_frontier_3_42`'s `moon_cave` region (the
corpus's only real LAIR-kind Place, `moon_cave_lair`,
data/content/world_modules/moon_cult_ruins.yaml) records zero deaths -- and therefore zero
`trauma_score` accrual -- across a full real 5000-tick `Kernel.tick_once()` run. Root cause is
spatial isolation, a fixed geometric fact of the world's composition (`moon_cave`'s
`grid_bounds: [100, 70, 130, 110]` sits ~30 units from the nearest populated region,
`orc_stronghold`/`orc_clan_territory`), not a wrong trauma threshold or broken accrual code --
the accrual/decay code itself (src/engine/world_dynamics.py "Death-triggered Trauma" block,
RegionalConsequenceService.process_recovery()) is real, correct, and wired elsewhere in the
corpus.

Recorded exit claim: CONDITION. The current registry label for `regional_trauma`
(`state: done`, `verified.verdict: contradicted`, dated 2026-09-17) already states this
accurately -- no registry label correction is warranted.

This is a "welcome failure" test by design: if a future world-composition change places a
hostile faction within combat range of `moon_cave`, this test starts failing -- that is the
signal the CONDITION classification needs re-examination, not a bug in the test to be silenced
or deleted.

Mirrors the Kernel/WorldRepository/WorldCompiler construction shape used by
tests/unit/worldassembly/test_corpus_diversity.py's own `generated_frontier_3_42` long-run
tests (`test_generated_frontier_3_42_extended_population_stability`).
"""
from __future__ import annotations

import pytest

from src.config.profiles import PROD_SMALL
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

pytestmark = pytest.mark.integration

_WORLD_ID = "generated_frontier_3_42"
_SEED = 42
_TICKS = 5000


@pytest.mark.resource_budget_large
def test_moon_cave_region_records_zero_trauma_across_full_corpus_run():
    repo = WorldRepository("data/worlds")
    spec = repo.load_world(_WORLD_ID)
    state, _report = WorldCompiler.compile(spec, _SEED)

    assert "moon_cave" in state.regions, (
        f"{_WORLD_ID} no longer composes a 'moon_cave' region -- this test's own fixture "
        "assumption changed; re-locate J2's LAIR-kind region before deciding whether the "
        "CONDITION classification still holds."
    )

    rng = DeterministicRNG(_SEED)
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=rng, flags={"no_frame_pacing": True})
    try:
        for _tick in range(1, _TICKS + 1):
            kernel.tick_once()
    finally:
        try:
            kernel.shutdown()
        except Exception:
            pass

    moon_cave = kernel._state.regions["moon_cave"]
    assert moon_cave.trauma_score == 0.0, (
        f"moon_cave.trauma_score is {moon_cave.trauma_score} after {_TICKS} ticks, not 0.0 -- "
        "J2's spatial-isolation CONDITION finding "
        "(TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING) may no longer hold. This "
        "is a welcome result, but it means the registry's `regional_trauma` exit claim needs "
        "re-examination, not a silent pass."
    )

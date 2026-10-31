"""World dynamics do not depend on presentation: the same seeded run, with and without the read models (the API presenters) being called
between every tick, ends in an identical canonical state hash.

audit_mode is on: it zeroes the wall-clock pressure signals, without which two quiet runs of the same seed can differ under machine load.

Sources: tests/helpers/scenario.py (the real Kernel), src/api/presenters/state_presenter.py (StatePresenter).
"""
import copy

from src.api.presenters.state_presenter import StatePresenter
from src.config.profiles import PROD_SMALL
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from tests.helpers.scenario import DEFAULT_FLAGS, compile_world

TICKS = 40


def _run(read_between_ticks, ticks=TICKS):
    state = compile_world("sandbox_world", 42)
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(42), flags={**DEFAULT_FLAGS, "audit_mode": True})
    reads = 0
    try:
        for _ in range(ticks):
            kernel.tick_once()
            if read_between_ticks:
                StatePresenter.present_minimal(kernel._state)
                StatePresenter.present_full(kernel._state)
                reads += 1
        return CanonicalStateHasher.get_hash(kernel._state), reads
    finally:
        kernel.shutdown()


def test_reading_every_tick_does_not_change_the_final_state():
    quiet_hash, _ = _run(read_between_ticks=False)
    read_hash, reads = _run(read_between_ticks=True)

    assert reads == TICKS
    assert read_hash == quiet_hash


def test_the_hash_is_able_to_tell_runs_apart():
    """Positive control: one tick fewer gives a different hash, so an equal hash above is evidence, not a constant."""
    assert _run(False, ticks=TICKS - 1)[0] != _run(False)[0]

"""Replay-diff helper, limited to the verified reproducibility envelope.

Reproducibility is verified only for a hand-built `AuthoritativeState` + `Kernel`, with the seed, tick
bound and `RuntimeProfile` used by
`tests/integration/kernel/test_determinism_suite.py::test_reproducibility` (constants
`REPRODUCIBILITY_SEED`, `REPRODUCIBILITY_TICKS`, `REPRODUCIBILITY_PROFILE`, imported below, never
restated here). Outside that envelope -- compiled worlds, other seeds or profiles, longer runs -- the helper does
not run and returns `outside-verified-scope`, never identical/different. Long-run determinism is parked, so
the envelope widens only when a new reproducibility test proves a wider scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

from src.config.profiles import RuntimeProfile
from src.core.state import AuthoritativeState
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from tests.integration.kernel.test_determinism_suite import (
    REPRODUCIBILITY_PROFILE,
    REPRODUCIBILITY_SEED,
    REPRODUCIBILITY_TICKS,
)

IDENTICAL = "identical"
DIFFERENT = "different"
OUTSIDE_VERIFIED_SCOPE = "outside-verified-scope"

HAND_BUILT = "hand-built"
EXECUTOR = "default"  # the kernel's default executor, as in the verified test


@dataclass(frozen=True)
class ReplayDiff:
    verdict: str
    reasons: Tuple[str, ...]
    seed: Optional[int]
    profile: str
    executor: str
    ticks: int
    world_source: str
    hashes: Tuple[str, ...] = ()


def envelope_violations(*, seed: Optional[int], ticks: int, profile: RuntimeProfile, world_source: str) -> List[str]:
    reasons: List[str] = []
    if world_source != HAND_BUILT:
        reasons.append(f"world_source {world_source!r} is not {HAND_BUILT!r}")
    if seed is None:
        reasons.append("unseeded run")
    elif seed != REPRODUCIBILITY_SEED:
        reasons.append(f"seed {seed} is not the verified seed {REPRODUCIBILITY_SEED}")
    if not 0 <= ticks <= REPRODUCIBILITY_TICKS:
        reasons.append(f"ticks {ticks} is outside 0..{REPRODUCIBILITY_TICKS}")
    if profile != REPRODUCIBILITY_PROFILE:
        reasons.append(f"profile {profile.name!r} is not the verified profile {REPRODUCIBILITY_PROFILE.name!r}")
    return reasons


def replay_diff(
    build_state: Callable[[], AuthoritativeState],
    *,
    seed: Optional[int],
    ticks: int,
    profile: RuntimeProfile = REPRODUCIBILITY_PROFILE,
    world_source: str = HAND_BUILT,
) -> ReplayDiff:
    """Replay `build_state()` twice from fresh states and compare final canonical hashes."""
    meta = dict(seed=seed, profile=profile.name, executor=EXECUTOR, ticks=ticks, world_source=world_source)
    reasons = envelope_violations(seed=seed, ticks=ticks, profile=profile, world_source=world_source)
    if reasons:
        return ReplayDiff(verdict=OUTSIDE_VERIFIED_SCOPE, reasons=tuple(reasons), **meta)
    hashes = []
    for _ in range(2):
        kernel = Kernel(profile, build_state(), DeterministicRNG(seed))
        try:
            for _ in range(ticks):
                kernel.tick_once()
            hashes.append(CanonicalStateHasher.get_hash(kernel._state))
        finally:
            kernel.shutdown()
    return ReplayDiff(verdict=IDENTICAL if hashes[0] == hashes[1] else DIFFERENT, reasons=(), hashes=tuple(hashes), **meta)

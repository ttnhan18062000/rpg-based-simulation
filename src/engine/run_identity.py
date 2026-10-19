"""
src/engine/run_identity.py
───────────────────────────────────────────────────────────────────────────────
TCK-20261011-DEFAULT-RUN-ID-CANNOT-COLLIDE-ACROSS-SAME-SEED-PROCESSES

A run's name and its directory. The run id is a name only: it is in no state hash and draws nothing from the simulation RNG (the seeded suffix is a
stateless pure function of the seed, kept so ids stay recognisable).
"""
from __future__ import annotations

import os
import time
import uuid
from typing import Any

from src.core.enums import Domain


def default_run_id(seeded_suffix: int) -> str:
    """A run id no other process can also pick: the wall-clock second, the seeded suffix, the process id and a NON-seeded nonce."""
    return f"run_{int(time.time())}_{seeded_suffix}_{os.getpid()}_{uuid.uuid4().hex[:8]}"


def new_run_id(rng: Any) -> str:
    """A fresh default run id; the suffix is a stateless draw (a pure function of the seed), so it moves no other draw."""
    draw = rng.get_int(Domain.INIT, 0, 0, 1000, 9999)
    return default_run_id(draw if isinstance(draw, int) else 0)  # a stand-in rng (a test mock) returns an object whose repr must never name a directory


def create_run_directory(repo: Any, run_id: str, manifest: Any, *, is_default: bool, rng: Any) -> str:
    """Create the run directory and return the run id actually used. An explicit run id may replace its own directory (the caller named it). A
    default id never touches an existing directory: it takes a fresh id and tries again, so two processes can never share one."""
    if not is_default:
        repo.create_run(run_id, manifest, overwrite=True)
        return run_id
    for _attempt in range(8):
        try:
            repo.create_run(run_id, manifest.model_copy(update={"run_id": run_id}), overwrite=False)
            return run_id
        except FileExistsError:
            run_id = new_run_id(rng)
    raise FileExistsError(f"no unused default run directory after 8 attempts (last id {run_id})")

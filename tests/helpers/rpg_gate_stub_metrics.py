"""A stand-in for rpg's metric module, following the ``rpg-gate-metrics/v1`` contract, for the harness tests (child 3 of the rpg gate epic).

``compute`` reports the entity count and the tick as one run outcome row and a zero-violation validity row; ``pool`` sums the validity rows over seeds.
Each outcome row carries its own ``k`` and ``floor`` and each validity row its ``oracle``, as rpg's module will. Two behaviours exist only so tests can prove isolation and failure handling: ``LEAK`` is a module global that every call increments (a fresh process
always sees 1), and the environment variable ``RPG_GATE_STUB_CRASH_SEED`` makes ``compute`` raise for that seed.
"""
from __future__ import annotations

import os

LEAK = 0


def compute(art):
    global LEAK
    LEAK += 1
    if os.environ.get("RPG_GATE_STUB_CRASH_SEED") == str(art.seed):
        raise RuntimeError(f"stub crash for seed {art.seed}")
    return [
        {"id": "S1.entities", "class": "outcome", "scope": "run", "group": "*", "tick": art.ticks, "value": len(art.state.entities), "k": 2.0, "floor": 1.0},
        {"id": "S2.leak", "class": "outcome", "scope": "run", "group": "*", "value": LEAK, "k": 2.0, "floor": 1.0},
        {"id": "V9", "class": "validity", "scope": "run", "group": "*", "violations": 0, "examples": [], "oracle": "stub-oracle", "counts": {"opaque": art.seed, "events_file_exists": art.events_path.exists()}},
    ]


def pool(docs):
    return [{"id": "V9", "class": "validity", "scope": "pooled", "group": "*", "violations": 0, "examples": [], "oracle": "stub-oracle"}]

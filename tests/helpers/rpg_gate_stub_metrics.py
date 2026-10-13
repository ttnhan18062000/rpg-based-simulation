"""A stand-in for rpg's metric module, following the ``rpg-gate-metrics/v1`` contract, for the harness tests (child 3 of the rpg gate epic).

``compute`` reports the entity count and the tick as one run outcome row and a zero-violation validity row; ``pool`` sums the validity rows over seeds.
Each outcome row carries its own ``k`` and ``floor`` and each validity row its ``oracle``, as rpg's module will. Two behaviours exist only so tests can prove isolation and failure handling: ``LEAK`` is a module global that every call increments (a fresh process
always sees 1), and the environment variable ``RPG_GATE_STUB_CRASH_SEED`` makes ``compute`` raise for that seed. ``RPG_GATE_STUB_V8`` (``absent`` by default, ``clean`` or ``violations``) adds a V8 row in the contract's shape (see :func:`v8_rows`).
"""
from __future__ import annotations

import os

LEAK = 0

V8_ORACLE = "docs/plans/test_architecture/reference/rpg_gate_baseline_format.md#v8-every-entity-added-mid-run-has-a-declared-source"
V8_MODES = ("absent", "clean", "violations")  # RPG_GATE_STUB_V8: no V8 row (the default), a V8 row at 0 violations, a V8 row with violations


def v8_rows(mode: str, seed=None):
    """The V8 row(s) the stub can emit, shaped as the contract in ``rpg_gate_baseline_format.md`` says: validity, group = kind group, a tally keyed
    ``<kind_group>:<source.kind>`` plus ``unsourced``, and per-violation examples of ``{entity_id, tick, site, check}``. ``absent`` emits nothing."""
    if mode not in V8_MODES:
        raise ValueError(f"unknown V8 stub mode {mode!r}; expected one of {V8_MODES}")
    if mode == "absent":
        return []
    bad = mode == "violations"
    counts = {"humanoid:BIRTH": 2, "humanoid:INITIAL": 40, "unsourced": 1 if bad else 0}
    examples = [{"entity_id": 91, "tick": 30, "site": "camp.spawn_monster", "check": "unsourced"}] if bad else []
    row = {"id": "V8", "class": "validity", "group": "*", "violations": len(examples), "examples": examples, "oracle": V8_ORACLE, "counts": counts}
    return [{**row, "scope": "run"}]


def compute(art):
    global LEAK
    LEAK += 1
    if os.environ.get("RPG_GATE_STUB_CRASH_SEED") == str(art.seed):
        raise RuntimeError(f"stub crash for seed {art.seed}")
    return [
        {"id": "S1.entities", "class": "outcome", "scope": "run", "group": "*", "tick": art.ticks, "value": len(art.state.entities), "k": 2.0, "floor": 1.0},
        {"id": "S2.leak", "class": "outcome", "scope": "run", "group": "*", "value": LEAK, "k": 2.0, "floor": 1.0},
        {"id": "V9", "class": "validity", "scope": "run", "group": "*", "violations": 0, "examples": [], "oracle": "stub-oracle", "counts": {"opaque": art.seed, "events_file_exists": art.events_path.exists()}},
        *v8_rows(os.environ.get("RPG_GATE_STUB_V8", "absent"), art.seed),
    ]


def pool(docs):
    rows = [{"id": "V9", "class": "validity", "scope": "pooled", "group": "*", "violations": 0, "examples": [], "oracle": "stub-oracle"}]
    mode = os.environ.get("RPG_GATE_STUB_V8", "absent")
    for row in v8_rows(mode):
        rows.append({**row, "scope": "pooled", "violations": sum(d_row.get("violations", 0) for d in docs for d_row in d.get("metrics", []) if d_row.get("id") == "V8")})
    return rows

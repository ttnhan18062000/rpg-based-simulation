"""Every seed of a world emits the same (id, group, key, tick) rows (TCK-20261020-RPG-GATE-ROWS-COME-FROM-DECLARED-DOMAINS).

Two real seeds of one world, a short run each, the real events file and the real ``compute`` with the gate config's seed set: the row identities match exactly,
though the two seeds' events differ. An absent row is never read as zero, so the sets must be equal, not merely overlapping.
"""
from __future__ import annotations

import pytest

from tests.integration.observability.test_gate_validity_checks_fire_through_the_real_kernel import WORLD, run_gate_metrics

pytestmark = pytest.mark.integration

SEEDS = (42, 43)


def _identities(rows):
    return {(r["id"], r["group"], str(r.get("key", "")), r.get("tick")) for r in rows}


def test_two_seeds_of_one_world_emit_identical_row_identities_through_the_real_kernel():
    docs = [run_gate_metrics(f"gate_rows_s{seed}", 60, world=WORLD, seed=seed, seeds=SEEDS) for seed in SEEDS]
    assert _identities(docs[0]) == _identities(docs[1])
    assert any(r["id"] == "O4.accepted" and r["value"] == 0 for r in docs[0]), "declared rows with nothing happening are true zeros"
    assert not [r for doc in docs for r in doc if r["id"] == "O1.starvation_share"], "the starvation share is a pooled row, never a run row"

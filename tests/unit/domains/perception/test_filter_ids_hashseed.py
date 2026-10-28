"""Perception filter ids for non-int signal ids do not depend on PYTHONHASHSEED.

TCK-20261023-SALTED-HASH-IN-HASHED-STATE-FACTION-SQUAD-GROUP-ID. The filter is not wired
into production state today, so this is a latent hazard closed, not a live behaviour change.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]

_SCRIPT = r'''
import json
from src.core.state import EntityState
from src.domains.perception.filter import PerceptionBudget, PerceptionFilterService
from src.domains.perception.salience import WorldSignal

signals = [
    WorldSignal("hero_abc", "HERO", (1.0, 1.0), 0.9),
    WorldSignal("herb_patch_7", "healing_resource", (2.0, 2.0), 0.9),
]
update = PerceptionFilterService.filter(EntityState(id=1, kind="HERO"), signals, PerceptionBudget(max_perceived=10))
print(json.dumps({
    "entity_ids": sorted(update.perceived_entities),
    "node_ids": sorted(r.node_id for r in update.perceived_resources.values()),
}))
'''


def _run(hashseed: str) -> dict:
    env = {**os.environ, "PYTHONHASHSEED": hashseed}
    out = subprocess.run(
        [sys.executable, "-c", _SCRIPT],
        cwd=_REPO_ROOT, env=env, capture_output=True, text=True, check=True, timeout=120,
    )
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_filter_ids_equal_across_hashseeds():
    from src.core.stable_hash import stable_int31

    a, b = _run("0"), _run("1")
    assert a == b
    assert a["entity_ids"] == [stable_int31("hero_abc")]
    assert a["node_ids"] == [stable_int31("herb_patch_7")]

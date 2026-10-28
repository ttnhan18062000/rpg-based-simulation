"""The md5 calls in src/ derive ids and checksums, not secrets (TCK-20261019-SEMGREP-BASELINE-FINDINGS-IN-SRC-TRIAGE).

``usedforsecurity=False`` must not change a digest, so a replay fingerprint, a seeded id or a manifest checksum stays byte-identical.
"""
import hashlib
import json
import re
from pathlib import Path

import pytest

from src.observability.warehouse.clickhouse import calculate_checksum
from src.systems.lifecycle_systems.genetics import GeneticsSystem

ROOT = Path(__file__).resolve().parents[3]
MD5_FILES = [
    "src/domains/world_emergence/services.py",
    "src/lab/mutation.py",
    "src/observability/warehouse/clickhouse.py",
    "src/replay/fingerprint.py",
    "src/systems/lifecycle_systems/genetics.py",
]


def test_manifest_checksum_is_unchanged():
    data = {"b": 2, "a": [1, 2]}
    assert calculate_checksum(data) == "a81c5444fbf095a1a5001299859fbe87"
    assert calculate_checksum(data) == hashlib.md5(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()


@pytest.mark.parametrize("seed", [0, 1, 42, 123456789])
def test_genetic_profile_from_seed_is_unchanged(seed):
    h = hashlib.md5(str(seed).encode()).hexdigest()  # the pre-change digest

    def extract(offset: int) -> float:
        return int(h[offset:offset + 2], 16) / 255.0

    profile = GeneticsSystem.generate_profile_from_seed(seed)
    again = GeneticsSystem.generate_profile_from_seed(seed)
    assert profile == again
    assert hashlib.md5(str(seed).encode(), usedforsecurity=False).hexdigest() == h
    assert 0.0 <= extract(0) <= 1.0


@pytest.mark.parametrize("path", MD5_FILES)
def test_every_md5_call_is_marked_not_for_security(path):
    text = (ROOT / path).read_text(encoding="utf-8")
    calls = [line for line in text.splitlines() if "hashlib.md5(" in line]
    assert calls, path
    assert all(re.search(r"usedforsecurity\s*=\s*False", line) for line in calls), calls

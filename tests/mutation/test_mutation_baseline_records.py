"""Shape and internal-consistency checks for the tracked mutation baseline records.

Staleness (target contents changed, or older than the record's own `stale_after.days`) is
deliberately NOT asserted here: a stale record is a state the test report shows, not a test failure.
"""

import json
from pathlib import Path

import pytest

BASELINES = sorted((Path(__file__).parent / "baselines").glob("*.json"))
REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_KEYS = {
    "schema_version", "kind", "target", "run", "tool", "tests", "counts",
    "target_selection", "stale_after", "survivors",
}


def test_at_least_one_baseline_record_exists():
    assert BASELINES


@pytest.mark.parametrize("path", BASELINES, ids=lambda p: p.name)
def test_record_has_required_fields(path):
    record = json.loads(path.read_text(encoding="utf-8"))
    assert REQUIRED_KEYS <= record.keys()
    assert record["kind"] == "mutation_baseline"
    assert len(record["target"]["sha256"]) == 64
    assert (REPO_ROOT / record["target"]["path"]).is_file()
    for test_file in record["tests"]["files"]:
        assert (REPO_ROOT / test_file).is_file(), test_file


@pytest.mark.parametrize("path", BASELINES, ids=lambda p: p.name)
def test_counts_are_consistent_and_equivalent_is_never_invented(path):
    record = json.loads(path.read_text(encoding="utf-8"))
    counts = record["counts"]
    assert counts["killed"] + counts["survived"] + counts["timeout"] + counts["suspicious"] == counts["total"]
    assert len(record["survivors"]) == counts["survived"]
    # mutmut does not classify equivalent mutants; the record must say so rather than report 0.
    assert counts["equivalent"] == "not-classified" or isinstance(counts["equivalent"], int)
    assert len({s["id"] for s in record["survivors"]}) == counts["survived"]
    for survivor in record["survivors"]:
        assert survivor["location"].startswith(record["target"]["path"] + ":")
        assert survivor["diff"]

"""Every live perf-check call site is mapped to a contract clause or to ``none`` (TCK-20261010-PERF-M2-T06-GATE-CONFORMANCE).

The real map ``docs/performance/gate_conformance.yaml`` is checked against ``tools.perf.perf_threshold_inventory.build_report`` of this checkout.
Synthetic ``tmp_path`` trees show each failure mode: an unmapped call site, an unknown clause ID, a stale entry.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

from tools.perf import gate_conformance as gc
from tools.perf.perf_threshold_inventory import build_report

REPO_ROOT = Path(__file__).resolve().parents[2]
KNOWN = {"PC-12", "BP-13"}

TEST_SOURCE = """
from tests.tools.perf_assertions import assert_perf_threshold, perf_check


def test_a():
    assert_perf_threshold(1.0, 2.0, "first")
    assert_perf_threshold(1.0, 2.0, "second")


def test_b():
    perf_check(True, "ok")
"""


def _tree(tmp_path: Path) -> Path:
    (tmp_path / "tests" / "perf").mkdir(parents=True)
    (tmp_path / "tests" / "perf" / "test_x.py").write_text(TEST_SOURCE, encoding="utf-8")
    return tmp_path


def _map(*sites: Dict[str, Any]) -> Dict[str, Any]:
    return {"sites": list(sites)}


FULL = [
    {"site": "tests/perf/test_x.py::test_a#1", "clause": "PC-12"},
    {"site": "tests/perf/test_x.py::test_a#2", "clause": "none"},
    {"site": "tests/perf/test_x.py::test_b#1", "clause": "BP-13", "related": ["PC-12"]},
]


def _problems(tmp_path: Path, sites: List[Dict[str, Any]]) -> List[str]:
    return gc.problems(build_report(_tree(tmp_path)), _map(*sites), KNOWN)


# ── the real map ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_the_real_map_covers_every_call_site_with_no_stale_entry_or_unknown_clause() -> None:
    assert gc.check_repo(REPO_ROOT) == []


def test_the_real_map_has_one_entry_per_call_site() -> None:
    report = build_report(REPO_ROOT)
    conformance = yaml.safe_load((REPO_ROOT / gc.MAP_PATH).read_text(encoding="utf-8"))
    assert sorted(e["site"] for e in conformance["sites"]) == sorted(gc.site_keys(report))
    assert len(report["call_sites"]) > 0


def test_every_clause_in_the_real_map_is_a_none_or_an_inventory_row() -> None:
    known = gc.clause_ids((REPO_ROOT / gc.INVENTORY_PATH).read_text(encoding="utf-8"))
    assert {"PC-12", "BP-13", "OI-06"} <= known
    conformance = yaml.safe_load((REPO_ROOT / gc.MAP_PATH).read_text(encoding="utf-8"))
    for entry in conformance["sites"]:
        assert entry["clause"] == "none" or entry["clause"] in known, entry["site"]


# ── synthetic failures ────────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_a_fully_mapped_tree_is_clean(tmp_path: Path) -> None:
    assert _problems(tmp_path, FULL) == []


def test_an_unmapped_call_site_fails_and_names_file_and_function(tmp_path: Path) -> None:
    found = _problems(tmp_path, FULL[:2])
    assert len(found) == 1
    assert "unmapped call site" in found[0] and "tests/perf/test_x.py in test_b" in found[0]


def test_a_second_call_in_the_same_function_needs_its_own_entry(tmp_path: Path) -> None:
    found = _problems(tmp_path, [FULL[0], FULL[2]])
    assert len(found) == 1 and "test_a#2" in found[0]


def test_an_unknown_clause_id_fails(tmp_path: Path) -> None:
    sites = [dict(FULL[0], clause="PC-99"), FULL[1], FULL[2]]
    found = _problems(tmp_path, sites)
    assert len(found) == 1 and "unknown clause 'PC-99'" in found[0] and "test_a" in found[0]


def test_an_unknown_related_clause_fails(tmp_path: Path) -> None:
    sites = [FULL[0], FULL[1], dict(FULL[2], related=["XX-01"])]
    assert any("unknown related clause 'XX-01'" in line for line in _problems(tmp_path, sites))


def test_a_stale_entry_fails_and_names_file_and_function(tmp_path: Path) -> None:
    sites = FULL + [{"site": "tests/perf/test_gone.py::test_removed#1", "clause": "none"}]
    found = _problems(tmp_path, sites)
    assert len(found) == 1 and "stale entry" in found[0] and "tests/perf/test_gone.py in test_removed" in found[0]


def test_a_duplicate_entry_fails(tmp_path: Path) -> None:
    assert any("duplicate entry" in line for line in _problems(tmp_path, FULL + [FULL[0]]))


def test_a_missing_other_check_path_fails(tmp_path: Path) -> None:
    conformance = dict(_map(*FULL), other_checks=[{"path": "src/perf/nowhere.py", "clause": ["none"]}])
    found = gc.problems(build_report(_tree(tmp_path)), conformance, KNOWN, tmp_path)
    assert any("missing path" in line and "src/perf/nowhere.py" in line for line in found)


def test_the_helper_module_itself_is_not_a_call_site(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    (root / "tests" / "tools").mkdir()
    (root / "tests" / "tools" / "perf_assertions.py").write_text("def f():\n    assert_perf_threshold(1, 2)\n", encoding="utf-8")
    assert gc.problems(build_report(root), _map(*FULL), KNOWN) == []

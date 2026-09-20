"""Tests for tools/mechanism_registry/registry.py::build_system_rollup and
tools/mechanism_registry/generate_mechanism_system_rollup_view.py.

TCK-20260919-MECHANISM-SYSTEM-ROLLUP-VIEW (child 3 of
TCK-20260918-EPIC-MECHANISM-SYSTEM-MEMBERSHIP). Two constraints are load-bearing here and are what
these tests actually guard: COUNTS never a single summary badge (AC #1), and every system's rate
shown against a live-computed whole-registry baseline, never in isolation (AC #2).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tools.mechanism_registry import build_system_rollup, VALID_STATES
from tools.mechanism_registry.generate_mechanism_system_rollup_view import render

REPO_ROOT = Path(__file__).resolve().parents[3]
_REGISTRY_PATH = REPO_ROOT / "registries" / "mechanisms.yaml"
_OUTPUT_PATH = REPO_ROOT / "docs" / "brainstorm" / "mechanism_system_rollup_view.md"


@pytest.fixture(scope="module")
def registry_data():
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _fixture_registry(monkeypatch, systems, mechanisms):
    """Same closed-universe fixture pattern as
    tests/unit/tools/test_mechanism_registry.py::_fixture_registry -- a complete,
    self-contained "registered systems + mechanism list" pair, not a subset of the real one."""
    import tools.mechanism_registry.registry as registry_module

    registry = {s: {"system": s, "added_date": "2026-09-19", "note": ""} for s in systems}
    monkeypatch.setattr(registry_module, "_load_system_registry", lambda *a, **kw: registry)
    return {"mechanisms": mechanisms}


# ---------------------------------------------------------------------------
# build_system_rollup -- counts, never a badge
# ---------------------------------------------------------------------------


def test_rollup_reports_counts_not_a_single_status(monkeypatch):
    data = _fixture_registry(
        monkeypatch,
        systems=["combat"],
        mechanisms=[
            {"id": "a", "systems": ["combat"], "state": "done", "implemented_by": ["x.py::A"]},
            {"id": "b", "systems": ["combat"], "state": "partial"},
        ],
    )
    rollup = build_system_rollup(data)
    combat = next(s for s in rollup["systems"] if s["system"] == "combat")

    # The load-bearing shape check: no single "status"/"badge"/"verdict" key anywhere in a row --
    # only counts and rates. A future change adding one would break this assertion, by design.
    forbidden_keys = {"status", "badge", "verdict", "summary_status"}
    assert not (forbidden_keys & set(combat.keys()))
    assert combat["count"] == 2
    assert combat["bound"] == 1
    assert combat["state_counts"]["done"] == 1
    assert combat["state_counts"]["partial"] == 1


def test_rollup_state_breakdown_covers_all_six_states_explicitly(monkeypatch):
    data = _fixture_registry(
        monkeypatch,
        systems=["combat"],
        mechanisms=[{"id": "a", "systems": ["combat"], "state": "done"}],
    )
    rollup = build_system_rollup(data)
    combat = next(s for s in rollup["systems"] if s["system"] == "combat")
    # Every state renders explicitly, including the five with zero real members here -- not
    # omitted, same "explicit absence" discipline as the verification view's own unverified rows.
    assert set(combat["state_counts"].keys()) == set(VALID_STATES)
    assert combat["state_counts"]["orphan"] == 0


# ---------------------------------------------------------------------------
# build_system_rollup -- baseline, never isolated
# ---------------------------------------------------------------------------


def test_rollup_baseline_computed_live_not_hardcoded(monkeypatch):
    """The exact failure the value investigation found: a system's raw rate can look informative
    until compared to a live baseline. Proves the baseline reflects THIS fixture's own data, not a
    fixed snapshot value that would silently drift from whatever registry is passed in."""
    data = _fixture_registry(
        monkeypatch,
        systems=["combat", "economy"],
        mechanisms=[
            {"id": "a", "systems": ["combat"], "state": "done", "implemented_by": ["x.py::A"]},
            {"id": "b", "systems": ["combat"], "state": "done", "implemented_by": ["x.py::B"]},
            {"id": "c", "systems": ["economy"], "state": "gap"},
            {"id": "d", "systems": ["economy"], "state": "gap"},
        ],
    )
    rollup = build_system_rollup(data)
    baseline = rollup["baseline"]
    assert baseline["count"] == 4
    assert baseline["bound"] == 2
    assert baseline["bound_rate"] == pytest.approx(0.5)

    combat = next(s for s in rollup["systems"] if s["system"] == "combat")
    economy = next(s for s in rollup["systems"] if s["system"] == "economy")
    # combat (100% bound) sits above baseline (50%); economy (0% bound) sits below it -- the
    # comparison a rollup consumer needs, not just each system's own number in isolation.
    assert combat["bound_rate"] > baseline["bound_rate"]
    assert economy["bound_rate"] < baseline["bound_rate"]


def test_rollup_distinguishes_bound_unverified_from_unbound_unverified(monkeypatch):
    """Peer-review finding: 'unverified' collapses two different-cost problems -- bound-but-
    unverified (the code is already located, cheapest to verify) vs unbound-and-unverified (we
    don't even know where to look). This is the view's own most actionable number, so it must be
    a real, separately-computed count, not something a reader has to infer."""
    data = _fixture_registry(
        monkeypatch,
        systems=["combat"],
        mechanisms=[
            {"id": "a", "systems": ["combat"], "state": "done", "implemented_by": ["x.py::A"]},
            {"id": "b", "systems": ["combat"], "state": "done"},
            {
                "id": "c", "systems": ["combat"], "state": "done", "implemented_by": ["x.py::C"],
                "verified": {"instrument": "code_trace", "verdict": "observed", "date": "2026-09-19"},
            },
        ],
    )
    rollup = build_system_rollup(data)
    combat = next(s for s in rollup["systems"] if s["system"] == "combat")
    # a: bound, unverified -> counts. b: unbound, unverified -> does not count. c: bound AND
    # verified -> does not count (already verified, not a target).
    assert combat["bound_unverified"] == 1
    assert combat["unverified"] == 2  # a and b


def test_rollup_runtime_verified_share_is_a_rate_of_verified_not_of_count(monkeypatch):
    """TCK-20260920-MECHANISM-VERIFICATION-INSTRUMENT-TRANSPARENCY. Peer-caught gap: a batch of
    code_trace-only re-verifications can raise `verified` while the registry's own runtime share
    silently drops, and nothing rendered that rate until this test's own metric existed. The
    denominator must be `verified` (mechanisms actually confirmed by some instrument), never
    `count` (all group members) -- conflating the two would understate the share whenever unbound/
    unverified mechanisms are present."""
    data = _fixture_registry(
        monkeypatch,
        systems=["combat"],
        mechanisms=[
            {
                "id": "a", "systems": ["combat"], "state": "done", "implemented_by": ["x.py::A"],
                "verified": {"instrument": "scenario", "verdict": "observed", "date": "2026-09-19"},
            },
            {
                "id": "b", "systems": ["combat"], "state": "done", "implemented_by": ["x.py::B"],
                "verified": {"instrument": "code_trace", "verdict": "observed", "date": "2026-09-19"},
            },
            {
                "id": "c", "systems": ["combat"], "state": "done", "implemented_by": ["x.py::C"],
                "verified": {"instrument": "code_trace", "verdict": "observed", "date": "2026-09-19"},
            },
            # d is unverified -- must not appear in the denominator.
            {"id": "d", "systems": ["combat"], "state": "done"},
        ],
    )
    rollup = build_system_rollup(data)
    combat = next(s for s in rollup["systems"] if s["system"] == "combat")
    assert combat["verified"] == 3
    assert combat["runtime_verified"] == 1
    assert combat["runtime_verified_share"] == pytest.approx(1 / 3)


def test_rollup_runtime_verified_share_is_zero_not_undefined_when_nothing_verified(monkeypatch):
    data = _fixture_registry(
        monkeypatch,
        systems=["combat"],
        mechanisms=[{"id": "a", "systems": ["combat"], "state": "gap"}],
    )
    rollup = build_system_rollup(data)
    combat = next(s for s in rollup["systems"] if s["system"] == "combat")
    assert combat["verified"] == 0
    assert combat["runtime_verified_share"] == 0.0


def test_rollup_unassigned_renders_with_real_count(monkeypatch):
    data = _fixture_registry(
        monkeypatch,
        systems=["combat"],
        mechanisms=[
            {"id": "a", "systems": ["combat"], "state": "done"},
            {"id": "b", "systems": [], "state": "done"},
        ],
    )
    rollup = build_system_rollup(data)
    assert rollup["unassigned"]["system"] == "unassigned"
    assert rollup["unassigned"]["count"] == 1


def test_rollup_computes_nothing_that_reads_as_a_ranking(monkeypatch):
    """AC #5: nothing here derives a priority/verdict from membership. systems is sorted
    alphabetically by mechanisms_by_system()'s own key order, not by any computed rate --
    ranking by a computed value would itself be a soft verdict."""
    data = _fixture_registry(
        monkeypatch,
        systems=["zeta", "alpha"],
        mechanisms=[
            {"id": "a", "systems": ["zeta"], "state": "done", "implemented_by": ["x.py::A"]},
            {"id": "b", "systems": ["alpha"], "state": "gap"},
        ],
    )
    rollup = build_system_rollup(data)
    names = [s["system"] for s in rollup["systems"]]
    assert names == sorted(names)


# ---------------------------------------------------------------------------
# render() / generator CLI
# ---------------------------------------------------------------------------


def test_render_includes_baseline_and_per_system_rates(registry_data):
    content = render(registry_data)
    assert "Baseline (all" in content
    assert "vs baseline" in content


def test_render_includes_bound_unverified_column(registry_data):
    content = render(registry_data)
    assert "Bound, Unverified" in content


def test_render_includes_unassigned_row(registry_data):
    content = render(registry_data)
    assert "`unassigned`" in content


def test_make_target_generates_rollup_view():
    result = subprocess.run(
        ["make", "mechanism-system-rollup-view"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert _OUTPUT_PATH.exists()


def test_generator_check_mode_detects_staleness(tmp_path):
    stale_output = tmp_path / "mechanism_system_rollup_view.md"
    stale_output.write_text("stale content that will never match", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "tools/mechanism_registry/generate_mechanism_system_rollup_view.py",
         "--check", "--output", str(stale_output)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1
    assert "STALE" in result.stdout


def test_real_rollup_view_is_up_to_date():
    """The load-bearing regression check: the committed file must match a fresh render, not just
    have been correct at generation time."""
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    expected = render(data)
    actual = _OUTPUT_PATH.read_text(encoding="utf-8")
    assert actual == expected, (
        "docs/brainstorm/mechanism_system_rollup_view.md is stale -- "
        "run `make mechanism-system-rollup-view`"
    )

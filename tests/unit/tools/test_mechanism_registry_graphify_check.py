"""Tests for tools/mechanism_registry/mechanism_registry_graphify_check.py — the report-only graphify cross-check
for docs/brainstorm/mechanisms.yaml's `depends_on` edges.

TCK-20260915-MECHANISM-REGISTRY-FOUNDATION Scope item 5. The load-bearing contract under test is
"never fails the build" — asserted with a fixture proven to actually trigger each of the three
report buckets (supported/suspicious/no_match), not a fixture that happens to pass silently,
mirroring Acceptance Criteria #4's own warning one level down: a never-fail claim tested only
against a fixture that never exercises the failure-shaped branch proves nothing.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import tools.mechanism_registry.mechanism_registry_graphify_check as graphify_check_module
from tools.mechanism_registry.mechanism_registry_graphify_check import _REAL_RELATIONS, check, main

REPO_ROOT = Path(__file__).resolve().parents[3]


def _fake_graph():
    # A small, hand-built graph: A and B are really connected via a real relation (supported);
    # C and D exist as nodes but share no path within the bound (suspicious); E has no node at
    # all in the graph (no_match).
    return {
        "nodes": [
            {"id": "n_alpha_service", "label": "AlphaService"},
            {"id": "n_beta_service", "label": "BetaService"},
            {"id": "n_gamma_service", "label": "GammaService"},
            {"id": "n_delta_service", "label": "DeltaService"},
        ],
        "links": [
            {"relation": "calls", "source": "n_alpha_service", "target": "n_beta_service"},
            # gamma and delta exist but are never linked at all.
        ],
    }


def _fake_registry():
    return {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "alpha", "layer": "entity", "depends_on": ["beta"], "state": "done"},
            {"id": "gamma", "layer": "entity", "depends_on": ["delta"], "state": "done"},
            {"id": "epsilon", "layer": "entity", "depends_on": ["zeta_nonexistent"], "state": "done"},
        ],
    }


def test_finds_a_supported_edge():
    result = check(registry=_fake_registry(), graph=_fake_graph())
    assert ("alpha", "beta") in result["supported"]


def test_flags_a_suspicious_edge():
    result = check(registry=_fake_registry(), graph=_fake_graph())
    assert ("gamma", "delta") in result["suspicious"]


def test_reports_no_match_when_a_mechanism_has_no_graph_node():
    result = check(registry=_fake_registry(), graph=_fake_graph())
    assert ("epsilon", "zeta_nonexistent") in result["no_match"]


def test_only_real_relations_count_as_supporting_a_path():
    # A "contains" edge must NOT count as supporting evidence -- investigation.md's own confirmed
    # false-positive source. alpha/beta are connected only via "contains" here, so must NOT
    # report supported.
    graph = {
        "nodes": [
            {"id": "n_alpha_service", "label": "AlphaService"},
            {"id": "n_beta_service", "label": "BetaService"},
        ],
        "links": [
            {"relation": "contains", "source": "n_alpha_service", "target": "n_beta_service"},
        ],
    }
    result = check(registry=_fake_registry(), graph=graph)
    assert ("alpha", "beta") not in result["supported"]
    assert "contains" not in _REAL_RELATIONS


def test_missing_graph_reports_and_never_fails(monkeypatch, tmp_path, capsys):
    # graphify-out/ is gitignored (not committed) -- present locally wherever `graphify update`
    # has run, absent on a fresh CI checkout. This is the exact condition
    # TCK-20260915-MECHANISM-REGISTRY-FOUNDATION's own Scope item 5 contract ("Report, never fail")
    # must survive without crashing. Never mutate the real graphify-out/ directory to test this --
    # monkeypatch the module's own path constant to a path that genuinely does not exist instead.
    monkeypatch.setattr(graphify_check_module, "_GRAPH_PATH", tmp_path / "does_not_exist.json")
    result = check(registry=_fake_registry())
    assert result["graph_unavailable"] is True
    assert result["supported"] == [] and result["suspicious"] == [] and result["no_match"] == []
    assert main() == 0
    captured = capsys.readouterr()
    assert "SKIPPED" in captured.out
    assert "does_not_exist.json" in captured.out


def test_never_fails_the_build_even_with_suspicious_and_no_match_findings():
    # The fixture above deliberately produces one of each bucket, including suspicious and
    # no_match -- proving the never-fail contract against a fixture that actually exercises the
    # branches it claims not to fail on, not one that happens to pass silently.
    result = check(registry=_fake_registry(), graph=_fake_graph())
    assert result["suspicious"], "fixture must actually trigger a suspicious finding for this test to mean anything"
    assert result["no_match"], "fixture must actually trigger a no_match finding for this test to mean anything"
    assert main() == 0  # runs against the real committed files; must still exit 0


def test_subprocess_invocation_always_exits_zero():
    result = subprocess.run(
        [sys.executable, "tools/mechanism_registry/mechanism_registry_graphify_check.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"graphify cross-check must never fail the build:\nstdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )

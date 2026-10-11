"""The gold sink is retired (EXCH-02, owner decisions 51 and 58, ruling 61; intentional divergence 2.111).

This file stays at its old path because the recorded conservation mutation baselines cite it. It now states what replaced the sink: no phase, no
fee intent, no periodic levy, and a flagged inflation spiral takes no coin from anyone.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

PIPELINE = Path(__file__).resolve().parents[3] / "src" / "engine" / "pipeline.py"


def test_the_gold_sink_module_is_gone():
    assert importlib.util.find_spec("src.engine.gold_sink") is None


def test_the_pipeline_runs_no_gold_sink_phase():
    assert "gold_sink" not in PIPELINE.read_text()


def test_no_fee_intent_kind_is_proposed_by_any_system():
    src = Path(__file__).resolve().parents[3] / "src"
    offenders = [str(p) for p in src.rglob("*.py") if 'transfer_kind="FEE"' in p.read_text()]
    assert offenders == []

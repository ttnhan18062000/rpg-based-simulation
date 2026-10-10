"""The nightly tripwire lane: the head against a promoted baseline record (TCK-20261010-PERF-M2-T03-TRIPWIRE-PAIRED).

The pull-request lane is ``tools/perf/tripwire.py`` (base and head paired, each in a fresh process). This lane compares the head with a baseline *record*
promoted by ``tools/perf/baseline_lifecycle.py``. A missing baseline, or one of the 15 legacy references that carry no identity, is ``INCONCLUSIVE`` with a
named reason: it is reported, never skipped and never a pass. Nothing here is blocking: a non-PASS outcome is a ``PerformanceThresholdWarning``.
"""
from __future__ import annotations

import dataclasses
import warnings
from pathlib import Path

import pytest

from src.perf.benchmark_record import OutcomeState
from tests.tools.perf_assertions import PerformanceThresholdWarning
from tools.perf import tripwire
from tools.perf.capacity_run import run_once


@pytest.mark.perf
@pytest.mark.slow
@pytest.mark.parametrize("name, spec", tripwire.TRIPWIRE_SCENARIOS, ids=[n for n, _ in tripwire.TRIPWIRE_SCENARIOS])
def test_regression_vs_baseline(name, spec, tmp_path):
    """Head against the latest promoted baseline of ``name``; INCONCLUSIVE with a reason when there is none."""
    baseline, reason = tripwire.load_baseline(name)
    if baseline is None:
        outcome = tripwire.compare_with_baseline(None, reason, None)
    else:
        head = run_once(dataclasses.replace(spec, samples_dir=str(tmp_path)))
        outcome = tripwire.compare_with_baseline(baseline, reason, head)

    print(f"\n{name}: {outcome.state.value}: {outcome.reason}")
    if outcome.state is not OutcomeState.PASS:
        warnings.warn(f"{name}: {outcome.state.value}: {outcome.reason}", PerformanceThresholdWarning, stacklevel=1)


def test_performance_contract_lists_runtimemode_scoped_claim():
    contract_text = Path("docs/engine/performance_contract.md").read_text()
    scoped_claims_section = contract_text.split("### 3.1 Scoped Claims")[1].split("### 3.2")[0]
    assert "RuntimeMode" in scoped_claims_section

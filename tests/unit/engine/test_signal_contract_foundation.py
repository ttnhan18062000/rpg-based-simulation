"""The signal-contract pieces added in Phase A step 2 (PERF-D1; TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY)."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.config.profiles import HardwareClass, RuntimeProfile, SignalContract
from src.core.governance import PressureSignals
from src.engine import work_units
from src.engine.runtime_status import RuntimeStatus
from src.engine.signal_source import CanonicalSignalSource, LiveSignalSource, ZeroedSignalSource, select_signal_source
from src.perf.scenarios import build_strategic_state


def _profile(**overrides) -> RuntimeProfile:
    fields = dict(name="p", hardware_class=HardwareClass.CLASS_B, max_ram_mb=1024, max_cpu_percent=90.0, max_worker_count=0,
                  max_queue_depth=10, max_replay_buffer_kb=64, max_observability_budget_percent=5.0, max_tick_budget_ms=100.0)
    fields.update(overrides)
    return RuntimeProfile(**fields)


# --- work model ---------------------------------------------------------------------------------------------------

def test_work_model_v1_weights_are_frozen():
    """A weight change is a new version, never an edit in place: these are the values perf-planner approved on 2026-10-08."""
    assert (work_units.WORK_MODEL_VERSION, work_units.WORK_MODEL_STATUS) == ("WORK_MODEL_V1", "PROVISIONAL")
    assert (work_units.ENTITY_MS, work_units.LEAD_MS) == (0.68, 7.42)


def test_tick_cost_is_the_weighted_sum_of_the_counts():
    demand = work_units.WorkDemand(entities_active=100, leads=10)
    assert work_units.tick_cost_ref_ms(demand) == pytest.approx(0.68 * 100 + 7.42 * 10)
    assert work_units.tick_cost_ref_ms(work_units.WorkDemand()) == 0.0


def test_count_demand_counts_active_entities_and_their_leads():
    state = build_strategic_state(entity_count=20)
    demand = work_units.count_demand(state)
    assert demand.entities_active == 20
    assert demand.leads == sum(len(e.strategic.leads) for e in state.entities.values())


def test_count_demand_ignores_inactive_entities():
    state = build_strategic_state(entity_count=6)
    first = next(iter(state.entities.values()))
    object.__setattr__(first.lifecycle, "active", False)
    assert work_units.count_demand(state).entities_active == 5


def test_work_units_module_imports_no_clock_or_host_module():
    forbidden = {"time", "psutil", "os", "threading", "datetime", "random"}
    tree = ast.parse(Path(work_units.__file__).read_text())
    imported = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    imported |= {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    assert not imported & forbidden


# --- PressureSignals fallbacks ------------------------------------------------------------------------------------

def test_signals_without_the_new_fields_use_the_measured_values():
    signals = PressureSignals(tick_compute_ms=42.0, phase_costs_ms={"locomotion": 3.0})
    assert signals.effective_tick_cost == 42.0
    assert signals.effective_tick_budget(100.0) == 100.0
    assert signals.effective_phase_cost == {"locomotion": 3.0}


def test_signals_with_the_new_fields_use_them():
    signals = PressureSignals(tick_compute_ms=42.0, phase_costs_ms={"locomotion": 3.0},
                              tick_cost=7.0, tick_budget=50.0, phase_cost={"locomotion": 1.0})
    assert signals.effective_tick_cost == 7.0
    assert signals.effective_tick_budget(100.0) == 50.0
    assert signals.effective_phase_cost == {"locomotion": 1.0}


def test_a_zero_cost_is_set_not_missing():
    assert PressureSignals(tick_compute_ms=42.0, tick_cost=0.0).effective_tick_cost == 0.0


def test_record_signals_keeps_the_new_fields():
    status = RuntimeStatus()
    status.record_signals(PressureSignals(tick_compute_ms=9.0, tick_cost=3.0, tick_budget=50.0, phase_cost={"x": 1.0}))
    recorded = status.signal_history[-1]
    assert (recorded.tick_cost, recorded.tick_budget, recorded.phase_cost) == (3.0, 50.0, {"x": 1.0})


# --- profile field and source choice ------------------------------------------------------------------------------

def test_signal_contract_defaults_to_live():
    assert _profile().signal_contract is SignalContract.LIVE


def test_signal_contract_accepts_canonical_and_rejects_anything_else():
    assert _profile(signal_contract="canonical").signal_contract is SignalContract.CANONICAL
    with pytest.raises(ValidationError):
        _profile(signal_contract="sometimes")


def test_live_profile_selects_the_live_source():
    assert type(select_signal_source(_profile(), audit_mode=False)) is LiveSignalSource


def test_audit_mode_wins_over_the_contract():
    assert type(select_signal_source(_profile(), audit_mode=True)) is ZeroedSignalSource
    assert type(select_signal_source(_profile(signal_contract="canonical"), audit_mode=True)) is ZeroedSignalSource


def test_canonical_profile_selects_the_canonical_source():
    assert type(select_signal_source(_profile(signal_contract="canonical"), audit_mode=False)) is CanonicalSignalSource

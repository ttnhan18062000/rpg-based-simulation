"""Gate self-test for V8, "every entity added mid-run has a declared source" (TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK, AC4).

A gate must be shown to fire. These cases drive rpg's real pieces end to end and never feed V8 a hand-built tally: a staged ``StateUpdate`` with
``entities_add`` (and ``entity_spawn_sources``) goes through the real ``ApplyPath.apply_generation``, the real ``RunLedger`` and ``StarvationRecorder``
observe each tick, their real closing events are written to the events file, and the real ``rpg_gate_metrics.compute`` reads it.

Never skip or xfail a case here: a V8 that cannot be shown to fire is a gate that reads as a pass.
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pytest

from src.core.builder import V2EntityBuilder
from src.core.spawn_source import SpawnKind, SpawnSource
from src.core.updates import StateUpdate
from src.engine.apply import ApplyPath, DuplicateEntityIdError
from src.engine.cadence import SystemCadence, should_run
from src.engine.need_pull import ESCALATION_ONSET, HUNGER_LINE
from src.observability import rpg_gate_metrics as metrics
from src.observability.run_ledger import RunLedger
from src.observability.starvation_record import StarvationRecorder
from tests.unit.observability.test_starvation_death_record import WHO, _world

Tick = Tuple[Sequence[Any], Dict[int, SpawnSource]]  # (entities_add, entity_spawn_sources) for one tick


@pytest.fixture(autouse=True)
def _no_world_compile(monkeypatch):
    """The self-test world has no spec: the O2.population floor's tick-0 counts (a world compile) are not under test here."""
    monkeypatch.setattr(metrics, "_gate_seeds", lambda: (1,))
    monkeypatch.setattr(metrics, "_tick0_alive", lambda world, seed: {})


@pytest.fixture(autouse=True)
def _clean():
    def reset() -> None:
        RunLedger.reset_run_state()
        StarvationRecorder.reset_run_state()
        StarvationRecorder.configure(SystemCadence.model_fields["strategic_intelligence"].default, ESCALATION_ONSET * HUNGER_LINE, should_run)
    reset()
    RunLedger.configure(True)
    yield
    reset()


def _new(entity_id: int):
    return V2EntityBuilder(entity_id).build()


def _drive(tmp_path: Path, ticks: Sequence[Tick], ledger_live: bool = True) -> Tuple[Any, Any]:
    """Apply each tick's adds through the real apply path, observe with the real recorders, close the run, and return (run, final state)."""
    RunLedger.configure(ledger_live)
    prior = _world()
    first = prior
    events: List[Any] = []
    for adds, sources in ticks:
        update = StateUpdate(entities_add=list(adds), entity_spawn_sources=dict(sources))
        current = ApplyPath.apply_generation(prior, update, next_tick=prior.tick + 1, passive=False)
        events += RunLedger.observe(prior, current, update) + StarvationRecorder.observe(prior, current, update)
        prior = current
    if ledger_live:
        events.append(RunLedger.tally_event())
    events.append(StarvationRecorder.tally_event())
    path = tmp_path / "simulation_events.jsonl"
    path.write_text("\n".join(json.dumps({"event_type": e.event_type, "payload": e.payload}, default=str) for e in events) + "\n", encoding="utf-8")
    run = SimpleNamespace(world="v8_self_test", seed=1, ticks=len(ticks), state=prior, events_path=path, run_dir=tmp_path, first=first)
    return run, prior


def _v8(run: Any) -> Dict[str, Any]:
    (row,) = [r for r in metrics.compute(run)["metrics"] if r["id"] == "V8" and r["group"] == "*"]
    return row


def _birth(parents: Tuple[int, ...] = (WHO, WHO + 1)) -> SpawnSource:
    return SpawnSource(SpawnKind.BIRTH, parent_ids=parents)


def _arrival() -> SpawnSource:
    return SpawnSource(SpawnKind.AUTHORED_ARRIVAL, rule_kind="calamity", rule_id="calamity.test_rule")


def test_a_an_add_with_no_spawn_source_is_a_violation_that_names_the_entity(tmp_path):
    run, _ = _drive(tmp_path, [([_new(500)], {})])
    row = _v8(run)
    assert row["violations"] >= 1
    assert row["examples"], "the row must carry examples"
    assert any("unsourced" in str(example) for example in row["examples"])


def test_b_an_authored_arrival_cannot_be_built_without_its_rule_so_the_only_unruled_add_is_an_unsourced_one(tmp_path):
    for bad in (dict(rule_kind="calamity"), dict(rule_id="calamity.x"), dict()):
        with pytest.raises(ValueError):
            SpawnSource(SpawnKind.AUTHORED_ARRIVAL, **bad)
    run, _ = _drive(tmp_path, [([_new(500)], {500: _arrival()})])
    assert _v8(run)["violations"] == 0


def test_c_a_birth_cannot_be_built_without_parents_so_the_only_parentless_add_is_an_unsourced_one(tmp_path):
    with pytest.raises(ValueError):
        SpawnSource(SpawnKind.BIRTH, parent_ids=())
    with pytest.raises(ValueError):  # and parents belong to a BIRTH alone
        SpawnSource(SpawnKind.INITIAL, parent_ids=(1,))
    run, _ = _drive(tmp_path, [([_new(500)], {500: _birth()})])
    assert _v8(run)["violations"] == 0


def test_d_fully_sourced_adds_of_every_kind_leave_zero_violations(tmp_path):
    ticks: List[Tick] = [
        ([_new(500)], {500: SpawnSource(SpawnKind.INITIAL)}),
        ([_new(501)], {501: _birth()}),
        ([_new(502)], {502: _arrival()}),
    ]
    run, _ = _drive(tmp_path, ticks)
    assert _v8(run)["violations"] == 0
    assert RunLedger.tally_event().payload["adds"], "the run must have counted its adds, or zero would mean nothing"


def test_e_a_silent_ledger_is_no_data_never_zero_violations(tmp_path):
    run, _ = _drive(tmp_path, [([_new(500)], {})], ledger_live=False)
    with pytest.raises(metrics.GateDataMissingError):
        metrics.compute(run)


def test_f_the_tally_counts_sum_to_the_number_of_adds_applied(tmp_path):
    ticks: List[Tick] = [
        ([_new(500), _new(501)], {500: _birth(), 501: _arrival()}),
        ([], {}),
        ([_new(502)], {}),
        ([_new(503), _new(504)], {503: SpawnSource(SpawnKind.INITIAL)}),
    ]
    applied = sum(len(adds) for adds, _ in ticks)
    run, final = _drive(tmp_path, ticks)
    assert sum(RunLedger.tally_event().payload["adds"].values()) == applied == len(final.entities) - len(run.first.entities)
    assert _v8(run)["violations"] == 2  # 502, and 504 (503 alone was sourced)


def test_g_an_add_reusing_an_existing_id_is_refused_loudly_and_nothing_records_an_overwrite():
    prior = _world()
    original = prior.entities[WHO]
    update = StateUpdate(entities_add=[_new(WHO)], entity_spawn_sources={WHO: _birth()})
    with pytest.raises(DuplicateEntityIdError):
        ApplyPath.apply_generation(prior, update, next_tick=prior.tick + 1, passive=False)
    assert prior.entities[WHO] is original and set(prior.entities) == {WHO}, "the refused add must not touch the state"
    assert RunLedger.tally_event().payload["adds"] == {}, "an add that never applied must not be counted"
    twice = StateUpdate(entities_add=[_new(500), _new(500)])  # the same id twice inside one update is refused too
    with pytest.raises(DuplicateEntityIdError):
        ApplyPath.apply_generation(prior, twice, next_tick=prior.tick + 1, passive=False)
    assert issubclass(DuplicateEntityIdError, ValueError)

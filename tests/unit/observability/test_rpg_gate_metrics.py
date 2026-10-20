"""M0 gate metric module: each validity row fails on a constructed counterexample and passes a clean run, silence is no-data, the output is
deterministic, and the module reads no live engine state. Staged on synthetic event files and ledger tallies (the module is a pure reader)."""
from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from src.observability import rpg_gate_metrics as m
from src.observability.run_ledger import LEDGER_LIVE_EVENT, LEDGER_TALLY_EVENT
from src.observability.starvation_record import (
    CHANNEL_LIVE_EVENT,
    CHANNEL_TALLY_EVENT,
    RECORD_EVENT,
)

PEOPLE, WOLF, DEER = "meat+plant+prepared", "meat", "graze+plant"


def _ledger(**over: Any) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "first_tick": 1, "last_tick": 100, "coin_first": 100.0, "coin_last": 100.0, "declared_coin": 0.0,
        "population": {"1": {PEOPLE: 10, WOLF: 4, DEER: 6}}, "transfers": {}, "hunger_drops": {}, "deaths": {}, "adds": {},
        "world_events": {}, "meat": {}, "attacks": {}, "out_of_world": {}, "out_of_world_examples": [], "unsourced_examples": [],
    }
    base.update(over)
    return base


def _record(entity_id=7, union=("CARRIED_FOOD",), tried=("CARRIED_FOOD",)):
    return {"event_type": RECORD_EVENT, "payload": {"entity_id": entity_id, "kind": "villager", "tick": 50, "cause_tick": 50,
            "ways_open_in_reach_union": list(union), "ways_in_reach_at_death": list(union), "ways_attempted": list(tried), "last_meal_tick": None}}


def _state():
    from tests.unit.observability.test_starvation_death_record import _world
    return _world()


def _run(tmp_path: Path, ledger: Dict[str, Any], records: List[Dict[str, Any]] = (), starvation=None, state=None, ledger_live=True, starvation_live=True):
    records = list(records)
    if starvation is None:
        # The starvation channel's tally must agree with the O2 count of starvation deaths (every entity): a run that has O2 starvation deaths carries as many records.
        starved = sum(n for key, n in ledger["deaths"].items() if key.endswith("|STARVATION"))
        records += [_record(entity_id=900 + i) for i in range(max(0, starved - len(records)))]
        starvation = {"starvation_deaths_seen": len(records), "records_emitted": len(records)}
    events = []
    if starvation_live:
        events.append({"event_type": CHANNEL_LIVE_EVENT, "payload": {}})
    events.extend(records)
    events.append({"event_type": CHANNEL_TALLY_EVENT, "payload": starvation})
    if ledger_live:
        events.insert(0, {"event_type": LEDGER_LIVE_EVENT, "payload": {}})
    events.append({"event_type": LEDGER_TALLY_EVENT, "payload": ledger})
    path = tmp_path / "simulation_events.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    return SimpleNamespace(world="w", seed=1, ticks=100, sha="s", state=state or _state(), events_path=path, run_dir=tmp_path)


def _row(result, vid, group="*"):
    (row,) = [r for r in result["metrics"] if r["id"] == vid and r["group"] == group]
    return row


def _violations(tmp_path, vid, **ledger):
    return _row(m.compute(_run(tmp_path, _ledger(**ledger))), vid)["violations"]


def test_a_clean_run_has_no_validity_violation_and_every_validity_row_names_its_rule(tmp_path):
    result = m.compute(_run(tmp_path, _ledger()))
    validity = [r for r in result["metrics"] if r["class"] == "validity"]
    assert {r["id"] for r in validity} == {"V1", "V2", "V3", "V4", "V5", "V6", "V8"}
    assert all(r["violations"] == 0 and r["oracle"] for r in validity)


def test_v1_a_hunger_drop_with_no_accepted_transfer_is_food_from_nothing(tmp_path):
    assert _violations(tmp_path, "V1", hunger_drops={f"{PEOPLE}|with_accepted_transfer": 5}) == 0
    assert _violations(tmp_path, "V1", hunger_drops={f"{PEOPLE}|without_transfer": 2}) == 2


def test_v2_meat_may_leave_the_world_only_through_the_decay_sink_and_the_books_must_balance(tmp_path):
    ok = _ledger(meat={"made": 8.0, "taken": 2.0, "looted": 2.0, "vanished": 4.0}, world_events={"MEAT_DECAYED": 1, "meat_decayed_quantity": 4.0})
    assert _row(m.compute(_run(tmp_path, ok)), "V2")["violations"] == 0  # a body looted whole is not meat vanishing
    leak = _ledger(meat={"made": 6.0, "taken": 2.0, "vanished": 4.0}, world_events={})
    assert _row(m.compute(_run(tmp_path, leak)), "V2")["violations"] >= 1
    unbalanced = _ledger(meat={"made": 9.0, "taken": 2.0, "vanished": 4.0}, world_events={"meat_decayed_quantity": 4.0})
    assert _row(m.compute(_run(tmp_path, unbalanced)), "V2")["violations"] >= 1


def test_v3_a_death_beside_a_way_judged_open_and_never_tried_is_a_violation(tmp_path):
    one_starved = _ledger(deaths={f"{PEOPLE}|STARVATION": 1})
    clean = m.compute(_run(tmp_path, one_starved, [_record()]))
    assert _row(clean, "V3")["violations"] == 0
    untried = m.compute(_run(tmp_path, one_starved, [_record(union=("CARRIED_FOOD", "INN_MEAL"), tried=("CARRIED_FOOD",))]))
    row = _row(untried, "V3")
    assert row["violations"] == 1 and row["examples"][0]["untried"] == ["INN_MEAL"]


def test_v3_cannot_be_read_when_the_starvation_tally_disagrees_with_the_o2_starvation_count(tmp_path):
    """O2 scans every entity (run_ledger._count_deaths): it is the independent count of starvation deaths. A tally below it is a silent miss."""
    agree = m.compute(_run(tmp_path, _ledger(deaths={f"{PEOPLE}|STARVATION": 1}), [_record()]))
    assert _row(agree, "V3")["violations"] == 0
    with pytest.raises(m.GateDataMissingError, match=r"starvation tally 0 != O2 starvation deaths 1"):
        m.compute(_run(tmp_path, _ledger(deaths={f"{PEOPLE}|STARVATION": 1}), [], starvation={"starvation_deaths_seen": 0, "records_emitted": 0}))
    with pytest.raises(m.GateDataMissingError, match=r"starvation tally 1 != O2 starvation deaths 0"):
        m.compute(_run(tmp_path, _ledger(deaths={f"{PEOPLE}|COMBAT": 3}), [_record()], starvation={"starvation_deaths_seen": 1, "records_emitted": 1}))


def test_v4_diet_gates_an_inn_meal_by_a_kind_without_prepared_food_and_node_food_by_a_meat_only_kind(tmp_path):
    assert _violations(tmp_path, "V4", transfers={f"{PEOPLE}|TOWN_SERVICE|accepted": 9, f"{DEER}|NODE|accepted": 9}) == 0
    assert _violations(tmp_path, "V4", transfers={f"{WOLF}|TOWN_SERVICE|accepted": 1}) == 1
    assert _violations(tmp_path, "V4", transfers={f"{WOLF}|NODE|accepted": 3}) == 3
    assert _violations(tmp_path, "V4", transfers={f"{WOLF}|TOWN_SERVICE|rejected": 4}) == 0  # a refused try is the gate working


def test_v5_a_moved_entity_outside_the_world_is_a_violation_with_examples(tmp_path):
    bad = _row(m.compute(_run(tmp_path, _ledger(out_of_world={PEOPLE: 2}, out_of_world_examples=[{"entity_id": 3, "tick": 9, "position": [1e6, 0]}]))), "V5")
    assert bad["violations"] == 2 and bad["examples"][0]["entity_id"] == 3


def test_v6_coin_created_beyond_declared_world_creation_is_minted_coin(tmp_path):
    assert _violations(tmp_path, "V6", coin_first=100.0, coin_last=110.0, declared_coin=10.0) == 0
    assert _violations(tmp_path, "V6", coin_first=100.0, coin_last=110.0, declared_coin=0.0) == 1


def test_v8_every_mid_run_add_needs_a_declared_source(tmp_path):
    assert _violations(tmp_path, "V8", adds={f"{PEOPLE}|BIRTH": 3}) == 0
    row = _row(m.compute(_run(tmp_path, _ledger(adds={f"{PEOPLE}|BIRTH": 3, f"{WOLF}|unsourced": 2, f"{DEER}|unsourced": 1}))), "V8")
    assert row["violations"] == 3 and "examples" not in row
    named = [{"entity_id": 9, "tick": 4, "kind_group": WOLF, "check": "unsourced"}]
    row = _row(m.compute(_run(tmp_path, _ledger(adds={f"{WOLF}|unsourced": 1}, unsourced_examples=named))), "V8")
    assert row["violations"] == 1 and row["examples"] == named


def test_silence_is_no_data_never_zero_violations(tmp_path):
    with pytest.raises(m.GateDataMissingError):
        m.compute(_run(tmp_path, _ledger(), ledger_live=False))
    with pytest.raises(m.GateDataMissingError):
        m.compute(_run(tmp_path, _ledger(), starvation_live=False))
    with pytest.raises(m.GateDataMissingError):  # a death seen whose record never reached the file
        m.compute(_run(tmp_path, _ledger(), starvation={"starvation_deaths_seen": 1, "records_emitted": 1}))
    with pytest.raises(m.GateDataMissingError):
        m.compute(SimpleNamespace(world="w", seed=1, ticks=1, state=_state(), events_path=tmp_path / "missing.jsonl"))


def test_outcome_rows_carry_their_thresholds_and_group_by_kind_property(tmp_path):
    ledger = _ledger(deaths={f"{DEER}|STARVATION": 3}, attacks={f"{WOLF}|0|1|hit": 4, f"{PEOPLE}|1|1|hit": 9, f"{WOLF}|0|1|kill": 1},
                     transfers={f"{PEOPLE}|CARRIED_FOOD|accepted": 5, f"{PEOPLE}|CARRIED_FOOD|rejected": 7}, world_events={"FEEDING_KILL": 1})
    rows = m.compute(_run(tmp_path, ledger))["metrics"]
    outcome = [r for r in rows if r["class"] == "outcome"]
    assert all(r["k"] > 0 and r["floor"] > 0 for r in outcome)
    assert _row({"metrics": rows}, "O1.starvation_share", DEER)["value"] == 0.5  # 3 of the 6 at the first tick
    assert _row({"metrics": rows}, "O3.attacks_on_people", WOLF)["value"] == 5  # people attacking people is not O3
    assert not [r for r in rows if r["id"].startswith("O5")], "net coin is the V6 validity check; O5 is per-group flows only"
    (ways,) = [r for r in rows if r["id"] == "O4.accepted"]
    assert ways["value"] == 5 and ways["key"] == "CARRIED_FOOD"  # only accepted transfers
    assert _row({"metrics": rows}, "O6.kills_not_eaten")["value"] == 0.0  # the one kill was a feeding kill
    assert not any(" " in r["group"] or r["group"] in ("hunter", "predator", "prey") for r in rows), "groups are diet properties, never roles"


def test_pool_counts_seeds_with_survivors_and_checks_the_liveness_of_declared_ways():
    def doc(survive, source_value, feeding):
        return {"world": "w", "metrics": [
            {"id": "O2.survivors", "group": WOLF, "value": survive},
            {"id": "O4.accepted", "group": PEOPLE, "key": "CORPSE_FOOD", "value": source_value},
            {"id": "O4.accepted", "group": PEOPLE, "key": "TOWN_SERVICE", "value": 1},
            {"id": "O4.accepted", "group": PEOPLE, "key": "NODE", "value": 1},
            {"id": "O2.survivors", "group": PEOPLE, "value": 1},
            {"id": "O6.feeding_kills", "group": "*", "value": feeding}]}
    rows = m.pool([doc(1.0, 0.0, 1.0), doc(0.0, 0.0, 0.0)])
    survivors = {r["group"]: r["value"] for r in rows if r["id"] == "O2.seeds_with_survivors"}
    assert survivors == {WOLF: 1.0, PEOPLE: 2.0}
    (v7,) = [r for r in rows if r["id"] == "V7"]
    assert v7["scope"] == "pooled" and v7["violations"] == 1 and v7["examples"][0]["way"] == "CORPSE_FOOD"  # a feeding kill and no body ever eaten
    assert [r for r in m.pool([doc(1.0, 3.0, 1.0)]) if r["id"] == "V7"][0]["violations"] == 0


def test_two_computes_of_the_same_run_write_the_same_bytes(tmp_path):
    run = _run(tmp_path, _ledger(deaths={f"{DEER}|STARVATION": 1}, transfers={f"{PEOPLE}|NODE|accepted": 2}))
    assert json.dumps(m.compute(run), sort_keys=True) == json.dumps(m.compute(run), sort_keys=True)


def test_the_module_imports_no_engine_decision_logic_and_no_live_kernel():
    tree = ast.parse(Path(m.__file__).read_text(encoding="utf-8"))
    imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert not any(mod.startswith(("src.engine", "src.systems", "src.domains")) for mod in imported), imported
    assert "Kernel" not in Path(m.__file__).read_text(encoding="utf-8").replace("no live kernel", "")


def test_a_person_who_hunts_is_a_person_and_a_wild_meat_eater_has_no_trade_trait(tmp_path):
    """D43: personhood is the coin-and-trade trait, never the diet. A trading meat-eater's attacks are not O3; a non-trading one's are."""
    trading_meat_eater = f"{WOLF}|1|1|hit"  # a diet with meat, and the trait: a person who hunts
    ledger = _ledger(attacks={trading_meat_eater: 6, f"{WOLF}|0|1|hit": 2, f"{WOLF}|0|0|hit": 8})  # the last one hits a non-person: not an attack on people
    rows = m.compute(_run(tmp_path, ledger))["metrics"]
    assert _row({"metrics": rows}, "O3.attacks_on_people", WOLF)["value"] == 2


def test_the_population_floor_is_a_tenth_of_the_first_tick_population_and_never_under_three(tmp_path):
    assert m.population_floor(10) == 3.0 and m.population_floor(29) == 3.0  # small: the base floor holds
    assert m.population_floor(100) == 10.0 and m.population_floor(250) == 25.0  # large: a tenth
    rows = m.compute(_run(tmp_path, _ledger(population={"1": {PEOPLE: 200, WOLF: 4}})))["metrics"]
    assert {r["floor"] for r in rows if r["id"] == "O2.population" and r["group"] == PEOPLE} == {20.0}
    assert {r["floor"] for r in rows if r["id"] == "O2.population" and r["group"] == WOLF} == {3.0}


def test_an_outcome_row_never_carries_a_verdict_and_pooled_outcomes_are_values_only(tmp_path):
    """Outcome drift is reported to the owner and never auto-fails (section 12.3): only validity rows carry violations."""
    rows = m.compute(_run(tmp_path, _ledger(deaths={f"{DEER}|STARVATION": 9})))["metrics"]
    assert all("violations" not in r and "oracle" not in r for r in rows if r["class"] == "outcome")
    docs = [{"world": "w", "metrics": [{"id": "O2.survivors", "group": WOLF, "value": 0.0}]}]
    assert all("violations" not in r for r in m.pool(docs) if r["class"] == "outcome")

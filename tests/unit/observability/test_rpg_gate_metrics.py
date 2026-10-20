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
        "population": {"1": {PEOPLE: 10, WOLF: 4, DEER: 6}}, "transfers": {}, "hunger_drops": {}, "diet_breaches": {}, "deaths": {}, "adds": {},
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


def _run(tmp_path: Path, ledger: Dict[str, Any], records: List[Dict[str, Any]] = (), starvation=None, state=None, ledger_live=True, starvation_live=True, seeds=(1,)):
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
    return SimpleNamespace(world="w", seed=1, ticks=100, sha="s", state=state or _state(), events_path=path, run_dir=tmp_path, seeds=seeds)


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


def test_v4_diet_gates_an_inn_meal_by_a_kind_without_prepared_food_and_counts_a_consumption_outside_the_diet(tmp_path):
    assert _violations(tmp_path, "V4", transfers={f"{PEOPLE}|TOWN_SERVICE|accepted": 9, f"{DEER}|NODE|accepted": 9}) == 0
    assert _violations(tmp_path, "V4", transfers={f"{WOLF}|TOWN_SERVICE|accepted": 1}) == 1
    # an acquisition is not a breach (a wolf at a herb node, issue: v1 gate V4 false positive): only a consumption counts
    assert _violations(tmp_path, "V4", transfers={f"{WOLF}|NODE|accepted": 3}) == 0
    assert _violations(tmp_path, "V4", diet_breaches={f"{WOLF}|CARRIED_FOOD|wild_berries": 2}) == 2  # a meat-only body ate plant-class food
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
    assert _row({"metrics": rows}, "O1.starved", DEER)["value"] == 3 and _row({"metrics": rows}, "O1.at_risk", DEER)["value"] == 6  # a share is two count rows
    assert not [r for r in rows if r["id"] == "O1.starvation_share"], "the share is a pooled row only"
    assert _row({"metrics": rows}, "O3.attacks_on_people", WOLF)["value"] == 5  # people attacking people is not O3
    assert not [r for r in rows if r["id"].startswith("O5")], "net coin is the V6 validity check; O5 is per-group flows only"
    ways = [r for r in rows if r["id"] == "O4.accepted" and r["group"] == PEOPLE and r["value"] > 0]
    assert [(r["key"], r["value"]) for r in ways] == [("CARRIED_FOOD", 5)]  # only accepted transfers; every other declared source is a true 0
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


_REAL_TICK0_ALIVE = m._tick0_alive


@pytest.fixture(autouse=True)
def _no_world_compile(monkeypatch):
    """The fake world "w" has no spec: its declaration (the compiled tick-0 groups) is the three kind groups of ``_ledger`` (people trade, wolves and deer do not)
    unless a test sets other counts with ``_tick0``."""
    monkeypatch.setattr(m, "_tick0_alive", lambda world, seed: {PEOPLE: 10, WOLF: 4, DEER: 6})
    monkeypatch.setattr(m, "_tick0_persons", lambda world, seed: {PEOPLE: 10})
    monkeypatch.setattr(m, "_spawn_kinds", lambda world, seed: [])


def _tick0(monkeypatch, per_seed):
    """Patch each seed's compiled tick-0 counts (the seed set itself is handed to ``compute`` by ``_run(seeds=...)``)."""
    monkeypatch.setattr(m, "_tick0_alive", lambda world, seed: dict(per_seed[seed]))


def _floors(result, group):
    return {r["floor"] for r in result["metrics"] if r["id"] == "O2.population" and r["group"] == group}


def test_the_population_floor_is_a_tenth_of_the_tick0_mean_and_never_under_three(tmp_path, monkeypatch):
    assert m.population_floor(10) == 3.0 and m.population_floor(29) == 3.0  # small: the base floor holds
    assert m.population_floor(100) == 10.0 and m.population_floor(250) == 25.0  # large: a tenth
    _tick0(monkeypatch, {1: {PEOPLE: 190, WOLF: 4}, 2: {PEOPLE: 210, WOLF: 4}})
    result = m.compute(_run(tmp_path, _ledger(population={"1": {PEOPLE: 200, WOLF: 4}}), seeds=(1, 2)))
    assert _floors(result, PEOPLE) == {20.0} and _floors(result, WOLF) == {3.0}


def test_the_floor_is_identical_in_every_seed_document_and_at_every_tick(tmp_path, monkeypatch):
    """Two seeds whose own tick-0 counts differ (as frontier's do) get the same floor, on every tick row."""
    _tick0(monkeypatch, {1: {PEOPLE: 310}, 2: {PEOPLE: 330}})
    docs = [m.compute(_run(tmp_path, _ledger(population={"1": {PEOPLE: n}, "50": {PEOPLE: n - 5}}), seeds=(1, 2))) for n in (310, 330)]
    floors = [r["floor"] for d in docs for r in d["metrics"] if r["id"] == "O2.population" and r["group"] == PEOPLE]
    assert len(floors) > 2 and set(floors) == {32.0}


def test_a_paired_arms_floor_does_not_move_when_only_the_other_arms_tick0_changes(tmp_path, monkeypatch):
    base = {1: {PEOPLE: 100}, 2: {PEOPLE: 100}}
    _tick0(monkeypatch, base)
    before = _floors(m.compute(_run(tmp_path, _ledger(population={"1": {PEOPLE: 100}}), seeds=(1, 2))), PEOPLE)
    _tick0(monkeypatch, {1: {PEOPLE: 400}, 2: {PEOPLE: 400}})  # the new arm's world: a different tick-0
    assert _floors(m.compute(_run(tmp_path, _ledger(population={"1": {PEOPLE: 400}}), seeds=(1, 2))), PEOPLE) == {40.0}
    _tick0(monkeypatch, base)  # the base arm, read again
    assert _floors(m.compute(_run(tmp_path, _ledger(population={"1": {PEOPLE: 100}}), seeds=(1, 2))), PEOPLE) == before == {10.0}


def test_a_world_with_no_spec_is_no_data_never_a_silent_floor():
    with pytest.raises(m.GateDataMissingError, match="has no spec"):
        _REAL_TICK0_ALIVE("no_such_world_for_the_floor", 42)


def test_a_run_with_no_seed_set_is_no_data_never_a_floor_from_nowhere(tmp_path):
    with pytest.raises(m.GateDataMissingError):
        m.compute(_run(tmp_path, _ledger(), seeds=()))


def test_the_compiled_tick0_population_equals_the_ledgers_first_observed_population():
    """The floor's base (a compile, no ticks) is what the ledger's first sample sees, on the gate worlds."""
    import shutil
    from pathlib import Path
    from tools.test_architecture.rpg_gate_run import build_kernel
    from src.observability.run_ledger import RunLedger
    for world in ("frontier_living_world", "urban_political", "crowded_frontier"):
        run_id = f"floor-tick0-{world}"
        kernel = build_kernel(world, 42, run_id)
        try:
            kernel.tick_once()
            payload = RunLedger.tally_event().payload
            first = payload["population"][str(payload["first_tick"])]
        finally:
            kernel.shutdown()
            shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)
        assert _REAL_TICK0_ALIVE(world, 42) == first, world


def test_an_outcome_row_never_carries_a_verdict_and_pooled_outcomes_are_values_only(tmp_path):
    """Outcome drift is reported to the owner and never auto-fails (section 12.3): only validity rows carry violations."""
    rows = m.compute(_run(tmp_path, _ledger(deaths={f"{DEER}|STARVATION": 9})))["metrics"]
    assert all("violations" not in r and "oracle" not in r for r in rows if r["class"] == "outcome")
    docs = [{"world": "w", "metrics": [{"id": "O2.survivors", "group": WOLF, "value": 0.0}]}]
    assert all("violations" not in r for r in m.pool(docs) if r["class"] == "outcome")


# ------------------------------------------------------------------------------------------------ declared row domains (TCK-20261020-RPG-GATE-ROWS-COME-FROM-DECLARED-DOMAINS)
def _row_keys(result):
    return {(r["id"], r["group"], str(r.get("key", "")), r.get("tick")) for r in result["metrics"]}


def test_two_seeds_with_different_events_emit_the_same_row_set(tmp_path):
    quiet = m.compute(_run(tmp_path, _ledger()))
    busy = m.compute(_run(tmp_path, _ledger(
        deaths={f"{DEER}|STARVATION": 2, f"{WOLF}|COMBAT": 1, f"{PEOPLE}|HAZARD": 3}, transfers={f"{PEOPLE}|NODE|accepted": 4, f"{WOLF}|CORPSE_FOOD|accepted": 2},
        attacks={f"{WOLF}|0|1|hit": 2}, world_events={"FEEDING_KILL": 1})))
    assert _row_keys(quiet) == _row_keys(busy)
    zero = [r for r in quiet["metrics"] if r["id"] == "O2.deaths"]
    assert zero and all(r["value"] == 0 for r in zero)


def test_the_death_causes_and_transfer_sources_are_the_declared_enumerations(tmp_path):
    from src.core.death_cause import DeathCause

    result = m.compute(_run(tmp_path, _ledger()))
    for group in (PEOPLE, WOLF, DEER):
        assert {r["key"] for r in result["metrics"] if r["id"] == "O2.deaths" and r["group"] == group} == {c.value for c in DeathCause}
        assert {r["key"] for r in result["metrics"] if r["id"] == "O4.accepted" and r["group"] == group} == set(m.TRANSFER_SOURCES)
    assert {r["group"] for r in result["metrics"] if r["id"] == "O3.attacks_on_people"} == {WOLF}  # only a declared wild meat-eater: a diet with meat, a body without the trade trait


def test_transfer_sources_cover_every_source_kind_literal_in_src():
    import re

    root = Path(m.__file__).resolve().parents[1]
    literals = {hit for path in root.rglob("*.py") for hit in re.findall(r'source_kind\s*=\s*"([A-Z_]+)"', path.read_text(encoding="utf-8"))}
    assert literals, "the scan found no source_kind literals: the pattern is stale"
    assert literals <= set(m.TRANSFER_SOURCES), sorted(literals - set(m.TRANSFER_SOURCES))


def test_something_seen_outside_its_declaration_is_no_data_not_a_new_row(tmp_path):
    with pytest.raises(m.GateDataMissingError, match="kind group"):
        m.compute(_run(tmp_path, _ledger(transfers={"phantom|NODE|accepted": 1})))
    with pytest.raises(m.GateDataMissingError, match="transfer source"):
        m.compute(_run(tmp_path, _ledger(transfers={f"{PEOPLE}|TELEPORT|accepted": 1})))
    with pytest.raises(m.GateDataMissingError, match="death cause"):
        m.compute(_run(tmp_path, _ledger(deaths={f"{PEOPLE}|MAGIC": 1})))
    with pytest.raises(m.GateDataMissingError, match="wild meat-eater"):
        m.compute(_run(tmp_path, _ledger(attacks={"meat+plant|0|1|hit": 1})))


def test_a_share_is_two_count_rows_and_a_pooled_row_that_is_null_when_the_denominator_is_empty(tmp_path):
    seed_a = m.compute(_run(tmp_path, _ledger(deaths={f"{DEER}|STARVATION": 3}, population={"1": {PEOPLE: 10, WOLF: 4, DEER: 6}})))
    seed_b = m.compute(_run(tmp_path, _ledger(deaths={}, population={"1": {PEOPLE: 10, WOLF: 4, DEER: 4}})))
    seed_c = m.compute(_run(tmp_path, _ledger(deaths={}, population={"1": {PEOPLE: 10, WOLF: 4}})))  # no deer at tick 0: an empty denominator on this seed
    for doc in (seed_a, seed_b, seed_c):
        assert not [r for r in doc["metrics"] if r["id"] == "O1.starvation_share"], "no per-seed share row"
        assert _row(doc, "O1.at_risk", DEER)["value"] in (6, 4, 0)
    docs = [dict(d, world="w") for d in (seed_a, seed_b, seed_c)]
    (share,) = [r for r in m.pool(docs) if r["id"] == "O1.starvation_share" and r["group"] == DEER]
    assert share["scope"] == "pooled" and share["value"] == pytest.approx(3 / 10)  # sum(starved) / sum(at risk): the empty seed adds nothing
    empty = [dict(m.compute(_run(tmp_path, _ledger(population={"1": {PEOPLE: 10, WOLF: 4}}))), world="w")]
    (null,) = [r for r in m.pool(empty) if r["id"] == "O1.starvation_share" and r["group"] == DEER]
    assert null["value"] is None and null["reason"] == "empty_denominator"


def test_every_pooled_share_row_names_its_numerator_and_denominator_run_rows(tmp_path):
    seed_docs = [m.compute(_run(tmp_path, _ledger(deaths={f"{DEER}|STARVATION": 1}))) for _ in range(2)]
    shares = [r for r in m.pool([dict(d, world="w") for d in seed_docs]) if r["id"] == "O1.starvation_share"]
    assert shares
    for share in shares:
        assert share["numerator"] == "O1.starved" and share["denominator"] == "O1.at_risk"
        for doc in seed_docs:  # the named rows exist on every seed's run document, for the share's own group
            assert _row(doc, share["numerator"], share["group"]) and _row(doc, share["denominator"], share["group"])


def test_at_risk_counts_every_individual_ever_alive_so_a_mid_run_spawn_raises_it_and_the_share_stays_at_most_one(tmp_path):
    ledger = _ledger(deaths={f"{WOLF}|STARVATION": 7}, adds={f"{WOLF}|BIRTH": 3, f"{WOLF}|AUTHORED_ARRIVAL": 2, f"{DEER}|BIRTH": 1})
    doc = m.compute(_run(tmp_path, ledger))
    assert _row(doc, "O1.at_risk", WOLF)["value"] == 4 + 3 + 2  # the tick-0 four plus every entry into the group
    assert _row(doc, "O1.at_risk", DEER)["value"] == 6 + 1 and _row(doc, "O1.at_risk", PEOPLE)["value"] == 10
    assert _row(doc, "O1.starved", WOLF)["value"] == 7  # spawned individuals who starved are in the numerator
    (share,) = [r for r in m.pool([dict(doc, world="w")]) if r["id"] == "O1.starvation_share" and r["group"] == WOLF]
    assert share["value"] == pytest.approx(7 / 9) and share["value"] <= 1.0


def test_a_world_declaring_a_spawn_of_a_kind_absent_at_tick_zero_has_that_groups_rows_on_every_seed(tmp_path, monkeypatch):
    RAIDER = "meat+plant"
    monkeypatch.setattr(m, "_spawn_kinds", lambda world, seed: ["raider_camp"])
    monkeypatch.setattr(m, "species_kind_group", lambda kind: RAIDER if kind == "raider_camp" else m.UNDECLARED)
    ticks = {"1": {PEOPLE: 10, WOLF: 4, DEER: 6}, "50": {PEOPLE: 10, WOLF: 4, DEER: 6}}  # the sampled ticks are part of a row's identity: the same in both seeds
    quiet = m.compute(_run(tmp_path, _ledger(population=ticks), seeds=(1, 2)))
    arrival = m.compute(_run(tmp_path, _ledger(adds={f"{RAIDER}|AUTHORED_ARRIVAL": 2}, population={"1": ticks["1"], "50": {**ticks["50"], RAIDER: 2}}), seeds=(1, 2)))
    assert _row_keys(quiet) == _row_keys(arrival)
    assert _row(quiet, "O1.at_risk", RAIDER)["value"] == 0 and _row(arrival, "O1.at_risk", RAIDER)["value"] == 2
    assert {r["key"] for r in quiet["metrics"] if r["id"] == "O4.accepted" and r["group"] == RAIDER} == set(m.TRANSFER_SOURCES)

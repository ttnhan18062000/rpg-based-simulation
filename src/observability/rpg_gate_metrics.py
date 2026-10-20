"""
src/observability/rpg_gate_metrics.py
───────────────────────────────────────────────────────────────────────────────
The metric module of the rpg regression gate (TCK-20261009-RPG-REGRESSION-METRICS-COMPUTED-FROM-TYPED-RECORDS). ALL metric definitions live in THIS file
(the harness hashes only this file, so a definition change makes a recorded baseline stale, as intended).

``compute(run)`` reads one finished run: its ``simulation_events.jsonl`` (the starvation-death records, the run ledger's live header and closing tally)
and the FINAL state, and returns ``{"metrics": [row, ...]}``. ``pool(docs)`` combines one world's per-seed documents into pooled rows. Nothing here
touches a live kernel, and a silent channel is never read as zero violations: a missing ledger or starvation channel raises ``GateDataMissingError`` and the
harness records the run as ``no-data``.

Rows (harness format ``rpg-gate-metrics/v1``): validity rows carry ``violations`` (an int, 0 is clean), ``oracle`` (the rule that was contradicted) and up to
five ``examples``; outcome rows carry ``value``, ``k`` (standard errors a paired drift must exceed) and ``floor`` (the smallest change worth tracing). Groups
are KIND GROUPS (what a kind's declared diet allows: ``meat``, ``plant+prepared``), never an entity role (decision 42, D46).

Validity (permanent, exact; each names its rule): V1 food from nothing, V2 conservation (meat), V3 no death beside a known untried way, V4 diet gates,
V5 in-world positions, V6 no minted coin, V7 liveness of declared ways (pooled over a world's seeds), V8 every mid-run add has a declared source.
Outcome (what the world did; paired against a baseline, never graded alone): O1 starvation share, O2 population and deaths by cause (and survivors),
O3 attacks on people by wild meat-eaters (a diet with meat, a species without the trade trait), O4 ways mix, O5 per-group coin flows (no producer yet:
the world's net coin is validity V6), O6 kills not eaten. An outcome row never grades: only a validity row can fail. O7 (tick time) is the harness's cost document, not a metric row here.

Floors and k are practical thresholds with a fiction reason each (``OUTCOME_THRESHOLDS``), never fitted to a measured baseline.
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from src.ai.goals.kind_group import kind_group
from src.observability.run_ledger import (
    LEDGER_LIVE_EVENT,
    LEDGER_TALLY_EVENT,
    UNSOURCED,
)
from src.observability.starvation_record import (
    CHANNEL_LIVE_EVENT,
    CHANNEL_TALLY_EVENT,
    RECORD_EVENT,
)
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository, WorldRepositoryError

MAX_EXAMPLES = 5
COIN_EPSILON = 1e-6
PEOPLE_CLASS = "prepared"  # the diet class of the inn's free meal (D44): the V4 diet gate. Personhood is NOT this: it is the trade trait (D43), carried as a 0/1 flag
MEAT_CLASS = "meat"
FOOD_NODE_SOURCE, INN_SOURCE, BODY_SOURCE = "NODE", "TOWN_SERVICE", "CORPSE_FOOD"


class GateDataMissingError(RuntimeError):
    """A channel the gate depends on is silent or inconsistent: the run is no-data, never a pass."""


# --------------------------------------------------------------------------------------------- thresholds
# id -> (k, floor, fiction reason). k = standard errors; floor = the smallest change worth tracing, in the row's own unit.
OUTCOME_THRESHOLDS: Dict[str, Tuple[float, float, str]] = {
    "O1.starvation_share": (2.0, 0.05, "a settlement notices when one more in twenty of a kind starves"),
    "O2.deaths": (2.0, 2.0, "two more deaths of one cause in a run is a story; one is noise"),
    "O2.population": (2.0, 3.0, "a tenth more or fewer of a kind alive, and never under three, is a visible crowd change"),
    "O2.survivors": (2.0, 1.0, "a kind alive or gone in a seed is the whole difference"),
    "O3.attacks_on_people": (2.0, 3.0, "three more bites on villagers a run is the first sign a hunter stopped judging prey"),
    "O4.accepted": (2.0, 5.0, "five more or fewer uses of a way is a change in how the kind lives"),
    "O5.coin_flow": (2.0, 25.0, "twenty-five coin is about five meals; less is rounding in the economy"),  # per-group flows only: no producer yet; the world's net coin is the V6 validity check
    "O6.kills_not_eaten": (2.0, 2.0, "two more kills left uneaten in a run is waste a kind would notice"),
    "O6.feeding_kills": (2.0, 2.0, "two more kills made to eat in a run is a change in how it hunts"),
}
POOLED_THRESHOLDS: Dict[str, float] = {"O2.seeds_with_survivors": 1.0}  # a seed more or fewer where a kind survives

ORACLES: Dict[str, str] = {
    "V1": "Bible 03 atomic conservation, gate H3: a hunger drop has an accepted transfer from a source behind it",
    "V2": "Bible 03 conservation, gate H7: meat leaves a body only by being taken, by the whole body being looted, or through the MEAT_DECAYED sink, and made = taken + looted + vanished + remaining",
    "V3": "SURV-06/07, gate H6, memo rows 54/56: no starvation death with a way the subject judged open and never attempted",
    "V4": "D43, D44, gate H4: a kind whose diet lacks a food class never eats it (the inn's meal needs prepared, checked by the transfer it was served through; every other meal is a consumption of an item, counted when its class is outside the eater's diet). Picking up or carrying a non-diet item is not a V4 breach",
    "V5": "LAW-POSITION-IN-WORLD, Bible 06 topology: a moved, alive entity stays inside the world extent",
    "V6": "EXCH-02, D38, gate H7: total coin changes only by declared world creation (an added entity's starting purse), so the net change beyond it is exactly 0",
    "V7": "SURV-06, D44/D48, gate H5: a declared way is used at least once in a world where it can be (the hunt instance: every feeding kill is eaten from somewhere)",
    "V8": "D67/D70: every mid-run entity add carries a declared, well-formed spawn source",
}


# --------------------------------------------------------------------------------------------- reading a run
def _group_has(group: str, food_class: str) -> bool:
    return food_class in group.split("+")


def _is_wild_meat_eater(group: str, person: str) -> bool:
    """A kind whose diet has meat and whose species lacks the coin-and-trade trait: a person who hunts is a person (D43)."""
    return _group_has(group, MEAT_CLASS) and person != "1"


def _read_events(run: Any) -> List[Dict[str, Any]]:
    path = run.events_path
    if not path.exists():
        raise GateDataMissingError(f"no event file at {path}")
    events = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def _channel(events: Sequence[Mapping[str, Any]], live: str, tally: str, label: str) -> Tuple[Dict[str, Any], List[Mapping[str, Any]]]:
    opened = [e for e in events if e.get("event_type") == live]
    closed = [e for e in events if e.get("event_type") == tally]
    if not opened:
        raise GateDataMissingError(f"{label}: no live header (the channel was silent)")
    if not closed:
        raise GateDataMissingError(f"{label}: no closing tally (the run did not shut down cleanly)")
    return dict(closed[-1]["payload"]), opened


def _final_alive_by_group(state: Any) -> Dict[str, int]:
    counts: Dict[str, int] = defaultdict(int)
    for entity in state.entities.values():
        if entity.combat.alive:
            counts[kind_group(entity)] += 1
    return dict(counts)


def _final_meat(state: Any) -> float:
    return float(sum(s.quantity for c in (state.corpses or {}).values() for s in c.items if s.item_id == "raw_meat"))


def _split(key: str, n: int) -> List[str]:
    parts = key.split("|")
    return parts + [""] * (n - len(parts))


# --------------------------------------------------------------------------------------------- rows
def _validity(vid: str, world: str, violations: int, examples: Optional[List[Any]] = None, **where: str) -> Dict[str, Any]:
    """A validity row; ``where`` may set ``group`` (default ``*``) and ``scope`` (default ``run``)."""
    row: Dict[str, Any] = {"id": vid, "class": "validity", "scope": where.get("scope", "run"), "world": world, "group": where.get("group", "*"),
                           "violations": int(violations), "oracle": ORACLES[vid]}
    if examples:
        row["examples"] = examples[:MAX_EXAMPLES]
    return row


def _outcome(oid: str, world: str, group: str, value: float, **where: Any) -> Dict[str, Any]:
    """A run outcome row; ``where`` may set ``key`` (a cause or a source), ``tick`` and ``floor`` (a row whose floor scales with its group)."""
    k, floor, _ = OUTCOME_THRESHOLDS[oid]
    return {"id": oid, "class": "outcome", "scope": "run", "world": world, "group": group, "value": float(value), "k": k, "floor": floor, **where}


def population_floor(tick0_mean_population: float) -> float:
    """O2.population's floor: a tenth of the group's tick-0 population, and never under the base floor (three).
    Relative floor, computed once per world from the pooled tick-0 mean of the gate config's seed set (identical in every seed document and at every tick)."""
    return max(OUTCOME_THRESHOLDS["O2.population"][1], 0.10 * tick0_mean_population)


def _tick0_alive(world: str, seed: int) -> Dict[str, int]:
    """The alive count by kind group of the world compiled for ``seed``, before any tick (what the ledger's first sample sees)."""
    try:
        spec, context = WorldRepository(os.path.join("data", "worlds")).load_world_with_context(world)
    except WorldRepositoryError as exc:
        raise GateDataMissingError(f"world {world!r} has no spec to compile for the O2.population floor (tick-0 counts): {exc}") from exc
    state, _report = WorldCompiler.compile(spec, seed, context=context)
    return _final_alive_by_group(state)


def tick0_means(world: str, seeds: Sequence[int]) -> Dict[str, float]:
    """The pooled tick-0 mean population per kind group over the gate config's seed set, handed in by the harness (a group absent from a seed counts 0 there)."""
    if not seeds:
        raise GateDataMissingError("the run carries no seed set: the O2.population floor is pooled over the gate config's seeds")
    per_seed = [_tick0_alive(world, seed) for seed in seeds]
    groups = {g for counts in per_seed for g in counts}
    return {g: sum(counts.get(g, 0) for counts in per_seed) / len(seeds) for g in groups}


def _check_food_source(ledger: Mapping[str, Any]) -> Tuple[int, List[Any]]:
    """A hunger drop with no accepted transfer behind it."""
    drops = {k: n for k, n in ledger["hunger_drops"].items() if k.endswith("|without_transfer")}
    return sum(drops.values()), [{"group_key": k, "ticks": n} for k, n in sorted(drops.items())]


def _check_meat_books(ledger: Mapping[str, Any], state: Any, decayed_quantity: float) -> Tuple[int, List[Any]]:
    """Meat leaves the world only through the MEAT_DECAYED sink, and made = taken + vanished + remaining."""
    meat = ledger.get("meat", {})
    made, taken, looted, vanished = meat.get("made", 0.0), meat.get("taken", 0.0), meat.get("looted", 0.0), meat.get("vanished", 0.0)
    found: List[Any] = []
    if abs(vanished - decayed_quantity) > COIN_EPSILON:
        found.append({"vanished_with_bodies": vanished, "meat_decayed_events": decayed_quantity})
    if abs(made - taken - looted - vanished - _final_meat(state)) > COIN_EPSILON:
        found.append({"made": made, "taken": taken, "looted_whole": looted, "vanished": vanished, "remaining_final": _final_meat(state)})
    return len(found), found


def _check_untried_way(records: Sequence[Mapping[str, Any]]) -> Tuple[int, List[Any]]:
    """A starvation death with a way judged open and never attempted."""
    found = [r["payload"] for r in records if set(r["payload"]["ways_open_in_reach_union"]) - set(r["payload"]["ways_attempted"])]
    return len(found), [{"entity_id": p["entity_id"], "kind": p["kind"], "tick": p["tick"],
                         "untried": sorted(set(p["ways_open_in_reach_union"]) - set(p["ways_attempted"]))} for p in found]


def _breaks_a_diet_gate(group: str, source: str) -> bool:
    if source == INN_SOURCE:
        return group != "undeclared" and not _group_has(group, PEOPLE_CLASS)
    return False


def _check_diet_gates(ledger: Mapping[str, Any]) -> Tuple[int, List[Any]]:
    """Diet gates, read from the group's declared food classes: only accepted transfers count (a refused try is the gate working)."""
    found: Dict[str, int] = {}
    for key, n in ledger["transfers"].items():
        group, source, outcome = _split(key, 3)
        if outcome == "accepted" and _breaks_a_diet_gate(group, source):
            found[key] = n
    examples = [{"transfer": k, "count": n} for k, n in sorted(found.items())]
    for key, n in sorted(ledger.get("diet_breaches", {}).items()):
        group, source, item = _split(key, 3)
        found[key] = n
        examples.append({"consumption": key, "count": n, "group": group, "source": source, "item": item})
    return sum(found.values()), examples


def _check_minted_coin(ledger: Mapping[str, Any]) -> Tuple[int, List[Any]]:
    """Coin created beyond declared world creation (an added entity's starting purse)."""
    delta = float(ledger["coin_last"]) - float(ledger["coin_first"]) - float(ledger["declared_coin"])
    if abs(delta) <= COIN_EPSILON:
        return 0, []
    return 1, [{"coin_first": ledger["coin_first"], "coin_last": ledger["coin_last"], "declared": ledger["declared_coin"]}]


def _check_unsourced_adds(ledger: Mapping[str, Any]) -> Tuple[int, List[Any]]:
    """Mid-run adds with no declared source."""
    found = {k: n for k, n in ledger["adds"].items() if k.endswith(f"|{UNSOURCED}")}
    return sum(found.values()), list(ledger["unsourced_examples"])


def _validity_rows(world: str, ledger: Mapping[str, Any], records: Sequence[Mapping[str, Any]], state: Any, decayed_quantity: float) -> List[Dict[str, Any]]:
    checks = {
        "V1": _check_food_source(ledger), "V2": _check_meat_books(ledger, state, decayed_quantity), "V3": _check_untried_way(records), "V4": _check_diet_gates(ledger),
        "V5": (sum(ledger["out_of_world"].values()), list(ledger["out_of_world_examples"])), "V6": _check_minted_coin(ledger), "V8": _check_unsourced_adds(ledger),
    }
    return [_validity(vid, world, count, examples) for vid, (count, examples) in checks.items()]


def _population_rows(world: str, ticks: int, ledger: Mapping[str, Any], state: Any, seeds: Sequence[int]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    population = ledger["population"]
    first = population[str(ledger["first_tick"])] if population else {}
    means = tick0_means(world, seeds)
    final = _final_alive_by_group(state)
    starved: Dict[str, int] = defaultdict(int)
    for key, n in ledger["deaths"].items():
        group, cause = _split(key, 2)
        if cause == "STARVATION":
            starved[group] += n
    for group in sorted(set(first) | set(final) | {g for t in population.values() for g in t}):
        rows.append(_outcome("O1.starvation_share", world, group, starved[group] / max(1, first.get(group, 0))))
        rows.append(_outcome("O2.survivors", world, group, 1.0 if final.get(group, 0) > 0 else 0.0))
        floor = population_floor(means.get(group, 0.0))
        rows += [_outcome("O2.population", world, group, at.get(group, 0), tick=int(t), floor=floor) for t, at in sorted(population.items(), key=lambda kv: int(kv[0]))]
        rows.append(_outcome("O2.population", world, group, final.get(group, 0), tick=ticks, floor=floor))
    return rows


def _death_rows(world: str, ledger: Mapping[str, Any]) -> List[Dict[str, Any]]:
    deaths: Dict[Tuple[str, str], int] = defaultdict(int)
    for key, n in ledger["deaths"].items():
        group, cause = _split(key, 2)
        deaths[(group, cause)] += n
    return [_outcome("O2.deaths", world, group, n, key=cause) for (group, cause), n in sorted(deaths.items())]


def _combat_rows(world: str, ledger: Mapping[str, Any]) -> List[Dict[str, Any]]:
    on_people: Dict[str, int] = defaultdict(int)
    kills = 0
    for key, n in ledger["attacks"].items():
        attacker, attacker_person, victim_person, outcome = _split(key, 4)
        if not _is_wild_meat_eater(attacker, attacker_person):
            continue
        if victim_person == "1":
            on_people[attacker] += n
        if outcome == "kill":
            kills += n
    feeding = float(ledger["world_events"].get("FEEDING_KILL", 0))
    rows = [_outcome("O3.attacks_on_people", world, attacker, n) for attacker, n in sorted(on_people.items())]
    return rows + [_outcome("O6.feeding_kills", world, "*", feeding), _outcome("O6.kills_not_eaten", world, "*", max(0.0, kills - feeding))]


def _way_rows(world: str, ledger: Mapping[str, Any]) -> List[Dict[str, Any]]:
    ways: Dict[Tuple[str, str], int] = defaultdict(int)
    for key, n in ledger["transfers"].items():
        group, source, outcome = _split(key, 3)
        if outcome == "accepted":
            ways[(group, source)] += n
    return [_outcome("O4.accepted", world, group, n, key=source) for (group, source), n in sorted(ways.items())]


def _outcome_rows(world: str, ticks: int, ledger: Mapping[str, Any], state: Any, seeds: Sequence[int]) -> List[Dict[str, Any]]:
    return _population_rows(world, ticks, ledger, state, seeds) + _death_rows(world, ledger) + _combat_rows(world, ledger) + _way_rows(world, ledger)


def compute(run: Any) -> Dict[str, Any]:
    """One finished run's rows. ``run`` carries ``world``, ``seed``, ``ticks``, ``state`` (the final state) and ``events_path``."""
    events = _read_events(run)
    ledger, _ = _channel(events, LEDGER_LIVE_EVENT, LEDGER_TALLY_EVENT, "run ledger")
    starvation, _ = _channel(events, CHANNEL_LIVE_EVENT, CHANNEL_TALLY_EVENT, "starvation-death record")
    records = [e for e in events if e.get("event_type") == RECORD_EVENT]
    if int(starvation["starvation_deaths_seen"]) != len(records) or int(starvation["records_emitted"]) != len(records):
        raise GateDataMissingError(f"starvation-death record: {starvation['starvation_deaths_seen']} deaths seen, {len(records)} records on file (some were dropped)")
    o2_starved = sum(n for key, n in ledger["deaths"].items() if _split(key, 2)[1] == "STARVATION")  # O2 scans every entity: the independent count
    if int(starvation["starvation_deaths_seen"]) != o2_starved:
        raise GateDataMissingError(f"starvation tally {starvation['starvation_deaths_seen']} != O2 starvation deaths {o2_starved} (V3 cannot be read)")
    rows = _validity_rows(run.world, ledger, records, run.state, float(ledger["world_events"].get("meat_decayed_quantity", 0.0)))
    rows += _outcome_rows(run.world, run.ticks, ledger, run.state, tuple(getattr(run, "seeds", ())))
    rows.sort(key=lambda r: (r["id"], r["group"], str(r.get("key", "")), r.get("tick") or 0))
    return {"metrics": rows}


# --------------------------------------------------------------------------------------------- pooling
def _liveness_row(world: str, groups: Set[str], used: Mapping[Tuple[str, str], float], feeding: float) -> Dict[str, Any]:
    """V7: a declared way that exists in this world is used at least once across its seeds (the hunt instance: a feeding kill is eaten from a body)."""
    dead: List[Dict[str, str]] = []
    if feeding > 0 and sum(v for (_, source), v in used.items() if source == BODY_SOURCE) == 0:
        dead.append({"way": BODY_SOURCE, "why": "feeding kills happened and no body was ever eaten"})
    if any(_group_has(g, PEOPLE_CLASS) for g in groups):
        for source in (INN_SOURCE, FOOD_NODE_SOURCE):
            if sum(v for (g, src), v in used.items() if src == source and _group_has(g, PEOPLE_CLASS)) == 0:
                dead.append({"way": source, "why": "people exist and the way was never used"})
    return _validity("V7", world, len(dead), dead, scope="pooled")


def pool(docs: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """One world's pooled rows from its per-seed documents: ``O2.seeds_with_survivors`` per group and V7 (liveness of declared ways)."""
    if not docs:
        return []
    world = docs[0]["world"]
    survivors: Dict[str, int] = defaultdict(int)
    used: Dict[Tuple[str, str], float] = defaultdict(float)
    feeding = 0.0
    for row in (r for doc in docs for r in list(doc.get("metrics", []))):
        if row["id"] == "O2.survivors":
            survivors[row["group"]] += int(row["value"])
        elif row["id"] == "O4.accepted":
            used[(row["group"], row["key"])] += row["value"]
        elif row["id"] == "O6.feeding_kills":
            feeding += row["value"]
    rows: List[Dict[str, Any]] = [
        {"id": "O2.seeds_with_survivors", "class": "outcome", "scope": "pooled", "world": world, "group": group,
         "value": float(n), "floor": POOLED_THRESHOLDS["O2.seeds_with_survivors"]} for group, n in sorted(survivors.items())]
    rows.append(_liveness_row(world, set(survivors), used, feeding))
    rows.sort(key=lambda r: (r["id"], r["group"]))
    return rows

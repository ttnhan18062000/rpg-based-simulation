"""Runtime probe: run one corpus world and count the real behaviour of seven registry mechanisms.

Evidence source for TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE (instrument
`corpus_run`). Usage, from the repo root:  python3 <this file> <world> [ticks] [seed]
Prints one JSON line. Patches are counters only; they never change arguments or results.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

world = sys.argv[1]
ticks = int(sys.argv[2]) if len(sys.argv) > 2 else 300
seed = int(sys.argv[3]) if len(sys.argv) > 3 else 42

from src.config.profiles import PROD_SMALL  # noqa: E402
from src.core.models.social import BetrayalRecord  # noqa: E402
from src.domains.chronicle.compiler import ChronicleCompiler  # noqa: E402
from src.domains.demographics.cohort import DemographicCycleService  # noqa: E402
from src.core.equipment import EquipmentService  # noqa: E402
from src.engine.faction_decision import Betrayal  # noqa: E402
from src.engine.kernel import Kernel  # noqa: E402
from src.engine.military_conflict import MilitaryConflictPhase  # noqa: E402
from src.platform.rng import DeterministicRNG  # noqa: E402
from src.progression.breakthroughs import BreakthroughService  # noqa: E402
from src.world.camp import CampService  # noqa: E402
from src.worldbuilding.compiler import WorldCompiler  # noqa: E402
from src.worldbuilding.repository import WorldRepository  # noqa: E402

C = {
    "betrayal_record_constructed": 0,
    "betrayal_directive_constructed": 0,
    "chronicle_compiler_constructed": 0,
    "equipment_external_calls": 0,
    "equipment_internal_calls": 0,
    "breakthrough_apply_calls": 0,
    "breakthrough_apply_nonempty_calls": 0,
    "military_conflict_execute_calls": 0,
    "camp_process_calls": 0,
    "demographic_process_calls": 0,
    "demographic_max_bracket_count_seen": 0,
}
DEMOGRAPHIC_EVENTS_BY_CATEGORY = {}


def _wrap_init(cls, key):
    orig = cls.__init__

    def init(self, *a, **k):
        C[key] += 1
        return orig(self, *a, **k)

    cls.__init__ = init


_wrap_init(BetrayalRecord, "betrayal_record_constructed")
_wrap_init(Betrayal, "betrayal_directive_constructed")
_wrap_init(ChronicleCompiler, "chronicle_compiler_constructed")

EQ_FILE = str((ROOT / "src/core/equipment.py").resolve())


def _wrap_static(cls, name, fn):
    orig = getattr(cls, name)
    setattr(cls, name, staticmethod(fn(orig)))


def _equipment_wrapper(orig):
    def wrapper(*a, **k):
        caller = sys._getframe(1).f_code.co_filename
        C["equipment_internal_calls" if str(Path(caller).resolve()) == EQ_FILE else "equipment_external_calls"] += 1
        return orig(*a, **k)
    return wrapper


for _name in ("get_gear_score", "rank_item", "should_replace", "auto_equip", "repair_equipment"):
    _wrap_static(EquipmentService, _name, _equipment_wrapper)


def _breakthrough_wrapper(orig):
    def wrapper(breakthrough_ids, *a, **k):
        C["breakthrough_apply_calls"] += 1
        if breakthrough_ids:
            C["breakthrough_apply_nonempty_calls"] += 1
        return orig(breakthrough_ids, *a, **k)
    return wrapper


_wrap_static(BreakthroughService, "apply_bonuses", _breakthrough_wrapper)


def _counting(key):
    def make(orig):
        def wrapper(*a, **k):
            C[key] += 1
            return orig(*a, **k)
        return wrapper
    return make


_wrap_static(MilitaryConflictPhase, "execute", _counting("military_conflict_execute_calls"))
_wrap_static(CampService, "process_camps", _counting("camp_process_calls"))


def _demographic_wrapper(orig):
    def wrapper(state, *a, **k):
        C["demographic_process_calls"] += 1
        for region in state.regions.values():
            for cohort in (region.population_cohorts or {}).values():
                C["demographic_max_bracket_count_seen"] = max(C["demographic_max_bracket_count_seen"], cohort.count)
        result = orig(state, *a, **k)
        for ev in getattr(result, "world_events_add", []) or []:
            name = getattr(getattr(ev, "category", None), "name", str(getattr(ev, "category", None)))
            DEMOGRAPHIC_EVENTS_BY_CATEGORY[name] = DEMOGRAPHIC_EVENTS_BY_CATEGORY.get(name, 0) + 1
        return result
    return wrapper


_wrap_static(DemographicCycleService, "process_demographics", _demographic_wrapper)


def cohort_total(state):
    return sum(c.count for r in state.regions.values() for c in (r.population_cohorts or {}).values())


repo = WorldRepository(str(ROOT / "data" / "worlds"))
spec, context = repo.load_world_with_context(world)
state, _ = WorldCompiler.compile(spec, seed, context=context)
camps_start = len(state.camps)
camp_snapshot = {k: (v.maturity, v.last_raid_tick) for k, v in state.camps.items()}
cohorts_start = cohort_total(state)
kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(seed), flags={"no_frame_pacing": True})
ticks_run = 0
try:
    for _ in range(ticks):
        kernel.tick_once()
        ticks_run += 1
finally:
    final_state = getattr(kernel, "state", state)
    kernel.shutdown()
camps_changed = sum(
    1 for k, v in final_state.camps.items() if camp_snapshot.get(k) != (v.maturity, v.last_raid_tick)
)
nonempty_breakthroughs = sum(
    1 for e in final_state.entities.values()
    if getattr(getattr(e, "attributes", None), "active_breakthroughs", None)
)
print(json.dumps({
    "world": world, "ticks_requested": ticks, "ticks_run": ticks_run, "seed": seed,
    "camps_start": camps_start, "camps_changed_by_end": camps_changed,
    "cohort_total_start": cohorts_start, "cohort_total_end": cohort_total(final_state),
    "entities_with_nonempty_breakthroughs_at_end": nonempty_breakthroughs,
    "demographic_events_by_category": DEMOGRAPHIC_EVENTS_BY_CATEGORY,
    **C,
}))

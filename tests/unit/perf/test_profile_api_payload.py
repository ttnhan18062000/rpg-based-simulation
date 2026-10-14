"""tools/perf/profile_api_payload.py (TCK-20260929-PROFILE-API-PAYLOAD-DEAD-API-REFS): a dead import or a dead API call fails here, not at `make profile-api`."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from src.perf.scenarios import build_idle_state
from tools.perf import profile_api_payload as pap

SOURCE = Path(pap.__file__).read_text(encoding="utf-8")


def test_the_module_imports_and_names_only_live_apis() -> None:
    assert pap.V2EngineManager.__name__ == "V2EngineManager" and hasattr(pap.StatePresenter, "present_map")
    for dead in ("SimulationConfig", "_loop", "_step()", "from src.config import", "engine_manager import EngineManager"):
        assert dead not in SOURCE, dead


def test_the_world_is_chosen_in_one_helper_that_a_stub_factory_can_replace() -> None:
    seen = {}

    def factory(profile, seed, entities_count, world_id):
        seen.update(profile=profile, seed=seed, entities_count=entities_count, world_id=world_id)
        return "mgr"

    assert pap.build_manager(7, world_id="some_world", entities=3, factory=factory) == "mgr"
    assert seen == {"profile": pap.DEFAULT_PROFILE, "seed": 7, "entities_count": 3, "world_id": "some_world"}
    assert SOURCE.count("factory(profile") == 1  # the only place a manager is built


def test_advance_ticks_the_kernel_without_starting_an_engine_thread() -> None:
    calls = []
    kernel = SimpleNamespace(state=SimpleNamespace(tick=0), tick_once=lambda: (calls.append(1), setattr(kernel.state, "tick", len(calls))))
    assert pap.advance(SimpleNamespace(kernel=kernel), 4) == 4 and len(calls) == 4
    assert pap.advance(SimpleNamespace(kernel=kernel), 0) == 4  # no ticks, no change


def test_measure_and_render_report_every_endpoint_for_a_real_state() -> None:
    state = build_idle_state(entity_count=5)
    sizes = pap.measure(state)
    assert sizes["alive_count"] == 5 and sizes["map_size"] > 0 and sizes["full_size"] > sizes["state_size"] > 0 and sizes["first_entity_id"] is not None
    text = pap.render(sizes)
    for line in ("GET /api/v1/map", "GET /api/v1/static", "GET /api/v1/state", "Full snapshot", "API PAYLOAD SIZE REPORT"):
        assert line in text

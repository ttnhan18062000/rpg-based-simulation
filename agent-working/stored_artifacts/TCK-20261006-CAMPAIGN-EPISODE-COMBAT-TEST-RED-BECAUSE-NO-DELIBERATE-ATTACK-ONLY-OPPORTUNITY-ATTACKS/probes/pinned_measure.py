"""The campaign test's three assertions measured under a pinned NORMAL governor.

usage: pinned_measure.py <root> [normal|degraded|none]   (cwd is set to <root>; content seeds from data/content)
`none` runs the unpinned scenario kernel (what the current test does)."""
import os
import sys
from collections import Counter

ROOT, PIN = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "normal")
os.chdir(ROOT)
sys.path.insert(0, ROOT)
import src  # noqa: E402

assert src.__file__.startswith(ROOT), (src.__file__, ROOT)
from src.config.profiles import HardwareClass, RuntimeProfile  # noqa: E402
from src.core.governance import RuntimeMode  # noqa: E402
from src.domains.campaigns.orchestrator import CampaignOrchestrator  # noqa: E402
from src.engine.combat import CombatResolutionSystem  # noqa: E402
from src.engine.governor import ResourceGovernor  # noqa: E402
from src.engine.kernel import Kernel  # noqa: E402
from src.engine.scenario_runtime import ScenarioRuntimeService  # noqa: E402
from src.platform.rng import DeterministicRNG  # noqa: E402
from tests.integration.campaigns.test_catalog_entity_spawn_wiring import (  # noqa: E402
    _campaign_life_arc_shaped_manifest, _CollectingRecorder)


class PinnedGovernor(ResourceGovernor):
    def __init__(self, mode):
        super().__init__()
        self._pin = mode

    def _get_indicated_mode(self, profile, signals):
        return self._pin

    def force_mode(self, mode, status, current_tick):
        return None


deliberate = Counter()
_ra = CombatResolutionSystem.resolve_attack


def counting(*a, **k):
    deliberate["resolve_attack"] += 1
    return _ra(*a, **k)


CombatResolutionSystem.resolve_attack = staticmethod(counting)

rec = _CollectingRecorder()
orch = CampaignOrchestrator(_campaign_life_arc_shaped_manifest(tick_limit=70))
spec = orch._manifest.episodes[0]
state = orch._build_initial_state(42, spec)
svc = ScenarioRuntimeService(spec, initial_state=state, scenario_event_recorder=None)
if PIN == "none":
    svc._kernel = svc._build_kernel()
else:
    profile = RuntimeProfile(name=spec.id, hardware_class=HardwareClass.CLASS_B, max_ram_mb=512, max_cpu_percent=100.0,
                             max_worker_count=0, max_queue_depth=1000, max_replay_buffer_kb=64,
                             max_observability_budget_percent=5.0, max_tick_budget_ms=200.0)
    mode = RuntimeMode.NORMAL if PIN == "normal" else RuntimeMode.DEGRADED
    svc._kernel = Kernel(profile, state, DeterministicRNG(base_seed=state.seed), flags={"no_replay": True},
                         governor=PinnedGovernor(mode))
svc._kernel._event_listeners = [lambda events: rec.events.extend(events)]
svc.start(tick_limit=70)
svc.abort()
c = Counter(e.event_type for e in rec.events)
total = sum(c.values())
share = c.get("cooperation_event", 0) / max(1, total)
modes = Counter(getattr(e, "payload", {}).get("to_mode") for e in rec.events if e.event_type == "GovernorModeChanged")
print("RESULT pin=%s invariant=%d | coop=%d total=%d share=%.4f (<0.5: %s) | deliberate resolve_attack=%d | combat_initiated=%d | GovernorModeChanged=%s" % (
    PIN, c.get("InvariantViolation", 0), c.get("cooperation_event", 0), total, share, share < 0.5,
    deliberate["resolve_attack"], c.get("combat_initiated", 0), dict(modes)))

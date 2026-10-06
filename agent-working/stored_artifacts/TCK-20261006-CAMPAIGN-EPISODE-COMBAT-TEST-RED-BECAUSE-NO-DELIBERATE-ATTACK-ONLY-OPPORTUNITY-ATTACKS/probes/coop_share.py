"""The non-combat assertions of the campaign event-stream test, evaluated without the combat assertion that hides them.

usage: coop_share.py <root>   (cwd is set to <root>; content seeds from the cwd-relative data/content)"""
import os
import sys
from collections import Counter

ROOT = sys.argv[1]
os.chdir(ROOT)
sys.path.insert(0, ROOT)
import src  # noqa: E402

assert src.__file__.startswith(ROOT), (src.__file__, ROOT)
from src.domains.campaigns.orchestrator import CampaignOrchestrator  # noqa: E402
from src.engine.scenario_runtime import ScenarioRuntimeService  # noqa: E402
from tests.integration.campaigns.test_catalog_entity_spawn_wiring import (  # noqa: E402
    _campaign_life_arc_shaped_manifest, _CollectingRecorder)

rec = _CollectingRecorder()
orch = CampaignOrchestrator(_campaign_life_arc_shaped_manifest(tick_limit=70))
spec = orch._manifest.episodes[0]
svc = ScenarioRuntimeService(spec, initial_state=orch._build_initial_state(42, spec), scenario_event_recorder=None)
svc._kernel = svc._build_kernel()
svc._kernel._event_listeners = [lambda events: rec.events.extend(events)]
svc.start(tick_limit=70)
svc.abort()
c = Counter(e.event_type for e in rec.events)
total = sum(c.values())
share = c.get("cooperation_event", 0) / max(1, total)
print("RESULT invariant=%d combat_initiated=%d coop=%d total=%d share=%.3f (<0.5 required: %s)" % (
    c.get("InvariantViolation", 0), c.get("combat_initiated", 0), c.get("cooperation_event", 0), total, share, share < 0.5))

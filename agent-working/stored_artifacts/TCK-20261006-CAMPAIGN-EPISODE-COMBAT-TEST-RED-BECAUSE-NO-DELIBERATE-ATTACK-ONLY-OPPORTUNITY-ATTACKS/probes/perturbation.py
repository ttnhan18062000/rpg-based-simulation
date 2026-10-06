"""Does the test's instrumentation perturb the pinned episode?  Runs the pinned-NORMAL episode with and without `_instrument`
(same governor, same manifest, same seed) and compares the full event-type Counters.

usage: perturbation.py <root>   (cwd is set to <root>; content seeds from the cwd-relative data/content)"""
import os
import sys
from collections import Counter

ROOT = sys.argv[1]
os.chdir(ROOT)
sys.path.insert(0, ROOT)
import pytest  # noqa: E402
import src  # noqa: E402

assert src.__file__.startswith(ROOT), (src.__file__, ROOT)
from src.domains.campaigns.orchestrator import CampaignOrchestrator  # noqa: E402
from src.engine.scenario_runtime import ScenarioRuntimeService  # noqa: E402
import tests.integration.campaigns.test_catalog_entity_spawn_wiring as T  # noqa: E402


def run(instrumented):
    rec = T._CollectingRecorder()
    counts = T._Counts()
    with pytest.MonkeyPatch.context() as mp:
        if instrumented:
            T._instrument(mp, counts)
        orch = CampaignOrchestrator(T._campaign_life_arc_shaped_manifest(tick_limit=T._EPISODE_TICKS))
        spec = orch._manifest.episodes[0]
        svc = ScenarioRuntimeService(spec, initial_state=orch._build_initial_state(42, spec), scenario_event_recorder=None,
                                     governor=T._PinnedNormalGovernor())
        svc._kernel = svc._build_kernel()
        svc._kernel._event_listeners = [lambda events: rec.events.extend(events)]
        svc.start(tick_limit=T._EPISODE_TICKS)
        svc.abort()
    return Counter(e.event_type for e in rec.events), counts


runs = {"instrumented #1": run(True), "plain #1": run(False), "instrumented #2": run(True), "plain #2": run(False)}
base = runs["plain #1"][0]
for name, (c, counts) in runs.items():
    diff = {k: (base.get(k, 0), c.get(k, 0)) for k in set(base) | set(c) if base.get(k, 0) != c.get(k, 0)}
    print("%-16s total=%d types=%d equal-to-plain#1=%s%s" % (name, sum(c.values()), len(c), c == base, (" DIFF=%s" % diff) if diff else ""))
print("PLAIN#1 COUNTER", dict(sorted(base.items())))
c1 = runs["instrumented #1"][1]
print("INSTRUMENTED COUNTS", c1)

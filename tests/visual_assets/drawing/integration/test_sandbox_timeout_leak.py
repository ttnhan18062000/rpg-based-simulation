"""A timed-out Aseprite job must leave no sandbox process behind, however early the timeout lands (needs Aseprite + bwrap).

`subprocess.run(timeout=)` killed only the outer bwrap; an inner bwrap (the init of the sandbox's PID namespace) could be orphaned
before it armed its parent-death signal, and then outlived the job holding a bind mount of the job directory. A single timeout rarely
hits that window, so this sweeps timeouts from far below setup time to about the whole job and counts survivors that name this test's
own workspace (never the rest of the machine). Against the old `sandbox.py` it leaked in about 1 run in 50.
"""

from __future__ import annotations

import pytest

from tests.visual_assets.drawing import proc_support
from visual_assets.drawing import api, config
from visual_assets.drawing.errors import AdapterError

pytestmark = [pytest.mark.needs_aseprite, pytest.mark.resource_budget_large]  # 7 s idle, 17-43 s under heavy CPU load: over the 60 s default

PX = [{"op": "pixels", "pixels": [{"x": 1, "y": 1, "color": "#ff0000"}]}]
RUNS = 150
SHORTEST, LONGEST = 0.002, 0.12


def test_no_sandbox_process_survives_any_timeout(workspace, monkeypatch):
    revision = api.new_sprite("s", 4, 4, "#00000000")["revision"]
    timed_out = 0
    for i in range(RUNS):
        monkeypatch.setattr(config, "JOB_TIMEOUT_S", SHORTEST + (LONGEST - SHORTEST) * i / (RUNS - 1))
        try:
            revision = api.apply_ops("s", revision, PX)["revision"]  # a run that finishes in time publishes; the next builds on it
        except AdapterError as exc:
            assert "timed out" in str(exc)
            timed_out += 1
    survivors = proc_support.wait_gone(str(workspace))
    detail = "\n".join(proc_support.describe(pid) for pid in survivors)  # read before any assertion can hide it
    assert survivors == [], f"{len(survivors)} sandbox process(es) outlived {timed_out} timeouts of {RUNS} runs:\n{detail}"
    assert timed_out >= 1, f"the sweep never reached the timeout path ({timed_out} of {RUNS} runs timed out)"

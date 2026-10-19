# Plan — TCK-20261016-GRIEF-AS-STATE-GRIEF-TRIGGERS-ARE-DETECTED-AND-CARRIED-IN-AUTHORITATIVE-STATE-D80

1. Add `src/core/grief_triggers.py::pending_grief_triggers(state)`: a pure function of typed state (inactive body with `death_record.tick == tick-1`, above the watermark; trust >= ALLY_TRUST_THRESHOLD; urgency `min(1.0, trust*0.8)`).
2. Add `AuthoritativeState.grief_drained_tick` (default -1), written through `StateUpdate.grief_drained_tick_set` in `ApplyPath`; left out of the canonical data and replay fingerprint while -1.
3. Kernel: `_phase_resolution` and the teardown flush read `pending_grief_triggers`; delete `_pending_grief_triggers` and `EventExtractor.detect_grief_triggers`.
4. Docs: divergence 2.134, parity SOC-277, Bible ch04 Path 2. Tests restated; add resume-once and observability OFF==ON.
5. Proof: projected-digest comparison vs base f06ae95c3 on 3 worlds x 5 seeds x 5000t, plus a forced ally-death scenario because no natural world forms allies.

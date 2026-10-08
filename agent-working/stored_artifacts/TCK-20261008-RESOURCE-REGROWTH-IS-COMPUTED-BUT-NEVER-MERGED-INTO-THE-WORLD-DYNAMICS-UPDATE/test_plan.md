---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261008-RESOURCE-REGROWTH-IS-COMPUTED-BUT-NEVER-MERGED-INTO-THE-WORLD-DYNAMICS-UPDATE
artifact_type: test_plan
tags: [ecology, economy, resource]
---

# Test plan
New: `tests/unit/world/test_resource_regrowth_wiring.py` (refined update carries regen and the recovered event; a non-depleted node regrows without the event; no regen off the interval, static node, or cooldown; a depleted node gains a charge through a real Kernel run). Existing: `tests/unit/world/test_resource_ecology.py` (service level), unchanged.

## Proof Plan
- **Level**: unit (refine step), a real Kernel run on a one-node state, and a five-seed corpus before and after on three worlds.
- **Proof kind**: regression tests that fail without the fix (3 of 4 checked by reverting the one-line change); before and after measurement reported, not tuned.
- **Oracle source**: Bible 03 section 3.1 (regen every ECOLOGY_INTERVAL, RESOURCE_RECOVERED on first recovery), parity entry TOWN-137.
- **Expected effect**: a depleted regen node gains charges and the recovered event fires through the tick path; charges harvested rise because nodes refill; alive counts and deaths stay within about 1 SD.
- **Selected commands**: `pytest tests/unit/world/test_resource_regrowth_wiring.py tests/unit/world/test_resource_ecology.py`; the scoped run `pytest tests/unit/world tests/unit/resource tests/unit/engine tests/unit/systems tests/unit/core tests/unit/tools tests/unit/strategic tests/unit/worldassembly tests/unit/worldbuilding tests/integration -m "not slow"`; `probes/job2.sh <arm> <rep> <world> <seed>` over the lines of `probes/jobs2.txt`.

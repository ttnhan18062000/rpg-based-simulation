---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261031-SDLC-HAND-PATH-OFFICIAL-AND-BASELINES-FROZEN
artifact_type: test_plan
tags: [ai, governance, delivery]
---

# Test plan

- Unit: `tests/tools/test_path_reason_and_phase_coverage.py` (validator: missing and empty note for both reasons; no note needed for the rest; every reason validates with a note; old row passes the shard check; CLI: `owner_directed` with a note is written, with none or blank is refused and nothing is written).
- Regression: `tests/tools/test_record_hand_orchestrated_closure.py`, `tests/tools/test_record_run.py`, `tests/agent_orchestration`, `tests/docs`.
- Full `tests/tools` in a lead slot before the push.

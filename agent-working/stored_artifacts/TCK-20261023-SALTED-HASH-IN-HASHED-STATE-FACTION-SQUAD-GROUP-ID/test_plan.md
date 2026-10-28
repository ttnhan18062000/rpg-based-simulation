---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261023-SALTED-HASH-IN-HASHED-STATE-FACTION-SQUAD-GROUP-ID
artifact_type: test_plan
tags: []
---

# Test plan

Unit: digest stability and distinctness; cross-PYTHONHASHSEED subprocess test on a hand-built WAR state (equal group id, equal canonical hash); perception filter id for a non-int signal id is equal across two hash seeds. Existing military-conflict, groups and perception tests stay green. Host-gated: `paired --neutral` on the 3 gate worlds (IDENTICAL expected).

## Proof Plan
- **Level**: unit plus cross-process (subprocess) tests; a gate-world run is pending (owner condition).
- **Proof kind**: determinism across processes. The same constructed state under PYTHONHASHSEED 0 and 1, two processes each, gives an equal squad group_id and an equal canonical state hash.
- **Oracle source**: `stable_int31(region, attacker, tick)` computed in the same process, plus a sensitivity check showing the old salted formula differs across hash seeds.
- **Expected effect**: no change on a world where no squad forms. A world that forms one gets different (now stable) group ids and its final hash moves (divergence 2.141).
- **Selected commands**: `pytest tests/unit/core/test_stable_hash.py tests/unit/domains/faction/ tests/unit/domains/perception/ tests/unit/social/test_groups.py tests/unit/social/test_group_lifecycle_fields.py tests/integration/scenarios/test_faction_campaign.py` (214 passed). Run 2026-10-27: `probe_a0.py` on the 3 gate worlds x seeds 43-46 x 5000 ticks (no WAR pair, no squad in 12 of 12) and `paired --neutral` on the gate worlds (IDENTICAL, PASS).

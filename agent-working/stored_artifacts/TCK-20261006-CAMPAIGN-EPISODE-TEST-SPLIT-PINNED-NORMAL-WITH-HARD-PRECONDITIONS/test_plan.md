---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261006-CAMPAIGN-EPISODE-TEST-SPLIT-PINNED-NORMAL-WITH-HARD-PRECONDITIONS
artifact_type: test_plan
tags: [engine, combat]
---

# Test plan

- Slow, over one episode run: invariant (green), cooperation share (strict xfail), deliberate attacks (strict xfail); the fixture's preconditions fail hard.
- Non-slow controls: router ATTACK dispatch counted; a decision that attacks counted with K >= 1; entry points restored; exactly one SKILL writer in `tactical.py`.
- Mutations of the instrument (offensive kinds emptied; perception count forced to 0; router wrapper removed) fail 2, 1 and 1 controls respectively.

## Proof Plan

- Level: integration (the real campaign episode) plus unit-level instrument controls.
- Proof kind: regression with strict xfails and positive controls.
- Oracle source: test-architecture-reviewer's ruling on `TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS` and the original thresholds (0.5 and 3).
- Expected effect: the invariant test passes; the share and attack tests xfail; a future fix that makes either condition true turns the strict xfail into a loud failure to flip.
- Selected commands: `pytest tests/integration/campaigns/test_catalog_entity_spawn_wiring.py -m slow --resource-budget large`; `pytest ... -m "not slow"`.

---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261006-CAMPAIGN-EPISODE-TEST-SPLIT-PINNED-NORMAL-WITH-HARD-PRECONDITIONS
artifact_type: investigation
tags: [engine, combat]
---

# Investigation

The evidence is in `agent-working/stored_artifacts/TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS/` (`investigation.md` and `probes/`): the bisect to `bc00caa1a` (#175), the file-group experiment that isolates the worker-utilization sentinel, the action and decision traces, the discriminator and the seed grid. This ticket adds two checks made while building:

- The instrumented run reproduces the uninstrumented measurements exactly (cooperation 926 of 1645, 0.5629), so the counting wrappers and the K computation do not perturb the run.
- K from the public perception API is 11, equal to the frame-based count from the discriminator probe, so the two definitions of "perceived" agree on this episode.
- A DEGRADED pin gives cooperation 1091 of 1872 (0.5828) and `combat_initiated` 1, so the pin takes effect.
- Every production call site of the wrapped entry points reaches them through the class attribute at call time: `ActionRouter.execute_action` at `domain_logic.py:54` and `intent/action_intent.py:298`; `TacticalDecisionSystem.evaluate_entity_intent` has one production caller, `engine/domain/cognition.py:76`, which calls it through the class. `resolve_attack` was not used as the instrument because SKILL and AOE_ATTACK never reach it and `resolve_opportunity_attack` is a second caller.

## Perturbation check (review item B1)

`probes/perturbation.py` (in the campaign ticket's artifacts) runs the pinned-NORMAL episode with and without `_instrument`, twice each, and compares the full event-type Counters: instrumented #1, plain #1, instrumented #2, plain #2 are all equal (21 event types, 1645 events, `cooperation_event` 926, `gold_sink_fired` 359, `hazard_drain_applied` 132, ...). The instrumented run's own counts: ticks 70, route calls 70, decisions 250, decisions with a hostile perceived 11, attempts 0, dispatches 0 of 0. The stream's 8 `action_executed` events are an agency bookkeeping event emitted from `last_routing_family` property updates (`observability/event_shapers.py`), not router dispatches, so they are not an action path that bypasses `ActionRouter.execute_action`.

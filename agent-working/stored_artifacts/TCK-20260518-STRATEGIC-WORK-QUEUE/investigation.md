---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260518-STRATEGIC-WORK-QUEUE
artifact_type: investigation
tags: [strategic, work, queue]
---

# Investigation: StrategicWorkQueue

`StrategicWorkQueue` narrows candidate entities for strategic intelligence evaluation each tick to avoid O(N) evaluation across all entities when only a few require immediate strategic cognition.

Priority tiers:
1. Failed action/path: `entity.navigation.wait_count >= 5`, `entity.navigation.oscillation_count >= 3`, or unaccepted latest intent results.
2. Unresolved blockers: `any(not b.resolved for b in entity.strategic.blockers.values())`.
3. Active project transition: `curr_id` project is completed/failed/abandoned or active objective is resolved/failed/missing.
4. Biological emergency: hunger > 80, energy < 20, or thirst > 80.
5. Contract expiration: accepted contract expiring within 100 ticks.
6. Dirty strategic entities: `e_id in dirty.strategic_entities`.
7. Background sweep sample: round-robin starvation prevention sorted by `((e_id + state.tick) % 100, e_id)`.

When `update.force_full_scan` is True or `dirty` is None, return all active/alive entities without narrowing.

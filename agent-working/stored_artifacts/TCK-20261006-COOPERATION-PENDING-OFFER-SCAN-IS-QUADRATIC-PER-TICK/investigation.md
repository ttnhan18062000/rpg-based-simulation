---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261006-COOPERATION-PENDING-OFFER-SCAN-IS-QUADRATIC-PER-TICK
artifact_type: investigation
tags: [performance, cooperation, regression]
---

# Investigation

- Cause (read from code and the bench): `find_pending_incoming_offer` iterated `sorted(state.entities.keys())` and every offerer's contracts for every entity on every tick, including entities with no help need (`CooperationPhase.execute`), so one tick is O(N^2 log N). `select` called it a second time for each evaluated entity.
- Safe to index once per tick: `CooperationPhase.execute` only appends to entity timelines inside the loop; every contract change is written into `new_entity_updates` and returned. `ContractService.accept_contract` returns a `StrategicUpdate` and mutates nothing.
- Measurements are in the ticket's Test Summary. On `d135dd6be`, this box: 34.0 s per tick, cooperation 10,246 ms, `combat_engagement` 15,823 ms, collection 2,761 ms; test-architecture-reviewer's box: 17.2 s, cooperation 10,846 ms, `combat_engagement` 3,226 ms, collection 1,391 ms. Cooperation matches across boxes, `combat_engagement` differs about 5x on identical code; unexplained, handed to Lane B's ticket.
- Probes (scratchpad, not committed): `coop_hash.py` (canonical hash every 100 ticks plus decision counts), `runcoop.sh`, and the reviewer's `bench.py`.

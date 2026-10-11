---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261009-A-STARVATION-DEATH-RECORDS-THE-WAYS-IN-REACH-AND-THE-WAYS-TRIED-M0-GATE-H6
artifact_type: test_plan
tags: []
---

# Test plan
- Normal flow: a starving subject (hunger past the line, no meal) dies on a staged state; exactly one `StarvationDeathRecord` is emitted on the fatal tick, with the typed cause tick and kind.
- A death with an untried in-reach way: an inn in range, the subject never EATs; the record lists INN_MEAL in `ways_open_in_reach`, empty `ways_attempted`; the H6 query flags it.
- A death with every way tried: the subject attempted each open way (accepted or rejected transfer); the H6 query does not flag it.
- A diet-restricted kind: only the ways its diet allows appear (a plant-eater lists no INN_MEAL if its diet gate excludes it once D44 lands; today a kind with no inn in range lists FORAGE only).
- Column (a) == (b) today: a test pins equality on the true-map world and documents that it diverges only when perception lands.
- Determinism: two runs of the same seed give byte-identical records; the record serialises (to_dict round trip).
- Observational: running with and without the extractor gives identical state hashes (no behaviour change).
- Not a starvation death (combat, hazard): no record.
- Channel liveness: observability OFF or a missing record path reads as channel-not-live (no-data, reason harness_error), never as zero violations; a normal run has the header and records == starvation_deaths_seen.
- Pinned run: a 1500-tick pinned run on the three worlds records every STARVATION death exactly once (count equals the deaths by `passive_death_cause`).

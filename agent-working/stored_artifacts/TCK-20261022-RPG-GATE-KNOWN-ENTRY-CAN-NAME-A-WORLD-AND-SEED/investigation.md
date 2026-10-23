---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261022-RPG-GATE-KNOWN-ENTRY-CAN-NAME-A-WORLD-AND-SEED
artifact_type: investigation
tags: [testing, regression]
---

# Investigation

- Matching is by string in `owner_of` for the slow registry; the gate registry's V3 rows are run rows with group `*`, so only a finding-aware matcher can name a (world, seed).
- V3 examples carry `entity_id` (`rpg_gate_metrics._check_untried_way`); the module caps examples at 5, so `violations == len(examples)` is the verifiability test. V3 has no pooled row (only V7 is pooled validity).
- `_missing_required` and `rebaseline` look entries up by string/match; scoped entries must not own a missing row, and rebaseline needs the ticket to tell two `V3` entries apart.
- Ids: the registry note and `v1_disclosure.md` M5 name urban_political/44 merchant 28 t3140, crowded_frontier/46 raider 38 t3778, frontier_living_world/44 worker 2 t3736. Confirmation against run 39799337778's docs artifacts was blocked: the artifact blob host fails with a TLS handshake timeout from this host (two attempts); rpg-planner is asked to confirm.

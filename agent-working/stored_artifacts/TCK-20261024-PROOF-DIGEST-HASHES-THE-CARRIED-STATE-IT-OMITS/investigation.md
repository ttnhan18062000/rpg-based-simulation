---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261024-PROOF-DIGEST-HASHES-THE-CARRIED-STATE-IT-OMITS
date: 2026-10-27
tags: [performance, determinism]
---

# Investigation

- The six state fields are carried by `ApplyPath.apply_generation` (`src/engine/apply.py`) and were absent from `CanonicalStateHasher.to_canonical_data`; `last_hit_tick` was excluded on purpose by HUNGER step B (ruling (ii)).
- Canonical forms: factions, clans and information providers have `to_canonical_dict`; `ItemInstance`, `QuestOpportunity` and `WorldEvent` do not, so a generic `_plain` form (dataclass by field, enum by value, string keys, sequences in order, sets sorted) is used. `recent_world_events` stays an ordered window.
- `paired --neutral` compares start and final hashes, which v3 moves by design; rpg amended condition 2 (option A): report DIFFERENT as printed and compare fates, start, counters and adds from the cached arms.

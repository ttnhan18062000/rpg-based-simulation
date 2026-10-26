---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261023-SALTED-HASH-IN-HASHED-STATE-FACTION-SQUAD-GROUP-ID
artifact_type: investigation
tags: []
---

# Investigation

See the ticket's Implementation Notes, Phase 1 findings (2026-10-26): probe A0 negative on four shipped worlds (no WAR pair, no squad in 5000 ticks, seed 42, PYTHONHASHSEED=0); `group_id` is hashed (sorted by id) and orders `groups.py` updates; `perception/filter.py:88,97` is not wired into production state (latent); only three salted `hash()` calls exist under `src/`.

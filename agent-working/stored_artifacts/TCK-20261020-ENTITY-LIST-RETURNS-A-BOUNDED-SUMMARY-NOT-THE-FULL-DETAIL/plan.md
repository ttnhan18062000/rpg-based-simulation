---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261020-ENTITY-LIST-RETURNS-A-BOUNDED-SUMMARY-NOT-THE-FULL-DETAIL
phase: done
date: 2026-10-20
tags: []
---

# Plan: TCK-20261020-ENTITY-LIST-RETURNS-A-BOUNDED-SUMMARY-NOT-THE-FULL-DETAIL

1. Presenter: `present_entity_summary` (bounded list model: identity, position, vitals, counts); `present_entity` (detail) keeps live quests / unresolved blockers / open contracts in full plus the newest 10 finished quests and 5 closed contracts, with `quests_total`, `blockers_resolved_count`, `contracts_total`; `present_entity_quests` pages the full quest history (status live|terminal|all, newest first, limit capped at 500).
2. Cache: a separate summary cache beside the detail cache, invalidated, evicted and cleared together; the list never builds the detail.
3. API: the list returns summaries; new router `src/api/routes/entities.py` serves `GET /api/v1/entities/{id}/quests`.
4. Tests: ceilings on an aged entity (summary <= 1 KB, detail <= 8 KB at 500 finished records of each kind), exact counts, exact paged history, cache separation, route test; the old item-metadata test now reads items from the detail.
5. Frontend: no change. The InspectPanel Quests tab reads `selected_entity` from `/state?selected=`, which this backend does not serve, and nothing in the frontend calls `/api/v1/entities`.

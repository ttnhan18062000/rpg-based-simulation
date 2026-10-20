---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261020-ENTITY-LIST-RETURNS-A-BOUNDED-SUMMARY-NOT-THE-FULL-DETAIL
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-ENTITY-LIST-RETURNS-A-BOUNDED-SUMMARY-NOT-THE-FULL-DETAIL

## Title
GET /api/v1/entities returns a bounded summary per entity; the full detail moves to the single-entity endpoint with capped history and paged sub-resources

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Platform's SLO run on 2026-10-19 (issue #593, 10-20 comment) found that `GET /api/v1/entities` levels off at about 691.5 KB for 12 entities, about 57 KB per entity, against about 7.4 KB per entity in #627. The payload per entity grows with world age, and the p95 latency alert fired at 50 users. Lane B read the code on 2026-10-20 (/mnt/data/scratch-rpg-implementer-2/entities_payload.md):
- The list route `get_entities_paged` → `ReadModelCache.get_entity_dto` → `StatePresenter.present_entity` returns the FULL detail model for every entity. There is no summary shape; `present_entity_slim` is used only by the WS delta.
- The most likely growth is `quests`. It is built from every QuestState in `strategic.projects` (state_presenter.py:118-128) with no status filter and no cap. Terminal projects are kept as records for the entity's lifetime (strategic.py:336-361).
- Further suspects: `strategic.blockers` and `strategic.contracts`, which have no capacity rule, and item `properties` copied into metadata.

## Scope
1. Measure first: per-key byte sizes of one aged entity's DTO, using the probe in section 4 of the finding file, to confirm which fields hold the bytes.
2. List = summary: bounded fields plus counts, with no unbounded arrays. Detail endpoint: live quests plus the newest N terminal ones with `quests_total`; unresolved blockers plus a resolved count; open contracts plus a recent tail; item metadata only in detail.
3. A paged history sub-resource, for example `/entities/{id}/quests?status=&offset=&limit=`.
4. Separate summary and detail DTO caches. Document a per-entity payload ceiling and pin it with a test.
5. Update the frontend InspectPanel Quests tab to use detail and history.

## Out of Scope
- Retiring terminal projects from simulation state. That is a durable-state change that moves the state hash and has its own ticket: TCK-20261020-TERMINAL-PROJECTS-ARE-RECORDS-WITH-NO-RETENTION-BOUND.

## Acceptance Criteria
- The list payload per entity is bounded and independent of world age. A test with an aged entity (many terminal quests) asserts the ceiling.
- Detail and history return everything, paged.
- The tests that pin the current shape are updated with reasons: tests/api/test_live_entity_inspection.py, test_paged_logic.py, tests/unit/api/test_read_model_cache.py, test_read_model_service.py, test_presenter_species_and_size.py, tests/perf/test_api_projection_perf.py.
- The simulation is unchanged (presenter only); the final hash is identical.
- Platform reruns the SLO load and p95 is under 300 ms at 50 users, or the remaining cost is named.

## Related Tickets
- TCK-20261020-TERMINAL-PROJECTS-ARE-RECORDS-WITH-NO-RETENTION-BOUND
- #627, #593 (platform findings)

## Related Docs
- docs/guidelines/design_patterns.md (API presenters)

## Related Stored Artifacts
- /mnt/data/scratch-rpg-implementer-2/entities_payload.md

## Related Code Areas
- src/api routes (get_entities_paged), ReadModelCache, StatePresenter.present_entity / present_entity_slim
- frontend/src/components/InspectPanel.tsx

## Assumptions / Open Questions
- Which field dominates is not measured until step 1.

## Implementation Notes
Presenter or API only, so it can land before or after v1 (no simulation change).

## Test Summary
Measured on an aged-entity fixture (tests/helpers/aged_entity.py), no live run: before, 500 finished quests = +88 KB, 500 resolved blockers = +52 KB, 500 closed contracts = +38 KB, 300 item properties = +15 KB per entity (all uncapped); after, the same aged entity is 4.1 KB as detail and 408 B as a list row. Tests: tests/unit/api/test_entity_read_model_is_bounded.py (11: ceilings at ages 0/10/500, counts, paged history, page ceiling, cache separation), tests/api/test_entity_quest_history_route.py, the updated item-metadata test in test_live_map_terrain_codes_resolve_through_the_manifest.py; tests/unit/api, test_paged_logic, test_api_projection_perf, test_request_duration_histogram, architecture_reviewer_static: 119 passed. mypy gate 0, import_contracts ci 17 kept, code-health 0 new / 0 worse. Platform's SLO rerun (p95 < 300 ms at 50 users) is not run here.

## Files Changed
src/api/presenters/state_presenter.py, src/api/read_model_cache.py, src/api/engine_manager.py, src/api/server.py, src/api/routes/entities.py (new), tests/helpers/aged_entity.py (new), tests/unit/api/test_entity_read_model_is_bounded.py (new), tests/api/test_entity_quest_history_route.py (new), tests/api/test_live_map_terrain_codes_resolve_through_the_manifest.py, docs/observability/read_model_service_contract.md. Frontend: none (the InspectPanel Quests tab reads `selected_entity` from /state?selected=, which this backend does not serve; nothing in the frontend calls /api/v1/entities).

## Completion Summary

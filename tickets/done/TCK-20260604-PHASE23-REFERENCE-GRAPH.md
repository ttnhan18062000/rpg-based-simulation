# TCK-20260604-PHASE23-REFERENCE-GRAPH

## Title
Phase 23 — Global content reference graph and active-data validation

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Upgrade catalog validation to use a generic, global `ContentReferenceGraph` containing all loaded content records and references. Detect "dead active data" that is loaded and marked as active but never referenced/consumed by downstream features.

## Scope
- Implement `ContentReferenceGraph` mapping loaded catalog records as nodes formatted as `family:id`, and references between them as directed edges `source -> target`.
- Expose reverse reference lookup APIs on the graph.
- Implement validator logic that uses the reference graph to verify referential integrity (checking for broken links).
- Implement the "no dead active data" rule, ensuring that any record in `EXISTING-LOGIC`, `LEGACY-EXPORT`, or `REDESIGNED-CORE` states has at least one downstream reference (unless explicitly exempted).
- Ensure warnings/errors output records with details of IDs and families.
- Write tests in `tests/unit/content/test_layered_catalog.py` to cover new rules.

## Out of Scope
- Rewriting compilation logic or simulation runners.

## Acceptance Criteria
- Reference graph includes all loaded content records and references.
- Broken references produce descriptive, family-aware errors.
- Reverse reference lookup is supported.
- Graph validation is fully deterministic.
- Active records with no downstream usage are flagged as warnings/errors.
- Future/design records (`ADDITIONAL`, `FUTURE-EXTENSION`, `DESIGN_ONLY`) are allowed to be unused.
- Errors/warnings include record ID and family.
- Existing tests pass without regression.

## Related Tickets
- TCK-20260604-PHASE22-SCHEMA-NORMALIZATION

## Related Docs
- `world_phase_20_28.md`

## Related Stored Artifacts
- None

## Related Code Areas
- `src/content/`
- `tests/unit/content/`

## Assumptions / Open Questions
- We assume the graph should represent all 35+ content families from the content usage matrix.
- We will define target reference resolution rules dynamically or via static configuration mapping model attributes to family keys.

## Implementation Notes
- Integrated `ContentReferenceGraph` into `CatalogValidator` and resolved dependency errors in sandbox world compile tests by adding engine built-in terrains (grass, floor, hill, sand) as virtual graph nodes.
- Fixed a state pollution bug in cognition unit tests by seeding registries in `test_phase2_knowledge_model_service.py`.
- Fixed the mock compile side-effect signature in `test_lab_budget_guardrails.py` to accept arbitrary arguments.

## Test Summary
- Added `test_phase23_reference_graph_and_dead_active_data` test case to verify `ContentReferenceGraph` nodes, edges, reverse lookups, and dead data validation.
- Verified that all 1940 unit, integration, and assembly tests pass successfully.

## Files Changed
- `src/content/reference_graph.py`
- `tests/unit/content/test_layered_catalog.py`
- `tests/unit/cognition/test_phase2_knowledge_model_service.py`
- `tests/unit/lab/test_lab_budget_guardrails.py`

## Completion Summary
- Successfully implemented Phase 23, including building the directed `ContentReferenceGraph` mapping loaded catalog records, modules, and compositions as nodes and directed reference edges, exposing reverse lookup APIs, and enforcing referential integrity and dead active data validation. All unit tests pass cleanly.

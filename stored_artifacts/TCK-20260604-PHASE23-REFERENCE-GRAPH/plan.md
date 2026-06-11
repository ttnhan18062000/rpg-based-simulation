---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260604-PHASE23-REFERENCE-GRAPH
artifact_type: plan
tags: [phase23, reference, graph]
---

# Implementation Plan: Phase 23 Content Reference Graph & Active Data Validation

## Proposed Changes

### Content Component

#### [NEW] [reference_graph.py](file:///home/vboxuser/Work/rpg-based-simulation/src/content/reference_graph.py)
- Implement `ContentReferenceGraph` building a directed graph from the loaded `CatalogRepository`.
- Extract record identifiers as nodes of format `family_short_name:id`.
- Scan record fields dynamically to find string/list/dict references pointing to other records, adding directed edges `source -> target`.
- Provide helper methods:
  - `has_node(node_id: str) -> bool`
  - `get_incoming_neighbors(node_id: str) -> Set[str]`
  - `get_outgoing_neighbors(node_id: str) -> Set[str]`
  - `is_record_used(node_id: str) -> bool`

#### [MODIFY] [validator.py](file:///home/vboxuser/Work/rpg-based-simulation/src/content/validator.py)
- Integrate `ContentReferenceGraph` into the validation process.
- In `CatalogValidator.validate()`, build the graph.
- Add generic relational validation that checks if all outgoing edges in the graph point to existing nodes. If not, append a `ValidationIssue` (this generically implements references checks, but we will keep the existing manual ones to satisfy old test codes exactly, while adding this new layer).
- Implement the "no dead active data" rule:
  - For every record, check if its family has maturity `EXISTING-LOGIC`, `LEGACY-EXPORT`, or `REDESIGNED-CORE` in `CONTENT_USAGE_MATRIX`.
  - If yes, verify it has at least one incoming reference (unless it is a top-level default/composition/scenario family).
  - If it is unused, raise a Warning or Error (warnings for modules, errors/warnings for archetypes/materials as specified).

### Test Component

#### [MODIFY] [test_layered_catalog.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/content/test_layered_catalog.py)
- Add unit tests verifying `ContentReferenceGraph` generation, deterministic nodes/edges, and reverse reference lookups.
- Add validation tests verifying that:
  - Active unused archetypes raise errors/warnings.
  - Active unused materials raise errors/warnings.
  - Active unused modules raise warnings.
  - Future/design records (`ADDITIONAL`, `FUTURE-EXTENSION`, `DESIGN_ONLY`) are allowed to be unused.
- Assert validation messages contain correct record IDs and families.

## Verification Plan

### Automated Tests
- Run `pytest tests/unit/content/test_catalog.py`
- Run `pytest tests/unit/content/test_layered_catalog.py`
- Run all content, worldassembly, and worldbuilding tests.

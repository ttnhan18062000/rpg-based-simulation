---
status: done
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260628-E43H-NARRATIVE-OBS
phase: done
date: 2026-06-28
tags: [narrative, observability, grief, nemesis, entity-inspector, p3]
---

# TCK-20260628-E43H-NARRATIVE-OBS

## Title
Narrative Modifiers Observability — expose grief urgency and nemesis blockers in EntityInspectionSnapshot

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
GriefUrgencyModifier (E43F) and NemesisRelation (E43G) are injected into the runtime
entity strategic layer (as ConcernState/BlockerState) at episode start. This ticket
surfaces them in a structured, inspectable form via the EntityInspectionSnapshot so
they appear in the observability API.

## Scope
- Add `narrative_modifiers: Dict[str, Any]` field to `EntityInspectionSnapshot`
- Populate it in `EntityInspector.inspect_entity()` by reading
  `entity.strategic.concerns` (grief) and `entity.strategic.blockers` (nemesis)
- Structure: `{"grief_concerns": [...], "nemesis_blockers": [...]}`
- Tests: grief concern extraction, nemesis blocker extraction, empty case

## Out of Scope
- Writing a separate `narrative_modifiers.jsonl` file (data already in entity state)
- CampaignState inspection (no access from EntityInspector)
- Observability mode gating (already in entity state; zero overhead to surface)

## Acceptance Criteria
- [ ] `EntityInspectionSnapshot.narrative_modifiers` contains `grief_concerns` list and `nemesis_blockers` list
- [ ] Grief concerns extracted from concerns with `id.startswith("grief_ally_")` and `kind=SOCIAL_THREAT`
- [ ] Nemesis blockers extracted from blockers with `kind=SOCIAL` and `subject.isdigit()`
- [ ] Empty lists when no grief/nemesis modifiers present
- [ ] Tests pass; existing entity inspector tests unaffected

## Related Tickets
- Parent epic: TCK-20260628-E-NARRATIVE-CONSEQUENCE
- Gate: TCK-20260628-E43F-GRIEF-URGENCY (DONE)
- Gate: TCK-20260628-E43G-NEMESIS-RELATION (DONE)

## Related Docs
- `docs/observability/decision_trace_contract.md`

## Related Code Areas
- `src/observability/live/entity_inspector.py`
- `tests/unit/observability/test_entity_inspector.py`

## Assumptions / Open Questions
- Grief concerns are identified by `concern.id.startswith("grief_ally_")` — deterministic key from GriefUrgencyImporter.
- Nemesis blockers identified by `blocker.kind == BlockerKind.SOCIAL` and `blocker.subject.isdigit()` — deterministic from NemesisRelationImporter.

## Implementation Notes
- Grief concerns identified by `concern.id.startswith("grief_ally_")` + `kind == ConcernKind.SOCIAL_THREAT`; dead_ally_id parsed from key suffix.
- Nemesis blockers identified by `blocker.kind == BlockerKind.SOCIAL` + `blocker.subject.isdigit()`; antagonist_id parsed from subject.
- `_extract_narrative_modifiers()` is a static helper on EntityInspector; wrapped in try/except so any strategic import failure silently returns empty lists.
- No observability mode gate needed — data is already in runtime entity state with zero overhead; cost of reading dict is negligible.

## Test Summary
5 tests in `tests/unit/observability/test_entity_inspector.py` (E43H group):
- empty when no grief/nemesis concerns/blockers
- grief_ally_ concern extracted with dead_ally_id and urgency
- SOCIAL nemesis blocker extracted with antagonist_id and severity
- MATERIAL blocker excluded (not a nemesis signal)
- both grief and nemesis present simultaneously

492 observability tests pass; no regressions.

## Files Changed
- `src/observability/live/entity_inspector.py` — narrative_modifiers field; _extract_narrative_modifiers() static method
- `tests/unit/observability/test_entity_inspector.py` — 5 E43H tests added

## Completion Summary
EntityInspectionSnapshot now surfaces active grief urgency concerns and nemesis blockers in a structured `narrative_modifiers` dict, making the narrative consequence layer fully inspectable via the observability API.


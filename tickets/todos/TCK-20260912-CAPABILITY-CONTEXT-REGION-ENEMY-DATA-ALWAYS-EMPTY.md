---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY
phase: open
date: 2026-09-12
tags: [cognition, self-model]
---

# TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY

## Title
`CapabilityContext.region_data`/`.enemy_data` are read at capability-estimation decision time but
populated by nothing, from any source — an always-empty decision input

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION`'s own
search for a real, concrete consumer that `KnowledgeFact`'s `"danger_rating"` fact type looked
plausibly shaped to feed. That investigation explicitly declined to build any connection between
the two (no design-doc declaration states one should feed the other), but the underlying structural
defect it surfaced along the way stands on its own, independent of `KnowledgeFact` entirely:

`CapabilityContext` (`src/cognition/capability_estimate.py:44-45`) declares two fields explicitly
typed for exactly this shape:
```python
enemy_data: Dict[str, Any] = field(default_factory=dict)     # {enemy_id: {level, danger_rating}}
region_data: Dict[str, Any] = field(default_factory=dict)    # {region_id: {danger_rating}}
```
Both are read at real decision time (`capability_estimate.py:124` — `enemy_info =
context.enemy_data.get(enemy_id, {})`; line 154 — `region_info = context.region_data.get(region_id,
{})`) to scale a capability confidence estimate.

**Confirmed, not assumed, that nothing anywhere populates either field with real content.** Grepped
every real `CapabilityContext` construction site in `src/`:
- `src/domains/adventure/scoring.py:394` — constructs `CapabilityContext(gather_resources=...,
  resource_data=...)`, a *different* field pair (`gather_resources`/`resource_data`), never
  `region_data`/`enemy_data`.
- `src/domains/adventure/scoring.py:416` — constructs with `craft_recipes`/`recipe_data`, same
  pattern, different fields again.
- `src/engine/tactical.py:405` — `CapabilityContext.for_combat(enemy_ids=[h.kind])`.
  `for_combat()`'s own signature accepts an optional `enemy_data` parameter, but this real call
  site never passes it, so it defaults to `{}`.

No other real construction site exists. `context.enemy_data.get(enemy_id, {})` and
`context.region_data.get(region_id, {})` therefore always return `{}` in every real code path,
meaning every real capability-confidence estimate that consults enemy- or region-level danger
scaling consults an empty dict, every time, regardless of what the entity has actually encountered,
learned, or observed about that enemy or region.

## Scope
- Confirm the above (already directly grepped, but re-verify as this ticket's own first step —
  standard practice for this whole audit arc, do not trust the citing ticket's own claim as final).
- Determine what a real, non-empty value for `enemy_data`/`region_data` should look like and where
  it should come from — this is explicitly **not** predetermined by this ticket. The shape-match to
  `KnowledgeFact`'s `"danger_rating"` fact type is a real observation worth investigating as one
  candidate source, but it is **unproven** — no design doc declares that correspondence, and
  `KnowledgeFact`'s own write side is itself confirmed inert in real gameplay today (see the parent
  investigation). Real candidate sources to weigh, not to assume: direct combat-history tracking
  (an entity's own record of enemies/regions it has actually fought), `KnowledgeFact` (if and when
  its own write-side gaps are separately resolved), some other existing per-entity memory, or a
  determination that these fields are speculative/unfinished and should be removed rather than
  populated.
- If a real source is chosen: wire it in, with real test coverage proving a populated dict
  measurably changes a real capability-confidence estimate.
- If no real source is judged worth building (e.g., genuinely no current gameplay need): document
  the fields as speculative/unfinished directly in `docs/cognition/capability_and_knowledge_
  contract.md`, and consider whether removing them (dead-but-not-yet-diagnosed) is more honest than
  leaving typed-but-always-empty fields in place — a real disposition decision, not automatic.

## Out of Scope
- Building any connection from `KnowledgeFact` specifically into these fields — that correspondence
  is explicitly unproven and undeclared; treating it as the answer here would be inventing gameplay
  design, not completing a declared one. If a future ticket determines `KnowledgeFact` should be
  the source, that is a separate, real design decision requiring its own declared intent, not an
  automatic consequence of this ticket closing.
- `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION`'s own disposition
  (documented as inert-and-not-built) — independent of whatever this ticket decides.
- `resource_data`/`recipe_data` (the two OTHER `CapabilityContext` fields, confirmed real and
  populated at their own real call sites) — not reopened here.

## Acceptance Criteria
- [ ] Re-verified: `region_data`/`enemy_data` are confirmed empty at every real call site, with a
      fresh grep, not inherited from this ticket's own citation.
- [ ] A real, evidence-based determination of what should populate these fields (or that nothing
      should, and the fields should be removed/marked speculative) — not assumed or guessed.
- [ ] If a source is chosen: wired with real test coverage proving a populated value measurably
      changes a real capability estimate output.
- [ ] If no source is chosen: `docs/cognition/capability_and_knowledge_contract.md` updated to
      state these fields are currently unpopulated by design/oversight (whichever the
      determination finds), closing the ambiguity for future readers.
- [ ] No regression in `tests/unit/cognition/`, `tests/unit/domains/adventure/`,
      `tests/unit/engine/test_tactical*` (or equivalent).

## Related Tickets
- `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION` (done — origin of this
  finding, found while searching for a real consumer for `KnowledgeFact`'s `danger_rating` fact
  type; explicitly declined to build that connection, filing this as its own independent finding
  instead)

## Related Docs
- `docs/cognition/capability_and_knowledge_contract.md` (the contract this ticket's disposition may
  need to update)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/cognition/capability_estimate.py` (`CapabilityContext`, `CapabilityEstimateService.estimate()`)
- `src/domains/adventure/scoring.py` (real construction sites, for the `resource_data`/`recipe_data`
  pattern this ticket's own fix should likely mirror if a source is chosen)
- `src/engine/tactical.py` (`CapabilityContext.for_combat()`'s own real call site)
- `src/core/self_model.py` (`KnowledgeFact`, the unproven candidate source named in Scope)

## Assumptions / Open Questions
- What should populate `region_data`/`enemy_data` — or whether nothing should — is the central,
  deliberately-unresolved question this ticket exists to answer. The `KnowledgeFact` shape-match is
  recorded as a real observation, explicitly marked unproven, not a predetermined answer.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_

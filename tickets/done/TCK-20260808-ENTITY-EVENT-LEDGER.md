---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260808-ENTITY-EVENT-LEDGER
phase: done
date: 2026-08-08
tags: [observability, world]
---

# TCK-20260808-ENTITY-EVENT-LEDGER

## Title
Build a parity-ledger-style catalog of every entity-level state-mutation type the engine's own
durable-state model defines — not just the ones currently emitted as observability events — to
find silent (unobserved) entity mutations. First phase of a broader eventual all-layers event
catalog, scoped to entity (the lowest, most central lifecycle layer) only.

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
A 2026-08-08 status discussion identified a real gap: `docs/simulation_quality/event_type_coverage.md`
documents every event_type that IS observed/scored by SimQ, but nothing enumerates every event
type that COULD exist based on the engine's own logic — `ObservabilityEventEnvelope.event_type`
(`src/observability/events.py`) is a bare `str`, not a fixed enum, and event strings are scattered
across many emission call sites (`event_extractor.py`, shapers) with no single canonical registry
of "every significant thing that can happen," independent of whether anyone bothered to emit +
observe it. This means a real state mutation could exist in engine logic with zero corresponding
observability event, and there is currently no way to discover that gap — it would only surface
by accident (the way this session found `event_extractor.py`'s hazard/combat misclassification bug
via a raw-event manual pull, not a systematic audit).

The fix, mirroring `docs/parity_ledger/`'s own proven pattern (id/text/status/evidence/test_path,
`verified`/`divergent`/`missing`/`unsupported` statuses) but for event coverage instead of
mechanics parity: enumerate every mutation type from the engine's own **authoritative durable-state
update model** (`src/core/updates.py` — `EntityUpdate` and its ~16 composed sub-update dataclasses:
`EquipmentUpdate`, `InteractionUpdate`, `CombatIntent`, `CombatUpdate`, `NavigationUpdate`,
`TaskUpdate`, `IdentityUpdate`, `SocialBondUpdate`, `SocialUpdate`, `BiologicalUpdate`,
`AttributeUpdate`, `LifecycleUpdate`, `RewardUpdate`, `StrategicUpdate`, `StaminaUpdate`,
`WoundUpdate`) — this is CLAUDE.md's own Durable State Rule in action: every durable entity change
already goes through a typed update record, which makes this catalog's source of truth real and
exhaustive rather than a best-effort code search. Cross-reference each mutation type/field against
actual observability-event emission to classify: `observed` (an event reliably fires),
`silent` (no corresponding event exists at all), or `partial` (an event exists but doesn't capture
every field/case of the mutation — e.g. this session's own confirmed finding that hazard-drain and
real combat damage were both routed through the same `combat_damage` event before the 2026-08-06
fix, a `partial`/misattributed case, not a `silent` one).

**Scoped to entity layer only** (per this ticket's own framing: "center and lowest lifecycle
layer") — region/faction/world-layer event catalogs are explicitly future work, not this ticket's
scope, to keep this tractable and let the entity-layer pass establish the methodology before
scaling it.

## Scope
1. **Investigate**:
   - Enumerate every field across `EntityUpdate` and its 16 composed sub-update dataclasses
     (`src/core/updates.py`) that represents a real state mutation (exclude pure bookkeeping
     fields like IDs/timestamps that carry no independent "something happened" meaning — this
     judgment call must be explicit and defensible per mutation, not silently applied).
   - For each mutation type, trace whether `event_extractor.py`/the shaper registry
     (`src/observability/event_shapers.py`) currently emits a corresponding
     `ObservabilityEventEnvelope` — cite exact function/line, not "probably."
   - Classify each as `observed`/`silent`/`partial`, with real evidence for each classification
     (a `partial` classification specifically needs the exact ambiguity/misattribution it has,
     not just "seems incomplete").
2. **Plan**: ledger file schema, mirroring `docs/parity_ledger/schema.json`'s shape but adapted
   for event coverage (id, mutation source: `dataclass.field`, status enum:
   `observed`/`silent`/`partial`, evidence: the tracing citation, corresponding `event_type` string
   if one exists, `test_path` if a test verifies the emission). Likely location:
   `docs/event_ledger/entity.yaml`, sibling in spirit to `docs/parity_ledger/`.
3. **Implement**: produce the ledger for the full entity-layer mutation set found in Investigate.
   For any `silent` mutations found, do NOT wire new event emission in this same ticket (that is
   real behavior-adjacent work requiring its own scoping/testing) — file each `silent` finding as
   its own small follow-up ticket instead, per this session's own established discipline against
   silently expanding scope mid-ticket.
4. Add a lightweight validation check (script or pytest) confirming the ledger's own entries still
   cite real, currently-existing dataclass fields and function references — so the ledger doesn't
   quietly go stale the way `corpus_tier_taxonomy.md`'s gap-list section did (found stale twice,
   2026-08-05).

## Out of Scope
- Region/faction/world-layer event catalogs — explicitly future phases, not this ticket.
- Actually wiring new observability events for any `silent` mutation found — filed as follow-up
  tickets instead (see Scope item 3).
- Re-litigating or duplicating `docs/simulation_quality/event_type_coverage.md`'s own scope (that
  doc covers SimQ-*scored* events specifically; this ledger covers ALL entity mutations whether or
  not SimQ scores them) — cross-reference, don't merge.

## Acceptance Criteria
- [x] investigation.md enumerates every entity-mutation-representing field across `EntityUpdate`'s
      20 fields (found 2 existing exhaustive source docs, `update_intents.md`/
      `event_type_coverage.md`, that already did most of the enumeration — reused rather than
      re-derived), with an explicit, defensible in/out judgment call per field
- [x] Each mutation classified `observed`/`silent`/`partial` with real tracing evidence
      (double-verified: intent-field-name AND real state-field-name grep for every candidate)
- [x] `docs/event_ledger/entity.yaml` produced, schema mirroring `docs/parity_ledger/schema.json`'s
      discipline
- [x] Every `silent` finding filed as its own follow-up ticket — 4 tickets, grouped by theme
      (vitals/attributes/equipment/identity-role-faction) rather than 6 tiny 1:1 tickets, disclosed
      as a grouping choice
- [x] A staleness-guard validation check exists (`tests/tools/test_entity_event_ledger.py`)
- [x] Scoped pytest passes

## Related Tickets
- TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX (the real, confirmed `partial`
  case this ticket's own framing cites — DONE)
- TCK-20260630-SIMQ-TRANSLATE (built `docs/simulation_quality/event_type_coverage.md`, the
  SimQ-scored-only precedent this ledger is broader than — DONE)

## Related Docs
- `docs/parity_ledger/schema.json` (schema-shape precedent)
- `docs/simulation_quality/event_type_coverage.md` (the narrower, SimQ-scored-only sibling doc)
- `docs/guides/observability.md` "Adding a new event type" section

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/core/updates.py` (`EntityUpdate` and its 16 composed sub-update dataclasses — the
  authoritative source of truth)
- `src/observability/event_extractor.py`, `src/observability/event_shapers.py` (emission tracing
  targets)
- `src/observability/events.py` (`ObservabilityEventEnvelope`, `EventCategory`)

## Assumptions / Open Questions
- Where exactly to draw the "carries independent meaning" line for excluding pure bookkeeping
  fields — not assumed; Investigate must make and justify this call per field, not apply a single
  blanket heuristic that could hide real gaps.
- Whether some `EntityUpdate` sub-dataclasses (e.g. `StrategicUpdate`) blur into cognition/AI
  rather than pure "entity lifecycle" — not assumed; Investigate should note any such boundary
  case explicitly rather than silently including or excluding it.

## Implementation Notes
Subagent spawn cap (200/200) reached earlier this session — Investigate/Implement/Verify performed
directly.

`mcp__knowledge-search__search_docs` surfaced `docs/core/update_intents.md` — an already-existing,
exhaustive, maintained enumeration of all 20 `EntityUpdate` fields — before any manual field-by-field
reading of `src/core/updates.py` was needed. Combined with `docs/simulation_quality/event_type_coverage.md`'s
own exhaustive event catalog (~95 entries), most of this ticket's own "enumerate everything" work
turned out to already exist; the real, new contribution was cross-referencing the two against each
other to find genuinely uncovered mutation types.

Caught and corrected my own initial grep methodology mid-investigation: `event_extractor.py`
performs post-tick STATE diffing, not intent-object reading (confirmed via this session's own
earlier COMBAT investigation finding the same architecture) — an initial grep for intent-dataclass
field names would have under-verified real coverage (e.g. `NavigationUpdate`'s own field name never
appears in `event_extractor.py`, yet `entity.navigation.position` IS read and observed via the
`movement` event). Re-verified every silent candidate against real `EntityState` component field
names before concluding silence, catching this before it produced a false "silent" classification.

Found 6 confirmed-silent mutation types (attributes, biological, equipment, stamina, wounds, task)
and 5 partial ones (navigation, identity, social, lifecycle, interaction) — double-verified via
grep for both intent-field and state-field names, zero matches for every silent classification.
Filed 4 grouped follow-up tickets rather than fixing any of them inline, per this ticket's own
explicit Out of Scope.

## Test Summary
`tests/tools/test_entity_event_ledger.py` (new): 3 passed — mutation-source field validity (guards
against a stale/renamed `EntityUpdate` field reference), evidence-citation file existence, and full
field-coverage (every real `EntityUpdate` dataclass field has a ledger entry, catching future drift
if a new field is added without a corresponding ledger update).

## Files Changed
- `docs/event_ledger/entity.yaml` (new, 20 entries)
- `tests/tools/test_entity_event_ledger.py` (new)
- `docs/simulation_quality/event_type_coverage.md` (cross-reference pointer)
- `tickets/todos/TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP.md`,
  `TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP.md`,
  `TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP.md`,
  `TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP.md` (new, filed not started)

## Completion Summary
Found and reused 2 already-existing, exhaustive source-of-truth docs rather than re-deriving their
own enumeration work from scratch — the real, new value this ticket added was the cross-reference
between them, which neither existing doc did on its own. Caught a real methodology mistake
(intent-field vs. state-field grep) before it produced a false classification, using this session's
own earlier COMBAT investigation finding as the clue. Filed 6 real, double-verified silent-coverage
findings as 4 grouped follow-up tickets rather than fixing any inline. Fifth and final ticket in
this batch.

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
BLOCKED — **not built, 2026-09-13.** Checked for a real, live belief source before writing any
code, per instruction. Found none exists in any real run today — see Completion Summary for the
two independent blocked chains. Wiring either source now would produce code that is correct and
never fires, the exact pattern this ticket exists to close; declining to add a fresh instance of it
rather than shipping one.

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
- [x] Re-verified: `region_data`/`enemy_data` are confirmed empty at every real call site, with a
      fresh grep, not inherited from this ticket's own citation. Also re-confirmed `travel_regions`
      still has zero production construction sites — the region half needs its own caller
      regardless of which belief source is chosen for `enemy_data`.
- [x] **A real, evidence-based determination made, but not the kind originally anticipated**: the
      two live-code candidate belief sources are both currently unreachable in real runs (see
      Completion Summary for the two independent blocked chains) — not "what should populate
      these fields" but "nothing can populate them yet, and here's exactly why."
- [ ] Not attempted: wiring either source now, per the disposition above — would produce code that
      compiles and never fires.
- [ ] Not attempted: the speculative/unfinished documentation path — premature while a real source
      is genuinely on a clean path to existing once the two blocking tickets resolve; marking the
      fields as speculative now would misdescribe the actual disposition (blocked, not abandoned).
- [ ] No regression — N/A, no code changed.

## Related Tickets
- `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION` (done — origin of this
  finding, found while searching for a real consumer for `KnowledgeFact`'s `danger_rating` fact
  type; explicitly declined to build that connection, filing this as its own independent finding
  instead)
- `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS` (blocked — per
  `docs/plans/rpg_design_roadmap/rpg_knowledge_investigation_closure_plan.md`, this ticket is
  gated on that one's disposition decision: this is the payoff item — until real facts/leads flow,
  this ticket's own "what should populate these fields" question has nothing real to feed it)
- `TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS` (open, P0 —
  **chain 1, step 1**: blocks the lead-belief path — `ENABLE_GUILD_QUEST_GENERATION`'s default
  doesn't reach real runs, so no `GuildAction.visit()` lead is ever granted to confirm)
- `TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH` (open — **chain 1, step 2**:
  even once a lead is granted, `BeliefCycleSystem.process_observation()` is never reached — the
  `float()` parse throws first for every guild-produced lead's `detail` format)
- `TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION` (open, unrelated pre-existing deferral —
  **chain 2**: `CombatEngagementPhase`'s real `combat_risk` `BeliefEntry` is gated
  `ENABLE_COMBAT_ENGAGEMENT`, default `OFF`; also a single per-actor scalar, not the
  per-`enemy_id`/`region_id` keyed shape `enemy_data`/`region_data` need — real adaptation work
  even once the flag question is resolved)

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
Re-verified the origin claim before doing anything else: `region_data`/`enemy_data` are still
empty at every real construction site; `travel_regions` still has zero production construction
sites (unchanged since the origin ticket).

Checked for a real, live source of entity belief data — per peer instruction, never world truth —
before wiring anything, since `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS`
(worked immediately before this ticket, same batch) had just found its own connection stays
`BLOCKED`. Found exactly two real, live-code candidates, and confirmed both are currently
unreachable:

**Chain 1 — the lead-belief path** (`GuildAction.visit()` → `entity.strategic.leads` →
`BeliefCycleSystem.process_observation()` in `intelligence.py:416`): blocked twice over. (1) The
lead is never granted in a real run — `ENABLE_GUILD_QUEST_GENERATION`'s default doesn't propagate
to `state.feature_flags` (`TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-
FLAGS`). (2) Even with a lead present, `process_observation()` sits *after* a `float()` parse on
`lead.detail` that throws for every guild-produced lead's narrative-text format
(`TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH`) — confirmed by reading the exact
code path, not assumed.

**Chain 2 — the combat-risk belief path** (`CombatEngagementPhase`'s real, tested `combat_risk`
`BeliefEntry`, `src/domains/combat_engagement/phase.py`): gated `ENABLE_COMBAT_ENGAGEMENT`, default
`OFF` (`TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION`, open, unrelated pre-existing deferral, not
part of this batch). Even were the flag on, this belief is a single per-actor scalar ("my own
current risk from the nearest hostile"), not the per-`enemy_id`/per-`region_id` keyed shape
`enemy_data`/`region_data` actually need — real adaptation design work, not a direct read.

`KnowledgeFact` (the third candidate the origin ticket already flagged as unproven) remains
separately confirmed at zero real writes, per the investigation that started this whole initiative.

**Disposition: do not wire either source now.** Both would produce code that compiles, has real
test coverage, and never fires in a real run — precisely the "looks live and isn't" pattern this
ticket exists to close, not extend. Declined for the second time in this batch, same reasoning as
`TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS`. Stays `BLOCKED` on the two
named chains above rather than closing `DONE` on an empty implementation or a premature
"speculative, remove" documentation call — the fields are genuinely on a path to a real source
once the blocking tickets resolve, not abandoned.

## Test Summary
No code changed — investigation only. Confirmed via direct code reading (not run, since no
mechanism to exercise exists yet): the exact line in `intelligence.py` where
`process_observation()` sits after the throwing `float()` parse; `ENABLE_COMBAT_ENGAGEMENT`'s
current default in `feature_flags.py`; `combat_risk`'s own single-scalar `BeliefEntry` shape.

## Files Changed
None — investigation and disposition only; no `src/` or `tests/` changes.

## Completion Summary
Checked for a real belief source before building, per instruction, rather than wiring against an
assumed one. Found two real candidates in code, both currently blocked from ever reaching a real
run — one stacked on two independent problems from this same batch (flag propagation, then a
contract mismatch), the other on an unrelated pre-existing flag deferral plus its own shape
mismatch (scalar vs. keyed dict). Declined to wire either, since doing so would add a fresh
"correct but unreached" mechanism to the ticket meant to close that exact pattern. Stays `BLOCKED`,
not `DONE`, with both chains named explicitly and the `travel_regions` region-half finding kept
visible so it doesn't silently inherit whatever the enemy-half source eventually resolves to.

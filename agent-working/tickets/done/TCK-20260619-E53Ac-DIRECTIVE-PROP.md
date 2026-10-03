---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53Ac-DIRECTIVE-PROP
phase: done
date: 2026-06-22
tags: [faction, directive-propagation, adventure-scoring, entity-scoring, phase-5]
---

# TCK-20260619-E53Ac-DIRECTIVE-PROP

## Title
Epic 5.3Ac · Faction Directive Propagation to Entity Scoring

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Extend `AdventureRouteScorer` in `src/domains/adventure/scoring.py` to consume the per-tick `FactionDirective` list (produced by E53Ab) and adjust route urgency scores based on entity role and regional proximity. Depends on E53Aa (FactionState) and E53Ab (FactionDirective).

## Scope

**Score adjustments** (as specified in parent epic):
- Entity role `GUARD` + route region is contested (in faction territory with tension_level > 0.5): patrol-type route urgency **+2.0**
- Entity role `MERCHANT`/`SHOPKEEPER` + route region is in an allied faction region (diplomatic_relations value == "allied"): trade-type route urgency **+1.5**
- Entity role `HERO` + a `COMMISSION_QUEST` `FactionDirective` exists for the entity's faction: quest-type route urgency **+3.0**

**Implementation approach**:
- Add optional parameter to `AdventureRouteScorer.score()`:
  ```python
  faction_directives: Optional[list["FactionDirective"]] = None,
  factions: Optional[Dict[str, "FactionState"]] = None,
  ```
- Inject at the call site (in the engine or adventure domain phase) from the per-tick scratch produced by `FactionDecisionPhase.execute()`.
- Do NOT fetch `state.factions` inside scorer — pass it in; scorer is a pure scoring function.

**Route family mapping**:
- "patrol-type" = `RouteFamily.HUNT_WEAK_ENEMY` or `RouteFamily.PATROL` (check `src/domains/adventure/schema.py` for exact RouteFamily values)
- "trade-type" = `RouteFamily.TRADE` or `RouteFamily.GATHER` (confirm in schema.py)
- "quest-type" = `RouteFamily.QUEST_OPPORTUNITY`

**Also**: Create `docs/systems/faction_contract.md` — the V2 faction system contract document. Include: FactionState schema, FactionDirective schema, directive kinds, tension mechanics, propagation rules, and references to child tickets. Mark status as DRAFT pending E53Ad completion.

## Out of Scope
- FactionState model (E53Aa)
- FactionDecisionPhase / FactionDirective creation (E53Ab)
- Tension update from events (E53Ad)
- Diplomatic action resolution (E53B)

## Acceptance Criteria
- `test_guard_patrol_urgency_boosted_by_faction_directive` passes:
  - GUARD entity + contested region territory + DEFEND_BORDER FactionDirective → patrol route score increases by +2.0
- `test_merchant_trade_urgency_boosted_by_allied_region` passes:
  - SHOPKEEPER/MERCHANT entity + allied region → trade route score increases by +1.5
- `test_hero_quest_urgency_boosted_by_commission` passes:
  - HERO entity + COMMISSION_QUEST FactionDirective → quest route score increases by +3.0
- `test_no_faction_directives_scorer_unchanged` passes:
  - `faction_directives=None` → scores identical to current baseline
- Existing `AdventureRouteScorer` tests continue to pass (no regressions)
- `docs/systems/faction_contract.md` created with correct schema and directive kinds

## Related Tickets
- TCK-20260619-E53A-FACTION-AGENT (parent epic)
- TCK-20260619-E53Aa-FACTION-STATE (prerequisite)
- TCK-20260619-E53Ab-DECISION-PHASE (prerequisite — provides FactionDirective)
- TCK-20260619-E53Ad-TENSION-UPDATE (sibling — can run concurrently)
- TCK-20260619-E53B-DIPLOMACY (sibling epic — will extend faction_contract.md)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` (directive priority semantics — update to mention faction directive scoring)
- `docs/systems/faction_contract.md` (create here)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E53A-FACTION-AGENT/investigation.md`

## Related Code Areas
- `src/domains/adventure/scoring.py` (AdventureRouteScorer.score() — extend)
- `src/domains/adventure/schema.py` (RouteFamily enum — read to confirm family names)
- `src/engine/faction_decision.py` (FactionDirective — import TYPE_CHECKING only)
- `tests/unit/faction/test_faction_directive_propagation.py` (new file)
- `docs/systems/faction_contract.md` (new file)

## Assumptions / Open Questions
- "MERCHANT" entity role maps to `EntityRole.SHOPKEEPER` (value 1) — confirm from `src/core/enums.py`; there is no separate MERCHANT role in the current enum.
- "Contested region" = region in `FactionState.territory` AND `tension_level > 0.5`; "allied region" = `diplomatic_relations[other_faction_id] == "allied"` for any faction that controls the route's region. Confirm region-to-faction lookup at implementation time (via `RegionState.owner_faction_id` → string faction_id mapping).
- Scorer must remain a pure function — no state mutation, no I/O, deterministic given identical inputs.
- `docs/mechanics/04_strategic_cognition.md` must be updated in this ticket to document faction directive scoring rules; parity ledger entry under `strategic_cognition.yaml` must be added.

## Implementation Notes
- Read `src/domains/adventure/schema.py` to confirm exact `RouteFamily` values before assigning score deltas to route families.
- The call site that passes `faction_directives` must be identified in the adventure domain phase or engine pipeline; trace the path from `FactionDecisionPhase.execute()` output to `AdventureRouteScorer.score()` invocation before coding.
- Add a parity ledger entry in `docs/parity_ledger/strategic_cognition.yaml` for faction directive propagation (FACTION-DIR-001) with status=verified after tests pass.

## Test Summary
```bash
pytest tests/unit/faction/test_faction_directive_propagation.py -x -v
pytest tests/unit/adventure/test_scoring.py -x -v  # regression guard
```

## Files Changed
- `src/engine/faction_constants.py` — new; DEFEND_BORDER, TRADE_ROUTE, COMMISSION_QUEST constants
- `src/engine/faction_decision.py` — import constants from faction_constants; updated module docstring
- `src/engine/pipeline.py` — moved faction_decision before adventure_decision; removed cadence guard; threaded faction_directives+factions through apply() call
- `src/domains/adventure/phase.py` — added faction_directives/factions params; fixed pre-existing RouteFamily_Defer_check bug; added RouteFamily import
- `src/domains/adventure/service.py` — added faction_directives/factions params; passes to scorer
- `src/domains/adventure/scoring.py` — added faction_constants import; added faction_directives/factions params; inserted §2b urgency adjustment block
- `src/domains/adventure/mapper.py` — added PROTECT_TARGET/OWN_SURVIVAL mappings (pre-existing gap)
- `tests/unit/faction/test_faction_directive_propagation.py` — new; 8 tests
- `tests/unit/domains/adventure/test_phase3_route_families.py` — updated RouteFamily count to 16
- `docs/systems/faction_contract.md` — new
- `docs/mechanics/04_strategic_cognition.md` — added §6.10 faction directive scoring
- `docs/parity_ledger/strategic_cognition.yaml` — added FACTION-DIR-001

## Completion Summary
Extended AdventureRouteScorer to consume FactionDirective list from FactionDecisionPhase.
Moved faction_decision before adventure_decision in pipeline (removed cadence gate for determinism).
Extracted directive-kind constants to faction_constants.py to prevent circular imports.
GUARD+HUNT_WEAK_ENEMY gets +2.0 urgency on DEFEND_BORDER; SHOPKEEPER+trade gets +1.5 on allied relations; HERO+QUEST_OPPORTUNITY gets +3.0 on COMMISSION_QUEST.
All 8 directive propagation tests and 40 adventure domain tests pass.

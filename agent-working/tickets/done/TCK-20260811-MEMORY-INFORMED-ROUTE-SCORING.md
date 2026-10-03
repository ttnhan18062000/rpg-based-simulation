---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING
phase: done
date: 2026-08-11
tags: [cognition, adventure]
---

# TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING

## Title
Wire memory-informed candidates into adventure route scoring (descoped)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Deepen adventure's internal reasoning by wiring memory-informed candidates via src/domains/memory/ into route generation/scoring, so entities' own causal memory measurably shapes route decisions instead of being ignored entirely -- descoped from the author's original vendor-cheating example, which investigation found is not buildable with the memory system's current 4 hardcoded event kinds.

## Scope
- AdventureRouteGenerator/AdventureRouteScorer read entity.cognition.memory's existing CausalMemoryEntry.future_advice values (currently zero references)
- A route family whose future_advice already exists after one of the 4 supported event_kinds (combat_loss, failed_search, failed_craft, party_abandoned) measurably suppresses/promotes that route family's score or benefit term
- New memory read stays the entity's own subjective belief, consistent with scoring.py's documented 'reads only subjective self-model aspects to protect information opacity' boundary

## Out of Scope
- The literal 'vendor who previously cheated the entity' example from the original proposal -- NOT buildable: CausalAttributionService.attribute() has no vendor/trade/cheating event_kind, and buy_item opportunities key to a shop/structure id, not an NPC vendor entity id; would require a new vendor-entity concept, out of scope for this ticket
- Capability-estimate-driven confidence (TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING) and relationship-aware FORM_PARTY (TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY) -- separate tickets, different risk/scope
- Any change to AdventureGoalScorer/AdventureDecisionService's wrapper migration -- this concern is orthogonal but touches the same files; recommend landing after that migration settles to avoid merge churn

## Acceptance Criteria
- [x] A route family whose CausalMemoryEntry.future_advice already exists (e.g. 'avoid_enemy' after combat_loss, 'boost_party_trust' after party_abandoned) measurably suppresses/promotes the matching route family's score/benefit vs. an entity with no matching causal memory
- [x] The vendor-cheating example is explicitly NOT scoped as a buildable AC for this ticket
- [x] STRAT-227 parity entry gains a test_path (currently null) — **reinterpreted** (see Implementation Notes): STRAT-227 already had a non-null test_path pre-ticket (a stale AC premise, confirmed during Plan review), so this is satisfied via the plan's approved reinterpretation — extending STRAT-227's existing test_path/text/v2_evidence with the new memory-informed term's coverage, not filling a null value that never existed.

## Related Tickets
- TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/adventure/generator.py
- src/domains/adventure/scoring.py
- src/domains/memory/attribution.py
- src/domains/memory/phase.py

## Assumptions / Open Questions
- Idea's headline example (vendor-cheating) is unbuildable as originally stated and has been descoped to what memory already supports; implementing the literal example would require a new vendor-entity concept, out of scope
- Sequencing/merge conflict risk with the adventure/cognition wrapper migration tickets (which declare AdventureRouteScorer/Generator 'unchanged internally') -- recommend landing after those settle, or explicitly disclaim the risk if landed concurrently
- Related design doc: docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md (Future Extension Patterns)

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING/plan.md`
(Steps 1-8), no deviations.

- **Step 1**: Added `memory_adjustment: float = 0.0` as the last field in `AdventureRouteOption`'s
  intermediate-scoring-term block (`src/domains/adventure/schema.py`), immediately after
  `plan_advance_bonus`. All 7 existing keyword-argument construction call sites (5 in
  `generator.py`, 2 in `service.py`) required no change — confirmed by the full regression suite
  staying green.
- **Step 2**: Added new step "4c. Memory-Informed Advice Adjustment" in
  `AdventureRouteScorer.score()` (`src/domains/adventure/scoring.py`), reading
  `entity.cognition.memory.causal.entries` directly (no new plumbing — `entity` already flows into
  `score()`). Implements exactly 2 advice→family mappings per plan: `avoid_enemy` →
  `HUNT_WEAK_ENEMY` suppress (−1.0, confirmed dead-code family — `generator.py` never emits it),
  `boost_party_trust` → `FORM_PARTY` promote (+1.0, confirmed live-generated family). Boolean-gated
  per advice string via `any(...)` over the full entries tuple, not accumulated per entry. Updated
  the final-score formula and the `dataclasses.replace(...)` call to include the new term. Updated
  both the function-level `Formula:` docstring and the module-level docstring (the latter now
  disclosing that `entity.cognition`, not just `entity.self_model`, is read) — per the round-1
  review finding, the function-level docstring was also missing `plan_advance_bonus`; both gaps
  (the pre-existing one and the new `memory_adjustment` addition) were closed in the same edit.
- **Step 3**: New file `tests/unit/domains/adventure/test_memory_informed_scoring.py` — all 7 tests
  from `test_plan.md` implemented using the `V2EntityBuilder(...).replace_cognition(CognitionModel(
  memory=MemoryModel(causal=CausalMemory(entries=(...,)))))` pattern. All 7 pass.
- **Steps 4-8 (docs)**: Added `docs/mechanics/04_strategic_cognition.md` §6.11 (new subsection,
  with the "Not yet live" callout disclosing `MemoryUpdatePhase` has zero pipeline call sites), and
  added the missing `plan_advance_bonus` row alongside the new `memory_adjustment` row to §6.2's
  Formula Term Constants table (8 rows total, per the round-1 review fix). Extended STRAT-227 in
  `docs/parity_ledger/strategic_cognition.yaml` (text/v2_evidence/test_path appended, no new
  sibling entry, status stays `verified`). Corrected `docs/simulation/domains/memory_contract.md`'s
  stale present-tense "feeds adventure route scoring" claim in the Domain Interactions table to
  disclose both halves (scoring-side read is real code; memory population is not live), and fixed a
  pre-existing field-name inaccuracy in the same doc's "What It May Mutate" table
  (`entity.cognition.causal_memory`/`spatial_memory` → the real `entity.cognition.memory.causal`/
  `entity.cognition.memory.spatial` paths). Added the new "What It Reads" row and
  `memory_adjustment` term-table row to `docs/simulation/domains/adventure_contract.md` without
  attempting a full resync of that table's other pre-existing staleness (out of scope per plan).
  Updated the "Memory-informed candidates" bullet in
  `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md` from an open
  Future Extension Pattern to closed/scoped, restating the vendor-cheating example's continued
  unbuildability.

**Recommendation (per plan's Scope Guards, not filed by this agent):** file a follow-up ticket
(e.g. `TCK-YYYYMMDD-MEMORY-UPDATE-PHASE-PIPELINE-WIRING`) scoped to (a) registering
`MemoryUpdatePhase` into `src/engine/pipeline.py` with a cadence decision, and (b) building a real
`trigger_event` producer wired to combat/search/craft/party-abandonment outcomes — today,
`MemoryUpdatePhase` has zero call sites outside its own file/tests, so this ticket's new
`memory_adjustment` scoring term is real, live-reachable code but is exercised only by unit tests
until that follow-up lands, mirroring how prior epic tickets in this series filed analogous
out-of-scope follow-ups.

## Test Summary

- `pytest tests/unit/domains/adventure/test_memory_informed_scoring.py -v` — **7/7 passed** (new
  file, all tests from test_plan.md).
- `pytest tests/unit/domains/adventure/ -q` — **80/80 passed** (full regression surface for the
  scoring/generator/service/eligibility unit tests, unaffected by the new defaulted field/term).
- `pytest tests/integration/domains/adventure/ -q` — **6/8 passed, 2 pre-existing failures**
  (`test_harvest_to_event.py::test_crafting_project_produces_item_crafted_event_through_full_pipeline`
  and `::test_reach_resource_arrival_produces_resource_harvested_event_through_full_pipeline`).
  Confirmed via `git stash` that both fail identically on the pre-ticket working tree — unrelated to
  this change, not touched or introduced by this ticket.
- `pytest tests/integration/domains/memory/ tests/integration/scenarios/test_phase13_temporal_causal_spatial_memory_scenarios.py -q`
  — **3/3 passed**.
- Combined scoped run (`tests/unit/domains/adventure/ tests/integration/domains/adventure/
  tests/integration/domains/memory/ tests/integration/scenarios/test_phase13_temporal_causal_spatial_memory_scenarios.py`)
  — **89 passed, 2 pre-existing failures** (same two, unrelated).

## Files Changed

- `src/domains/adventure/schema.py` — added `memory_adjustment: float = 0.0` field to
  `AdventureRouteOption`
- `src/domains/adventure/scoring.py` — added the memory-informed adjustment step (4c), updated the
  final-score formula, the `dataclasses.replace(...)` call, the function-level `Formula:` docstring,
  and the module-level docstring
- `tests/unit/domains/adventure/test_memory_informed_scoring.py` — new file, 7 tests
- `docs/mechanics/04_strategic_cognition.md` — added §6.11, updated §6.1 formula and §6.2 Formula
  Term Constants table (added `plan_advance_bonus` and `memory_adjustment` rows)
- `docs/parity_ledger/strategic_cognition.yaml` — extended STRAT-227 (`text`/`v2_evidence`/
  `test_path`)
- `docs/simulation/domains/memory_contract.md` — corrected the Adventure-domain Domain Interactions
  row; fixed the pre-existing `causal_memory`/`spatial_memory` field-name inaccuracy in "What It May
  Mutate"
- `docs/simulation/domains/adventure_contract.md` — added a "What It Reads" row and a
  `memory_adjustment` term-table row
- `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md` — updated
  the "Memory-informed candidates" bullet from open to closed/scoped

## Completion Summary

Added a new `memory_adjustment` scoring term to `AdventureRouteScorer.score()` that reads the
entity's own `entity.cognition.memory.causal.entries` (its subjective causal-memory beliefs) and
applies a fixed ±1.0 adjustment for 2 of 10 real advice→route-family mappings (`avoid_enemy` →
suppress `HUNT_WEAK_ENEMY`, `boost_party_trust` → promote `FORM_PARTY`), with zero new plumbing
since `entity` already flows into `score()` unchanged. The term is real, live-reachable, read-only
code, covered by 7 new unit tests plus the full existing regression suite staying green, but is not
yet observable in any running simulation because `MemoryUpdatePhase` (the only code that populates
causal-memory entries) has zero pipeline call sites — this out-of-scope gap is disclosed in the
Mechanics Bible, the parity ledger, and both domain-contract docs, and a follow-up pipeline-wiring
ticket is recommended (not filed) per the plan's Scope Guards. All 6 doc/parity artifacts named in
the plan (Mechanics Bible §6.11 + §6.2 table fix, STRAT-227 extension, `memory_contract.md`,
`adventure_contract.md`, the architecture design doc) were updated in this same session.

Plan review went through 2 rounds: round 1 found the plan falsely claimed `plan_advance_bonus` was
already documented in `scoring.py`'s docstring and the Mechanics Bible §6.2 table (it was actually
missing, a pre-existing gap from a different ticket) -- fixed by adding it alongside the new
`memory_adjustment` term in both spots. Architecture-Verify went through 3 rounds: round 1 found a
real arithmetic error -- 3 landed files (the Mechanics Bible, `memory_contract.md`, and the test
docstring) claimed "8 real, reachable `future_advice` values" when the true count (per
`CausalAttributionService.attribute()`'s 4 event_kinds) is 10 -- fixed across all 3 files. Round 2
found one residual, uncorrected arithmetic clause left in the staging plan.md itself
("8 total minus 2 mapped = 6 remaining") -- fixed to "10 total minus 2 mapped = 8 remaining". Round
3 APPROVED with no further gaps. Parity phase independently re-verified STRAT-227 and confirmed
`social_narrative.yaml`/`progression.yaml` (both flagged by the file-path hint) are false positives,
correctly left untouched.

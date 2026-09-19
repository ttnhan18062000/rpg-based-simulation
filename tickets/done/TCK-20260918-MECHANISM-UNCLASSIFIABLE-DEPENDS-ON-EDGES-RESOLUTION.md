---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-RESOLUTION
phase: done
date: 2026-09-18
tags: [architecture, schema]
---

# TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-RESOLUTION

## Title
Resolve the 17 edges `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` could not classify —
45% of the surviving graph is still unvalidated

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` checked all 70 remaining `depends_on`
edges: 21 KEEP, 32 REMOVE, 17 UNCLASSIFIABLE (a genuine grep + `graphify query` search failed to
locate a confident, distinguishable implementation for at least one side of each). The 17 are now
visibly marked in `registries/mechanisms.yaml` itself (`unaudited_depends_on_edges`, validated by
`registry.py`'s invariant #8) and surfaced per-row in the generated priority view — so the gap is
honest, not hidden — but they remain unresolved. Of the 38 edges that survive the audit (70
audited, 32 removed), **17 unvalidated out of 38 is roughly 45% of the surviving graph** — the new
priority ranking is materially better grounded than the pre-audit one, but not itself clean.

**The 17 are not 17 independent investigations — they collapse into roughly 5-6 real threads**,
which is the material fact for deciding whether to pick this ticket up: locating `goal_hierarchy`'s
own implementation resolves 3 of the 17 at once (#8-10 below); locating `race_archetype`'s resolves
2 more (#2, #16); and 2 more (#5-6, `motivation_doctrine`'s pair) may resolve for free, without any
fresh investigation, once `TCK-20260918-MOTIVATION-DOCTRINE-STALE-AGAINST-RETIRED-DOCTRINE-VALUES-CHAIN`
lands, since if `motivation_doctrine` itself retires, the edges declared on it retire with it. "17
edges" and "5-6 threads" are very different scoping decisions — the real remaining work is answering
two implementation-location questions (`goal_hierarchy`, `race_archetype`) plus a handful of
genuinely independent one-offs, not 17 separate searches.

## Scope
For each of the 17 edges, find or definitively confirm the absence of real implementing code,
narrower and more targeted than the original 70-edge sweep since each one already has a documented
starting point (what was searched, what came back inconclusive) in
`stored_artifacts/TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT/edge_audit_results.md`'s
own UNCLASSIFIABLE section:

1. `conversation → action_pacing_readiness` — no "conversation" implementation found (`state: gap`).
2. `class_assignment → race_archetype` — neither side confidently located.
3. `build_diversity → class_assignment` — depends on #2.
4. `trauma → combat_resolution` — no per-entity "trauma" implementation distinct from
   `RegionState.trauma_score` (regional) or `WoundState` (physical injury).
5. `motivation_doctrine → goal_hierarchy` — `MotivationModel` is a pure dataclass; see the related
   `TCK-20260918-MOTIVATION-DOCTRINE-STALE-AGAINST-RETIRED-DOCTRINE-VALUES-CHAIN` finding, which may
   resolve this and #6 together (if `motivation_doctrine` itself is retired, both edges retire with
   it rather than needing independent resolution).
6. `motivation_doctrine → affection_relationship_bonds` — same cause as #5.
7. `commitment_betrayal → combat_resolution` — no distinct `commitment_betrayal` implementation
   separate from `commitment_pressure_consequences`'s own bound files.
8. `goal_hierarchy → belief_cycle` — `goal_hierarchy`'s own implementation unlocatable.
9. `goal_hierarchy → reputation` — same cause as #8.
10. `committed_intentions → goal_hierarchy` — `CommitmentModel` is a pure dataclass; also blocked on
    #8's `goal_hierarchy` question.
11. `country_lifecycle → betrayal_siege_war` — no `country_lifecycle` implementation found anywhere.
12. `city → regional_sovereignty` — no distinct "city" aggregate implementation found.
13. `ruins_mines_battlefields → regional_trauma` — low-confidence mapping to
    `create_battlefield_scar()`, not confirmed.
14. `ruins_mines_battlefields → regional_sovereignty` — same mapping issue as #13.
15. `nest → camp` — no "nest" implementation found anywhere.
16. `settlement_capacity_axis → race_archetype` — blocked on #2's `race_archetype` question.
17. `commitment_pressure_consequences → commitment_betrayal` — same cause as #7.

Note the real clustering: #8-10 all block on locating `goal_hierarchy`; #2, #16 block on locating
`race_archetype`; #5-6 and #7, #17 may resolve via other already-filed/related work rather than
needing fresh investigation. Resolving `goal_hierarchy` and `race_archetype`'s own implementation
status first may collapse several of these at once.

## Out of Scope
- Re-litigating the 21 KEEP / 32 REMOVE verdicts — already resolved with evidence, not reopened.
- Building anything new — this is confirming or correcting existing declared edges, same
  correction-pass discipline as the parent audit.

## Acceptance Criteria
1. Every one of the 17 edges reaches a real KEEP/REMOVE verdict, or is confirmed as genuinely
   unresolvable with a stronger statement of why (e.g. the mechanism has no code at all and is
   purely aspirational) — not left in the same "search came back inconclusive" state twice.
2. `registries/mechanisms.yaml`'s `unaudited_depends_on_edges` list shrinks to reflect only
   whatever remains genuinely unresolved after this pass.

## Related Tickets
- `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` — parent; the 17 edges and their search
  history come from this ticket's own `edge_audit_results.md`.
- `TCK-20260918-MOTIVATION-DOCTRINE-STALE-AGAINST-RETIRED-DOCTRINE-VALUES-CHAIN` — may resolve #5-6
  as a side effect of its own scope.

## Related Docs
None new — see the parent ticket's own Related Docs.

## Related Stored Artifacts
`stored_artifacts/TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT/edge_audit_results.md` —
the UNCLASSIFIABLE section is this ticket's own starting point.

## Related Code Areas
- `registries/mechanisms.yaml` (`unaudited_depends_on_edges`, plus the affected mechanisms'
  `depends_on` lists)

## Assumptions / Open Questions
Whether `goal_hierarchy` and `race_archetype` have real implementations under names too different
for grep/graphify to have found, or are genuinely aspirational registry entries with no code, is
itself an open question this ticket needs to answer before the edges depending on locating them can
resolve.

## Implementation Notes
Resolved 15 of the 17 edges with real code-read evidence, per-edge verdicts recorded on each
mechanism's own `verified` block in `registries/mechanisms.yaml` (not just in this ticket) so the
evidence lives next to the data it's about, the same discipline every other correction in this epic
has followed.

**KEEP, confirmed with real citations (4)**:
- #2 `class_assignment → race_archetype`: `src/content/resolver.py:257-258` iterates
  `species.compatible_roles` directly — role resolution cannot proceed without the species' own
  declared list.
- #8 `goal_hierarchy → belief_cycle`: `StrategicIntelligenceSystem` (see below) calls
  `BeliefCycleSystem.process_observation()`/`apply_contradiction()` inside the same strategic pass
  that manages project/objective selection.
- #10 `committed_intentions → goal_hierarchy`: `strat.committed_intentions[0]` read directly inside
  `StrategicIntelligenceSystem`'s own objective-selection pipeline — real reader, unexercised only
  because nothing ever populates the list (writer-side orphan, already known).
- #12 `city → regional_sovereignty`: City *is* `RegionState` (wiring map's own explicit finding,
  "today a City is a Region"), and `RegionState.owner_faction_id` is regional_sovereignty's own
  core tracked field — same underlying state object.

**REMOVE, confirmed absent (11)**: #1 `conversation`, #3 `build_diversity`, #9 `goal_hierarchy →
reputation`, #11 `country_lifecycle → betrayal_siege_war`, #13/#14 `ruins_mines_battlefields` (both),
#15 `nest`, #16 `settlement_capacity_axis` — each either has zero implementing code anywhere
(confirmed by grep + atlas/wiring-map card check) or, where the dependent's own real code was
located, that code was confirmed to never read the declared dependency. #7/#17 `commitment_betrayal`
pair flagged as an identity/duplication question (no distinct `commitment_betrayal` code exists
separate from `commitment_pressure_consequences`'s own bound files) rather than forced into either
verdict — see `commitment_betrayal`'s own entry.

**Deferred, unresolved (2)**: #5/#6 `motivation_doctrine` pair — `MotivationModel` remains a pure,
dead dataclass and `goal_hierarchy`'s own real code (now located) doesn't read it either. Left in
`unaudited_depends_on_edges` per this ticket's own original plan, pending
`TCK-20260918-MOTIVATION-DOCTRINE-STALE-AGAINST-RETIRED-DOCTRINE-VALUES-CHAIN`.

**Two mechanisms located that the parent audit couldn't find, resolving 5 edges at once each**:
- `race_archetype` → `SpeciesDefinition` (`src/content/schema.py:134`). The parent audit's grep for
  "race"/"Race" class names came back empty because `TCK-20260904-EPIC-RACE-TO-SPECIES-
  TERMINOLOGY` (2026-09-04) had already renamed `RaceDefinition`/`race_id` → `SpeciesDefinition`/
  `species_id` repo-wide — a terminology-drift search miss the original audit ran into blind,
  before that rename's own history was checked.
- `goal_hierarchy` → `StrategicIntelligenceSystem` (`src/systems/strategic_systems/intelligence.py`,
  1782 lines, one class). The parent audit's grep for "goal hierarchy" and `graphify query` both
  failed because the wiring map's own definition ("Directive → Project → Objective → Action") maps
  to this class's project/objective methods (`evaluate_project_switch`, `resume_project`,
  `process_project_outcome`, `_resolve_active_objective`, `evaluate_strategic_intent`), never a
  literally-named "goal hierarchy" symbol. Not bound via `implemented_by` — this one multi-concern
  class also implements `strategic_intelligence_core` and others via different methods, the same
  method-level binding gap already recorded on `action_pacing_readiness`/`skill_unlocks`
  (TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION).
- Similarly, `country_lifecycle`'s own real code was found (`FactionDecisionPhase`,
  `src/engine/faction_decision.py` — "Country" and "Faction" are the same underlying class per the
  atlas's own investigation) even though its one edge to `betrayal_siege_war` still resolved REMOVE
  (that class never references siege/war/betrayal concepts).

**One real state correction, found while checking edge #4** (`trauma → combat_resolution`): the
parent audit concluded no per-entity trauma implementation exists at all. That was itself a search
miss — real per-entity trauma tracking exists (`RecoveryState.trauma_tags`/`confidence_loss`/
`retry_readiness`, written by `RecoveryReadinessService.register_near_death()`,
`src/domains/emotion/recovery_service.py`) — but `register_near_death` has ZERO callers anywhere in
`src/`, a third independently-confirmed instance of this session's own orphan-mechanism pattern
(after `status_effects`, `ruins_mines_battlefields`'s own `create_battlefield_scar`). `trauma`'s
state corrected `done` → `orphan` with a full `verified` block; `-> combat_resolution` kept as KEEP
(structurally real, currently unexercised — the same "correct-but-unexercised" shape as
`combat_resolution -> status_effects`'s own SHATTER-bonus finding).

## Test Summary
Registry surgery across 12 mechanisms' `depends_on`/`state`/`verified` fields plus the
`unaudited_depends_on_edges` list (17 → 2). Propagation required regenerating every downstream
consumer: `mechanism_atlas_regenerate.py`, `mechanism_capabilities_regenerate.py` (both fixed
exactly the one expected `trauma` badge/tier), and `mechanism_wiring_map_classdef.py`'s own
Entity Operating Loop diagram (`TRM` node moved from inline-implicit `live` to explicit `:::bug`,
matching the `INT`/`MOT` precedent already in that diagram). 5 pre-existing pinned-count tests
across `test_mechanism_priority_derivation.py` (2), `test_mechanism_registry.py` (2), 
`test_mechanism_registry_view.py` (1), and `test_mechanism_state_caller_check.py` (1) updated with
real recomputed numbers and citations, following the same "update only alongside a real
investigation, never adjust silently" discipline each test's own docstring already required.
`registry.py::validate()` clean (93 mechanisms). Full `tests/unit/tools/` suite: 218 passed.

## Files Changed
- `registries/mechanisms.yaml` — 12 mechanisms' `depends_on`/`state`/`verified` edited;
  `unaudited_depends_on_edges` reduced from 17 to 2.
- `docs/brainstorm/rpg_feature_atlas.html`, `docs/brainstorm/simulation_capabilities.html` —
  regenerated (surgical, tool-written) for `trauma`'s state correction.
- `docs/brainstorm/rpg_simulation_wiring_map.html` — `TRM` node's own classdef and label updated by
  hand (this diagram's colouring isn't auto-regenerated, only checked — `mechanism_wiring_map_
  classdef.py` is report-only).
- `docs/brainstorm/mechanism_verification_view.md`, `mechanism_priority_view.md`,
  `mechanism_registry_view.md`, `mechanism_registry.html` — regenerated.
- `tests/unit/tools/test_mechanism_priority_derivation.py`,
  `tests/unit/tools/test_mechanism_registry.py`,
  `tests/unit/tools/test_mechanism_registry_view.py`,
  `tests/unit/tools/test_mechanism_state_caller_check.py` — pinned counts/mechanism picks updated
  with real-investigation citations.

## Completion Summary
**Done, with 2 of 17 deliberately deferred, not left silently unresolved.** All Acceptance
Criteria met: AC #1 — every edge reached a real KEEP/REMOVE verdict or a stronger "confirmed no
code at all"/identity-question statement, none left in the original "search came back
inconclusive" state twice. AC #2 — `unaudited_depends_on_edges` shrank from 17 to 2, the genuine
remainder pending a named, already-filed follow-on ticket. Two previously "unlocatable" mechanisms
(`race_archetype`, `goal_hierarchy`) were found and their real implementations documented,
collapsing what the parent audit treated as 10 separate unknowns into 2 location questions plus a
handful of genuinely independent edges, exactly as this ticket's own Request Summary predicted.
One real, unanticipated state correction (`trauma`: done → orphan) surfaced and fully propagated,
extending this session's own recurring orphan-mechanism-with-dead-dependent-branches pattern to a
third confirmed instance.

**Addendum, 2026-09-19, peer review — worth stating plainly rather than left implicit in the
diffs**: `action_pacing_readiness`'s own transitive-dependent count has now moved
**~115-125 → 23-25 → 1 → 0** across three separate corrections (the initial dependency-graph
population, the parent edge-semantics audit, and this ticket's own removal of `conversation`'s
edge to it). `betrayal_siege_war` moved **42 → 14 → 1 → 0** the same way (dependency-graph
population, parent audit, this ticket's own removal of `country_lifecycle`'s edge to it). The
mechanism that once topped this registry's derived-priority ranking now has zero real dependents.
Each individual correction was justified on its own real evidence at the time it was made — this
is not a claim that any single correction was wrong. But the cumulative movement is the honest
measure of how wrong the *original* graph was, and it is stated here so the next person reading
today's priority ranking treats it as the current best evidence, not as settled — the same
correction shape could in principle still be sitting undiscovered elsewhere in the graph.

**Self-correction, same day, 2026-09-19: this ticket's own `trauma` state correction above (done →
orphan) was itself wrong, caught and reverted the same day.** While building
`TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION`'s own status-language scan (immediately after
this ticket closed), the atlas's `entity-modification#0` card for `trauma` turned out to be titled
"Trauma: A Lasting Physical Consequence" — the physical Wound→Scar combat-consequence system, not
the psychological near-death tracking this ticket's own edge #4 investigation had attributed it
to. Checking `trauma`'s own original citation
(`stored_artifacts/TCK-20260915-MECHANISM-REGISTRY-FOUNDATION/investigation.md:199`, never
consulted before making the correction above) confirmed it: `trauma`'s real implementation is
`WoundService` (`src/engine/rpg_depth.py`) — `create_wound()` called from
`CombatResolutionSystem._get_wound_infliction()` at all 4 real attack-resolution call sites
(`src/engine/combat.py:194,288,504,562`), with `tactical_decision`'s own code reading the resulting
wound/scar penalties (`src/engine/tactical.py:48,57`). Fully live, confirmed real callers on both
ends. `state` reverted done → orphan → **done**; `implemented_by` corrected to `WoundService`;
`systems:` corrected `[cognition]` → `[combat]` (wound/scar is a combat consequence, not a
cognitive process — the original `[cognition]` placement was itself downstream of the same
misattribution). `RecoveryReadinessService.register_near_death()` (`src/domains/emotion/
recovery_service.py`) is still real, orphaned code — it just implements a different,
currently-unregistered concept, not this mechanism. Full correction recorded on `trauma`'s own
`verified` block in `registries/mechanisms.yaml`.

**The error itself, stated plainly**: found a real orphan candidate that was *plausibly*
describable as "trauma" in English, and bound it to this registry entry without first checking the
entry's own original citation trail — exactly the discipline this registry's own citation
convention exists to enforce, and exactly the kind of unforced error that convention is supposed
to prevent. A sixth shape worth adding to this session's own catalogue of search failures
(`docs/plans/mechanism_claims_as_tests_initiative.md` §3.1): **a real orphan finding, correctly
attributed to the wrong registry entry**, distinct from all five "confident absence" shapes already
catalogued there — this one is "confident (mis)attribution," where the search correctly finds real
code but skips checking whether it's the code the existing entry's own history actually points to.
Not yet added to §3.1 as a numbered sixth shape — flagged here for whoever next touches that
catalogue, since a shape only just discovered deserves its own dedicated treatment rather than a
rushed one-line addition to an already-written section.

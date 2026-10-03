---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260905-CHORE-CARRYFORWARD-DERIVER-CONSOLIDATION
phase: open
date: 2026-09-05
tags: [social, strategy]
---

# TCK-20260905-CHORE-CARRYFORWARD-DERIVER-CONSOLIDATION

## Title
Consolidate the 4 near-identical Deriver/Model/Exporter-Importer carry-forward triples

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Four structurally near-identical modules now exist, all built to the same 3-layer
Deriver/Model/Exporter-Importer pattern originated by `CultureDeriver`
(`src/domains/culture/`) and repeated verbatim in shape by three later M5 siblings:
`src/domains/fidelity/` (idea 62, `TCK-20260905-CHRONICLE-FIDELITY-DRIFT`),
`src/domains/fame/` (idea 57, `TCK-20260905-FAME-DERIVER-LEGEND-FACT`), and
`src/domains/belief_institution/` (idea 63, `TCK-20260905-BELIEF-INSTITUTION-DESIGN`). Each
module independently defines its own frozen State dataclass, its own CarryForward wrapper
(`{key}, {state}, derived_episode: int`, each with hand-written `to_dict()`/`from_dict()`), its
own pure stateless Deriver class, and its own Exporter/Importer pair with an
`export(campaign_state, hierarchy, episode_index, ...)` / thin-lookup `Importer` shape. Flagged
(non-blocking) by architecture review during `TCK-20260905-BELIEF-INSTITUTION-DESIGN`'s own Review
phase as real, growing duplication worth a dedicated consolidation pass now that a 4th instance of
the identical shape exists.

## Scope
- Extract a shared base/mixin (e.g. `src/domains/campaigns/carry_forward.py`) capturing the common
  `CarryForward` wrapper shape (`key`/`state`/`derived_episode` + `to_dict()`/`from_dict()`
  boilerplate) that all 4 (and any future) siblings can build on, reducing hand-written
  serialization duplication.
- Consider (not commit to without further investigation) whether the Exporter/Importer pair's
  `export(campaign_state, hierarchy, episode_index, ...)` shape and "existing entries not
  re-derived this episode persist unchanged" merge behavior can also be factored into a shared
  helper, given all 4 current implementations do this identically.
- Audit whether `BeliefInstitutionExporter`'s extra `clans` parameter (the one real structural
  deviation from the other 3 siblings' otherwise-identical signature) should become part of a
  more general "optional extra read-only input" convention for future siblings, or stays a
  one-off special case.

## Out of Scope
- Any behavior change to Culture Drift, Chronicle Fidelity Drift, Living Legend Fame, or Belief
  Institution's own derivation logic, event-type rules, or thresholds -- this is a pure
  structural refactor, zero behavior change, verified by each existing test suite passing
  unmodified.
- Building any new Deriver-pattern sibling for a not-yet-scoped idea -- this ticket only
  consolidates the 4 that already exist.

## Acceptance Criteria
- [ ] A shared CarryForward base/mixin exists, and all 4 existing siblings (Culture, Fidelity,
      Fame, Belief-Institution) are migrated onto it with zero behavior change.
- [ ] Every existing test for all 4 siblings passes unmodified after the refactor.
- [ ] No new duplication is introduced elsewhere as a side effect (e.g. a 5th near-identical
      pattern for the shared base itself).

## Related Tickets
- TCK-20260905-CHRONICLE-FIDELITY-DRIFT
- TCK-20260905-FAME-DERIVER-LEGEND-FACT
- TCK-20260905-BELIEF-INSTITUTION-DESIGN
- TCK-20260905-EPIC-RPG-M5-HISTORY-BELIEF

## Related Docs
- docs/mechanics/05_world_evolution.md (§7 Cultural Drift, §8 Chronicle Fidelity Drift, §9 Living Legend Fame, §10 Belief Institutions)
- docs/world/fame_legend_contract.md
- docs/world/chronicle_fidelity_contract.md
- docs/world/belief_institution_contract.md

## Related Stored Artifacts
None -- not yet scoped/planned.

## Related Code Areas
- src/domains/culture/{model,deriver,exporter}.py
- src/domains/fidelity/{model,deriver,exporter}.py
- src/domains/fame/{model,deriver,exporter}.py
- src/domains/belief_institution/{model,deriver,exporter}.py
- src/domains/campaigns/state.py
- src/domains/campaigns/orchestrator.py

## Assumptions / Open Questions
- Whether the Deriver classes themselves (not just the CarryForward wrapper) share enough real
  structure to warrant a shared base, versus staying independent given each has genuinely
  different derivation logic, is an open Plan-phase question -- not resolved by this scoping.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

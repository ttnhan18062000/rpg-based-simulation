---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING
artifact_type: plan
tags: [feature-flags, determinism]
---

# Plan — TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING

## Fix
`src/engine/pipeline.py`'s `adventure_decision` phase call site: wrap `AdventureDecisionPhase.apply(...)`'s
return value in `u.merge(...)`, matching every other phase in the file. One line changed
(already implemented and verified during Investigate — this is a bug found and fixed in the
course of a single controlled probe session, not requiring separate design exploration).

## Anchor re-verification (per `corpus_tier_taxonomy.md`'s Regression/baseline-tier drift policy)
Real-recalibrate `hero_guild_routing` and `simq_routing_test` (all existing anchored
seed/tick-length combinations) post-fix. Compare each pillar's grade/score against the currently
committed `grade_anchors.json` entries:
- SOCIAL/FACTION/INFORMATION: expected unchanged (investigation.md confirmed no real signal was
  being suppressed for these 2 worlds specifically — flag OFF or no content authored).
- ECONOMY: expected to change (real signal restored). If it changes, update the anchor with
  attribution to this ticket, matching `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`'s own Step 4a
  precedent cited by the taxonomy doc.
- AGENCY/COGNITION/COMBAT/PROGRESSION/WORLD/NARRATIVE: not expected to change (their own producing
  phases run after `adventure_decision` or don't depend on pre-adventure-decision accumulated
  state) — verify, don't assume.

## Docs
- `docs/guidelines/intentional_divergences.md`: new entry (Bug Fix rationale class).
- `docs/parity_ledger/strategic_cognition.yaml`: new entry (AdventureDecisionPhase's own domain,
  from `expected_subsystems_for_files()`'s real mapping for `src/engine/pipeline.py`).

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| investigation.md identifies the exact real mechanism | investigation.md — missing `u.merge()`, not RNG |
| investigation.md confirms/rules out coupling on the 2 existing routing worlds | investigation.md's own section |
| Real fix lands, verified via before/after comparison | Already verified during Investigate; re-verify post-formal-commit |
| Scoped pytest passes | Test phase |

## Out of scope (unchanged from ticket)
- Re-attempting the `frontier_marches` flag flip itself — deferred to a future ticket per this
  ticket's own explicit condition.

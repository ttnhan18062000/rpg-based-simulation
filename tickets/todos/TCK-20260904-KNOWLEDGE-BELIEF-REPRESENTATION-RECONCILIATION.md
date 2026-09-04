---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION
phase: open
date: 2026-09-04
tags: [content]
---

# TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION

## Title
Decide whether BeliefEntry and KnowledgeFact should be reconciled — two parallel belief/knowledge
models with zero cross-references

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
`docs/brainstorm/codex/2026-09-02-core-rpg-knowledge-belief-axis-proposal.md` flagged this as a real
finding, not yet resolved. Re-confirmed directly against current code (not re-read from the proposal):
- `BeliefEntry` (`src/systems/strategic_systems/belief.py:23`) — `subject`, `claim`, `certainty`,
  `source` (`observation`/`rumor`/`deduction`), `source_entity_id`, `contradictions`. Stored on
  `StrategicComponent.beliefs: Dict[str, Any]` (`src/core/strategic.py:425`). Real consumers:
  `src/domains/cooperation/evaluators.py`, `src/systems/strategic_systems/detour.py`.
- `KnowledgeFact` (`src/core/self_model.py:49`) — `subject`, `fact_type`, `details`, `certainty`,
  `source_id`. Stored on `KnowledgeModelComponent.facts: Dict[str, KnowledgeFact]`
  (`src/core/self_model.py:178`). Real consumers: `src/cognition/knowledge_model.py`,
  `src/domains/information/{assimilation,schema,phase}.py`,
  `src/engine/pipeline_phases/lead_contradiction.py`, `src/engine/intent/action_intent.py`,
  `src/engine/domain/cognition_extras.py`, `src/core/cognition_accessors.py`, `src/core/cognition.py`.

Both model "an entity's uncertain claim about the world, with a subject, a certainty, and a source" —
structurally close, yet **zero cross-references exist anywhere in the codebase** between them,
confirmed via direct grep. This is not a naming collision (unlike `KnowledgeFact`'s own docstring,
which already correctly disambiguates itself from `src.world.providers.information.KnowledgeFact`, an
unrelated ephemeral provider-side transfer object — that pairing is fine and out of scope here).
`BeliefEntry` and `core/self_model.py`'s `KnowledgeFact` are the two real, live, unreconciled models.

## Scope
- Investigate whether the two representations are genuinely serving different purposes (e.g.
  `BeliefEntry` for uncertain/contested claims with a decay-toward-resolution lifecycle vs.
  `KnowledgeFact` for more settled, assimilated information) or whether they're accidental duplication
  that should merge.
- Check for any observed or plausible bug class from the split — e.g. an entity holding contradictory
  belief and knowledge about the same subject with no reconciliation path, or duplicated
  certainty-decay logic drifting apart between the two systems over time.
- Present real options (matching the calendar-authority ticket's own precedent: options + a
  recommendation, plan-owner sign-off) rather than picking one unilaterally:
  1. Keep both, but document the split explicitly (which domain owns which kind of belief) so future
     ideas don't accidentally duplicate a third representation.
  2. Reconcile into one model, migrating one consumer set onto the other's schema.
  3. Add an explicit bridge/reconciliation layer (e.g. a lookup that checks both) without merging the
     underlying storage.
- Record the decision in `rpg_design_roadmap.md`'s "Knowledge/Belief axis" section, the same
  reconciliation-note pattern already used there and for the Temporal/Social axes.

## Out of Scope
- Actually implementing whichever option is chosen — this ticket investigates and decides, matching
  `TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY`'s own precedent (a dedicated decision ticket, with
  implementation deferred to a follow-up).
- `src.world.providers.information.KnowledgeFact` — already correctly disambiguated from
  `core/self_model.py`'s `KnowledgeFact` via docstring; not part of this reconciliation question.
- The Knowledge axis's canonical-hash gap — already closed separately
  (`TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP`).

## Acceptance Criteria
- [ ] Real purpose/overlap of `BeliefEntry` vs. `KnowledgeFact` characterized with evidence (not
      assumed) — which domains actually read which, and whether any real behavior depends on the
      split being separate vs. accidental.
- [ ] At least one concrete plausible bug scenario evaluated (contradictory belief/knowledge for the
      same subject) — confirmed present, confirmed absent, or confirmed structurally impossible, with
      reasoning.
- [ ] A decision recorded (keep-and-document, reconcile, or bridge) with plan-owner sign-off, the same
      rigor as the calendar-authority decision.
- [ ] `rpg_design_roadmap.md`'s Knowledge/Belief axis section updated with the decision.
- [ ] If "reconcile" or "bridge" is chosen: a follow-up implementation ticket filed, not implemented
      inline here.

## Related Tickets
- TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY (the precedent this ticket's process mirrors: investigate,
  quantify, decide, defer implementation)
- TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP (closed the separate determinism-gap finding from the same
  brainstorm pass)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` ("Knowledge/Belief axis" section)
- `docs/brainstorm/codex/2026-09-02-core-rpg-knowledge-belief-axis-proposal.md`
- `docs/simulation/belief_and_detour_contract.md`, `docs/simulation/domains/information_contract.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/systems/strategic_systems/belief.py`, `src/core/strategic.py` (`StrategicComponent.beliefs`)
- `src/core/self_model.py` (`KnowledgeFact`, `KnowledgeModelComponent.facts`)
- `src/domains/cooperation/evaluators.py`, `src/systems/strategic_systems/detour.py`
- `src/cognition/knowledge_model.py`, `src/domains/information/{assimilation,schema,phase}.py`

## Assumptions / Open Questions
- Whether the split is intentional-but-undocumented or accidental duplication is the central open
  question this ticket must resolve with evidence, not assume either way going in.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

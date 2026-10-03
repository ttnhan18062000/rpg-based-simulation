---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION
phase: done
date: 2026-09-04
tags: [content]
---

# TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION

## Title
Decide whether BeliefEntry and KnowledgeFact should be reconciled — two parallel belief/knowledge
models with zero cross-references

## Status
DONE

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
- [x] Real purpose/overlap of `BeliefEntry` vs. `KnowledgeFact` characterized with evidence (not
      assumed) — which domains actually read which, and whether any real behavior depends on the
      split being separate vs. accidental. Confirmed via `phase.py`'s own dispatch site: structured
      query responses -> `KnowledgeFact`; raw witnessed events -> `BeliefEntry`. Deliberate split.
- [x] At least one concrete plausible bug scenario evaluated (contradictory belief/knowledge for the
      same subject) — confirmed present, confirmed absent, or confirmed structurally impossible, with
      reasoning. No unified query surface exists, and no live consumer needs one today — a latent,
      not active, gap.
- [x] A decision recorded (keep-and-document, reconcile, or bridge) with plan-owner sign-off, the same
      rigor as the calendar-authority decision. **Option 1 chosen: keep both, document explicitly.**
- [x] `rpg_design_roadmap.md`'s Knowledge/Belief axis section updated with the decision.
- [x] If "reconcile" or "bridge" is chosen: a follow-up implementation ticket filed, not implemented
      inline here. N/A — Option 1 chosen, no merge/bridge ticket needed. A separate, unrelated
      dead-code finding (`"combat_risk"` never written) was filed as its own follow-up,
      `TCK-20260904-COMBAT-RISK-BELIEF-DEAD-READ`.

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
(staging artifacts in `staging_artifacts/TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION/`)

## Related Code Areas
- `src/systems/strategic_systems/belief.py`, `src/core/strategic.py` (`StrategicComponent.beliefs`)
- `src/core/self_model.py` (`KnowledgeFact`, `KnowledgeModelComponent.facts`)
- `src/domains/cooperation/evaluators.py`, `src/systems/strategic_systems/detour.py`
- `src/cognition/knowledge_model.py`, `src/domains/information/{assimilation,schema,phase}.py`

## Assumptions / Open Questions
- Whether the split is intentional-but-undocumented or accidental duplication is the central open
  question this ticket must resolve with evidence, not assume either way going in.

## Implementation Notes
`src/domains/information/phase.py` is the single dispatch site that decides which model new
information becomes: line 69 (`InformationAssimilationService.assimilate()`, structured query
responses -> `KnowledgeFact`), line 162 (`ObservationBeliefBridge.process_observation()`, raw witnessed
events -> `BeliefEntry`). `BeliefEntry`'s contradiction-tracking is real, live-consumed behavior
`KnowledgeFact` has no equivalent for (`detour.py`'s `_score_detour()`: `matching_belief.contradictions
* 25.0` penalty). This is a coherent two-track pipeline, not accidental duplication — Option 1 (keep
both, document) is the correct call; reconciling would be over-engineering given the evidence.

Documented the relationship directly in both `docs/simulation/belief_and_detour_contract.md` and
`docs/simulation/domains/information_contract.md` so a future reader has the cross-reference without
re-deriving it.

Also corrected a factual error found along the way: the roadmap's original brainstorm-pass text claimed
`StrategicComponent.beliefs: Dict[str, BeliefEntry]` — it is actually typed `Dict[str, Any]`
(`src/core/strategic.py:425`), and in practice holds real `BeliefEntry` objects alongside at least one
unrelated ad-hoc key. That ad-hoc key (`"combat_risk"`, `src/domains/cooperation/evaluators.py:47`) was
confirmed dead code — never written anywhere in `src/` — and filed as its own separate, non-blocking
follow-up (`TCK-20260904-COMBAT-RISK-BELIEF-DEAD-READ`), since it's unrelated to this ticket's own
reconciliation question.

## Test Summary
No code changed — decision/investigation/documentation only. No new tests needed.

## Files Changed
- `docs/simulation/belief_and_detour_contract.md` — cross-reference note added.
- `docs/simulation/domains/information_contract.md` — cross-reference note added.
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — Knowledge/Belief axis section updated with
  the decision and the `StrategicComponent.beliefs` typing correction.
- `tickets/todos/TCK-20260904-COMBAT-RISK-BELIEF-DEAD-READ.md` — new, filed as a separate follow-up.

## Completion Summary
Closed the Knowledge/Belief axis's flagged `BeliefEntry`/`KnowledgeFact` reconciliation question.
Confirmed via the real dispatch site (`phase.py`) that the split is deliberate, not accidental
duplication: structured/queried information becomes `KnowledgeFact`, raw/observed information becomes
`BeliefEntry`, each with a genuinely different lifecycle (capacity-bounded vs.
contradiction-tracked-and-decaying). Decision: keep both, document explicitly — no merge/bridge
implementation, matching the evidence rather than over-engineering a fix for a non-problem. Documented
the relationship in both contract docs and the roadmap. Found and separately filed one small,
unrelated dead-code issue (`"combat_risk"`) surfaced during the investigation.

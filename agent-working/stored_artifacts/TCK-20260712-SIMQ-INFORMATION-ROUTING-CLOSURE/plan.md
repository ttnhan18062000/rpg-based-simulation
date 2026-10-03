---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE
artifact_type: plan
tags: [cognition, information, self-model, observability, simulation-quality]
---

# Plan — TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE

**Retrospective reconstruction note:** this file documents the plan that was actually implemented
(commit `0a99c725`, all 7 steps), reconstructed from the ticket's own "Implementation Notes" section
after the fact. The ticket's account states this plan was architecture-reviewed over 2 rounds before
implementation — that claim is the original session's own report and was not independently monitored
or recorded at the time (no `agent-monitoring/` entries exist for that session). This backfill cannot
verify the review-round claim beyond the ticket author's own account; however, the resulting code was
independently re-verified against architecture/Mechanics-Bible constraints via this ticket's own
fresh Architecture-Verify pass (see `stored_artifacts/TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE/`
once finalized, or the ticket's Implementation Notes for the live verification record).

## Ordered Steps

1. **`src/domains/information/resolver.py`** — widen `InformationIntentResolver.resolve()`'s return
   type to `Union[ActionIntent, InformationResponse]`. Affordability gate returns
   `InformationResponse(answer_kind="insufficient_gold", cost_gold=candidate.cost_gold,
   source_id=str(candidate.source_id))` instead of `None`. `ASK_INFORMATION` payload additively gains
   `"expected_certainty"` and `"source_kind"`; existing `"subject"`, `"query_kind"`, `"cost_paid"`
   keys unchanged.
2. **`src/domains/information/phase.py`** — Branch B loops over all candidates from
   `InformationQueryRouter.route()`, calling `resolve()` on each, breaking on the first real
   `ActionIntent` (via `isinstance`). If every candidate is unaffordable, no `EntityUpdate` for the
   tick (unchanged silent-skip for the genuinely-can't-afford-anything case).
3. **`src/observability/event_extractor.py`** — additive `route_new_query` branch (one event, since
   Branch B writes only one property-update pair per tick), inserted after the existing
   `belief_assimilated`/`belief_updated` block, gated on `last_routed_query_tick ==
   prior_state.tick`. Not wired into `InformationScorer.EVENT_TYPES` — out of this step's scope.
4. **`src/engine/intent/action_intent.py`** — `ASK_INFORMATION` branch rewritten to discriminate on
   `"query_kind" in intent.payload`. Absent (adventure domain) → byte-identical pre-fix behavior.
   Present (information domain) → reads `"cost_paid"`, builds an `InformationQuery`, calls
   `InformationResponseNormalizer.normalize()` → `InformationAssimilationService.assimilate()` →
   `dataclass_replace(entity.self_model, knowledge=assim.knowledge_update)`, returns via
   `EntityUpdate.self_model_bundle_set` alongside the real gold deduction — reuses Branch A's
   existing capacity-bounded call chain, no hand-rolled `KnowledgeFact` merge (architecture-review
   round-2 correction over the original hand-rolled approach).
5. **Grade-anchor probe fixture formalized** — `git mv
   config/simulation_quality/profiles/_investigation_probe_urban_political_selfmodel_only.yaml
   config/simulation_quality/profiles/urban_political_selfmodel_probe.yaml`; header comment updated
   to permanent-fixture framing. New `grade_anchors.json` key
   `urban_political_selfmodel_probe_seed42_200t` plus a dedicated
   `test_urban_political_selfmodel_cognition_isolated_grade_anchor` test.
6. **6 new tests** added (see `test_plan.md`), verbatim names from the parent investigation's "New
   Tests Required" section.
7. **`docs/parity_ledger/infrastructure.yaml`** — added `INFRA-267` (new entry); `INFRA-266` left
   untouched as historical pre-fix record.

## Files to Change Per Step

| Step | Files |
|---|---|
| 1 | `src/domains/information/resolver.py` |
| 2 | `src/domains/information/phase.py` |
| 3 | `src/observability/event_extractor.py` |
| 4 | `src/engine/intent/action_intent.py` |
| 5 | `config/simulation_quality/profiles/urban_political_selfmodel_probe.yaml` (renamed), `tests/simulation_quality/fixtures/grade_anchors.json`, `tests/simulation_quality/test_grade_regression.py` |
| 6 | `tests/unit/domains/information/test_phase5_information_intent_resolver.py`, `tests/integration/domains/information/test_phase5_information_belief_phase.py`, `tests/integration/domains/information/test_phase5_branch_b_realworld.py` (new), `tests/unit/observability/test_event_extractor_information2.py` |
| 7 | `docs/parity_ledger/infrastructure.yaml` |

## Explicit Scope Guards (from ticket's Out of Scope)

- Do not change `ENABLE_SELF_MODEL_COGNITION`/`ENABLE_BELIEF_ASSIMILATION` defaults in any shipped
  profile.
- Do not widen into the full belief-assimilation response cycle beyond the 5 numbered fix points.
- Do not touch `SelfAssessmentService`, `NeedInterpretationService`, or `CapabilityEstimateService`.
- Do not combine `ENABLE_ADVENTURE_ROUTING`/AGENCY with self-model flags in the same test.
- `router.py`'s ranking heuristic is NOT touched — confirmed via the unmodified, still-passing
  `test_phase5_information_query_router.py`.

## Dependency Map

Steps 1→2 (phase.py's fallback loop depends on resolver.py's structured signal) → 3 (event
visibility is independent but logically follows once routing can succeed) → 4 (intent-closure is
independent of 1-3 but shares the same `ASK_INFORMATION` payload shape from step 1) → 5 (probe
fixture depends on steps 1-4 being complete, to measure their real effect) → 6 (tests depend on all
of 1-5) → 7 (parity ledger update depends on 6's tests passing).

## Acceptance Criteria Map

| AC | Step(s) |
|---|---|
| Router/Phase/Resolver resolve a real query end-to-end for ≥1 candidate, all 3 seeds | 1, 2 |
| `event_extractor.py` emits a scoreable event for successful routing | 3 |
| Executed `ASK_INFORMATION` intent produces a re-assimilable answer | 4 |
| All 6 new tests pass; cross-tick-boundary anchor passes unmodified | 6 |
| `INFRA-266`/new successor entry updated with passing `test_path` | 7 |
| `make evaluate --dry-run` shows 0 new regressions | 5, 6 |

## Deviations

1. **Scope item 5's literal wording** ("`pending_information_responses`-equivalent entry") was
   substituted with a direct `self_model_bundle_set` write via the existing
   `InformationResponseNormalizer`/`InformationAssimilationService` chain — no durable-write path
   exists for `pending_information_responses` today; building one would be new, unscoped work. Test
   5 verifies this via direct `ActionIntentAdapter.execute()` invocation, not a live multi-tick
   pipeline run (no production call site exists for that adapter).
2. **Plan's literal Step 5 instruction** to "commit the resulting calibration data directory" was not
   followed — `data/calibration/` is repo-wide `.gitignore`d (confirmed: zero calibration
   directories tracked anywhere in this repo). Followed the actual repo convention instead: only
   `grade_anchors.json` and the anchor test are committed; the calibration report itself is
   transient/regenerated per session.

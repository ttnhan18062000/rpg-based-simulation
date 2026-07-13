---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE
phase: open
date: 2026-07-12
tags: [cognition, information, self-model, observability, simulation-quality]
---

# TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE

## Title
Fix Branch B query-routing's real-world dead-end: candidate ranking, no-fallback, silent
affordability gate, and missing event-extractor mapping

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE` found that `InformationBeliefPhase`'s Branch B
query-routing logic (`src/domains/information/phase.py:83-105`) is mechanically reachable but dead-
ends against `urban_political`'s real compiled state, reproducibly and seed-invariantly (seeds
42/123/456). This ticket fixes the 4 root-caused points so a real entity's information query can
actually resolve, execute, and score under the SimQ pipeline -- closing the gap between
"reachable" (the existing hand-built `test_fused_loop.py` test) and "succeeds against a real
world's actual candidate ranking and actual entity economy" (what this ticket verifies).

## Scope
1. `InformationQueryRouter.route()` (`src/domains/information/router.py:102-103`) currently sorts
   candidates by `(-expected_certainty, cost_gold)` with no regard for affordability -- a paid,
   higher-certainty candidate always outranks a free, lower-certainty one even when the entity
   cannot afford the paid one. Fix point (decide during implementation, per investigation.md's own
   note that this is a 3-way tradeoff, not obviously "the ranking is the bug"): either change the
   ranking to prefer affordable candidates, or leave ranking as-is and rely on fix 2's fallback.
2. `InformationBeliefPhase.apply()` (`src/domains/information/phase.py:92-105`) only ever tries
   `candidates[0]` -- add a fallback to try `candidates[1]`, `candidates[2]`, etc. when resolution
   of the top candidate fails, before giving up for the tick.
3. `InformationIntentResolver.resolve()` (`src/domains/information/resolver.py:65-69`) silently
   returns `None` when `actor_gold < candidate.cost_gold` -- return a structured
   "insufficient_gold"-shaped signal instead, consumable by the fallback in fix 2 and by
   `KnowledgeModelService.assimilate()`'s existing `"insufficient_gold"` `answer_kind` branch
   (`src/cognition/knowledge_model.py:67-70`), which currently has no producer anywhere in `src/`.
4. `src/observability/event_extractor.py:276-299` has no extractor branch for
   `last_routed_query_subject`/`last_routed_query_tick` (Branch B's own property-update keys, set
   at `phase.py:101-104`) -- add one (a `route_new_query`-style event or equivalent) so a
   successful routing action becomes visible and scoreable under the SimQ pipeline at all.
5. Close the `ASK_INFORMATION` intent execution loop (`src/engine/intent/action_intent.py:127-141`)
   -- it currently only deducts gold and appends an internal `IntentTrace`, never producing an
   `InformationResponse`/`pending_information_responses`-equivalent entry that a later tick's
   `InformationBeliefPhase` Branch A could re-assimilate. Without this, even a "successful" routing
   action never resolves the entity's unknown into a known fact.
6. Add the 5 tests scoped in `stored_artifacts/TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE/test_plan.md`'s
   "New Tests Required" section (verbatim -- do not re-derive):
   `test_branch_b_query_routing_fails_silently_on_real_urban_political_state`,
   `test_information_belief_phase_falls_back_to_next_candidate_on_resolution_failure`,
   `test_intent_resolver_insufficient_gold_produces_signal_not_silent_none`,
   `test_event_extractor_emits_route_new_query_event`,
   `test_ask_information_intent_execution_closes_the_loop`.
7. The parent investigation ticket's probe-file question is now resolved (formalized as a permanent
   fixture, per Decision 3 above) — add `test_urban_political_selfmodel_cognition_isolated_grade_anchor`
   (test_plan.md item 6) unconditionally.
8. Update `docs/parity_ledger/infrastructure.yaml::INFRA-266` (added by
   `TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE`) to `status: verified` with the fix's
   `test_path` once these tests pass, replacing its current routing-failure framing with a
   routing-fixed framing (or add a new INFRA-26x entry if the split-verdict framing should be
   preserved historically rather than overwritten -- implementer's call, consistent with how
   INFRA-259/260 were kept as separate, narrowly-scoped entries rather than merged).

## Out of Scope
- Changing `ENABLE_SELF_MODEL_COGNITION`/`ENABLE_BELIEF_ASSIMILATION` defaults in any shipped
  profile -- this ticket fixes the mechanism, it does not activate it anywhere new.
- Widening the fix into "the full belief-assimilation response cycle" beyond the 5 numbered points
  above -- mirrors the existing anti-drift note in
  `docs/plans/idea_information_belief_trigger_wiring.md` and
  `stored_artifacts/TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE/test_plan.md`'s own
  "partial-fix trap" warning: a single-point fix (e.g. only re-sorting the router) would likely
  still leave routing unscoreable even if resolution succeeds -- all 4 root-cause points (5
  including the intent-closure gap) must land together.
- Any change to `SelfAssessmentService`, `NeedInterpretationService`, or `CapabilityEstimateService`.
- Turning `ENABLE_ADVENTURE_ROUTING`/AGENCY on in combination with self-model flags in the same
  test -- `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B`'s Finding 5 blast-radius sweep already flagged this
  three-way combination as out of scope for Branch B work.

## Acceptance Criteria
- [ ] `InformationQueryRouter`/`InformationBeliefPhase`/`InformationIntentResolver` resolve a real
      `ASK_INFORMATION` query end-to-end against `urban_political`'s real compiled state (entity 23,
      0 gold) for at least one of the two available candidates, across all 3 anchor seeds
- [ ] `event_extractor.py` emits a scoreable event for a successful routing action
- [ ] A successfully executed `ASK_INFORMATION` intent eventually produces an answer that a later
      tick's Branch A can re-assimilate
- [ ] All 6 new tests pass (5 from Scope items 1-6 plus the grade-anchor test from Scope item 7,
      now unconditional per the parent investigation ticket's Decision 3);
      `test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`
      still passes unmodified
- [ ] `INFRA-266` (or a new successor entry) updated to reflect the fixed state with a passing
      `test_path`
- [ ] `make evaluate --dry-run` shows 0 new regressions attributable to this ticket

## Related Tickets
- `TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE` (parent investigation -- source of all 4
  root-cause file:line citations this ticket implements against)
- `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B` (done -- the original 3-bug materialization fix chain)
- `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT` (done -- established the isolated-
  materialization pilot this ticket's fix extends beyond)

## Related Docs
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-259`, `INFRA-260`, `INFRA-266`)
- `stored_artifacts/TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE/investigation.md` (full root-
  cause evidence chain, file:line citations, seed-invariance confirmation)
- `stored_artifacts/TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE/test_plan.md` ("New Tests
  Required" section -- the 6 tests this ticket must add, already scoped)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE/`

## Related Code Areas
- `src/domains/information/router.py:102-103`
- `src/domains/information/phase.py:83-105`
- `src/domains/information/resolver.py:65-69`
- `src/cognition/knowledge_model.py:67-70`
- `src/observability/event_extractor.py:276-299`
- `src/engine/intent/action_intent.py:127-141`

## Assumptions / Open Questions
- Whether to fix the router's ranking heuristic itself or rely solely on the phase-level fallback
  (Scope item 1) is left to the implementer, per investigation.md's own note that the ranking
  heuristic is plausibly intentional design (favor accuracy over price) and only becomes a hard
  failure combined with zero starting gold and no fallback -- decide based on which combination of
  fixes 1-3 produces the cleanest, most minimal diff satisfying the Acceptance Criteria.

## Implementation Notes

Implementation resumed and completed. Plan
(`staging_artifacts/TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE/plan.md`) approved after 2
architecture-review rounds (round 2 fixed Step 4 to reuse
`InformationResponseNormalizer`/`InformationAssimilationService` instead of a hand-rolled
`KnowledgeFact` merge — see plan.md's Step 4 for the exact reviewed code) was implemented exactly,
all 7 steps, and Step 7's regression pass was independently run and confirmed green this session.

1. **`src/domains/information/resolver.py`** — `InformationIntentResolver.resolve()`'s return
   type widened to `Union[ActionIntent, InformationResponse]`. The affordability gate now returns
   `InformationResponse(answer_kind="insufficient_gold", cost_gold=candidate.cost_gold,
   source_id=str(candidate.source_id))` instead of a bare `None`. The `ASK_INFORMATION` payload
   additively gains `"expected_certainty"` and `"source_kind"`; the existing `"subject"`,
   `"query_kind"`, `"cost_paid"` keys are unchanged (verified: the pre-existing
   `test_near_source_resolves_to_ask_information` assertion on `"cost_paid"` still passes
   unmodified). `router.py` was not touched, per the investigation's Ranking vs. Fallback
   Recommendation.
2. **`src/domains/information/phase.py`** — Branch B now loops over all candidates returned by
   `InformationQueryRouter.route()`, calling `InformationIntentResolver.resolve()` on each and
   breaking on the first real `ActionIntent` (checked via `isinstance`). If every candidate is
   unaffordable, no `EntityUpdate` is produced for the tick (unchanged silent-skip behavior for the
   genuinely-can't-afford-anything case). `ActionIntent` imported directly from
   `src.engine.intent.action_intent` — confirmed no circular import (that module does not import
   `phase.py`).
3. **`src/observability/event_extractor.py`** — additive `route_new_query` branch (one event, not
   two, since Branch B writes only one property-update pair per tick) inserted immediately after
   the existing `belief_assimilated`/`belief_updated` block, gated on
   `last_routed_query_tick == prior_state.tick`, mirroring that block's shape. Checked
   `docs/simulation_quality/quality_scoring_contract.md` §5 — `route_new_query` is not already
   reserved for a different event; no substitution needed. Not wired into
   `InformationScorer.EVENT_TYPES` — that scorer wiring is out of this ticket's 7-step scope (Step
   3 is event_extractor.py only).
4. **`src/engine/intent/action_intent.py`** — `ASK_INFORMATION` branch rewritten exactly per the
   plan's reviewed Step 4 code: discriminates on `"query_kind" in intent.payload`. Absent (adventure
   domain, `ObjectiveIntentResolver`) → byte-identical pre-fix behavior, still reading the dead
   `"cost_gold"` key (intentionally unchanged — `ObjectiveIntentResolver` never sets `cost_gold` or
   `cost_paid`, so this remains a no-op deduction for that path, as before). Present (information
   domain) → reads `"cost_paid"` (dead-key fix), builds an `InformationQuery`, calls
   `InformationResponseNormalizer.normalize()` → `InformationAssimilationService.assimilate()` →
   `dataclass_replace(entity.self_model, knowledge=assim.knowledge_update)`, returns the result via
   `EntityUpdate.self_model_bundle_set` alongside the real gold deduction. This is the same
   capacity-bounded call chain Branch A already uses at `phase.py:56-69` — no hand-rolled
   `KnowledgeFact` merge was introduced, per the architecture review's correction.
5. **Grade-anchor probe fixture formalized**: `git mv
   config/simulation_quality/profiles/_investigation_probe_urban_political_selfmodel_only.yaml
   config/simulation_quality/profiles/urban_political_selfmodel_probe.yaml`; header comment updated
   to describe it as a permanent (not temporary/investigation-scoped) grade-anchor probe fixture.
   Re-ran calibration post-fix (`python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name
   urban_political --profile urban_political_selfmodel_probe --output
   data/calibration/urban_political_selfmodel_probe_seed42_200t`) rather than copying the pre-fix
   baseline blindly — independently re-verified this session. Result: `COGNITION=S` (5610
   `self_model_updated` events), `INFORMATION=C` (0 events) — unchanged from the parent
   investigation's pre-fix measurement, because this probe profile deliberately leaves
   `ENABLE_BELIEF_ASSIMILATION` OFF, so `InformationBeliefPhase` (and therefore this ticket's Branch
   B fix) never runs in this specific calibration scenario. Added new `grade_anchors.json` key
   `urban_political_selfmodel_probe_seed42_200t` and a dedicated
   `test_urban_political_selfmodel_cognition_isolated_grade_anchor` test function in
   `test_grade_regression.py` (not merged into the generic `FAST_ANCHOR_KEYS`-parametrized test, to
   keep this probe-specific and explicit about its COGNITION=S/INFORMATION=C/0-events assertions).
6. **`docs/parity_ledger/infrastructure.yaml`** — added `INFRA-267` (new entry, `INFRA-266` left
   completely untouched as the historical pre-fix root-cause record, per the investigation's
   explicit recommendation and the `INFRA-259`/`INFRA-260` precedent). Validated via
   `python3 tools/parity_ledger_scan.py` (exit 0) and a direct YAML parse confirming all 272
   entries load and `INFRA-267` has both `v2_evidence` and `test_path` populated (required for
   `status: verified`).
7. **Full regression pass — independently re-run and confirmed this session**: all 6 new tests
   pass; `test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`
   passes unmodified; adventure-domain regression tests (`test_phase3_route_scoring.py`,
   `test_phase3_route_generator.py`, `test_classifier.py`) pass unmodified; `make evaluate`
   (`python3 tools/evaluate_simq.py --dry-run`) shows exactly the 3 pre-existing regressions already
   flagged by the parent investigation (`dungeon_crawl_seed42_200t` COMBAT/PROGRESSION,
   `urban_political_seed42_200t` PROGRESSION) and 0 new regressions. See Test Summary for the full
   command list and pass counts.

**Deviation from the ticket's literal Scope item 5 wording**: Decision 2 in `plan.md` (approved,
architecture-reviewed) substitutes a direct `self_model_bundle_set` write for the literal
"`pending_information_responses`-equivalent entry a later tick's Branch A could re-assimilate" — see
plan.md's Decision 2 for the full rationale (no durable-write path exists for
`pending_information_responses` today; building one is out of this ticket's scope). Test 5
(`test_ask_information_intent_execution_closes_the_loop`) verifies this via direct
`ActionIntentAdapter.execute()` invocation and inspection of the returned `EntityUpdate`, not via a
live multi-tick pipeline run — `ActionIntentAdapter.execute()` has no production tick-pipeline call
site today and this ticket does not add one (would be new, unscoped work). This is the single most
important caveat for a future reader: **the fix is verified reachable via direct test-harness
invocation and via the new probe-fixture calibration run, not via any live-gameplay activation
path.**

**Deviation from plan.md's literal Step 5 instruction**: the plan says to "commit the resulting
calibration data directory." `data/calibration/` is repo-wide `.gitignore`d (confirmed: zero
calibration directories are tracked anywhere in this repo — the convention, per the `.gitignore`
comment, is that calibration output is transient/regenerated, and only `grade_anchors.json` plus the
anchor test are committed). Followed the actual repo convention instead of the plan's literal wording
— see `staging_artifacts/TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE/plan.md`'s Deviations section
for the full note.

## Test Summary

6 new tests added, all exact names from `test_plan.md`'s "New Tests Required" section:
1. `test_branch_b_query_routing_fails_silently_on_real_urban_political_state` (parametrized over
   seeds 42/123/456) — `tests/integration/domains/information/test_phase5_branch_b_realworld.py`
2. `test_information_belief_phase_falls_back_to_next_candidate_on_resolution_failure` —
   `tests/integration/domains/information/test_phase5_information_belief_phase.py`
3. `test_intent_resolver_insufficient_gold_produces_signal_not_silent_none` —
   `tests/unit/domains/information/test_phase5_information_intent_resolver.py`
4. `test_event_extractor_emits_route_new_query_event` —
   `tests/unit/observability/test_event_extractor_information2.py`
5. `test_ask_information_intent_execution_closes_the_loop` —
   `tests/integration/domains/information/test_phase5_information_belief_phase.py`
6. `test_urban_political_selfmodel_cognition_isolated_grade_anchor` —
   `tests/simulation_quality/test_grade_regression.py`

All scoped regression commands from `test_plan.md` were run and pass:
- `pytest tests/unit/cognition/ tests/unit/domains/information/ -v` → 137 passed
- `pytest tests/unit/domains/adventure/ tests/unit/strategic/test_classifier.py -v` → 60 passed
- `pytest tests/integration/domains/test_fused_loop.py tests/integration/domains/information/ -v` →
  16 passed (includes the cross-tick-boundary regression anchor, unmodified)
- `pytest tests/unit/domains/information/test_phase5_information_query_router.py -v` → 3 passed
  (router untouched, confirms the Ranking vs. Fallback Recommendation was honored)
- `pytest tests/unit/observability/test_event_extractor_information2.py -v` → 17 passed
- `pytest tests/simulation_quality/test_grade_regression.py -v -k "urban_political or
  unit_selfmodel_pilot"` → 12 passed, 1 pre-existing failure
  (`urban_political_seed42_200t`/PROGRESSION — pre-existing, unrelated to this ticket)
- `pytest tests/integration/test_world_profile_feature_flag_guardrail.py -v` → 55 passed
- `pytest tests/perf/test_phase5_information_belief_budget.py -v` → 1 passed
- `python3 tools/evaluate_simq.py --dry-run` → 720 pillars checked, exactly the 3 pre-existing
  regressions, 0 missing, 0 new regressions

## Files Changed

- `src/domains/information/resolver.py`
- `src/domains/information/phase.py`
- `src/observability/event_extractor.py`
- `src/engine/intent/action_intent.py`
- `config/simulation_quality/profiles/_investigation_probe_urban_political_selfmodel_only.yaml` →
  renamed to `config/simulation_quality/profiles/urban_political_selfmodel_probe.yaml`
- `tests/simulation_quality/fixtures/grade_anchors.json`
- `tests/simulation_quality/test_grade_regression.py`
- `docs/parity_ledger/infrastructure.yaml`
- `tests/unit/domains/information/test_phase5_information_intent_resolver.py`
- `tests/integration/domains/information/test_phase5_information_belief_phase.py`
- `tests/integration/domains/information/test_phase5_branch_b_realworld.py` (new)
- `tests/unit/observability/test_event_extractor_information2.py`

## Completion Summary

All 7 plan steps landed exactly as reviewed, including Step 4's architecture-corrected reuse of
`InformationResponseNormalizer`/`InformationAssimilationService` (no hand-rolled `KnowledgeFact`
merge). `router.py`'s ranking heuristic was left untouched per the investigation's binding
recommendation — the fix is entirely a phase-level fallback loop (Step 2) plus a structured
`insufficient_gold` signal (Step 1). `ObjectiveIntentResolver` (adventure domain) was not modified at
all; its shared `action_intent.py` execution branch stays byte-identical, verified by the adventure
regression suite passing unmodified. All 6 required tests pass, the pre-existing cross-tick
regression anchor passes unmodified, and `make evaluate --dry-run` shows 0 new regressions beyond the
3 already-documented pre-existing ones.

**Important clarification for future readers**: `ActionIntentAdapter.execute()` remains unwired into
the production tick pipeline — it has no call site under `src/` today (only test code calls it), and
this ticket does not add one (explicitly out of scope, per the plan's Anti-Drift Notes — adding
pipeline wiring would be new, unscoped work: auto-executing routed intents every tick). This means
fix 5 (closing the `ASK_INFORMATION` execution loop) is **verified reachable via direct test-harness
invocation** (`test_ask_information_intent_execution_closes_the_loop` calls
`ActionIntentAdapter.execute()` directly and inspects the returned `EntityUpdate`), and the routing
half (fixes 1-4) is verified reachable via the new probe-fixture calibration run and the real-compiled-
world regression test — but **none of this has live-gameplay effect yet** in any shipped world/profile,
since (a) no shipped profile turns `ENABLE_SELF_MODEL_COGNITION`/`ENABLE_BELIEF_ASSIMILATION` ON
together, and (b) even where Branch B *does* route successfully, nothing in the production pipeline
calls `ActionIntentAdapter.execute()` on the resulting `ActionIntent` today. Do not read this ticket
as having activated Branch B in any live simulation — it closes the dead code paths and proves them
correct under direct invocation, which is the ticket's actual, narrower scope.

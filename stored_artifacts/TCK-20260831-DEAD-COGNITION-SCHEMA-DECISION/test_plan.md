---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION
artifact_type: test_plan
tags: [cognition]
---

# Test Plan — TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION

## Regression Surface

Existing tests that must keep passing, grouped by domain. Several of these files directly
construct/assert against the dead `cognition.py::SelfModel`/`SubjectiveModel` shell and **will need
edits, not just a pass-through run**, if the "cut" branch is chosen — listed explicitly so the
implementer doesn't discover them mid-change:

**Unit — cognition schema (will require edits under "cut"):**
- `tests/unit/entity/test_phase11_cognition_model_schema.py` — asserts `cog.subjective.self` is a
  `SelfModel` instance (line 33) and exercises all four `cognition_accessors.py` functions against
  the dead path (lines 43-49). Must be rewritten to match whichever schema shape "cut" produces
  (either the `self` field removed from `SubjectiveModel`, or accessors repointed).
- `tests/unit/domains/perception/test_phase12_attention_focus_service.py` — hand-builds
  `SelfModel(needs=needs)` → `SubjectiveModel(self=self_model)` → `CognitionModel(subjective=subjective)`
  (lines 8-15) to drive `AttentionFocusService.get_attention_focus()`. This is the exact
  "hand-built cognition.py shell" the ticket's AC forbids as proof — must be rewritten to construct
  the state via the real `SelfModelUpdatePhase`/`entity.self_model` path instead.

**Integration — perception/attention scenarios (will require edits under "cut"):**
- `tests/integration/scenarios/test_phase12_perception_attention_scenarios.py` — same
  hand-built-`SelfModel` pattern (line 13), feeding `AttentionFocusService` via
  `PerceptionUpdatePhase`.
- `tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py` — constructs
  `SelfModel(recovery=recovery)` (line 13); only the `RecoveryState`-via-`SelfModel` construction
  needs updating if `RecoveryState` moves or is re-homed — confirm during implementation whether this
  file's assertions touch `needs`/`awareness`/`capability` at all (a quick read shows it only uses
  `.recovery`, so this file may be lower-risk than the two above, but must still be checked against
  whatever final schema shape "cut" leaves for `RecoveryState`).
- `tests/integration/domains/perception/test_phase12_perception_phase.py` — exercises
  `PerceptionUpdatePhase.run()` directly; does not construct `SelfModel` but does exercise the
  `AttentionFocusService.get_attention_focus()` call inside step 2 — must keep passing with the
  repointed read.

**Unit — perception filter/salience (no `SelfModel` construction, but exercise the affected call chain):**
- `tests/unit/domains/perception/test_phase12_perception_filter_service.py`
- `tests/unit/domains/perception/test_phase17_decision_trace_scenarios.py` (imports `SelfModel` per
  graphify's edge list — confirm during implementation whether it constructs one or only imports the
  type)

**Unit — real self-model path (must stay green, proves the "cut" repoint target still works):**
- `tests/unit/config/test_phase10_feature_flags.py` (`ENABLE_SELF_MODEL_COGNITION` flag mode tests)
- `tests/certification/test_phase10_enhanced_determinism_parity.py`
- `tests/unit/core/test_entity_integrity.py` (hash-stability regression guard, explicitly documents
  `ENABLE_SELF_MODEL_COGNITION` OFF as the shipped baseline — must confirm this guard still holds
  after the `cognition.py` schema shape changes, since it changes `CognitionModel.to_canonical_dict()`'s
  output)
- `tests/integration/test_world_profile_feature_flag_guardrail.py` (asserts
  `ENABLE_SELF_MODEL_COGNITION` stays OFF in the fixture world profile)
- `tests/integration/domains/information/test_phase5_information_belief_phase.py`
- `tests/integration/domains/test_fused_loop.py`
- `tests/architecture/test_adventure_routing_flag_inert.py`

**Determinism / canonical-hash regression (must re-verify after schema shape change):**
- `tests/unit/entity/` — full directory, since `EntityState.to_canonical_dict()`'s shape changes
- `tests/certification/` — canonical hash / replay parity suite

**Consumers of the real `entity.self_model` path (must stay green, unaffected by this ticket but
prove no accidental cross-wiring):**
- `tests/unit/domains/adventure/` (generator/scoring `entity.self_model.*` reads)
- `tests/unit/engine/` (tactical.py, `lead_contradiction.py`)
- `tests/unit/domains/information/` (assimilation.py)

## New Tests Required

Per acceptance criteria:

1. **AC — explicit keep/cut decision recorded**
   - Test name: `test_cognition_domain_ownership_records_self_model_decision` (or equivalent doc-content
     assertion, matching repo convention for doc-content guard tests, e.g.
     `tests/tools/test_cognition_strategy_skill_content.py`'s pattern of asserting on doc text)
   - Category: unit (doc-content guard)
   - Verifies: `docs/architecture/cognition_domain_ownership.md` (or the new ADR, whichever the Plan
     phase chooses) contains an explicit, unambiguous statement of the keep/cut decision for
     `SelfModel`/`SubjectiveModel.self` — not just a mention.
   - Location: `tests/tools/` (mirrors existing doc-content guard test placement)

2. **If cut — schema removal proof**
   - Test name: `test_subjective_model_has_no_self_field` (or equivalent)
   - Category: unit / architecture guard
   - Verifies: `SubjectiveModel` no longer declares a `self` field (or `dataclasses.fields()`
     introspection confirms its removal), and `SelfModel`/`RecoveryState` (if also removed) are no
     longer importable from `src.core.cognition`.
   - Location: `tests/unit/entity/test_phase11_cognition_model_schema.py` (rewritten) or a new
     `tests/architecture/test_dead_cognition_schema_removed.py` guard, matching the pattern of
     `tests/integrity/test_logic_guards.py::test_evolution_service_deleted_and_not_reintroduced` from
     `TCK-20260824-WIRE-ORPHANED-MECHANISMS`.

3. **If cut — accessor repoint proof**
   - Test name: `test_cognition_accessors_read_real_self_model_path`
   - Category: unit
   - Verifies: `get_self_awareness`/`get_need_interpretation`/`get_capability_estimate` (repointed)
     return `entity.self_model.self_awareness`/`.needs`/`.capabilities` respectively, using a real
     `EntityState` (not a hand-built `cognition.py` shell).
   - Location: `tests/unit/entity/test_phase11_cognition_model_schema.py` (rewritten section) or
     `tests/unit/core/test_cognition_accessors.py` (new, if the schema test file is being
     substantially restructured).

4. **If cut — `AttentionFocusService` repoint proof, using the real `SelfModelUpdatePhase` path
   (ticket AC's explicit requirement, "not a hand-built cognition.py shell")**
   - Test name: `test_attention_focus_reads_real_self_model_dominant_need`
   - Category: integration
   - Verifies: build an `EntityState` with real biological/attribute pressure such that
     `SelfAssessmentService`/`NeedInterpretationService` (via `SelfModelUpdatePhase.run()`) produce a
     genuine `dominant_need` (e.g. `"healing"`) on `entity.self_model.needs.dominant_need`, then call
     `AttentionFocusService.get_attention_focus()` on the resulting entity and assert the correct
     focus tags (`"healing_resource"`, `"healer"`, `"safe_place"`) are produced — proving the read
     path is now correctly wired end-to-end from the real writer, not asserted via a synthetic
     `cognition.py::SelfModel(needs=...)` shortcut.
   - Location: `tests/integration/domains/perception/test_phase12_perception_phase.py` (extend) or a
     new `tests/integration/scenarios/test_self_model_attention_focus_integration.py`, since
     `PerceptionUpdatePhase` is not pipeline-wired (Investigation finding 2) and this test must
     therefore call `SelfModelUpdatePhase.run()` then `AttentionFocusService.get_attention_focus()`
     directly rather than via `AuthoritativeApplyPipeline.refine()`.

5. **If kept — real writer proof (only if Plan chooses "keep")**
   - Test name: `test_self_model_writer_populates_cognition_subjective_self`
   - Category: integration
   - Verifies: whatever new writer is added populates `entity.cognition.subjective.self.needs.dominant_need`
     via the authoritative `EntityUpdate`/apply path (not a direct mutation), with a real trigger
     condition (mirroring `SelfModelUpdatePhase`'s own dirty-check pattern).
   - Location: new file under `tests/unit/domains/` or `tests/integration/domains/`, colocated with
     wherever the new writer service lives.

6. **Canonical-hash shape regression guard (both branches)**
   - Test name: `test_cognition_canonical_dict_shape_after_self_model_decision`
   - Category: architecture guard
   - Verifies: `CognitionModel.empty().to_canonical_dict()` produces the expected key shape post-change
     (no `subjective.self` key if cut; the field present and correctly serializing if kept), and that
     `EntityState.to_canonical_dict()` still round-trips deterministically (two independently
     constructed default entities produce identical canonical dicts) — extends the existing
     `test_cognition_model_serializes_deterministically` pattern
     (`tests/unit/entity/test_phase11_cognition_model_schema.py:38-41`).
   - Location: `tests/unit/entity/test_phase11_cognition_model_schema.py`

7. **Idea 22 / idea 24 resolution recorded (ticket-body assertion, not source-code test)**
   - No automated test — this AC is satisfied by the ticket's own `## Assumptions / Open Questions`
     or `## Completion Summary` text recording the resolution evidenced in this investigation's
     "Prior Work" section. If the repo's doc-content guard convention (see item 1) is extended to
     cover this too, a single combined guard test can assert both the decision record and the idea
     22/24 resolution text are present in the closed ticket.

## Scoped Pytest Commands

Never `pytest tests/`. Scoped to the cognition/self-model/perception domains and their direct
consumers, plus the determinism/certification suites that observe canonical-hash shape:

```
.venv/bin/python3 -m pytest \
  tests/unit/entity/ \
  tests/unit/core/ \
  tests/unit/domains/perception/ \
  tests/integration/domains/perception/ \
  tests/integration/scenarios/test_phase12_perception_attention_scenarios.py \
  tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py \
  tests/unit/domains/adventure/ \
  tests/unit/engine/ \
  tests/unit/domains/information/ \
  tests/unit/config/test_phase10_feature_flags.py \
  tests/integration/test_world_profile_feature_flag_guardrail.py \
  tests/integration/domains/information/test_phase5_information_belief_phase.py \
  tests/integration/domains/test_fused_loop.py \
  tests/architecture/test_adventure_routing_flag_inert.py \
  tests/certification/ \
  tests/integrity/test_logic_guards.py \
  -m "not slow"
```

Run with the repo venv (`bare python3` lacks `pydantic` in this sandbox, per prior tickets'
Test Summary notes). If the structural test-scope-coverage backstop
(`tools/gate_checks/test_scope_coverage_static.py`) flags a gap against the actual changed files
(likely `src/core/cognition.py`, `src/core/cognition_accessors.py`,
`src/domains/perception/service.py`, plus whichever test files are edited), re-scope to a strict
superset per the pattern `TCK-20260824-RELATIONSHIP-ROLE-FIELD` used (it added `tests/unit/core/`
when the backstop flagged `src/core/models/social.py` as insufficiently covered).

## Anti-Drift Test Guards

- **Guard against re-introducing dead `SelfModel(...)` hand-construction as test proof.** If "cut" is
  chosen, a lint/architecture check (or a simple `grep`-based guard test, mirroring
  `test_evolution_service_deleted_and_not_reintroduced`'s pattern) should assert no test file
  constructs `cognition.py::SelfModel(...)` directly anymore — forcing any future perception/attention
  test to go through the real `SelfModelUpdatePhase` path instead.
- **Guard against `entity.self_model` / `entity.cognition.subjective.self` path confusion.** A test
  should assert the two are genuinely distinct `EntityState` fields (or, if cut, that only
  `entity.self_model` exists) — catching any future accidental re-introduction of a parallel
  self-model representation under `cognition.py`, per the investigation's "Risk if keep is chosen"
  finding about durable-state duplication.
- **Guard `EmotionalModel`/`PerceptionModel`/`TemporalModel` are untouched.** Since the cut is scoped
  specifically to `SelfModel`/`SubjectiveModel.self`, run the existing
  `test_near_death_hardening_emotion.py` (from `TCK-20260824-WIRE-ORPHANED-MECHANISMS`) and
  `tests/unit/domains/memory/` (if present) unmodified as a sibling-field regression guard — a green
  result proves the cut did not accidentally widen into the live/flag-gated sibling fields
  identified in Investigation finding 3.
- **Guard the real `self_model.py` consumers stay unaffected.** `tests/unit/domains/adventure/`,
  `tests/unit/engine/` (tactical/lead_contradiction), and `tests/unit/domains/information/`
  (assimilation) all read `entity.self_model.*` today and must produce identical results before and
  after this ticket — these tests exercise the "real" self-model path this ticket does not modify,
  and a diff in their output would indicate an accidental cross-wiring between the two systems.
- **Guard `ENABLE_SELF_MODEL_COGNITION` stays OFF in production world profiles.** Re-run
  `tests/integration/test_world_profile_feature_flag_guardrail.py` unmodified — this ticket must not
  change the flag's rollout state, only the dead-code path it (currently, incidentally) helps mask.

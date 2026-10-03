---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION
artifact_type: plan
tags: [cognition]
---

# Implementation Plan — TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION

## Summary

**Decision: CUT.** `core/cognition.py::SelfModel` and `SubjectiveModel.self` have zero production
constructions anywhere (investigation finding 1, re-confirmed by direct read of
`src/core/cognition.py`, `src/core/cognition_accessors.py`) and the real self-model system
(`src/core/self_model.py::SelfModelBundle`, `entity.self_model`) is already wired, flag-gated, and
has 6+ real consumers — adding a second writer for the `cognition.py` copy would create an
unreconciled durable-state duplication CLAUDE.md's Architecture Rule warns against. This plan removes
`SelfModel`/`SubjectiveModel.self` and repoints every dead reader (`cognition_accessors.py`'s three
functions, `AttentionFocusService.get_attention_focus()`) to the real `entity.self_model.*` path,
proven by tests that exercise the real `SelfModelUpdatePhase` writer rather than a hand-built
`cognition.py` shell. `RecoveryState` — nested inside `SelfModel` today but, per a direct read of
`src/domains/emotion/recovery_service.py`, independently imported and used by
`RecoveryReadinessService` — is explicitly **kept in place, untouched**, correcting an inaccuracy in
`investigation.md`'s Anti-Drift Hazards (see Step 1 and Anti-Drift Notes). Wiring
`PerceptionUpdatePhase` into the pipeline is explicitly out of scope (a separate, larger orphan-phase
gap) and is recorded as a disclosed follow-up in the ticket rather than silently expanded into. Idea
22/24 open questions are resolved by recording the investigation's confirmed findings directly in the
ticket. A new parity ledger entry (`STRAT-261`) documents the `AttentionFocusService` repoint. The
determinism/canonical-hash risk is verified, not just flagged: `grep -rln "subjective\.self\|SelfModel(" tests/certification/ data/`
and a broader `grep -rln "subjective" tests/certification/ data/` both return zero hits, and no test
anywhere pins a literal canonical-hash string value — no certification/replay fixture embeds the old
`subjective.self`-inclusive shape, so no fixture regeneration is required.

## Steps

### Step 1 — Cut `SelfModel`/`SubjectiveModel.self` from `src/core/cognition.py`; keep `RecoveryState` untouched
**Files:** `src/core/cognition.py`

**Change:**
- Remove the `SelfModel` dataclass in full (`src/core/cognition.py:118-132`).
- Remove the `self: SelfModel = field(default_factory=SelfModel)` field from `SubjectiveModel`
  (`src/core/cognition.py:214`).
- Update `SubjectiveModel.to_canonical_dict()` (`src/core/cognition.py:220-228`) to remove the
  `"self": self.self.to_canonical_dict()` entry (line 223) — the returned dict's remaining keys
  (`perception`, `knowledge`, `risk`, `time`, `emotion`) are unchanged.
- Remove the now-unused imports `SelfAwarenessComponent`, `NeedInterpretationComponent`,
  `CapabilityEstimateComponent` from the top-of-file import block
  (`src/core/cognition.py:14-21`) — confirmed by reading the full file body that these three are
  referenced *only* inside the deleted `SelfModel` class (lines 121-123) and nowhere else in
  `cognition.py`. **Do not** remove `KnowledgeModelComponent`, `KnowledgeFact`, or `UnknownFact` from
  that same import block — `KnowledgeModelComponent` is still used at `SubjectiveModel.knowledge`
  (line 215); `KnowledgeFact`/`UnknownFact` are pre-existing unused imports unrelated to this
  ticket's scope (leave them exactly as found — do not opportunistically clean up unrelated dead
  imports).
- **Do NOT touch `RecoveryState`** (`src/core/cognition.py:99-115`). Correction to
  `investigation.md`'s Anti-Drift Hazards, which stated `RecoveryState` was "only referenced from
  within `SelfModel`": a direct read of `src/domains/emotion/recovery_service.py:9,15,23` shows
  `RecoveryReadinessService.is_ready_to_retry(state: RecoveryState, ...)` and
  `.register_near_death(state: RecoveryState, ...)` both import `RecoveryState` directly from
  `src.core.cognition` and operate on it as a free-standing value — independent of `SelfModel`. If
  `RecoveryState` were deleted, `src/domains/emotion/recovery_service.py`'s import would break.
  Separately verified (`grep -rn "RecoveryReadinessService|register_near_death|is_ready_to_retry" src/`):
  `RecoveryReadinessService` itself has zero production callers (only its own file and
  `src/domains/emotion/__init__.py`'s re-export reference it) — it is a second, distinct dead-code
  cluster. The ticket's resolve-instruction #1 names only `SelfModel`, `SubjectiveModel.self`, and
  the 3 accessors for removal — `RecoveryState` is not named, so it is out of this ticket's scope
  either way. Leave `RecoveryState`'s class definition exactly where it is (still importable from
  `src.core.cognition`); it simply stops being referenced as a field inside `SelfModel`, which no
  longer exists.

**Do NOT touch:** `PerceptionModel`, `EmotionalModel`, `TemporalModel`, `MotivationModel`,
`RelationshipModel`, `SpatialMemory`, `RiskModel`, `MemoryModel`, `CommitmentModel`, or any other
dataclass in `cognition.py` — all verified still-referenced per investigation finding 3. Do not
delete or restructure `RecoveryState` (see above). Do not touch `cognition_accessors.py`'s
`get_knowledge_model` (unrelated, unaffected field).

**Verify:** `tests/unit/entity/test_phase11_cognition_model_schema.py` (rewritten in Step 4) —
`dataclasses.fields()` introspection confirms `SubjectiveModel` no longer declares a `self` field and
`SelfModel` is no longer importable from `src.core.cognition`.

---

### Step 2 — Repoint `src/core/cognition_accessors.py`'s three dead accessors to `entity.self_model.*`
**Files:** `src/core/cognition_accessors.py`

**Change:** Per `src/core/self_model.py:224-235`, `SelfModelBundle`'s fields are named
`self_awareness` / `needs` / `capabilities` / `knowledge` — flatter than `cognition.py`'s
`SelfModel.awareness` / `.needs` / `.capability`. Repoint exactly:
- `get_self_awareness` (`src/core/cognition_accessors.py:12-14`):
  `entity.cognition.subjective.self.awareness` → `entity.self_model.self_awareness`
- `get_need_interpretation` (`src/core/cognition_accessors.py:16-18`):
  `entity.cognition.subjective.self.needs` → `entity.self_model.needs`
- `get_capability_estimate` (`src/core/cognition_accessors.py:20-22`):
  `entity.cognition.subjective.self.capability` → `entity.self_model.capabilities`

Update each function's docstring comment ("Helper to read X from new nested path") to say it reads
from the real `entity.self_model` path, not the legacy `cognition.subjective` path, so the comment
doesn't mislead a future reader.

**Do NOT touch:** `get_knowledge_model` (`src/core/cognition_accessors.py:24-26`) — reads
`entity.cognition.subjective.knowledge`, a genuinely live, unaffected field (Step 1 does not touch
`SubjectiveModel.knowledge`). The module's imports of `SelfAwarenessComponent`,
`NeedInterpretationComponent`, `CapabilityEstimateComponent`, `KnowledgeModelComponent` from
`src.core.self_model` (`cognition_accessors.py:5-10`) are unchanged — they are already imported from
`self_model.py`, not `cognition.py`, so no import-line edit is needed here.

**Verify:** New test `test_cognition_accessors_read_real_self_model_path` (Step 4) — asserts
`get_self_awareness(entity) == entity.self_model.self_awareness`, and likewise for
`get_need_interpretation`/`get_capability_estimate`, using a real `EntityState` (no hand-built
`cognition.py` shell).

---

### Step 3 — Repoint `AttentionFocusService.get_attention_focus()` to the real self-model path
**Files:** `src/domains/perception/service.py`

**Change:** `src/domains/perception/service.py:22`:
`dominant_need = entity.cognition.subjective.self.needs.dominant_need` →
`dominant_need = entity.self_model.needs.dominant_need`.

**Other writers/readers of this line's inputs, checked for interaction:**
- `entity.self_model` itself has exactly one production writer, `SelfModelUpdatePhase.apply()`
  (`src/cognition/self_model_phase.py:32-74`), wired at `src/engine/pipeline.py:164` behind
  `ENABLE_SELF_MODEL_COGNITION` (`FeatureMode.OFF` by default, `src/domains/optimization/feature_flags.py:19`).
  This repoint does not change that writer or its flag gating — it only changes which field
  `AttentionFocusService` reads.
- `AttentionFocusService.get_attention_focus()` has exactly two callers in `src/`:
  `src/domains/perception/phase.py:40` (`PerceptionUpdatePhase.run()` step 2) and
  `src/domains/perception/filter.py:55` (`PerceptionFilterService.filter()`, itself only called from
  `PerceptionUpdatePhase.run()` step 3). Neither caller needs any change — both already just call
  `get_attention_focus(entity)` and use its return value; the repoint is internal to the function
  body.
- `PerceptionUpdatePhase` has zero call sites in `AuthoritativeApplyPipeline.refine()` (investigation
  finding 2, confirmed) — this repointed code does not run in any production pipeline tick today.
  This is expected and explicitly out of scope (see Scope Guards / Step 8).

**Do NOT touch:** the other two `entity.cognition.subjective.*` reads in this same method (lines 42
and 46, `emotion.fear` / `emotion.curiosity`) — `EmotionalModel` is genuinely live (investigation
finding 3) and unrelated to this ticket. Do not touch `entity.strategic.current_project_id` (line 37).

**Verify:** New integration test `test_attention_focus_reads_real_self_model_dominant_need` (Step 6).

---

### Step 4 — Rewrite `tests/unit/entity/test_phase11_cognition_model_schema.py`
**Files:** `tests/unit/entity/test_phase11_cognition_model_schema.py`

**Change:** This file currently (full content read) imports `SelfModel` from `src.core.cognition`
(line 10) and both:
- asserts `isinstance(cog.subjective.self, SelfModel)` (line 33, `test_cognition_model_default_is_empty_and_safe`)
- exercises all 3 relevant `cognition_accessors.py` functions against the dead path (lines 43-49,
  `test_cognition_accessors_read_new_path`)

Rewrite:
1. Drop `SelfModel` from the `src.core.cognition` import list (line 3-14); it is no longer
   importable there per Step 1.
2. Remove the `isinstance(cog.subjective.self, SelfModel)` assertion from
   `test_cognition_model_default_is_empty_and_safe` (line 33); keep the other three `isinstance`
   assertions (`EmotionalModel`, `TemporalModel`, `RiskModel`) unchanged.
3. Rewrite `test_cognition_accessors_read_new_path` (lines 43-49) to assert against the real
   `entity.self_model.*` path per Step 2's repoint:
   `get_self_awareness(entity) == entity.self_model.self_awareness`,
   `get_need_interpretation(entity) == entity.self_model.needs`,
   `get_capability_estimate(entity) == entity.self_model.capabilities`,
   `get_knowledge_model(entity) == entity.cognition.subjective.knowledge` (unchanged, still the
   correct dead-field-untouched assertion).
4. Add a new test `test_subjective_model_has_no_self_field` using `dataclasses.fields()` on
   `SubjectiveModel` to assert no field named `self` remains — the schema-removal proof the ticket's
   AC requires (test_plan.md item 2).
5. Extend `test_cognition_model_serializes_deterministically` (lines 38-41, unchanged in spirit) with
   a new `test_cognition_canonical_dict_shape_after_self_model_decision` asserting
   `CognitionModel.empty().to_canonical_dict()["subjective"]` has no `"self"` key (test_plan.md item
   6).

**Do NOT touch:** `test_entity_state_has_default_cognition_model` (lines 22-29) — unaffected,
verifies unrelated `CognitionModel` sub-fields.

**Verify:** `pytest tests/unit/entity/test_phase11_cognition_model_schema.py`.

---

### Step 5 — Rewrite `tests/unit/domains/perception/test_phase12_attention_focus_service.py` off the hand-built shell
**Files:** `tests/unit/domains/perception/test_phase12_attention_focus_service.py`

**Change:** Current file (full content read) hand-builds `SelfModel(needs=needs)` →
`SubjectiveModel(self=self_model)` → `CognitionModel(subjective=subjective)` (lines 8-15) in
`test_low_health_focuses_on_healing_and_safety` — exactly the anti-pattern the ticket's AC forbids as
proof, and it will no longer compile once `SelfModel`/`SubjectiveModel.self` are removed (Step 1).
Rewrite this test to set `entity.self_model` directly instead:
```
entity = replace(EntityState(id=1, kind="HERO"),
                  self_model=replace(SelfModelBundle(), needs=NeedInterpretationComponent(dominant_need="healing")))
```
(construct via `dataclasses.replace`/`SelfModelBundle(needs=...)`, whichever reads cleaner — both are
equivalent since `SelfModelBundle` is a plain frozen dataclass, `src/core/self_model.py:211-235`).
Drop the `SelfModel`, `SubjectiveModel` imports from `src.core.cognition` (line 4); add
`SelfModelBundle` from `src.core.self_model`. `test_fear_focuses_on_threats_and_escape`
(lines 22-33) is unaffected — it only constructs `EmotionalModel`/`SubjectiveModel(emotion=...)`,
neither touched by this ticket — leave it exactly as-is.

**Do NOT touch:** `test_fear_focuses_on_threats_and_escape`.

**Verify:** `pytest tests/unit/domains/perception/test_phase12_attention_focus_service.py`.

---

### Step 6 — Add the real-path integration proof required by the ticket's AC
**Files:** New test in `tests/integration/domains/perception/test_phase12_perception_phase.py`
(extend) or a new file `tests/integration/scenarios/test_self_model_attention_focus_integration.py`
(implementer's choice, per test_plan.md item 4 — either location is acceptable; prefer extending the
existing file to avoid a new file if its fixtures already build a real biologically-pressured entity)

**Change:** Add `test_attention_focus_reads_real_self_model_dominant_need`: build an `EntityState`
with real biological/attribute pressure, call `SelfModelUpdatePhase.run(entity=entity, tick=1)`
(`src/cognition/self_model_phase.py:77-84`, signature confirmed by direct read: `run(entity, state=None,
events=[], tick=0, capability_context=None, trace_events_collector=None) -> SelfModelBundle`) to
produce a genuine `dominant_need` (e.g. `"healing"`) on the returned `SelfModelBundle.needs`, attach
it via `entity = dataclasses.replace(entity, self_model=new_bundle)`, then call
`AttentionFocusService.get_attention_focus(entity)` and assert the correct focus tags
(`"healing_resource"`, `"healer"`, `"safe_place"`) are produced. This must call
`SelfModelUpdatePhase.run()` and `AttentionFocusService.get_attention_focus()` directly rather than
via `AuthoritativeApplyPipeline.refine()`, because `PerceptionUpdatePhase` (the only pipeline caller
of `AttentionFocusService`) has zero call sites in the pipeline (investigation finding 2) — see Step
8 / Scope Guards.

**Do NOT touch:** Do not attempt to wire `PerceptionUpdatePhase` into
`AuthoritativeApplyPipeline.refine()` to make this test exercise the full pipeline — that is
explicitly out of scope (Step 8).

**Verify:** the new test itself, run via
`pytest tests/integration/domains/perception/test_phase12_perception_phase.py` (or the new file's
path).

---

### Step 7 — Fix the two remaining `SelfModel(...)` hand-constructions and confirm the third file
**Files:** `tests/integration/scenarios/test_phase12_perception_attention_scenarios.py`,
`tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py`,
`tests/unit/domains/perception/test_phase17_decision_trace_scenarios.py`

**Change:**
- `tests/integration/scenarios/test_phase12_perception_attention_scenarios.py:13` constructs
  `SelfModel(needs=needs)` (confirmed by grep). Apply the same fix pattern as Step 5: build
  `entity.self_model` directly via `SelfModelBundle(needs=...)` instead.
- `tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py:11-17`
  (`test_near_death_prevents_immediate_retry`, full content read) constructs
  `RecoveryState(recent_near_death=True, retry_readiness=0.1)` then wraps it in
  `SelfModel(recovery=recovery)` → `CognitionModel(subjective=replace(..., self=self_model))` purely
  to call `RecoveryReadinessService.is_ready_to_retry(entity.cognition.subjective.self.recovery, ...)`.
  Since `RecoveryState` (Step 1) stays a free-standing, unstored dataclass — it was never actually
  read back from `entity` by `RecoveryReadinessService` for any other purpose — simplify this test to
  call the service directly against the standalone value, dropping all `SelfModel`/`CognitionModel`/
  entity wiring:
  ```
  recovery = RecoveryState(recent_near_death=True, retry_readiness=0.1)
  assert RecoveryReadinessService.is_ready_to_retry(recovery, current_tick=10) is False
  ```
  Drop the now-unused `SelfModel` import from this file's `src.core.cognition` import line (keep
  `RecoveryState`, `EmotionalModel`, `HabitMemory`, `MemoryModel` — all still used/imported
  elsewhere in this same file's other test functions, confirmed by the full file read). The other two
  tests in this file (`test_repeated_failure_causes_route_switch`,
  `test_opportunity_cost_prevents_selling_needed_material`) do not construct `SelfModel` at all —
  leave unchanged.
- `tests/unit/domains/perception/test_phase17_decision_trace_scenarios.py`: confirm during
  implementation (grep of this specific file for `SelfModel(` returned no construction hit, unlike
  the two files above, but graphify's edge list flags it as importing the `SelfModel` type per
  investigation/test_plan) — if it only imports the type without constructing it, drop the dead
  import; if it does construct one, apply the Step 5 fix pattern.

**Do NOT touch:** the two unaffected tests inside `test_phase16_emotion_recovery_habit_scenarios.py`
noted above. Do not touch `EmotionUpdateService`/`OpportunityCostEvaluator` call sites in that file —
unrelated to this ticket.

**Verify:**
`pytest tests/integration/scenarios/test_phase12_perception_attention_scenarios.py tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py tests/unit/domains/perception/test_phase17_decision_trace_scenarios.py`.

---

### Step 8 — Add the reintroduction guard, matching the `TCK-20260824-WIRE-ORPHANED-MECHANISMS` precedent
**Files:** `tests/integrity/test_logic_guards.py`

**Change:** Add `test_self_model_cognition_wrapper_deleted_and_not_reintroduced`, modeled directly on
this same file's existing `test_evolution_service_deleted_and_not_reintroduced`
(`tests/integrity/test_logic_guards.py:513` onward, read as precedent) — same "STRICT LAW" /
"Fraud this catches" docstring convention. Assert:
- `SelfModel` is not importable from `src.core.cognition` (`ImportError`/`AttributeError` check, or a
  grep-based source-text guard consistent with this file's existing style).
- No test file under `tests/` constructs `cognition.py::SelfModel(...)` (a grep-based guard over
  `tests/**/*.py` source text, since `SelfModel` no longer exists as an importable symbol to
  type-check against).
- `entity.self_model` and `entity.cognition` remain genuinely distinct `EntityState` fields
  (`src/core/state.py:734-735`) — guards against a future accidental re-introduction of a parallel
  self-model representation under `cognition.py` (test_plan.md's "Guard against path confusion").

This is a Plan-phase placement decision, not left open: `tests/integrity/test_logic_guards.py` is
used (not a new `tests/architecture/` file) because it is the exact precedent location test_plan.md
cites and is already included in the scoped pytest command.

**Do NOT touch:** any other guard already in `test_logic_guards.py` (e.g.
`test_evolution_service_deleted_and_not_reintroduced` itself).

**Verify:** the new guard test itself.

---

### Step 9 — Update `docs/simulation/domains/perception_contract.md`'s read-path documentation
**Files:** `docs/simulation/domains/perception_contract.md`

**Change:** Line 147's "What It Reads" table currently states
`entity.cognition.subjective.self.needs.dominant_need` as `AttentionFocusService`'s dominant-need
input — the exact dead path from Step 3. Change to `entity.self_model.needs.dominant_need`, matching
the Step 3 repoint. The other rows in that table (lines 145-152) are unaffected and untouched.

Additionally, per architecture review (NEEDS_CHANGES verdict on this plan): the line 147 fix alone
makes the file's own line 13 (`docs/simulation/domains/perception_contract.md:13`, confirmed by
direct read: `**Authoritative status:** Read-phase direct update — NOT a StateUpdate producer. Uses
`dataclasses.replace` to overwrite `entity.cognition.subjective.perception` in-place per entity.`)
more misleading than it was before the fix — a reader who traces the now-correctly-repointed line
147 would reasonably conclude the whole contract is live in production, when in fact (Step 3's
Change section, investigation finding 2) `PerceptionUpdatePhase` has zero call sites in
`AuthoritativeApplyPipeline.refine()` and does not run in production at all, independent of this
ticket's repoint. Add one sentence immediately after the existing line 13 text disclosing this, e.g.:

`**Note:** `PerceptionUpdatePhase` currently has zero call sites in `AuthoritativeApplyPipeline.refine()` and does not run in any production pipeline tick today, independent of the path fix above (see TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION; pipeline wiring is tracked as a separate, out-of-scope follow-up).`

This is a one-line documentation addition to a file already in this step's scope — it does not wire
`PerceptionUpdatePhase` into the pipeline, and the Scope Guards forbidding that remain unchanged.

**Do NOT touch:** `docs/cognition/README.md` — already documents the correct target contract at line
72 (`entity.self_model.needs` → attention focus), confirmed accurate by investigation, no edit
needed. Do not touch `docs/mechanics/04_strategic_cognition.md` — has zero existing coverage of
`AttentionFocusService`, and this ticket is correcting an existing doc's pointer, not introducing a
new Mechanics Bible law. Do not wire `PerceptionUpdatePhase` into
`AuthoritativeApplyPipeline.refine()` — the disclosure sentence above documents the gap, it does not
close it (see Scope Guards).

**Verify:** doc-content grep/read only (no automated test targets this specific line); consistency is
implicitly verified by Step 6's integration test exercising the corrected code path the doc now
describes. The disclosure sentence is prose-only and has no dedicated test, consistent with this
step's existing verification approach.

---

### Step 10 — Record the keep/cut decision in `docs/architecture/cognition_domain_ownership.md`
**Files:** `docs/architecture/cognition_domain_ownership.md`

**Change:** Current file (full content read) is a single table of `CognitionModel` sub-components
with confirmed real owners — it has no row for `SelfModel`/`SubjectiveModel.self` today. Since
`self_model` (the real, kept system) is a sibling top-level `EntityState` field
(`src/core/state.py:734`), not a `CognitionModel` sub-component nested under `cognition.*`
(`state.py:735`), forcing it into the existing table's "Stored Path: `cognition.xxx`" column format
would misrepresent its actual location. Add a new section below the table instead:

```markdown
## Decisions

### `SelfModel` / `SubjectiveModel.self` — CUT (TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION, 2026-09-01)

`core/cognition.py::SelfModel` (formerly `cognition.subjective.self`) was removed. It had zero
production constructions anywhere in `src/` — the only writer path for entity self-model data is
the real, distinct `entity.self_model` field (`SelfModelBundle`, `src/core/self_model.py`), owned by
`src/cognition/` (`SelfModelUpdatePhase`, gated by `ENABLE_SELF_MODEL_COGNITION`) and already
documented in `docs/cognition/README.md`. `entity.self_model` and `entity.cognition` are genuinely
distinct `EntityState` fields with confusingly identical component class names
(`SelfAwarenessComponent`, `NeedInterpretationComponent`, `CapabilityEstimateComponent`) — do not
reintroduce a second self-model representation under `cognition.py`.
```

**Do NOT touch:** the existing table rows (`PerceptionModel` through `DecisionTrace`) — unaffected by
this decision. Do not add rows for `MotivationModel`/`RelationshipModel` here — out of this ticket's
scope (ticket's Out of Scope section).

**Verify:** New doc-content guard test (Step 11).

---

### Step 11 — Add the decision doc-content guard test
**Files:** `tests/tools/test_cognition_domain_ownership_decision.py` (new; mirrors the existing
doc-content guard convention, e.g. `tests/tools/test_cognition_strategy_skill_content.py`, per
test_plan.md item 1)

**Change:** Add `test_cognition_domain_ownership_records_self_model_decision`: read
`docs/architecture/cognition_domain_ownership.md` and assert it contains an unambiguous statement of
the CUT decision (e.g. assert the substring `"SelfModel"` and `"CUT"` and the ticket ID
`"TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION"` all appear in the file text) — proving Step 10's
addition, not just its presence in this plan.

**Do NOT touch:** the referenced existing doc-content guard test file itself — only used as a pattern
reference, not modified.

**Verify:** the new test itself.

---

### Step 12 — Add parity ledger entry `STRAT-261`
**Files:** `docs/parity_ledger/strategic_cognition.yaml`

**Change:** No existing entry in this file (or any `docs/parity_ledger/*.yaml`) references
`attention_focus`/`AttentionFocusService` (investigation's Parity Ledger Overlap section, confirmed:
`STRAT-227/229/245/247` and `SUB-374` all reference the unrelated real `self_model.py` path). The
last entry in the file is `STRAT-260` (`docs/parity_ledger/strategic_cognition.yaml:3779`) — add a
new entry `STRAT-261` immediately after it, following the exact same YAML shape (`id`, `text`,
`status`, `priority`, `legacy_evidence`, `v2_evidence`, `proof_type`, `test_path`,
`divergence_note`, `support_boundary`):

```yaml
- id: STRAT-261
  text: 'AttentionFocusService.get_attention_focus()''s dominant-need read (src/domains/perception/service.py)
    now targets the real, wired entity.self_model.needs.dominant_need (SelfModelBundle,
    src/core/self_model.py, populated by SelfModelUpdatePhase behind ENABLE_SELF_MODEL_COGNITION)
    instead of the dead entity.cognition.subjective.self.needs.dominant_need path -- the
    latter''s container, core/cognition.py::SelfModel/SubjectiveModel.self, was deleted
    (zero production writers found) as part of TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION.
    docs/simulation/domains/perception_contract.md''s Inputs table updated to match.
    PerceptionUpdatePhase (AttentionFocusService''s only pipeline-side caller) itself has
    zero call sites in AuthoritativeApplyPipeline.refine() -- unaffected by and separate
    from this fix; tracked as a disclosed follow-up gap, not addressed here.'
  status: verified
  priority: P2
  legacy_evidence: null
  v2_evidence: src/domains/perception/service.py (AttentionFocusService.get_attention_focus()),
    src/core/self_model.py (SelfModelBundle.needs), src/cognition/self_model_phase.py
    (SelfModelUpdatePhase writer), src/core/cognition.py (SelfModel/SubjectiveModel.self
    removed)
  proof_type: parity
  test_path: tests/integration/domains/perception/test_phase12_perception_phase.py::test_attention_focus_reads_real_self_model_dominant_need
  divergence_note: null
  support_boundary: null
```

(Adjust `test_path` to the actual final location/name chosen in Step 6 if the implementer places the
new test in a different file.)

**Do NOT touch:** any existing `STRAT-###` entry, or `SUB-374` in `substrate.yaml` — none require
changes from this ticket's decision (investigation's Parity Ledger Overlap, confirmed).

**Verify:** `docs/parity_ledger/strategic_cognition.yaml` remains valid YAML against
`docs/parity_ledger/schema.json` (run the repo's existing parity-ledger validation tool/test, if one
is scoped in the test_plan's pytest command set — otherwise a manual YAML parse is sufficient).

---

### Step 13 — Update the ticket body: idea 22/24 resolution, PerceptionUpdatePhase follow-up disclosure, Implementation Notes
**Files:** `tickets/inprogress/TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION.md`

**Change:**
- In `## Assumptions / Open Questions`, replace the two existing bullets (which pre-date this
  investigation and are now stale/partially incorrect — the first bullet's "masked only because the
  flag is OFF" framing is corrected by investigation finding 2) with the resolved findings:
  - The keep/cut decision is CUT, recorded in `docs/architecture/cognition_domain_ownership.md`
    (Step 10).
  - Idea 22 (`TCK-20260824-RELATIONSHIP-ROLE-FIELD`) is confirmed unrelated/moot: it shipped against
    `SocialBond.role` in `src/core/models/social.py`, a different module and data model from
    `cognition.py`'s `RelationshipModel` (`EntityState.social` vs. `EntityState.cognition.relationships`).
  - Idea 24 (`TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK`) is confirmed informed-not-blocked: its own
    scoping work is complete, but its deferred implementation ACs remain blocked on a separate,
    not-yet-filed `MotivationModel.values` foundation ticket — unrelated to `SelfModel` specifically.
  - **Disclosed follow-up gap (not silently expanded into this ticket):**
    `PerceptionUpdatePhase` (and therefore the entire `PerceptionFilterService`/`AttentionFocusService`/
    `SignalSalienceEvaluator` chain) has zero call sites in `AuthoritativeApplyPipeline.refine()` —
    it does not run in production at all, independent of any feature flag. This is a separate,
    materially larger orphan-phase-wiring gap discovered during this ticket's investigation, out of
    scope for this keep/cut decision. Recommend filing a new ticket to either wire
    `PerceptionUpdatePhase` into the pipeline or explicitly document it as intentionally-not-yet-wired
    in `perception_contract.md`'s "Authoritative status" line.
- In `## Implementation Notes`, record the step order actually followed (this plan's Steps 1-12) and
  the two corrections this plan made to `investigation.md`'s claims (`RecoveryState` is not
  container-only-referenced, per Step 1; `RecoveryReadinessService` is itself a second dead-code
  cluster, out of scope).

**Do NOT touch:** `## Scope`, `## Out of Scope`, `## Acceptance Criteria`, `## Related Tickets`,
`## Related Docs`, `## Related Code Areas` sections — unchanged from the ticket as scoped. Do not
mark `## Status` as `DONE` or move the file to `tickets/done/` as part of this step — that happens
at ticket close (Finalize), not Plan/Implement.

**Verify:** manual read — this is a documentation-of-decision step, not a source-code change; no
automated test targets ticket-body prose specifically (test_plan.md item 7 confirms no dedicated
test is required here).

## Scope Guards

- Do not delete or restructure `PerceptionModel`, `EmotionalModel`, `TemporalModel`, `MotivationModel`,
  `RelationshipModel`, `SpatialMemory`, `RiskModel`, `MemoryModel`, or `CommitmentModel` in
  `cognition.py` — all verified still-referenced by other code (investigation finding 3), even where
  currently flag-gated or unwired. Only `SelfModel`, `SubjectiveModel.self`, and the imports that
  become unused solely because of that removal are in scope.
- Do not delete or restructure `RecoveryState` — it has an independent consumer
  (`src/domains/emotion/recovery_service.py`) outside `SelfModel`, confirmed by direct read; deleting
  it would break that module's import. Not named in the ticket's resolve-instruction #1 either.
- Do not wire `PerceptionUpdatePhase` into `AuthoritativeApplyPipeline.refine()`. This is a
  confirmed-real, separately-scoped orphan (zero call sites in the pipeline, independent of any
  feature flag) discovered during this ticket's investigation, but it is a materially larger and
  different change (pipeline wiring, not a schema keep/cut decision) than this ticket's scope. It is
  disclosed as a follow-up in the ticket body (Step 13), not silently folded into this plan.
- Do not touch `TemporalModel`/`MemoryUpdatePhase`'s `ENABLE_MEMORY_UPDATE` flag gating — owned by
  `TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING` per `TCK-20260824-WIRE-ORPHANED-MECHANISMS`'s own
  Out-of-Scope note.
- Do not fold `MotivationModel`/`RelationshipModel` into this decision — separately dead
  (`MotivationModel`) or partially-live (`RelationshipModel`) fields covered by
  `TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK` and untouched by `TCK-20260824-WIRE-ORPHANED-MECHANISMS`
  respectively.
- Do not file or implement the separate `MotivationModel.values` foundation ticket idea 24 depends
  on — out of this ticket's scope per the ticket's own Out of Scope section; only disclose it, per
  Step 13.
- Do not add a new writer for `entity.cognition.subjective.self` under any circumstances — the CUT
  decision (Step 1-13) is final for this plan; the "keep" branch's steps (test_plan.md item 5) are
  not part of this plan.

## Dependency Map

- Step 1 (schema cut) must land before Steps 2, 3, 4, 5, 6, 7, 8 — all of them either read the new
  post-cut shape of `cognition.py` or (Steps 4-8) exercise code that no longer compiles against the
  pre-cut shape.
- Step 2 (accessor repoint) and Step 3 (service repoint) are independent of each other but both
  depend on Step 1.
- Step 4 depends on Steps 1 and 2 (asserts the repointed accessor behavior).
- Step 5, Step 7 depend on Step 1 (rewriting hand-built-shell constructions that no longer compile).
- Step 6 depends on Steps 1 and 3 (exercises the repointed `AttentionFocusService` via the real
  writer).
- Step 8 depends on Step 1 (asserts the symbol is gone).
- Step 9 depends on Step 3 (documents the repointed read path).
- Step 10 is independent of Steps 1-9 (a documentation decision record) but should land in the same
  change set; Step 11 depends on Step 10 (guards its content).
- Step 12 depends on Step 3 and Step 6 (cites the new test's path as `v2_evidence`/`test_path`).
- Step 13 depends on Steps 1-12 being complete (records what was actually done) and should be the
  last step before Verify/Finalize.
- All steps are otherwise independently verifiable — each has its own test command.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Ticket records an explicit keep-or-cut decision scoped to `SelfModel`/`SubjectiveModel.self` specifically, persisted in `docs/architecture/cognition_domain_ownership.md` | Step 10 | Step 11's `test_cognition_domain_ownership_records_self_model_decision` |
| If cut: `SelfModel` is removed | Step 1 | Step 4's `test_subjective_model_has_no_self_field` |
| If cut: `cognition_accessors.py`'s `get_self_awareness`/`get_need_interpretation`/`get_capability_estimate` are repointed to `entity.self_model.*` | Step 2 | Step 4's `test_cognition_accessors_read_real_self_model_path` |
| If cut: `AttentionFocusService` is repointed to read the real self_model path, proven by a test using the real `SelfModelUpdatePhase` path (not a hand-built `cognition.py` shell) | Step 3, Step 6 | Step 6's `test_attention_focus_reads_real_self_model_dominant_need` |
| Idea 22/24 open question is answered with the evidence above, recorded in the ticket, not left open | Step 13 | Manual read of the updated ticket body (no automated test; test_plan.md item 7 confirms none required) |

## Anti-Drift Notes

- **`entity.self_model` (real, `self_model.py`) vs. `entity.cognition.subjective.self` (dead,
  `cognition.py`, now removed) are genuinely different `EntityState` top-level fields**
  (`src/core/state.py:734` vs. `735`) that happen to reuse identically-named component classes
  (`SelfAwarenessComponent`, `NeedInterpretationComponent`, `CapabilityEstimateComponent` — literally
  the same imported classes, since `cognition.py` re-imported them from `self_model.py` rather than
  defining its own). Every step above repoints to `entity.self_model.*` directly (flat field names
  `self_awareness`/`needs`/`capabilities`, per `src/core/self_model.py:224-235`) — never
  `entity.self_model.self.*` or any other guessed nesting.
- **`RecoveryState` correction**: investigation.md's Anti-Drift Hazards claimed `RecoveryState` was
  "only referenced from within `SelfModel`." A direct read of
  `src/domains/emotion/recovery_service.py` shows this is inaccurate — `RecoveryReadinessService`
  imports and operates on `RecoveryState` independently. This plan keeps `RecoveryState` untouched in
  `cognition.py` (Step 1) rather than deleting it, to avoid breaking that module's import — a
  narrower, more conservative cut than investigation.md proposed, consistent with the ticket's own
  resolve-instruction #1 which never named `RecoveryState` for removal.
  `RecoveryReadinessService` itself being separately dead (zero production callers) is a distinct
  finding, out of this ticket's scope, not acted on here.
- **Determinism verified, not just flagged**: `grep -rln "subjective\.self\|SelfModel(" tests/certification/ data/`
  and `grep -rln "subjective" tests/certification/ data/` both return zero hits; no test anywhere
  pins a literal canonical-hash string (`grep -rn "canonical_hash\s*==\s*[\"']" tests/` returns
  nothing). `CognitionModel.to_canonical_dict()`'s only certification-suite exercise is the
  round-trip-identity assertion `test_cognition_model_serializes_deterministically`
  (`tests/unit/entity/test_phase11_cognition_model_schema.py:38-41`), which compares two freshly
  constructed defaults against each other rather than against a pinned value — removing the `"self"`
  key changes both sides identically, so this test stays green with no special handling. No fixture
  regeneration is required.
- **`PerceptionUpdatePhase` unwired-in-pipeline finding is real but must not expand this ticket.**
  Every step in this plan that exercises `AttentionFocusService` post-repoint (Step 6) calls it and
  `SelfModelUpdatePhase.run()` directly, not through `AuthoritativeApplyPipeline.refine()` — because
  the latter would not exercise this code path at all today, for reasons unrelated to this ticket's
  fix.
- **Do not re-run or trust the three now-deleted `SelfModel(...)` test constructions as a regression
  baseline** — they are the exact anti-pattern this ticket removes (investigation finding 1); their
  replacements (Steps 5-7) prove the same behavior against the real, live path instead.

## Deviations

- **Step 7's third file path was wrong; the file was found and fixed under its real path.** The
  plan named `tests/unit/domains/perception/test_phase17_decision_trace_scenarios.py` as the third
  file to check for a `SelfModel` import. That path does not exist. The actual file is
  `tests/integration/scenarios/test_phase17_decision_trace_scenarios.py` (confirmed by a full
  `python3 -m pytest -k "cognition or self_model or attention or perception or recovery"` sweep,
  which caught the stale `SelfModel` import as an `ImportError` at collection time after Step 1's
  cut landed). It imports `SelfModel` but never constructs it, matching the plan's own documented
  fallback for that case ("if it only imports the type without constructing it, drop the dead
  import") — the import was dropped, no other change was needed in that file.
- **`tests/integrity/test_logic_guards.py` edit initially mis-spliced an existing test's final
  assertion.** A `Read` of the file's tail with an off-by-a-few-lines offset caused the first Edit
  attempt to insert the new `test_self_model_cognition_wrapper_deleted_and_not_reintroduced` guard
  in the middle of the pre-existing `test_building_hp_reduction_traces_to_single_authoritative_source`
  function, splitting its final `assert source.count("BuildingSabotageSystem.resolve") == 1` line
  off into orphaned code after the new function. Caught immediately by running the scoped test
  suite (`NameError: name 'source' is not defined`); fixed by moving that assertion back into its
  original function before the new guard test. No plan-scope change — pure implementation-mechanics
  fix, noted here per Gate Integrity discipline (never silently paper over a caught defect).
- **Guard test's grep-based check needed a self-referential-safe string form.** The plan's Step 8
  description used the literal text `SelfModel(...)` inside its own guard-test docstring/assert
  message as an example — if written literally, the new guard test's own source file would trip its
  own `"SelfModel(" not in text` check when scanning `tests/**/*.py`. Implemented by building the
  search string via `"SelfModel" + "("` string concatenation (so the literal substring never
  appears in the guard file's own source) and phrasing the docstring/messages around "the deleted
  wrapper dataclass" instead of spelling out the literal pattern. Same check, same coverage — no
  plan-scope change, just a self-consistency fix the plan's prose example didn't anticipate.

---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION
artifact_type: investigation
tags: [cognition]
---

# Investigation — TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION

## Current Behavior

### 1. `core/cognition.py::SelfModel` / `SubjectiveModel.self` — confirmed zero-constructed dead wrapper

- `SelfModel` dataclass: `src/core/cognition.py:119-132`. Wraps `SelfAwarenessComponent`,
  `NeedInterpretationComponent`, `CapabilityEstimateComponent` (all re-imported from
  `src/core/self_model.py:14-21`) plus a `RecoveryState` shell.
- `SubjectiveModel.self: SelfModel` field: `src/core/cognition.py:214`.
- **Zero explicit production construction anywhere in `src/`.** `grep -rn "SelfModel(" src/`
  returns nothing — the only place `SelfModel` is instantiated is via its own `field(default_factory=SelfModel)`
  default inside `cognition.py` itself. The only explicit `SelfModel(...)` constructor calls in the
  whole repo are in three **test** files: `tests/unit/domains/perception/test_phase12_attention_focus_service.py:12`,
  `tests/integration/scenarios/test_phase12_perception_attention_scenarios.py:13`, and
  `tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py:13`. These are the
  "hand-built cognition.py shell" the ticket's AC explicitly says not to rely on as proof.
- `cognition_accessors.py` (`src/core/cognition_accessors.py:12-22`) exposes
  `get_self_awareness`/`get_need_interpretation`/`get_capability_estimate`/`get_knowledge_model`, all
  reading `entity.cognition.subjective.self.*` (three of the four) or `entity.cognition.subjective.knowledge`
  (the fourth). **Every one of these four functions has zero production callers.** The only callers
  anywhere are in `tests/unit/entity/test_phase11_cognition_model_schema.py:43-49`, which is a
  self-referential test asserting the accessor equals the same dead field it reads — not a
  regression guard against real behavior.

### 2. `AttentionFocusService.get_attention_focus()` — confirmed reads the dead path, and confirmed **never executes in production regardless of the flag**

- `src/domains/perception/service.py:14-57`. Line 22: `dominant_need = entity.cognition.subjective.self.needs.dominant_need`.
  This is exactly the dead `SubjectiveModel.self` path from finding 1 — never written by any code
  path in `src/`.
- **Important correction to the ticket's stated premise.** The ticket's Assumptions section says the
  bug is "currently masked only because `ENABLE_SELF_MODEL_COGNITION` defaults OFF." That is true of
  the *data* (nothing ever populates `cognition.subjective.self` regardless of the flag — see
  finding 4), but it is not the only thing masking the bug from firing at all: `AttentionFocusService.get_attention_focus()`
  itself has exactly two callers in `src/`, both inside the perception domain:
  `src/domains/perception/phase.py:40` (`PerceptionUpdatePhase.run()`, step 2) and
  `src/domains/perception/filter.py:55` (`PerceptionFilterService.filter()`, called only from
  `PerceptionUpdatePhase.run()` step 3). **`PerceptionUpdatePhase` itself has zero call sites in
  `src/engine/pipeline.py` or anywhere else in `src/`** — `grep -rn "PerceptionUpdatePhase(" src/ tests/`
  finds it only in two test files (`tests/integration/domains/perception/test_phase12_perception_phase.py`,
  `tests/integration/scenarios/test_phase12_perception_attention_scenarios.py`). There is no
  `run_phase("perception", ...)` (or similarly named) entry in `AuthoritativeApplyPipeline.refine()`'s
  full phase list (`src/engine/pipeline.py`, all ~40 `run_phase(...)` calls enumerated and checked —
  none invoke perception). So today, in production, `AttentionFocusService.get_attention_focus()`
  never runs at all — independent of `ENABLE_SELF_MODEL_COGNITION`'s value. The masking is
  structural (the whole perception-attention chain is unwired), not just flag-state. This does not
  change the ticket's required fix (the read path is still wrong and must be repointed before
  anyone wires `PerceptionUpdatePhase` in), but it changes the urgency framing: the bug cannot
  "start firing silently the moment [`ENABLE_SELF_MODEL_COGNITION`] flips on" — it would additionally
  require someone to wire `PerceptionUpdatePhase` into the pipeline, which is a separate, currently
  unscoped gap. See Risks and Open Questions.

### 3. Live vs. dead `cognition.py` fields — precise, current, file:line-grounded list

Per-field production-write status, verified by tracing every writer of `entity.cognition` in `src/`
(`grep -rn "cognition=" src/` narrowed to actual `EntityState`/`CognitionModel`/`SubjectiveModel`
replace chains):

| Field | Writer | Wiring status |
|---|---|---|
| `SubjectiveModel.perception` (`PerceptionModel`) | `PerceptionUpdatePhase.run()` (`src/domains/perception/phase.py:63-65`) | **Written by real code, but that code has zero call sites in the pipeline** (see finding 2) — currently dead in production despite being "real" code, contrary to how the ticket's Out-of-Scope section characterizes it. No reader of `cognition.subjective.perception` exists anywhere in `src/` either (`grep -rn "subjective\.perception\b" src/` matches only the writer itself). |
| `SubjectiveModel.emotion` (`EmotionalModel`) | `NearDeathHardeningPhase.apply()` (`src/engine/pipeline_phases/hardening.py:96-100`), called unconditionally from `src/engine/pipeline.py:357` (`run_phase("near_death_hardening", ...)` — no `feature_flag` argument, so `FeatureMode.ON` always) | **Genuinely live**, unconditional. Read by `src/domains/perception/salience.py:47,52` (fear/curiosity — but that reader is itself inside the unwired perception chain, finding 2) and `src/views/readiness.py:36,57` (confidence — a presenter/view layer, real consumer). |
| `SubjectiveModel.time` (`TemporalModel`, `.urgency` only) | `MemoryUpdatePhase.run()` (`src/domains/memory/phase.py:74-77`), wired via `run_phase(..., "ENABLE_MEMORY_UPDATE")` at `src/engine/pipeline.py:154-157` | Wired but **flag-gated OFF by default** (`ENABLE_MEMORY_UPDATE: FeatureMode.OFF`, `src/domains/optimization/feature_flags.py`) — same shape of gating as `SelfModel` would need if kept, contrary to the ticket's framing of `TemporalModel` as unconditionally "genuinely live." |
| `CognitionModel.memory.causal` / `.spatial` | Same `MemoryUpdatePhase.run()` | Same as above — flag-gated OFF by default. |
| `SubjectiveModel.self` (`SelfModel`) | **None.** | Dead — confirmed finding 1. |
| `CognitionModel.motivation` (`MotivationModel`) | **None found** (`grep -rn "motivation=" src/` outside `cognition.py`'s own default factory returns nothing) | Dead. `ValuePreferenceProfile`'s 7 fields stay at their `0.5` defaults in every production run — independently re-confirmed here, matching `TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK`'s finding. |
| `CognitionModel.relationships` (`RelationshipModel`) | `src/engine/quests.py:235` (`reputation_cognition_update = replace(base_cognition, relationships=new_relationships)`) | Has at least one real writer, unlike `MotivationModel` — not part of this ticket's scope either way, noted for completeness only (contradicts the task prompt's framing of `RelationshipModel` as flatly dead; it has one confirmed write site, not independently verified live end-to-end here since out of scope). |

Net: the ticket's own Out-of-Scope framing ("PerceptionModel, EmotionalModel, and TemporalModel …
genuinely written by real pipeline phases, not part of this decision's scope") is accurate only for
`EmotionalModel`. `PerceptionModel` and `TemporalModel` are written by real code but are currently
inert in production (unwired / flag-OFF respectively) — the same structural category `SelfModel`
would fall into *if* it had a writer, which it does not. This does not change the ticket's scope
boundary (`SelfModel`/`SubjectiveModel.self` only) — it is flagged as a Risk since it affects how
confidently "Out of Scope" can be asserted, not as a reason to expand this ticket.

### 4. `entity.self_model.*` (`src/core/self_model.py`) — the real self-model, confirmed wired but currently unpopulated in production

- `SelfModelBundle` (`src/core/self_model.py:212-249`) is `EntityState.self_model`
  (`src/core/state.py:734`), a field distinct from `EntityState.cognition` (`state.py:735`).
- **Writer**: `SelfModelUpdatePhase.apply()`/`.run()` (`src/cognition/self_model_phase.py:32-220`),
  wired into the pipeline at `src/engine/pipeline.py:164`:
  `run_phase("self_model", update, lambda u: SelfModelUpdatePhase.apply(state, u), "ENABLE_SELF_MODEL_COGNITION")`.
  `SelfModelUpdatePhase.apply()` sets `EntityUpdate.self_model_bundle_set`, which `src/engine/apply.py:594`
  applies to `entity.self_model` (confirmed by tracing `self_model_bundle_set` through
  `src/core/updates.py:659,718` into `apply.py`).
- **Flag default**: `ENABLE_SELF_MODEL_COGNITION: FeatureMode.OFF` — `src/domains/optimization/feature_flags.py:19`,
  with an explicit comment citing `TCK-20260824-ROLLOUT-FLAG-DECISIONS` (deferred, no corpus profile
  turns it ON) and a named follow-up `TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION`. Confirmed
  current — no code in `src/config/` or any rollout profile overrides it ON. The only place it is
  set ON is `src/testing/scenario_runner.py:102` (a dev/test harness) and the unit/integration test
  suite itself.
- `V2EntityBuilder` (`src/core/builder.py:110`) default-constructs `self._self_model = SelfModelBundle()`
  (all-empty) at entity creation; `archetype_factory.py` passes it through unchanged on non-self-model
  entity rebuilds (`src/entities/archetype_factory.py:152,178`).
- **Net**: `entity.self_model.*` is at its all-default empty state in every production run today,
  same observable outcome as the dead `cognition.subjective.self` — **but for a structurally
  different reason**: `self_model.py` has a real, wired writer (`SelfModelUpdatePhase`) gated behind
  a documented, intentionally-deferred rollout flag, and it already has **real, non-test consumers**
  wired to read from it, ready to receive real data the instant the flag flips ON:
  `src/domains/adventure/generator.py:95-96`, `src/domains/adventure/scoring.py:112`,
  `src/domains/information/assimilation.py:37`, `src/engine/tactical.py:400`,
  `src/engine/pipeline_phases/lead_contradiction.py:195,209`, `src/engine/intent/action_intent.py:159,183`,
  and per `docs/cognition/README.md:75-76`, `src/systems/strategic_systems/intelligence.py` and
  `src/strategy/`. `cognition.py`'s `SelfModel` has none of this — no writer, no flag, no real
  consumer, only a self-referential accessor and its own schema test.

### 5. Prior related tickets — what they actually concluded (verified against their own closed ticket text, not restated from this ticket's framing)

- **`TCK-20260824-RELATIONSHIP-ROLE-FIELD` (idea 22)** — `tickets/done/TCK-20260824-RELATIONSHIP-ROLE-FIELD.md`,
  `## Status: DONE`. Added `RelationshipRole` enum + `SocialBond.role` field in
  **`src/core/models/social.py`**, wired through `SocialBondUpdate`/`RelationshipService.process_update()`,
  consumed by `PartyCompositionScorer.score()`. This is a completely different module and data model
  from `core/cognition.py`'s `RelationshipModel` (which lives under `EntityState.cognition.relationships`,
  not `EntityState.social`). **Confirmed unrelated/moot to this ticket's decision** — the ticket
  text's framing is accurate: idea 22 shipped against `SocialBond`, not `CognitionModel.relationships`.
- **`TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK` (idea 24)** — `tickets/done/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK.md`,
  `## Status: DONE` (scoping-only; ticket body's internal `## Status` was `BLOCKED` for the deferred
  implementation ACs, per its own "Status = DONE clarification" note). It independently re-verified
  the *separate* `MotivationModel.values` (`ValuePreferenceProfile`) dead-on-arrival finding
  (`src/core/cognition.py:382-402,440-444`) and named "a separate, not-yet-existing
  `MotivationModel.values` foundation ticket" as a hard blocking dependency for its own deferred
  implementation ACs — explicitly stating "No foundation ticket for `MotivationModel.values` exists
  yet anywhere in `docs/tickets/stored_artifacts`." **Confirmed**: idea 24's own scoping work is
  complete/informed (not blocked from being documented), but the actual Personal Economy feature
  implementation remains blocked pending that not-yet-filed foundation ticket. This is unrelated to
  `SelfModel`/`SubjectiveModel.self` specifically — it concerns `MotivationModel.values`, a sibling
  dead field this ticket's scope explicitly excludes.
- **`TCK-20260824-WIRE-ORPHANED-MECHANISMS`** — `tickets/done/TCK-20260824-WIRE-ORPHANED-MECHANISMS.md`,
  `## Status: DONE`. Wired 6 of 7 originally-scoped orphaned mechanisms (`InformationNeedDetector`,
  deleted `EvolutionService`/`SabotageAction` duplicates, `EmotionUpdateService.update_on_event()` for
  `"near_death"` — this is the exact commit that made `EmotionalModel` "genuinely live" per finding 3
  above — `compute_elder_attribute_update()`, `consequence_events.evaluate_social_consequence()`).
  Explicitly out-of-scoped **"MemoryUpdatePhase wiring — owned by TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING (C11)"**,
  consistent with finding 3's observation that `TemporalModel`/`CausalMemory`/`SpatialMemory` remain
  flag-gated OFF today. This ticket never touched `SelfModel`/`SubjectiveModel.self` or
  `cognition_accessors.py` — confirmed no overlap.

## Mechanics / Engine Constraints

- `docs/core/state.md`'s immutability law and this repo's Durable State Rule (CLAUDE.md) apply: any
  cut must go through the authoritative `EntityUpdate`/apply path, not a direct mutation. The
  existing `SelfModelUpdatePhase.apply()` → `self_model_bundle_set` → `apply.py:594` path already
  satisfies this for `entity.self_model`; no new durable-state mechanism is needed for the "cut"
  branch, only repointing reads.
- `EntityState.to_canonical_dict()` (`src/core/state.py:797-798`) unconditionally includes both
  `"self_model"` and `"cognition"` in the canonical hash. Deleting `SelfModel`/`SubjectiveModel.self`
  changes `CognitionModel.to_canonical_dict()`'s output shape (`subjective.self` key disappears),
  which changes the canonical hash of every `EntityState` — this is a determinism-relevant schema
  change and must be treated as such (existing certification/replay baselines that pin a canonical
  hash including the old `subjective.self` shape would need regeneration). No parity ledger entry
  currently asserts a specific canonical-hash value depending on `subjective.self`'s presence
  (verified: no `SUB-###` entry references `cognition.subjective.self`).
- `docs/architecture/cognition_domain_ownership.md`'s existing ownership table (read in full,
  reproduced above under "Docs Requiring Update") has no row for `SelfModel`/`SubjectiveModel.self`,
  `MotivationModel`, or `RelationshipModel` at all today — the table only documents the fields with
  confirmed real owners. Recording the keep/cut decision here follows the same convention: either
  omit the row permanently (cut) or add one naming a real owner package (keep).

## Docs Requiring Update

- `docs/architecture/cognition_domain_ownership.md`: ticket AC #1 requires the explicit keep/cut
  decision for `SelfModel`/`SubjectiveModel.self` to be persisted here (or a new ADR); this doc is
  the existing, already-referenced home for exactly this kind of cognition sub-model ownership
  record, so the decision belongs here rather than a new file.
- `docs/simulation/domains/perception_contract.md`: line 147's Inputs table currently states
  `entity.cognition.subjective.self.needs.dominant_need` as `AttentionFocusService`'s dominant-need
  input source — this is the exact dead path from finding 2 and must be corrected to
  `entity.self_model.needs.dominant_need` once the accessor/service is repointed, regardless of
  whether the cut or keep branch is chosen (both branches require this specific line to change: cut
  repoints to the real path; keep requires a real writer at the currently-cited path, which would
  also need the doc's wording double-checked against whatever writer is added).
- `docs/parity_ledger/strategic_cognition.yaml`: no existing entry documents `AttentionFocusService`/
  `get_attention_focus()`/attention-focus dominant-need behavior at all (`grep` confirms zero hits
  for `attention_focus` or `AttentionFocusService` across every `docs/parity_ledger/*.yaml` file).
  Per the Authoritative Mechanics Rule ("If no entry exists, add one"), fixing this read path is a
  behavior change to a mechanic this ledger's subsystem scope covers ("AI goal hierarchy, leads,
  attention bounds" per CLAUDE.md's table) and needs a new `STRAT-###` entry with `v2_evidence`
  citing the corrected read path and a `test_path` proving it.

`docs/cognition/README.md` (path: `docs/cognition/README.md`, under `docs/cognition/`) is not
required to change for this ticket: it already documents the *correct* intended contract at line 72
(`entity.self_model.needs` → attention focus for salience scoring, under `src/domains/perception/`)
— this is exactly the target state the "cut" branch's repoint produces, so the doc is already
accurate for the fix and does not need editing. `docs/mechanics/04_strategic_cognition.md` (path:
`docs/mechanics/04_strategic_cognition.md`, under `docs/mechanics/`) is not required to change
either: it currently has zero coverage of `AttentionFocusService`/dominant-need attention scoring at
all, and this ticket's fix is correcting an already-existing perception-domain contract's read
pointer, not introducing a new law the Mechanics Bible needs to adopt as its own — `perception_contract.md`
is the doc that already claims ownership of this mechanism. `docs/architecture/cognition_domain_ownership.md`'s
own table structure (path: same file, referenced above under Format 1 for the required decision
record) does not need a new row for `MotivationModel`/`RelationshipModel` as part of *this* ticket:
those are out of scope per the ticket's own Scope section, and finding 3/5 above found no code
change to either field here.

## Parity Ledger Overlap

- No existing parity ledger entry (`STRAT-227`, `STRAT-229`, `STRAT-245`, `STRAT-247` in
  `strategic_cognition.yaml`, or `SUB-374` in `substrate.yaml` — the entries found by grepping for
  `self_model`/`SelfModel` across `docs/parity_ledger/`) references `core/cognition.py`'s
  `SelfModel`/`SubjectiveModel.self` or `cognition_accessors.py` specifically. All five reference the
  **real** `self_model.py`/`SelfModelUpdatePhase` path (`SUB-374`: canonical-hash participation of
  `EntityState.self_model`; `STRAT-227/229/245/247`: `AdventureRouteScorer`, memory-phase wiring,
  self-model-updated observability events) — none require changes from this ticket's cut/keep
  decision, and none are P0. Confirmed by direct `grep -n -A8 "^- id: <ID>"` inspection of each entry.
- No parity entry exists yet for `AttentionFocusService`'s dominant-need read (see Docs Requiring
  Update) — a new `STRAT-###` entry is needed as part of implementing this ticket, not an update to
  an existing one.
- No P0-priority entry anywhere in the ledger references this ticket's scope; no `test_path`
  gap-flag applies here since no relevant entry exists yet to check.

## Prior Work

- `docs/plans/rpg_design_roadmap/rpg_direction_alignment_audit.md` (a prior, independent audit pass,
  not produced by this ticket) already reached the identical conclusion, section E/F: the genuinely
  orphaned `cognition.py` subset is "`SelfModel`, `RiskModel`, `SubjectiveModel`, `TrustEntry`,
  `RelationshipModel`, `PartnerMemory`, `CommitmentModel`, `MotivationModel`, `AmbitionProfile`,
  `ValuePreferenceProfile`, `MoralPreferenceProfile`" (line ~155-163), and explicitly names the
  naming collision this ticket exists to resolve: "this `SelfModel` is `core/cognition.py`'s orphaned
  dataclass — a different class from `core/self_model.py`'s live `SelfModelBundle` gated by idea 9's
  `ENABLE_SELF_MODEL_COGNITION` flag" (line 163-164). It recommends (Section G, item 5) "a one-line
  note distinguishing idea 8's orphaned `core/cognition.py::SelfModel` from idea 9's live, wired
  `core/self_model.py::SelfModelBundle`" — this ticket's decision record in
  `cognition_domain_ownership.md` satisfies that recommendation directly.
- `TCK-20260824-WIRE-ORPHANED-MECHANISMS` is the ticket that made `EmotionalModel` genuinely live
  (wiring `EmotionUpdateService.update_on_event()` into `NearDeathHardeningPhase.apply()`), and is
  the direct precedent for this ticket's "cut" mechanics — same pattern of confirming a duplicate/dead
  path via a real grep-based duplicate-check before deleting, same pattern of a dedicated
  test-and-parity closing sequence (see its `Implementation Notes` Step 4 and 7).
- `docs/cognition/README.md` (written for the *real* `self_model.py` subsystem, `last_verified:
  2026-06-13`) already fully documents the target end-state this ticket's "cut" branch produces —
  no new architecture needs to be invented, only wiring the two already-known-correct pieces
  (`cognition_accessors.py`, `AttentionFocusService`) to the already-documented real path.

## Risks and Open Questions

- **Open question requiring a Plan-phase decision, not assumed here**: cutting `SelfModel`/`SubjectiveModel.self`
  changes `CognitionModel.to_canonical_dict()`'s output shape, which changes every `EntityState`'s
  canonical hash (see Mechanics/Engine Constraints). No parity entry currently pins a hash value
  affected by this, but any stored replay/certification fixture bytes that embed a serialized
  canonical dict (not just a hash) would need regeneration. Investigation did not find such a fixture
  referencing `subjective.self` specifically, but Plan should confirm no `tests/certification/` or
  `data/` golden file embeds the old shape before implementation.
- **Structural finding beyond this ticket's stated scope, flagged not acted on**: `PerceptionUpdatePhase`
  (and therefore the entire `PerceptionFilterService`/`AttentionFocusService`/`SignalSalienceEvaluator`
  chain) has zero call sites in `AuthoritativeApplyPipeline.refine()` — it is not wired into
  production at all, independent of any feature flag. This means `PerceptionModel` is not the
  "genuinely live sibling field" the ticket's Out-of-Scope section assumes it to be (see finding 3).
  This does not block this ticket's SelfModel-scoped decision, but the eventual `AttentionFocusService`
  repoint fix (AC #2, "if cut") will not be exercised by any real pipeline tick until a separate
  ticket wires `PerceptionUpdatePhase` in — the test proving the repoint must therefore call
  `AttentionFocusService`/`PerceptionUpdatePhase` directly (as the ticket's own AC already requires,
  "proven by a test using the real `SelfModelUpdatePhase` path"), not rely on a full-pipeline
  integration run to exercise it. Recommend a follow-up ticket to either wire `PerceptionUpdatePhase`
  into the pipeline or explicitly document it as intentionally-not-yet-wired in `perception_contract.md`'s
  "Authoritative status" line — out of scope here, flagged for the record.
- **Risk if "keep" is chosen instead of "cut"**: the ticket's AC for "keep" requires "a real writer so
  `entity.cognition.subjective.self.needs.dominant_need` is actually populated." Given finding 4 (the
  real self-model system, `self_model.py`, already exists, is already wired, already has 6+ real
  consumers, and is only flag-gated pending a named validation ticket
  `TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION`), adding a *second*, independent writer for the
  `cognition.py` copy would create two parallel self-model representations with no reconciliation
  rule — a durable-state duplication CLAUDE.md's Architecture Rule warns against ("Shared world
  behavior should go through systems/registries, not scattered local hacks"). This is a strong
  argument for "cut" over "keep," documented here as investigation evidence for Plan's decision, not
  as a resolved decision.

## Anti-Drift Hazards

- **Do not delete the entire `cognition.py` file.** `PerceptionModel`, `EmotionalModel`, `TemporalModel`,
  `MemoryModel` (`causal`/`spatial` sub-fields), and their nested dataclasses have real writers
  (finding 3) even where currently flag-gated or unwired — a whole-file deletion would destroy live
  code paths. Scope the cut to exactly `SelfModel`, `SubjectiveModel.self`, and `RecoveryState` (only
  referenced from within `SelfModel`) plus their re-imports from `self_model.py` at the top of
  `cognition.py`.
- **Do not conflate `entity.self_model` (`self_model.py`, real, wired, flag-gated) with
  `entity.cognition.subjective.self` (`cognition.py`, dead) when writing the fix or the test.** They
  are genuinely different `EntityState` top-level fields (`state.py:734` vs. `735`) with confusingly
  identical component-class names (`SelfAwarenessComponent`, `NeedInterpretationComponent`,
  `CapabilityEstimateComponent` are literally the same imported classes reused as fields in both —
  `cognition.py` re-imports them from `self_model.py` rather than defining its own). A test that
  hand-builds a `cognition.py::SelfModel(...)` and asserts against it (the exact anti-pattern in the
  three existing test files, finding 1) proves nothing about the real, flag-gated pipeline path — the
  ticket's own AC already requires the real `SelfModelUpdatePhase` path be used instead.
  `cognition_accessors.py`'s repoint (if cut) must go to `entity.self_model.*`, not
  `entity.self_model.self.*` or any other guessed nesting — `SelfModelBundle`'s fields are named
  `self_awareness`/`needs`/`capabilities`/`knowledge` directly (`self_model.py:224-235`), a flatter
  shape than `cognition.py`'s `SelfModel.awareness`/`.needs`/`.capability`.
- **Do not widen this ticket into fixing `PerceptionUpdatePhase`'s pipeline wiring gap** (Risks
  section) or `TemporalModel`/`MemoryUpdatePhase`'s flag-gating — both are real findings surfaced
  during this investigation but are explicitly out of this ticket's scope and already tracked
  (`ENABLE_MEMORY_UPDATE` gating is owned by `TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING` per
  `TCK-20260824-WIRE-ORPHANED-MECHANISMS`'s own Out-of-Scope note).
- **Do not fold `MotivationModel`/`RelationshipModel` into this decision.** They are separately dead
  (or partially-live, `RelationshipModel`) fields covered by `TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK`
  and untouched by `TCK-20260824-WIRE-ORPHANED-MECHANISMS` respectively — this ticket's Out-of-Scope
  section already excludes them, do not expand it while implementing.

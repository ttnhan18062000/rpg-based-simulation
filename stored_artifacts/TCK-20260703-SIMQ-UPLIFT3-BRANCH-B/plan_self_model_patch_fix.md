# Supplementary Plan — Finding 5 fix: `self_model_bundle_set` durable materialization

**Ticket:** TCK-20260703-SIMQ-UPLIFT3-BRANCH-B (this is an in-scope follow-up to the ticket's own
Finding 5, documented in its `Assumptions / Open Questions` section, dated 2026-07-04). Main
`plan.md` covers the two already-shipped fixes (Steps 1-9); this file is additive and does not
modify that plan.

**Investigator confirmation (2026-07-04):** re-derived from direct source read, not re-litigated
from the ticket's prose alone. All line numbers below were verified against current `src/` this
session.

---

## 0. Confirmed fix shape

- `src/core/updates.py:637` — `EntityUpdate.self_model_bundle_set: Optional[Any] = None`. Confirmed
  **replace-if-present** semantics, identical in shape to `group_id_set` (line 636) and `kind_set`
  (line 614):
  - `EntityUpdate.is_noop()` (line 660): `... and self.group_id_set is None and
    self.self_model_bundle_set is None and ...` — already correctly wired into noop detection.
  - `EntityUpdate.merge()` (line 694): `if other.self_model_bundle_set is not None: changes["self_model_bundle_set"] = other.self_model_bundle_set`
    — already correctly wired into merge (last-write-wins on the field, standard "_set" convention).
  - `SelfModelUpdatePhase.apply()` (`src/cognition/self_model_phase.py:57-71`) always calls
    `SelfModelUpdatePhase.run()` and always assigns its return value via
    `dataclass_replace(entity_up, self_model_bundle_set=new_bundle)` for every alive/active entity,
    every tick this phase runs — `run()` (line 76-220) always returns a **complete**
    `SelfModelBundle` (either `old_bundle` unchanged at line 161, or a fully-reconstructed
    `SelfModelBundle(...)` at line 215-220 with all 4 components populated). There is no partial/delta
    shape to merge component-by-component — this confirms a pure "whole-object replace" patch is the
    correct and complete fix, not a field-by-field merge like `StrategicPatch`.
  - `src/engine/patches.py` has 17 `ComponentPatch` subclasses (`KindPatch` through `WoundPatch`,
    lines 38-625) and `extract_patches()` (line 628-684) checks every other `EntityUpdate` field —
    confirmed **zero** references to `self_model_bundle_set` anywhere in `patches.py`.
  - `src/engine/apply.py:578` — `_fast_replace_entity()`:
    `object.__setattr__(res, "self_model", changes.get("self_model", getattr(entity, "self_model", None)))`
    — reads `changes["self_model"]`, which nothing ever populates. Confirmed the entity's prior
    `self_model` (or `None` via the `getattr` fallback on entities predating the field) is always
    carried forward unchanged.

- `src/core/self_model.py:212-246` — `SelfModelBundle` is a plain frozen dataclass, default-empty via
  `SelfModelBundle.empty()`. No merge logic lives on `SelfModelBundle` itself — confirms nothing is
  lost by not doing component-level merging in the patch; the phase already computed the full
  merged bundle before handing it to `EntityUpdate`.

**Conclusion:** the fix is a **direct structural mirror of `KindPatch`** (`src/engine/patches.py:38-52`,
the simplest existing sibling: one `Optional` field, no merge-target substructure, "set if present,
else leave untouched").

---

## 1. New `SelfModelPatch(ComponentPatch)` — insert after `WoundPatch` (line 625), before
`extract_patches()` (line 628)

```python
@dataclass(frozen=True, slots=True)
class SelfModelPatch(ComponentPatch):
    self_model_bundle_set: Optional[Any] = None  # SelfModelBundle

    def is_noop(self) -> bool:
        return self.self_model_bundle_set is None

    def merge(self, other: SelfModelPatch) -> SelfModelPatch:
        if not other or other.is_noop():
            return self
        return SelfModelPatch(
            entity_id=self.entity_id,
            self_model_bundle_set=other.self_model_bundle_set if other.self_model_bundle_set is not None else self.self_model_bundle_set,
        )

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        if self.self_model_bundle_set is not None:
            changes["self_model"] = self.self_model_bundle_set
```

Notes:
- No `from src.engine.apply import replace` needed inside `apply()` — unlike `KindPatch`, this is a
  whole-object replace of a dataclass instance the phase already fully constructed, not a
  component-level `replace(...)` call against the entity's current component.
- `Optional[Any]` matches `EntityUpdate.self_model_bundle_set`'s own type exactly (kept `Any` rather
  than importing `SelfModelBundle` into `patches.py`, consistent with how every other patch class
  types its `Update`-typed field as `Optional[Any]` under `TYPE_CHECKING`-only imports at the top of
  the file — see lines 6-14).
- `entity_id` positional-arg convention (`SelfModelPatch(entity_id, self_model_bundle_set=...)`)
  matches the call convention `extract_patches()` uses for every other patch (e.g. `KindPatch(entity_id, kind_set=update.kind_set)`).

## 2. Wire into `extract_patches()` (line 628-684)

Add immediately after the `WoundPatch` block (line 681-683), before `return patches`:

```python
    if update.self_model_bundle_set is not None:
        p = SelfModelPatch(entity_id, self_model_bundle_set=update.self_model_bundle_set)
        if not p.is_noop(): patches.append(p)
    return patches
```

Placement note: no ordering dependency exists — `self_model` is never read by the "PH8 Derived Stats
Re-calc" block in `_apply_entity_update_to_dict()` (`apply.py:448-497`, which only reads
`attributes`/`equipment`/`identity`/`wound_update`/`combat`), and no other patch's `apply()` reads
`changes.get("self_model", ...)`. Appending last (after `WoundPatch`) is safe and matches
`self_model_bundle_set`'s declaration position as the last "_set" field on `EntityUpdate` before
`intent_results`/`property_updates`.

No changes needed to `_fast_replace_entity()` (`apply.py:557-592`) — line 578 already reads
`changes.get("self_model", ...)`; it was always correct, just never fed.

---

## 3. Blast-radius: every consumer of `entity.self_model`, per-consumer risk assessment

Full sweep performed via `grep -rn "\.self_model\b" src/` plus targeted follow-up greps to resolve
every hit to a real read/write site or a false positive (import, docstring, unrelated
`self_model_usage` field on a campaign scorecard schema — see below). Every consumer below reads
`entity.self_model` directly off durable `EntityState`, except where noted as reading the transient
`EntityUpdate`/`StateUpdate` (unaffected by this fix by construction).

| # | Consumer | Live-wired? | Effect of fix | Risk |
|---|---|---|---|---|
| 1 | `src/cognition/self_model_phase.py::SelfModelUpdatePhase.run()` (`old_bundle = entity.self_model`, line 101) | Yes — the phase this ticket already fixed (Step 1's `events=[]`) | Currently always starts from `SelfModelBundle.empty()` every tick (durable state never carried the previous tick's bundle). After the fix, `old_bundle` will be the **real prior tick's** bundle — Step 1 assimilation becomes genuinely cumulative across ticks (facts/unknowns accrue) instead of being rebuilt from scratch every tick. | **None — this is the intended fix.** This is the whole point of Finding 5: makes the dirty-check (`self_model_phase.py:148-154`) and cumulative knowledge model actually work as the contract (`docs/cognition/self_model_contract.md`) describes. Gated behind `ENABLE_SELF_MODEL_COGNITION`, OFF in every shipped profile — confirmed via `grep -rn "ENABLE_SELF_MODEL_COGNITION" config/ data/worlds/` (zero hits). No shipped-world behavior changes. |
| 2 | `src/cognition/need_interpretation.py:163` (`NeedInterpretationService.interpret()`, `knowledge = getattr(entity.self_model, "knowledge", None)`) | Yes, but only ever called with a **locally-constructed `temp_entity`** (`self_model_phase.py:176-184`), never the raw durable entity | No behavior change at all — this consumer was never blocked by Finding 5; it already operates on the current tick's freshly-assimilated `new_knowledge`, not stale durable state, regardless of whether materialization works. | **None.** Confirmed by reading `self_model_phase.py:176-184` — the `entity` argument passed to `NeedInterpretationService.interpret()` is always `temp_entity`, a `dataclasses.replace(entity, self_model=SelfModelBundle(...new_knowledge...))`, constructed fresh every call. |
| 3 | `src/cognition/knowledge_model.py:60` (`KnowledgeModelService.assimilate()`, `current = entity.self_model.knowledge`) | Yes, called from Step 1 of `self_model_phase.py::run()` (line 113-114), always on a `temp_entity` built from `old_bundle` | Same as #1 — becomes genuinely cumulative once `old_bundle` carries real history instead of always-empty. | **None — intended fix effect**, same reasoning as #1. |
| 4 | `src/domains/adventure/generator.py:94-95` (`AdventureRouteGenerator.generate()`, reads `entity.self_model.self_awareness.perceived_weaknesses` / `entity.self_model.needs.active_needs` directly off the durable entity) | Yes — wired via `AdventureDecisionPhase`, gated behind `ENABLE_ADVENTURE_ROUTING` (`src/engine/pipeline.py:227-235`) | Currently always sees `()`/`{}` (both fields default-empty on `SelfModelBundle.empty()`), so lines 97+ (forced `RECOVER`/equipment-improvement routes on `low_health`/`weak_weapon` weaknesses) never fire — dead code in practice today. Once BOTH `ENABLE_SELF_MODEL_COGNITION` and `ENABLE_ADVENTURE_ROUTING` are ON together, these forced-route injections would start firing for real. | **Contained, not concerning, but the "never both ON" claim was too narrow (architecture review, 2026-07-04).** Confirmed via `grep -rn "ENABLE_ADVENTURE_ROUTING\|ENABLE_SELF_MODEL_COGNITION" config/ data/worlds/`: `ENABLE_ADVENTURE_ROUTING` is ON only in the dedicated `data/worlds/simq_routing_test` calibration world; `ENABLE_SELF_MODEL_COGNITION` appears in no shipped `config/`/`data/worlds/` file. **However**, `src/domains/optimization/rollout_profiles.py`'s `RolloutProfileManager` defines `CLASS_B` (lines 59-63) and `CLASS_C` (lines 73-79) `RolloutProfile.enabled_phases` lists that explicitly include BOTH `ENABLE_SELF_MODEL_COGNITION` and `ENABLE_ADVENTURE_ROUTING` together — a committed design target for those hardware-class profiles. No code path wires `RolloutProfileManager`'s matrix into any live `AuthoritativeState.feature_flags` default today (referenced only by `tests/unit/config/test_phase10_rollout_profiles.py` and `tests/perf/test_phase10_integrated_enhanced_stack_budget.py`), so this remains a **feature becoming reachable for the first time**, not a live regression — but the earlier blanket claim that "no shipped profile combines these two flags" must be qualified: true for `config/`/`data/worlds/` runtime profiles, NOT true of `RolloutProfileManager`'s committed CLASS_B/CLASS_C matrix, which this fix must not silently break (see section 4.5). |
| 5 | `src/domains/adventure/scoring.py:99` (`getattr(entity.self_model.needs, "active_needs", {})`) | Yes, same `ENABLE_ADVENTURE_ROUTING` gate as #4, same file's `AdventureDecisionPhase` | Same reasoning as #4 — currently always `{}`, would start reflecting real needs once both flags ON. | Same as #4 — contained, same test-coverage recommendation, including the `RolloutProfileManager` committed-matrix caveat. |
| 6 | `src/domains/information/assimilation.py:37` (`InformationAssimilationService`, `self_model = entity.self_model`) | Yes — Branch A, already shipped and load-bearing (`TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`) | Reads `entity.self_model` to build on **prior** facts when assimilating a new `InformationResponse`. Prior to this fix, always starts from empty — after, genuinely accumulates facts tick over tick, matching the docstring intent. | **None — intended fix effect.** No shipped profile currently depends on cross-tick fact accumulation being broken; this only strengthens the existing, already-verified Branch A behavior (calibration already confirms `belief_assimilated` fires; nothing currently asserts the bundle stays empty). |
| 7 | `src/domains/information/phase.py:69, 85-89` (`InformationBeliefPhase.apply()` — Branch A write at line 69, Branch B read at line 85-89) | Yes — both branches, gated `ENABLE_BELIEF_ASSIMILATION` | Branch B's routing precondition (`self_model.knowledge.unknowns` populated) can now genuinely be met **across a tick boundary** once self_model durably persists — this is precisely the follow-up this ticket's own Finding 5 recommended. Within a single `refine()` call Branch B still cannot see the *same-tick* self_model write (phase-ordering limitation, unrelated to materialization — confirmed in `test_branch_b_on_compiled_urban_political_state_...`), but on tick N+1 it now can. | **None — intended fix effect, this is the ticket's own stated goal.** Worth an explicit "Branch B fires across a real tick boundary in the live pipeline" test (see Test Plan item 4) since no existing test proves this across `Kernel.tick_once()` — the existing Branch-B tests all hand-construct `state` to have the precondition pre-seeded rather than proving the accumulation-then-routing sequence end-to-end. |
| 8 | `src/engine/pipeline_phases/lead_contradiction.py:165, 179` (`LeadContradictionSystem`, reads/writes `entity.self_model.knowledge`) | **No** — confirmed via `grep -rln "LeadContradictionSystem" src/`: only its own defining file and `tests/unit/cognition/test_information_seeking.py` reference it. Not imported by `pipeline.py` or any other live orchestration path. | None — orphaned system, this fix has zero effect on it because it is never invoked in any live run. | **None.** Out of scope; flagged for completeness only. |
| 9 | `src/engine/domain/cognition_extras.py:61` (`InformationNeedDetector.detect_and_generate()`, `knowledge = entity.self_model.knowledge`) | **No** — confirmed via `grep -rln "InformationNeedDetector" src/ tests/`: only its own file and unit tests call it directly; no caller in `pipeline.py` or any orchestration module. Explicitly named as "still orphaned" in this ticket's own Out-of-Scope section. | None — orphaned, same reasoning as #8. | **None.** Explicitly out of scope per this ticket's Out-of-Scope list; unaffected either way. |
| 10 | `src/entities/archetype_factory.py:139, 165` (`self_model=entity.self_model` passthrough when building heir/derived entities) | Yes — heir/archetype creation path | Pure copy, no branching logic reads the bundle's content — an heir now inherits a potentially non-empty `self_model` instead of always-empty. | **None.** No logic keys off the copied value's content; this is a structural copy only. |
| 11 | `src/core/state.py:750` (`EntityState.to_canonical_dict()`, `"self_model": self.self_model.to_canonical_dict()`, unconditional — no flag/gate) and `:887` (`with_...`-style copy, `self_model=self.self_model`) | Yes — canonical hashing AND debug export share the exact same code path | **Correction (architecture review, 2026-07-04): the docstring at `src/core/self_model.py:216-219` claiming `SelfModelBundle` is "intentionally excluded from authoritative canonical hash" is FALSE and pre-existing (not introduced by this fix).** `CanonicalStateHasher.to_canonical_data()` (`src/engine/checkpoint.py:81`, the authoritative hash used for determinism/replay/certification, gated by `CanonicalHashScheduler`) calls `state.entities[eid].to_canonical_dict()` for every entity — the identical method that includes `"self_model"` at line 750. There is no separate hash-only vs. debug-only path. `self_model` DOES participate in the canonical hash today, and always has. | **Docstring correction required (see section 7), NOT a hash-formula change.** Changing hash computation itself is out of scope — it would retroactively alter every existing calibration baseline's hash value across the whole test suite. Because `ENABLE_SELF_MODEL_COGNITION` is OFF in every shipped profile, `self_model` stays constant `SelfModelBundle.empty()` regardless of whether this fix lands, so no shipped baseline's hash VALUE changes as a direct result of this fix — only the docstring's claim about what participates in the hash was wrong. |
| 12 | `src/observability/event_extractor.py:277` (`getattr(e_upd_ext, "self_model_bundle_set", None) is not None` → emits `self_model_updated` telemetry event) | Yes | Reads the **`EntityUpdate`**, not `EntityState.self_model` — already fires correctly today regardless of durable materialization (confirmed: this event has always fired whenever the phase runs, since it's built off the same-tick `update`, not the committed `state`). | **None** — already decoupled from Finding 5; unaffected by this fix in either direction. |
| 13 | `src/simulation_quality/scorers/cognition.py:90-91` (consumes `self_model_updated` event → `self_model_active` pillar credit) | Yes | Consumes the telemetry event from #12, not durable state directly — unaffected by this fix. | **None**, same reasoning as #12. |
| 14 | `src/domains/campaigns/scorecard.py` / `schema.py` / `reports.py` (`self_model_usage` field) | Yes | **False positive** — `self_model_usage` here is an unrelated campaign-scorecard field derived from `behavior_change_proofs` (event-derived, from `BehaviorDetector.detect(events)`, `runner.py:134`), not from `entity.self_model` at all. Confirmed via `grep -rn "behavior_change_proofs" src/` — no path from this field back to `EntityState.self_model`. | **None** — not actually a consumer of the field this fix touches; name collision only. |
| 15 | `src/testing/scenario_runner.py:60` (imports `SelfModelBundle`, `SelfAwarenessComponent`, `NeedInterpretationComponent`) | Test scaffolding only | Import-only; no runtime read of `entity.self_model` content. | **None.** |

**Summary:** of 15 identified touch-points, 2 are orphaned code with zero live callers (#8, #9,
already out of scope per the ticket), 3 are false positives / already-decoupled telemetry paths
(#12, #13, #14), 1 is pure passthrough (#10), 1 required a **docstring correction, not a code
change** (#11 — the "excluded from canonical hash" claim was false; `self_model` already
participates in the canonical hash today, see section 7), and the remaining 8 are all **intended,
positive fix effects** — every one of them was previously silently getting `SelfModelBundle.empty()`
(all-defaults) instead of real data, and the fix simply makes them see what they were always
supposed to see. The only two consumers with *any* live behavior change under currently-plausible
flag combinations are #4/#5 (`AdventureRouteGenerator`/`scoring.py`, under
`ENABLE_SELF_MODEL_COGNITION` + `ENABLE_ADVENTURE_ROUTING` both ON) — no shipped `config/`/
`data/worlds/` runtime profile combines those two flags today, but `RolloutProfileManager`'s
committed `CLASS_B`/`CLASS_C` matrix (`src/domains/optimization/rollout_profiles.py:59-63,73-79`)
does combine them, even though nothing wires that matrix into a live default yet (see corrected
row #4 above and section 4.5).

---

## 4. Test plan — regression sweep targeting every live consumer above, not just cognition/information tests

### 4.1 New unit tests — `tests/unit/optimization/test_component_patches.py`
Mirror the existing `test_patch_noop_detection` / `test_patch_merging` pattern (lines 10-31) with a
`SelfModelPatch`-specific set:
- `test_self_model_patch_noop_detection` — `SelfModelPatch(entity_id=1, self_model_bundle_set=None).is_noop() is True`;
  non-`None` bundle → `is_noop() is False`.
- `test_self_model_patch_merge_prefers_other` — two `SelfModelPatch` instances with distinct bundles,
  confirm `merge()` returns `other`'s bundle (last-write-wins), and confirm `self`'s bundle is
  preserved when `other.self_model_bundle_set is None`.
- `test_self_model_patch_apply_sets_changes_key` — construct a bare `EntityState`-like stub (or reuse
  `V2EntityBuilder`), call `.apply(entity, changes)`, assert `changes["self_model"] is bundle`
  (identity, not just equality — confirms no incidental copy/mutation).
- Extend `test_order_sensitivity` (or add a sibling) to include `self_model_bundle_set` in the
  `EntityUpdate(...)` construction and confirm `SelfModelPatch` appears in `extract_patches()`'s
  output list — no ordering constraint to assert (confirmed no dependency in section 2), just
  presence.

### 4.2 New/updated integration test — `tests/integration/optimization/test_component_patch_apply_parity.py`
Add a case asserting **durable materialization end-to-end**: build an `EntityUpdate` with a non-empty
`self_model_bundle_set` (real `SelfModelBundle` with populated `knowledge.facts`/`knowledge.unknowns`),
run it through `ApplyPath._apply_entity_update()` (or `apply_generation()`), and assert
`result_entity.self_model == the_bundle` (full equality, not just `is not None`) — this is the direct
regression guard for Finding 5 itself.

### 4.3 Strengthen existing (weak) assertions in `tests/integration/domains/test_fused_loop.py`
Per section 5 below — these currently pass trivially and will continue to pass after the fix, but
should be strengthened to actually prove the fix rather than merely tolerate it:
- `test_belief_assimilation_persists_facts` (line 168-217): change
  `assert next_actor.self_model.knowledge is not None` (line 217) to assert the **coal_ore fact
  content** — e.g. `next_actor.self_model.knowledge.facts.get("coal_ore") is not None` and its
  `details == {"source": "old_mine"}` (or equivalent, whatever `InformationAssimilationService`
  actually produces for a `KNOWN_FACT` response) — this is the assertion the test's own docstring
  ("Verify Phase 5 belief assimilation facts persist into entity.self_model across ticks") already
  promised but never checked.
- `test_self_model_apply_sources_events_from_pending_field_isolated_from_finding4` (line 220-271):
  remove/rewrite the stale "NOTE (Finding 5... not part of this ticket's approved scope)" comment
  block (lines 259-270) — it will no longer be accurate once this follow-up lands — and strengthen
  line 271's `assert next_state.entities[1].self_model.knowledge is not None` to assert the actual
  `unknowns["material.moon_resin.source"]` entry persisted with the expected `reason`.
- `test_branch_b_on_compiled_urban_political_state_self_model_and_branch_a_coexist` (line 389-437):
  its docstring's "Honest scope note" (lines 398-405) about same-tick visibility remains accurate
  (that's a phase-ordering fact, independent of Finding 5) and needs no change; no assertion in this
  test currently depends on durable materialization, so no strengthening needed here, but a
  **new** sibling test (4.4 below) should prove the cross-tick case this test deliberately doesn't
  cover.

### 4.4 New test proving Branch B fires across a real tick boundary (the ticket's own recommended follow-up, now addressed)
Add to `tests/integration/domains/test_fused_loop.py` or
`tests/integration/scenarios/test_phase5_information_belief_scenarios.py`: seed
`pending_self_model_information_events` for an entity with an `"unknown"` event, run
`AuthoritativeApplyPipeline.refine()` + `ApplyPath.apply_generation()` to materialize tick N's
self_model write, then run a **second** `refine()` call on the resulting `next_state` (tick N+1, no
new seed) with `ENABLE_BELIEF_ASSIMILATION` ON and confirm `InformationBeliefPhase`'s Branch B now
routes a query for that entity — proving the full seed → assimilate → materialize → route sequence
works end-to-end across a tick boundary, which is exactly what Finding 5 blocked and this fix
resolves.

### 4.5 Blast-radius-targeted regression probes (not just cognition/information suites)
Per the blast-radius table, run/extend:
- `tests/unit/domains/adventure/test_phase3_route_generator.py` and
  `tests/unit/domains/adventure/test_phase3_route_scoring.py` — add one case with a non-empty
  `self_model_bundle_set` in a durable entity (built via `V2EntityBuilder.replace_self_model(...)`)
  confirming `AdventureRouteGenerator.generate()`/scoring correctly surfaces the forced
  `RECOVER`/equipment-improvement routes when `perceived_weaknesses`/`active_needs` are non-empty —
  this exercises consumer #4/#5's previously-dead code path for the first time under direct test
  control (not full both-flags-on pipeline, which is out of scope for a shipped profile).
- `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py` — confirm no existing
  test asserts routes are ALWAYS absent when weaknesses would be non-empty (i.e., no test is
  accidentally relying on `self_model` always being empty as an implicit precondition). Spot-check
  performed this session: `test_phase3_adventure_decision_boundary.py:38-39` already **constructs**
  a non-empty `self_model` by hand and asserts on it directly — confirms the adventure domain's own
  test suite does not assume permanent emptiness.
- `tests/unit/config/test_phase10_rollout_profiles.py` and
  `tests/perf/test_phase10_integrated_enhanced_stack_budget.py` (added 2026-07-04, architecture
  review) — these are the only two test files exercising
  `src/domains/optimization/rollout_profiles.py`'s `RolloutProfileManager`, whose `CLASS_B`
  (lines 59-63) and `CLASS_C` (lines 73-79) `RolloutProfile.enabled_phases` matrices commit to BOTH
  `ENABLE_SELF_MODEL_COGNITION` and `ENABLE_ADVENTURE_ROUTING` being enabled together — the same
  flag combination flagged as consumer #4/#5's live-behavior-change trigger. No live code path wires
  this matrix into `AuthoritativeState.feature_flags` today, so it does not gate any current run, but
  both files must be re-run unchanged to confirm this fix does not silently break the committed
  matrix's shape or its perf budget assertions.
- Full regression sweep (existing suites, re-run unchanged): `tests/unit/cognition/`,
  `tests/unit/domains/information/`, `tests/unit/domains/adventure/`, `tests/unit/optimization/`,
  `tests/unit/config/test_phase10_rollout_profiles.py`, `tests/perf/test_phase10_integrated_enhanced_stack_budget.py`,
  `tests/integration/optimization/`, `tests/integration/domains/test_fused_loop.py`,
  `tests/integration/domains/information/`, `tests/integration/domains/adventure/`,
  `tests/integration/scenarios/test_phase5_information_belief_scenarios.py`,
  `tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py`,
  `tests/integration/scenarios/test_phase2_self_model_scenarios.py`, `tests/unit/entity/test_phase2_self_model_components.py`,
  `tests/unit/core/test_entity_integrity.py` (canonical-hash participation + baseline-stability, see 4.6, corrected 2026-07-04),
  `tests/perf/test_phase2_self_model_budget.py`, `tests/perf/test_phase5_information_belief_budget.py`,
  `tests/simulation_quality/test_cognition_scorer.py`, `tests/simulation_quality/test_information_scorer.py`,
  `tests/unit/campaigns/test_phase9_semantic_campaign_scorecard.py` (confirm #14 false-positive holds — no change expected),
  plus a `calibrate_simq.py` spot-check on `urban_political` (shipped flags, confirms zero shipped-profile
  regression) — consistent with the depth of the sweep already run for Steps 1-9.

### 4.6 Determinism / canonical-hash participation + baseline-stability regression (consumer #11, corrected 2026-07-04)
Architecture review confirmed the plan's original premise here was **false**: `self_model` is NOT
excluded from the authoritative canonical hash — `CanonicalStateHasher.to_canonical_data()`
(`src/engine/checkpoint.py:81`) calls the exact same `EntityState.to_canonical_dict()`
(`src/core/state.py:750`) that unconditionally includes `"self_model": self.self_model.to_canonical_dict()`.
There is no separate hash-only vs. debug-only code path. Do NOT propose changing hash computation —
that would retroactively change every existing calibration baseline's hash value across the whole
test suite, far too large a blast radius for this ticket. Instead, add two tests to
`tests/unit/core/test_entity_integrity.py`:

1. `test_self_model_participates_in_canonical_hash` — construct two otherwise-identical
   `EntityState`s differing ONLY in `self_model` content (e.g. one with `SelfModelBundle.empty()`,
   one with a `SelfModelBundle` carrying a non-empty `knowledge.facts` entry), and assert their
   `to_canonical_dict()` outputs (and therefore `CanonicalStateHasher`-derived hashes) are
   **DIFFERENT** — the opposite of what this plan originally (incorrectly) proposed to test. This is
   the corrected, actually-true invariant: `self_model` participates consistently in the canonical
   hash; it is never excluded.
2. `test_self_model_fix_preserves_existing_baseline_hashes_when_flag_off` — a before/after
   hash-stability regression guard: run at least one existing calibration scenario (e.g.
   `urban_political`, matching the `calibrate_simq.py` spot-check already planned in section 4.5)
   with `ENABLE_SELF_MODEL_COGNITION` OFF (the shipped default), once on the pre-fix code path and
   once on the post-fix (`SelfModelPatch`-wired) code path, and assert the canonical hash is
   **identical** across both — proving this fix changes zero shipped baseline hash values, because
   `self_model` stays constant `SelfModelBundle.empty()` regardless of whether `SelfModelPatch`
   wiring exists, when the flag is off.

Both tests directly support the corrected docstring in section 7 and the new parity ledger entry
`SUB-374` (`docs/parity_ledger/substrate.yaml`).

---

## 5. Tests currently asserting the broken (None-tolerant) behavior — must be strengthened, not just left passing

Confirmed via `grep -rn "self_model" tests/` that **no** test currently asserts
`entity.self_model is None` (there would be nothing to "break" in that direction — the field always
defaults to `SelfModelBundle.empty()`, never `None`, for any entity built via `V2EntityBuilder`).
The actual regression-class risk identified (matching the ticket's own framing) is the opposite
shape: tests asserting `is not None` where `SelfModelBundle.empty()`'s always-non-None default makes
the assertion trivially true regardless of whether the field materializes correctly. Two confirmed
instances, both in `tests/integration/domains/test_fused_loop.py`:

1. Line 217 — `test_belief_assimilation_persists_facts`: `assert next_actor.self_model.knowledge is not None`
2. Line 271 — `test_self_model_apply_sources_events_from_pending_field_isolated_from_finding4`: `assert next_state.entities[1].self_model.knowledge is not None`

Neither will **fail** once the fix lands (both stay non-`None`) — but both must be strengthened per
section 4.3 so they actually validate the fix instead of continuing to pass by coincidence. This
mirrors the exact gap this ticket's own Finding 5 called out in `test_belief_assimilation_persists_facts`.

No test was found asserting `SelfModelBundle.empty()`-equality or emptiness as an expected/required
outcome (i.e., no test would need to be *deleted* or have its expected value changed from empty to
non-empty) — the two items above are strengthenings, not corrections of a wrong expected value.

---

## 6. Documentation / parity ledger follow-up (do not skip once code lands)

- `docs/cognition/self_model_contract.md:87` — "The resulting `SelfModelBundle` is written to
  `entity.self_model` through the authoritative apply path." This line is **currently false**
  (the entire substance of Finding 5) and will become true once this fix lands — no wording change
  needed at that point, but this is the exact sentence that re-establishes doc/code parity.
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-256`'s `support_boundary` (line ~3064) currently
  reads "Branch B (`self_model.knowledge.unknowns`) remains unreachable: `SelfModelUpdatePhase.apply()`
  hardcodes `events=[]`..." — this sentence is itself now stale (Steps 1-9 already fixed the
  `events=[]` half; this fix resolves the remaining materialization half). Needs a follow-up
  `v2_evidence`/`support_boundary` update citing this fix's `test_path`(s) once implemented, per the
  Authoritative Mechanics Rule's parity requirement.
- Per this ticket's own precedent (documenting Finding 4/5 honestly rather than silently patching),
  record this fix in the ticket's `Implementation Notes` as a distinct, separately-tested addendum,
  and reference `docs/guidelines/design_patterns.md` Pattern 2 (Decision/Mutation Separation via
  Typed Update Records) as the pattern this fix completes — `self_model_bundle_set` was a Pattern-2
  typed update record whose apply-path wiring was simply missing, not a new pattern.

---

## 7. Correction (architecture review, 2026-07-04): self_model DOES participate in the canonical hash — docstring was false, not the code

**Finding:** the plan's original consumer #11 entry (section 3) and original test 4.6 both repeated
a false claim already present in `src/core/self_model.py:216-219`'s docstring — that
`SelfModelBundle` is "intentionally excluded from authoritative canonical hash." Direct code
inspection shows:
- `EntityState.to_canonical_dict()` (`src/core/state.py:750`) unconditionally includes
  `"self_model": self.self_model.to_canonical_dict()` — no flag, no gate, no conditional.
- `CanonicalStateHasher.to_canonical_data()` (`src/engine/checkpoint.py:81`) — the authoritative
  hash used for determinism/replay/certification, gated by `CanonicalHashScheduler` — calls
  `state.entities[eid].to_canonical_dict()` for every entity, i.e. the EXACT SAME method used for
  the hash and for debug/inspection exports. There is no separate "hash path" vs. "debug path."

This is a **pre-existing docstring/code divergence**, not introduced by this fix. It is benign today
only because `ENABLE_SELF_MODEL_COGNITION` is OFF in every shipped profile, so `self_model` stays
constant `SelfModelBundle.empty()` regardless of whether the `SelfModelPatch` fix (sections 1-2)
lands — no shipped baseline's hash VALUE changes as a direct result of this fix.

**Decision:** do NOT change hash computation to retroactively make the docstring's claim true — that
would alter every existing calibration baseline's hash value across the whole test suite, far too
large a blast radius for this ticket. Instead, correct the docstring to match actual code, and
record the true (inclusive) behavior in the parity ledger.

### 7.1 Docstring fix — `src/core/self_model.py:216-219`

Old text (false — to be removed):
```python
    Default: all components at their empty/zero default values.
    Intentionally excluded from authoritative canonical hash (it is derived from
    raw state, not a mutation source).  Include via to_canonical_dict() only in
    inspection/debug exports.
```

New text (corrected — replaces the above verbatim, same location within the `SelfModelBundle`
class docstring, lines 216-219 of `src/core/self_model.py`):
```python
    Default: all components at their empty/zero default values.
    Participates in the authoritative canonical hash: to_canonical_dict() is called
    unconditionally by EntityState.to_canonical_dict() (src/core/state.py:750), which is
    the same method CanonicalStateHasher.to_canonical_data() (src/engine/checkpoint.py:81)
    uses to compute the full canonical hash for determinism/replay/certification. There is
    no separate hash-only vs. debug-only code path — to_canonical_dict()'s output is used
    for both the canonical hash and inspection/debug exports.
```

This is a pure documentation correction — no behavior changes as a result of this edit alone.

### 7.2 New parity ledger entry — `docs/parity_ledger/substrate.yaml`

Confirmed the correct home: no existing entry in `substrate.yaml`, `strategic_cognition.yaml`, or
`infrastructure.yaml` covers this canonical-hash-participation claim. Next available ID in
`substrate.yaml` is `SUB-374` (last existing entry is `SUB-373`). Add:

```yaml
- id: SUB-374
  text: >
    EntityState.self_model (SelfModelBundle) participates in the authoritative canonical
    hash. EntityState.to_canonical_dict() unconditionally includes
    "self_model": self.self_model.to_canonical_dict(), and
    CanonicalStateHasher.to_canonical_data() calls this same method for every entity when
    computing the full canonical hash used for determinism/replay/certification. There is
    no separate hash-only vs. debug-only code path for self_model.
  status: divergent
  priority: P1
  legacy_evidence: null
  v2_evidence: >
    src/core/state.py:750 (EntityState.to_canonical_dict(), unconditional
    "self_model" key) + src/engine/checkpoint.py:81
    (CanonicalStateHasher.to_canonical_data(), calls entities[eid].to_canonical_dict()
    for every entity) + src/core/self_model.py:216-219 (SelfModelBundle docstring,
    corrected under TCK-20260703-SIMQ-UPLIFT3-BRANCH-B)
  proof_type: parity
  test_path: tests/unit/core/test_entity_integrity.py::test_self_model_participates_in_canonical_hash
  divergence_note: >
    The SelfModelBundle docstring previously claimed self_model was "intentionally excluded
    from authoritative canonical hash" — this was false and pre-existing, not introduced by
    TCK-20260703-SIMQ-UPLIFT3-BRANCH-B's self_model_bundle_set materialization fix. The
    docstring was corrected to match actual code (self_model IS included), rather than
    changing the hash formula to match the stale docstring — changing hash computation would
    retroactively alter every existing calibration baseline's hash value across the whole
    test suite, judged out of scope / too disruptive for this ticket. Because
    ENABLE_SELF_MODEL_COGNITION is OFF in every shipped profile, self_model stays constant
    SelfModelBundle.empty() regardless of this fix, so no shipped baseline's hash VALUE
    changes as a direct result of landing SelfModelPatch.
  support_boundary: null
```

To be applied to `docs/parity_ledger/substrate.yaml` in the same session this fix's code lands, per
the Authoritative Mechanics Rule's parity requirement — alongside the `src/core/self_model.py`
docstring fix in section 7.1 and the `docs/cognition/self_model_contract.md` / `INFRA-256` updates
already noted in section 6.

---

## Unresolved questions requiring human decision

**None remaining** after the 2026-07-04 architecture review corrections (see section 7 and the
updated table rows #4/#11 above). The blast-radius sweep is fully resolved with evidence:
- 2 of 15 consumers are confirmed orphaned (zero live callers) — no risk.
- 3 are false positives / already-decoupled telemetry — no risk.
- 1 is pure passthrough — no risk.
- 1 (#11, canonical hash) required a **docstring correction, not a verification test** —
  architecture review found the docstring's "excluded from canonical hash" claim was false
  (`self_model` already participates in the canonical hash today, via the same
  `to_canonical_dict()` path used by both `EntityState`'s hash and its debug export). Section 7
  specifies the exact corrected docstring text and a new parity ledger entry (`SUB-374`) recording
  this. Test 4.6 was rewritten accordingly to assert the true invariant (self_model participation)
  instead of the false one (exclusion), plus a baseline-stability regression guard.
- The only 2 consumers with any live conditional behavior change (#4/#5, `AdventureRouteGenerator`)
  require both `ENABLE_SELF_MODEL_COGNITION` and `ENABLE_ADVENTURE_ROUTING` ON simultaneously. This
  combination exists in **no shipped `config/`/`data/worlds/` runtime profile today** (confirmed via
  direct config grep), but architecture review found it IS present as a committed (if currently
  unwired) design target in `RolloutProfileManager`'s `CLASS_B`/`CLASS_C` matrices
  (`src/domains/optimization/rollout_profiles.py:59-63,73-79`). Turning either flag on globally in
  any shipped calibration profile remains explicitly out of scope for both this ticket and its
  parent (`UQ-2`). This is a feature becoming reachable as designed, not a concerning behavior
  change — the regression sweep (section 4.5) now explicitly includes both `RolloutProfileManager`
  test files (`tests/unit/config/test_phase10_rollout_profiles.py`,
  `tests/perf/test_phase10_integrated_enhanced_stack_budget.py`) so this fix cannot silently break
  the committed matrix.

Both points a reviewer previously flagged as worth a second look (the canonical-hash exclusion
claim and the "no shipped profile combines these two flags" claim) have been corrected above; no
further open question remains before implementation.

---

## Deviations (implementation session, 2026-07-04)

Implemented as specified with the following execution-level adjustments (no scope or architecture
deviation from the approved plan):

1. **Section 4.4 (cross-tick-boundary test)**: `information_source_profiles` on `AuthoritativeState`
   turned out to be a per-tick-seeded field itself (not carried forward by
   `ApplyPath.apply_generation()`, same as `pending_information_responses` and
   `pending_self_model_information_events`) — this was not called out explicitly in section 3's
   blast-radius table. The new test
   (`test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`,
   `tests/integration/domains/test_fused_loop.py`) re-seeds `information_source_profiles` on
   `next_state` before the tick N+1 `refine()` call, with an explicit assertion confirming it resets
   to `[]` after tick N (documented inline as unrelated to this fix — a live world would supply
   routable source profiles every tick regardless).
2. **Section 4.6 test 2 (hash-stability regression guard)**: the plan's proposed "run once on
   pre-fix code path, once on post-fix code path" was implemented as a single self-contained unit
   test in `tests/unit/core/test_entity_integrity.py` using a navigation-only `EntityUpdate` (not an
   attribute-delta update as might be the naive choice) to stay clear of the PH8 derived-stats
   recompute block (`src/engine/apply.py:448-497`), and `ApplyPath.apply_generation(..., passive=False)`
   to disable ambient per-tick biological/lifecycle aging systems — both of which would otherwise
   make the manually-reconstructed comparison state diverge from the real apply-path output for
   reasons unrelated to `self_model`. The test asserts `extract_patches()` never emits a
   `SelfModelPatch` when `self_model_bundle_set` is `None`, and that the resulting canonical hash
   matches a manually-constructed equivalent state where `self_model` was never touched.
3. **Section 4.5 / 7 (hash stability spot-check)**: in addition to the unit-level test above, ran a
   direct empirical proof: compiled `urban_political`'s real resolved world (seed 42, shipped default
   flags), advanced 50 ticks through the real pipeline, and computed
   `CanonicalStateHasher.get_hash()` both with `SelfModelPatch` present and with
   `src/engine/patches.py`'s `SelfModelPatch` addition temporarily reverted via `git stash push --
   src/engine/patches.py` (isolating exactly this fix's code, none of Steps 1-9's already-shipped
   changes). Both hashes were bit-identical
   (`15081e225da292dd91ae8179922729ec0103f1b9a09cc64be8e14f49c8549591`), directly confirming the
   plan's central hash-stability claim rather than relying solely on the unit-test proxy.
4. **Section 4.5 (adventure-domain regression probes)**: confirmed, as the plan itself anticipated in
   its own spot-check note, that `tests/unit/domains/adventure/test_phase3_route_generator.py` and
   `test_phase3_route_scoring.py` already construct non-empty `self_model` bundles directly via
   `V2EntityBuilder.replace_self_model()` (bypassing the apply pipeline entirely) and already assert
   on the previously-dead `RECOVER`/`ASK_INFORMATION` forced-route paths. No new test was added there
   — re-ran the existing suite unchanged as part of the regression sweep, per the plan's own
   conclusion that this was already covered.
5. **Section 6 (docs follow-up)**: `docs/cognition/self_model_contract.md:87` and
   `docs/parity_ledger/infrastructure.yaml`'s `INFRA-256` `support_boundary` update were left
   deferred, consistent with this ticket's own precedent of deferring the whole-ticket docs pass
   (Step 10) to a separate phase — this session's explicit implementation scope was sections 1, 2,
   7.1, and 7.2 only (code + `SUB-374` parity ledger entry), not the full section 6 doc sweep.

No test failures were encountered that indicated an incorrect premise in the plan; all deviations
above are implementation-detail adjustments needed to make the specified tests concretely runnable,
not changes to the plan's architecture or scope.

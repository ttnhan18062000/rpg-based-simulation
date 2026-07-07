---
status: active
layer: world
authority: P1
audience: agent
artifact_type: investigation
tags: [simulation-quality, self-model, corpus, calibration, cognition]
---

# Investigation — TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT

PHASE_TS: 2026-07-07T00:27:21Z

## Context search performed (per CLAUDE.md hard rule)

1. `mcp__knowledge-search__search_docs` (query: "Branch B self-model pending_self_model_information_events
   ENABLE_SELF_MODEL_COGNITION SelfModelUpdatePhase InformationBeliefPhase interaction") — surfaced
   `docs/audits/D19_domain_phase_inventory.md` (§2/§3 phase inventory), `docs/cognition/README.md`
   ("Pipeline: SelfModelUpdatePhase"), `docs/plans/idea_information_belief_trigger_wiring.md`,
   `tickets/done/TCK-20260703-SIMQ-UPLIFT3-BRANCH-B.md`, and
   `docs/simulation_quality/event_type_coverage.md` (the `self_model_updated` row) — confirming the
   prior-work trail this ticket depends on.
2. `graphify query "pending_self_model_information_events ENABLE_SELF_MODEL_COGNITION
   SelfModelUpdatePhase self_model canonical hash"` — 657-node BFS rooted at `SelfModelUpdatePhase`
   and the BRANCH-B ticket's own summary node; confirmed `SelfModelPatch` (`src/engine/patches.py`),
   `KnowledgeModelComponent`/`UnknownFact`/`SelfModelBundle` (`src/core/self_model.py`), and
   `AuthoritativeState`/`StateUpdate`/`EntityUpdate` as the structural surface — no undiscovered edge
   contradicted the doc trail.

Both tools confirmed the same picture later verified by direct source reads; raw grep/Read was used
only as follow-up per the Hard Rules.

**Path correction (per task instruction):** the ticket cites
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md`. That folder was renamed;
the current path is `staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md` (its own
first paragraph documents the rename). All §3/§4 references below are to that file.

---

## 1. All 3 Branch-B fixes re-verified genuinely in place (not reverted/touched since)

Re-read every file directly this session (not assumed from the prior ticket's own claims):

1. **`events=[]` hardcoding fixed** — `src/cognition/self_model_phase.py:45-61`
   (`SelfModelUpdatePhase.apply()`): builds `events_by_actor: Dict[int, List[Any]]` by grouping
   `getattr(state, "pending_self_model_information_events", [])` by `entry["actor_id"]`, then passes
   `events=events_by_actor.get(entity_id, [])` into `.run()` — no `events=[]` literal remains anywhere
   in the file.
2. **`information_belief` pipeline-wiring merge fix in place** — `src/engine/pipeline.py:152`:
   `update = run_phase("information_belief", update, lambda u:
   u.merge(InformationBeliefPhase.apply(state, source_profiles, pending_resps)),
   "ENABLE_BELIEF_ASSIMILATION")` — the `u.merge(...)` wrapper (Finding 4's fix, `INFRA-260`) is
   present, matching the sibling `faction_awareness`/`diplomatic_transitions`/`military_conflict`
   call sites.
3. **`SelfModelPatch` materialization fix in place** — `src/engine/patches.py:629-646` defines
   `SelfModelPatch(ComponentPatch)` with `is_noop()`, `merge()`, and `apply()` (writes
   `changes["self_model"] = self.self_model_bundle_set`); `extract_patches()` (`patches.py:704-706`)
   emits it whenever `update.self_model_bundle_set is not None`. `EntityUpdate.self_model_bundle_set`
   (`src/core/updates.py:637`) and its `merge()` last-write-wins wiring (`updates.py:694`) are intact.
   `src/engine/apply.py:578`'s `changes.get("self_model", ...)` read site (previously fed by nothing)
   is now fed by this patch.

All 3 confirmed via direct file read this session, not inferred from the prior ticket's prose.
Ran the existing regression suite live: `pytest tests/unit/cognition/test_phase2_self_model_phase.py
tests/unit/optimization/test_component_patches.py -q` → **14 passed**;
`pytest tests/integration/domains/test_fused_loop.py -q -k "self_model or branch_b or belief"` →
**7 passed** (includes
`test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`,
`test_information_belief_merge_preserves_self_model_writes_both_flags_on`,
`test_belief_assimilation_persists_facts`). Nothing regressed.

Parity ledger cross-check: `docs/parity_ledger/infrastructure.yaml::INFRA-259`/`INFRA-260` and
`docs/parity_ledger/substrate.yaml::SUB-374` all exist with `status: verified`/`divergent`
respectively, and `docs/simulation_quality/event_type_coverage.md`'s `self_model_updated` row already
documents the fix and its current 0-hit state (flag OFF everywhere shipped). `strategic_cognition.yaml`
has no self_model/Branch-B/`SUB-3xx`/`INFRA-259`/`INFRA-260` entry — confirms `infrastructure.yaml` +
`substrate.yaml` remain the correct homes, per the prior ticket's own resolved decision.

---

## 2. World composition and addressing mechanism

### Addressing mechanism — confirmed identical to `UNIT-WORLDS-FACTION-INFO`'s precedent

Traced `src/worldbuilding/compiler.py:265-317`: for each `PopulationSpec` in the fully merged
`WorldSpec.entities` list, `pop_key = getattr(pop_spec, "id", f"pop_{pop_idx}")` and every compiled
entity from that spec gets `properties["population_id"] = pop_key`.
`pending_self_model_information_events`' `target_population_id` is resolved at compile time
(`compiler.py:456-473`) via `next((eid for eid, e in entities.items() if
e.properties.get("population_id") == r.target_population_id), None)` — the **identical** mechanism
already used for `pending_information_responses` (`compiler.py:428-452`) and confirmed by
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`'s own World B (`unit_information_source`, which
targets `pop_0`).

The actual `pop_N` **string** is assigned by `src/worldassembly/resolver.py:452-453`:
`pop_id = f"{prefix}{getattr(pop, 'id', f'pop_{pop_idx}')}"`, where `pop_idx` enumerates
**that module's own** `population_recipes` list (not a global index across the whole world), and
`prefix` is the module's `namespace` (if any) from its `module_refs` entry. This explains
`urban_political`'s resolved `pop_0`/`pop_1`/`pop_2` (from `hero_adventurers`, 3 recipes, no
namespace) and `trading_pop_0` (from `trading_company_hub`, namespace `"trading"`). Modules whose
populations come from the catalog `populations: [...]` shorthand (e.g. `frontier_village_core`'s
`"frontier_village_population"`) get compound catalog-derived ids
(`frontier_village_population_village_worker`, etc.) instead of bare `pop_N` — **not** every module
yields `pop_N`-style ids; only modules with raw `population_recipes:` entries lacking an explicit
`id:` do (confirmed: `hero_adventurers`, `trading_company_hub`).

**Conclusion: identical positional `pop_N` fallback mechanism as the FACTION/INFORMATION sibling
ticket used** — confirmed by source read, not assumed from the ticket's own framing.

### Concrete composition recommendation

`hero_adventurers` (`data/content/world_modules/hero_adventurers.yaml`) is the cleanest module for
unambiguous single-actor addressing: 3 population recipes, each `count: 1`, no explicit `id`, no
namespace when referenced without one → yields exactly `pop_0`, `pop_1`, `pop_2`, each a **single**
distinct entity (no ambiguity from `next()` picking "first of N" within a larger count group).

Recommended composition, mirroring `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`'s own World B
almost exactly (that ticket used `frontier_village_core` + `hero_adventurers` = 16 entities, target
`pop_0`):

```yaml
module_refs:
  - module_id: "frontier_village_core"   # 13 entities: 8 worker + 3 guard + 1 merchant + 1 blacksmith
  - module_id: "hero_adventurers"        # 3 entities: pop_0, pop_1, pop_2 (each count:1, no namespace)
```

= **16 entities total** — above `wilderness_survival`'s 11-entity floor (UQ-1's minimum), below
`sandbox_world`'s 18 (UQ-1's stronger-evidence target), and byte-identical in shape to
`unit_information_source`'s already-proven-to-compile-and-run composition (same two modules), which
de-risks the compile/resolve step (the `stone_outcrop`/`materials.yaml` blocker that ticket hit is
already fixed in the repo — confirmed present: `data/content/foundation/materials.yaml` has a `stone`
entry).

Target actor: any of `pop_0`/`pop_1`/`pop_2` — **unlike `urban_political`, none is reserved by a
Branch-A `pending_information_responses` entry in this new world** (Scope item 3 forbids seeding one
here), so there is no `pop_0`-vs-`pop_1` collision risk analogous to the one the BRANCH-B ticket's own
plan.md had to resolve. `pop_1` is still the recommended choice purely for direct consistency with
`urban_political`'s own precedent (same field values: `answer_kind: "unknown"`,
`unknowns: ["material.moon_resin.source"]`), not because of any addressing constraint.

**If UQ-1's "stronger evidence, sandbox_world-scale" option is preferred**: add `wolf_den_near_forest`
(5 entities) → `frontier_village_core` + `wolf_den_near_forest` + `hero_adventurers` = 21 entities.
Still a valid, if slightly-above-18, population. Judgment call for the implementer, not blocking.

---

## 3. Exact Branch-B firing trigger chain (traced tick-by-tick, direct source read)

**Two distinct mechanisms are both labeled "Branch B" across the doc trail — this distinction is
load-bearing for this pilot and must not be conflated:**

- **Step 1 (`SelfModelUpdatePhase`, gated `ENABLE_SELF_MODEL_COGNITION`)**: knowledge assimilation.
  Populates `self_model.knowledge.unknowns` from `pending_self_model_information_events`. This is what
  `INFRA-259`/`SUB-374` fixed and what the epic investigation's §1 table calls "Self-model / Branch B
  seed events."
- **`InformationBeliefPhase.apply()`'s own internal branch pair, gated `ENABLE_BELIEF_ASSIMILATION`**
  (`src/domains/information/phase.py:53-105`): "Branch A" (lines 53-81, the `if actor_resps:` path —
  assimilates a Branch-A pending response) and **"Branch B"** (lines 83-105, the `elif` —
  `if actor.id not in entity_updates: ... if km and km.unknowns: ... route a query`). **This is the
  literal "Branch B" the BRANCH-B ticket's own test name
  (`test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`) and Finding
  4 both refer to** — the query-routing logic that produces `intent_results`
  (`ASK_INFORMATION`/`MOVE_TO`) and `property_updates["last_routed_query_subject"]`.

**Full trigger chain, tick by tick, confirmed by direct read of `phase.py`, `pipeline.py:130-153`, and
the passing `test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`:**

1. **Tick 0 (compile time)**: `pending_self_model_information_events` is seeded once
   (`AuthoritativeState.pending_self_model_information_events`, single-fire, not carried forward by
   `ApplyPath.apply_generation()` — confirmed, no such keyword in `apply.py`).
2. **Tick 0, `refine()`**: `self_model` phase (PP-02, gated `ENABLE_SELF_MODEL_COGNITION`) runs
   **before** `information_belief` (PP-04, gated `ENABLE_BELIEF_ASSIMILATION`) in the same call
   (`pipeline.py:142` vs. `:152`). Step 1 reads the seeded event, populates
   `self_model.knowledge.unknowns`, and writes `EntityUpdate.self_model_bundle_set` into this tick's
   `update` (surviving the merge fix even if `information_belief` also runs this tick). **But**
   `InformationBeliefPhase.apply()` reads `actor.self_model` off the **frozen `state`** parameter, not
   the in-flight `update` — so even within the same `refine()` call where both phases run, Branch B
   cannot see Step 1's own same-tick write. This is a phase-ordering fact, independent of any bug, and
   is unfixable without restructuring the pipeline (not proposed by anyone).
3. **Materialization**: `ApplyPath.apply_generation()` (via `extract_patches()` →
   `SelfModelPatch.apply()`) commits `EntityUpdate.self_model_bundle_set` into
   `EntityState.self_model` for the next tick's frozen `state`.
4. **Tick 1+, `refine()`**: `self_model`'s phase-skip / dirty-check logic
   (`self_model_phase.py:144-158`) leaves the now-durable `unknowns` entry untouched (no new event
   seeded, `has_info_event` stays `False`, `is_dirty` may be `False` too — either way the existing
   `unknowns` entry persists in `old_bundle`/`new_bundle` since nothing removes it). **If and only if
   `ENABLE_BELIEF_ASSIMILATION` is ALSO ON**, `information_belief` now sees `state.entities[id].self_model`
   with the durable unknown, and the `elif` (Branch B) at `phase.py:84-105` fires: builds an
   `InformationQuery(subject=first_unk.subject, kind="material_source")`, routes it through
   `InformationQueryRouter.route()` against `state.information_source_profiles` (which — separately —
   must be re-seeded every tick since it is *also* single-fire/not-carried-forward; a live world's
   compiled content supplies it every tick unconditionally, so this is a non-issue for a real
   calibration run, only relevant for hand-built unit tests), and if a candidate profile matches
   (`InformationQueryRouter.matches_scope()`, `kind == "material_source"` against
   `"common_resource_sources" in scopes`), resolves an intent via `InformationIntentResolver.resolve()`.

**Nothing else "resolves" or "converts" the unknown** — it is not removed from
`self_model.knowledge.unknowns` by Step 1 itself (Step 1 only *adds* unknowns via
`KnowledgeModelService.assimilate()`; nothing in the reachable pipeline deletes an entry once
recorded). It sits durably in `unknowns` every tick after materialization, indefinitely, unless/until
Branch B's routing (which itself does not clear `unknowns` either — it only sets
`last_routed_query_subject`/`last_routed_query_tick` property updates and an intent) fires. **This
means Step 1's part of the mechanism, once materialized, produces a stable, repeatable (not
one-shot) durable-state fact every subsequent tick** — good for calibration signal stability, but also
confirms `self_model_updated`'s telemetry event (see §5) will fire every tick for every alive/active
entity for the entire run once `ENABLE_SELF_MODEL_COGNITION` is ON, independent of the seeded event.

---

## 4. `ENABLE_BELIEF_ASSIMILATION` OFF — confirmed genuinely isolates Step 1, but this is a
   critical, non-obvious scope/naming gap for the ticket's own stated goal

**Confirmed by reading the actual phase code, not by trusting the ticket's own reasoning:**

- `InformationBeliefPhase.apply()` (`phase.py:27-110`) contains **both** Branch A (lines 53-81) and
  Branch B (lines 83-105) — there is exactly one call site (`pipeline.py:152`), gated by exactly one
  flag, `ENABLE_BELIEF_ASSIMILATION`. `run_phase()`'s `mode == FeatureMode.OFF` branch
  (`pipeline.py:108-110`) returns `upd` **unchanged**, before `phase_fn` (the lambda wrapping
  `InformationBeliefPhase.apply(...)`) is ever invoked.
- **Therefore: with `ENABLE_BELIEF_ASSIMILATION` OFF (as this ticket's Scope item 3 mandates),
  `InformationBeliefPhase.apply()` never runs at all in this pilot — Branch B's query-routing logic
  (the literal mechanism the BRANCH-B ticket's own test proves, and the mechanism the epic
  investigation's §3 Finding-4 risk is about) cannot fire, structurally, by construction.** This is
  not a bug and not a risk of Finding 4 recurring — it is the direct, correct consequence of gating
  the entire phase behind one flag. Because the phase never runs, there is also **no way for Finding
  4's clobbering defect to manifest** (nothing to clobber, since the phase that clobbers never
  executes) — this **positively confirms** the ticket's Scope item 3 assumption that keeping
  `ENABLE_BELIEF_ASSIMILATION` OFF avoids the interaction risk, by the strongest possible margin (the
  code path is entirely unreached, not merely well-behaved).
- **What DOES fire with only `ENABLE_SELF_MODEL_COGNITION` ON**: Step 1 (knowledge assimilation) runs
  every tick for every alive/active entity (gated by its own, independent flag), populates
  `self_model.knowledge.unknowns` for the seeded actor, and durably materializes it via
  `SelfModelPatch` — this alone is real, genuine, previously-never-exercised-at-scale signal (proves
  `INFRA-259`/`SUB-374` at multi-entity/multi-tick scale, which is this ticket's real, valid
  contribution).

**The gap**: this ticket's own Title ("Pilot Branch B (self-model) activation... with live multi-tick
evidence") and Acceptance Criteria bullet ("actual COGNITION/INFORMATION pillar grades... recorded")
read as though the pilot will observe Branch-B **query-routing** behavior at scale. **It will not, by
the ticket's own Scope item 3 design** — only Step 1's knowledge-assimilation half is exercised. The
existing single-entity proof this ticket is meant to extend
(`test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`) itself only
achieves "Branch B routes" by turning `ENABLE_BELIEF_ASSIMILATION` ON for its second tick — the exact
combination this pilot's Scope explicitly forbids. **No amount of population/tick scaling changes
this: it is a structural gating fact, not a scale/sample-size problem.** See §7 for the full
implication and the recommended honest framing.

---

## 5. SimQ pillar(s) this mechanism actually feeds — confirmed by reading the scorers directly

- **`CognitionScorer`** (`src/simulation_quality/scorers/cognition.py:14-20`, `EVENT_TYPES` includes
  `"self_model_updated"`) — `if et == "self_model_updated": return _rec(self.weights["self_model_active"],
  ...)` (line 90-91). `self_model_updated` is emitted by
  `src/observability/event_extractor.py:277-283`: `if getattr(e_upd_ext, "self_model_bundle_set", None)
  is not None: events.append(SimulationEvent(event_type="self_model_updated", ...))`. Since
  `SelfModelUpdatePhase.apply()` unconditionally assigns `self_model_bundle_set=new_bundle` for
  **every** alive/active entity **every tick** it runs (not conditional on a seeded event — confirmed
  at `self_model_phase.py:57-71`), **`self_model_updated` will fire for the entire population, every
  tick, for the whole run**, independent of whether any single actor has a seeded
  `pending_self_model_information_events` entry. This is genuine, high-volume, real COGNITION-pillar
  signal (`self_model_active` tag) as soon as `ENABLE_SELF_MODEL_COGNITION` is turned ON for this
  world — confirmed via direct code read, this is not an inert/dormant-C outcome; it is a real,
  structural, expected-nonzero signal.
- **`InformationScorer`** (`src/simulation_quality/scorers/information.py:17-25`, `EVENT_TYPES`:
  `belief_assimilated`, `lead_certainty_updated`, `lead_contradiction_resolved`,
  `paid_information_transaction`, `paid_info_changed_goal`, `belief_stale`,
  `decision_diverged_by_belief`) — **every one of these event types is emitted only from
  `InformationBeliefPhase.apply()` or its downstream intent-execution consumers** (Branch A/B, or
  `LeadContradictionSystem`/`InformationNeedDetector`, both confirmed **orphaned** — zero live callers
  outside their own test files, per the BRANCH-B ticket's own blast-radius sweep, re-confirmed present
  and unchanged this session). **With `ENABLE_BELIEF_ASSIMILATION` OFF, none of these can fire.**
  **Conclusion: this pilot, as scoped, produces genuine signal for the COGNITION pillar only — the
  INFORMATION pillar will show zero incremental signal from this pilot and should be expected/reported
  to stay at whatever its current baseline is (`C`, inert) for this world.** This directly contradicts
  a literal reading of the ticket's own AC wording ("actual COGNITION/**INFORMATION** pillar grades");
  see §7.
- **Minor, separate, out-of-scope-but-worth-noting gap**: `SelfModelUpdatePhase.run()`'s own internal
  `trace_events_collector` (`KnowledgeFactLearnedEvent`, `KnowledgeUnknownRecordedEvent`,
  `SelfAwarenessUpdatedEvent`, `NeedInterpretedEvent`, `CapabilityEstimateUpdatedEvent`,
  `self_model_phase.py:20-26`) is **never returned or collected** by `.apply()` — `.apply()` calls
  `.run()` without passing a `trace_events_collector` argument (`self_model_phase.py:57-62`), so these
  five event types are constructed and immediately discarded every call. Confirmed: neither
  `knowledge_fact_learned` nor `knowledge_unknown_recorded` appears anywhere in
  `docs/simulation_quality/event_type_coverage.md` (not even as a documented gap) — they are simply
  invisible to the whole SimQ event pipeline today, always, regardless of this pilot. This is a
  separate, pre-existing gap, not part of this pilot's job to fix, and does not change §5's conclusion
  (COGNITION credit comes entirely through `self_model_updated`, which is wired correctly), but is
  worth a one-line honesty note in the Completion Summary so nobody expects to see
  `knowledge_unknown_recorded` hits in the calibration output.

---

## 6. Test coverage that must not break

Full existing self-model/Branch-B test inventory, all confirmed passing this session
(`pytest tests/unit/cognition/test_phase2_self_model_phase.py
tests/unit/optimization/test_component_patches.py tests/integration/domains/test_fused_loop.py -q -k
"self_model or branch_b or belief or phase2"` → 21 passed total across the two runs):

- `tests/unit/cognition/test_phase2_self_model_phase.py` — 5 tests exercising `.run()` directly
  (`test_phase2_update_phase_first_run_is_always_run`, `_clean_entity_skips_run`,
  `_dirty_hp_triggers_run`, `_assimilates_info_event`, `_capability_estimates_scoped`) — unaffected by
  this ticket (no code change), must stay green.
- `tests/unit/optimization/test_component_patches.py` — 6 `SelfModelPatch`-specific tests
  (`test_self_model_patch_noop_detection`, `_merge_prefers_other`, `_apply_sets_changes_key`,
  `_apply_noop_leaves_changes_untouched`, `test_extract_patches_includes_self_model_patch`,
  `_omits_self_model_patch_when_unset`) — pure unit tests, unaffected by new world content.
- `tests/integration/domains/test_fused_loop.py` — 7 tests:
  `test_self_model_phase_runs_in_shadow_without_state_mutation`,
  `test_belief_assimilation_persists_facts`,
  `test_self_model_apply_sources_events_from_pending_field_isolated_from_finding4`,
  `test_information_belief_merge_preserves_self_model_writes_both_flags_on`,
  `test_information_belief_branch_b_routes_query_when_unknown_precondition_met`,
  `test_branch_b_on_compiled_urban_political_state_self_model_and_branch_a_coexist`,
  `test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization` — all
  hand-construct state or load `urban_political`; none reference the new world this ticket would add,
  so adding a new world/profile cannot regress them structurally. Must still pass unmodified.
- **Calibration regression sweep**: this ticket is purely additive (one new `data/worlds/<new>/`
  world + one new `config/simulation_quality/profiles/<new>.yaml`), so the existing
  `grade_anchors.json`/`FAST_ANCHOR_KEYS` entries for `urban_political`, `dungeon_crawl`,
  `sandbox_world`, `simq_routing_test`, `unit_faction_tension`, `unit_information_source` must show 0
  regression — `ENABLE_SELF_MODEL_COGNITION` stays OFF in every one of those profiles (re-confirm at
  implementation time via `grep -rn "ENABLE_SELF_MODEL_COGNITION" config/`).
- New tests needed (implementation phase, not this investigation): none required beyond what's already
  covered by the existing unit/integration suite — this ticket is content-authoring plus a calibration
  run, not a code change, so its own "new tests" are the grade-anchor entries and the
  population-stability check (following `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`'s
  precedent exactly — see `test_plan.md`).

---

## 7. Honest assessment: is there a real chance of a non-boring, non-obvious outcome?

**Yes — but it is not the interaction-bug risk the ticket's own Scope item 3 anticipated (that risk is
fully neutralized, per §4). It is a different, real risk: a scope/naming mismatch between what this
ticket says it will demonstrate and what its own chosen isolation (Scope item 3) structurally
permits.**

1. **Finding-4-style clobbering cannot recur** — confirmed with the strongest possible evidence
   (the gating flag means the clobbering phase never executes at all when
   `ENABLE_BELIEF_ASSIMILATION` is OFF). This part of the ticket's own risk framing is resolved
   cleanly and is not a genuine open risk.
2. **The real, non-obvious risk**: as scoped (Scope item 3, `ENABLE_BELIEF_ASSIMILATION` OFF), this
   pilot cannot produce "Branch B fires" evidence in the sense the BRANCH-B ticket's own test name and
   the epic investigation's Finding 4 use that term (query-routing, `intent_results`,
   `last_routed_query_subject`) — only Step 1 (self-model knowledge assimilation) is exercised. The
   INFORMATION pillar will not move. **This is not a bug, not a regression, and not something
   discovered mid-implementation that needs a follow-up ticket — it is a direct, foreseeable
   consequence of the ticket's own Scope item 3, verifiable by reading `pipeline.py`'s two-line gating
   before writing a single line of new content.** But if the Completion Summary reports "Branch B
   piloted successfully, clean grades" without this distinction, that would overclaim — the pilot
   would have actually validated **Step 1's durability at scale** (a real, valuable, and previously
   entirely untested claim — `INFRA-259`/`SUB-374` have zero multi-entity/multi-tick calibration
   evidence today), not "Branch B" in the query-routing sense.
3. **Recommended honest framing for the Completion Summary / `eval_matrix_results.md` entry** (not a
   scope change — this is how to report Scope item 3's own already-chosen design, not a request to
   revisit it): state explicitly that (a) COGNITION pillar shows genuine, real, non-dormant
   `self_model_active` signal (from `self_model_updated`, firing every tick for every entity) — this
   is new, valuable, and directly validates `INFRA-259`/`SUB-374` at scale for the first time; (b)
   INFORMATION pillar is expected to show **zero incremental signal** from this pilot specifically,
   because Branch B's query-routing lives entirely inside the `ENABLE_BELIEF_ASSIMILATION`-gated
   `InformationBeliefPhase`, which this pilot deliberately never invokes; (c) the query-routing sense
   of "Branch B" remains proven **only** by the existing single-entity unit test
   (`test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`) — this
   pilot does not, and by its own Scope item 3 cannot, extend that proof to multi-entity/multi-tick
   scale. If multi-entity Branch-B-routing evidence is wanted, that is necessarily a **different,
   not-yet-scoped pilot** that turns `ENABLE_BELIEF_ASSIMILATION` ON too — exactly the combination
   Scope item 3 (correctly, for isolation purposes) excludes, and exactly the interaction
   investigation.md §3 flagged as higher-trust-required. This is a genuine tension in the ticket's own
   framing, not resolved by anything already written, and is stated here as the one open point.
4. **Everything else checked out clean and boring, as the ticket hoped**: no reversion of any of the 3
   BRANCH-B fixes; the addressing mechanism is exactly the established `pop_N` pattern; the trigger
   chain is fully deterministic and already proven by a passing test; canonical-hash participation
   (`SUB-374`) means this world's committed hash baseline will change once real (non-empty)
   `self_model` content exists under `ENABLE_SELF_MODEL_COGNITION: "ON"` — expected baseline churn for
   this one new world only, not a correctness risk, and worth one explicit line in
   `docs/parity_ledger/strategic_cognition.yaml` (a short cross-reference to `SUB-374`, since
   `SUB-374` itself already documents the general mechanism and does not need a duplicate entry) rather
   than a new parity-ledger entry from scratch.

## Open questions requiring a human decision

1. **Does "Branch B confirmed reachable... with live multi-tick evidence" (this ticket's own Title/AC
   framing) mean Step 1 alone (as Scope item 3 scopes it) or the full query-routing sequence (which
   structurally requires `ENABLE_BELIEF_ASSIMILATION` ON)?** This investigation cannot resolve this —
   it is a genuine tension between the ticket's stated goal and its own chosen isolation constraint,
   not an implementation detail. Recommendation: proceed with Scope item 3 as written (isolate the
   single mechanic, matching the sibling FACTION/INFORMATION tickets' philosophy) and report the
   COGNITION-only signal honestly per §7 point 3, rather than reinterpreting Scope item 3 to add
   `ENABLE_BELIEF_ASSIMILATION` — but this is a judgment call the ticket owner should confirm before
   the calibration run is treated as "the" Branch-B-at-scale evidence, since it demonstrably is not
   that, by the ticket's own design.

No other open question in this investigation requires a human decision — the 3 fixes, addressing
mechanism, trigger chain, and pillar mapping are all resolved with direct evidence above.

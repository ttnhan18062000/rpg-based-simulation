---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE
artifact_type: plan
tags: [simulation-quality, cognition, information, self-model]
---

# Implementation Plan — TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE

## Summary

This plan wires `ActionIntentAdapter.execute()` into the production tick pipeline as a new,
flag-gated sub-phase (`information_intent_execution`) that consumes the `ActionIntent` objects
`InformationBeliefPhase` Branch B already routes into `EntityUpdate.intent_results` each tick. The
approach is a narrow, additive call-site: register a new `ENABLE_INFORMATION_INTENT_EXECUTION`
flag (defaulting OFF), implement a small standalone phase module that filters
`intent_results` by `isinstance(x, ActionIntent)`, iterates entities in sorted-ID order, calls
`ActionIntentAdapter.execute()` per routed intent, and merges each returned
`Dict[int, EntityUpdate]` back into the tick's update set using the exact
`existing_upd.merge(action_upd)` pattern `ActionRoutingPhase.route()` already uses
(`src/engine/pipeline_phases/actions.py:197-202`). The phase is inserted between
`information_belief` and `cooperation` in `src/engine/pipeline.py`, registered (cosmetically) in
`PhaseDependencyGraph.PHASES`, and verified via 6 new tests plus a new non-shipped probe profile
mirroring `urban_political_selfmodel_probe.yaml`. `INFRA-267`'s parity ledger claim ("no production
call site") is superseded by a new successor entry, following the `INFRA-266`→`INFRA-267`
succession precedent already established in this lineage (historical entries are not rewritten in
place). No mechanics law, `ActionIntentAdapter.execute()` internals, or `InformationBeliefPhase`
routing logic changes — this is exclusively a new call site plus its gating and verification.

## Steps

### Step 1 — Register the new feature flag
**Files:** `src/domains/optimization/feature_flags.py`
**Change:** Add `"ENABLE_INFORMATION_INTENT_EXECUTION": FeatureMode.OFF,` to the `_flags` dict in
`FeatureFlagManager.__init__` (lines 13-24), alongside the other 10 entries (e.g. immediately after
`"ENABLE_BELIEF_ASSIMILATION"` for readability, since it is the phase this one causally follows).
No other method in this file needs to change — `get_flag_mode`, `set_flag_mode`, `is_enabled`,
`is_shadow`, `serialize` are all keyed generically off `self._flags`.
**Do NOT touch:** Any other flag's default value or the class's public method signatures.
**Verify:** New Test 6 (Step 7) — `test_new_flag_registered_in_feature_flag_manager`. Also confirm
`test_all_enhancement_flags_default_to_off_or_shadow`
(`tests/unit/config/test_phase10_feature_flags.py:5-10`) still passes unmodified (it iterates
`get_all_flags()` generically, so the new flag is covered automatically once it defaults to OFF).

### Step 2 — Implement the new phase module
**Files:** `src/engine/pipeline_phases/information_intent_execution.py` (new file)
**Change:** Create `InformationIntentExecutionPhase` with a single `@staticmethod execute(state,
update) -> StateUpdate`, mirroring the structural pattern of
`src/engine/pipeline_phases/paid_information.py` (module docstring, `TYPE_CHECKING` imports,
returns `update` unchanged if nothing changed) combined with `ActionRoutingPhase.route()`'s merge
mechanics (`actions.py:197-202`). Exact logic:
1. `refined_entity_updates = dict(update.entity_updates)`.
2. Iterate `for eid in sorted(update.entity_updates.keys())` — **sorted order is required for
   determinism**, matching `docs/engine/kernel.md` line 19 and `ActionRoutingPhase.route()`'s own
   `sorted(actors_with_tasks)` convention (`actions.py:108`). Do not iterate the raw dict.
3. For each `eid`, read `ent_upd = update.entity_updates[eid]`; skip if `not ent_upd.intent_results`.
4. Resolve `entity = state.entities.get(eid)`; skip if `None`.
5. For each `candidate in ent_upd.intent_results`: skip unless
   `isinstance(candidate, ActionIntent)` (import `ActionIntent` from
   `src.engine.intent.action_intent`) — this is the mandatory filter guarding against
   `economy.py`/`patches.py`-populated real `IntentResult` entries in the same field (see Anti-Drift
   Hazards / Scope Guards below).
6. For each surviving `ActionIntent`, call
   `ActionIntentAdapter.execute(entity=entity, intent=candidate, current_tick=state.tick,
   neighbor_view=None, context=state)`. **`execute()` returns `Dict[int, EntityUpdate]`, not a
   single `EntityUpdate`** (confirmed: `action_intent.py:49-56` signature, and both the
   `ASK_INFORMATION` legacy-adventure branch at line 142-145 and the information-domain branch at
   line 178-183 return `{entity.id: EntityUpdate(...)}`). Iterate that dict:
   `for action_eid, action_upd in adapter_updates.items(): existing_upd =
   refined_entity_updates.get(action_eid, EntityUpdate(entity_id=action_eid));
   refined_entity_updates[action_eid] = existing_upd.merge(action_upd)`. This is the exact pattern
   at `actions.py:197-202` — do not simplify to a single-entity merge, since a future intent kind
   Branch B routes could touch a second entity (current kinds, `MOVE_TO`/`ASK_INFORMATION`, only
   ever touch the actor, but the merge code must not assume that).
7. Do not build a `sliding_state`/`working_entities` proxy — per investigation.md's Risks section,
   neither `MOVE_TO` nor `ASK_INFORMATION`'s `Requirement` list depends on `context`, so passing
   `state` directly (as `InformationBeliefPhase` itself does) is sufficient and avoids unnecessary
   complexity.
8. Return `update` unchanged if `refined_entity_updates == dict(update.entity_updates)`, else
   `replace(update, entity_updates=refined_entity_updates)`.
**Do NOT touch:** `ActionIntentAdapter.execute()`'s internals (dispatch table, requirement gating,
`ASK_INFORMATION` branching) — call it, do not modify it. Do not touch
`InformationBeliefPhase.apply()` or its Branch B routing logic.
**Verify:** New Tests 3 and 4 (Step 3).

### Step 3 — Unit tests for the new phase (filter + determinism)
**Files:** `tests/unit/engine/test_information_intent_execution_phase.py` (new file, flat in
`tests/unit/engine/` alongside `test_capability_registry.py` etc. — no `pipeline_phases/`
subdirectory exists yet under `tests/unit/engine/` and creating one for a single file adds
unneeded structure)
**Change:** Add two tests per test_plan.md New Tests 3 and 4:
- `test_action_intent_execution_phase_filters_non_action_intent_entries` — construct a minimal
  `StateUpdate`/`EntityUpdate` where `intent_results` contains a real `IntentResult`
  (`src/core/state.py:655`, e.g. `IntentResult(transaction_id=..., accepted=True, reason=...,
  source_kind=..., source_id=...)`) and no `ActionIntent`. Call
  `InformationIntentExecutionPhase.execute(state, update)`. Call
  `ActionIntentAdapter.clear_traces()` before, `ActionIntentAdapter.get_traces()` after — assert it
  is empty (i.e. `.execute()` on the adapter was never invoked for that entity). Also test the mixed
  case (one `IntentResult` + one real `ActionIntent` in the same list) to confirm only the
  `ActionIntent` triggers execution.
- `test_action_intent_execution_phase_preserves_deterministic_entity_order` — construct a
  `StateUpdate` with 3+ entities (non-sequential IDs, e.g. 30, 5, 17) each carrying a routed
  `ActionIntent` (use `kind="MOVE_TO"` with a trivial/no-op-safe payload, or `kind="ASK_INFORMATION"`
  without `"query_kind"` to hit the cheap legacy branch) in `intent_results`. Clear traces, run the
  phase, assert `ActionIntentAdapter.get_traces()`'s `actor_id` sequence is `[5, 17, 30]` (sorted),
  not insertion/dict order.
**Do NOT touch:** `tests/unit/strategic/test_intents.py` (existing direct `.execute()` unit tests —
must stay untouched, this ticket does not modify that file).
**Verify:** `pytest tests/unit/engine/test_information_intent_execution_phase.py -q`.

### Step 4 — Wire the phase into `pipeline.py`
**Files:** `src/engine/pipeline.py`
**Change:** Insert a new `run_phase(...)` block between the end of the `information_belief` block
(after line 153, `costs["information_belief"] = ...`) and the `cooperation` block's comment (line
155), exactly at the merge point the investigation confirmed:
```python
        # --- Enhanced RPG Phase 6: Information Intent Execution (self-model query-routing) ---
        t_start = time.perf_counter_ns()
        from src.engine.pipeline_phases.information_intent_execution import InformationIntentExecutionPhase
        update = run_phase(
            "information_intent_execution", update,
            lambda u: InformationIntentExecutionPhase.execute(state, u),
            "ENABLE_INFORMATION_INTENT_EXECUTION",
        )
        costs["information_intent_execution"] = (time.perf_counter_ns() - t_start) / 1e6
```
This must run strictly after `information_belief` (so `intent_results` is populated this tick) and
before `cooperation` (no ordering dependency there, but this is the confirmed merge point).
**Do NOT touch:** The `information_belief` block (lines 146-153) or `cooperation` block (lines
156-159) themselves — insert between them, do not modify their bodies. Do not reorder any other
phase in `refine()`.
**Verify:** New Tests 1 and 2 (Step 6) — these are the only tests that exercise this wiring through
the real `AuthoritativeApplyPipeline.refine()` call path.

### Step 4a — Doc parity: `authoritative_pipeline.md`, `feature_flags.md`, and (conditionally) `known_limitations.md`
**Files:** `docs/engine/authoritative_pipeline.md`, `docs/guides/feature_flags.md`, and
`docs/engine/known_limitations.md` if sub-step 2's grep finds a stale count there (confirmed present
as of this writing — §1.5 "Feature Flag Defaults (Phase 10 Rollout Gates)" independently asserts
"All 10 Phase 10 feature flags... default to `FeatureMode.OFF`" and lists all 10 by name — treat
this as a third file requiring the same edit, not merely a possibility to check).
**Why:** Flagged by architecture review (NEEDS_CHANGES) — both docs are active/P1 and make
explicit, now-false factual claims once Steps 1 and 4 land. Per CLAUDE.md's Authoritative Mechanics
Rule, doc/code parity must be fixed in the same session, not deferred.
**Change:**
1. `docs/engine/authoritative_pipeline.md` — this doc's phase table states "Phase names match the
   `run_phase()` call identifiers in `src/engine/pipeline.py:refine()`" and enumerates phases by
   exact name under heading `## The 31 Phases of Refinement` (confirmed: exactly 31 numbered rows,
   `information_belief` is row #4, `cooperation` is row #5, back-to-back with no gap). Insert a new
   row for `information_intent_execution` between them (same columns as existing rows: phase name /
   flag / brief description, matching the existing row format exactly), assign it #5, and
   **renumber every subsequent row** (old #5 `cooperation` through old #31, the final row) up by one
   (new #6 through #32) — the `#` column is a strict sequential index; leaving a duplicate or
   skipped number is itself a doc-parity break, not merely leaving the heading stale. Update the
   heading to `## The 32 Phases of Refinement`.
2. `docs/guides/feature_flags.md` — this doc states "`FeatureFlagManager.__init__` hardcodes exactly
   10 flags. All 10 default to `FeatureMode.OFF`" and lists all 10 by name in a "## The 10 flags"
   table. Add `ENABLE_INFORMATION_INTENT_EXECUTION` as an 11th row (same columns as the existing
   rows), and correct every "10" reference in this doc (heading text, prose count, anywhere else the
   number appears) to 11. Also grep `docs/engine/known_limitations.md` §1.5-adjacent content for any
   independent "10 flags" assertion — if found, update it too in this same step (do not leave a
   second stale copy of the same count elsewhere).
**Do NOT touch:** Any other row/section in either doc, or any other doc's independent flag/phase
count unless the grep in sub-step 2 finds one.
**Verify:** Manual read-through confirming the new rows match sibling rows' format exactly, and no
"10 flags"/"31 phases" (or whatever the confirmed original count was) string survives uncorrected in
either file. No dedicated test enforces this doc's prose — this is a documentation-accuracy step, not
a test-covered one.

### Step 5 — Register the phase in `PhaseDependencyGraph.PHASES`
**Files:** `src/engine/phase_graph.py`
**Change:** Add one entry to the `PHASES` dict (lines 36-69), alongside the other Phase 2-8
Enhanced RPG entries (after `"information_belief"` at line 63, before `"cooperation"` at line 64):
```python
        "information_intent_execution": PhaseMetadata("information_intent_execution", {"strategic"}, {"strategic", "inventory"}),
```
This is cosmetic/documentation-only per the investigation's confirmed trace: `update.dirty_set is
None` for the entire early pipeline section (first set at line 257, well after this phase runs), so
`should_run_phase` always returns `True` here regardless of `input_domains`/`output_domains` — do
not rely on this registration for correctness, only for consistency with sibling phases
`information_belief`/`cooperation`.
**Do NOT touch:** Any other `PHASES` entry, `should_run_phase()`'s logic itself, or add a new
`TickPhase` (confirmed not required — this is a `RESOLUTION`-internal sub-phase, per
`docs/engine/kernel.md` §"Phase Domain Permissions").
**Verify:** `pytest tests/architecture/test_phase_domain_permissions.py -q` (confirms no `TickPhase`
permission drift was introduced).

### Step 6 — Integration tests proving the phase fires through the real pipeline
**Files:** `tests/integration/domains/information/test_phase5_information_belief_phase.py`
(existing file — add alongside `test_ask_information_intent_execution_closes_the_loop`, reusing its
`UnknownFact`/`InformationSourceProfile` setup pattern, per test_plan.md's stated preference to keep
the file cohesive)
**Change:** Add two tests per test_plan.md New Tests 1 and 2:
- `test_action_intent_execution_phase_fires_in_real_tick_pipeline` — construct a real
  `AuthoritativeState` with an entity carrying an unresolved `self_model.knowledge.unknowns` entry
  and a reachable `InformationSourceProfile`; set `state.feature_flags` (or equivalent) with
  `ENABLE_SELF_MODEL_COGNITION`, `ENABLE_BELIEF_ASSIMILATION`, and
  `ENABLE_INFORMATION_INTENT_EXECUTION` all `"ON"`. Call
  `AuthoritativeApplyPipeline.refine(state, StateUpdate())` end-to-end (not direct
  `ActionIntentAdapter.execute()` invocation). Assert the returned `StateUpdate`'s entity update for
  the actor carries `self_model_bundle_set` with the unknown resolved into `facts` — this is the
  `.execute()` postcondition and proves the call fired through the pipeline.
- `test_action_intent_execution_phase_off_by_default_is_a_noop` — identical setup, but leave
  `ENABLE_INFORMATION_INTENT_EXECUTION` unset/default (`OFF`), with
  `ENABLE_SELF_MODEL_COGNITION`/`ENABLE_BELIEF_ASSIMILATION` still `ON` so Branch B still routes an
  `ActionIntent` into `intent_results`. Assert `self_model_bundle_set` is **not** populated on the
  resulting update — the routed intent sits inert in `intent_results`, proving the flag gate
  actually blocks production reachability (this is the direct unit/integration-level verification of
  Acceptance Criterion 4, ahead of the corpus-level `evaluate_simq.py --dry-run` check in Step 11).
**Do NOT touch:** `test_ask_information_intent_execution_closes_the_loop` itself (must remain
byte-identical/unmodified per Acceptance Criteria) or
`test_information_belief_phase_falls_back_to_next_candidate_on_resolution_failure`.
**Verify:** `pytest tests/integration/domains/information/test_phase5_information_belief_phase.py -q`.

### Step 7 — Flag-registration regression test
**Files:** `tests/unit/config/test_phase10_feature_flags.py` (existing file)
**Change:** Add `test_new_flag_registered_in_feature_flag_manager`
(test_plan.md New Test 6): instantiate `FeatureFlagManager()`, assert
`"ENABLE_INFORMATION_INTENT_EXECUTION" in manager.get_all_flags()` and
`manager.get_flag_mode("ENABLE_INFORMATION_INTENT_EXECUTION") == FeatureMode.OFF`. This directly
guards the single most likely silent-failure mode identified in investigation.md (unregistered flag
→ permanent silent no-op).
**Do NOT touch:** The 5 existing tests in this file.
**Verify:** `pytest tests/unit/config/test_phase10_feature_flags.py -q`.

### Step 8 — Extend the shipped-profile guardrail
**Files:** `tests/integration/test_world_profile_feature_flag_guardrail.py`
**Change:** Add `"ENABLE_INFORMATION_INTENT_EXECUTION"` as a fourth entry to the `_GATED_FLAGS`
tuple (line 33): `_GATED_FLAGS = ("ENABLE_ADVENTURE_ROUTING", "ENABLE_BELIEF_ASSIMILATION",
"ENABLE_SELF_MODEL_COGNITION", "ENABLE_INFORMATION_INTENT_EXECUTION")`. **Decision (resolving the
investigation's flagged open question): yes, extend it.** This is the one existing mechanism that
would catch a future accidental shipped-profile activation of the new flag, and the ticket's
Out-of-Scope line explicitly forbids that activation — wiring the guardrail is in-scope hygiene for
a ticket that adds a new gated flag, not scope creep.
**Do NOT touch:** `tests/simulation_quality/fixtures/expected_world_flag_state.json` — this fixture
should need no changes, since no shipped world profile will set the new flag; if the test fails
after this edit, that means a shipped profile unexpectedly has the flag set (a real bug to
investigate, not a fixture to silently update).
**Verify:** `pytest tests/integration/test_world_profile_feature_flag_guardrail.py -q`.

### Step 9 — New probe profile + calibration grade-anchor test
**Files:** `config/simulation_quality/profiles/urban_political_selfmodel_execution_probe.yaml` (new
file), `tests/simulation_quality/test_grade_regression.py` (new test function),
`tests/simulation_quality/fixtures/grade_anchors.json` (new key)
**Change:**
1. Create the new probe profile, mirroring `urban_political_selfmodel_probe.yaml`'s structure and
   header-comment convention but as a **separate, new file** (do not repurpose the existing one —
   see Scope Guards). Base it on `urban_political.yaml`'s shipped profile with
   `ENABLE_SELF_MODEL_COGNITION: "ON"`, `ENABLE_BELIEF_ASSIMILATION: "ON"`, and
   `ENABLE_INFORMATION_INTENT_EXECUTION: "ON"` all set in its `feature_flags:` block. Header comment
   must state this is a non-shipped, permanent grade-anchor probe (not referenced by any world's
   default calibration chain), analogous to the existing probe.
2. Add `test_urban_political_selfmodel_execution_isolated_grade_anchor` to
   `tests/simulation_quality/test_grade_regression.py`, structurally mirroring
   `test_urban_political_selfmodel_cognition_isolated_grade_anchor` (same file, lines 334-378): run
   a real calibration (`tools/calibrate_simq.py`) against the new probe profile, assert
   COGNITION/INFORMATION pillar grades against a new `grade_anchors.json` key (e.g.
   `urban_political_selfmodel_execution_probe_seed42_200t`), and add a direct assertion that at
   least one `ActionIntentAdapter`-attributable signal fired — use
   `ActionIntentAdapter.get_traces()` if the calibration harness runs in-process and exposes it,
   otherwise assert on a resulting non-empty `self_model_bundle_set`/`facts` delta in the run's
   output that could only be true if `.execute()` actually ran through `Kernel.tick_once()`. Include
   the same `pytest.skip()` fallback pattern as the existing anchor test if the calibration report or
   anchor key is absent.
3. Generate the new `grade_anchors.json` entry by **running the real calibration** (`tools/
   calibrate_simq.py` against the new probe, seed 42, 200 ticks) and copying its actual output —
   never hand-author the entry. Use the `{grade, score}` per-pillar schema
   `TCK-20260713-SIMQ-RAWSCORE-PERSIST` (same epic batch, done) introduced, with `score` populated
   from `normalized_score` — a bare grade string or a stale-schema entry will fail that ticket's
   independent score-tolerance assertion (`abs_delta <= max(0.05, 0.20 * |anchored_score|)`)
   regardless of whether the letter grade is correct.
**Do NOT touch:** `urban_political_selfmodel_probe.yaml` (the existing probe file) — do not add
`ENABLE_BELIEF_ASSIMILATION` or the new flag to it, and do not change its `feature_flags:` block in
any way. Do not touch `test_urban_political_selfmodel_cognition_isolated_grade_anchor` or its
existing `grade_anchors.json` key. Do not touch any *shipped* profile
(`config/simulation_quality/profiles/urban_political.yaml`, or any `data/worlds/*/world.yaml`
calibration chain).
**Verify:** `pytest tests/simulation_quality/test_grade_regression.py -k "urban_political" -q`; the
existing `test_urban_political_selfmodel_cognition_isolated_grade_anchor` must still pass with its
hardcoded `pillars["INFORMATION"]["event_count"] == 0` assertion unchanged.

### Step 10 — Update the parity ledger
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** `INFRA-267`'s `support_boundary` text currently states *"ActionIntentAdapter.execute()
has no production tick-pipeline call site today (unchanged by this ticket)..."* — this claim is now
false. **Decision (resolving the investigation's flagged either/or): add a new successor entry**
rather than editing `INFRA-267`'s text in place, following the `INFRA-266`→`INFRA-267` succession
precedent already established in this exact lineage (investigation.md confirms `INFRA-266` was left
untouched/historical when `INFRA-267` superseded it — entries in this lineage are not rewritten
retroactively; each ticket's ledger entry is a historically accurate snapshot of what that ticket
verified). Before adding, `grep -oP '^- id: INFRA-\K[0-9]+' docs/parity_ledger/infrastructure.yaml
| sort -n | tail -1` to confirm the next free ID (269 is taken as of this writing by an unrelated
entry — `INFRA-269`; use whatever is actually free at implementation time, do not hardcode a number
that may have been claimed by a same-batch sibling ticket). New entry: `status: verified`,
`priority: P1`, `text` describing that `ActionIntentAdapter.execute()` now has a production call
site (`InformationIntentExecutionPhase`, `src/engine/pipeline_phases/information_intent_execution.py`,
wired into `AuthoritativeApplyPipeline.refine()` gated by `ENABLE_INFORMATION_INTENT_EXECUTION`,
default OFF), `v2_evidence` citing `src/engine/pipeline.py`'s new `run_phase(...)` call and
`information_intent_execution.py`, `test_path` citing the new Step 6 integration tests plus Step 9's
calibration anchor test, `support_boundary` explicitly noting the flag remains OFF in every shipped
profile (Out of Scope) and citing Step 8's guardrail extension as the enforcement mechanism.
**Do NOT touch:** `INFRA-266` (left untouched per existing precedent) or `INFRA-267`'s own
`text`/`v2_evidence`/`test_path` fields — those remain an accurate historical record of what
`TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE` verified at the time. No entry in
`docs/parity_ledger/strategic_cognition.yaml` needs a change (confirmed by investigation.md — no
existing entries reference this subsystem by name).
**Verify:** Manual review only (no automated parity-ledger schema test is named in test_plan.md for
this file); confirm the new entry validates against `docs/parity_ledger/schema.json`'s required
fields if a lint step is run as part of Finalize.

### Step 11 — Full regression verification sweep
**Files:** none (verification only, no code changes)
**Change:** Run, in order, the full scoped command set from test_plan.md's "Scoped Pytest Commands"
section:
```bash
pytest tests/unit/cognition/ tests/unit/domains/information/ tests/integration/domains/information/ \
  tests/unit/strategic/test_intents.py tests/unit/observability/test_event_extractor_information2.py -q
pytest tests/unit/domains/adventure/ tests/unit/strategic/test_classifier.py -q
pytest tests/integration/domains/test_fused_loop.py -q
pytest tests/integration/test_world_profile_feature_flag_guardrail.py -q
pytest tests/perf/test_phase5_information_belief_budget.py -q
pytest tests/unit/engine/test_information_intent_execution_phase.py -q
pytest tests/simulation_quality/test_grade_regression.py -k "urban_political" -q
pytest tests/architecture/test_phase_domain_permissions.py -q
python3 tools/evaluate_simq.py --dry-run
```
Confirm: (a) every existing test in the regression surface passes unmodified; (b)
`test_ask_information_intent_execution_closes_the_loop` specifically passes unchanged; (c) the
`evaluate_simq.py --dry-run` sweep shows 0 regressions with the new flag left at its default OFF
state. **If the dry-run sweep flags a COGNITION-pillar delta:** cross-check it against the known,
pre-existing, environment-load-sensitive self-model loop-detection nondeterminism recorded by
`TCK-20260713-SIMQ-SCORE-CEILING-FIX` (filed separately as
`TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`, open, out of scope) before treating it as a
regression this ticket caused. Do not silently ignore any COGNITION delta, and do not assume every
COGNITION delta is this ticket's fault — reproduce 2-3 times to see if it matches that ticket's
documented flaky signature; if it does not reproduce-flake and correlates with the new phase, it is
a real regression to fix before closing this ticket.
**Do NOT touch:** Do not run the unscoped `pytest tests/`.
**Verify:** All commands above exit 0 / report 0 regressions.

### Step 12 — Update ticket documentation
**Files:** `tickets/inprogress/TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE.md`
**Change:** Fill in `## Implementation Notes` (summarize the phase/flag/merge approach and the
INFRA-267 successor-entry decision), `## Test Summary` (list the 6 new tests and the full regression
command set run in Step 11, with pass/fail outcome), `## Files Changed` (enumerate every file
touched across Steps 1-10, including Step 4a's doc edits — up to three files: `authoritative_pipeline.md`,
`feature_flags.md`, and `known_limitations.md` if its stale count was present and corrected), and
`## Completion Summary` (confirm
all 4 Acceptance Criteria are met, and explicitly restate that the new flag was not turned on in any
shipped profile). This step is documentation only — no source or test changes.
**Do NOT touch:** `## Scope`, `## Out of Scope`, `## Acceptance Criteria` (these are the ticket's
original contract, not to be edited retroactively).
**Verify:** N/A (documentation step); reviewed as part of the Definition of Done checklist at ticket
close.

## Scope Guards

- Do not modify `ActionIntentAdapter.execute()`'s internals (requirement gating, dispatch table, the
  `ASK_INFORMATION` branch's `"query_kind"` discrimination) — this ticket only adds a call site.
- Do not modify `InformationBeliefPhase.apply()` or `InformationBeliefPhase`'s Branch A/B routing
  logic in `src/domains/information/phase.py`.
- Do not modify `InformationIntentResolver.resolve()` or `InformationQueryRouter.route()` in
  `src/domains/information/resolver.py`/`router.py`.
- Do not turn `ENABLE_INFORMATION_INTENT_EXECUTION` `ON` in any shipped world profile
  (`data/worlds/*/world.yaml`'s default calibration chain) or any shipped
  `config/simulation_quality/profiles/*.yaml` — it must only ever be `ON` in the new, dedicated,
  non-shipped probe profile and in test fixtures.
- Do not mutate `urban_political_selfmodel_probe.yaml` in any way — its existing anchor test
  (`test_urban_political_selfmodel_cognition_isolated_grade_anchor`) depends on its exact current
  contents (`ENABLE_SELF_MODEL_COGNITION` ON, `ENABLE_BELIEF_ASSIMILATION` absent/OFF).
- Do not change `EntityUpdate.intent_results`'s declared type (`List[IntentResult]`,
  `src/core/updates.py:638`) or "fix" the pre-existing type mismatch where Branch B stores a raw
  `ActionIntent` there — that is explicitly out of scope, a separate unscoped cleanup.
- Do not reorder any other phase in `AuthoritativeApplyPipeline.refine()` beyond inserting the one
  new block between `information_belief` and `cooperation`.
- Do not add a new `TickPhase` or modify `src/engine/phase_domain_permissions.py`.
- Do not edit `INFRA-266` or rewrite `INFRA-267`'s existing text/evidence/test_path fields.
- Do not touch `tests/simulation_quality/fixtures/expected_world_flag_state.json`.
- Do not fix or attempt to fix the known COGNITION self-model loop-detection nondeterminism
  (`TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`) — cross-check against it, do not resolve it.
- Never run the unscoped `pytest tests/`.

## Dependency Map

- Step 1 (flag registration) has no dependencies. Blocks Step 4 (pipeline needs the flag name to
  gate on), Step 6/9 (need the flag to turn ON in tests/probe), Step 7, Step 8.
- Step 2 (phase module) has no dependencies. Blocks Step 3 (unit tests need the module to exist) and
  Step 4 (pipeline wiring calls into this module).
- Step 3 (unit tests) depends on Step 2 only.
- Step 4 (pipeline wiring) depends on Steps 1 and 2.
- Step 4a (doc parity) depends on Steps 1 and 4 (needs the final flag name and phase name/position
  to describe accurately) — do the doc edits after those land, not speculatively before.
- Step 5 (phase-graph registration) depends on Step 4 only for the phase name string; otherwise
  independent/cosmetic — can be done any time after Step 4 is drafted.
- Step 6 (integration tests) depends on Steps 1, 2, and 4 (needs the full wiring live).
- Step 7 (flag-registration test) depends on Step 1 only.
- Step 8 (guardrail extension) depends on Step 1 only (needs the flag name).
- Step 9 (probe + calibration test) depends on Steps 1, 2, 4, 5 (needs the complete, working phase
  reachable via a real `feature_flags:` block) and on `TCK-20260713-SIMQ-RAWSCORE-PERSIST`'s schema
  (already done/merged, no dependency action needed here).
- Step 10 (parity ledger) depends on Steps 1-9 all being complete and verified (it documents the
  finished state).
- Step 11 (regression sweep) depends on all of Steps 1-9 being complete.
- Step 12 (ticket docs) depends on Step 11's outcome (needs pass/fail results to report).

All steps within 1-9 are otherwise independently implementable and testable; the map above lists
only genuine input dependencies, not suggested ordering beyond what correctness requires.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| A new gated phase exists in `pipeline.py` calling `ActionIntentAdapter.execute()`, off by default (flag-gated). | Steps 1, 2, 4, 5 | `test_new_flag_registered_in_feature_flag_manager` (Step 7); `test_action_intent_execution_phase_off_by_default_is_a_noop` (Step 6) |
| A calibration run with the new flag deliberately enabled shows at least one `ActionIntentAdapter.execute()` call firing through the real `Kernel.tick_once()` loop. | Step 9 (probe profile + calibration test); Step 4 (the wiring being calibrated) | `test_urban_political_selfmodel_execution_isolated_grade_anchor` (Step 9) |
| `test_ask_information_intent_execution_closes_the_loop` and the existing Branch A/B regression suite continue to pass unmodified. | No step modifies these files (Scope Guards) | Step 11's regression sweep, specifically `tests/integration/domains/information/`, `tests/unit/domains/information/` |
| 0 regressions on a full `evaluate_simq.py` sweep with the new flag left off (default state). | Steps 1, 4 (flag defaults OFF) | Step 11 — `python3 tools/evaluate_simq.py --dry-run` |

## Anti-Drift Notes

- **Flag registration is the single most likely silent-failure mode.** If Step 1 is skipped or
  mistyped, `set_flag_mode`/`get_flag_mode` silently no-op to `FeatureMode.OFF` forever — the new
  probe profile (Step 9) would then "pass" while actually never exercising the phase at all, giving
  a false-positive AC2. Step 7's test exists specifically to catch this.
- **`execute()` returns `Dict[int, EntityUpdate]`, not a single `EntityUpdate`.** The investigation's
  shorthand ("merge the returned `EntityUpdate`") is a simplification — the actual return type
  requires iterating the dict and merging per-key, exactly as `actions.py:197-202` does. A naive
  single-entity merge implementation would work today (both current intent kinds only ever populate
  the actor's own key) but would silently break if a future intent kind populated a second entity's
  update — Step 2 must implement the dict-iteration form regardless.
- **The `isinstance(x, ActionIntent)` filter is mandatory, not optional.** `intent_results`'s
  declared type is the unrelated `IntentResult` dataclass, and `economy.py`/`patches.py` already
  populate that same field with real `IntentResult` instances for resource-transfer outcomes
  elsewhere in the pipeline. Skipping the filter risks either a crash (attribute access on the wrong
  type) or silent misbehavior the moment any other phase's `intent_results` entries reach this new
  phase in the same tick.
- **Sorted-order iteration is a determinism requirement, not a style preference** — per
  `docs/engine/kernel.md` line 19. Test 4 (Step 3) exists specifically to catch a regression to dict
  insertion-order iteration.
- **`ActionIntentAdapter._traces` is pre-existing, class-level (not tick-scoped) mutable state.** Any
  test relying on `get_traces()` must call `clear_traces()` first — this is not new state introduced
  by this ticket, but tests written against it must account for cross-test pollution if run in the
  same process without clearing.
- **The COGNITION loop-detection nondeterminism is a known, separate, open issue** — do not spend
  implementation time chasing it if Step 11's dry-run sweep flags a COGNITION delta; cross-check
  first (see Step 11), and only escalate if it does not match the known flaky signature.
- **`INFRA-267`'s text must not be silently left stale.** Once Step 4 lands, `INFRA-267`'s claim that
  no production call site exists is false; Step 10's new successor entry is what keeps the parity
  ledger accurate — do not skip Step 10 because "nothing about `.execute()`'s internals changed."
  The support-boundary claim changed, which is exactly what the parity ledger is required to track.

## Unresolved Questions

None. Step 4a resolves the architecture review's two doc-parity findings
(`authoritative_pipeline.md`'s phase table, `feature_flags.md`'s "10 flags" table). Both open
decisions the investigation flagged (extending `_GATED_FLAGS`, and
`PhaseDependencyGraph.PHASES` registration) are resolved above (Steps 8 and 5, both "yes, add it").
The INFRA-267 update mechanism (edit-in-place vs. new successor entry) is resolved in Step 10
(new successor entry, following the existing `INFRA-266`→`INFRA-267` lineage precedent). The exact
new `INFRA-` ID number is intentionally left as "confirm at implementation time via grep" rather than
hardcoded, since same-batch sibling tickets may claim IDs concurrently — this is a mechanical lookup,
not a design ambiguity.

## Deviations (recorded during implementation)

1. **Step 8 — `expected_world_flag_state.json` required a mechanical fixture extension, contrary
   to the plan's "Do NOT touch" note.** The plan assumed `test_flag_state_matches_expected_per_world`
   would either pass unchanged or fail with a semantic mismatch ("a shipped profile unexpectedly
   has the flag set"). Verified directly: the test does `expected = entry["flags"][flag]` (strict
   dict indexing, not `.get(flag, "OFF")`), so extending `_GATED_FLAGS` to a 4th flag the fixture's
   17 existing entries don't carry raises `KeyError` for every world, not a value mismatch. Since no
   shipped profile actually sets `ENABLE_INFORMATION_INTENT_EXECUTION` (confirmed: only the new,
   non-shipped probe profile sets it), added `"ENABLE_INFORMATION_INTENT_EXECUTION": "OFF"` to all
   17 existing `flags` entries — a mechanical schema-completion edit, not a semantic value change,
   so it does not violate the guard's underlying intent (only its literal "no edits at all" wording).
   Confirmed via `git stash` comparison that this is the only behavior change; two pre-existing,
   unrelated failures remain in this file both before and after this ticket's changes (see item 3).

2. **Step 9 — the `urban_political` corpus does not route `InformationBeliefPhase` Branch B within
   the specified 200-tick/seed-42 window**, verified directly via an in-process
   `ActionIntentAdapter.get_traces()` check against the exact new probe profile/world/seed/tick
   combination (0 traces). This matches INFRA-266's pre-existing "does NOT generalize" finding for
   this corpus — INFRA-267's fix makes Branch B's fallback logic *correct*, not *guaranteed to
   fire* in every corpus. Consequence: the calibration-based grade-anchor test alone cannot serve
   as Acceptance Criterion 2's proof for this specific probe/corpus. Added a second, separate test,
   `test_information_intent_execution_fires_through_kernel_tick_once`
   (`tests/simulation_quality/test_grade_regression.py`), using a minimal hand-built scenario
   (guaranteed-reachable unknown + free information source) driven through a real `Kernel.tick_once()`
   call, asserting via `ActionIntentAdapter.get_traces()`. This is the plan's own first-choice
   fallback option ("use `ActionIntentAdapter.get_traces()` if the calibration harness runs
   in-process and exposes it") — `tools.calibrate_simq` is confirmed importable/callable in-process
   (existing precedent: `tests/simulation_quality/test_calibrate_world_loading.py`). The grade-anchor
   test (`test_urban_political_selfmodel_execution_isolated_grade_anchor`) is retained as specified,
   documented as proving "the phase does not regress calibration output when wired in and gated ON,"
   not as the AC2 firing-proof.

3. **Two additional pre-existing anti-drift assertions needed mechanical updates as a direct,
   expected consequence of adding one new `grade_anchors.json` entry** (not separately called out
   in the plan, but implied by Step 9.3's "Generate ... never hand-author"): `grade_anchors.json`
   now has 76 real scenario entries instead of 75, so
   `test_grade_anchors_entry_count_unchanged`'s hardcoded `== 75` was updated to `== 76` (and its
   docstring). Confirmed via `git stash` comparison that `test_grade_anchor_file_exists_and_valid`'s
   failure (missing local `data/calibration/hero_guild_routing_seed42_1000t/quality_report.json`)
   and `test_world_profile_feature_flag_guardrail.py`'s two failures (missing
   `unit_information_density` fixture entry) are pre-existing environment/corpus gaps unrelated to
   this ticket — present identically before and after this ticket's changes — and were left
   untouched, out of scope.

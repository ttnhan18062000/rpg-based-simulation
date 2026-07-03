# Plan — TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER

## Correction to Steps 5-9 (read this first)

Architecture review found that Steps 5-9 as originally drafted made a factually wrong claim: that
the seeded `pending_information_responses` entry for `pop_0` "re-assimilates every tick... for the
entire run" because `InformationBeliefPhase.apply()` never clears/consumes the list. A source-level
trace shows this is wrong:

- `src/engine/kernel.py:702-722` (`Kernel._phase_advancement()`, called once per tick in the real
  tick loop) calls `ApplyPath.apply_generation()` (`src/engine/apply.py:179-416`) every tick to
  rebuild `AuthoritativeState` from `prior_state`.
- The final `AuthoritativeState(...)` constructor call inside `apply_generation()`
  (`apply.py:356-408`) does **not** pass `pending_information_responses=` or
  `information_source_profiles=` from `prior_state` — grep confirms zero references to either field
  anywhere in `apply.py`. Both fields default via `field(default_factory=list, ...)` on
  `AuthoritativeState`, so they silently reset to `[]` on the very first tick advancement after any
  refine.
- Net effect: the compiled seed is visible to `InformationBeliefPhase.apply()` for exactly **one**
  `refine()` call — the initial compiled state at tick 0 (the state `tools/calibrate_simq.py:228-233`
  injects directly into `Kernel` before looping `tick_once()`, the real path Step 10 exercises). From
  tick 1 onward `state.pending_information_responses` is permanently `[]`. The seed fires **once**,
  then stops — it does not re-fire every tick forever.

This does not change Steps 1-4 (schema/compiler/resolver/content are unaffected — the compiled seed
is still correctly constructed exactly once). It changes what Steps 5-9 test/document/expect:
single-fire, not repeat-fire. See the corrected Steps 6, 9 below (renumbered from the original Steps
6-9 after the 2026-07-03 scope expansion inserted the kernel tick-alignment fix as Steps 7-8; the
recalibration/docs steps are now Steps 10-11), and the side note after Step 11 about the same trait
applying to the parent ticket's already-shipped `information_source_profiles` scaffolding
(informational only, out of scope here).

---

## Why this path, not the idea doc's two options

The idea doc (`docs/plans/idea_information_belief_trigger_wiring.md`) offered two options: wire
Branch B by fixing `SelfModelUpdatePhase.apply()`'s hardcoded `events=[]` (Option 1), or wire the
`paid_information_transaction` path via `InformationNeedDetector` + `state.information_providers`
seeding (Option 2). This ticket's investigation (`staging_artifacts/.../investigation.md`) traced
both to the bottom and found neither is self-contained:

- **Option 1** requires (a) a new `InformationResponse` producer wired into the tick (none exists
  reachably — `GuideInformationProvider.query()` is itself orphaned, a third dead entry point
  discovered by this ticket), (b) new cross-phase/per-tick event-collection infrastructure in
  `StateUpdate`/`EntityUpdate` (none exists today), and (c) new logic inside `ASK_INFORMATION`
  intent execution to actually call a provider and produce a response. Even if built, Branch B
  never sets `last_assimilated_tick`, so it still could not satisfy the AC's `belief_assimilated`
  requirement. This is squarely the "new, riskier engine work" class the ticket's own framing
  warns against, and is scope-equivalent to the explicitly out-of-scope "full information
  marketplace / NPC query-response loop."
- **Option 2** shares Option 1's exact root blocker (`InformationNeedDetector.detect_and_generate()`
  itself reads the same dead `self_model.knowledge.unknowns` state) and adds its own shared-code
  wiring surface (`CognitionDomain.execute_brain()`, run for every world) plus a second durable-state
  seed (`state.information_providers`, distinct from `information_source_profiles` — do not conflate).

The investigation instead found a **third path, not named in the idea doc**: seed
`state.pending_information_responses` at compile time (Branch A of `InformationBeliefPhase.apply()`,
`src/domains/information/phase.py:53-81`). Branch A's own logic — normalization
(`InformationResponseNormalizer.normalize()`) and assimilation
(`InformationAssimilationService.assimilate()`) — is already fully implemented, unit-tested, and
proven end-to-end through the real `AuthoritativeApplyPipeline.refine()` pipeline by
`tests/integration/domains/test_fused_loop.py:186-200`. The only reason it never fires in any
calibration world is that **no compiler ever constructs
`AuthoritativeState.pending_information_responses`** — the exact same "compiler never constructs
the field" bug class the parent ticket (`TCK-20260702-SIMQ-UPLIFT2-INFORMATION`) already fixed for
`information_source_profiles`. This plan reuses that exact schema→compiler→resolver plumbing
pattern a third time (after FACTION and parent INFORMATION), confined entirely to
`src/worldbuilding/`, `src/worldassembly/`, and `urban_political` world content. It requires **zero**
changes to `SelfModelUpdatePhase`, `InformationNeedDetector`, `CognitionDomain.execute_brain()`, or
`ENABLE_SELF_MODEL_COGNITION` (which stays OFF everywhere, unchanged) — the smallest blast radius of
the three paths, and the only one confined to worldbuilding/worldassembly compiler code.

**Parity ledger next-free ID confirmed by re-reading `docs/parity_ledger/infrastructure.yaml`:**
all `INFRA-nnn` ids present were enumerated (228 through 256, non-monotonic file order but no gaps
above 256); the highest id anywhere in the file is `INFRA-256` (the parent ticket's entry). The
investigation's guess of `INFRA-257` for the new entry is **confirmed correct**.

---

## Actor/content choice: `urban_political`'s first `hero_adventurers` population entity (`pop_0`)

`pending_information_responses` entries require a concrete `actor_id: int` matching a compiled
`AuthoritativeState.entities` key (`src/domains/information/phase.py:49`,
`resp_by_actor.setdefault(actor_id, ...)` then matched against `actor.id` for entities filtered to
`combat.alive and lifecycle.active`). Compiled entity IDs are purely positional
(`next_entity_id` counter, `src/worldbuilding/compiler.py:262`) and are **not** stably addressable
from world-content YAML by raw integer — this is the identical fragility the parent ticket's UQ-4
already ruled out for `source_id`. Hardcoding an integer here would carry the same risk.

However, the compiler already writes a stable, addressable key onto every compiled entity:
`ent_properties["population_id"] = pop_key` (`compiler.py:315-316`, where `pop_key =
getattr(pop_spec, "id", ...)`), and this is already read back elsewhere in the same function
(`compiler.py:285-297`, per-population profile overrides via `context.entities[pop_key]`) — i.e.
`population_id` is an established, existing addressing mechanism for compile-time
population-targeted content, not a new invention.

`data/worlds/urban_political/resolved/world.resolved.yaml` (lines 163-177) confirms
`hero_adventurers` compiles to three population entries `pop_0`, `pop_1`, `pop_2`, each `count: 1`,
`role: hero`, `faction: hero_guild`, `spawn_region: hometown` (module has no `namespace:`, so no
prefix is added). **Chosen actor: `pop_0`** (the first hero adventurer) — a single, unambiguous
compiled entity, thematically appropriate (an adventurer holding an assimilated belief about the
world), and reuses population targeting rather than inventing a new addressing scheme.

**Chosen response content**: a `KNOWN_FACT` about `regional_danger` for `bandit_road` (a subject
already meaningful in `urban_political`'s existing `bandit_road_trade_pressure` module and matching
the `town_notice_board` information-source profile's `knowledge_scopes` seeded by the parent ticket
— thematically consistent, though Branch A itself does not consult `information_source_profiles`
for routing/validation, only for logging `source_id` as free text):

```yaml
pending_information_responses:
  - target_population_id: "pop_0"
    subject: "bandit_road_danger"
    query_kind: "danger_rating"
    source_id: "town_notice_board"
    answer_kind: "KNOWN_FACT"
    certainty: 0.8
    details:
      danger_level: "elevated"
      region: "bandit_road"
    reason: null
    cost_paid: 0
```

`answer_kind: "KNOWN_FACT"` is chosen (not `UNKNOWN`) so the seeded content is a genuine assimilated
belief, not merely an event-emission technicality — `phase.py:72-81` sets
`last_assimilated_tick`/`last_assimilated_subject` unconditionally for every processed response
regardless of `answer_kind`, but `KNOWN_FACT` is the only branch that actually produces a
`KnowledgeFact` (`normalizer.py:47-57`), making the assimilated belief real and inspectable via
`entity.self_model.knowledge.facts`, not just an event side-effect.

**AC traceability check**: `event_extractor.py:286` emits `belief_assimilated` when
`prop.get("last_assimilated_tick") == tick`. `phase.py:76-78` sets
`property_updates["last_assimilated_tick"] = state.tick` inside the `for r in actor_resps:` loop —
this fires for `pop_0` on the initial compiled state (tick 0), the one `refine()` call where
`state.pending_information_responses` is non-empty, so `state.tick` matches the same tick
`event_extractor` reads it in. From tick 1 onward, `ApplyPath.apply_generation()`
(`src/engine/apply.py:179-416`, esp. the `AuthoritativeState(...)` construction at lines 356-408)
does not carry `pending_information_responses` forward from `prior_state` (see the correction note
at the top of this plan), so the list is empty and Branch A has nothing left to process — this is a
single fire, not a per-tick recurrence. This closes the loop: compiled seed → Branch A processes it
once at tick 0 → `last_assimilated_tick == tick` → `belief_assimilated` emitted once →
`calibration_hits == 1` per calibration run (see Step 10 — this additionally requires the Step 7
kernel tick-alignment fix to be observable through the real live loop; see the Deviations note
below for how this was discovered).

---

## Step 1 — Schema: `PendingInformationResponseSpec` on `WorldSpec`, mirrored on
`WorldCompositionSpec`/`NormalizedWorldComposition`

**Files:**
- `src/worldbuilding/schema.py` — new `PendingInformationResponseSpec` class (co-located near
  `InformationSourceProfileSpec`, current lines 57-72) + `WorldSpec.pending_information_responses`
  field (near `information_source_profiles`, current line 157)
- `src/worldassembly/schema.py` — `WorldCompositionSpec.pending_information_responses` field (near
  `information_source_profiles`, current lines 44-47) + import; `NormalizedWorldComposition` mirror
  (near current lines 158-161)

**Changes:**

1. `src/worldbuilding/schema.py` — new model:
   ```python
   class PendingInformationResponseSpec(BaseModel):
       model_config = ConfigDict(frozen=True)

       target_population_id: str = Field(
           ..., min_length=1,
           description="References an existing PopulationSpec.id (post-merge population key, "
                       "e.g. 'pop_0'). Compiler resolves this to the actor_id of the first "
                       "compiled entity whose properties['population_id'] matches — the same "
                       "addressing mechanism already used for per-population profile overrides "
                       "(compiler.py context.entities lookup). Not a raw entity ID: compiled "
                       "entity IDs are positional and not stably addressable from world content."
       )
       subject: str = Field(..., min_length=1, description="Matches InformationQuery.subject / KnowledgeFact.subject")
       query_kind: str = Field(..., min_length=1, description="Matches InformationQuery.kind (e.g. 'material_source' | 'recipe_definition' | 'danger_rating')")
       source_id: str = Field(..., min_length=1, description="Free-text provenance label for the normalized response; not validated against information_source_profiles")
       answer_kind: Literal["KNOWN_FACT", "PARTIAL_LEAD", "RUMOR", "CONTRADICTION"] = Field(
           ..., description="Matches InformationResponseNormalizer.normalize()'s branching. 'UNKNOWN' is intentionally excluded here — it produces no KnowledgeFact/LeadState and is not a meaningful thing to author as static compile-time content"
       )
       certainty: float = Field(1.0, ge=0.0, le=1.0)
       details: Dict[str, Any] = Field(default_factory=dict)
       reason: Optional[str] = Field(None, description="Only meaningful when answer_kind produces an UnknownFact; unused for KNOWN_FACT/PARTIAL_LEAD/RUMOR/CONTRADICTION but accepted for schema symmetry with the raw_response dict shape")
       cost_paid: int = Field(0, ge=0)
   ```
2. `WorldSpec` gains:
   ```python
   pending_information_responses: List[PendingInformationResponseSpec] = Field(default_factory=list)
   ```
3. `src/worldassembly/schema.py` — add `PendingInformationResponseSpec` to the existing
   `from src.worldbuilding.schema import RegionSpec, FactionSpec, PopulationSpec, QuestDefinition,
   InformationSourceProfileSpec` import line. `WorldCompositionSpec` gains:
   ```python
   pending_information_responses: List[PendingInformationResponseSpec] = Field(
       default_factory=list,
       description="Compile-time-seeded pending information responses, targeted at a population "
                   "by target_population_id. No global catalog exists for this content (same "
                   "reasoning as information_source_profiles). Scoped to this composition only."
   )
   ```
   `model_config` stays `frozen=True, extra="forbid"` — unchanged.
4. `NormalizedWorldComposition` gains the same field, mirrored verbatim — required because
   `WorldCompositionNormalizer.normalize()` does `composition.model_dump()` →
   `NormalizedWorldComposition(**data)`, and `NormalizedWorldComposition` has `extra="forbid"`; an
   unmirrored field raises `ValidationError` on **every** call to `normalize()`, for every world.

**Dependency:** none (root of the change). Blocks Steps 2 and 3.

**Verification:**
- `PendingInformationResponseSpec(target_population_id="pop_0", subject="x", query_kind="danger_rating", source_id="s", answer_kind="KNOWN_FACT", certainty=0.8)` constructs with `details == {}`, `reason is None`, `cost_paid == 0`.
- `PendingInformationResponseSpec(..., answer_kind="UNKNOWN")` raises `ValidationError` (Literal excludes it).
- `PendingInformationResponseSpec(..., certainty=1.5)` raises `ValidationError` (bound check).
- `WorldSpec.model_validate({... no pending_information_responses key ...})` → `.pending_information_responses == []`.
- `WorldCompositionNormalizer.normalize(...)` succeeds without raising for a composition with no
  `pending_information_responses` key, and `NormalizedWorldComposition.pending_information_responses
  == []`; a composition with one entry round-trips it onto the normalized model unchanged. Add this
  as a new assertion in `tests/unit/worldassembly/test_assembly.py`, alongside the
  `information_source_profiles`/`faction_tension_overrides` mirrored-field coverage (same pattern
  the parent ticket used per its Deviations note — appended to
  `test_composition_normalization_shorthand_and_mixed`, not a new test function).
- `tests/unit/worldbuilding/test_worldspec_schema.py::test_valid_minimal_world_spec_loads` must
  still pass unmodified.

---

## Step 2 — Resolver: pass composition-level `pending_information_responses` through to the
resolved `WorldSpec`

**File:** `src/worldassembly/resolver.py`, `WorldAssemblyResolver.assemble()`

**Change:** in the `world_spec = WorldSpec(...)` constructor call (currently lines 665-678,
alongside `information_source_profiles=list(normalized_comp.information_source_profiles)` at line
673), add:
```python
pending_information_responses=list(normalized_comp.pending_information_responses),
```
Direct passthrough, no merge — there is no catalog or module contribution path for this content,
same as `information_source_profiles`.

**Dependency:** requires Step 1 (both new fields must exist on `NormalizedWorldComposition` and
`WorldSpec`). Independent of Step 3.

**Verification (new tests in `tests/unit/worldassembly/test_assembly.py`, per the parent ticket's
Deviations note that `WorldAssemblyResolver.assemble()`-level composition tests live there, not in
`test_resolver.py` which tests the unrelated `CompileProfileResolver`):**
- `test_resolver_passes_pending_information_responses_from_composition`: a composition declaring 1
  `pending_information_responses` entry → `resolved.world_spec.pending_information_responses`
  contains it, all fields round-tripped unchanged.
- `test_resolver_no_pending_information_responses_declared_yields_empty_list`: a composition with no
  `pending_information_responses` key → `resolved.world_spec.pending_information_responses == []`
  (regression guard — every world other than `urban_political` must be unaffected).

---

## Step 3 — Compiler: resolve `target_population_id` to a compiled `actor_id` and construct the
`pending_information_responses` dict list

**File:** `src/worldbuilding/compiler.py`

**Changes:**
1. Insert **after** the entity-compilation loop completes (after current line 351, where `entities:
   Dict[int, EntityState]` is fully populated) and before the final `AuthoritativeState(...)`
   assembly — this ordering is required because resolution needs the completed `entities` dict:
   ```python
   # 6b. Resolve pending_information_responses: target_population_id -> compiled actor_id
   pending_information_responses: List[Dict[str, Any]] = []
   for r in spec.pending_information_responses:
       actor_id = next(
           (eid for eid, e in entities.items()
            if e.properties.get("population_id") == r.target_population_id),
           None,
       )
       if actor_id is None:
           warnings.append(
               f"pending_information_responses target_population_id "
               f"'{r.target_population_id}' matched no compiled entity; entry skipped"
           )
           continue
       pending_information_responses.append({
           "actor_id": actor_id,
           "subject": r.subject,
           "query_kind": r.query_kind,
           "source_id": r.source_id,
           "raw_response": {
               "answer_kind": r.answer_kind,
               "certainty": r.certainty,
               "details": dict(r.details),
               "reason": r.reason,
           },
           "cost_paid": r.cost_paid,
       })
   ```
   `warnings` is the same list already declared at current line 356 (`warnings: List[str] = []`,
   used by the quest-compilation block) — if this insertion point lands before that declaration,
   move the `warnings: List[str] = []` declaration earlier (to before this new block) rather than
   duplicating it; confirm exact ordering against current file state at implementation time since
   line numbers may have shifted since this investigation snapshot.
2. Pass `pending_information_responses=pending_information_responses` into the single
   `AuthoritativeState(...)` constructor call (currently lines 427-441, alongside
   `information_source_profiles=information_source_profiles`). This is the one authoritative init
   point for a fresh `AuthoritativeState`; no second seeding path is added.
3. No new import needed — the dict shape matches `AuthoritativeState.pending_information_responses:
   List[Dict[str, Any]]` (`src/core/state.py:1144`) exactly; unlike `information_source_profiles`
   this field is untyped (`Dict[str, Any]`), so no domain dataclass construction is required here,
   only the dict literal above (matching the exact shape `InformationBeliefPhase.apply()` reads at
   `phase.py:49,57,60-63` and the exact shape `tests/integration/domains/test_fused_loop.py:186-200`
   already exercises).

**Dependency:** requires Step 1 (`spec.pending_information_responses` must exist on `WorldSpec`) and
the entity-compilation block (pre-existing, unconditional ordering within `compile()`). Independent
of Step 2 — fully testable with a hand-built `WorldSpec` fixture that never touches the resolver.

**Verification:**
- `test_compiler_seeds_pending_information_responses_from_spec` (new,
  `tests/unit/worldbuilding/test_world_compiler.py`): hand-built `WorldSpec` with one population
  (`id="pop_test"`, count 1) and one `PendingInformationResponseSpec(target_population_id="pop_test",
  ...)` → `state.pending_information_responses` has length 1, with `actor_id` equal to the single
  compiled entity's id, and `subject`/`query_kind`/`source_id`/`raw_response`/`cost_paid` matching
  the spec exactly.
- `test_compiler_pending_information_response_unmatched_population_is_skipped_with_warning` (new,
  same file): `target_population_id` referencing a population that does not exist in `spec.entities`
  → `state.pending_information_responses == []` and a warning is recorded (exact warning-surfacing
  mechanism — return value vs. logged — must match however `compile()` already surfaces the
  quest-validation warnings at this call site; verify against current code, don't invent a new
  reporting path).
- `test_compiler_no_pending_information_responses_declared_yields_empty_list` (new, same file):
  `spec.pending_information_responses == []` → `state.pending_information_responses == []`.
- Existing `test_compiler_minimal_world` must still pass unmodified.

---

## Step 4 — Content: seed `urban_political` via composition-level `pending_information_responses`

**Files:**
- `data/worlds/urban_political/world.yaml` (composition — hand-edited)
- `data/worlds/urban_political/resolved/world.resolved.yaml` (regenerated, **not** hand-edited)

**Changes:**
1. Add to `data/worlds/urban_political/world.yaml` (alongside the existing
   `information_source_profiles` block, current lines 27-43):
   ```yaml
   pending_information_responses:
     - target_population_id: "pop_0"
       subject: "bandit_road_danger"
       query_kind: "danger_rating"
       source_id: "town_notice_board"
       answer_kind: "KNOWN_FACT"
       certainty: 0.8
       details:
         danger_level: "elevated"
         region: "bandit_road"
       cost_paid: 0
   ```
   (see "Actor/content choice" section above for rationale.)
2. Regenerate the resolved artifact — do not hand-edit it:
   ```bash
   python -m src.worldbuilding.cli resolve urban_political
   ```
3. Confirm the regenerated `world.resolved.yaml` shows a `pending_information_responses:` block
   with exactly this 1 entry, and diff the regenerated artifact against its prior committed version:
   only the new `pending_information_responses` block (and any incidental
   `provenance_manifest.json`/timestamp fields, per FACTION/parent-INFORMATION precedent) should
   change — regions/entities/resources/buildings/quests/factions/information_source_profiles must
   be byte-identical.

**Dependency:** requires Steps 1-3 complete, or the new YAML key is rejected (`extra="forbid"` prior
to Step 1) or silently unused/mis-resolved (prior to Step 2/3).

**Verification:**
- `test_urban_political_resolved_world_seeds_one_pending_information_response` (new,
  `tests/unit/worldbuilding/test_world_compiler.py`): load
  `data/worlds/urban_political/resolved/world.resolved.yaml`, compile with a fixed seed, assert
  `len(state.pending_information_responses) == 1`, the entry's `actor_id` matches the compiled
  `pop_0` entity's id (cross-check via `state.entities[actor_id].properties["population_id"] ==
  "pop_0"`), and all other fields match the content above exactly.
- `python -m src.worldbuilding.cli validate urban_political --strict` is **not** expected to exit 0
  — same pre-existing `[WORLD-UNEXPECTED-SECTION]` gap the FACTION/parent-INFORMATION plans already
  documented for composition-level fields predating the `--strict` validator's section allowlist.
  Confirm this is the same pre-existing gap (not a new regression) the same way those plans did.

---

## Step 5 — End-to-end integration test: compiled `urban_political` state produces `belief_assimilated`

**File:** `tests/integration/scenarios/test_phase5_information_belief_scenarios.py` (extend existing
file — mirrors its existing style, per test_plan.md item 6) or a new test in
`tests/integration/domains/information/test_phase5_information_belief_phase.py`; confirm at
implementation time which file already has the compiled-world-loading fixture pattern most similar
to this need.

**Change:** load the actual compiled `urban_political` `AuthoritativeState` (via
`WorldCompiler.compile()` against the resolved YAML, not a hand-built state — this proves the full
compile→pipeline path, the gap the parent ticket's `test_fused_loop.py:186-200` test does not close
since it hand-constructs `pending_information_responses` via `dataclass_replace`), call
`AuthoritativeApplyPipeline.refine(state, StateUpdate())` for one tick, and assert:
- `event_extractor`'s emitted events for that tick include `belief_assimilated` with
  `payload["subject"] == "bandit_road_danger"` for the `pop_0` entity.
- The refined entity's `self_model.knowledge.facts["bandit_road_danger"]` is populated (proves
  `KNOWN_FACT` branch actually assimilated, not just the property-flag side effect).

**Dependency:** requires Steps 1-4 (needs the compiled `urban_political` state with the seeded
entry).

---

## Step 6 — Single-fire regression test (documents accepted behavior, not a new gap)

**File:** same file as Step 5, or `tests/integration/domains/information/test_phase5_information_belief_phase.py`.

**Change:** run the compiled `urban_political` world for >= 2 ticks through the real
tick-advancement path — `Kernel.tick_once()` → `Kernel._phase_advancement()`
(`src/engine/kernel.py:702-722`) → `ApplyPath.apply_generation()` (`src/engine/apply.py:179-416`),
the same path `tools/calibrate_simq.py:228-233` drives in a loop, the real path Step 10 uses — and
assert:
- After the first `refine()` call (tick 0, the injected compiled state),
  `state.pending_information_responses` is non-empty and `belief_assimilated` fires once for
  `pop_0`.
- From tick 1 onward, `state.pending_information_responses == []` for every subsequent tick —
  confirming `ApplyPath.apply_generation()`'s final `AuthoritativeState(...)` construction
  (`apply.py:356-408`) does not carry the field forward from `prior_state`.
- No further `belief_assimilated` (or `belief_updated`) events fire from tick 1 onward across the
  remaining ticks — the seed is single-fire, not idempotent-repeat, and this is **not** something
  `InformationBeliefPhase` manages itself; it is a property of the broader compile-vs-apply state
  reconstruction in `apply.py`.
- No exception is raised across the run.

This is **not a bug to fix** — a bounded, single-fire assimilation is the correct/expected outcome
given how `AuthoritativeState` is rebuilt every tick advancement; it satisfies the AC
(`calibration_hits > 0`, exactly 1) with no unbounded repeat behavior. Document this as an accepted,
correctly-understood mechanism per the note below (Step 7).

**Dependency:** requires Steps 1-5.

---

## Step 7 — Kernel tick-alignment fix: 3 one-line changes (`prior_state.tick` instead of the
shared post-advance `tick`)

**Per 2026-07-03 user direction, this ticket's scope is expanded** to include the kernel
tick-alignment bug found while empirically verifying Step 6 (documented in the Deviations note
above and in `staging_artifacts/.../tick_alignment_bug_investigation.md`, a focused follow-up
investigation that sized and confirmed this fix). This is fix (b)+(b′) from that investigation —
the small, surgical option, not fix (a) (relabeling the shared `tick` variable globally, which the
investigation found would regress `InvariantViolation` tick-correctness and shift every event's
`tick` field across every scenario for no compensating benefit).

**Root cause (all 3 sites, same shape):** `Kernel._phase_advancement()` (`src/engine/kernel.py:702-736`)
captures `prior_state = self._state` (the pre-advance state) at line 713, then reassigns
`self._state` to the newly-advanced state via `ApplyPath.apply_generation(..., next_tick=self._state.tick + 1, ...)`
at line 714, and only afterward calls `self._phase_observability(prior_state, update)` at line 725.
Both `EventExtractor.extract()` (called from `_phase_observability`) and `_phase_observability`
itself derive a `tick` local from the now-advanced `current_state`/`self._state` (`event_extractor.py:81`,
`tick = current_state.tick`; `kernel.py:815`, `tick = self._state.tick`) — this is the correct,
unchanged, post-advance label used for the `SimulationEvent.tick` field on every emitted event
(consistent with `_phase_persistence`'s `TICK_END` convention, per the investigation's Contract/
Documentation Answer section — do not change this). The bug is narrower: three specific
Resolution-phase-stamped properties were stamped using the **pre-advance** tick but are compared
against the **post-advance** `tick` local, so the equality check can never match through the real
per-tick loop. `prior_state` is already an in-scope parameter at both comparison sites and is
exactly the pre-advance state whose `.tick` matches what was stamped — the fix substitutes it in,
nothing else.

**Site 1 — `src/observability/event_extractor.py:286`** (`belief_assimilated`/`belief_updated`).
Stamped by `InformationBeliefPhase.apply()` at `src/domains/information/phase.py:77`:
`property_updates["last_assimilated_tick"] = state.tick` — `state` there is the pre-advance state
Resolution operates on, i.e. the same object as `extract()`'s `prior_state` parameter.
`extract()`'s own signature (`event_extractor.py:71-76`) already receives `prior_state` — no new
parameter or plumbing needed, this is a direct read of an existing local.

Before:
```python
                # Information: belief_assimilated + belief_updated (PP-04)
                if prop.get("last_assimilated_tick") == tick:
```
After:
```python
                # Information: belief_assimilated + belief_updated (PP-04)
                if prop.get("last_assimilated_tick") == prior_state.tick:
```

**Site 2 — `src/observability/event_extractor.py:899`** (`calamity_spawned`). Stamped by
`CalamityService.process_world_dynamics()` at `src/world/calamity.py:56`:
`last_calamity_tick_set=state.tick` inside the `StateUpdate` it returns — `state` there is the
pre-advance state passed into `process_world_dynamics()` during Resolution, i.e. the same
`prior_state` `extract()` already receives. Same mechanism as Site 1.

Before:
```python
        if getattr(update, "last_calamity_tick_set", None) == tick:
```
After:
```python
        if getattr(update, "last_calamity_tick_set", None) == prior_state.tick:
```

**Site 3 — `src/engine/kernel.py:836`** (`GovernorModeChanged`). This one is **not** in
`event_extractor.py` — it lives directly inside `Kernel._phase_observability()`
(`kernel.py:806-855`), which already takes `prior_state` as its first parameter (`kernel.py:806`,
`def _phase_observability(self, prior_state: AuthoritativeState, update: Any) -> None:`) — no
signature change needed. Confirmed by tracing `tick_once()`'s phase order (`kernel.py:332-415`):
`_phase_init()` runs at line 353 (**before** `_phase_advancement()` at line 396, in the same
`tick_once()` call) and calls `self._governor.evaluate(..., self._state.tick, ...)`
(`kernel.py:535-541`) using `self._state.tick` **at that point** — which is still the pre-advance
tick for this tick, i.e. numerically identical to the `prior_state.tick` that
`_phase_advancement()` will capture later in the same call. `ResourceGovernor.evaluate()`
(`src/engine/governor.py:27-63`) calls `status.reset_dwell(indicated_mode, current_tick)`
(`governor.py:45` or `:51`) on a mode transition, which stamps `RuntimeStatus.last_transition_tick`
(`src/engine/runtime_status.py:79`, `reset_dwell(self, new_mode, current_tick)`) with that
pre-advance tick. `_phase_observability`'s own `tick = self._state.tick` (line 815) is, by the time
this runs, the post-advance tick — so the existing `== tick` check never matches. Fix: compare
against `prior_state.tick` instead, using the parameter already in scope.

Before:
```python
        # Emit GovernorModeChanged if a transition happened this tick
        if getattr(self._status, "last_transition_tick", -1) == tick:
```
After:
```python
        # Emit GovernorModeChanged if a transition happened this tick
        if getattr(self._status, "last_transition_tick", -1) == prior_state.tick:
```

**Scope guards for this step (do not exceed):**
- Do **not** change `_phase_observability`'s `tick = self._state.tick` assignment (`kernel.py:815`)
  or `event_extractor.py`'s `tick = current_state.tick` assignment (`event_extractor.py:81`) — both
  remain the correct label for `SimulationEvent.tick` on every event, unchanged. Only the 3
  stamped-property comparison sites above change.
- Do **not** touch `InvariantViolation`'s tick labeling (`kernel.py:824-833`, uses `tick` = post-advance,
  correct as-is per the investigation's finding that `HardLawMonitor.check()` runs against the
  already-advanced state) — this is fix (a)'s regression risk, explicitly not being taken here.
- Do **not** touch any other `== tick` comparison in `event_extractor.py` not confirmed affected by
  the investigation (`belief_stale` at line 434, `ecology_cycle_completed`/`spawn_cadence_fired`/
  `conservation_law_verified` modulo checks at lines 814/826/841, `progression_plateau_detected`'s
  self-referential diff at lines 736-747, and all diff/state-comparison-based checks at lines 626-629
  and 945-981) — the investigation confirmed these are either unaffected (self-cancelling diffs) or
  only benignly phase-shifted by 1 tick (modulo checks), not "never fires" bugs, and are out of scope.
- Do **not** introduce a new explicit `tick:` parameter to `EventExtractor.extract()` — the
  investigation's option (c) found this touches every call site (13+ test files) for no additional
  correctness benefit over reusing the existing `prior_state` parameter.

**Dependency:** independent of Steps 1-6 (this is a pre-existing kernel/observability bug, not
introduced by this ticket's schema/compiler/resolver work) but discovered by Step 6's real-loop
testing, and its fix is a prerequisite for Step 10's recalibration to observe non-zero
`calibration_hits` through the live loop. Blocks Step 8 (tests for this fix) and Step 10
(recalibration).

**Verification:** covered by Step 8's tests, plus confirming zero regressions in the existing
`tests/unit/observability/test_event_extractor_*.py` suite (same-state-twice pattern, per the
investigation's Test Impact section — these are no-ops under this fix since `prior_state is
current_state` in every one of them, so `prior_state.tick == current_state.tick` always holds
regardless of which side the comparison reads).

---

## Step 8 — Kernel-fix-specific regression tests: prove the 3 previously-dead event types now fire
through the REAL `Kernel.tick_once()` loop

**Files:** `tests/integration/observability/test_kernel_event_recording.py` (existing file — already
hosts the closest precedent pattern: `test_kernel_observability_event_recording` constructs a
`Kernel` with a distinct `prior_state`/current `state` pair and calls `kernel._phase_observability(prior_state, None)`
directly, then asserts on `kernel._event_recorder.events` — extend this file rather than inventing a
new one) or new tests added there.

**Change:** add 4 new tests (3 fix-proving + 1 regression guard):

1. `test_belief_assimilated_fires_through_real_tick_once_loop` — construct a `Kernel` seeded with
   the actual compiled `urban_political` `AuthoritativeState` (same compiled-state fixture as Steps
   5/6, via `WorldCompiler.compile()` against the resolved YAML — reuse, don't hand-build), call
   `kernel.tick_once()` **once** (the real loop entry point, not `_phase_observability()` called
   directly, and not `AuthoritativeApplyPipeline.refine()` called directly as Steps 5/6 do — this is
   the gap the Deviations note flagged: Steps 5/6 proved the pipeline mechanism but not the real
   `Kernel` loop), and assert `kernel._event_recorder.events` (or `kernel._entity_timeline_store`,
   whichever the existing `test_kernel_observability_event_recording` precedent uses — confirm at
   implementation time) contains a `belief_assimilated` event for `pop_0` with
   `payload["subject"] == "bandit_road_danger"`. Before this fix, this test would show **zero**
   matching events (confirmed by the Deviations note's direct instrumentation: 5 real ticks, 0
   `belief_assimilated` events); after the fix, exactly 1.
2. `test_calamity_spawned_fires_through_real_tick_once_loop` — construct a minimal
   `AuthoritativeState` with `tick` set to a multiple of `CalamityService.CALAMITY_FORCE_INTERVAL`
   (5000, `src/world/calamity.py:20`), `last_calamity_tick` at least `CALAMITY_MIN_INTERVAL` (2000,
   `calamity.py:18`) ticks earlier, and at least one region with `calamity_intensity > 0.3`
   (`calamity.py:39`, the `should_spawn` gate) so `CalamityService.process_world_dynamics()`
   deterministically spawns a `world_boss` and sets `last_calamity_tick_set=state.tick` on that
   exact tick. Confirm at implementation time exactly how `process_world_dynamics()` is invoked
   inside `Kernel._phase_resolution()`'s system list (grep for `CalamityService` call sites in
   `kernel.py`/`src/engine/pipeline_phases/` to find the wiring — not traced in this plan). Call
   `kernel.tick_once()` once at that tick and assert `calamity_spawned` fires with
   `payload["tick"]` matching. This is a genuinely new firing (per the investigation: `calamity_spawned`
   has **never** fired in any real run to date, confirmed by source trace), so this test also proves
   the event is reachable at all, not just the tick-alignment fix.
3. `test_governor_mode_changed_fires_through_real_tick_once_loop` — construct a `Kernel`/`RuntimeStatus`/
   profile where the first `tick_once()` call's `_phase_init()` (`kernel.py:488-546`) produces
   `indicated_mode > current_mode` (an escalation) — e.g. by feeding `PressureSignals` values that
   `ResourceGovernor._get_indicated_mode()` escalates on (confirm the exact signal(s) — `tick_compute_ms`,
   `worker_utilization`, `queue_utilization`, or `work_debt_total` — by reading
   `src/engine/governor.py::ResourceGovernor._get_indicated_mode()` at implementation time; do not
   guess). Call `kernel.tick_once()` once and assert `GovernorModeChanged` fires with
   `payload["current_mode"]` reflecting the escalated mode. `GovernorModeChanged` is not scored by
   any SimQ pillar (per the investigation — no reference in `simulation_quality/`), so this test's
   only purpose is proving the event itself now reaches the real loop; no scoring assertion needed.
4. `test_existing_event_extractor_same_state_tests_unchanged` — not a new test of new behavior, but
   an explicit regression-confirmation step: run
   `tests/unit/observability/test_event_extractor_cognition.py` and
   `tests/unit/observability/test_event_extractor_world.py` (the two files the investigation
   identified as using the `prior_state is current_state` pattern for `belief_assimilated`/
   `calamity_spawned` coverage) and confirm every existing test in both files still passes
   unmodified after Step 7's fix — per the investigation's Test Impact section, this is expected to
   be a true no-op (the comparison target change from `current_state.tick` to `prior_state.tick` is
   inert when both are the same object). This does not require new test code, only running the
   existing suite and recording the result; if any of these tests fail, STOP — Step 7's fix does not
   match the investigation's characterization and needs re-review before proceeding.

**Dependency:** requires Step 7 (the fix itself). Blocks Step 10 (recalibration needs the fix
proven correct first).

**Verification:** all 4 items above pass. No existing test in
`tests/unit/observability/test_event_extractor_*.py`, `tests/integration/observability/`, or
`tests/integration/kernel/` regresses.

---

## Step 9 — Docs: single-fire mechanism note

**File:** `docs/guidelines/intentional_divergences.md` (the actual file — **not**
`docs/guidelines/v2_intentional_divergences.md`, which `CLAUDE.md` cites but does not exist; do not
create a stray duplicate).

**Change:** add a short entry (rationale class: **Bounded** — the behavior is inherently bounded by
construction, not something requiring mitigation) documenting: compile-time-seeded
`pending_information_responses` entries are processed by `InformationBeliefPhase` exactly **once** —
at the initial compiled state (tick 0 of any run/calibration) — because
`ApplyPath.apply_generation()` (`src/engine/apply.py:179-416`, esp. lines 356-408) does not carry
`pending_information_responses` (or `information_source_profiles`) forward from `prior_state` when
rebuilding `AuthoritativeState` on every subsequent tick advancement
(`src/engine/kernel.py:702-722`, `Kernel._phase_advancement()`). This is a property of the
compile-vs-apply state reconstruction model, not something `InformationBeliefPhase`/Branch A manages
itself. Net effect: the seed is a genuine one-shot inbox, not a per-tick recurring event — this is
good (bounded, deterministic, exactly one `belief_assimilated` per run), not a risk needing
mitigation. Verification path: Step 6's single-fire test.

**Dependency:** independent of Steps 1-6 in principle (and independent of Steps 7-8's kernel fix —
this note describes the compile-vs-apply single-fire mechanism, unrelated to the tick-alignment
bug), but should describe the actual shipped behavior, so land after Step 6's test confirms it
empirically.

---

## Step 10 — Targeted recalibration: `urban_political` (info-plumbing) + calamity/governor-mode
spot-checks (kernel fix); confirm `calibration_hits > 0` through the real live loop; 0 unintended
regressions

**This step replaces the original plan's Step 8.** The original Step 8 could not have succeeded as
written: per the Deviations note and the `tick_alignment_bug_investigation.md` follow-up, the
`Kernel._phase_advancement()` tick-misalignment meant `belief_assimilated` would have shown
`calibration_hits == 0` through the real live loop (`tools/calibrate_simq.py` drives
`Kernel.tick_once()`), not `> 0`, until Step 7's fix landed. This step now runs the same
`urban_political` recalibration **plus** targeted spot-checks for the two newly-unblocked event
types the kernel fix affects (`calamity_spawned`, `GovernorModeChanged`), per the 2026-07-03 scope
expansion. **This is explicitly a targeted spot-check, not a full 30-scenario sweep** — per the
ticket's Out of Scope guard.

**Part A — `urban_political` recalibration (info-plumbing, now provable through the live loop):**
```bash
# Every urban_political_* scenario present in grade_anchors.json
python3 tools/calibrate_simq.py --ticks 200  --seed 42  --name urban_political
python3 tools/calibrate_simq.py --ticks 500  --seed 42  --name urban_political
python3 tools/calibrate_simq.py --ticks 500  --seed 123 --name urban_political
python3 tools/calibrate_simq.py --ticks 500  --seed 456 --name urban_political
python3 tools/calibrate_simq.py --ticks 1000 --seed 42  --name urban_political
python3 tools/calibrate_simq.py --ticks 1000 --seed 123 --name urban_political
python3 tools/calibrate_simq.py --ticks 1000 --seed 456 --name urban_political

# Spot-check one untouched world to confirm 0 leakage
python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name dungeon_crawl --profile dungeon_crawl
```

Verification for Part A:
- Every `urban_political_*` run's quality report shows `belief_assimilated` with
  `calibration_hits > 0` (expected: exactly **1 hit per calibration run** — the seed fires once, at
  the initial compiled state / tick 0, per Step 6's finding, and Step 7's fix is what makes this
  visible in `simulation_events.jsonl` through the real loop for the first time — confirm this is
  genuinely `> 0` now, not still `0`; if it is still `0`, STOP and re-check Step 7/8 before
  proceeding, do not silently accept a `0` result as "expected").
- `belief_updated` also shows `calibration_hits > 0` (also exactly 1 per run) — expected, not
  separately targeted by this ticket's AC but a natural consequence.
- `lead_certainty_updated`/`paid_information_transaction` remain `0` — expected (out of scope; not
  the chosen trigger path).
- INFORMATION pillar grade in `tests/simulation_quality/fixtures/grade_anchors.json` for every
  `urban_political_*` entry: measure the actual grade from the real run, then update the anchor
  file to match **only if it changed from `C`** — do not hand-edit speculatively ahead of a measured
  run (per test_plan.md's anti-drift guard).
- `dungeon_crawl` (untouched) shows 0 INFORMATION-pillar change.

**Part B — spot-checks for `calamity_spawned`/`GovernorModeChanged` (kernel fix):**

`calamity_spawned` requires `state.tick - state.last_calamity_tick >= CalamityService.CALAMITY_MIN_INTERVAL`
(2000) **and** `state.tick % CalamityService.CALAMITY_FORCE_INTERVAL == 0` (5000) — confirmed by
reading `src/world/calamity.py:18-20,35-36`. **No scenario currently in
`tests/simulation_quality/fixtures/grade_anchors.json` reaches tick 5000** — the longest existing
entries top out at 2000 ticks (`dungeon_crawl_seed{42,123,456}_2000t`,
`sandbox_world_seed42_2000t`), which is below even the 2000-tick minimum-interval gate on its own
and far below the 5000-tick force interval. This means **no existing calibration scenario can
exercise `calamity_spawned` even with the kernel fix applied** — this is not a gap in the fix, it
is a gap in calibration scenario duration that predates this ticket. To spot-check `calamity_spawned`
specifically, run one **new, one-off diagnostic run** at a tick count that crosses the force
interval, e.g.:
```bash
python3 tools/calibrate_simq.py --ticks 5200 --seed 42 --name dungeon_crawl --profile dungeon_crawl
```
(`dungeon_crawl` chosen because it already has a 2000t baseline for comparison and its profile has
no other reason to suppress calamities; confirm at implementation time whether `urban_political` or
`sandbox_world` would be equally or more suitable — this plan does not mandate a specific world for
this diagnostic run beyond "one with an existing shorter-duration baseline to diff against"). This
run is scoped as a **one-off diagnostic to confirm the fix works, not a permanent addition to the
calibration suite or `grade_anchors.json`** — do not add a new `_5200t` anchor entry unless a human
separately decides the calibration suite should extend to this duration. Confirm: `calamity_spawned`
fires with `calibration_hits > 0` at or after the first tick that is both `% 5000 == 0` and `>= 2000`
ticks since world start, and the resulting WORLD-pillar grade is compared before/after the kernel fix
at the same tick count to check for unintended movement (per the investigation's finding that
`calamity_spawned` feeds `WorldDynamicsScorer`'s `calamity_active`/`calamity_dormant` gate, so fixing
it is a genuine first-time behavior change to that scorer, not risk-free).

`GovernorModeChanged` is infrastructure telemetry gated on runtime resource-pressure signals
(`ResourceGovernor.evaluate()`, `src/engine/governor.py:27-63`), not on scenario tick count or
content — it is not scored by any SimQ pillar (confirmed by the investigation: no reference in
`src/simulation_quality/`). Spot-check by inspecting the longest-duration existing calibration
runs' `simulation_events.jsonl` (e.g. `dungeon_crawl_seed{42,123,456}_2000t`,
`sandbox_world_seed42_2000t` — the longest sustained-load runs already in the suite) for any
`GovernorModeChanged` events, before and after the kernel fix. A result of `0` events in these runs
is **not** itself a regression signal — governor mode transitions depend on actual runtime resource
pressure at execution time (CPU/memory/worker load), which may legitimately never escalate in a
short/light calibration run; this spot-check confirms the event *can* fire when a transition occurs
(proven directly by Step 8's dedicated unit test), not that every run must produce one. Do **not**
manufacture artificial resource pressure inside the standard calibration suite to force this event —
that is out of this step's scope.

**Stop condition:** if any spot-check in Part A or Part B surfaces an unexpected grade regression
(a pillar grade moving on a world/scenario this ticket does not target, or an unexpected magnitude
of movement on `urban_political`'s INFORMATION pillar or the diagnostic run's WORLD pillar), **STOP
and surface this to a human** rather than expanding the sweep, tuning scoring thresholds, or
re-scoping the fix unilaterally. This mirrors the ticket's Out of Scope guard verbatim.

```bash
python3 tools/evaluate_simq.py --dry-run
```
must exit 0 with 0 regressions on every pillar/world other than `urban_political`'s INFORMATION
pillar (expected to move, per AC) and the Part B diagnostic run's WORLD pillar (expected to move
only if `calamity_spawned` actually fires within it, per AC's kernel-fix bullet).

**Dependency:** requires Steps 1-9 complete (content seeded, compiler/resolver wired, kernel fix
applied and tested, tests green).

---

## Step 11 — Docs: `event_type_coverage.md` + parity ledger (`INFRA-256` revision, new `INFRA-257`
for info-plumbing, new `INFRA-258` for the kernel tick-alignment fix)

**Files:**
- `docs/simulation_quality/event_type_coverage.md` — revise the `belief_assimilated` row (current
  line 63) and `belief_updated` row (current line 64) to state `calibration_hits > 0` (with the
  actual measured count from Step 10 — expected to be exactly **1** per calibration run, since the
  seed fires once at the initial compiled state / tick 0 and `pending_information_responses` is not
  carried forward across ticks by `ApplyPath.apply_generation()`, `src/engine/apply.py:179-416`) and
  describe the compile-time `pending_information_responses` seed for `pop_0` in `urban_political` as
  the (single-fire) trigger, **plus** note that the kernel tick-alignment fix (Step 7) is what makes
  this observable through the real live loop for the first time — prior to Step 7,
  `calibration_hits` would have measured `0` despite the seed/assimilation mechanism working
  correctly. Leave `paid_information_transaction`, `lead_certainty_updated`, and the other still-0
  INFORMATION rows (current lines 72, 80-84, 98) unchanged in status but update their
  cross-references if the now-completed ticket ID changes their framing (e.g. "deferred to
  TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER" becomes "TCK-20260703-... shipped Branch A;
  Branch B / paid-info path remain unaddressed, no new follow-up ticket filed by this change" —
  do not imply those other event types are now reachable, they are not).
- `docs/simulation_quality/event_type_coverage.md` — also revise the `calamity_spawned` row
  (WorldDynamicsScorer / WORLD pillar section; confirm current line number at implementation time)
  to note it is now reachable through the real live loop as of the kernel tick-alignment fix (Step
  7), whereas previously it **never** fired in any real run regardless of scenario content (source
  trace confirmed, not merely untested) — cross-reference `INFRA-258` (below) and Step 10's
  diagnostic-run finding. Do not claim it fires in any of the standard `grade_anchors.json`
  scenarios — per Step 10, none reach the required tick count.
- `docs/simulation_quality/event_type_coverage.md` — if a `GovernorModeChanged`/infrastructure-
  telemetry row exists (it is not scored by any SimQ pillar; confirm whether this file tracks
  non-scored infrastructure events at all before adding one), note the same kernel fix makes it
  reachable through the real loop for the first time; if no such row exists in this file today, skip
  this bullet rather than inventing a new tracked-event category outside this file's existing scope.
- `docs/parity_ledger/infrastructure.yaml::INFRA-256` — **revise in place** (not append):
  - `text`: remove "Pillar is NOT active" language; state that
    `pending_information_responses` compile-time plumbing (this ticket, `INFRA-257`) makes Branch A
    reachable once per run and `belief_assimilated` calibration_hits are now > 0 (exactly 1 per run)
    for `urban_political`; Branch B (`self_model.knowledge.unknowns`) and the paid-information path
    remain unreachable.
  - `divergence_note`: replace "Pillar remains functionally inactive..." with a note that the
    pillar is now partially active via Branch A — firing exactly once, at the initial compiled state
    (tick 0 of any run), because `ApplyPath.apply_generation()` (`src/engine/apply.py:179-416`, esp.
    lines 356-408) does not carry `pending_information_responses` forward from `prior_state` on
    later tick advancements (`src/engine/kernel.py:702-722`); this is a property of the
    compile-vs-apply state reconstruction model, not something Branch A itself manages. Branch
    B/paid-info remain the documented residual gap (no new ticket implied unless a human decides to
    file one).
  - `support_boundary`: replace the "even with the flag ON... both of apply()'s trigger branches
    are unreachable" language — Branch A is no longer unreachable (it fires once, at tick 0, per
    run); keep the Branch B unreachability description (`SelfModelUpdatePhase.apply()`'s
    `events=[]`) unchanged, since this ticket does not touch it.
  - `status`/`priority`/`test_path`: `status` stays `verified` (compile-time construction remains
    correctly verified, now additionally exercised live); extend `test_path` to include this
    ticket's new tests (Steps 3-6).
- `docs/parity_ledger/infrastructure.yaml` — add a **new** entry, `id: INFRA-257` (confirmed
  next-free — see "Why this path" section above), documenting the
  `pending_information_responses` compile-time plumbing itself (schema/compiler/resolver +
  `population_id`-based actor targeting), following the same template as `INFRA-256`:
  ```yaml
  - id: INFRA-257
    text: >
      pending_information_responses compile-time plumbing: a PendingInformationResponseSpec on
      WorldSpec/WorldCompositionSpec/NormalizedWorldComposition is resolved by WorldCompiler.compile()
      into AuthoritativeState.pending_information_responses dict entries, with target_population_id
      resolved to a compiled actor_id via entity.properties["population_id"] matching (the same
      mechanism used for per-population profile overrides). Closes the "compiler never constructs
      the field" gap that made InformationBeliefPhase's Branch A permanently unreachable
      (TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER). urban_political seeds one entry targeting
      pop_0 (bandit_road_danger, KNOWN_FACT); belief_assimilated/belief_updated calibration_hits
      are now > 0 (exactly 1 per run). The seed fires exactly once, at the initial compiled state
      (tick 0 of any run), because pending_information_responses is not carried forward by
      ApplyPath.apply_generation() (src/engine/apply.py:179-416, esp. lines 356-408) across
      subsequent tick advancements (src/engine/kernel.py:702-722) — a property of the broader
      compile-vs-apply state reconstruction model, not something Branch A itself manages. Branch B
      (self_model.knowledge.unknowns) and the paid-information path remain unaddressed — see
      INFRA-256's support_boundary.
    status: verified
    priority: P1
    legacy_evidence: null
    v2_evidence: >
      src/worldbuilding/schema.py::PendingInformationResponseSpec,
      WorldSpec.pending_information_responses;
      src/worldassembly/schema.py::WorldCompositionSpec.pending_information_responses,
      NormalizedWorldComposition.pending_information_responses;
      src/worldassembly/resolver.py (WorldAssemblyResolver.assemble() passthrough);
      src/worldbuilding/compiler.py (target_population_id -> actor_id resolution +
      AuthoritativeState(pending_information_responses=...) seeding);
      data/worlds/urban_political/world.yaml (pop_0 seed);
      src/engine/apply.py::ApplyPath.apply_generation() (lines 179-416, esp. 356-408 — confirms
      pending_information_responses/information_source_profiles are not carried forward from
      prior_state, establishing the single-fire mechanism);
      src/engine/kernel.py:702-722 (Kernel._phase_advancement(), the per-tick caller of
      apply_generation())
    proof_type: parity
    test_path: "tests/unit/worldbuilding/test_world_compiler.py; tests/unit/worldassembly/test_assembly.py; tests/integration/scenarios/test_phase5_information_belief_scenarios.py"
    divergence_note: "Compile-time-seeded responses are processed by InformationBeliefPhase exactly once — at the initial compiled state (tick 0 of any run) — because ApplyPath.apply_generation() does not carry pending_information_responses forward from prior_state on later tick advancements. This is a single-fire seed, not a per-tick recurrence, and not something Branch A itself manages. Documented in docs/guidelines/intentional_divergences.md."
    support_boundary: >
      Only Branch A (pending_information_responses assimilation) is made reachable by this entry,
      and only once per run (tick 0). Branch B (routing new queries via self_model.knowledge.unknowns)
      and the paid_information_transaction path remain unreachable — see INFRA-256.
  ```
- `docs/parity_ledger/infrastructure.yaml` — add a **second new** entry, `id: INFRA-258` (confirmed
  next-free after `INFRA-257`: the file's highest existing id is `INFRA-256`, `INFRA-257` is claimed
  by this ticket's info-plumbing entry above, so `INFRA-258` is the next-free id for the kernel fix
  itself — do not reuse or renumber `INFRA-257`), documenting the kernel tick-alignment fix
  (Steps 7-8) as its own distinct parity fact, separate from the info-plumbing entries above since
  it is shared kernel/observability infrastructure affecting event types beyond this ticket's
  `urban_political`-only content scope:
  ```yaml
  - id: INFRA-258
    text: >
      Kernel tick-alignment fix: Kernel._phase_advancement() (src/engine/kernel.py:702-736)
      reassigns self._state to the post-advance tick before calling _phase_observability(prior_state,
      update), but three Resolution-phase-stamped properties (last_assimilated_tick,
      phase.py:77; last_calamity_tick_set, calamity.py:56; RuntimeStatus.last_transition_tick,
      runtime_status.py:79, set via reset_dwell() from _phase_init(), kernel.py:535-541) are all
      stamped using the pre-advance tick. EventExtractor.extract()'s and _phase_observability's
      == tick checks (event_extractor.py:286, event_extractor.py:899, kernel.py:836) compared these
      against the post-advance tick local, so belief_assimilated/belief_updated, calamity_spawned,
      and GovernorModeChanged could never match through the real Kernel.tick_once() loop — a
      pre-existing bug discovered while empirically verifying
      TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER's Step 6 against the real Kernel loop (not
      introduced by that ticket's schema/compiler/resolver work). Fixed by comparing each of the 3
      sites against prior_state.tick (already an in-scope parameter at all 3 call sites) instead of
      the shared post-advance tick variable, leaving the tick label on every emitted
      SimulationEvent (including InvariantViolation and GovernorModeChanged's own tick field)
      unchanged — this preserves the existing codebase convention (_phase_persistence's TICK_END
      also uses the post-advance tick) rather than globally relabeling _phase_observability's tick,
      which would have additionally regressed InvariantViolation's currently-correct
      post-advance labeling. Un-blocks belief_assimilated/belief_updated (feeds InformationScorer,
      SQ-15/16), calamity_spawned (feeds WorldDynamicsScorer's calamity_active/calamity_dormant
      gate, SQ-17), and GovernorModeChanged (infrastructure telemetry, not scored by any SimQ
      pillar) through the live per-tick loop for the first time in the codebase's history for all
      three event types.
    status: verified
    priority: P1
    legacy_evidence: null
    v2_evidence: >
      src/engine/kernel.py:702-736 (Kernel._phase_advancement(), prior_state/self._state
      reassignment ordering); src/engine/kernel.py:806-855 (_phase_observability(), the
      prior_state.tick fix at line 836); src/observability/event_extractor.py:286,899 (the two
      prior_state.tick fixes); src/domains/information/phase.py:77 (last_assimilated_tick stamped
      with pre-advance state.tick); src/world/calamity.py:56 (last_calamity_tick_set stamped with
      pre-advance state.tick); src/engine/runtime_status.py:79 (reset_dwell stamps
      last_transition_tick with the current_tick argument, called pre-advance from
      src/engine/governor.py:45,51 via kernel.py:535-541's _phase_init()); the follow-up
      investigation staging_artifacts/TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER/tick_alignment_bug_investigation.md
      (full site inventory, blast-radius analysis, and test-impact confirmation).
    proof_type: parity
    test_path: "tests/integration/observability/test_kernel_event_recording.py; tests/unit/observability/test_event_extractor_cognition.py; tests/unit/observability/test_event_extractor_world.py"
    divergence_note: "This is a bug fix (not an intentional behavior divergence in the usual sense): three stamped-property comparisons in EventExtractor.extract()/_phase_observability() were comparing pre-advance-stamped values against a post-advance tick, so the equality check could never match through the real per-tick loop. The fix is surgical (3 one-line changes, comparing against prior_state.tick, already in scope at each site) and does not change the tick label on any emitted SimulationEvent. Documented in docs/guidelines/intentional_divergences.md per the project's Divergence rule (rationale class: Bug Fix)."
    support_boundary: >
      Fixes exactly 3 confirmed "never fires" sites (belief_assimilated/belief_updated,
      calamity_spawned, GovernorModeChanged). Does NOT change any other == tick comparison in
      event_extractor.py — belief_stale's diff/threshold check (line 434), the modulo-gated
      ecology_cycle_completed/spawn_cadence_fired/conservation_law_verified checks (lines
      814/826/841), progression_plateau_detected's self-referential diff (lines 736-747), and all
      diff/state-comparison-based checks (lines 626-629, 945-981) were confirmed unaffected or only
      benignly phase-shifted by the investigation and are explicitly out of scope for this entry.
      Does NOT change _phase_observability's or event_extractor's shared tick label used for every
      SimulationEvent.tick field, and does NOT change InvariantViolation's tick labeling. No
      existing calibration scenario in tests/simulation_quality/fixtures/grade_anchors.json reaches
      the tick count required for calamity_spawned to fire (CalamityService.CALAMITY_FORCE_INTERVAL
      = 5000; longest existing scenario is 2000 ticks) — see Step 10's Part B for the one-off
      diagnostic run used to confirm this fix instead.
  ```
- `docs/parity_ledger/infrastructure.yaml::INFRA-246` (`WorldDynamicsScorer` /
  `calamity_spawned` ownership entry) — **check for cross-reference update, not a rewrite.**
  `INFRA-246`'s `text` already lists `calamity_spawned` as a `WorldDynamicsScorer.EVENT_TYPES`
  member (`src/simulation_quality/scorers/world_dynamics.py:17-18,66`) but says nothing about the
  event never having fired in practice. Add a short cross-reference clause to `INFRA-246`'s `text`
  or `divergence_note` (whichever is null/shorter — confirm at implementation time) pointing to
  `INFRA-258`: something like "`calamity_spawned` was unreachable through the real per-tick loop
  until the kernel tick-alignment fix (`INFRA-258`, TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER);
  see that entry for the historical gap and fix." Grep confirmed (2026-07-03, this plan's own
  investigation) that no other `docs/parity_ledger/*.yaml` entry references `calamity_spawned` or
  `GovernorModeChanged` by name today — `INFRA-246` is the only existing entry needing this
  addendum.

**Side note (informational only, out of scope):** the same single-fire trait applies to the parent
ticket's (`TCK-20260702-SIMQ-UPLIFT2-INFORMATION`) already-shipped `information_source_profiles`
compile-time scaffolding — `ApplyPath.apply_generation()` does not carry `information_source_profiles`
forward from `prior_state` either (confirmed by the same grep: zero references to either field
anywhere in `apply.py`), so any assumption that scaffolding persists/recurs across ticks would be
equally wrong. This ticket is **not** asking to fix that — it is noted here only so the parity
ledger/docs record does not carry the same misunderstanding forward for that already-shipped piece.
No action item is created by this note; a human may choose to file a follow-up ticket if this
matters for `information_source_profiles`' actual usage (Branch A here only reads `source_id` as a
free-text log label, not `information_source_profiles`, so functionally it may not matter — left as
an open observation, not a claim of impact).

**Dependency:** requires Step 10's actual measured `calibration_hits` values (must confirm they are
genuinely > 0, not guessed — expected exactly 1 per run) and Step 10's diagnostic-run finding for
`calamity_spawned`. If any file under `docs/` changed, run `make knowledge-index-update` per the
project Workflow Rule.

**Also required for this step (kernel fix documentation, per the 2026-07-03 scope expansion):**
add an entry to `docs/guidelines/intentional_divergences.md` (rationale class: **Bug Fix**,
per the project's Divergence rule table) documenting the kernel tick-alignment fix: what it was
(3 one-line comparisons switched from the shared post-advance `tick` to the already-in-scope
`prior_state.tick`), why exactly-once-per-tick stamped-property comparisons matter (a
Resolution-phase-stamped value must be compared against the state snapshot it was stamped
against, not a later-advanced one, or the comparison can never match), and which 3 event types it
un-blocks (`belief_assimilated`/`belief_updated`, `calamity_spawned`, `GovernorModeChanged`).
Verification path: Step 8's tests. This is a **separate entry** from Step 9's single-fire-mechanism
note (that one is rationale class **Bounded**, about the compile-vs-apply seed lifecycle; this one
is rationale class **Bug Fix**, about the tick-comparison bug) — do not merge the two into one
entry, they document unrelated mechanisms that happen to be adjacent in this ticket's history.

---

## Scope Guards (do NOT do these)

- Do **not** touch `src/cognition/self_model_phase.py`'s `events=[]`, `SelfModelUpdatePhase`, or
  any shared cognition-pipeline code.
- Do **not** touch `InformationNeedDetector.detect_and_generate()`
  (`src/engine/domain/cognition_extras.py`) or wire it into `CognitionDomain.execute_brain()`.
- Do **not** touch `GuildAction.visit()` (`src/town/guild.py`).
- Do **not** touch `state.information_providers` (`InformationProviderState`, `state.py:1150`) or
  `PaidInformationTransactionSystem` — a separate durable registry/system from this ticket's target.
- Do **not** touch any `data/content/world_modules/*.yaml` file — `pending_information_responses`
  must stay composition-level only (`urban_political/world.yaml`), for the same reason
  `information_source_profiles` did: shared modules (`frontier_village_core`,
  `bandit_road_trade_pressure`) are referenced by 6+ other worlds, and module-level content would
  leak INFORMATION-pillar activation into all of them, violating this ticket's `urban_political`-only
  scope.
- Do **not** enable `ENABLE_SELF_MODEL_COGNITION` anywhere — Branch A does not depend on it; leave
  it OFF everywhere, unchanged.
- Do **not** change `InformationSourceProfile`/`InformationQuery`/`NormalizedInformationResponse`/
  `InformationAssimilationResult` dataclass shapes in `src/domains/information/schema.py`.
- Do **not** change `InformationBeliefPhase.apply()`'s Branch A logic, `InformationResponseNormalizer`,
  or `InformationAssimilationService` — reuse them exactly as-is; this ticket only adds the missing
  compile-time producer of their input.
- Do **not** hand-edit `data/worlds/urban_political/resolved/world.resolved.yaml` — always
  regenerate via `python -m src.worldbuilding.cli resolve urban_political`.
- Do **not** create `docs/guidelines/v2_intentional_divergences.md` — the real file is
  `docs/guidelines/intentional_divergences.md`.
- Do **not** widen this into a general information marketplace, NPC query/response loop, or any
  content beyond the single `pop_0` seed in `urban_political`.
- Do **not** mark `lead_certainty_updated` or `paid_information_transaction` as newly reachable in
  any doc — only `belief_assimilated`/`belief_updated` are activated by this ticket's chosen path.

**Additional scope guards for the kernel tick-alignment fix (Steps 7-11, per the 2026-07-03 scope
expansion):**
- Do **not** change `_phase_observability`'s `tick = self._state.tick` assignment
  (`src/engine/kernel.py:815`) itself, or `EventExtractor.extract()`'s `tick = current_state.tick`
  assignment (`src/observability/event_extractor.py:81`) itself — both remain the correct label for
  every emitted `SimulationEvent.tick`. Only the 3 specific stamped-property comparison sites
  (`event_extractor.py:286`, `event_extractor.py:899`, `kernel.py:836`) change, each substituting
  `prior_state.tick` for the shared `tick` local at that one comparison only.
- Do **not** touch any other `== tick` pattern in `event_extractor.py` not explicitly confirmed
  affected by `tick_alignment_bug_investigation.md` — specifically leave `belief_stale` (line 434),
  `ecology_cycle_completed`/`spawn_cadence_fired`/`conservation_law_verified` (lines 814/826/841),
  `progression_plateau_detected` (lines 736-747), and all diff/state-comparison-based checks (lines
  626-629, 945-981) unchanged; the investigation confirmed these are either self-cancelling or only
  benignly phase-shifted by 1 tick, not "never fires" bugs.
- Do **not** take fix (a) from the investigation (relabeling `_phase_observability`'s shared `tick`
  variable to `prior_state.tick` globally) — this was evaluated and explicitly rejected because it
  would regress `InvariantViolation`'s currently-correct post-advance tick labeling and shift every
  event's `tick` field across every scenario's event log for no compensating benefit over the
  surgical fix (b)/(b′) actually specified in Steps 7-8.
- Do **not** expand Step 10's recalibration/spot-checks beyond the targeted scope described there
  (urban_political's standard scenarios + the one-off `calamity_spawned` diagnostic run + the
  existing-longest-run `GovernorModeChanged` inspection) without first stopping to ask a human — this
  applies both to adding more scenarios/worlds and to promoting the one-off diagnostic run into a
  permanent `grade_anchors.json` entry.
- Do **not** add a new `_5200t` (or similar) anchor entry to `tests/simulation_quality/fixtures/grade_anchors.json`
  for the Step 10 Part B diagnostic run — it is a one-off verification run, not a permanent addition
  to the calibration suite, unless a human separately decides otherwise.

---

## Dependency Map

```
Step 1 (schema: PendingInformationResponseSpec + WorldSpec/WorldCompositionSpec/NormalizedWorldComposition fields)
  ├─→ Step 2 (resolver passthrough)          [independent of Step 3; testable standalone]
  └─→ Step 3 (compiler: target_population_id -> actor_id resolution + seeding)
         [independent of Step 2; testable standalone with a hand-built WorldSpec]
             └─→ Step 4 (urban_political content: world.yaml pop_0 seed + regenerate resolved.yaml)
                    ├─→ Step 5 (end-to-end integration test: compiled state -> belief_assimilated)
                    └─→ Step 6 (single-fire regression test)
                           │
                           │   [kernel tick-alignment fix — independent of Steps 1-6's own
                           │    correctness, but discovered by Step 6's real-loop testing; a
                           │    prerequisite for Step 10 to observe non-zero calibration_hits]
                           ├─→ Step 7 (kernel tick-alignment fix: 3 one-line prior_state.tick changes)
                           │      └─→ Step 8 (kernel-fix-specific regression tests via real Kernel.tick_once())
                           │
                           └─→ Step 9 (intentional_divergences.md single-fire note, describes Step 6's
                                  confirmed behavior — independent of Steps 7-8's kernel fix)

Step 8 ──┐
Step 9 ──┴─→ Step 10 (targeted recalibration: urban_political info-plumbing [needs Steps 1-6] +
                calamity_spawned/GovernorModeChanged spot-checks [needs Steps 7-8]; confirm
                calibration_hits > 0 through the real live loop; 0 unintended regressions)
                    └─→ Step 11 (event_type_coverage.md + INFRA-256 revision + new INFRA-257
                           [info-plumbing] + new INFRA-258 [kernel fix] + INFRA-246 cross-reference
                           check + intentional_divergences.md kernel-fix note; needs Step 10's
                           measured numbers)
```

Steps 2 and 3 can be implemented in either order or in parallel (both depend only on Step 1).
Step 4 through Step 6 are strictly sequential (each needs the prior step's concrete
artifact/measurement). Steps 7-8 (kernel fix + its tests) can be implemented in parallel with Step 9
(the unrelated single-fire doc note) — both only require Step 6 to have landed — but Step 10
requires **all** of Steps 1-9 complete (both the info-plumbing chain and the kernel-fix chain feed
into the one recalibration step), and Step 11 requires Step 10's measured results.

---

## Acceptance Criteria → Step Mapping

| Ticket AC | Step(s) |
|---|---|
| Idea doc's findings re-verified against current `src/` before planning | Done above (this plan's investigation re-confirmed all file:line evidence during planning) |
| `AuthoritativeState.pending_information_responses` contains 1 entry (`pop_0`, `bandit_road_danger`) after compilation of `urban_political` | Steps 1-4 |
| Direct-pipeline integration test proves `belief_assimilated` fires and a real `KnowledgeFact` is assimilated via `AuthoritativeApplyPipeline.refine()` | Step 5 |
| Single-fire behavior confirmed and documented (not carried forward past tick 0) | Steps 6, 9 |
| Kernel tick-alignment fix applied (3 one-line changes); `belief_assimilated`, `calamity_spawned`, and `GovernorModeChanged` all confirmed reachable through the real `Kernel.tick_once()` loop where applicable | Steps 7-8 |
| At least one `urban_political_*` calibration run shows `belief_assimilated calibration_hits > 0` through the real live loop (not just the direct-pipeline test) | Step 10, Part A |
| `make evaluate --dry-run` exits 0 (0 regressions on targeted spot-check scenarios) | Step 10 |
| `docs/simulation_quality/event_type_coverage.md` and parity ledger updated to reflect the pillar as genuinely active, plus the kernel fix's own parity entry | Step 11 (`INFRA-256` revised in place + new `INFRA-257` [info-plumbing] + new `INFRA-258` [kernel fix] + `INFRA-246` cross-reference + `intentional_divergences.md` kernel-fix note) |

---

## Unresolved Questions

None requiring a human decision. Both of the ticket's own open questions (UQ-1: which option;
UQ-2: does `ENABLE_SELF_MODEL_COGNITION` need to flip) were already resolved by the investigation
with concrete evidence (Branch A chosen; flag stays OFF, unaffected). This plan's own remaining
judgment calls — which actor to target (`pop_0`, justified above by the existing `population_id`
addressing mechanism and by being the only unambiguous single-count population in
`hero_adventurers`) and the exact seeded response content (`bandit_road_danger` /
`KNOWN_FACT`, thematically tied to the parent ticket's `town_notice_board` profile and the existing
`bandit_road_trade_pressure` module) — are resolved by direct evidence from the compiler/schema
code, not left open. The parity ledger next-free IDs (`INFRA-257` for the info-plumbing entry,
`INFRA-258` for the kernel tick-alignment fix entry, added per the 2026-07-03 scope expansion) were
both confirmed by re-reading the file's full ID list (`grep -oE "^- id: INFRA-[0-9]+"` across
`docs/parity_ledger/infrastructure.yaml`, highest existing id `INFRA-256`), not assumed. The
`INFRA-246` cross-reference (`WorldDynamicsScorer.EVENT_TYPES` entry, which already lists
`calamity_spawned` but says nothing about it never having fired) was confirmed as the only existing
parity ledger entry mentioning either `calamity_spawned` or `GovernorModeChanged` by name, via a
direct grep across all `docs/parity_ledger/*.yaml` files during this plan's investigation.

---

## Deviations (implementation, 2026-07-03)

- Steps 1-6 were implemented exactly as specified: field placement/types/defaults on
  `PendingInformationResponseSpec`, the `population_id`-based `target_population_id` -> `actor_id`
  resolution and insertion point in `compiler.py`, the `urban_political/world.yaml` seed content,
  and the resolved-YAML regeneration via the CLI all match this plan verbatim. No schema/compiler/
  resolver/content deviation.
- Steps 5-6's tests were placed in
  `tests/integration/scenarios/test_phase5_information_belief_scenarios.py` (the plan's primary
  suggested location) rather than a new file — that file already hosts Phase 5 belief-loop scenario
  tests and had no compiled-world fixture to conflict with.
- **New finding, beyond what this plan's "Correction to Steps 5-9" section anticipated**: while
  empirically verifying Step 6's "single-fire ... through the real tick-advancement path" claim by
  instrumenting a live `Kernel(profile=PROD_SMALL, state=<compiled urban_political state>,
  rng=...).tick_once()` loop, direct execution showed `EventExtractor.extract()`
  (`src/observability/event_extractor.py:286`, `prop.get("last_assimilated_tick") == tick`) **never**
  matches when driven through `Kernel._phase_advancement()`
  (`src/engine/kernel.py:702-736`) — that method reassigns `self._state` to the advanced tick
  (`next_tick=self._state.tick + 1`) *before* calling `_phase_observability(prior_state, update)`,
  so `EventExtractor.extract()`'s internal `tick = current_state.tick` is always one tick ahead of
  `last_assimilated_tick`, which `InformationBeliefPhase.apply()` stamps with the **pre-advance**
  `state.tick` (`phase.py:77`). Confirmed via direct instrumented execution: 5 ticks through the
  real `Kernel.tick_once()` loop produced **zero** `belief_assimilated`/`belief_updated` events,
  even though `state.pending_information_responses`, the entity's `property_updates`, and
  `self_model_bundle_set` were all correctly populated at tick 0 (verified by intercepting
  `EventExtractor.extract`'s arguments directly). This is a **pre-existing, one-tick misalignment in
  `Kernel._phase_advancement()`'s observability wiring**, not introduced by this ticket's
  schema/compiler/resolver work, and not unique to `belief_assimilated` (the only other `== tick`
  comparison in `event_extractor.py`, `last_calamity_tick_set` at line 899, has the same exposure).
  Every existing `EventExtractor` unit test in the repo
  (`tests/unit/observability/test_event_extractor_*.py`) calls
  `EventExtractor.extract(state, state, update, mode)` with the **same** state object for both
  `prior_state`/`current_state` — none of them exercise the live Kernel's actual N-vs-N+1 state
  pairing, so this was not previously caught by any existing test.
  This ticket's Step 5/6 tests were written using that same established repo convention (matching
  `state.tick` on both sides of `extract()`), which is internally consistent with `phase.py`'s own
  tick-stamping and correctly proves Branch A's assimilation mechanism fires exactly once from the
  compiled seed. **However, this means Step 8's recalibration (not attempted in this implementation
  pass) is very likely to show `belief_assimilated`/`belief_updated` `calibration_hits == 0` in
  `simulation_events.jsonl`, not `> 0` as this plan's Step 8 verification expects, unless
  `Kernel._phase_advancement()`'s tick-pairing is separately fixed first** — a fix that is out of
  this ticket's authorized scope (no changes to `kernel.py`/`apply.py` were made or requested).
  **This should be raised to a human/architecture-review before Step 8 is attempted**; it may
  require either a small, separately-scoped fix to `_phase_observability`'s prior/current state
  pairing, or a re-scoping of Step 8's expectations, before this ticket's Step 8/9 can be completed
  as written.
- Steps 7-9 (docs: `intentional_divergences.md`, recalibration, `event_type_coverage.md` +
  parity ledger) were **not** attempted in this implementation pass, per the explicit scope
  instruction for this run (schema/compiler/resolver/content/test changes for Steps 1-6 only). This
  is scope-as-directed, not an omission — see the ticket's Implementation Notes for the finding
  above that should inform how Steps 7-9 are eventually completed.

- **Steps 7-8 (2026-07-03, follow-up pass):** implemented exactly as specified, no deviations from
  the plan's before/after code snippets. All 3 sites were re-verified against the live file content
  immediately before editing (per this run's instruction to not blindly trust line numbers) and
  matched the plan's line numbers exactly — no drift had occurred since the plan was written.
  - `test_calamity_spawned_fires_through_real_tick_once_loop`'s assertion needed one correction
    versus a literal reading of Step 8 item 2's wording ("assert `calamity_spawned` fires ... with
    `payload["tick"]` matching"): the event's own `tick`/`payload["tick"]` fields correctly use the
    **post-advance** tick (5001, i.e. `state.tick + 1` for a seed built at `tick=5000`), not 5000 —
    this is `event_extractor.py`'s existing, unchanged `tick = current_state.tick` label, exactly as
    Step 7's scope guards require staying untouched. The test asserts `payload["tick"] ==
    calamity_events[0].tick == 5001` (both post-advance), not 5000. This is not a plan deviation —
    it is what "payload matching" always meant (the tick the event is labeled with, whichever value
    that turns out to be for this state), just clarified empirically rather than left as a guess.
  - `test_governor_mode_changed_fires_through_real_tick_once_loop` used `state.work_debt` exceeding
    `profile.max_work_debt` as the escalation signal (one of the 4 candidates the plan named:
    `tick_compute_ms`, `worker_utilization`, `queue_utilization`, `work_debt_total` — the plan
    explicitly deferred the exact choice to implementation time). `work_debt_total` was chosen
    because it is fully controlled by state construction alone (no need to fake platform RSS
    sampling, executor worker/queue stats, or tick-compute timing), giving a deterministic,
    zero-flake escalation to `SURVIVAL` on the very first `_phase_init()` call.
  - `test_calamity_spawned_fires_through_real_tick_once_loop`'s wiring-confirmation grep (per Step
    8 item 2's "confirm at implementation time exactly how `process_world_dynamics()` is invoked"):
    `CalamityService.process_world_dynamics()` is called from `WorldDynamicsSystem.resolve_dynamics()`
    (`src/engine/world_dynamics.py:133`), itself called from `AuthoritativeApplyPipeline.refine()`
    (`src/engine/pipeline.py:277`, `run_phase("world_dynamics", ...)`), gated by
    `should_run(state.tick, None, cadence.world_dynamics)` (`world_dynamics.py:131`,
    `cadence.world_dynamics` defaults to 50 and is 100 under `PROD_SMALL` — both divide 5000 evenly,
    so the phase runs on the chosen test tick regardless of which profile is used).
  - Regression sweep run beyond the plan's minimum list: also ran
    `tests/unit/world/test_calamity_pressure_propagator.py`/`test_calamity_raid.py` (the actual
    calamity test files present in the repo — no `test_calamity*.py` exists directly under
    `tests/unit/world/` matching a narrower name) and `tests/unit/resource/test_resource_governor_contract.py`
    (the actual governor contract test file — no `tests/unit/engine/test_governor*.py` exists). Both
    pass unmodified. Full sweep: `tests/unit/observability/`, `tests/integration/observability/`,
    `tests/integration/kernel/`, the two calamity test files, the governor contract test file, and
    Steps 1-6's own test files — all green, 0 regressions.
  - Steps 9-11 remain not attempted this pass, per this run's explicit Steps-7-8-only scope.

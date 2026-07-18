---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER
artifact_type: investigation
tags: [simulation-quality, information, belief, cognition, self-model]
---

# Investigation — TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER

## Current Behavior (file:line refs)

### The CRITICAL LEAD, verified: the contract is real, but the fix it implies is not self-contained

`docs/cognition/README.md` (status active, P1, last_verified 2026-06-13) and
`docs/cognition/self_model_contract.md` (same status) both document
`SelfModelUpdatePhase`'s Step 1 as:

> `Step 1: Knowledge assimilation (KnowledgeModelService.assimilate) └─ Only if
> InformationResponse events exist for this entity this tick`

`src/cognition/self_model_phase.py:47-52` (inside `SelfModelUpdatePhase.apply()`) hardcodes
`events=[]` on every call to `SelfModelUpdatePhase.run()`. **Confirmed: this is the only
caller of `.run()` anywhere in `src/`** (`grep -rn "SelfModelUpdatePhase"` outside
`self_model_phase.py` returns only `src/cognition/__init__.py`'s re-export and
`src/engine/pipeline.py:142-143`'s single call to `.apply(state, u)` — which itself takes no
`events` parameter at all). So the contract is genuinely violated: this is a real bug relative
to an active, P1, human-authored contract doc, not a hypothetical.

**However, tracing the fix reveals it is not a one-line change** — there is currently no
producer of `InformationResponse`-shaped events anywhere in the tick for `events=[]` to be
corrected *to*:

- `src.world.providers.information.InformationResponse` (`src/world/providers/information.py:24-32`,
  `answer_kind` field matches what `self_model_phase.py:99`'s `hasattr(event, "answer_kind")`
  check expects) is only ever constructed inside `GuideInformationProvider.query()`
  (`information.py:36-`). **`GuideInformationProvider.query()` has zero callers anywhere in
  `src/`** (verified via grep for `GuideInformationProvider` and for
  `from src.world.providers.information`/`providers.information import` — only a
  `TYPE_CHECKING`-only import in `knowledge_model.py:26` and a docstring cross-reference in
  `self_model.py:53`). It is orphaned code, the same class of dead entry point as
  `InformationNeedDetector.detect_and_generate()` and `GuildAction.visit()` already found by the
  prior investigation — this is a **third, previously undocumented orphan** in the same family.
- There is no generic per-tick "events" plumbing in the engine that any phase could read to
  populate `SelfModelUpdatePhase.apply()`'s `events` argument. `StateUpdate`
  (`src/core/updates.py:868-919`) and `EntityUpdate` (`updates.py:607-639`) were read in full:
  neither has a general "this tick's events" list; the closest typed lists are
  `rejection_events: List[RejectionEvent]` and `world_events_add: List[WorldEvent]`
  (`updates.py:903`, `:911`), both unrelated to information responses. `apply()`
  (`self_model_phase.py:33-64`) receives only `(state, update)` — it does not even have an
  `events` parameter to thread through; `events=[]` is passed as a literal at the `.run()` call
  site, not sourced from `update` or `state` at all.
- **Even if this plumbing existed and Branch B fired**, it still would not satisfy the AC.
  `InformationBeliefPhase.apply()`'s Branch B (`src/domains/information/phase.py:83-105`) only
  ever produces an `ActionIntent` (`MOVE_TO` or `ASK_INFORMATION`,
  `src/domains/information/resolver.py:50-77`) plus `property_updates` of
  `last_routed_query_subject`/`last_routed_query_tick` — **`event_extractor.py` never reads
  either of those two property keys** (confirmed by grep of `event_extractor.py` for
  `last_routed_query`: zero hits). Branch B never sets `last_assimilated_tick`
  (`phase.py:76-78`, Branch A only), so it cannot produce `belief_assimilated`, and it does not
  touch lead certainty, so it cannot produce `lead_certainty_updated` either.
  Tracing the `ASK_INFORMATION` intent's execution
  (`src/engine/intent/action_intent.py:127-141`) shows it **only deducts gold**
  (`InventoryUpdate(gold_delta=-gold_deduct)`) — it does not call any provider, does not
  construct an `InformationResponse`, and does not write to
  `state.pending_information_responses`. **The response loop does not close anywhere in the
  current engine**: routing a query (Branch B) has no wired path back to producing a response
  that Branch A (or anything else) could ever assimilate.

**Conclusion on UQ-1, Branch B literal reading (idea doc's "Option 1"):** wiring
`events=[]` to something real requires (a) a new `InformationResponse` producer wired into the
tick (none exists reachably), (b) new cross-phase/per-tick event-collection infrastructure in
`StateUpdate`/`EntityUpdate` (none exists for this purpose today), and (c) new logic inside
`ASK_INFORMATION` intent execution to actually call a provider and produce a response that
flows back into `pending_information_responses` for a future tick's Branch A to assimilate.
This is squarely **option (b)** from the ticket's own framing — "deeper engine-pipeline changes
... that would constitute genuinely new, riskier engine work needing careful architecture
review" — not option (a). It is also indistinguishable in scope from "the full information
marketplace / NPC query-response loop" the ticket's Out of Scope explicitly excludes. The
CRITICAL LEAD's premise is half right (this is a real, documented-contract bug) and half wrong
(fixing it properly is not low-risk or self-contained).

### A simpler, previously-unnamed path that resolves the same underlying bug class: seed `pending_information_responses` at compile time (Branch A)

Branch A (`phase.py:53-81`) is **not** blocked by any code defect — its logic
(`InformationResponseNormalizer.normalize()` + `InformationAssimilationService.assimilate()`,
`src/domains/information/normalizer.py`, `src/domains/information/assimilation.py`) is fully
implemented, unit-tested (`tests/unit/domains/information/test_phase5_information_assimilation.py`,
`test_phase5_information_response_normalizer.py`), and already exercised end-to-end through the
**real pipeline** by an existing integration test:
`tests/integration/domains/test_fused_loop.py:186-200` builds an entity with a
`KnowledgeModelComponent` unknown, sets
`state = dataclass_replace(state, pending_information_responses=[...], feature_flags={"ENABLE_BELIEF_ASSIMILATION": FeatureMode.ON})`,
and calls `AuthoritativeApplyPipeline.refine(state, update)` — the assertions
(`refined.entity_updates[1].self_model_bundle_set is not None`) confirm Branch A works
end-to-end today, and (via `event_extractor.py:286-289`) would emit `belief_assimilated` when
`last_assimilated_tick == tick`, given a real `state.tick` match.

The only reason Branch A never fires in any calibration world is that
**`AuthoritativeState.pending_information_responses` (`state.py:1144`) is never constructed by
the compiler** — grep of `src/worldbuilding/compiler.py`, `src/worldbuilding/schema.py`,
`src/worldassembly/schema.py`, and `src/worldassembly/resolver.py` for
`pending_information_responses` returns **zero hits** in all four files. This is the **exact
same bug class** the parent ticket (`TCK-20260702-SIMQ-UPLIFT2-INFORMATION`) already fixed for
`information_source_profiles` — confirmed fixed: `compiler.py:412-440` now constructs
`InformationSourceProfile` objects from `spec.information_source_profiles` and passes
`information_source_profiles=information_source_profiles` into the `AuthoritativeState(...)`
call; `worldassembly/schema.py:44,158` and `worldassembly/resolver.py:673` mirror the field
through the composition→resolved-spec pipeline. **`pending_information_responses` has received
no equivalent plumbing anywhere.**

`pending_information_responses` and `information_source_profiles` are declared with identical
dataclass decorators (`field(default_factory=list, repr=False, compare=False)`, `state.py:1144-1145`)
— i.e. there is no field-level signal that one is meant to be compile-time-seedable durable
content and the other is not; the only difference is that one has compiler/schema/resolver
plumbing today and the other does not.

**This means the lowest-risk path to satisfy the AC is: add the same compiler/schema/resolver
plumbing for `pending_information_responses` that already exists for
`information_source_profiles`, seeding one static entry for one `urban_political` entity.**
This:
- Requires **zero changes** to `src/cognition/self_model_phase.py`, `SelfModelUpdatePhase`, or
  any shared cognition-pipeline code used by every world.
- Requires **zero changes** to `ENABLE_SELF_MODEL_COGNITION` (UQ-2 becomes moot — Branch A never
  reads `entity.self_model` through `SelfModelUpdatePhase` at all; it writes
  `self_model_bundle_set` directly via `InformationAssimilationService`, `phase.py:66-81`).
- Is confined entirely to `src/worldbuilding/{schema,compiler}.py`,
  `src/worldassembly/{schema,resolver}.py`, and `urban_political` world content — matching the
  ticket's Scope preference ("confined to `urban_political` calibration content where
  possible").
- Reuses already-implemented, already-tested Branch A logic with no code-path changes inside
  `src/domains/information/` at all.

### Order-of-phases check (ruled out as a blocker, confirmed independently)

`self_model` (PP-02, `pipeline.py:143`) runs before `information_belief` (PP-04,
`pipeline.py:152`) in `AuthoritativeApplyPipeline.refine()`'s phase sequence. This ordering is
irrelevant to same-tick data visibility either way: `state` is the single frozen
`AuthoritativeState` snapshot passed into `refine()` for the whole tick (`pipeline.py:34-39`
onward) — every phase closure captures the *same* `state` object
(`lambda u: SelfModelUpdatePhase.apply(state, u)`, `lambda u: InformationBeliefPhase.apply(state, ...)`),
and no phase re-reads a materialized version of `update` back into `state.entities[...]`
mid-tick. Any self-model mutation from PP-02 becomes visible to other phases only on the
**next** tick's `refine()` call, once `ApplyPath` materializes `update` into a new
`AuthoritativeState`. This confirms the prior investigation's conclusion ("no ordering conflict
... the blocker is upstream data availability") independently, and confirms Branch A firing on
tick N (from a compile-time-seeded `pending_information_responses`) is visible with no
tick-lag concerns since it does not depend on any other same-tick phase's output.

### Option 2 (`paid_information_transaction` path) re-verified: shares the *same* root blocker, plus wider blast radius

`PaidInformationTransactionSystem.enforce()` (`src/engine/pipeline_phases/paid_information.py:74-183`)
is wired unconditionally at `pipeline.py:297` (no feature flag) and requires an entity with an
**active `ProjectKind.INFORMATION_SEEKING` project** (`paid_information.py:96-104`) plus a
non-empty `state.information_providers` (`state.py:1150`, a *different* durable field from
`information_source_profiles`, confirmed distinct per the prior investigation's Anti-Drift
note — re-confirmed here, no conflation).

The only code that ever creates an `INFORMATION_SEEKING` project is
`InformationNeedDetector.detect_and_generate()` (`src/engine/domain/cognition_extras.py:46-98`),
whose own docstring (`cognition_extras.py:15-16`) instructs: *"Wire-up: call
detect_and_generate() in CognitionDomain.execute_brain() after existing project evaluation and
before route scoring."* `CognitionDomain.execute_brain()` is at `src/engine/domain/cognition.py:27`
— confirmed zero calls to `InformationNeedDetector` anywhere in `src/` outside its own file.

Critically, `detect_and_generate()` itself reads `entity.self_model.knowledge.unknowns`
(`cognition_extras.py:61-70`) — **the identical dead-state dependency as Branch B.** Wiring
`InformationNeedDetector` into `CognitionDomain.execute_brain()` (which touches shared
brain-execution code used by every world, not just `urban_political`) would still produce
nothing without also solving the `unknowns`-population problem — i.e. Option 2 is not
independent of Option 1's blocker; it inherits it, and adds its own extra wiring surface
(`CognitionDomain.execute_brain()`, a shared per-tick decision path) plus a second durable-state
seed (`state.information_providers`, `InformationProviderState`) on top. `GuildAction.visit()`
(`src/town/guild.py:14-73`) — re-verified, still zero callers anywhere in `src/` — creates
`LeadState` entries directly (not an `INFORMATION_SEEKING` project), so it cannot satisfy
`PaidInformationTransactionSystem`'s precondition either, confirming the prior investigation's
finding.

**Conclusion: Option 2, as literally scoped in the idea doc, is strictly more work and touches
more shared code than the compile-time `pending_information_responses` seed (Branch A) — it is
not the simpler option once traced.**

## Mechanics/Engine Constraints

- `docs/mechanics/04_strategic_cognition.md` still has no chapter documenting
  `InformationSourceProfile`, `InformationBeliefPhase`, or the belief-assimilation
  query/response cycle (re-confirmed, unchanged from the prior investigation's finding) — this
  remains a genuine Mechanics Bible coverage gap, out of this ticket's scope to fix per its own
  Out of Scope clause, but should be flagged again for a future doc ticket.
- `docs/cognition/README.md` / `self_model_contract.md` (both P1, active) describe Step 1 of
  `SelfModelUpdatePhase` as intended to assimilate `InformationResponse` events — this
  investigation confirms that description is aspirational/contract-only; no engine wiring
  currently realizes it. If the chosen fix (Branch A compile-time seed) is implemented, these
  two docs remain accurate as written (they describe `SelfModelUpdatePhase`'s *own* internal
  step, which the chosen fix does not touch) — no doc update is required for them under the
  Branch A recommendation. If a future ticket instead pursues the Branch B event-plumbing route,
  these docs would need no correction either (their contract is what should eventually be built),
  but a new doc noting the current unimplemented state would be warranted at that time.
- Engine kernel phase ordering (`docs/engine/kernel.md`): re-confirmed no ordering conflict
  (see "Order-of-phases check" above) — the blocker is upstream data availability at compile
  time, not phase sequencing, independent of which option is chosen.

## Parity Ledger Overlap (IDs + status)

- `docs/parity_ledger/infrastructure.yaml::INFRA-256` (lines ~3023-3038): current text states
  "Scaffolding only ... Pillar is NOT active ... calibration_hits stay at 0 pending
  TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER." Per this ticket's own Scope item 5, this entry's
  `status`/`text`/`divergence_note`/`support_boundary` must be **revised in place** (not
  appended) once a trigger is made reachable. Under the Branch A recommendation, the revision
  should state: compile-time `pending_information_responses` seeding closes the "compiler never
  constructs the field" gap (same class INFRA-256 already fixed for
  `information_source_profiles`); `belief_assimilated` is reachable via Branch A;
  `lead_certainty_updated` and `paid_information_transaction` remain unreachable (Branch B /
  paid-info path deferred, still blocked on `self_model.knowledge.unknowns`); pillar is
  genuinely (partially) active, not merely scaffolded.
- `docs/parity_ledger/infrastructure.yaml::INFRA-245` (`InformationScorer` contract entry,
  lines ~3007-3021): unchanged, no revision needed — still documents the scorer, not emission
  reachability; already correctly cross-references INFRA-256 for compile-time construction.
- A **new** parity ledger entry (recommend `infrastructure.yaml`, same file as INFRA-256, for
  placement consistency) is needed for the `pending_information_responses` compile-time
  plumbing itself — analogous to how INFRA-256 documents `information_source_profiles`'
  plumbing. Suggest `INFRA-257` (next available id in that file; confirm exact next-free id at
  implementation time by re-checking the file, since other tickets may land first).
- `docs/parity_ledger/social_narrative.yaml` (`paid_information_transaction` /
  `paid_info_transaction` emitter entries, prior investigation's ~lines 3023-3035): unchanged —
  these describe the emitter correctly; still unreachable per this investigation's Option 2
  findings; no `status` change needed since Option 2 is not the chosen path.

## Prior Work

- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-INFORMATION/investigation.md` — direct ancestor;
  all four dead-path findings (Branch A/B, `InformationNeedDetector`, `GuildAction.visit()`)
  re-verified here and confirmed still accurate against current `src/`. This investigation adds:
  (1) the `docs/cognition/` contract-violation framing was checked and found real but
  non-trivial to fix, (2) `GuideInformationProvider.query()` identified as a third orphaned
  entry point, (3) confirmation that Branch B's `ASK_INFORMATION` intent execution is a
  dead-end (gold deduction only, no response produced) even if `unknowns` were populated, (4)
  the compile-time `pending_information_responses` seed as a lower-risk alternative not named
  in the idea doc, validated against an existing full-pipeline integration test
  (`test_fused_loop.py:186-200`).
- `docs/plans/idea_information_belief_trigger_wiring.md` — re-verified; its Option 1/Option 2
  framing and "rough lean" toward Option 1 is superseded by this investigation's finding that
  neither idea-doc option is actually the lowest-risk path — the compile-time Branch A seed is.
- `TCK-20260702-SIMQ-UPLIFT2-FACTION` — sibling ticket; its compiler/schema/resolver plumbing
  pattern (schema field → compiler seeding → resolver mirror → composition-level `world.yaml`
  content) is the directly reusable template for `pending_information_responses`, exactly as it
  was already reused for `information_source_profiles` by the parent ticket. This ticket's
  Branch A recommendation is a third application of the same template.

## Risks and Open Questions

1. **UQ-1 resolved: recommend the compile-time `pending_information_responses` seed (a
   previously-unnamed "Branch A" path), not idea-doc Option 1 (Branch B/events fix) or Option 2
   (paid-information path).** Evidence above shows: Branch B's literal fix is option (b) from
   the ticket's framing (genuinely deeper engine work: new event producer + new cross-phase
   event infrastructure + new response-generation logic inside `ASK_INFORMATION` intent
   execution) and would still not alone satisfy the AC even if built, since Branch B never sets
   `last_assimilated_tick`. Option 2 shares Branch B's exact blocker (`unknowns` population) and
   adds its own shared-code wiring surface (`CognitionDomain.execute_brain()`) plus a second
   durable-state seed. The compile-time Branch A seed reuses fully-implemented, tested,
   pipeline-verified logic and touches only worldbuilding/worldassembly compiler code plus
   `urban_political` world content — the smallest blast radius of the three paths, and the only
   one confined entirely to "information/cognition domains" in the narrow sense the ticket asks
   to verify for option (a).
2. **UQ-2 resolved: `ENABLE_SELF_MODEL_COGNITION` does NOT need to be turned ON.** Branch A does
   not go through `SelfModelUpdatePhase` at all — it writes `self_model_bundle_set` directly via
   `InformationAssimilationService` inside `InformationBeliefPhase.apply()`
   (`phase.py:66-81`), gated only by `ENABLE_BELIEF_ASSIMILATION` (already `ON` in
   `urban_political.yaml:9`). Blast radius of the recommended fix on
   `ENABLE_SELF_MODEL_COGNITION` is **zero** — that flag remains `OFF` everywhere, unchanged,
   and no other calibration world's self-model behavior is touched.
3. **Repeat-fire behavior, not a blocker but must be documented**: nothing in
   `InformationBeliefPhase.apply()` clears or consumes entries from
   `state.pending_information_responses` after assimilation (no `StateUpdate` field removes
   them), and the compiler would seed this list once at world-compile time (durable, not
   re-derived per tick). This means the seeded response would be **re-assimilated on every
   tick** for the seeded actor for the entire run (idempotent no-op after the first tick, since
   `InformationAssimilationService.assimilate()` just re-sets the same fact/unknown-removal each
   time — verified by reading `assimilation.py:41-73`, safe but redundant). This should be noted
   as an accepted, documented behavior (a divergence from a hypothetical "one-shot inbox"
   design) rather than silently shipped — recommend a short note in
   `docs/guidelines/intentional_divergences.md` (see Anti-Drift Hazards; note the path named in
   this repo's `CLAUDE.md`, `docs/guidelines/v2_intentional_divergences.md`, does not exist —
   the actual file is `docs/guidelines/intentional_divergences.md`).
4. Exact next-free parity ledger id in `infrastructure.yaml` for the new
   `pending_information_responses` plumbing entry should be re-confirmed at implementation time
   (this investigation suggests `INFRA-257` based on `INFRA-256` being the last id seen in that
   file's INFORMATION-adjacent block, but other tickets may land first).
5. No open question remains that requires a *human* decision before planning: UQ-1 and UQ-2 are
   both resolved above with concrete evidence. The only remaining implementation-time judgment
   call (which actor/entity in `urban_political` to seed the response for, and the exact
   `subject`/`raw_response` content) is a plan-phase detail, not an architecture question.

## Anti-Drift Hazards

- Do **not** conflate `state.information_providers` (`InformationProviderState`, `state.py:1150`,
  consumed by `PaidInformationTransactionSystem`) with `state.pending_information_responses`
  (`List[Dict[str, Any]]`, `state.py:1144`, consumed by `InformationBeliefPhase` Branch A) or
  `state.information_source_profiles` (`state.py:1145`, consumed by `InformationBeliefPhase`
  Branch B / `InformationQueryRouter`) — three separate durable registries. This ticket's
  recommended fix touches only `pending_information_responses`.
- Do **not** touch `src/cognition/self_model_phase.py`'s `events=[]` as part of implementing the
  recommended (Branch A) fix — that hardcoding is a real, documented-contract bug, but fixing it
  is explicitly **out of scope** for this ticket's chosen path (it is idea-doc Option 1, shown
  above to require new engine infrastructure); leave it as a separately-trackable future finding,
  not a drive-by fix bundled into this ticket.
- Do **not** wire `InformationNeedDetector.detect_and_generate()` into
  `CognitionDomain.execute_brain()` as part of this ticket (Option 2) — shown above to share
  Branch B's exact blocker and add its own shared-code wiring surface; not the chosen path.
- Do **not** hand-edit `data/worlds/urban_political/resolved/world.resolved.yaml` — regenerate
  via `python -m src.worldbuilding.cli resolve urban_political`, per the FACTION/INFORMATION
  precedent.
- `docs/cognition/README.md` and `self_model_contract.md`'s Step 1 description remains accurate
  as a description of `SelfModelUpdatePhase`'s intended internal behavior — do **not** edit
  those docs to say "this never happens" as part of this ticket; they describe a real, still-true
  contract for a piece of code this ticket does not touch. If a future ticket fixes
  `events=[]` properly, no correction to these docs is needed at that time either (the contract
  was correct all along; only the implementation was incomplete).
- The repo's `CLAUDE.md` cites `docs/guidelines/v2_intentional_divergences.md` for divergence
  records; that exact path does not exist. The actual file is
  `docs/guidelines/intentional_divergences.md`. Use the real path; do not create a
  `v2_intentional_divergences.md` duplicate.
- Reuse the FACTION/INFORMATION compiler-plumbing template exactly (schema field on
  `WorldSpec` → `WorldCompositionSpec`/`NormalizedWorldComposition` mirror → compiler seeding →
  resolver override application → composition-level `world.yaml` content) — do not invent a new
  plumbing shape for `pending_information_responses`.

---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-BRANCH-B
artifact_type: investigation
tags: [simulation-quality, information, cognition, self-model, bug]
---

# Investigation — TCK-20260703-SIMQ-UPLIFT3-BRANCH-B

## Current Behavior (file:line refs)

### 1. Re-verified: `events=[]` hardcoding still present, unchanged

`src/cognition/self_model_phase.py:47-52` (`SelfModelUpdatePhase.apply()`) still hardcodes:

```python
new_bundle = SelfModelUpdatePhase.run(
    entity=entity, state=state, events=[], tick=state.tick
)
```

`SelfModelUpdatePhase.apply()` is still `.apply()`'s only caller of `.run()` in `src/`
(re-confirmed via grep), and `pipeline.py:142-143` is `.apply()`'s only caller. The finding from
`stored_artifacts/TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER/investigation.md` is accurate
against current `src/` — line numbers unchanged.

### 2. UQ-1(a) resolved: NO — Branch A's phase output cannot be read directly

Two independent, conclusive reasons:

**Phase order.** `pipeline.py:143` runs `self_model` (PP-02) before `pipeline.py:152` runs
`information_belief` (PP-04) inside the same `AuthoritativeApplyPipeline.refine()` call. Both
phase closures capture the *same* frozen `state` object for the whole tick (no phase re-reads a
materialized version of `update` mid-tick — re-confirmed, matches the prior investigation's
"Order-of-phases check"). This means even if Branch A produced a durable, readable event object,
`self_model` (running first) could not see it until the *next* tick's `refine()` call, after
`ApplyPath` materializes `update` into a new `AuthoritativeState`.

**No object to read even ignoring order.** `InformationBeliefPhase.apply()`
(`src/domains/information/phase.py:53-81`, Branch A) does not produce or store any
`InformationResponse`-shaped object anywhere durable. It normalizes the raw pending-response dict
into a locally-scoped `NormalizedInformationResponse` (`normalizer.py:33`), immediately feeds it to
`InformationAssimilationService.assimilate()` (`assimilation.py:28`), and writes the result straight
into `EntityUpdate(self_model_bundle_set=new_self_model)` (`phase.py:68-81`) — bypassing
`KnowledgeModelService`/`SelfModelUpdatePhase` entirely. There is no "this tick's InformationResponse
events" list anywhere in `StateUpdate`/`EntityUpdate` that Branch A populates and any other phase
could read (confirmed again in Finding 5 below).

**Type/shape incompatibility, confirmed by direct comparison.** Even if Branch A's intermediate
object were exposed, it is a *different, incompatible type* from what
`KnowledgeModelService.assimilate()` (`src/cognition/knowledge_model.py`, Step 1's actual consumer)
expects:

| Field | `src.world.providers.information.InformationResponse` (what Step 1 expects, `information.py:23-31`) | `src.domains.information.schema.NormalizedInformationResponse` (what Branch A produces, `schema.py:62-77`) |
|---|---|---|
| `answer_kind` values | lowercase: `"known"`/`"partial"`/`"unknown"`/`"insufficient_gold"` | UPPERCASE: `"KNOWN_FACT"`/`"PARTIAL_LEAD"`/`"RUMOR"`/`"UNKNOWN"`/`"CONTRADICTION"` |
| unknowns field | `unknowns: Tuple[str, ...]` (plain subject strings) | `unknowns: Tuple[UnknownFact, ...]` (objects) |
| leads field name | `suggested_leads` | `leads` |

`KnowledgeModelService.assimilate()` (`knowledge_model.py:93-101`) does
`for unknown_subject in getattr(response, "unknowns", ()): ... unknowns[unknown_subject] = UnknownFact(subject=unknown_subject, ...)`
— if fed a `NormalizedInformationResponse`, `unknown_subject` would be a whole `UnknownFact` object,
not a string, silently corrupting the `Dict[str, UnknownFact]` (wrong key type, `subject=<UnknownFact
object>`). This is a real, demonstrable incompatibility, not a hypothetical — confirmed by reading
both dataclasses side by side. **Confirmed: `tests/unit/cognition/test_phase2_self_model_phase.py:79-101`
already unit-tests Step 1 exclusively against `src.world.providers.information.InformationResponse`
(imported explicitly, lowercase `answer_kind="known"`) — this is the one and only shape Step 1 is
built for.**

**Conclusion: UQ-1(a) is NO.** There is no minimal way to read Branch A's output directly.

### 3. UQ-1(b) resolved: YES, new plumbing is required — but the ticket's literal framing understates the gap

`src.world.providers.information.InformationResponse` — the type Step 1 actually needs — is
constructed *only* inside three provider classes' `.query()` methods:
`GuideInformationProvider.query()`, `BlacksmithInformationProvider.query()`,
`GuildInformationProvider.query()` (all in `src/world/providers/information.py`). Re-verified via
grep (`grep -rn "GuideInformationProvider\|BlacksmithInformationProvider\|GuildInformationProvider"
src/ --include=*.py`, excluding their own definition file): **zero results** — all three are
orphaned, not just `GuideInformationProvider` as the prior investigation found. There is no live
producer of the exact event type Step 1 needs anywhere in the reachable pipeline today.

`src/core/updates.py` (`StateUpdate`, lines ~868-919; `EntityUpdate`, lines ~607-639) was re-read in
full: still no generic "this tick's events" list. The closest typed lists
(`rejection_events: List[RejectionEvent]`, `world_events_add: List["WorldEvent"]`,
`quest_registry_add`, etc.) are all single-purpose and unrelated to information responses. This
re-confirms the prior investigation's finding independently.

**However — there IS a smaller path than "wire a live provider call," which the ticket's own
framing (new "per-tick event plumbing... genuinely new... shared-engine-path scope") does not
explicitly name:** the repo has an established, three-times-reused pattern (per
`docs/parity_ledger/infrastructure.yaml::INFRA-256`/`INFRA-257`, and the `FACTION`/`INFORMATION`
compiler-plumbing template cited in that ledger) of **compile-time-seeding a durable
`AuthoritativeState` field, then teaching exactly one phase to read it directly from `state`** —
no live producer, no generic StateUpdate event-bus. `pending_information_responses`
(`state.py:1144`) is exactly this pattern for Branch A. The same template *could* be reused a
third time for Step 1: add a new durable field (e.g. `pending_self_model_information_events`) seeded
via the identical schema→compiler→resolver chain, containing dicts that map 1:1 onto
`src.world.providers.information.InformationResponse`'s actual field names/vocabulary (lowercase
`answer_kind`, `unknowns` as plain subject strings, `suggested_leads`), and teach
`SelfModelUpdatePhase.apply()` to read `getattr(state, "pending_self_model_information_events", [])`,
filter by `entity_id`, convert each dict into an `InformationResponse` object, and pass the list as
`events=[...]` into `.run()`. This is a **third application of an already-precedented pattern**, not
"the full information marketplace" — it needs no fix to the orphaned providers, no fix to
`ASK_INFORMATION` intent execution, and no generic cross-phase event bus. It does, however, still
require: a new schema field (`WorldSpec`/`WorldCompositionSpec`/`NormalizedWorldComposition`), new
compiler/resolver code, a new `AuthoritativeState` field, and new read logic inside
`SelfModelUpdatePhase.apply()` — this is genuinely new plumbing, just of the smallest precedented
shape available, not brand-new architecture.

### 4. NEW FINDING (not anticipated by either ticket): `InformationBeliefPhase`'s pipeline wiring silently discards every other phase's same-tick `StateUpdate` contributions

This is independent of the `events=[]` bug and was discovered while tracing whether a Step-1 fix
could ever be *observed* end-to-end. `InformationBeliefPhase.apply()` (`phase.py:27-33`) has **no
`update`/`StateUpdate` parameter in its signature at all** — `apply(state, profiles,
pending_responses, context)`. Its `pipeline.py:152` call site wires it as:

```python
update = run_phase("information_belief", update,
    lambda u: InformationBeliefPhase.apply(state, source_profiles, pending_resps),
    "ENABLE_BELIEF_ASSIMILATION")
```

The lambda's `u` parameter is never referenced. `run_phase` (`pipeline.py:102-133`) returns
`phase_fn(upd)`'s result **directly, replacing** `upd` for the next phase — there is no merge
step. Compare with three *other* "delta"-producing phases in the same file that use the
established `u.merge(...)` pattern instead: `faction_awareness` (`pipeline.py:181`),
`diplomatic_transitions` (`pipeline.py:211`), `military_conflict` (`pipeline.py:221`) — all wrap
their phase's output in `lambda u: u.merge(PhaseDelta(...))`. `information_belief`'s wiring is the
one phase in this family that does not. `StateUpdate.merge()` (`src/core/updates.py:946`) is a
real, established method used precisely for this purpose elsewhere.

**Empirically confirmed** (not just static analysis) by running the real pipeline:

```
# ENABLE_SELF_MODEL_COGNITION=ON, ENABLE_BELIEF_ASSIMILATION=OFF, 1 entity, no info events:
refined.entity_updates = {1: EntityUpdate(self_model_bundle_set=<not None>)}   # self_model's write SURVIVES

# ENABLE_SELF_MODEL_COGNITION=ON, ENABLE_BELIEF_ASSIMILATION=ON, 2 entities, no pending responses/unknowns:
refined.entity_updates = {}   # self_model's writes for BOTH entities are WIPED
```

`InformationBeliefPhase.apply()` builds its own `entity_updates: Dict[int, EntityUpdate] = {}`
from scratch (`phase.py:38`) and returns `StateUpdate(entity_updates=entity_updates)`
(`phase.py:108`) or the bare default `StateUpdate()` (`phase.py:37`, via the `if entity_updates:`
guard at `phase.py:107`) if it processed no actors that tick. Either way, **every field on the
`StateUpdate` from every earlier phase this tick — `self_model`'s per-entity
`self_model_bundle_set`, `trust_boundary`'s and `actor_validity`'s effects, anything — is discarded
wholesale**, because the returned object is a brand-new `StateUpdate`, not a merge.

**Why this has never been observed before:** no calibration profile anywhere (re-confirmed via
grep across `config/simulation_quality/profiles/*.yaml`) sets `ENABLE_SELF_MODEL_COGNITION: "ON"`.
`ENABLE_BELIEF_ASSIMILATION` is `"ON"` only for `urban_political`. The two flags have never been
`ON` simultaneously in any run to date, so this clobbering has had nothing to clobber. **This
ticket's own Acceptance Criteria — "Branch B confirmed reachable" — would be the first scenario in
this repo's history to require both flags ON at once**, which is precisely the combination that
triggers this pre-existing defect.

**Consequence for this ticket's Acceptance Criteria:** fixing `events=[]` alone is **not sufficient**
to make `self_model.knowledge.unknowns` durably populated (surviving into materialized state) in any
scenario where `ENABLE_BELIEF_ASSIMILATION` is also ON — which is required for Branch B to be
reachable at all, since Branch B's routing logic lives inside `InformationBeliefPhase.apply()`
itself. Whatever Step 1 writes for an entity in tick N gets wiped in the very same `refine()` call
(before `ApplyPath` ever materializes it), *unless* `InformationBeliefPhase.apply()`'s pipeline
wiring is also fixed to merge with the incoming `update` (matching the `faction_awareness` /
`diplomatic_transitions` / `military_conflict` pattern). This is a second, distinct defect from the
one this ticket is scoped to (`events=[]`), and fixing it touches `pipeline.py`'s
`information_belief` wiring and/or `InformationBeliefPhase.apply()`'s signature — a different, if
adjacent, piece of shared cognition-pipeline code.

### 5. `ENABLE_SELF_MODEL_COGNITION` re-verified — orthogonal to the code fix, but load-bearing for verification

`ff_manager` defaults `ENABLE_SELF_MODEL_COGNITION` to `FeatureMode.OFF`
(`src/domains/optimization/feature_flags.py:15`). No calibration world's profile
(`config/simulation_quality/profiles/*.yaml`) turns it on; `urban_political.yaml` sets only
`ENABLE_SOCIAL_COOPERATION` and `ENABLE_BELIEF_ASSIMILATION`. `rollout_profiles.py` defines
`CLASS_A`/`CLASS_B`/`CLASS_C` hardware profiles that *do* include
`ENABLE_SELF_MODEL_COGNITION` in `enabled_phases`, but no calibration world config wires a
`rollout_profile` in (grep of `data/worlds/` for `rollout_profile` returns zero hits). This means:
in every calibration scenario run through `tools/calibrate_simq.py` today, **`SelfModelUpdatePhase.
apply()` never executes at all** — `run_phase`'s `mode == FeatureMode.OFF` branch
(`pipeline.py:108-110`) returns `upd` unchanged before Step 1 (or the `events=[]` bug) ever runs.

This confirms the prior investigation's UQ-2 conclusion in the narrow sense that stands: **the code
fix to `events=[]` itself does not require flipping this flag ON anywhere** (the fix is inert
whether the flag is on or off; turning the flag ON is a separate act from fixing the bug). But it
means: **Acceptance Criterion "self_model.knowledge.unknowns confirmed populated in at least one
calibration scenario... via direct-pipeline test" can only be satisfied by a test that explicitly
overrides `state.feature_flags` (or `pressure_signals`) to turn `ENABLE_SELF_MODEL_COGNITION` ON for
that one test invocation** — exactly the same pattern `tests/integration/domains/test_fused_loop.py:186-200`
already used for `ENABLE_BELIEF_ASSIMILATION` to verify Branch A, and exactly what
`src/testing/scenario_runner.py:100-106` already does (sets `pressure_signals={"ENABLE_SELF_MODEL_COGNITION": 1.0, ...}`
for its own scenario). This is **not** "turning it on globally" in the sense the ticket's Out of
Scope prohibits (no calibration world's shipped profile YAML needs to change) — it is a scoped,
per-test override, consistent with the ticket's own Out-of-Scope wording.

## Mechanics/Engine Constraints

- `docs/cognition/self_model_contract.md` (`status: active`, P1) and `docs/cognition/README.md`
  describe Step 1 exactly as the code (once fixed) would implement it: "Only if InformationResponse
  events exist for this entity this tick." Neither doc needs correction under either the
  compile-time-seed plumbing approach or a live-producer approach — both describe
  `SelfModelUpdatePhase`'s *own* internal contract, which stays accurate regardless of where the
  events come from.
- `docs/engine/authoritative_pipeline.md:23` documents `self_model` as PP-03 gated by
  `ENABLE_SELF_MODEL_COGNITION`; unchanged by this ticket's scope.
- `docs/audits/D19_domain_phase_inventory.md:78` labels `self_model` "feature-gated" — accurate,
  re-confirmed.
- No existing doc anywhere documents the `InformationBeliefPhase.apply()` update-clobbering defect
  (Finding 4) — this is a genuine, previously-undocumented engine-contract gap. It does not violate
  any *written* contract (no doc claims phases are merge-safe against `information_belief`
  specifically), but it violates the implicit invariant the `u.merge(...)` pattern establishes
  elsewhere in the same file, and `docs/engine/kernel.md`'s framing of `refine()` as accumulating
  refinements across 17 phases.

## Parity Ledger Overlap (IDs + status)

- `docs/parity_ledger/infrastructure.yaml::INFRA-256` (support_boundary, ~line 3064): already
  states "Branch B (self_model.knowledge.unknowns) remains unreachable: SelfModelUpdatePhase.apply()
  hardcodes events=[], so the assimilation loop that would populate it never runs." This entry will
  need revision once/if this ticket lands a fix — but per Finding 4, the revision must be careful
  not to overclaim reachability unless the `InformationBeliefPhase` clobbering defect is also
  addressed (or the test scope is explicit about only exercising Step 1 in isolation from Branch A/B
  together).
- `docs/parity_ledger/infrastructure.yaml::INFRA-257` (support_boundary, ~line 3110-3113): same
  cross-reference to INFRA-256 for Branch B's unreachability — same revision consideration applies.
- No parity ledger entry currently documents `InformationBeliefPhase.apply()`'s missing
  `update`-merge (Finding 4). If this ticket (or a follow-up) fixes it, a **new** entry is needed in
  `infrastructure.yaml` (next available id after INFRA-258, which is the last id observed in that
  file's INFORMATION-adjacent block as of this investigation — re-confirm at implementation time).
- If this ticket's fix is scoped *only* to `events=[]` (per its Out-of-Scope wording, "this ticket
  touches only Step 1's event plumbing") and does **not** also fix Finding 4, then INFRA-256/257
  should likely stay as-is (Branch B genuinely still unreachable end-to-end in any scenario with
  both flags on) with a note added describing the newly-found secondary blocker, rather than being
  marked resolved.

## Prior Work

- `stored_artifacts/TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER/investigation.md` — direct
  ancestor; found the `events=[]` bug and explicitly deferred its fix to this ticket. Its framing of
  "Option 1 requires (a) a new producer + (b) new cross-phase infrastructure + (c) new
  `ASK_INFORMATION` logic" is refined here: (a)+(c) can be avoided entirely by reusing the
  compile-time-seed template a third time (Finding 3); (b) is smaller than a generic event bus if
  that template is followed. That investigation's "repeat-fire every tick" speculation about
  `pending_information_responses` is superseded by the now-shipped, verified behavior documented in
  `INFRA-257`: it fires exactly once, at tick 0, because `ApplyPath.apply_generation()` does not
  carry `pending_information_responses` forward from `prior_state`
  (`src/engine/apply.py:179-416`, esp. 356-408).
- `docs/parity_ledger/infrastructure.yaml::INFRA-256`/`INFRA-257`/`INFRA-258` — Branch A's shipped,
  verified compile-time plumbing; the reusable template for a third application (Finding 3), and the
  authoritative up-to-date state of `pending_information_responses`'s actual runtime behavior.
- `docs/guidelines/intentional_divergences.md` (lines ~259-286) — records the single-fire behavior
  of `pending_information_responses` as an intentional divergence; a Step-1 fix following the same
  template would need an analogous entry.

## Risks and Open Questions

1. **UQ-1 resolved**: (a) No — Branch A's output cannot be read directly (phase order + no exposed
   event object + type/vocabulary incompatibility, all independently conclusive). (b) Yes, new
   plumbing is required, but the smallest available shape is a **third application of the
   compile-time-seed template** already used for `information_source_profiles` and
   `pending_information_responses` — not a live provider call, not a fix to `ASK_INFORMATION`, not a
   generic StateUpdate event bus.
2. **UQ-2 resolved**: `ENABLE_SELF_MODEL_COGNITION` remains orthogonal to the *code fix* itself (the
   fix is flag-agnostic), but is **load-bearing for verification** — no calibration profile turns
   it on, so satisfying the Acceptance Criteria requires a scoped per-test flag override (matching
   `test_fused_loop.py`'s and `scenario_runner.py`'s existing pattern), not a change to any shipped
   world profile.
3. **NEW, ticket-critical risk (Finding 4)**: `InformationBeliefPhase.apply()`'s pipeline wiring
   (`pipeline.py:152`) discards every other phase's same-tick `StateUpdate` contribution, because it
   has no `update` parameter and its call site doesn't use the established `u.merge(...)` pattern.
   Empirically confirmed via direct `AuthoritativeApplyPipeline.refine()` calls. This means: **even
   after fixing `events=[]`, `self_model.knowledge.unknowns` will not survive into materialized
   state in any scenario where `ENABLE_BELIEF_ASSIMILATION` is also on** — which is required for
   Branch B (living inside `InformationBeliefPhase.apply()`) to fire at all. Satisfying this
   ticket's literal Acceptance Criteria ("Branch B confirmed reachable") requires either (a) fixing
   this second defect too (out of this ticket's stated Out-of-Scope wording, which restricts to
   "Step 1's event plumbing"), or (b) documenting honestly that Branch B remains blocked by a
   separate, adjacent defect even after this ticket's fix lands, per the ticket's own allowance
   ("or, if it's still blocked by something else discovered during investigation, document that
   honestly rather than claim success").
4. **Recommendation for scope**: given Finding 4 is squarely "adjacent shared cognition/information
   pipeline code," not "Step 1's own event plumbing," the cleanest path consistent with this
   ticket's stated scope is: (a) implement the Step-1 `events=[]` fix using the compile-time-seed
   template (Finding 3), (b) verify it in isolation (a direct `SelfModelUpdatePhase.run()` /
   `.apply()` unit+integration test with `ENABLE_BELIEF_ASSIMILATION` OFF, confirming
   `self_model.knowledge.unknowns` becomes populated and survives materialization), and (c) document
   Finding 4 as a newly-discovered, separately-trackable blocker for actual Branch B reachability,
   rather than silently expanding this ticket's scope to fix `InformationBeliefPhase.apply()`'s
   wiring too. This is a judgment call for the plan phase / a human decision if the team wants
   Branch B *actually* reachable versus merely "no longer blocked by the events=[] bug specifically."
5. No open question here requires a human decision to *begin* planning the Step-1 fix itself (UQ-1
   and UQ-2 are resolved with evidence). The one item that does plausibly warrant a human/product
   decision: **whether "Branch B confirmed reachable" (the AC's literal wording) is satisfied by
   fixing only `events=[]` and documenting Finding 4 as a residual blocker, or whether the ticket's
   scope should be expanded to include fixing `InformationBeliefPhase.apply()`'s merge defect too.**
   This does affect ticket scope/AC satisfaction and should be flagged to the ticket owner before
   implementation proceeds, rather than assumed either way.

## Anti-Drift Hazards

- Do **not** conflate `src.world.providers.information.InformationResponse` (lowercase
  `answer_kind`, what Step 1/`KnowledgeModelService` actually consumes) with
  `src.domains.information.schema.NormalizedInformationResponse` (uppercase `answer_kind`, what
  Branch A/`InformationAssimilationService` consumes) — they are different types with incompatible
  field shapes despite similar names. Any new compile-time-seed field for Step 1 must construct the
  *former*, not adapt/reuse the latter.
- Do **not** assume `pending_information_responses` (Branch A's field) can be directly repurposed
  for Step 1 without a translation layer — its seeded `raw_response.answer_kind` values
  (`"KNOWN_FACT"`, etc., confirmed in `data/worlds/urban_political/world.yaml:44-50`) use the
  Branch-A/normalizer vocabulary, not Step 1's vocabulary. A shared field would require either two
  parallel vocabularies or a mapping table — recommend a **separate** new field (per the established
  template) rather than overloading `pending_information_responses`.
- Do **not** assume this ticket's fix alone makes Branch B reachable — Finding 4 is a real,
  empirically-confirmed, additional blocker. Do not mark
  `docs/parity_ledger/infrastructure.yaml::INFRA-256`/`INFRA-257` as fully resolved for Branch B
  unless Finding 4 is also fixed and verified; otherwise the ledger would overclaim.
- Do **not** enable `ENABLE_SELF_MODEL_COGNITION` in any shipped calibration profile YAML
  (`config/simulation_quality/profiles/*.yaml`) as part of this ticket — verification should use a
  scoped, per-test `feature_flags`/`pressure_signals` override, matching
  `test_fused_loop.py:186-200`'s and `scenario_runner.py:100-106`'s existing pattern. Enabling it
  globally would be a much larger, unreviewed blast-radius change (it would newly execute
  `SelfModelUpdatePhase` for every entity in every tick of every world using that profile) and is
  explicitly Out of Scope.
- Do **not** hand-edit `data/worlds/urban_political/resolved/world.resolved.yaml` if a new
  compile-time seed field is added — regenerate via
  `python -m src.worldbuilding.cli resolve urban_political`, per the FACTION/INFORMATION precedent.
- The repo's `CLAUDE.md` cites `docs/guidelines/v2_intentional_divergences.md`; the real file is
  `docs/guidelines/intentional_divergences.md` (re-confirmed, same discrepancy the prior
  investigation already flagged — still unresolved, not this ticket's job to fix but worth noting
  again).

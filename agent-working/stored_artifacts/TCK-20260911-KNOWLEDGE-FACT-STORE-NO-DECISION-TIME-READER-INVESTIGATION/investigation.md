# Investigation — TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION

## Step 1: re-verify the premise on current `main` (per peer review's explicit instruction —
did not trust the ticket's own prior listing)
Fresh grep sweep, not the ticket's own citation list, for every real access to
`self_model.knowledge.facts` outside `src/core/self_model.py`:
- `src/domains/information/assimilation.py:44,51,93` — write path.
- `src/cognition/knowledge_model.py:62` — write path.
- `src/engine/pipeline_phases/lead_contradiction.py:204` — passthrough reconstruction.
- `src/cognition/self_model_phase.py:117-118` — trace-only diff for event emission.
- (`src/worldbuilding/compiler.py:705` matches `.facts` textually but is an unrelated field —
  `SelfModelInformationFactSpec.facts`, a world-seeding spec, not `self_model.knowledge.facts`.)

Also checked every file importing the `KnowledgeFact` type itself (broader than the `.facts`
attribute grep) for any reference I might have missed: all remaining hits are either the unrelated
`src.world.providers.information.KnowledgeFact` (a different class, the provider-side transfer
object, already correctly disambiguated per `TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-
RECONCILIATION`), comments, or type imports with zero real usage (`src/core/cognition.py` imports
`KnowledgeFact` and never references it again in the file).

**Premise confirmed to still hold, unchanged, on current `main`.** Neither
`information_source_profiles` threading (Batch C) nor real entity density (this batch) added a new
consumer. Also checked the one candidate that looked promising from `TCK-20260904-...`'s own
(imprecise) "real consumers" listing — `src/engine/domain/cognition_extras.py`
(`InformationNeedDetector`) is a real, live decision-time reader, but of `entity.self_model
.knowledge.unknowns` (`UnknownFact`, a sibling field), not `.facts` (`KnowledgeFact`) at all. Noted
as a correction to that prior ticket's own imprecise "real consumers" list, which conflated
consumers of the `KnowledgeModelComponent` container generally with consumers of `.facts`
specifically.

## Step 2: a deeper finding — facts are barely ever even *written* in real default gameplay
Before assuming the write side runs and only the read side is missing, instrumented a real
500-tick `frontier_living_world` Campaign run (seed 7, same scenario this whole audit arc uses) and
patched `InformationAssimilationService.assimilate()` directly (the sole real function that ever
constructs a `KnowledgeFact` and merges it into `self_model.knowledge.facts`).

**Result: `assimilate()` was called zero times.** Traced why, confirming rather than assuming:
`InformationAssimilationService.assimilate()` has exactly two real call sites:
1. `InformationBeliefPhase.apply()`'s Branch A, driven entirely by a `pending_responses` parameter
   — itself read from `state.pending_information_responses`
   (`src/engine/pipeline.py:199`). This field is never threaded into Campaign's own
   `AuthoritativeState` construction — a real, already-disclosed, already-open gap
   (`TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH`, filed the same day as
   this ticket, explicitly out of scope here). So this path is structurally empty for any Campaign
   run today.
2. `ActionIntentAdapter.execute()`'s `ASK_INFORMATION` handler
   (`src/engine/intent/action_intent.py:182`) — the "closes the loop" path
   `TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE`'s own test proves works correctly in isolation. But
   reaching it requires `InformationIntentExecutionPhase` to actually execute the routed
   `ActionIntent`, and that phase is gated `ENABLE_INFORMATION_INTENT_EXECUTION` — confirmed
   default OFF (`TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-STRATEGIC-
   WORK-QUEUE`'s own investigation), and not enabled by `frontier_living_world`'s own shipped
   profile (confirmed empirically: zero calls in the real run).

Git chronology, per peer review's explicit request: `belief.py` (`BeliefEntry`) 2026-04-23;
`assimilation.py` (`KnowledgeFact`) 2026-05-30, over a month later — the newer mechanism, same
pattern as every other "later, more deliberate design" finding this audit arc has made.
`ENABLE_INFORMATION_INTENT_EXECUTION` introduced 2026-07-14
(`TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE`), nearly two months after `KnowledgeFact` itself —
that ticket's own Out of Scope explicitly deferred turning the flag on as a future decision needing
its own calibration validation, not an oversight.

**So the "no decision-time reader" finding, while structurally true, is not the binding constraint
in practice**: under real default settings, `KnowledgeFact`s are essentially never created at all,
for two already-known, already-scoped-elsewhere reasons unrelated to this ticket's own question.

## Step 3: the "name the missing behaviour" test (per peer review's explicit framing)
Applied directly: does an entity ever learn something via a structured query and then behave
differently because of it? Looked for the most concrete, plausible candidate rather than a generic
one.

`KnowledgeFact.fact_type` (`src/core/self_model.py:57`) explicitly includes `"danger_rating"` as a
real, named example — and this is not hypothetical: `src/domains/information/router.py:51,84`
shows real query routing for `kind == "danger_rating"`, and `src/world/providers/
information.py:158-161` shows a real provider constructing a `danger_rating` fact response with a
real numeric value. A player could plausibly expect: *ask a guide how dangerous the east road is,
learn the answer, then avoid or seek that road accordingly.*

Checked for a real, already-existing consumer-shaped hole this could plausibly feed:
`src/cognition/capability_estimate.py`'s `CapabilityContext.region_data`/`.enemy_data` fields are
explicitly typed to hold exactly this shape (`{region_id: {danger_rating}}`,
`{enemy_id: {level, danger_rating}}`) and are read at capability-estimation decision time
(lines 124, 154-155) — but **confirmed via grep that nothing anywhere in `src/` ever populates
either field with real content**; both are permanently empty (`= {}` default, never overridden by
any real call site). This is a second, independent, already-existing "wired-but-unconsumed" pattern
— a real consumer-shaped hole that a `danger_rating` `KnowledgeFact` looks like it should
plausibly feed, and currently cannot, because nothing feeds `CapabilityContext.region_data`/
`.enemy_data` from any source at all, not just not from `KnowledgeFact`.

**But per Step 2, this correspondence is not currently observable in practice.** Since
`KnowledgeFact`s are essentially never created in real default gameplay (the write side itself is
gated off), a player cannot currently observe "learned a road was dangerous, then walked into it
anyway" as a live bug — there is no real danger_rating fact in existence to have been ignored. The
honest answer to the "name the missing behaviour" test, under CURRENT real default settings, is:
**nothing is currently observably missing**, because the feature that would generate the
observable case does not run today.

## Determination
This does not cleanly map to either of the ticket's own two originally-framed outcomes, nor
does it look like peer review's third, newer "two competing memory models" framing — reported in
full to peer rather than picked unilaterally, since the real picture combines pieces of more than
one framing:

1. **Structurally** (code-only, flags aside): confirmed, no decision-time reader for `.facts`
   exists anywhere — the original finding holds precisely.
2. **Practically** (real default gameplay): the write side itself barely runs, for two already-
   known, already-ticketed reasons entirely outside this ticket's own scope
   (`ENABLE_INFORMATION_INTENT_EXECUTION` default-off; `pending_information_responses` never
   threaded in Campaign mode). The reader question is therefore largely moot under current real
   settings — there is rarely a fact in existence to read.
3. **A real, concrete, named candidate consumer exists** (`CapabilityContext.region_data`/
   `.enemy_data`, tailor-shaped for `danger_rating` facts) but it is itself completely unpopulated
   by anything, and there is no explicit design-doc declaration (unlike `JOIN_PARTY`'s own
   `intent_mapping`) stating facts are *meant* to feed it specifically — building that connection
   would be inventing a design decision, not completing a declared one, per peer review's explicit
   constraint.
4. **No observable missing behaviour exists today**, per the explicit test peer review set as the
   real bar — the honest finding, not a proxy for it.

Reported to peer for the disposition call, per the explicit "bring it to me" instruction for any
finding that would require building an undeclared consumer, and per this ticket's own Scope
requiring a design-intent determination with real evidence before choosing a fix path.

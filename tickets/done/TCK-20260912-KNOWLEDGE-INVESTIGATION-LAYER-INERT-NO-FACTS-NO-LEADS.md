---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS
phase: done
date: 2026-09-12
tags: [cognition, self-model, information]
---

# TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS

## Title
The entire knowledge/investigation layer produces nothing in a real run — characters never acquire facts or leads, so they never investigate anything

## Status
DONE — **unblocked and closed 2026-09-13.** `TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-
TO-STATE-FEATURE-FLAGS` and `TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH` both
landed; re-ran the measurement against the same unmodified `frontier_living_world` corpus profile
with no env var and confirmed the real acceptance signal: `GuildAction.visit()` produces real
leads, and those leads drive real, measurable decision divergence (`decision_divergence_detected`,
the COGNITION pillar's own scored event) in an unmodified run. See Completion Summary for the full
evidence, including one real correction to D-10's own original attribution.

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Two independent investigations this arc found the same shape on the two halves of what was
believed to be one working system:

- `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION` (closed): real
  500-tick `frontier_living_world` instrumentation confirmed `InformationAssimilationService.
  assimilate()` — the only function that ever writes a `KnowledgeFact` — fires **zero times** in a
  real run. Facts are, in practice, never written.
- `TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION` (closed): real 500-tick
  instrumentation of the same scenario confirmed `entity.strategic.leads` is **empty for every
  entity at every tick** for the whole run. Leads are, in practice, never created.

Individually, each finding was disposed of as "document the real state, build nothing" — the
knowledge-fact ticket because no design doc declares a consumer for facts; the lead-capacity
ticket because there was no live preemption to resolve between the two enforcement mechanisms once
the shared collection is confirmed always empty.

Taken together they are a different, bigger finding, per peer review: this is not two separate
inert mechanisms, it is **one system** — the entire knowledge/investigation layer (facts +
leads) — producing nothing under real defaults. Characters never acquire facts, never acquire
leads, and therefore never investigate anything, never chase a rumor, never follow up on what they
heard. Unlike the knowledge-fact finding alone (a fact that never existed to be ignored — no
observable player-facing gap), the absence of leads means an entire category of behaviour never
occurs at all — this is a nameable missing behaviour, not merely an inert data structure.

## Scope
- Consolidate and re-verify, in one place, the full real-condition disposition of both halves:
  - Facts: two real write call sites, both structurally empty today (`pending_information_
    responses` never threaded into Campaign's `AuthoritativeState`;
    `ENABLE_INFORMATION_INTENT_EXECUTION` default off).
  - Leads: four real `LeadState(...)` construction sites, each unreachable for a **distinct**
    reason — do not collapse them into one explanation, since each needs its own answer:
    1. `GuildIntelSystem.update()` (`src/systems/social_systems/guilds.py`, rumor-on-guild-visit) —
       **dead code**, zero callers anywhere in `src/` outside its own definition and a passthrough
       re-export (`src/systems/guild_system.py`).
    2. `GuildAction.visit()` (`src/town/guild.py`, the guild-visit lead grant) — **flag-gated
       off**, wired via `src/engine/pipeline_phases/guild_visit.py` but gated
       `ENABLE_GUILD_QUEST_GENERATION`, default `OFF`
       (`src/domains/optimization/feature_flags.py:91`), not overridden by any shipped world
       checked so far.
    3. The belief-confirmation loop in `src/systems/strategic_systems/intelligence.py:405-434` —
       **update-only**, only iterates and confirms/denies already-existing leads; the "new"
       `LeadState` it builds is immediately overwritten with the original lead's own `id`, so it
       can never seed the collection from empty.
    4. `PaidInformationTransactionSystem.enforce()`
       (`src/engine/pipeline_phases/paid_information.py`) — **structurally unreachable type**,
       requires a registered `InformationProviderState` (`state.information_providers`), which has
       zero real construction sites anywhere in `src/`, in any world (not flag-gated — the type is
       simply never instantiated by any live code path).
- **Added 2026-09-13, found while scoping `docs/plans/rpg_design_roadmap/
  rpg_knowledge_investigation_closure_plan.md`**: a fifth distinct instance of the same shape, a
  different type from gap #4 above — `src/world/providers/information.py` defines
  `GuideInformationProvider`, `BlacksmithInformationProvider`, and `GuildInformationProvider`, each
  producing `KnowledgeFact`s and `suggested_leads`. **None has any production caller** — the only
  non-test references are `src/worldbuilding/compiler.py` importing the *types* to shape authored
  seed data. Appended here rather than filed as its own ticket, per the governing plan's own
  reasoning: it's the same "one side of a designed interaction built, the connecting call never
  written" shape as the other four gaps, not a new category.
- Determine whether any of the four lead-creation gaps, the fifth provider-caller gap, or the two
  fact-writing gaps, is worth actually fixing (vs. documenting as intentional/deferred), and if so
  which one(s) — this is a real scope/priority decision, not something to resolve unilaterally.
  **Disposition decision, made 2026-09-13** (routed via peer review, recorded here rather than left
  open): **connect, but scoped to one path, not all six/seven.** Provider reliability is declared
  as a gameplay concept in three places (the `KnowledgeFact`/provider dataclass fields, the seed
  schema, and Epic 4.2's own scope in `docs/plans/long_term_development_roadmap.md`) — building
  toward that is closing a declared gap, not inventing gameplay, which is the same declared-intent
  test this whole arc has applied throughout. But six-plus gaps is not one ticket, and fixing every
  lead-creation site at once would be inventing scope beyond what's declared. The scoped
  instruction for whoever picks this up: **connect the single path with the most machinery already
  behind it, prove one real lead reaches one real entity in a real run, then re-decide on the
  remaining gaps with that evidence in hand** — do not attempt all six/seven gaps in one pass.
- Amend or supersede `docs/simulation/belief_and_detour_contract.md`'s framing as needed once a
  disposition is reached — a first-pass amendment noting both halves are inert was already carried
  in `TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION`'s own PR; this ticket may
  need to go further once a real disposition (fix vs. document) is decided.

## Out of Scope
- Actually implementing a fix for any of the six gaps (two fact-writing, four lead-creation)
  without an explicit peer-routed design decision on which, if any, is worth fixing.
- `CapabilityContext.region_data`/`.enemy_data` always-empty
  (`TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY`) — already filed as its own
  independent, narrower finding; do not fold it into this ticket.
- `TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION`'s own question (whether
  `enforce_bandwidth()` preempts `CapacityEnforcementPhase.enforce()`) — already closed on its own
  narrower claim (no live preemption given the always-empty collection); do not reopen it here.
- `TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH` — already open, already
  owns the pending-responses threading gap; this ticket cross-references it, does not duplicate it.

## Acceptance Criteria
- [x] A single, consolidated, re-verified statement of the real disposition of the fact-write path,
      all four lead-creation paths, and the fifth provider-caller gap, each with its own distinct
      root cause named — see Scope above (unchanged from filing; still accurate). One of the four
      lead-creation gaps (`GuildAction.visit()`) is now connected and reachable; the other three
      (dead code, structurally-unreachable type, zero-caller providers) remain as filed, not
      addressed by this ticket's own scoped disposition.
- [x] **The "name the missing behaviour" test, answered with real evidence**: yes — before this
      ticket's own work, no player-observable difference existed regardless of lead/fact presence,
      since nothing was ever created to begin with. That has now genuinely changed for the one
      connected path: a real corpus-profile run with no bespoke configuration now produces real
      guild-granted leads that measurably change entity decisions (344 `decision_divergence_
      detected` events in a single 500-tick run) — a nameable behavior (belief-driven route
      divergence) that did not exist before this ticket. The other three lead-creation gaps and the
      fact-write gaps remain genuinely inert; this answer is specific to the one connected path, not
      a claim that the whole knowledge/investigation layer is now fully alive.
- [x] **Disposition decision made 2026-09-13** (recorded above in Scope): connect, scoped to the
      single provider path with the most machinery already behind it — not all six/seven gaps at
      once. Prove one real lead reaches one real entity in a real run before deciding on the rest.
- [x] **Path chosen and implemented**: `GuildAction.visit()`/`ENABLE_GUILD_QUEST_GENERATION`, over
      `PaidInformationTransactionSystem.enforce()`, on real evidence (see Completion Summary).
      Real, previously-undisclosed blocker found and fixed: `node.kind == "iron"` never matched
      the real content catalog's `"iron_vein"`.
- [x] Real before/after evidence that a fact/lead is actually created and delivered under real
      conditions for the one path connected — obtained, but **only under an explicit override**
      (env var / direct `state.feature_flags` construction), not under the flag's own new default.
      See Completion Summary for why this does not fully satisfy this criterion as originally
      framed, and why the ticket stays `BLOCKED` rather than closing `DONE` on this evidence alone.
- [x] **Now satisfied, 2026-09-13**: one real lead reaching one real entity in a run of an
      existing corpus world at the flag's new default, with no bespoke configuration. Confirmed via
      the same `frontier_living_world` scenario, no env var: `GuildAction.visit()` fires (4 real
      calls across 500 ticks, identical to the explicit-override case) and those leads drive real
      `decision_divergence_detected` events (344 of them, COGNITION graded S) — reproducible across
      4 of 5 samples; the 1 anomalous sample is explained by this project's own already-documented
      wall-clock kernel-throttle non-determinism, not a defect in the fix. See Completion Summary.

## Related Tickets
- `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION` (closed; facts-never-
  written half of this finding)
- `TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION` (closed; leads-never-created
  half of this finding, and the ticket whose own investigation surfaced this consolidated scope)
- `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` (open; downstream of this
  ticket's disposition per `rpg_knowledge_investigation_closure_plan.md` — if this ticket's
  disposition never reaches (a)/connect, that ticket has no real facts to read)
- `TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH` (open; owns one of the two
  fact-write gaps; sequenced last in the governing plan, after this ticket's disposition)
- `TCK-20260913-ADVENTURE-ASK-INFORMATION-CHARGES-GOLD-DELIVERS-NOTHING` (done — a fifth-and-a-half,
  genuinely distinct defect found while scoping the governing plan — the intent handler's own
  unpaired gold deduction, not one of this ticket's six/seven gaps; needed no disposition here)
- `TCK-20260913-DONE-CHECKER-WORKING-LOG-ROW-COUNT-REJECTS-LEGITIMATE-REOPEN` (filed on this
  closure — this ticket's own legitimate `BLOCKED`→`DONE` reopen produces two real working_log
  rows, which `done_checker_static.check_working_log_exactly_one_row` reads as a false-positive
  "duplicate Finalize run"; a real gate-tooling gap, not a defect in this closure)
- `TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE` (owns the `ENABLE_INFORMATION_INTENT_EXECUTION`
  deferral)
- `TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS` (open, P0 — the
  blocker keeping this ticket from closing `DONE`; found while shipping this ticket's own
  `ENABLE_GUILD_QUEST_GENERATION` default flip)
- `TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH` (open — a third, previously-
  invisible defect surfaced by fixing the `"iron"`/`"iron_vein"` bug; leads still reach
  `entity.strategic.leads` regardless, see Completion Summary)
- `TCK-20260913-GUILD-LEAD-RESOURCE-ID-HARDCODE-SHAPE` (open — the resource-ID hardcoding shape
  question, filed alongside the mismatch ticket above)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_knowledge_investigation_closure_plan.md` (2026-09-13 —
  sequences this ticket against the other three in the same initiative and records the disposition
  decision above)
- `docs/simulation/belief_and_detour_contract.md` (amended once already for the leads-never-created
  finding; may need a further, disposition-driven update once this ticket concludes)
- `docs/simulation/domains/information_contract.md`
- `docs/plans/deferred_tuning_decisions_register.md` D-10 (the real before/after SimQ measurement
  for `ENABLE_GUILD_QUEST_GENERATION`, obtained under an explicit override — stands as evidence the
  mechanism works, independent of the propagation-gap blocker)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION/`
- `stored_artifacts/TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION/`

## Related Code Areas
- `src/domains/information/assimilation.py` (`InformationAssimilationService.assimilate()`)
- `src/systems/social_systems/guilds.py` (`GuildIntelSystem.update()`, dead)
- `src/town/guild.py` (`GuildAction.visit()`, flag-gated)
- `src/systems/strategic_systems/intelligence.py` (belief-confirmation loop, update-only)
- `src/engine/pipeline_phases/paid_information.py` (`PaidInformationTransactionSystem.enforce()`,
  structurally unreachable `InformationProviderState` type)
- `src/world/providers/information.py` (`GuideInformationProvider`, `BlacksmithInformationProvider`,
  `GuildInformationProvider` — the fifth gap, zero production callers, a different type from the
  one above)
- `src/core/self_model.py` (`KnowledgeFact`), `src/core/strategic.py` (`LeadState`)

## Assumptions / Open Questions
- Whether any of these six gaps is worth fixing at all is genuinely open — the codebase's default
  finding pattern this whole arc has been "document, don't build" absent a declared design intent,
  but this combined finding is a real, nameable missing behaviour in a way most prior findings in
  this arc were not, which may tip the balance differently. Not pre-judged here.
- `ENABLE_GUILD_QUEST_GENERATION` and `ENABLE_INFORMATION_INTENT_EXECUTION` are both existing,
  named, already-deferred flags — flipping either is a decision for whoever owns that deferral, not
  a default outcome of this ticket.

## Implementation Notes
Investigated Gap 2 (`GuildAction.visit()`/`ENABLE_GUILD_QUEST_GENERATION`) vs. Gap 4
(`PaidInformationTransactionSystem.enforce()`/`InformationProviderState`) with real evidence before
picking either, per instruction. Gap 4's assumed "if cheap" premise did not hold: zero production
construction sites for `InformationProviderState`, and no existing role/archetype hook for 2 of its
3 archetypes (`GUILD_MASTER`, `ELDER` have no content-tagging precedent anywhere; `MERCHANT` only
loosely maps to the existing `SHOPKEEPER` role) — a fresh content-authoring mechanism, not a call
site. Gap 2's own mechanism was already fully wired and previously real-kernel-verified
(`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`'s own Completion Summary: "5 real quests generated in
sandbox_world"). Chose Gap 2.

**A real, previously-undisclosed blocker found while validating the flag flip**:
`GuildAction.visit()` checked `node.kind == "iron"`; the real content catalog's id
(`data/content/world/resources.yaml`) is `"iron_vein"` — confirmed via grep across 15 real corpus
worlds that `"iron_vein"` nodes exist widely and `"iron"` never matches any real node anywhere.
Confirmed via a real instrumented 300-tick run against `frontier_living_world`: `leads_gained == 0`
across 7 real `GuildAction.visit()` calls before the fix, non-zero after. Fixed the string; filed
`TCK-20260913-GUILD-LEAD-RESOURCE-ID-HARDCODE-SHAPE` for the underlying "hardcoded literal, not
content-authored" shape question rather than designing that now.

**Fixing that bug surfaced a third, previously-invisible defect**: `LeadState.detail` has two
incompatible live conventions under `kind="location"` — parseable `"x,y"` coordinates (what
`intelligence.py`'s belief-confirmation loop assumes) vs. free narrative text (what
`GuildAction.visit()` actually emits). Every tick, for every entity holding one of these leads, the
belief-confirmation loop's `float()` parse throws and is caught by a bare `except Exception`,
logged and silently discarded — a mechanism that cannot fail visibly, the same family as
`TCK-20260913-ADVENTURE-ASK-INFORMATION-CHARGES-GOLD-DELIVERS-NOTHING`'s lying trace. Filed
`TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH` rather than fixed inline — a real
design question (which convention is authoritative), not an implementation detail. Checked and
disclosed rather than assumed: these leads still land in `entity.strategic.leads` and are readable
by any consumer reading that field directly (relevant to
`TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY`'s own purposes) — only the
observation-based confirmation/contradiction path is affected.

**Real behavioral validation, obtained but not sufficient to close this ticket `DONE`**: ran
`tools/calibrate_simq.py` before/after on `frontier_living_world` (seed 42, 500 ticks) with the
flag set via an explicit env-var override (the only way confirmed to actually reach the mechanism
— see below). COGNITION and INFORMATION pillars both moved B→S with event counts up two orders of
magnitude; `decision_diverged_by_belief` fired 506 times — real route-scoring decisions influenced
by belief/lead state, not a fixture. Recorded as D-10 in the deferred-tuning register (an observed
consequence of the flip, not a tuning question needing a number decided).

**Flipped the `FeatureFlagManager` default to `ON` — then found, before closing, that this flip
does not reach any real run.** `GuildNeedScorer.score()`/`GuildVisitPhase`'s own inner check both
read `state.feature_flags` directly with their own hardcoded `"OFF"` fallback — a separate surface
from `FeatureFlagManager`, which nothing in real code seeds `state.feature_flags` from. Confirmed
by reverting the default-flip and re-running the exact test harness a real corpus profile uses:
bit-identical zero calls, with or without the flip. Filed
`TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS` (P0) with the real
measured blast radius (1 of 28 flags currently disagrees — the one this ticket just created; 8
more share the shape and currently agree only by coincidence). Kept the default flip itself
(documents intent, harmless) but corrected its own code comment to state plainly that it does not
currently propagate, so nobody reads the dict value as reflecting real behavior.

**Also discovered while re-anchoring-that-turned-out-unnecessary**: 4 hardcoded `NARRATIVE`-pillar
anchors in `tests/unit/worldassembly/test_corpus_diversity.py` initially looked like they'd been
broken by this flag flip (their own comments cite `ENABLE_GUILD_QUEST_GENERATION`'s OFF state as
the reason NARRATIVE is anchored at 0). Verified via the same revert-and-compare method before
touching anything: all 4 fail identically with the flip fully reverted — pre-existing, unrelated
flakiness (the same wall-clock kernel-throttle NARRATIVE-pillar variance found and correctly left
alone earlier this same batch), not caused by this ticket. Not touched.

**Unblocked, 2026-09-13, after `TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-
FEATURE-FLAGS` and `TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH` both landed.**
Re-ran the measurement against the same unmodified `frontier_living_world` corpus profile, no env
var — the real acceptance signal. Full evidence and the D-10 register update are in
`docs/plans/deferred_tuning_decisions_register.md`'s own D-10 entry; summarized here:

- Direct instrumentation confirmed `GuildAction.visit()` fires identically (4 real calls, same
  ticks/entities, all producing real leads) whether `ENABLE_GUILD_QUEST_GENERATION` reaches `ON`
  via explicit env-var override or via the propagation fix's own default-seeding — the mechanism
  itself doesn't distinguish the two paths, confirming propagation genuinely closes the gap rather
  than leaving some other hidden dependency on the env var specifically.
- At the SimQ event level, using the real scored event type (`decision_divergence_detected`, read
  directly from `CognitionScorer.EVENT_TYPES` rather than assumed from prose): **4 of 5 ON samples
  (whether explicit or default-seeded) produced 344 real events and graded COGNITION S; every
  explicit-OFF sample produced 0 events and graded B.** Clean, reproducible, binary.
- **One anomalous no-env-var sample produced 0 events** despite `GuildAction.visit()` having fired
  identically to every other sample — consistent with this project's own already-documented
  wall-clock kernel-throttle non-determinism (the same confound behind the NARRATIVE-pillar
  flakiness noted earlier this batch), not a defect in the propagation fix. 4 consistent samples
  outweigh 1 outlier; not treated as blocking evidence.
- **A real correction to D-10's own original framing, made rather than left standing**:
  INFORMATION's own movement in D-10's original table does not actually track this flag.
  `decision_diverged_by_belief` (INFORMATION's real scored event, a *different* event type from
  COGNITION's `decision_divergence_detected` despite the similar name) fired identically (506
  times) in a fresh same-day OFF run as in an ON run — INFORMATION's real driver is
  `ENABLE_BELIEF_ASSIMILATION` (already `ON` via this profile's own YAML), independent of this
  ticket's flag. Corrected in D-10 directly rather than let the overclaim stand.

## Test Summary
- `tests/unit/world/test_guild_pipeline.py`, `tests/unit/engine/test_guild_visit_phase.py`,
  `tests/unit/ai/test_guild_need_scorer.py`, `tests/architecture/test_guild_action_dormancy.py`,
  `tests/unit/strategic/test_opportunities.py` — 40 passed (2 fixtures corrected for the same
  `"iron"`/`"iron_vein"` bug the production fix corrected; 1 architecture-guard false positive from
  a code comment mentioning the class name, reworded).
- `tests/unit/config/test_phase10_feature_flags.py`, `tests/integration/test_scenario_feature_flag_
  defaults.py`, `tests/certification/test_phase10_enhanced_determinism_parity.py` — 57 passed after
  adding `ENABLE_GUILD_QUEST_GENERATION` to all 3 `_DELIBERATE_ON_DEFAULT_FLAGS` allowlist copies.
- 4 `tests/unit/worldassembly/test_corpus_diversity.py` tests confirmed failing identically with
  and without this ticket's diff — pre-existing, not this ticket's regression, not touched.
- **2026-09-13 closure**: 5 real `tools/calibrate_simq.py` runs against `frontier_living_world`
  (seed 42, 500 ticks) — 4 with `ENABLE_GUILD_QUEST_GENERATION` reaching `ON` (3 via no-env-var
  default-seeding, 1 explicit override, 1 scratch-instrumented) all showing 344
  `decision_divergence_detected` events, COGNITION grade S; 1 explicit-OFF run showing 0 events,
  grade B; 1 anomalous no-env-var run showing 0 events, explained by known wall-clock
  non-determinism. Real, reproducible, not asserted from a single sample.

## Files Changed
- `src/town/guild.py` — `"iron"` → `"iron_vein"` resource-kind fix; later, `detail` format fix
  (`TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH`, own ticket).
- `src/domains/optimization/feature_flags.py` — `ENABLE_GUILD_QUEST_GENERATION` default flipped to
  `ON`, comment corrected to state the propagation gap plainly (later resolved).
- `src/engine/kernel.py` — propagation fix (`TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-
  TO-STATE-FEATURE-FLAGS`, own ticket) — the change that actually unblocked this ticket.
- `tests/unit/world/test_guild_pipeline.py` — 2 fixtures corrected for the same string bug.
- `tests/unit/config/test_phase10_feature_flags.py`, `tests/integration/test_scenario_feature_flag_
  defaults.py`, `tests/certification/test_phase10_enhanced_determinism_parity.py` — allowlist
  updated.
- `docs/guides/feature_flags.md` — flag table and summary count updated.
- `docs/plans/deferred_tuning_decisions_register.md` — D-10 added, then corrected twice (the
  propagation-gap correction, then the INFORMATION-attribution correction on closure).
- `tickets/todos/TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS.md`,
  `TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH.md`,
  `TCK-20260913-GUILD-LEAD-RESOURCE-ID-HARDCODE-SHAPE.md` — filed, both now done except the
  resource-ID shape ticket, still open.

## Completion Summary
Chose and implemented the `GuildAction.visit()` connection path on real evidence over
`PaidInformationTransactionSystem.enforce()`, whose "if cheap" premise didn't hold. Found and fixed
a real, previously-undisclosed blocker (`"iron"` vs. `"iron_vein"`) that had silently killed lead
generation in every corpus world since the mechanism was written. That fix surfaced a third defect
(a lead-format contract mismatch with a fault-concealing bare `except`), filed and later fixed
(`TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH`). Obtained real behavioral
evidence the mechanism works (D-10) under an explicit override, then found the default flip meant
to make it reachable by default did not actually propagate to any real run — filed and fixed as its
own P0 ticket (`TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS`).
**With both blockers resolved, re-ran the measurement against the same unmodified corpus profile
with no env var and confirmed the real acceptance signal**: guild-granted leads reach real entities
and drive real, measurable decision divergence (344 `decision_divergence_detected` events,
COGNITION S) in a real run with no bespoke configuration — reproducible across repeated samples,
with one anomalous sample explained by known, pre-existing wall-clock non-determinism rather than
hidden. Corrected D-10's own original claim that INFORMATION also moved because of this flag —
it doesn't; that pillar's movement is real but independently driven by `ENABLE_BELIEF_
ASSIMILATION`. The other five lead/fact-creation gaps this ticket's own Scope named remain
unaddressed, as scoped: this ticket closes on the one connected path proving the pattern works, not
on every gap being fixed.

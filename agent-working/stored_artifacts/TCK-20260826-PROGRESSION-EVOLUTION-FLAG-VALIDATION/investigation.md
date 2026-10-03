---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION
artifact_type: investigation
tags: [feature-flags, progression]
---

# Investigation — TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION

## Method
Context search per CLAUDE.md was already run by the orchestrator this session before dispatch:
`mcp__knowledge-search__search_docs` returned "index not found" (the knowledge index isn't built in
this worktree — a pre-existing environment gap unrelated to this ticket) and
`graphify query "ENABLE_PROGRESSION_EVOLUTION ProgressionConversionPhase"` returned 61 nodes rooted
at `src/domains/progression/phase.py:23`. This investigation reads every file graphify surfaced
plus the flag registration, gate site, all 9 `src/domains/progression/*.py` service modules, every
test file that references the flag or the Phase-6 domain logic, `docs/guidelines/
intentional_divergences.md` DEV-002/003/004 in full, `docs/parity_ledger/progression.yaml`,
`config/simulation_quality/corpus_registry.yaml`, and the 3 sibling M1 flag-validation tickets'
stored trial evidence for format precedent.

## Current Behavior

**Gate site**: `src/engine/pipeline.py:343` — `run_phase("progression_conversion", update, lambda
u: ProgressionConversionPhase.execute(state, u), "ENABLE_PROGRESSION_EVOLUTION")`. `run_phase`
(`src/engine/pipeline.py:102-132`) reads the flag via `FeatureFlagManager.get_flag_mode(...)`; if
`FeatureMode.OFF` the phase is skipped entirely (`metric_counters["skip_progression_conversion"]`
incremented, `upd` returned unmodified) and `phase_fn` (i.e. `ProgressionConversionPhase.execute`)
is never called. This is the real, live gate.

**Flag registration**: `src/domains/optimization/feature_flags.py:47` —
`"ENABLE_PROGRESSION_EVOLUTION": FeatureMode.OFF`, with an inline comment confirming the deferral
and naming this exact ticket as the follow-up. No shipped `config/simulation_quality/profiles/
*.yaml` sets this flag (grep across all 19 profile files: zero matches) — confirmed no production
evidence exists today, matching the parent ticket's finding.

**`ProgressionConversionPhase.execute`** (`src/domains/progression/phase.py:28-92`): for every
active, alive entity, runs a 6-step pipeline: `PossessionUnderstandingService.evaluate` →
`GrowthGapEvaluator.evaluate` → `RewardInterpretationService.interpret` →
`ConversionOptionGenerator.generate` → `ConversionDecisionService.select` →
`ConversionIntentResolver.resolve`, then stores the raw `ProgressionDecisionResult` object into
`property_updates["last_progression_decision"]` (a non-typed, free-form property slot — see Risks).

**Secondary, vestigial internal gate**: `phase.py:35` — `feature_flag = getattr(state,
"progression_conversion_enabled", True)`; if `False`, the phase no-ops. This attribute is never
set on `AuthoritativeState` anywhere in `src/` (confirmed by grep) — its only 2 uses are
`phase.py`'s own read and one test
(`tests/integration/domains/progression/test_phase6_progression_conversion_phase.py`) that
manually subclasses `AuthoritativeState` to set it `False`. In every real pipeline run this
attribute is absent, so `getattr(..., True)` always resolves `True` and this internal check is a
no-op dead branch — the actual gating is entirely `run_phase`'s `ENABLE_PROGRESSION_EVOLUTION`
check at the pipeline level. Not a bug to fix in this ticket (out of scope — no behavior change
requested), but worth naming because it could confuse a future reader into thinking there are two
independent gates that both need flipping.

**The single most load-bearing finding of this investigation — the reward ledger is never
populated in any real pipeline run**: `phase.py:48-51` reads `entity.identity.properties.get(
"reward_ledger")`; if absent, it creates a fresh, empty `RewardLedgerComponent()` in local memory
only. `RewardLedgerService` (`src/domains/progression/ledger.py`, the utility class with
`record_entry`/`mark_consumed` that would append real XP/gold/item events into the ledger) has
**zero callers anywhere in `src/`** (confirmed by grep for `RewardLedgerService` and for
`RewardEntry(`/`RewardLedgerComponent(` construction outside `schema.py`/`ledger.py`/tests). No
phase that actually grants XP, gold, or items (`quest_rewards`, `resource_transactions`,
`evolution`, `governance_ecology`, etc. — `src/engine/pipeline.py:319-338`) ever calls
`RewardLedgerService.record_entry`. Additionally, `phase.py` itself never writes the (possibly
freshly-created) ledger back into `entity.identity.properties` — there is no `IdentityUpdate`
carrying an updated `reward_ledger` anywhere in `phase.py`'s output. So even if something did
populate the ledger once, nothing persists incremental changes tick-over-tick either.

Net effect: in a real `Kernel`/pipeline run, `ledger.entries` is **always empty**. Tracing the
consequences downstream:
- `RewardInterpretationService.interpret` (`interpretation.py:48`) iterates `ledger.entries` —
  empty input produces `meanings=()`.
- `ConversionOptionGenerator.generate` (`generator.py:35`) only adds non-fallback options by
  iterating `interpretation.meanings` — empty input means **only the `SAVE_FOR_LATER` fallback
  option is ever generated**, regardless of the entity's real gaps (weapon/repair/material/gold/AP).
- `ConversionDecisionService.select` therefore always selects `SAVE_FOR_LATER`.
- `ConversionIntentResolver.resolve` (`resolver.py:32-104`) has no `elif` branch for
  `ConversionKind.SAVE_FOR_LATER` — it falls through the whole if/elif chain and returns the
  untouched `EntityUpdate(entity_id=entity.id)` initialized at the top of the function (a genuine
  no-op).

**This means that even with the flag flipped ON, `ProgressionConversionPhase` is very likely to
produce zero real entity mutations in any live corpus trial today** — not because the phase is
broken in isolation (its unit-level logic is deep and correct per the Phase-6 test suite, see Test
Coverage Depth Assessment below), but because its only real input feed (the reward ledger) has no
live producer wired anywhere in the pipeline. `GrowthGapEvaluator` does compute real gaps directly
from entity state (equipment/inventory/gold/unspent_ap — not ledger-dependent), but those gaps only
ever surface as `dominant_gap`/severity metadata; they do not by themselves cause
`ConversionOptionGenerator` to emit a non-fallback option, since option generation is driven by
`interpretation.meanings`'s `suggested_conversion_tags`, which is itself entirely ledger-driven.

**Direct consequence for DEV-004's `ALLOCATE_AP` divergence**: `ConversionOptionGenerator` only
emits a `ConversionKind.ALLOCATE_AP` option when an interpretation meaning carries the `"allocate"`
tag, and the only place that tag is ever produced is `RewardInterpretationService.interpret`'s
XP-kind branch (`interpretation.py:108-113`, unconditional on any ledger XP entry existing). Since
the ledger is never populated with XP entries in live runs, `resolver.py:82-89`'s `ALLOCATE_AP`
branch (the DEV-004 zero-attribute-delta divergence) is very likely **not just gated OFF by the
feature flag today, but additionally unreachable even if the flag were ON**, for the separate,
independent reason that its only trigger path (a ledger XP entry) has no live producer. This is a
new finding beyond what `test_allocate_ap_dormancy.py` proved (that test only proves the branch is
dormant while the flag is OFF over a real 150-tick kernel loop against `sandbox_world`; it does not
and cannot speak to what happens if the flag were flipped ON, since it never flips it).

## Mechanics / Engine Constraints
No `docs/mechanics/` chapter directly governs the progression-conversion decision logic (item
keep/sell/equip/craft/repair prioritization, personality-weighted option scoring) — this is a
Phase-6/Phase-10-era subsystem built after the Mechanics Bible chapters were certified, and none of
chapters 01-06 describe a "reward conversion" mechanic. `docs/mechanics/01_entity_anatomy.md`
covers XP scaling and attribute points generically (the source of `unspent_ap`, which
`GrowthGapEvaluator` reads directly), but does not describe how AP gets *spent* — that remains
entirely undocumented mechanics, consistent with `ALLOCATE_AP` being a decided-dormant divergence
(DEV-004) rather than a certified law. `docs/engine/known_limitations.md` §1.5 (referenced by
`test_scenario_feature_flag_defaults.py`) documents the DEV-002 all-flags-default-OFF policy this
flag falls under — that is the one binding engine-contract constraint directly on point: this flag
must not be flipped ON without going through the same real-evidence bar the other M1 rollout
decisions used.

## Docs Requiring Update
- `docs/architecture/rollout_flag_decisions_m1.md`: the `ENABLE_PROGRESSION_EVOLUTION` row (current
  line ~32, "Kept OFF, deferred — No production evidence...") must be replaced with a "Kept OFF,
  deferred (real trial evidence now on file)" row matching the 3 sibling rows above it, plus a new
  `## ENABLE_PROGRESSION_EVOLUTION — Validation Trial Result (TCK-20260826)` section appended
  after the existing `ENABLE_WORLD_EMERGENCE` section (before `## RolloutProfileManager — Cut`),
  matching that section's format (commands run, world-loading confirmation, evidence tally table,
  no-suppression check, honest-gap disclosure) — this is produced during Implement once the real
  trial is run, not by this investigation.

No other doc requires updating as part of this ticket. `docs/guidelines/intentional_divergences.md`
(DEV-002/DEV-003/DEV-004) is directly relevant background but this ticket's own scope is explicitly
"keep OFF, produce evidence" — it does not flip the flag's default (Out of Scope, ticket body), so
DEV-003's flag-default-changes ledger does not get a new entry from this ticket, and DEV-004's
existing text already correctly cites this ticket by ID as its own not-yet-run follow-up (no edit
needed there either — it already accurately reflects "not yet run", and this ticket does not change
that decision). `docs/parity_ledger/progression.yaml` is examined below (Parity Ledger Overlap) but
no entry there is scoped to change by a keep-OFF, evidence-only ticket — flipping that would only
be warranted if this ticket's Implement phase surfaces a real behavioral divergence from a
Mechanics Bible law, which none of chapters 01-06 currently define for this subsystem (see
Mechanics/Engine Constraints above).

## Parity Ledger Overlap
`docs/parity_ledger/progression.yaml` has no entry directly scoped to
`ProgressionConversionPhase`'s own decision logic (possession/gaps/interpretation/generator/
selector/resolver) — the closest entries are:
- **PROG-116** (status `verified`, priority P1): "When `unspent_ap` decreases between ticks,
  `EventExtractor` emits `progression_conversion_applied`..." — this is the *observability* hook
  that would fire if `resolver.py`'s `ALLOCATE_AP` branch ever executed for real. Since that branch
  is unreachable today (both by the flag being OFF and, per the finding above, independently by the
  empty reward ledger), this event has no live emission path from the conversion phase in the
  current corpus. Verified/correct as written; not something this ticket needs to change.
- **PROG-068 / PROG-069** (status `divergent`, priority P0): both about `src/engine/domain/
  core_actions.py::execute_allocate_ap` — the *other*, `ActionRouter`-reachable AP-allocation path
  (a sibling dormant branch per DEV-004, distinct from this flag's `resolver.py` branch). Same
  underlying "AP spend grants zero attribute delta" family of bug, different call site, not gated
  by `ENABLE_PROGRESSION_EVOLUTION`. Flagged here for completeness/cross-reference only — not this
  ticket's flag, not this ticket's scope to fix, and DEV-004 already documents both branches as a
  single decided-dormant decision.
- No P0 entry exists whose `status` would newly require a passing `test_path` as a direct result of
  this ticket's evidence-gathering work (this ticket does not flip the flag's default).

## Prior Work
- `stored_artifacts/TCK-20260824-ROLLOUT-FLAG-DECISIONS/investigation.md` — the parent ticket that
  first confirmed the "Progression Conversion" M1-epic-prose maps to `ENABLE_PROGRESSION_EVOLUTION`
  (its own §"SELF_MODEL_COGNITION, WORLD_EMERGENCE, PROGRESSION_EVOLUTION, INFORMATION_INTENT_
  EXECUTION" section, and its Decision table row) and deferred this flag with "No production
  evidence" as the stated reason — this ticket's whole job is to produce that evidence.
- `stored_artifacts/TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION/trial_evidence.md` and
  `stored_artifacts/TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION/trial_evidence.md` — precedent
  shape for the trial evidence artifact this ticket's Implement phase must produce: a 4-leg (2
  worlds x OFF/ON) real `tools/calibrate_simq.py` corpus trial, with a metric-counter evidence
  table, an explicit no-suppression check (comparing ON vs OFF signal collapse), and an honest
  disclosure section when real activity signal is thin (both sibling trials disclosed this rather
  than smoothing it over — this ticket's trial is very likely to need the same honesty given the
  reward-ledger finding above).
- This ticket is referenced by DEV-004's own text (as `tickets/todos/TCK-20260826-PROGRESSION-
  EVOLUTION-FLAG-VALIDATION.md`, its path at the time DEV-004 was written) as "already-filed,
  not-yet-run" — now `tickets/inprogress/TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION.md`.
  Confirms this ticket's identity and scope are already cross-referenced from the divergences doc;
  no naming or scope drift found.
- `docs/parity_ledger/substrate.yaml::SUB-376` and `docs/event_ledger/entity.yaml::ENTITY-008` are
  cited by DEV-004 as the original reachability investigation for the `ALLOCATE_AP` dormancy — not
  re-read in full here since DEV-004 already ratifies their conclusion and this ticket does not
  need to re-derive it, only extend it with the reward-ledger finding above.

## Candidate World/Seed for the Implement-Phase Trial
Not run here — for the Implement phase to execute, following the sibling tickets' 2-world/4-leg
(OFF/ON x2) format. `config/simulation_quality/corpus_registry.yaml`:
- **Primary candidate: `dungeon_crawl`** (archetype `monster_only_gauntlet`, 32 entities, tier
  `end_to_end`, run_keys already covering seeds 42/123/456 at 200/500/1000/2000 ticks). This is the
  same world `TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION`'s trial used and is the best-fit
  archetype here too: a monster-only combat gauntlet is precisely the setting most likely to grant
  entities XP, gold, and loot drops (combat rewards) and to stress equip/repair decisions (weapon
  damage from repeated fights) — exactly the inputs `GrowthGapEvaluator`/`PossessionUnderstanding
  Service` read directly from entity state (independent of the reward-ledger gap). Recommend `seed
  42`, `2000` ticks, matching the sibling `COMBAT_ENGAGEMENT`/`WORLD_EMERGENCE` trials' own tick
  budget for direct comparability.
- **Secondary candidate: `crowded_frontier` or `frontier_extended`** (both `civilian_settlement`,
  higher `quest_density`/`resource_density` than `dungeon_crawl`) as the second OFF/ON leg — a
  civilian-settlement world exercises quest-reward gold/item grants and crafting-recipe gold gaps
  (`GrowthGapEvaluator`'s `material_gap`/`gold_gap` checks) that a monster-only gauntlet under-
  represents, giving the 2-world trial some archetype diversity the way the sibling trials paired a
  combat-heavy world with a non-combat one.
- Whichever world(s) are chosen, the trial run should also capture `metric_counters
  ["run_progression_conversion"]`/`["skip_progression_conversion"]`, any `item_equipped`/
  `item_unequipped`/`equipment_durability_changed`/`progression_conversion_applied` events, and the
  distribution of `last_progression_decision` values across entities (ideally by sampling a handful
  of entities' final `property_updates` or an equivalent trace) — the last one is the single most
  direct way to confirm or refute the "converges entirely on SAVE_FOR_LATER" prediction above.

## Risks and Open Questions
- **Open question (does not block Implement, but must shape how the trial's result is read)**: if
  the real corpus trial shows near-zero effect (all entities converging on `SAVE_FOR_LATER`,
  `run_progression_conversion` metric counter nonzero but no non-trivial `EntityUpdate` content, no
  `equip_item`/`item_unequipped`/`equipment_durability_changed`/`progression_conversion_applied`
  events beyond baseline), that result must **not** be reported as "flag is safe to flip ON, no
  observed risk" — the correct honest reading is "the trial could not exercise the phase's real
  decision space because its only input feed (`reward_ledger`) has no live producer; the flag's
  *wiring* is safe (no crash, no suppression of other phases), but its *behavioral* safety under
  real reward flow remains genuinely untested." This distinction must be preserved explicitly in
  the trial evidence doc and the final keep/flip recommendation, not collapsed into a blanket
  "clean pass."
- **Open question**: would populating the reward ledger (wiring `RewardLedgerService.record_entry`
  into `quest_rewards`/`resource_transactions`/`evolution`) be a prerequisite fix needed before a
  trial can produce meaningful evidence, or is a "flag ON, ledger empty, mostly no-op" trial still
  useful evidence in its own right (proves at minimum: no crash, no suppression, bounded perf under
  the existing perf-budget test)? This ticket's Scope explicitly excludes "writing new test coverage
  beyond what's needed to trust the trial itself" and Out of Scope excludes "flipping the flag's
  default" — wiring a new ledger producer would be new production logic, arguably out of scope for
  an evidence-gathering chore ticket. Recommendation: run the trial as-is first (it is still real,
  informative evidence — confirms wiring safety even if it can't confirm decision-logic safety
  under load), and explicitly flag the ledger-producer gap as a **named blocking prerequisite for
  any future flip-ON decision**, not something this ticket should silently work around by hand-
  seeding ledger entries into a real corpus world (which would not be a real trial, just another
  unit-style test).
- **Risk**: `property_updates["last_progression_decision"]` stores a raw `ProgressionDecisionResult`
  dataclass instance (not a typed, serializable durable-state field) directly into an entity's
  free-form `properties` dict. This looks adjacent to the project's Durable State Rule ("Do not
  store durable meaning in ... free-form `metadata`"), but is pre-existing behavior unrelated to
  this ticket's evidence-gathering scope — flagged for awareness, not something to fix here (fixing
  it would be new production logic changing the phase's contract, matching the same "not this
  ticket's job" reasoning as the ledger-wiring question above).

## Anti-Drift Hazards
- **Do not wire a real `RewardLedgerService` producer into `quest_rewards`/`resource_transactions`/
  `evolution`** as part of this ticket to "make the trial show real activity" — that is new
  production logic outside this ticket's explicit "Out of Scope: Actually flipping the flag's
  default" / evidence-gathering framing, and the ticket's Acceptance Criteria only ask for an honest
  assessment plus a real ON trial, not a fix to make the trial look more interesting.
  Also, this is exactly the shape of "quietly fixing an underlying gap to make a check/trial look
  clean" that the project's Gate Integrity rule warns against, generalized: report the empty-ledger
  finding honestly as a limitation of the trial's evidentiary value, don't paper over it.
- **Do not hand-construct a `RewardLedgerComponent` with fake entries directly into the trial
  world's entity state before running `calibrate_simq.py`** — that would defeat the entire purpose
  of a *real* corpus trial (indistinguishable from the existing `test_phase6_progression_conversion_
  scenarios.py` unit-style tests, which already do exactly this in isolation). The trial must run
  against the corpus world's actual, organically-evolving state — that is the entire evidentiary
  value this ticket adds on top of the existing hand-seeded unit/scenario tests.
- **Do not conflate this ticket's flag (`resolver.py`'s `ConversionKind.ALLOCATE_AP` branch, gated
  by `ENABLE_PROGRESSION_EVOLUTION`) with the sibling dormant `core_actions.py::execute_allocate_ap`
  branch (gated by nothing — it's simply never invoked, per DEV-004)** — PROG-068/069 are about the
  latter. A trial of this flag does not and cannot exercise or fix PROG-068/069.
- **Do not treat `test_scenario_feature_flag_defaults.py`'s passing default-OFF assertions as
  evidence about the phase's behavior when ON** — that file (and `_DELIBERATE_ON_DEFAULT_FLAGS`)
  only proves the *default* is correctly OFF; it says nothing about safety if flipped, and must not
  be cited in the trial evidence doc as behavioral coverage.

## Test Coverage Depth Assessment

The ticket's own Scope explicitly demands this be assessed honestly, not assumed. Splitting the
relevant test surface into the two categories the task requires:

### (a) Dormancy / gating-mechanics-only coverage
- `tests/integration/test_scenario_feature_flag_defaults.py` — asserts `ENABLE_PROGRESSION_EVOLUTION`
  defaults to `FeatureMode.OFF` across every loaded scenario and that `FeatureFlagManager` instances
  are stable/isolated. Constructs `FeatureFlagManager()` directly; never touches
  `ProgressionConversionPhase`, `pipeline.py`, or any progression domain service. Pure gating-default
  scaffolding — would pass identically whether or not the phase's internal logic were entirely
  broken. Exactly matches the ticket description's characterization ("default-off allowlist
  scaffold test, not real behavioral coverage").
- `tests/unit/observability/test_event_extractor_equipment.py` — its docstring *references*
  `ENABLE_PROGRESSION_EVOLUTION` (explaining why real-kernel verification was abandoned in favor of
  hand-built states), but the tests themselves call `EventExtractor.extract()` directly against
  hand-constructed before/after `AuthoritativeState` pairs — they never call
  `ProgressionConversionPhase`, `ConversionIntentResolver`, or go through the pipeline at all. This
  is not gating coverage either; it is unrelated event-diffing coverage that happens to explain, in
  prose, why it *isn't* testing the flag's real code path. Of the ticket's named "2 test files that
  literally reference the flag name," this one is the weaker of the two — a comment, not a
  behavioral or gating assertion.
- `tests/integration/progression/test_allocate_ap_dormancy.py` — genuinely stronger than either of
  the above: runs a real, non-mocked `Kernel.tick_once()` loop (150 ticks, `sandbox_world`) and
  proves `unspent_ap` never decreases and no `attribute_changed` event co-occurs — i.e., it proves
  the `ALLOCATE_AP` branch does NOT fire while the flag is OFF. This is real dormancy-under-real-
  conditions proof, not domain-logic verification of what *would* happen if it did fire. It is a
  negative-result test by design (proves absence, not correctness of presence).

### (b) Real behavioral coverage of the gated code path (would catch a regression if ON)
The `test_phase6_*.py` suite (10 files: `test_phase6_progression_conversion_phase.py`,
`test_phase6_progression_conversion_scenarios.py` (7 scenarios), `test_phase6_progression_conversion
_budget.py`, `test_phase6_conversion_decision_service.py`, `test_phase6_conversion_intent_bridge.py`,
`test_phase6_conversion_option_generator.py`, `test_phase6_growth_gap_evaluator.py`,
`test_phase6_possession_understanding_service.py`, `test_phase6_reward_interpretation_service.py`,
`test_phase6_reward_ledger_service.py`) all call `ProgressionConversionPhase.execute(state, update)`
or its constituent services **directly**, constructing `AuthoritativeState`/`StateUpdate`/entities by
hand via `V2EntityBuilder`. None of them go through `src/engine/pipeline.py`'s `run_phase` gate or a
real `Kernel` loop, so **every one of these tests would pass identically regardless of whether
`ENABLE_PROGRESSION_EVOLUTION` is OFF or ON** — they bypass the flag gate entirely by construction.
This confirms the ticket's own framing precisely: they are real, deep behavioral coverage of the
domain logic itself (possession scoring, gap evaluation, reward interpretation, option generation,
personality-weighted selection, intent resolution — verified against 7 hand-built scenarios covering
gold→repair, item→keep, and other conversion paths) but they are **not** evidence that the phase is
correctly *wired* into the real pipeline, nor that it behaves correctly under realistic, organically-
evolved entity/world state (real inventories, real personality distributions, real concurrent-phase
interaction, real reward-ledger population — which per the Current Behavior finding above does not
actually happen in live runs anyway).

### Honest verdict
The ticket's own characterization — "thinnest coverage of the 5 deferred flags" — is correct but
needs a more precise decomposition than a flat file count suggests:
- **Domain-logic depth is actually strong**, not thin: 10 dedicated Phase-6 test files exercise
  every service (`possession.py`, `gaps.py`, `interpretation.py`, `generator.py`, `selector.py`,
  `resolver.py`) both individually and through 7 integrated scenarios, plus a dedicated perf-budget
  test. This is comparable to or deeper than the domain-logic coverage the sibling flags
  (`COMBAT_ENGAGEMENT`, `WORLD_EMERGENCE`) had before their own trials. But this depth is entirely
  isolated-unit-level — independently, no real kernel-level regression test exists that exercises
  this phase's domain logic under a live pipeline.
- **Pipeline-wiring / flag-gating coverage is thin**: exactly 2 files reference the flag by name,
  and neither is a strong gating-mechanics test in the sense the other M1 sibling tickets had (e.g.
  `ENABLE_COMBAT_ENGAGEMENT`'s own dedicated real-kernel-loop fix-regression tests). No test proves
  `run_phase("progression_conversion", ...)` correctly skips/runs based on the flag through a real
  `Kernel` loop (the closest is `test_allocate_ap_dormancy.py`, which is real-kernel but only proves
  the OFF state, never toggles ON).
- **The most important coverage gap is neither dormancy nor domain logic, but the reward-ledger
  producer gap** documented above — no test anywhere (including the Phase-6 suite) exercises the
  phase under conditions where the ledger is populated by a real upstream producer, because no such
  producer exists. All 7 "scenario" tests hand-inject a `RewardLedgerComponent` directly into the
  entity's `properties` before calling `execute()` — which is the correct way to unit-test the
  domain logic, but it also means **no test in the repo demonstrates that the ledger is reachable
  from real gameplay at all.**

**Verdict**: this coverage is deep enough to trust that the phase's *internal decision logic* is
correct in isolation (the domain-logic tests are genuinely thorough), but it is **not** deep enough
to trust a clean ON trial result at face value as "safe to flip." A clean/near-zero-effect trial
result must be caveated as likely reflecting the reward-ledger gap (a structural wiring absence, not
validated safety) rather than confirmed behavioral safety — the honest "not enough coverage to trust
a trial's *clean-pass conclusion* without qualification" framing the ticket's own Scope anticipates,
even though the trial itself is still worth running as real evidence of wiring/perf/suppression
safety.

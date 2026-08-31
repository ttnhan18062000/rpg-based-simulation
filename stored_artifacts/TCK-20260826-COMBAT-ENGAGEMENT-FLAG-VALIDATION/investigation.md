---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION
artifact_type: investigation
tags: [feature-flags, combat]
---

# Investigation — TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION

## Method
`search_docs` (MCP) and `python3 tools/knowledge_search.py query ... --top-k 5` both returned
"index not found" this session — a known, pre-existing environment gap already confirmed by the
orchestrator, not specific to this ticket. `graphify query "ENABLE_COMBAT_ENGAGEMENT feature flag
combat_engagement phase.py pipeline.py push shaper"` (run by the orchestrator) and a follow-up
`graphify query "CombatEngagementDecisionService"` both returned generic/unhelpful matches — the
query terms are too code-heavy for graphify's fuzzy matcher on this topic. Proceeded directly to
source reads and targeted grep per the orchestrator's explicit instruction, which is consistent
with CLAUDE.md's own fallback design (grep/read as follow-up once semantic tools are confirmed
unavailable, not skipped pre-emptively). Read: the ticket, all 4 `combat_engagement/` domain
files, `src/engine/pipeline.py`'s `run_phase()` machinery and the `combat_engagement` phase
registration, `src/domains/optimization/feature_flags.py`, `tools/calibrate_simq.py`'s flag/corpus
plumbing, `src/observability/event_shapers.py`'s `CombatShaper`, the TCK-20260809 bug ticket and
its 3 stored artifacts, the TCK-20260824 decision ticket's 3 stored artifacts,
`docs/architecture/rollout_flag_decisions_m1.md`, `docs/guidelines/intentional_divergences.md`
(DEV-002/DEV-003), and `config/simulation_quality/corpus_registry.yaml` /
`config/simulation_quality/profiles/*.yaml`.

## Current Behavior

### `CombatEngagementPhase` (src/domains/combat_engagement/phase.py:20-96)
A static `apply(state, context=None) -> StateUpdate` method run once per eligible actor. For every
alive+active entity, it queries neighbors within radius 10.0 (spatial grid if present, else an
O(n) fallback loop, `phase.py:44-62`), evaluates up to 3 nearby targets (`phase.py:65`,
`targets_to_evaluate = targets[:3]`), calls
`CombatEngagementDecisionService.evaluate(actor, target, state)` for each, and on the **first**
evaluated target (`phase.py:68-90`, `break` at line 90) writes a subjective posture
(`last_combat_posture`, `last_combat_posture_target` property updates) plus whatever
`strategic` update `PostureIntentResolver.resolve()` returns. It builds and returns a **brand
new, standalone `StateUpdate()`** (`phase.py:33`, `phase.py:92-95`) — it has zero knowledge of
any other phase's output in the same tick. This is the exact shape of object the pipeline's
merge-vs-replace bug (below) operates on.

### `CombatEngagementDecisionService` / `EngagementRiskEvaluator` / `CombatPostureSelector`
(`service.py`, `risk_evaluator.py`, `selector.py`, `schema.py`) — pure, deterministic, read-only
decision logic. `service.py:37-38` short-circuits to `AVOID` on `combat_loss_counts.get(target.id,
0) >= 3` (fear avoidance). Otherwise `risk_evaluator.py` computes `win_confidence`, `death_risk`,
`uncertainty_penalty`, `objective_value`, `personality_bias`, `emotional_bias` from perceived
opponent/self estimates and personality traits, and `selector.py` maps the resulting
`EngagementRiskEvaluation` to one of 12 `CombatPosture` enum values (`IGNORE` through
`VENGEANCE_ENGAGE`). None of this code path emits any of the 5 push-shaper combat event types
directly, and none of it authoritatively mutates `combat.hp`/`combat.alive` — it only ever
produces `property_updates`/`strategic` `EntityUpdate` fields (posture bookkeeping), consistent
with the Strategic/Tactical Rule (strategy informs, tactics execute) and confirmed correct and
untouched by the TCK-20260809 fix (`stored_artifacts/TCK-20260809-.../plan.md`: "the bug is
entirely in how its own output gets chained, not in what it computes").

### `FeatureFlagManager` (src/domains/optimization/feature_flags.py:9-79)
`ENABLE_COMBAT_ENGAGEMENT` defaults `FeatureMode.OFF` (line ~31, inside the dict literal, with an
inline comment citing this exact ticket as the deferred follow-up). Modes are `OFF | SHADOW | ON |
STRICT`; `is_enabled()` treats `ON`/`STRICT` as enabled (line ~113). There is no dedicated env var
reader inside `feature_flags.py` itself — overrides flow in from three places, all consumed in
`src/engine/pipeline.py::refine()` (lines 69-92):
1. `state.rollout_profile.enabled_phases/shadow_phases/disabled_phases` (a dead mechanism —
   `RolloutProfileManager` itself was cut by TCK-20260824; only the field-reading code in
   `pipeline.py` remains, effectively unreachable in practice since nothing constructs a
   `rollout_profile` with this flag in it anymore).
2. `state.feature_flags` dict — direct per-flag `FeatureMode` overrides on `AuthoritativeState`.
3. `state.pressure_signals` — any key starting `ENABLE_` maps a truthy float to `ON`.

`tools/calibrate_simq.py` (the real corpus-trial driver) applies overrides in exactly this order:
profile YAML's `feature_flags:` block first (lower priority), then a real OS env-var read
(`os.environ.get(flag, "")`, `calibrate_simq.py:271-277`) that can override the profile — both
paths write into `state.feature_flags` via `dataclasses.replace` (`calibrate_simq.py:279-283`),
which `pipeline.py:82-84` then applies onto the `FeatureFlagManager`. `ENABLE_COMBAT_ENGAGEMENT`
is in `calibrate_simq.py`'s own `_KNOWN_FLAGS` allow-list (line 245), so
`ENABLE_COMBAT_ENGAGEMENT=ON python3 tools/calibrate_simq.py ...` is a real, already-supported way
to force the flag on for a single trial run without touching code.

### The TCK-20260809 fix in `pipeline.py` — exact mechanism
`run_phase()` (`pipeline.py:102-133`) is the pipeline's own per-phase wrapper: it evaluates the
`FeatureMode` for a given `feature_flag` name (skip entirely if `OFF`), evaluates
`PhaseDependencyGraph.should_run_phase()`, and if the phase should run, does
`phase_upd = phase_fn(upd)` then (outside `SHADOW` mode) `return phase_upd` (`pipeline.py:117,
129`) — **wholesale replacing** the caller's `update` variable with whatever the phase's own
lambda returns. This is safe only if `phase_fn` itself folds the incoming `upd` into its result.
The `combat_engagement` registration (`pipeline.py:276`) is:
```python
update = run_phase("combat_engagement", update, lambda u: u.merge(CombatEngagementPhase.apply(state)), "ENABLE_COMBAT_ENGAGEMENT")
```
The `u.merge(...)` call is the fix (`pipeline.py:266-275`'s own comment documents this in detail,
citing TCK-20260809 by name). Before the fix, the lambda was
`lambda u: CombatEngagementPhase.apply(state)` — it discarded `u` (the incoming accumulated
`StateUpdate`, i.e. `upd` inside `run_phase`) entirely and returned only
`CombatEngagementPhase.apply(state)`'s own brand-new `StateUpdate()`. Because `combat_engagement`
runs (`pipeline.py:263-277`) **after** `action_routing`/`position_swaps`/`movement_routing`
(`pipeline.py:257-261` — Phase 3, including the real `ATTACK` intent dispatch that produces
`hp_delta` `CombatUpdate`s) but **before** `interaction_routing`/`interaction_enforcement`
(`pipeline.py:279-289` — Phase 4), any accumulated `hp_delta`/`attacker_id` `EntityUpdate`s
produced by `action_routing`'s real `ATTACK` dispatch earlier in the same tick were silently
wiped the moment `combat_engagement` ran unmerged. `src/observability/event_shapers.py`'s
`CombatShaper` (`event_shapers.py:108-330`) derives `combat_damage`/`combat_engagement_started`/
`entity_killed` from exactly that kind of `combat_upd.hp_delta` + `_real_combat_update()`
discriminant (`event_shapers.py:214-231`, `event_extractor.py:27-44`) reading `update.
entity_updates` — so wiping those `EntityUpdate`s upstream meant the shaper had nothing to shape,
downstream, for the whole tick. `combat_engagement_ended` derives similarly from `task`/
`property_updates` fields (`event_shapers.py:142-193`) that were equally vulnerable to the same
wholesale replacement. This is a real, deterministic, whole-tick effect, not probabilistic —
confirmed in `stored_artifacts/TCK-20260809-.../investigation.md` via 3 separate live corpus runs
on `dungeon_crawl_seed42` pre-fix (100% suppression) vs. post-fix (reliable firing,
`combat_engagement_ended=10` in that specific run).

### Regression guard already in place
`tests/unit/domains/combat_engagement/test_combat_engagement_phase_merge.py` (2 tests, both from
the TCK-20260809 fix) directly asserts a hand-constructed prior-phase `EntityUpdate` survives a
real `AuthoritativeApplyPipeline.refine()` call with `ENABLE_COMBAT_ENGAGEMENT=ON`. This test
covers the **mechanism** (merge vs. replace) at the unit level with a synthetic marker key, not a
**real corpus** run with genuine combat activity — which is exactly the gap this ticket exists to
close (a unit-level mechanism guard is necessary but was already explicitly disclosed in
TCK-20260824's own decision table as insufficient to justify flipping the default: "a one-off
validated fix... is necessary but not sufficient on its own").

## Mechanics / Engine Constraints
- **Strategic/Tactical Rule** (CLAUDE.md, also reflected in `docs/mechanics/04_strategic_
  cognition.md`): `CombatEngagementPhase` is explicitly scoped to subjective posture assessment
  (strategy/perception), not damage resolution (tactics). This ticket's trial must confirm the
  flag, when ON, still respects that boundary — i.e. the ATTACK/damage-resolution path
  (`action_routing`, `src/engine/tactical.py`) keeps firing and producing real combat events
  independent of whatever posture `CombatEngagementPhase` assigns, rather than the flag somehow
  gating tactical combat itself (which was the mistaken initial hypothesis in TCK-20260809, ruled
  out there and not reopened by this ticket).
- **Durable State Rule**: `CombatEngagementPhase.apply()`'s posture output
  (`last_combat_posture`/`last_combat_posture_target`) is written as typed `EntityUpdate.
  property_updates`, applied only through the authoritative pipeline (`AuthoritativeApplyPipeline.
  refine()`) — already compliant; this ticket does not change that.
- **Kernel 7-phase loop** (`docs/engine/kernel.md`): `combat_engagement` sits inside the
  Resolution phase of a single tick, ordered after action/movement routing and before interaction
  enforcement (`pipeline.py`'s own phase order, Enhanced RPG Phase 4 out of the ~17-phase
  `refine()` sequence) — the trial must run enough real ticks (matching the 2000-tick precedent)
  for this ordering-dependent interaction to be exercised many times, not just once.

## Docs Requiring Update
- `docs/architecture/rollout_flag_decisions_m1.md`: this ticket is the named follow-up its own
  `ENABLE_COMBAT_ENGAGEMENT` table row cites ("Kept OFF, deferred... Follow-up:
  TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION"). Regardless of which way the real trial comes
  out (flip ON or stay OFF with a stronger evidence-backed rationale), that row's Verdict/
  Rationale cell must be updated with the real trial's result so the table stops pointing at an
  open follow-up that has actually been run — leaving it unchanged after this ticket closes would
  make the decision artifact itself stale and undiscoverable, the exact failure mode
  TCK-20260824's own precedent was written to prevent.

The `docs/guidelines/intentional_divergences.md` doc (a new `DEV-00N` entry, `DEV-003`-shaped) is
**not** listed above because whether it needs a new entry depends on the real trial's outcome,
which is not decided by this investigation — Implement's job, not Investigate's, per the
Uncertainty Rule ("vague leads stay vague until evidence narrows them"). If the real trial
recommends flipping `ENABLE_COMBAT_ENGAGEMENT` to `ON`, a new `DEV-006`-or-next-numbered entry
mirroring `DEV-003`'s structure is required (same class of change: a Phase-10 flag's default
diverging from DEV-002's blanket OFF policy). If the trial instead recommends staying OFF with a
now-stronger evidence-backed rationale (e.g. real combat activity confirmed but insufficient
corpus-profile production usage to justify a flip, matching the other 4 still-deferred flags'
posture), no new divergence exists to record — the flag's behavior versus the Mechanics Bible does
not change either way, only the flip/no-flip decision's evidentiary basis does, which lives in the
architecture doc above, not `intentional_divergences.md`. The `docs/audits/D19_domain_phase_
inventory.md` §12 entry (path: `docs/audits/D19_domain_phase_inventory.md`, under `docs/`) is
similarly not required to change: it documents `CombatEngagementPhase`'s scope ("posture
assessment only"), which this ticket's trial is expected to *confirm*, not *revise* — TCK-20260809
already ruled out the alternate hypothesis that the flag gates tactical combat itself, and nothing
in this investigation reopens that question.

## Parity Ledger Overlap
None found that this ticket's own scope touches directly. `docs/parity_ledger/combat_movement.yaml`
carries `COMB-308` (added by TCK-20260809 for the merge-bug fix itself, already `verified` per
that ticket's own Files Changed list) — this ticket does not change `CombatEngagementPhase`'s
logic or the `pipeline.py` merge fix, so `COMB-308`'s existing status should not need updating.
Confirmed no P0 parity entry names `ENABLE_COMBAT_ENGAGEMENT` specifically (grepped
`docs/parity_ledger/*.yaml` for `COMBAT_ENGAGEMENT` and `combat_engagement`; only match is
`COMB-308`'s own text, already accounted for above). If the real trial surfaces a genuine new
divergence (not expected, but per the Uncertainty Rule this is not pre-decided), the Implement
phase must add or update a parity entry then — not assumed here.

## Prior Work
- **TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS** (DONE): found and fixed
  the exact merge-vs-replace bug this ticket's trial must confirm still holds. Method: a
  controlled A/B test on `dungeon_crawl_seed42`, 2000-tick, in-memory and on-disk JSONL, comparing
  flag-ON vs. flag-OFF event counts for `combat_engagement_started/ended`, `combat_resolved`,
  `combat_damage`, `entity_killed`. This ticket's own trial should mirror that exact method (same
  world/seed precedent, same event-type checklist) rather than inventing a new one, per this
  ticket's own Scope: "Run... against at least one SimQ corpus world with the flag explicitly ON,
  comparing against the same world with it OFF."
- **TCK-20260824-ROLLOUT-FLAG-DECISIONS** (DONE): reviewed 8 Phase-10 flags including
  `ENABLE_COMBAT_ENGAGEMENT`, explicitly deferred it (kept OFF) specifically because the
  TCK-20260809 fix's own verification was "a one-off A/B test, not a standing production signal,"
  and named this ticket as the follow-up whose job is to produce that standing signal. Established
  the decision-artifact format (`docs/architecture/rollout_flag_decisions_m1.md`) this ticket's
  own eventual recommendation doc should mirror, and the two legitimate decision classes ("Flip
  ON" requires real standing production evidence; "Keep OFF, deferred" requires a named follow-up,
  not an indefinite someday) that frame what this ticket's trial needs to produce either way.
- **DEV-002/DEV-003** (`docs/guidelines/intentional_divergences.md`): DEV-002 is the blanket
  Phase-10 default-OFF policy with `tools/balance_measure.py` re-run as its literal unblock
  condition. DEV-003 established the precedent that *equivalent-strength alternative evidence*
  (standing real SimQ-corpus-profile usage in the flag's own domain) can satisfy DEV-002's intent
  without literally re-running `balance_measure.py`, when `balance_measure.py`'s own metrics
  (adventure-routing/economy/hunger) aren't in the flag's domain. `ENABLE_COMBAT_ENGAGEMENT`'s
  domain (combat) is even further from `balance_measure.py`'s metrics than DEV-003's
  belief/social-cooperation case was — so this ticket's real corpus-profile combat-event evidence
  is the same class of substitute evidence DEV-003 already legitimized, not a new precedent.

## Risks and Open Questions
- **Open question (blocks the flip/no-flip decision, not this investigation's job to resolve):**
  a single successful ON/OFF corpus comparison confirming push-shaper events fire correctly is
  necessary evidence but, per DEV-003's own precedent, may not alone be *sufficient* to justify
  flipping the global default — DEV-003's actual flips were justified by pre-existing, already-
  running *production* profile usage (`urban_political.yaml`/`sandbox_world.yaml` already had the
  flag ON before the ticket ran), not a fresh one-off trial. `ENABLE_COMBAT_ENGAGEMENT` currently
  has **zero** shipped profiles turning it on. Implement/Verify must weigh whether "we ran a real
  trial and it worked" is itself now sufficient standing evidence, or whether the honest
  recommendation is still "keep OFF, but now with a real corpus trial on file" pending a shipped
  profile actually using it — this is a genuine judgment call for whoever writes the final decision
  doc, not something to assume either way here.
- **Risk**: `dungeon_crawl`'s `COMBAT: 2.0` pillar weight (highest of any profile) makes it the
  single strongest candidate for exercising real combat volume, but it is also the *exact* world/
  seed already used to find and verify the original bug — a second, independent world
  (`wilderness_survival`, also `monster_only_gauntlet` archetype but a different scale/seed) should
  be included so the confirmation isn't solely "the same fix holds on the same world it was fixed
  on."
- **Risk**: `CombatEngagementPhase.apply()`'s own real per-tick cost (0.85ms avg, up to 17.3ms peak
  per TCK-20260809's own disclosed secondary finding) raises the tick-budget-exceeded rate from
  6.2% to 7.1% on `dungeon_crawl`. This is a real, already-disclosed, out-of-scope-for-fixing cost;
  the trial should note it recurs (not investigate or fix it) if observed again, consistent with
  TCK-20260809's own explicit non-fix decision.
- **Risk**: `PhaseDependencyGraph.should_run_phase()` (`pipeline.py:113`) gates whether
  `combat_engagement` runs at all on a given tick even when the flag is `ON` — if this dependency
  policy skips the phase on most ticks in a chosen corpus world (e.g. too few nearby entity pairs
  within radius 10.0), the trial could show a false "no suppression, but also no real activity"
  result. The trial's evidence-capture step must check `metric_counters["run_combat_engagement"]`
  vs. `metric_counters["skip_combat_engagement"]` (both written by `run_phase()`,
  `pipeline.py:114-115/131-132`) alongside raw event counts, not raw event counts alone, to rule
  this out.

## Anti-Drift Hazards
- **Do not conflate this ticket with fixing or extending `CombatEngagementPhase` itself.** Out of
  Scope explicitly excludes "any new gameplay content for the combat-engagement system." The trial
  is purely evidence-gathering; if it surfaces a *new* bug (not the already-fixed TCK-20260809
  merge issue), that is a new finding to disclose and hand off as a separate ticket, not something
  to fix inline here.
- **Do not flip the flag's default as part of this ticket.** Out of Scope is explicit: "Actually
  flipping the flag's default... is not something to do unilaterally here." The deliverable is a
  recommendation with evidence, plus (if flip is recommended) a *named* next-step ticket — not the
  flip itself.
- **Do not treat a clean ON/OFF event-count diff alone as sufficient "real combat activity"
  evidence** without also checking absolute event volume is non-trivial (e.g. `combat_damage`
  count > 0 in the OFF/baseline run too) — a world with near-zero baseline combat activity would
  make an ON/OFF diff of "0 vs 0" pass a naive suppression check while proving nothing about real
  behavior under load.
- **Do not silently reuse `data/calibration/` or `data/runs/` output from a different session's
  concurrent work** — per the Hard Rules on shared-directory concurrency, always generate a fresh,
  uniquely-tagged run (`--output`/`--name` with this ticket's own tag) rather than trusting
  pre-existing directories that might belong to another in-flight investigation.
- **Clean up `data/runs/*` and any ad hoc calibration output** at Finalize per the Definition of
  Done ("Temporary run data cleaned"), same as every other ticket — a validation trial is not
  exempt from this even though it produces no permanent code change.

## Corpus Trial Plan

### Primary candidate — `dungeon_crawl` (seed 42, 2000 ticks)
**Why**: highest `COMBAT` pillar weight of any shipped profile (`2.0`, vs. `1.0` default and `0.3`
for `urban_political`), `monster_only_gauntlet` archetype (32 entities, `end_to_end` tier per
`config/simulation_quality/corpus_registry.yaml`), and the exact world/seed TCK-20260809 already
used to find and verify the original bug — directly continuing that precedent, per this ticket's
own Scope ("mirroring... the decision-artifact format") and per Prior Work above.

Commands (OFF is the real corpus default — no override needed; run it anyway for a fresh,
identically-tagged baseline rather than trusting an old artifact):
```
# OFF (baseline)
python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_combat_engagement_OFF

# ON
ENABLE_COMBAT_ENGAGEMENT=ON python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_combat_engagement_ON
```

### Secondary candidate — `wilderness_survival` (seed 42, 2000 ticks; no dedicated scoring
profile exists, so `--profile default` applies the balanced `COMBAT: 1.0` weight)
**Why**: also `monster_only_gauntlet` archetype but a different, independent world (11 entities,
`end_to_end` tier) — confirms the fix generalizes past the one specific world it was discovered
and fixed on, addressing the Risk noted above. Smaller entity count than `dungeon_crawl`, so
expect a lower absolute combat-event volume; still useful as a second independent data point, not
a replacement for the primary.
```
# OFF (baseline)
python3 tools/calibrate_simq.py --name wilderness_survival --seed 42 --ticks 2000 --profile default \
  --output data/calibration/wilderness_survival_seed42_2000t_combat_engagement_OFF

# ON
ENABLE_COMBAT_ENGAGEMENT=ON python3 tools/calibrate_simq.py --name wilderness_survival --seed 42 --ticks 2000 --profile default \
  --output data/calibration/wilderness_survival_seed42_2000t_combat_engagement_ON
```
(Both commands assume a compiled world spec named `wilderness_survival` resolves via
`_load_world_state()` inside `calibrate_simq.py` the same way `dungeon_crawl` does — if it does
not, `calibrate_simq.py` falls back to the generic hero+goblins scenario, which is still a valid,
if weaker, real-combat comparison; Implement should confirm which path actually triggers and
disclose it rather than assume.)

### What evidence to capture (per world, per ON/OFF pair)
1. **Raw event counts from `data/runs/{run_id}/simulation_events.jsonl`** (the file
   `calibrate_simq.py::_run_engine()`/`_replay_jsonl_through_hub()` reads, `calibrate_simq.py:445-
   465`) — count occurrences of each of the 5 event types TCK-20260809 checked:
   `combat_engagement_started`, `combat_engagement_ended`, `combat_resolved`, `combat_damage`,
   `entity_killed` (e.g. `grep -c '"event_type": *"combat_damage"' data/runs/<run_id>/
   simulation_events.jsonl`, repeated per type). The suppression signature to rule out is exactly
   TCK-20260809's own pre-fix finding: **ON producing zero across all 5 types while OFF produces
   nonzero counts for the same world/seed/tick-count.**
2. **`metric_counters["run_combat_engagement"]` / `["skip_combat_engagement"]`** from the pipeline
   run (written by `run_phase()`, `pipeline.py:114-115/131-132`) — confirms the phase actually ran
   on a meaningful number of ticks when ON, ruling out the "phase skipped, so nothing to suppress"
   false-negative noted in Risks above.
3. **`quality_report.json`'s `COMBAT` pillar_event_counts`** (written by `QualityHub.
   get_quality_report()`/`QualityReportBuilder`, `src/simulation_quality/quality_hub.py`) for both
   ON and OFF — a second, independently-computed cross-check on the same underlying events, via the
   SimQ scoring path rather than raw JSONL grep.
4. **Absolute (not just relative) event volume in the OFF/baseline run** — confirms "real combat
   activity" per this ticket's own Scope, i.e. `combat_damage`/`entity_killed` counts meaningfully
   above zero in the baseline, not just "ON == OFF" on two near-empty runs (see Anti-Drift Hazards
   above).
5. **Whether `PhaseDependencyGraph.should_run_phase()` skips `combat_engagement` on most ticks** —
   from item 2 above; if skip-rate is very high, note it as a caveat on how strong the evidence
   actually is, not silently omit it.

### What "real combat activity" means for these worlds
For `dungeon_crawl`: `monster_only_gauntlet` archetype with `COMBAT: 2.0` pillar weight means the
world is purpose-built for combat encounters between the hero and goblin-class monsters at close
spatial proximity — TCK-20260809's own baseline run already confirmed `combat_engagement_ended=10`
in a comparable configuration, giving a concrete non-zero floor to check the OFF run against. For
`wilderness_survival`: same archetype, smaller scale — real activity means nonzero
`combat_damage`/`entity_killed` counts in the OFF run, though likely proportionally lower given 11
vs. 32 entities; Implement should report the actual OFF-run counts rather than assume they will
be nonzero.

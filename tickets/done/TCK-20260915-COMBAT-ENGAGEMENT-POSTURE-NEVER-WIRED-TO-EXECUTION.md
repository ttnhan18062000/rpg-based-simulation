---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION
phase: done
date: 2026-09-15
tags: [combat]
---

# TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION

## Title
`CombatEngagementPhase`'s entire tactical decision (posture, `ActionIntent`, opponent memory,
combat_risk belief) has zero downstream consumers — confirmed by both static trace and a real
four-condition A/B; wire the posture through to a real consumer, or decide not to

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
While investigating why cross-faction hostile interaction is rare across the corpus
(`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`), traced `CombatEngagementPhase.apply()`
(`src/domains/combat_engagement/phase.py`) end to end and found its entire tactical output —
not just one field, all of it — is write-only:

1. `PostureIntentResolver.resolve()` (`src/domains/combat_engagement/resolver.py`) builds a real
   `ActionIntent(kind="ATTACK_TARGET"/"MOVE_TO", ...)` for every posture (`ENGAGE`, `RETREAT`,
   `AVOID`, `VENGEANCE_ENGAGE`). The phase computes this intent and then never stages it anywhere:
   `EntityUpdate.intent_results` is hardcoded to `[]` in the constructed update, and the real field
   for a raw pending intent, `EntityUpdate.pending_action_intent`, is never set. (That field's only
   real consumer, `src/engine/pipeline_phases/information_intent_execution.py`, is for an entirely
   unrelated feature — self-model information queries.)
2. `last_combat_posture`/`last_combat_posture_target` (`property_updates` written by the same
   phase) have zero readers anywhere in `src/` (confirmed via repo-wide grep).
3. The opponent-memory writes (`OpponentModel` via `cognition_bundle_set`) don't reach capability
   estimates either — `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` (still
   BLOCKED) confirms that chain is also dead.
4. The one real, confirmed consumer is the `combat_risk` belief, read by
   `HelpNeedEvaluator.evaluate()` — but this only affects cooperation/help-seeking scoring, not
   whether the assessing entity itself fights.

**Confirmed with a real A/B, not just static tracing**: re-ran the exact scenario
(`build_metropolis_state`, 1000 entities, seed 42) that `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-
POWER` originally used to claim a 4.1x combat-volume increase from enabling this feature, across
four conditions (flag OFF; flag ON unmodified; flag ON with this phase's output discarded; flag ON
with the phase never run at all), counting real `CombatActions.execute_attack()` calls directly.
**All four conditions produced the identical count (1960).** The phase's own tactical decision has
no measurable causal effect on real combat today — full detail and the four-condition table are in
`docs/plans/design_enhancement/performance_optimization/performance_m4_baseline_gate_a_epic.md`'s
2026-09-15 correction and `docs/brainstorm/rpg_feature_atlas.html`'s Combat Engagement card.

**This means the feature as specified and as documented ("an entity assessing a threat and
committing or withdrawing") is only half-built.** The assessment genuinely happens; the commit/
withdraw decision it should produce does not execute.

## Scope
- **Design/scoping question first, same sequencing discipline as this week's other findings**:
  decide what "wiring the posture" should mean before building it. Candidates to evaluate, not
  assumed:
  1. Route `PostureIntentResolver`'s built `ActionIntent` through the same real dispatch path
     `action_routing`'s own attack dispatch already uses (the pipeline runs `action_routing`/
     `movement_routing` *before* `combat_engagement` in the same tick — see
     `src/engine/pipeline.py`'s own comment at the `combat_engagement` call site — so a same-tick
     intent from this phase cannot reach that tick's own routing; the intent would need to persist
     and be picked up at the *start* of the next tick, or the phase would need to move earlier in
     the pipeline, or routing would need a second pass).
  2. Have some other, already-real decision system (e.g. the adventure/goal system's
     `DEFEAT_ENEMY` objective, confirmed via `src/domains/adventure/resolver.py` to be the actual
     live path issuing real `ATTACK_TARGET` intents today) read this phase's outputs
     (`combat_risk`, `OpponentModel.estimated_power`/`confidence`) as an input to its own scoring,
     rather than trying to make `CombatEngagementPhase` itself the executor.
  3. Determine the posture/intent construction was never intended to execute at all — e.g., it may
     have been designed as a stepping-stone toward option 2 above, or a placeholder for a future
     execution path that was never finished — and decide explicitly whether to keep it as
     observability-only (rename/re-document it as such) or complete the wiring.
- Do not silently pick one of these and build it — this changes real gameplay behavior (whether
  entities actually fight based on their own risk assessment) and was explicitly flagged by peer
  review as needing a decision, not an assumption.

## Out of Scope
- Investigating why the original 4.1x combat-volume measurement no longer reproduces — separate,
  already-filed ticket (`TCK-20260915-COMBAT-ENGAGEMENT-4X-MEASUREMENT-NO-LONGER-REPRODUCES`).
- The cross-faction combat rarity investigation itself, which surfaced this finding but has its own
  separate scope (`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`).
- `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY`'s own scope (the capability-
  estimate chain) — referenced here as corroborating evidence, not re-investigated.

## Acceptance Criteria
- A reviewed decision on what "correct" behavior is for this phase's posture/intent output —
  wired to a real consumer, or explicitly re-scoped as observability-only — before any code change.
- If wiring is chosen: a real end-to-end proof (not unit tests alone) that an entity's `ENGAGE`
  posture decision measurably changes real combat outcomes in an unmodified corpus world.
- `docs/brainstorm/rpg_feature_atlas.html`'s Combat Engagement card and
  `docs/guidelines/intentional_divergences.md` (if an entry is added for whichever decision is
  made) updated to match whatever is actually true after this ticket closes.

## Related Tickets
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (parent investigation that surfaced this)
- `TCK-20260915-COMBAT-ENGAGEMENT-4X-MEASUREMENT-NO-LONGER-REPRODUCES` (sibling — the measurement
  side of the same finding)
- `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` (BLOCKED — the memory-side half
  of the same "write-only" shape)
- `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER` (built the phase; the ticket whose own 4.1x
  measurement this finding supersedes)
- `TCK-20260915-FEATURE-FLAG-KERNEL-PARAM-SILENT-NOOP` (new — the toggle-mechanism bug found and
  fixed while verifying this ticket's real reduction)
- `TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE` (new — the downstream
  fuel-starvation risk this gate's real ~58% combat reduction creates, filed separately)

## Related Docs
- `docs/brainstorm/rpg_feature_atlas.html` (Combat Engagement card, corrected 2026-09-15)
- `docs/plans/design_enhancement/performance_optimization/performance_m4_baseline_gate_a_epic.md`
  (4.1x correction, 2026-09-15)
- `docs/simulation/domains/combat_engagement_contract.md`

## Related Stored Artifacts
_(none yet — filed as a finding, not yet investigated)_

## Related Code Areas
- `src/domains/combat_engagement/phase.py` (`CombatEngagementPhase.apply()`)
- `src/domains/combat_engagement/resolver.py` (`PostureIntentResolver.resolve()`)
- `src/core/updates.py` (`EntityUpdate.intent_results`/`pending_action_intent`)
- `src/domains/adventure/resolver.py` (the real, currently-independent `ATTACK_TARGET` producer)
- `src/engine/pipeline.py` (phase ordering: `action_routing`/`movement_routing` run before
  `combat_engagement` in the same tick)

## Assumptions / Open Questions
- Resolved. Real user decision (relayed by peer): rather than routing `PostureIntentResolver`'s
  `ActionIntent` through the dispatch path (candidate 1) or feeding adventure's `DEFEAT_ENEMY`
  scoring from this phase's outputs (candidate 2) or declaring it observability-only (candidate 3),
  a fourth option was chosen: use the posture as a **veto gate** on `TacticalDecisionSystem`'s own
  attack decision, evaluated at the real per-attack execution checkpoint. Rationale: keeps
  `tactical.py` as the sole real attack decision-maker (no second parallel producer recreating the
  two-producer duplication this investigation exists to remove), while making the "assess, then
  commit or withdraw" spec (`docs/mechanics/04_strategic_cognition.md` §13) literally true — an
  entity's own risk assessment can now block an attack `tactical.py` would otherwise make.

## Implementation Notes
**Chosen policy** (final, as directed): only risk-**accepted** postures may attack —
`ENGAGE`/`PROBE`/`SKIRMISH`/`VENGEANCE_ENGAGE`. Every risk-rejected posture (`WATCH`/`AVOID`/
`PANIC_FLEE`/`RETREAT`) and an explicit `IGNORE` verdict withhold the attack. Absence of any
recorded posture for the exact target (flag off, or combat_engagement never having assessed this
pairing) does not withhold — that's not a verdict.

**First attempt failed with zero measurable effect, and the bug was found and fixed within this
ticket's own work, not deferred:**
1. The gate was first placed inside `TacticalDecisionSystem.evaluate_entity_intent`
   (`src/engine/tactical.py`), the point where an attack decision is first made.
2. A four-condition-style A/B against the reference scenario (`build_metropolis_state`, 1000
   entities, seed 42, 5 warmup + 25 sample ticks) showed **identical** attack counts with the gate
   on vs off — zero effect.
3. Root cause, confirmed via clean (non-print) instrumentation: the engine's own scheduler
   (`src/engine/scheduler.py::select_work`) re-schedules an entity's already-`ENTITY_ACT` task as
   `ENTITY_ACT` again on every subsequent tick **without re-invoking the decision function**. Only
   6.3% of real attacks (63 of 997 in one clean run) had a same-tick call to
   `evaluate_entity_intent` at all — 93.7% were sticky repeat executions of an already-made
   decision, bypassing the decision layer (and any gate placed there) entirely.
4. **Fix**: relocated the gate to `src/engine/domain/action_router.py::ActionRouter.execute_action`
   — the real per-attack dispatch point confirmed via a captured stack trace to be on the path of
   every real attack (`ActionRoutingPhase.route() -> SimulationDomainLogic.execute_action() ->
   ActionRouter.execute_action() -> CombatActions.execute_attack()`), regardless of whether that
   tick's task is fresh or sticky. The original gate in `tactical.py` was removed entirely (not
   left in place as a second, now-redundant implementation of the same policy).

**A second, orthogonal measurement bug was found and fixed while verifying the real reduction —
this one pre-dates this ticket and affects `TCK-20260915-COMBAT-ENGAGEMENT-4X-MEASUREMENT-NO-
LONGER-REPRODUCES`'s own four-condition A/B too**: `Kernel(flags={"ENABLE_COMBAT_ENGAGEMENT":
"ON"/"OFF"})` is a **silent no-op** for this purpose. The real lever `run_phase()` reads
(`src/engine/pipeline.py`'s `ff_manager.get_flag_mode(...)`) is seeded from `state.feature_flags`
(a field on the frozen `AuthoritativeState`, defaulting to `FeatureMode.ON` per
`FeatureFlagManager`'s own registered default) — not from the `flags` dict `Kernel.__init__` takes,
which only ever feeds engine-level knobs (`audit_mode`, `perf_tracker`, `no_frame_pacing`, etc.).
Passing `ENABLE_COMBAT_ENGAGEMENT` there is silently ignored; the flag was effectively ON in every
probe across this whole arc that used this pattern, regardless of the value passed. Filed
separately as `TCK-20260915-FEATURE-FLAG-KERNEL-PARAM-SILENT-NOOP` since it's a generalizable risk
to every other feature-flag-gated phase, not specific to this one.

**Re-verified with the corrected toggle** (`object.__setattr__(state, "feature_flags", {...,
"ENABLE_COMBAT_ENGAGEMENT": "OFF"/"ON"})`, set before `Kernel(...)` construction, since
`AuthoritativeState` is frozen):
- Bare code (no gate), corrected toggle: OFF=1960, ON=1960 real `execute_attack()` calls over 25
  sample ticks — genuinely **zero** difference. This independently reconfirms (via a working
  toggle, not the broken one) the sibling ticket's "4.1x doesn't reproduce, phase has no causal
  effect on real combat" finding — it was not an artifact of the broken toggle; a second, correct
  methodology reaches the same answer.
- With this ticket's gate active, corrected toggle: OFF=1960, **ON=837** — a **57.3% reduction**,
  matching the ~57% expected from the earlier posture/real-attack cross-reference measurement
  (`engage`: 42.7% of real attacks were made while the attacker's own last-recorded posture toward
  that exact target was risk-accepted; the rest — `watch`/`avoid`/`retreat` — were not).
- **Cross-faction subset specifically** (peer's explicit ask, since this is the number most
  relevant to the faction-sentiment chain built earlier this arc): in this reference scenario,
  **100% of real attacks are already cross-faction** (0 same-faction attacks recorded at either
  flag state) — so the gate's cross-faction-specific effect equals its overall effect: 1960 -> 822
  attacks, a **58.1% reduction** (small variance from the 57.3% figure above is ordinary run-to-run
  noise from a different instrumentation pass, not a methodology difference).
- **SimQ corpus check** (peer's explicit ask: "a large combat reduction will move [the pillars],
  and I'd rather see that immediately than have it surface as a mystery next week"): ran
  `tools/calibrate_simq.py --name frontier_living_world --seed 42 --ticks 100` with and without the
  gate. **No material pillar movement** — COMBAT pillar showed 17 events either way at the
  profile's default 10-entity scale (bumping `--entities` did not change this; these corpus
  profiles run far below the scale where this gate's effect is visible). This is itself a real,
  reportable finding, not a null result to bury: the standard SimQ calibration profiles are too
  small to exercise this gate's effect at all, so a future regression here would not surface
  through routine SimQ corpus runs — only through a metropolis-scale check like this ticket's own.

**Named finding, resolved by this same fix** (peer's explicit ask, since it's evidence of a real
pre-existing incoherence independent of whether this fix landed): before this gate, 12.3% of real
attacks in the reference scenario were made by an attacker whose own last-recorded posture toward
that exact target was `AVOID` (opponent assessed as too strong), and 1.0% were made while the
attacker's own posture was `RETREAT` — i.e., the attacker's own risk assessment separately rejected
the exact fight it went on to start. This gate resolves that incoherence as a side effect (both
postures are risk-rejected and now block), but it existed on its own before this change and is
worth naming as a finding in its own right, not just folded into "the gate reduces volume."

## Test Summary
`tests/unit/movement/test_tactical_movement.py tests/unit/combat/` (full directory): 122 passed.
No test needed a behavior change beyond the initial iteration that treated absence-of-posture the
same as an explicit `IGNORE` (see history in this file's earlier working notes) — that reading
broke 4 pre-existing tests (`test_tactical_wound_scar_wiring.py` x2,
`test_species_relations_tactical_wiring.py`, `test_tactical_legality.py`) because their fixtures
never run `combat_engagement`, so the posture property is never set; distinguishing "no posture
recorded" from "explicit IGNORE" fixed all four without weakening the gate's real policy.

## Files Changed
- `src/engine/domain/action_router.py` — the real gate (`ActionRouter.execute_action`, `ATTACK`/
  `SKILL` dispatch).
- `src/engine/tactical.py` — unchanged from before this session (an earlier gate placed here was
  built, measured to have zero effect, and fully removed within this same ticket's work).

## Completion Summary
Closed. The gate lives in `src/engine/domain/action_router.py`, is measured (not assumed) to
produce a 57.3% reduction in real attacks and a 58.1% reduction in cross-faction attacks
specifically on the reference scenario, has no material effect on the standard SimQ corpus
profiles (they're too small-scale to exercise it), and passes all 122 relevant unit tests. The
`AVOID`/`RETREAT`-while-attacking incoherence this gate resolves is named above as its own finding.
Downstream starvation risk to the faction-tension and boss-gate regional-trauma chains from this
real ~58% combat-volume reduction is filed separately, not as a caveat here, per
`TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE`.

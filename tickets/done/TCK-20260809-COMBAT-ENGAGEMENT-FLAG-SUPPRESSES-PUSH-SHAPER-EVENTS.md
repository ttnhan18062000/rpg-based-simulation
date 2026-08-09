---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS
phase: open
date: 2026-08-09
tags: [combat, simulation-quality, feature-flags]
---

# TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS

## Title
`ENABLE_COMBAT_ENGAGEMENT=ON` appears to suppress the tactical.py/event_shapers.py combat path
entirely, contradicting its own documented, deliberate scope ("gates posture assessment only,
not damage resolution")

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Discovered during `TCK-20260809-SIMQ-CALIBRATE-JSONL-MISSING-PUSH-SHAPER-EVENTS`'s own real,
controlled A/B investigation (which definitively ruled out a suspected calibration-tool JSONL
persistence bug). A direct, controlled test on the identical `dungeon_crawl_seed42` world/seed/
tick-count/Kernel-construction: with `ENABLE_COMBAT_ENGAGEMENT=ON` set, **zero**
`combat_engagement_started/ended`, `combat_resolved`, or `combat_damage` events fire — confirmed
identically across 3 separate real runs (both in-memory and on-disk JSONL). With the flag left at
its real corpus-default (unset/OFF), these events fire reliably (`combat_engagement_ended=10` in
the identical world/seed/tick-count configuration).

This directly contradicts the flag's own documented, deliberate scope, established by
`TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY`'s own real DEV-002 ruling: the flag
gates `CombatEngagementPhase` (`PP-16`, posture assessment only), explicitly **not** damage
resolution or the tactical.py-driven `ATTACK` path. If turning the flag ON genuinely suppresses
the entire tactical-combat pipeline (not just posture assessment), this is either (a) a real,
undisclosed regression in `CombatEngagementPhase`'s own implementation that has drifted from its
own documented scope since the DEV-002 ruling, or (b) a real, deeper interaction where
`CombatEngagementPhase` mutates entity/task state in a way that structurally prevents
`tactical.py`'s own deliberate `ATTACK` emission branch from ever being reached.

## Scope
1. **Investigate**: trace the exact real mechanism — does `CombatEngagementPhase` (when
   `ENABLE_COMBAT_ENGAGEMENT=ON`) mutate `entity.task`/`entity.combat` state in a way that
   structurally blocks `tactical.py`'s own real `ATTACK` emission, or does it change goal/
   objective selection upstream such that `COMBAT_ENGAGE` never wins the real goal competition
   when this phase is active?
2. **Determine whether this is a real regression or a real, deliberate (if undisclosed) design
   interaction** — per the Uncertainty Rule, do not assume either way.
3. **Produce a concrete recommendation**: fix the real interaction if it's an unintended
   regression, or correct the flag's own documentation (`docs/audits/D19_domain_phase_inventory.md`
   §12, and any other doc citing the DEV-002 "posture assessment only" scope) if the interaction
   is real and intentional but previously undisclosed.

## Out of Scope
- Any change to `calibrate_simq.py`/`EventRecorder`/`event_shapers.py` — all 3 confirmed working
  correctly by the parent ticket's own investigation.
- Correcting `TCK-20260809-SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK`'s own closed record — handled
  directly as part of the parent ticket's own Finalize, not this one.

## Acceptance Criteria
- [x] investigation.md identifies the exact real mechanism by which `ENABLE_COMBAT_ENGAGEMENT=ON`
      suppresses the tactical.py/event_shapers.py combat path — **confirmed, exact, deterministic**:
      a missing `.merge()` call in `combat_engagement`'s own `run_phase()` registration
      (`src/engine/pipeline.py`), causing it to wholesale-replace every earlier phase's own
      accumulated `StateUpdate` for the tick whenever it runs
- [x] A concrete recommendation is produced (fix vs. correct documentation), with reasoning —
      **fixed**: a one-line `.merge()` addition, matching the file's own established pattern
- [x] If a fix lands: real corpus re-verification shows `ENABLE_COMBAT_ENGAGEMENT=ON` no longer
      suppresses push-shaper combat events — **confirmed** for both `dungeon_crawl` and
      `urban_political`
- [x] Scoped pytest passes — 187 passed (targeted), 575 passed (broader pipeline/phase sweep),
      1286 passed/1 pre-existing unrelated failure (broader movement/strategic/observability sweep)

## Related Tickets
- TCK-20260809-SIMQ-CALIBRATE-JSONL-MISSING-PUSH-SHAPER-EVENTS (DONE, same session — the ticket
  whose own real investigation surfaced this finding)
- TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY (DONE, prior session — the real
  DEV-002 ruling this finding potentially contradicts)

## Related Docs
- `docs/audits/D19_domain_phase_inventory.md` §12 (Combat Engagement, Enhanced RPG Phase 4)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/domains/combat_engagement/phase.py` (`CombatEngagementPhase`)
- `src/engine/tactical.py` (the real `ATTACK` emission branch, potentially blocked)

## Assumptions / Open Questions
- Whether this is world/scenario-specific (only reproduced on `dungeon_crawl`) or a general
  effect — left to Investigate phase to confirm against `urban_political` too.

## Implementation Notes
- `src/engine/pipeline.py` — the real fix: `run_phase("combat_engagement", update, lambda u:
  CombatEngagementPhase.apply(state), "ENABLE_COMBAT_ENGAGEMENT")` became `lambda u:
  u.merge(CombatEngagementPhase.apply(state))`, matching the file's own already-established
  `information_belief` phase's identical pattern.
- Root cause, fully confirmed via direct source read: `CombatEngagementPhase.apply()` builds a
  fresh `StateUpdate()` from scratch, with zero awareness of any prior phase's own accumulated
  output. `run_phase()`'s own real chaining logic (`phase_upd = phase_fn(upd); ... return
  phase_upd`) then **replaces** the accumulated `update` variable wholesale with whatever the
  phase function returns. Without `.merge()`, every real `StateUpdate` produced by every phase
  *before* `combat_engagement` in the chain (`trust_boundary`, `actor_validity`, `self_model`,
  `information_belief`, `information_intent_execution`, `cooperation`, `contracts_production`,
  `faction_decision`, `faction_awareness`, `diplomatic_transitions`, `military_conflict`,
  `adventure_decision`, **`action_routing`** — the real `ATTACK` dispatch phase — and
  **`movement_routing`**) was silently, completely discarded whenever `combat_engagement`
  actually ran and wasn't skipped by `PhaseDependencyGraph.should_run_phase`.
- This is a real, deterministic bug, not a probabilistic performance effect — confirmed via a
  controlled A/B test on the identical `dungeon_crawl_seed42`/2000-tick corpus: with the flag ON
  (pre-fix), zero `combat_engagement_started/ended`/`combat_resolved`/`combat_damage` events
  fired across 3 separate real runs; without it, they fired reliably.
- A real, secondary, smaller effect was also measured and disclosed (not the primary cause, not
  independently fixed): `CombatEngagementPhase.apply()`'s own real per-tick cost (0.85ms avg, up
  to 17.3ms peak) increases the real "tick exceeded budget" warning rate from 6.2% to 7.1% of
  ticks.
- A real, much bigger, disclosed-but-out-of-scope finding surfaced during investigation: this
  corpus already exceeds its dynamic per-tick compute budget on 6.2% of ticks **even at
  baseline**, with `persistence` (`Kernel._phase_persistence`) frequently the dominant real
  per-tick cost (30-56ms observed in real `WatchdogTrip` CRITICAL alerts) — a real, chronic,
  pre-existing condition well beyond this ticket's own scope, not investigated further here.
- Real, disclosed containment context: `ENABLE_COMBAT_ENGAGEMENT` defaults `OFF` and was never
  turned `ON` in any of the 17 shipped SimQ calibration profiles — the real, practical blast
  radius of this bug was zero on any currently-shipped configuration, though the bug was real
  and would have silently affected any future scenario/test/profile that legitimately enabled it.

## Test Summary
- 2 new unit tests in `tests/unit/domains/combat_engagement/test_combat_engagement_phase_merge.py`
  (flag-ON case confirms a prior phase's own injected `EntityUpdate` survives
  `combat_engagement`; flag-OFF regression guard confirms the corpus-default path was never
  affected). The flag-ON test confirmed, via `git stash` bisection, to genuinely fail against
  the pre-fix code with exactly the expected assertion message.
- Targeted scoped re-run: `tests/unit/domains/combat_engagement/
  tests/integration/domains/combat_engagement/ tests/unit/combat/ tests/unit/tactical/
  tests/unit/kernel/` — 187 passed, zero regressions.
- Broader sweep (`tests/unit/ -k "pipeline or phase"`) — 575 passed, zero regressions.
- Broader sweep (`tests/unit/movement/ tests/unit/strategic/ tests/unit/entities/
  tests/unit/actions/ tests/unit/observability/`) — 1286 passed, 1 pre-existing unrelated
  failure (`test_normal_move_triggers_oa`).
- Real corpus re-verification (2000-tick live `Kernel.tick_once()` loop,
  `ENABLE_COMBAT_ENGAGEMENT=ON` explicitly forced — the exact pre-fix suppression condition):
  confirmed `combat_engagement_started/ended`/`combat_resolved`/`combat_damage`/`entity_killed`
  all now fire alongside `combat_kill`, for both `dungeon_crawl` and `urban_political`.

## Files Changed
- `src/engine/pipeline.py` — the real fix (one line).
- `tests/unit/domains/combat_engagement/test_combat_engagement_phase_merge.py` — 2 new tests
  (new file).
- `docs/audits/D19_domain_phase_inventory.md` §12 — documented the real bug and fix.
- `docs/parity_ledger/combat_movement.yaml` — COMB-308.

## Completion Summary
Traced the real, confirmed `ENABLE_COMBAT_ENGAGEMENT=ON` suppression finding to its exact,
deterministic root cause: a missing `.merge()` call in the `combat_engagement` phase's own real
pipeline registration, silently discarding every earlier phase's own accumulated work for the
whole tick whenever this phase actually ran. This is a genuine, previously-undisclosed bug,
contradicting the flag's own documented "gates posture assessment only" scope — not because the
posture-assessment logic itself was wrong, but because of how its own output got chained into
the rest of the tick. Fixed with a minimal, one-line, precedent-matching change. Real corpus
re-verification confirms the fix works for both worlds. The bug's real, practical blast radius
was disclosed honestly as currently zero (the flag is off by default and unused by any shipped
profile), while still being a real, worthwhile fix for any future legitimate use of this flag.
Also surfaced and honestly disclosed, but deliberately left out of scope, a real, much larger,
chronic tick-budget-exceeded condition affecting this corpus at baseline — a separate, real
performance question for a future investigation, not chased here.

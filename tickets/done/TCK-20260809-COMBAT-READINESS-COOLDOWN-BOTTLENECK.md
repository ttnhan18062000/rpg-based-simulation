---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK
phase: open
date: 2026-08-09
tags: [combat, simulation-quality]
---

# TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK

## Title
Investigate whether the real post-attack readiness cooldown (a full -100.0 reset, regenerating
at `readiness_speed=10.0/tick`, i.e. 10 ticks to recover) is now the dominant bottleneck
suppressing sustained combat, now that identity-resolution and pursuit-tracking are fixed

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Direct continuation of the user's own combat-investigation request. With
`TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE` (identity resolution) and
`TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE` (live target tracking) both fixed, real hostile
pairs are now detected and pursuit genuinely converges (real `is_attack_legal` rate improved
from 0% to 44% in `dungeon_crawl`). The next real candidate bottleneck, per
`docs/mechanics/02_combat_laws.md` §7's own documented law: every successful attack resets the
attacker's `readiness` by a full `-100.0`, and passive regeneration is `readiness_speed`
(default `10.0/tick`) — meaning an attacker is legally ineligible to attack again for a real,
minimum 10 ticks after every single attack, regardless of target proximity or continued
hostility.

Combined with `TacticalDecisionSystem.evaluate_entity_intent()`'s own real ~10-tick brain-cadence
gate (`SystemCadence.strategic_intelligence`, confirmed load-bearing by the sibling pursuit-
tracking ticket), this creates a real, plausible compounding effect: an entity that successfully
lands one attack becomes both readiness-blocked AND brain-cadence-blocked for roughly the same
~10-tick window, meaning sustained multi-hit combat sequences (the kind that would actually
produce a kill against anything but the lowest-HP targets) may be structurally rare — not because
hostiles can't be found or reached, but because the attacker can't act again fast enough to
finish what it started before its own target (or the tactical situation) has moved on.

## Scope
1. **Investigate**: live-instrumented, real corpus trace of the actual real gap between
   consecutive `ATTACK` attempts by the same attacker against the same (still-alive) target —
   confirm whether readiness or brain-cadence is the actual binding constraint in practice (they
   may not both apply simultaneously — e.g. if `STUCK-ATTACK-TASK-DEAD-TARGET`'s own fix changes
   how quickly a live attacker re-engages). Check real corpus data for how many real combat
   sequences involve more than one hit from the same attacker vs. a single hit followed by
   disengagement/target-loss.
2. **Determine** whether this is a real design intent (readiness as a deliberate pacing
   mechanism, matching its own documented "cooldown gate" framing) vs. an unintentionally severe
   compounding effect with the brain-cadence gate that undermines sustained combat specifically.
3. **Produce a concrete recommendation** (tune `readiness_speed`, decouple/desynchronize the two
   cadences, or document as intentional pacing) — per the Uncertainty Rule, do not force a fix
   before the evidence narrows the real cause.

## Out of Scope
- Any change to `calculate_damage()`/`resolve_attack()`'s own resolution logic.
- Rebalancing `readiness_speed`'s default value without real, corpus-verified evidence that a
  specific new value measurably improves sustained combat without new side effects.
- `TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET`'s own bug — a related but distinct finding
  (a stuck task retried with no cooldown gate at all, vs. this ticket's own question of whether
  the *intended* cooldown is itself too long relative to real combat pacing needs).

## Acceptance Criteria
- [x] investigation.md presents real, live-instrumented evidence of the actual real gap between
      consecutive attacks by the same attacker, and which constraint (readiness, brain-cadence,
      target loss, or some combination) is empirically binding — **confirmed: readiness alone**,
      exactly 11 real ticks between hits, zero variance across 16 sampled gaps in 3 real combat
      pairs; the brain-cadence gate is confirmed NOT to compound with it for sustained combat
      (a real correction to this ticket's own original hypothesis)
- [x] A concrete recommendation is produced (fix vs. document as intentional), with reasoning —
      **document as confirmed-intentional**: the observed rhythm matches
      `docs/mechanics/02_combat_laws.md` §7's own existing "cooldown gate" framing exactly, with
      no real evidence of unintended severity
- [x] If a fix lands: real corpus re-verification shows a measurable increase in multi-hit combat
      sequences or kill rate — **not applicable**: no fix landed (investigation-only, per
      `plan.md`'s own explicit reasoning)

## Related Tickets
- TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET (same session — a related but distinct
  finding about a *different* combat-pacing failure mode)
- TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE, TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION,
  TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE (DONE, same session — the real
  readiness-mechanics history this ticket builds on)

## Related Docs
- `docs/mechanics/02_combat_laws.md` §7 (Action Legality & the Readiness Gate — the real,
  documented cooldown law this ticket investigates)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/engine/legality.py` (`verify_attack_legality`'s readiness check)
- `src/core/state.py` (`CombatComponent.readiness_speed`)
- `src/engine/cadence.py` (`SystemCadence.strategic_intelligence`)
- `src/engine/domain/cognition.py` (`CognitionDomain.execute_brain`'s cadence gate)

## Assumptions / Open Questions
- Whether readiness cooldown is a deliberate design choice (pacing combat to feel less like
  spam-clicking) that should be left alone, vs. an unintended severity — left open per the
  Uncertainty Rule.

## Implementation Notes
No production code changed — investigation-only, per `plan.md`'s explicit reasoning. Real,
live-instrumented probe (run after the sibling `STUCK-ATTACK-TASK-DEAD-TARGET` fix landed, so
results reflect corrected state) found 3 real (attacker, target) pairs with genuine, sustained,
repeated combat in `dungeon_crawl` (57 real resolved attacks with a real `outcome_kind`, 55
`SURVIVE` + 2 `KILL`). Every real gap between consecutive hits — 16 measurements across the 3
pairs — was exactly 11 ticks, zero variance. This precisely matches the documented readiness law
(`-100.0` reset on a successful attack, `10.0/tick` regen, 10 ticks to recover + 1 tick for the
scheduler to re-admit = 11). Critically, this **refutes** the ticket's own original hypothesis
that readiness cooldown compounds with the ~10-tick tactical-brain-cadence gate: once an entity
has a real, still-legal `target_id` locked in its task payload, the same non-empty-payload
mechanism that caused the sibling stuck-task bug works in the *opposite*, beneficial direction
here — it keeps retrying the same live target every tick readiness allows, with zero dependency
on the brain-cadence stagger. The brain-cadence gate only matters for the *first* engagement
decision and for re-targeting after a target becomes permanently invalid (both already addressed
by sibling tickets), not for an already-locked-on fight. `urban_political` showed zero sustained
pairs in this specific run — a real, honest absence, consistent with this session's own
repeatedly-observed run-to-run variance.

## Test Summary
No `src`/`tests` code changed (confirmed via `git status` — zero diffs). Frontmatter validated
on the ticket and all 3 staging artifacts. The real verification IS the live corpus probe itself
(documented in `investigation.md`), not a unit-test suite.

## Files Changed
- `staging_artifacts/TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK/` — `investigation.md`,
  `plan.md`, `test_plan.md` (new).

## Completion Summary
Investigated the second of the user's own 3 requested combat follow-ups. Found real, precise,
zero-variance evidence (16/16 identical 11-tick gaps across 3 real sustained-combat pairs) that
readiness cooldown alone — not a compounded readiness+brain-cadence effect as originally
hypothesized — governs sustained combat pacing, and that it operates exactly as
`docs/mechanics/02_combat_laws.md` §7 already documents. Honestly corrected the ticket's own
original hypothesis rather than forcing a fix the evidence doesn't support: the brain-cadence
gate does not compound with readiness for an already-engaged fight. Closed as
investigation-only, with a clear, disclosed path for a future, separately-justified balance
change (tuning `readiness_speed`) if the real kill-volume data from the sibling
`SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK` ticket later warrants it.

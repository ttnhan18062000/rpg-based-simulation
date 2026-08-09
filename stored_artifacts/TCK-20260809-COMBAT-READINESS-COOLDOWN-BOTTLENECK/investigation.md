---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK
artifact_type: investigation
tags: [combat, simulation-quality]
---

# Investigation — TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK

## Methodology
Real, live-instrumented probe against a real 2000-tick `dungeon_crawl_seed42`/
`urban_political_seed42` `Kernel.tick_once()` loop (run **after**
`TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET`'s own fix, so the results reflect the
corrected state, not the pre-fix stuck-task condition). Monkey-patched
`CombatActions.execute_attack` to capture every real, resolved attack (`outcome_kind` present on
the **defender's** own returned `EntityUpdate` — confirmed via direct source read that
`execute_attack()`'s attacker-side update never carries `combat`, only `readiness_delta`; the
initial probe draft checked the wrong side and had to be corrected before trusting the data).

## Real, confirmed finding: readiness cooldown is the sole, deterministic pacing mechanism for
## sustained combat — exactly 11 real ticks between consecutive hits, zero variance
`dungeon_crawl` produced 3 real (attacker, target) pairs with genuine, repeated, resolved attacks
(55 `SURVIVE` + 2 `KILL` outcomes, 61 total real dispatches, 57 with a real `outcome_kind`). Every
one of the 3 pairs shows the **exact same real gap between consecutive hits: 11 ticks, with zero
variance** across 16 total gap measurements (17, 5, and 8 distinct-tick hit sequences for the 3
pairs respectively). This matches the documented readiness law
(`docs/mechanics/02_combat_laws.md` §7) precisely: a successful attack resets readiness by a full
`-100.0`; passive regeneration at the default `readiness_speed=10.0/tick` takes exactly 10 ticks
to reach 100.0 again; the 11th tick is when the scheduler's own readiness gate (`ent.combat.
readiness >= 100.0`, `scheduler.py` line 73) re-admits the entity's still-locked `ATTACK` task.
`urban_political` produced zero sustained-combat pairs in this same run (a real, honest absence,
consistent with this session's own repeatedly-observed run-to-run combat-volume variance across
worlds).

## This directly refutes the ticket's own original compounding hypothesis
The ticket's own Request Summary hypothesized that readiness cooldown *and* the tactical-brain
cadence gate (`SystemCadence.strategic_intelligence`, confirmed real by the sibling
`TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE` ticket) compound to block sustained combat. Real
evidence shows this is **not what happens**: once an entity has a real `target_id` locked in its
own `task.payload` (from a deliberate `ATTACK` decision that is currently legal, or was legal and
failed only on a *recoverable* reason), the SAME mechanism that caused the sibling
`STUCK-ATTACK-TASK-DEAD-TARGET` bug (a non-empty `ENTITY_ACT` payload bypasses the brain-cadence
gate entirely) works in the *opposite*, beneficial direction here: the entity keeps retrying the
*same, still-legal* target every tick readiness allows, with **no dependency on the ~10-tick
brain-cadence stagger at all**. The brain-cadence gate only matters for the *first* engagement
decision (already the sibling pursuit-tracking ticket's own real finding) and for re-targeting
after a target becomes permanently invalid (already fixed by the stuck-task ticket) — not for an
already-locked-on, ongoing fight. The observed real rhythm (exactly 11 ticks/hit, matching
readiness alone) confirms readiness is the sole real gate for sustained combat, not a compounded
effect.

## Real recommendation: document as confirmed-intentional pacing, no fix warranted
`docs/mechanics/02_combat_laws.md` §7 already frames readiness explicitly as "a pure attack-
eligibility/cooldown gate" — a deliberate design choice, not an accident. The real, live-
confirmed 11-tick-per-hit rhythm is exactly what that documented law predicts, with zero
unexplained variance across every sampled real occurrence. There is no real evidence in this
ticket's own investigation that this pacing is *unintentionally* severe — it is precisely the
documented mechanic operating exactly as specified. Per the Uncertainty Rule and this session's
own established precedent (`TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE`'s own
honest non-forced closure), this ticket closes as investigation-only: **no fix lands**. If the
real, low absolute combat-kill volume across the corpus (separately tracked by
`TCK-20260809-SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK`) is later judged unsatisfactory, tuning
`readiness_speed`'s own default value (currently `10.0/tick`) would be the real, correct lever —
but that is a genuine game-design/balance decision requiring its own explicit justification and
real corpus-verified before/after comparison, not something this bug-investigation ticket's own
evidence supports deciding unilaterally.

## Docs Requiring Update
None — the existing `docs/mechanics/02_combat_laws.md` §7 documentation already correctly frames
readiness as an intentional cooldown gate; this investigation confirms that framing is accurate,
not stale.

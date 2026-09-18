---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION
phase: open
date: 2026-09-17
tags: [strategy, combat, investigation]
---

# TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION

## Title
Why the decision-driven ATTACK path fires 0–2 times per 2000 ticks while incidental
movement-triggered combat fires 181–2177 — investigate, do not fix

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (PR #214) established that nearly all real
combat in the corpus worlds is **incidental**, not decisional:

| Path | Calls / 1000 ticks |
|---|---|
| `resolve_multi_attack()` — movement's opportunity-attack mechanic | **181 – 2177** |
| `resolve_attack()` — the decision-driven ATTACK-intent path | **0 – 2** |

Entities essentially never *decide* to attack. The entire strategic combat layer — posture
selection, risk evaluation, perceived power, the veto gate — operates on a path that almost never
fires outside the metropolis scenario.

**This is not a new observation, which is what makes it load-bearing.**
`TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION` recorded `resolve_attack(): 0 real calls`
in August, for an entirely unrelated reason. Three independent investigations, three different
questions, the same underlying fact — and nothing connected them until now.

It also explains, without any mechanism being broken, the progression starvation chain measured in
PR #213: few kills → XP never accumulates → no level-ups → `stats_dirty` never fires → agility never
reaches `readiness_speed`.

## Scope
**Investigate and report. Do not fix.** If the repair is substantial it gets its own ticket —
mixing them makes it impossible to tell what the investigation established.

### Four candidate causes, each with a different fix

These are drawn from findings already recorded elsewhere in the repo. Separate them by measurement
rather than by reasoning.

**1. Sticky tasks — the decision function is rarely re-invoked.**
`docs/engine/kernel.md`'s Sticky-Task Law records that 93.7% of attacks are scheduler
re-executions of an already-active task *without re-invoking the decision function*. Directly
corroborated during the combat-judgement scenario work: **one** `evaluate_entity_intent` call was
recorded for the staged goblin across an entire 20-tick run. If tasks are long-lived, decisions are
structurally rare regardless of what the decision logic would choose.

**2. The `hostiles` gate.** `src/engine/tactical.py:308`'s carve-out excludes `DEFEAT_ENEMY` from
the general `obj.kind`-driven branch specifically because it's "handled entirely by the
hostile-engagement branch below (gated on `hostiles`, not `obj.kind`)" — confirmed directly against
the code, the comment states it verbatim. `hostiles` (line 182 onward) is populated from the
entity's own perceived-neighbor filtering earlier in the same function. If perception rarely
populates `hostiles`, the ATTACK branch is unreachable no matter what the objective says.

**3. Corrected 2026-09-17, before filing — the original candidate 3 ("intent-vocabulary
mismatch") does not apply to this call site.** The draft proposed that an `ActionIntent` built by
the decision layer might never be translated into an `EntityUpdate.task`. Checked directly:
`TacticalDecisionSystem.evaluate_entity_intent`'s own hostile-engagement branch (`src/engine/tactical.py`,
roughly lines 442–761 — target selection, kiting, guarding, intercepting, HOLD, SKILL, and the
default ATTACK case) builds `EntityUpdate(task=TaskUpdate(work_kind_set="ENTITY_ACT"/"ENTITY_MOVE",
payload_set={...}))` **directly, at every decision point in that branch** — the exact vocabulary
`ActionRoutingPhase`/`ActionRouter` reads. `ActionIntent`/`ActionIntentAdapter` appear only earlier
in the same function, for the structurally separate harvest/reach-location objective branches —
never in the hostile-engagement branch. There is no `ActionIntent` construction step here to fail
to translate; the vocabulary-mismatch shape is real, but it is what
`TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION` already found and fixed for
`combat_engagement`'s own separate posture decision, a different mechanism, already closed.

**Reframed candidate 3: does the correctly-built ATTACK `TaskUpdate` this branch already returns
survive to real dispatch, or does something drop or overwrite it before the next tick's
`ActionRoutingPhase` reads the resulting task?** This overlaps candidate 1 rather than being a
wholly separate mechanism — a `TaskUpdate` emitted once, if the entity's task then gets
overwritten by a different system before the scheduler dispatches it (or the scheduler's own
sticky-task cadence skips re-evaluating it as described in candidate 1), would look identical to
"the decision never happened" from the outside. Measure whether emission and dispatch actually
diverge; if they don't, fold this back into candidate 1 rather than reporting it as independent.

**4. Objectives never reach `DEFEAT_ENEMY`.** If the objective assigned to entities rarely or never
carries that kind, the decision path is simply not taken.

### The discriminating measurements

Instrument, across the three corpus worlds plus metropolis, per world and never aggregated:

- `evaluate_entity_intent` invocation count per entity per 1000 ticks — tests **(1)**
- how often `hostiles` is non-empty at that call site — tests **(2)**
- ATTACK `TaskUpdate`s *returned* by `evaluate_entity_intent` versus ATTACK tasks actually
  *dispatched* by `ActionRoutingPhase`/`ActionRouter` — tests the reframed **(3)**; a gap between
  them is decisive, and their absence would fold this into candidate 1
- distribution of `obj.kind` across entities — tests **(4)**

Metropolis is the control: the decision path demonstrably *does* fire there, so whatever differs is
the answer.

## Out of Scope
- **Any repair.** Investigation only.
- **Changing the opportunity-attack mechanic.** It may be working exactly as intended; that it
  dominates is the finding, not a defect in it.
- **Re-litigating the posture gate.** It works where the decision path fires (metropolis, 1960 → 822
  cross-faction). Its irrelevance elsewhere is a consequence of this defect, not a fault of its own.
- **Tuning the XP threshold** (`TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME`). That
  ticket stays filed and stays after this one — lowering a threshold to fit starved combat silences
  the signal rather than fixing it.

## Acceptance Criteria
1. Each of the four candidates (candidate 3 in its reframed form) is confirmed or ruled out **by
   measurement**, not by reasoning about the code.
2. Results are reported **per world**. Metropolis and the corpus worlds tell different stories, and
   an average hides both.
3. Any claim that something "never happens" states **which pattern or call site was instrumented** —
   the `heir_entity_id` / `heir_entity_id_set` miss produced this arc's only false verification
   verdict, and search-shaped evidence under-reports in a consistent direction.
4. Positive controls run through a **real Kernel tick**, not a direct service call. PR #213's first
   control bypassed `EvolutionSystem.evaluate()` and produced a false wiring-gap conclusion that had
   to be retracted.
5. The verdict is recorded against `tactical_decision` in the registry, whatever it is.

## Related Tickets
- `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` — groups this ticket with 4 others measuring the
  same causal chain; this ticket is sequenced first (P0, sharpest open question)
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` — produced the path-split measurement
- `TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION` — independent August sighting
- `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS` — the downstream chain
- `TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE` — boss-gate half still open
- `TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION` — closed; the real, different
  mechanism the original candidate 3 was describing (`combat_engagement`'s own dead `ActionIntent`,
  not `tactical_decision`'s)

## Related Docs
- `docs/engine/kernel.md` — the Sticky-Task Law
- `docs/mechanics/04_strategic_cognition.md` — goal hierarchy and interruption resistance

## Related Stored Artifacts
- PR #214's investigation artifacts — the per-world A/B and the path-split trace

## Related Code Areas
- `src/engine/tactical.py` — notably the `:308` carve-out and the hostile-engagement branch
  (~442–761) that emits `TaskUpdate` directly
- `src/engine/domain/action_router.py` — where the veto gate sits, and what it can and cannot see
- `src/engine/movement.py` — `resolve_multi_attack()`, the dominant real path
- `registries/mechanisms.yaml` — `tactical_decision`, `combat_resolution`, `movement`

## Assumptions / Open Questions
1. The candidates are not mutually exclusive; two or more may hold simultaneously, and sticky
   tasks **(1)** would mask the others by making the decision site rare enough to look healthy.
2. Whether the decision path firing more is even desirable is a **design** question, not a defect
   question. If entities correctly decline unfavourable fights, a world where nothing progresses may
   be correct individual behaviour producing an undesirable global outcome. Report the mechanism;
   the disposition is the user's.
3. Metropolis differs from the corpus worlds in ways not yet characterised — density, faction
   composition, hostility. That difference may itself be the answer, in which case this is the
   world-composition family again rather than a logic defect.

## Implementation Notes
The four candidates come from findings already recorded across this arc; rediscovering them would
cost days. Candidate 3 was corrected before filing (see Scope) — the original wording described a
real defect shape (`ActionIntent` built and never translated) that is real elsewhere in this repo
but does not apply to `tactical_decision`'s own ATTACK branch, which builds the correct
`TaskUpdate` vocabulary directly with no `ActionIntent` step to fail to translate.

## Test Summary
To be completed during implementation.

## Files Changed
To be completed during implementation.

## Completion Summary
Open.

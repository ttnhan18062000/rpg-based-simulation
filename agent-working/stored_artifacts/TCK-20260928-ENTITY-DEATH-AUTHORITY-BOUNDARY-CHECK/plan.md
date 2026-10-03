---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK
phase: open
date: 2026-10-01
tags: [engine, lifecycle, combat]
---

# Plan — TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK (Card C1)

This ticket is **a check that produces a verdict**, not a fix. The plan is therefore an
observation plan, and its only code deliverable is test coverage pinning what was observed.

## Scope guard

**No fix is written here.** The ticket's Out of Scope is explicit: a confirmed defect is routed as
separate work. Three things follow:

- No change to `src/engine/world_dynamics.py`, `src/systems/lifecycle_systems/lifecycle.py`,
  `src/engine/apply.py`, or the pipeline phase order — even though the defect is now located
  precisely in the first of those.
- **AC6 is therefore not triggered by this ticket** (no fix touching world-dynamics/lifecycle
  ordering is written), and **AC7 is not triggered** (nothing here alters who decides alive/dead).
  Both bind the follow-up ticket instead. `make semantic-control-plane-drift-check` is
  consequently not run here; recording a clean run would be recording a check of nothing.
- `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION` is untouched and its verified
  comparison of the two ownership writers is **not** re-derived (ticket's Out of Scope).

## Steps

1. **Static trace** of the death-authority boundary: every writer of `lifecycle.active`, every
   writer and reader of `CombatUpdate.outcome_kind`, and the real phase order between them.
   → `investigation.md` Q3/Q4.
2. **Mechanism differential** on `mechanic_scenario_combat_judgement_withdrawal` through real
   `Kernel.tick_once()`, reusing B0's forced-lethal-ATTACK staging, changing exactly one field
   (`hazard_kind`) between arms. → Q2.
3. **Production reachability probe** instrumenting `WorldDynamicsSystem.resolve_dynamics` on an
   unmodified corpus world, with a positive control that injects a synthetic `KILL` so a zero
   reading is distinguishable from a blind instrument. → Q1.
4. **Pin the findings** in `tests/mechanic_scenarios/test_entity_death_authority_boundary.py`,
   following B0's precedent of pinning an assessment ticket's empirical findings so they cannot
   silently regress. Tests assert the *current, defective* behaviour on purpose and say so.
5. **Route** the confirmed defect and record the dated roadmap §3.1 addendum.

## Acceptance-criteria map

| AC | Where satisfied |
|---|---|
| 1 — exactly one exit state | `investigation.md` § Exit state: `DEFECT_CONFIRMED` |
| 2 — harness limitation never reported as "fine" | Not reported as fine at all; the scripted-arm caveat is stated in `investigation.md` Q2 and in the test module docstring, and the unscripted corpus evidence is kept separate |
| 3 — production reachability answered separately from precedence | Q1 (reachability) and Q3 (precedence) are separate answers with different evidence |
| 4 — "exactly once" answered with evidence | Q2, from committed state in both arms, not from the comments |
| 5 — dated addendum in roadmap §3.1 | Routed to `world-rule-catalog-design`, who owns the roadmap; see § Routing |
| 6 — escalate a fix touching world-dynamics/lifecycle ordering | Not triggered here (no fix); recorded as binding on the follow-up ticket |
| 7 — SCP drift check if alive/dead authority changes | Not triggered here (no authority change); recorded as binding on the follow-up ticket |
| 8 — findings routed back to the roadmap track | § Routing in `investigation.md` |

## Routing of the confirmed defect

Two separate pieces of follow-up work, deliberately not merged into one:

1. **Missing HP/alive death branch** — `resolve_lifecycle` recognises only `KILL`/`PERMADEATH`
   and `OLD_AGE`, so hazard, `DEFEAT` and `REBIRTH` routes to `combat.alive=False` all produce an
   entity dead to combat/groups/clans/trauma and alive to lifecycle, with no recorded cause.
   Owner: **`TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`** (already open; this supplies
   the production evidence it lacked).
2. **Unconditional `outcome_kind` overwrite** at `src/engine/world_dynamics.py:39` destroying a
   same-tick `KILL`. **No open ticket covers this**; needs a new one. A fix here touches
   world-dynamics/lifecycle ordering → AC6 escalation and sequencing against
   `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`, which is determinism-sensitive.

Filing those two tickets is a planner decision for the user to approve, not something this
check does unilaterally.

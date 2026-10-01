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

# Investigation — TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK (Card C1)

Observed engine commit: `e9db40f0a` (`origin/main`, 2026-10-01), i.e. at/after
`5d4e4a237` (PR #254) as the ticket's Related Tickets section requires.

## Exit state

**`DEFECT_CONFIRMED`** — routed as separate work, not fixed here (ticket's own Out of Scope).

The defect is **not the one this card hypothesised.** C1 asked whether same-tick combat and hazard
deaths "resolve under a declared rule". The answer is that there is no rule to resolve *under*,
because `resolve_lifecycle` does not recognise hazard death as death at all — so the collision
does not resolve wrongly, it **destroys the combat death record entirely**. See Q4.

## Answers

### Q1 — Is a same-tick combat + hazard kill on one entity reachable in production?

**Partly, and the honest answer splits in two.**

- The **combat half did not occur at all** in unscripted corpus play. 120 ticks of unmodified
  `frontier_marches` @ seed 42 produced **zero** `KILL`/`PERMADEATH` outcomes. Every
  `outcome_kind` seen at the hazard-overwrite point was `SURVIVE` (84), `REJECTED` (34),
  `DEFEAT` (4), `REBIRTH` (1). This is consistent with `registries/mechanisms.yaml`'s
  `tactical_decision` entry (corpus-verified 2026-09-19: 0–2 real `resolve_attack()` calls per
  1000–2000 ticks across three worlds), cited independently by B0's landed test module.
- The **hazard half does occur**, but it is rare per entity-tick: hazard drain > 0 on only
  **0.3%** of eligible entity-ticks (19 / 6567) in that run.
- The **joint event was therefore not observed**. `kills_colliding == 0`. **This is not evidence
  of unreachability** — it is the expected outcome of sampling a conjunction of two independently
  rare events for 120 ticks. Nothing in the code prevents the conjunction; see the mechanism
  proof in Q2.

**However, the committed end-state the collision produces is reached in production constantly, by
other routes.** See Q2's zombie table — that is the finding that matters, and it does not depend
on a combat kill happening.

### Q2 — Committed state, recorded cause, processed exactly once?

**Mechanism proof (scripted, real pipeline).** A single-variable differential on
`mechanic_scenario_combat_judgement_withdrawal` through real `Kernel.tick_once()`, reusing B0's
own forced-lethal-ATTACK staging. `hazard_level` pinned at the world's compiled `1.0` in both
arms; **`hazard_kind` is the only field that differs**:

| arm | `hazard_kind` | drain | after tick 1 | after tick 2 |
|---|---|---|---|---|
| control | `NATURAL_TERRAIN` (orc_clan is immune) | 0 | `active=False`, `death_reason='COMBAT'`, `death_tick=0`, `permadeath=True` | unchanged |
| collision | `ARCANE_CORRUPTION` (not immune) | 10 | `active=True`, `death_reason=None`, `death_tick=None`, `combat.alive=False`, `hp=0`, `permadeath=False` | `active=False`, **`death_reason` still `None`**, `death_tick=None`, `permadeath=False` |

Region `trauma_score` is **identical in both arms** (`0.9995` two ticks after the booked `+1.0`,
which is subject to per-tick trauma decay) — the world books the death either way, while
lifecycle books no death at all in the collision arm.

So the committed state is: **the death is processed exactly once, but as a non-death.** It is
*not* double-processed. The recorded cause is `None`. Lost: `death_reason`, `death_tick`,
`is_permadeath`, and therefore the entire succession/heirloom/lineage dispatch that
`resolve_lifecycle` performs only inside its `if is_dead:` block. Deactivation still happens, one
tick late, via `src/engine/apply.py:109`'s passive HP gate (`active=(new_hp > 0 and ...)`) — which
is `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`'s subject, not a death path.

**Caveat, load-bearing (AC2).** The collision arm is a **scripted** forced-lethal ATTACK. It
proves the mechanism and the routing, exactly as B0's module docstring frames its own tests. It is
**not** a claim that this collision is common in unscripted play — Q1 says the opposite.

**Production evidence, unscripted (no staging, no injection).** The same committed signature —
`combat.alive=False` **and** `lifecycle.active=True` **and** `death_reason=None` — occurs in
unmodified `frontier_marches` @ seed 42 within 120 ticks, on 8 separate ticks:

| tick | entity | hp | hazard drain | `outcome_kind` at overwrite point | attributed cause |
|---|---|---|---|---|---|
| 2 | 63 | 0 | 30 | none | hazard-only |
| 4 | 55 | 0 | 30 | none | hazard-only |
| 5 | 20 | 0 | 20 | none | hazard-only |
| 5 | 21 | 0 | 20 | none | hazard-only |
| 20 | 40 | 0 | 0 | `DEFEAT` | HERO-defender non-lethal |
| 68 | 60 | 0 | 0 | `DEFEAT` | HERO-defender non-lethal |
| 88 | 33 | 0 | 0 | `REBIRTH` | rebirth path |
| 113 | 44 | 0 | 0 | `DEFEAT` | HERO-defender non-lethal |
| 115 | 26 | 0 | 0 | `DEFEAT` | HERO-defender non-lethal |

(The hazard-only rows show no `outcome_kind` because the probe samples *before* `resolve_dynamics`
writes its own hazard update; their drain ≥ hp and no combat update exists.)

**Three independent production routes** reach the same unrecorded-death state. None of them is
the combat+hazard collision. `DEFEAT` arises because `src/engine/combat.py:136` forces
`is_lethal=False` for `EntityRole.HERO` defenders, so a lethal blow on a HERO yields `DEFEAT`
(with `alive_set=False`) rather than `KILL` — and `resolve_lifecycle` ignores `DEFEAT`.

### Q3 — Does the commented precedence actually hold?

**The premise does not hold: those two comments are not a precedence rule.**

`src/systems/world_systems/groups.py:99` and `src/engine/pipeline_phases/clan_lifecycle.py:19`
both assert a **same-tick read-freshness** rule for *downstream consumers* — "respect same-tick
`CombatUpdate(alive_set=False)`, do not read only the start-of-tick entity". Neither states, nor
implies, any precedence between combat and hazard damage. C1's Request Summary describes them as
asserting precedence; that is a misreading, and this check supersedes it.

Worse, those comments are the mechanism by which the inconsistency becomes observable: groups and
clan succession use `is_alive()`/`is_active()` and therefore **do** treat an `alive_set=False`
entity as dead, while `resolve_lifecycle` does not. Group dissolution and clan succession fire for
an entity that lifecycle still considers alive.

The actual ordering, all within one accumulating `update` in one tick
(`src/engine/pipeline.py`): `action_routing` (:297) → `combat_engagement` (:320) →
**`world_dynamics` (:348)** → `lifecycle` (:414). `world_dynamics.py:39` does
`replace(c_upd, ..., outcome_kind="HAZARD", alive_set=(new_hp > 0))` — an **unconditional**
overwrite of whatever `outcome_kind` the victim's update already carried, positioned exactly
between the phase that writes `KILL` and the phase that reads it. Its loop guard
(`world_dynamics.py:31`) reads *committed* state, where a victim killed earlier in this same tick
is still `alive`/`active`, so the victim is always eligible. The `KILL` lands on the **victim's**
own `EntityUpdate` (`combat.py:495`, `:553`) — precisely the key `resolve_lifecycle` reads.

### Q4 — Is a "hazard death" even representable today?

**No, and this is the root cause.** `resolve_lifecycle`
(`src/systems/lifecycle_systems/lifecycle.py:189–218`) has exactly two death branches —
`age_ticks >= max_age_ticks` → `OLD_AGE`, and `outcome_kind in ("KILL","PERMADEATH")` → `COMBAT`.
There is no HP/alive-based branch and no third `death_reason` literal anywhere in `src/`.

So the correct framing of C1's invariant is not an ordering question. `resolve_lifecycle` is the
**sole runtime writer** of `lifecycle.active` for deaths (confirmed: the only other writers of
`active=False` are `archetype_factory.py:131`, which is construction, `camp.py:185`, which is
camps not entities, and `apply.py:109`'s passive HP gate). Every route to `combat.alive=False`
that is not `KILL`/`PERMADEATH`/`OLD_AGE` produces an entity that is dead to combat, dead to
groups and clans, dead to regional trauma, and alive to lifecycle — with no cause recorded.

This is materially different from `CONFIRMED_FINE_WITHIN_SCOPE` and is reported as such, per the
ticket's own Q4 instruction.

## Routing (AC8)

- Primary owner: **`TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`** — the missing
  HP/alive-based death branch is exactly its subject. The `DEFEAT`/`REBIRTH`/hazard rows above are
  its production evidence, which it did not previously have.
- New, not covered by any open ticket: the **unconditional `outcome_kind` overwrite** at
  `world_dynamics.py:39` destroying a same-tick `KILL`. Needs its own ticket; a fix there touches
  world-dynamics/lifecycle ordering and therefore triggers this ticket's **AC6** escalation and
  sequencing against `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`.
- Findings routed back to the systemic-world roadmap track (`world-rule-catalog-design`) for the
  §3.1 dated addendum (AC5).

## AC6 / AC7 status

Neither is triggered **by this ticket**, because this ticket writes no fix and alters nothing about
who decides alive/dead. Both bind the follow-up ticket that changes the overwrite.
`make semantic-control-plane-drift-check` is therefore not run here; AC7's condition ("if any
change alters who decides alive/dead") is not met.

## Instrument honesty

Four instrument errors were found and corrected before any conclusion was drawn, per
`feedback_a_probe_is_an_instrument_that_can_be_wrong`:

1. First differential reported `hazard_drain=0` in *both* arms. Cause: `orc_clan` declares
   `NATURAL_TERRAIN` endurance and the arena's `hazard_kind` is `NATURAL_TERRAIN`, so the hazard
   never bit. A negative reading caused by immunity, not by absence of the defect.
2. `trauma_level` was read via `getattr(..., 0.0)`; the real field is `trauma_score`. The default
   silently reported `0.0`. Corrected — trauma is actually booked in both arms, which reverses the
   reading.
4. The corrected trauma readout was then printed as `round(..., 3)`, showing `1.0` and hiding a
   real per-tick decay (`0.9995`). The first version of the pinning test asserted
   `trauma_score >= 1.0` on the strength of that rounding and failed. Rewritten as an equality
   differential against the control arm, so nothing pins the decay rate by accident. **The
   assertion was not loosened to pass** — the substantive lifecycle assertions passed on the
   first run; only this instrument artifact failed.
3. The first differential changed two fields (`hazard_level` **and** `hazard_kind`). Re-run with
   `hazard_level` pinned at 1.0 so `hazard_kind` is the only variable.

Positive control for the reachability probe: a synthetic `KILL` `outcome_kind` injected onto one
living victim's `EntityUpdate` was counted (`kills_in` 1, `injected` 1), proving `kills_in == 0`
in the clean run means "no kills happened", not "the probe cannot see kills".

Probe sources: `probe_c1.py` (differential) and `probe_c1_reach.py` (reachability), reproduced in
`test_entity_death_authority_boundary.py`.

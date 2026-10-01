---
status: active
layer: engine
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND
phase: open
date: 2026-10-01
tags: [bug, lifecycle, engine, determinism]
---

# Investigation — TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND

Observed at `71c4aa321`. **This investigation discharges AC4's joint-planning requirement** against
`TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`.

The ticket body already carries C1's verified mechanism, phase positions and measured differential —
**not re-derived here** (its own instruction). This file adds only what is new: the joint premise, two
findings that rule out the obvious fixes, and the baseline change caused by R1.

## The joint premise with the sovereignty consolidation (AC4)

Both tickets are about the **same pipeline ordering**: `world_dynamics` (`pipeline.py:348`) runs
**before** `lifecycle` (`pipeline.py:414`).

| | this ticket | sovereignty consolidation |
|---|---|---|
| What the ordering breaks | `world_dynamics` overwrites `outcome_kind` before `lifecycle` reads it | `world_dynamics`' unconditional ownership sweep settles ownership before `lifecycle` writes death influence deltas |
| Tempting fix | move `world_dynamics` after `lifecycle` | move the ownership sweep after `lifecycle` |

So "plan together, from one premise" means answering one question: **do we reorder the pipeline, or make
the data non-destructive?**

### Ruling: this ticket does NOT reorder. The fix is non-destructive data.

**Decisive reason — this ticket's own AC3.** AC3 requires "a named seed/world produces a byte-identical
state hash before and after for a run containing **no** collision". Moving `world_dynamics` relative to
`lifecycle` changes when hazard damage is applied for **every hazard-affected entity**, not only
colliding ones — hazard drain touches 0.3% of entity-ticks in the corpus while collisions were 0 in 120
ticks. A reorder therefore fails AC3 broadly, for runs the fix is not even meant to affect. Secondary
reasons: reordering a 39-phase authoritative pipeline is determinism-sensitive and would have to be
re-validated against the Sliding State ordering rule plus the kernel and authoritative-pipeline
contracts; and the sovereignty ticket itself flags the equivalent move as "a genuine pipeline-ordering
change" rather than a mechanical one.

### What this leaves the sovereignty ticket, and why the two are now separable

The hazard write (`world_dynamics.py:30-40`) and the ownership sweep (`:44+`) are **two independent
blocks inside one function**. Moving the ownership sweep to a later phase does **not** move the hazard
block. Since this ticket's fix is order-independent — it makes `outcome_kind` non-destructive wherever
the phase sits — the sovereignty ticket remains free to choose any of its three recorded outcomes
(accept a one-tick delay, move the settlement sweep after `lifecycle`, or conclude two writers are
correct) **without re-opening this fix**.

**The joint premise to record in both tickets:** *the hazard fix is order-independent and does not move
`world_dynamics`; any later sovereignty consolidation may move the ownership sweep without disturbing
it.* That is the shared premise the constraint demanded, and it is what prevents "two efforts editing
the same ordering from different premises". The sovereignty decision itself is **not** pre-empted here
and stays in its own ticket — a legitimate outcome per its own Scope.

## Finding 1 — a plain non-clobbering conditional is NOT sufficient

The obvious fix ("don't overwrite a terminal `outcome_kind`") preserves the combat death but **silently
destroys the hazard mechanic's own observability**, violating this ticket's AC2.

`src/observability/event_extractor.py:778`:
```python
if not _push_shapers_active and combat_upd and getattr(combat_upd, "outcome_kind", None) == "HAZARD":
    ... event_type="hazard_drain_applied", event_category="combat",
```

`hazard_drain_applied` is emitted **solely** from `outcome_kind == "HAZARD"`. So if the write declines to
clobber a `KILL`, the colliding entity emits no `hazard_drain_applied` at all — hazard damage is applied
to its HP with no record that hazard touched it. AC2 explicitly requires preserving "the
`hazard_drain_applied` observability path".

**Therefore the fix needs two halves:** hazard application must be signalled **independently of
`outcome_kind`**, and `outcome_kind` must be left alone when it already holds a terminal combat outcome.

## Finding 2 — `alive_set` can also be clobbered, and must be guarded

`world_dynamics.py:39` writes `alive_set=(new_hp > 0)` unconditionally. `new_hp` is computed from
`entity.combat.hp + c_upd.hp_delta - hazard_dmg`, so it does account for the accumulated combat damage
and in practice stays `0` for a combat victim. But the write is still unconditional, and
`CombatPatch.apply` (`patches.py:322`) honours `alive_set` **over** the HP-derived value:
`alive=(new_hp > 0) if u_com.alive_set is None else u_com.alive_set`. A future change to hazard
arithmetic, or any path where combat sets `alive_set=False` while HP remains positive (`DEFEAT` forces
`is_lethal=False` but still sets `alive=False`), would let hazard **resurrect** a defeated entity.
**Guard it: hazard must never flip `alive_set` from `False` to `True`.** This is latent today rather
than observed, and is recorded as a guard rather than a claimed defect.

## Finding 3 — the baseline this ticket must restore has CHANGED since it was filed (R1)

**AC2's "hazard-only drain deaths keep their current observable behaviour" is no longer achievable as
written, and must be rewritten.** The batch
`TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER` +
`...-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE` (R1, user-accepted) removes the HP term from
`apply.py`'s lifecycle `active=` write, making `resolve_lifecycle` the sole declared authority for
HP-death deactivation.

Consequence, measured by `rpg-implementer` (frontier_marches, seed 42, 400 ticks, order-of-magnitude per
its own caveat — the world's population varies under load):

| tree | HP-0 entities, by `(active, death_reason, alive)` |
|---|---|
| base `71c4aa321` | `{(False, None, False): 34}` — deactivated late and silently |
| R1 branch | `{(False, 'DEFEAT', False): 20, (True, None, False): 8}` |

Those **8 are this ticket's population**: `active=True`, `hp=0`, `alive=False`, `death_reason=None`,
**permanently** — because `outcome_kind` is `"HAZARD"`, `resolve_lifecycle` has no `HAZARD` branch, and
after R1 nothing else deactivates them. First-seen ticks 2, 4, 5 (monsters and two `GUARD`s), 151 (a
`HERO`, `generation=1`), 167, 302, 303; `hunger < 17` and passive cause `None` throughout, which rules
out the biological route and confirms they are the hazard population rather than the sibling's.

So this ticket must now also **record the hazard death**, not merely stop the overwrite. That is not
scope creep: the ticket's own **Q2 answer** already states it — "this ticket (decline to clobber a
non-lethal outcome, or carry hazard lethality in a separate field) is the prerequisite; the `HAZARD`
classification lands **with or after** it". R1 turns "with or after" into "with", because "after" now
means shipping permanent zombies. **The ticket's Out of Scope needs amending**: its exclusion of a
`death_reason` branch was aimed at the *HP/alive* branch owned by the sibling, and a `HAZARD` branch
keyed on `outcome_kind` is the same shape as the existing `KILL`/`PERMADEATH` ones, not the sibling's.

## Q1 — collision precedence: no law exists, so a rule must be declared

Checked: `docs/mechanics/05_world_evolution.md` contains no hazard-death precedence rule (no match for
hazard+death/lethal/precedence), `02_combat_laws.md` has none either, and C1's own resolution records
that "there is no declared rule" for this boundary. So Q1 cannot be answered by citation and needs a
**declared** rule plus an `intentional_divergences.md` entry, exactly as Q1 anticipated.

**Recommendation: the combat kill wins; the collision records `death_reason='COMBAT'`.** Rationale:
a combat kill is the *proximate, attributable* cause and carries a `killer_id`, succession, heirloom and
lineage consequences; ambient hazard drain carries none of that. Recording `HAZARD` would discard
strictly more durable information than recording `COMBAT` does, and CAUSE-01/CAUSE-05 favour keeping the
cause that is real and attributable over the one that merely coincided. This also matches the ticket's
own AC1, which already specifies `death_reason='COMBAT'` matching the hazard-free control arm — so AC1
had effectively pre-answered Q1, and this records *why* rather than leaving it an implementation guess.
The hazard contribution is not lost: Finding 1's independent hazard signal still records that hazard was
applied.

**Referred to `world-rule-catalog-design` for ruling (2026-10-01)** since it is a rule-semantics call,
not an implementation detail. Flagged in the plan as the one item that should not be implemented from my
recommendation alone.

## Q3 — `hp_delta` double-counting

Still open, as the ticket records. `new_hp` at `:38` reads `entity.combat.hp + c_upd.hp_delta -
hazard_dmg`, which looks correct (it does not re-apply combat damage), and `hp` floors at 0 either way,
so the arithmetic is "not provably wrong" rather than verified. Worth an explicit assertion during
implementation now that a collision will be a tested path rather than a theoretical one.

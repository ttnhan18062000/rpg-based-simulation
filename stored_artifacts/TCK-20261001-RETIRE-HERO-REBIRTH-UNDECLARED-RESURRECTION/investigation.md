---
status: active
layer: combat
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION
phase: open
date: 2026-10-01
tags: [lifecycle, combat, progression, architecture]
---

# Investigation — TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION

Observed at `71c4aa321`. The rule analysis is in the ticket body and is **not** re-derived here (STR-02,
ID-02, CAUSE-04, ID-06, verified directly by the planner at
`docs/world_rules/magic-supernatural/supernatural-transformation.md:84`). This file maps the **code
blast radius**, which is larger than the ticket's first draft assumed.

## Finding 1 — there are TWO rebirth sites, and the one that actually fires is the second

The ticket's Related Code Areas named `combat.py:170-187`. That is `resolve_attack`. **There is a
second, identical branch at `combat.py:401-413`, inside `resolve_multi_attack`** — and its own comment
says the first one is dead:

> "this branch previously existed only in `resolve_attack`, the one real combat function this corpus's
> own AI never actually calls (0 real calls in 2000-tick runs), making Hero's Journey rebirth
> structurally unreachable regardless of HERO population size or kill rate. `resolve_multi_attack`
> already computes the correct classification … this only ports the consumption of that value into the
> path that's actually exercised (`movement.py`'s opportunity-attack mechanic)."
> — ported by `TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION`

**Both must be retired.** Retiring only `:183` would leave rebirth fully live on the only path that
runs. This also explains the single `REBIRTH` in C1's 120-tick corpus run: it arrived through the
opportunity-attack path, not through `resolve_attack`.

It is also a second, independent confirmation of the ticket's premise: an earlier ticket already found
that rebirth was *structurally unreachable* and "fixed" the reachability without anyone asking whether
the mechanic should exist. That is the same pattern — hardening an undeclared mechanic instead of
questioning it — that this ticket stops.

## Finding 2 — `generation` is baked into durable `CorpseState`

`src/engine/apply_plan.py:340-348` constructs every corpse with `generation=life.generation`:

```python
corpse = CorpseState(
    id=corpse_id, original_entity_id=e_id, position=nav.position,
    items=list(inv.items), decay_tick=tick + 100,
    generation=life.generation,
)
```

So the rebirth count is **durable state on a second object**, not just a field on the entity. Whatever
Q2 decides, `CorpseState.generation` has to be decided with it — it cannot silently keep carrying a
retired meaning. Under removal it must go too; under re-grounding its meaning changes retroactively for
every already-persisted corpse, which is the "retroactively change the meaning of recorded data" hazard
flagged to the rule owner.

## Finding 3 — an observability diagnostic depends on `generation` meaning "rebirth count"

`src/observability/event_extractor.py:1283-1292` emits `life_arc_incoherent` when:

```python
_cap_generation >= _LATE_GENERATION_THRESHOLD
and _cap_levels_numeric and _cap_curr_level <= 1
and not set(_cap_curr_skills)
```

i.e. *"a late-generation entity that is still level ≤ 1 with no skills is incoherent."* That inference is
**only valid if `generation` counts completed lives that should have accumulated capability.** A lineage
generation (birth order) implies nothing about an individual's level or skills — a 4th-generation
newborn is legitimately level 1 with no skills.

**So this diagnostic loses its basis when rebirth is retired and must be retired or re-grounded with
it.** Leaving it would emit a false `life_arc_incoherent` for ordinary young descendants under any
lineage-generation reading. `event_extractor.py:66`'s comment ("Minimum `lifecycle.generation` — a
completed Hero's Journey rebirth already occurred") states the dependency explicitly; it is the same
`_LATE_GENERATION_THRESHOLD` constant's rationale.

This is the strongest code-side argument for Q2 = **remove**: the only two consumers of `generation`'s
*meaning* (this diagnostic and `CorpseState`) both depend on the rebirth reading, so re-grounding
silently invalidates both rather than preserving anything.

## Finding 4 — `generation_delta` plumbing is wider than the two rebirth sites

`generation_delta` is lifted onto a `LifecycleUpdate` at four call sites, all with the same guard shape:
`src/engine/movement.py:250-252`, `domain/combat_actions.py:111-113`, `domain/skill_actions.py:125-127`,
`domain/aoe_actions.py:75-77`; applied at `patches.py:82`
(`generation=new_lifecycle.generation + u_life.generation_delta`). With both rebirth sites retired,
`generation_delta` is always `0` and every one of those guards reduces to
`is_permadeath_set is not None`.

**Do not leave `generation_delta` as dead plumbing.** Retire it with the mechanic, or the next reader
finds a field that exists, is threaded through four call sites and a patch, and can never be non-zero —
which is exactly the kind of undeclared vestigial structure that made rebirth hard to see. Note this
interacts with the hazard ticket's R4 finding: those same four guards are why
`movement.py:248-252` produces `lifecycle_upd=None` for a terminal `DEFEAT`.

## Q1 — answered by the rule owner, and verified

**Fold `REBIRTH` and `PERMADEATH` into `KILL`; retire both outcome kinds. Keep `is_permadeath`.**

Verified basis: LIFE-01's single final marker was never the `PERMADEATH` *outcome kind* — LIFE-01's own
evidence names the lifecycle field `LifecycleUpdate.is_permadeath_set`, and ID-05's finding is phrased
`active=False, is_permadeath_set=True`. `PERMADEATH` is a combat classification *label*;
`is_permadeath` is the lifecycle *fact*. Consequences:

- Both labels drop out of `_DEFEATED_OUTCOME_KINDS` (`learning_outcome.py:33`). `KILL` is already in it,
  so the combat-learning layer sees the same "defender lost" signal under one label — no change in what
  learning believes.
- **`is_permadeath` stays a separately tracked fact** even though it becomes `True` for every recorded
  death and so looks redundant with "has a `death_reason`". It is the hook STR-02 requires: a future
  *declared* resurrection process would be the only thing permitted to produce a recorded death with
  `is_permadeath False`. **Flagged explicitly so it is not "simplified away" later as redundant.**

## Q2 — `lifecycle.generation`: delegated by the user to the rule owner, answer pending

The user's answer to "remove / re-ground / defer" was "ask `world-rule-catalog-design`", so the decision
is the owner's. Its recommendation is **remove**; Findings 2 and 3 above are new code-side evidence that
supports it (both consumers of the field's *meaning* depend on the rebirth reading, so re-grounding
preserves nothing and silently invalidates both). The planner has flagged to the owner the one argument
against — that the user's reproduction/succession model may later want a stored lineage depth — and the
retroactive-meaning hazard for already-persisted `CorpseState.generation`.

**Do not implement Q2 until the owner answers.** Q1 and Findings 1/4 are unblocked.

## Sequencing

This ticket is a **merge blocker** for the death batch, alongside
`TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND`:

- With the death batch's R1 landed and the rebirth restore (correctly) dropped, a `REBIRTH` defender ends
  `hp=0`, `alive=False`, `generation+1`, `active=True` and **nothing deactivates it** — the `DEFEAT`
  branch ignores `REBIRTH` and the HERO branch is held. `REBIRTH` is therefore a second zombie class
  alongside the hazard population (`rpg-implementer`, measured).
- Q1's fold-into-`KILL` closes it: no `REBIRTH` is emitted, so the lethal hit records an ordinary
  `COMBAT` death and `resolve_lifecycle` deactivates it as the sole authority.
- It also **releases the death batch's HERO `death_reason` hold** automatically, because that branch is
  already role-blind and the hold exists purely because `REBIRTH` had no deactivator.

`rpg-implementer` is taking the hazard fix first (its call, agreed — this ticket had no artifacts and two
code-shaping open questions at the time).

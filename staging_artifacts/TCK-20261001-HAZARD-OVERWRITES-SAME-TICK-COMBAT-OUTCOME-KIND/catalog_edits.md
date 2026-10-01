---
status: active
layer: engine
authority: P1
audience: agent
artifact_type: report
ticket_id: TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND
phase: open
date: 2026-10-01
tags: [bug, lifecycle, engine, determinism]
---

# Verbatim Mechanics Bible edit — supplied by `world-rule-catalog-design`, 2026-10-01

Answers the ticket's **Q1**. Relayed verbatim so the exact text lives in git rather than only in a
session transcript.

## The ruling, and why my recommendation's *reasoning* was wrong

I recommended "the combat kill wins" because it carries more durable information. **The owner ruled the
same outcome on different grounds — sufficiency plus declared phase order — and that difference changes
an edge case my reasoning would have gotten wrong.**

A `KILL` means combat damage **alone** was sufficient to take the subject from `hp > 0` to `hp <= 0`
(`combat.py:163-171` decides from `defender.combat.hp - damage`: combat damage only, against
start-of-tick HP), and combat resolves first (`pipeline.py:297`/`:320`, before `world_dynamics` at
`:348`). The hazard drain then lands on a subject combat has already killed, so recording `HAZARD` would
assert a causal link that was not there:

- **CAUSE-03** — temporal adjacency is not causation.
- **CAUSE-06** — a record must not invent a causal relation.
- **LIMIT-04** — pushing HP further below zero is not a cause.

The information-content argument is a *consequence*, not the justification. The rule is therefore **not**
"combat always wins"; it is **"the first cause in declared phase order whose own effect was sufficient to
reach 0 HP wins"** — which also decides the cases information-content cannot.

**No new world-rule Rule ID is needed.** The owner ruled this an application of CAUSE-03, CAUSE-06,
LIMIT-04 and BODY-07, so by the admission test it is a reference, not a new Rule. The engine-level law
belongs in the Mechanics Bible, below.

Also ruled: omitting the hazard contribution from `death_reason` violates nothing, because the hazard
drain is a real **exposure** event (BODY-07) but not a cause of *this* death. The independent
hazard-applied field (plan S1) is the correct representation — **but it must not be presented as a
secondary death cause**, which would violate CAUSE-06 in the other direction.

## NOT FINAL — one clause depends on an open user decision

The **`REBIRTH` bullet's** treatment is contingent on an unresolved question the owner raised and the
user has escalated back to it: whether hero rebirth is consistent with the world-rule model at all,
given that reproduction and lineage (LIFE-04 / ID-04) already provide continuity through a *new*
identity while `REBIRTH` provides it through the *same* identity. Until that resolves:

- **Do not land this block yet.**
- **Do not land any `death_reason` for a HERO** on either this ticket's hazard path or the death batch's
  passive-cause path.

Permitted substitutions when it does land: `<DEFEAT_REASON>`, `<TICKET>`, and the `REBIRTH` bullet's
final clause once the hero-rebirth question is answered. **Nothing else.**

---

## EDIT — `docs/mechanics/01_entity_anatomy.md`

Insert as a **new subsection at the end of §4 "Biological Laws (Decay & Needs)"**, before the `---` that
precedes §5:

```
### Death Attribution (Same-Tick Causes)
A death records exactly one `death_reason`: the first cause, in declared pipeline phase order, whose own effect was sufficient to take the subject from `hp > 0` to `hp <= 0`. Combat resolves before world dynamics, so:
- If a combat outcome alone reached 0 HP (`KILL`, `PERMADEATH`, or terminal `DEFEAT`), its classification stands (`COMBAT` or `<DEFEAT_REASON>`). Same-tick hazard drain applied afterwards is recorded as an exposure event, not as a cause of the death.
- If combat damage alone did not reach 0 HP and hazard drain then did, the death records `HAZARD`. The earlier combat damage stays traceable through its own events as part of the accumulated condition.
- A same-tick combat `REBIRTH` is never overridden by hazard drain.
- Hazard drain can cause death only where `EnvironmentService.calculate_hazard_drain()` returns a nonzero drain after the subject's immunities.
Basis: world rules CAUSE-03, CAUSE-06, LIMIT-04, BODY-07 (`docs/world_rules/`). Declared by `<TICKET>`.
```

**Acceptance (owner's wording):** "this block only, plus a parity entry. If the implementation's
semantics differ from any bullet, stop and send me the delta."

## Edge cases this rule decides — all four must be pinned

The owner was explicit that the AC set should cover these, because the sufficiency rule (not a
"combat wins" rule) is what decides them:

1. **Combat non-lethal (`SURVIVE`) + hazard drain reaches 0** → `death_reason = HAZARD`. Hazard was the
   decisive producer. **This is the case a "combat always wins" implementation gets wrong.**
2. **Terminal `DEFEAT` + same-tick hazard** → the `DEFEAT` classification stands, since combat was
   sufficient.
3. **`REBIRTH` + same-tick lethal hazard** → the hero ends **reborn**: `alive`, `max_hp`,
   `generation + 1`, **not** permadeath. Today the overwrite erases `REBIRTH`, so a gen 1–3 hero would
   die permanently by `HAZARD` — a LIFE-02 violation *with* permadeath. Note the rebirth restore lands in
   lifecycle (after `:348`), so this needs an explicit test, not an inference.
4. **An immune subject cannot die of `HAZARD`** — automatic, since the drain is 0, but pin it.

Plus: hazard deaths are **final** (`is_permadeath = True`), by the same sufficiency reasoning.

---
status: active
layer: combat
authority: P1
audience: agent
artifact_type: report
ticket_id: TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION
phase: open
date: 2026-10-01
tags: [lifecycle, combat, progression, architecture]
---

# Verbatim catalog edits K1–K6 — supplied by `world-rule-catalog-design`, 2026-10-01

The **six remaining** catalog docs that still list the retired `REBIRTH`/`PERMADEATH` outcome kinds as
live. Separate from `catalog_edits.md` (C1–C5), which is already applied.

Relayed verbatim because these are whole-block replacements and `rpg-implementer` correctly refused to
reconstruct them from a prose summary.

## Rules of application

1. Apply on **`entity-death-cause-at-writer`**, as a follow-up push to **PR #276**. Not blocking it.
2. **Bump `last_verified` to `"2026-10-01"`** in all three files: `conflict-combat.md`,
   `body-condition.md`, `capability-progression.md`.
3. **The validator must pass and no other spans may change.**
4. Every anchor below carries a **file-unique neighbouring word**, deliberately — the six-value
   `outcome_kind` list appears near-identically in **two** files. **Still check uniqueness before each
   replace.**
5. **If an anchor fails to match, STOP and report the delta** — do not paraphrase.

### Two transcription notes — read before applying

- **Quote escaping.** The owner's message rendered inner double quotes as `\"` (message-level escaping).
  The blocks below use **plain double quotes**, which is what belongs in the markdown. If any anchor
  fails on a quote character, that is the reason — report it rather than improvising.
- **K4's conditional is RESOLVED.** The owner asked whether the passive cause has a real `death_reason`
  literal, and permitted that substitution as the only deviation. Verified on the branch:
  `lifecycle.py:229` is `death_reason = entity.lifecycle.passive_death_cause.value`, and
  `PassiveDeathCause` (`src/core/enums.py:29-30`) is `STARVATION` / `SLEEP_DEPRIVATION`. The full
  `death_reason` set on the branch is `OLD_AGE` / `COMBAT` / `DEFEAT` / `HAZARD` / `STARVATION` /
  `SLEEP_DEPRIVATION`. **K4 below already has the substitution applied.**

### Status correction carried into these edits (owner's, accepted)

The planner initially wrote "only the enumerations are stale". That undersells it. Because every zero-HP
outcome is now a recorded death, `conflict-combat`'s "defeat ≠ death" and BODY-02's "zero HP doesn't
determine what happens next" both drop from *realised* to **permitted, not currently realised** —
inheriting LIFE-02's own status, as INHERITED rules should. **All Dispositions stay; nothing is
invalidated.** "Victory ≠ kill" remains realised via `SURVIVE`, `REJECTED` and `FLED`.

---

## K1 (Kind A — quoted Rule text) — `docs/world_rules/capability-progression/conflict-combat.md`

Replace exactly:

```
> A combat encounter resolves into one of several distinct outcomes — kill, non-lethal defeat,
> rebirth, permanent death, mutual survival, rejection, or withdrawal — never a binary
> victory/death pair.
```

with:

```
> A combat encounter resolves into one of several distinct outcomes — for example kill,
> defeat (which need not mean death; LIFE-02), mutual survival, rejection, or withdrawal —
> never a binary victory/death pair. (Example list revised 2026-10-01: it no longer names
> specific mechanisms; the former `REBIRTH`/`PERMADEATH` outcomes were retired.)
```

## K2 (Kind B — evidence) — same file

Replace the span **from** `**Repository evidence: SUPPORTED, with one additional confirmed outcome beyond Batch 05's own`
**through** `confirms withdrawal is a genuine seventh category, not merely combat resolving to one of the six`
+ `` `CombatUpdate.outcome_kind` values. `` with:

```
**Repository evidence: PARTIAL (revised 2026-10-01).** "Victory ≠ kill" is SUPPORTED:
`src/engine/combat.py`'s real `outcome_kind` values are `KILL`/`DEFEAT`/`SURVIVE`/`REJECTED`,
plus a separately-produced `FLED` (`src/engine/movement.py`'s
`combat_escape="EVASIVE_SUCCESS"`), so an encounter can end without anyone dying. "Defeat ≠
death" is permitted, not currently realised, inherited from LIFE-02's own status: terminal
`DEFEAT` is now a recorded, classified death (`death_reason` `DEFEAT`). The former `REBIRTH`/
`PERMADEATH` outcomes were retired as an undeclared resurrection
(`TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION`; see STR-02).
```

**Keep the following sentence unchanged:** `**Confirmed MISSING**, checked directly: no surrender,
capture...`

## K3 (Kind A — quoted Rule text) — `docs/world_rules/life-body/body-condition.md`, BODY-02

Replace exactly:

```
> classification (`KILL`/`DEFEAT`/`REBIRTH`/`PERMADEATH`), not one hardcoded "death" transition.
```

with:

```
> classification (a declared outcome and, where it is a death, a declared cause), not one
> hardcoded "death" transition. (Wording revised 2026-10-01: it no longer names retired mechanisms.)
```

## K4 (Kind B — evidence) — same file, BODY-02 evidence

Replace the span **from** `**Repository evidence: SUPPORTED**, reusing LIFE-02's own evidence: `` `new_hp <= 0` is the ``
**through** `predetermined result.` with (**substitution already applied**):

```
**Repository evidence: PARTIAL (revised 2026-10-01), reusing LIFE-02's own status.**
`new_hp <= 0` is the trigger condition, and a real classification follows: combat classifies
`KILL` or terminal `DEFEAT`, and lifecycle records each death with a declared cause
(`COMBAT`, `DEFEAT`, `HAZARD`, `STARVATION` or `SLEEP_DEPRIVATION`). Classification of
*cause* is SUPPORTED. Classification of *fate* is not currently realised: every zero-HP
outcome today ends in a recorded death, and no declared route to continued existence exists
(permitted by LIFE-02, not required). The former generation/rebirth-eligibility check cited
here was retired with hero `REBIRTH`.
```

## K5 (Kind B) — `docs/world_rules/capability-progression/capability-progression.md`

Replace exactly:

```
near-death survival (beyond `REBIRTH`'s own generation increment,
  which is a lifecycle fact, not a capability grant)
```

with:

```
near-death survival (the former hero `REBIRTH` generation increment, retired 2026-10-01, was a
  lifecycle fact, not a capability grant)
```

## K6 (Kind B) — same file

Replace exactly:

```
`outcome_kind` values: `KILL`/`DEFEAT`/`REBIRTH`/`PERMADEATH`/`SURVIVE`/`REJECTED`
  (`src/engine/combat.py`)
```

with:

```
`outcome_kind` values: `KILL`/`DEFEAT`/`SURVIVE`/`REJECTED` (`src/engine/combat.py`; `REBIRTH`/
  `PERMADEATH` retired 2026-10-01)
```

**The "Confirmed real" text before it and the `FLED` text after it stay unchanged.**

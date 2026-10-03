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

# Verbatim catalog edits C1–C5 — supplied by `world-rule-catalog-design`, 2026-10-01

Relayed verbatim so the exact strings live in git rather than only in a session transcript.

## Rules of application — from the owner

1. **Land only in this ticket's commit**, with the code that makes the text true.
2. Written against the state **after both** the death batch (its EDITs A–F and R2) **and** this ticket
   have landed. It uses **whole-block replacements** deliberately, to survive anchor drift from those
   earlier edits.
3. **Permitted substitutions, exactly two:** `<DATE>` → this ticket's landing date; `<DEFEAT_REASON>` →
   the death batch's chosen `death_reason` literal for terminal `DEFEAT`.
4. **Bump `last_verified` to `<DATE>` in all three files.** The validator must pass and no other spans
   may change.
5. **If this ticket's or the death batch's final semantics differ from anything stated here, STOP and
   send the owner the delta — do not adapt the text.**
6. Verify each anchor is unique before replacing (an owner-supplied anchor for one of these same files
   turned out to occur 8 times earlier today).

## Withdrawn earlier edits — do not apply

The owner **withdrew** EDITs **R1, R3 and R4** from the death batch when it reversed its approval of the
rebirth restore (R1 declared a BODY-05 HP-restoration path that will not exist; R3/R4 declared LIFE-02
"resolved via `REBIRTH`"). `rpg-implementer` has reverted all three to HEAD. **EDIT R2** (the LIFE-01
wording correction) **still stands and is kept.** C1–C5 below are the replacements.

---

## C1 — `docs/world_rules/life-body/lifecycle.md`, LIFE-02

Replace everything from the line beginning `**Repository evidence:` up to (**not** including) the
`**Scenarios:**` line with:

```
**Repository evidence: PERMITTED, NOT CURRENTLY REALISED (revised `<DATE>`, `TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION`).** `CombatResolutionSystem` classifies an outcome that takes HP to zero as `KILL`, or as terminal `DEFEAT` when the attack is non-lethal (`is_lethal=False`: an opportunity attack, `src/engine/movement.py:241`, `combat.py:251-252`). Lifecycle records both as real, final deaths with distinct `death_reason`s (`COMBAT` / `<DEFEAT_REASON>`). No current mechanism routes a defeat toward continued existence: this Rule permits such a route, does not require one, and none exists today.

**History.** Until 2026-10-01 this Rule cited the hero `REBIRTH` outcome (the same entity continuing with `generation + 1`) as its evidence. That outcome was retired because in substance it was an undeclared resurrection (STR-02), gated on a role label (ID-02, CAUSE-04), and it never worked at runtime (every `REBIRTH` ended in a permanent, unrecorded deactivation). Calling it a "non-lethal defeat" was a reframing that hid it from STR-02. Any future route from defeat to continued existence must be a declared mechanism, and if it reverses a death, it must satisfy STR-02.
```

## C2 — same file, LIFE-01

Insert this sentence at the **end of LIFE-01's Repository evidence paragraph** (after the EDIT R2 wording
already landed) — note the **leading space**:

```
 No current mechanism produces a non-permanent loss of active participation: that half of this Rule is permitted, not currently realised (the former hero `REBIRTH` was retired `<DATE>`; see LIFE-02 and STR-02). `is_permadeath_set` remains the single final-death marker, and is the field any future declared resurrection process (STR-02) would have to leave `False`.
```

## C3 — same file, "## Open questions carried forward" item 1

In the "Resolved 2026-10-01" text landed by EDIT D, replace the sentence (it **wraps**):

```
A `HERO` never reaches it (always
   rebirth-eligible, `combat_rewards.py:44-51`/`:106`).
```

with:

```
Since the hero rebirth retirement (`<DATE>`), any defender can reach it through an opportunity attack; no role is exempt.
```

## C4 — `docs/world_rules/magic-supernatural/supernatural-transformation.md`, STR-02

Replace the whole paragraph beginning `**Repository evidence: MISSING.**` and ending
`...a declared reversal process to exist).` with:

```
**Repository evidence: MISSING (corrected `<DATE>`).** No declared resurrection, undeath, or comparable death-reversal mechanism exists in this repository. Correction: until `<DATE>` the repository did contain an *undeclared* one, the hero `REBIRTH` outcome, where the same `entity_id` continued with `generation + 1` after HP reached zero. It recorded no death, had no declared process, and assumed same-identity continuity, so it failed all three of this Rule's requirements. The original search missed it because it was framed as a combat outcome rather than as death reversal. It was retired by `TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION`. Death is now a real, permanent, historical event with no reversal path, which is consistent with, though narrower than, this Rule's target semantics (it permits, but does not require, a declared reversal process).
```

## C5 — `docs/world_rules/scenarios/life-body-batch-05.md`, LB-S02

Replace the **entire** `- **Result:` bullet (from `- **Result:` up to the blank line before `## LB-S03`)
with:

```
- **Result: permitted, not currently realised (revised `<DATE>`).** No current mechanism lets a defeated subject survive. `KILL` and terminal `DEFEAT` (opportunity attack, `is_lethal=False`) are both recorded, classified, final deaths. The former hero `REBIRTH` previously cited here was an undeclared resurrection and has been retired (`TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION`; see LIFE-02 and STR-02). The scenario's actual requirement, no *accidental* `defeat = death` assumption, still holds: each death is a declared lifecycle classification, never an implicit consequence of HP reaching zero.
```

---

## Explicitly NOT changed

`docs/plans/systemic_world/roadmap.md` §3.1's addendum stating that "a HERO is always rebirth-eligible
and resolves to `REBIRTH`" **stays as written**. It is a dated record of the C1 run at `e9db40f0a` and
was true then. Dated point-in-time evidence is not rewritten retroactively — the owner was explicit
about this, and so is this project's own practice.

Likewise, previously recorded `life_arc_incoherent` events keep their original meaning (a rebirth count
as of the run that emitted them), even though the detector is retired.

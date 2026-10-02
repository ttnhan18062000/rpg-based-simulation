---
status: active
layer: engine
authority: P1
audience: agent
artifact_type: report
ticket_id: TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE
phase: open
date: 2026-10-01
tags: [bug, lifecycle, engine]
---

# Verbatim catalog edits R1–R4 — supplied by `world-rule-catalog-design`, 2026-10-01

Relayed **verbatim** from the rule owner's 2026-10-01 message, at the implementer's request (it
correctly refused to paraphrase). This file exists so the exact strings live in git rather than only in
a session transcript.

## Rules of application — from the owner, not negotiable here

1. **Apply these ONLY in the same commit as the code that makes them true.** Never ahead of it. They
   assert behaviour that does not exist on `main`.
2. **Permitted substitutions are exactly two:** `<DEFEAT_REASON>` → the actual `death_reason` literal
   chosen for terminal `DEFEAT`; `<TICKET>` → the implementing ticket ID. **Nothing else may change.**
3. **If any anchor fails to match exactly, STOP and send the owner the delta — do not paraphrase.**
   Watch the line wraps in R2 and R3.
4. **If the user changes decision 1, 2 or 4, or the implementation differs from the recorded decisions,
   stop and send the owner the delta rather than adapting the text.**
5. **Verify each anchor is unique before replacing.** Earlier today an anchor the owner supplied for
   this same LB-S02 file (`- **Result: covered.**`) turned out to occur **8 times**; it was resolved by
   anchoring on the unique continuation instead, and the owner confirmed that was correct.

Note R3's and R4's anchors are written against the **post-EDIT-B/E state** of these files — i.e. the
corrections already applied and pushed in `11c7d8e56`. They will not match the pre-`11c7d8e56` text.

---

## EDIT R1 — `docs/world_rules/life-body/body-condition.md`, BODY-05

Directly after the paragraph that ends `...whenever one is built.` and **before** `**Scenarios:**`,
insert:

```
**Update (2026-10-01, `<TICKET>`):** one declared HP-restoration path now exists: hero `REBIRTH` restores `combat.hp` to `max_hp` and `alive` to `True`, declared as part of the rebirth law in `docs/mechanics/02_combat_laws.md` ("The Hero's Journey"). It is a lifecycle-transition consequence, not a general recovery mechanism. General recovery from injury or impairment (time, treatment, rest) remains **MISSING**, and this Rule binds any future recovery mechanism as before.
```

## EDIT R2 — `docs/world_rules/life-body/lifecycle.md`, LIFE-01 evidence

Replace exactly (the anchor **wraps after "The two"**):

```
The two
fields are never conflated in the same write.
```

with:

```
The two
facts are never derived from one another: `alive` is written by combat at `hp <= 0`, and
`is_permadeath_set` only by a lifecycle death classification (a `death_reason`). A final death
legitimately has both set; what this Rule forbids is inferring permanence from `alive=False`
alone (wording corrected 2026-10-01).
```

## EDIT R3 — `docs/world_rules/life-body/lifecycle.md`, LIFE-02 evidence

**R3a.** In the parenthetical that starts ``DEFEAT` (non-lethal: the terminal outcome when`, replace:

```
`DEFEAT` (non-lethal: the terminal outcome
```

with:

```
`DEFEAT` (non-lethal at combat classification, and since `<TICKET>` recorded by lifecycle as a death with `death_reason` `<DEFEAT_REASON>`; the terminal outcome
```

**R3b.** At the **end** of the "Application-layer contradiction" paragraph (after
`The Rule text and Disposition are unchanged.`), append — note the **leading space**:

```
 **Resolved by `<TICKET>` (2026-10-01):** `REBIRTH` now restores HP and `alive` (identity continues at runtime), and terminal `DEFEAT` is a recorded, classified death, not a silent deactivation. Evidence returns to **SUPPORTED**; continued existence after defeat is realised by `REBIRTH`.
```

**R3c.** Change the evidence heading line:

```
**Repository evidence: SUPPORTED at classification; CONTRADICTED at application (corrected 2026-10-01).**
```

to:

```
**Repository evidence: SUPPORTED (application-layer contradiction found and resolved 2026-10-01).**
```

## EDIT R4 — `docs/world_rules/scenarios/life-body-batch-05.md`, LB-S02

Replace:

```
- **Result: covered at classification; contradicted at application** (see LIFE-02's application-layer note, corrected 2026-10-01).
```

with:

```
- **Result: covered** (`REBIRTH` restores the subject at runtime since `<TICKET>`; terminal `DEFEAT` is a classified death, see LIFE-02).
```

---

## Acceptance (owner's own wording)

> these spans only; the validator passes; R1–R4 land in the same commit as the code that makes them
> true.

Run `python3 tools/validate_frontmatter.py --content-type doc <file>` on all three touched files after
applying.

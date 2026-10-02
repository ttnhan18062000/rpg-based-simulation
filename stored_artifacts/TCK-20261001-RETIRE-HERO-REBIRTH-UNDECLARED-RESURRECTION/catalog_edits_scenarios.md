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

# Verbatim catalog edits S1–S2 — supplied by `world-rule-catalog-design`, 2026-10-01

The **last two** catalog locations presenting the retired `REBIRTH`/`PERMADEATH` outcomes as live. Third
and final batch, after `catalog_edits.md` (C1–C5, applied) and `catalog_edits_remaining_docs.md`
(K1–K6, applied).

## Rules of application

1. Apply on **`entity-death-cause-at-writer`**, as a follow-up push to **PR #276** (or after merge if it
   closes first). Not blocking the merge.
2. **No substitutions are permitted.** Both blocks are final text.
3. **Bump `last_verified` to `"2026-10-01"` in `capability-progression-batch-07.md`** only —
   `life-body-batch-05.md` is already at that date (verified).
4. Only these two spans change. **The validator must pass.**
5. **If either anchor does not match exactly, STOP and report the delta** — do not paraphrase.

**Anchor uniqueness verified by the planner** on `origin/entity-death-cause-at-writer`: each opening
phrase occurs exactly **once** in its own file.

## The owner's rulings behind these two

- **CP-S11 needs a status change, not just a list fix.** Its scenario statement is literally "one
  participant is defeated; **survives**", so with nothing preserving existence after a defeat it becomes
  *permitted, not currently realised* — the same treatment LB-S02 got in C5.
- **LB-S03 follows the BODY-02 K3/K4 template.** It stays **covered for cause** classification; **fate**
  classification is not realised; and "role and generation" goes away. Note "depending on role" was
  itself the ID-02/CAUSE-04 coupling the retirement removed, and "generation" names a field that no
  longer exists.

---

## S1 — `docs/world_rules/scenarios/capability-progression-batch-07.md`, CP-S11

Replace the **entire bullet**, from
`- **Result: covered — reconfirms Batch 05 with one additional real outcome.**`
through `beyond Batch 05's own original six-value vocabulary.` with:

```
- **Result: permitted, not currently realised (revised 2026-10-01).** No current mechanism lets a defeated participant survive. `KILL` and terminal `DEFEAT` both end in a recorded, final death, and the former hero `REBIRTH`, previously cited here as preserving continued existence, was retired as an undeclared resurrection (`TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION`; see LIFE-02 and STR-02). What remains real: a participant who loses HP without reaching zero (`SURVIVE`) can carry a wound or scar as a real capability regression (CP-S08's own evidence). The encounter may become a `CausalMemoryEntry` (LEARN-01's own epistemic finding) when the memory flag is on. `FLED` is a genuinely distinct real outcome, so "victory ≠ kill" holds even though "defeat ≠ death" is not currently realised.
```

## S2 — `docs/world_rules/scenarios/life-body-batch-05.md`, LB-S03

Replace the **entire bullet**, from
`- **Result: covered — the answer was determined, not assumed in advance.**`
through `any single predetermined result.` with:

```
- **Result: covered for cause; fate not currently realised (revised 2026-10-01).** Reaching `new_hp <= 0` still triggers a real classification, never an assumed one. Combat classifies `KILL` or terminal `DEFEAT` by the attack's own lethality (`is_lethal`; opportunity attacks are non-lethal), not by the subject's role. Lifecycle then records the death with a declared cause (`COMBAT`, `DEFEAT`, `HAZARD`, `STARVATION`, `SLEEP_DEPRIVATION`). The former role- and generation-dependent branch (`REBIRTH`/`PERMADEATH`) was retired, and the `generation` field removed. Zero HP is a necessary trigger for cause classification. Fate is not currently classified: every zero-HP outcome today is a final death, and no declared route to continued existence exists (permitted by LIFE-02 and BODY-02, not required).
```

---

## Running total — catalog locations updated for the rebirth retirement

| batch | file(s) | status |
|---|---|---|
| C1–C5 | `lifecycle.md` (LIFE-01, LIFE-02, open question 1), `supernatural-transformation.md` (STR-02), `life-body-batch-05.md` (LB-S02) | applied |
| K1–K6 | `conflict-combat.md` (Rule text + evidence), `body-condition.md` (BODY-02 Rule text + evidence), `capability-progression.md` (×2) | applied |
| **S1–S2** | `capability-progression-batch-07.md` (CP-S11), `life-body-batch-05.md` (LB-S03) | **pending** |

Plus the earlier EDITs A–F and R2, and the withdrawn R1/R3/R4 (recorded in `catalog_edits.md`).

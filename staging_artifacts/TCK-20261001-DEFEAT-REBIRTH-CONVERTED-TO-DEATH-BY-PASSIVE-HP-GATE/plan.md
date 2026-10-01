---
status: active
layer: engine
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE
phase: open
date: 2026-10-01
tags: [bug, lifecycle, engine]
---

# Plan — TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE

v2, incorporating the `architecture-reviewer` `NEEDS_CHANGES` verdict of 2026-10-01. Batch sibling of
`TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER`, whose `plan.md` is the **batch
primary** and carries the review record, R1 and the shared sequencing. Read that first.

**Implement after the primary's R1 and S1–S3**, in the same batch. The primary makes
`resolve_lifecycle` the sole authority for HP-death deactivation; this ticket's S3 adds a reason branch
beside the one it creates.

## RULE RULING RECEIVED — S3 is UNBLOCKED (`world-rule-catalog-design`, 2026-10-01)

The planner referred the `is_permadeath_set=True` question to the rule owner, asking whether stamping
permadeath on a terminal `DEFEAT` collapses LIFE-01's two-separate-facts rule. **Ruling: it does not,
and no divergence entry is needed.** Reasoning, accepted:

- LIFE-01 requires the two facts to be **separately tracked**; it does not say both cannot be true. A
  `DEFEAT` death under decision 2 **is** a final death, so `is_permadeath = True` is the *correct* value.
- Conflation would mean **deriving** one fact from the other (`alive=False` ⇒ permadeath). This design
  derives `is_permadeath` from a real lifecycle classification (the `death_reason`) — exactly as
  `KILL` → `COMBAT` and `OLD_AGE` already do through this same `if is_dead:` block. **If `DEFEAT`
  conflated the facts, every existing death would too.**
- **The planner's option (ii) would have been the actual violation.** A recorded death without the
  permadeath flag and with no return path is a non-final death that never returns — it breaks
  `is_permadeath` as the single final marker LIFE-01, ID-05 and LB-S02 rely on, and creates exactly the
  limbo state decision 2 exists to avoid.
- What *is* wrong is LIFE-01's own evidence sentence ("The two fields are never conflated in the same
  write"), which describes a write-site detail rather than the rule and invites this misreading. The
  owner supplied verbatim replacement text — **EDIT R2** in S6 below.

**Additional requirement from the ruling:** LIFE-01's "may lose participation without permanence" must
have a **positive runtime case** after this batch, not just a classification label. Pin a test asserting
a `REBIRTH` entity ends with `alive = True` **and** `is_permadeath = False` (test plan T9b).

## Decisions this plan implements (user, 2026-10-01)

1. `REBIRTH` restores `combat.hp = combat.max_hp` and `combat.alive = True`, keeping the `generation`
   increment.
2. A terminal `DEFEAT` resolves to a recorded death with its own distinct `death_reason`. **No** durable
   downed state and **no** revival writer.

Both were also sent to the rule owner for review (2026-10-01), along with the BODY-05 question that
rebirth becomes the **first HP restore in the engine**, and the BODY-03 consequence in S6.

## Steps

### S1 — Pin the current behaviour with failing tests first
Add `test_plan.md` T8 and T9 asserting the intended contract. They must fail on `71c4aa321` for the
stated reason. The defect is a silent deactivation one tick removed from its cause, so a test written
after the fix can pass for the wrong reason.

### S2 — Make `REBIRTH` actually rebirth, via `CombatUpdate` (R3)
`combat.py:182-187` sets `gen_delta = 1` and nothing else. The restore rides on **`CombatUpdate`**, not
`LifecycleUpdate`: `src/core/updates.py:444-459` has no hp/alive fields, `LifecyclePatch.apply` writes
none, and `LifecycleComponent` has no `hp`. (`movement.py:248-252` lifting
`generation_delta`/`is_permadeath_set` is not a counter-precedent — those *are* lifecycle fields.)

**The `alive` write must be explicitly positive.** `combat.py:171` sets the local `alive = False`,
returned as `alive_set=alive` (`:234`), and `CombatPatch.apply` (`patches.py:322`) does
`alive=(new_hp > 0) if u_com.alive_set is None else u_com.alive_set`. With `alive_set=False` the earlier
`False` stands **regardless of HP**. The rebirth branch must set `alive = True`.

**R3 — `CombatUpdate` cannot currently express "restore to `max_hp`", and this is a real blocker.**
Verified: it carries only `hp_delta` (relative, `updates.py:104`), and `CombatPatch.apply` computes
`new_hp = max(0, new_combat.hp + u_com.hp_delta)` with **no upper clamp at `max_hp`**, against a
`changes["combat"]` that Section A may already have drained by up to 3 HP on a life-due tick. So a
`hp_delta = max_hp - prior_hp` restore lands at `max_hp - passive_drain`, and T9's
`combat.hp == combat.max_hp` becomes cadence-dependent.

**Fix:** add `hp_set: Optional[int]` to `CombatUpdate`, following the existing `alive_set` /
`is_permadeath_set` / `*_set` precedent, with last-write-wins `merge` semantics, applied in
`CombatPatch.apply` **after** `hp_delta`/`max_hp_delta`. Accepting delta drift instead is acceptable
**only** if the law text in `02_combat_laws.md` and T9 are both weakened to match — do not write an
absolute law and then verify it with a relative mechanism.

### S3 — Record the `DEFEAT` death reason in `resolve_lifecycle` — **unblocked by the ruling above**
`lifecycle.py:202` branches on `outcome_kind in ("KILL", "PERMADEATH")` → `death_reason = "COMBAT"`. Add
`DEFEAT` with its **own** distinct reason (candidate `"DEFEAT"`, aligned with the `outcome_kind` that
produced it) so AC1's "distinguishable from `COMBAT`" holds. Read the persisted `outcome_kind` only —
never re-derive from HP or role. Share the primary's R6 idempotency guard; do not write a second one.

**Consequence to name in the ticket, not discover:** every terminal `DEFEAT` now enters `recent_deaths`
and triggers `_select_default_heir` plus heirloom / nemesis / dying-wish dispatch (4 occurrences in the
cited 120-tick run), touching the inheritance mechanism the world-rules README already records as
CONFLICTING.

### S4 — Reconcile the `apply.py` `active=` gate
**Do not edit `apply.py:106-109`.** The primary owns that change (R1), exactly once. This ticket only
**asserts against** it:
- A reborn entity must not be deactivated on the following life-due tick. Because Section A reads
  prior-tick HP and rebirth restores to `max_hp` at tick N, tick N+1's gate sees `hp > 0` — the review
  confirms this resolves favourably, but **T9 must still prove it rather than reason it**.
- A terminal `DEFEAT` must still be deactivated, with its reason recorded via S3.

If T9 shows a reborn entity still deactivated, fix the gate in coordination with the primary — do not
compensate by inflating the restored HP.

### S5 — Rewrite the corpus assertion
`tests/mechanic_scenarios/test_entity_death_authority_boundary.py` asserts that `DEFEAT`/`REBIRTH`
leftovers *remain unrecorded* — the defect encoded as the contract. Rewrite to the new contract; do not
delete it.

### S6 — Docs, law and parity

**Condition from the rule owner (decision 1): the restore must be *declared*, not a code side effect.**
BODY-05 forbids spontaneous, undeclared recovery; it does not forbid a restore that a declared law
produces. Rebirth is already a declared lifecycle transition, so the restore is compliant **only if**
`docs/mechanics/02_combat_laws.md` §"The Hero's Journey (Generations)" step 2 states it. Required text
content: rebirth restores `combat.hp` to `max_hp` and `alive` to `True`, **and wounds and scars persist
across rebirth** (decision 4). Add the matching parity entry.

**Hard constraint from the same ruling:** do **not** build this as a general `heal`/restore helper that
other paths can call. It is a **rebirth-only consequence**. General recovery from injury or impairment
stays MISSING, and BODY-05 binds any future recovery mechanism separately.

- **Rebirth does NOT clear `wounds`/`scars`** — rule-compliant as the default, confirmed by the owner:
  BODY-06 permits persistent injury after the harmful event ends; HP-01 and ID-05 (history survives) plus
  "identity continues" lean toward carrying rather than resetting; CAUSE-01/CAUSE-05 require a declared
  cause for any deletion. A reset would be legitimate only as an explicitly declared part of the rebirth
  law, which is **a gameplay/balance decision for the user, not a rule requirement**. Ship no-reset.
  **Consequence: wound/scar penalties accumulate across all four generations**, which nothing will
  measure while SimQ is untrustworthy (`TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED`) —
  **file a KEEP balance follow-up** to measure cross-generation penalty accumulation once SimQ is
  trustworthy again. Do not decide balance by rule.
- **Do not conflate** `CombatComponent.scars` (per-entity `ScarState`) with
  `update.scars_add_or_update` / `local_scars` (region-level `LocalScarState`, `apply_plan.py:86,104`).

#### Verbatim catalog edits — apply in this batch, ONLY alongside the code that makes them true

Supplied by `world-rule-catalog-design` 2026-10-01 under the standing small-doc handoff. **Never land
these ahead of the implementation** — they assert behaviour that does not exist yet. Permitted
substitutions are **only** `<DEFEAT_REASON>` (the actual `death_reason` literal chosen in S3) and
`<TICKET>` (the implementing ticket ID). If the implementation differs from the decisions, or the user
changes decision 1, 2 or 4, **stop and send the owner the delta rather than adapting the text.**

- **EDIT R1** — `docs/world_rules/life-body/body-condition.md`, BODY-05. BODY-05's Repository Finding
  ("No positive HP-restoration path was found anywhere") goes stale the moment this lands. Insert the
  owner's supplied "**Update (2026-10-01, `<TICKET>`)**" paragraph directly after the paragraph ending
  "...whenever one is built." and before "**Scenarios:**".
- **EDIT R2** — `docs/world_rules/life-body/lifecycle.md`, LIFE-01 evidence. Replace the wrapped
  sentence "The two / fields are never conflated in the same write." with the owner's corrected
  derivation-based wording (the anchor wraps after "The two").
- **EDIT R3** — same file, LIFE-02 evidence. Qualify `DEFEAT` as "non-lethal **at combat
  classification**", append the owner's "**Resolved by `<TICKET>`**" sentence to the
  application-layer paragraph, and change the evidence heading to
  "**Repository evidence: SUPPORTED (application-layer contradiction found and resolved 2026-10-01).**"
- **EDIT R4** — `docs/world_rules/scenarios/life-body-batch-05.md`, LB-S02. Replace the "covered at
  classification; contradicted at application" result line with the owner's plain "**Result: covered**"
  line citing `REBIRTH`'s runtime restore.

The exact replacement strings are in the owner's 2026-10-01 message and must be copied from it verbatim.
**Caution learned earlier in this batch:** verify each anchor is unique before replacing — an earlier
edit to this same LB-S02 file used an anchor (`- **Result: covered.**`) that occurs 8 times.
- **Do not conflate** `CombatComponent.scars` (per-entity `ScarState`) with
  `update.scars_add_or_update` / `local_scars` (region-level `LocalScarState`, `apply_plan.py:86,104`).
- `docs/guidelines/intentional_divergences.md`: required only if implementation departs from the Bible;
  judge honestly at implementation time. The LIFE-01 permadeath question above may generate one.
- Parity ledger: **`combat_movement.yaml::COMB-297`** (P2, `verified`) — update `v2_evidence`: S2 changes
  what rebirth does, and R4 removed the planned `movement.py` guard widening. Plus a `combat_movement.yaml`
  entry (or outcome-lattice update) for terminal `DEFEAT` becoming a recorded death.
- **AC5: do not edit `docs/world_rules/life-body/lifecycle.md`.** The owner applied its own corrections
  on 2026-10-01 (LIFE-02 evidence, open question 1, LB-S02, roadmap §3.1); cite those as the catalog-side
  update.

## Removed from v1 by the review (R4) — do not reinstate

v1's S3 claimed that `movement.py:248-252`'s guard means "no lifecycle update reaches the apply path at
all" for a terminal `DEFEAT`, and called it "the blocking defect for AC1". **That was wrong.** Verified:
`resolve_lifecycle` **synthesizes its own** update — `ent_upd = ent_upd or EntityUpdate(entity_id=e_id)`
then `life_upd = ent_upd.lifecycle or LifecycleUpdate()` (`lifecycle.py:205-216`) — so a `death_reason`
reaches the apply path regardless. The real gap is solely the missing discriminant at `:202`, i.e. S3.

Widening the guard as v1 specified would emit `LifecycleUpdate(age_delta=0, generation_delta=0,
is_permadeath_set=None)`, for which `is_noop()` is `True` — it carries nothing. The only widening that
*would* carry something is `movement.py` setting `death_reason_set` itself, placing a lifecycle
classification in an opportunity-attack call site reading a combat outcome: the exact inversion both
investigations reject elsewhere. `COMB-297` and the `:243-247` comment remain relevant history, but this
is **not** another instance of that bug.

Test **T11 is likewise dropped** (it tested a mechanism that should not exist) and replaced by a test
that `resolve_lifecycle` synthesizes its own `LifecycleUpdate` for a `DEFEAT` with no incoming lifecycle
update — the real invariant.

## Scope guards

- No durable downed/recoverable state, no revival writer.
- Do **not** touch `world_dynamics.py:39` or the `"HAZARD"` discriminant.
- Do **not** alter `_NON_COMBAT_OUTCOME_KINDS` (`phase.py:95`) — `DEFEAT` is already correctly absent.
- Do **not** alter `_DEFEATED_OUTCOME_KINDS` (`learning_outcome.py:33`) — it already contains `DEFEAT`
  and `REBIRTH`; the learning layer already agrees the defender lost.
- A HERO at `generation >= 4` must still resolve to `PERMADEATH` (AC3). Do not widen the rebirth path.
- Do **not** edit `apply.py:106-109` (primary owns R1).

## Acceptance-criteria map

| AC | Steps | Verified by |
|---|---|---|
| 1 — terminal `DEFEAT` recorded with a distinct reason | S1, S3 *(blocked on ruling)* | T8, T10, T11′ |
| 2 — `REBIRTH` yields a live entity at `max_hp`, still active next tick | S1, S2 (incl. R3), S4 | T9 |
| 3 — gen ≥ 4 still `PERMADEATH`, rebirth path not widened | S2 | T12 |
| 4 — combat laws record the HP value; divergence + parity recorded | S6 | S6 diff |
| 5 — LIFE-02 updated by its owner, handover recorded | S6 | Implementation Notes |

---
status: active
layer: engine
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE
phase: open
date: 2026-10-01
tags: [bug, lifecycle, engine]
---

# Test Plan — TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE

Continues the batch-primary test plan
(`staging_artifacts/TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER/test_plan.md`,
T1–T7, plus architecture tests A1–A3 which apply to this ticket unchanged). Numbering continues at T8.

**Homes:** `tests/unit/engine/test_apply.py` (gate reconciliation), `tests/unit/progression/test_lifecycle.py`
(reason classification), a combat-outcome unit home for the lattice tests, and
`tests/mechanic_scenarios/test_entity_death_authority_boundary.py` (corpus rewrite, plan S6).

**Scoped command:**
`pytest tests/unit/engine/test_apply.py tests/unit/progression/test_lifecycle.py tests/mechanic_scenarios/test_entity_death_authority_boundary.py -m "not slow"`

## Write these two first (plan S1) — they must fail on `71c4aa321`

**T8 — a terminal `DEFEAT` is recorded, not silently deactivated.** Non-HERO entity driven to 0 HP by an
opportunity attack (`resolve_multi_attack(..., is_lethal=False)`, the `movement.py:241` path — the sole
producer of terminal `DEFEAT`). Advance one life-due tick. Assert `lifecycle.active is False` **and**
`death_reason` is non-`None`, distinct from `"COMBAT"`, and distinct from the sibling's passive reasons.
On `71c4aa321` this fails with `death_reason is None`. Covers AC1.

**T9 — a reborn HERO is alive at full HP and still active on the next life-due tick.** HERO at
`generation == 1` driven to 0 HP. Assert immediately after resolution: `outcome_kind == "REBIRTH"`,
`generation == 2`, `combat.hp == combat.max_hp`, `combat.alive is True`. Then advance **one life-due
tick** and assert `lifecycle.active is True` and `hp` still positive. On `71c4aa321` this fails twice
over — first at `hp == 0`/`alive is False`, then at the age-path deactivation. Covers AC2.

**`combat.hp == combat.max_hp` is cadence-dependent until R3 lands** (architecture review): `CombatUpdate`
carries only relative `hp_delta` and `CombatPatch.apply` has no upper clamp at `max_hp`, while Section A
may already have drained up to 3 HP on a life-due tick. So a delta-based restore lands at
`max_hp - passive_drain` and this assertion flakes with cadence. Either plan S2's `hp_set` lands and this
asserts exact equality, or the law and this test are **both** weakened together — never assert an
absolute value against a relative mechanism.

**T9b — LIFE-01 gets a positive runtime case (rule owner, 2026-10-01).** Required by the ruling that
unblocked S3: LIFE-01's "a subject may lose active-participant status without that being permanent" must
be realised at runtime, not merely as a classification label. Assert a `REBIRTH` entity ends with
`combat.alive is True` **and** `lifecycle.is_permadeath is False`. This is the test that distinguishes
"defeat need not be permanent" from "every defeat is recorded as permanent" — without it, the batch
makes `is_permadeath` true for `DEFEAT` and leaves LIFE-01 with no demonstrated non-permanent case.

The second half of T9 is the load-bearing assertion of this ticket: the age path runs every life-due
tick independently of damage, so "rebirth restored HP" and "the reborn entity survives the next tick"
are genuinely two different claims. Plan S5 explicitly refuses to settle the second by reasoning.

## Edge cases

**T10 — the `DEFEAT` reason is distinguishable at the consumer, not just at the writer.** Assert a
terminal `DEFEAT` and a `KILL` produce different `death_reason` values and that anything keyed on
`"COMBAT"` (notably `event_extractor.py`, which stays exact-match) does not silently absorb `DEFEAT`.

**~~T11~~ — DROPPED by the architecture review (R4).** v1 asserted that `movement.py`'s *widened* guard
produces a non-`None` `lifecycle_upd`. That tested a mechanism that **should not exist**: the guard must
not be widened, because `resolve_lifecycle` already synthesizes its own update, and the only widening
that would carry anything would put lifecycle classification inside an opportunity-attack call site.

**T11′ — the real invariant, replacing T11.** Assert that `resolve_lifecycle` **synthesizes its own**
`EntityUpdate`/`LifecycleUpdate` for a terminal `DEFEAT` that arrives with **no** incoming lifecycle
update (`movement.py` legitimately passes `lifecycle_upd=None` for it, since `generation_delta == 0` and
`is_permadeath_set is None`). This is what actually makes T8 possible, and pinning it means a future
change that breaks the synthesis fails here with a clear cause rather than only as a mysterious missing
`death_reason`.

**T12 — a HERO at `generation >= 4` still resolves to `PERMADEATH`.** Assert `outcome_kind ==
"PERMADEATH"`, `is_permadeath is True`, and that **no** HP/alive restore was applied. Guards against
plan S2 widening the rebirth path. Covers AC3.

**T13 — `REBIRTH` does not clear wounds/scars.** Settled: both the architecture review and the rule owner
ruled no-reset (BODY-06 permits persistence; HP-01/ID-05 and "identity continues" lean toward carrying;
CAUSE-01/CAUSE-05 require a declared cause for a deletion). Give a HERO accumulated `wounds` and `scars`,
drive it to `REBIRTH`, and assert **both lists survive intact** alongside the restored HP. Assert against
`CombatComponent.wounds` / `.scars` (per-entity) — **not** `update.scars_add_or_update` / `local_scars`,
which are region-level `LocalScarState` (`apply_plan.py:86,104`) and a different thing entirely.

Record in the ticket that this makes wound/scar penalties accumulate across all four generations, that
nothing currently measures the balance effect (SimQ excluded), and that a KEEP balance follow-up is filed
per the owner's instruction. Do not quietly convert the balance question into a rule decision.

## Failure modes

**T14 — a terminal `DEFEAT` on an entity that is also starving.** Overlap with the sibling: the entity
is at 0 HP from `DEFEAT` and both bio thresholds are breached. Assert the `DEFEAT` reason wins and no
passive cause is recorded (mirrors primary T3 from the other side). This pair is the batch's real
integration risk.

**T15 — a reborn HERO that is then starving.** After rebirth at `max_hp`, drive `hunger` above threshold
until HP reaches zero again. Assert this records a **passive** reason via the sibling's role-blind
discriminant, not a combat one — confirming the two tickets compose rather than shadowing each other.

## Corpus (plan S6)

**T16 — rewrite the boundary corpus assertion.** `test_entity_death_authority_boundary.py` currently
asserts `DEFEAT`/`REBIRTH` leftovers *remain unrecorded*, which encodes the defect as the contract.
Rewrite to the new contract over the same `frontier_marches` seed-42 120-tick run that produced the
original evidence (4 `DEFEAT`, 1 `REBIRTH`). Assert each `DEFEAT` carries a recorded reason and the
`REBIRTH` entity is alive and active afterwards. **Do not delete the assertion** — a corpus test that
stops asserting anything about this population is a coverage regression, and its counts are the only
production-like evidence this batch has.

Expect the corpus event counts to shift once rebirth stops ending in deactivation. Re-baseline
deliberately and state the old and new counts in the ticket's Test Summary; never loosen the assertion
to absorb the change.

## Verification constraint

SimQ is **not** a valid signal for this batch: 13 of 15 grade anchors are independently red on untouched
`main` (`TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED`, verified at `e9db40f0a`). Do not cite a
SimQ score as evidence for or against this change in either direction.

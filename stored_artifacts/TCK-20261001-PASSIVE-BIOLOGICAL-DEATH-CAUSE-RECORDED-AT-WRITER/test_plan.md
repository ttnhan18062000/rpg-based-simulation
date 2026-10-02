---
status: active
layer: engine
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER
phase: open
date: 2026-10-01
tags: [bug, lifecycle, engine, determinism]
---

# Test Plan — TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER

Batch-primary test plan; T8–T13 live in the sibling's `test_plan.md`.

## v2 — corrections from the architecture review (2026-10-01), read first

The review found six real defects in v1 of these test plans. All are fixed below; recorded here so the
implementer knows which assertions changed and why.

1. **Every classification assertion needs an explicit tick advance.** The passive cause is written
   *after* `resolve_lifecycle` within a tick (`kernel.py:776-781`), so it is first readable at tick N+1.
   T1, T2, T5, T5b, T5c and T6 all read as same-tick assertions in v1 and would have passed or failed
   for the wrong reason.
2. **T6 was vacuous.** It asserted a branch ordering that never occurs in one invocation. Rewritten
   against the R6 cross-tick idempotency guard.
3. **The existing pinned test must be named.**
   `tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py:155::test_starvation_sleep_debt_driven_hp_loss_is_still_silent_post_fix`
   asserts the current silence and **will fail** on R1. Its docstring prescribes updating it, not
   deleting the assertion. Named in T0 below — an unnamed expected failure is how a real signal gets
   mistaken for flake.
4. **A2's oracle was false.** v1 asserted the cause "reaches durable state via `patches.py`". It does
   not: `apply.py` writes `changes["lifecycle"]` directly in Section A, which *is* the authoritative
   path but is not the patch path. Restated.
5. **T4's rationale pinned a mechanism this batch removes** — see T4.
6. **`PROG-030`'s P0 test must pass** and was unnamed in v1. Added as T0b.

**Homes:** `tests/unit/engine/test_apply.py` (writer-side T1–T4), `tests/unit/progression/test_lifecycle.py`
(classification T6), new serialization coverage beside the component's existing round-trip tests (T5, T7),
`tests/mechanic_scenarios/test_entity_death_authority_boundary.py` (corpus).

**Scoped command** (never the full suite, per the Testing Rule):
`pytest tests/unit/engine/test_apply.py tests/unit/progression/test_lifecycle.py tests/mechanic_scenarios/test_entity_death_authority_boundary.py -m "not slow"`

## Expected failures to update, not delete (R1)

**T0 — `test_starvation_sleep_debt_driven_hp_loss_is_still_silent_post_fix`** (`test_natural_aging_old_age_dispatch.py:155`)
asserts `hp == 0`, `alive is False`, `active is False`, `death_reason is None`. R1 makes the last two
false. Update it to the new contract per its own docstring's instruction; **do not delete the
assertion**, and name it in the ticket's Test Summary as an expected, understood failure.

**T0b — `PROG-030`'s P0 `test_path` must still pass**:
`test_natural_aging_old_age_dispatch.py::test_natural_aging_death_is_recorded_as_old_age_and_dispatches_succession`.
R1 extends that entry's sole-authority contract from age to HP deaths; the age path must be unaffected.
Run it explicitly rather than relying on it being swept up.

## Normal flow

**T1 — a hunger death records `STARVATION` with full lineage.** Entity at `hp = 2`, `hunger >= 95`,
`sleep_debt` below threshold, on a life-due tick. Assert at tick N: `combat.hp == 0`, `alive is False`,
the typed cause field is the starvation value **and carries the zeroing tick** (plan S1 option (a)).
**Then advance one tick** and assert `death_reason == "STARVATION"`, `is_permadeath is True`,
`death_tick` set (to N+1), and the succession dispatch fired. The tick advance is mandatory — the cause
is not readable by `resolve_lifecycle` until N+1. Covers AC1.

**T2 — a sleep-debt death records `SLEEP_DEPRIVATION`.** Same shape at `hp = 1` with `sleep_debt >= 98`
and `hunger` below threshold. Asserts the two causes are genuinely distinct values, not one reason with a
cosmetic label.

## Edge cases

**T3 — a `DEFEAT` leftover is not classified by this path.** Entity already at `hp == 0` from a prior
tick's terminal `DEFEAT`, `hunger` and `sleep_debt` both *above* threshold (the hostile case: a
threshold-reading implementation would mislabel it). Assert the typed cause stays `None` and
`resolve_lifecycle` records no passive reason. This is the regression that killed the rejected
threshold-inference design, so it must assert on the cause field directly, not merely on the absence of a
crash. Covers AC2.

**T4 — a `REBIRTH` entity is not classified by this path.** HERO with `generation == 2`. **v1's rationale
is corrected:** v1 asserted the discriminant excludes it "because it is already at `hp == 0`" — true on
`main`, but the sibling ticket **removes that mechanism**, leaving a reborn entity at `max_hp`. After the
batch the exclusion holds for the opposite reason: `new_hp == 0` is false because the entity is healthy.
Assert the exclusion, and state the post-batch reason, so the test does not pin behaviour the batch
deletes. Covers AC2.

**T5 — both thresholds breached on the fatal tick resolves to `STARVATION`.** Entity at `hp = 3` with
`hunger >= 95` **and** `sleep_debt >= 98`, so the summed drain of `3` takes it exactly to zero. Advance a
tick, then assert the recorded reason. **Assert the declared precedence rule (R5), not the arithmetic:**
the test must reference the contract-doc rule "hunger outranks sleep debt as a recorded cause of death",
not the `+= 2` / `+= 1` damage magnitudes. If those constants are ever retuned to 1/1 this test must
still express the intended rule rather than silently changing meaning.

**T5b — a non-fatal passive drain records nothing.** Entity at `hp = 10`, `hunger >= 95`. Assert
`hp == 8`, `alive is True`, cause field `None`. Guards the `comb.hp > 0 and new_hp == 0` boundary from
becoming `new_hp <= 0` or firing on every drain.

**T5c — an entity already at `hp == 0` with zero passive damage.** The age-path case from the
investigation: assert this path does not invent a passive cause for it. This is the overlap point with
the sibling ticket and the one most likely to regress when both land.

## Failure modes

**T6 — a combat death outranks a passive cause (R6 idempotency, NOT branch ordering).** v1 specified
this as branch ordering inside one `resolve_lifecycle` invocation; the two facts are **never visible in
the same invocation** (combat classifies at tick N from `outcome_kind`; the passive cause is readable at
N+1), so that test would have passed vacuously.

Correct shape: entity at `hp = 2` with `hunger >= 95` that also takes a lethal `KILL` on tick N. Note
`comb.hp` in Section A is the **prior-tick** HP, so the passive cause **is** written on the same tick the
combat death is classified. Assert at N: `death_reason == "COMBAT"`. **Then advance a tick** and assert
the passive cause was **not** applied over it and no second death was dispatched — i.e. the R6 guard
("never classify a passive cause on an entity that already carries `death_reason` or `is_permadeath`")
holds across the tick boundary.

**T6b — the stale cause never surfaces (R2).** Same setup. The cause field sits on the corpse with
`death_reason == "COMBAT"` already set. Assert the stale cause is ignored/cleared and is never reported
as that entity's cause of death by any consumer or debug surface.

**T7 — the typed field survives a serialization round trip and is inspectable.** `to_dict`/`from_dict`
(or the component's established round-trip) preserves the cause; the field appears in
`to_canonical_dict()` per the architecture verdict. Assert `event_extractor.py` remains **exact-match on
`COMBAT`** — i.e. a passive reason does not leak into the combat event stream. Covers AC3.

## Architecture tests (per the Testing Rule)

**A1 — read-only logic did not mutate live state.** Assert `resolve_lifecycle` leaves the input
`AuthoritativeState` unmodified and expresses its effect only through the returned `StateUpdate`.

**A2 — the authoritative application path was used.** **v1's oracle was false** and is restated: the
cause does **not** travel through `patches.py`. `apply.py` writes `changes["lifecycle"]` directly in
Section A — that *is* the authoritative path, but it is not the patch path. Assert the real mechanism:
the cause is written into the `changes` dict that `_compute_entity_changes` returns and is committed by
`ApplyPath.apply_generation`, with no direct mutation of a live `EntityState` anywhere. Asserting
`patches.py` involvement would assert something untrue.

**A3 — determinism.** Two runs of the same seeded scenario produce identical causes and identical
canonical hashes. If the field is added to `to_canonical_dict()`, the corpus baseline hash changes
**once** — re-baseline deliberately and record it, never by loosening the assertion.

## Regression-prone paths

- The `new_hp > 0` gates in `apply.py` — T5b, T5c.
- Branch ordering in `resolve_lifecycle` — T6.
- The canonical-dict field list — A3.
- The corpus test's existing `DEFEAT`/`REBIRTH` assertions, which the sibling rewrites (its S6). Run the
  corpus test after **both** tickets land, not after each.

## Out of scope

No new `@slow` tests. Note that 13 of 15 SimQ grade anchors are independently red on untouched `main`
(`TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED`), so SimQ is **not** a valid verification
signal for this batch and must not be cited as one either way.

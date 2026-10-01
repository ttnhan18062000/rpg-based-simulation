---
status: active
layer: engine
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER
phase: open
date: 2026-10-01
tags: [bug, lifecycle, engine, determinism]
---

# Plan — TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER

**This is the batch-primary plan**, covering this ticket and
`TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE`.

## Architecture review — COMPLETE, verdict `NEEDS_CHANGES`, revisions applied

`architecture-reviewer` ran over v1 of both plans on 2026-10-01 and returned **`NEEDS_CHANGES`** with
six required changes, R1–R6. **Every load-bearing claim was independently re-verified by the planner
before acceptance** (phase order, the `:147` eligibility guard, the synthesis at `:205-216`,
`CombatUpdate`'s field set, `CombatPatch.apply`'s lack of an HP clamp, and `PROG-030`'s text). The review
was right on all of them, and it corrected **two factual errors in v1** — see the investigation's
CORRECTION section and R4 below.

**R1 is a scope expansion and was accepted by explicit user decision, 2026-10-01.** It brings in
completing the dual-writer fix that `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE` deliberately
left half-done. This plan is v2 and incorporates R1–R6 as substance, not as gate appeasement.

**Still open, awaiting a rule ruling from `world-rule-catalog-design` (requested 2026-10-01):** whether
routing a terminal `DEFEAT` through the shared `if is_dead:` block — which stamps
`is_permadeath_set=True` unconditionally — is an acceptable collapse of LIFE-01's two-separate-facts
rule, or whether `DEFEAT` needs a death record without the permadeath stamp. **Do not implement the
sibling's `DEFEAT` branch until that answer lands.** This ticket's own steps are unaffected and may
proceed.

## R1 — the blocking change (do this first)

**Problem.** The classification branch planned for `resolve_lifecycle` is **unreachable**. The passive
drain runs *after* `resolve_lifecycle` within a tick (`kernel.py:776-781`), so the cause is first
readable at tick N+1; and by then `apply.py:109` has set `active=False`, so `lifecycle.py:147`'s
`if not entity.lifecycle.active: continue` skips the entity before any branch runs.

**Change.** Drop the HP term from `apply.py:109`'s `active=` expression:

```python
active=(life.active or new_age < life.max_age_ticks)
```

making `resolve_lifecycle` the **sole declared authority** for HP-death deactivation — exactly mirroring
what `PROG-030` records for the age half of this same race. The `new_hp` computation and the
`alive=(new_hp > 0)` write on `changes["combat"]` are **unchanged**; only the lifecycle `active=` term
loses its HP gate.

**Consequences, to be planned and not discovered:**

1. **Passive death lands one tick later.** `PROG-030` records the identical shift for the age path.
   **Requires** an `docs/guidelines/intentional_divergences.md` entry alongside §2.59 (rationale class
   and verification path). v1 said no divergence entry was expected — that was wrong.
2. **`PROG-030` (P0, `verified`) enters this ticket's parity set.** R1 changes the `active=` formula that
   entry quotes verbatim and extends its sole-authority contract to HP deaths. Being P0, its
   `test_path` (`test_natural_aging_old_age_dispatch.py::test_natural_aging_death_is_recorded_as_old_age_and_dispatches_succession`)
   **must pass**. v1 named neither — this was the review's find.
3. **A new live signal.** `EconomicVacancyService.check_and_emit` fires off `resolve_lifecycle`'s
   `recent_deaths`. Today a passive death never enters that list; after R1 it will. Same finding
   `PROG-030`'s ticket recorded for the age path.
4. **An existing test becomes an expected failure.**
   `tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py:155::test_starvation_sleep_debt_driven_hp_loss_is_still_silent_post_fix`
   pins the current silence. Its own docstring prescribes updating it with this follow-up, not deleting
   the assertion. **It is named here deliberately** — an unnamed expected failure is how a real signal
   gets mistaken for flake.

**Rejected alternative:** relaxing the `continue` at `lifecycle.py:147`. A dead, deactivated entity would
re-enter the death-detection loop every tick and re-dispatch succession, and it contradicts `PROG-030`'s
single-declared-authority contract.

## Steps

### S1 — Add the typed cause field (R2)
On **`LifecycleComponent`** (ruled: a transient is impossible since the fact crosses a tick boundary;
`CombatComponent` is rejected as the fact is a lifecycle classification). Requirements:

- A real **enum** (`Optional[DeathCause]`), **not** a second bare `str` beside `death_reason`. Populate
  `death_reason` from the same enum's value so the two cannot drift.
- Add it to `LifecycleComponent.to_canonical_dict()` — it is durable state read across a tick boundary,
  so omitting it reproduces the silent-field-drop class recorded in `COMB-298`. `death_reason` is
  already canonical at `state.py:192`, so this is additive to an established pattern.
- **Measure, do not assert, the re-baseline surface.** v1 claimed this "changes every canonical hash in
  the corpus"; that is overstated, since most canonical-hash tests compare two runs for equality.
  Check `tests/regression/baseline_5k.json`, `tests/perf/baselines/`,
  `tests/integration/lab_agent/test_golden_run_fixture.py`, and state the real before/after.
- `to_dict`/`from_dict` round-trip coverage.
- **The field must preserve the zeroing tick (CAUSE-05 / TIME-02 condition, rule owner 2026-10-01).**
  Once R1 moves `death_tick` to N+1 while HP actually reached zero at tick N, the record must not lose
  N — "a cause may have a later consequence, and it must stay traceable". Two compliant options:
  **(a)** the cause field carries the tick the passive write drove HP to zero (making it a
  `(cause, tick)` pair rather than a bare enum), or **(b)** the `intentional_divergences.md` entry states
  that `death_tick = cause tick + 1` **by construction**, so N is reconstructable. **Prefer (a)** — it
  keeps traceability in the data rather than in prose, and it survives any future cadence change that
  would break the fixed `+1` relationship. Silent drift satisfies neither.

**Field lifecycle (R2) — v1's spec was insufficient.** "Never left stale on a surviving entity" does not
cover the real hazard. Because Section A (passive) in `_compute_entity_changes` runs **before** Section B
(`_apply_entity_update_to_dict`, `apply.py:162-163`), `comb.hp` is the **prior-tick** HP, unaffected by
this tick's combat. An entity at `hp=2` with `hunger >= 95` that also takes a lethal `KILL` on tick N
gets the passive cause written **and** `death_reason="COMBAT"` from `resolve_lifecycle` at tick N — the
cause field then sits stale on a corpse forever. **Spec: the field is ignored and cleared once
`death_reason` or `is_permadeath` is set**, and a test must assert the stale value never surfaces.

### S2 — Write the cause at the writer (`apply.py:103-110`)
Set the cause when `comb.hp > 0 and new_hp == 0`. Do not change `total_passive_dmg` or the `new_hp`
computation. **The v1 guard "do not change the `new_hp > 0` gates" is removed** — R1 changes the
lifecycle `active=` gate deliberately, and v1's guard forbade its own prerequisite.

The write stays inside the same `changes` dict at the same position — no second pass over entities, so
determinism and iteration order are untouched.

**Both-thresholds precedence (R5).** When `hunger >= 95` and `sleep_debt >= 98` both hold on the fatal
tick, record `STARVATION`. A fixed precedence is what LIMIT-04 requires (a rule explicitly declaring the
causal reading), so a composite cause is not needed. **But state it in
`docs/simulation/lifecycle_systems_contract.md` as a declared precedence rule — "hunger outranks sleep
debt as a recorded cause of death" — not as a derivation from the damage magnitudes.** v1 derived it from
"hunger contributes 2 of the 3 damage", which makes the recorded cause an artifact of two undeclared
constants (`+= 2`, `+= 1` at `apply.py:99-100`); retuning them to 1/1 would silently evaporate the
rationale with no test noticing. T5 asserts the declaration, not the arithmetic.

### S3 — Classify in `resolve_lifecycle` (`lifecycle.py:191-216`)
Add a branch reading the typed field and setting `death_reason` to `STARVATION` / `SLEEP_DEPRIVATION`
with `is_permadeath_set=True` and the existing succession dispatch. It must never infer from
`hunger`/`sleep_debt` (LIMIT-04) nor from role. Reachable only because of R1.

**Guard shape (R6) — v1's "branch ordering" was the wrong mechanism.** The combat and passive facts are
never visible in the same invocation: a combat death is classified at tick N from
`ent_upd.combat.outcome_kind`, while the passive cause is first readable at N+1. Today a combat death is
protected only incidentally, because `resolve_lifecycle` writes `active=False` at N so the `:147` guard
skips the entity at N+1. After R1 that still holds, but it is a **cross-tick idempotency property, not
branch ordering**. Specify it as such: **never classify a passive cause on an entity that already
carries `death_reason` or `is_permadeath`.** Implement it **once**, where the sibling's `DEFEAT` branch
shares it — one implementation, not two. T6 must advance a tick to exercise it; a same-invocation
ordering test passes vacuously.

### S4 — Docs and parity
- `docs/simulation/lifecycle_systems_contract.md`: the new reasons, the **declared** precedence rule
  (S2/R5), the R6 idempotency guard, and R1's authority change.
- `docs/guidelines/intentional_divergences.md`: **required** entry for R1's one-tick shift, alongside
  §2.59 as the template. The rule owner confirmed (2026-10-01) that `PROG-030`'s precedent is sufficient
  for the shift itself; the entry must additionally satisfy the CAUSE-05 traceability condition in S1 —
  if option (a) is taken the entry records that the zeroing tick is preserved in the cause field; if
  option (b), it must state the `death_tick = cause tick + 1` construction explicitly.
- Parity ledger: **`progression.yaml::PROG-030`** (P0 — update `v2_evidence` for the extended contract;
  its `test_path` must pass), plus a new `progression.yaml` entry for the passive death cause and its
  reasons (if filed P0, it needs a passing `test_path`). Re-read `town_resource.yaml` ~:2331-2341, which
  reasons explicitly about `combat.alive_set` never being written for OLD_AGE deaths — R1 moves that
  ground.

### S5 — Tests
Per `test_plan.md`. `event_extractor.py` must remain exact-match on `COMBAT` (AC3) — assert it.

## Scope guards

- Do **not** touch the hazard route or `world_dynamics.py:39` — that is
  `TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND`.
- Do **not** add `DEFEAT`/`REBIRTH` handling here — the sibling's, same batch.
- Do **not** change the `"HAZARD"` discriminant or `_NON_COMBAT_OUTCOME_KINDS`.
- Do **not** introduce a role check on this path; role-blindness is what covers a starving HERO here.
- **The `active=` change (R1) is made exactly once, here.** The sibling asserts against it and must not
  re-edit those lines.

## Acceptance-criteria map

| AC | Steps | Verified by |
|---|---|---|
| 1 — passive death records a distinct reason + full lineage | R1, S1, S2, S3 | T1, T2, T6 |
| 2 — `DEFEAT`/`REBIRTH` leftover never classified by this path | S2 discriminant, R6 guard | T3, T4 |
| 3 — typed, serialized, inspectable; extractor stays exact-match | S1 | T5, T7 |
| 4 — architecture verdict recorded; contract + parity updated | review above, S4 | Implementation Notes + S4 diff |

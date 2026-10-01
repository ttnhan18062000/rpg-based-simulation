---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP
phase: done
date: 2026-09-28
tags: [bug, lifecycle, engine, determinism]
---

# TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP

## Title
Passive starvation/sleep-debt HP-loss deaths are silent: `resolve_lifecycle` has no HP/alive-based
death-detection branch

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`LifecycleSystem.resolve_lifecycle` (`src/systems/lifecycle_systems/lifecycle.py`) currently
detects death via exactly two branches: `age_ticks >= max_age_ticks` (`"OLD_AGE"`, `:193-195`) and
`ent_upd.combat.outcome_kind in ("KILL", "PERMADEATH")` (`"COMBAT"`, `:202-204`) — confirmed by a
repo-wide grep finding these are the only two `death_reason =` string literals anywhere in `src/`.

An entity whose HP is driven to 0 purely by passive hunger/sleep-debt decay
(`ApplyPath._compute_entity_changes`'s `total_passive_dmg` branch, `src/engine/apply.py:98-106`)
writes `combat.hp=0, combat.alive=False, lifecycle.active=False` directly, with no corresponding
`EntityUpdate` for `resolve_lifecycle` to ever observe. It never receives a `death_reason` and
never dispatches lineage consequences (heir/heirloom transfer, nemesis-feud transfer, dying-wish
seeding) — the identical silent-death *symptom* that `TCK-20260928-NATURAL-AGING-DEATH-DUAL-
WRITER-RACE` fixed for old age, but from a genuinely different *cause*: a missing detection
branch, not a timing race between two writers.

Empirically confirmed by that ticket's own investigation and regression test
(`tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py::
test_starvation_sleep_debt_driven_hp_loss_is_still_silent_post_fix`): an entity built with
`hunger=95.0, sleep_debt=98.0, hp=1`, run through one `Kernel.tick_once()`, ends with
`combat.hp=0, combat.alive=False, lifecycle.active=False, lifecycle.death_reason=None` — still
silent after that ticket's writer-precedence fix landed, exactly as expected, since that fix only
changed the age term.

## Production Evidence Added 2026-10-01 (from `TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK`)

C1's authority-boundary check landed on this gap as its **root cause** and produced the unscripted
production evidence this ticket previously lacked. Observed at engine commit `e9db40f0a`.

In **120 unscripted ticks of `frontier_marches` @ seed 42** — no staging, no injection, no forced
dispatch — the signature `combat.alive=False` **and** `lifecycle.active=True` **and**
`death_reason=None` occurs as **9 rows on 8 distinct ticks**, via **three distinct routes** (only the first is this ticket's):

| tick | entity | hp | hazard drain | `outcome_kind` present | route |
|---|---|---|---|---|---|
| 2 | 63 | 0 | 30 | none | hazard-only drain death |
| 4 | 55 | 0 | 30 | none | hazard-only drain death |
| 5 | 20 | 0 | 20 | none | hazard-only drain death |
| 5 | 21 | 0 | 20 | none | hazard-only drain death |
| 20 | 40 | 0 | 0 | `DEFEAT` | HERO-defender non-lethal — **out of scope, see correction below** |
| 68 | 60 | 0 | 0 | `DEFEAT` | HERO-defender non-lethal — **out of scope** |
| 88 | 33 | 0 | 0 | `REBIRTH` | rebirth path — **out of scope** |
| 113 | 44 | 0 | 0 | `DEFEAT` | HERO-defender non-lethal — **out of scope** |
| 115 | 26 | 0 | 0 | `DEFEAT` | HERO-defender non-lethal — **out of scope** |

**Correction, 2026-10-01 — `DEFEAT` and `REBIRTH` are explicitly OUT OF SCOPE for this ticket,
and the first version of this note got that wrong.** It originally said both should be swept into
this ticket's new branch. That was wrong:
`docs/world_rules/life-body/lifecycle.md` **LIFE-02** ("Incapacitation/defeat does not necessarily
mean death", Disposition: **ACCEPT**) names exactly these two as the *intended non-lethal*
classifications — `DEFEAT` "explicitly non-lethal, e.g. for `EntityRole.HERO`, where `is_lethal` is
forced `False`" (`src/engine/combat.py:136`), `REBIRTH` "`generation_delta=1`, identity continues"
(`combat.py:182-187`, which leaves `perma_set` False) — with "only `PERMADEATH` … as truly final".
**Recording either as an `is_permadeath_set=True` death would contradict an accepted world rule.**

For those two rows the defect runs the other way: a classified-non-lethal outcome is silently
converted into a permanent death by `apply.py:109`'s passive HP gate a tick later. That is a
separate ticket, not this one. (Verified while correcting this: no runtime writer ever sets
`alive=True` again — every `alive=True` in `src/` is construction.)

**What this ticket's branch should key on.** Not an outcome-kind allow-list, and not simply
"`combat.alive=False` with no `death_reason`" either: when passive damage drives `new_hp` to 0,
`apply.py:106`/`:109` set `combat.alive=False` **and** `lifecycle.active=False` in the same apply,
and `resolve_lifecycle`'s loop guard (`:147-148`) then skips the entity permanently. So the passive
route needs a retroactive pass over **already-inactive, unreasoned** entities, while the hazard
route can be caught same-tick from the update. Two shapes, one ticket.

**Not a new death_reason literal decision.** Only `OLD_AGE` and `COMBAT` exist repo-wide; what the
missing branch should record (a `HAZARD` literal, a generic `UNKNOWN`/`INJURY`, or per-route
literals) is still this ticket's call and C1 deliberately did not pre-empt it.

Full evidence, instrument caveats and the separately-routed overwrite defect:
`stored_artifacts/TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK/investigation.md`.
Regression coverage asserting the current defective behaviour (expected to fail when this ticket's
fix lands, and to be rewritten rather than deleted):
`tests/mechanic_scenarios/test_entity_death_authority_boundary.py`.

## Scope
**Narrowed 2026-10-01 (user decision, via rpg-feature-planning): partial delivery.** This ticket ships
only the same-tick `HAZARD` half. The passive hunger/sleep-debt half moves to
`TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER`, because classifying it needs a
persisted cause that does not exist today (see Implementation Notes).
- Add a `resolve_lifecycle` branch that records `death_reason="HAZARD"` for a same-tick hazard-drain death
  (`outcome_kind == "HAZARD"`, `alive_set is False`) and runs the existing lineage dispatch.
- Rewrite the two C1 pinned-defect tests to the fixed contract; update the contract and parity ledger.

## Out of Scope
- `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE`'s own writer-precedence fix (already
  shipped, unaffected by this ticket).
- Any change to the `total_passive_dmg` computation itself, the hunger/sleep-debt accrual rates, or
  the `new_hp > 0` immediate-HP-death gate in `ApplyPath._compute_entity_changes` — this ticket
  only adds a *detection* branch in `resolve_lifecycle`, it does not change how or when HP is lost.
- Deciding whether starvation- and sleep-debt-caused deaths need distinct `death_reason` strings
  vs. one shared reason — real design choice for this ticket's own investigation/plan phase, not
  pre-decided here.

## Acceptance Criteria
1. A hazard-drain death is recorded with `death_reason="HAZARD"` the tick it happens, and dispatches
   succession/heirloom/feud/dying-wish like `OLD_AGE`/`COMBAT`.
2. The C1 pinned-defect tests are rewritten to the fixed contract, not deleted; the negative control
   still passes.
3. Passive starvation/sleep-debt deaths are explicitly NOT classified here and the gap stays documented
   as open in `docs/simulation/lifecycle_systems_contract.md`; the follow-up ticket exists.
4. `DEFEAT` / `REBIRTH` are not classified as deaths (LIFE-02); that defect has its own ticket.
5. Existing death, inheritance, passive-decay, clan-lifecycle and vacancy tests pass unmodified.
6. Parity ledger entry PROG-126 added; the contract's death-trigger table gains the `HAZARD` row.
**Not delivered (moved):** the original AC1-AC4 for passive bio deaths.

## Related Tickets
- `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE` — parent investigation. Fixed the age
  dual-writer race (AC1-AC6); its own AC7 answered this starvation/sleep-debt path as
  empirically-affected-but-not-fixed-here and split it into this ticket.

## Related Docs
- `docs/simulation/lifecycle_systems_contract.md` — the death-trigger table and Biological section
  this ticket must update once the new branch lands.
- `docs/mechanics/01_entity_anatomy.md` §4 "Biological Laws" — hunger/sleep-debt accrual rates and
  HP-damage thresholds (unaffected by this ticket, which only adds detection, not the underlying
  formula).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE/investigation.md` — the
  empirical probe and root-cause trace this ticket's Request Summary is drawn from.

## Related Code Areas
- `src/systems/lifecycle_systems/lifecycle.py:189-205` — `resolve_lifecycle`'s two existing
  death-detection branches; the new branch belongs alongside these.
- `src/engine/apply.py:98-106` — `ApplyPath._compute_entity_changes`'s `total_passive_dmg` branch,
  the write site this ticket's new detection branch must observe (indirectly, via `combat.alive`
  and the absence of an existing `death_reason`), not modify.
- `tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py::
  test_starvation_sleep_debt_driven_hp_loss_is_still_silent_post_fix` — the pinned pre-fix
  signature this ticket's own fix must update.

## Assumptions / Open Questions
- ~~**Death-reason string(s).**~~ **DECIDED 2026-10-01 by `rpg-feature-planning`: use two distinct
  death reasons, one for hunger-driven and one for sleep-debt-driven death. Do not collapse them
  into a single `"BIOLOGICAL"` reason.** Rationale: this repo produced four separate instances in
  one week of a single field carrying multiple meanings — `owner_faction_id`'s three concepts, the
  `resource_type` node-kind-vs-yield-item collision (`TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND`),
  the same-name class pairs (`TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS`), and a `social_memory`
  homonym that produced a false `depends_on` edge in `registries/mechanisms.yaml`. Two distinct
  death causes sharing one reason string is that same failure, made prospectively. The exact string
  values are an implementation detail for Plan.
- **Detection mechanism shape.** Whether the new `resolve_lifecycle` branch should read
  `entity.combat.alive` (pre-tick, already `False` from a *prior* tick's passive write) or inspect
  something staged this same tick is an implementation detail for the investigation phase to
  resolve against the real phase-ordering trace, not assumed here.

## Implementation Notes
- Design history, recorded because it explains the narrowing. A first version recorded passive deaths
  retroactively (inactive, combat-dead, unrecorded entity at hunger >= 95 / sleep_debt >= 98 ->
  `STARVATION`/`SLEEP_DEPRIVATION`, with succession). It was dropped: `outcome_kind` is not persisted,
  `DEFEAT` can also hit non-HERO entities (opportunity attacks force `is_lethal=False`, `combat.py:251`,
  `movement.py:241`), so a `DEFEAT` leftover at a threshold would be stamped dead with succession fired.
  Inferring cause from being at a threshold fabricates provenance (`LIMIT-04`, `CAUSE-01`, `HP-02`,
  `CAUSE-05`, `LIFE-02`). A role gate does not close the hole.
- Accepted risk of shipping only `HAZARD`: ALL passive bio deaths stay unrecorded, exactly as today. A
  known, reversible gap, not new damage.
- The sound fix records the cause at the writer: when `apply.py`'s passive branch takes HP from positive to
  zero (`comb.hp > 0 and new_hp == 0`). A `DEFEAT`/`REBIRTH` entity is already at `hp == 0`, so that
  condition excludes every combat-caused zero with no role or outcome inference. It needs a typed field
  (Durable State Rule) and an architecture-reviewer pass first; filed as its own ticket.
- `resolve_lifecycle`: new same-tick `HAZARD` branch after the `COMBAT` check; `is_permadeath_set=True`
  and the full dispatch are reused unchanged.
- The combat+hazard collision is now recorded as `HAZARD`, not `COMBAT`: an improvement, not a fix for
  `TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND`.
- Evidence is two-source: a `frontier_marches` probe here reproduced C1's four hazard-death rows
  (entities 20, 21, 55, 63), now recorded as `HAZARD`.

## Test Summary
- `tests/mechanic_scenarios` (incl. the three rewritten/retained death-authority-boundary tests, one slow), `tests/parity`,
  `tests/docs`, `tests/architecture`: pass. Wider lane run (`simulation_quality`, `integration`, `unit/engine`,
  `unit/progression`): 2056 passed; `test_bravery_quartile_combat_rate_2x` and `test_long_run_stability` fail
  identically on the untouched base (control run), so they are not caused by this change.
- The passive starvation test is unchanged and still pins the open gap.

## Files Changed
- `src/systems/lifecycle_systems/lifecycle.py`
- `tests/mechanic_scenarios/test_entity_death_authority_boundary.py`
- `docs/simulation/lifecycle_systems_contract.md`, `docs/parity_ledger/progression.yaml` (PROG-126)

## Completion Summary
Partial delivery by decision (user, via rpg-feature-planning, 2026-10-01): the same-tick `HAZARD` death route is
recorded with the existing succession dispatch. Passive hunger/sleep-debt deaths remain unrecorded (a known,
reversible gap); their fix is `TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER`, and the
defeat-becomes-death defect is `TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE`. LIFE-02's
evidence note was corrected in `docs/world_rules/life-body/lifecycle.md`.

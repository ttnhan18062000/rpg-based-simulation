---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE
artifact_type: plan
tags: [bug, lifecycle, engine, determinism]
---

# Implementation Plan — TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE

## Summary

The dual-writer race is fixed by changing exactly one boolean expression in Writer 1
(`ApplyPath._compute_entity_changes`'s passive branch, `src/engine/apply.py:107-110`) so it can no
longer independently deactivate an entity for old age — deactivation-for-age becomes the sole
responsibility of Writer 2 (`LifecycleSystem.resolve_lifecycle`'s OLD_AGE branch,
`src/systems/lifecycle_systems/lifecycle.py:193-195`). The mechanism that lets Writer 2 override
Writer 1 already exists in the pipeline today (`_compute_entity_changes` calls
`ApplyPath._apply_entity_update_to_dict` for `u_ent` at `apply.py:162-164`, which runs
`LifecyclePatch.apply()`, `src/engine/patches.py:69-73` — it reads Writer 1's own computed
`changes["lifecycle"]` as a base and overrides `.active` whenever Writer 2's `EntityUpdate.active`
is not `None`); the bug is only that Writer 1's own formula computes the wrong value one tick
before Writer 2 ever gets a chance to see the updated age. The new formula,
`active=(new_hp > 0 and (life.active or new_age < life.max_age_ticks))`, is provably
behavior-identical to the current formula in every case except the one buggy case (a currently
active, non-dying entity whose age has just reached the maximum) — it reduces to the current
formula exactly whenever `life.active` is `False` (dead entities, dormant spawns), so it requires
no phase-ordering change, does not touch the `new_hp > 0` immediate-HP-death gate, and does not
collapse the incidental `initial_active=False` reactivation path (Q3). AC7 (starvation/sleep-debt
silent death) is a distinct root cause — a missing HP/alive-based detection branch in
`resolve_lifecycle`, not a timing race — and is answered here as empirically-confirmed-affected,
with its own fix split into a drafted follow-up ticket rather than implemented in this one.

## Steps

### Step 1 — Add the ordinary-per-tick natural-aging regression test (must fail pre-fix)
**Files:** `tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py` (new file)
**Change:** Write an integration test using a real `Kernel.tick_once()` loop (not staged
mid-run state) that constructs an entity with a small `max_age_ticks` (e.g. 3, matching the
investigation's own reproduction) and runs it through ordinary per-tick progression to death.
Assert, across the full trace:
- `death_reason == "OLD_AGE"` once the entity dies (AC1).
- The heir receives the deceased's inventory/heirlooms, matching the already-working staged-age
  assertions in `tests/simulation_quality/test_heir_inventory_transfer_corpus.py` (AC2).
- No tick exists where `active is False and death_reason is None` (AC3) — assert this on every
  tick of the trace, not just the final one.
- The exact tick the death is recorded on is asserted explicitly, with a comment stating the death
  now lands one tick after `age_ticks` first reaches `max_age_ticks` (the tick
  `resolve_lifecycle` next runs against the persisted post-increment age — see Step 2's Change for
  the mechanics), not the tick age reaches max itself (AC4).
Run this test file against the current (unfixed) tree and confirm it fails for the described
reason (`death_reason` stays `None`, not some unrelated error) — this is the proof AC6 requires,
and must be re-run after the file's content is finalized, not assumed from the investigation's own
prior run of the (different, WIP-authored) file.
**Do NOT touch:** `tests/simulation_quality/test_heir_inventory_transfer_corpus.py`,
`tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py`,
`tests/integration/optimization/test_force_full_scan_phase_compliance.py`,
`tests/mechanic_scenarios/test_aging_death_value_differential.py`,
`tests/mechanic_scenarios/test_succession_heir_selection_value_differential.py` — these are the
existing staged-age tests named in the ticket/investigation as masking this bug; they must keep
passing unmodified per AC8, not be rewritten to "fix" them into ordinary-progression tests.
**Verify:** the new test file itself, run and confirmed to fail against pre-fix `src/engine/apply.py`.

### Step 2 — Fix Writer 1's `active=` formula (the declared-authority fix)
**Files:** `src/engine/apply.py`
**Change:** In `ApplyPath._compute_entity_changes` (the passive branch), change line
`active=(new_hp > 0 and new_age < life.max_age_ticks)` (`apply.py:109`, confirmed by direct read)
to `active=(new_hp > 0 and (life.active or new_age < life.max_age_ticks))`. This is the plan's
answer to Q1: **Writer 2 (`resolve_lifecycle`'s OLD_AGE branch) becomes the sole authority for
old-age deactivation; Writer 1 keeps only the immediate HP-death gate.** Do not adopt the WIP
prototype's `active=(new_hp > 0 and life.active)` verbatim — that expression was evaluated in
`investigation.md` and found to silently collapse the Q3 dormant-spawn reactivation path (an
`initial_active=False` entity's `life.active` starts `False` and the WIP formula ANDs against it,
so it can never flip `True` again). The formula above instead ORs `life.active` with the original
age term, so for any entity where `life.active` is currently `False` (a dead entity, or a dormant
spawn) the expression reduces to exactly `new_hp > 0 and new_age < life.max_age_ticks` — bit-
identical to today's formula — while for an entity where `life.active` is currently `True`, age
alone can no longer flip it to `False`. This is the concrete, non-default resolution to both Q1
and Q3 the investigation asked the plan to produce, not a placeholder.

Precedence mechanics this relies on (read, not inferred): `_compute_entity_changes` runs the
passive branch (Section A, `apply.py:84-160`) to build `changes["lifecycle"]` first, then — only
if `u_ent` (Writer 2's own `EntityUpdate` for this entity this tick, sourced from
`update.entity_updates`, itself built by `resolve_lifecycle` during the earlier resolution phase
per `src/engine/kernel.py:387-454`) is truthy — calls
`ApplyPath._apply_entity_update_to_dict(entity, u_ent, changes)` (`apply.py:162-164`, "Section B:
Intentional Logic"). That call runs `extract_patches` (`patches.py:762-764`, which builds a
`LifecyclePatch` whenever `update.lifecycle is not None or update.active is not None`) then
`patch.apply(entity, changes)` for each patch. `LifecyclePatch.apply` (`patches.py:69-73`) reads
`changes.get("lifecycle", entity.lifecycle)` — i.e. Section A's own output, the exact dict this
step edits — as its base, and overrides `.active` with the patch's own `self.active` (sourced from
`EntityUpdate.active`, `updates.py:697`) whenever it is not `None` and differs. So whenever
`resolve_lifecycle` does detect a death this tick (now one tick later than today, once age has
actually persisted past max — `lifecycle.py:193-195` checks `entity.lifecycle.age_ticks >=
entity.lifecycle.max_age_ticks` against `state`, the pre-tick snapshot, per `investigation.md`'s
kernel-phase trace), its `EntityUpdate.active=False` (`lifecycle.py:211-212`) already correctly
overrides whatever Section A computed for that same tick — no code change is needed to this
override mechanism, only to Section A's own formula so it stops disagreeing on the tick *before*
Writer 2 gets a chance to see the persisted age.

Do not change the `new_hp > 0` term. It is the immediate-HP-death gate (combat-adjacent HP loss
must still deactivate promptly) and is orthogonal to the age precedence question, per
`investigation.md`'s Anti-Drift Hazards.
**Do NOT touch:** `src/engine/kernel.py` (no phase-ordering change — this fix works entirely
within the existing resolution-before-advancement order), `src/engine/combat.py` (KILL/PERMADEATH
path, out of scope), `src/engine/patches.py` (the override mechanism already works correctly and
needs no change), the `total_passive_dmg`/hunger/sleep-debt computation at `apply.py:98-106`
(AC7's separate root cause, not touched by this step).
**Verify:** Step 1's test file now passes in full (AC1-AC4); re-run to confirm.

### Step 3 — Add the declared-authority architecture guard (AC5)
**Files:** `tests/unit/engine/test_apply.py` (new test function; create the file if it does not
already exist, colocated with `ApplyPath` per the existing project convention of one test module
per source module)
**Change:** Add a guard test asserting the passive branch's `active=` expression, for an entity
that is currently `active=True`, does not go `False` on the tick its age first reaches
`max_age_ticks` (i.e. it stays `True` for exactly one more tick than the pre-fix formula would
produce) — this is the source-level proof that Writer 1 no longer unilaterally deactivates for
age, matching the shape of the sovereignty ticket's own
`test_world_dynamics_ownership_threshold_uses_shared_constants`-style guard (referenced in
`test_plan.md`, from `stored_artifacts/TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT/`).
Call `ApplyPath._compute_entity_changes` directly (or `ApplyPath.apply_generation` with a
single-entity state, whichever this test module's existing pattern uses) rather than a full
`Kernel.tick_once()`, since this step verifies the narrow formula contract, not the full pipeline
(Step 1 already covers the full pipeline).
**Do NOT touch:** the formula itself (already changed in Step 2) — this step only adds coverage.
**Verify:** the new guard test passes against the Step 2 fix and fails if the formula is reverted
to `active=(new_hp > 0 and new_age < life.max_age_ticks)`.

### Step 4 — Pin the vacancy-detection tick shift (AC4/AC8 interaction)
**Files:** `tests/integration/economy/test_economic_vacancy_signal.py` (new test function; add to
this file rather than `tests/unit/economy/test_vacancy.py` since it needs a real
`Kernel.tick_once()` trace to observe the tick shift, matching this file's existing integration
scope)
**Change:** `src/economy/vacancy.py`'s vacancy check reads `lifecycle.active`/`combat.alive`
directly (per `investigation.md`'s Risks section), not `death_reason`. Since Step 2 shifts the
OLD_AGE death tick by one (the entity now stays `active=True` for one additional tick before
`resolve_lifecycle` catches it), a sole-shopkeeper's vacancy signal for an old-age death will now
fire one tick later than pre-fix. Add a test that runs an old-age death to completion through
`Kernel.tick_once()` and asserts the vacancy event fires on the tick `resolve_lifecycle` records
the death (not the tick age first reached max), documenting this as an intentional,
determinism-visible consequence of Step 2, not an unnoticed side effect. Starvation- and
combat-triggered vacancy detection are unaffected (those paths already set `combat.alive=False`
immediately, per `investigation.md`) — do not add assertions for those paths here, they are
already covered by the existing unmodified tests.
**Do NOT touch:** `src/economy/vacancy.py` itself — no code change needed here, the shift is a
correct and expected consequence of Step 2, not a bug in vacancy detection.
**Verify:** the new test, plus `tests/unit/economy/test_vacancy.py` and
`tests/integration/economy/test_economic_vacancy_signal.py`'s existing tests passing unmodified.

### Step 5 — Add the Q3 (`initial_active=False`) behavior-pin guard
**Files:** `tests/unit/entities/test_archetype_entity_factory.py` (new test function alongside the
existing `test_spawn_initial_active_false`, which stays unmodified per AC8)
**Change:** Construct an entity via `ArchetypeEntityFactory.build_entity` with
`spawn.initial_active=False` (per `src/entities/archetype_factory.py:129-131`, confirmed by
`investigation.md`'s direct read), then run several real `tick_once()`s with `hp>0` and age well
below `max_age_ticks`. Assert the entity's `active` flag reaches `True` after `is_life_due` next
fires — i.e. pin that the accidental reactivation path Step 2's formula deliberately preserves
(`life.active or new_age < life.max_age_ticks` reduces to the original formula when `life.active`
is `False`) still behaves identically post-fix. This is a pin of *current* behavior, not a design
decision: per `investigation.md`, this path has zero production callers today (only this one
construction-only test exercises the flag), so this guard exists solely to catch a *future*
accidental change to the passive branch's formula, per `test_plan.md`'s own Anti-Drift Test Guards
section. Q3's underlying design question (should an `initial_active=False` spawn require an
explicit, intentional activation path instead of this accidental one) is correctly left unanswered
by this ticket and returned to the systemic-world roadmap, as `investigation.md` recommends — do
not invent an intentional activation mechanism here.
**Do NOT touch:** `src/entities/archetype_factory.py`, `src/worldassembly/entity_spawner.py`
(hardcodes `initial_active=True` today, per `investigation.md`; no production caller is affected
either way) — no source change in this step, pin-only.
**Verify:** the new test, plus `test_spawn_initial_active_false` passing unmodified.

### Step 6 — Answer AC7 empirically without fixing it here
**Files:** `tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py` (second scenario
function in the same file, per `test_plan.md`'s primary suggested location; keep the subject
entity for this function entirely separate from Step 1's aging subject, per `test_plan.md`'s own
anti-drift guard against sharing one fixture across the two concerns)
**Change:** Reproduce the investigation's own empirical probe as a real test:
construct an entity with `hunger=95.0, sleep_debt=98.0, hp=1, max_age_ticks` far from reach, run
one `tick_once()`, and assert the currently-confirmed silent signature still holds post-Step-2-fix
(`hp == 0`, `alive is False`, `active is False`, `death_reason is None`). This is an intentional
"pins the known gap" test, not a bug-reproduction-that-must-fail test — it documents, with a
comment citing the follow-up ticket drafted in Step 7, that AC7's root cause (no HP/alive-based
detection branch anywhere in `resolve_lifecycle` — confirmed by `investigation.md`'s repo-wide
grep of `death_reason =` assignments, only `"OLD_AGE"` and `"COMBAT"` exist) is answered as
**affected, not fixed here**, per the ticket's own "fix it here or split it out with a written
reason" scope language. Record this same answer directly in the ticket body's Implementation
Notes at Implement time (not left as `UNKNOWN` or `BLOCKED`).
**Do NOT touch:** `src/systems/lifecycle_systems/lifecycle.py` — do not add a new detection branch
in this ticket; that is the follow-up ticket's own scope (Step 7).
**Verify:** the new test passes (asserting the still-silent signature), documenting AC7's answer.

### Step 7 — Draft and file the AC7 follow-up ticket
**Files:** a new ticket file under `tickets/todos/` or `tickets/inprogress/` (implementer's call,
via the `ticket-scoper`/`create-tickets` workflow at Implement time — not a code file)
**Change:** File a new ticket with:
- **Ticket ID (drafted):** `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP` (adjust the date
  segment to the actual filing date if it differs from today).
- **Title (drafted):** "Passive starvation/sleep-debt HP-loss deaths are silent: `resolve_lifecycle`
  has no HP/alive-based death-detection branch."
- **Scope summary (drafted, one paragraph):** `LifecycleSystem.resolve_lifecycle` currently detects
  death only via two branches — `age_ticks >= max_age_ticks` ("OLD_AGE") and
  `ent_upd.combat.outcome_kind in ("KILL", "PERMADEATH")` ("COMBAT") — confirmed by a repo-wide
  grep finding these are the only two `death_reason =` string literals anywhere in `src/`. An
  entity whose HP is driven to 0 purely by passive hunger/sleep-debt decay
  (`ApplyPath._compute_entity_changes`'s `total_passive_dmg` branch, `apply.py:98-106`) writes
  `combat.hp=0, combat.alive=False, lifecycle.active=False` directly with no corresponding
  `EntityUpdate` for `resolve_lifecycle` to ever observe, so it never receives a `death_reason` and
  never dispatches lineage consequences — the identical silent-death symptom this ticket fixed for
  old age, but from a genuinely different cause (a missing detection branch, not a timing race).
  The fix adds a new `resolve_lifecycle` branch that detects an already-`combat.alive=False`
  entity with no existing `death_reason` reaching this tick's refine pass, assigns a new
  `death_reason` (e.g. `"STARVATION"` or `"BIOLOGICAL"` — the follow-up ticket's own investigation
  should decide the exact string and whether hunger- and sleep-debt-caused deaths need to be
  distinguished), and wires it through the same lineage-dispatch path (heir/heirloom transfer,
  nemesis-feud transfer, dying-wish seeding) OLD_AGE and COMBAT already use. This is a materially
  larger, separately-verifiable piece of work than this ticket's writer-precedence fix, and does
  not depend on it.
**Do NOT touch:** do not begin implementing the follow-up ticket's fix as part of this one — file
it, then stop.
**Verify:** the new ticket file exists, is correctly formatted per the project's ticket schema, and
this ticket's own AC7 is recorded as answered-not-fixed-here with the follow-up ticket ID cited as
the reason.

### Step 8 — Update the lifecycle systems contract doc (AC5)
**Files:** `docs/simulation/lifecycle_systems_contract.md`
**Change:** In the "Entity lifecycle states" and "Death triggers" sections (currently at
`lifecycle_systems_contract.md:24-33`, confirmed by direct read — the two-flags description and
the death-trigger table), add a subsection stating the declared authority and resolution rule:
`resolve_lifecycle`'s OLD_AGE branch is the sole authority for old-age deactivation;
`ApplyPath._compute_entity_changes`'s passive branch may only deactivate an entity immediately via
its HP gate (`new_hp <= 0`), and — as of this ticket — can no longer independently deactivate an
entity for age once it is already active. Cite the exact formula from Step 2. In the "Biological"
section (currently at `lifecycle_systems_contract.md:67-104`, confirmed by direct read — the
hunger/sleep-debt rates and damage-condition table), add a forward-reference note that a
starvation/sleep-debt-caused HP loss to 0 does **not** currently produce a `death_reason` or
lineage dispatch (still silent, per Step 6's answer), with a citation to the Step 7 follow-up
ticket, since this ticket's own AC7 explicitly leaves that gap open rather than closing it.
**Do NOT touch:** the Combat death trigger row or the Succession/heirlooms section — unaffected by
this ticket's fix (the ticket's own PERMADEATH-vs-KILL table gap, if any, is pre-existing and out
of scope here).
**Verify:** manual read-through confirming the doc now states one clear authority and the AC7 gap
is disclosed, not silently left inconsistent with the code (per `investigation.md`'s Docs
Requiring Update section).

### Step 9 — Add the intentional-divergences entry for the death-tick shift (AC4)
**Files:** `docs/guidelines/intentional_divergences.md`
**Change:** Add a new `§2.59` entry (the next available number after the existing `§2.58`
sovereignty entry at `intentional_divergences.md:1895`, confirmed by direct read), following that
entry's own shape: rationale class `Bug Fix`, stating the old-age death tick now lands one tick
later than pre-fix behavior (the tick `resolve_lifecycle` observes the persisted post-increment
age, rather than the tick the passive branch independently zeroed `active`), citing Step 2's diff
and Step 1's/Step 3's pinning tests as the `Verification` test paths.
**Do NOT touch:** any other numbered entry in this file, including `§2.58` itself.
**Verify:** manual read-through; entry follows the existing format for `Rationale class` and
`Verification` fields used by neighboring entries.

### Step 10 — Update the PROG-030 parity ledger entry (AC9)
**Files:** `docs/parity_ledger/progression.yaml`
**Change:** `PROG-030` (currently `status: legacy_verified`, `test_path: null`, confirmed by
direct read at `progression.yaml:329-337`) is the on-point P0 entry for `test_aging_and_death`.
Update `v2_evidence` to describe the Step 2 fix and cite the death-tick shift, and set `test_path`
to point at Step 1's new regression test (the first P0-required real `test_path` this entry has
had). Use `tools/parity_ledger_writer.py` for this edit, not a raw YAML edit or ad-hoc script (full
schema-validating rewrite; a hand-edited large diff to this file is a known corruption risk per
prior incident history) — per CLAUDE.md's Authoritative Mechanics Rule, this P0 entry requires a
passing `test_path` once its status changes, and this fix supplies one for the first time.
**Do NOT touch:** any other entry in `progression.yaml`, or the SOC-245/SOC-269 entries in
`social_narrative.yaml` (per `investigation.md`, both test lineage-dispatch logic downstream of
death detection via staged already-dead state, unaffected by either writer's fix — no update
needed).
**Verify:** `tools/parity_ledger_writer.py`'s own validation passes; the referenced `test_path`
exists and passes (Step 1's test, confirmed in Step 12).

### Step 11 — Add dated evidence notes to the mechanism registry entries (AC9)
**Files:** `registries/mechanisms.yaml`
**Change:** The `aging_death` entry (lines 634-706, confirmed by `investigation.md`'s direct read)
already carries a 2026-09-20 note flagging `apply.py::_compute_entity_changes`'s own `new_age <
life.max_age_ticks` computation as a possibly-unintended duplicate code path — add a dated
(today's date) follow-up note stating this ticket resolved that flag: the duplication is now a
declared, one-directional precedence (Writer 2 sole authority for age-based deactivation), not two
competing independent writers, and cite this ticket's ID and Step 2's fix. Add a matching dated
note to the `succession` entry (line 707 onward, confirmed by direct read) stating that
natural-aging-triggered succession now correctly fires for ordinary per-tick deaths (previously
only exercised by tests staging age past max), citing Step 1's new regression test as evidence.
**Do NOT touch:** any other mechanism entry in this file, and do not alter either entry's existing
2026-09-20 note text — append a new dated note, don't rewrite history.
**Verify:** manual read-through; both entries carry a note dated to this ticket's implementation
date, distinct from the pre-existing 2026-09-20 note.

### Step 12 — Run the full scoped regression surface (AC8)
**Files:** none (verification only)
**Change:** Run all five scoped pytest command groups from `test_plan.md`'s "Scoped Pytest
Commands" section (core lifecycle/progression + new mechanic-scenario tests; apply-path/apply-plan
optimization parity; economy vacancy; group/clan lifecycle; long-run integration), plus the new
tests added in Steps 1, 3, 4, 5, 6. Confirm every test named in `test_plan.md`'s "Regression
Surface" section passes unmodified, with special attention to the three tests explicitly flagged
as needing confirmation rather than assumption:
`tests/unit/engine/test_dirty_set_passive_decay_consumers.py` (all 4 tests — exercises Writer 1's
formula on an already-combat-dead fixture where `new_hp > 0` is already `False`, hand-traced by
`investigation.md` as unaffected but must run for real),
`tests/integration/optimization/test_force_full_scan_phase_compliance.py:242-252` (a third
staged-past-max OLD_AGE test beyond the two the ticket names), and
`tests/unit/entities/test_archetype_entity_factory.py::test_spawn_initial_active_false`. Record
the full pass/fail counts and which command groups were run in the ticket's own Test Summary
section at Implement/Finalize time.
**Do NOT touch:** do not modify any test in the Regression Surface list to make it pass — if any
fails, per the Gate Integrity rule, stop and report it as a real finding rather than editing the
test to route around it.
**Verify:** this step is itself the verification; its output is the evidence AC8 requires.

## Scope Guards

- Do not change `src/engine/kernel.py`'s phase ordering (Init → Scheduling → Collection →
  Resolution → Cleanup → Advancement → Persistence). The Step 2 fix works entirely within the
  existing order; if any implementation difficulty tempts a phase-ordering change instead, stop
  and escalate to `rpg-feature-planning` before proceeding, per the ticket owner's explicit
  scope guard (`TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION` would need sequencing
  against any such change).
- Do not touch `src/engine/combat.py`'s KILL/PERMADEATH path or `resolve_lifecycle`'s COMBAT
  branch (`lifecycle.py:202-204`). Out of scope per the ticket; investigation traced it as routing
  through `ent_upd.combat.outcome_kind`, not the passive branch's age/hp gate, and unaffected by
  Step 2's formula change (verified by hand-trace above, not by running a scenario — Step 12's
  regression run is the closest available confirmation).
- Do not touch `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`'s territory (region/faction
  ownership fields). Held, out of scope, different fields entirely.
- Do not edit `docs/plans/systemic_world/{first_wave_plan.md,ticket_planner_handoff.md,roadmap.md}`.
  These files do not exist in this worktree (only on the unmerged `systemic-world-roadmap-proposal`
  branch, PR #249); already flagged to `rpg-feature-planning` as a cross-branch gap, not this
  ticket's problem to solve.
- Do not implement AC7's actual fix (a new `resolve_lifecycle` HP/alive detection branch) in this
  ticket. Answer it (Step 6) and file the follow-up (Step 7); do not begin its implementation.
- Do not decide Q3's underlying design question (whether `initial_active=False` spawns need an
  intentional activation mechanism). Pin current behavior (Step 5) and leave the design question
  for the systemic-world roadmap, per `investigation.md`'s explicit instruction not to default it.
- Do not modify `src/economy/vacancy.py`. The vacancy-detection tick shift (Step 4) is a correct,
  expected consequence of the fix, not a defect in vacancy detection.
- Do not rewrite any of the staged-age tests named in `investigation.md`/`test_plan.md`
  (`test_heir_inventory_transfer_corpus.py`, `test_lineage_dispatch_deterministic_kernel_tick.py`,
  `test_force_full_scan_phase_compliance.py`, `test_aging_death_value_differential.py`,
  `test_succession_heir_selection_value_differential.py`) to exercise ordinary progression instead
  of staged state — Step 1 adds a new file for that; these existing files must pass unmodified
  (AC8).
- Do not hand-edit `docs/parity_ledger/progression.yaml` outside `tools/parity_ledger_writer.py`
  (Step 10) — raw/ad-hoc edits to this file are a known corruption risk.

## Dependency Map

- Step 2 depends on Step 1 (the test must exist and be confirmed failing against pre-fix code
  first, to satisfy AC6's "fails against pre-fix code, proven by running it" requirement).
- Step 3 depends on Step 2 (the guard test asserts the post-fix formula's behavior).
- Step 4 depends on Step 2 (needs the real tick-shift to exist to pin it).
- Step 5 depends on Step 2 (asserts the formula's Q3-preserving branch post-fix; logically could
  run against pre-fix code too since that branch is unchanged, but sequencing after Step 2 avoids
  re-running it twice).
- Step 6 has no code dependency on Steps 1-5 (different code path, unfixed either way), but should
  run after Step 1 exists so both natural-aging scenarios live in the same test file per
  `test_plan.md`'s suggested location.
- Step 7 depends on Step 6's empirical answer (the follow-up ticket's scope text cites it).
- Steps 8, 9 depend on Step 2 (they document the fix and the tick shift it produces) and, for
  Step 8's AC7 forward-reference, on Step 7 (the follow-up ticket ID must exist to cite).
- Step 10 depends on Step 1 (the `test_path` it points at) and Step 2 (the `v2_evidence` it
  describes).
- Step 11 depends on Step 2 (aging_death note) and Step 1 (succession note, citing the new
  regression test).
- Step 12 depends on all prior steps being complete; it is the final gate before Finalize.
- All other step pairs are independent and can be done in any relative order within the
  constraints above.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — OLD_AGE death via ordinary progression | Steps 1, 2 | `tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py` (new) |
| AC2 — lineage consequences dispatch | Steps 1, 2 | same file, heir/heirloom assertion |
| AC3 — no silent `active=False`/`death_reason=None` terminal tick | Steps 1, 2 | same file, full-trace assertion |
| AC4 — death tick pinned and shift documented | Steps 1, 2, 9 | same file's tick-pin assertion + `docs/guidelines/intentional_divergences.md` §2.59 |
| AC5 — single declared authority documented with resolution rule | Steps 2, 3, 8 | `tests/unit/engine/test_apply.py` guard + `docs/simulation/lifecycle_systems_contract.md` |
| AC6 — regression test fails against pre-fix code | Step 1 | same file, confirmed failing before Step 2 lands |
| AC7 — starvation/sleep-debt path answered (affected, split out) | Steps 6, 7 | same file's second scenario function + drafted follow-up ticket `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP` |
| AC8 — existing tests pass unmodified | Step 12 | full scoped regression surface per `test_plan.md` |
| AC9 — registry/parity dated evidence notes | Steps 10, 11 | `docs/parity_ledger/progression.yaml::PROG-030` + `registries/mechanisms.yaml::aging_death`/`::succession` |

## Anti-Drift Notes

- **Do not conflate the age-race fix with the AC7 starvation gap fix.** Step 2's formula change
  touches only the age term; it does not and cannot fix AC7 (confirmed distinct root cause per
  `investigation.md`). Steps 6-7 answer AC7 without implementing its fix.
- **Do not silently change the `new_hp > 0` gate.** Step 2's formula preserves it exactly;
  verifying this is part of Step 2's own Change text derivation (the formula is provably
  behavior-identical to today's for every `life.active == False` case).
- **The WIP branch's `active=(new_hp > 0 and life.active)` is explicitly not the formula adopted.**
  Step 2 adopts `active=(new_hp > 0 and (life.active or new_age < life.max_age_ticks))` instead,
  specifically because it preserves the Q3 dormant-spawn path the WIP formula silently removes.
  Do not substitute the WIP's formula during implementation on the assumption it is equivalent —
  it is not (see Step 2's Change text for the exact case where they diverge).
- **The vacancy-tick shift (Step 4) is expected, not a regression to chase down.** If Step 12's
  regression run shows `test_vacancy.py`/`test_economic_vacancy_signal.py` failing in a way not
  explained by the one-tick shift, that is a real new finding to report, not something to explain
  away as "the known shift."
- **Q3 stays unresolved as a design question on purpose.** Step 5 pins current (post-fix,
  bit-identical-to-pre-fix) behavior; it does not invent an intentional spawn-activation mechanism.
  Do not let an implementer "helpfully" design one while touching this area.
- **`docs/plans/systemic_world/*` remain unreachable from this worktree.** No step in this plan
  assumes they exist; if a future session merges PR #249's content into this tree, updating the
  first_wave_plan.md §3 scheduling row (already noted as no-longer-owed per the ticket's own
  Assumptions section, since `43db4a7fc` superseded the original override framing) is not part of
  this ticket's scope regardless.

## Unresolved Questions

None. Q1, Q3, and AC7 are resolved above per explicit prior guidance from the ticket owner; no
other open question from `investigation.md` remains that would change this plan's implementation
approach.

## Deviations

No step's approach, scope, or file targets deviated from this plan. One finding surfaced during
Step 12 that the plan did not explicitly anticipate, recorded here for traceability rather than
silently absorbed:

- **Step 4's own framing ("will now fire one tick later than pre-fix") undersold the real
  pre-fix severity.** `EconomicVacancyService.check_and_emit` is only ever invoked from
  `resolve_lifecycle`'s own `recent_deaths` aggregate, which an entity enters only on the tick
  `resolve_lifecycle` itself detects `is_dead=True`. Pre-fix, an ordinary-progression old-age death
  was never added to `recent_deaths` at all (skipped forever once the passive branch silently
  deactivated it), so the vacancy signal did not merely fire one tick late for this specific path —
  it never fired. Post-fix it correctly fires one tick after `age_ticks` first reaches
  `max_age_ticks`, exactly as Step 4 intended the test to pin; the test and its assertions did not
  need to change, only this framing note.
- **Step 12's regression run surfaced two pre-existing, unrelated test failures**
  (`tests/integration/world/test_long_run_stability.py::test_long_run_stability` and
  `tests/integration/kernel/test_long_run_determinism.py::test_1000_tick_determinism`, both a
  `TimeoutError` from a `governance_ecology` phase-cost spike around tick 501). Confirmed
  pre-existing by temporarily reverting `src/engine/apply.py` to its pre-fix content and
  re-running both tests: byte-identical failure (same tick, same phase-cost breakdown) before the
  fix was restored. Matches the already-known, owner-parked "slow regression" class of issue.
  Per the plan's own Step 12 "Do NOT touch" instruction, these were not modified — reported as a
  real, pre-existing finding in the ticket's Implementation Notes and Test Summary instead.

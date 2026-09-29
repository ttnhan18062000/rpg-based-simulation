---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE
artifact_type: test_plan
tags: [bug, lifecycle, engine, determinism]
---

# Test Plan — TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE

## Regression Surface

All of the following pass today against `origin/main`; the ticket's AC8 requires them to keep
passing unmodified (or any change justified explicitly, per the Gate Integrity rule). Grouped by
domain, as required.

**Unit — lifecycle/progression core:**
- `tests/unit/progression/test_lifecycle.py` — in particular `test_aging_per_tick`,
  `test_death_by_old_age` (staged `age_ticks=1000==max_age_ticks`, calls `resolve_lifecycle`
  directly — unaffected by either writer), `test_combat_death_classification`,
  `test_permadeath_death_classification`, `test_succession_and_heirloom_transfer`,
  `test_manual_heir_entity_id_transfers_even_if_heir_inactive`,
  `test_default_heir_selected_from_strongest_bond` and the other `test_default_heir_*` variants,
  `test_life_stage_flips_at_age_boundary`, `test_life_stage_transition_is_monotonic_forward_only`,
  the `test_coming_of_age_*` family, `test_sole_shopkeeper_death_emits_vacancy_event`,
  `test_non_sole_occupant_death_does_not_emit_vacancy_event`,
  `test_role_and_region_scope_of_sole_occupant_check`, `test_near_death_hardening_logic`,
  the `test_lifecycle_component_canonical_dict_*`/`test_lifecycle_patch_apply_*` round-trip tests.
- `tests/unit/entities/test_archetype_entity_factory.py::test_spawn_initial_active_false` — the
  construction-only assertion this ticket's Q3 discussion depends on staying true.
- `tests/unit/engine/test_dirty_set_passive_decay_consumers.py` — all 4 tests. Directly exercises
  Writer 1's own `active=` formula (via a real `AuthoritativeApplyPipeline.refine()` +
  `ApplyPath.apply_generation()` call) on an already-combat-dead fixture where `new_hp > 0` is
  already False; confirmed by hand-trace to be unaffected by the WIP-style candidate fix, but must
  be run for real, not assumed.
- `tests/unit/engine/test_lifecycle_supervisor.py`

**Unit — passive-decay/apply-path plumbing:**
- `tests/unit/domains/optimization/test_apply_plan_builder.py`
- `tests/integration/optimization/test_apply_plan_parity.py`
- `tests/integration/optimization/test_component_patch_apply_parity.py`
- `tests/integration/optimization/test_phase_skip_parity.py`
- `tests/integration/optimization/test_force_full_scan_phase_compliance.py` — contains a
  staged-past-max OLD_AGE assertion (`:242-252`) on `refined.entity_updates[1].active`, a third
  "stages age past max" test beyond the two the ticket names; confirm explicitly.

**Unit — economy vacancy:**
- `tests/unit/economy/test_vacancy.py`

**Integration — economy vacancy / lineage dispatch / long-run stability:**
- `tests/integration/economy/test_economic_vacancy_signal.py`
- `tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py` — stages age past
  max (ticket-named).
- `tests/integration/world/test_long_run_stability.py` (cited by
  `docs/simulation/lifecycle_systems_contract.md`'s own "Regression tests" section — death
  detection, succession, permadeath flag, influence shift on death)
- `tests/integration/kernel/test_long_run_determinism.py` (hunger/sleep accumulation rates, HP
  damage at thresholds — same doc)

**Group/clan lifecycle:**
- `tests/unit/social/test_group_lifecycle_fields.py`
- `tests/unit/domains/faction/test_clan_lifecycle.py`
- `tests/unit/domains/faction/test_clan_succession.py`

**Simulation-quality / mechanic-scenario (mechanism-registry-cited, staged-age pattern — the exact
class of test the ticket's own root-cause note says is masking the bug; must be re-verified, not
re-authored):**
- `tests/simulation_quality/test_heir_inventory_transfer_corpus.py` (ticket-named)
- `tests/simulation_quality/test_age_tier_transitions_corpus.py`
- `tests/mechanic_scenarios/test_aging_death_value_differential.py` (backs
  `registries/mechanisms.yaml::aging_death`'s own verification)
- `tests/mechanic_scenarios/test_succession_heir_selection_value_differential.py`

**Demographics / archetype-choice (construct entities with `max_age_ticks` but do not exercise the
race directly — lower risk, still in scope for the scoped run):**
- `tests/unit/world/test_demographics.py`
- `tests/unit/strategic/test_coming_of_age_archetype_choice.py`

## New Tests Required

Per acceptance criteria:

1. **`test_natural_aging_death_is_recorded_as_old_age_and_dispatches_succession`** (AC1, AC2)
   - Category: integration (real `Kernel.tick_once()` loop, no staged mid-run state)
   - Verifies: an entity aged to `max_age_ticks` through ordinary per-tick progression ends with
     `death_reason == "OLD_AGE"`, and the heir receives the deceased's inventory/heirlooms
     (matching the existing staged-age tests' own assertions).
   - Location: `tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py` (new file; the WIP
     branch's own file of this name is optional starting evidence, not to be merged as-is — its
     assertions must be re-derived against whatever Q1 resolution the plan actually adopts).

2. **`test_no_tick_leaves_the_subject_inactive_without_a_death_reason`** (AC3)
   - Category: integration, same harness as #1
   - Verifies: across the full natural-aging trace, no tick exists where
     `active is False and death_reason is None` — the silent-death signature this ticket exists to
     eliminate.
   - Location: `tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py`

3. **`test_old_age_death_tick_is_pinned`** (AC4)
   - Category: integration, same harness
   - Verifies: the exact tick the death is recorded on (relative to the tick `age_ticks` first
     reaches `max_age_ticks`) is asserted explicitly, with a comment stating whether/why it shifted
     relative to pre-fix behavior. Must fail loudly (not silently pass) if the tick shifts again in
     the future without an update here.
   - Location: `tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py`

4. **A source-level or behavioral guard for the declared authority (AC5)**
   - Category: architecture guard
   - Verifies: whichever writer is declared authoritative, the other writer's code path cannot
     independently flip `lifecycle.active` to a *different* value than the authoritative writer
     would produce for the same tick/state — e.g. (shape depends on the plan's Q1 decision) a guard
     that the passive branch's `active=` expression never depends on `new_age`/`max_age_ticks`
     directly (if Writer 2 is chosen sole authority), or an equivalent check if Writer 1 is chosen
     instead. Pattern-matches the sovereignty ticket's own
     `test_world_dynamics_ownership_threshold_uses_shared_constants`-style source guard
     (`stored_artifacts/TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT/`).
   - Location: `tests/unit/engine/test_apply.py` or `tests/unit/progression/test_lifecycle.py`
     (implementer's call, prefer colocating with whichever function's own test module already
     covers it).

5. **Regression test that fails against pre-fix code (AC6)**
   - Category: integration, same as #1-#3 but explicitly run-and-confirmed against the pre-fix tree
     before merging (not merely asserted) — this investigation already performed that confirmation
     once using the WIP branch's own file (3/3 fail against current `origin/main`-equivalent code);
     the plan/implementation phase must re-confirm against whatever the actual new test file's
     content ends up being, since it may differ from the WIP file.
   - Location: same file as #1-#3, or split if the implementer prefers one file per concern.

6. **Starvation/sleep-debt silent-death answer (AC7)**
   - Category: integration
   - Verifies (empirically, already reproduced once in this investigation): an entity driven to
     `hp<=0` purely via passive hunger/sleep-debt decay (no combat, no aging) either (a) now
     produces a real `death_reason` and dispatches lineage consequences identically to OLD_AGE/
     COMBAT, if fixed in this ticket, or (b) is explicitly asserted to still reproduce the silent
     signature with a comment pointing at the split-out follow-up ticket, if descoped — either way,
     `UNKNOWN` must not be the closing state (per AC7's own text). This investigation's own probe
     (hunger=95.0, sleep_debt=98.0, hp=1, one `tick_once()` call → `active=False,
     death_reason=None`) is a ready-made starting fixture.
   - Location: `tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py` (a second scenario
     function in the same file) or a new sibling file
     `tests/mechanic_scenarios/test_passive_biological_death_dispatch.py` if split out.

7. **`initial_active=False` spawn behavior under the chosen fix (Q3, conditional)**
   - Category: unit
   - Verifies: whatever the plan decides for Q3 (explicitly removing the accidental reactivation
     path with a documented rationale, or preserving/replacing it with an intentional one) is
     covered by a real runtime test (construct with `initial_active=False`, run several
     `tick_once()`s with `hp>0`/age below max, assert the entity's `active` stays `False` or is
     reactivated only through the documented mechanism — not left as an implicit side effect of
     whichever formula happens to be chosen).
   - Location: `tests/unit/entities/test_archetype_entity_factory.py` (construction-adjacent) or
     `tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py` (runtime-adjacent);
     implementer's call based on where the fix actually lands. **Only required if Q3 is answered in
     this ticket rather than returned to the systemic-world roadmap** — if returned, this test is
     not required, but the return-to-roadmap decision itself should be stated in Implementation
     Notes.

## Scoped Pytest Commands

```
# Core lifecycle/progression + new mechanic-scenario regression
.venv/bin/python3 -m pytest tests/unit/progression/test_lifecycle.py \
  tests/unit/engine/test_dirty_set_passive_decay_consumers.py \
  tests/unit/engine/test_lifecycle_supervisor.py \
  tests/unit/entities/test_archetype_entity_factory.py \
  tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py \
  tests/mechanic_scenarios/test_aging_death_value_differential.py \
  tests/mechanic_scenarios/test_succession_heir_selection_value_differential.py \
  -q

# Apply-path / apply-plan optimization parity (the exact plumbing the fix touches)
.venv/bin/python3 -m pytest tests/unit/domains/optimization/test_apply_plan_builder.py \
  tests/integration/optimization/test_apply_plan_parity.py \
  tests/integration/optimization/test_component_patch_apply_parity.py \
  tests/integration/optimization/test_phase_skip_parity.py \
  tests/integration/optimization/test_force_full_scan_phase_compliance.py \
  -q

# Economy vacancy (death-as-vacancy-signal consumer)
.venv/bin/python3 -m pytest tests/unit/economy/test_vacancy.py \
  tests/integration/economy/test_economic_vacancy_signal.py -q

# Group/clan lifecycle (AC8-named domain)
.venv/bin/python3 -m pytest tests/unit/social/test_group_lifecycle_fields.py \
  tests/unit/domains/faction/test_clan_lifecycle.py \
  tests/unit/domains/faction/test_clan_succession.py -q

# Long-run integration (death detection/succession/determinism at scale)
.venv/bin/python3 -m pytest tests/integration/world/test_long_run_stability.py \
  tests/integration/kernel/test_long_run_determinism.py \
  tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py \
  tests/simulation_quality/test_heir_inventory_transfer_corpus.py \
  tests/simulation_quality/test_age_tier_transitions_corpus.py -q
```

Never `pytest tests/`. All five groups above are scoped to the domains this ticket's fix can
plausibly touch (lifecycle/progression, apply-path plumbing, economy vacancy as a downstream
consumer, group/clan lifecycle as an AC8-named adjacent domain, and long-run/lineage-dispatch
integration).

## Anti-Drift Test Guards

- **The AC6 "fails against pre-fix code" proof must be re-run against the actual final diff, not
  only against the WIP branch's file.** A regression test that happens to fail today for the wrong
  reason (e.g. a typo) would falsely satisfy AC6; confirm the failure reason matches the described
  defect (death_reason stays `None`), not merely "the test fails."
- **A guard that the starvation/sleep-debt fix (if done here) does not also change the age fix's own
  tick-pinning (AC4).** These are two different code paths inside the same function
  (`_compute_entity_changes`); a test asserting the pinned OLD_AGE tick should not incidentally
  start failing because of an unrelated starvation-path change, and vice versa. Keep the two
  scenario functions in #1-#3 and #6 independent (separate entities/fixtures), not sharing one
  subject.
- **A guard against `initial_active=False` silently regressing (Q3)** — even if Q3 is explicitly
  returned to the roadmap rather than fixed here, add or confirm one test that pins *current*
  behavior (whatever it ends up being post-fix) for an `initial_active=False` spawn across several
  ticks, so a future change to the passive branch's formula that silently reintroduces or removes
  the reactivation side effect is caught, rather than discovered again by inspection.
- **A guard against the economy-vacancy consumer silently changing its own detection tick.** If the
  death tick genuinely shifts by one (AC4), `src/economy/vacancy.py`'s `if not
  other.lifecycle.active or not other.combat.alive` check will now fire one tick later for an
  old-age death specifically (starvation/combat deaths are unaffected, since those already set
  `combat.alive=False` immediately). Add or confirm a test that pins the vacancy-detection tick
  relative to the OLD_AGE death tick explicitly, so this one-tick shift is a documented, tested fact
  rather than an unnoticed side effect discovered later in production telemetry.

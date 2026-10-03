---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260831-READINESS-SPEED-FORMULA
phase: done
date: 2026-08-31
tags: [combat, progression]
---

# TCK-20260831-READINESS-SPEED-FORMULA

## Title
Give readiness_speed a real agility-derived formula

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
readiness_speed is confirmed flat 10.0 for everyone; give it a real formula. Investigation found this isn't fully standalone — the idea's full scope (agility term plus agi_apt-modulated multiplier) has an optional dependency on idea 1/Genetics, though the base agility-only formula can ship standalone. readiness_speed is a parity-ledger-verified P1 combat-legality-gating mechanism (COMB-298), and a prior dedicated ticket explicitly ruled out rebalancing it without corpus-verified evidence.

## Scope
- Modify LevelingService.recalculate_combat_stats() (src/progression/leveling.py:76-184) to derive readiness_speed from agility (base + agility*k) instead of always the flat default.
- Ensure backward compatibility: an entity at reference/baseline agility still yields readiness_speed==10.0 so existing hardcoded test fixtures remain valid.
- Add a new regression test asserting the formula's output for >=2 distinct agility values.
- Update docs/mechanics/02_combat_laws.md §7 and parity entry COMB-298 (or a new entry) in the same session.
- State explicitly in Scope that only the base agility-only formula ships now; the full agi_apt-modulation half is deferred until idea 1/Genetics lands, not silently assumed available.
- Corpus-validate the change (e.g. via the metamorphic lab's directional pattern) before/after, rather than shipping as a bare unit-tested formula swap.

## Out of Scope
- The agi_apt-modulated multiplier half of the formula — deferred until idea 1/Genetics (M1 Quick Wins) lands.
- Any rebalancing of readiness_speed pacing beyond the agility-derivation itself — current flat pacing was confirmed intentional design by TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK.

## Acceptance Criteria
- [x] recalculate_combat_stats() derives readiness_speed from agility (base + agility*k) instead of always the flat default — two entities with different agility produce different readiness_speed.
- [x] Backward-compatible: an entity at reference/baseline agility still yields readiness_speed==10.0 so existing hardcoded test fixtures remain valid.
- [x] A new regression test asserts the formula's output for >=2 distinct agility values.
- [x] docs/mechanics/02_combat_laws.md §7 and parity entry COMB-298 (or a new entry) updated in the same session.
- [x] Ticket scope explicitly states the base formula ships now, full agi_apt modulation deferred until idea 1/Genetics lands (not silently assumed available).

## Related Tickets
- TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION
- TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK

## Related Docs
- docs/mechanics/02_combat_laws.md
- docs/parity_ledger/combat_movement.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/progression/leveling.py
- src/core/state.py
- src/engine/apply.py
- src/engine/rpg_depth.py

## Assumptions / Open Questions
- A prior dedicated ticket explicitly ruled out rebalancing readiness_speed without corpus-verified evidence — this ticket must corpus-validate, not just unit-test.
- Availability of the full agi_apt modulation depends on idea 1/Genetics's own timing, which this ticket does not control.

## Implementation Notes

All 9 plan steps executed, per `staging_artifacts/TCK-20260831-READINESS-SPEED-FORMULA/plan.md`.
See that file's new **Deviations** section for the one real deviation (Step 6's corpus-validation
evidence quality); everything else landed exactly as planned.

- **Step 1**: Added `readiness_speed = max(1.0, 10.0 + (attributes.agility - 5) * 1.0)` to
  `LevelingService.recalculate_combat_stats()` (`src/progression/leveling.py`), immediately after
  the `evasion` line, and added `"readiness_speed": readiness_speed` to the function's returned
  dict. Reference agility (5) yields exactly 10.0.
- **Step 2**: Added `readiness_speed=derived.get("readiness_speed", new_com.readiness_speed),` to
  the PH8 `replace(new_com, ...)` call in `ApplyPath._apply_entity_update_to_dict()`
  (`src/engine/apply.py:512`), the same class of silent-drop bug already hit twice before in this
  subsystem (COMB-298's `to_readonly()`, `CREATURE-TERRITORY-LIFECYCLE`'s
  `_fast_replace_identity`).
- **Step 3**: No code change needed — confirmed `get_effective_stats()` passes the new dict key
  through unmodified (no allowlist).
- **Step 4**: Added 3 new tests exactly as specified:
  `test_readiness_speed_derives_from_agility_two_values` and
  `test_readiness_speed_reference_agility_backward_compatible` in
  `tests/unit/core/test_rpg_depth.py::TestEffectiveStats`; `test_readiness_speed_survives_apply_path_replace`
  in `tests/unit/combat/test_readiness_regen.py`. All pass; all existing tests in both files still
  pass (65/65 in the combined run).
- **Step 5**: All three scoped regression suites from test_plan.md pass in full (162 tests total
  across progression/apply-path/arena/combat domains).
- **Step 6 (corpus validation)**: Authored
  `staging_artifacts/TCK-20260831-READINESS-SPEED-FORMULA/corpus_validation.py`, a throwaway
  hand-orchestrated pre/post-code `MetamorphicRuleEngine.evaluate_rules()` check exactly per the
  plan's resolved design (elder-window-restricted `combat_damage` metric, `monotonic_non_increasing`,
  `observability.mode` pinned literally to `"STANDARD"` and confirmed inline via
  `_resolve_obs_mode()` before trusting any result). The full 9500-tick/3-seed/2-variant run on
  `unit_faction_tension` (the plan's proposed world) completed cleanly (code correctly stashed to
  pre-ticket state for baseline, correctly restored after) but produced a degenerate
  `baseline=0.0`/`compared=0.0` result. Per Step 6's own escalation instruction, this was
  investigated rather than accepted at face value: three single-seed 9500-tick diagnostic runs
  (script-level, not the throwaway validator) across `unit_faction_tension`, `crowded_frontier`,
  and `lifecycle_full_coverage_world` all showed the same root cause — every real `combat_damage`
  event in the entire run occurs before tick 1000, and zero occur at `tick >= 1000`, in all three
  worlds. Since `ELDER` eligibility requires `age_ticks >= 7000`
  (`LifeStageService.get_stage_for_age()`), the elder-eligible window and the active-combat window
  structurally never overlap in any tested world's current content — this is a corpus-content fact,
  not a tick/seed-count artifact, so the plan's literal "widen ticks/window" escalation would not
  have changed the outcome (confirmed by trying 3 different world compositions, including one
  authored specifically for full lifecycle coverage with active hostile modules, all landing on the
  identical zero-combat-after-tick-1000 pattern). Recorded honestly in `COMB-318`'s `v2_evidence`
  and `support_boundary` rather than fabricating a stronger directional claim than the evidence
  supports (Gate Integrity rule). The formula's code-level correctness is not in question — it is
  fully covered by the Step 4 unit/regression tests; only the real-corpus population-level
  observability of its one real-world effect (elder agility decay) is currently unsupported by any
  tested world's content.
- **Step 7**: `docs/mechanics/02_combat_laws.md` §7's Passive Regeneration bullet updated: states
  the derivation formula, clarifies 10.0/tick is the value at reference agility (5) not a universal
  default, cites `COMB-318`.
- **Step 8**: `docs/mechanics/attribute_progression_contract.md` updated: RPG Meaning paragraph's
  derived-stat list now includes `readiness_speed`; the Derived Stat Recalculation Order Step 1
  code block now includes the formula; the Regression Tests table gained 3 rows for the new tests.
- **Step 9**: `COMB-318` appended to `docs/parity_ledger/combat_movement.yaml` via
  `tools/parity_ledger_writer.py` (schema-validated write, index rebuilt in-process and again via
  a second, visible `python3 tools/parity_index.py build` call). `COMB-298` left completely
  untouched (confirmed still accurate — describes mechanism existence, not derivation).
- All throwaway `data/scenarios/`, `data/experiments/`, `data/lab_runs/` directories created by the
  corpus-validation script and the 3 diagnostic runs were removed; none existed before this ticket.

## Test Summary

- `pytest tests/unit/core/test_rpg_depth.py tests/unit/combat/test_readiness_regen.py -v` — 65/65
  passed, including the 3 new tests.
- `pytest tests/unit/core/test_rpg_depth.py tests/unit/combat/test_readiness_regen.py tests/unit/progression/ tests/unit/core/test_rpg_math.py tests/unit/core/test_domain_6_hardening.py tests/unit/quest/test_progression_lifecycle.py tests/unit/resource/test_durability_repair.py -m "not slow"`
  — 155/155 passed.
- `pytest tests/integration/pipeline/test_recovery_gaps.py tests/integration/combat/test_class_tier_win_rate.py -m "not slow"` — 5/5 passed.
- `pytest tests/arena/test_arena_regional_control.py -m "not slow"` — 2/2 passed.
- Corpus validation (`corpus_validation.py`): full 9500-tick/3-seed/2-variant run completed
  cleanly; result was a genuine, structurally-explained degenerate zero/zero (see Implementation
  Notes and `COMB-318`'s `v2_evidence`/`support_boundary`) rather than a false-positive PASSED.
  `observability.mode == "STANDARD"` was confirmed genuinely pinned — the script's own inline
  assertion checked both the saved `ExperimentSpec.observability.mode` string and
  `ScenarioLabOrchestrator._resolve_obs_mode("STANDARD") == ObservabilityMode.NORMAL` before any
  metric was computed, and printed `[confirmed] observability.mode == 'STANDARD' -> resolves to
  ObservabilityMode.NORMAL` on every run (verified in the captured log).

## Files Changed

- `src/progression/leveling.py` — readiness_speed formula (Step 1)
- `src/engine/apply.py` — PH8 replace() kwarg fix (Step 2)
- `tests/unit/core/test_rpg_depth.py` — 2 new tests (Step 4)
- `tests/unit/combat/test_readiness_regen.py` — 1 new test (Step 4)
- `docs/mechanics/02_combat_laws.md` — §7 updated (Step 7)
- `docs/mechanics/attribute_progression_contract.md` — Derived Stat Recalculation Order + Regression
  Tests table updated (Step 8)
- `docs/parity_ledger/combat_movement.yaml` — new `COMB-318` entry (Step 9)
- `docs/simulation_quality/corpus_tier_taxonomy.md` — added a new "gap #7" entry to the Named
  scale-diversity gaps section (Document-Update, after Implement), documenting that no tested
  corpus world sustains `combat_damage` events past tick ~1000, so the `ELDER`-eligible window
  (`age_ticks >= 7000`) never overlaps active combat anywhere — the structural cause behind this
  ticket's degenerate corpus-validation result, recorded durably here (not just in `COMB-318`'s
  `support_boundary` field) so future corpus-validation-dependent tickets discover it independently.
- `staging_artifacts/TCK-20260831-READINESS-SPEED-FORMULA/corpus_validation.py` — new, throwaway
  hand-orchestrated corpus validation script (Step 6)
- `staging_artifacts/TCK-20260831-READINESS-SPEED-FORMULA/investigation.md` — created this run
  (pre-implementation artifact)
- `staging_artifacts/TCK-20260831-READINESS-SPEED-FORMULA/plan.md` — created this run
  (pre-implementation artifact); Deviations section added during implementation
- `staging_artifacts/TCK-20260831-READINESS-SPEED-FORMULA/test_plan.md` — created this run
  (pre-implementation artifact)
- `tickets/inprogress/TCK-20260831-READINESS-SPEED-FORMULA.md` — this ticket, created this run

## Completion Summary

Added a real, agility-derived `readiness_speed` formula (`max(1.0, 10.0 + (agility - 5) * 1.0)`)
to `LevelingService.recalculate_combat_stats()`, replacing the previously-flat `10.0` default,
and fixed a 4th recurrence of the PH8 `replace(new_com, ...)` silent-drop bug in `ApplyPath` so the
derived value actually survives into the live `CombatComponent`. Backward compatibility is exact
(reference agility 5 still yields 10.0), covered by 3 new unit/regression tests, and both docs
(`02_combat_laws.md` §7, `attribute_progression_contract.md`) plus a new parity ledger entry
(`COMB-318`) were updated in the same session. A full hand-orchestrated pre/post-code corpus
validation was run per the ticket's Scope requirement; it surfaced a genuine, well-diagnosed
finding — real combat activity structurally ceases before tick 1000 in every tested corpus world,
so the formula's one real population-level effect (elder agility decay) is currently unobservable
via corpus combat metrics in any tested world — which is recorded honestly in `COMB-318` rather
than papered over with a stronger claim than the evidence supports.

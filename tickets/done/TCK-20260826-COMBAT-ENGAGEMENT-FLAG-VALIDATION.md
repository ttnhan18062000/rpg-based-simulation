---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION
phase: done
date: 2026-08-26
tags: [feature-flags]
---

# TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION

## Title
Produce real validation evidence for `ENABLE_COMBAT_ENGAGEMENT` before deciding its default

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Named follow-up from `TCK-20260824-ROLLOUT-FLAG-DECISIONS`: `ENABLE_COMBAT_ENGAGEMENT` was kept
`OFF` by default because it has a real fix history (`TCK-20260809-COMBAT-ENGAGEMENT-FLAG-
SUPPRESSES-PUSH-SHAPER-EVENTS`, a genuine bug found and fixed via one-off live corpus A/B testing)
but no standing production validation -- no SimQ corpus profile turns it on today. This ticket's
job is to produce that evidence (a real corpus-profile trial, or documented reasons it should stay
deferred), not to flip the flag itself.

## Scope
- Run `src/domains/combat_engagement/phase.py`'s real behavior against at least one SimQ corpus
  world with the flag explicitly `ON`, comparing against the same world with it `OFF`.
- Confirm the `TCK-20260809-...` fix (the `u.merge(...)` pattern in `src/engine/pipeline.py`) still
  holds under this trial -- combat push-shaper events must not be suppressed.
- Produce a real keep/flip recommendation with evidence, mirroring
  `TCK-20260824-ROLLOUT-FLAG-DECISIONS`'s own decision-artifact format.

## Out of Scope
- Actually flipping the flag's default -- that's this ticket's own eventual recommendation feeding
  back into a decision, not something to do unilaterally here.
- Any new gameplay content for the combat-engagement system itself.

## Acceptance Criteria
- [x] A real corpus-profile ON/OFF comparison is run and documented
- [x] A keep/flip recommendation with evidence is produced
- [x] If flip is recommended, a concrete next-step ticket is named (not flipped here) — vacuously satisfied: the real evidence did not support a flip, so nothing is named.

## Related Tickets
- TCK-20260824-ROLLOUT-FLAG-DECISIONS (source of this deferral)
- TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS (the real fix this validation
  must confirm still holds)

## Related Docs
- docs/guidelines/intentional_divergences.md (DEV-002, DEV-003)

## Related Stored Artifacts
- staging_artifacts/TCK-20260824-ROLLOUT-FLAG-DECISIONS/investigation.md (the evidence gathered so
  far)

## Related Code Areas
- src/domains/combat_engagement/phase.py
- src/engine/pipeline.py
- src/domains/optimization/feature_flags.py

## Assumptions / Open Questions
- Which corpus world(s) are the right trial subject -- not decided here.

## Implementation Notes
Ran the real 4-leg corpus trial `plan.md` specifies via `tools/calibrate_simq.py`, seed 42, 2000
ticks each, OFF then ON, for `dungeon_crawl` (32-entity `monster_only_gauntlet`, the same
world/seed TCK-20260809 used) and `wilderness_survival` (11-entity, same archetype, `--profile
default` since it has no dedicated scoring profile). Environment note: the worktree's bare
`python3` lacks `pydantic`; all 4 runs used
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` (the main checkout's venv)
instead, cwd unchanged, so output still landed at `data/calibration/` and `data/runs/` as the plan
specifies.

Confirmed via each run's own tick-0 `fingerprint.entity_count` (32 for `dungeon_crawl`, 11 for
`wilderness_survival`, matching `corpus_registry.yaml`) that both worlds loaded their real
compiled `world.resolved.yaml` spec, not the generic hero+goblins fallback — resolving Step 2's
open question. Full raw tally (all 5 signals x 4 legs, plus the `run_combat_engagement`/
`skip_combat_engagement` metric-counter sums and per-leg `quality_report.json` COMBAT pillar
counts) is in `staging_artifacts/TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION/trial_evidence.md`
and mirrored into `docs/architecture/rollout_flag_decisions_m1.md`'s new
"ENABLE_COMBAT_ENGAGEMENT — Validation Trial Result (TCK-20260826)" section.

**No-suppression check passes in both worlds**: `combat_engagement_ended` fired identically
(10 == 10) on ON vs OFF in both `dungeon_crawl` and `wilderness_survival`, and
`run_combat_engagement`/`skip_combat_engagement` confirm `CombatEngagementPhase` ran on ~100% of
eligible ticks when ON (0% skip rate in both ON legs, vs. 100% skip when OFF, as expected). This
is the opposite of TCK-20260809's own documented pre-fix signature (a full collapse to zero across
all 5 event types on the ON leg) — the `u.merge(...)` fix in `src/engine/pipeline.py:276` still
holds.

**Honest gap, disclosed rather than smoothed over**: `combat_resolved`/`combat_damage`/
`entity_killed` were 0 in all 4 legs, including both OFF baselines — thinner than TCK-20260809's
own OFF baseline on the same world/seed (`damage=1`/`resolved=1`/`killed=1`). Per this ticket's own
plan Anti-Drift Notes, a near-zero OFF baseline is a real finding about the trial world/seed at
this tick count, not proof the flag is safe under lethal combat load — disclosed as such rather
than treated as a clean pass.

No deviation from `plan.md`'s steps other than the interpreter substitution above (recorded in
`plan.md`'s own Deviations section) and creating one additional evidence file
(`trial_evidence.md`, `artifact_type: report`) the plan flagged as optional/useful.

## Test Summary
All three scoped pytest commands from `test_plan.md`'s "Scoped Pytest Commands" section were run
and passed, with zero source changes made:
- `tests/unit/domains/combat_engagement/ tests/integration/domains/combat_engagement/
  tests/integration/scenarios/test_phase4_combat_engagement_scenarios.py
  tests/perf/test_phase4_combat_engagement_budget.py -m "not slow"` → **37 passed, 1 deselected**
- `tests/unit/config/test_phase10_feature_flags.py
  tests/integration/test_scenario_feature_flag_defaults.py
  tests/certification/test_phase10_enhanced_determinism_parity.py` → **57 passed**
- `tests/integration/scenarios/test_balance_regression.py -k adventure_routing_defaults_off` →
  **1 passed, 3 deselected**

`test_combat_engagement_phase_merge.py` (the TCK-20260809 regression guard) and all three
`_DELIBERATE_ON_DEFAULT_FLAGS` allowlist copies passed unmodified, confirming
`ENABLE_COMBAT_ENGAGEMENT` correctly stays absent from the ON-default allowlist.

## Files Changed
- `docs/architecture/rollout_flag_decisions_m1.md` (updated `ENABLE_COMBAT_ENGAGEMENT` table row
  + new "ENABLE_COMBAT_ENGAGEMENT — Validation Trial Result (TCK-20260826)" section)
- `staging_artifacts/TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION/trial_evidence.md` (new —
  raw 4-leg evidence tally)
- `staging_artifacts/TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION/plan.md` (Deviations section
  added)
- `tickets/inprogress/TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION.md` (this file — Status,
  Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary)

No `src/` file was touched, per this ticket's hard scope guard.

## Completion Summary
Ran a real 2-world (`dungeon_crawl`, `wilderness_survival`), 4-leg (OFF/ON each), 2000-tick, seed
42 corpus trial for `ENABLE_COMBAT_ENGAGEMENT` via `tools/calibrate_simq.py`. The TCK-20260809
`u.merge(...)` fix holds — no suppression regression in either world (`combat_engagement_ended`
matched exactly between ON/OFF, and the phase ran on ~100% of eligible ticks when ON). However,
`combat_damage`/`combat_resolved`/`entity_killed` stayed at zero in every leg including both OFF
baselines, a thinner real-combat-activity signal than TCK-20260809's own baseline — disclosed
honestly rather than treated as sufficient. Recommendation: **Keep OFF, deferred** — real trial
evidence confirming no regression is now on file, but `ENABLE_COMBAT_ENGAGEMENT` still has zero
shipped SimQ corpus profiles using it in production, which is DEV-003's actual bar for a flip. No
flip is recommended, so no next-step ticket is named. No new
`docs/guidelines/intentional_divergences.md` entry was added since the flag's behavior versus the
Mechanics Bible is unchanged.

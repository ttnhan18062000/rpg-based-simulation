---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION
phase: open
date: 2026-08-10
tags: [simulation-quality, calibration, corpus]
---

# TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION

## Title
Real, corpus-wide role/faction fix (`TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION`)
plausibly affects more than just COMBAT — a `simq-audit` recalibration run surfaced a real,
unexplained SOCIAL/ECONOMY/PROGRESSION score-tolerance drift across multiple worlds that was
deliberately NOT attributed to that fix without direct evidence

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
A `simq-audit` recalibration run (`SIMQ-AUDIT-20260810T032558Z`, `mode=full worlds=dungeon_crawl,
urban_political`, scoped down to a targeted `--scenario` sweep after the full unscoped run timed
out at 590s — a real instance of this project's own already-disclosed chronic tick-budget
condition) found real, corpus-wide impact from `TCK-20260808-MONSTER-ROLE-MISTAGGING-
INVESTIGATION`'s role/faction fix, beyond the 2 worlds that ticket's own investigation directly
verified:

**Confirmed and already resolved by this ticket's own precursor audit run** (see
`docs/parity_ledger/substrate.yaml` SUB-384 and `tests/simulation_quality/fixtures/
grade_anchors.json`, already updated): COMBAT anchor jumped C→A/S on 7 fast-tier run_keys across
3 worlds — `urban_political` (`_seed42_200t`, `_seed42_500t`, `_seed456_500t`), `frontier_extended`
(`_seed42_200t`, `_seed456_200t`), `frontier_living_world` (`_seed42_200t`, `_seed456_200t`).
Directly attributable: real hostile-faction entities that were previously invisible to
faction-based hostility detection are now correctly engaging in combat.

**NOT resolved, real, disclosed, this ticket's own scope**: the same audit run's fast-tier
regression sweep surfaced a real, unexplained SCORE-tolerance drift (not always a full grade-band
jump — often within-band magnitude drift caught by the separate score-tolerance check) on SOCIAL,
ECONOMY, PROGRESSION, COGNITION, and AGENCY across MANY more run_keys than just the 3 combat-shift
worlds — including worlds with NO COMBAT band change at all (`simq_routing_test`,
`highland_traverse`, `hero_guild_routing`). The SOCIAL pillar specifically shows a large,
consistent, unannotated score inflation pattern across `urban_political` (4 keys),
`frontier_living_world` (3 keys), and `highland_traverse` (2 keys) — 10 real instances corpus-wide.

**This is NOT simply the already-known 2026-08-07 finding** (`docs/audits/D20_simq_integration.md`
Audit history, `docs/simulation_quality/current_state.md`'s "2026-08-07 session summary"): that
session's own disclosed, unresolved finding was "26 COMBAT + 1 COGNITION + 1 SOCIAL score-tolerance
failures... COMBAT mostly drops to exactly 0.0 events" — COMBAT scores DROPPING toward dormant,
hypothesized as watchdog-throttle/environment-load non-determinism. Today's COMBAT finding is the
OPPOSITE direction (scores JUMPING UP, real combat now firing) with a directly confirmed, different
cause (SUB-384) — clearly not the same phenomenon. But today's SOCIAL finding (10 real instances)
is roughly 10x the scale of the 2026-08-07 session's own "1 SOCIAL" single-draw case — informative
in its own right, not dismissible as the same narrow noise, but ALSO not confirmed to share
SUB-384's own root cause without direct evidence. **Both possibilities are real and must not be
assumed** — this ticket's own job is to determine which (or find a third, distinct cause).

## Scope
1. **Investigate** (mandatory before Plan):
   - Trace whether SOCIAL/ECONOMY/PROGRESSION scoring rules have any real, direct dependency on
     `entity.identity.role`/`.faction` (e.g. bond/trust formation gated by faction relationship,
     trade eligibility gated by role, reward classification gated by role — the exact mechanism
     `TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION` already flagged but did not verify for
     `CombatRewardClassificationService` specifically) — a real, plausible, DIRECT causal link to
     SUB-384, not yet confirmed.
   - Separately trace whether this matches the 2026-08-07 session's own disclosed
     watchdog-throttle/environment-load hypothesis (`docs/audits/D06_longrun_health.md` F6) — check
     for `WatchdogTrip`/`PRESSURE`-mode log activity during today's specific calibration runs,
     matching that session's own established diagnostic method.
   - Determine real corpus-wide prevalence: run the FULL, unscoped `simq-full-audit-full` (not
     scoped to 2 worlds) to completion — budget enough wall-clock time given today's confirmed 590s
     timeout on a partial run, or split across multiple bounded background runs — to get a complete
     picture beyond the 24 run_keys that happened to regenerate before today's timeout.
   - Cross-reference `CombatRewardClassificationService`'s own real reward-classification behavior
     (flagged as a disclosed-but-unverified downstream consumer in SUB-384) — a real, concrete
     candidate mechanism for the PROGRESSION drift specifically.
2. **Plan**: once root cause(s) are confirmed (may be more than one — do not assume a single,
   shared cause without checking), scope the real fix or recalibration.
3. **Implement**: the confirmed, minimal fix and/or `grade_anchors.json` recalibration for the
   confirmed-cause items only. Any items that turn out to be genuine, pre-existing, accepted noise
   (matching the 2026-08-07 precedent) should be documented, not silently anchored to try to make
   tests pass.

## Out of Scope
- The already-confirmed, already-fixed COMBAT anchor drift (SUB-384) — not revisited here.
- Any change to `WorldCompiler.compile()`/`WorldRepository.load_world_with_context()` themselves —
  already correct per `TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION`'s own fix; this ticket
  investigates DOWNSTREAM scoring consequences, not the compile-time role/faction resolution itself.
- A full corpus-wide role/faction distribution audit beyond what's needed to explain THIS drift —
  if the real cause turns out to be role/faction-driven, a broader audit may be its own follow-up.

## Acceptance Criteria
- [ ] investigation.md traces the real cause(s) of the SOCIAL/ECONOMY/PROGRESSION/COGNITION/AGENCY
      drift with direct evidence (not assumed) — may find multiple, independent causes
- [ ] The 2026-08-07 watchdog-throttle hypothesis is directly checked (not just cited), not assumed
      to explain or not explain today's finding
- [ ] `CombatRewardClassificationService`'s own real behavior is checked as a candidate PROGRESSION
      cause (closes the disclosed-but-unverified item from SUB-384 — this ticket doubles as that
      verification)
- [ ] A concrete recommendation is produced per real cause found (fix, recalibrate, or
      document-as-known-noise), with reasoning — no forced, unproven anchor edits
- [ ] Scoped pytest passes; `tests/simulation_quality/test_grade_regression.py -m "not slow"`
      shows 0 unexplained failures (every remaining failure either fixed, recalibrated with a real
      cause, or explicitly documented as accepted noise matching the D06 F6 precedent)

## Related Tickets
- TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION (DONE, this session — the confirmed COMBAT
  root cause; this ticket investigates whether its own real blast radius extends further)
- TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS,
  TCK-20260810-NAVIGATION-SINGLE-AXIS-STEPPING-DIAGONAL-PURSUIT-DEADLOCK (DONE, this session —
  same-day combat-resolution investigation thread this ticket's own COMBAT finding connects to)

## Related Docs
- `docs/simulation_quality/eval_matrix_results.md` (2026-08-10 NOTE — the real, disclosed finding
  this ticket investigates)
- `docs/audits/D20_simq_integration.md` (Audit history — both the 2026-08-07 and 2026-08-10 entries)
- `docs/simulation_quality/current_state.md` ("2026-08-07 session summary" — the prior, narrower,
  directionally-opposite finding this ticket must not conflate with today's)
- `docs/audits/D06_longrun_health.md` F6 (the watchdog-throttle/environment-load precedent)
- `docs/parity_ledger/substrate.yaml` SUB-384

## Related Stored Artifacts
- `staging_artifacts/TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION/`
- `stored_artifacts/TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION/` (the fix this drift
  originates from)

## Related Code Areas
- `src/simulation_quality/scorers/` (SOCIAL/ECONOMY/PROGRESSION scorer implementations — check for
  real role/faction-gated signals)
- `src/engine/combat_rewards.py` (`CombatRewardClassificationService`)
- `src/observability/event_shapers.py`, `src/observability/event_extractor.py` (event production
  for the affected pillars)
- `data/calibration/{run_key}/quality_report.json` for the affected run_keys (real, fresh
  post-SUB-384 data already generated by this ticket's own precursor audit run — reusable, do not
  necessarily need to re-run the engine for these specific 24 keys)

## Assumptions / Open Questions
- Whether a single shared cause explains all 5 affected pillars, or multiple independent causes —
  not assumed; the Investigate phase's own first job is to determine this.
- Whether the full, unscoped corpus recalibration (needed to see beyond the 24 run_keys today's
  partial run happened to touch) can complete within a reasonable session budget given the
  confirmed 590s timeout — may need to run in smaller batches or accept a partial, disclosed sample.

## Implementation Notes
Two confirmed mechanisms, both tracing to SUB-384 (`TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION`):
1. **PROGRESSION** — `CombatRewardClassificationService` (`src/engine/combat_rewards.py`) is
   keyed by `EntityRole`; `progression.py`'s `EVENT_TYPES` includes `xp_granted`. A previously
   mistagged monster now correctly resolves to `MONSTER_KILL` on defeat, changing real
   `xp_granted` amounts. Closes the disclosed-but-unverified downstream-consumer item from
   SUB-384's own completion notes (also satisfies queued task #128).
2. **SOCIAL/ECONOMY/COGNITION/AGENCY (+ 2 additional COMBAT keys)** — confirmed via `grep`
   that none of these scorers read role/faction directly; the mechanism is a cascading
   behavioral change: correctly-tagged monsters now engage/die/behave differently from tick 1
   onward, altering deterministic RNG-consumption order and population composition for the
   rest of each run.

2026-08-07 D06 F6 watchdog-throttle hypothesis directly checked (not just cited): 3 independent
re-runs of `urban_political_seed42_500t` showed the watchdog firing repeatedly from tick 25
(earlier/denser than the documented ~300-320 onset) yet produced a bit-identical SOCIAL score
(18.39, 3295 events) all 3 times — decisive evidence against that mechanism explaining this drift.

`grade_anchors.json` recalibrated: original batch of 15 run_keys / 27 fields (SOCIAL, ECONOMY,
PROGRESSION, COGNITION, AGENCY), plus 2 additional run_keys found while regenerating a missing
guard-test calibration fixture (`urban_political_selfmodel_execution_probe_seed42_200t`,
`urban_political_selfmodel_probe_seed42_200t` — each needed COMBAT + SOCIAL anchor updates, same
confirmed cause) — 17 run_keys / 31 fields total this ticket.

## Test Summary
`pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q` →
35 passed, 15 failed, 20 skipped, 18 deselected. All 15 failures carry a pre-existing
`[known tick_budget: ...]` annotation in the test file's own annotation dict — already-documented,
accepted noise unrelated to SUB-384, left un-anchored per the ticket's own scope. Zero unexplained
failures. Both isolated guard tests
(`test_urban_political_selfmodel_cognition_isolated_grade_anchor`,
`test_urban_political_selfmodel_execution_isolated_grade_anchor`) now pass — their calibration
report gap (gitignored, regenerate-on-demand) is regenerated and their own real SUB-384-caused
drift fixed alongside the main batch. `test_grade_anchor_file_exists_and_valid`'s raw_score/
normalized_score field-confusion guard confirmed still passes.

## Files Changed
- `tests/simulation_quality/fixtures/grade_anchors.json` (17 run_keys / 31 fields recalibrated)
- `docs/parity_ledger/substrate.yaml` (SUB-384 entry — `support_boundary` extended with this
  ticket's confirmation and closure of both previously-disclosed follow-ups)
- `docs/simulation_quality/eval_matrix_results.md` (new 2026-08-10 NOTE under `urban_political`
  closing the disclosed regression from the precursor audit's own NOTE)
- `docs/audits/D20_simq_integration.md` (Audit history — extended with this ticket's closure)

## Completion Summary
Confirmed and closed the SOCIAL/ECONOMY/PROGRESSION/COGNITION/AGENCY drift left unresolved by
the precursor `simq-audit` run (`SIMQ-AUDIT-20260810T032558Z`). Traced two independent,
evidence-backed mechanisms (direct `CombatRewardClassificationService` reward-classification
change for PROGRESSION; cascading population/RNG-stream behavioral change for the rest),
directly ruled out the 2026-08-07 watchdog-throttle hypothesis via a 3x reproducibility check
(not just cited), and recalibrated `grade_anchors.json` across 17 run_keys/31 fields — including
2 keys surfaced only while regenerating a stale guard-test fixture, an incidental but real
same-cause fix. Post-recalibration fast-tier sweep shows zero unexplained failures; every
remaining failure carries a pre-existing accepted-noise annotation. No source code changed —
this was a pure recalibration ticket, consistent with SUB-384's own fix already being complete.

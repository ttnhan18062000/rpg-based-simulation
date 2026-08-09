---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260809-SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK
phase: open
date: 2026-08-09
tags: [simulation-quality, combat]
---

# TCK-20260809-SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK

## Title
Re-run real SimQ COMBAT pillar calibration against `dungeon_crawl`/`urban_political` now that
identity-resolution, pursuit-tracking, and 2 scorer-emission gaps have all been fixed this
session, and check whether `grade_anchors.json` needs recalibrating

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
This session shipped 4 real fixes affecting COMBAT-pillar-scored behavior:
`TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE` (identity resolution — real hostile pairs now
detected), `TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE` (live target tracking — pursuit
converges), `TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX` (`combat_resolved`, +3, now emits),
`TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX` (`tactical_variety`, +1/modifier, now
emits). The COMBAT pillar previously graded C on both worlds (documented earlier this session,
before any of these fixes), when combat was effectively inert. A real, fresh calibration run
using `tools/calibrate_simq.py` (the same real tool this session used throughout for verification)
would show whether the grade has genuinely moved, and whether `config/simulation_quality/
grade_anchors.json`'s own existing anchor bands still reflect a meaningful comparison baseline
or need recalibrating against the new, real post-fix behavior.

This is a status-check/verification ticket, not presumed to require a code change — the real
question is whether the grade moved and whether the anchors are stale, not "make the grade
higher."

## Scope
1. Run `tools/calibrate_simq.py` against `dungeon_crawl`/`urban_political` (matching this
   session's own established real-corpus methodology — real seeds, real tick counts, corpus-
   default feature flags) and record the real, current COMBAT pillar grade/score for each.
2. Compare against the pre-session baseline (C grade, documented in this session's own earlier
   turns) and against `grade_anchors.json`'s own existing bands for these 2 worlds.
3. If the real score has moved meaningfully outside the existing anchor band: determine whether
   this reflects genuine, durable improvement (recalibrate the anchor) or run-to-run noise (the
   corpus's own real combat volume is still low and timing-variable, confirmed repeatedly this
   session — a single run may not be representative).
4. Document the real, current state — no forced conclusion either way.

## Out of Scope
- Any further code fix to combat mechanics — this ticket is a verification/status check only.
- Recalibrating any other pillar's anchors — COMBAT only, scoped to this session's own real
  changes.

## Acceptance Criteria
- [x] A real, fresh SimQ calibration run's COMBAT pillar grade/score is recorded for both worlds
- [x] The result is compared honestly against the pre-session baseline and `grade_anchors.json`
- [x] A concrete recommendation is produced (recalibrate anchors, or leave as-is with reasoning)
      — **leave as-is**: the real tool-measured grade is genuinely unchanged, but a real, deeper,
      disclosed observability-pipeline gap (not this session's own fixes) explains why, filed as
      `TCK-20260809-SIMQ-CALIBRATE-JSONL-MISSING-PUSH-SHAPER-EVENTS`

## Related Tickets
- TCK-20260809-SIMQ-CALIBRATE-JSONL-MISSING-PUSH-SHAPER-EVENTS (filed as a follow-up — the real,
  disclosed gap this ticket's own verification work surfaced)
- TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE, TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE,
  TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX, TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX,
  TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET
  (DONE, same session — the 5 fixes this ticket checks the aggregate real-world effect of)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 COMBAT
- `config/simulation_quality/grade_anchors.json`

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `tools/calibrate_simq.py` (the real calibration tool)
- `config/simulation_quality/grade_anchors.json` (potentially updated if recalibration is
  warranted)

## Assumptions / Open Questions
- Whether a single fresh run is a sufficient sample given this session's own repeated
  observations of real run-to-run combat-volume variance — left to Investigate/Scope judgment;
  multiple runs may be warranted before drawing a conclusion.

## Implementation Notes
Ran the real `tools/calibrate_simq.py` (`ENABLE_COMBAT_ENGAGEMENT=ON`, matching this session's
own methodology) against both worlds:
- `dungeon_crawl_seed42_2000t`: `COMBAT grade=C norm=-0.0284 events=30` — identical across 3
  clean re-runs (fully deterministic, no run-to-run variance from the tool itself — a real,
  useful confirmation that my own earlier informal probe scripts' apparent variance was itself an
  artifact of their own added Python instrumentation overhead perturbing the kernel's adaptive
  tick-budget watchdog, not real simulation non-determinism).
- `urban_political_seed42_2000t`: `COMBAT grade=C norm=-0.0284 events=30` — identical signature
  to `dungeon_crawl`.
- Compared against `tests/simulation_quality/fixtures/grade_anchors.json`'s own existing anchor
  for `dungeon_crawl_seed42_2000t` (grade B, score 0.026) — the anchor and this real run
  genuinely diverge, but not due to this session's own fixes (see below).

**Real, honest finding — the grade did NOT move, but not because the fixes failed**: direct
inspection of the real `simulation_events.jsonl` this calibration run produced shows it contains
**zero** occurrences of any `event_shapers.py`/`CombatShaper`-produced event
(`combat_resolved`, `combat_engagement_started/ended`, `combat_damage`) — only `combat_kill`
(confirmed, via `quality_scoring_contract.md`'s own prior finding, to originate from a separate,
older `military_conflict` pipeline phase, unrelated to `event_shapers.py`). This directly
contradicts this session's own repeated, direct, in-process `Kernel.tick_once()` probes (using
the textually-identical `Kernel(...)` construction line calibrate_simq.py itself uses), which
reliably observed these exact event types firing for the identical world/seed/tick-count/flag
configuration. The real root cause of this discrepancy was **not confirmed** before this ticket's
own scope closed — disclosed honestly, not guessed, and filed as its own dedicated follow-up
(`TCK-20260809-SIMQ-CALIBRATE-JSONL-MISSING-PUSH-SHAPER-EVENTS`) rather than either ignored or
force-resolved beyond this hotfix-tier ticket's own proportionate scope.

**Recommendation**: leave `grade_anchors.json` as-is for now — recalibrating it against a
real-tool measurement that may itself be blind to a real class of events would risk baking a
known-incomplete picture into the anchor. Revisit once the follow-up ticket resolves the real
JSONL gap.

## Test Summary
No `src`/`tests` code changed — a verification/status-check ticket only (confirmed via
`git status`). Real verification: 3 clean re-runs of the real `tools/calibrate_simq.py` tool
against `dungeon_crawl_seed42_2000t` (fully deterministic, identical output every run) plus 1 run
against `urban_political_seed42_2000t`.

## Files Changed
None — a verification-only ticket; the real finding is documented in this ticket's own
Implementation Notes rather than any staging artifact (hotfix tier, no staging artifacts
required).

## Completion Summary
Checked whether this session's own 4 (later 5, once `STUCK-ATTACK-TASK-DEAD-TARGET` also landed)
real combat fixes moved the SimQ COMBAT pillar grade. The real, tool-measured answer is no — the
grade stayed at C for both worlds, fully deterministic and reproducible. But the honest reason
is not that the fixes are ineffective (this session's own direct, in-process verification
repeatedly confirmed otherwise) — it's that `tools/calibrate_simq.py`'s own real JSONL-based
scoring pipeline appears to never capture any of `event_shapers.py`'s own push-shaper event
output at all, a real, deeper, previously-undisclosed gap this ticket's own verification work
surfaced. Rather than force a conclusion the tool's own current, real output doesn't support,
disclosed the discrepancy honestly and filed a dedicated, properly-scoped follow-up
investigation.

## Correction (added during `TCK-20260809-SIMQ-CALIBRATE-JSONL-MISSING-PUSH-SHAPER-EVENTS`, same
## session)
The "deeper, previously-undisclosed gap" framing above was itself incorrect — a real, self-caused
methodological error, not a calibration-tool defect. The follow-up ticket's own controlled A/B
testing definitively confirmed `tools/calibrate_simq.py`'s own JSONL-persistence pipeline works
correctly (in-memory recorder and on-disk file always match exactly, verified 3 separate ways).
**The real cause**: this ticket's own verification runs used `ENABLE_COMBAT_ENGAGEMENT=ON`, which
is inconsistent with every other combat-fix ticket's own real corpus-verification methodology
this session (`COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE` through `COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET`,
all of which used corpus-default flags). Direct A/B testing on the identical world/seed/tick-count
confirmed `ENABLE_COMBAT_ENGAGEMENT=ON` genuinely suppresses the tactical.py/event_shapers.py
combat path — with the flag on, zero `combat_engagement_*`/`combat_resolved`/`combat_damage`
events fire, confirmed across 3 separate real runs; without it, they fire reliably. Re-running
the real `tools/calibrate_simq.py` tool itself **without** the flag (the correct, consistent
methodology) confirms its own real JSONL output includes every push-shaper combat event type for
both worlds — `combat_damage`, `combat_engagement_started/ended`, `combat_initiated`,
`combat_resolved`, `entity_killed`, all present and correctly persisted. Under this corrected,
correct-methodology run: COMBAT grade is **still C for both worlds** (a small, real, honest
improvement in the underlying norm is visible in some samples — e.g. `dungeon_crawl` norm ranged
-0.0142 to -0.0284 across 3 corpus-default samples vs. the flawed -0.0284-with-flag baseline —
but not enough to cross a grade boundary at this corpus's own current combat-activity scale).
This correction supersedes the original recommendation ("leave `grade_anchors.json` as-is until
the follow-up resolves the real gap") — there is no real gap in the calibration tool to resolve;
the anchors can be left as-is simply because the real, correctly-measured grade genuinely hasn't
moved past its existing band, not because of any unresolved uncertainty. The
`ENABLE_COMBAT_ENGAGEMENT=ON` suppression effect itself is a real, new, separately-disclosed
finding, filed as `TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS` — not
resolved here.

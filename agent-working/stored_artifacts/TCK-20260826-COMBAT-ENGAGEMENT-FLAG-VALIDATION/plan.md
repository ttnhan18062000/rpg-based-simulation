---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION
artifact_type: plan
tags: [feature-flags, combat]
---

# Implementation Plan — TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION

## Summary
This ticket produces evidence, not code. The plan runs the two corpus trials investigation.md
already scoped (`dungeon_crawl` primary, `wilderness_survival` secondary, both seed 42 / 2000
ticks, each with an ON and OFF leg), captures the five evidence signals investigation.md's Corpus
Trial Plan specifies (raw JSONL event counts, `metric_counters["run_combat_engagement"]` /
`["skip_combat_engagement"]`, `quality_report.json` COMBAT pillar counts, absolute OFF-baseline
volume, and the phase skip-rate), then writes the real result into a new row/section in
`docs/architecture/rollout_flag_decisions_m1.md` (the doc TCK-20260824 already named as the target)
and into this ticket's own Implementation Notes / Completion Summary. No file under `src/` is
touched. The keep/flip judgment call flagged in investigation.md's Risks section is resolved here
using DEV-003's own standard (standing production profile usage, not a one-off trial) — since
`ENABLE_COMBAT_ENGAGEMENT` has zero shipped profiles turning it on today (confirmed:
`src/domains/optimization/feature_flags.py:31`, `"ENABLE_COMBAT_ENGAGEMENT": FeatureMode.OFF`, and
no corpus profile YAML sets it), a clean trial cannot by itself meet that bar — so unless the trial
data surfaces something that changes this reasoning, the expected recommendation is "Keep OFF, but
now with real trial evidence on file," not a flip. Step 3 below states this as the working
conclusion the real data must confirm or overturn, not a foregone one.

## Steps

### Step 1 — Run the `dungeon_crawl` primary trial (OFF then ON)
**Files:** None changed. Writes only to `data/calibration/` (temporary, cleaned at Finalize) and
`data/runs/{run_id}/` (temporary, cleaned at Finalize per Definition of Done — do not clean
mid-ticket, later steps read these outputs).
**Change:** Run exactly the two commands investigation.md's Corpus Trial Plan specifies
(`staging_artifacts/TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION/investigation.md` lines 277-284),
verified against `tools/calibrate_simq.py:470-500`'s real argparse definitions (`--ticks`, `--seed`,
`--name`, `--output` all exist as read) and `tools/calibrate_simq.py:243-283`'s `_KNOWN_FLAGS`
allow-list / env-var-to-`state.feature_flags` plumbing (confirms `ENABLE_COMBAT_ENGAGEMENT=ON` as a
prefix is a real, already-supported override path, not something this step invents):
```
# OFF (baseline)
python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_combat_engagement_OFF

# ON
ENABLE_COMBAT_ENGAGEMENT=ON python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_combat_engagement_ON
```
Record the `run_id` each invocation prints/creates under `data/runs/` — Step 3 needs it to locate
`simulation_events.jsonl` and `quality_report.json`.
**Do NOT touch:** `src/domains/combat_engagement/phase.py`, `src/engine/pipeline.py`,
`src/domains/optimization/feature_flags.py` — this step only runs existing tooling with an env-var
override, per this ticket's Out of Scope.
**Verify:** Both commands exit 0 and produce a `data/runs/{run_id}/simulation_events.jsonl` and a
`quality_report.json` for each leg (4 files total: OFF/ON x events/report). This is the raw input
Step 3 analyzes — there is no separate pytest assertion for this step, consistent with test_plan.md
("New Tests Required: None... the trial itself is not a pytest artifact").

### Step 2 — Run the `wilderness_survival` secondary trial (OFF then ON)
**Files:** Same as Step 1 (temporary `data/calibration/` and `data/runs/` output only).
**Change:** Run the two commands investigation.md specifies (lines 294-300), using `--profile
default` since `wilderness_survival` has no dedicated SimQ scoring profile (investigation.md line
286-287):
```
# OFF (baseline)
python3 tools/calibrate_simq.py --name wilderness_survival --seed 42 --ticks 2000 --profile default \
  --output data/calibration/wilderness_survival_seed42_2000t_combat_engagement_OFF

# ON
ENABLE_COMBAT_ENGAGEMENT=ON python3 tools/calibrate_simq.py --name wilderness_survival --seed 42 --ticks 2000 --profile default \
  --output data/calibration/wilderness_survival_seed42_2000t_combat_engagement_ON
```
Before treating results as valid, confirm which code path `_load_world_state()` actually took for
`wilderness_survival` (a real compiled world spec vs. the generic hero+goblins fallback) and record
which one fired — investigation.md flags this as unconfirmed (lines 302-306) and explicitly assigns
Implement the job of resolving it by observation rather than assumption.
**Do NOT touch:** Same scope guard as Step 1.
**Verify:** Both commands exit 0 and produce the same 4-file set (events/report x OFF/ON) as Step 1.
Note in Step 3's writeup which world-loading path fired.

### Step 3 — Extract and cross-check the evidence signals from both trials
**Files:** None changed (analysis only, working notes can live in scratch/terminal output — the
durable record is written in Step 4).
**Change:** For each of the 4 run legs (dungeon_crawl OFF/ON, wilderness_survival OFF/ON), capture
all 5 signals investigation.md's "What evidence to capture" section specifies (lines 308-331):
1. Count each of `combat_engagement_started`, `combat_engagement_ended`, `combat_resolved`,
   `combat_damage`, `entity_killed` in `data/runs/{run_id}/simulation_events.jsonl` (e.g. `grep -c
   '"event_type": *"<type>"' data/runs/{run_id}/simulation_events.jsonl` per type).
2. Read `metric_counters["run_combat_engagement"]` / `["skip_combat_engagement"]` from the pipeline
   run's own metrics output (written by `run_phase()`, cited in investigation.md at
   `pipeline.py:114-115/131-132` — this plan does not re-derive that citation, it is investigation's
   verified finding, consumed here as evidence-extraction target, not re-asserted as this step's own
   new claim about `pipeline.py`'s internals).
3. Read the `COMBAT` pillar's `pillar_event_counts` from each leg's `quality_report.json`.
4. Confirm the OFF/baseline leg's absolute `combat_damage`/`entity_killed` counts are non-trivial
   (>0, ideally comparable in order of magnitude to TCK-20260809's own recorded
   `combat_engagement_ended=10` baseline on the same `dungeon_crawl_seed42` world) — this rules out
   the "0 vs 0 passes trivially" failure mode test_plan.md's Anti-Drift Test Guards flags.
5. Compute the phase skip-rate (`skip_combat_engagement / (run_combat_engagement +
   skip_combat_engagement)`) for the ON legs — a high skip-rate weakens how strong the "no
   suppression" evidence actually is, and must be disclosed either way, not silently dropped if
   unfavorable.
The pass/fail check for "no suppression" (the TCK-20260809 regression class) is: ON-leg counts for
all 5 event types must be non-zero and roughly consistent in magnitude with the OFF-leg counts (not
identical — `CombatEngagementPhase` legitimately changes posture-driven engagement behavior — but
not a collapse to near-zero, which was the pre-fix signature).
**Do NOT touch:** No source files. This step only reads generated JSONL/JSON artifacts.
**Verify:** A written tally (5 signals x 4 legs) exists and explicitly states, per world, whether
the no-suppression check passed. This tally is the direct evidence base for Step 4's recommendation
and Step 5's ticket update — both must cite these exact numbers, not a paraphrase.

### Step 4 — Write the real decision into `docs/architecture/rollout_flag_decisions_m1.md`
**Files:** `docs/architecture/rollout_flag_decisions_m1.md`
**Change:** This file's existing table row for `ENABLE_COMBAT_ENGAGEMENT` (read directly at lines
22-33 of the current file; the row is line 29: `| `ENABLE_COMBAT_ENGAGEMENT` | **Kept OFF,
deferred** | Real fix history (...) but no standing production validation. Follow-up:
`TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION`. |`) currently points at this ticket as an open
follow-up. Update that row's Verdict/Rationale cell in place to reflect the real outcome, and add a
new subsection below "## The 8 Flags Reviewed" (mirroring the structure of "## A Real Correction
Made During Implementation" — a named `##`-level section, not a nested table cell wall of text)
titled "## ENABLE_COMBAT_ENGAGEMENT — Validation Trial Result (TCK-20260826)" containing: the two
corpus worlds tested, the exact commands run (from Steps 1-2), the Step 3 evidence tally (all 5
signals, both worlds, both legs), and the recommendation.
Per DEV-003's own stated standard (this file's own "## The Precedent This Sets" section, lines
48-55: "Flip ON requires real, standing evidence the system already runs safely in production...
here, a live SimQ corpus profile already exercising it. A one-off validated fix... is necessary but
not sufficient on its own") and the fact confirmed directly at
`src/domains/optimization/feature_flags.py:31` (default is `FeatureMode.OFF`) plus a check of
`config/simulation_quality/profiles/*.yaml` for any profile setting
`ENABLE_COMBAT_ENGAGEMENT` (none found per investigation.md's own search), the expected
recommendation is **"Keep OFF, deferred — real trial evidence now on file, but still no standing
production profile usage; re-open only if a shipped profile begins using it."** This is the working
conclusion, not predetermined: if Step 3's tally shows a suppression regression (the TCK-20260809
class re-appearing) or any other anomaly, the recommendation must instead be "investigate as a new
bug" (per test_plan.md's Anti-Drift Test Guards and investigation.md's own Anti-Drift Hazards — a
new bug is out of this ticket's scope to fix, only to disclose and hand off).
Do not add a `DEV-00N` entry to `docs/guidelines/intentional_divergences.md` unless the
recommendation is "flip" — investigation.md's Docs Requiring Update section is explicit that a
"stay OFF" outcome requires no new divergence entry (the flag's behavior vs. the Mechanics Bible
does not change either way).
**Do NOT touch:** Any other row in the 8-flag table (`ENABLE_BELIEF_ASSIMILATION`,
`ENABLE_SOCIAL_COOPERATION`, etc.) — only the `ENABLE_COMBAT_ENGAGEMENT` row and the new
subsection. Do not touch "## RolloutProfileManager — Cut" or "## A Real Correction Made During
Implementation" — those are historical records of the prior ticket, not this one.
**Verify:** No automated test covers doc prose content; verification is a re-read confirming the
row and new section accurately reflect Step 3's real numbers (not placeholder/hypothetical
numbers), and that `python3 tools/validate_frontmatter.py docs/architecture/rollout_flag_decisions_m1.md`
(or the project's standard frontmatter validator, run the same way `done-checker`'s
`frontmatter_valid` condition does) still passes since the file's frontmatter block is untouched.

### Step 5 — Update this ticket's own Implementation Notes / Test Summary / Completion Summary
**Files:** `tickets/inprogress/TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION.md`
**Change:** Fill in `## Implementation Notes` with a condensed version of Step 3's tally and Step
4's recommendation (link to the doc section rather than duplicate the full tally). Fill in `## Test
Summary` with the scoped pytest command results from test_plan.md's "Scoped Pytest Commands"
section (all three command blocks must be run and reported — see Step 6). Fill in `## Files
Changed` listing only `docs/architecture/rollout_flag_decisions_m1.md` (plus this ticket file
itself and staging artifact moves at Finalize — no `src/` entries). Fill in `## Completion Summary`
stating the keep/flip outcome and, if flip was recommended, naming the concrete next-step ticket ID
(not creating it — per Out of Scope, naming only).
**Do NOT touch:** `## Scope`, `## Out of Scope`, `## Acceptance Criteria`, `## Related Tickets` —
those sections are already correct from ticket creation and are not implementation output.
**Verify:** Re-read confirms every acceptance criterion checkbox in `## Acceptance Criteria` can be
checked off against what Steps 1-4 actually produced (see Acceptance Criteria Map below).

### Step 6 — Run the scoped regression suite from test_plan.md
**Files:** None changed. Test execution only.
**Change:** Run all three scoped pytest commands from
`staging_artifacts/TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION/test_plan.md`'s "Scoped Pytest
Commands" section verbatim:
```
pytest tests/unit/domains/combat_engagement/ tests/integration/domains/combat_engagement/ \
  tests/integration/scenarios/test_phase4_combat_engagement_scenarios.py \
  tests/perf/test_phase4_combat_engagement_budget.py -m "not slow"

pytest tests/unit/config/test_phase10_feature_flags.py \
  tests/integration/test_scenario_feature_flag_defaults.py \
  tests/certification/test_phase10_enhanced_determinism_parity.py

pytest tests/integration/scenarios/test_balance_regression.py -k adventure_routing_defaults_off
```
This confirms `test_combat_engagement_phase_merge.py` (the TCK-20260809 regression guard) and the
`_DELIBERATE_ON_DEFAULT_FLAGS` allowlist tests still pass unmodified — both must reject
`ENABLE_COMBAT_ENGAGEMENT` as an ON-default flag, since Step 4 does not add it to that allowlist
under the expected "keep OFF" outcome. If the tally in Step 3 somehow drove Step 4 to a flip
recommendation, these tests are still expected to pass as-is (the flip is only *named*, not
implemented) — a failure here under either outcome is a real signal to stop, not route around, per
CLAUDE.md's Gate Integrity rule.
**Do NOT touch:** No test file is modified by this ticket. If any of these tests fail for a reason
unrelated to `ENABLE_COMBAT_ENGAGEMENT` (e.g. a concurrent session's work), that is a signal to
investigate separately, not something this ticket absorbs (test_plan.md's own Anti-Drift Test
Guards).
**Verify:** All three pytest invocations pass (or, for the third, the deselected/collected count
matches expectations for a `-k` filter with a `-m` marker elsewhere unset — report actual pass
count).

## Scope Guards
- Do not change `src/domains/optimization/feature_flags.py`'s `ENABLE_COMBAT_ENGAGEMENT` default
  (`FeatureMode.OFF` at line 31). This ticket's job is evidence, not the flip itself.
- Do not change `src/domains/combat_engagement/phase.py` or `src/engine/pipeline.py`'s
  `combat_engagement` registration (`pipeline.py:276`, the `u.merge(...)` fix) — confirmed present
  and correct by investigation.md; this ticket only re-validates it via corpus trial, never edits
  it.
- Do not add `ENABLE_COMBAT_ENGAGEMENT` to any `_DELIBERATE_ON_DEFAULT_FLAGS` allowlist copy
  (`tests/unit/config/test_phase10_feature_flags.py`,
  `tests/integration/test_scenario_feature_flag_defaults.py`,
  `tests/certification/test_phase10_enhanced_determinism_parity.py`) under any outcome of this
  ticket — that only happens in a future, separate flip ticket.
- Do not create or edit any `config/simulation_quality/profiles/*.yaml` file to turn the flag on —
  that would itself constitute "standing production evidence" fabricated by this ticket rather than
  found, which would corrupt the evidence this ticket exists to produce honestly.
- Do not add a new `docs/guidelines/intentional_divergences.md` entry unless Step 4's real evidence
  drives a flip recommendation (see Step 4's Change text) — do not add one speculatively either way.
- Do not fix any new bug the trial might surface (e.g. a genuine new suppression case distinct from
  TCK-20260809) inline — disclose it in Step 4's writeup and this ticket's Completion Summary as a
  new finding requiring a separate ticket, per Out of Scope.
- Do not modify `docs/audits/D19_domain_phase_inventory.md` §12 — investigation.md confirms the
  trial is expected to confirm, not revise, that entry's "posture assessment only" scope statement.
- Leave `data/runs/*` and `data/calibration/*` trial output in place until the ticket's normal
  Finalize cleanup step (`rm -rf data/runs/* reports/release_proof/*` per Definition of Done) — do
  not clean up mid-ticket, since Steps 3-4 need to read that output.

## Dependency Map
- Step 1 and Step 2 are independent of each other (different corpus worlds) and can run in either
  order or in parallel.
- Step 3 depends on both Step 1 and Step 2 completing (needs all 4 run legs' output).
- Step 4 depends on Step 3 (needs the real evidence tally to write into the doc).
- Step 5 depends on Step 4 (the ticket's Completion Summary references the doc section Step 4
  wrote).
- Step 6 is independent of Steps 1-5 (it exercises pre-existing tests, not this ticket's own
  output) but is listed last since it is the final gate before the ticket can be considered
  complete — it can technically run any time after ticket creation, including before Step 1, with no
  functional difference either way.

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| A real corpus-profile ON/OFF comparison is run and documented | Steps 1, 2, 3, 4 | No pytest — verified by re-reading the doc section Step 4 writes against Step 3's real tally (raw numbers must match, not be paraphrased/invented) |
| A keep/flip recommendation with evidence is produced | Step 4 | Same as above; recommendation must cite `feature_flags.py:31` and the corpus-profile-absence check as its DEV-003 basis |
| If flip is recommended, a concrete next-step ticket is named (not flipped here) | Step 4, Step 5 | Manual check: under the expected "keep OFF" outcome this AC is vacuously satisfied (no flip recommended, so nothing to name); if the real evidence instead drives a flip, Step 4/5 must name an actual ticket ID string and Step 6's allowlist tests must still show the flag absent from the ON-default set |

## Anti-Drift Notes
- **The "no suppression" check is about magnitude, not exact equality.** ON-leg event counts will
  legitimately differ from OFF-leg counts because `CombatEngagementPhase` changes engagement
  posture/behavior when active — the regression signature to rule out is a collapse to near-zero
  across all 5 event types on the ON leg specifically, not any numeric difference from OFF.
- **A near-zero OFF-leg baseline invalidates that world's data point, not just its ON leg** — per
  test_plan.md's Anti-Drift Test Guards, if `dungeon_crawl`'s OFF run itself shows near-zero
  `combat_damage`, that is not evidence the flag is safe, it is evidence the trial world/seed needs
  reconsideration (flag it in Step 4's writeup rather than treat it as a clean pass).
- **`PhaseDependencyGraph.should_run_phase()` can silently starve the ON leg of real exercise** even
  when the flag is `ON` — Step 3's skip-rate computation exists specifically to catch this; a high
  skip-rate must be disclosed as a caveat on the strength of the evidence, not omitted because the
  raw event counts happened to look fine.
- **`dungeon_crawl` is not an independent confirmation on its own** — it is the exact world/seed
  TCK-20260809 already used to find and fix the bug. `wilderness_survival` (Step 2) exists
  specifically to show the fix generalizes to a different world; do not treat Step 1 alone as
  sufficient and skip Step 2.
- **The elevated tick-budget-exceeded rate (6.2% → 7.1% on `dungeon_crawl`, per TCK-20260809's own
  disclosed finding) is expected to recur and is not a new problem to fix here** — note it if
  observed again in Step 3/4's writeup, consistent with TCK-20260809's own explicit non-fix
  decision; do not open a performance investigation inline.
- **Three independently-maintained copies of `_DELIBERATE_ON_DEFAULT_FLAGS` exist**
  (`rollout_flag_decisions_m1.md` lines 75-82) — Step 6 running all three test files is intentional
  redundancy checking all three copies stay consistent, not a mistake to dedupe here.

## Deviations

- **Interpreter substitution (Steps 1-2, 6).** The worktree's bare `python3` has no `pydantic`
  installed (`ModuleNotFoundError: No module named 'pydantic'` on the very first
  `tools/calibrate_simq.py` invocation) — a pre-existing environment gap unrelated to this ticket.
  All four trial runs and all three scoped pytest commands were instead run with
  `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` (the main checkout's venv,
  which has `pydantic` installed), with `cwd` left unchanged in the worktree so `data/runs/` and
  `data/calibration/` output still landed exactly where the plan's commands specify. No command
  text itself changed, only the interpreter path prefix.
- **One additional file created beyond the plan's explicit "Files" lists**:
  `staging_artifacts/TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION/trial_evidence.md`
  (`artifact_type: report`). The plan's own preamble flagged this as optional ("possibly a new
  stored-evidence file... if useful"); it was used to hold the full raw 5-signal x 4-leg tally so
  `rollout_flag_decisions_m1.md`'s new section could summarize rather than duplicate it in full.
- **Real evidence outcome differs from the plan's own stated expectation in one respect.** The
  plan's Step 3/4 text anticipated the OFF baseline would show real, nonzero
  `combat_damage`/`entity_killed` "comparable in order of magnitude to TCK-20260809's own recorded
  `combat_engagement_ended=10` baseline." The real trial matched `combat_engagement_ended=10`
  exactly in all 4 legs (a genuine hit), but `combat_damage`/`combat_resolved`/`entity_killed` came
  back 0 in all 4 legs, including both OFF baselines — weaker than TCK-20260809's own OFF baseline
  (`damage=1`/`resolved=1`/`killed=1`). This was disclosed as a real finding in
  `trial_evidence.md` and the ticket's Implementation Notes rather than treated as a clean pass;
  it did not change the plan's expected "Keep OFF, deferred" recommendation, since no-suppression
  evidence (the ticket's actual mandate) was still confirmed and the thin real-activity signal only
  reinforces, rather than overturns, the working conclusion.

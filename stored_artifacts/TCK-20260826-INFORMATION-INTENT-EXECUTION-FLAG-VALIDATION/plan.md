---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION
artifact_type: plan
tags: [feature-flags]
---

# Implementation Plan — TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION

## Summary
This is an evidence-gathering ticket — no `src/` behavior change is proposed. The plan runs a
controlled, single-variable OFF-vs-ON corpus trial for `ENABLE_INFORMATION_INTENT_EXECUTION`
against `urban_political` (seed 42, 200 ticks), holding `ENABLE_SELF_MODEL_COGNITION` and
`ENABLE_BELIEF_ASSIMILATION` ON in both legs so Branch B has its best real chance to route a
query. The ON leg reuses the existing permanent probe profile
`config/simulation_quality/profiles/urban_political_selfmodel_execution_probe.yaml`. The OFF leg
requires a new, temporary profile YAML (`_KNOWN_FLAGS` in `tools/calibrate_simq.py` does not
include this flag, so an env-var override silently no-ops — confirmed by direct read,
`tools/calibrate_simq.py:243-250`) that duplicates that profile's `pillar_weights` and its
`ENABLE_SELF_MODEL_COGNITION`/`ENABLE_BELIEF_ASSIMILATION` flags but *omits*
`ENABLE_INFORMATION_INTENT_EXECUTION` entirely, leaving it at the real code-level default (OFF,
`feature_flags.py:42`). Critically, the ON leg's calibration output directory must be named
exactly `data/calibration/urban_political_selfmodel_execution_probe_seed42_200t` — that is the
only `grade_anchors.json` key registered for this profile (confirmed:
`tests/simulation_quality/fixtures/grade_anchors.json` has no other `*execution*` key), and it is
the exact `run_key` `test_urban_political_selfmodel_execution_isolated_grade_anchor`
(`tests/simulation_quality/test_grade_regression.py:466-501`) looks up — using any other output
name would leave that test permanently skipped instead of actually asserting. The OFF leg has no
matching anchor entry (new profile, never anchored) and is evaluated by direct comparison only,
not a pytest anchor. After the trial, the temporary OFF-leg profile is deleted, `rollout_flag_decisions_m1.md`
is updated (table row + new dedicated section, matching the 4 prior sibling sections' format),
and `trial_evidence.md` documents the raw run data, the confirmed
distinction-from-`ENABLE_BELIEF_ASSIMILATION` finding, and the `_KNOWN_FLAGS` tooling-gap
disclosure. No test code is added or modified (per test_plan.md's "New Tests Required: None").

## Steps

### Step 1 — Baseline regression run (pre-trial)
**Files:** none changed — read-only verification step.
**Change:** Run the 5 scoped pytest commands from `test_plan.md`'s "Scoped Pytest Commands"
section, using `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` (confirmed
necessary by the SELF-MODEL-COGNITION sibling's own trial — bare `python3` in this worktree lacks
`pydantic`; re-verify this is still true before assuming it, per test_plan.md's own note, by
trying bare `python3 -c "import pydantic"` first):
```
.venv/bin/python3 -m pytest tests/unit/engine/test_information_intent_execution_phase.py -q
.venv/bin/python3 -m pytest tests/integration/domains/information/test_phase5_information_belief_phase.py -q
.venv/bin/python3 -m pytest tests/unit/config/test_phase10_feature_flags.py -q
.venv/bin/python3 -m pytest tests/integration/test_world_profile_feature_flag_guardrail.py -q
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py -k "information_intent_execution or selfmodel_execution" -q
```
Record the exact pass/fail/skip counts, especially for
`test_urban_political_selfmodel_execution_isolated_grade_anchor` and
`test_information_intent_execution_fires_through_kernel_tick_once` — expect the former to
`SKIP` (no `data/calibration/urban_political_selfmodel_execution_probe_seed42_200t/quality_report.json`
on disk yet, per `_load_calibration_report`'s skip-on-missing-report behavior,
`tests/simulation_quality/test_grade_regression.py:441-443`) and the latter to `PASS` (hand-built
scenario test, no calibration report dependency, `test_grade_regression.py:507` docstring
confirmed by direct read).
**Do NOT touch:** Any test file's assertions or skip conditions.
**Verify:** This step's own output is the verification — it establishes the "before" baseline
Step 6 is compared against.

### Step 2 — Create the temporary OFF-leg probe profile YAML
**Files:** `config/simulation_quality/profiles/urban_political_information_intent_execution_off_probe.yaml`
(new file).
**Change:** Create a profile YAML matching `urban_political_selfmodel_execution_probe.yaml`'s
`pillar_weights` block exactly (`FACTION: 1.5, ECONOMY: 1.5, SOCIAL: 1.5, COMBAT: 0.3` — read
directly, `config/simulation_quality/profiles/urban_political_selfmodel_execution_probe.yaml:11-15`)
and its `ENABLE_SOCIAL_COOPERATION: "ON"`, `ENABLE_SELF_MODEL_COGNITION: "ON"`,
`ENABLE_BELIEF_ASSIMILATION: "ON"` flags, but **omit `ENABLE_INFORMATION_INTENT_EXECUTION`
entirely** (not set to `"OFF"` — simply absent from the `feature_flags:` block), so
`_load_profile_feature_flags()` (`tools/calibrate_simq.py:51-71`) never emits that key into
`combined_flag_overrides`, and `FeatureFlagManager` falls through to its real code-level default,
`FeatureMode.OFF` (`src/domains/optimization/feature_flags.py:42`, confirmed by direct read this
session). Add a header comment explicitly marking the file TEMPORARY, naming this ticket ID, and
stating it must be deleted after the trial (mirrors the existing probe profiles' own header-comment
convention, e.g. `urban_political_selfmodel_execution_probe.yaml`'s own header, which names its
origin ticket in a comment, not the filename — consistent with the project's naming convention of
keeping ticket IDs out of identifiers/filenames and in comments/docs only).
**Do NOT touch:** `urban_political_selfmodel_execution_probe.yaml` itself (read-only reference for
this step) or any *shipped* profile (`urban_political.yaml`, `sandbox_world.yaml`, etc.).
**Verify:** `python3 -c "import yaml; print(yaml.safe_load(open('config/simulation_quality/profiles/urban_political_information_intent_execution_off_probe.yaml'))['feature_flags'])"`
must print a dict with exactly 3 keys (`ENABLE_SOCIAL_COOPERATION`, `ENABLE_SELF_MODEL_COGNITION`,
`ENABLE_BELIEF_ASSIMILATION`) and no `ENABLE_INFORMATION_INTENT_EXECUTION` key.

### Step 3 — Run the OFF-leg trial
**Files:** none in `src/`/`tests/`; writes `data/runs/<run_id>/` and
`data/calibration/urban_political_information_intent_execution_off_probe_seed42_200t/`.
**Change:** Run (venv python confirmed necessary per Step 1):
```
.venv/bin/python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name urban_political \
  --profile urban_political_information_intent_execution_off_probe \
  --output data/calibration/urban_political_information_intent_execution_off_probe_seed42_200t
```
Other writers to `data/runs/` and `data/calibration/` during this trial: Step 4 below (the ON leg,
a separate `--output` subdirectory, no collision) and any other concurrent session's own
calibration runs sharing this worktree's `data/` tree (per CLAUDE.md's shared-worktree hazard) —
mitigated by this step's fully-qualified, descriptive `--output` path not colliding with any
existing directory name (confirmed: `urban_political_information_intent_execution_off_probe_*` is
a new name, not reused by any prior ticket). Capture the `[calibrate_simq] Profile feature flags:
...` echo line verbatim into `trial_evidence.md` (Step 8) — it must show only the 3 flags from
Step 2, confirming `ENABLE_INFORMATION_INTENT_EXECUTION` was never set as an override for this
run (the direct proof the OFF leg is real, not a false "OFF-identical" result from a silently
no-op'd env-var — the exact trap `investigation.md`'s Anti-Drift Hazards section names).
**Do NOT touch:** `ENABLE_BELIEF_ASSIMILATION`'s value in this or any other invocation — it must
stay `"ON"` in every leg of this trial, never toggled off to isolate the flag artificially (ticket's
own Acceptance Criteria requirement).
**Verify:** Command exits 0; `entities=10` printed (real `urban_political` compiled state loaded,
not a silent fallback to the generic world — same check the sibling ticket's own trial used,
`calibrate_simq.py:138-153`'s `FileNotFoundError`-on-missing-world behavior makes a successful run
itself sufficient proof).

### Step 4 — Run the ON-leg trial (fresh, this ticket's own primary evidence)
**Files:** none in `src/`/`tests/`; writes `data/runs/<run_id>/` and
`data/calibration/urban_political_selfmodel_execution_probe_seed42_200t/`.
**Change:** Run (venv python):
```
.venv/bin/python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name urban_political \
  --profile urban_political_selfmodel_execution_probe \
  --output data/calibration/urban_political_selfmodel_execution_probe_seed42_200t
```
This output directory name is **not arbitrary** — it must exactly match
`"urban_political_selfmodel_execution_probe_seed42_200t"`, the only key
`grade_anchors.json` registers for this profile (verified directly:
`python3 -c "import json; ..."` against `tests/simulation_quality/fixtures/grade_anchors.json`
this session showed exactly one `*execution*` key, that one) and the exact `run_key`
`test_urban_political_selfmodel_execution_isolated_grade_anchor` looks up
(`test_grade_regression.py:466`). This directory was previously populated by the
SELF-MODEL-COGNITION sibling ticket's own trial (`run_1788018253_5169`) but that ticket's own
Finalize cleanup (`rm -rf data/runs/* reports/release_proof/*`, plus this batch's own documented
`data/calibration/*` cleanup precedent) is expected to have already removed it — this step
regenerates it fresh under this ticket's own execution, which is also the correct resolution of
investigation.md's central open question (cite vs. re-run): re-run, not cite, matching all 4 prior
sibling tickets' own precedent. Other writers to this same directory name: only this trial and the
already-closed sibling ticket's own (already-cleaned) prior run — no concurrent writer risk within
this ticket's own execution window.
**Do NOT touch:** The profile YAML itself (`urban_political_selfmodel_execution_probe.yaml`) — read
and run against as-is, never edited.
**Verify:** Command exits 0; `entities=10` printed; profile-echo line shows all 3 flags
(`ENABLE_SELF_MODEL_COGNITION`, `ENABLE_BELIEF_ASSIMILATION`, `ENABLE_INFORMATION_INTENT_EXECUTION`)
`ON`.

### Step 5 — Evidence tally: compare the two legs
**Files:** none changed — analysis step, output goes into `trial_evidence.md` (Step 8).
**Change:** For both `data/calibration/.../quality_report.json` files, tabulate per-pillar
grade/score/event_count (mirroring the SELF-MODEL-COGNITION sibling's own tally table format,
`stored_artifacts/TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION/trial_evidence.md`'s "Step 3
signal 1" table). Additionally: `grep -c '"event_type": *"action_intent"' data/runs/<off_run_id>/simulation_events.jsonl`
and the same for the ON run's `run_id`, to directly confirm the `ActionIntentAdapter` trace count
in each leg (expected: 0 in both, per `INFRA-270`'s own `support_boundary` and this
investigation's independent trace-through — Branch B is not expected to route a query in
`urban_political` at seed 42 within a 200-tick window regardless of which leg). Cross-check the ON
leg's pillar grades/scores against `grade_anchors.json["urban_political_selfmodel_execution_probe_seed42_200t"]`
using the same `_within_band`/tolerance logic Step 6's pytest run will apply (do this manually
here so Step 8's report can state pass/fail before running pytest). The OFF leg has no matching
anchor entry — state this explicitly, do not treat its absence as a gap requiring a new
`grade_anchors.json` entry (this is a temporary, non-permanent profile; adding a permanent anchor
for it would contradict Step 9's cleanup and the Anti-Drift Hazard against creating new permanent
fixtures for a single validation ticket).
**Do NOT touch:** `grade_anchors.json` itself — read-only comparison, no new entries added.
**Verify:** This step's own tabulated comparison is the artifact; no test to run, but its numbers
must match what Step 8's `trial_evidence.md` states.

### Step 6 — Regression suite re-run, un-skipped (post-trial)
**Files:** none changed — same 5 commands as Step 1.
**Change:** Re-run the identical 5 scoped pytest commands from Step 1. Because
`data/calibration/urban_political_selfmodel_execution_probe_seed42_200t/quality_report.json` now
exists (Step 4), `test_urban_political_selfmodel_execution_isolated_grade_anchor` transitions from
`SKIP` to actually asserting — record whether it passes or fails and, if it fails, the exact
band/tolerance failure detail (mirroring the sibling ticket's own "Failure detail" format in its
`trial_evidence.md`). Compare full pass/fail/skip counts against Step 1's baseline.
**Do NOT touch:** Any assertion, tolerance, or skip condition in
`tests/simulation_quality/test_grade_regression.py` even if a pillar drifts and the test fails —
per CLAUDE.md's Gate Integrity rule and this ticket's own Anti-Drift Hazards, a failing anchor test
here is a finding to disclose (Step 8), not an obstacle to edit away.
**Do NOT touch:** `_DELIBERATE_ON_DEFAULT_FLAGS` or any equivalent allowlist in
`tests/unit/config/test_phase10_feature_flags.py`,
`tests/integration/test_scenario_feature_flag_defaults.py`, or
`tests/certification/test_phase10_enhanced_determinism_parity.py` — the expected "keep OFF"
outcome means this flag must not be added to any of those lists.
**Verify:** The recorded pass/fail/skip tallies themselves are the verification; feed exact numbers
into `trial_evidence.md` (Step 8).

### Step 7 — Update `docs/architecture/rollout_flag_decisions_m1.md`
**Files:** `docs/architecture/rollout_flag_decisions_m1.md`.
**Change:** Two edits, matching the 4 existing sibling sections' exact format
(`ENABLE_COMBAT_ENGAGEMENT`/`ENABLE_SELF_MODEL_COGNITION`/`ENABLE_WORLD_EMERGENCE`/
`ENABLE_PROGRESSION_EVOLUTION` sections, lines 35/117/204/307, all read directly this session):
1. Update the `ENABLE_INFORMATION_INTENT_EXECUTION` table row (line 33) — change verdict to `Kept
   OFF, deferred (real trial evidence now on file)` and rewrite the rationale cell to summarize
   Steps 3-6's findings (expected: no suppression regression, `ENABLE_BELIEF_ASSIMILATION`'s
   now-ON default correctly does not activate this flag's own execution — the two systems remain
   independently gated as designed — but zero shipped profiles turn this flag on and Branch B did
   not route a query in either leg of this trial's corpus/seed/window, matching `INFRA-270`'s and
   `INFRA-266`'s prior findings).
2. Append a new `## ENABLE_INFORMATION_INTENT_EXECUTION — Validation Trial Result (TCK-20260826)`
   section after the existing `## ENABLE_PROGRESSION_EVOLUTION` section (end of file), documenting:
   the confirmed distinction from `ENABLE_BELIEF_ASSIMILATION` (Branch B *production* vs Branch B
   *execution*, per investigation.md's own confirmed-not-assumed finding), the OFF-vs-ON trial
   commands/results from Steps 3-6, the `_KNOWN_FLAGS` tooling-gap disclosure (stated as a real gap,
   not fixed here), and the recommendation (Step 8's own conclusion). State explicitly that this is
   the 5th and final of the 5 flags `TCK-20260824-ROLLOUT-FLAG-DECISIONS` originally deferred, now
   all carrying real trial evidence on file.
**Do NOT touch:** Any other flag's row or section in this file (`ENABLE_BELIEF_ASSIMILATION`'s row,
already-flipped, must not be re-litigated per Out of Scope).
**Verify:** No automated test — manual read-through confirming the new section matches the 4
existing sections' structure (World tested / Commands / Evidence tally / Honest gap /
Recommendation subsections, per the sibling section's own layout).

### Step 8 — Write `trial_evidence.md`
**Files:** `staging_artifacts/TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION/trial_evidence.md`
(new file, moved to `stored_artifacts/` at ticket close per Definition of Done).
**Change:** Document, in the same structure as
`stored_artifacts/TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION/trial_evidence.md` (read
directly this session as the format precedent): environment note (venv python substitution),
verbatim commands run (Steps 3-4), world-loading confirmation, the Step 5 evidence tally table
(both legs, `ActionIntentAdapter` trace counts, grade-anchor cross-check for the ON leg only),
the Step 6 pytest re-run results (before/after skip-to-assert transition), an explicit **"Honest
Gap"** section disclosing (a) the `tools/calibrate_simq.py` `_KNOWN_FLAGS` allowlist gap (cite
`tools/calibrate_simq.py:243-250` — env-var overrides silently no-op for this flag; not fixed by
this ticket) and (b) any other new finding the trial surfaces (e.g. if Step 6's anchor test fails
or any anomaly appears) — disclosed, not fixed inline, with a note that a follow-up ticket would
be needed. Add a closing line noting this is the 5th and final of the 5 originally-deferred flags
now all having real trial evidence on file (mirrors Step 7's doc note). State the final keep/flip
recommendation with its evidentiary basis (expected: "Keep OFF, deferred" — no shipped profile
turns this flag on anywhere, matching all 4 sibling outcomes and `investigation.md`'s Risks
section reasoning — but do not pre-commit to this if Steps 3-6 surface a different result).
**Do NOT touch:** Do not silently omit a negative/messy finding (a failing anchor test, an
unexpected trace count) to make the evidence look cleaner than it is — per Gate Integrity, report
truthfully.
**Verify:** File exists, frontmatter valid (`status: historical`, `artifact_type: report`,
`tags: [feature-flags]`, matching the sibling's own frontmatter pattern), content cross-checked
against Steps 3-6's actual recorded numbers (not invented).

### Step 9 — Cleanup
**Files:** delete `config/simulation_quality/profiles/urban_political_information_intent_execution_off_probe.yaml`
(the Step 2 temporary file); clean `data/runs/*` and `reports/release_proof/*` per Definition of
Done; clean the two `data/calibration/urban_political_*` trial output directories created in Steps
3-4, following the same precedent all 4 sibling tickets' own Finalize already established for this
batch.
**Change:** `rm config/simulation_quality/profiles/urban_political_information_intent_execution_off_probe.yaml`;
`rm -rf data/runs/* reports/release_proof/*`; `rm -rf data/calibration/urban_political_information_intent_execution_off_probe_seed42_200t data/calibration/urban_political_selfmodel_execution_probe_seed42_200t`.
Confirm via `git status` that the temporary profile file is not staged and no stray trial artifact
remains uncommitted before the ticket's own commit.
**Do NOT touch:** `config/simulation_quality/profiles/urban_political_selfmodel_execution_probe.yaml`
(permanent fixture, keep as-is) or any other existing `data/calibration/*` directory belonging to a
different ticket's own already-committed evidence.
**Verify:** `git status` shows no new/modified file under `config/simulation_quality/profiles/`;
`ls data/calibration/ | grep information_intent_execution` returns nothing.

## Scope Guards
- Never flip `ENABLE_INFORMATION_INTENT_EXECUTION`'s or `ENABLE_BELIEF_ASSIMILATION`'s actual
  default in `src/domains/optimization/feature_flags.py` — this plan produces a recommendation
  only, never a default change.
- Do not fix `tools/calibrate_simq.py`'s `_KNOWN_FLAGS` allowlist gap inline. Disclose it in
  `trial_evidence.md`'s Honest Gap section (Step 8) only.
- If the trial surfaces any other real bug or gap unrelated to this ticket's own scope (e.g. an
  anchor drift, a pipeline error), disclose it in Step 8 — do not fix it inline, do not author a
  new regression test for it, do not re-anchor `grade_anchors.json` to make a failing test pass.
- The temporary OFF-leg probe profile (Step 2) must never be left behind as an uncommitted or
  permanent artifact — Step 9 explicitly deletes it. It must never be treated as a second permanent
  fixture alongside `urban_political_selfmodel_execution_probe.yaml`.
- Do not create or edit any *shipped* `config/simulation_quality/profiles/*.yaml` (e.g.
  `urban_political.yaml`, `sandbox_world.yaml`) to make a real archetype world ship this flag ON —
  that would fabricate the "shipped production evidence" this ticket exists to honestly assess.
- Do not re-litigate `ENABLE_BELIEF_ASSIMILATION`'s already-decided ON default (Out of Scope, ticket
  body) — it stays ON, unchanged, in every leg of this trial.
- Do not touch `InformationBeliefPhase`, `InformationIntentExecutionPhase`, `ActionIntentAdapter`,
  or any other production source file — this is an evidence-gathering ticket only; `behavior_changed`
  is expected to report `false` at Implement time since no `src/` file is modified.
- Do not add `ENABLE_INFORMATION_INTENT_EXECUTION` to any `_DELIBERATE_ON_DEFAULT_FLAGS`-style
  allowlist (`tests/unit/config/test_phase10_feature_flags.py`,
  `tests/integration/test_scenario_feature_flag_defaults.py`,
  `tests/certification/test_phase10_enhanced_determinism_parity.py`) — the expected "keep OFF"
  outcome does not warrant this.
- Do not use a bare env-var override (`ENABLE_INFORMATION_INTENT_EXECUTION=ON python3
  tools/calibrate_simq.py ...`) anywhere in this trial — confirmed to silently no-op for this
  specific flag (`tools/calibrate_simq.py:243-250`'s `_KNOWN_FLAGS` list does not include it). Every
  invocation in this plan uses `--profile` pointing at a YAML with its own `feature_flags:` block.
- Do not edit `docs/parity_ledger/infrastructure.yaml`'s `INFRA-270`/`INFRA-266`/`INFRA-267` entries
  unless Steps 3-6 surface a genuinely new finding requiring an addendum (not expected per
  investigation.md — these entries were re-read directly this session and confirmed still accurate).
- No new unit/integration test code is required or should be authored (test_plan.md: "New Tests
  Required: None").

## Dependency Map
- Step 1 (baseline) is independent — can run first, standalone.
- Step 2 (create OFF profile) has no dependency; must complete before Step 3.
- Step 3 (OFF-leg trial) depends on Step 2.
- Step 4 (ON-leg trial) depends on nothing new (uses the existing permanent profile) but should run
  after Step 2/3 only for narrative/report ordering — no technical dependency between Step 3 and
  Step 4 (they write to disjoint `data/calibration/` subdirectories and disjoint `data/runs/<run_id>/`
  directories, so order between them does not matter).
- Step 5 (evidence tally) depends on both Step 3 and Step 4 having completed.
- Step 6 (post-trial regression re-run) depends on Step 4 specifically (needs
  `data/calibration/urban_political_selfmodel_execution_probe_seed42_200t/quality_report.json` to
  exist for the anchor test to un-skip) and should also follow Step 3, though Step 3's data is not
  itself consumed by any pytest test.
- Step 7 (doc update) depends on Step 5 and Step 6 (needs their actual numbers).
- Step 8 (trial_evidence.md) depends on Steps 3-6 (needs their actual output) and should be written
  alongside or immediately after Step 7 (same source data).
- Step 9 (cleanup) must run last, after Steps 7-8 have captured everything needed from the trial
  output — deleting the temp profile and calibration directories before Step 7/8 are written would
  destroy the evidence being documented.

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| The distinction from `ENABLE_BELIEF_ASSIMILATION`/`information_belief` is confirmed and documented, not assumed | Already confirmed in investigation.md (Current Behavior section, phase.py/pipeline.py reads); durably documented by Step 7 (rollout_flag_decisions_m1.md new section) and Step 8 (trial_evidence.md) | No test — documentation-only AC; verified by direct read of `src/domains/information/phase.py` and `src/engine/pipeline.py:161-184` already cited in investigation.md |
| A real corpus-profile ON trial is run and documented, with `ENABLE_BELIEF_ASSIMILATION` left at its now-ON default | Steps 2-6 (OFF+ON legs, both with `ENABLE_BELIEF_ASSIMILATION: "ON"`), Step 7, Step 8 | `test_urban_political_selfmodel_execution_isolated_grade_anchor` (un-skipped by Step 4/6), `test_information_intent_execution_fires_through_kernel_tick_once`, plus the 5 scoped pytest commands in Steps 1/6 |
| A keep/flip recommendation with evidence is produced | Step 5 (tally), Step 7 (doc section), Step 8 (trial_evidence.md's Recommendation) | No test — evidence-quality is verified by cross-checking Step 8's stated numbers against Steps 3-6's actual raw output during Verify/Architecture-Verify |

## Anti-Drift Notes
- `INFRA-270`'s own `support_boundary` and this investigation's independent trace-through both
  already establish that "0 `ActionIntentAdapter` traces in `urban_political` at seed 42" is an
  **expected, not-reached** result, not a suppression/regression finding. Steps 3-5 are very likely
  to reproduce this in both legs — that is not itself a negative outcome and must not be reported as
  a fresh problem.
- Extended-tick leg (e.g. 2000 ticks) considered and **not included** in this plan: none of the 4
  prior sibling tickets in this batch ran a longer-than-200-tick leg for their own trials
  (established evidence-bar precedent for this batch), the expected recommendation ("Keep OFF,
  deferred") turns on the DEV-003 "no shipped profile" bar rather than on whether Branch B
  eventually fires at some longer tick count, and `INFRA-270`'s existing hand-built-scenario test
  (`test_information_intent_execution_fires_through_kernel_tick_once`) already deterministically
  proves execution works when Branch B does fire — an extended-tick leg would mostly re-confirm the
  already-documented "not reached in a short window" finding at added run cost, for low marginal
  evidentiary value relative to this ticket's own scope. If the team later wants to definitively
  settle whether Branch B ever organically routes in real corpus play, that is a new, separate
  ticket (not this one) — noted here, not actioned.
- The exact ON-leg output directory name (`urban_political_selfmodel_execution_probe_seed42_200t`)
  is load-bearing for Step 6's anchor test to actually assert instead of skip — do not rename it
  even for clarity; it must match `grade_anchors.json`'s registered key and the test's own
  hardcoded `run_key` string exactly.
- The OFF-leg profile (Step 2) intentionally *omits* the flag key rather than setting it `"OFF"` —
  both have the same net effect (falls through to the code default) since
  `_load_profile_feature_flags()` only emits keys present in the YAML, but omission more precisely
  demonstrates "this flag was never touched by this trial leg," which is the point of a
  single-variable OFF-vs-ON design.
- Per test_plan.md's Anti-Drift Test Guards: `test_action_intent_execution_phase_off_by_default_is_a_noop`
  must keep passing unmodified throughout — if this ticket's trial ever seemed to require changing
  that test's assertions, that would itself be a signal to stop and report, not to edit around (Out
  of Scope forbids flipping the default).

## Unresolved Questions
None. The investigation's central open question (cite the sibling's existing run vs. run a fresh
trial) is resolved by this plan: Steps 3-4 run a fresh trial under this ticket's own execution,
matching all 4 prior sibling tickets' precedent, per the orchestrator's own explicit instruction.

## Deviations

- **Step 1's expected `SKIP` did not occur — the baseline ran as an unexpected `FAIL` instead.**
  Plan expected `test_urban_political_selfmodel_execution_isolated_grade_anchor` to `SKIP` at Step
  1 (no local `quality_report.json` yet). In fact, a report for this exact run key already existed
  on disk before this ticket ran anything — leftover output from the separately-tracked, still-`OPEN`
  `TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION` ticket's own prior calibration
  run (file timestamp 2026-08-29 22:44, one day before this ticket's own execution on 2026-08-30).
  So Step 1 observed the test already asserting and already failing on the same `SOCIAL`-pillar
  drift that ticket disclosed. Step 4's own fresh ON-leg run then overwrote that file with this
  ticket's own independently-produced data, and Step 6's re-run reproduced the identical failure —
  confirming the drift is real and deterministic, not an artifact of the leftover data. This did
  not change the plan's own steps or scope guards; documented as a finding in
  `trial_evidence.md`'s Honest Gap section rather than treated as a plan defect requiring rework.
- **Step 9's literal cleanup command (`rm -rf data/calibration/urban_political_information_intent_execution_off_probe_seed42_200t
  data/calibration/urban_political_selfmodel_execution_probe_seed42_200t`) was not executed.**
  Per the orchestrator's explicit instruction at Implement time, matching the SELF-MODEL-COGNITION
  and WORLD-EMERGENCE sibling tickets' own actual precedent (their `data/calibration/*` trial
  output directories remain in place on disk as part of the standing evidentiary record, not
  deleted at their own Finalize despite this plan's Step 9 template language), both this ticket's
  `data/calibration/` output directories were left in place rather than deleted. Only the truly
  incidental temp file — the Step 2 OFF-leg probe profile YAML — was deleted, confirmed via
  `git status --porcelain -- config/simulation_quality/profiles/` showing no trace. `data/runs/*`
  and `reports/release_proof/*` cleanup was also left untouched at Implement time: this shared
  worktree's `data/runs/` directory contained 3 run directories (of 5 total) not attributable to
  this ticket's own two `calibrate_simq.py` invocations, consistent with a concurrent session
  actively writing to the same shared directory (per CLAUDE.md's own documented shared-worktree
  hazard) — a blind `rm -rf data/runs/*` at Implement time risked destroying another session's
  in-flight work. This is left for Finalize (which runs after this shared-worktree risk window has
  a chance to clear) rather than attempted here.

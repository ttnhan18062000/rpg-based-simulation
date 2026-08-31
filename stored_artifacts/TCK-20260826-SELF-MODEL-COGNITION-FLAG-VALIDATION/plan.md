---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION
artifact_type: plan
tags: [feature-flags]
---

# Implementation Plan — TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION

## Summary
This ticket produces evidence, not code — same shape as its sibling
`TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION`. Unlike that sibling, real trial evidence already
exists for `ENABLE_SELF_MODEL_COGNITION` (a shipped-ON Unit-tier world, two permanent grade-anchor
probe profiles, and `INFRA-266`'s real 3-seed generalization trial against `urban_political`) —
investigation.md's job was to confirm none of it amounts to a *shipped archetype-world default*
turning the flag on, the DEV-003 bar the sibling was measured against. This plan's job is to (1)
run a genuinely fresh trial — not just cite the historical one — by regenerating both
`urban_political_selfmodel*_probe` profiles' `data/calibration/` reports under this ticket's own
run and un-skipping the 6 grade-anchor tests that currently skip for lack of local calibration
data, (2) resolve AC2 (the `ENABLE_ADVENTURE_ROUTING` combination question) using the static grep
evidence investigation.md already gathered — no empirical combination trial, per investigation's
own explicit Anti-Drift Hazard against burning compute to re-confirm a structural guarantee — and
add a durable regression guard test so that resolution cannot silently go stale, (3) write the
`docs/architecture/rollout_flag_decisions_m1.md` row + new section mirroring the combat-engagement
sibling's exact shape, (4) produce a `trial_evidence.md` artifact mirroring the sibling's raw-tally
format, and (5) re-run the full scoped regression suite from test_plan.md. No file under `src/` is
touched. The expected recommendation, per investigation.md's own Risks section, is "Keep OFF,
deferred" — `unit_selfmodel_pilot` (the only flag-ON shipped profile) is a dedicated 16-entity
Unit-tier isolation world, not a real archetype world like `urban_political`/`sandbox_world`, so
even with three independent real trials on file the DEV-003 "shipped production profile" bar is
still unmet. This plan states that as the working conclusion the fresh trial data must confirm or
overturn, not a foregone one.

## Steps

### Step 1 — Run a fresh ON calibration trial: `urban_political_selfmodel_probe` (materialization-only)
**Files:** None changed. Writes only to `data/calibration/urban_political_selfmodel_probe_seed42_200t/`
and `data/runs/{run_id}/` (temporary, cleaned at Finalize per Definition of Done — do not clean
mid-ticket, Steps 3-4 read these outputs).
**Change:** Run the exact non-standard invocation this profile requires — confirmed by direct read
of `tools/calibrate_simq.py:39-48` (`_resolve_profile()`: profile name defaults to `--name` only if
a matching `config/simulation_quality/profiles/{name}.yaml` exists) and `:512-516` (explicit
`--profile` always wins over name-based resolution), and independently confirmed as the real,
previously-used command by two prior tickets'
stored artifacts (`stored_artifacts/TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE/test_plan.md:66-68`,
`stored_artifacts/TCK-20260713-SIMQ-SCORE-CEILING-FIX/plan.md:451-454`, both documenting this exact
profile/name split as a known naming quirk):
```
python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name urban_political \
  --profile urban_political_selfmodel_probe \
  --output data/calibration/urban_political_selfmodel_probe_seed42_200t
```
`--name urban_political` loads the real compiled `data/worlds/urban_political/resolved/world.resolved.yaml`
state (`calibrate_simq.py:138-153`, `_load_world_state()` — a name that fails to resolve raises
`FileNotFoundError` rather than silently falling back, so a successful run itself confirms the real
corpus world loaded, not the generic hero+goblins fallback). `--profile urban_political_selfmodel_probe`
loads `config/simulation_quality/profiles/urban_political_selfmodel_probe.yaml`'s `feature_flags:`
block (`ENABLE_SELF_MODEL_COGNITION: "ON"`, `ENABLE_BELIEF_ASSIMILATION` explicitly absent/OFF —
confirmed by investigation.md's direct read of that file) via `calibrate_simq.py:522-524`. Record
the printed `run_id` (format `run_{timestamp}_{pid}`, confirmed unique per invocation at
`calibrate_simq.py:291` and by the sibling ticket's own 4 distinct `run_id` values) for Step 3.
**Other writers to `data/calibration/` and `data/runs/`:** any concurrent session running its own
`tools/calibrate_simq.py` invocation (e.g. another of the 3 sibling flag-validation tickets, or a
routine `evaluate_simq.py` sweep) writes to a different `{run_key}`/`{run_id}` directory — no
collision, since this ticket's own `--output` path is unique to this exact
profile+world+seed+ticks combination and `run_id` is timestamp+pid-keyed. `grade_anchors.json`
(the comparison fixture) is never written by `calibrate_simq.py` (grepped, zero matches) — this
step cannot mutate the anchor data it will be compared against.
**Do NOT touch:** `src/cognition/self_model_phase.py`, `src/domains/optimization/feature_flags.py`,
`config/simulation_quality/profiles/urban_political_selfmodel_probe.yaml` — this step only runs
existing tooling against an existing profile, per this ticket's Out of Scope.
**Verify:** Command exits 0 and produces
`data/calibration/urban_political_selfmodel_probe_seed42_200t/quality_report.json`. This is the raw
input Step 3 analyzes and Step 4's pytest re-run depends on; there is no separate pytest assertion
for this step alone, consistent with test_plan.md ("this ticket is fundamentally
evidence-gathering... No new pytest test is strictly required to satisfy AC1").

### Step 2 — Run a fresh ON calibration trial: `urban_political_selfmodel_execution_probe` (full-stack)
**Files:** Same as Step 1 (writes only to `data/calibration/urban_political_selfmodel_execution_probe_seed42_200t/`
and a new `data/runs/{run_id}/`).
**Change:**
```
python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name urban_political \
  --profile urban_political_selfmodel_execution_probe \
  --output data/calibration/urban_political_selfmodel_execution_probe_seed42_200t
```
Same mechanism as Step 1, against `config/simulation_quality/profiles/urban_political_selfmodel_execution_probe.yaml`,
which adds `ENABLE_BELIEF_ASSIMILATION: "ON"` and `ENABLE_INFORMATION_INTENT_EXECUTION: "ON"` on top
of `ENABLE_SELF_MODEL_COGNITION: "ON"` (confirmed by investigation.md's direct read of that file).
Per `tests/simulation_quality/test_grade_regression.py:466-486`'s own docstring (read directly this
session), this profile's `urban_political`/seed 42/200-tick combination is known not to route a
Branch B query (`0 ActionIntentAdapter traces`) — this run is expected to reproduce that same
finding (a real, disclosed non-generalization), not treated as a failure if it does.
**Other writers to `data/calibration/`/`data/runs/`:** same as Step 1 — a distinct, uniquely-keyed
output path; no collision with concurrent sessions or Step 1's own output.
**Do NOT touch:** Same scope guard as Step 1, plus
`config/simulation_quality/profiles/urban_political_selfmodel_execution_probe.yaml` and
`src/domains/information/` (`InformationIntentExecutionPhase`) — out of this ticket's edit scope
per investigation.md's Anti-Drift Hazards.
**Verify:** Command exits 0 and produces
`data/calibration/urban_political_selfmodel_execution_probe_seed42_200t/quality_report.json`.

### Step 3 — Extract and cross-check evidence signals from both fresh runs
**Files:** None changed (analysis only; the durable record is written in Steps 6-7).
**Change:** For each of the 2 fresh runs, capture:
1. `pillars.COGNITION.grade`/`.score` and `pillars.INFORMATION.grade`/`.score`/`.event_count` from
   each `quality_report.json` (schema confirmed by direct read of
   `test_grade_regression.py:441-448`, which asserts exactly these keys against the
   `urban_political_selfmodel_probe` run).
2. `self_model_updated`/`self_model_active` event counts from `data/runs/{run_id}/simulation_events.jsonl`
   (e.g. `grep -c '"event_type": *"self_model_updated"' data/runs/{run_id}/simulation_events.jsonl`) —
   compare against `INFRA-266`'s historically recorded `~5610-5611` events/run at this same
   world/seed/tick-count (investigation.md's own citation) to confirm the fresh run reproduces that
   order of magnitude, not just a nonzero count.
3. Cross-check both reports' grades/scores against
   `tests/simulation_quality/fixtures/grade_anchors.json`'s existing entries for these two exact
   `run_key`s (confirmed present this session: `urban_political_selfmodel_probe_seed42_200t` →
   `COGNITION: S/28.05`, `INFORMATION: C/0.0`; `urban_political_selfmodel_execution_probe_seed42_200t`
   → `COGNITION: S/27.485`, `INFORMATION: B/0.2`) — a match confirms the fresh trial reproduces the
   anchored baseline; a drift beyond the anchor's ±1 band is a real finding to disclose (matching
   test_plan.md's Anti-Drift Test Guards: "Do not weaken... to make this ticket pass faster").
4. Note the execution probe's `INFORMATION` grade is anchored `B` (not `C`), not `0 traces` as its
   own docstring's prose might suggest in isolation — `event_count`/grade is a different metric from
   `ActionIntentAdapter` trace count, and this plan does not attempt to reconcile that nuance beyond
   citing both data points as they exist; Step 6/7's write-up must report the anchor's real `B`
   grade, not silently round it to the docstring's "does not generalize" framing.
**Do NOT touch:** No source or fixture files — read-only extraction.
**Verify:** A written tally (both runs' pillar grades/scores/event counts vs. INFRA-266's historical
figures and the `grade_anchors.json` entries) exists and explicitly states whether each run
reproduced its anchor. This tally is the direct evidence base for Steps 4, 6, and 7 — all three
must cite these exact numbers, not a paraphrase.

### Step 4 — Re-run the grade-anchor regression suite un-skipped (AC1's pytest verification)
**Files:** None changed. Test execution only.
**Change:** Run `tests/simulation_quality/test_grade_regression.py -k selfmodel -q` now that Steps
1-2 have produced both `data/calibration/{run_key}/quality_report.json` files. Per investigation.md
(re-confirmed this session: 6 skipped, none failed, because the reports were absent), this is
expected to now show the 2 grade-anchor tests
(`test_urban_political_selfmodel_cognition_isolated_grade_anchor`,
`test_urban_political_selfmodel_execution_isolated_grade_anchor`) actually assert and pass, rather
than skip — this is the concrete mechanism by which this ticket satisfies AC1's "run and documented"
requirement with a real, non-skipped pytest pass, not citation of a historical run alone. The other
4 `selfmodel`-matched entries (the `unit_selfmodel_pilot` seed/tolerance band checks) require
`unit_selfmodel_pilot`'s own calibration reports; if those remain absent locally, note the
unchanged skip count for those 4 specifically (not a blocker — `unit_selfmodel_pilot`'s own
evidence already exists from its own ticket, per investigation.md's Prior Work). Also re-run
`tests/unit/cognition/test_phase2_self_model_phase.py tests/unit/config/test_phase10_feature_flags.py
-q` and `tests/integration/domains/test_fused_loop.py -k "self_model or branch_b or belief" -q`
(test_plan.md's Scoped Pytest Commands) to reconfirm the phase/patch/cross-tick coverage
investigation.md already re-ran once this session.
**Do NOT touch:** No test file is modified by this step.
**Verify:** `test_grade_regression.py -k selfmodel -q` reports at least the 2 grade-anchor tests
passing (not skipped); the other two commands reproduce investigation.md's own re-run counts (12
passed; 7 passed, 3 deselected) or better.

### Step 5 — Resolve AC2: confirm static evidence suffices, add a durable regression guard
**Files:** New file `tests/architecture/test_adventure_routing_flag_inert.py`.
**Change:** This step makes the explicit decision the orchestrator asked Plan to make (not defer to
Implement): investigation.md's static analysis — `grep -rn "ENABLE_ADVENTURE_ROUTING" src/ tools/`
returning zero live `is_enabled(...)`/`get_flag_mode(...)`/`run_phase(..., feature_flag=...)` call
sites, `AdventureGoalScorer.score()` (`src/ai/goals/adventure_scorer.py:119-121`, comment read
directly by investigation.md) running unconditionally, and `docs/engine/known_limitations.md` §1.5
(lines 33-65, read directly) already documenting this inertness in prose, backed by
`docs/parity_ledger/strategic_cognition.yaml`'s `STRAT-252` entry — **is sufficient on its own to
resolve AC2**. No empirical combination trial (e.g. running self-model ON against a world where
`ENABLE_ADVENTURE_ROUTING` is also ON, such as `hero_guild_routing`/`simq_routing_test`) is
scheduled, per investigation.md's own explicit Anti-Drift Hazard: "an empirical trial would burn
real compute to re-confirm something the code structure already guarantees." There is no runtime
code path where the two flags' values can interact, so no trial result could produce a different
answer than the static analysis already gives.
To make this resolution durable (test_plan.md's proposed, optional "New Tests Required" entry,
accepted here since it is a single self-contained unit test with zero `src/` changes and directly
strengthens AC2's "resolved, not left open again" requirement against future silent drift): add
`test_enable_adventure_routing_has_no_live_gating_call_site` to a new file in `tests/architecture/`
(matching that directory's existing static-analysis-guard convention — confirmed by directory
listing: `test_adventure_route_score_max_unchanged.py`, `test_no_new_hardcoded_gameplay_truth.py`,
`test_fallback_retirement_gate.py`, etc. all live there and follow this pattern). The test greps
`src/` for `is_enabled("ENABLE_ADVENTURE_ROUTING")`, `get_flag_mode("ENABLE_ADVENTURE_ROUTING")`,
and `feature_flag="ENABLE_ADVENTURE_ROUTING"`, and asserts zero matches outside
`feature_flags.py`'s own registration line (`feature_flags.py:25`). If a future ticket re-wires the
flag to gate something again, this test fails loudly and forces an explicit update to
`known_limitations.md` §1.5's claim, rather than letting the doc go stale silently.
**Other writers to `src/`:** none relevant — this is a read-only grep-based test; it does not
depend on or race with any other writer, since it only inspects committed `src/` files at test-run
time.
**Do NOT touch:** `src/ai/goals/adventure_scorer.py`, `docs/engine/known_limitations.md`,
`docs/parity_ledger/strategic_cognition.yaml` — the static finding is already correct and
documented; this step only adds a regression guard, it does not re-verify or re-write the existing
citations. Do not schedule or attempt any empirical `ENABLE_ADVENTURE_ROUTING` +
`ENABLE_SELF_MODEL_COGNITION` combination trial.
**Verify:** `pytest tests/architecture/test_adventure_routing_flag_inert.py -q` passes (new test,
1 passed).

### Step 6 — Produce `staging_artifacts/TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION/trial_evidence.md`
**Files:** `staging_artifacts/TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION/trial_evidence.md`
(new file, `artifact_type: report`, mirroring
`stored_artifacts/TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION/trial_evidence.md`'s exact shape:
frontmatter, commands run verbatim, evidence tally table, an explicit pass/fail statement, an
honest-gap section if one exists).
**Change:** Write the full raw record: the two commands from Steps 1-2 (verbatim), the world-loading
confirmation (`--name urban_political` resolves the real compiled world, not the fallback — the
`FileNotFoundError`-on-failure behavior from `calibrate_simq.py:138-153` makes a successful run
itself sufficient proof, no separate fingerprint check needed here since only one world is used
across both legs, unlike the sibling's two-world A/B), the full Step 3 evidence tally (both runs'
pillar grades/scores/event counts, the INFRA-266 historical comparison, the `grade_anchors.json`
cross-check), the Step 4 pytest re-run results (skip→pass transition), and the Step 5 AC2
resolution summary (static evidence + new guard test). Include an explicit "honest gap" section if
Step 3 finds any drift from the anchored/historical figures — do not smooth over a real finding.
**Other writers to this file:** none — this is a new file scoped to this ticket only; no other
ticket or session writes to this exact path.
**Do NOT touch:** `stored_artifacts/TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION/trial_evidence.md`
(the sibling's own file) — reference it as a format precedent only, never edit it.
**Verify:** Re-read confirms the file's tally matches Step 3's real numbers exactly (not
placeholder/hypothetical numbers), and
`python3 tools/validate_frontmatter.py staging_artifacts/TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION/trial_evidence.md`
passes.

### Step 7 — Write the real decision into `docs/architecture/rollout_flag_decisions_m1.md`
**Files:** `docs/architecture/rollout_flag_decisions_m1.md`
**Change:** This file's existing table row for `ENABLE_SELF_MODEL_COGNITION` (confirmed at line 30
of the current file: `| ENABLE_SELF_MODEL_COGNITION | **Kept OFF, deferred** | No production
evidence; the dead RolloutProfileManager's own conflicting default (enabled) was confirmed not
usable as evidence. Follow-up: TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION. |`) currently
points at this ticket as an open follow-up, and its rationale ("no production evidence") is now
known to understate what already existed (investigation.md's own finding). Update that row's
Verdict/Rationale cell in place to reflect the real, more nuanced outcome (three independent prior
trials plus this ticket's own fresh confirming run, still short of a shipped archetype-world
default), and add a new `## ENABLE_SELF_MODEL_COGNITION — Validation Trial Result (TCK-20260826)`
section directly below the existing `## ENABLE_COMBAT_ENGAGEMENT — Validation Trial Result
(TCK-20260826)` section (lines 35-115 of the current file), mirroring its exact structure: worlds
tested, commands run, evidence tally, a "no suppression"-equivalent confirmation (here: "reproduces
anchored baseline" instead, since self-model's risk profile is generalization/regression, not
suppression), the honest gap (if any, from Step 3/6), and the recommendation.
Per `docs/guidelines/intentional_divergences.md` DEV-003's own standard (this file's own "## The
Precedent This Sets" section, lines 130-144: flip ON requires "real, standing evidence the system
already runs safely in production... a live SimQ corpus profile already exercising it"), and the
fact confirmed by investigation.md's direct read of every shipped profile YAML this session (only
`unit_selfmodel_pilot.yaml`, a dedicated 16-entity Unit-tier isolation world, ships the flag ON —
`urban_political`'s own two probe profiles are explicitly not its shipped default), the expected
recommendation is **"Keep OFF, deferred — three independent real trials now on file (shipped-ON
unit-tier world, two grade-anchor probes, INFRA-266's real-world generalization split verdict),
still no shipped archetype-world default profile; re-open only if a shipped profile begins using
it."** This is the working conclusion Steps 1-4's fresh data must confirm, not a foregone one: if
Step 3/4 surfaces a real anchor-band drift or regression, the recommendation must instead disclose
that as a new finding requiring a separate ticket, per test_plan.md's Anti-Drift Test Guards.
Also add the resolved AC2 finding (the `ENABLE_ADVENTURE_ROUTING` combination is structurally
inert, static analysis + the new `tests/architecture/test_adventure_routing_flag_inert.py` guard
from Step 5) as a subsection or paragraph within the same new section, since this ticket's own
scope bundles both questions.
Do not add a `DEV-00N` entry to `docs/guidelines/intentional_divergences.md` unless the
recommendation is "flip" — investigation.md's Docs Requiring Update section is explicit that a
"stay OFF" outcome requires no new divergence entry.
**Other writers to this shared file:** three sibling flag-validation tickets
(`TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION`, `TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION`,
`TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION`) each own a different row in the same
"## The 8 Flags Reviewed" table and are expected to each add their own new `##`-level section below
it, potentially in a concurrent or later session — the already-landed `ENABLE_COMBAT_ENGAGEMENT`
section (lines 35-115) is one such precedent already in the file. This step touches **only** the
`ENABLE_SELF_MODEL_COGNITION` row (line 30) and adds **only** the new
`ENABLE_SELF_MODEL_COGNITION` section, immediately after the existing `ENABLE_COMBAT_ENGAGEMENT`
section and before `## RolloutProfileManager — Cut` — a row-scoped/section-appended edit, not a
full-file rewrite, to avoid colliding with any sibling ticket's own concurrent edit to a different
row/section. If a `git` conflict arises against a concurrent sibling edit to this same file, resolve
it by keeping both sections (never drop another ticket's already-landed content).
**Do NOT touch:** Any other row in the 8-flag table, the `## RolloutProfileManager — Cut`, `## The
Precedent This Sets`, or `## A Real Correction Made During Implementation` sections — those are
historical records of other tickets, not this one.
**Verify:** No automated test covers doc prose content; verification is a re-read confirming the
row and new section accurately reflect Steps 3/4/5's real numbers and outcomes (not
placeholder/hypothetical), and
`python3 tools/validate_frontmatter.py docs/architecture/rollout_flag_decisions_m1.md` still passes
since the file's own frontmatter block (lines 1-7) is untouched.

### Step 8 — Update this ticket's own Implementation Notes / Test Summary / Files Changed / Completion Summary
**Files:** `tickets/inprogress/TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION.md`
**Change:** Fill in `## Implementation Notes` with a condensed version of Steps 3-5's findings and
Step 7's recommendation (link to the doc section rather than duplicate the full tally). Fill in
`## Test Summary` with the scoped pytest command results from test_plan.md's "Scoped Pytest
Commands" section (all commands must be run and reported — see Step 9). Fill in `## Files Changed`
listing `docs/architecture/rollout_flag_decisions_m1.md`,
`tests/architecture/test_adventure_routing_flag_inert.py` (new), and this ticket file itself plus
staging-artifact moves at Finalize — no other `src/` entries. Fill in `## Completion Summary`
stating the keep/flip outcome and the AC2 resolution.
**Other writers to this file:** none — this ticket file is scoped to this ticket only; no
concurrent session should be editing it.
**Do NOT touch:** `## Scope`, `## Out of Scope`, `## Acceptance Criteria`, `## Related Tickets` —
already correct from ticket creation, not implementation output.
**Verify:** Re-read confirms every acceptance criterion checkbox in `## Acceptance Criteria` can be
checked off against what Steps 1-7 actually produced (see Acceptance Criteria Map below).

### Step 9 — Run the remaining scoped regression suite from test_plan.md
**Files:** None changed. Test execution only.
**Change:** Run the remaining commands from test_plan.md's "Scoped Pytest Commands" not already
covered by Step 4:
```
pytest tests/integration/test_world_profile_feature_flag_guardrail.py -q
pytest tests/unit/config/test_phase10_feature_flags.py \
  tests/integration/test_scenario_feature_flag_defaults.py \
  tests/certification/test_phase10_enhanced_determinism_parity.py -q
pytest tests/integration/scenarios/test_balance_regression.py -k adventure_routing_defaults_off -q
pytest tests/unit/worldassembly/test_corpus_diversity.py -k unit_selfmodel_pilot -q
pytest tests/unit/optimization/test_component_patches.py -q
```
This confirms the `urban_political` T5 exception (guardrail test) still holds, all three
`_DELIBERATE_ON_DEFAULT_FLAGS` allowlist copies still reject `ENABLE_SELF_MODEL_COGNITION` as
ON-default (Step 5/7 do not add it under the expected "keep OFF" outcome),
`ENABLE_ADVENTURE_ROUTING`'s own default-OFF sentinel still holds, and the shipped-ON
`unit_selfmodel_pilot` world's population stability is unaffected by this ticket's work.
**Do NOT touch:** No test file is modified by this step. If any test fails for a reason unrelated
to `ENABLE_SELF_MODEL_COGNITION` (e.g. a concurrent session's work), that is a signal to
investigate separately, not something this ticket absorbs (test_plan.md's own Anti-Drift Test
Guards).
**Verify:** All five invocations pass with counts matching or exceeding investigation.md's own
already-confirmed baselines (67 passed for the guardrail file).

## Scope Guards
- Do not change `src/domains/optimization/feature_flags.py`'s `ENABLE_SELF_MODEL_COGNITION` default
  (`FeatureMode.OFF`, line 19). This ticket's job is evidence, not the flip itself.
- Do not add `ENABLE_SELF_MODEL_COGNITION` to any `_DELIBERATE_ON_DEFAULT_FLAGS` allowlist copy
  (`tests/unit/config/test_phase10_feature_flags.py`,
  `tests/integration/test_scenario_feature_flag_defaults.py`,
  `tests/certification/test_phase10_enhanced_determinism_parity.py`) under any outcome of this
  ticket — that only happens in a future, separate flip ticket.
- Do not create or edit any `config/simulation_quality/profiles/*.yaml` file to make
  `urban_political` (or any other archetype world) ship the flag ON by default — that would
  fabricate the "shipped production evidence" this ticket exists to honestly assess, not find.
- Do not touch `urban_political`'s own `INFRA-259`/`INFRA-260` exception in
  `tests/simulation_quality/fixtures/expected_world_flag_state.json`'s `known_exceptions` block —
  nothing in this plan's steps requires resolving it, per this ticket's Out of Scope.
- Do not edit `src/cognition/self_model_phase.py`, `src/domains/information/` (`InformationBeliefPhase`,
  `InformationIntentExecutionPhase`), or `src/ai/goals/adventure_scorer.py` — this ticket
  re-validates existing behavior via corpus trial and static analysis, it never edits it.
- Do not schedule or attempt an empirical `ENABLE_SELF_MODEL_COGNITION` + `ENABLE_ADVENTURE_ROUTING`
  combination trial — Step 5's static resolution + new guard test already closes AC2; a trial
  cannot produce a different answer since no runtime path exists for the two flags to interact.
- Do not add a `docs/guidelines/intentional_divergences.md` entry unless Step 7's real evidence
  drives a flip recommendation — do not add one speculatively either way.
- Do not fix any new bug the trial might surface (e.g. a genuine new anchor-band regression)
  inline — disclose it in Step 6/7's writeup and this ticket's Completion Summary as a new finding
  requiring a separate ticket.
- Leave `data/runs/*` and `data/calibration/*` trial output in place until the ticket's normal
  Finalize cleanup step — do not clean up mid-ticket, since Steps 3-7 need to read that output.

## Dependency Map
- Step 1 and Step 2 are independent of each other (different profiles, same world) and can run in
  either order or in parallel.
- Step 3 depends on both Step 1 and Step 2 completing (needs both runs' `quality_report.json`).
- Step 4 depends on both Step 1 and Step 2 (the grade-anchor tests read the same calibration output
  paths those steps produce).
- Step 5 is independent of Steps 1-4 (pure static analysis + a new self-contained test) — can run
  any time, including before Step 1.
- Step 6 depends on Step 3 (needs the real evidence tally) and, for its AC2 summary, on Step 5.
- Step 7 depends on Step 5 (AC2 resolution) and Step 6 (references the trial_evidence.md file it
  summarizes) — write Step 7 after Step 6, not in parallel, to avoid duplicating numbers that could
  drift out of sync between the two files.
- Step 8 depends on Step 7 (the ticket's Completion Summary references the doc section Step 7
  wrote).
- Step 9 is independent of Steps 1-8 (it exercises pre-existing tests, not this ticket's own
  output) but is listed last as the final gate before the ticket can be considered complete.

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| A real corpus-profile ON trial is run and documented | Steps 1, 2, 3, 4, 6, 7 | `pytest tests/simulation_quality/test_grade_regression.py -k selfmodel -q` (Step 4) shows the 2 grade-anchor tests passing, not skipped; doc/trial_evidence.md content re-read against Step 3's real numbers |
| The `ENABLE_SELF_MODEL_COGNITION` + `ENABLE_ADVENTURE_ROUTING` combination question is resolved, not left open again | Step 5, documented in Step 7 | `pytest tests/architecture/test_adventure_routing_flag_inert.py -q` (new guard test, 1 passed) |
| A keep/flip recommendation with evidence is produced | Step 7 | No pytest — verified by re-reading the doc section against Steps 3-5's real tally; recommendation must cite the DEV-003 shipped-profile-absence check as its basis |

## Anti-Drift Notes
- **The existing prior evidence (shipped-ON Unit-tier world, two grade-anchor probes, INFRA-266's
  generalization trial) is real and citable, but it is not this ticket's own new finding** — cite
  it, and layer this ticket's fresh Step 1-4 run on top of it as additional confirming evidence, do
  not re-present the historical numbers as newly discovered.
- **A grade-anchor match is a "reproduces baseline" signal, not a "generalizes to a new corpus"
  signal** — both probe profiles are still `urban_political`-only; this ticket's fresh run does not
  test a different archetype world, and Step 7's writeup must not overstate the recommendation's
  evidentiary strength beyond what was actually run.
- **The execution probe's `INFORMATION` grade is anchored `B`, not `C`/`0`, despite its own
  docstring describing "0 `ActionIntentAdapter` traces"** — these are two different metrics (pillar
  event/score vs. adapter trace count); report both honestly in Step 3/6/7's writeup rather than
  reconciling or picking one number to match a narrative.
- **AC2's resolution rests entirely on `ENABLE_ADVENTURE_ROUTING` having zero live gating call
  sites today** — if `test_adventure_routing_defaults_off` (Step 9) or the new Step 5 guard test
  ever fails in a future session, that is the signal AC2's "resolved" status needs re-examination,
  not something to silently patch around.
- **Do not conflate this ticket with fixing or extending `SelfModelUpdatePhase`/
  `KnowledgeModelService`/`InformationBeliefPhase`** — Out of Scope excludes flipping the flag's
  default and resolving `urban_political`'s `INFRA-259`/`INFRA-260` exception; a fresh confirming
  trial reproducing already-known results does not, by itself, require resolving that exception.
- **Three independently-maintained copies of `_DELIBERATE_ON_DEFAULT_FLAGS` exist** — Step 9 running
  all three test files is intentional redundancy checking all three copies stay consistent, not a
  mistake to dedupe here.
- **Clean up `data/runs/*`/`data/calibration/*` trial output at Finalize**, per Definition of Done —
  same as the combat-engagement sibling's own precedent.

## Deviations

- **Step 4's stated expectation did not hold: the 2 grade-anchor tests un-skipped and ran, but
  FAILED rather than passed.** `test_urban_political_selfmodel_cognition_isolated_grade_anchor`
  failed a hard `assert pillars["INFORMATION"]["grade"] == "C"` (actual: `B`, `event_count=1` not
  `0`). `test_urban_political_selfmodel_execution_isolated_grade_anchor` failed its score-tolerance
  check on `SOCIAL` (no existing `known ceiling` classification covers it) plus 3 other pillars
  that do carry an existing, pre-existing `known tick_budget` classification. This is disclosed
  fully in `trial_evidence.md`'s Honest Gap section and in the new
  `rollout_flag_decisions_m1.md` section — not silently smoothed over, and not fixed inline
  (no edit to `grade_anchors.json` or `self_model_phase.py`), per Scope Guards and this ticket's
  own Anti-Drift Notes anticipating exactly this possibility. The recommendation itself (Keep OFF,
  deferred) is unchanged by this finding, since the DEV-003 shipped-profile bar was already unmet
  independent of anchor cleanliness — but a separate follow-up ticket is now needed to re-anchor
  or investigate `INFORMATION`/`SOCIAL` for these two run keys.
- **Step 9's `test_component_patches.py` path was wrong in the plan**: it specified
  `tests/unit/optimization/test_component_patches.py`, which does not exist. The real path is
  `tests/unit/domains/optimization/test_component_patches.py` (confirmed via `find tests
  -iname "*component_patch*"`). Ran the correct path: **10 passed**.
- **Step 9's `test_corpus_diversity.py -k unit_selfmodel_pilot` did not cleanly pass**: 1 of 3
  matched tests (`test_unit_selfmodel_pilot_seed42_1000t_cognition_economy_narrative_grade_stability`)
  failed both on first run and on a retry with a `tools.calibrate_simq.CalibrationIntegrityError`
  (`pressure_mode_final=PRESSURE`, watchdog/tick-budget throttling under this environment's load —
  `persistence` phase cost dominates, matching the same pre-existing, already-disclosed condition
  the combat-engagement sibling's own trial noted). This is a real 1000-tick load-sensitivity class
  the test's own docstring already documents (`TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP`),
  unrelated to `ENABLE_SELF_MODEL_COGNITION` or this ticket's own 200-tick trial (Steps 1-2, which
  completed without any `CalibrationIntegrityError`). Not investigated or fixed further, per
  Step 9's own guard: "If any test fails for a reason unrelated to `ENABLE_SELF_MODEL_COGNITION`...
  that is a signal to investigate separately, not something this ticket absorbs." The other 2
  matched tests in that file passed.

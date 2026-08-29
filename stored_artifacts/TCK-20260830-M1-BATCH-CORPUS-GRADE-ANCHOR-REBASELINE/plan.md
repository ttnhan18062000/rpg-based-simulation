---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE
artifact_type: plan
tags: [simulation-quality, grade-thresholds, calibration]
---

# Plan — TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE

## Ordered Steps

1. **Freeze the evidence snapshot.** Do not re-run `tools/evaluate_simq.py` again. Use the
   `data/calibration/*/quality_report.json` snapshot already produced (the same one
   `investigation.md`'s evidence table was built from) as the sole source for new anchor values.
   Files: none changed (verification-only step).

2. **Write the anchor update programmatically, not by hand-editing 210 individual JSON values.**
   Use a small one-off script (not a durable `tools/` addition — this is a single-use write,
   mirroring how `tools/parity_ledger_writer.py` is the sanctioned mechanism for parity YAML
   full-file rewrites but grade_anchors.json has no equivalent existing writer script) that:
   - Loads `tests/simulation_quality/fixtures/grade_anchors.json`.
   - For each of the 210 `(run_key, pillar)` combos investigation.md classifies as "known-*" or
     "M1-batch drift" (i.e. every failing combo except `highland_traverse_seed42_200t`/SOCIAL),
     overwrite that entry's `{grade, score}` with the fresh `actual_grade`/`actual_score` from
     `quality_report.json`.
   - Leaves every other entry — including all entries for the 2 selfmodel-probe run_keys, all
     passing pillars, and `highland_traverse_seed42_200t`'s SOCIAL entry — byte-for-byte
     untouched.
   - Writes the result back preserving the file's existing key order and JSON formatting style
     (2-space indent, matching the current file) so the diff is minimal and reviewable.
   Files: `tests/simulation_quality/fixtures/grade_anchors.json`.

3. **Verify the diff is exactly the expected 210-entry set** — `git diff --stat` and a structural
   check (parse both old and new JSON, diff key-by-key, assert the changed-key set equals the
   210-combo set from investigation.md, assert the 2 selfmodel-probe run_keys show zero diff).
   Files: none changed (verification-only step).

4. **Re-run the fast-tier suite** (`pytest tests/simulation_quality/test_grade_regression.py -m
   "not slow" -q`) and confirm the only remaining failure is
   `test_grade_within_anchor_band[highland_traverse_seed42_200t]`. If any other failure appears,
   stop — do not force-fit it into this ticket's scope (Gate Integrity).
   Files: none changed (verification-only step).

5. **Append a worked-example section to `docs/testing/regression_policy.md`** documenting this
   re-baseline (per investigation.md's Docs Requiring Update section) — dominant SOCIAL/COGNITION
   driver, the PROGRESSION 200t/500t sign-flip nuance, and the one disclosed
   `highland_traverse_seed42_200t` cooperation-cooldown finding left un-fixed. This is the
   Document-Update phase's job, not Implement's — listed here only for step-ordering visibility.
   Files: `docs/testing/regression_policy.md` (Document-Update phase, not this step).

6. **Update the ticket's own body** (`Implementation Notes`, `Test Summary`, `Files Changed`,
   `Completion Summary`) with the final numbers and the disclosed finding, matching the
   Implement-phase agent's standard responsibility.

## Files to Change

- `tests/simulation_quality/fixtures/grade_anchors.json` (210 of 211 failing entries updated;
  `highland_traverse_seed42_200t`/SOCIAL and both selfmodel-probe run_keys explicitly excluded)
- `docs/testing/regression_policy.md` (new worked-example section — Document-Update phase)
- `tickets/inprogress/TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE.md` (Implementation
  Notes / Completion Summary)

## Explicit Scope Guards (what NOT to touch)

- Do NOT modify any code under `src/domains/cooperation/` to add a cooldown/backoff — the
  `highland_traverse_seed42_200t` finding is disclosed only, per the ticket's explicit
  instruction. A follow-up ticket is the correct vehicle for that fix.
- Do NOT modify any feature flag default in `src/domains/optimization/feature_flags.py`.
- Do NOT modify `tools/simq_ceiling.py`'s ceiling tables — the 118 `tick_budget` / 9 `flag_gated`
  / 3 `watchdog_variance` / 1 `corrected` classifications used in this ticket's analysis are all
  pre-existing entries, read-only inputs to this ticket.
- Do NOT touch `urban_political_selfmodel_probe_seed42_200t` or
  `urban_political_selfmodel_execution_probe_seed42_200t` anchor entries — out of scope, owned by
  `TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION`.
- Do NOT re-baseline `highland_traverse_seed42_200t`'s SOCIAL entry — leave it failing, disclosed.
- Do NOT touch `SLOW_ANCHOR_KEYS` entries (1000t/2000t) — explicitly out of scope per the ticket.

## Dependency Map

Step 1 → Step 2 → Step 3 → Step 4 (hard sequential; each step's output gates the next). Step 5 and
Step 6 are independent of each other and can happen in either order after Step 4 passes, but both
must complete before Verify.

## Acceptance Criteria → Step Mapping

- "`test_grade_regression.py -m 'not slow'` passes clean or remaining failure is disclosed" → Step
  4 (verification) + investigation.md's existing disclosure (already written).
- "diff touches only the run_keys this ticket's investigation named" → Step 2 (mechanical
  constraint) + Step 3 (verification).
- "loop_detected cases and PROGRESSION sign-flip explicitly written up" → already satisfied by
  investigation.md (Investigate phase, already complete).

## Unresolved Questions

None. All classification decisions were resolved during Investigate with direct evidence (see
investigation.md) — no open question requires human input before implementation.

## Deviations

**Step 4**: the plan states the fast-tier suite's only remaining failure after the anchor update
would be `test_grade_within_anchor_band[highland_traverse_seed42_200t]`. In practice, **3** tests
fail, not 1: that one, plus `test_urban_political_selfmodel_cognition_isolated_grade_anchor` and
`test_urban_political_selfmodel_execution_isolated_grade_anchor`. Both extra failures are dedicated
test functions (not `FAST_ANCHOR_KEYS` parametrized cases), structurally unreachable from this
ticket's anchor-writing loop, and were confirmed via `git stash` to already fail identically
**before** this ticket's diff — i.e. genuinely pre-existing, not a new regression caused by this
re-baseline. They are already covered by `TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-
INVESTIGATION`, per this same plan's and the ticket's own Out-of-Scope sections. The plan's Step 4
wording appears to have been written assuming only `FAST_ANCHOR_KEYS`-parametrized failures would
appear in the run; it did not account for the 2 non-parametrized dedicated test functions that
collection also picks up under `-m "not slow"`. This does not change any acceptance criterion's
outcome — the ticket's actual Acceptance Criteria text allows "any remaining failure [that] is
independently new and disclosed as its own finding," and both extra failures are independently
pre-existing and already disclosed/tracked, not new. No anchor value or code was force-fit to
route around this; it is recorded here per the Gate Integrity rule instead.

---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261023-RPG-GATE-CANDIDATE-RECORDS-ITS-CI-RUN-AND-KNOWN-FILE
phase: done
date: 2026-10-23
tags: [testing]
---

# TCK-20261023-RPG-GATE-CANDIDATE-RECORDS-ITS-CI-RUN-AND-KNOWN-FILE

## Title
The rpg gate candidate records the CI run it came from and the known-reds file it was judged against, and `rebaseline()` refuses a candidate with no CI run

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Found independently by rpg-planner and lead-planner-u24 (2026-10-23, after the v1 record #725).

`rpg_gate_candidate.build_candidate` writes `provenance: {commit_sha, harness_hash, worlds, seeds, ticks}` (rpg_gate_candidate.py ~line 324). It records neither which `rpg_gate_known.yaml` decided the omitted (owned) validity rows nor which CI run produced the documents. `rebaseline()` (rpg_gate_baseline.py ~line 520) refuses only `evidence_only` candidates (branch-ref dispatches). So someone could take a main run's `rpg-gate-docs-*`, add a later or edited known file, build a candidate offline, and it would pass `rebaseline()` leaving no trace. #725's candidate has the gap; its PR body cites the run id by hand. v1 took the clean path (entries committed, then re-dispatched on main), so v1 itself is not in question and is not changed here.

## Scope
1. `build_candidate` adds to `provenance`:
   - `known_file_sha256`: the sha256 of the exact bytes of the `--known` file it loaded;
   - `ci`: `{run_id, run_attempt, event_name, ref}`, read from `GITHUB_RUN_ID`, `GITHUB_RUN_ATTEMPT`, `GITHUB_EVENT_NAME` and `GITHUB_REF`.

   When `GITHUB_RUN_ID` is unset (a local build), `ci` is `null`, never a guessed value.
2. `rebaseline()` refuses a candidate whose `provenance.ci` is null or missing, or whose `ci.ref` is not `refs/heads/main`. It keeps refusing `evidence_only`. The message says to re-dispatch the gate on main. There is no override flag.
3. The baseline file carries both fields into its provenance. `_lint_provenance` requires them for version >= 2. Version 1 (`rpg_gate_v1.json`) is exempt by version number, because it predates the rule. Don't edit v1 to add them.
4. The workflow (`rpg-gate-report.yml`) needs no change if the aggregate job builds the candidate, because the GitHub env vars are already set there. Confirm this, and say so in investigation.md.
5. Docs: `docs/plans/test_architecture/reference/rpg_gate_baseline_format.md`, "Candidate and recording", states both fields and the refusal.

## Out of Scope
- Re-recording or editing v1.
- Verifying the run id against the GitHub API (a network call in rebaseline). The recorded id is evidence for review, not a cryptographic check. File it separately if it's ever wanted.
- The harness cost data: per-run `wall_seconds` and `peak_rss_mb` are already in `matrix.json` and `*.cost.json` in the gate-docs artifacts (checked on run 39799337778).

## Acceptance Criteria
- [x] AC1: a candidate built with the GitHub env vars set carries `known_file_sha256` (equal to `sha256sum` of the file) and `ci` with all four fields. Built without them, `ci` is null.
- [x] AC2: `rebaseline()` refuses a candidate with `ci` null or missing, and one whose `ci.ref` is a branch other than main. It accepts one with `ci.ref == refs/heads/main`. Each case has a test, and the evidence_only refusal still holds.
- [x] AC3: the baseline lint requires both fields for version >= 2 and passes `rpg_gate_v1.json` unchanged.
- [x] AC4: the format doc states the rule, and the `rpg_gate_candidate.py` / `rpg_gate_baseline.py` docstrings match.
- [x] AC5: the tests in `tests/unit/tools/` for the candidate and the baseline pass, and no existing assertion is weakened.

## Related Tickets
- TCK-20261011-RPG-GATE-BASELINE-CANDIDATE-FROM-HARNESS-DOCS (the candidate)
- TCK-20261019-RECORD-BASELINE-V1 (#725)
- TCK-20261022-RPG-GATE-KNOWN-ENTRY-CAN-NAME-A-WORLD-AND-SEED (changes what the known file can say, which makes its hash matter more)

## Related Docs
- docs/plans/test_architecture/reference/rpg_gate_baseline_format.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/test_architecture/rpg_gate_candidate.py
- tools/test_architecture/rpg_gate_baseline.py
- .github/workflows/rpg-gate-report.yml (read-only unless Scope 4 finds otherwise)

## Assumptions / Open Questions
- The candidate is built in a GitHub Actions job (aggregate) on the main run. If it turns out to be built locally from downloaded docs, stop and tell testing-planner: the design then needs the run id passed explicitly, still never guessed.

## Implementation Notes
See investigation.md / plan.md in stored_artifacts. Scope 4 confirmed: the candidate is built in the aggregate job of rpg-gate-report.yml where the GITHUB_* variables are set, so the workflow is unchanged. Decisions flagged for review: ci is null unless all four variables are set; known_file_sha256 is a required keyword; the lint also checks the hash shape and ci.ref == refs/heads/main; the refusal applies to version 1 too (v1 already exists, untouched).

## Test Summary
tests/unit/tools/test_rpg_gate_{baseline,candidate,report,workflow_support,harness}.py + tests/static: 375 passed. New tests: 11 groups across the candidate and baseline files (see test_plan.md). Two existing assertions were extended (provenance equality, candidate fixture); none removed or weakened.

## Files Changed
- tools/test_architecture/rpg_gate_candidate.py
- tools/test_architecture/rpg_gate_baseline.py
- docs/plans/test_architecture/reference/rpg_gate_baseline_format.md
- tests/unit/tools/test_rpg_gate_candidate.py
- tests/unit/tools/test_rpg_gate_baseline.py

## Completion Summary
The candidate records known_file_sha256 and the CI run; rebaseline() refuses a candidate with no CI run or a run off main (no override); the lint requires both fields from version 2; v1 unchanged. No workflow change.

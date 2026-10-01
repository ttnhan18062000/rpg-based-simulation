---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION
phase: open
date: 2026-09-29
tags: [testing]
---

# TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION

## Title
Epic B — Test structure and selection: level conventions and metadata, scenario tests on relevant PRs, and a first impact report

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary

Agents can't tell which test level, harness or placement fits a change, or which tests and lanes a
change affects:

- `docs/testing/test_taxonomy.md` describes legacy-parity markers, several of them unused (0 uses of
  `legacy_characterization` and `intentional_divergence`);
- no test declares a domain or level;
- mechanic scenario tests are skipped on PRs that touch only several core-RPG paths (`PERF_RE` in
  `.github/workflows/test.yml`);
- test selection relies on per-ticket agent grep.

Roadmap: `docs/plans/test_architecture/roadmap.md` §3.

## Scope

**Decision record (2026-09-30).** D-R2 is approved with changes (roadmap §11); its HOLD is lifted. Approval does not close this epic: part 2 is in progress and criterion 4 is open.

1. **Conventions** (ungated):
   - rewrite `docs/testing/test_taxonomy.md` **in place** with level contracts, technique criteria,
     evidence classification, placement and the oracle principle (keeping its valid worldassembly
     and performance sections);
   - register domain/level metadata markers with an **advisory** consistency check, required for
     new or modified core-RPG tests;
   - shared scenario helper;
   - worked examples that are **synthetic or confirmed stable** with the feature team;
   - replay-diff helper limited to the **verified reproducibility envelope** (hand-built state, fixed
     seed, ≤ 10 ticks, the determinism-suite profile).
2. **Scenario-lane CI rule** (D-R2, approved with changes; in progress): the lane triggers on `src/**`, known scenario
   dependencies and `tests/mechanic_scenarios/**` (the old `PERF_RE` omitted the last, so a scenario-test-only PR ran
   no scenario test). Unknown/new paths run the lane and are named in the job summary; known-irrelevant paths are
   listed with evidence. Dedicated job, **not required** (`main` has no branch protection, so that is by convention),
   and it never double-runs what `perf-cert-arena` already runs. Lane cost is measured before any further rule change.
3. **Impact report v0** (ungated): changed paths → components/domains → recommended levels, tests and lanes,
   with reasons and an explicit `impact-unknown` list. It **never removes a lane**. It reports
   selected / triggered / executed separately.

## Out of Scope

- Feature-specific proof commitments.
- Bulk classification of existing tests beyond advisory proposals.
- Seeded-fault evaluation and per-test coverage contexts (deferred to their triggers).
- Mapping party (deferred, D-P).
- Any use of the impact report to skip tests.

## Acceptance Criteria

1. The taxonomy doc answers "which level and harness, and how is it reported" for every level. All
   existing links to `docs/testing/test_taxonomy.md` still resolve.
2. A newly marked test is located and classified by Epic A's report. A deliberately mismatched
   marker is flagged by the advisory check.
3. Each worked example runs green in its declared lane and is labelled synthetic or
   confirmed-stable. The replay-diff helper returns `outside-verified-scope` for inputs outside the
   envelope.
4. **Open** (job implemented; the ~10-PR cost record has not started). A PR touching only `src/progression/**` runs the scenario tests. A docs-only PR
   does not. An unknown path runs them and appears in the job summary. Lane wall time is recorded for
   the first ~10 relevant PRs. The measured cost is shared with the feature teams before any rule promotion.
5. The impact report, run on sample changes (local rule, shared substrate, cross-domain,
   content/config, unmapped), gives the expected domains and lanes with reasons, and flags the
   unmapped sample as `impact-unknown`.

## Related Tickets
- Child: `TCK-20260930-IMPACT-REPORT-ECONOMY-CORE-OWNERSHIP-AND-DECLARED-MARKERS` (impact report fixes found by the pilot, done).
- Depends on Epic A (report v0) for criterion 2.
- Feeds Epics C and D.

## Related Docs
- `docs/plans/test_architecture/roadmap.md`
- `docs/plans/test_architecture/reference/architecture_design_notes.md` §3–4 (non-binding)
- `docs/plans/test_architecture/reference/milestone_design_notes.md` (MT, R2, M1; non-binding)

## Related Stored Artifacts
None.

## Related Code Areas
`docs/testing/`; `pyproject.toml` (markers); `tests/helpers/`; `tests/mechanic_scenarios/`;
`.github/workflows/test.yml` (gated part only).

## Assumptions / Open Questions
- **D-R2 approved (2026-09-30):** part 2 is in progress; criterion 4 stays open until CI has actually run the lane on real PRs and the cost is recorded and shared.

## Implementation Notes
**Progress (2026-09-30):** parts 1 and 3 are DONE via child tickets `TCK-20260930-TEST-TAXONOMY-LEVEL-CONTRACTS`, `TCK-20260930-TEST-DOMAIN-LEVEL-MARKERS-ADVISORY-CHECK`, `TCK-20260930-TEST-SCENARIO-HELPER-AND-REPLAY-DIFF`, `TCK-20260930-TEST-IMPACT-REPORT-V0` (acceptance criteria 1, 2, 3, 5). Part 2 (scenario-lane job, `tools/test_architecture/scenario_lane_paths.py`) is **in progress in the 2026-09-30 decisions batch**: implemented and locally tested, **not yet run in CI**. Criterion 4 is **open, half observed (2026-10-01)**: PR #271 (a `tests/`-and-`docs/`-only change that fails open into the lane and does not match `PERF_RE`) ran the `Scenario lane` job for the first time: it ran once, succeeded, and `Perf / cert / arena` was skipped (job time 51 s). The `src/progression/**`-only trigger and the docs-only skip are still unobserved, and the lane cost has one datapoint. Earlier note: PR #267 itself matched `PERF_RE` (it edits `test.yml`), so the dedicated job was skipped and its own steps (wall-time arithmetic, summary) have not run in CI. Criterion 4 closes only when a real PR whose paths hit `run_scenario_lane` but not `PERF_RE` (for example `src/progression/**` only) shows the lane running, and a docs-only PR shows it skipped; that first PR is also the first cost datapoint. This epic stays open in `todos/`.
**Gap flagged:** "tactical navigation" has no code root; the impact report lists such paths as `impact-unknown` and invents none.

Scenario-lane cost is assumed at 1–3 min per relevant PR; measured under criterion 4.

## Test Summary
Defined by child tickets.

## Files Changed
(Child tickets.)

## Completion Summary
(Open.)

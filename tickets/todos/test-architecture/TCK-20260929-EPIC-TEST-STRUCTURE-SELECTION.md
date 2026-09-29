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

1. **Conventions:**
   - rewrite `docs/testing/test_taxonomy.md` **in place** with level contracts, technique criteria,
     evidence classification, placement and the oracle principle (keeping its valid worldassembly
     and performance sections);
   - register domain/level metadata markers with an **advisory** consistency check, required for
     new or modified core-RPG tests;
   - shared scenario helper;
   - worked examples that are **synthetic or confirmed stable** with the feature team;
   - replay-diff helper limited to the **verified reproducibility envelope** (hand-built state, fixed
     seed, ≤ 10 ticks, the determinism-suite profile).
2. **Scenario-lane CI rule — gated by D-R2 (only this part):** scenario tests run on relevant PRs;
   unknown/new paths run the lane and are named in the job summary; lane cost is measured before any
   further rule change.
3. **Impact report v0:** changed paths → components/domains → recommended levels, tests and lanes,
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
4. **(After D-R2)** A PR touching only `src/progression/**` runs the scenario tests. A docs-only PR
   does not. An unknown path runs them and appears in the job summary. Lane wall time is recorded for
   the first ~10 relevant PRs.
5. The impact report, run on sample changes (local rule, shared substrate, cross-domain,
   content/config, unmapped), gives the expected domains and lanes with reasons, and flags the
   unmapped sample as `impact-unknown`.

## Related Tickets
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
- **D-R2 pending:** parts 1 and 3 proceed without it.

## Implementation Notes
Scenario-lane cost is assumed at 1–3 min per relevant PR; measured under criterion 4.

## Test Summary
Defined by child tickets.

## Files Changed
(Child tickets.)

## Completion Summary
(Open.)

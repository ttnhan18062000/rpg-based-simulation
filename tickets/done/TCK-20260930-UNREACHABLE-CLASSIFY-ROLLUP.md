---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260930-UNREACHABLE-CLASSIFY-ROLLUP
phase: done
date: 2026-09-30
tags: [investigation, root-cause, corpus]
---

# TCK-20260930-UNREACHABLE-CLASSIFY-ROLLUP

## Title
Roll up the unreachable-mechanism classification: the shared verdict document, the ranked fix order for the `DEFECT` subset,
the `CONDITION` owner split, and the named follow-ups

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Child `T06` of `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION`. Its prerequisites, `T01`-`T05`, are all closed, so every
one of the 14 corpus tickets now carries a verdict in its own body. This ticket produces the epic's remaining deliverables:
the shared classification document (Deliverable 1), a ranked fix order for the `DEFECT` subset only (Deliverable 3), the
split of the `CONDITION` set by owner and the run-length-versus-content statement (Deliverable 4 / AC-6), and the deferred
corrections written down as named, owned follow-ups. It also states prominently that every kernel measurement in the epic was one
world and one seed.

## Scope
- Write `docs/plans/unreachable_mechanism_classification.md`: verdict and evidence for all 14, with the strength of each kind of
  evidence stated up front.
- Rank the four `DEFECT`s without forcing unlike fixes onto one list.
- Split the `CONDITION` set by owner; recommend where the run-length side belongs and leave that call to its owner.
- List each deferred correction (docs, registry entries, one priority) with a proposed owner; do not make any of them.
- Report the registry-verdict staleness process finding to `agent-working-design` by message.

## Out of Scope
- Fixing any `DEFECT`, choosing among the `UNDECLARED` options, or correcting any doc, parity entry, registry entry or priority.
- Editing `registries/mechanisms.yaml` (byte-for-byte unchanged against `origin/main` across the epic).
- Creating follow-up tickets, pushing, or opening a PR.

## Acceptance Criteria
1. The document carries one verdict and its evidence for each of the 14 tickets, with the single-world/single-seed limit stated in
   the first section, not as a footnote. (Epic AC 1-3.)
2. The `DEFECT` subset is ranked, and the ranking says which fixes need a design call before code. (Epic Deliverable 3.)
3. The `CONDITION` set is split into world content versus corpus run length, each with a proposed owner. (Epic AC 6.)
4. The deferred corrections are listed as owned follow-ups and none is made.
5. `registries/mechanisms.yaml` unchanged and no `src/`/`tests/` change, verified against `origin/main`. (Epic AC 4-5.)

## Related Tickets
- `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION` — parent epic; this is its `T06`.
- `TCK-20260929-UNREACHABLE-CLASSIFY-ZERO-CALLER`, `TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED`,
  `TCK-20260929-UNREACHABLE-CLASSIFY-DEAD-GUARD`, `TCK-20260929-UNREACHABLE-CLASSIFY-WAVE-CONFIRM`,
  `TCK-20260930-UNREACHABLE-CLASSIFY-PERCEPTION-AUTHORITY` — the prerequisite passes (all done).
- `TCK-20260915-SIMQ-CORPUS-BLIND-TO-SCALE-DEPENDENT-BEHAVIOR` — proposed owner of the run-length side.
- `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION` — adjacent (owns registry `implemented_by` residue), not merged.

## Related Docs
- `docs/plans/unreachable_mechanism_classification.md` — the deliverable (new).
- `docs/plans/world_composition_precondition_gap_finding.md` — the pattern document this corpus was grouped from; flagged, not edited.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260928-EPIC-SYSTEMIC-WORLD-FIRST-WAVE/` — method precedent.
- `stored_artifacts/TCK-20260930-UNREACHABLE-CLASSIFY-ROLLUP/` — this ticket's own `investigation.md`/`plan.md`/`test_plan.md`, migrated at closure.

## Related Code Areas
None — no code is touched.

## Assumptions / Open Questions
- Open, for the owners: every follow-up in the document's F1-F6 table.

## Implementation Notes

Produced `docs/plans/unreachable_mechanism_classification.md` (the epic's Deliverable 1). Contents: a leading section on what the verdicts do and do not establish (one world, one seed, with the evidence kinds separated by how much a single sample can prove); the 14-row verdict table; five premises that turned out wrong or incomplete; the `DEFECT` fix order in two tracks; the `CONDITION` owner split; the `UNDECLARED` decisions; follow-ups F1-F6; AC status.

Final tally: `DEFECT` 4, `UNDECLARED` 5, `CONDITION` 2, `STALE-PREMISE` 2, `NO-MECHANISM` 1, `MISLABEL` 0.

Judgement calls, stated in the document so they can be overruled:
- The influence defect ranks first among the `DEFECT`s but is **not** described as a one-line fix: it would make dynamic conquest fire for the first time in every world and carries an open design question, so it ranks first to be decided and needs a SimQ re-baseline afterwards.
- `CALAMITY-INTENSITY` and `REGION-DANGER-SEEN` are not ranked against each other or against Track A: each needs a wire-or-delete design call first.
- The run-length `CONDITION` is recommended to belong with the SimQ corpus ticket (a finding about the corpus, not the code); left to that ticket's owner to accept.
- Follow-up F5 recommends lowering the capacity ticket's `P1` to `P2` with the single-sample limit stated; the priority itself is not changed.

The process finding was sent to `agent-working-design`, who corrected its framing: the two registry verdicts were wrong when written (`instrument: code_trace` verdicts asserting runtime world-data absence), not stale, so a date-versus-code check would not have caught them; they filed `TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE`.

## Test Summary

No repo test suite authored or run. Verified the new document with `validate_frontmatter.py`, checked the ticket IDs it cites against the tree, and diffed `registries/mechanisms.yaml` and `src/tests/registries` against `origin/main` (empty).

## Files Changed

No `src/`/`tests/`/registry/parity change; `registries/mechanisms.yaml` unchanged against `origin/main`. Files touched:
- `docs/plans/unreachable_mechanism_classification.md` — new; the shared classification document.
- this ticket: created in and closed from `tickets/inprogress/` to `tickets/done/`; `stored_artifacts/TCK-20260930-UNREACHABLE-CLASSIFY-ROLLUP/` migrated from `staging_artifacts/`.
- `docs/REGISTRY.yaml` — regenerated by Finalize's self-check, not hand-edited.

## Completion Summary
The epic's remaining deliverables are done: the shared classification document exists with the single-world/single-seed limit stated first; the four `DEFECT`s are ranked in two tracks; the `CONDITION` set is split by owner; the deferred corrections are named F1-F6 with proposed owners, and none was made. Not done, on purpose: fixing anything; choosing among the `UNDECLARED` options (five need a person); correcting F1-F4; changing any priority; creating follow-up tickets; pushing or opening a PR. F1 is blocked on the sovereignty-service decision. Whether a wired `PerceptionModel` would enter the state-hash surface was not checked.

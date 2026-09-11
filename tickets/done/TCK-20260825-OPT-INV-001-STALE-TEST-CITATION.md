---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260825-OPT-INV-001-STALE-TEST-CITATION
phase: done
date: 2026-08-25
tags: [performance, testing]
---

# TCK-20260825-OPT-INV-001-STALE-TEST-CITATION

## Title
`docs/performance/optimization_invariants.md`'s OPT-INV-001 cites a test file that doesn't exist

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
`docs/performance/optimization_invariants.md:55` (OPT-INV-001's "Test Citation") reads:
`tests/integration/optimization/test_static_dirtyset_guard.py` (Proves zero direct dirty set
references exist across all gameplay systems)" -- **this file does not exist anywhere in the
repo**, confirmed by two independent `find` checks during `TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE`'s
Plan and Verify phases (that ticket's own `_refresh_dirty_set`/OPT-INV-002 fix is unrelated to this
stale citation; it just happened to be discovered while reading the same doc file).

That ticket's Verify pass identified the real, current guard test for this exact invariant:
`tests/static/test_no_direct_dirtyset_candidate_selection.py`, delivered by the already-closed
`tickets/done/TCK-20260517-STATIC-DIRTYSET-GUARD.md`. The citation in `optimization_invariants.md`
appears to predate a later rename/relocation of that test file and was never updated.

## Scope
- Update `docs/performance/optimization_invariants.md:55`'s Test Citation to reference the real,
  current file: `tests/static/test_no_direct_dirtyset_candidate_selection.py`.
- Confirm that file's actual test function(s) genuinely prove OPT-INV-001's claim ("zero direct
  dirty set references exist across all gameplay systems") before citing it -- read the file, don't
  just trust the name.
- Grep `docs/` more broadly for any other reference to the now-confirmed-nonexistent
  `test_static_dirtyset_guard.py` filename, in case the stale citation exists in more than one
  place.

## Out of Scope
- Any change to `src/` -- this is a pure doc-accuracy fix, no behavior change.
- `TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE`'s own OPT-INV-002 changes -- already landed, unrelated
  invariant.

## Acceptance Criteria
- [x] `optimization_invariants.md:55`'s Test Citation references a file that genuinely exists
- [x] The cited file's actual test(s) verified to prove OPT-INV-001's stated claim
- [x] No other stale reference to the old filename remains anywhere in `docs/` that should be
      corrected -- one further hit exists (`docs/audits/D25_engine_docs_drift.md:305`), deliberately
      left untouched: see Implementation Notes.

## Related Tickets
- TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE (where this was discovered, flagged, and deliberately not
  fixed as out of that ticket's own scope)
- TCK-20260517-STATIC-DIRTYSET-GUARD (original ticket that delivered the real, current guard test)

## Related Docs
- docs/performance/optimization_invariants.md

## Related Stored Artifacts
None.

## Related Code Areas
- tests/static/test_no_direct_dirtyset_candidate_selection.py

## Assumptions / Open Questions
- Whether the file was ever actually named `test_static_dirtyset_guard.py` and later renamed, or
  whether the doc citation was simply wrong from the start -- not investigated, doesn't change the
  fix (point the citation at the real file either way).

## Implementation Notes

Repo-wide grep for `test_static_dirtyset_guard` found 6 hits total. Classified each:

1. `docs/performance/optimization_invariants.md:55` -- the live, authoritative citation. **Fixed**
   to `tests/static/test_no_direct_dirtyset_candidate_selection.py`.
2. `docs/audits/D25_engine_docs_drift.md:305` -- a "Dead citation(s)" finding row in a dated
   (2026-08-21), point-in-time audit report. This is the historical record of the audit having
   *already found* this exact citation dead 4 days before this ticket. Editing it would corrupt
   what the audit actually observed at the time -- **deliberately left untouched**, same convention
   as `audits/`/`archive/` being excluded from routine doc-updates project-wide. This also answers
   the ticket's own open question: the citation has been stale since at least the D25 audit, not
   something that broke recently.
3. `tickets/done/TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE.md:150`, `stored_artifacts/TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE/{plan.md,test_plan.md}` --
   closed-ticket/staging-artifact history for an already-finalized ticket. These are immutable
   records of what was actually planned/decided at the time (the plan explicitly says "flag, don't
   fix" for this exact citation) -- not live docs, left untouched.
4. This ticket's own body text (`tickets/todos/TCK-20260825-OPT-INV-001-STALE-TEST-CITATION.md`) --
   quotes the stale name as the subject being fixed; not a citation, no change needed.

Read `tests/static/test_no_direct_dirtyset_candidate_selection.py` in full before citing it: it
walks `src/engine/pipeline_phases`, `src/systems`, and `src/ai` for `.dirty_set`/`dirty_set.`
substring matches and asserts none exist -- this genuinely proves OPT-INV-001's Invariant Rule 1
("Gameplay systems, AI decision trees, and action resolvers are strictly prohibited from
referencing `state.dirty_set`"). Ran it standalone to confirm it currently passes (1 passed).

## Test Summary
`tests/static/test_no_direct_dirtyset_candidate_selection.py` -- 1/1 passing (the now-correctly-cited
guard test itself; unaffected by this doc-only change, run to confirm the citation points at a real,
green test). `tests/docs/test_doc_path_existence.py` + `tests/tools/test_add_frontmatter_live.py`
(the two suites referencing `optimization_invariants.md` by path) -- 108 passed, 1 xfailed, no drift.

## Files Changed
- `docs/performance/optimization_invariants.md` (OPT-INV-001's Test Citation line corrected)

`make knowledge-index-update` was attempted per the After-Work rule (a `docs/` file changed) but
fails in this sandbox on a pre-existing, unrelated environment gap: no HuggingFace connectivity for
the embedding model download (`OSError: We couldn't connect to 'https://huggingface.co'`), the same
gap already on file from prior sessions. Not caused by, or fixable within, this ticket's scope.

## Completion Summary
Fixed the one live, authoritative stale test citation (`optimization_invariants.md:55`) to point at
the real current guard test, verified by reading that test's actual logic rather than trusting the
name. Left 5 other hits of the same stale filename untouched -- all are historical/frozen records
(a dated audit report, a closed ticket and its staging artifacts) whose job is to document what was
true at the time, not to track current reality.

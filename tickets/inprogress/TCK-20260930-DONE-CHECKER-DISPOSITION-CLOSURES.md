---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260930-DONE-CHECKER-DISPOSITION-CLOSURES
phase: open
date: 2026-09-30
tags: [agent-monitoring, data-quality]
---

# TCK-20260930-DONE-CHECKER-DISPOSITION-CLOSURES

## Title
Tickets closed as a disposition (no implementation) can never pass done-checker; add an explicit, validated Disposition field

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Reported by rpg-feature-planning on 2026-09-30, and re-verified by that session on a branch that includes PR #261 (`64312b24c`, which contains origin/main `833b60306`). Two standard-tier tickets were closed as STALE-PREMISE at `791e6bf6b`: their premise was already false, so nothing was built. On post-#261 code, done_checker_static.py still FAILs one condition on both: `[finalize] migration_complete` ("Missing or empty file(s) in stored_artifacts/<id>: plan.md, investigation.md, test_plan.md"). A disposition produces no staging artifacts. The only ways through are fabricating artifacts (forbidden) or ignoring a FAIL, which trains readers to treat FAIL as noise.

The other FAILs first reported were stale-base artefacts that #261 already fixed: ticket_location, frontmatter_valid, ticket_field_values_valid, working_log_no_row_yet, staging_artifacts_complete, docs_to_update_coverage. #261 suppresses the whole [precheck] section once a ticket resolves under tickets/done/. They are NOT in scope.

Expected recurrence: TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION classified 14 tickets (STALE-PREMISE 2, NO-MECHANISM 1, UNDECLARED 5, and others). The 2 STALE-PREMISE tickets have closed this way, and roughly 3–8 more are expected from that epic alone.

A second, independently confirmed defect: running done_checker_static.py regenerates `docs/REGISTRY.yaml` as a side effect. On origin/main code it changes the `# Generated:` timestamp. A read-only gate check must not write a tracked, shared file. TCK-20260929-DONE-CHECKER-TESTS-WRITE-TRACKED-FILES fixed the tests, not this runtime path.

## Design decision (agent-working-design, 2026-09-30)
Use an explicit field, NOT inference from absence. "No Files Changed means a disposition" infers intent from an absence, the same mistake that produced the wrong code_trace absence verdicts (TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE). It is also NOT a fourth tier: tier is chosen at filing and routes the pipeline, while a disposition is an outcome discovered later, on a ticket of any tier.

The field's main value is evidence and corpus visibility, not the skip. The skip list is only one condition (`migration_complete`). What the field buys is that every disposition closure carries a cited rationale, and that dispositions become queryable across tickets/done/. Today there is no way to find them.

Two sections, so every body field keeps one parsing convention and `grep -A1 '^## Disposition$'` gives a clean value column across tickets/done/.

## Scope
1. Add an optional `## Disposition` body section holding the bare value only, validated by `tools/ticket_field_values.py` with `check_body_field_enum` unchanged, alongside Tier/Status/Priority. Allowed values: STALE-PREMISE, NO-MECHANISM, DUPLICATE, SUPERSEDED, WONT-DO. Add a separate `## Disposition Rationale` body section holding the prose; it is required whenever `## Disposition` is present, must be non-empty, and must contain at least one evidence citation (a commit SHA or file:line, or compile/run output). Do NOT add a first-line parsing variant: `parse_body_section` returns the whole section up to the next `## `, and `^## Disposition\s*\n` does not match the `## Disposition Rationale` heading, so the two sections parse independently. Absent `## Disposition` means a normal implementation closure.
2. done_checker_static.py: when Disposition is present and valid, `migration_complete` reports PASS with a note naming the disposition, instead of FAIL. It must also require (a) `## Disposition Rationale` to be present, non-empty and to contain at least one evidence citation, and (b) zero `src/` changes attributed to the ticket's own commits. If Disposition is present but either requirement fails, FAIL with a message saying which one. Every other condition is unchanged.
3. Stop done_checker_static.py from writing `docs/REGISTRY.yaml`. Trace the call path. If the checker needs a fresh registry, generate it in memory or to a temp path and compare. Finalize's real regeneration step (the one CLAUDE.md "After Work" describes) must keep working.
4. Document it once in docs/guides/delivery_process.md: when to use Disposition, the value list, and the evidence rule. Don't edit CLAUDE.md. If you believe CLAUDE.md's Ticket Format section must change, stop and tell agent-working-design, because governing-file edits need the user's direct confirmation.
5. Verification only for the two tickets closed at `791e6bf6b` (TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION and TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED). They live on rpg-feature-planning's branch `rpg-planning-post-258` (not yet on main), and rpg-feature-planning will add both sections to them on that branch once the shape is committed here. Message rpg-feature-planning when the shape is committed. After both land, run done_checker_static.py on those two tickets and record the result in this ticket. No cross-branch edit and no rebase dependency.

## Out of Scope
- Any [precheck] condition (fixed by #261).
- Changing tier routing or the implement-ticket.js pipeline.
- Re-closing any past ticket other than the verification run in Scope 5.
- Editing another session's branch.

## Acceptance Criteria
1. A ticket with a valid Disposition and cited Disposition Rationale, zero src/ changes and no staging artifacts passes done_checker_static.py fully. Test it with fixtures.
2. Disposition present with an empty or uncited Disposition Rationale FAILs, Disposition present with no Disposition Rationale section FAILs, and Disposition present with src/ changes attributed to the ticket FAILs. All three are tested, each naming which requirement failed.
3. A ticket without Disposition still FAILs migration_complete when artifacts are missing (regression).
4. ticket_field_values.py rejects an unknown Disposition value (tested).
5. On a clean checkout, running done_checker_static.py leaves `git status --porcelain -- docs/REGISTRY.yaml` empty (tested with a guard). The Finalize regeneration still updates it.
6. delivery_process.md carries the rule exactly once.
7. A test pins that `## Disposition` and `## Disposition Rationale` parse independently through `parse_body_section`.

## Related Tickets
- TCK-20260929-DONE-CHECKER-POST-CLOSURE-FALSE-FAILS (done, #261; fixed the [precheck] class)
- TCK-20260929-DONE-CHECKER-TESTS-WRITE-TRACKED-FILES (done, #261; fixed the tests, not the runtime REGISTRY write)
- TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION (source of the disposition closures)
- TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE (same batch; why absence-inference was rejected)
- TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE (done; the CLI)

## Related Docs
- `docs/guides/delivery_process.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- tools/gate_checks/done_checker_static.py
- tools/ticket_field_values.py
- docs/guides/delivery_process.md
- tests for both tools

## Assumptions / Open Questions
- None blocking. The value list mirrors the classification epic's vocabulary. If the epic's UNDECLARED outcomes need a value, add one in plan.md with a rationale; don't leave it open.

## Implementation Notes
_(pending)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_

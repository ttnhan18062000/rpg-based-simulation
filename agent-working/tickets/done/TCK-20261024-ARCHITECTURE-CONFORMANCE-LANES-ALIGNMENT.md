---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261024-ARCHITECTURE-CONFORMANCE-LANES-ALIGNMENT
phase: done
date: 2026-10-24
tags: [architecture, determinism]
---

# TCK-20261024-ARCHITECTURE-CONFORMANCE-LANES-ALIGNMENT

## Title
Conformance-suite design: replace the draft lane table with testing-planner's placement, close Q1 and Q4, and add rpg's schedule for F3 to F5

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`docs/plans/architecture/conformance_suite_design.md` (#724) left lane placement (§8, Q1) pending testing-planner, and Q4
(a purpose-built attack world) pending rpg-planner. Both have since answered:
- testing-planner: #593 issuecomment-6355976419;
- rpg's estimated schedule for the audit findings, relayed by lead-planner-u24: #593 issuecomment-6356470108.
The user approved this follow-up on 2026-10-24 (#715 issuecomment-6384095317).

## Scope
Edit `conformance_suite_design.md` only.
1. **§8 lanes:** replace the DRAFT table with testing-planner's placement, citing #593 6355976419. Read the comment itself; it
   wins over this summary.
   - **C-short:** a path-filtered PR-time job in `test.yml`. It is ADVISORY, not required. Both arms run in one job on one
     VM, the runner identity is recorded once, there is no timing, and it writes JUnit plus a step summary. It starts with
     A0, C1, G1 and P2 only. Mode 1 two-process on W1/W5 joins after T2; P1 and Mode 1 vs Mode 2 join after T3. Promotion
     to required is a recorded owner decision, made after at least 2 weeks / 20 PR runs on main with 0 false reds and a
     measured wall time.
   - **C-nightly:** its own testing-owned `conformance-nightly.yml`, not the `test.yml` cron (because of `test.yml`'s
     cancel-in-progress group). It runs with `cancel-in-progress: false`, sharded one job per world, with a step summary and
     no required status.
   - **C-slow:** `slow-regression.yml`, only after one measured dry run of W4 1000t, X3 and the Mode 4 invariants. If they
     add more than about 20 min, they move to C-nightly. Mode 4 reuses the existing certification long-run tests.
   - **Mode 3 cells:** not CI yet. When they come, comparisons stay within one job on one runner, never against the local
     VM (DET-PORT-0). They wait for T2's identity record and the 3a code.
   - **Every lane:** known fails are registered like `slow_known_reds.yaml`, with an owner, a ticket and an expiry, and
     there is no silent skip. A case waiting on step-1 code is not collected, rather than xfail'd.
   Replace the C-short row and any other row that conflicts with this. Drop "DRAFT, pending testing-planner" from the heading.
2. **§8 dependency table:** add rpg's estimated dates, marked "rpg estimates, not commitments", citing #593 6356470108:
   - F3 PR around 10-30;
   - F4: the A0 probe short runs on `unit_faction_tension` and `urban_political` around 10-31 to 11-01, a purpose-built
     world only if no squad forms, and the fix around 11-06/07 as its own paired step;
   - F5 after F4, leaning toward deleting the `ENABLE_*` back door;
   - F3 and F4 are M1-record prerequisites (roadmap §12.5).
   Quote the dates from the comment, not from this ticket.
3. **§9:** strike Q1 (testing-planner, 2026-10-23) and Q4 (rpg-planner: probe first, a purpose-built world only if no
   squad forms) as resolved, as was done for Q2, Q5, Q6 and Q7.
4. Add a short "Revised 2026-10-24" line near the top.

## Out of Scope
- Every other doc (the proposal and the audit stay as merged), and anything outside `docs/plans/architecture/**`.
- Filing testing's T1 to T3 or any workflow change; those are testing-planner's.

## Acceptance Criteria
- AC1: §8 matches #593 6355976419 with no contradiction, and no row is left marked DRAFT.
- AC2: the rpg dates match #593 6356470108, are labelled estimates, and are cited.
- AC3: Q1 and Q4 are struck as resolved, with attribution.
- AC4: frontmatter validates, and `docs/REGISTRY.yaml` is regenerated and committed.
- AC5: no file outside `docs/plans/architecture/conformance_suite_design.md`, `docs/REGISTRY.yaml`, this ticket and
  `agent-working/agent-monitoring/` changes.

## Related Tickets
- TCK-20261022-ARCHITECTURE-CONFORMANCE-SUITE-DESIGN

## Related Docs
- docs/plans/architecture/conformance_suite_design.md (section 8 lanes and dependencies; Q1, Q3 and Q4 struck in section 9)

## Related Stored Artifacts
- none

## Related Code Areas
- none (docs only)

## Assumptions / Open Questions
- Where the #593 comments differ from this ticket's summary, the comments win.

## Implementation Notes
Branch: a FRESH branch from origin/main. Never reuse the merged architecture-implementer-engine-modes branch. Close by hand
with `--path-reason investigation_only`. Send the SHA to architecture-planner before any push.

## Test Summary
Docs only; no tests apply. `tools/validate_frontmatter.py` on the design doc: no violations. Grep for DRAFT and pending
testing-planner in the doc finds none.

## Files Changed
- docs/plans/architecture/conformance_suite_design.md
- docs/REGISTRY.yaml (regenerated); ticket move and monitoring shards

## Completion Summary
Section 8 now holds testing-planner's placement (#593 comment 6355976419): C-short advisory in test.yml, C-nightly in its own
workflow, C-slow after a dry run, Mode 3 cells not CI, known-red registration. rpg's estimated dates for F3, F4 and F5
(#593 comment 6356470108) are in the dependency table, labelled estimates. Q1 and Q4 are struck as resolved. A Revised
2026-10-24 line is added. Two small related fixes inside section 8: the stale "H2, H3, H4 fixes" row now says H3 and H4 are
closed, and the runner-facts paragraph no longer names the test.yml cron. Q3 (recent_world_events) was already ruled by rpg
(#593 comment 6347182683); architecture-planner asked for it to be struck in this batch, so Q3 is struck as resolved too
(an edit beyond the ticket's original scope, approved by architecture-planner). C-short's starting set was matched to testing-planner's
list (A0, C1, G1, P2); C2 is noted as joining when the side digest is built, placement to be confirmed with testing-planner.

---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-TEST-ARCH-MAINT2-EPIC-B-COST-ROW-304
phase: done
date: 2026-10-03
tags: [testing]
---

# TCK-20261003-TEST-ARCH-MAINT2-EPIC-B-COST-ROW-304

## Title
Epic B cost record: the row for #304 and any PR merged after it

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary

Append the Epic B cost-record row for #304 (merged as `f76fda2cc03dc32481f66c6ba18d980ed28bdff2`), plus any PR
merged after #304 by the time this is done, by the same method and verification as maintenance-1. Records only.

## Scope

Append one dated `**Update ... (row for #304 ...)**` paragraph to
`agent-working/tickets/done/test-architecture/TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION.md`, after the latest
update paragraph, with no header, frontmatter or status change. Per PR, by this session from `gh api`:

1. The final head by full 40-character SHA. For #304 the reviewer reports
   `83e2ca759777582b493f9baf75ccf815bcea52c4`, run `37128617859`, docs-only, lane and Perf both skipped;
   those are read again by this session, not copied.
2. Exactly one `Tests` run for that SHA; a PR that cannot be pinned is "not recorded" with the reason.
3. `Scenario lane` and `Perf / cert / arena` conclusions and whole-job wall time of any job that ran.
4. PRs merged after #304 at the time of writing (listed with `gh pr list --state merged`), each verified the
   same way; open PRs (#291 and #301 at last check) are not recorded.
5. Totals line restated: the 30 PRs / 36 rows of the maintenance-1 update plus this update, and the lane-ran
   count (14 PRs across 19 rows at last record). State plainly how the carried totals were checked.
6. Re-check watch item (c) from each PR's own paginated file list (`src/progression/` matches).

If the GitHub API returns a TLS or other error, those results are discarded and re-queried, never read as
zeros.

## Out of Scope

- Any file other than the Epic B done ticket (plus this ticket, monitoring and registry files).
- Routing counts; any claim that the lane is promoted to required; any `tests/` edit.

## Acceptance Criteria

- [ ] Every recorded row names the final head by full SHA and exactly one `Tests` run id.
- [ ] Conclusions and wall times are read from the jobs API by this session.
- [ ] A PR not pinnable by full SHA is listed as "not recorded" with the reason and not counted.
- [ ] Totals restated with how they were checked; watch item (c) stated with its evidence.
- [ ] `git diff --name-only origin/main...HEAD` shows no `src/` or parity-ledger path and `tests/` paths only
  under `tests/unit/tools/`.

## Related Tickets

- `TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION` (done; the record lives here)
- `TCK-20261003-TEST-ARCH-MAINT-EPIC-B-COST-ROWS-292-302` (done; previous update)
- Siblings: `TCK-20261003-TEST-ARCH-MAINT2-REPORT-SOCIAL-DOMAIN`, `TCK-20261003-TEST-ARCH-MAINT2-ESCAPED-DEFECT-SEPTEMBER-COUNT`

## Related Docs

- `docs/plans/test_architecture/roadmap.md` §6

## Related Stored Artifacts

None.

## Related Code Areas

- `.github/workflows/test.yml` (read only)

## Assumptions / Open Questions

- Done last in the batch, just before the PR, so a PR merged in between is included.
- #304's own CI row is a docs/`agent-working`-only both-skipped observation.
- Context scan was by targeted reads; `search_docs` and graphify were unavailable.

## Implementation Notes

Approved as written by test-architecture-reviewer at plan review of `38423a1151a0ee2c9f6d6de0a55ad67406d009d4`.
Done last in the batch. Scope grew by one PR: **#301**, which was open when the previous update was written, merged
on 2026-10-03T13:42:40Z (between #302 and #304) and had no row, is recorded here with an explicit note. PRs merged
after #304 at the time of writing: only #306. Open, not recorded: #291 and #305. No TLS or other API error in this
pass.

## Test Summary

Records only. Each of #301, #304 and #306 returned exactly one `Tests` run for its final head SHA; the figures
were read from `gh api` by this session (the reviewer's #304 head and run id matched). Lane ran on #301 (31 s)
and #306 (39 s); both jobs skipped on #304, whose file list was checked and held only `agent-working/` and `docs/`
paths. Watch item (c): 0 `src/progression/` matches in all 3 file lists, unfired.

Totals, stated plainly: 30 PRs / 36 rows are carried forward from the previous update; that line's own chain
(18 / 23 through #288, plus #290, plus 11 PRs / 12 rows) adds up, but earlier rows were not re-enumerated one by
one. Adding 3 PRs and 3 rows gives 33 PRs / 39 rows; the lane ran on 16 PRs across 21 rows, whole-job 31-61 s.

## Files Changed

- `agent-working/tickets/done/test-architecture/TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION.md` (one dated update
  paragraph inserted after the previous update; nothing else changed)

## Completion Summary

Done 2026-10-03. Rows recorded for #301, #304 and #306 by final head full SHA and one `Tests` run each: lane ran
on #301 and #306, both jobs skipped on #304. #301 was added because it merged after the previous update was
written. #291 and #305 are open and not recorded. Watch item (c) is unfired. The lane has now run on 16 PRs
against the roughly 10 planned; no promotion of the lane to required is made or implied.

---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-TEST-ARCH-MAINT3-EPIC-B-COST-ROWS-AFTER-306
phase: done
date: 2026-10-04
tags: [testing]
---

# TCK-20261004-TEST-ARCH-MAINT3-EPIC-B-COST-ROWS-AFTER-306

## Title
Epic B cost record: rows for every PR merged after #306 (and the missed #303)

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary

Append one dated Update paragraph to the Epic B cost record covering every PR merged after #306 up to a stated
cut, by the same method and verification as the 2026-10-03 "rows for #301, #304 and #306" update. Records only.
Brief from `test-architecture-reviewer` (maintenance 3, T1).

## Scope

One new `**Update 2026-10-04 (rows for ...)**` paragraph in
`agent-working/tickets/done/test-architecture/TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION.md`, after the latest
update and without touching earlier paragraphs. Per PR, read from `gh api` by this session (every call under
`timeout 30`): final head by full 40-character SHA, exactly one `Tests` run, `Scenario lane` / `Perf / cert / arena`
conclusions and whole-job wall time from that run's jobs API, `src/progression/` matches in the paginated
`pulls/N/files` list (watch item c), and fixture/hash/baseline/scorer paths by file name (watch item b). Totals
restated.

## Out of Scope

- Any file other than the Epic B done ticket (plus this ticket, monitoring and registry files).
- Routing counts, a promotion of the lane to required, any `tests/` or `src/` edit.

## Acceptance Criteria

- [x] The cut (an `origin/main` full SHA) is stated; the set is every merged PR after #306 up to it.
- [x] Every row names the final head by full SHA and one `Tests` run id; a PR with other than one run says so.
- [x] #310 was re-read, not copied.
- [x] Watch items (b) and (c) stated with their evidence and limits; totals restated with how they were carried.

## Related Tickets

- `TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION` (done; the record lives here)
- `TCK-20261003-TEST-ARCH-MAINT2-EPIC-B-COST-ROW-304` (previous update)
- Siblings in this batch: `TCK-20261004-TEST-ARCH-MAINT3-SOCIAL-LEDGER-LINKS-AND-FINDING`,
  `TCK-20261004-TEST-ARCH-MAINT3-API-SERVER-READINESS-POLL`,
  `TCK-20261004-TEST-ARCH-MAINT3-DECISION-TRACE-VACUOUS-ASSERT`

## Related Docs

- `docs/plans/test_architecture/roadmap.md` §6

## Related Stored Artifacts

None.

## Related Code Areas

- `.github/workflows/test.yml` (read only)

## Assumptions / Open Questions

- Done last in the batch so a PR merged in between is included; it was: #316 merged after the first enumeration and
  was added, and the cut moved to its merge commit.
- `search_docs` returned nothing relevant and graphify had no graph in this worktree; not a gate.

## Implementation Notes

The reviewer's list (#305, #307, #308, #310, #291, #318-#321) was not taken as complete: enumerating from
`gh pr list --state merged` gave 19 PRs after #306, and **#303** (merged 2026-10-03T14:06:23Z, before #306) was in no
earlier update, so it is recorded here with an explicit note, as #301 was. Cut: `origin/main`
`54e46f43930d7652c1d3f779c196c84c9b36554a` (the #316 merge commit). No API error occurred; none of the pulls
queries returned an empty result that was read as zero.

## Test Summary

Records only. All 20 PRs returned exactly one `Tests` run for the final head (event `pull_request`, success). Lane
ran on 7 PRs (35-44 s), Perf ran on 10 (82-121 s, lane skipped), both skipped on 3 docs-only PRs (#307, #312, #322).
Watch item (c): 0 `src/progression/` matches in all 20 file lists, unfired. Watch item (b): seven PRs carry
fixture/baseline/hash-like paths, recorded by file name only. Totals: 33 PRs / 39 rows carried forward plus 20 / 20
gives 53 PRs / 59 rows; the lane ran on 23 PRs across 28 rows.

## Files Changed

- `agent-working/tickets/done/test-architecture/TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION.md` (one dated update
  paragraph inserted after the previous update; nothing else changed)

## Completion Summary

Done 2026-10-04. The cost record now covers #303 and the 19 PRs merged after #306 up to the cut, with the lane's
whole-job range unchanged at 31-61 s and watch item (c) still unfired. The lane has run on 23 PRs against the
roughly 10 planned; no promotion of the lane to required is made or implied.

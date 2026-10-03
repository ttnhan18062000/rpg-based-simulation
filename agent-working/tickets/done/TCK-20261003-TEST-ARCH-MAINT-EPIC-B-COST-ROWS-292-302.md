---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-TEST-ARCH-MAINT-EPIC-B-COST-ROWS-292-302
phase: done
date: 2026-10-03
tags: [testing]
---

# TCK-20261003-TEST-ARCH-MAINT-EPIC-B-COST-ROWS-292-302

## Title
Epic B cost record: dated rows for every PR merged after the #290 row, through #302

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary

The Epic B closure watch item (c) keeps a dated cost record in the frozen done ticket. The last row is
#290 (totals then: 19 PRs, 24 rows). PRs #292-#300 and #302 merged after it (#291 and #301 are OPEN at
`origin/main` `7d0b6e6f7432a1da254fd01e66ccf8815dda6818`). Append their rows by the same method as the #290
row, and restate the totals line. Records only.

## Scope

Append one dated `**Update 2026-10-03 (rows for ...)**` block to
`agent-working/tickets/done/test-architecture/TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION.md` (frozen folder;
the closure watch item says to append anyway). Per PR, from `gh api`:

1. The final head by full 40-character SHA (`gh api pulls/N`).
2. Exactly one `Tests` run for that SHA (event `pull_request`); a PR whose run cannot be pinned to exactly
   one run by full SHA is marked "not recorded" with the reason, and is not counted.
3. From that run's jobs API: `Scenario lane` and `Perf / cert / arena` conclusions and the whole-job wall time
   of any job that ran.
4. Candidates: #292-#300 and #302 (#289 merged before #290 and has no row: recorded only if its run pins by
   full SHA, else "not recorded" with the reason). Known so far: #294 docs-only, both skipped, run
   37110612188, head `a3267a23017309cff8d7c331bc1a505844983e1a`; #302 the lane RAN, final run 37126297588,
   head `d7ca92cf86eca94a5261eaf950334ef50fa7bbf1`. Earlier #302 heads (for example
   `09f13898e588908d1e2d0633d3d77ea787e82cea`, run 37120256157) are recorded only as earlier heads of the
   same PR, like #278: a row, not a new PR.
5. The restated totals line, recounted from the file (count verified rows only), and the lane-ran count and
   wall-time range.
6. State watch item (c): the reviewer's path scan of #290-#302 found no `src/progression` change, so the
   `src/progression/**`-only trigger is still unfired; this ticket re-checks it from the PRs' own file lists.

## Out of Scope

- Any file other than the Epic B done ticket (plus this ticket, monitoring and registry files).
- Routing counts (matched, unknown, irrelevant) unless cheap to compute; not required.
- Any change to `PERF_RE`, `scenario_lane_paths.py` or the workflow; any `tests/` edit; any claim that the
  lane is promoted to required.
- #291 and #301 (open).

## Acceptance Criteria

- [ ] Every recorded row names the final head by full 40-character SHA and exactly one `Tests` run id.
- [ ] Each row states the `Scenario lane` and `Perf / cert / arena` conclusions and, for a job that ran,
  the whole-job wall time, all read from the jobs API by this session (not copied from a peer).
- [ ] Any PR whose run cannot be pinned by full SHA is listed as "not recorded" with the reason and is
  not counted in the totals.
- [ ] The totals line is recounted from the file and states PRs, rows, lane-ran PRs and the wall-time range.
- [ ] Watch item (c) is stated: fired or unfired, with the evidence.
- [ ] `git diff --name-only origin/main...HEAD` shows no `tests/` path.

## Related Tickets

- `TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION` (done; the record lives here)
- `TCK-20261001-TEST-LANE-ROUTING-COST-VIEW-BASELINE-V2` (done)
- Sibling: `TCK-20261003-TEST-ARCH-MAINT-MUTATION-BASELINE-METHOD-DOC`

## Related Docs

- `docs/plans/test_architecture/roadmap.md` §6

## Related Stored Artifacts

None.

## Related Code Areas

- `.github/workflows/test.yml` (read only)
- `tools/test_architecture/scenario_lane_paths.py` (read only)

## Assumptions / Open Questions

- Context scan: `search_docs` MCP failed to connect this session, `graphify-out/graph.json` is absent in
  the worktree and `tools/knowledge_search.py` needs `sentence-transformers` (not installed); the scan was
  done by targeted reads of the Epic B ticket and `gh` instead. Disclosed, not a gate.
- A run that the jobs API no longer serves (expired) is "not recorded", never inferred.

## Implementation Notes

Plan for reviewer: (1) `gh api pulls/N` per PR for the final head; (2) `gh api` the `Tests` runs for that
head SHA, require exactly one; (3) read its jobs; (4) write one block in the same shape as the #290 update;
(5) recount totals from the file text before writing them.

Plan approved by test-architecture-reviewer at review of `5d2360f2229f1ae50ce9e87147803fdbafa69281`, who
confirmed: no header, frontmatter or status change on the frozen Epic B ticket, and one paragraph in the shape
of the #290 row. The GitHub API returned TLS certificate errors partway through the first pass (from #296
on); those empty results were discarded, not read as zeros, and the failed PRs were re-queried once the API
answered again. Every figure in the paragraph comes from the second, error-free read. The earlier #302 head
was queried by this session by full SHA (one run, lane success).

## Test Summary

Records only, no code. Each of the 11 recorded PRs (#289, #292-#300, #302) returned exactly one `Tests` run
for its final head SHA; the extra earlier #302 head (`09f13898e588908d1e2d0633d3d77ea787e82cea`) also one run.
Lane wall times were computed from the jobs' `started_at` and `completed_at`. Watch item (c) was checked per PR
from `gh api pulls/N/files`: 0 `src/progression/` matches in all 11. Gate:
`git diff --name-only origin/main...HEAD` is checked before the PR.

Limit, stated plainly: the totals line (30 PRs, 36 rows; lane ran on 14 PRs across 19 rows) adds this update to
the 19 PRs / 24 rows already stated in the #290 row. I checked that the file's stated chain is internally
consistent (18 PRs / 23 rows through #288, plus #290) but did not re-enumerate every earlier row, so "recounted
from the file" means that consistency check, not a row-by-row recount.

## Files Changed

- `agent-working/tickets/done/test-architecture/TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION.md` (one dated
  update paragraph inserted after the #290 row; nothing else changed)

## Completion Summary

Done 2026-10-03. Rows recorded for #289 and #292-#300 and #302, each by final head full SHA and one `Tests`
run: the lane ran on 6 PRs (#293, #295, #296, #299, #300, #302; whole-job 33-61 s), `Perf / cert / arena` ran
and covered the scenario tests on 3 (#289, #292, #297), both jobs were skipped on 2 (#294, #298). #302's
earlier head is a second row of the same PR. #291 and #301 are open and not recorded. Watch item (c) is
unfired. The lane has now run on 14 PRs against the roughly 10 planned; no promotion of the lane to required
is made or implied.

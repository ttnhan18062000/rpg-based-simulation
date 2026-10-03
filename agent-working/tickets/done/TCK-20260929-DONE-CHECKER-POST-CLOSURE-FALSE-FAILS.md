---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260929-DONE-CHECKER-POST-CLOSURE-FALSE-FAILS
phase: done
date: 2026-09-29
tags: [agent-monitoring, data-quality]
---

# TCK-20260929-DONE-CHECKER-POST-CLOSURE-FALSE-FAILS

## Title
done_checker_static CLI gives false FAILs after closure and blames sibling tickets' docs

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
test-architecture-implementer reported two defects on 2026-09-29. They came from running
`python3 tools/gate_checks/done_checker_static.py --ticket-id <id>` after hand-orchestrated
closures. The evidence is on branch `test-baseline-reliability` at `a37aa2b13`, with tickets
`TCK-20260929-CATALOG-REGISTRY-TEST-LEAK`, `-VERIFICATION-VIEW-TEST-TRACKED-WRITE` and
`-ESCAPED-DEFECT-TAG`. Design confirmed both against origin/main source.

1. **The CLI default checks the wrong phase after closure.** `main()` defaults to
   `--part both`, so it runs Part A (`run_static_precheck`) as well. Part A's conditions assume
   the ticket is still in `tickets/inprogress/`:
   - `ticket_location`
   - `ticket_field_values_valid`
   - `frontmatter_valid`
   - `working_log_no_row_yet`, which fails because the row exists, and that is the correct
     post-closure state
   After a closure these FAIL, so the run prints `RESULT: FAIL` even though every [finalize]
   condition passes. CLAUDE.md's After Work bullet tells agents to run this CLI "after a
   hand-orchestrated Finalize" without `--part finalize`, so the documented usage always reports
   a misleading FAIL.
2. **The reverse `docs_to_update_coverage` check can't tell tickets apart.** It unions
   `_git_status_touched_paths()` (every uncommitted docs/ path in the tree) with the ticket's own
   commits (~l.620-629). Every uncommitted docs/ path is then required in *this* ticket's Files
   Changed or Related Docs. When a batch closes several tickets before one commit, each ticket
   gets flagged for its siblings' docs. `docs/REGISTRY.yaml` is flagged as well, even though
   Finalize regenerates it by design at every close.

## Scope
1. In `main()`, when `--part` is not given explicitly and the ticket resolves under
   `tickets/done/`, run only the finalize part. Print one line saying that precheck was skipped
   because the ticket is closed. An explicit `--part precheck`/`both` keeps working as it does
   today. Fixing the tool keeps CLAUDE.md correct, so CLAUDE.md is not edited.
2. Always exclude `docs/REGISTRY.yaml` from the reverse check's touched set, because it is a
   generated file. Put the exclusion in one named constant with a comment citing the regen rule.
3. Sibling attribution. From the **uncommitted** half only, drop any docs/ path that another
   ticket's `## Files Changed` or `## Related Docs` claims. "Another ticket" means one in
   `tickets/inprogress/`, or in `tickets/done/` and also modified or untracked in `git status`,
   i.e. closed in this same uncommitted batch. The committed half (the ticket's own commits by
   ID) stays as it is, since it's already attributed correctly. A path that no ticket claims
   still FAILs for the ticket being checked, so there is no new blind spot.

## Out of Scope
- The tests writing tracked files. That's `TCK-20260929-DONE-CHECKER-TESTS-WRITE-TRACKED-FILES`,
  the sibling ticket. Do it first; both touch the same test file.
- Changing the forward (investigation.md-driven) half of `docs_to_update_coverage`.
- Editing CLAUDE.md.

## Acceptance Criteria
1. A ticket already in `tickets/done/` with a valid working_log row and a clean finalize state
   gives `RESULT: PASS` under the bare CLI (no `--part`), plus the skipped-precheck note.
2. With `--part both` set explicitly on the same ticket, the run still shows the precheck
   results, so behavior is unchanged when asked for.
3. Reverse check: with two in-progress tickets A and B and uncommitted docs edits `docs/a.md`
   (claimed by A) and `docs/b.md` (claimed by B), checking A passes and checking B passes. An
   uncommitted `docs/c.md` claimed by neither makes both FAIL.
4. An uncommitted change to `docs/REGISTRY.yaml` alone never FAILs the reverse check.
5. The existing `test_done_checker_static.py` coverage passes, and new tests use tmp roots only.
   Per the sibling ticket, `git status` must stay clean after the run.

## Related Tickets
- TCK-20260929-DONE-CHECKER-TESTS-WRITE-TRACKED-FILES (sibling, same batch, do first)
- TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE (done; added the CLI whose
  default this fixes)
- TCK-20260904-DOC-COVERAGE-REVERSE-CHECK, TCK-20260916-DOC-COVERAGE-CHECK-BLIND-TO-COMMITTED-CHANGES
  (done; built the reverse check and its committed-paths half)
- TCK-20260709-REGISTRY-REGEN-ON-CLOSE (done; why REGISTRY.yaml is always touched at close)

## Related Docs
- CLAUDE.md "After Work" (the hand-run instruction; left unchanged because the tool is fixed)

## Related Stored Artifacts
- None.

## Related Code Areas
- `tools/gate_checks/done_checker_static.py` (`main()` ~l.1282; `check_docs_to_update_coverage`
  ~l.733; `_git_status_touched_paths` ~l.528; union ~l.620)
- `tests/tools/test_done_checker_static.py`

## Assumptions / Open Questions
- Scope 3 relies on the sibling tickets' Files Changed sections being filled in before the check
  runs. A sibling that hasn't written them yet will still cause a FAIL, which is the correct,
  conservative result.

## Implementation Notes
- `--part` default changed from a fixed `"both"` to `None`, resolved at runtime: `check_ticket_finalized(ticket_id)[0] == "PASS"` (reused, not reimplemented) decides whether the ticket already resolves under `tickets/done/`; if so, defaults to `"finalize"` and prints a `NOTE:` line, else `"both"` as before. `--part both`/`--part precheck` explicitly still force precheck to run.
- Reverse check now computes `status_touched`/`committed_touched` separately (via `_git_status_touched_paths`/`_git_ticket_commits_touched_paths` directly) instead of the combined `_git_touched_paths`, so sibling-attribution and the `docs/REGISTRY.yaml` exclusion apply only to the uncommitted half, per Scope. The forward half's own `touched = _git_touched_paths(ticket_id)` lookup is untouched.
- `_sibling_declared_docs_paths()`: "another ticket" = anything in `tickets/inprogress/`, or a `tickets/done/*.md` ticket that is itself present in the uncommitted `git status` (closed in this same batch). A done ticket NOT in that status is an already-committed prior closure, not a same-batch sibling — its declared docs don't excuse anything (pinned by a dedicated test).
- `docs/REGISTRY.yaml` exclusion is a named module-level constant (`_GENERATED_DOCS_EXCLUDED_FROM_REVERSE_CHECK`) with a comment citing `TCK-20260709-REGISTRY-REGEN-ON-CLOSE`, applied unconditionally, not just when it's the sole touched path.
- One pre-existing test (`test_reverse_docs_coverage_reproduces_RACE_RELATIONS_MATRIX_incident`) mocked the now-bypassed `_git_touched_paths` for the reverse half — updated to also mock `_git_status_touched_paths` directly rather than weakening the assertion.

## Test Summary
`pytest tests/tools/test_done_checker_static.py tests/tools/test_monitoring_consolidation.py -q`
— 165 passed. `git status --porcelain -- docs/REGISTRY.yaml tickets/working_log.csv
agent-monitoring/data/` empty afterward. New tests: 2 CLI-level (AC1/AC2, via the existing
subprocess `_run_cli` helper), 3 sibling-attribution (AC3, including the done-but-not-uncommitted
edge case), 2 REGISTRY.yaml-exclusion (AC4, including alongside a real undeclared doc). Also ran
`tests/tools/test_finalize_knowledge_index_refresh.py` (the only other file referencing the
touched functions) — 4 passed, unaffected.

## Files Changed
- `tools/gate_checks/done_checker_static.py` — `main()`'s `--part` default logic;
  `_GENERATED_DOCS_EXCLUDED_FROM_REVERSE_CHECK` constant; `_sibling_declared_docs_paths()`
  helper; `check_docs_to_update_coverage()`'s reverse-check touched-set computation.
- `tests/tools/test_done_checker_static.py` — 1 existing test updated (new mock target), 7 new
  tests (2 CLI, 3 sibling-attribution, 2 REGISTRY.yaml).

## Completion Summary
Fixed both defects test-architecture-implementer reported: the bare CLI now correctly skips
precheck (with an explanatory note) for a ticket already in `tickets/done/`, avoiding the
misleading `RESULT: FAIL` CLAUDE.md's own documented post-closure usage always produced;
`--part both` still forces precheck to run when explicitly asked. The reverse `docs_to_update_coverage`
check now excludes `docs/REGISTRY.yaml` unconditionally and drops sibling-claimed uncommitted
docs/ paths — from the uncommitted half only, scoped to genuinely same-batch siblings — so a
multi-ticket batch closing before one shared commit no longer cross-blames tickets for each
other's own declared docs, with no new blind spot for a genuinely undeclared path.

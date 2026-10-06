---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261006-PR-BODY-ATTRIBUTION-TRAILER-NOT-CHECKED
phase: done
date: 2026-10-06
tags: [ai, process-improvement]
---

# TCK-20261006-PR-BODY-ATTRIBUTION-TRAILER-NOT-CHECKED

## Title
Nothing mechanical catches an attribution trailer in a PR body; the read-back check and CI both miss it

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Repo law (`docs/guides/delivery_process.md:298-370`) and the owner, who restated it on 2026-10-06, forbid any
attribution trailer in a PR body: no "🤖 Generated with [Claude Code](...)" line, no
`https://claude.ai/code/session_...` link, and no `Co-Authored-By`. It still happens. #369 merged with the
"Generated with" line, and #372 (open on 2026-10-06) carries both lines. The cause is the harness's system
reminder, which tells every session to end PR descriptions with that line. The rule depends on each session
remembering it.

The required read-back, `pr_render.py --check --pr <N>`, cannot catch it. `check_against_live` compares only the
title and the generated sections, so a trailer appended after the hand-written `## Review notes` or `Closes:`
still gives `matches: True`.

## Scope
1. **`tools/delivery/pr_render.py`**: `check_against_live` scans the live body for attribution patterns. These
   are matched case-insensitively, one shared list:
   - `Generated with \[?Claude Code`
   - `claude\.ai/code/session_`
   - `^Co-Authored-By:`
   - the robot emoji followed by "Generated"

   Any hit sets `attribution_found: [<matched line>, ...]` and forces `matches: False`. The text output prints
   `attribution trailer found: ... — remove it and PATCH again`. The exit code is unchanged: `--check` never
   exits non-zero for a real difference.
2. **A CI net that does not depend on a session running `--check`**: a small job on `pull_request` events
   (`opened`, `edited`, `synchronize`). It reads the event's PR body (`github.event.pull_request.body`, no checkout
   of untrusted code needed) and fails, naming the matched line, when the same pattern list hits.
   - The pattern list lives in one place (e.g. `tools/delivery/pr_body_lint.py`). `pr_render.py` imports it and
     the job runs it.
   - The owner confirms the literal workflow diff before it lands.
3. **Docs**: `delivery_process.md` step 4 says `--check` now reports a trailer and the CI job fails on one.

## Out of Scope
- Commit-message trailers, which are unchanged and still required by the attribution convention.
- Rewriting merged PR bodies (#369).
- Changing the harness reminder itself. That is outside the repo.

## Acceptance Criteria
1. A live body whose generated sections match but which ends with
   "🤖 Generated with [Claude Code](https://claude.com/claude-code)" makes `--check` report `matches: False` and
   `attribution_found` with that line. A session-link-only body does the same.
2. A clean body is unchanged: `matches: True`, no `attribution_found`.
3. A body that only mentions the rule in prose, for example "no Generated with line", is not a false positive.
   The patterns are anchored on the real trailer shapes. A test pins this.
4. The CI job fails on the fixture bodies from AC1 and passes on a clean one. A unit test drives
   `pr_body_lint.py` directly; the workflow wiring is checked by the existing CI-workflow coverage test pattern
   (`ci_workflow_test_coverage.py`).
5. `tests/tools/test_delivery_pr_render.py` and the new lint tests are green. `delivery_process.md` is updated.

## Related Tickets
- `TCK-20260927-PR-RENDER-NO-RECORDED-TICKET-EXCLUSION` (the last change to `check_against_live`)

## Related Docs
- `docs/guides/delivery_process.md` ("PR Lifecycle", steps 3 and 4)

## Related Stored Artifacts
- None.

## Related Code Areas
- `tools/delivery/pr_render.py` (`check_against_live` at about :607, `main` at :646)
- new `tools/delivery/pr_body_lint.py`
- `.github/workflows/`

## Assumptions / Open Questions
- Should a CI failure on a PR-body lint block merge (a required check)? Recommended: yes. It is cheap to fix
  (PATCH the body), and the owner has restated the rule more than once.

## Implementation Notes
Drafted by `agent-working-design` on 2026-10-06 from origin/main, at the owner's request.

## Test Summary
`tests/tools/test_pr_body_lint.py` (new, 9 pass): a Generated-with line, a session-link-only line and a Co-Authored-By line are each found; a clean body and prose that only mentions the rule are not; `main` exits 1 with an `::error::` line on a hit and 0 otherwise; `check_against_live` gives `matches: False` plus `attribution_found` for either trailer and is unchanged for a clean body; the workflow file triggers on opened/edited/synchronize and passes the body through `env`, never shell text. `test_delivery_pr_render.py` (59) and the CI-workflow coverage and split tests stay green.

## Files Changed
- `tools/delivery/pr_body_lint.py` (new, the one pattern list)
- `tools/delivery/pr_render.py` (`check_against_live`, `--check` text output)
- `.github/workflows/pr-body-lint.yml` (new; literal diff confirmed by the owner)
- `tests/tools/test_pr_body_lint.py` (new)
- `docs/guides/delivery_process.md` (PR Lifecycle step 4)

## Completion Summary
Closed 2026-10-06. All five acceptance criteria met. `--check` now reports `attribution_found` and forces `matches: False`; the `PR body lint` workflow runs the same list on the PR body. Not done by me: making it a required check, which is a `protect_branches` ruleset change for the owner (they chose to add the workflow; the recommendation is to require it). The workflow itself has not run on GitHub yet; its first run is on this PR.

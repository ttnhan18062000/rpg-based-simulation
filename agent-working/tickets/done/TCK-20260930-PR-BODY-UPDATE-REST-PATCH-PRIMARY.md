---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-PR-BODY-UPDATE-REST-PATCH-PRIMARY
phase: done
date: 2026-09-30
tags: [delivery, ai, documentation]
---

# TCK-20260930-PR-BODY-UPDATE-REST-PATCH-PRIMARY

## Title
Make REST PATCH plus a read-back check the only documented way to update a PR body

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
test-architecture-implementer reported this on 2026-09-30, on PR #259. `gh pr edit 259 --title ...
--body-file ...` printed only the GraphQL "Projects (classic) is being deprecated ...
(repository.pullRequest.projectCards)" message and left the PR body unchanged. A read-back through
`gh api .../pulls/259 --jq .body` confirmed the body hadn't changed.
`gh api -X PATCH repos/<owner>/<repo>/pulls/259 -F body=@<file> -f title=<title>` worked, and
`pr_render.py --check --pr 259` then reported `matches: True`. The local gh is 2.45.0.

`docs/guides/delivery_process.md` "PR Lifecycle" already knows about this bug (step 3, ~l.226-228,
and step 4, ~l.239-241). But it still names `gh pr edit` as the primary update path and the PATCH
only as a fallback. It also puts the `--check` read-back only in step 4, for the push-more-tickets
case. The failure looks like an ordinary gh warning, so a session following the primary path can
believe the body was updated when it wasn't.

## Scope
1. In the PR Lifecycle section, make `gh api -X PATCH repos/{owner}/{repo}/pulls/<N> -F
   body=@<file> -f title=<title>` the one documented way to update a PR title or body. Name the
   `gh pr edit` projectCards GraphQL failure as the reason, once, and state it as a silent no-op.
   Remove `gh pr edit` as a recommended path.
2. Require `python3 tools/delivery/pr_render.py --check --pr <N>` after **every** PR body write,
   including the initial `gh pr create`, and treat `matches: False` as the write having failed.
   State this in one place and reference it from steps 3 and 4. Don't write it twice.
3. Leave `gh pr create` as it is. It doesn't hit the bug.

## Out of Scope
- Giving `pr_render.py` an apply/PATCH mode. Its docstring deliberately keeps PR writes out of
  scope, so revisit only if the doc fix proves insufficient.
- Upgrading gh.

## Acceptance Criteria
1. `docs/guides/delivery_process.md` no longer recommends `gh pr edit` for body or title updates.
   The PATCH command appears as the single update path, with the reason given once.
2. The read-back `--check` requirement covers every body write and is stated exactly once.
3. `make knowledge-index-update` has been run, since a docs/ file changed.

## Related Tickets
- TCK-20260924-DELIVERY-PR-RENDERER (done; introduced pr_render.py and the PR Lifecycle steps)
- TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS (done; made `--check` reliable enough to use as the
  read-back)

## Related Docs
- `docs/guides/delivery_process.md` ("PR Lifecycle", steps 3-4)

## Related Stored Artifacts
- None.

## Related Code Areas
- `tools/delivery/pr_render.py` (read-only; its `--check` is the verification)

## Assumptions / Open Questions
- This assumes the projectCards failure is a gh 2.45 / GraphQL-side defect that `gh pr edit`
  can't route around. The REST path avoids it entirely, so the gh version doesn't matter for this
  fix.

## Implementation Notes
- Step 3 (`gh pr create`) is otherwise unchanged, per Out of Scope — only its no-attribution
  paragraph's reference to "later `gh pr edit` calls" was reworded to point at step 4 instead, and
  a one-line cross-reference to step 4's read-back check was added immediately after it.
- Step 4 is rewritten as the single home for both: the PATCH command (with the projectCards/
  GraphQL silent-no-op reason stated once, including the confirmed `gh` version it was found on)
  and the read-back requirement (stated once, explicitly covering the initial `gh pr create` too,
  not just later pushes) — cross-referenced from step 3 rather than duplicated.
- Checked `docs/`, `CLAUDE.md`, and `.claude/` for other `gh pr edit` recommendations before
  closing — only `docs/guides/delivery_process.md` itself had one; the two hits remaining in
  `.claude/handover/*.md` are historical session notes, not instructions, and are out of scope.
- No test pins this section's prose (confirmed: the two tests matching "PR Lifecycle" use the
  heading only as a text-boundary marker for an unrelated section, `### CI Failure Triage`).

## Test Summary
`pytest tests/docs/ -q` — 70 passed, 1 skipped, 1 xfailed (pre-existing, unrelated) — confirms the
two tests using "### PR Lifecycle" as a section boundary still resolve correctly. `make
knowledge-index-update` run per AC3 (4 files re-embedded, this doc among them).

## Files Changed
- `docs/guides/delivery_process.md` — "PR Lifecycle" steps 3-4 rewritten: `gh api -X PATCH` is now
  the single documented PR title/body update path, the `gh pr edit` GraphQL no-op is named once as
  the reason, and the `pr_render.py --check` read-back is required after every body write
  (including the initial `gh pr create`), stated once and cross-referenced.

## Completion Summary
`docs/guides/delivery_process.md` no longer recommends `gh pr edit` for any PR title/body update —
`gh api -X PATCH repos/{owner}/{repo}/pulls/<N>` is the one documented path, with the confirmed
silent-no-op failure mode named once as the reason. The `pr_render.py --check --pr <N>` read-back
is now required after every PR body write, including the initial `gh pr create`, stated in one
place and cross-referenced from both steps rather than duplicated. `gh pr create` itself is
unchanged.

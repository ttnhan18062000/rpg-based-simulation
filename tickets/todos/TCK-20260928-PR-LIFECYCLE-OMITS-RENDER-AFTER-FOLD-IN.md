---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260928-PR-LIFECYCLE-OMITS-RENDER-AFTER-FOLD-IN
phase: open
date: 2026-09-28
tags: [delivery, process-improvement]
---

# TCK-20260928-PR-LIFECYCLE-OMITS-RENDER-AFTER-FOLD-IN

## Title

The PR Lifecycle contract never names `pr_render.py` and has no step to re-render after tickets are
added to an open PR, so #252 merged with a title saying "(1 ticket)" while carrying 2.

## Status

OPEN

## Tier

hotfix

## Type

bug

## Priority

P3

## Request Summary

PR #252 squash-merged as `9bcae32c5` with the title "ai: pr_render.py has no way to record an
intentional ticket exclusion (1 ticket)". The commit closes two tickets:
`TCK-20260927-PR-RENDER-NO-RECORDED-TICKET-EXCLUSION` and
`TCK-20260927-PHASE-PROMPTS-OMIT-GATE-PRECONDITIONS`. The second was added to the already-open PR
on the user's instruction ("if the current PR is small, push more work into that PR"), and nobody
re-rendered the title or body afterwards.

The tooling to catch this exists. `tools/delivery/pr_render.py` renders the title and body from
the branch's tickets, and `--check --pr N` reports drift against the live PR, title included.
Nothing in the process tells anyone to run it. `docs/guides/delivery_process.md` "PR Lifecycle"
step 3 says to push and `gh pr create` with no mention of rendering, and no step covers pushing
more tickets to an open PR. `git grep pr_render` outside ticket history finds only the tool, its
tests, the delivery plan and `docs/agent-monitoring/README.md`. Neither
`delivery_process.md` nor any agent or skill file references it.

Adding tickets to an open PR is standing practice here (one open PR per batch, follow-ups
pushed onto it), so this will recur on every batch that grows after its PR opens.

## Scope

1. In `docs/guides/delivery_process.md` "PR Lifecycle" step 3, say the title and the generated
   body sections come from `python3 tools/delivery/pr_render.py`. Hand-write only
   `## Review notes`, per the renderer's own docstring. Keep the existing no-attribution rule
   unchanged.
2. Add a step after it for pushing more tickets to an **open** PR: after the push, run
   `python3 tools/delivery/pr_render.py --check --pr <N>`. If the title or any generated section
   drifted, re-render and update the PR with `gh pr edit` (or the documented `gh api … --method
   PATCH` fallback). That is a PR edit on an already-user-authorized PR, and the same
   no-attribution rule applies.
3. Before writing, confirm the exact output flags against `pr_render.py --help` on the branch
   (e.g. whether `--json` or plain stdout gives separate title and body). Do not describe a flag
   the tool does not have.
4. Run `make knowledge-index-update` (a `docs/` file changes).

## Out of Scope

- Automating the re-render (a hook or CI job that edits the PR). PR edits stay deliberate,
  user-authorized actions per `pr_render.py`'s own out-of-scope note. A CI job that only
  *reports* `--check` drift could be a later ticket if the doc step proves insufficient.
- Retitling #252 after the fact. It is merged, and the squash commit subject is permanent.

## Acceptance Criteria

- AC1: `delivery_process.md` PR Lifecycle names `pr_render.py` for creating the title and body,
  with flags that exist on the branch's version of the tool.
- AC2: A step covers adding tickets to an open PR: run `--check --pr N`, and re-render plus
  `gh pr edit` on drift.
- AC3: `make knowledge-index-update` has been run; `docs/REGISTRY.yaml` is regenerated per the usual close.

## Related Tickets

- `TCK-20260924-DELIVERY-PR-RENDERER`: the renderer.
- `TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS`, `TCK-20260927-PR-RENDER-NO-RECORDED-TICKET-EXCLUSION`:
  made `--check` trustworthy enough to put into the process.

## Related Docs

- `docs/guides/delivery_process.md` ("PR Lifecycle", "PR Title Template", "PR Body Template")

## Related Stored Artifacts

None.

## Related Code Areas

- `tools/delivery/pr_render.py` (read only)

## Assumptions / Open Questions

- `delivery_process.md` is not a governing file (CLAUDE.md / settings.json), so no direct
  user-confirmation step is needed. CLAUDE.md already links to it rather than restating the steps.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

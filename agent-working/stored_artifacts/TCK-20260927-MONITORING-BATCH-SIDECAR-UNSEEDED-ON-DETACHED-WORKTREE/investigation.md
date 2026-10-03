---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260927-MONITORING-BATCH-SIDECAR-UNSEEDED-ON-DETACHED-WORKTREE
artifact_type: investigation
tags: [agent-monitoring, data-quality, hooks]
---

# Investigation — TCK-20260927-MONITORING-BATCH-SIDECAR-UNSEEDED-ON-DETACHED-WORKTREE

## Reflog reliability, verified directly on this worktree (not just the reporting one)

`doc-tag-enforcement` (this worktree) has 90 `checkout: moving from ... to ...` entries in its own
`<gitdir>/logs/HEAD`, and the most recent one (`checkout: moving from
monitoring-scope-boundary-doc-followups to monitoring-and-delivery-batch-2`) names exactly this
worktree's real current branch. Confirms the ticket's claim independently, on a second worktree,
not just the one that raised it — the reflog-based recovery is not specific to one worktree's
history shape.

## Why the reflog path is only ever reached on a genuinely detached HEAD

`resolve_batch_identifier()`'s step 1 (`_branch_from_head_file`) already succeeds directly from
`HEAD`'s own content whenever the worktree is attached to a branch — the reflog step (inserted at
step 2.5, between the sidecar and `detached-<sha>`) is only ever consulted when step 1 has already
determined HEAD is a raw SHA, not a `ref:` line. So at the exact point this new step runs, the
worktree is provably NOT currently on any branch — the reflog's last `checkout: moving to <name>`
entry is not "the current branch" in a live sense, it is "the last branch this worktree was validly
on before whatever detached it," which is precisely the same semantic the sidecar itself already
caches, just recovered from git's own history instead of a side channel that never got written.

## Two open questions, decided

1. **Validate the recovered name against `refs/heads/`?** — No. The sidecar's own purpose is
   attribution ("which batch do these monitoring rows belong to"), not a live git operation — a
   branch squash-merged and deleted after these rows were written is still the correct historical
   attribution for them. Validating would silently discard a real, correct answer in exactly the
   case (a finished, deleted branch) this project's own delivery process produces routinely.
2. **Write the recovered value to the sidecar, or use it in-memory only?** — Write it. This is what
   actually closes the ticket's own stated gap: a worktree detached at every moment this module has
   ever run on it would otherwise NEVER get a chance to seed `.claude/current_batch`, defeating
   Option A's whole point. Writing it is also consistent with the module's own existing principle
   ("refreshed on every successful resolution, never written once and left stale") — the reflog
   recovery IS a successful resolution, just a colder one than a live attached HEAD.

## No `git` subprocess introduced (AC2)

The new step reads `<gitdir>/logs/HEAD` with the same plain-file-read discipline as every existing
step (`_real_gitdir`, `_branch_from_head_file`) — confirmed by writing it with no `subprocess`
import and no shell-out, matching the module's own existing zero-subprocess invariant.

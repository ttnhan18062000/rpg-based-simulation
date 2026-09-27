---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260927-MONITORING-BATCH-SIDECAR-UNSEEDED-ON-DETACHED-WORKTREE
artifact_type: plan
tags: [agent-monitoring, data-quality, hooks]
---

# Plan — TCK-20260927-MONITORING-BATCH-SIDECAR-UNSEEDED-ON-DETACHED-WORKTREE

## New function

```python
def _branch_from_reflog(gitdir: Path) -> str | None:
    """Last-resort recovery for a detached HEAD with no sidecar: the most recent `checkout:
    moving from ... to <name>` entry in <gitdir>/logs/HEAD -- the last branch this worktree was
    validly attached to before whatever detached it. Plain file read, no subprocess, matching
    every other step in this module. Returns None if the file is absent or has no such entry
    (e.g. a fresh worktree, or a reflog pruned by gc.reflogExpire). Not validated against
    refs/heads/ -- see investigation.md: a deleted branch's name is still the correct historical
    attribution for rows already written under it."""
```

Reads the file once, scans lines in reverse (last entry wins), matches
`re.search(r"checkout: moving from \S+ to (\S+)$", line)` (message text is the tail of the line,
safe to anchor on `$` since git reflog messages don't contain trailing whitespace).

## Resolution order change

`resolve_batch_identifier()` gains one step between the sidecar read and the `detached-<sha>`
fallback:

1. Attached HEAD (unchanged).
2. Sidecar (unchanged).
3. **New**: reflog recovery. If found, write it to the sidecar (closing the actual gap this ticket
   exists to fix) and return it.
4. `detached-<sha>` (unchanged, still reachable when the reflog has no usable entry either).

## Docstring update (AC1)

Rewrite the "the sidecar already covers the common case (a worktree that was ever attached to a
real branch even once)" claim to state the real chain: attached HEAD, else sidecar, else reflog
recovery (also seeding the sidecar), else `detached-<sha>` — and name the actual guarantee: any
worktree with at least one real `checkout: moving to <branch>` entry anywhere in its reflog
resolves to that branch, not just one seeded by a hook run after this module shipped.

## Tests

1. Reflog present, most recent entry names a real branch → resolves to it, sidecar written.
2. Reflog present but every entry is a bare-SHA move (no `checkout: moving ... to <name>` shape) →
   falls through to `detached-<sha>`, no crash.
3. Reflog file absent entirely → falls through to `detached-<sha>`, no crash.
4. Reflog's most recent entry names a branch that no longer exists as a real ref → still resolves
   to that name (AC1's stated non-validation decision), not silently rejected.
5. Attached-HEAD path is completely unaffected — a test asserting step 1 still short-circuits
   before the reflog is ever read (e.g. via a reflog fixture that would resolve to a DIFFERENT
   name than the real attached branch, proving step 1 wins).
6. `detached-<sha>` remains reachable and still prints its warning — a scratch repo with a detached
   HEAD, no sidecar, and no reflog at all.
7. End-to-end (AC5): a scratch repo with no `.claude/current_batch`, a reflog naming a real branch,
   and a detached HEAD — `resolve_write_target()` returns a path keyed by that branch, not
   `detached-<sha>`.

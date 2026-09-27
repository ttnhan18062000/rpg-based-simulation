---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260927-MONITORING-BATCH-SIDECAR-UNSEEDED-ON-DETACHED-WORKTREE
phase: open
date: 2026-09-27
tags: [agent-monitoring, data-quality, hooks]
---

# TCK-20260927-MONITORING-BATCH-SIDECAR-UNSEEDED-ON-DETACHED-WORKTREE

## Title

`monitoring_batch_identifier`'s `detached-<sha>` last resort fires on worktrees the module's own
docstring claims are covered, because `.claude/current_batch` is only ever seeded by an
attached-HEAD hook run that happened *after* the module shipped.

## Status

OPEN

## Tier

standard

## Type

bug

## Priority

P2

## Request Summary

`tools/agent-monitoring/monitoring_batch_identifier.py` resolves the per-batch monitoring shard
filename in three steps: attached `HEAD` (authoritative), else the `.claude/current_batch` sidecar,
else a `detached-<sha>` label. Its docstring (lines 50-55) describes the third step as an accepted
rare degraded mode, and justifies that acceptance with a specific coverage claim:

> the sidecar already covers the common case (a worktree that was ever attached to a real branch
> even once).

**That claim is stronger than the implementation.** The sidecar is written only on a *successful
attached-HEAD resolution inside a hook invocation*. It is therefore not "a worktree that was ever
attached to a real branch", but "a worktree in which a monitoring hook ran while attached, at some
point after this module existed". A long-lived worktree that happened to be sitting on a detached
HEAD when the module landed never seeds the sidecar, and stays in the last-resort branch
permanently — not rarely, and not degraded-once, but on every hook call until something reattaches
HEAD there.

**Observed live, 2026-09-27**, in
`.claude/worktrees/agent-monitoring-data-quality-fix`, a worktree that has been attached to at
least 20 distinct real branches over its life:

- `.claude/current_batch` does not exist (it is gitignored, `.gitignore:297`, so it is per-worktree
  and cannot arrive via a merge).
- Resyncing the worktree to `origin/main` with `git checkout --detach` produced an untracked
  `agent-monitoring/data/2026-W39/detached-3314be4bb606.tools.jsonl` with 9 hook-written rows,
  alongside the 4 legitimately branch-keyed shard files already in that directory.

**Not a data-loss bug.** `monitoring_consolidation.py:51` globs `*.{kind}.jsonl`, so the orphan file
is picked up by consolidation and the index. The cost is filename-space pollution and a
per-detached-SHA fragment count that the docstring's own rationale assumed would be rare.

**A recovery path exists that fits the module's stated constraints.** The docstring rejects
`git rev-parse`/`git symbolic-ref` on correctness *and* hot-path cost grounds ("two small file
reads, no subprocess"), and that rejection is sound. But the worktree's own reflog is a plain file
at `<resolved gitdir>/logs/HEAD`, readable with exactly the same discipline — no subprocess. In the
worktree above, it yields 20+ real branch names, and its most recent
`checkout: moving from <x> to <branch-name>` entry is a direct answer to "what branch was this
worktree last attached to". This makes the documented coverage claim achievable rather than
aspirational.

## Scope

- Reconcile `monitoring_batch_identifier.py`'s documented coverage claim with its actual behavior.
  Either close the gap or narrow the claim — see Assumptions / Open Questions for the options and
  the recommendation.
- If the seeding path is implemented: read the resolved gitdir's `logs/HEAD` with plain file reads
  only (no subprocess), take the most recent `checkout: moving from ... to <name>` target that is a
  real local branch name, and seed `.claude/current_batch` from it. Attached-HEAD resolution stays
  authoritative and unchanged; this only inserts a step between the sidecar and the
  `detached-<sha>` last resort.
- Tests for: reflog present with a resolvable branch, reflog present but every entry is a bare SHA,
  reflog absent entirely, reflog naming a branch that no longer exists, and the ordinary
  attached-HEAD path still short-circuiting before any of this runs.
- Update the docstring's rationale block to state whichever coverage guarantee the implementation
  actually provides after this ticket.

## Out of Scope

- **Re-litigating the `detached-<sha>` design decision itself.** The fragmenting last-resort label,
  and the choice not to try to make it stable across detaches without a branch name to anchor to,
  are deliberate, documented, and correct. This ticket does not remove that branch — it only stops
  it from being reached in a case the module claims is already covered.
- Replacing the direct-file-read approach with `git` subprocess calls anywhere on the hook path.
  The existing rejection of that stands.
- Retroactively renaming or merging existing `detached-*.jsonl` files. Consolidation already reads
  them; leave the historical ones alone.
- The 9 read sites being consolidated by `TCK-20260926-MONITORING-READ-PATH-CONSOLIDATION`. That
  ticket is in flight on `monitoring-and-delivery-batch-2` and owns the read path; this ticket is
  write-path identifier resolution only. **Sequence this one after it** to avoid touching a module
  it may still be moving.

## Acceptance Criteria

1. `monitoring_batch_identifier.py`'s docstring coverage claim and its implementation agree — a
   reader cannot conclude from the docstring that a case is covered when it is not.
2. No `git` subprocess is introduced on the hook resolution path (assert by inspection; the module
   currently has zero and the docstring records that as deliberate).
3. Attached-HEAD resolution is unchanged and still short-circuits first.
4. The five reflog cases named in Scope have tests, including the two degenerate ones (no reflog,
   all-SHA reflog) falling through to `detached-<sha>` without raising.
5. In a worktree with no `.claude/current_batch` and a reflog naming a real branch, a hook
   invocation writes to that branch's shard file, not a `detached-<sha>` one.
6. `detached-<sha>` remains reachable and still prints its warning when nothing else resolves —
   verified by a test, not just by the branch still existing in the source.

## Related Tickets

- `TCK-20260926-MONITORING-READ-PATH-CONSOLIDATION` — in flight; owns the read side. Sequence after.
- `TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET` — the sibling write-target ticket from the same
  shard-keying batch.

## Related Docs

- `docs/agent-monitoring/README.md`
- `docs/guides/delivery_process.md` — "Worktree & Branch Isolation", which sanctions the
  same-directory-fresh-branch fallback the sidecar's refresh-on-every-resolution design protects
  against.

## Related Stored Artifacts

None yet.

## Related Code Areas

- `tools/agent-monitoring/monitoring_batch_identifier.py` — the resolution chain and its docstring.
- `tools/agent-monitoring/post_tool_hook.py` — the hot-path caller.
- `tools/agent-monitoring/monitoring_consolidation.py` — the `*.{kind}.jsonl` glob that keeps this
  from being data loss.
- `.gitignore:297` — `.claude/current_batch`.

## Assumptions / Open Questions

**The one real decision: close the gap, or narrow the claim?**

- **Option A — seed the sidecar from the worktree reflog (recommended).** Verified feasible above:
  plain file read, no subprocess, 20+ branch names available in the observed case, and the most
  recent checkout entry is exactly the value wanted. Makes the docstring's existing claim true
  rather than editing it down. Costs one more file read, and only on the path that is already the
  slow fallback — never on the attached-HEAD hot path.
- **Option B — narrow the docstring claim to match the code.** Zero behavior change, near-zero
  cost. But it leaves this worktree, and any other worktree detached at the wrong moment, generating
  a fragment per SHA forever, which is the outcome the rationale assumed was rare.

Recommend **A**, with the docstring updated to state the reflog step explicitly. B is the acceptable
fallback if investigation finds the reflog unreliable in a way the observed case did not show — e.g.
if `gc.reflogExpire` pruning or a `logs/HEAD`-less worktree turns out to be common here rather than
theoretical. That reliability question is the thing investigation should settle first.

Open, smaller:

- Should a reflog-recovered branch name be validated against `refs/heads/` before use, or is a
  stale-but-real-looking name acceptable? The sidecar is a cache for attribution, not a git
  operation, so a deleted branch's name may still be the correct attribution for those rows — but
  this should be decided deliberately, not fall out of the implementation.
- Should the recovered value be written to the sidecar (persisting it, so later calls are cheap) or
  only used in-memory? Writing it matches the existing refresh-on-resolution design; not writing it
  keeps the sidecar meaning "a real attached resolution happened here".

## Implementation Notes

_To be filled during implementation._

## Test Summary

_To be filled during implementation._

## Files Changed

_To be filled during implementation._

## Completion Summary

_To be filled during implementation._

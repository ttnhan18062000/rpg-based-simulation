---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX
phase: done
date: 2026-09-25
tags: [observability, testing]
---

# TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX

## Title

Re-key monitoring-shard writes from per-ticket to per-PR/batch, and fix the two write sites that
never adopted per-identifier branching at all

## Status

DONE

## Tier

standard

## Type

bug

## Priority

P1

## Request Summary

The user inspected this branch's own emitted monitoring files and found
`TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE`'s per-ticket write path never
fired for `runs.jsonl`/`events.jsonl` — every one of today's 14 ticket closures landed its run and
event records in the shared week files, not per-ticket ones. agent-working-design verified this
independently. Root cause: `tools/agent-monitoring/record_hand_orchestrated_closure.py` (the
wrapper CLAUDE.md instructs every hand-orchestrated close to use) still hardcodes the shared paths
— a fourth, unmigrated copy of the write-target formula, missed because the prior ticket's tests
exercised the writer modules directly rather than the real closure path. A full sweep found a fifth
independent copy (`shadow_reviewer_events.py`) with the same gap, plus a genuine key-identity
mismatch (`post_tool_hook.py` keys by `ticket_id`, everything else by `run_id`).

The user's design decision, relayed and confirmed: **key per PR/batch, not per ticket** — this
14-ticket batch should produce exactly 3 files total (one `runs.jsonl`, one `events.jsonl`, one
`tools.jsonl`), not up to ~42. Per agent-working-design/the user: **land this fix on
`github-delivery-process-epic`, riding PR #246** — not a fresh branch — since the defect is in code
this same PR introduced and shipping an inert feature on the repo's actual (hand-orchestrated)
usage path would be worse than the extra churn on an already-open PR.

## Scope

1. New shared module `tools/agent-monitoring/monitoring_batch_identifier.py`:
   `resolve_batch_identifier()` — subprocess-free branch-name resolution (direct `.git`/worktree-
   gitlink-aware `HEAD` file read), a `.claude/current_batch` self-healing sidecar fallback for
   detached HEAD, and a final `detached-<sha>` labeled fallback that never silently collapses to
   the shared filename. `sanitize_for_filename()` for branch names containing `/`.
2. Rewire all six write sites to the one shared resolver: `record_run.py`, `record_events.py`,
   `retrieval_events.py`, `record_hand_orchestrated_closure.py` (the headline fix — currently
   hardcodes the shared path entirely), `post_tool_hook.py` (currently keys by `ticket_id`,
   reconciled to the same scheme as everything else), `shadow_reviewer_events.py` (currently has no
   per-identifier branch at all — the fifth copy).
3. Fix `implement-ticket.js:631`'s dead `record_events.EVENTS_FILE` reference (an attribute removed
   by `TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY`, silently swallowed by a `try/except: pass` —
   confirmed already fully inert, not a live risk this ticket worsens) to use the shared resolver.
4. Update `monitoring_consolidation.py`'s tests (not its code — confirmed already
   identifier-shape-agnostic) with a mixed old/new-shape fixture.
5. Real, subprocess-level end-to-end test proving a real closure produces exactly the per-PR files
   and leaves shared files untouched — the exact gap unit tests over the writer modules alone did
   not catch.
6. Update every existing test asserting the old per-ticket/per-run_id filename shape.

## Out of Scope

- Rewriting `monitoring_consolidation.py`'s own fold logic (confirmed unnecessary — its glob is
  already identifier-shape-agnostic).
- Building automated test coverage for the `SHADOW_CONTEXT_PACKET_ENABLED` shadow-packet path
  beyond fixing its dead attribute reference — no test harness exists for it today; out of scope
  per plan.md.
- Re-deriving whether per-PR (vs. per-ticket) is the right granularity — the user's already-made
  decision, not re-litigated here.
- `writer.py`'s own lock-retry mechanism — untouched.
- A fresh branch — explicitly decided against; this rides `github-delivery-process-epic`/PR #246.

## Acceptance Criteria

1. A real hand-orchestrated closure (proven via a real subprocess invocation in a scratch repo, not
   by calling internal functions) produces exactly one new `<batch-id>.runs.jsonl`, one
   `<batch-id>.events.jsonl` (plus the pre-existing `<batch-id>.tools.jsonl` behavior) — never the
   shared files.
2. That same real closure leaves the pre-existing shared `{runs,events,tools}.jsonl` files
   byte-identical (untouched).
3. Detached HEAD without a `.claude/current_batch` sidecar resolves to a clearly-labeled
   `detached-<sha>` identifier, never the bare shared filename or the literal string `"HEAD"`.
4. Detached HEAD *with* a sidecar (self-healed by a prior attached-branch resolution in the same
   worktree) resolves to the sidecar's value.
5. All six rewired write sites resolve to the identical identifier given the same repo state —
   the `run_id`-vs-`ticket_id` mismatch is gone.
6. `resolve_batch_identifier()`'s own module makes no `subprocess`/`Popen`/`os.system` call —
   `post_tool_hook.py` fires on every tool call and must not gain new shell-out overhead.
7. `monitoring_consolidation.py` folds a mixed corpus of old per-ticket-shaped and new
   per-PR-shaped files correctly.
8. Full `tests/tools/` regression passes.
9. **After pushing, this branch's own next real monitoring write lands in one new per-PR file** —
   checked directly against the actual file on disk, not inferred from green tests. Reported with
   the exact observed filename.
10. PR #246's title and body updated to reflect the 15th closed ticket, same discipline as before
    (`Closes:` body-only, no attribution trailer, title count and theme both current since the
    repo squash-merges and the title becomes the permanent mainline record).
11. `pr_status.py --pr 246` re-checked GREEN against the branch's real new head after this lands —
    not the prior, now-stale `1833e6494` result.

## Related Tickets

- `TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE` — the ticket whose own AC1/AC2
  (per-identifier `runs.jsonl`/`events.jsonl` write path) is fixed here; that ticket stays closed
  (the user's explicit call — fix forward, don't reopen).
- `TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY` — removed `record_events.EVENTS_FILE`, the
  attribute `implement-ticket.js:631` still (dead-)referenced.
- `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` — built
  `record_hand_orchestrated_closure.py`, the file at the center of this ticket's headline fix.
- `TCK-20260904-SHADOW-REVIEWER-LOGGING` — built `shadow_reviewer_events.py`, the fifth copy.

## Related Docs

- `docs/agent-monitoring/schema.md` — if it documents the per-identifier write scheme, update to
  reflect per-PR/batch keying (checked and updated during Implement if applicable).

## Related Stored Artifacts

- `stored_artifacts/TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX/` (this ticket's own
  investigation.md, plan.md, test_plan.md).

## Related Code Areas

- `tools/agent-monitoring/monitoring_batch_identifier.py` (new)
- `tools/agent-monitoring/record_run.py`
- `tools/agent-monitoring/record_events.py`
- `tools/retrieval_events.py`
- `tools/agent-monitoring/record_hand_orchestrated_closure.py`
- `tools/agent-monitoring/post_tool_hook.py`
- `tools/agent-monitoring/shadow_reviewer_events.py`
- `.claude/workflows/implement-ticket.js`
- `tools/agent-monitoring/monitoring_consolidation.py` (tests only)

## Assumptions / Open Questions

1. Whether `docs/agent-monitoring/schema.md` (or any doc) documents the per-ticket write scheme in
   enough detail to need an update — checked during Implement, not assumed either way.
2. Whether `record_run.py`/`record_events.py` expose a write function `record_hand_orchestrated_closure.py`
   can call directly (rather than re-deriving the file path a fourth time) — checked during
   Implement; if their `main()` entry points don't cleanly separate validation from writing, the
   wrapper will call the shared resolver directly instead, accepting one more (correct, shared) copy
   of the *resolver call* rather than forcing an awkward refactor of `main()` boundaries.

## Implementation Notes

New shared module `tools/agent-monitoring/monitoring_batch_identifier.py`:
`resolve_batch_identifier()` reads `.git` directly (handling both a plain directory and a
worktree gitlink file, confirmed against this repo's own real worktree shape) and the resolved
gitdir's `HEAD` file, distinguishing attached (`ref: refs/heads/<name>`) from detached (raw SHA)
without the `git rev-parse --abbrev-ref HEAD` → literal `"HEAD"` trap. No subprocess call
anywhere in the module (confirmed by its own dedicated test) — `post_tool_hook.py` fires on every
tool call and makes zero subprocess calls today, so this avoids adding a real per-invocation cost
to the hottest path in the system.

`.claude/current_batch` self-healing sidecar for detached HEAD: refreshed on **every** successful
attached-HEAD resolution, never write-once — a write-once design would go stale the moment a
worktree switches branches, which CLAUDE.md explicitly sanctions as a normal path (the
same-directory-fresh-branch fallback), not an edge case. This sidecar shares `.claude/current_run`'s
*shape* (single file per worktree) but not its known contamination bug: that bug is a
session-scoped field (`run_id`) sharing state across sessions with legitimately different
values; a batch/PR identifier is branch-scoped, and every session in one worktree shares that one
branch, so a shared sidecar is the correct granularity here, not an accident repeating the same
mistake — documented explicitly in the module's own docstring so a future reader doesn't conflate
the two. `detached-<sha>` (final fallback, no sidecar available) is a deliberate,
intentionally-fragmenting last resort, not a mode to "optimize away."

`resolve_write_target(kind, iso_week=None, cwd=None)` takes `iso_week` as a caller-supplied
parameter rather than computing it internally — found necessary after an initial version broke
every existing week-boundary-freeze test (`_freeze_now` monkeypatching e.g. `record_run.datetime`
has no effect on a `datetime.now()` call inside this different module). This function resolves
WHO (the batch identifier); each caller still decides WHEN, matching its own pre-existing
`datetime.now(timezone.utc).strftime(...)` convention and keeping every existing freeze-based test
working unchanged in spirit (only the expected filename shape needed updating).

Rewired all six write sites (`record_run.py`, `record_events.py` — simplified: no longer groups
records by `run_id` before writing, since the identifier no longer depends on record content at
all, so one `write_lines()` call per batch again, restoring the "one call = one contiguous block"
property to its simplest form — `retrieval_events.py`, `record_hand_orchestrated_closure.py` — the
headline fix: this wrapper never adopted the prior ticket's per-identifier scheme at all, instead
of re-deriving the write path, it now delegates to the shared resolver directly — `post_tool_hook.py`
— reconciled its own `ticket_id`-keyed branch to the shared scheme, and removed its own
now-fully-dead local `iso_week` variable (was only ever used for the old write-path branch) —
`shadow_reviewer_events.py` — the confirmed 5th independent copy, which never had a per-identifier
branch at all).

Full-repo sweep (`grep -rn '"agent-monitoring/data"'`, `grep -rn iso_week`) before touching
anything, per investigation.md, confirmed exactly these six write sites and no seventh. Also fixed
`implement-ticket.js:631`'s `record_events.EVENTS_FILE` reference — confirmed via direct grep that
this attribute has not existed on `record_events` since `TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY`,
so this was a fully dead, silently-swallowed `AttributeError` since before this epic started, not a
live risk this redesign worsens; fixed anyway since the fix is cheap once the resolver exists.

`monitoring_consolidation.py` needed no code change (confirmed: its glob,
`week_dir.glob(f"*.{kind}.jsonl")`, is identifier-shape-agnostic) — added a mixed old-shape/new-shape
fixture test to prove it, rather than just asserting the code was unchanged.

Every existing test asserting the old per-ticket/per-run_id filename shape was found by running
each affected file, not assumed from a code-level scan: `test_record_run.py` (6),
`test_record_events.py` (9), `test_post_tool_hook.py` (14, plus a real concurrency hazard found
and fixed — `_ensure_git_repo_on_test_branch`'s own idempotent git-init check is not itself safe
against N threads racing their first call simultaneously; fixed by pre-initializing the repo
before spawning the thread pool in that one test), `test_retrieval_events.py` (1),
`test_record_hand_orchestrated_closure.py` (6, plus one new acceptance test),
`test_execution_identity_end_to_end.py` (3, requiring a deeper semantic redesign — this file's own
premise, "a ticket-scoped write creates a brand-new file with no pre-existing content," no longer
holds once the identifier is branch- not ticket-scoped; rewrote its seeding/assertions around the
real per-branch file rather than patching the old assertions to a new filename).

## Test Summary

- `python3 -m pytest tests/tools/test_monitoring_batch_identifier.py -v` — **9 passed** (attached
  branch resolution, worktree-gitlink resolution, detached-HEAD fallback + its printed warning,
  sidecar self-heal, slash-sanitization, write-target shape with both explicit and default `cwd`,
  no-subprocess-call source check).
- `python3 -m pytest tests/tools/test_record_run.py tests/tools/test_record_events.py
  tests/tools/test_post_tool_hook.py tests/tools/test_retrieval_events.py
  tests/tools/test_record_hand_orchestrated_closure.py tests/tools/test_monitoring_consolidation.py
  tests/tools/test_execution_identity_end_to_end.py tests/tools/test_monitoring_batch_identifier.py -q`
  — **173 passed**, 0 failed (every directly-rewired site plus its own existing suite).
- `TestRealClosureProducesExactlyThreePerPRFiles` (new, in
  `test_record_hand_orchestrated_closure.py`): a real subprocess invocation of the actual CLI
  wrapper against a real git repo, with pre-existing shared files seeded — confirms exactly the
  per-PR files are created and the seeded shared files remain byte-identical. This is the test
  that would have caught the original bug; unit tests over the writer modules alone did not.
- Full regression: `python3 -m pytest tests/tools/ -m "not slow and not extra_slow" -q` — **3037
  passed**, 25 skipped, 28 deselected, 1 xfailed, 0 failed.
- Manual check of the `implement-ticket.js:631` fix: confirmed via direct source read that the
  replaced call now imports `monitoring_batch_identifier` (already on `sys.path` from the
  surrounding snippet) and calls `resolve_write_target('events')` in place of the dead
  `record_events.EVENTS_FILE` reference — no automated test added for this gated,
  `SHADOW_CONTEXT_PACKET_ENABLED`-only path, per plan.md's explicit Out of Scope.

## Files Changed

- `tools/agent-monitoring/monitoring_batch_identifier.py` — new.
- `tools/agent-monitoring/record_run.py` — per-branch write target via the shared resolver.
- `tools/agent-monitoring/record_events.py` — per-branch write target; simplified back to one
  `write_lines()` call per batch (no more per-`run_id` grouping).
- `tools/retrieval_events.py` — per-branch write target via the shared resolver.
- `tools/agent-monitoring/record_hand_orchestrated_closure.py` — the headline fix: no longer
  hardcodes the shared path.
- `tools/agent-monitoring/post_tool_hook.py` — reconciled its own `ticket_id`-keyed branch to the
  shared scheme; removed its now-dead local `iso_week` variable.
- `tools/agent-monitoring/shadow_reviewer_events.py` — added the missing per-identifier branch
  (the 5th copy, previously always shared-file).
- `.claude/workflows/implement-ticket.js` — fixed the dead `record_events.EVENTS_FILE` reference.
- `tests/tools/test_monitoring_batch_identifier.py` — new, 9 tests.
- `tests/tools/test_record_run.py`, `test_record_events.py`, `test_post_tool_hook.py`,
  `test_retrieval_events.py` — updated existing tests to the new per-branch filename shape.
- `tests/tools/test_record_hand_orchestrated_closure.py` — updated existing tests; added
  `TestRealClosureProducesExactlyThreePerPRFiles`, the central acceptance test.
- `tests/tools/test_monitoring_consolidation.py` — added a mixed old/new-shape fold test.
- `tests/tools/test_execution_identity_end_to_end.py` — semantically redesigned around the new
  per-branch (not per-ticket) write target.
- `.gitignore` — added `.claude/current_batch`, matching the existing
  `.claude/current_run`/`.claude/current_run.*` ephemeral-hook-state precedent.
- `docs/REGISTRY.yaml` — regenerated as part of ticket close (routine, unconditional per the
  Finalize rule).

## Completion Summary

Fixed the actual root cause the user found by inspecting this branch's own emitted monitoring
files: `record_hand_orchestrated_closure.py` (the wrapper CLAUDE.md instructs every
hand-orchestrated close to use) never adopted `TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE`'s
per-identifier write path at all — it hardcoded the shared `runs.jsonl`/`events.jsonl` paths
directly, so every one of this epic's 14 hand-orchestrated ticket closures landed its run/event
records in the shared week files regardless of what the (correctly per-identifier)
`record_run.py`/`record_events.py` write functions did when called directly. A full sweep found a
5th independent copy of the same drifted formula (`shadow_reviewer_events.py`, no branch at all)
and a genuine key-identity mismatch (`post_tool_hook.py` keyed by `ticket_id`, everything else by
`run_id`) — both fixed by routing every write site through one new shared resolver module.

Re-keyed from per-ticket to per-PR/batch (the user's explicit design decision, relayed via
agent-working-design): the real conflict this whole mechanism exists to avoid is between two
different branches' concurrent writes at merge time, not between tickets sharing one branch — so
a 14-ticket batch now produces 3 files total, not up to 42. The identifier is resolved without any
subprocess call (a direct `.git`/worktree-gitlink-aware `HEAD` file read), since `post_tool_hook.py`
fires on every tool call and had zero existing subprocess use to build on. Detached HEAD — a real,
not hypothetical, case (agent-working-design's own session ran detached all day) — is handled by a
self-healing `.claude/current_batch` sidecar, refreshed on every successful attached resolution
(never write-once, which would go stale the moment a worktree switches branches, a CLAUDE.md-
sanctioned normal path) with a clearly-labeled `detached-<sha>` last resort that never silently
collapses to the shared filename.

Also fixed a fully dead (since before this epic started) attribute reference in
`implement-ticket.js:631`, found during the same sweep, and added a real subprocess-level
end-to-end test (`TestRealClosureProducesExactlyThreePerPRFiles`) that invokes the actual CLI
wrapper — the exact test class whose absence let the original bug pass unnoticed, since every
prior test exercised the writer functions directly rather than the wrapper real closures go
through.

**Migration state, disclosed per agent-working-design's explicit instruction**: this branch's
earlier commits (everything before this ticket's own) wrote their monitoring rows to the shared
`2026-W39/{runs,events,tools}.jsonl` files, under the (buggy) pre-fix wrapper behavior. This
ticket's own commits (from here forward) write to the new per-branch file. Both are visible in the
same PR diff — this is the correct, disclosed final state of a mid-PR migration, not a leftover
defect.

**Acceptance evidence, checked directly against the real file, not inferred from tests**: this
ticket's own hand-orchestrated closure was itself the first real closure since the fix. It created
exactly `agent-monitoring/data/2026-W39/github-delivery-process-epic.{runs,events,tools}.jsonl` —
the real current branch name, not a ticket ID — with this ticket's own run/event data
(`run_id`/`ticket_id`: `TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX`, 7 events). `git diff --stat`
against the pre-existing shared `agent-monitoring/data/2026-W39/{runs,events}.jsonl` shows zero
changes — confirmed untouched, not asserted.

No known material gap. `docs/agent-monitoring/schema.md` was checked (per Assumption 1) and found
to never have documented the per-ticket scheme in the first place, so no doc update was needed.

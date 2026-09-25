---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX
artifact_type: plan
phase: inprogress
date: 2026-09-25
tags: [observability, testing]
---

# Plan — TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX

## Summary

Re-key the monitoring-shard per-identifier write path from per-ticket to per-PR/batch (the user's
explicit design decision), fix the wrapper that never adopted the per-identifier scheme at all
(the headline bug — `record_hand_orchestrated_closure.py`), fix a second independently-missed site
(`shadow_reviewer_events.py`), reconcile the `run_id`-vs-`ticket_id` key mismatch, and add tests
that assert against real emitted files from a real closure — not just unit tests over the writer
functions in isolation.

## New module: `tools/agent-monitoring/monitoring_batch_identifier.py`

Single source of truth for "what identifier does this write/read belong to", replacing every
ad-hoc `run_id`/`ticket_id` branch across the five-plus write sites.

```
resolve_batch_identifier(cwd: Path | None = None) -> str
```

Resolution order:
1. **Live branch name**, via a subprocess-free file read (no `git` shell-out):
   - Read `<cwd>/.git`. If it's a directory, the real gitdir is `<cwd>/.git` itself. If it's a
     file, parse `gitdir: <path>` and use `<path>` as the real gitdir (the worktree-gitlink case —
     confirmed this repo's normal mode).
   - Read `<gitdir>/HEAD`. If it starts with `ref: refs/heads/`, return the branch name (the part
     after that prefix, stripped).
   - If it's a raw SHA (detached — no `ref:` prefix), this step yields nothing; fall through.
2. **`.claude/current_batch` sidecar** (new, parallel to the existing `.claude/current_run`
   pattern): if step 1 found nothing (detached) and this file exists and is non-empty, return its
   content.
3. **Self-heal**: whenever step 1 *does* resolve a real branch name, write it to
   `.claude/current_batch` (only if different from the current content, to avoid needless writes on
   every single call) — so a later detached invocation in the same worktree recovers it via step 2.
4. **Final fallback**: neither step 1 nor step 2 yielded anything (a genuinely fresh worktree,
   never on a named branch, no sidecar yet) — return `f"detached-{short_sha}"` (first 12 hex chars
   of the raw `HEAD` content) and print one `WARNING:` to stderr. Never returns `""`/`None`/a value
   that collapses to the shared filename.

Memoized at module level per `(cwd,)` for the lifetime of one Python process — harmless (each
`post_tool_hook.py`/`record_hand_orchestrated_closure.py` invocation is its own process, so this
memoization only helps the latter, which calls the resolver multiple times in one run) and cheap
to add.

`sanitize_for_filename(identifier: str) -> str`: branch names can contain `/` (e.g.
`feature/foo`) which is not a valid filename component. Replace `/` with `-` (matching this
project's own `TCK-` naming convention of hyphen-separation, and avoiding any need to create
subdirectories under `agent-monitoring/data/<week>/`). Documented as a real, disclosed lossy
mapping (two differently-slashed branch names could theoretically collide after sanitization) —
acceptable given branch names in this repo don't currently use `/`, confirmed by
`git branch -a | grep '/' | grep -v remotes` returning only remote-tracking refs, no local
slashed branch names.

## Sites to rewire (all six write sites, all read the same resolved identifier)

1. **`tools/agent-monitoring/record_run.py`** — replace its own `run_id`-based branch with a call
   to `resolve_batch_identifier()` (keeping `run_id` as a *field inside* the record, unchanged —
   only the *file-targeting* key changes).
2. **`tools/agent-monitoring/record_events.py`** — same swap.
3. **`tools/retrieval_events.py`** — same swap (mirrors `record_events.py`'s target computation by
   its own docstring's stated intent; keep that mirroring, now pointed at the shared resolver
   instead of re-deriving `run_id`-keyed logic independently).
4. **`tools/agent-monitoring/record_hand_orchestrated_closure.py`** — the headline fix. Stop
   hardcoding `runs_file`/`events_file`; call `resolve_batch_identifier()` once and use it for both
   file targets, matching the other write functions' now-shared logic. Prefer delegating to
   `record_run.py`/`record_events.py`'s own write functions directly (if they expose a
   file-writing entry point beyond `main()`) over re-deriving the path a fourth time — checked
   during Implement, since this is exactly the kind of drift-inducing duplication the whole
   investigation is about.
5. **`tools/agent-monitoring/post_tool_hook.py`** — replace its `ticket_id`-based branch with the
   shared resolver (reconciles Root cause 3 — one identifier scheme, not two).
6. **`tools/agent-monitoring/shadow_reviewer_events.py`** — add the missing branch (it currently
   has none at all), using the shared resolver.

## `implement-ticket.js:631`

Replace `record_events.EVENTS_FILE` (a already-removed, dead attribute reference silently
swallowed by the surrounding `try/except: pass` — confirmed inert since
`TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY`, not a live risk this ticket worsens) with a call
into the new resolver from the embedded Python snippet (`sys.path.insert(0, 'tools/agent-monitoring')`
already present; add an import of the new module and use its resolved target file for the
`load_jsonl(...)` call). Verify with the existing `SHADOW_CONTEXT_PACKET_ENABLED=1` manual gate,
not a new test harness — this path already has no automated test coverage per its own comment
("no real retrieval pipeline wired in") and adding one is out of scope here.

## `monitoring_consolidation.py`

No code change (investigation.md confirmed its glob is already identifier-shape-agnostic). Update
its existing tests' fixtures to use a per-PR-shaped identifier (e.g. `some-branch-name.tools.jsonl`)
alongside the existing per-ticket-shaped ones, proving both shapes fold correctly — since real
historical per-ticket files from before this fix will coexist with new per-PR files until the next
retro consolidation run.

## Migration state — disclosed, not hidden

This ticket's own commits will themselves be hand-orchestrated closures. Once the fix lands
mid-ticket, **this very ticket's own later phases (Test, Verify, Finalize) will be the first real
proof**: their monitoring rows must land in one new per-PR-named file, not the shared one. Recorded
explicitly in Test Summary/Completion Summary which rows landed where and why, per
agent-working-design's instruction — a reviewer must not have to infer this from the diff.

## Acceptance-criteria map

| AC | Where verified |
|---|---|
| Real closure produces exactly 3 new per-PR files (not per-ticket, not 0) | New end-to-end test in `tests/tools/test_monitoring_batch_identifier.py` invoking `record_hand_orchestrated_closure.py` as a real subprocess against a scratch repo, then asserting on the actual files it created |
| Shared `{runs,events,tools}.jsonl` untouched by that same real closure | Same test — asserts the shared files' `mtime`/content unchanged after the run |
| Detached HEAD does not silently fall back to the shared file | Dedicated test constructing a detached-HEAD scratch repo, no `.claude/current_batch` present, asserting the `detached-<sha>` shape, not the shared filename |
| `.claude/current_batch` self-heals a later detached call | Test: resolve on an attached branch (writes the sidecar), then simulate detached HEAD in the same scratch dir, confirm the sidecar's value, not the SHA fallback, is returned |
| `post_tool_hook.py` and `record_run.py`/`record_events.py` agree on one identifier | Test asserting all six rewired call sites, given the same scratch repo state, resolve to the identical string |
| `monitoring_consolidation.py` folds both old (per-ticket) and new (per-PR) shaped files | Existing consolidation tests extended with a mixed-shape fixture |
| No subprocess call added to `post_tool_hook.py`'s hot path | Static test: `grep`/AST-scan `resolve_batch_identifier`'s own module source for `subprocess`/`Popen` — must be absent |
| This branch's own next real closure lands in one per-PR file | Not a unit test — a live, disclosed check against this branch's actual push, reported in the ticket, per agent-working-design's explicit instruction |

## Out of Scope

- Rewriting `monitoring_consolidation.py`'s own logic (confirmed unnecessary).
- Adding automated test coverage for the `SHADOW_CONTEXT_PACKET_ENABLED` shadow-packet path beyond
  fixing its dead attribute reference — that path has no test harness today and building one is a
  separate, larger effort.
- Re-litigating whether per-PR (vs. per-ticket) is the right granularity — that is the user's
  already-made design decision, not open for re-derivation here.
- Any change to `writer.py`'s own lock-retry mechanism.

## Risks / open items for Review

- Branch-name sanitization (`/` → `-`) is a real, disclosed lossy mapping with no current
  collision risk (verified no local branch names contain `/`) but no guard against one in the
  future. Accepted, not hardened further, matching this repo's own precedent for similarly-scoped
  disclosed residual risks (e.g. `TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX`'s partial-install
  gap).
- The migration leaves a mixed-shape corpus (old per-ticket files, older-still shared-file rows,
  new per-PR files) until the next retro consolidation run. Disclosed in Completion Summary with
  exactly which rows are where.

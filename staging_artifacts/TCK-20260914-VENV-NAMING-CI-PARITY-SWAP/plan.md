---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260914-VENV-NAMING-CI-PARITY-SWAP
phase: open
date: 2026-09-15
tags: [ai, process-improvement]
---

# Plan — TCK-20260914-VENV-NAMING-CI-PARITY-SWAP

## Why this plan stops short of executing the rename

The rename (`mv .venv .venv-knowledge && mv .venv313 .venv`, or equivalent) mutates shared
filesystem state outside this repo's git tree, used by every concurrent session on this machine —
not just this one. Per this session's own risk-handling convention, that is exactly the class of
action ("affects shared systems beyond your local environment") to surface for confirmation rather
than execute opportunistically, and the peer reviewing this batch independently suggested the same
sequencing. This plan prepares every file change needed so the rename itself is a single, fast,
mechanical step once timing is confirmed — not a reason to delay preparing the rest.

## Step 1 — draft (not yet committed) all tracked-file changes needed once the rename lands

**Correction made while writing this plan**: an earlier draft of this section called these edits
"safe to do anytime, no shared-state risk." That's wrong and was caught before committing it.
`tools/start_search_mcp.sh` is a per-worktree tracked file (confirmed via its own comment) that any
session sharing this branch could pull/see — the peer's own worktree
(`.claude/worktrees/agent-monitoring-data-quality-fix`) has this exact branch checked out right
now. If the edited script (pointing at `.venv-knowledge`) is committed and pushed *before* the
actual rename happens, any session that pulls it and then runs `search_docs` would break
immediately, against a path that does not exist yet — the exact failure this ticket exists to
prevent, self-inflicted by landing the two steps out of order. **Step 1 and Step 2 must land
together, atomically** (same commit, executed immediately before/alongside the `mv` in Step 2) —
not committed ahead of time. The edits below are fully specified and ready to apply verbatim at
that moment; they are intentionally not yet written to the tracked files.

1. **`tools/start_search_mcp.sh`** — change the absolute hardcoded first candidate from
   `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` to
   `/home/u24desktop/Working/rpg-based-simulation/.venv-knowledge/bin/python3` (name pending
   confirmation — see Open Question below). Update the comment above it to match.
2. **`Makefile`** — add a dedicated interpreter-resolution variable for the knowledge stack,
   independent of `$(PYTHON3)`:
   ```make
   PYTHON_KNOWLEDGE := $(shell for py in .venv-knowledge/bin/python3 /home/u24desktop/Working/rpg-based-simulation/.venv-knowledge/bin/python3 python3; do [ -x "$$py" ] && echo "$$py" && break; done)
   ```
   Point `knowledge-index`, `knowledge-index-update`, and `eval-search` at `$(PYTHON_KNOWLEDGE)`
   instead of `$(PYTHON3)`/the inline discovery loop. Every other `$(PYTHON3)`/`$(PYTHON)` target
   is left untouched — those become *more* correct once `.venv` is the CI-matching env, not broken.
3. **`docs/guidelines/agent_working_environment.md`** — swap the venv table's names (CI-matching
   env becomes `.venv`, knowledge-only env becomes `.venv-knowledge`), update the "Run tests as..."
   sentence to say `.venv/bin/python3` (now correct, matching CI, matching the whole point of this
   ticket), update the "must be preserved" paragraph's cited path, and change the first-time-setup
   `uv venv .venv313 ...` recipe to build the *new* env under its final name from the start (a
   fresh machine following this doc post-swap should never create a stray `.venv313`).
4. **`tools/perf/live_map_ws_payload_measure.py`** — update the docstring's example invocation for
   consistency (not functionally required, but leaving a stale `.venv/bin/python3` example next to
   a doc that now says `.venv` is the CI-matching env would itself become a small, confusing
   instance of exactly the documentation-decay pattern this whole batch has been about).

All four of these are ordinary git-tracked file edits — reviewable, revertable, no different from
any other ticket's changes. Prepare and commit them, but do not run any `mv`/rename command in the
same step.

## Step 2 (the actual rename — requires confirmed timing, NOT executed by this implementation)

```bash
mv /home/u24desktop/Working/rpg-based-simulation/.venv /home/u24desktop/Working/rpg-based-simulation/.venv-knowledge
mv /home/u24desktop/Working/rpg-based-simulation/.venv313 /home/u24desktop/Working/rpg-based-simulation/.venv
```

**This must not run while any other session on this machine might be mid-command against
`.venv/bin/python3`.** Recommended sequencing, surfaced to the user rather than decided here:
- Confirm via `ListAgents` (or asking directly) that no other session is actively running a
  command against the shared venv at the moment of the swap.
- Run the two `mv` commands back-to-back in one shell invocation (no gap between them) so there is
  no window where neither name exists.
- Immediately after, verify (Step 3) before considering the ticket's own rename step complete.

## Step 3 — verification (AC checklist, run immediately after Step 2)

1. `.venv/bin/python3 --version` reports `3.13.x` (AC #1).
2. A real `mcp__knowledge-search__search_docs` query returns non-empty, real results, not just "the
   MCP server started" (AC #2 — see investigation.md's note on why the weaker check is insufficient).
3. `grep -rn "/home/u24desktop/Working/rpg-based-simulation/\.venv[^-]" .` (excluding
   `tickets/done/`, `staging_artifacts/`, `stored_artifacts/`, `.git/`) returns zero hits that
   still point at the OLD meaning of `.venv` — i.e., nothing still expects `.venv` to be the
   knowledge/3.12 env after the swap (AC #3).
4. `make knowledge-index-update` runs without an import error (proves Hazard #2's fix actually
   works, not just that it was written).
5. `docs/guidelines/agent_working_environment.md`'s table matches `--version` reality for both
   envs (AC #4).

## Open question to put to the user alongside this plan (not decided here)

The ticket's own Scope says the exact rename target names are "suggested shape, not mandated." This
plan uses `.venv-knowledge` throughout as a concrete, working name so the file edits above are
real and reviewable rather than templated placeholders — but the final name is the user's call, not
assumed. If a different name is chosen, Step 1's edits need the substitution applied before Step 2
runs; trivial since every occurrence is now enumerated above.

## No code changes yet in this implementation pass

Per the sequencing above, this ticket's own artifacts (investigation.md, this plan.md, test_plan.md)
are being committed now; Step 1's actual file edits and Step 2's rename are follow-up work gated on
the user confirming timing, not part of this same commit.

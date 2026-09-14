---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260914-VENV-NAMING-CI-PARITY-SWAP
phase: open
date: 2026-09-14
tags: [ai, process-improvement]
---

# TCK-20260914-VENV-NAMING-CI-PARITY-SWAP

## Title
Default venv name points at the non-CI Python version — rename so `.venv` is the CI-matching environment

## Status
BLOCKED

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
On u24desktop there are now two virtualenvs, deliberately (documented in
`docs/guidelines/agent_working_environment.md`):

- `.venv` — Python 3.12.3, holds the knowledge-search stack (`torch`, `sentence-transformers`)
- `.venv313` — Python 3.13.14, matches CI's declared `python-version: "3.13"`, used for engine/API/tests

**The naming is backwards relative to how the two are used.** `.venv` is the name every tool,
habit, and shell autocompletion reaches for by default, but it is the one that does *not* match CI.
A session running `.venv/bin/python3 -m pytest` — or bare `python3`, which is also 3.12 — gets a
green result that cannot rule out a version-specific CI failure.

That is not hypothetical: on 2026-09-14 two CI jobs failed with unreadable logs (network-filter
blocked), and the Python version gap could not be eliminated as a cause until a 3.13 venv was built
specifically to test it. Several hours were spent on a hypothesis that a correctly-named default
would have ruled out in one command. (The version gap turned out *not* to be the cause — 120 tests
passed identically on 3.13 against the failing commit — but ruling it out was only possible after
the fact.)

## Scope
- Rename so the CI-matching environment is the default-named one. Suggested shape, not mandated:
  `.venv` → `.venv-knowledge` (or similar explicit name), `.venv313` → `.venv`.
- Update `tools/start_search_mcp.sh`, which **hardcodes the absolute path**
  `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` as its first-priority
  candidate. This is deliberate — its own comment explains that per-worktree `$REPO_ROOT/.venv`
  never has the knowledge deps, so the absolute shared path must win. Any rename must update this
  or `search_docs` silently falls through to bare `python3` and stops working.
- Update `docs/guidelines/agent_working_environment.md`'s venv table to match.
- Check for any other hardcoded `.venv` references (Makefile targets, CI scripts, tooling).

## Out of Scope
- Migrating the knowledge stack to 3.13. **Not possible on this network**: `download.pytorch.org`
  is blocked by the content filter (`O = Fortinet, CN = Fortiguard SDNS Blocked Page`), so
  `torch==2.12.1+cpu` cannot be installed for any new Python version here. The 3.12 environment
  must be preserved as-is; it predates the block and cannot be rebuilt.
- Any change to which Python version CI uses.

## Acceptance Criteria
- [ ] `.venv/bin/python3 --version` reports the same major.minor as `.github/workflows/test.yml`'s
      declared `python-version`.
- [ ] `search_docs` still returns results after the rename — verified by a real query, not by the
      MCP server merely starting.
- [ ] No remaining hardcoded reference resolves to the wrong environment (grep, don't assume).
- [ ] The environment doc's venv table matches reality.

## Related Tickets
- None directly. Adjacent in spirit to the CI-triage guidance in CLAUDE.md, which already documents
  the network-filter block for GitHub Actions log fetching — the same filter, different host.

## Related Docs
- `docs/guidelines/agent_working_environment.md` — the venv table, the network-block explanation,
  and the sudo-free `uv` install recipe were added 2026-09-14 alongside this ticket.

## Related Stored Artifacts
- None.

## Related Code Areas
- `tools/start_search_mcp.sh`
- `docs/guidelines/agent_working_environment.md`
- `.mcp.json` (references the launcher, not a venv path directly)

## Assumptions / Open Questions
- **Timing matters more than the change does.** The rename breaks `search_docs` for any session
  running at that moment, and this machine routinely has 8+ concurrent sessions sharing the one
  venv. Do it when sessions are quiet, not opportunistically.
- Unresolved: whether the knowledge stack should eventually move to a container (the search server
  already has a Docker path, `make search-server-docker`) so it stops depending on a host-installed
  torch that can no longer be reinstalled here. That would make the whole venv split unnecessary,
  but it is a larger question than this ticket.

## Implementation Notes
Investigation and plan complete; the actual rename is deliberately **not executed** in this pass.
It mutates shared filesystem state (`.venv`/`.venv313`) used by every concurrent session on this
machine, not just this one — the kind of action this session's own risk-handling convention (and
independently, the peer reviewing this batch) says to surface for confirmation rather than execute
opportunistically.

Two hazards found and fully scoped:
1. **`tools/start_search_mcp.sh`'s hardcoded absolute path** — already named in the ticket's own
   Scope, re-confirmed: after a naive rename this would resolve to an *existing* interpreter that
   lacks `torch`, a louder failure (ImportError) than the ticket's own "silent fallthrough to bare
   python3" framing, but still a real breakage.
2. **`Makefile`'s `knowledge-index`/`knowledge-index-update`/`eval-search` targets** — NOT named in
   the ticket's own Scope, found by grepping per AC #3 rather than assuming the Scope list was
   complete. These resolve via `$(PYTHON3)`, whose first candidate is the relative `.venv/bin/
   python3` — post-rename this becomes the 3.13 env, which lacks the knowledge-search deps these
   three targets need. Every OTHER `$(PYTHON3)`-using target is unaffected (becomes more correct,
   not broken, once `.venv` is the CI-matching env).

**Self-caught correction while writing plan.md**: an earlier draft called the file edits (script,
Makefile, doc) "safe to do anytime" and considered committing them ahead of the actual rename.
That's wrong for a shared-worktree environment — `tools/start_search_mcp.sh` is a per-worktree
tracked file the peer's own concurrent worktree has checked out on this same branch; committing an
edit that points at a not-yet-existing `.venv-knowledge` before the rename actually happens would
break `search_docs` for anyone who pulls it in the interim, which is exactly the failure class this
ticket exists to prevent, self-inflicted by landing the steps out of order. Corrected: the file
edits and the rename must land together, atomically, not staged ahead of time. Full exact diffs are
specified in `plan.md` Step 1, ready to apply verbatim once timing is confirmed.

**This ticket is not implementing the rename or asking the user to approve a vague "when it's
safe" — it's surfacing a concrete plan (exact file diffs, exact `mv` commands, exact verification
checklist) and one open naming decision (`.venv-knowledge` as a working name, user's call per the
ticket's own "suggested shape, not mandated") for a go/no-go decision on timing.**

## Test Summary
No code changed — investigation and planning only. See `test_plan.md` for the verification
checklist that runs once the rename itself executes (a future step, not part of this pass).

## Files Changed
- `staging_artifacts/TCK-20260914-VENV-NAMING-CI-PARITY-SWAP/` (investigation.md, plan.md,
  test_plan.md — new).
- This ticket file (Implementation Notes/Test Summary/Files Changed/Completion Summary; `## Status`
  set to `BLOCKED`).
- No `src/`, `tools/`, `Makefile`, or `docs/` files touched — those edits are fully specified in
  `plan.md` but deliberately not yet written to the tracked files, per the ordering hazard above.

## Completion Summary
Investigation and plan complete, not yet implemented. Confirmed the ticket's own named hazard
(`tools/start_search_mcp.sh`) and found a second, unnamed one (`Makefile`'s knowledge-stack targets)
by grepping rather than trusting the Scope list was exhaustive. Self-caught and corrected an
ordering mistake in the plan itself (file edits must land atomically with the rename, not ahead of
it) before it could have caused the exact class of breakage this ticket exists to prevent. Left
`BLOCKED`, not `DONE` — the actual rename requires a user go/no-go on timing (concurrent-session
safety) and the final target name, neither of which this session can decide alone.

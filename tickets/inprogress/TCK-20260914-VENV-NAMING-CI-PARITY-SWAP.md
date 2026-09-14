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
OPEN

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
_(to be filled during implementation)_

## Test Summary
_(to be filled during implementation)_

## Files Changed
_(to be filled during implementation)_

## Completion Summary
_(to be filled during implementation)_

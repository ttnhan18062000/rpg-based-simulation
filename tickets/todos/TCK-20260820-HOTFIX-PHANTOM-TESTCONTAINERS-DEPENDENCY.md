---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260820-HOTFIX-PHANTOM-TESTCONTAINERS-DEPENDENCY
phase: open
date: 2026-08-20
tags: [testing]
---

# TCK-20260820-HOTFIX-PHANTOM-TESTCONTAINERS-DEPENDENCY

## Title
testcontainers[redis] is declared in pyproject.toml's dev deps but never referenced anywhere in the codebase

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
Found while auditing `requirements.txt` against all of `pyproject.toml`'s optional-dependency
groups (a follow-up to `TCK-20260820-HOTFIX-REQUIREMENTS-TXT-MISSING-CORE-DEPS`, checking `dev`/
`knowledge`/`search-mcp` groups too, not just core deps). `pyproject.toml`'s `[project.optional-
dependencies].dev` declares `testcontainers[redis]>=4.0.0`. Searched the entire repo (not just
`tests/`) for any import or reference — `grep -rl "testcontainers" . --include="*.py"` (excluding
`.venv/`/`node_modules/`) returns **zero hits**. `TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC`'s own
completion summary mentions "new/extended integration tests against live Redis," but those tests
apparently use a real, already-running Redis instance (e.g. from `docker-compose.yml`'s `redis`
service) rather than `testcontainers`-managed ephemeral containers — meaning the dependency was
declared, presumably anticipating this use, but never actually adopted.

## Scope
- Confirm via `git log -S testcontainers` (pickaxe search) whether this was ever used and later
  removed without cleaning up the declaration, or was declared and never used at all — informs
  whether removal is safe or whether there's a half-finished integration worth completing instead.
- If genuinely unused: remove `testcontainers[redis]>=4.0.0` from `pyproject.toml`'s `dev` extras.
- If a real, still-relevant use case exists (e.g. isolating Redis-dependent tests from a shared
  live instance): that's a larger decision than a hotfix — flag it back as a separate,
  properly-scoped ticket instead of silently either removing or half-adopting it here.

## Out of Scope
- Migrating existing live-Redis integration tests to use `testcontainers` — a real feature
  addition, not this hotfix's scope, only relevant if the `git log -S` check suggests it was the
  original intent and is still wanted.

## Acceptance Criteria
- [ ] The `git log -S testcontainers` history check is done and its finding documented.
- [ ] Either the dependency is removed (if confirmed unused and not wanted), or a follow-up
      ticket is filed for real adoption (if wanted) — not left ambiguous either way.

## Related Tickets
- TCK-20260820-HOTFIX-REQUIREMENTS-TXT-MISSING-CORE-DEPS (the audit that surfaced this while
  checking `pyproject.toml`'s other dependency groups)
- TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC (the epic whose completion summary mentions live-Redis
  integration tests, the likely original motivation for this declaration)

## Related Docs
None beyond this ticket's own evidence.

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- pyproject.toml

## Assumptions / Open Questions
- Whether this was ever actually used and later abandoned, or declared and never adopted, is not
  yet known — resolved by this ticket's own first scope step, not assumed here.

## Implementation Notes
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)

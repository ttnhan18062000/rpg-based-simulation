---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260820-HOTFIX-PHANTOM-TESTCONTAINERS-DEPENDENCY
phase: done
date: 2026-08-20
tags: [testing]
---

# TCK-20260820-HOTFIX-PHANTOM-TESTCONTAINERS-DEPENDENCY

## Title
testcontainers[redis] is declared in pyproject.toml's dev deps but never referenced anywhere in the codebase

## Status
DONE

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
- [x] The `git log -S testcontainers` history check is done and its finding documented.
- [x] Either the dependency is removed (if confirmed unused and not wanted), or a follow-up
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
`git log -S testcontainers --oneline -- .` returned 4 commits: `bfdf91a6` ("Update stacks", commit
#1 — the project's very first, foundational commit, which already declared
`testcontainers[redis]>=4.0.0`), `ff0235a7`/`29d78798` (later `pyproject.toml` touches for
unrelated reasons, `testcontainers` line untouched in both diffs), and `6927d59a` (this session's
own earlier PR, which only touched the *ticket text* mentioning "testcontainers", not
`pyproject.toml`). `git log --all -S "import testcontainers"` and `-S "from testcontainers"` both
return zero commits — confirming this was **declared and never adopted from day one**, not a
"used and later abandoned" case. This resolves the ticket's own scope-step 1 finding cleanly:
removal is safe, no half-finished integration to preserve or complete.

Removed `"testcontainers[redis]>=4.0.0"` from `pyproject.toml`'s `dev` extras. Regenerated
`uv.lock` via `uv lock` to keep it consistent (single atomic resolve — could not be scoped to only
this one package). This also surfaced that `uv.lock` had independently drifted beyond just this
ticket's finding: it still listed `confluent-kafka`, `pika`, and `docker` as resolved packages,
leftover artifacts from before `TCK-20260817-DEAD-INFRA-REMOVAL-EPIC` removed them from
`pyproject.toml` — the lockfile was never regenerated after that epic closed. `uv lock` removed
all 5 stale packages in one pass (`confluent-kafka`, `docker`, `pika`, `testcontainers`, `wrapt` —
the last a transitive dep of the others). Confirmed via grep that none of the 5 removed packages
have any live import anywhere in the repo (`.venv`/`node_modules` excluded).

## Test Summary
Created a genuinely fresh venv and verified both `pip install -e .` (core deps) and
`pip install -e ".[dev]"` (dev extras, now without `testcontainers`) succeed cleanly with no
errors. Scratch venv removed after.

## Files Changed
- pyproject.toml
- uv.lock

## Completion Summary
Confirmed via `git log -S` (both on `pyproject.toml`'s declaration and on any Python import,
across full history) that `testcontainers[redis]` was declared in the project's very first commit
and never actually adopted — a phantom dependency, not an abandoned integration. Removed it from
`pyproject.toml`'s dev extras and regenerated `uv.lock`, which as a side effect also cleaned up 4
more stale lockfile entries (`confluent-kafka`, `docker`, `pika`, `wrapt`) left over from an
earlier epic's `pyproject.toml` removal that never triggered a lockfile regeneration. Verified a
fresh venv install of both core and dev dependency sets still succeeds.

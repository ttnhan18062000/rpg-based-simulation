---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261023-SEMGREP-SEARCH-DOCKERFILE-USER-AND-TRANSIT-SHA1
phase: done
date: 2026-10-23
tags: [ai, governance]
---

# TCK-20261023-SEMGREP-SEARCH-DOCKERFILE-USER-AND-TRANSIT-SHA1

## Title
The two open Semgrep alerts on agent-working paths are resolved: the search server image runs as a non-root user, and handover_transit's git blob id is marked not-for-security

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
This is a finding from lead-planner-u24 (2026-10-23; the user asked it to route code-scanning alerts to their owners). It
was verified by agent-working-planner-u24 through `gh api .../code-scanning/alerts`. Both alerts are open and first seen
2026-10-19. Both paths are agent-working's since #701.

- **#248** `dockerfile.security.missing-user.missing-user`, `tools/search/Dockerfile:31`. The container runs as root.
  **A real finding.**
- **#247** `python.lang.security.insecure-hash-algorithms.insecure-hash-algorithm-sha1`, `tools/handover_transit.py:220`.
  `_blob_id` computes git's own blob object id (`sha1("blob <len>\0" + data)`) to compare against git's blob ids. It
  is an identifier, not a security control, and must stay SHA-1 to match git. **A false positive.**

Convention (platform-planner-u24, as used in #701): suppress in code with `# nosemgrep: <full rule id>` and a
one-line reason. Never dismiss in the Security tab.

## Scope
1. `tools/search/Dockerfile`: create an unprivileged user (fixed uid, for example `app`, uid 10001) and switch to it with
   `USER` before `CMD`.
   - The embedding model is pre-downloaded at build time as root, into root's Hugging Face cache. Set `HF_HOME`, or the
     sentence-transformers cache, to a path under `/app` before the download step and `chown` it to the new user.
     Otherwise the server can't load the model at runtime, or tries to download it again.
   - The `knowledge-index` volume is mounted read-only (`docker-compose.yml`). Check that the new user can read it
     (it's world-readable on the host).
2. `tools/handover_transit.py:220`: `hashlib.sha1(..., usedforsecurity=False)` plus
   `# nosemgrep: python.lang.security.insecure-hash-algorithms.insecure-hash-algorithm-sha1`, with the reason "git blob
   object id; must match git's SHA-1, not a security use". Take the rule id from the alert (already quoted above).

## Out of Scope
- Other alerts. #243 (`tools/ci_aseprite_skip_line.py`) is asset's.
- SECURITY.md ownership. That's a separate question, which lead-planner-u24 put to the owner.
- Pinning the base image or the pip versions.
- Any behaviour change in handover_transit.

## Acceptance Criteria
1. `docker build -f tools/search/Dockerfile .` succeeds, and the container started via `tools/search/docker-compose.yml`
   reports `id -u` != 0. `/api/health` returns OK, and a search query returns results without any model download at
   startup (no download in the logs). Record this in Test Summary. If Docker is unavailable or disk is too low (the host
   is under 10 GB free), say so and rely on the PR's own security-scan for the alert, but don't claim the runtime check.
2. `_blob_id` returns the same value as `git hash-object <file>` for a sample file. Add or keep a test.
3. `pytest tests/tools -k "transit or search" -p no:randomly` passes, run serially.
4. After merge, code-scanning shows #247 and #248 `fixed`. The planner checks this.

## Related Tickets
- TCK-20261019-SEMGREP-BASELINE-AGENT-WORKING-PATHS (#701): the same convention.
- TCK-20261019-SESSION-ROLES-OWN-UNOWNED-SEMGREP-PATHS (#701): gave agent-working these two paths.

## Related Docs
- `docs/guides/delivery_process.md`

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/search/Dockerfile`, `tools/search/docker-compose.yml`, `tools/handover_transit.py` (`_blob_id`)
- `tests/tools/test_handover_transit*.py`

## Assumptions / Open Questions
- Assumed: the search image is rebuilt by whoever runs it locally, and no CI job builds it. If one does, the PR's run
  covers AC 1.

## Implementation Notes
- Dockerfile: `ENV HF_HOME=/app/.cache/huggingface` and `useradd --system --uid 10001 app` before the model download, `chown -R app:app /app/.cache` after the app COPYs, then `USER app` before CMD. The model is baked under /app, so the runtime user reads it with no download. The `knowledge-index` volume is a read-only bind mount; the server only reads it (no writes under /app), and host files are world-readable.
- `_blob_id`: `usedforsecurity=False` plus the nosemgrep with the rule id from the alert and the reason; behavior unchanged.

## Test Summary
- NOT RUN: `docker build` and the container runtime check (AC 1: `id -u` != 0, `/api/health`, a search query with no model download). The torch index is TLS-blocked on this host and the disk has about 6 GB free, so the image cannot be built here; the runtime check is unverified, not passed. The PR's security-scan speaks for alert #248.
- `test_blob_id_equals_git_hash_object` added: `_blob_id` equals `git hash-object` for a sample file (text, unicode, NUL bytes). `tests/tools/test_handover_transit.py` passes.
- Serial `pytest tests/tools -k "transit or search or session or route or roster or card"`: only the SECURITY.md roster failures (ticket 2, backed out) failed; they are not in this change.

## Files Changed
tools/search/Dockerfile, tools/handover_transit.py, tests/tools/test_handover_transit.py.

## Completion Summary
The search image drops root; `_blob_id` marked not-for-security. Alerts #247/#248 are for the planner to confirm `fixed` after merge.

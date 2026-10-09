---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261009-SEARCH-SERVER-IMAGE-PYTHON-FLOOR
phase: done
date: 2026-10-09
tags: []
---

# TCK-20261009-SEARCH-SERVER-IMAGE-PYTHON-FLOOR

## Title
The knowledge-search server image runs Python 3.11, below the repo's Python floor; the environment guide names only one machine's knowledge venv

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
PR #456 (`TCK-20261009-PYTHON-FLOOR-3-12`, codebase domain) raises `requires-python` to `>=3.12`. Its handoff to
agent-working (`docs/plans/codebase_health/handoffs/handoff_to_agent_working.md`, "Update 2026-10-09") names
`tools/search/Dockerfile` as ours to align: it is `FROM python:3.11-slim`, below the new floor, and outside `uv.lock`.
Nothing in CI builds it.

The same handoff asks whether "the other machine's" `.venv-knowledge` is on 3.13. Checked 2026-10-09 on host
`u24desktop-Virtual-Machine`: `.venv-knowledge` is CPython **3.12.3** (`/usr/bin/python3.12`; this host has no 3.13),
and `import torch, sentence_transformers, sqlite_vec` works (torch 2.12.1+cpu, sentence-transformers 5.6.0). The
codebase planner's host is on 3.13.7. Both reports are true for their own machine. #456's environment-guide row says
"this machine: 3.13.7" and calls the `.venv-knowledge` row "may be stale", which misleads a reader on this host.

## Scope
1. `tools/search/Dockerfile`: `FROM python:3.11-slim` -> `FROM python:3.13-slim`. 3.13 matches CI
   (`.github/workflows/test.yml`), `.python-version` and `docker/backend.Dockerfile`; the image does not depend on any
   local venv, so the 3.12 floor (set by this host's venv) does not constrain it. torch CPU wheels and
   sentence-transformers are confirmed to import on 3.13 on the other host.
2. **After #456 merges** (it edits the same table): `docs/guidelines/agent_working_environment.md`, so the Python row
   and the `.venv-knowledge` row name each machine by host with its knowledge-venv version (u24desktop-Virtual-Machine:
   3.12.3, verified 2026-10-09; the other host: 3.13.7 per #456), and state that the floor can reach 3.13 only when
   this host's venv does, which is blocked by the torch-index note in the same guide. Also note the search image's
   Python version next to `make search-server-docker`. If #456 has not merged when item 1 is done, land item 1 and
   leave item 2 for a follow-up commit on the same batch branch.

## Out of Scope
- Raising the floor to 3.13 (codebase domain, gated on this host's venv).
- Rebuilding `.venv-knowledge` (it must be preserved; see the guide's torch-index section).
- A CI job that builds the search image (the backend image has one since #453; propose separately if wanted).
- Pinning the image's pip deps to `uv.lock`.

## Acceptance Criteria
- AC1: `tools/search/Dockerfile` starts `FROM python:3.13-slim`; no other line changes.
- AC2: `docker build -f tools/search/Dockerfile .` succeeds and the container's `/api/health` answers, **or**, if the
  torch index download is blocked on the build host (the guide's TLS/torch-index note), the Test Summary records the
  exact failing step and its error. The ticket may close with the build marked unverified on this host; it may not claim
  a build it did not run.
- AC3 (item 2, if done here): the environment guide names both hosts with their knowledge-venv versions and dates, and no
  row says "this machine" without naming the host.
- AC4: `validate_frontmatter.py` passes on this ticket; the closure is recorded with
  `record_hand_orchestrated_closure.py` (path reason `small_change`).

## Related Tickets
- TCK-20261009-PYTHON-FLOOR-3-12 (PR #456, codebase): sets the floor; its handoff asks for this.
- TCK-20261008-CI-BACKEND-IMAGE-BUILD-CHECK (#453): the backend image's build check; the search image has none.

## Related Docs
- `docs/guidelines/agent_working_environment.md` (Python row, `.venv-knowledge` row, torch-index section, `make search-server-docker`)
- `docs/plans/codebase_health/handoffs/handoff_to_agent_working.md` ("Update 2026-10-09", on #456's branch)

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- `tools/search/Dockerfile`
- `tools/search_server.py`, `tools/knowledge_search.py` (copied into the image; unchanged)

## Assumptions / Open Questions
- Assumes 3.13 over 3.12 for the image, since it matches CI and the backend image. If the build shows a dependency without
  a 3.13 wheel, use `python:3.12-slim` and say why in the Test Summary.
- The `search_docs` index is not built and this worktree has no graphify graph, so the duplicate scan for this ticket
  was done by grep over `agent-working/tickets/` and `gh pr view 456` only. No duplicate was found.

## Implementation Notes
Item 1 done 2026-10-09: `tools/search/Dockerfile` line 1 `python:3.11-slim` -> `python:3.13-slim`, nothing else. Item 2 (environment guide) deferred to follow-up `TCK-20261009-ENV-GUIDE-NAME-BOTH-HOSTS` (owner decision 2026-10-09, relayed by agent-working-planner): PR #456 was still open.

## Test Summary
AC2 UNVERIFIED on this host. `docker build -f tools/search/Dockerfile -t search-img-test .` (Docker 29.5.3) failed at Dockerfile:7, the CPU torch install `pip install torch --index-url https://download.pytorch.org/whl/cpu`, after about 16 s: `SSLError(SSLCertVerificationError ... certificate verify failed: unable to get local issuer certificate)`, then `ERROR: Could not find a version that satisfies the requirement torch (from versions: none)` / `No matching distribution found for torch`, exit code 1. This is the torch-index TLS block the environment guide describes. The base image pull and the `FROM python:3.13-slim` layer succeeded; no later step ran, so no 3.13 wheel check for sentence-transformers/sqlite-vec was done in the image and `/api/health` was not exercised.

## Files Changed

## Completion Summary
Item 1 done: `tools/search/Dockerfile` is `FROM python:3.13-slim`. The image build is UNVERIFIED on this host: `docker build` stopped at the CPU torch install (TLS certificate verify failed on download.pytorch.org). It still needs a run on the other host (the one with an unblocked torch index), and sentence-transformers and sqlite-vec on Python 3.13 are untested inside the image. Item 2 (the environment guide naming both hosts, AC3) is NOT done here: it is deferred to `TCK-20261009-ENV-GUIDE-NAME-BOTH-HOSTS`, filed in `todos/`, to start after #456 merges. AC1 and AC4 met; AC2 met by its own unverified clause; AC3 deferred.

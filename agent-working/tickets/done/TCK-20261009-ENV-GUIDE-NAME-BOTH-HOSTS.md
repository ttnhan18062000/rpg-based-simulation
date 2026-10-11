---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261009-ENV-GUIDE-NAME-BOTH-HOSTS
phase: done
date: 2026-10-09
tags: []
---

# TCK-20261009-ENV-GUIDE-NAME-BOTH-HOSTS

## Title
The agent-working environment guide says "this machine" without naming the host and must name both hosts' knowledge-venv Python versions

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Start after PR #456 merges (it edits the same table). Split out of `TCK-20261009-SEARCH-SERVER-IMAGE-PYTHON-FLOOR` item 2 by owner decision 2026-10-09. #456's environment-guide row says "this machine: 3.13.7" and calls the `.venv-knowledge` row "may be stale"; on host `u24desktop-Virtual-Machine` `.venv-knowledge` is CPython 3.12.3 (verified 2026-10-09; torch 2.12.1+cpu, sentence-transformers 5.6.0), and the other host is on 3.13.7.

## Scope
`docs/guidelines/agent_working_environment.md`, so the Python row and the `.venv-knowledge` row name each machine by host with its knowledge-venv version (u24desktop-Virtual-Machine: 3.12.3, verified 2026-10-09; the other host: 3.13.7 per #456), and state that the floor can reach 3.13 only when this host's venv does, which is blocked by the torch-index note in the same guide. Also note the search image's Python version (3.13, `tools/search/Dockerfile`) next to `make search-server-docker`, and that its build is unverified until run on a host with an unblocked torch index.

## Out of Scope
- Raising the floor to 3.13; rebuilding `.venv-knowledge`; a CI job that builds the search image.

## Acceptance Criteria
- AC1 (was AC3): the environment guide names both hosts with their knowledge-venv versions and dates, and no row says "this machine" without naming the host.
- AC2: `validate_frontmatter.py` passes on this ticket; closure via `record_hand_orchestrated_closure.py` (path reason `small_change`).

## Related Tickets
- TCK-20261009-SEARCH-SERVER-IMAGE-PYTHON-FLOOR (parent; item 1 done)
- TCK-20261009-PYTHON-FLOOR-3-12 (PR #456)

## Related Docs
- `docs/guidelines/agent_working_environment.md`

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- `docs/guidelines/agent_working_environment.md`

## Assumptions / Open Questions
- Assumes #456 merges; if its table changes shape, adapt the wording to what main holds then.

## Implementation Notes
Edited against the table as main holds it after #456 (its Python row already named `ubuntu` and `u24desktop-Virtual-Machine`). Python row now lists the knowledge-venv version per host with dates and states the floor can reach 3.13 only when u24desktop's venv does (blocked by the torch-index filter section). Docker row gives the search image's Python (3.13, `tools/search/Dockerfile`) and that its build is unverified until run on a host with an unblocked torch index. Every "this machine" in the guide now names the host (uv row, `.venv-knowledge` row, torch-block section) or is reworded host-neutrally (git hooks bullet); none remains.

## Test Summary
Docs only. `grep 'this machine'` over the guide is empty; frontmatter validated.

## Files Changed
`docs/guidelines/agent_working_environment.md`.

## Completion Summary
The environment guide names both hosts with their knowledge-venv Python versions and dates.

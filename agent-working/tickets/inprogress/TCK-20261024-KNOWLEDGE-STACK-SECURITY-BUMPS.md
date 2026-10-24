---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261024-KNOWLEDGE-STACK-SECURITY-BUMPS
phase: open
date: 2026-10-24
tags: [knowledge-store, security]
---

# TCK-20261024-KNOWLEDGE-STACK-SECURITY-BUMPS

## Title
`requirements-knowledge.txt` takes the patched mcp, graphifyy and torch versions, with the index rebuilt and search quality checked

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
lead-planner finding (2026-10-24): `requirements-knowledge.txt` on main 42c2e2b4e has 3 open Dependabot alerts:
`mcp` medium (pinned 1.28.1, patched 1.30.0), `graphifyy` medium (pinned 0.8.39, patched 0.9.70), `torch` low
(pinned 2.12.1+cpu, patched 2.13.0). The same mcp/torch alerts in `uv.lock` are handled separately by
TCK-20261024-UV-LOCK-SECURITY-BUMPS (lead-planner's ticket, codebase-implementer); that ticket does not touch
`requirements-knowledge.txt`. The owner approved this ticket on 2026-10-24 (#715, issuecomment-6385754764).

## Scope
1. Before anything: `python3 tools/sessions/disk_headroom.py`; record free space. Stop and report if the repo
   filesystem is under 10 GB free (a full venv rebuild with torch is several GB). RPG measurement lanes have disk and
   CPU priority; say when the rebuild ran.
2. Baseline on current pins: `make eval-search` (rebuild the index first with `make knowledge-index` if it is
   missing); record Recall@5 / MRR@10.
3. Build a throwaway venv (never mutate the main `.venv-knowledge` until the result is in) with the three new pins.
   torch is the CPU wheel: `pip install torch==2.13.0+cpu --index-url https://download.pytorch.org/whl/cpu`
   (see the note in `pyproject.toml` `[project.optional-dependencies]`; that index is reachable on host ubuntu,
   blocked on u24desktop, so run this on ubuntu). Build a scratch index with it and run the same eval, plus the 5
   fixed `search_docs` spot-check queries from TCK-20261014-KNOWLEDGE-STACK-PIN-AND-EMBEDDING-MAJOR's
   `test_plan.md`; compare top-5 doc ids.
4. Smoke the other two packages in the throwaway venv: `tools/search_mcp.py` starts and answers one
   `search_docs` call (mcp); `graphify query "<topic>"` and `graphify update .` on a scratch copy run without
   error (graphifyy 0.8 -> 0.9 is a 0.x minor: read its changelog for CLI or graph-format changes and record what
   you find; if `graphify-out/` format changed, say so and stop before touching the shared graph).
5. Decision rule: take all three pins if Recall@5 and MRR@10 are not lower than baseline and both smokes pass.
   If one package fails, take the others and record the failing one with its reason (an open alert stays visible;
   do not silence it). Then update `requirements-knowledge.txt`, rebuild the main `.venv-knowledge` and the real
   index.
6. Remove the throwaway venv and scratch index; report the space recovered.

## Out of Scope
- `uv.lock` / `pyproject.toml` (TCK-20261024-UV-LOCK-SECURITY-BUMPS).
- mcp 2.x or any other major.
- Rebuilding the shared `graphify-out/` beyond the smoke.

## Acceptance Criteria
- `requirements-knowledge.txt` pins mcp==1.30.0 (or later 1.x), graphifyy==0.9.70 (or later), torch==2.13.0+cpu,
  unless the ticket records why one was not taken.
- The ticket records: disk before/after, baseline and candidate Recall@5/MRR@10, the 5 spot-check comparisons,
  both smoke results, the graphifyy changelog note, and the decision.
- `search_docs` answers queries from the main checkout after the rebuild.
- No throwaway venv or scratch index left behind.
- The three Dependabot alerts on `requirements-knowledge.txt` close after merge (check after the PR lands).

## Related Tickets
- TCK-20261014-KNOWLEDGE-STACK-PIN-AND-EMBEDDING-MAJOR (method), TCK-20261014-KNOWLEDGE-STACK-FILES-OWNED
- TCK-20261024-UV-LOCK-SECURITY-BUMPS (lead-planner, `uv.lock` side)

## Related Docs
- `docs/guidelines/agent_working_environment.md` ("Why the knowledge stack is stuck on 3.12")
- `docs/plans/agent_infrastructure/llm_security_mapping.md` (follow-up 5: mcp pinned exactly)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261014-KNOWLEDGE-STACK-PIN-AND-EMBEDDING-MAJOR/`

## Related Code Areas
- `requirements-knowledge.txt`, `tools/search_mcp.py`, `tools/knowledge_search.py`, `tools/eval_search.py`

## Assumptions / Open Questions
- torch 2.13.0+cpu is published on the CPU index; if not, take the nearest patched CPU build and say so.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261024-KNOWLEDGE-STACK-SECURITY-BUMPS
phase: done
date: 2026-10-24
tags: [knowledge-store, security]
---

# TCK-20261024-KNOWLEDGE-STACK-SECURITY-BUMPS

## Title
`requirements-knowledge.txt` takes the patched mcp, graphifyy and torch versions, with the index rebuilt and search quality checked

## Status
DONE

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
Ran on host ubuntu, 2026-10-24, alone (load average about 1.5; no RPG measurement lane was running that I saw). Disk (repo filesystem): 12.0 GB free before, 9.7 GB at the lowest (throwaway venv 1.8 GB plus the scratch index), 12 GB after cleanup; the throwaway venv (1.8 GB) and the baseline index copy (126 MB) are removed.

**Baseline** (pins as installed: torch 2.12.1+cpu, sentence-transformers 5.6.0, mcp 1.28.1, graphifyy 0.8.39), 61 queries: Recall@5 0.41, Recall@10 0.67, MRR@10 0.27, zero-result 0. **Candidate** (throwaway venv from the new `requirements-knowledge.txt` pins, so sentence-transformers 6.1.0 as the file already pinned; scratch index rebuilt from nothing over the same 16537 chunks): Recall@5 0.41, Recall@10 0.67, MRR@10 0.27, zero-result 0. Not lower on either metric. (Both sit under the tool's 0.80 report threshold; that is the standing state, not this change.)

**Spot checks** (top-5 doc ids, baseline vs candidate): 'mechanics damage formula', 'authoritative mutation pipeline contract', 'disk headroom midsession warning', 'regional sovereignty region boundaries', 'pre-push advisory hook': identical in all five.

**mcp 1.30.0 smoke:** a stdio client started `tools/search_mcp.py`, listed `search_docs` and `search_health`, and one `search_docs` call returned a result (`isError` false). The server delegated to the already-running shared search server, so the proof is the MCP layer, not a fresh backend.

**graphifyy 0.9.70 smoke:** the project CHANGELOG at the upstream repo only covers 0.1.x, so there was no changelog to read for 0.8 -> 0.9; I tested instead. `graphify query` reads the existing 0.8-built `graph.json` (53188 nodes) and prints a note that it uses the pre-#1504 node-ID scheme and that `graphify extract --force` would give path-qualified IDs (fixes same-name-file collisions). It also returned more nodes for the same query than 0.8 (222 vs 33) and flags truncation. `graphify update .` on a scratch copy ran without error (it rebuilt the scratch tree and dropped nodes of absent files, as before). So the graph format changed in 0.9 (node-ID scheme) but the old graph still loads. I did NOT touch the shared `graphify-out/`; whoever refreshes it from the main checkout should expect that `graphify update .` and a full `extract --force` may re-key nodes (not tested on the real graph).

**Decision:** all three pins taken (every metric equal, both smokes pass). The main `.venv-knowledge` was upgraded in place with `uv pip` (it has no pip): torch 2.13.0+cpu, mcp 1.30.0, graphifyy 0.9.70, and sentence-transformers 6.1.0 (it was at 5.6.0, behind the 6.1.0 the file already pinned). `pip check` clean. The real index in this worktree is the one built by the candidate venv; `tools/knowledge_search.py query` on the main venv returns the same top-3 as before. The Dependabot alerts are checked after merge.

**Known gaps** (not fixed here; the planner files the first as a follow-up):
- The `graphify` on PATH is `~/.local/bin/graphify` on the system python, at graphifyy 0.6.7, not the pinned `.venv-knowledge` 0.9.70. The CLI that hooks and sessions run is therefore not the pinned one; this predates this ticket and is filed as TCK-20261024-GRAPHIFY-ON-PATH-IS-NOT-THE-PINNED-VERSION. The smokes above ran the 0.9.70 binary from the throwaway venv.
- `torch==2.13.0+cpu` is only on `download.pytorch.org`, which is blocked on `u24desktop-Virtual-Machine`: its `.venv-knowledge` stays at torch 2.12.1+cpu and the low torch alert stands for that host. The new mcp and graphifyy pins come from PyPI but their upgrade there is not verified. Noted in `docs/guidelines/agent_working_environment.md`.
- The 0.9 node-ID re-key applies when the shared `graphify-out/` is next rebuilt with 0.9; it was not exercised on the real graph.

## Test Summary
Measurement ticket, no code: eval and spot checks above (candidate equals baseline), two smokes pass. No repo tests changed.

## Files Changed
- requirements-knowledge.txt
- docs/guidelines/agent_working_environment.md
- tests/tools/test_code_test_index.py (the graphifyy pin test follows the new pin; found by CI on the PR, not by the local scope)

## Completion Summary
`requirements-knowledge.txt` pins mcp 1.30.0, graphifyy 0.9.70 and torch 2.13.0+cpu; search quality is unchanged and the main knowledge venv is rebuilt.

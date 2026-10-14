---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261014-KNOWLEDGE-STACK-PIN-AND-EMBEDDING-MAJOR
phase: done
date: 2026-10-14
tags: [knowledge-store, security, process-improvement]
---

# TCK-20261014-KNOWLEDGE-STACK-PIN-AND-EMBEDDING-MAJOR

## Title
Pin `mcp` exactly for the knowledge stack, rebuild the missing search index, and take sentence-transformers 6 only if search quality holds

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Dependabot opened #581 (sentence-transformers 5.6.0 -> 6.1.0) and #582 (mcp 1.28.1 -> 2.3.0). Both bump the
knowledge-search stack, not the game. The user closed both on 2026-10-14 as superseded by this ticket:
- #582 only moved `uv.lock`. Follow-up 5 of `docs/plans/agent_infrastructure/llm_security_mapping.md` (#550) asks
  for `mcp` to be pinned exactly; today it is `>=1.0.0` in `pyproject.toml` and absent from
  `requirements-knowledge.txt`, so the version the search MCP runs is whatever is installed (1.28.1 in the main
  checkout's `.venv-knowledge` on 2026-10-14).
- #581 moved the `requirements-knowledge.txt` pin with no index rebuild and no quality check. A major version may
  change embeddings.
Separately, the local index is missing: `agent-working/.index/knowledge-index/` does not exist in the main checkout
(search reports "index not found"), so it has to be rebuilt anyway.

## Scope
1. Add `mcp==1.28.1` (the installed, working version) to `requirements-knowledge.txt` with a one-line comment citing
   follow-up 5 of the security mapping. Do not take mcp 2.x here (a major with an API change risk for
   `tools/search_mcp.py`; out of scope).
2. Before any rebuild, run `python3 tools/sessions/disk_headroom.py` and record free space. Stop and report if
   /mnt/data is under 10 GB free. RPG measurement lanes have disk and CPU priority: run rebuilds when RPG load is
   light, and say when they ran.
3. Rebuild the index on the current pin (sentence-transformers 5.6.0): `make knowledge-index`. Then run
   `make eval-search` and save the Recall@5 / MRR@10 numbers as the baseline.
4. In a separate, throwaway venv (never mutate the main `.venv-knowledge` until the result is in), install
   sentence-transformers 6.1.0 with the same torch, build an index into a scratch location, and run the same
   `tools/eval_search.py` evaluation against it. Also spot-check 5 fixed `search_docs` queries (list them in
   `test_plan.md`) and compare the top-5 doc ids.
5. Decision rule: take 6.1.0 (update the pin, rebuild the real index with it) only if Recall@5 and MRR@10 are not
   lower than the baseline. Otherwise keep 5.6.0 and record the numbers and the reason in the ticket.
6. Remove the throwaway venv and scratch index afterwards; report the space recovered.

## Out of Scope
- mcp 2.x, and any change to `tools/search_mcp.py` / `tools/search_server.py` behaviour.
- `pyproject.toml` / `uv.lock` (lead-owned). If `uv.lock` must follow, say so in Review notes for lead-planner.
- Claiming ownership of `requirements-knowledge.txt`, `tools/knowledge_search.py`, `tools/eval_search.py` (all
  unowned per `tools/sessions/route.py`). Note it as a follow-up; a roster change needs the owner's diff confirm.
- The Dependabot semver-major ignore (platform's).

## Acceptance Criteria
- `requirements-knowledge.txt` pins `mcp` exactly, with the comment.
- The index exists again and `search_docs` answers queries in the main checkout.
- The ticket records: disk free before and after, baseline and candidate Recall@5 / MRR@10, the 5 spot-check
  comparisons, and the decision with its reason.
- If 6.1.0 is taken, the pin and the real index both use it; if not, nothing in the main venv changed version.
- No throwaway venv or scratch index left behind.

## Related Tickets
- TCK-20261013-HARNESS-LLM-SECURITY-MAPPING (follow-up 5)
- TCK-20261013-SEARCH-MCP-FILES-OWNED
- TCK-20261014-DISK-HEADROOM-MIDSESSION-WARNING-AND-MERGED-WORKTREES
- TCK-20261009-SEARCH-SERVER-IMAGE-PYTHON-FLOOR

## Related Docs
- docs/plans/agent_infrastructure/llm_security_mapping.md
- docs/guidelines/agent_working_environment.md
- docs/guides/agent_session_reset_boundaries.md ("Disk headroom")

## Related Stored Artifacts
- none

## Related Code Areas
- requirements-knowledge.txt
- tools/knowledge_search.py, tools/eval_search.py, tools/search_mcp.py
- Makefile targets `knowledge-index`, `eval-search`

## Assumptions / Open Questions
- Assumes `tools/eval_search.py` still runs (last touched by TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX). If it is
  broken, report that before deciding; do not decide on spot checks alone.
- Model downloads may hit the TLS block; `HF_HUB_ETAG_TIMEOUT` and the cert env in the Makefile already apply.

## Implementation Notes
- `requirements-knowledge.txt`: `mcp==1.28.1` added with a comment citing follow-up 5 of the security mapping; `sentence-transformers` 5.6.0 -> 6.1.0
  (decision below). `uv.lock` / `pyproject.toml` are lead-owned and untouched: `pyproject.toml` has `sentence-transformers>=2.7.0` and
  `mcp>=1.0.0` (unpinned), so lead-planner decides whether `uv.lock` follows.
- Disk (`disk_headroom.py`) before any rebuild: 14.4 GB free of 48.9 GB (floor 10 GB). Rebuilds ran 2026-10-14 18:42-19:10 +07 after the 1-minute
  load fell to 0.2-2.6 on 6 cores (it was 14-37 earlier, so they were held until then).
- Baseline: `make knowledge-index` on sentence-transformers 5.6.0 (15562 documents, 6m47s), then `make eval-search`:
  **Recall@5 0.43, Recall@10 0.65, MRR@10 0.26** (61 queries, 54 with expected; the tool's own threshold Recall@5 >= 0.80 FAILS on the baseline, so it
  is not a gate for this decision).
- Candidate: throwaway venv (`uv venv`, sentence-transformers 6.1.0 installed `--no-deps` over the main venv's torch 2.12.1+cpu and transformers
  5.12.1 via a .pth), full index (6m46s), same eval: **Recall@5 0.43, Recall@10 0.65, MRR@10 0.26**, identical per query. The cached
  embeddings are bit-identical (max abs diff 0.0 over 200 vectors), so a model-weights-preserving major changes nothing here.
- Five fixed spot checks (top-5 doc ids compared, 5.6.0 vs 6.1.0 index): "mechanics damage formula", "authoritative mutation pipeline contract",
  "disk headroom midsession warning", "regional sovereignty region boundaries", "pre-push advisory hook": identical lists for all five.
- Decision rule met (Recall@5 and MRR@10 not lower): 6.1.0 taken. The pin is bumped, the 6.1.0-built index is the real one in this worktree
  (`agent-working/.index/knowledge-index/`, gitignored), and the shared `.venv-knowledge` was upgraded to 6.1.0 (`--no-deps`, the same
  combination the trial ran). The main checkout has no index of its own; this worktree's is the one built (a build there is
  `make knowledge-index`, not run here).
- Throwaway venv and scratch indexes removed; free space 14.64 GB -> 14.77 GB after the cleanup.
- Not verified: a docker/CI image build of the search server on 6.1.0 (the host cannot reach the torch index); `uv.lock` unchanged.

## Test Summary
- No code change; verification is the measured eval above. `tests/tools/test_session_status.py` 13 passed in the low-load window (the earlier
  timeout was load). Search answers queries from the 6.1.0 index with the upgraded main venv (`pre-push advisory hook` returns the right tickets).

## Files Changed
- requirements-knowledge.txt

## Completion Summary
`mcp` is pinned to 1.28.1 and sentence-transformers is 6.1.0: same Recall@5/MRR@10 (0.43/0.26) as 5.6.0, identical embeddings and spot checks.
The local index is rebuilt and answers queries. Follow-ups for others: `uv.lock` (lead-planner), a stable regex module is unrelated and filed in the lane ticket.

---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260817-KGMCP-SEARCH-MCP-TEST-REQUIRES-UNBUILT-CI-INDEX
phase: open
date: 2026-08-17
tags: [ai, mcp, testing]
---

# TCK-20260817-KGMCP-SEARCH-MCP-TEST-REQUIRES-UNBUILT-CI-INDEX

## Title
`test_gateway_down_search_mcp_test_mode_still_works` requires a built `knowledge-index/`, which
CI's lean `requirements.txt` environment deliberately never builds

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found while fixing `TCK-20260817-HOTFIX-KGMCP-MISSING-JSONSCHEMA-DEPENDENCY` (missing `jsonschema`/
`mcp` pip dependencies that were causing `tests/tools/test_knowledge_gateway_failure_semantics.py`
to fail at collection time on CI). After fixing those, a real, clean-venv re-run surfaced one
further, genuinely different failure in the same file:
`test_gateway_down_search_mcp_test_mode_still_works` calls `tools/search_mcp.py --test`, which
requires a real, built `knowledge-index/knowledge.db` (the semantic search index) to answer a query
— but `requirements.txt`'s own header comment explicitly states the knowledge-search stack (torch,
sentence-transformers, sqlite-vec, rank-bm25 — declared in `requirements-knowledge.txt` instead) is
deliberately excluded from CI's lean install, and `.github/workflows/test.yml` has no `make
knowledge-index` (or equivalent) step anywhere. This means this specific test has likely never
passed on CI, for as long as it's existed — its own execution-time failure was simply masked until
now by the `jsonschema`/`mcp` collection-time failures landing first in the same file.

## Scope
- Confirm how long this test has been failing on CI (check `git blame`/`git log` for when it was
  added, and whether it predates the `jsonschema`/`mcp` masking).
- Decide the correct fix: (a) build a small, CI-safe, deterministic fixture index just for this
  test (would require adding at least a lightweight subset of `requirements-knowledge.txt`'s stack
  to CI, contradicting the existing "not needed by the test suite" comment — needs a real cost/
  benefit case if pursued), (b) mark this test to skip when `knowledge-index/knowledge.db` doesn't
  exist, with a clear, dated, honest skip reason (mirroring the precedent already established this
  session for `test_gate_a_readpath_review.py`'s corpus-dependent skip guards), or (c) move this
  test out of the CI-covered `tests/tools` collection entirely into a locally-only or
  manually-triggered check, if it's meant purely as a local dev sanity check, not a CI gate.
- Apply the chosen fix and confirm `pytest tests/tools -m "not slow"` is genuinely clean on this
  test going forward, in an environment that mirrors CI's own lean dependency set (not this local
  dev environment, which already has the full knowledge-search stack installed and a built index).

## Out of Scope
- Any change to `requirements.txt`'s own deliberate exclusion of the heavy ML stack (torch etc.)
  from CI, unless the chosen fix explicitly requires and justifies it.
- The `jsonschema`/`mcp` dependency fix itself (already done in
  `TCK-20260817-HOTFIX-KGMCP-MISSING-JSONSCHEMA-DEPENDENCY`).

## Acceptance Criteria
- [ ] Root cause and history confirmed (how long this has silently failed on real CI).
- [ ] A real, disclosed decision made among (a)/(b)/(c) above, with rationale.
- [ ] `test_gateway_down_search_mcp_test_mode_still_works` (or its replacement) passes in an
      environment that mirrors CI's own lean dependency set, not this local dev environment's
      already-built index.

## Related Tickets
- `TCK-20260817-HOTFIX-KGMCP-MISSING-JSONSCHEMA-DEPENDENCY` (found this while fixing the
  masking collection-time failures in the same test file)

## Related Docs
- `docs/guidelines/agent_working_environment.md` (KGMCP local cache/index setup)

## Related Code Areas
- `tests/tools/test_knowledge_gateway_failure_semantics.py`
- `tools/search_mcp.py`
- `.github/workflows/test.yml`
- `requirements.txt` / `requirements-knowledge.txt`

## Assumptions / Open Questions
- Whether any OTHER test in `tests/tools` has the same silent, always-failing-on-CI characteristic
  (masked by the same jsonschema/mcp collection error, or independently) is unconfirmed — worth a
  quick scan during Investigate.

## Implementation Notes
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)

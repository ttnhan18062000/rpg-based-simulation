---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260817-KGMCP-SEARCH-MCP-TEST-REQUIRES-UNBUILT-CI-INDEX
tags: [ai, mcp, testing]
---

# Investigation — TCK-20260817-KGMCP-SEARCH-MCP-TEST-REQUIRES-UNBUILT-CI-INDEX

## Scope widened
Originally scoped to just `test_gateway_down_search_mcp_test_mode_still_works`. Real CI logs
(job "API / tools / logging", run https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/32000421496)
showed the same root-cause class affects 12 tests total across 6 files, not 1.

## Root cause
`requirements.txt` (installed by every CI job) deliberately excludes the knowledge-search ML
stack — its own header comment: "The local agent knowledge-search tooling (torch,
sentence-transformers, sqlite-vec, rank-bm25) lives in requirements-knowledge.txt instead — those
packages are not needed [in CI]." `Makefile`'s `knowledge-index` target is labeled "developer env
only — not CI." The `graphify` CLI (package `graphifyy`) is likewise declared only in
`requirements-knowledge.txt`, never installed in CI.

12 failing tests call real functions that hard-require one of: `rank_bm25`/`numpy` (unconditional
imports inside `tools/knowledge_search.py`'s BM25/hybrid-fusion code paths — `numpy` specifically
is imported at `tools/knowledge_search.py:998` even in pure keyword-mode, a real source gap the
class docstrings claim doesn't exist), a real built `knowledge-index/knowledge.db`, the `graphify`
binary, or a pre-warmed local `knowledge-index/retrieval_cache.db` L2 cache row left behind by a
specific historical session's own live run (gitignored, not reproducible on any fresh checkout).

## Existing repo precedent
Confirmed strong, already-used convention for exactly this situation:
`tests/tools/test_knowledge_search.py` already has dozens of
`pytest.skip("sentence-transformers / sqlite-vec not installed")` /
`pytest.skip("knowledge index not built — run make knowledge-index")` guards.
`tests/tools/test_gate_a_readpath_review.py` uses `@pytest.mark.skipif(not _CORPUS_AVAILABLE, ...)`
for a missing local corpus file. `tests/tools/test_codex_capability_diagnostics.py` uses
`shutil.which("codex")` + skip for a missing CLI binary. None of the 12 actually-failing
tests/classes followed this pattern before this fix.

## Decision
Per the repo's own twice-reaffirmed architectural decision (`TCK-20260702-CI-REQUIREMENTS-SPLIT`,
`requirements.txt`'s header, `Makefile`'s own target comment) that CI intentionally stays lean:
add proper skip guards (option b from the original ticket's Scope), not install the ML stack in CI
(option a) or relocate the tests (option c). This is consistent with existing convention and
requires no CI workflow change.

## Verification
Simulated a genuinely fresh-CI-like environment (patched `builtins.__import__` to raise
`ImportError` for `numpy`/`rank_bm25`, `shutil.which` to return `None` for `graphify`, and
`search_mcp._DB_PATH` to a nonexistent path) and confirmed all 12 previously-failing tests skip
gracefully instead of failing, while the full real local environment (all deps present) still
passes all of them for real.

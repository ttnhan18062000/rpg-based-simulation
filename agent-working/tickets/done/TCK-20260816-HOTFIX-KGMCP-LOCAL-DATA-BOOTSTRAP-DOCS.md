---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260816-HOTFIX-KGMCP-LOCAL-DATA-BOOTSTRAP-DOCS
phase: done
date: 2026-08-16
tags: [ai, mcp, setup]
---

# TCK-20260816-HOTFIX-KGMCP-LOCAL-DATA-BOOTSTRAP-DOCS

## Title
Add a `make kgmcp-bootstrap` target and document where KGMCP's local, gitignored caches live and
how to rebuild them in a new environment

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
The user asked where the Knowledge Gateway MCP's local cache/data lives, confirmed it is not
committed, and asked how to move to another environment — then asked for a tool or Makefile target
plus documentation, if needed. Real, verified answer: three local, gitignored artifacts exist
(`knowledge-index/retrieval_cache.db` — KGMCP Level 1/2 cache; `knowledge-index/knowledge.db` +
`bm25.pkl` + `embeddings_cache.pkl` + `manifest.json` — the semantic search index; `parity-index/
parity.db` — the Parity Ledger query index), none tracked by git (`.gitignore:264,271`), all
deliberately disposable/rebuildable per this project's own "local database must remain disposable"
principle (`tmp/mcp-followup-instruction.md` §10). `docs/guidelines/agent_working_environment.md`
already documents the semantic search index's own setup in detail, but has no mention of
`parity-index/` or KGMCP's own `retrieval_cache.db` at all — a real, genuine documentation gap for
anyone following that doc to set up a fresh environment. `retrieval_cache.db`'s own Level 1/2
tables (`_get_level1_connection()`/`_get_level2_connection()` in `tools/retrieval_cache.py`) have
no CLI bootstrap path today — they only self-initialize lazily on the first real
`knowledge_context`/`knowledge_status` gateway call — this must be documented accurately, not
papered over with an invented "build" step that doesn't correspond to real code.

## Scope
- Add a new `make kgmcp-bootstrap` Makefile target that chains the two real, existing rebuildable
  targets (`parity-index`, `knowledge-index`) in one command, for a fresh-environment setup.
- Add a new section to `docs/guidelines/agent_working_environment.md` (the existing single-reference
  setup doc) documenting all 3 local KGMCP-adjacent cache artifacts: their real paths, real sizes,
  confirmation none are committed, and the real rebuild path for each — including honestly stating
  that `retrieval_cache.db`'s own Level 1/2 tables have no explicit bootstrap command and simply
  self-initialize cold on first real gateway call.
- Cross-reference the existing KGMCP-specific docs (`docs/plans/knowledge-gateway-mcp-proposal.md`,
  `docs/engine/contracts/knowledge_gateway_mcp/*.md`) rather than duplicating their content.

## Out of Scope
- Adding a CLI bootstrap/init command to `tools/retrieval_cache.py` for Level 1/2 schema
  pre-creation — this ticket documents the real, current lazy-init behavior accurately; adding new
  runtime behavior to the gateway's own cache module is a separate, larger change requiring its own
  Architecture Review, not a hotfix-tier doc/Makefile change.
- Any change to `.gitignore`, the real cache file formats, or what gets committed.
- Any change to the semantic search index's own already-documented setup flow.

## Acceptance Criteria
- [ ] `make kgmcp-bootstrap` exists and runs `parity-index` + `knowledge-index` in sequence,
      succeeding on a real run.
- [ ] `docs/guidelines/agent_working_environment.md` accurately documents all 3 local cache
      artifacts' real paths, non-committed status, and real rebuild commands — including the honest
      disclosure that `retrieval_cache.db`'s KGMCP tables have no bootstrap command and self-init
      lazily.
- [ ] No new runtime behavior is added to any gateway/cache source file.

## Related Docs
- `docs/guidelines/agent_working_environment.md` (the doc this ticket extends)
- `docs/plans/knowledge-gateway-mcp-proposal.md` §10 (Cache Design)

## Related Code Areas
- `Makefile` (`parity-index`, `knowledge-index` targets — reused, not modified)
- `tools/retrieval_cache.py` (`_get_level1_connection()`, `_get_level2_connection()` — read-only
  reference for documenting real lazy-init behavior)

## Implementation Notes
Added `kgmcp-bootstrap: parity-index knowledge-index` to `Makefile` (line 318-323). It chains the
two existing, genuinely rebuildable targets rather than introducing new build logic, and prints an
informational line explaining that `knowledge-index/retrieval_cache.db` (KGMCP Level 1/2 cache) is
deliberately not part of the chain: `_get_level1_connection()`/`_get_level2_connection()` in
`tools/retrieval_cache.py` have no CLI bootstrap subcommand today (only `stats`/`check-index`/
`check-query`/`check-packet`/`prune` exist) — the tables self-initialize lazily via real
`CREATE TABLE IF NOT EXISTS` migrations on the first genuine `knowledge_context`/`knowledge_status`
gateway call. Documenting this honestly (rather than inventing a bootstrap step that doesn't
correspond to real code) was required by the ticket's own Out of Scope section and the Gate
Integrity rule.

Added a new `## Other Local, Gitignored Caches (Knowledge Gateway MCP)` section to
`docs/guidelines/agent_working_environment.md` (lines 267-296) with a comparison table of all 3
artifacts (`knowledge-index/retrieval_cache.db`, `knowledge-index/knowledge.db` + `bm25.pkl` +
`embeddings_cache.pkl` + `manifest.json`, `parity-index/parity.db`) — real paths, approximate sizes
(~400KB / ~54MB / ~3.7MB), confirmed-gitignored status (`.gitignore:264,271`), and the real rebuild
command for each, plus a `make kgmcp-bootstrap` one-liner and a Command Reference table row.

No new runtime behavior was added to any gateway/cache source file, per scope.

## Test Summary
- `make -n kgmcp-bootstrap` dry-run confirmed correct target chaining (`parity-index` →
  `knowledge-index`) with no interference with either target's own existing recipe.
- Real full `make kgmcp-bootstrap` run (background, completed exit 0): rebuilt both
  `parity-index/parity.db` and `knowledge-index/knowledge.db` (+ `bm25.pkl`) with fresh mtimes;
  output confirmed the informational `retrieval_cache.db` self-init message printed correctly.
- `python3 tools/validate_frontmatter.py` run against this ticket and the modified doc file: clean,
  after registering the new `setup` tag (`python3 tools/tag_registry.py add setup --category
  meta-process --note "..."`) that this ticket introduced.
- No code paths changed, so no pytest scope applies; this is a Makefile + documentation change only.

## Files Changed
- `Makefile` — new `kgmcp-bootstrap` target (lines 318-323).
- `docs/guidelines/agent_working_environment.md` — new "Other Local, Gitignored Caches (Knowledge
  Gateway MCP)" section (lines 267-296) plus a Command Reference table row.

## Completion Summary
All scope items and acceptance criteria are met: `make kgmcp-bootstrap` exists, chains the two real
rebuildable targets, and was verified with a real successful run; `docs/guidelines/
agent_working_environment.md` accurately documents all 3 local cache artifacts including the honest
disclosure that `retrieval_cache.db`'s KGMCP tables have no bootstrap command and self-init lazily;
no new runtime behavior was added to any gateway/cache source file. Verify's 1st pass (done-checker)
found the underlying substance fully accurate and independently verified — the only gaps were this
ticket's own body sections (Status/Implementation Notes/Test Summary/Files Changed/Completion
Summary) not yet being filled in, which this revision closes. No further code or documentation
content changes were required.

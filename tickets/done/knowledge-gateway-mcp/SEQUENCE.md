# Implementation Sequence — knowledge-gateway-mcp

All child tickets are Phase 0 ("Contract and Measurement Baseline") work only, per
`docs/plans/knowledge-gateway-mcp-proposal.md` §20 and this epic's Out of Scope. None authorize
Phase 1+ implementation (routing, live MCP tools, payload caching).

## Order

1. TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC (scope-only parent)
2. TCK-20260814-KGMCP-CONTRACT-SCHEMAS (foundational — freezes the `status`/`freshness`/
   `verification` enums and `ProviderCapabilities` shape the other children reference)
3. TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY (after #2 — its evidence-dependency contract cites
   #2's frozen enums; can start once #2's enum shapes are stable even if #2 isn't fully closed)
4. TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY (parallel with #3 after #2 — its token-counting
   method feeds #2's budget fields, and its GC rules must not evict rows #3's identity contract
   still considers valid, so #3 and #4 should be reconciled before either closes)
5. TCK-20260814-KGMCP-MEASUREMENT-BASELINE (independent of #2-#4 — reuses existing
   `retrieval_baseline_metrics.py` tooling directly; gated on checking
   `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s real status first, not on #2-#4)
6. TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT (independent of #2-#5 — gated on checking
   `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`'s real status first; can run any time in
   parallel with the others, but must not activate its draft regardless of the other children's
   progress)

## Cross-Epic Sequencing Note

Two children in this folder each depend on real status checks against
`tickets/todos/agent-tooling-integrity-hardening/` siblings, not on anything in this folder:

- #5 (`KGMCP-MEASUREMENT-BASELINE`) must confirm
  `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s status before building its baseline
  corpus, to avoid a second `read_to_search_ratio`-equivalent.
- #6 (`KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT`) must confirm
  `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`'s status (and, ideally, whether a retro window
  has confirmed its fix holds) before drafting the pre-scan-mandate relaxation, and must never
  activate that draft while the hardening fix is unverified.

## Verification Note

This epic is not closed by #2-#6 merely landing artifacts. Per the epic's own Acceptance Criteria,
Phase 0's bar is frozen contracts + a real measured baseline + a ratified redaction/retention policy
+ an inert, correctly-sequenced instruction draft — not code existing. Activating the
pre-scan-mandate instruction change (#6's output) is explicitly out of scope for this epic and
requires a separate future ticket once Phase 0 is reviewed.

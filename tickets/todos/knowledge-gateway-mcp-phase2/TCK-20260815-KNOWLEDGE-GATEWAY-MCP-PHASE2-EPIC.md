---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE2-EPIC
phase: open
date: 2026-08-15
tags: [ai, mcp, process-improvement]
---

# TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE2-EPIC

## Title
Local Knowledge Gateway MCP — Phase 2: Real Provider-Result Cache

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE1-EPIC` closed Phase 1 (real, tested `knowledge_context`/
`knowledge_status` MCP tools; deterministic routing; extractive packet assembly; tested fail-open
behavior) on 2026-08-15. Its final child, `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON`, honestly
measured the real gateway against Phase 0's frozen corpus and found all 3 predeclared §4 promotion
thresholds (latency, token reduction, no-regression-recall) FAIL — a genuine, unmanipulated result,
not engineered around. This epic tracks and gates **Phase 2: Real Provider-Result Cache** (§20) as
the next, separately-authorized increment: adding the SQLite payload cache Phase 1 deliberately
did not build, per proposal §10.2's "Level 1: Provider-result cache."

**This epic explicitly carries forward, rather than silently assumes away, 3 real findings from
Phase 1's own honest measurement:**

1. **Latency FAIL is Phase 2's own justification.** Phase 1 measured every call cold (no cache
   exists yet) against a threshold framed as a warm-hit bar. Phase 2's cache-hit path is expected
   to structurally fix this — but this epic's own acceptance work must measure the REAL cache-hit
   latency once built, not assume the fix without re-measuring (mirroring Phase 1's own "real run,
   not estimate" discipline).
2. **Token-reduction FAIL is NOT automatically solved by caching.** Caching avoids recomputation;
   it does not shrink the structured JSON response payload that caused Phase 1's token-reduction
   miss. This epic must NOT silently assume caching fixes this — if a child ticket's own
   measurement shows tokens still fail to reduce, that must be reported honestly, exactly as Phase
   1 did, not glossed over as "will improve with Phase 2."
3. **Recall's single-provider-routing cause remains out of this epic's scope entirely.** That
   cause is architectural (§8's routing table), not a caching concern — Phase 2 does not touch
   routing. Only recall's OTHER, now-fixed cause (the `doc_id`/`source_id` normalization bug,
   closed by `TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION`) was addressed, separately, before
   this epic began.

## Scope
- Gate all work strictly to Phase 1's already-shipped gateway plus Phase 2's own §20 bullets: add
  SQLite schema and migrations, store actual bounded normalized results, validate direct evidence
  fingerprints before hits (falling back to provider generation only when the provider capability
  contract lacks reliable finer-grained evidence), add exact normalized-query reuse.
- Build "Level 1: Provider-result cache" per proposal §10.2 — normalized, bounded provider results,
  keyed by query hash/deterministic intent/resolved entity IDs/filters, with provider
  name/adapter version, result payload, source IDs/paths, evidence hashes, provider generation,
  repository/branch scope, timestamps, and hit counters (the exact row shape §10.2 specifies).
- Reuse Phase 0's frozen artifacts as this epic's actual contract surface: the cache-lookup vs.
  evidence-validity identity split (`evidence_cache_identity_contract.md` §1-§4), the migration
  design (`cache_migration_plan.md` — same `knowledge-index/retrieval_cache.db` file, new
  migrations, never a second database), and the ratified redaction/retention policy
  (`redaction_retention_policy.md` §2-§10 — allowlist, redaction rules, size cap, secret-scan
  baseline, never-cache enumeration, `kgmcp_char_heuristic_v1`, SQLite operational limits, GC
  defaults).
- Re-run `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON`'s comparison methodology (not its exact
  historical numbers, which stand as a permanent record) against the real cache-hit path once built,
  honestly reporting whether the latency threshold is now met.

## Out of Scope
- Level 2 (assembled context-packet cache) and Level 3 (verified reusable knowledge) per §10.2 —
  Phase 3 and Phase 6 respectively.
- Semantic/fuzzy cache-key matching, entity-alias reuse, or cross-phrasing cache hits (Phase 5).
- Any change to routing (`tools/knowledge_gateway_router.py`) or packet assembly's extractive
  rendering logic (`tools/knowledge_gateway_packet_assembly.py`) beyond what's needed to read from
  and write to the new cache layer — this epic adds a cache, it does not redesign Phase 1's routing
  or assembly behavior.
- A second cache database — migrations extend the existing `knowledge-index/retrieval_cache.db`
  file per `cache_migration_plan.md`'s own design decision.
- Silently assuming the token-reduction threshold is fixed by caching alone (see Request Summary
  point 2) — if it isn't, that must be reported honestly by this epic's own acceptance-measurement
  child ticket, not assumed away.
- Any change to `CLAUDE.md`, `.claude/agents/*.md`, or `.claude/skills/*.md`.

## Acceptance Criteria
- [ ] Only Phase 2 (§20) work is scoped/authorized under this epic; no Phase 3+ deliverable
      (context-packet caching, semantic reuse, durable knowledge records) is claimed as done here.
- [ ] The cache schema and migrations extend `knowledge-index/retrieval_cache.db` in place, per
      `cache_migration_plan.md`'s design — no second database, no full-rebuild-and-atomic-swap.
- [ ] Cached rows are validated against real evidence fingerprints before being served as a hit,
      with a real, tested fallback to provider-generation-level validation when finer-grained
      evidence isn't available (per `evidence_cache_identity_contract.md` §4).
- [ ] Only allowlisted source types (Context Search + Graphify results, per
      `redaction_retention_policy.md` §2) ever reach a cache write; the redaction rules (§3), size
      cap (§5), and secret-scan baseline (§4) are real, tested code paths, not documentation only.
- [ ] Exact normalized-query reuse works: an identical repeated query (same normalized intent,
      entity IDs, filters, budget class) produces a genuine cache hit on the second call, verified
      by a real test proving the second call bypasses the provider round-trip.
- [ ] This epic's own acceptance-measurement child ticket honestly re-measures the real cache-hit
      latency and reports whether §4.1's threshold is now met — and separately, honestly reports
      whether §4.2's token-reduction threshold is met, without assuming caching alone fixes it.
- [ ] `docs/plans/knowledge-gateway-mcp-proposal.md` §20's Phase 2 bullets are annotated Done as
      child tickets land, mirroring the Phase 0/Phase 1 epics' own annotation convention.
- [ ] `CLAUDE.md`, `.claude/agents/*.md`, and `.claude/skills/*.md` remain byte-unchanged by every
      child ticket in this epic.
- [ ] This epic is not closed merely because a child ticket's code lands — Phase 2's own bar (all
      §20 Phase 2 bullets Done, a real cache genuinely producing hits with fingerprint-validated
      freshness, and an honest re-measurement of §4.1/§4.2 against the real cache-hit path) must be
      met.

## Related Tickets
- TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS (child 1; SQLite schema + migrations — see
  SEQUENCE.md)
- TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH (child 2; ratified redaction/retention policy as
  real, enforced code)
- TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING (child 3; cache lookup/fingerprint-validation/
  write wired into the real gateway)
- TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON (child 4; honest cold-vs-warm §4.1/§4.2/§4.3
  re-measurement — closes this epic's acceptance loop)
- TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE1-EPIC (DONE; parent Phase 1 epic — supplies the real
  gateway this epic adds caching to, and the honest threshold-FAIL finding this epic responds to)
- TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC (DONE; parent Phase 0 epic — supplies every frozen
  contract this epic implements against, including the cache-identity and redaction/retention
  contracts)
- TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY (DONE; the lookup-vs-validity identity split and
  `cache_migration_plan.md` design this epic implements)
- TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY (DONE, ratified; the policy this epic's cache
  writes must enforce)
- TCK-20260815-KGMCP-P1-BASELINE-COMPARISON (DONE; the honest all-FAIL acceptance measurement this
  epic's own acceptance-measurement child ticket re-runs against the real cache-hit path)
- TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION (DONE; fixed the doc_id/source_id evidence-ID
  mismatch this epic's evidence-fingerprint validation reuses)
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC (BACKLOG; supplies the existing
  `retrieval_cache.db`/marker-only cache tables this epic's migrations extend, per
  `cache_migration_plan.md`'s "same file, not a second database" decision)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §10 (Cache Design), §20 (Phase 2 bullets)
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md`
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md`
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`
- `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` (the honest FAIL
  result this epic responds to)
- `docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md` (child 4's own
  honest cold+warm §4.1/§4.2/§4.3 recomparison result — 0/7 genuine cache hits, all thresholds
  FAIL, closing this epic's acceptance loop)

## Related Stored Artifacts
None yet — scope-only epic, no staging artifacts per the Phase 0/Phase 1 epics' own precedent.

## Related Code Areas
- `tools/retrieval_cache.py` (existing marker-only cache module this epic's migrations extend)
- `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_router.py`,
  `tools/knowledge_gateway_packet_assembly.py` (Phase 1's frozen gateway this epic wires a cache
  into — read/write additions only, no redesign)
- `knowledge-index/retrieval_cache.db` (the file this epic's migrations extend)

## Assumptions / Open Questions
- Exact module/file layout for the new cache read/write layer (extend
  `tools/knowledge_gateway_packet_assembly.py` in place, or a new sibling module) is not decided
  here — the first child ticket's Investigate/Plan phases should decide based on the real,
  already-landed Phase 1 module structure.
- Whether the token-reduction threshold miss needs its own dedicated follow-up ticket (a leaner
  response mode, opt-in verbosity control) is not decided here — this epic's acceptance-measurement
  child ticket should surface this honestly once real numbers exist, and a human reviewer decides
  whether that follow-up is warranted, mirroring the Phase 0 epic's own §24-ratification precedent.

## Implementation Notes
(pending — scope-only epic; no direct implementation)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)

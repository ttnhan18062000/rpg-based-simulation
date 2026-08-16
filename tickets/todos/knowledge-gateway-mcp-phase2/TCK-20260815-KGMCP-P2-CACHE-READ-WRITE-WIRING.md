---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING
phase: open
date: 2026-08-15
tags: [ai, mcp]
---

# TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING

## Title
Wire cache lookup, evidence-fingerprint validation, and cache write into the real Phase 1 gateway

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS` builds the schema; `TCK-20260815-KGMCP-P2-
REDACTION-WRITE-PATH` builds the redaction/write-path functions. This ticket wires both into the
real, already-shipped Phase 1 gateway's actual request handling: on `knowledge_context`, check the
cache first (validating direct evidence fingerprints per §12.2, falling back to provider generation
only when finer-grained evidence isn't available per §12.1's fallback rule), serve a real hit when
valid, and write a real, redacted, policy-compliant result on a miss.

## Scope
- Implement cache-lookup identity per `evidence_cache_identity_contract.md` §1 (normalized_intent,
  resolved_entity_ids, filters, budget_class, routing_policy_version, repo_branch_scope) as the real
  key computed from a real `knowledge_context` request.
- Implement evidence-validity checking per §2/§3's non-collapse rule: lookup identity and
  evidence-validity identity are checked as genuinely separate steps, never collapsed into one.
- Implement §12.2's lazy, read-time evidence-fingerprint revalidation: re-check direct evidence
  fingerprints before serving a hit, falling back to `PROVIDER_GENERATION`-level validation only
  when the provider capability contract lacks reliable finer-grained evidence (per
  `evidence_cache_identity_contract.md` §4's already-frozen fallback rule).
- Implement §12.3's branch/working-tree awareness: cache scope includes repository identity,
  branch/detached-HEAD marker, HEAD commit (recorded for provenance, not itself a cache-miss
  trigger), and a fingerprint of relevant uncommitted changes — computed only for the overlap
  between changed paths and cached evidence paths, never a full working-tree hash per request.
- On a genuine cache miss, call the real providers (exactly as Phase 1's `knowledge_context` already
  does), assemble the packet as Phase 1 already does, then write the result through the redaction
  write-path (dependency ticket) before returning it.
- On a genuine cache hit, return the cached, already-redacted result without a provider round-trip
  — this is the behavior `TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON` will measure.
- Update `knowledge_status`'s response to include real cache-domain fields Phase 1 explicitly
  omitted (cache entry counts, hit/miss rates, staleness counts) — now genuinely populable since a
  real cache exists.

## Out of Scope
- Any change to routing decisions (`tools/knowledge_gateway_router.py` stays untouched) or
  extractive rendering logic in `tools/knowledge_gateway_packet_assembly.py` beyond the minimal
  hook needed to check/write the cache — this ticket adds caching around Phase 1's existing
  pipeline, it does not redesign that pipeline.
- Level 2 (context-packet) or Level 3 (verified knowledge) caching — Phase 3/6.
- Semantic/fuzzy cache-key matching (Phase 5) — this ticket implements exact normalized-query reuse
  only.
- Cache-GC scheduling/automation — the GC defaults are defined by the dependency ticket; actually
  running GC on a schedule (vs. on-demand/manual) is not required here unless Plan finds it trivial
  to include.

## Acceptance Criteria
- [ ] An identical repeated `knowledge_context` call (same normalized intent/entity IDs/filters/
      budget class) produces a genuine cache hit on the second call — verified by a real test
      proving the second call never reaches `_run_search()`/`graphify query`.
- [ ] A cache hit is rejected and refreshed when its direct evidence fingerprint no longer matches
      real repository state (e.g. a cited document's content hash changed) — real test, not a
      documentation claim.
- [ ] The `PROVIDER_GENERATION` fallback genuinely triggers only when the provider capability
      contract lacks finer-grained evidence (confirmed against the real
      `provider_capabilities_*.json` files, same providers Phase 1 already validated) — never used
      as the default path when finer-grained evidence IS available.
- [ ] Branch/working-tree scope is real: a cached result from one branch is not served on an
      unrelated branch when the underlying evidence differs; a new commit alone does not force a
      cache miss when direct evidence is unchanged.
- [ ] Cache writes go through `TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH`'s real functions — no
      raw/unredacted write path exists anywhere in this ticket's code.
- [ ] `knowledge_status`'s cache-domain fields (previously omitted per Phase 1's own honest
      not-yet-available disclosure) are now real and populated from the real cache.

## Related Tickets
- TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE2-EPIC (parent)
- TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS (dependency)
- TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH (dependency)
- TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE (DONE; the real gateway this ticket adds caching to —
  read, do not modify its routing/assembly logic beyond the minimal cache hook)
- TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY (DONE; the identity/fallback contracts this ticket
  implements as real logic for the first time)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §12, §12.1, §12.2, §12.3
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/knowledge_gateway_mcp.py` (the request-handling hook point)
- `tools/retrieval_cache.py` (the schema/write-path this ticket reads/writes through)

## Assumptions / Open Questions
- Whether the cache-lookup hook belongs inside `tools/knowledge_gateway_mcp.py`'s
  `_run_knowledge_context()` directly, or as a new thin wrapper layer between it and the router/
  packet-assembler — Investigate should decide based on the real, already-landed Phase 1 code
  structure, minimizing invasiveness to Phase 1's frozen logic.

## Implementation Notes
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)

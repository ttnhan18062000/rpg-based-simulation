---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING
phase: open
date: 2026-08-16
tags: [ai, mcp, security]
---

# TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING

## Title
Wire real Level 2 context-packet cache lookup and write into the live `_run_knowledge_context()`,
checked before Level 1

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS` builds the Level 2 schema;
`TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT` builds real deduplicated, budget-enforced
packet assembly; `TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION` builds packet dependency
records and targeted invalidation. This ticket wires all three into the real, already-shipped
`_run_knowledge_context()` call path: on `knowledge_context`, check Level 2 (the assembled-packet
cache) FIRST for an exact packet match, serve a real hit when valid, and only on a genuine Level 2
miss fall back to Level 1 (the already-wired provider-result cache from Phase 2) or, on a further
miss, live providers — mirroring `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`'s own precedent of
adding a layer around Phase 1's existing pipeline, not redesigning it. This ticket adds a layer, it
does not redesign the existing Level 0/1 pipeline Phase 1/Phase 2 already shipped.

## Scope
- Implement Level 2 lookup identity (packet-level equivalent of §1's normalized_intent/
  resolved_entity_ids/filters/budget_class/routing_policy_version/repo_branch_scope) as the real
  key computed from a real `knowledge_context` request, reusing `compute_lookup_identity()` where
  the identity shape is genuinely the same as Level 1's, extending it only where a packet-level
  identity genuinely differs (e.g. budget_tokens as part of the key, since two requests for the same
  question at different budgets may need different assembled packets).
- On a Level 2 hit (exact packet match, dependency-invalidation-checked per the dependency ticket's
  real logic), return the cached, already-assembled, already-redacted packet payload without
  reassembling from Level 1/live providers.
- On a Level 2 miss, fall through to Level 1's already-wired provider-result cache lookup exactly as
  it already works today (Phase 2's real, unmodified behavior), assemble the packet using the
  dedup/budget-enforcement ticket's real logic, then write the result through the Level 2
  write-path before returning it.
- **Explicit re-verification requirement, not an assumption:** independently verify whether
  Level 1's existing write-path enforcement (`tools/knowledge_gateway_redaction.py`'s
  `evaluate_write_candidate()`, allowlist, secret-scan, `MAX_PAYLOAD_BYTES = 65536` size cap)
  correctly applies to Level 2 packet payloads too, given a packet aggregates content from
  potentially multiple provider results and may be a materially different shape/size than a single
  Level 1 row. Do not assume Level 1's write-path enforcement automatically covers Level 2 — call it
  and prove with a real test that a Level 2 write is genuinely gated through the same (or an
  explicitly justified equivalent) redaction/secret-scan/size-cap machinery, with no bypass path.
- Update `knowledge_status`'s response to include real Level 2 cache-domain fields (Level 2 entry
  counts, Level 2 hit/miss rates, Level 2 vs. Level 1 hit attribution) — distinct from, and
  additive to, Phase 2's already-real Level 1 fields.

## Out of Scope
- Any change to routing decisions (`tools/knowledge_gateway_router.py` stays untouched) beyond the
  minimal hook needed to check/write the Level 2 cache.
- Level 3 (verified reusable knowledge) caching — Phase 6.
- Semantic/fuzzy cache-key matching (Phase 5) — this ticket implements exact normalized-identity
  reuse only, at the packet level.
- Redesigning or weakening Level 1's existing lookup/write behavior — this ticket adds a Level 2
  check in front of it; Level 1's own already-tested logic (`TCK-20260815-KGMCP-P2-CACHE-READ-
  WRITE-WIRING`) is reused as-is, not modified, except for the minimal call-site change needed to
  fall through from a Level 2 miss.
- Assuming (rather than verifying) that Level 1's write-path enforcement covers Level 2 payloads —
  see the Scope section's explicit re-verification requirement; if verification finds a genuine gap,
  closing that gap is in scope for this ticket (it is the ticket that makes Level 2 writes live), but
  silently assuming coverage without checking is explicitly disallowed.
- Cache-GC scheduling/automation beyond what the dependency-invalidation ticket already defines.

## Acceptance Criteria
- [ ] An identical repeated `knowledge_context` call (same normalized intent/entity IDs/filters/
      budget class/budget_tokens) produces a genuine Level 2 cache hit on the second call — verified
      by a real test proving the second call never reaches packet assembly or the Level 1 lookup at
      all (not merely that it skips live providers).
- [ ] A Level 2 miss correctly falls through to Level 1's existing, unmodified lookup behavior —
      verified by a real test showing Level 1 is still consulted on a Level 2 miss, exactly as
      before this ticket landed.
- [ ] A Level 2 hit is rejected and refreshed when the underlying packet's dependency-invalidation
      logic (from the dependency ticket) determines it stale — real test, not a documentation claim.
- [ ] Level 2 cache writes are independently verified — not assumed — to go through real redaction/
      secret-scan/size-cap enforcement with no bypass path; if this required extending or adapting
      Level 1's existing `evaluate_write_candidate()` call for packet-shaped payloads, that
      extension itself is tested.
      (`test_level2_cache_write_calls_evaluate_write_candidate_before_any_insert`,
      `test_no_raw_insert_statement_bypasses_redaction_anywhere_in_level2_cache_module` — exact
      test names TBD by this ticket's own test_plan.md, mirroring the Level 1 precedent's naming.)
- [ ] Branch/working-tree scope from the dependency ticket is genuinely enforced before a Level 2
      hit is served — real test.
- [ ] `knowledge_status`'s Level 2 cache-domain fields are real and populated from the real Level 2
      cache, distinct from Level 1's existing fields.
- [ ] `tools/knowledge_gateway_router.py` remains byte-unchanged.
- [ ] A real, schema-valid `docs/parity_ledger/infrastructure.yaml` entry is added for this
      ticket's own behavior change, per this repo's own governance rule.

## Related Tickets
- TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE3-EPIC (parent)
- TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS (dependency)
- TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT (dependency)
- TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION (dependency)
- TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING (DONE; the real Level 1 wiring this ticket falls
  through to on a Level 2 miss — read, do not modify beyond the minimal call-site hook)
- TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION (DONE; the real `MAX_PAYLOAD_BYTES = 65536`
  value this ticket's write-path re-verification checks against Level 2 payload sizes)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §10.2, §10.3, §12.1-§12.3, §20 Phase 3, §21
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md`
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §4, §5, §6, §11 (the
  write-path enforcement this ticket must verify, not assume, applies to Level 2 payloads)
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` §2

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/knowledge_gateway_mcp.py` (`_run_knowledge_context()`, `_run_knowledge_status()` — the
  request-handling hook points this ticket extends)
- `tools/knowledge_gateway_cache.py` (Level 1's real orchestration module — the direct structural
  precedent for this ticket's Level 2 orchestration; may be extended in place or given a Level 2
  sibling module, per this ticket's own Investigate-phase decision)
- `tools/retrieval_cache.py` (Level 2 schema/read/write functions this ticket calls)
- `tools/knowledge_gateway_redaction.py` (the write-path enforcement this ticket's own scope
  requires independently re-verifying against Level 2 payload shapes)

## Assumptions / Open Questions
- Whether the Level 2 orchestration lives inside `tools/knowledge_gateway_cache.py` (extended in
  place) or a new sibling module (e.g. `tools/knowledge_gateway_packet_cache.py`) is not decided
  here — Investigate should decide based on the real, already-landed Level 1 module structure,
  minimizing invasiveness, consistent with how the Level 1 wiring ticket itself made this same
  choice for its own module.
- Whether Level 1's `evaluate_write_candidate()` needs a genuine code change to correctly handle
  packet-shaped payloads (multi-source aggregated content) versus working unmodified because its
  redaction/scan logic already operates on raw text regardless of source shape, is the central open
  question this ticket's own Investigate phase must resolve — not assumed either way here.
- Whether budget_tokens should be part of the Level 2 lookup-identity key (two different budgets for
  the same question producing two different cached packets) or handled by re-deriving a smaller
  packet from one canonical cached packet is left open — Investigate/Plan should decide with
  reference to the dedup/budget-enforcement ticket's own chosen tolerance mechanism.

## Implementation Notes
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)

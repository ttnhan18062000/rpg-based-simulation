---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY
phase: open
date: 2026-08-14
tags: [ai, security, process-improvement]
---

# TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY

## Title
Ratify the Knowledge Gateway cached-payload redaction/retention policy and freeze operational
limits (token-counting, budget tolerance, SQLite limits, cache-GC defaults)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`docs/plans/knowledge-gateway-mcp-proposal.md` §17 requires the gateway to inherit and extend the
existing retrieval redaction policy before any cached payload is written, with an explicit
allowlist/redaction/secret-scan/size-cap pipeline. §19 requires SQLite operational defaults (max
database size, TTL/usage-based eviction, crash-recovery tests, restrictive file permissions, WAL
mode, busy timeouts, one-writer-safe migrations, per-key lease/transaction guard against cache
stampedes) before payload caching is enabled. §15/§24 item 4 requires a reproducible token-counting
method and budget-class tolerance. §24 item 1 requires reviewers to explicitly ratify or reject
caching bounded/redacted answer/context payloads from allowlisted source types at all — this ticket
produces the artifact that review decides on, it does not itself decide it.

## Scope
- Draft the cached-payload policy for review (§17, §24 item 1): eligible source types/paths
  allowlist, redaction of local usernames and machine-specific absolute paths, existing
  secret-detection rule reuse, payload size cap, and a recorded redaction-policy version. Explicitly
  enumerate what must never be cached: secrets/credentials, tokens, raw environment values,
  unredacted sensitive tool output, arbitrary configuration-file contents, unrestricted raw prompts.
- Define the reproducible token-counting method and budget-class tolerance (§15, §24 item 4) used
  to measure `budget_requested`/`budget_returned` and to validate the Phase 3 pilot's "returned
  content respects the requested budget within a documented tolerance" acceptance bar (§21).
- Freeze SQLite operating limits: maximum database size, TTL/usage-based eviction rules, restrictive
  file permissions, WAL mode where supported, bounded transactions, busy timeouts, one-writer-safe
  migration discipline, and a per-key lease/transaction guard against cache stampedes (§19).
- Define cache-GC defaults and safe-eviction candidates (§19): expired exact-query results, packets
  for deleted branches, obsolete provider-version rows, low-use regenerable packets, stale rows
  superseded by refreshed rows, failed/incomplete writes — while confirming historical project
  facts remain in authoritative sources regardless of cache eviction.
- Write crash-recovery tests validating the database can be deleted and rebuilt without losing
  project truth (§10.1, §19, §21).

## Out of Scope
- Implementing the cache read/write paths — Phase 0 is policy/contract-only.
- MCP schemas and evidence/cache-identity contracts — covered by
  `TCK-20260814-KGMCP-CONTRACT-SCHEMAS` and `TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`
  respectively; this ticket's policy must be compatible with both once they land.
- Deciding §24's open questions outright — this ticket drafts the policy artifact; ratification is
  an explicit reviewer decision per the epic's Acceptance Criteria.

## Acceptance Criteria
- [ ] A written redaction/retention policy document exists covering the allowlist, redaction rules,
      secret-scan reuse, payload size cap, and redaction-policy versioning from §17.
- [ ] The policy explicitly enumerates the never-cache categories from §17 with no ambiguity.
- [ ] A reproducible token-counting method and budget-class tolerance definition exists, referenced
      by name from `TCK-20260814-KGMCP-CONTRACT-SCHEMAS`'s budget fields.
- [ ] SQLite operational limits (max size, eviction rules, WAL/busy-timeout/permissions defaults,
      stampede guard) are documented and testable.
- [ ] Cache-GC default rules are documented, distinguishing disposable cache rows from durable
      project truth that must never be evicted alongside them.
- [ ] A crash-recovery test demonstrates the (currently-empty-schema) database can be deleted and
      rebuilt with no loss of authoritative project truth.
- [ ] The policy artifact is explicitly flagged as requiring reviewer ratification (§24 item 1)
      before Phase 2 payload caching may begin — this ticket does not self-ratify.

## Related Tickets
- TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC (parent)
- TCK-20260814-KGMCP-CONTRACT-SCHEMAS (sibling; this policy's token-counting method feeds that
  ticket's budget fields)
- TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY (sibling; this policy's GC rules must not evict rows
  that identity contract still considers valid evidence)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §15, §17, §19, §21, §24

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/retrieval_cache.py`
- `tools/retrieval_events.py` (existing redaction precedent to extend, not replace)

## Assumptions / Open Questions
- Whether this repo's existing secret-detection rules (used elsewhere in the retrieval/redaction
  pipeline) are directly reusable as-is or need a Knowledge-Gateway-specific extension —
  Investigate must confirm by reading the existing redaction implementation before drafting the
  allowlist, not assume.
- §24 item 1 itself (ratify or reject payload caching at all) remains an open reviewer decision this
  ticket's artifact feeds but does not resolve.

## Implementation Notes
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)

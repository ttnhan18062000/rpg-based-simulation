---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE1-EPIC
phase: done
date: 2026-08-15
tags: [ai, mcp, process-improvement]
---

# TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE1-EPIC

## Title
Local Knowledge Gateway MCP — Phase 1: Read-Only Gateway

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC` closed Phase 0 (contracts, ratified redaction/retention
policy, ratified token-counting method, measurement baseline, and an inert pre-scan-mandate
relaxation draft) on 2026-08-15. `docs/plans/knowledge-gateway-mcp-proposal.md` §20's own
Incremental Delivery Plan gates each phase as a separate authorization boundary — Phase 0's epic
explicitly did not authorize any Phase 1+ work. This epic tracks and gates **Phase 1: Read-Only
Gateway** (§20) as the next, separately-authorized increment: a deterministic-routing, uncached,
extractive/template-only MCP gateway exposing `knowledge_context` and `knowledge_status` over the
already-frozen Phase 0 contracts.

Phase 1 explicitly excludes caching (Phase 2), model-generated synthesis or model-based intent
classification (deferred, per §9.1), Parity Ledger routing (Phase 4), and any change to
`CLAUDE.md`'s current search-before-grep mandate (still gated on
`TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`'s retro-confirmed compliance signal, per the
Phase 0 draft's own activation precondition — unaffected by this epic).

## Scope
- Gate all work strictly to Phase 0's already-frozen contracts plus Phase 1's own §20 bullets:
  deterministic routing, `knowledge_context`/`knowledge_status` MCP tool exposure, uncached
  normalized results with provenance, deterministic classification and extractive/template packet
  assembly only, preserved direct provider tools, and fail-open behavior.
- Register the new MCP server as an ambient, phase-agnostic repository utility (`.mcp.json` entry),
  callable without any ticket/workflow/run-ID metadata, consistent with proposal §2.1's positioning.
- Reuse Phase 0's frozen artifacts as the implementation's actual contract surface: the JSON
  Schemas under `docs/engine/contracts/knowledge_gateway_mcp/`, the populated
  `provider_capabilities_context_search.json`/`provider_capabilities_graphify.json` descriptors, the
  ratified redaction/retention policy (§2–§10 of `redaction_retention_policy.md`), and the
  `kgmcp_char_heuristic_v1` token-counting method.
- Wire `tools/retrieval_events.py`'s 3 Wrapper functions (`wrap_hybrid_retrieval`,
  `wrap_retrieval_cache_check`, `wrap_context_packet_assembly`) into this gateway's real call
  sites — Phase 0's measurement-baseline contract explicitly flagged them as "implemented but not
  invoked by any live call site"; Phase 1 is the first opportunity to close that gap honestly,
  where it is architecturally correct to do so (not forced into an unrelated call site).

## Out of Scope
- Any caching (Phase 2): no SQLite payload writes, no cache-hit/miss logic, no
  `tools/retrieval_cache.py` schema changes. `knowledge_status`'s Phase 1 response omits all
  cache-specific fields (hit/miss rates, cache entry counts, staleness counts) that §9.2 lists —
  those require Phase 2's cache to exist first; a Phase 1 ticket will define the reduced field set.
- Model-generated synthesis or model-based intent classification (§9.1: "deferred until separately
  approved").
- Parity Ledger as a routed provider (Phase 4).
- Context-packet caching, token-budget enforcement via measured cache size, or packet dependency
  records (Phase 3).
- Any change to `CLAUDE.md`, `.claude/agents/*.md`, or `.claude/skills/*.md` — in particular, this
  epic does **not** activate `docs/ai/claude_md_prescan_mandate_relaxation_draft.md`. Registering
  the new MCP server in `.mcp.json` makes the tool *available*; it does not make the tool
  *mandatory* or change any existing search-before-grep instruction.
- `knowledge_learn`, `knowledge_promote`, `knowledge_verify`, or any invalidation tool (§9.3:
  explicitly deferred tools).
- Claim/fact/inference/decision durable records or promotion governance (Phase 6).

## Acceptance Criteria
- [x] Only Phase 1 (§20) work is scoped/authorized under this epic; no Phase 2+ deliverable
      (caching, packet-dependency invalidation, Parity routing, semantic reuse, durable knowledge
      records) is claimed as done here. Verified: no child ticket introduced caching,
      `tools/retrieval_cache.py` untouched throughout.
- [x] `knowledge_context` and `knowledge_status` are exposed as real, callable MCP tools, registered
      in `.mcp.json`, conforming to Phase 0's frozen request/response JSON Schemas. Delivered by
      `TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE`; real `jsonschema.Draft7Validator` used for both
      request and response validation.
- [x] Routing is deterministic only (§8's stable-identifier recognition plus the intent/provider
      table); no model-based classification exists in this epic's code. Delivered by
      `TCK-20260815-KGMCP-P1-QUERY-ROUTER`.
- [x] Every response's `answer`/`context` content is a rendering of `statements` entries, each
      pointing to real `evidence_ids`; nothing is fabricated when the token budget cannot be met
      (§15, §16's token-budget-assembly-failure row). Delivered by
      `TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY`; structural (non-hardcoded-string) fabrication guards
      enforced by test.
- [x] Fail-open behavior is real and tested: gateway process unavailable → agents still have direct
      provider tools; one provider unavailable → partial result with explicit provider failure, not
      a hard error. Delivered by `TCK-20260815-KGMCP-P1-FAILOPEN-TESTS`; 13 tests proving all 5
      Phase-1-applicable §16 rows.
- [x] `docs/plans/knowledge-gateway-mcp-proposal.md` §20's Phase 1 bullets are annotated Done as
      child tickets land, mirroring the Phase 0 epic's own annotation convention. All 6 Phase 1
      bullets confirmed Done.
- [x] `CLAUDE.md`, `.claude/agents/*.md`, and `.claude/skills/*.md` remain byte-unchanged by every
      child ticket in this epic — verified per-ticket via the same git-diff-based regression
      pattern `TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT` established. Confirmed empty
      diff on every one of the 5 child tickets, independently re-verified at Architecture-Verify and
      Verify for each.
- [x] This epic is not closed merely because a child ticket's code lands — Phase 1's own bar (all
      §20 Phase 1 bullets Done, `knowledge_context`/`knowledge_status` real and passing acceptance
      tests against a real repository query set) must be met. This bar IS met: all bullets Done, both
      tools are real and structurally tested (100% pass rate across all 5 children's own test
      suites), and `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON` genuinely ran the required acceptance
      test against a real repository query set. **Separately and honestly recorded** (see Completion
      Summary): that acceptance run found all 3 of `measurement_baseline_contract.md` §4's
      *performance* thresholds (predeclared as Phase 3's pilot-promotion bar, not this epic's own
      closure bar) currently FAIL. This epic's own AC bar concerns Phase 1 functioning correctly and
      being honestly measured — it does not require the §4 performance thresholds to pass; whether
      to proceed toward Phase 2/3 given this result is a separate, later decision.

## Related Tickets
- TCK-20260815-KGMCP-P1-QUERY-ROUTER (child 1; deterministic routing — see SEQUENCE.md)
- TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY (child 2; statement/evidence/packet assembly)
- TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE (child 3; real `knowledge_context`/`knowledge_status`
  FastMCP tools)
- TCK-20260815-KGMCP-P1-FAILOPEN-TESTS (child 4; §16 failure-matrix test suite)
- TCK-20260815-KGMCP-P1-BASELINE-COMPARISON (child 5; measures the real gateway against the Phase 0
  baseline corpus — closes this epic's acceptance loop. Landed 2026-08-15 with an honest result: all
  3 of `measurement_baseline_contract.md` §4's predeclared thresholds — §4.1 latency, §4.2 token
  reduction, §4.3 no-regression recall — FAIL, in aggregate and for every one of the 7 corpus
  entries. No threshold was redefined and no entry excluded. Full numbers:
  `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md`)
- TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC (DONE; parent Phase 0 epic — supplies every frozen
  contract this epic implements against)
- TCK-20260814-KGMCP-CONTRACT-SCHEMAS (DONE; wire/provider JSON Schemas this epic's tools must
  conform to)
- TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY (DONE; evidence-identity kinds this epic's provenance
  fields reuse — cache-lookup identity itself is Phase 2, out of scope here)
- TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY (DONE, ratified; token-counting method
  `kgmcp_char_heuristic_v1` this epic's token-budgeted assembly must use)
- TCK-20260814-KGMCP-MEASUREMENT-BASELINE (DONE; real-run corpus/fixture this epic's acceptance
  tests should extend, not duplicate; also names the 3 unwired Wrapper functions this epic wires in)
- TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT (DONE; the still-inert CLAUDE.md draft this
  epic must not activate)
- TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP (DONE; its retro-confirmed compliance signal is
  the precondition for a *future*, separate ticket to activate the pre-scan-mandate draft — still
  not this epic's concern)
- TCK-20260612-LOCAL-CTX-MCP (DONE; the existing `tools/search_mcp.py` FastMCP server this epic's
  new MCP server mirrors the shape of, and must never remove or hide per the fail-open requirement)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §8 (Query Routing), §9 (MCP Tool Surface), §13
  (Authority and Provenance), §14 (Conflict Handling), §15 (Token-Budgeted Assembly), §16 (Failure
  and Fallback Semantics), §20 (Phase 1 bullets), §21 (Phase 3 Pilot Acceptance Criteria — forward
  reference only, not this epic's bar)
- `docs/engine/contracts/knowledge_gateway_mcp_contract.md` and the sibling schema/contract files
  under `docs/engine/contracts/knowledge_gateway_mcp/`

## Related Stored Artifacts
None yet — scope-only epic, no staging artifacts per the Phase 0 epic's own precedent.

## Related Code Areas
- `tools/search_mcp.py` (existing FastMCP server this epic's new server mirrors, must not modify or
  remove)
- `tools/retrieval_events.py` (the 3 Wrapper functions this epic wires into a real call site)
- `tools/agent-monitoring/kgmcp_baseline_corpus.py`,
  `tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json` (Phase 0's real-run corpus
  this epic's acceptance tests extend)
- `.mcp.json` (new server registration)
- New: `tools/knowledge_gateway_mcp.py` or equivalent (exact module name/layout is this epic's own
  first child ticket's decision, not pre-decided here)

## Assumptions / Open Questions
- Exact module/file layout for the new gateway server (single file vs. a `tools/knowledge_gateway/`
  package) is not decided here — the first child ticket's Investigate/Plan phases should decide
  based on `tools/search_mcp.py`'s existing shape and this repo's own module-size conventions.
- Whether `knowledge_status`'s Phase-1-appropriate field set (with all cache-specific fields
  omitted) needs its own frozen JSON Schema variant, or can reuse
  `knowledge_status_response.schema.json` with cache fields treated as always-null/omitted in this
  phase — flagged for the MCP-tool-surface child ticket's Investigate phase to resolve against the
  existing frozen schema before Plan.
- **2026-08-15 note, not yet resolved:** child 5 (`TCK-20260815-KGMCP-P1-BASELINE-COMPARISON`) ran
  the real gateway against the real Phase 0 7-entry corpus and found all 3 of
  `measurement_baseline_contract.md` §4's predeclared promotion thresholds (§4.1 latency, §4.2
  token reduction, §4.3 no-regression recall) FAIL, in aggregate and per-entry — see
  `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` for the full numbers
  and root-cause analysis. None of this epic's own Acceptance Criteria above cite §4 by name (this
  epic's stated Phase 1 bar is the §20 checklist plus passing MCP tool-surface acceptance tests,
  not §4's promotion thresholds — §21's Phase 3 pilot bar is the forward reference that would
  consume §4-style thresholds), so this finding does not by itself contradict any checked box here.
  It is, however, real and unresolved evidence directly bearing on whether/how to proceed toward
  Phase 2 — a separate human-reviewer decision this epic does not make (see Out of Scope). Whoever
  closes this epic should read the real numbers before writing a Completion Summary, rather than
  characterizing Phase 1 as an unqualified success.

## Implementation Notes
Scope-only epic; no direct implementation by this ticket. All work delivered through its 5 child
tickets, in dependency order per SEQUENCE.md:
- `TCK-20260815-KGMCP-P1-QUERY-ROUTER` — deterministic routing, capability-aware, INFRA-335 (DONE)
- `TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY` — extractive statement/evidence/packet assembly,
  INFRA-336 (DONE)
- `TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE` — real knowledge_context/knowledge_status FastMCP
  tools, INFRA-337 (DONE; required 4 architecture-review passes to reject and correct an
  unauthorized scope-creep attempt before landing)
- `TCK-20260815-KGMCP-P1-FAILOPEN-TESTS` — real fail-open code fixes + 13-test §16 failure-matrix
  suite, INFRA-338 (DONE)
- `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON` — real gateway measured against Phase 0's frozen
  corpus, INFRA-339 (DONE; honest result: all 3 §4 thresholds FAIL for all 7 entries — see
  Completion Summary)

## Test Summary
Each child ticket ran and passed its own scoped test suite (31+27+12+13+14 = 97 new tests across
the 5 children, all passing), plus full regression coverage across all sibling suites at every
step. No test failure traced to this epic's own work at any point; the only failures encountered
throughout (3 tests, all pointing to `docs/mechanics/content_usage_matrix.md`'s pre-existing
missing frontmatter) were independently confirmed via `git log` to predate this epic entirely and
are explicitly out of its scope.

## Files Changed
No files changed directly by this epic ticket's own work beyond its own frontmatter/body (this
edit). All substantive changes are attributed to and listed in the 5 child tickets' own Files
Changed sections.

## Completion Summary
Closed the knowledge-gateway-mcp-phase1 epic after all 5 child tickets landed. All 8 of this
epic's own Acceptance Criteria are independently verified true: `knowledge_context` and
`knowledge_status` are real, schema-validated FastMCP tools; routing is deterministic-only; every
response traces to real evidence with structural fabrication guards; fail-open behavior is real
and tested against all 5 Phase-1-applicable §16 rows; all 6 §20 Phase 1 bullets are annotated Done;
`CLAUDE.md`/`.claude/agents/*.md`/`.claude/skills/*.md` remained byte-unchanged across all 5
children, independently re-verified at every Architecture-Verify and Verify step.

**Honest, separately-recorded result from the acceptance measurement itself:**
`TCK-20260815-KGMCP-P1-BASELINE-COMPARISON` ran the real Phase 1 gateway against Phase 0's frozen
7-entry corpus and found that all 3 of `measurement_baseline_contract.md` §4's predeclared
promotion thresholds — minimum latency, minimum token reduction, no-regression-recall — FAIL, in
aggregate and for every one of the 7 entries. This was independently re-verified as a genuine,
unmanipulated negative result by 2 separate review passes (one tracing the root causes to real code
— no cache exists yet for Phase 1 so every call is necessarily cold against a threshold framed as a
warm-hit bar; the structured JSON response outweighs routing's token savings; and a genuine
`doc_id`-vs-`source_id` normalization discrepancy between `search_mcp.py` and the gateway's
evidence-ID derivation). No threshold was redefined, no corpus entry was excluded, and Phase 1 is
not characterized as an unqualified success. §4's thresholds are Phase 3's pilot-promotion bar per
the proposal's own framing, not this epic's own closure bar — this epic's Acceptance Criteria
concern Phase 1 functioning correctly and being honestly measured, both of which are true. Whether
and how to proceed toward Phase 2 or address the measured performance gap first is a separate,
later decision for the epic owner, explicitly flagged as unresolved in this ticket's own
Assumptions/Open Questions history (added during `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON`'s
Document-Update phase) and now folded into this closing summary.

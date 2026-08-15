---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY
phase: done
date: 2026-08-15
tags: [ai, mcp]
---

# TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY

## Title
Deterministic, extractive/template packet assembly: statements, evidence, provenance, and
token-budgeted truncation

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Given a routing decision and raw provider results (from `TCK-20260815-KGMCP-P1-QUERY-ROUTER`),
assemble the deterministic, extractive/template-only packet content proposal §9.1/§13/§14/§15
define: `statements` (each `FACT`/`INFERENCE`/`DECISION`-labeled, pointing to real `evidence_ids`),
`context`, `evidence`, `provenance_providers`, structural conflict representation, and
token-budgeted truncation using the ratified `kgmcp_char_heuristic_v1` method. No MCP server code,
no caching. Depends on `TCK-20260815-KGMCP-P1-QUERY-ROUTER` for routing input.

## Scope
- Implement statement construction: every `answer`/`context` sentence must trace to one or more
  `statements[]` entries, each with a real `evidence_id` — assembled by rendering, not
  paraphrasing or synthesizing, retrieved provider content (§9.1: "extractive/template-based
  assembly", no model generation).
- Implement the `FACT`/`INFERENCE`/`DECISION` classification (§13) as an ephemeral per-statement
  label only — no durable claim entity, no promotion, matching §13's explicit early-phase scope.
- Implement negative-knowledge support per §13.1's `NegativeClaimSupport` shape: an empty provider
  result alone must never be rendered as evidence of absence; only providers whose capability
  descriptor declares `negative_knowledge_support != NONE` may contribute to a negative claim, and
  the claim must carry `validated_scopes[]`/`exclusions_or_blind_spots[]`, defaulting to
  `UNVERIFIED` when scope completeness can't be established.
- Implement structural-only conflict detection per §14: represent conflicts already exposed by
  providers (explicit supersession metadata, incompatible current document records) — do not add
  semantic/model-based conflict comparison (explicitly deferred to Phase 6).
- Implement §15 token-budgeted assembly: priority order (invariants/decisions →
  facts/symbols/parity status → tests/dependencies → history → optional background), deduplication
  before truncation (one statement + multiple evidence refs, not repeated excerpts), and real
  measurement of returned content via `kgmcp_char_heuristic_v1` — never an estimate multiplied by
  candidate count.
- Implement the §16 token-budget-assembly-failure fallback: on a budget that cannot fit the minimum
  required content, return a smaller evidence list or provider references, never fabricated
  content.
- Output is a plain typed packet record — not yet an MCP JSON-RPC response envelope (that's the
  MCP-tool-surface ticket's job); this ticket's tests operate directly on the packet type.

## Out of Scope
- MCP tool exposure — separate ticket (`TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE`).
- Query routing itself — consumes `TCK-20260815-KGMCP-P1-QUERY-ROUTER`'s output, does not
  reimplement routing.
- Caching of assembled packets (Phase 3).
- Model-generated synthesis (deferred).
- Semantic/model-based conflict comparison (Phase 6).
- Durable claim/fact/inference/decision records or promotion (Phase 6).

## Acceptance Criteria
- [x] Every rendered sentence in a test packet's `answer`/`context` traces to a real
      `statements[].evidence_ids` entry; a test asserts this invariant structurally (e.g. via a
      linter over the assembled packet, not manual inspection).
- [x] Negative-knowledge claims are rejected/downgraded to `UNVERIFIED` when the contributing
      provider's capability descriptor lacks `negative_knowledge_support`, or when
      `validated_scopes[]` cannot be established as complete — tested against both frozen provider
      capability fixtures.
- [x] Token-budgeted assembly uses `kgmcp_char_heuristic_v1` to measure real returned content, with
      a test proving `budget_returned` never exceeds `budget_requested` and deduplication occurs
      before truncation (a duplicated fact across 2 providers yields 1 statement with 2 evidence
      IDs, not 2 statements).
- [x] A budget-assembly-failure test proves the fallback returns a smaller real list, never
      fabricated placeholder content.
- [x] Conflict representation only ever surfaces conflicts backed by real supersession/document
      metadata already present in a provider's own result — no test exercises a semantic-judgment
      code path, since none exists.

## Related Tickets
- TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE1-EPIC (parent)
- TCK-20260815-KGMCP-P1-QUERY-ROUTER (dependency; supplies routing decisions and raw provider
  results this ticket assembles into packets)
- TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY (DONE, ratified; source of the
  `kgmcp_char_heuristic_v1` method this ticket implements as a real callable for the first time)
- TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY (DONE; evidence identity kinds this ticket's
  `evidence_ids` reuse)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §9.1, §13, §13.1, §14, §15, §16 (budget-failure
  row)
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §8
  (`kgmcp_char_heuristic_v1`)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §8 (method to
  implement as a real callable — currently documented only, per that ticket's own Out of Scope)
- `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json` (the
  `statements`/`context`/`evidence` shapes this ticket's output must conform to)
- New: a packet-assembly module under `tools/` (path decided alongside the router ticket's Plan
  phase, likely the same package)

## Assumptions / Open Questions
- Whether `kgmcp_char_heuristic_v1` should be implemented as a shared utility importable by both
  this ticket and any future Phase-2+ cache-sizing code, or scoped locally to this module first and
  extracted later if a second real caller appears — Plan phase decides, consistent with this
  repo's no-premature-abstraction convention.

## Implementation Notes
Implemented `tools/knowledge_gateway_packet_assembly.py` following `staging_artifacts/TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY/plan.md`'s 10 ordered steps exactly:

1. `kgmcp_char_heuristic_v1(text) -> int` — real callable, `math.ceil(len(text.encode("utf-8"))/4)`, scoped locally to this module (no second real caller exists, per the repo's no-premature-abstraction convention).
2. `_evidence_id_for_context_search_result()` / `_evidence_id_for_graphify_result()` — derive `DOCUMENT_SECTION`/`TICKET`/`FILE`/`SYMBOL` evidence IDs from the 8 closed kinds. `source_path` (never the chunk-scoped `doc_id`) is the registry-id component; `docs/`-prefixed paths get slugified-heading anchors with ordinal disambiguation (`#overview`, `#overview-2`) via a caller-owned `anchor_counts` dict (never module-global state); `tickets/{inprogress,done}/TCK-*.md` paths get `TICKET`; everything else falls back to `FILE`.
3. `call_providers_for_routing_decision()` — sibling-loads `tools/search_mcp.py` and `tools/knowledge_gateway_router.py` via `importlib.util.spec_from_file_location` under this module's own `sys.modules` keys (independent of the router's own internal sibling-load and of the test suite's own loader), calls `_run_search()`/`match_symbol_name()` directly using `providers_selected` only. Handles `_run_search()`'s `{"error": ...}` shape and `match_symbol_name()`'s `subprocess.TimeoutExpired`/non-zero-returncode/empty-stdout cases without ever treating an error or empty result as content.
4. `render_candidates()` — builds `Statement`/`ContextEntry`/`EvidenceEntry` dataclasses; `text` is always `result["excerpt"].strip()` or `result["stdout"].strip()` verbatim, never edited beyond whitespace-strip; `evidence_id` is computed in the same loop iteration as its statement.
5. `deduplicate_statements()` — groups by normalized (casefold, whitespace-collapsed) exact-text match, provider-agnostic; merges `evidence_ids` into the first-encountered statement.
6. `build_negative_claim_support()` — real, fully-branching `NegativeClaimSupport` logic. Against the two real `provider_capabilities_*.json` descriptors (both `negative_knowledge_support: "NONE"`) this always returns `UNVERIFIED`; `SCOPED`/`COMPLETE` branches are reachable only via a monkeypatched/temp-copy descriptor in tests, documented honestly in both the module docstring and the test file's own module docstring. Wired into `assemble_packet()` as a structural auto-trigger only when zero statements survive rendering.
7. `build_conflicts()` — real, generic structural-signal-key scan (`superseded_by`/`supersedes`/`incompatible_with` via `dict.get()`); always empty against real provider shapes today (neither real provider exposes these keys), never a semantic/topical-similarity heuristic.
8. `assemble_within_budget()` — sorts by `(priority_tier, original order)`, greedily admits statements while `running_total + kgmcp_char_heuristic_v1(text) <= budget_requested`; `budget_returned` is the literal running total of real per-statement measurements, never `len(candidates) * constant` (the anti-pattern at `tools/context_packet_assembler.py:287`).
9. §16 budget-failure fallback wired directly into `assemble_packet()`: when statements existed pre-truncation but none survive `assemble_within_budget()`, the packet returns `statements=[]`, `context=[]`, `evidence=<every real candidate's already-derived EvidenceEntry>`, `status="PARTIAL"` — no fabricated/placeholder content anywhere.
10. `assemble_packet()` orchestrates render → dedup → negative-claim trigger → conflicts → budget-truncate → failure-fallback in that fixed order; `PacketAssembly` carries the 5 required top-level response-schema fields plus `answer/statements/context/evidence/conflicts/budget_requested/budget_returned` (all named schema properties) plus one additional field, `negative_claim_support` (justified per plan Design Decision D7 — the response schema is not `additionalProperties: false`).

No deviations from plan.md. One necessary implementation detail not explicit in the plan's abbreviated step-1 signature listings: `render_candidates()` and `_evidence_id_for_context_search_result()` take `query_text`/`anchor_counts` parameters respectively — both are explicitly anticipated by the plan's own Step 2/Step 4 prose (the counter-dict-through-orchestration and graphify-evidence-id-needs-query-text requirements), so this is not recorded as a deviation in plan.md.

One test-implementation adjustment recorded here: `test_module_does_not_edit_knowledge_gateway_router` cannot use a `git diff HEAD` check as its primary signal, because `tools/knowledge_gateway_router.py` and its own test file are currently **untracked** in this working tree (that sibling ticket's own commit has not yet landed) — a git-diff check against HEAD would silently pass regardless of whether this ticket edited the file. Used plan.md's own documented alternative instead: running `tests/tools/test_knowledge_gateway_router.py`'s real suite as a subprocess and asserting it passes unmodified.

## Test Summary
New file `tests/tools/test_knowledge_gateway_packet_assembly.py` — 27 tests, all passing, implementing every test named in `test_plan.md` (structural linters, extractive-only guard, negative-knowledge honesty branches, budget/dedup/priority-tier tests, §16 failure-fallback tests, structural-conflict tests, ephemeral-classification/no-durable-write guard, evidence-identity-kind guard plus 3 additional derivation-path tests for DOCUMENT_SECTION-disambiguation/TICKET/FILE kinds, and the 4 out-of-scope architecture guards).

```
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_packet_assembly.py -v
# 27 passed

.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_router.py tests/tools/test_search_mcp.py -v
# test_knowledge_gateway_router.py: all pass
# test_search_mcp.py: 45 passed, 2 pre-existing failures unrelated to this ticket
#   (TestMcpJson::test_command_is_python3, TestMcpJson::test_args_point_to_search_mcp — both
#   fail because .mcp.json's knowledge-search entry now wraps python3 in a bash launcher script;
#   this ticket did not touch .mcp.json, search_mcp.py, or its test file — confirmed via `git
#   status`, neither file appears in this session's changes)

.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_contract_schemas.py -v
# 19 passed
```

**Test phase (orchestrator-run, post-Implement scoped regression):**
`.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_packet_assembly.py
tests/tools/test_knowledge_gateway_router.py tests/docs/test_redaction_retention_policy_doc.py
tests/docs/test_doc_integrity.py tests/tools/test_generate_registry.py
tests/tools/test_validate_frontmatter.py -v` → initial run: 200 passed, 1 skipped, 4 failed. 3
failures traced to the pre-existing, unrelated `docs/mechanics/content_usage_matrix.md`
missing-frontmatter gap (confirmed to predate this epic). 1 NEW genuine failure — this ticket's own
§8 doc edit changed "No callable ships in `tools/`..." (present tense) to "No callable shipped
in..." (past tense, now accurate since the callable is real), but
`tests/docs/test_redaction_retention_policy_doc.py::test_token_counting_method_returns_integer_compatible_with_budget_schema`
still hard-asserted the old present-tense string. Fixed directly: updated the test's assertion to
match the new, accurate wording (documented inline why the wording changed), re-ran
`tests/docs/test_redaction_retention_policy_doc.py` → 6/6 pass. This was a genuine in-scope
test/doc drift caused by this ticket's own edit, not a pre-existing issue — fixed rather than
deferred.

## Files Changed
- `tools/knowledge_gateway_packet_assembly.py` (new)
- `tests/tools/test_knowledge_gateway_packet_assembly.py` (new)
- `tickets/inprogress/TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY.md` (this file — Status, Acceptance
  Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary)
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` (§8 "no callable
  ships" claim corrected to past tense, citing the real `kgmcp_char_heuristic_v1` callable,
  Document-Update phase)
- `docs/plans/knowledge-gateway-mcp-proposal.md` (§20 Phase 1's "extractive/template packet
  assembly" bullet annotated Done, Document-Update phase)
- `tests/docs/test_redaction_retention_policy_doc.py` (assertion updated to match §8's new,
  accurate past-tense wording, Test phase)
- `docs/parity_ledger/infrastructure.yaml` (new `INFRA-336` entry, via `write_entry()`, Parity
  phase)

## Completion Summary
Implemented `tools/knowledge_gateway_packet_assembly.py`, a new flat module under `tools/` that
takes a `RoutingDecision` plus query text, independently calls the two real Knowledge Gateway
providers, and assembles a plain typed `PacketAssembly` record: extractive/template-only
`statements[]`/`context[]`/`evidence[]` built from the 8 closed evidence-identity kinds, an
honestly-scoped `NegativeClaimSupport` (real logic, structurally `UNVERIFIED` against today's two
real `NONE`-declaring providers), structural-only `conflicts[]` (real logic, empty against
today's real provider shapes), and §15 token-budgeted assembly using the newly-implemented real
`kgmcp_char_heuristic_v1` callable with dedup-before-truncation and the §16 budget-failure
fallback. `tools/knowledge_gateway_router.py` was only ever imported/called, never modified. All
27 new tests pass; the router's and contract-schema's regression suites pass unmodified.
Document-Update corrected `redaction_retention_policy.md` §8's stale "no callable ships" claim to
past tense and annotated `knowledge-gateway-mcp-proposal.md` §20's extractive-assembly bullet Done.
Test phase found and fixed one genuine in-scope test/doc drift caused by that same §8 edit (a
stale present-tense assertion in `test_redaction_retention_policy_doc.py`), re-verified 6/6 pass.
Parity added `INFRA-336`, re-verified 27/27 `test_path` pass, shape-matches the `INFRA-335`
precedent. Both phases are now complete.

---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY
artifact_type: test_plan
tags: [ai, mcp]
---

# Test Plan — TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY

## Regression Surface

This ticket adds one new `tools/`-tier module that imports (read-only) from
`tools/knowledge_gateway_router.py` and `tools/search_mcp.py`, and reads (read-only) the frozen
Phase 0 contract files under `docs/engine/contracts/knowledge_gateway_mcp/`. No `src/` file is
touched, so no simulation-domain regression suite applies.

**Unit — sibling modules this ticket has a hard, load-bearing dependency on (must still pass
unmodified; a failure here means this ticket's assumed input shapes have drifted):**
- `tests/tools/test_knowledge_gateway_router.py` (31 tests) — `RoutingDecision`'s 7-field shape,
  `route()`/`route_ambiguous()` signatures and return semantics, `capability_allows()`. This
  ticket's module must consume `RoutingDecision` exactly as this suite already characterizes it —
  it must not assume a field (e.g. raw provider results) that this suite proves does not exist.
- `tests/tools/test_search_mcp.py` (15 tests) — `_run_search()`'s return-dict shape (`doc_id, title,
  heading, source_path, section, score, semantic_score, keyword_score, excerpt`) and its
  `{"error": ...}` failure-dict path.
- `tests/tools/test_knowledge_gateway_contract_schemas.py` — the frozen `provider_capabilities_*.json`
  descriptor shape and `capability_allows()` semantics this ticket's negative-knowledge logic
  consumes read-only.

**Unit — frozen contract fixtures this ticket's output must stay structurally compatible with (no
test file exists for these paths themselves — they are read-only data assertions this ticket's own
new tests perform, not a pre-existing suite to re-run):**
- `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json`
- `docs/engine/contracts/knowledge_gateway_mcp/shared_enums.schema.json`
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_identity_kinds.schema.json`
- `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_context_search.json`,
  `provider_capabilities_graphify.json`

**Integration/architecture — none required beyond the module's own new tests**, since nothing in
`.claude/workflows/*.js`, `src/`, or the API layer is modified by this ticket.

## New Tests Required

All new tests live in a new file mirroring the router's own convention (flat file under
`tests/tools/`, name TBD by Plan — e.g. `tests/tools/test_knowledge_gateway_packet_assembly.py`),
following `tests/tools/test_knowledge_gateway_router.py`/`tests/tools/test_context_packet_assembler.py`'s
established conventions: no live ML dependency required for the packet-assembly logic itself
(Context-Search-shaped inputs are hand-built fixture dicts matching `_run_search()`'s real return
shape, not a live index call), `tmp_path`/`monkeypatch` isolation for any file-path or capability-
descriptor state, small hand-built fixtures only.

| Test name | Category | What it verifies | AC |
|---|---|---|---|
| `test_every_answer_sentence_traces_to_a_real_statement_evidence_id` | unit / structural linter | Given an assembled packet, a structural walk over `answer` (split into sentences) proves every sentence is a rendering of at least one `statements[]` entry, and every such entry's `evidence_ids` is non-empty and each ID resolves to a real entry in `evidence[]` — not manual inspection, an automated linter function the test calls | AC1 |
| `test_context_summary_sentences_also_trace_to_statements` | unit / structural linter | Same invariant applied to `context[].summary` fields, not only `answer` | AC1 |
| `test_statement_text_is_a_verbatim_rendering_of_provider_excerpt_not_new_prose` | unit | Given a fixture Context Search result with a distinctive excerpt string, the resulting `statements[].text` contains that excerpt (template/quote), and does not appear anywhere with wording the fixture excerpt does not contain (guards against accidental paraphrase/synthesis) | Scope bullet 1 |
| `test_negative_claim_rejected_when_provider_lacks_negative_knowledge_support` | unit | Fixture: real `provider_capabilities_context_search.json`/`provider_capabilities_graphify.json` (both `negative_knowledge_support: "NONE"`) feed a negative-knowledge query; result must be `UNVERIFIED`, never `VERIFIED`/`SUPPORTED` | AC2 (frozen fixture 1 of 2) |
| `test_negative_claim_accepted_only_with_monkeypatched_scoped_or_complete_support` | unit | A monkeypatched/temp-copy capability descriptor with `negative_knowledge_support: "SCOPED"` or `"COMPLETE"` is the only way a non-`UNVERIFIED` negative claim can be produced; test asserts this explicitly and documents (in the test docstring/comment) that no real provider today reaches this branch, per the investigation's finding 5 | AC2 (frozen fixture 2 of 2) |
| `test_negative_claim_downgrades_to_unverified_when_validated_scopes_incomplete` | unit | Even with a `SCOPED`/`COMPLETE`-declaring descriptor, an empty/incomplete `validated_scopes[]` still forces `UNVERIFIED` | AC2 |
| `test_negative_claim_carries_exclusions_or_blind_spots_and_checked_at` | unit | A produced `NegativeClaimSupport`-shaped record always has non-null `exclusions_or_blind_spots[]` and `checked_at`, per §13.1's shape | AC2 |
| `test_budget_returned_computed_by_real_kgmcp_char_heuristic_v1_not_estimate` | unit | `budget_returned` equals `kgmcp_char_heuristic_v1(actual_serialized_content)`, and a test that swaps in more/fewer statements (same count) but longer/shorter text changes `budget_returned` accordingly — proving it is not `len(items) * constant` (the named anti-pattern in `tools/context_packet_assembler.py`) | AC3 |
| `test_kgmcp_char_heuristic_v1_matches_frozen_formula` | unit | The real callable returns `ceil(len(text.encode("utf-8")) / 4)` for known byte-length fixtures (ASCII and multi-byte UTF-8 cases) — direct parity check against `redaction_retention_policy.md` §8's formula | AC3 |
| `test_budget_returned_never_exceeds_budget_requested` | unit | For a `budget_requested` smaller than the full candidate content, assembly trims and `budget_returned <= budget_requested` always holds | AC3 |
| `test_duplicate_fact_across_two_providers_yields_one_statement_two_evidence_ids` | unit | Two fixture results (one from `context_search`, one from `graphify`) supporting the same fact produce exactly one `statements[]` entry with `len(evidence_ids) == 2`, not two separate statements | AC3 |
| `test_deduplication_occurs_before_truncation_not_after` | unit | A fixture with duplicate-then-truncatable content proves dedup collapses first (so the truncation step sees the deduplicated set) — assert truncation would have dropped the duplicate under budget pressure if dedup ran second, then show it doesn't | AC3 |
| `test_priority_order_invariants_before_facts_before_tests_before_history` | unit | A fixture with a candidate in each of §15's five priority tiers, under a tight budget, proves higher-tier content survives truncation before lower-tier content | Scope bullet 5 (§15) |
| `test_budget_assembly_failure_returns_smaller_real_list_not_fabricated_content` | unit | A budget too small to fit any full statement returns a packet whose `evidence`/`context` (or an explicit smaller list) contains only real, already-retrieved provider references — no synthesized placeholder text anywhere in the result | AC4 |
| `test_budget_assembly_failure_packet_has_no_new_content_beyond_real_provider_output` | unit | Recursive walk of the failure-path packet finds every string value traceable back to a real fixture provider result (no string invented by the assembler itself, other than fixed template scaffolding like labels) | AC4 |
| `test_conflict_only_surfaces_real_supersession_metadata` | unit | Given a fixture pair of provider results carrying explicit supersession/incompatible-document metadata, `conflicts[]` is populated with that pair; given a fixture pair with no such structural signal (just two plausibly-related excerpts), `conflicts[]` stays empty — proves no semantic-judgment path exists | AC5 |
| `test_conflicts_never_populated_from_bare_topical_similarity` | unit | Two fixture results about the same subject but with zero structural supersession/incompatibility signal never produce a `conflicts[]` entry, even though a semantic reader would flag them as related | AC5 |
| `test_statement_classification_is_ephemeral_not_persisted` | unit / architecture guard | Assembling a packet does not write to any file, registry, or `docs/parity_ledger/` path — confirmed via a `tmp_path`-scoped repo-root override plus a post-call filesystem diff, or an explicit static scan proving no `open(..., "w")`/registry-write call exists in the new module | Scope bullet 2 (§13's "no durable claim entity") |
| `test_evidence_id_uses_closed_evidence_identity_kind_form` | unit | Every `evidence_ids`/`evidence[].evidence_id` string matches one of the 8 closed stable-identity-form patterns from `evidence_identity_kinds.schema.json` (`doc:`, `file:`, `symbol:`, `ticket:`, `parity:`, `registry:`, `generation:`) — never a raw `doc_id` chunk string or an invented ID scheme | Related Code Areas / evidence-cache-identity reuse |
| `test_packet_never_carries_raw_provider_results_verbatim_beyond_rendered_statements` | unit / architecture guard | The assembled packet object has no field holding the full unprocessed raw provider result blob (e.g. the entire `_run_search()` list or raw `graphify` stdout) — only rendered `statements`/`context`/`evidence` derived from it, mirroring `context_packet_assembler.py`'s `Candidate`-has-no-raw-text-field precedent | Anti-Drift |
| `test_module_not_referenced_by_any_claude_workflows_file` | architecture guard | Static scan of `.claude/workflows/*.js` finds zero references to the new module's filename/import path | Anti-Drift (mirrors sibling ticket's AC5 guard) |
| `test_module_introduces_zero_mcp_server_code` | architecture guard | AST/grep scan of the new module confirms no `def knowledge_context(`/`def knowledge_status(`, no `.mcp.json` edits, no `FastMCP`/`server.tool()` usage | Out of Scope guard |
| `test_module_does_not_modify_or_import_retrieval_cache` | architecture guard | Static scan confirms the new module does not import `tools/retrieval_cache.py` and no cache read/write call appears anywhere in its diff | Out of Scope guard (no caching) |
| `test_module_does_not_edit_knowledge_gateway_router` | architecture guard | Confirms `tools/knowledge_gateway_router.py`'s file hash/content is unchanged by this ticket (or: confirms the router's own test suite, `tests/tools/test_knowledge_gateway_router.py`, still passes unmodified) | Out of Scope guard (router is DONE/frozen) |

## Scoped Pytest Commands

```
pytest tests/tools/test_knowledge_gateway_packet_assembly.py -v   # exact filename per Plan's decision
pytest tests/tools/test_knowledge_gateway_router.py tests/tools/test_search_mcp.py -v
pytest tests/tools/test_knowledge_gateway_contract_schemas.py -v
```

Never `pytest tests/`. All three commands are scoped strictly to `tools/`-tier
agent-orchestration/retrieval tooling — this ticket touches no `src/` or `tests/unit/` simulation
code, so no `tests/unit/` suite is in scope.

## Anti-Drift Test Guards

- **`test_every_answer_sentence_traces_to_a_real_statement_evidence_id` /
  `test_context_summary_sentences_also_trace_to_statements`** — the single highest-value guard in
  this plan, directly implementing the ticket's AC1 "structural linter" requirement; a passing test
  here is the only mechanical proof the extractive-only invariant holds, not just "the code looks
  right."
- **`test_statement_text_is_a_verbatim_rendering_of_provider_excerpt_not_new_prose`** — guards
  against the single most tempting drift for this ticket: quietly starting to paraphrase or
  lightly-edit retrieved text "to make it read better," which would violate §9.1's explicit
  extractive/template-only mandate.
- **`test_negative_claim_rejected_when_provider_lacks_negative_knowledge_support` /
  `test_negative_claim_downgrades_to_unverified_when_validated_scopes_incomplete`** — guard the
  exact failure mode §13.1 exists to prevent: treating an empty or under-scoped result as evidence
  of absence. Both must run against the *real* frozen descriptor files, not only mocks, so a future
  edit to either `provider_capabilities_*.json` file is caught if it silently flips
  `negative_knowledge_support`.
- **`test_budget_returned_computed_by_real_kgmcp_char_heuristic_v1_not_estimate`** — directly guards
  against reintroducing `tools/context_packet_assembler.py`'s already-landed
  `len(candidates) * constant` anti-pattern, named explicitly in this ticket's own Scope text.
- **`test_deduplication_occurs_before_truncation_not_after`** — guards the specific ordering §15
  requires; a naive "truncate then dedup" implementation would pass a weaker "final result has no
  duplicates" test but fail this one, which is the point.
- **`test_conflicts_never_populated_from_bare_topical_similarity`** — guards against the tempting
  shortcut of wiring in "these two excerpts are both about X, so flag a conflict," which would be
  exactly the semantic-judgment path §14 defers to Phase 6.
- **`test_statement_classification_is_ephemeral_not_persisted`** — guards §13's "no durable claim
  entity, no promotion" constraint; catches any future edit that starts writing classified
  statements to a registry, cache, or `docs/` path.
- **`test_evidence_id_uses_closed_evidence_identity_kind_form`** — guards against inventing a ninth,
  ad-hoc evidence-ID scheme instead of reusing the 8 closed kinds this ticket's Related Tickets
  section explicitly says to reuse.
- **`test_packet_never_carries_raw_provider_results_verbatim_beyond_rendered_statements`** — guards
  against a shortcut implementation that just stuffs the entire raw `_run_search()` list or graphify
  stdout into an extra field "for completeness," which would silently balloon packet size and defeat
  the whole point of bounded, deduplicated assembly.
- **`test_module_does_not_edit_knowledge_gateway_router` / `test_module_not_referenced_by_any_claude_workflows_file`
  / `test_module_introduces_zero_mcp_server_code` / `test_module_does_not_modify_or_import_retrieval_cache`**
  — the four Out-of-Scope boundary guards, mirroring the router ticket's own anti-drift test suite
  pattern; together they prove this ticket stayed inside "assembly only," touching neither its
  upstream dependency (router), its downstream consumer (MCP tool surface), nor a future phase
  (caching).
- Regression commands above (`test_knowledge_gateway_router.py`, `test_search_mcp.py`,
  `test_knowledge_gateway_contract_schemas.py` full suites) guard against this ticket accidentally
  modifying any of its three consumed modules' behavior instead of purely reading their output
  shapes, which Out of Scope implicitly requires (mirroring the sibling context-packet-assembler
  ticket's own regression-surface reasoning).

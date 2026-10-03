---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT
phase: done
date: 2026-08-16
tags: [ai, mcp]
---

# TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT

## Title
Implement real multi-provider packet deduplication and real caller-budget enforcement using
measured output size

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Proposal §20 Phase 3 requires "Assemble deduplicated multi-provider packets" and "Enforce caller
budgets using measured output size" as two of its four bullets. Today,
`tools/knowledge_gateway_packet_assembly.py`'s `assemble_packet()` performs Phase 1's extractive
rendering but does not deduplicate context items collected from multiple providers (Context Search
and Graphify may both return overlapping evidence for the same query), and does not enforce a
caller-supplied `budget_tokens` against the real measured output size of the assembled packet. This
ticket implements both as real, tested logic in the packet-assembly layer, ahead of Level 2 cache
wiring (`TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`) so there is a real deduplicated,
budget-respecting packet to cache in the first place.

## Scope
- Implement real deduplication of context items collected across multiple providers within a single
  `assemble_packet()` call — items that are genuinely the same evidence (same source path/symbol/
  hash, per whatever identity the existing evidence-kind normalization already establishes) collapse
  to one entry in the assembled packet, never duplicated verbatim from each provider that happened
  to surface it.
- Implement real caller-budget enforcement: when a `knowledge_context` request specifies
  `budget_tokens`, the assembled packet's real measured output size (via the existing
  `kgmcp_char_heuristic_v1_token_count()` measurement, reused not reimplemented) is checked against
  that budget, and the packet is genuinely constrained to fit within a documented tolerance — not
  merely reported as over budget after the fact.
- **Investigate-phase question, not decided here:** whether "respects budget within documented
  tolerance" requires dropping lowest-priority context items with a visible, structured marker
  (e.g. a `budget_truncated: true` / `omitted_items_count` field) rather than silently truncating
  content in a way that hides missing information. This must not collapse into ordinary text
  truncation that leaves the caller unable to tell content is missing — consider whether §5's
  already-established "reject, not truncate; never silently incomplete" size-cap philosophy from
  Phase 2's redaction work (`tools/knowledge_gateway_redaction.py`'s size-cap gate) is the right
  model to extend here, or whether budget enforcement is a genuinely different concern (partial
  delivery is acceptable for budgets in a way it isn't for a hard payload-size reject). Resolve this
  explicitly in this ticket's own Investigate/Plan phases and document the decision; do not assume
  either answer in Scope.
- Real tests: two providers returning overlapping evidence produce one deduplicated context item in
  the assembled packet, not two; a request with a `budget_tokens` value smaller than the real
  unconstrained packet size produces a packet whose real measured size is within the documented
  tolerance of that budget; whatever pruning/marking behavior is chosen is verified to be visible
  (not silent) via a real assertion on the response shape.

## Out of Scope
- Level 2 cache schema, storage, or read/write wiring — that is
  `TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS` and
  `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`'s job; this ticket only changes how a
  packet is assembled, not how/whether it is cached.
- Packet dependency records or targeted invalidation — `TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-
  INVALIDATION`'s job.
- Any change to `tools/knowledge_gateway_router.py`'s routing decisions.
- Conflict-detection/conflict-surfacing logic beyond ensuring deduplication does not accidentally
  merge genuinely conflicting claims into one silently-resolved item — per proposal §14's existing
  structured conflict boundary and §21's "Conflicts are visible and never silently merged"
  criterion, deduplication must only ever collapse identical evidence, never conflicting claims
  presented as if agreeing. If existing `CONFLICTED` handling from §14 already governs this, reuse
  it; do not invent a parallel conflict-suppression path.
- Semantic/fuzzy deduplication (treating differently-worded but equivalent claims as duplicates) —
  Phase 5 territory; this ticket deduplicates only on exact/structural evidence identity.

## Acceptance Criteria
- [x] Two providers returning overlapping evidence for the same query produce a genuinely
      deduplicated assembled packet — verified by a real test asserting item count, not just visual
      inspection.
- [x] A `knowledge_context` request with `budget_tokens` smaller than the real unconstrained packet
      size produces a packet whose real `kgmcp_char_heuristic_v1_token_count()`-measured size is
      within the documented tolerance of that budget — verified by a real test using actual
      measurement, not an estimate.
- [x] Whatever budget-enforcement mechanism this ticket's own Investigate/Plan phases choose (visible
      pruning-with-marker vs. another approach), it is never silent — a caller can always tell from
      the response shape whether content was omitted to fit budget, verified by a real test.
- [x] Deduplication never collapses genuinely conflicting claims into a single silently-resolved
      item — a real test proves two providers returning conflicting (not merely overlapping) claims
      about the same evidence still surface as a structured conflict, not a silent merge.
- [x] `tools/knowledge_gateway_router.py` remains byte-unchanged.
- [x] A real, schema-valid `docs/parity_ledger/infrastructure.yaml` entry is added for this
      ticket's own behavior change, per this repo's own governance rule. (Done — Parity phase
      added `INFRA-347` via `tools/parity_ledger_writer.py::write_entry()`; see Files Changed.)

## Related Tickets
- TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE3-EPIC (parent)
- TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS (the schema this ticket's real deduplicated,
  budget-enforced packet output will eventually be written into by a later ticket)
- TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE (DONE; the real Phase 1 `assemble_packet()` /
  `kgmcp_char_heuristic_v1_token_count()` this ticket extends)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §10.2 (Level 2 row shape), §10.3 (Conceptual
  Cached Packet Schema), §14 (Conflict Handling), §15 (Token-Budgeted Assembly), §20 Phase 3, §21
  ("Returned content respects the requested budget within a documented tolerance," "Conflicts are
  visible and never silently merged")
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §5 (the existing
  size-cap "reject not truncate, never silently incomplete" philosophy to consider extending or
  distinguishing from)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/knowledge_gateway_packet_assembly.py` (`assemble_packet()`,
  `kgmcp_char_heuristic_v1_token_count()` — the module this ticket's dedup/budget logic lands in)
- `tools/knowledge_gateway_mcp.py` (`_run_knowledge_context()` — the caller supplying
  `budget_tokens`)

## Assumptions / Open Questions
- Whether budget-driven pruning uses a visible marker/omission-count field versus another
  documented tolerance mechanism is explicitly not decided here — see the Scope section's
  Investigate-phase question above.
- What counts as "the same evidence" for deduplication purposes (exact source path + symbol match,
  content-hash match, or something looser) is not decided here — Investigate should check what
  identity the existing evidence-kind normalization (`evidence_identity_kinds.schema.json`) already
  establishes and reuse it rather than inventing a new identity concept.
- Whether this ticket's dedup logic needs to be aware of Level 1's already-cached provider results
  (to avoid re-deduplicating work already done) is left to this ticket's own Investigate phase —
  Scope only requires correct deduplication of the current call's live provider outputs.

## Implementation Notes
Implemented exactly per the Architecture-Review-approved plan.md (Steps 1-8; Step 9
Document-Update is left to the separate Document-Update phase, per plan.md's own Dependency Map
framing). No reimplementation of `deduplicate_statements()`/`assemble_within_budget()`/
`build_conflicts()` — all three targeted gaps were closed as narrow, additive edits on top of the
existing, real Phase 1 code in `tools/knowledge_gateway_packet_assembly.py`.

- **Steps 1-2 (dedup identity, Gap 1):** Added module-level `_content_hash(text: str) -> str`
  helper (single `hashlib.sha256(text.strip().encode("utf-8")).hexdigest()` call site in the whole
  module — verified by direct grep). Added `Statement.evidence_hash: Optional[str] = None`.
  `render_candidates()`'s two former inline `hashlib.sha256(...)` literals (context_search and
  graphify branches) now both call `_content_hash(text)` and thread the result into the
  `Statement(...)` constructor. `_dedup_key()` now returns `statement.evidence_hash` when present,
  falling back to `_content_hash(statement.text)` only for directly-constructed test fixtures.
- **Steps 3-4 (dedup-vs-conflict guard, Gap 2/AC4 — the safety-critical piece):** Added
  `_conflict_signal_index_pairs()`, reusing the existing `_structural_supersession_signal()`
  primitive `build_conflicts()` already calls, computed over the same raw
  `context_search`+`graphify` ordering `render_candidates()` uses. `deduplicate_statements()` gained
  an optional `conflict_index_pairs` parameter: on a dedup-key collision between two statements
  whose original indices are a known conflict-flagged pair, the later statement is forced into its
  own distinct group (`f"{key}::conflict-{idx}"`) instead of merging. `assemble_packet()` now
  computes `conflict_index_pairs` immediately after `render_candidates()`, followed by the
  Architecture-Review-mandated fail-loud cardinality assertion (`len(statements) ==
  len(context_search results) + (1 if graphify else 0)`), before calling
  `deduplicate_statements(statements, conflict_index_pairs)`. `build_conflicts()` itself and its
  call site are byte-unchanged.
- **Steps 5-7 (budget-truncation marker, Gap 3/AC2/AC3):** Added `PacketAssembly.budget_truncated:
  bool` and `PacketAssembly.omitted_statement_count: int`, computed once in `assemble_packet()`
  immediately after `assemble_within_budget()` returns
  (`omitted_statement_count = len(statements) - len(included_statements)`, `budget_truncated =
  omitted_statement_count > 0`) — verified correct in both the ordinary-truncation branch and the
  §16 total-failure fallback branch by direct test. Threaded into `_run_knowledge_context()`'s main
  response dict and the router-failure `fallback_response` (both `False`/`0` there, since nothing
  was ever truncated by budget on that path); `error_response` deliberately excluded, matching the
  existing precedent for `budget_requested`/`budget_returned`/`provider_failures`. Added both fields
  to `knowledge_context_response.schema.json`'s `properties` block as additive, non-required
  properties (no `schema_version` bump — matches the `provider_failures` precedent).
- **Step 8 (tests):** Added all 13 new tests specified in test_plan.md (11 in
  `tests/tools/test_knowledge_gateway_packet_assembly.py`, 2 in
  `tests/tools/test_knowledge_gateway_mcp.py`), including both Architecture-Review-mandated guard
  tests. Directly re-verified (not just claimed) that both mandated guard tests genuinely catch what
  they exist to catch: temporarily removed the Step 4 cardinality assertion and confirmed
  `test_conflict_index_pairs_correspondence_invariant_raises_on_desync` fails
  ("DID NOT RAISE AssertionError"); temporarily reintroduced a second inline
  `hashlib.sha256(...)` literal in `_dedup_key()`'s fallback (bypassing `_content_hash()`) and
  confirmed `test_evidence_hash_and_dedup_key_share_single_content_hash_helper` fails on the
  resulting hash mismatch. Both were then restored byte-identical to the intended implementation
  (diffed against a pre-change backup to confirm exact restoration) before the final test run.

**One documented deviation** (see staging_artifacts plan.md's new "Deviations" section for full
detail): `tests/tools/test_knowledge_gateway_mcp.py::test_search_mcp_py_provably_untouched` (an
existing test from the DONE `TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE`) asserted
`tools/knowledge_gateway_packet_assembly.py` must show zero `git diff --stat HEAD` lines — an
invariant this ticket's own approved scope directly falsifies (its entire purpose is to edit that
module). `tools/knowledge_gateway_packet_assembly.py` was removed from that test's `banned_path`
tuple (with an explanatory docstring), while `tools/search_mcp.py`,
`tools/knowledge_gateway_router.py`, and `tools/retrieval_events.py` remain in the guard, fully
preserved — those three are still genuinely frozen per this ticket's own AC5/Out-of-Scope.

**Invariants directly verified (not just claimed):**
- `tools/knowledge_gateway_router.py`: `git diff --stat HEAD` shows zero lines — byte-unchanged.
- `tools/knowledge_gateway_cache.py`/`tools/retrieval_cache.py`: zero working-tree delta from this
  session (`git diff` vs. index is empty for both; the `retrieval_cache.py` diff visible in
  `git diff --stat HEAD` is entirely staged, pre-existing from the already-committed sibling
  `TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS` ticket, not touched this session).
- Exactly one `hashlib.sha256(...)` literal exists in
  `tools/knowledge_gateway_packet_assembly.py` (inside `_content_hash()` itself) — confirmed by
  direct grep.
- Two conflict-flagged items with identical text never collapse into one — confirmed by
  `test_dedup_does_not_merge_conflict_flagged_pair_even_with_identical_text`
  (`len(packet.statements) == 2`, `packet.status == "CONFLICTED"`).

## Test Summary
All scoped commands from test_plan.md run and passing:
```
python3 -m pytest tests/tools/test_knowledge_gateway_packet_assembly.py -v   # 38 passed (27 existing + 11 new)
python3 -m pytest tests/tools/test_knowledge_gateway_mcp.py -v               # 22 passed (20 existing + 2 new)
python3 -m pytest tests/tools/test_knowledge_gateway_router.py -q            # 31 passed (regression proxy for router byte-unchanged)
python3 -m pytest tests/docs/test_redaction_retention_policy_doc.py -q       # 7 passed
```
Combined: 98 passed, 0 failed. No existing test assertion was weakened; the one existing test body
edited (`test_search_mcp_py_provably_untouched`) had one now-stale banned-path entry removed, not
an assertion weakened for any path that remains genuinely frozen — see Deviations above. Both
Architecture-Review-mandated guard tests independently re-verified to genuinely raise/fail when
their target regression is reintroduced (see Implementation Notes).

## Files Changed
- `tools/knowledge_gateway_packet_assembly.py` — `_content_hash()` helper;
  `Statement.evidence_hash` field; `render_candidates()` threading; `_dedup_key()` content-hash
  switch; `_conflict_signal_index_pairs()`; `deduplicate_statements()`'s new
  `conflict_index_pairs` parameter; Step 4 fail-loud cardinality assertion in `assemble_packet()`;
  `PacketAssembly.budget_truncated`/`omitted_statement_count` fields and their computation.
- `tools/knowledge_gateway_mcp.py` — `budget_truncated`/`omitted_statement_count` threaded into
  the main `response` dict and the router-failure `fallback_response`.
- `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json` —
  additive, non-required `budget_truncated`/`omitted_statement_count` properties.
- `tests/tools/test_knowledge_gateway_packet_assembly.py` — 11 new tests; no existing test body
  changed.
- `tests/tools/test_knowledge_gateway_mcp.py` — 2 new tests; `test_search_mcp_py_provably_untouched`
  had one stale `banned_path` entry removed (documented deviation, see Implementation Notes).
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-336`'s `v2_evidence` text corrected: the stale
  "`deduplicate_statements() (Step 5, exact-text-match dedup merging evidence_ids)`" phrase now
  describes the real content-hash dedup identity (`_content_hash()`) and the conflict-signal-aware
  exclusion guard this ticket adds, with a note that the text was amended by this ticket and a
  pointer to the new `INFRA-347` entry. `status: verified` unchanged — textual accuracy correction
  only, not a status change.
- `docs/parity_ledger/infrastructure.yaml` — added new entry `INFRA-347` (status=verified,
  priority=P1, proof_type=regression) via `tools/parity_ledger_writer.py::write_entry()`, citing
  `_content_hash()`/`_dedup_key()`/`_conflict_signal_index_pairs()`/the fail-loud cardinality
  assertion/`PacketAssembly.budget_truncated`+`omitted_statement_count` with real line numbers in
  `tools/knowledge_gateway_packet_assembly.py`, plus the response-threading lines in
  `tools/knowledge_gateway_mcp.py`, and citing all 13 new tests. Its `support_boundary` states
  explicitly that this ticket hardens already-existing Phase 1 dedup/budget mechanisms rather than
  originating them. Also corrected `INFRA-343`'s `v2_evidence` line-number citations into
  `tools/knowledge_gateway_mcp.py` (`:220-237`→`:222-239`, `:315-323`→`:319-327`,
  `:346-410`→`:350-414`), which drifted because this ticket's two `budget_truncated`/
  `omitted_statement_count` insertions into `_run_knowledge_context()`'s response dicts shifted
  every line below them; `:128-135` (`_load_cache_module()`, unshifted) was left as-is.
  `tools/parity_index.py build` run twice (once per entry write) to keep the derived index fresh.
  `docs/plans/knowledge-gateway-mcp-proposal.md` was deliberately **not edited**: this ticket's real
  contributions (content-hash dedup identity, the dedup-vs-conflict collision fix, the
  `budget_truncated`/`omitted_statement_count` visibility marker) harden dedup and budget-enforcement
  mechanisms that already existed as of Phase 1's `TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY`
  (`deduplicate_statements()`/`assemble_within_budget()`/`kgmcp_char_heuristic_v1()` were all real,
  already-landed code before this ticket per `INFRA-336`'s own pre-correction text). Marking §20
  Phase 3's "Assemble deduplicated multi-provider packets" or "Enforce caller budgets using measured
  output size" bullets **Done** for this ticket would misattribute those bullets' core capability to
  this ticket rather than to Phase 1. This mirrors the precedent set by the immediately-preceding
  sibling ticket `TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS`, which also left this file
  untouched rather than invent a partial-progress annotation the doc's own strictly-binary
  (blank/`**Done**`) convention has no room for.

## Completion Summary
Implemented the 3 real, targeted fixes this ticket's twice-reviewed plan scoped: (1) a shared
`_content_hash()` helper backing both `render_candidates()`'s `evidence_hash` computation and
`_dedup_key()`'s content-hash dedup identity, replacing the old casefold-text key; (2) a
`_conflict_signal_index_pairs()` guard plus a fail-loud cardinality assertion so two
conflict-flagged items can never silently collapse into one deduplicated statement even when their
rendered text is byte-identical (AC4, the ticket's single most safety-critical requirement); and
(3) a `budget_truncated`/`omitted_statement_count` marker on `PacketAssembly`, threaded through to
the `knowledge_context` MCP response and its schema, so budget-driven truncation is always visible,
never silent. All 13 planned tests were added and pass, both Architecture-Review-mandated guard
tests were independently confirmed to genuinely catch their target regressions, and all critical
invariants (router/cache modules byte-unchanged, single hash-formula source of truth,
conflict-vs-dedup safety) were directly verified via git diff/grep and targeted regression checks.

Document-Update: corrected `INFRA-336`'s now-stale `v2_evidence` text in
`docs/parity_ledger/infrastructure.yaml` to describe the real content-hash dedup identity and
conflict-signal-aware exclusion guard, per plan.md's Step 9; `status: verified` unchanged. Left
`docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 3 unmarked — this ticket hardens
already-existing Phase 1 dedup/budget mechanisms rather than originating either bullet's core
capability, so marking either **Done** here would overclaim (see Files Changed for full rationale
and the sibling-ticket precedent this follows).

Architecture-Verify APPROVED (independently re-proving both safety-critical guard tests
non-vacuous via a live break/restore cycle of its own — see Implementation Notes). Test phase
independently re-ran 6 scoped test files (130/130 passed) and confirmed AC3's visibility guarantee
holds at the real response-shape level, not just the dataclass level.

Parity: added new entry `INFRA-347` to `docs/parity_ledger/infrastructure.yaml` via
`tools/parity_ledger_writer.py::write_entry()` (status=verified, priority=P1,
proof_type=regression), and corrected `INFRA-343`'s drifted `tools/knowledge_gateway_mcp.py`
line-number citations (shifted by this ticket's own response-dict insertions) in place — see
Files Changed for both. `tools/parity_index.py build` run as a separate visible call after each
write.

Verify's first pass found a real gap: `investigation.md`'s "Docs Requiring Update" section still
listed `docs/plans/knowledge-gateway-mcp-proposal.md` as required, even though Document-Update had
deliberately, and for good reason, left it untouched — the artifact of record was never revised to
reflect that resolution. Fixed by restructuring `investigation.md`: moved that bullet out of "Docs
Requiring Update" into a new "Docs Considered But Not Required" section recording the full
resolution (hardens, does not originate, the Phase 3 capability; flagged for the epic's own closure
to consider whether `TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY` should retroactively get credit).
Independently confirmed via direct script re-run that `check_docs_to_update_coverage()` now returns
PASS. Verify's second pass independently re-confirmed the restructuring is genuine and substantively
accurate (not a routed-around gate), re-ran all 13 DoD conditions, and confirmed READY_TO_CLOSE.
This ticket is now finalized and moved to `tickets/done/`.

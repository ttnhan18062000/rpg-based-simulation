---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY
artifact_type: plan
tags: [ai, mcp]
---

# Implementation Plan — TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY

## Summary

Add one new flat module, `tools/knowledge_gateway_packet_assembly.py`, that takes a
`RoutingDecision` (`tools/knowledge_gateway_router.py:315-323`) plus the original query text,
independently calls the two real providers (`tools/search_mcp.py::_run_search()` for
`context_search`, `tools/knowledge_gateway_router.py::match_symbol_name()` for `graphify`) using
`RoutingDecision.providers_selected` as routing metadata, and assembles a plain typed
`PacketAssembly` record: extractive/template-rendered `statements[]` (verbatim quotes of real
provider excerpts/stdout, never paraphrased), `context[]`/`evidence[]` built from the same
candidates using the 8 closed evidence-identity-kind forms, an honestly-scoped
`NegativeClaimSupport` record (structurally correct, `UNVERIFIED` against both real `NONE`-declaring
provider descriptors, upgradeable only via monkeypatched fixtures), structural-only `conflicts[]`
(always empty against today's real provider shapes, never fabricated), and §15 token-budgeted
assembly using a newly-implemented real `kgmcp_char_heuristic_v1(text) -> int` callable
(`ceil(len(text.encode("utf-8"))/4)`) with dedup-before-truncation and the §16
budget-assembly-failure fallback (smaller real evidence list, never fabricated content). The router
module is only ever imported/called, never modified. No MCP tool code, no caching, no
model-generated synthesis, and no durable claim/promotion records are introduced anywhere in this
module.

## Steps

### Step 1 — `kgmcp_char_heuristic_v1`: real callable

**Files:** `tools/knowledge_gateway_packet_assembly.py` (new)

**Change:** Add `def kgmcp_char_heuristic_v1(text: str) -> int: return math.ceil(len(text.encode("utf-8")) / 4)`.
This is the first real callable implementing the formula documented at
`docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md:148`
(`token_count ≈ ceil(len(text.encode("utf-8")) / 4)`), whose closing line
(`redaction_retention_policy.md:179-181`) explicitly states "No callable ships in `tools/` as part
of this ticket... A future ticket implements `kgmcp_char_heuristic_v1` as a callable function" —
this ticket is that future ticket. Scope it locally to this new module (module-level function, not
a new shared-utility file) per the ticket's own Assumptions/Open Questions note: no second real
caller exists today (Phase 2+ cache-sizing code is unbuilt), so per this repo's
no-premature-abstraction convention it stays local here and is extracted to a shared location only
if/when a second real caller lands. `budget_class`'s provisional small/medium/large buckets
(`redaction_retention_policy.md:174-177`) are explicitly not frozen as an enum anywhere and are not
required by any acceptance criterion — do not implement `budget_class` derivation in this ticket.

**Do NOT touch:** `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` itself
(Document-Update phase's job, see Docs and Parity Follow-Up below); do not add a `tiktoken` or any
other tokenizer dependency.

**Verify:** `test_kgmcp_char_heuristic_v1_matches_frozen_formula`

### Step 2 — Evidence-identity derivation helpers

**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:** Add two pure derivation functions building `evidence_id` strings using the 8 closed
`stable_identity_form` patterns defined in
`docs/engine/contracts/knowledge_gateway_mcp/evidence_identity_kinds.schema.json:21-101` (read in
full this session):

- `_evidence_id_for_context_search_result(result: dict) -> str` — input is one element of
  `_run_search()`'s real return list, confirmed shape `{doc_id, title, heading, source_path,
  section, score, semantic_score, keyword_score, excerpt}` (`tools/search_mcp.py:131-141`).
  `doc_id` is chunk-scoped and is NOT used as the identity component (confirmed:
  `tools/search_mcp.py:132` sets `doc_id: r.doc_id`, a hybrid-retrieval chunk ID, distinct from a
  `docs/REGISTRY.yaml` registry-id). Instead:
  - If `source_path` starts with `"docs/"` (the same repo-relative-path form
    `match_registered_doc_path()` already treats as a registry-id via `entry["path"]`,
    `tools/knowledge_gateway_router.py:121-126`): build **DOCUMENT_SECTION**
    (`evidence_identity_kinds.schema.json:32-40`), form `doc:<source_path>#<anchor>`, where
    `<anchor>` = slugify(`heading` if non-empty else `section`): lowercase, non-alphanumeric runs
    collapsed to a single `-`, leading/trailing `-` stripped. If two rendered statements within the
    same assembled packet derive an identical `(source_path, anchor)` pair from two distinct result
    dicts, disambiguate by appending `-2`, `-3`, ... in first-seen candidate order, per
    `evidence_identity_kinds.schema.json:38`'s own documented duplicate-anchor rule ("the second
    `## Overview` becomes `doc:<registry-id>#overview-2`"). Implement this disambiguation as a
    small counter dict passed through the Step 4 orchestration call, not module global state.
  - Elif `source_path` matches `tickets/(inprogress|done)/(TCK-\d{8}-[A-Z0-9-]+)\.md` (a **local**
    regex constant in this new module, re-derived rather than imported — mirrors
    `tools/context_packet_assembler.py:44-47`'s own documented precedent of not importing another
    module's private underscore-prefixed symbol, here `_TICKET_ID_RE`,
    `tools/knowledge_gateway_router.py:67`): build **TICKET**
    (`evidence_identity_kinds.schema.json:62-70`), form `ticket:<ticket-id>`.
  - Else: build **FILE** (`evidence_identity_kinds.schema.json:42-50`), form
    `file:<source_path>` — the correct closed-kind fallback for any non-doc, non-ticket corpus path
    (no section-anchor concept applies to FILE).
- `_evidence_id_for_graphify_result(query_text: str) -> str` — build **SYMBOL**
  (`evidence_identity_kinds.schema.json:52-60`), form `symbol:<query_text>`, using the literal
  queried string as the qualified-name component. This is the closest available proxy: raw
  `graphify query` stdout (`tools/knowledge_gateway_router.py:114-118`) has no structured field to
  parse a true fully-qualified symbol name from without semantic interpretation, which would
  violate §9.1's extractive-only mandate. `query_text` is also exactly the value `match_symbol_name`
  itself echoes back as its own `"symbol"` field (`tools/knowledge_gateway_router.py:114-118`), so
  this reuses the provider's own naming rather than inventing a new one. Document this as an
  accepted Phase 1 approximation in the module docstring — a future ticket that structures
  graphify's stdout could derive a truer per-symbol identity.

**Do NOT touch:** `docs/engine/contracts/knowledge_gateway_mcp/evidence_identity_kinds.schema.json`
(frozen, read-only); do not invent a 9th evidence-identity kind.

**Verify:** `test_evidence_id_uses_closed_evidence_identity_kind_form`

### Step 3 — Provider-calling layer

**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:** Add `call_providers_for_routing_decision(routing_decision: "RoutingDecision", query_text: str) -> dict`
returning `{"context_search": <raw _run_search() return | None>, "graphify": <raw match_symbol_name() return | None>, "failures": list[str]}`.

Sibling-load `tools/knowledge_gateway_router.py` and `tools/search_mcp.py` via
`importlib.util.spec_from_file_location`, mirroring the exact sibling-load shape
`tools/knowledge_gateway_router.py:258-273` already uses internally for the same two modules (this
ticket does not reuse that private helper function itself — it duplicates the *shape*, a new,
independent call site, per the investigation's resolved design question; see Design Decision 1).

Iterate `routing_decision.providers_selected` (confirmed: this list is reliably populated on **all
three** `route()` paths — `providers_selected=list(row.primary_providers)` on both the
identifier-match path, `tools/knowledge_gateway_router.py:409`, and the shape-classification path,
`:424`; and `providers_selected=list(_AMBIGUOUS_PROVIDERS)` on the ambiguous-fallback path, `:296` —
so this module only ever branches on `providers_selected`, never on `providers_consulted`, which
stays empty except on the ambiguous path, `:416`/`:430` vs `:303`). Confirmed by reading
`ROUTING_TABLE` in full (`tools/knowledge_gateway_router.py:151-185`) that `primary_providers`
values are drawn only from `{"context_search", "graphify"}` — `"registry"`/`"working_log"` appear
only as `optional_providers` and `"parity_ledger"` only as `not_yet_routed`, neither of which this
module calls (no call function exists for them; building one is new provider-integration work this
ticket's Scope does not ask for — flag as a future-ticket gap in the packet if a caller ever passes
a routing decision naming them, do not silently invent a call).

For `"context_search"`: call `_sm._run_search(query_text)`. Its real return shape is `list[dict]`
on success or `{"error": str, ...}` on failure (`tools/search_mcp.py:82-96`, confirmed by direct
read) — if a dict with `"error"` comes back, treat `context_search` as unavailable for this call
(append `f"context_search: {result['error']}"` to `failures`, contribute zero statements from it),
never render the error string as content. This implements §16's "One provider unavailable → Return
partial result with explicit provider failure" row.

For `"graphify"`: call `_kgr.match_symbol_name(query_text)`, wrapped in `try/except
subprocess.TimeoutExpired` (the function's own `timeout=120`,
`tools/knowledge_gateway_router.py:112`, can raise) — on timeout, append
`"graphify: subprocess timeout"` to `failures` and contribute zero statements. On a normal return
with `returncode != 0` or empty `stdout.strip()`, also contribute zero statements (an empty/failed
call is never itself content — see Step 6's negative-knowledge framing for why this matters).

**Do NOT touch:** `tools/knowledge_gateway_router.py::route_ambiguous()` — do not modify it to
return raw results. Accept its known duplicate-call cost: on the ambiguous path,
`route_ambiguous()` (`tools/knowledge_gateway_router.py:281-304`) already calls both providers once
internally and discards the results (`:289-292`); this module's own call is a second, independent
invocation of the same read-only operations (a sqlite/vector read, a `graphify query` subprocess
call). Neither is a durable-state writer, so there is no correctness race, only a latency/redundancy
cost accepted as a documented Phase 1 tradeoff — fixing it would require editing the frozen,
already-ledgered (`INFRA-335`) router, which is out of scope for every step in this plan.

**Verify:** covered indirectly by every downstream test that exercises real fixture provider
results; no standalone test is listed for this step alone in test_plan.md, but
`test_budget_assembly_failure_packet_has_no_new_content_beyond_real_provider_output` and the
architecture-guard tests (`test_module_does_not_edit_knowledge_gateway_router`) depend on this
step's call shape being correct and non-mutating.

### Step 4 — Extractive statement/context/evidence construction

**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:** Add dataclasses `Statement(statement_id: str, text: str, classification: str,
evidence_ids: list[str], verification: str | None = None)`, `ContextEntry(kind, summary, source_id,
path, evidence_hash, authority)`, `EvidenceEntry(evidence_id, source_id, path, evidence_hash)` —
field names match `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json`
exactly: `statements[]` requires `statement_id, text, classification, evidence_ids` with optional
`verification` (`:39-53`); `context[]` items have all-optional `kind, summary, source_id, path,
evidence_hash, authority` (`:60-68`); `evidence[]` items have all-optional `evidence_id, source_id,
path, evidence_hash` (`:74-80`) — confirmed by direct read this session.

Add `render_candidates(provider_results: dict) -> tuple[list[Statement], list[ContextEntry], list[EvidenceEntry]]`:

- For each `context_search` result dict: `text = result["excerpt"].strip()` — a direct quote of
  `tools/search_mcp.py:140`'s `r.text[:200].replace("\n", " ")`, never edited/paraphrased (this is
  the literal substrate §9.1 requires). `evidence_id` from Step 2. `evidence_hash =
  hashlib.sha256(text.encode("utf-8")).hexdigest()` — mirrors (does not import)
  `tools/context_packet_assembler.py:79-86`'s `_hash_content()` hashing convention. `classification
  = "FACT"` (see Design Decision 2). `verification = "SUPPORTED"` (has real evidence, but no
  independent second-source cross-check exists to justify `"VERIFIED"`). Build a matching
  `ContextEntry(kind="context_search", summary=text, source_id=evidence_id, path=source_path,
  evidence_hash=evidence_hash, authority=None)` and `EvidenceEntry(evidence_id, source_id=evidence_id,
  path=source_path, evidence_hash=evidence_hash)`. Leave `authority` unset (`None`) rather than
  fabricate a value — no Phase 1 signal derives it.
- For each non-empty, successful `graphify` result: `text = result["stdout"].strip()` — the full
  raw stdout, quoted verbatim, no line-splitting or parsing (Design Decision 4).
  `classification = "FACT"`. Same `evidence_hash`/`ContextEntry`/`EvidenceEntry` construction as
  above, `kind="graphify"`, `path=None` (graphify has no path-shaped output field).
- `statement_id` assigned as `f"stmt-{n:03d}"` over the final candidate ordering (context_search
  results in `_run_search()`'s own returned order, `tools/search_mcp.py:143` sorts by score
  descending; graphify statement, if any, appended last) — deterministic given fixed input order,
  satisfying "do not break determinism."

**Do NOT touch:** do not add a `text`/`excerpt`/`raw` field anywhere that would hold a provider's
full unprocessed result blob — only the per-candidate rendered `text` derived above is ever stored,
mirroring `tools/context_packet_assembler.py:52-70`'s `Candidate`-has-no-raw-text-field structural
guarantee (though this ticket, unlike that module, does render text into `Statement.text` itself —
the guard is against storing the *raw, unprocessed* provider payload alongside the rendered
statement, not against rendering at all).

**Verify:** `test_every_answer_sentence_traces_to_a_real_statement_evidence_id`,
`test_context_summary_sentences_also_trace_to_statements`,
`test_statement_text_is_a_verbatim_rendering_of_provider_excerpt_not_new_prose`,
`test_packet_never_carries_raw_provider_results_verbatim_beyond_rendered_statements`

### Step 5 — Deduplication before truncation

**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:** Add `deduplicate_statements(statements: list[Statement]) -> list[Statement]`: group by
exact-match on `text.strip().casefold()` with internal whitespace collapsed to single spaces (a
purely mechanical/string-based key, not a semantic-similarity judgment — §14's ban on
semantic-judgment applies to *conflict* detection, not this §15-required dedup step, which is a
distinct concern). For each group with >1 member, keep the first-encountered `Statement` (its
`statement_id`/`text` survive) and merge every other group member's `evidence_ids` into it (list,
order-preserved, no duplicate IDs). This logic is provider-agnostic — keyed only on rendered text,
never on `provider_id` — so it naturally handles both same-provider duplicate chunks (a real
occurrence with overlapping context_search results) and the cross-provider case
`test_duplicate_fact_across_two_providers_yields_one_statement_two_evidence_ids`'s fixture
constructs (two fixture results, one per provider, engineered to render identical text).

This function must run immediately after Step 4's render and strictly before Step 8's
priority-sort-and-truncate loop — call ordering inside the Step 10 orchestrator is
render → dedup → (negative-claim / conflicts) → sort+truncate, never sort+truncate → dedup.

**Do NOT touch:** do not key dedup on `evidence_id` (two different real excerpts could
coincidentally share a source path) — key on rendered `text` only, per above.

**Verify:** `test_duplicate_fact_across_two_providers_yields_one_statement_two_evidence_ids`,
`test_deduplication_occurs_before_truncation_not_after`

### Step 6 — `NegativeClaimSupport` (honestly-scoped)

**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:** Add dataclass `NegativeClaimSupport(statement: str, subject_ids: list[str],
validated_scopes: list[str], scope_evidence_dependencies: list[str],
providers_and_adapter_versions: list[str], exclusions_or_blind_spots: list[str], checked_at: str,
verification: str)` — field names taken verbatim from
`docs/plans/knowledge-gateway-mcp-proposal.md:817-825`'s `NegativeClaimSupport` shape listing
(`statement / subject/entity IDs[] / validated_scopes[] / scope_evidence_dependencies[] /
providers_and_adapter_versions[] / exclusions_or_blind_spots[] / checked_at / verification`,
confirmed by direct read this session), matching the ticket's own AC2 wording
(`validated_scopes[]`/`exclusions_or_blind_spots[]`/`UNVERIFIED`) exactly.

Add `build_negative_claim_support(statement: str, subject_ids: list[str], provider_ids: list[str],
validated_scopes: list[str] | None = None) -> NegativeClaimSupport`:

- Load both real frozen descriptors fresh from disk each call (mirrors
  `tools/knowledge_gateway_router.py:59-62`'s own no-module-cache convention, reimplemented locally
  rather than importing the router's private `load_capability_descriptor` — this module defines its
  own `_CONTRACTS_DIR`/`_CONTEXT_SEARCH_CAPS_PATH`/`_GRAPHIFY_CAPS_PATH` constants, identical values
  to `tools/knowledge_gateway_router.py:35-37`, to keep this module's dependency on the router
  limited to `RoutingDecision`/`match_symbol_name`, not its private constants).
- `negative_knowledge_support` enum is `{"NONE", "SCOPED", "COMPLETE"}`
  (`docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities.schema.json:51-54`, confirmed
  by direct read). Both real descriptors declare `"NONE"`
  (`provider_capabilities_context_search.json:11`, `provider_capabilities_graphify.json:11`,
  confirmed by direct read).
- Contributing providers = those in `provider_ids` whose descriptor's
  `negative_knowledge_support != "NONE"`. With today's real descriptors this set is always empty.
- If contributing set is empty → `verification = "UNVERIFIED"`, `validated_scopes = []`,
  `exclusions_or_blind_spots = [f"{pid}: negative_knowledge_support=NONE — cannot validate absence"
  for pid in provider_ids]`.
- If contributing set is non-empty (only reachable via a monkeypatched/temp-copy descriptor in
  tests) but the caller-supplied `validated_scopes` is falsy/empty →
  `verification = "UNVERIFIED"` regardless of descriptor level (AC2's second clause: "or when
  `validated_scopes[]` cannot be established as complete" — Phase 1 has no automated
  scope-completeness computation, so an empty/unsupplied `validated_scopes` always forces
  `UNVERIFIED`, never upgraded by descriptor level alone).
- If contributing set is non-empty AND `validated_scopes` is non-empty →
  `verification = "VERIFIED"` if any contributing descriptor declares `"COMPLETE"`, else
  `"SUPPORTED"` if any declares `"SCOPED"` (both are `shared_enums.schema.json:15-18`'s real
  `verification` enum values, confirmed by direct read).
- `exclusions_or_blind_spots` and `checked_at` (`datetime.now(timezone.utc).isoformat()`) are always
  populated/non-null on every branch — this is agent-tooling metadata, not authoritative simulation
  state, so a wall-clock timestamp does not implicate this repo's determinism law (which governs
  `src/` simulation ticks, not `tools/`-tier retrieval metadata).

Wire a single, structural (not semantic) auto-trigger into the Step 10 orchestrator: if
`render_candidates` (Step 4) produces **zero** statements across all consulted providers, attach
`build_negative_claim_support(statement=f"no content found for: {query_text}", subject_ids=[],
provider_ids=<providers actually consulted this call>)` to the packet's
`negative_claim_support` field (see Design Decision 7 for why this is an extra field beyond the
frozen response schema). This trigger is structural — "the real provider call(s) returned nothing"
— never a keyword-sniffed guess at whether the query text itself was phrased as a negative claim
(which would require semantic judgment §9.1 forbids).

**Do NOT touch:** never let a real (non-monkeypatched) provider call reach `"VERIFIED"` or
`"SUPPORTED"` — both real descriptors are `"NONE"` today, so any code path producing a non-
`"UNVERIFIED"` result from the two real `provider_capabilities_*.json` files is a bug.

**Verify:** `test_negative_claim_rejected_when_provider_lacks_negative_knowledge_support`,
`test_negative_claim_accepted_only_with_monkeypatched_scoped_or_complete_support`,
`test_negative_claim_downgrades_to_unverified_when_validated_scopes_incomplete`,
`test_negative_claim_carries_exclusions_or_blind_spots_and_checked_at`

### Step 7 — Structural-only conflict representation

**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:** Add dataclass `ConflictClaim(value, source_id, authority, valid_from, valid_to)` and
`Conflict(subject, claims: list[ConflictClaim], automatic_resolution, recommended_action)` — field
names match `knowledge_context_response.schema.json:82-107`'s required `conflicts[]` shape exactly
(confirmed by direct read: `subject, claims, automatic_resolution, recommended_action`, each
`claims[]` entry requiring `value, source_id, authority, valid_from, valid_to`).

Add `build_conflicts(context_search_results: list[dict], graphify_result: dict | None) ->
list[Conflict]`: real, generic logic that inspects each result dict for explicit structural
supersession/incompatibility signal keys (e.g. `"superseded_by"`, `"supersedes"`,
`"incompatible_with"`, using `dict.get()` so absence is safe) and only emits a `Conflict` when two
results carry mutually-referencing or explicitly-incompatible signal values. Confirmed by direct
read this session: **neither** `_run_search()`'s real return dict
(`tools/search_mcp.py:131-141`, exactly `doc_id, title, heading, source_path, section, score,
semantic_score, keyword_score, excerpt` — no supersession field) **nor** `match_symbol_name()`'s
real return dict (`tools/knowledge_gateway_router.py:114-118`, exactly `symbol, returncode, stdout`
— no supersession field) exposes any such key today. Consequence: `build_conflicts()` is real,
tested code, but against today's two real providers it always returns `[]` — this must be stated
honestly in the module docstring, mirroring the router's own frozen-provider-shape honesty note. Do
not add any topical-similarity/keyword-overlap heuristic to manufacture non-empty `conflicts[]` —
that is precisely the semantic-judgment path §14 defers to Phase 6.

**Do NOT touch:** no embedding/similarity comparison of any kind.

**Verify:** `test_conflict_only_surfaces_real_supersession_metadata`,
`test_conflicts_never_populated_from_bare_topical_similarity`

### Step 8 — Token-budgeted assembly: priority order, real measurement, truncation

**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:** Add a `priority_tier: int` field to `Statement` (extends Step 4's dataclass; range 1-5
matching §15's five listed tiers, `docs/plans/knowledge-gateway-mcp-proposal.md:894-898`, confirmed
by direct read: 1=hard invariants/decisions, 2=facts/symbols/parity, 3=tests/dependencies,
4=history, 5=optional background). Default assignment for real provider-derived statements (Step 4):
`context_search` and `graphify` statements both default to `priority_tier=2` ("directly relevant
facts, symbols" — matches `context_search`'s own primary routing-table use for
`definition_terminology_architecture`/`symbol_lookup_callers_references`); a `negative_claim_support`
auto-generated statement (if Step 6's trigger fires) defaults to `priority_tier=1` (closest analog
to "hard invariants and current human decisions"). No real Phase 1 provider signal exists to
populate tier 3/4/5 — the sort/truncate function itself is fully generic over `priority_tier`, so it
correctly handles tier-3/4/5 candidates that a test constructs directly with the dataclass
(satisfying `test_priority_order_invariants_before_facts_before_tests_before_history`'s fixture-
driven design), even though no real Phase 1 call path produces them today. State this honestly in
the module docstring alongside Step 7's conflicts honesty note.

Add `assemble_within_budget(statements: list[Statement], budget_requested: int) ->
tuple[list[Statement], int]`:
1. Sort by `(priority_tier ascending, original candidate order)` — stable sort, ties broken by
   input order (deterministic).
2. Greedily accumulate: for each statement in sorted order, compute
   `cost = kgmcp_char_heuristic_v1(statement.text)` (Step 1's real callable — never `len(candidates)
   * constant`, the named anti-pattern at `tools/context_packet_assembler.py:287`
   (`budget_returned = len(included_candidates) * DEFAULT_EXCERPT_BUDGET`), confirmed by direct read
   this session and explicitly forbidden by this ticket's Scope). Include the statement and add
   `cost` to a running total only if `running_total + cost <= budget_requested`; otherwise stop
   (this and all remaining lower-priority statements are dropped).
3. Return `(included_statements, running_total)` — `running_total` **is** `budget_returned`,
   computed as the literal sum of real `kgmcp_char_heuristic_v1()` calls over the exact text that
   was actually included, so `budget_returned <= budget_requested` holds by construction of the
   admission condition in step 2, not by a post-hoc clamp.

This function must be called only after Step 5's `deduplicate_statements()` has already run — the
sort/truncate loop must see the deduplicated set (§15's "Deduplication should occur before
truncation").

**Do NOT touch:** never compute `budget_returned` as an estimate/constant multiplied by a count of
anything.

**Verify:** `test_budget_returned_computed_by_real_kgmcp_char_heuristic_v1_not_estimate`,
`test_budget_returned_never_exceeds_budget_requested`,
`test_priority_order_invariants_before_facts_before_tests_before_history`

### Step 9 — §16 budget-assembly-failure fallback

**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:** In the Step 10 orchestrator, after Step 8's `assemble_within_budget()` returns, if
`included_statements` is empty (the budget was too small to admit even the single lowest-cost,
highest-priority statement — this is the failure case, distinct from ordinary partial truncation
which already leaves ≥1 statement included): build the packet with `statements=[]`, `context=[]`,
but `evidence=[]` populated from **every** real candidate's already-derived `EvidenceEntry` (Step 4)
regardless of whether its statement was admitted — these are metadata-only pointers
(`evidence_id`/`source_id`/`path`/`evidence_hash`, no `text` field exists on `evidence[]` items per
`knowledge_context_response.schema.json:74-80`, confirmed by direct read, so this cannot leak
rendered text) — and `status="PARTIAL"` (an existing `shared_enums.schema.json:7-10` value, no new
status invented). `provenance_providers`/`providers_consulted_this_call` still reflect the real
providers that were actually called (Step 3), so the caller knows what to consult directly. Nothing
synthesized/fabricated is ever added — every string in the fallback packet traces back to a real
candidate's already-derived metadata.

**Do NOT touch:** do not emit a placeholder/apology string (e.g. `"content omitted"`) as if it were
retrieved content — only real `evidence[]` metadata and existing enum values are used.

**Verify:** `test_budget_assembly_failure_returns_smaller_real_list_not_fabricated_content`,
`test_budget_assembly_failure_packet_has_no_new_content_beyond_real_provider_output`

### Step 10 — Top-level orchestrator and `PacketAssembly` record

**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:** Add `@dataclass(frozen=True) class PacketAssembly(status, freshness, verification,
provenance_providers, providers_consulted_this_call, answer, statements, context, evidence,
conflicts, budget_requested, budget_returned, negative_claim_support)` — the first 5 plus
`answer/statements/context/evidence/conflicts/budget_requested/budget_returned` map directly onto
`knowledge_context_response.schema.json`'s named properties (confirmed by direct read: `status,
freshness, verification, provenance_providers, providers_consulted_this_call` are the schema's 5
required top-level fields, `:7-13`; `answer, statements, context, evidence, conflicts,
budget_requested, budget_returned` are named optional properties, `:32-118`).
`negative_claim_support` is an **extra** field with no corresponding named property in the frozen
schema (see Design Decision 7) — acceptable because this ticket's own Scope states its output is "a
plain typed packet record — not yet an MCP JSON-RPC response envelope," only "structurally
compatible," and the schema's top-level object is deliberately not `additionalProperties: false`
(`knowledge_context_response.schema.json:4`, confirmed by direct read of the schema's own
description field explaining this design choice).

`assemble_packet(routing_decision, query_text, budget_requested) -> PacketAssembly` orchestrates in
this fixed order: Step 3 (call providers) → Step 4 (render statements/context/evidence) → Step 5
(dedup) → Step 6 (negative-claim auto-trigger, conditional on zero statements) → Step 7 (conflicts)
→ Step 8 (priority sort + real-measurement truncation) → Step 9 (failure fallback, conditional).
`answer` = the included statements' `text` values joined with a single space (a template join, not
new prose) so `test_every_answer_sentence_traces_to_a_real_statement_evidence_id`'s structural
linter can walk it. `provenance_providers` = the deduplicated set of `provider_id` values that
contributed ≥1 evidence_id to a statement that survived Step 8/9; `providers_consulted_this_call` =
every provider_id actually invoked in Step 3 regardless of survival — both are real, tracked values,
never fabricated. Top-level `verification = "SUPPORTED"` if `included_statements` non-empty, else
`"UNVERIFIED"`. Top-level `status = "PARTIAL"` if Step 9's fallback fired or `failures` (Step 3) is
non-empty, `"CONFLICTED"` if `conflicts` non-empty (never true against real providers per Step 7),
else `"OK"`. `freshness = "UNKNOWN"` (no corpus-generation/timestamp comparison logic exists in this
ticket's scope — honestly defaulting rather than fabricating a comparison this ticket does not
implement).

**Do NOT touch:** do not add `cache`/`mode`/`cache_key_version`/`error` fields — those are
MCP-envelope-only concerns this ticket's Out of Scope explicitly excludes.

**Verify:** all remaining test_plan.md cases exercise this orchestrator end-to-end:
`test_statement_classification_is_ephemeral_not_persisted`,
`test_module_not_referenced_by_any_claude_workflows_file`,
`test_module_introduces_zero_mcp_server_code`,
`test_module_does_not_modify_or_import_retrieval_cache`,
`test_module_does_not_edit_knowledge_gateway_router`

## Scope Guards

- No MCP server code anywhere in `tools/knowledge_gateway_packet_assembly.py`: no `def
  knowledge_context(`, no `def knowledge_status(`, no `.mcp.json` edits, no `FastMCP`/`server.tool()`
  usage. That is `TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE`'s job.
- No caching: no SQLite, no import of `tools/retrieval_cache.py`, no cache read/write call anywhere.
  §15's dedup-before-truncation (Step 5) is packet-internal, never cache-key dedup.
- No model-generated synthesis: every `Statement.text` is a verbatim quote/join of real provider
  output (Steps 4, 10's `answer` join) — never a paraphrase, summary, or generated sentence.
- No durable claim/fact/inference/decision records, no promotion path, no new registry, no write to
  any `docs/` path or `docs/parity_ledger/*.yaml` shard from inside this module. §13's
  `FACT`/`INFERENCE`/`DECISION` labels (Step 4) and §13.1's `NegativeClaimSupport` (Step 6) live only
  on the in-memory `PacketAssembly` return value for the caller's current call.
- No semantic/model-based conflict comparison: Step 7's `build_conflicts()` only ever inspects
  explicit structural signal keys already present on a provider's own result dict — no
  embedding/similarity/keyword-overlap heuristic.
- Do not modify `tools/knowledge_gateway_router.py` or its tests in any way — it is DONE, frozen,
  and already ledgered (`INFRA-335`). Every provider call this module makes is a new, independent
  call site (Step 3), never a change to `route()`/`route_ambiguous()`'s return shape.
- Place the new module directly under `tools/` (flat file, not a subpackage) — the router ticket's
  own anti-drift guard test (`test_no_live_gateway_tool_code_or_mcp_registration_introduced`,
  `tests/tools/test_knowledge_gateway_router.py:368-378` and its
  `test_knowledge_gateway_contract_schemas.py` twin, `:338-350`) globs `tools/*.py`
  non-recursively; a subpackage would silently escape that coverage.
- Do not touch `docs/REGISTRY.yaml`, `registries/layer_registry.jsonl`, or any
  `docs/parity_ledger/*.yaml` shard directly from code in this module — the one new `INFRA-*` entry
  this ticket needs is written by hand at this ticket's own later Parity phase (see Docs and Parity
  Follow-Up), never by runtime code.

## Dependency Map

Steps 1 (heuristic) and 2 (evidence-ID derivation) are independent of each other and of Step 3
(provider calling) — each can be implemented and unit-tested standalone. Step 4 depends on Steps 1
(hash convention parallel, not literal dependency), 2 (evidence IDs), and 3 (raw provider results as
input). Step 5 depends on Step 4's `Statement` list. Step 6 depends on Step 2's provider-capability
loading pattern conceptually but is otherwise standalone-callable; its auto-trigger wiring depends on
Step 4/5's statement count. Step 7 depends on Step 3's raw results (reads them directly, independent
of Step 4's rendering). Step 8 depends on Step 5 (must run after dedup) and Step 1 (real heuristic).
Step 9 depends on Step 8's output. Step 10 wires Steps 3-9 together in the fixed order documented in
Step 10's Change text — this ordering (render → dedup → negative-claim → conflicts →
sort+truncate → fallback) is itself load-bearing and must not be reordered by the implementer for
convenience.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — every rendered sentence traces to a real `statements[].evidence_ids` entry | Steps 4, 10 | `test_every_answer_sentence_traces_to_a_real_statement_evidence_id`, `test_context_summary_sentences_also_trace_to_statements` |
| AC2 — negative-knowledge claims rejected/downgraded to `UNVERIFIED` per real/fixture descriptors and `validated_scopes[]` completeness | Step 6 | `test_negative_claim_rejected_when_provider_lacks_negative_knowledge_support`, `test_negative_claim_accepted_only_with_monkeypatched_scoped_or_complete_support`, `test_negative_claim_downgrades_to_unverified_when_validated_scopes_incomplete`, `test_negative_claim_carries_exclusions_or_blind_spots_and_checked_at` |
| AC3 — `budget_returned` via real `kgmcp_char_heuristic_v1`, never exceeds `budget_requested`, dedup before truncation | Steps 1, 5, 8 | `test_budget_returned_computed_by_real_kgmcp_char_heuristic_v1_not_estimate`, `test_kgmcp_char_heuristic_v1_matches_frozen_formula`, `test_budget_returned_never_exceeds_budget_requested`, `test_duplicate_fact_across_two_providers_yields_one_statement_two_evidence_ids`, `test_deduplication_occurs_before_truncation_not_after` |
| AC4 — budget-failure fallback returns smaller real list, never fabricated content | Step 9 | `test_budget_assembly_failure_returns_smaller_real_list_not_fabricated_content`, `test_budget_assembly_failure_packet_has_no_new_content_beyond_real_provider_output` |
| AC5 — conflicts only surface real structural supersession metadata, never semantic judgment | Step 7 | `test_conflict_only_surfaces_real_supersession_metadata`, `test_conflicts_never_populated_from_bare_topical_similarity` |
| Scope bullet 5 (§15 priority order) | Step 8 | `test_priority_order_invariants_before_facts_before_tests_before_history` |
| Related Code Areas (evidence-identity-kind reuse) | Step 2 | `test_evidence_id_uses_closed_evidence_identity_kind_form` |
| Out-of-scope guards (no MCP code, no cache, router untouched, not workflow-referenced) | Scope Guards | `test_module_introduces_zero_mcp_server_code`, `test_module_does_not_modify_or_import_retrieval_cache`, `test_module_does_not_edit_knowledge_gateway_router`, `test_module_not_referenced_by_any_claude_workflows_file` |
| §13 ephemeral-only classification | Step 4, Scope Guards | `test_statement_classification_is_ephemeral_not_persisted` |
| Anti-drift (no raw payload leakage) | Step 4 | `test_packet_never_carries_raw_provider_results_verbatim_beyond_rendered_statements` |

## Design Decisions

**D1 — Provider-calling layer.** The packet-assembly module independently sibling-loads
`tools/search_mcp.py` and `tools/knowledge_gateway_router.py` (Step 3) and calls
`_sm._run_search()`/`_kgr.match_symbol_name()` directly, using `RoutingDecision.providers_selected`
as the routing metadata — never reusing the router's private `_run_context_search_provider`/
`_run_graphify_provider` wrapper functions (those exist only to serve `route_ambiguous()`'s
internal, discarded calls) and never modifying the router to add a results-returning `route()`
variant. This resolves the investigation's "Blocking-for-Plan" open question directly: option (a)
from the investigation (call one level lower, at `_run_search`/`match_symbol_name`) is chosen over
option (b) (wrap the router's private helpers), because reaching into
`_run_context_search_provider`/`_run_graphify_provider` — both private, underscore-prefixed,
router-internal helpers not part of the router's public contract — would create a tighter, more
fragile coupling than calling the two genuinely public, independently-tested functions
(`_run_search` has its own 15-test suite, `match_symbol_name` has dedicated router tests) directly.
The accepted cost is a real, documented double-call on the ambiguous-routing path (see Step 3's
Change text) — never a correctness issue since both calls are read-only, but a known latency cost
this ticket does not attempt to eliminate.

**D2 — Statement classification default.** Every statement rendered from real provider output in
Phase 1 is deterministically classified `"FACT"`. Neither `_run_search()`'s excerpt field nor
`match_symbol_name()`'s stdout carries any structural signal distinguishing an "inference" or a
"decision" from a plain retrieved fact — inventing a keyword-sniffing rule (e.g. flagging text
containing "should"/"decided") to assign `"INFERENCE"`/`"DECISION"` would itself be exactly the kind
of interpretive judgment §9.1's extractive-only mandate forbids. The enum values remain valid and
usable by a future ticket if a provider ever emits structural decision/inference metadata — this
mirrors the same honesty framing already applied to negative-knowledge support (D3 below) and
conflicts (Step 7).

**D3 — Negative-knowledge honesty framing.** `build_negative_claim_support()` (Step 6) is real,
fully tested logic — not a stub — but is structurally unreachable past `"UNVERIFIED"` against
today's two real provider descriptors, both of which declare `negative_knowledge_support: "NONE"`
(confirmed by direct read of both `provider_capabilities_*.json` files this session). Tests must
exercise the `"SCOPED"`/`"COMPLETE"` branches only via a monkeypatched or temp-copy descriptor, and
must say so explicitly in the test docstring, per test_plan.md's own
`test_negative_claim_accepted_only_with_monkeypatched_scoped_or_complete_support` design. This is a
faithful implementation of §13.1, not a shortcut — the logic is correct and ready for the day a
provider genuinely declares `SCOPED`/`COMPLETE` support.

**D4 — Graphify quoting.** A graphify-sourced statement's `text` is the full raw `stdout`
(`tools/knowledge_gateway_router.py:117`), stripped of leading/trailing whitespace, quoted verbatim
with zero parsing/line-splitting/structuring — adopting the investigation's own recommendation
directly. Graphify's stdout is unstructured CLI traversal text with no JSON/structured return path
available from `match_symbol_name()` (confirmed by direct read); any attempt to parse individual
lines into sub-facts would require interpretation this ticket's extractive-only scope does not
permit.

**D5 — Evidence-ID derivation for context_search results.** `source_path` (not the chunk-scoped
`doc_id`) is the registry-id component of a `DOCUMENT_SECTION`/`FILE` evidence identity, because
`match_registered_doc_path()` already treats exactly this repo-relative-path form as a registry-id
lookup key (`tools/knowledge_gateway_router.py:121-126`, confirmed by direct read). Paths under
`docs/` become `DOCUMENT_SECTION` (with heading/section-derived, ordinal-disambiguated anchor);
paths matching a `tickets/{inprogress,done}/TCK-*.md` shape become `TICKET`; everything else falls
back to the always-valid `FILE` kind. This is new derivation logic (confirmed: no existing code in
the repo performs this mapping today) written locally in this module, not imported from anywhere,
since nothing to import exists.

**D6 — §15 priority-tier assignment given no real tiering signal.** No real provider or routing
metadata distinguishes "hard invariant" from "fact" from "test dependency" from "history" from
"background" today. The sort/truncate mechanism (Step 8) is built fully generic over an explicit
`priority_tier: int` field so the required fixture-driven test
(`test_priority_order_invariants_before_facts_before_tests_before_history`) can exercise all 5 tiers
via directly-constructed `Statement` fixtures, while real Phase 1 provider-derived statements default
honestly to only the 2 tiers (`1` for a negative-claim signal, `2` for ordinary retrieved facts/
symbols) that current provider output actually justifies.

**D7 — `negative_claim_support` as an extra field beyond the frozen response schema.** Direct read
of `knowledge_context_response.schema.json` confirms it names no top-level property for §13.1's
`NegativeClaimSupport` shape — only the 5 required fields plus `mode/cache/answer/statements/
context/evidence/conflicts/provenance_providers/providers_consulted_this_call/budget_requested/
budget_returned/cache_key_version/error` are defined properties (`:14-127`). Since this ticket's own
Scope states its output is "a plain typed packet record — not yet an MCP JSON-RPC response
envelope... structurally compatible" rather than a literal schema instance, and the schema's
top-level object is deliberately not `additionalProperties: false` (unlike the request schema, per
the schema's own `description` field, `:4`), `PacketAssembly` carries `negative_claim_support` as a
genuine additional field. The exact eventual JSON-RPC-envelope placement (e.g. folded into a future
`context[]` entry with `kind="negative_claim_support"`, or a schema amendment adding a dedicated
property) is explicitly left to `TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE`, which owns the
envelope-mapping decision — this ticket only needs its own internal record type to hold the data
faithfully.

## Docs and Parity Follow-Up

**Docs to update (Document-Update phase, not this Plan/Implement pass):**

- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §8
  (`:179-181`): the "No callable ships in `tools/` as part of this ticket... A future ticket
  implements `kgmcp_char_heuristic_v1` as a callable function" line becomes stale once Step 1 lands.
  Update to point at `tools/knowledge_gateway_packet_assembly.py::kgmcp_char_heuristic_v1()`.
- `docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 1 (`:1132-1147`, confirmed by direct read
  this session): the "Use deterministic classification and extractive/template packet assembly
  only" bullet (`:1142`) is currently un-annotated, unlike the Query Router bullet immediately above
  it which already carries `**Done** (TCK-20260815-KGMCP-P1-QUERY-ROUTER)` and a one-paragraph
  summary (`:1134-1140`). Add the matching `**Done** (TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY)`
  annotation in the same style once this ticket lands.

**Parity ledger — correction to investigation.md's finding:** investigation.md's "Parity Ledger
Overlap" section states no `docs/parity_ledger/` entry is required, reasoning by analogy to sibling
KGMCP *contract-only* documents. Direct read of `docs/parity_ledger/infrastructure.yaml:8643-8672`
this session shows this generalization is incomplete: this ticket's own direct dependency and
nearest sibling, `TCK-20260815-KGMCP-P1-QUERY-ROUTER`, **did** add a new entry (`INFRA-335`)
specifically because — unlike the Phase 0 contract-only tickets — it landed real, testable Python
code, following the `INFRA-281` through `INFRA-334` "agent-tooling-infrastructure" precedent for
ledgering real code landings under `tools/`. This ticket also lands real code (the entire packet-
assembly module, `kgmcp_char_heuristic_v1` as a first real callable, the provider-calling layer) —
by the identical precedent, **this ticket DOES warrant a new `INFRA-*` entry**, written by hand at
this ticket's own later Parity phase (not now, and not auto-generated). Do not skip the Parity phase
based on investigation.md's incomplete "None" framing.

## Anti-Drift Notes

- The single most tempting drift for this ticket is quietly starting to "clean up" or lightly
  reword a quoted excerpt "to make it read better" inside Step 4's rendering — this is exactly the
  paraphrase §9.1 forbids. `Statement.text` must always contain the source excerpt/stdout as a
  substring with zero character-level edits beyond `.strip()`.
- Do not let Step 8's truncation loop run before Step 5's dedup — a naive "truncate then dedup"
  implementation produces a final result with no duplicates (deceptively passing a weaker check) but
  fails `test_deduplication_occurs_before_truncation_not_after`, which specifically catches this
  ordering mistake.
- Do not "fix" Step 6/Step 7's honest emptiness (negative claims always `UNVERIFIED`, conflicts
  always `[]`) against real providers by inventing a heuristic that makes the field non-empty for
  demo purposes — both are structurally correct precisely because they stay empty/`UNVERIFIED`
  against today's real provider shapes.
- Do not reach into `tools/knowledge_gateway_router.py`'s private, underscore-prefixed constants
  (`_CONTRACTS_DIR`, `_CONTEXT_SEARCH_CAPS_PATH`, `_TICKET_ID_RE`, etc.) — redefine the small number
  needed locally in the new module, per this repo's own established precedent
  (`tools/context_packet_assembler.py:44-47`) of not importing another module's private symbols.
- The router's own architecture-guard test glob (`tools/*.py`, non-recursive) is the mechanism that
  keeps this ticket's MCP/caching-code guards enforceable — placing the new module anywhere other
  than directly under `tools/` silently defeats that coverage.

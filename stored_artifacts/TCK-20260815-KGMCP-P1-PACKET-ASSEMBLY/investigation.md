---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY
artifact_type: investigation
tags: [ai, mcp]
---

# Investigation — TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY

## Current Behavior

### `tools/knowledge_gateway_router.py` (DONE, `TCK-20260815-KGMCP-P1-QUERY-ROUTER`)

Pure decision logic. `route(query_text, requested_guarantee=None) -> RoutingDecision`
(`tools/knowledge_gateway_router.py:392-433`) tries 6 stable-identifier matchers, then keyword-based
shape classification, then falls through to `route_ambiguous()`. `RoutingDecision`
(`:315-323`) is a frozen dataclass: `providers_selected: list[str]`, `matched_identifier:
Optional[IdentifierMatch]`, `routing_shape: Optional[str]`, `rationale: str`,
`capability_constraints: list[CapabilityConstraint] = []`, `not_yet_routed: Optional[str] = None`,
`providers_consulted: list[str] = []`.

**Critical structural finding: `RoutingDecision` never carries raw provider results.** On the
identifier-match and shape-classification paths (`route()` lines 396-431), `providers_selected` is
populated from the routing table but no provider is actually called — the decision only says which
provider(s) *should* be consulted. On the ambiguous-fallback path, `route_ambiguous()`
(`:281-304`) does call `_run_context_search_provider(query_text)` and `_run_graphify_provider(query_text)`,
but **discards their return values** (lines 289-292 call them for side effect only, not assigning
the result) and reports only `providers_consulted: list[str]` (provider IDs, not payloads).
Confirmed against `tests/tools/test_knowledge_gateway_router.py:304-338`: every test that exercises
`route_ambiguous` monkeypatches the two provider-call functions and asserts only on
`providers_consulted` membership/count — no test anywhere asserts on returned raw content, because
none exists to assert on.

**Consequence for this ticket:** the ticket's Request Summary says "given a routing decision and
raw provider results ... assemble". Those two inputs are not co-located anywhere today. This
ticket's module must independently invoke the provider(s) named in `RoutingDecision.providers_selected`
(or `providers_consulted` on the ambiguous path) itself, using the same two call shapes the router
already uses internally:
- Context Search: `tools/knowledge_gateway_router.py::_run_context_search_provider()` (`:258-273`)
  sibling-loads `tools/search_mcp.py` and calls `_sm._run_search(query_text)` — returns
  `{"provider_id": "context_search", "results": <list[dict] | dict>}`.
- Graphify: `_run_graphify_provider()` (`:276-278`) calls `match_symbol_name(query_text)` (`:98-118`)
  — returns `{"symbol": text, "returncode": int, "stdout": str}`, wrapped as
  `{"provider_id": "graphify", "results": {...}}`.

This is a genuine open design question for the Plan phase, not something this investigation
resolves: whether the packet assembler re-imports and calls these two `_run_*_provider` helpers
directly (reusing the router's exact call shape) or calls `tools/search_mcp.py::_run_search` /
`knowledge_gateway_router.py::match_symbol_name` one level lower. Either way, **no router code
change is needed or in scope** — the router ticket is DONE and this ticket must not modify it.

### `tools/search_mcp.py::_run_search()` (`:82-144`) — raw Context Search provider result shape

Returns `list[dict]` (or `{"error": ...}` on failure) where each dict has exactly:
`doc_id, title, heading, source_path, section, score, semantic_score, keyword_score, excerpt`.
`excerpt` is `r.text[:200].replace("\n", " ")` (`:140`) — **the raw retrieved text, truncated to 200
chars, not a summary or paraphrase.** This is the literal substrate for "extractive... assembly":
statement text must be built by rendering/quoting this real excerpt (or the full underlying chunk
text, if a caller wants more than 200 chars — `_run_search` does not expose a way to get more), never
by generating new prose. `doc_id` here is a **chunk-level ID** (e.g.
`"plans/knowledge-gateway-mcp-proposal#15-token-budgeted-assembly-018"`), not directly the
`docs/REGISTRY.yaml` registry-id (which is the plain repo-relative path, e.g.
`docs/plans/knowledge-gateway-mcp-proposal.md`). `source_path` is the closer analog to a
registry-id/`DOCUMENT` stable-identity form. Building a `DOCUMENT_SECTION`-kind `evidence_id`
(`doc:<registry-id>#<section-anchor>`, per `evidence_identity_kinds.schema.json`) needs
`source_path` + `heading`/`section`, not `doc_id` verbatim — flagged as an open question below.

### `tools/knowledge_gateway_router.py::match_symbol_name()` — raw Graphify provider result shape

`{"symbol": text, "returncode": int, "stdout": str}` (`:114-118`). `stdout` is raw `graphify query`
CLI text output — unstructured. Rendering a statement from this requires parsing/quoting lines of
that stdout; no structured JSON result is available from this call path (confirmed:
`graphify query "<term>"` prints plain traversal text, per the earlier `graphify query` call in this
investigation's own search-before-grep pass).

### `tools/context_packet_assembler.py` (existing, DONE, `TCK-20260729-CONTEXT-PACKET-ASSEMBLY`) — the nearest prior-art module

This is a **different contract** (`docs/engine/contracts/context_packet_contract.md`'s
`ContextPacket`/`included[]`/`excluded_summary[]`), not the Knowledge Gateway MCP's
`statements`/`context`/`evidence`/`conflicts` shape, and this ticket does not extend or import it.
But it is directly relevant prior art for two reasons:

1. **It is the closest existing "extractive assembly" precedent, and it deliberately never renders
   text.** `Candidate` (`:52-70`) has "no field capable of holding raw text" — every adapter
   computes a `hash` at construction and discards the source content (`:84-91`,
   `_hash_content()`). `build_included_entry()` (`:231-245`) only ever emits metadata
   (`source_id`/`kind`/`path`/`heading_or_symbol`/`hash`/`authority`/`freshness`/`score`/
   `inclusion_reason`/`excerpt_budget`) — no `text`/`excerpt`/`answer` field exists anywhere in its
   output. **Confirmed: no extractive/template text-rendering pattern exists anywhere in `tools/`
   today.** This ticket is the first module in this repo that must actually render sentence text
   from retrieved content into a response field (`statements[].text`, `answer`, `context[].summary`).
   There is nothing to reuse for the rendering step itself; only conventions (flat single-file module
   under `tools/`, dataclass-based intermediate shapes, `hashlib.sha256`-based hashing) carry over.

2. **It contains a documented anti-pattern this ticket's own scope explicitly forbids repeating.**
   `assemble_context_packet()` (`:266-291`) computes
   `budget_returned = len(included_candidates) * DEFAULT_EXCERPT_BUDGET` (`:287`) — a **constant
   multiplied by candidate count**, not a real measurement of assembled content. This ticket's Scope
   explicitly requires "real measurement of returned content via `kgmcp_char_heuristic_v1` — never
   an estimate multiplied by candidate count" (§15). `context_packet_assembler.py` is the concrete,
   already-landed example of exactly the anti-pattern §15 warns against. This is a load-bearing
   contrast to get right, not a coincidence to ignore: this ticket must not copy that module's
   `budget_returned` computation, even though it is otherwise a reasonable structural precedent.

### `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §8 — `kgmcp_char_heuristic_v1`

Frozen formula: `token_count ≈ ceil(len(text.encode("utf-8")) / 4)` (`:148`). Ratified 2026-08-15,
±20% documented tolerance against any downstream true token count (`:157-160`). **"No callable ships
in `tools/` as part of [the redaction-retention-policy] ticket... A future ticket implements
`kgmcp_char_heuristic_v1` as a callable function."** (`:179-181`) — this ticket is that future
ticket; it is the first to implement this as real code. Feeds the already-frozen integer fields
`budget_requested`/`budget_returned` (`knowledge_context_response.schema.json:117-118`) and
`budget_tokens` (`knowledge_context_request.schema.json:17-19`). `budget_class` (small ≤500 /
medium 501–2000 / large >2000, `:174-177`) is documented as provisional/illustrative-only and is not
frozen as an enum anywhere — not required by this ticket's acceptance criteria, no need to implement
it as part of this ticket unless Plan decides otherwise.

### `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json` — target output shape

`statements[]` requires `statement_id, text, classification, evidence_ids` (`classification` refs
`shared_enums.schema.json#/definitions/statement_classification` = `FACT|INFERENCE|DECISION`;
optional `verification`). `context[]` items: `kind, summary, source_id, path, evidence_hash,
authority` (none required — all optional per the schema, though the ticket's scope implies they
should be populated where derivable). `evidence[]` items: `evidence_id, source_id, path,
evidence_hash` (also all optional in the schema itself). `conflicts[]` items require `subject,
claims, automatic_resolution, recommended_action`, each `claims[]` entry requiring `value,
source_id, authority, valid_from, valid_to`. Top-level required: `status, freshness, verification,
provenance_providers, providers_consulted_this_call`. The ticket's own Scope note ("Output is a
plain typed packet record — not yet an MCP JSON-RPC response envelope") means this ticket's output
type only needs to be **structurally compatible** with these field shapes (buildable into this JSON
shape by a later ticket), not literally an instance of this schema with every required top-level
field populated (e.g. `cache`, `mode` are MCP-envelope-only concerns this ticket's Out of Scope
excludes).

### Provider capability descriptors — negative-knowledge-support finding (investigation item 5)

Both `provider_capabilities_context_search.json` and `provider_capabilities_graphify.json` declare
`"negative_knowledge_support": "NONE"` (confirmed by direct read, both files, single field).
**Concretely: with today's exactly-2 real providers, no real provider currently declares
`negative_knowledge_support != NONE`.** Per this ticket's own Scope, "only providers whose
capability descriptor declares `negative_knowledge_support != NONE` may contribute to a negative
claim." The structural consequence: the `NegativeClaimSupport`-shaped code path this ticket must
build (§13.1) is **currently unreachable by any real provider call** — it can only be exercised by
tests using a hand-built/monkeypatched fixture descriptor declaring `SCOPED` or `COMPLETE` support,
never against the two real, live descriptor files. This must be stated honestly in this ticket's
test plan and acceptance-criteria mapping, not glossed over: the negative-knowledge logic is
structurally present (correctly rejecting/downgrading to `UNVERIFIED` given the real `NONE`
descriptors) but has zero real trigger path in Phase 1. This mirrors the router ticket's own
Anti-Drift Note ("Both descriptors have `negative_knowledge_support: 'NONE'` — an empty result from
either provider must never be treated... as a verified-absence signal").

### `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` and `evidence_identity_kinds.schema.json` — evidence ID kinds to reuse

8 closed kinds, each with a fixed `stable_identity_form`: `DOCUMENT` (`doc:<registry-id>`),
`DOCUMENT_SECTION` (`doc:<registry-id>#<section-anchor>`), `FILE` (`file:<repo-relative-path>`),
`SYMBOL` (`symbol:<qualified-name>`), `TICKET` (`ticket:<ticket-id>`), `PARITY_ENTRY`
(`parity:<entry-id>`), `REGISTRY_ENTRY` (`registry:<registered-name>`), `PROVIDER_GENERATION`
(`generation:<provider-id>@<corpus-generation>`, fallback-only, never a default dependency for the
other 7 kinds — `evidence_cache_identity_contract.md` §4's hard rule). This ticket's `evidence_ids`
must be built using these existing forms — e.g. a Context Search result maps naturally to
`DOCUMENT`/`DOCUMENT_SECTION` (using `source_path` as the registry-id component, not the raw
chunk-level `doc_id`), a Graphify symbol-lookup result maps to `SYMBOL`. **Open question for Plan:**
`_run_search()`'s raw `doc_id` field is chunk-scoped and does not, by itself, equal a
`docs/REGISTRY.yaml` registry-id or a stable section-anchor string — some derivation/normalization
step is needed to go from `{source_path, heading, section}` to a well-formed
`doc:<registry-id>#<section-anchor>` identity, and this investigation did not find that derivation
already implemented anywhere. This is new logic this ticket likely must write, not an existing
callable to import.

## Mechanics / Engine Constraints

This is agent-orchestration/retrieval tooling under `tools/`, not simulation logic — the Mechanics
Bible (`docs/mechanics/`) and Engine Contracts (`docs/engine/kernel.md`,
`authoritative_pipeline.md`, etc.) do not apply. The governing "laws" here are the Knowledge Gateway
MCP's own Phase 0 contracts, all under `docs/engine/contracts/knowledge_gateway_mcp/` and
`docs/plans/knowledge-gateway-mcp-proposal.md`:

- §9.1: "extractive/template-based assembly... model-generated synthesis... deferred" — statement
  text must be a rendering (quote/template substitution) of real retrieved content, never a
  generated/paraphrased sentence.
- §13: `FACT`/`INFERENCE`/`DECISION` are "ephemeral labels on returned statements... do not create
  durable claim entities" — this ticket must not add any durable storage, registry entry, or
  promotion path for these classifications (Phase 6 concern, explicitly out of scope).
- §13.1: `NegativeClaimSupport` requires `validated_scopes[]`/`exclusions_or_blind_spots[]`,
  defaulting to `UNVERIFIED` when scope completeness can't be established — "An empty provider
  result is not evidence of absence."
- §14: pre-Phase-6 conflict detection is "intentionally limited to contradictions already
  represented structurally by providers, explicit supersession metadata, and incompatible current
  document records" — no semantic/model-based comparison.
- §15: priority order (invariants/decisions → facts/symbols/parity → tests/dependencies → history →
  optional background); dedup before truncation; real measurement via `kgmcp_char_heuristic_v1`.
- §16 (Failure and Fallback Semantics table): "Token-budget assembly failure → Return a smaller
  evidence list or provider references, never fabricated content."
- `evidence_cache_identity_contract.md` §3 (Non-collapse rule): lookup identity and validity
  identity must never share field names / be conflated. This ticket does not implement caching, so
  it should not introduce either identity concept prematurely — it only needs `evidence_ids`
  (identity strings), not a lookup-vs-validity split, which remains Phase 2+ work.

## Docs Requiring Update

- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`: §8's closing line
  ("No callable ships in `tools/` as part of this ticket... A future ticket implements
  `kgmcp_char_heuristic_v1` as a callable function") becomes stale once this ticket lands a real
  callable — must be updated to point at the new file:line implementing it.
- `docs/plans/knowledge-gateway-mcp-proposal.md`: §20 Phase 1's bullet list currently has "Use
  deterministic classification and extractive/template packet assembly only" as an un-annotated,
  not-yet-done bullet (unlike the Query-Router bullet immediately above it, which is annotated
  **Done**). This ticket's completion should add the same `**Done** (TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY)`
  annotation with a one-paragraph summary, following the exact pattern already used for the Query
  Router and all Phase 0 bullets.

No `docs/parity_ledger/` entry is required — this subsystem is agent-orchestration/retrieval
tooling, the same category every sibling KGMCP Phase-0/Phase-1 contract document already classifies
as not requiring one (`redaction_retention_policy.md`'s closing note, `evidence_cache_identity_contract.md`
§6, `knowledge_gateway_mcp_contract.md` §5, `context_packet_contract.md` §4).

## Parity Ledger Overlap

None. Consistent with every sibling Knowledge Gateway MCP Phase 0/Phase 1 ticket to date (see Docs
Requiring Update above) — this is agent-orchestration/retrieval tooling under `tools/`, not
simulation-domain logic, and no `docs/parity_ledger/*.yaml` entry exists or is warranted for it. No
P0 parity entries are touched or need a passing `test_path` as a result of this ticket.

## Prior Work

- `TCK-20260815-KGMCP-P1-QUERY-ROUTER` (DONE) — `tools/knowledge_gateway_router.py` and its
  `stored_artifacts/TCK-20260815-KGMCP-P1-QUERY-ROUTER/{investigation,plan,test_plan}.md`. Direct
  dependency; consumed in full above. Its plan.md explicitly names this ticket as one of two known
  future importers of the router module and defers "how raw provider results reach the packet
  assembler" without resolving it — confirmed this remains genuinely open (see Current Behavior).
- `TCK-20260729-CONTEXT-PACKET-ASSEMBLY` (DONE) — `tools/context_packet_assembler.py` and its
  stored artifacts. A different contract (`ContextPacket`, not `knowledge_context`'s
  `statements`/`evidence`), but the closest structural precedent for a `tools/`-tier assembly
  module: flat single file, dataclass-based `Candidate`/output shapes, `hashlib.sha256`-based
  content hashing, `tests/tools/test_context_packet_assembler.py`'s testing conventions (`tmp_path`/
  `monkeypatch` isolation, no live ML dependency, small hand-built fixtures, an architecture-guard
  test confirming the module is never referenced from `.claude/workflows/*.js`). Its
  `budget_returned = len(candidates) * DEFAULT_EXCERPT_BUDGET` computation is the concrete
  anti-pattern this ticket's §15 requirement explicitly forbids repeating (see Current Behavior).
- `TCK-20260814-KGMCP-CONTRACT-SCHEMAS`, `TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`,
  `TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY` (all DONE) — the frozen schemas/contracts this
  ticket's output must be structurally compatible with; all read in full above.
- `docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 1 confirms the epic's own sequencing:
  Query Router done; this ticket next; `knowledge_context`/`knowledge_status` MCP exposure and
  caching are separate, later, explicitly-out-of-scope tickets for this one.

## Risks and Open Questions

- **Blocking-for-Plan: how does the packet assembler obtain raw provider results?** `RoutingDecision`
  never carries them (see Current Behavior). Plan must decide whether this module (a) calls
  `tools/search_mcp.py::_run_search` and `tools/knowledge_gateway_router.py::match_symbol_name`
  directly using `providers_selected`/`providers_consulted`, or (b) some other shape. This is not an
  ambiguity investigation should resolve by guessing — it is a genuine architectural decision with
  more than one defensible answer (e.g. does it duplicate the router's `_run_*_provider` wrapper
  functions, or call one level lower?).
- **`doc_id` → `DOCUMENT`/`DOCUMENT_SECTION` evidence-identity derivation is unimplemented anywhere.**
  See Current Behavior — `_run_search()`'s chunk-scoped `doc_id` is not directly a registry-id or a
  normalized section-anchor. Plan must decide the exact derivation (likely: use `source_path` as the
  registry-id component, and `heading`/`section` — normalized how?  — as the anchor) since no
  existing code performs this mapping.
- **Negative-knowledge code path has no real trigger with today's 2 providers** (see Current
  Behavior, item 5) — test_plan.md must test it via a fixture/monkeypatched capability descriptor,
  not against the real `NONE`-declaring files, and this must be stated honestly rather than implied
  as end-to-end-exercised.
- **Graphify raw result is unstructured stdout text**, not structured JSON — rendering a `FACT`/
  `INFERENCE` statement from it extractively (not by paraphrasing) is more mechanically awkward than
  from Context Search's clean `excerpt` field. Plan should decide how much of `stdout` gets quoted
  verbatim vs. what minimal parsing (if any) is acceptable before it stops being "extractive" and
  starts being interpretation.
- **`kgmcp_char_heuristic_v1`'s home module is an explicit open question the ticket itself already
  raises** (Assumptions/Open Questions in the ticket body) — shared utility vs. scoped-locally-then-
  extracted-later. Investigation surfaces no second real caller today (Phase 2+ cache-sizing code
  does not exist yet), so the repo's no-premature-abstraction convention favors scoping it locally to
  this ticket's new module first; Plan should make this explicit rather than leave it implicit.
- **`context[]`/`evidence[]` schema fields are all optional** in
  `knowledge_context_response.schema.json` — this gives this ticket real latitude in exactly which
  sub-fields it populates, but Plan should still aim to populate every field derivable from the real
  provider result (e.g. `evidence_hash` from `_hash_content()`-style hashing of the excerpt) rather
  than leaving fields empty by default, to stay maximally useful to the later MCP-tool-surface
  ticket.

## Anti-Drift Hazards

- **Do not replicate `context_packet_assembler.py`'s `len(candidates) * CONSTANT` budget estimate.**
  This is the single most concrete, named anti-pattern in this investigation (see Current Behavior)
  and directly contradicts this ticket's own Scope line. A test should assert `budget_returned` is
  computed by actually calling the real `kgmcp_char_heuristic_v1` callable over the assembled
  content, not derived from a candidate count.
- **Do not modify `tools/knowledge_gateway_router.py` or its tests.** The router is DONE and frozen;
  this ticket only imports/calls it. Any "raw provider results" gap identified above must be solved
  in this ticket's own new module, never by reaching back into the router to add a
  results-returning variant of `route()`/`route_ambiguous()`.
- **Do not build MCP server code, `.mcp.json` registration, or `def knowledge_context(`/
  `def knowledge_status(` anywhere.** That is explicitly `TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE`'s
  job. The router ticket's own anti-drift guard test
  (`test_no_live_gateway_tool_code_or_mcp_registration_introduced`,
  `tests/tools/test_knowledge_gateway_contract_schemas.py`) globs `tools/*.py` non-recursively — a
  new packet-assembly module placed directly under `tools/` is automatically covered by that guard;
  placing it in a subpackage would silently weaken that coverage, mirroring the router's own
  Anti-Drift Note about the same risk.
- **Do not build any SQLite/cache code, and do not import `tools/retrieval_cache.py`.** Caching is
  explicitly out of scope (Phase 3). §15's dedup-before-truncation requirement is about
  packet-internal deduplication (one statement + multiple evidence refs), not cache-key dedup — do
  not conflate the two.
- **Do not upgrade negative-knowledge claims past what the real descriptors support.** Given both
  real providers declare `NONE`, any code path that would make a negative claim `VERIFIED` or
  `SUPPORTED` off a real (not test-fixture) provider call today is a bug, not a feature — the correct
  real-world behavior for Phase 1 is always `UNVERIFIED` with recorded `exclusions_or_blind_spots[]`.
- **Do not add semantic/model-based conflict comparison.** §14 explicitly defers this to Phase 6;
  the only conflicts this ticket may surface are ones already structurally present in a provider's
  own result (explicit supersession metadata, incompatible current document records) — there is no
  such structural signal in either `_run_search()`'s or `match_symbol_name()`'s current return shape,
  so a fully honest Phase 1 implementation may legitimately never populate `conflicts[]` from a real
  call; do not invent a heuristic conflict detector to make the field non-empty.
- **Do not create durable claim/fact/inference/decision records or any promotion path.** §13
  explicitly scopes `FACT`/`INFERENCE`/`DECISION` as ephemeral, in-response-only labels — no new
  registry, no new `docs/` write, no persistence of a classified statement beyond the returned packet
  object's lifetime.

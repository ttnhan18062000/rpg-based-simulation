---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P4-PARITY-ADAPTER
artifact_type: investigation
tags: [ai, mcp]
---

# Investigation — TCK-20260816-KGMCP-P4-PARITY-ADAPTER

## Current Behavior

**`tools/knowledge_gateway_router.py`** (pure decision logic, no MCP/cache/packet code):
- `match_parity_id()` (L77-83) shape-matches `PREFIX(-PREFIX)*-digits` text (e.g. `INFRA-349`)
  into `IdentifierMatch(category="parity_id", value=text)` — existence-agnostic by design ("Design
  Decision D1").
- `_match_identifier()` (L364-389) tries `ticket_id -> parity_id -> source_path ->
  registered_doc_path -> subsystem_id -> symbol_name` in order; a `parity_id` match maps
  (`route()` L392-417, dict at L398-405) to `shape_id = "requirement_completeness_verification"`.
- `ROUTING_TABLE["requirement_completeness_verification"]` (L162-166) is currently
  `RoutingTableRow(primary_providers=("context_search",), not_yet_routed="parity_ledger")`.
- Critically, **`route()` never calls any provider function for an identifier-matched or
  shape-classified `RoutingDecision`** — it only builds and returns the `RoutingDecision` record
  (L396-431). The only place `route()`/its helpers actually *call* a provider is
  `route_ambiguous()` (L281-304), which is reached **only** when no identifier matched and no
  shape classified (the `_AMBIGUOUS_PROVIDERS = ("context_search", "graphify")` fixed pair, L255).
  A `parity_id`-shaped query always short-circuits at the identifier-match branch and never reaches
  `route_ambiguous()`. So `_run_context_search_provider()`/`_run_graphify_provider()` (L258-278),
  the "existing adapter-call pattern" the ticket says to mirror, are **only ever invoked from
  `route_ambiguous()`** — they are not on the call path for any parity_id query today, nor would a
  same-shaped `_run_parity_provider()` be, if added only to this file and not wired anywhere else.

**Real dead-end today**: a `parity_id`-matched query currently returns a `RoutingDecision` with
`providers_selected=["context_search"]` and `not_yet_routed="parity_ledger"`. Nothing downstream
consumes `not_yet_routed` to attempt a fallback — `tools/knowledge_gateway_mcp.py::_run_knowledge_context()`
passes the `RoutingDecision` straight to `assemble_packet()` and never inspects `not_yet_routed` at
all (confirmed by reading `_run_knowledge_context()` in full, L149-371). So today a parity-ID query
is silently answered by Context Search's full-text retrieval over parity ledger YAML prose,
never by a real structured `parity_index.py` lookup.

**`tools/knowledge_gateway_packet_assembly.py`** (the module that actually invokes providers for
every real `_run_knowledge_context()` call, including identifier-matched ones):
- `call_providers_for_routing_decision()` (L159-200) is a **second, independent** provider-calling
  layer from the router's own `_run_context_search_provider`/`_run_graphify_provider` — it has its
  own hardcoded `if provider_id == "context_search": ... elif provider_id == "graphify": ...`
  chain, with an explicit trailing comment (L196-198): `"# else: no call function exists for
  'registry'/'working_log'/'parity_ledger' — building one is new provider-integration work outside
  this ticket's scope; silently skipped rather than inventing a call."` That comment was written
  for the DONE `TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY` — it describes *that* ticket's own scope
  boundary, not this one's, but the code behavior it describes is current and real.
- Consequence: **even if `ROUTING_TABLE`'s row is changed to select a `"parity_ledger"` primary
  provider, and `_run_parity_provider()` is added to `knowledge_gateway_router.py` mirroring the
  other two, a real end-to-end `_run_knowledge_context()` call for a parity_id query will still
  never reach `tools/parity_index.py`** — `call_providers_for_routing_decision()` will silently
  skip `"parity_ledger"` (falling into the unhandled `else` branch) and return
  `{"context_search": None, "graphify": None, "failures": []}`, producing an empty/negative-claim
  packet, not real parity data. See "Risks and Open Questions" below — this is the single most
  important finding of this investigation and is not resolved by the ticket's stated scope as
  written.

**`tools/parity_index.py`** (already-built, DONE, read-only interface — confirmed by direct read,
not assumed):
- `entry(entry_id, db_path=None)` (L550-596): `SELECT * FROM entries WHERE id = ?` against
  `parity-index/parity.db`; on no row, returns exactly `{"entry_id": entry_id, "found": False}`
  (L558) — **no staleness check is performed as part of this call**. On a hit, returns the full
  record plus `code_refs`/`test_refs`/`constraint_refs`/`ticket_refs`/`health_findings`.
- `impact(changed_path=None, test_path=None, symbol=None, db_path=None)` (L599-658): path-level
  lookup across `code_refs`/`constraint_refs`/`ticket_refs`/`test_refs`; `symbol` accepted but
  unused (L650-654, matches ticket's Out of Scope). Requires at least one of `changed_path`/
  `test_path` or returns `{"status": "no_filter_provided", "results": []}`.
- `health(subsystem=None, priority=None, db_path=None)` (L661-708): joins `entry_health`+`entries`.
- `check_staleness(db_path=None, ledger_dir=None)` (L406-447): recomputes `source_manifest_hash`
  from the **live** `docs/parity_ledger/*.yaml` shards (via `_load_shards()`+`_shard_manifest_hash()`
  — the exact functions a real `build` uses) and compares it against the DB's own stored hash,
  returning `NOT_BUILT`/`FRESH`/`STALE`. This is a real, cheap, callable freshness signal — but it
  is a **separate function the caller must invoke explicitly**; `entry()`/`impact()`/`health()`
  never call it internally.
- `IndexNotBuiltError` (L90-91): raised by `_connect_readonly()` (L94-99) whenever `db_path` does
  not exist — i.e. before `parity-index/parity.db` has ever been built via `build` (L530-547).
  `entry()`/`impact()`/`health()` all call `_connect_readonly()` first and so all three can raise
  this.

**Capability descriptor format template** (`docs/engine/contracts/knowledge_gateway_mcp_contract.md`
§2-§3, and the two real populated instances):
- `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_context_search.json` and
  `.../provider_capabilities_graphify.json` are the two real, frozen instances — both declare
  `negative_knowledge_support: "NONE"`, `cancellation: false`, `timeout: false`.
- `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities.schema.json` is the shape
  contract: 11 required fields + optional `generation_fingerprint`; `negative_knowledge_support`
  enum is `["NONE", "SCOPED", "COMPLETE"]` (not just `NONE`/non-`NONE` — `SCOPED` is a real,
  intended-to-be-reachable middle value, not a placeholder).
- `knowledge_gateway_mcp_contract.md` §3 is the **evidence-citation format template** the ticket
  asks for: one bullet per field, each grounded in a specific, cited, directly-observed piece of
  real code/CLI/schema behavior — e.g. `"adapter_version: null — _run_health() ... returns
  index_version, derived from the SQLite index file's mtime, not a code/adapter version ...
  null is the honest value"`. A Parity `### Parity Ledger` subsection must be added to this same
  §3 in exactly this style: every field justified by a specific `tools/parity_index.py` line/
  behavior, never copied from the other two descriptors (per ticket Scope's own instruction).
- §2 already states: `"Parity Ledger gains one before its Phase 4 adapter is enabled"` — this
  ticket is the one that fulfills that forward reference.

**Fail-open precedent to mirror** (`tools/knowledge_gateway_mcp.py::_run_knowledge_context()`,
L192-220): the router-failure branch is the closer analogue to `IndexNotBuiltError` than the
cache-layer's broad `except Exception: pass` blocks (L229-235, L252-257, L353-360, L364-368),
because it is a **named, specific exception type** caught around a **provider/data-source call**
(not a cache convenience layer) and converted into a typed `PARTIAL` fallback response with a
human-readable reason appended to `provider_failures`, not silently swallowed:
```python
try:
    routing_decision = _kgr.route(query)
except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
    reason = ("graphify: binary not found on PATH" if isinstance(exc, FileNotFoundError)
              else "graphify: subprocess timeout")
    fallback_response = {"status": "PARTIAL", ..., "provider_failures": [reason]}
    RESPONSE_VALIDATOR.validate(fallback_response)
    return fallback_response
```
`call_providers_for_routing_decision()` in `knowledge_gateway_packet_assembly.py` (L159-200) shows
the equivalent pattern one layer down — per-provider `try/except` inside the loop, appending a
string to `results["failures"]` and `continue`-ing rather than crashing the whole packet assembly
(see graphify's `subprocess.TimeoutExpired`/`FileNotFoundError` handling, L180-189).
`_run_parity_provider()` (wherever it ultimately lives) should catch
`tools.parity_index.IndexNotBuiltError` the same way: append a string reason (e.g.
`"parity_ledger: index not built — run tools/parity_index.py build"`) to the failures/
`provider_failures` list at whichever layer it is wired into, never raise past that layer.

## Mechanics / Engine Constraints

Not a simulation-mechanics ticket — no `docs/mechanics/` chapter applies. The governing contracts
are `docs/engine/contracts/knowledge_gateway_mcp_contract.md` (§2 `ProviderCapabilities` semantics
— "the router must never claim a capability the descriptor does not advertise") and
`docs/plans/knowledge-gateway-mcp-proposal.md` §7.1 ("Parity adapter, when Phase 4 begins: call the
existing parity-index Python/query interface" — in-process, never subprocess/recursive-MCP) and §3.3
("The Parity Ledger remains authoritative for implementation-completeness questions. The gateway may
cache and explain its results but must never replace or independently override ledger status" — the
adapter must be read-only passthrough, matching this ticket's own Out of Scope).

## Docs Requiring Update

- `docs/engine/contracts/knowledge_gateway_mcp_contract.md`: §2/§3 explicitly anticipate a third,
  Parity Ledger `### ` evidence-citation subsection ("Parity Ledger gains one before its Phase 4
  adapter is enabled") — add it in the same per-field-cited-evidence format as the Context
  Search/Graphify subsections, including the honest `negative_knowledge_support` resolution below.
- `docs/plans/knowledge-gateway-mcp-proposal.md`: §20's "Phase 4: Parity and Workflow Integration"
  bullet "Add Parity Ledger routing" should get a real results-narrative note once implemented,
  matching the precedent set for Phase 1/2/3 bullets by prior sibling tickets (INFRA-347/INFRA-350
  entries both describe appending "results-narrative paragraphs" after the relevant §20 bullet
  rather than leaving the plan a purely aspirational document).
`tmp/mcp-followup-instruction.md` is a scratch/working instruction document (lives under `tmp/`,
not `docs/`) — it is the source of design constraints for this ticket, not a living doc tracked for
parity; no update to it is warranted.

## Docs Considered But Not Required (Document-Update phase, 2026-08-16)

- `docs/parity_ledger/infrastructure.yaml`: originally flagged above (a new `INFRA-351` entry, per
  AC5) but **not touched by the Document-Update phase** — `docs/parity_ledger/*.yaml` is
  `parity-updater`'s exclusive territory, per its own scope boundary, and is handled in the
  dedicated, later Parity phase of the pipeline, not by doc-updater. AC5 remains unchecked on the
  ticket and the separate Parity phase is responsible for adding the entry and checking it before
  the ticket can move to `tickets/done/` — this was already explicit in the ticket's own
  Implementation Notes ("Not done in this Implement pass... left for the separate Parity and
  Document-Update phases") and plan.md Step 10; the Document-Update phase's own job (Step 11) is
  limited to `knowledge_gateway_mcp_contract.md` and the proposal doc, both of which were updated —
  see `staging_artifacts/TCK-20260816-KGMCP-P4-PARITY-ADAPTER/plan.md` Step 11 for the citation.
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md`: not originally
  flagged above, and verified (not assumed) during the Document-Update pass to need no change — it
  already anticipates the `parity:<entry-id>` deterministic identity form (§1) and its
  evidence-validity-identity field set (§2) is provider-agnostic prose with no per-provider
  enumeration to extend.
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`: not originally
  flagged above, but the Document-Update pass verified it and found a real, disclosed gap requiring
  a note (not a fix) — see that document's own §2 for the full disclosure: the newly-live
  `parity_ledger` provider is not yet reflected in `tools/knowledge_gateway_redaction.py::ALLOWED_SOURCE_TYPES`
  or the Level 1/Level 2 cache-write `source_type` derivation in `tools/knowledge_gateway_cache.py`,
  both of which stay out of this ticket's own Scope/Related Code Areas and are therefore left as a
  disclosed gap for a follow-up ticket, not fixed here.

## Parity Ledger Overlap

No existing parity ledger entry currently describes the router/packet-assembly/adapter code this
ticket touches at the "parity_id routing" granularity — the closest prior entries are INFRA-335
(router, DONE), INFRA-336 (packet assembly, DONE), INFRA-337 (MCP server, DONE), all `verified`,
none P0-flagged as blocking this work. No P0 entry is directly impacted (this subsystem is
agent-orchestration/retrieval tooling, not simulation code — matching the "no parity ledger entry"
precedent §5 of `knowledge_gateway_mcp_contract.md` documents for the *contract* doc itself, though
this *ticket*, unlike that doc, does add one per its own AC5).

## Prior Work

- `stored_artifacts/TCK-20260815-KGMCP-P1-QUERY-ROUTER/` — built `ROUTING_TABLE`, `match_parity_id()`,
  and the `not_yet_routed` placeholder mechanism this ticket closes.
- `stored_artifacts/TCK-20260814-KGMCP-CONTRACT-SCHEMAS/` — built the `ProviderCapabilities` schema
  and the two real descriptor instances/evidence-citation format this ticket must follow.
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_identity_kinds.schema.json` already defines
  a closed `PARITY_ENTRY` evidence kind (L72-79): `stable_identity_form: "parity:<entry-id>"`,
  `preferred_fingerprint: "entry-id plus canonical_fragment_hash"` (citing
  `tools/parity_index.py`'s own `_EXPECTED_COLUMNS['entries']` `canonical_fragment_hash` column) —
  this is the real, already-frozen evidence-id shape any packet-assembly-side rendering of a parity
  result must use (mirrors `_evidence_id_for_context_search_result()`/`_evidence_id_for_graphify_result()`
  in `knowledge_gateway_packet_assembly.py`, which would need a `_evidence_id_for_parity_result()`
  sibling if packet-assembly wiring is in scope — see Risks below).
  `tests/tools/test_knowledge_gateway_packet_assembly.py:431` already lists `"parity:"` in a closed
  evidence-id-prefix set, confirming this is treated as load-bearing today, not speculative.
- Two existing router tests will need to flip when `not_yet_routed` is removed for this row:
  `tests/tools/test_knowledge_gateway_router.py::test_routes_requirement_completeness_to_context_search_with_not_yet_routed_marker`
  (L169-174) and `::test_parity_id_identifier_routes_via_requirement_completeness_row_with_marker`
  (L216-221) — both currently assert `providers_selected == ["context_search"]` and
  `not_yet_routed == "parity_ledger"`.

## Risks and Open Questions

**1. (Blocking — flagged, not assumed) The router-only fix does not achieve real end-to-end
reachability.** The ticket's Related Code Areas names only `tools/parity_index.py` and
`tools/knowledge_gateway_router.py`. But as shown above, `route()` never calls providers for any
identifier-matched/shape-classified query — the real provider-invocation path for every live
`_run_knowledge_context()` call is `knowledge_gateway_packet_assembly.py::call_providers_for_routing_decision()`,
which has its own separate, hardcoded provider dispatch that explicitly skips anything not named
`"context_search"`/`"graphify"`. Adding `_run_parity_provider()` only to `knowledge_gateway_router.py`
(mirroring `_run_context_search_provider`/`_run_graphify_provider`, which are themselves only
reachable via the ambiguous-intent fallback, which a parity_id query never enters) produces a
function with **no live caller anywhere** — AC3 ("reaches `tools/parity_index.py::entry()` ...
verified by a real test") would only be satisfiable by a test that calls `_run_parity_provider()`
directly/in isolation, not by any test that drives the real `_run_knowledge_context()` MCP tool
end-to-end with a parity-ID query. No sibling Phase 4 ticket
(`P4-CHANGED-PATH-CONTEXT`/`P4-WORKFLOW-RECOMMENDATION-EVALUATION`/`P4-DIRECT-TOOL-COMPARISON`, all
read via `tickets/todos/knowledge-gateway-mcp-phase4/`) covers `knowledge_gateway_packet_assembly.py`
wiring either — this is genuinely this ticket's own unaddressed gap, not deferred elsewhere. The
Plan phase must explicitly decide and state which of these it is doing:
  (a) treat "wiring the adapter into the router" as also covering
      `call_providers_for_routing_decision()`'s dispatch — i.e. add a `"parity_ledger"` branch there
      too, even though that file isn't named in Related Code Areas (a scope amendment, not scope
      creep, since it's required for the ticket's own stated ACs to be true end-to-end); or
  (b) explicitly narrow AC3's "real test" to a router/adapter-level unit test only, and record in
      Implementation Notes that full `_run_knowledge_context()` end-to-end parity routing remains
      unwired pending a follow-up ticket.
Silently doing neither — landing `_run_parity_provider()` in `knowledge_gateway_router.py` alone and
calling AC3 satisfied via only an isolated unit test — would leave the shipped feature
non-functional through the only real caller (the MCP tool) while appearing "done."

**2. `negative_knowledge_support`: resolved as `SCOPED`, conditionally.** `tmp/mcp-followup-instruction.md`
§5 requires "evidence + validated search scope," explicitly rejecting "a missing search result
alone." `entry()`'s raw `{"found": False}` on a bare, un-augmented call **is** exactly "a missing
search result alone" — it queries a real, well-defined scope (the SQLite index built from every
`docs/parity_ledger/*.yaml` shard present at last `build` time, `_load_shards()` globs `*.yaml`
with no exclusions), but the call does **not** itself verify that scope is still valid relative to
the live YAML shards; `check_staleness()` is a separate, uninvoked function. §5 explicitly says
"changes within [the checked] scopes should invalidate the negative claim" — with `entry()` alone,
a shard edited after the last `build` (adding the very entry being queried) would silently produce
a false `found: False`, exactly the failure mode §5 warns against. **Therefore: `SCOPED` is only
honest if `_run_parity_provider()`'s implementation calls `check_staleness()` (or equivalently
re-derives freshness) as part of resolving every negative (`found: False`) result, and only reports
the negative claim as validated when `status == "FRESH"`** — surfacing the checked scope (e.g. "all
`docs/parity_ledger/*.yaml` shards as of `source_manifest_hash`") and downgrading to an honestly
unverified/stale response otherwise. If the Plan/Implement phases wire `_run_parity_provider()` as
a bare passthrough to `entry()`/`impact()` without this staleness check, the honest descriptor value
is `NONE`, not `SCOPED` — declaring `SCOPED` without the staleness check would be exactly the kind
of unearned capability claim §2 of `knowledge_gateway_mcp_contract.md` forbids ("the router must
never claim a capability the descriptor does not advertise" — the inverse failure, a descriptor
claiming a capability the adapter doesn't actually earn, is equally dishonest). This is a **design
requirement for the Plan phase**, not a free descriptor-label choice.

**3. `negative_knowledge_support: SCOPED` alone does not make `assemble_packet()`'s auto-triggered
negative claim actually verify.** `build_negative_claim_support()` in `knowledge_gateway_packet_assembly.py`
(L428-498) only reaches `SUPPORTED`/`VERIFIED` if a non-empty `validated_scopes` list is passed in;
`assemble_packet()`'s own only call site (L692-699, the "no statements found" auto-trigger) never
supplies `validated_scopes` (always `None` -> `[]`), so it always falls into the "validated_scopes
not established as complete" `UNVERIFIED` branch (L472-484) **regardless of what any contributing
provider's descriptor declares**. Declaring parity's `negative_knowledge_support: SCOPED` is honest
about the *provider's* real capability, but will not, by itself, change any real
`_run_knowledge_context()` response's `verification` field unless a further wiring change (out of
this ticket's stated Related Code Areas, same category of gap as Risk 1) also threads
`validated_scopes` through for parity-sourced negative claims. Record this as a known, disclosed
limitation rather than silently expecting the descriptor change alone to "just work."

**4. `check_staleness()` as a `generation_fingerprint`-equivalent signal**: yes, real and usable —
`source_manifest_hash`/`live_hash` is a genuine content-derived fingerprint of the exact shard set,
directly analogous to Graphify's `built_at_commit` (`generation_fingerprint: true` there). Reporting
`generation_fingerprint: true` for Parity, backed by `check_staleness()`, is defensible — but only
if the adapter actually surfaces/uses it (same caveat as #2: a descriptor field must be earned by
real adapter behavior, not just by the interface's raw availability).

**5. `docs/parity_ledger/infrastructure.yaml`'s id pattern is `^[A-Z]+-[0-9]{3}$`** (exactly 3
digits, `docs/parity_ledger/schema.json` L9-12) — `INFRA-351` still fits; not an issue now, but note
for whoever eventually crosses `INFRA-999`.

## Anti-Drift Hazards

- Do not let "mirror `_run_context_search_provider()`/`_run_graphify_provider()`'s existing shape"
  become an excuse to place `_run_parity_provider()` somewhere with no real caller (Risk 1) — a
  function that type-checks and unit-tests cleanly but is never invoked by the live gateway is a
  drift risk masquerading as done work.
- Do not let the `negative_knowledge_support` field default to whatever value makes an
  already-planned test pass most easily — Risk 2 above requires an actual staleness-aware
  implementation choice, made and justified in `plan.md`, before the descriptor value is picked.
- Do not touch `tools/parity_index.py` itself (Out of Scope is explicit and this investigation found
  no reason to violate it — the interface as built already exposes everything this ticket needs).
- Do not thread `changed_paths`/`impact(changed_path=...)` wiring into this ticket — that is
  `TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT`'s explicit job (Out of Scope, confirmed by reading
  that ticket's own place in `SEQUENCE.md`).
- Do not modify `route_ambiguous()`'s fixed `_AMBIGUOUS_PROVIDERS` pair to add `"parity_ledger"` as
  a drive-by "fix" for Risk 1 — a parity_id-shaped query is never ambiguous by construction
  (`match_parity_id()` always short-circuits it before the ambiguous fallback is reached), so adding
  it there would be dead code disguised as a fix, not a real solution to Risk 1.
- The two `not_yet_routed`-asserting router tests (Prior Work) must be **updated**, not deleted —
  deleting a test that would otherwise correctly fail is exactly the kind of gate-avoidance CLAUDE.md
  forbids; the correct fix is updating their assertions to match the new real behavior.

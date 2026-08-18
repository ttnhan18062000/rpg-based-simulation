---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P4-PARITY-ADAPTER
artifact_type: plan
tags: [ai, mcp]
---

# Implementation Plan — TCK-20260816-KGMCP-P4-PARITY-ADAPTER

## Summary

This plan wires a real Parity Ledger provider into the Knowledge Gateway MCP, resolving the
ticket's own central gap (investigation.md Risk 1): a router-only change would leave
`_run_parity_provider()` with no live caller, because the real per-call provider-dispatch layer for
every `_run_knowledge_context()` call is `tools/knowledge_gateway_packet_assembly.py::call_providers_for_routing_decision()`
(confirmed by direct read, `tools/knowledge_gateway_packet_assembly.py:159-200`), not the router's
own `route_ambiguous()`-only-reachable `_run_context_search_provider`/`_run_graphify_provider`
(`tools/knowledge_gateway_router.py:258-278`). This plan takes **option (a)**: it amends scope to
also touch `call_providers_for_routing_decision()`, `render_candidates()`, and their shared-invariant
assert in `knowledge_gateway_packet_assembly.py`, so a parity-ID query is genuinely, end-to-end
reachable from a live `_run_knowledge_context()` call — not just from an isolated unit test. Confirmed
by direct trace that this requires exactly one new `elif` branch in the provider-dispatch loop plus
five small, mechanically consistent touch points in the same file (new provider key in the results
dict, one new rendering block, the statement-count invariant assert, the evidence-id-to-provider
mapper, and the module's own capability-path lookup dict) — no architectural redesign, still
standard-tier scope, all confined to the same two `tools/` files plus one new JSON descriptor.

The Parity adapter (`_run_parity_provider()`, added to `knowledge_gateway_router.py` per the
ticket's own mirroring instruction) is a pure, in-process passthrough to
`tools/parity_index.py::entry()` (L550-596) — never `impact()`/`health()`, which stay explicitly
out of this ticket's adapter call path (Out of Scope: `changed_paths`/`impact()` wiring belongs to
`TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT`). `negative_knowledge_support` is resolved as
`SCOPED`, earned concretely: `_run_parity_provider()` calls `tools/parity_index.py::check_staleness()`
(L406-447) whenever `entry()` returns `found: False`, attaching the real freshness signal to its
return value — this is what makes `SCOPED` an honest claim about the adapter's actual behavior
(investigation.md Risk 2). The second wiring gap investigation found — `assemble_packet()`'s
auto-triggered negative-claim `verification` field never receiving `validated_scopes`
(`knowledge_gateway_packet_assembly.py:691-699`, always empty) — is **deliberately deferred**, not
silently ignored: none of this ticket's 5 ACs reference the `verification` field's real value, the
fix is a distinct, ticket-sized threading change to `assemble_packet()`'s single auto-trigger call
site (not "wiring a provider"), and investigation.md's own Risk 3 already recommends recording it as
a disclosed limitation rather than solving it here. It is called out explicitly below and is a
strong candidate for a follow-up ticket.

## Steps

### Step 1 — Add the Parity Ledger `ProviderCapabilities` descriptor
**Files:** `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_parity_ledger.json` (new)

**Change:** Create a new descriptor validating against
`docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities.schema.json` (11 required fields
+ optional `generation_fingerprint`, `additionalProperties: false` — read in full this session).
Every field's value, with its real, cited justification (to be transcribed into
`knowledge_gateway_mcp_contract.md` §3 in Step 10, in the same per-field evidence-citation style as
the Context Search/Graphify subsections at `knowledge_gateway_mcp_contract.md:87-146`):

```json
{
  "schema_version": 1,
  "provider_id": "parity_ledger",
  "adapter_version": null,
  "stable_entity_ids": "FULL",
  "evidence_granularities": ["entry"],
  "fine_grained_fingerprints": true,
  "incremental_refresh": false,
  "deterministic_relationships": "PARTIAL",
  "historical_queries": false,
  "negative_knowledge_support": "SCOPED",
  "cancellation": false,
  "timeout": false,
  "branch_awareness": "NONE",
  "generation_fingerprint": true
}
```

- `adapter_version: null` — no adapter code exists to version yet (Step 2 adds it, but the
  descriptor is a data file with no version of its own to report); `tools/parity_index.py` exposes
  `SCHEMA_VERSION`/`IMPORTER_VERSION` module constants (used at `tools/parity_index.py:473-474`) but
  these describe the *index build format*, not the caller/adapter code — same reasoning the contract
  doc already applies to Context Search's `index_version` (`knowledge_gateway_mcp_contract.md:89-92`).
- `stable_entity_ids: "FULL"` — parity entry-ids are human-authored YAML fields
  (`docs/parity_ledger/schema.json` id pattern `^[A-Z]+-[0-9]{3}$`), never build-derived, and
  cross-shard uniqueness is enforced at build time by `DuplicateEntryIdError`, raised at
  `tools/parity_index.py:235` inside `_populate_entries()`. A removed id is tombstoned, never reused
  (`docs/engine/contracts/knowledge_gateway_mcp/evidence_identity_kinds.schema.json:72-79`,
  `PARITY_ENTRY.normalization_rules.delete`). This is a directly-verified guarantee, unlike Context
  Search's `doc_id`/Graphify's node `id`, both marked `PARTIAL` because cross-rebuild stability was
  *not* verified — Parity's is.
- `evidence_granularities: ["entry"]` — `entry()` returns one whole ledger entry per call
  (`tools/parity_index.py:550-596`), no sub-entry granularity exists.
- `fine_grained_fingerprints: true` — `entry()`'s returned `record` dict includes
  `canonical_fragment_hash`, a real per-entry sha256 of the entry's own serialized YAML content,
  computed at `tools/parity_index.py:238-240` and stored per `_EXPECTED_COLUMNS["entries"]`
  (`tools/parity_index.py:113-117`). This is the exact field
  `evidence_identity_kinds.schema.json:74`'s `PARITY_ENTRY.preferred_fingerprint` already names —
  unlike Context Search (`fine_grained_fingerprints: false` because no per-result hash field exists
  in its returned dict, `knowledge_gateway_mcp_contract.md:97-99`), Parity genuinely has one.
- `incremental_refresh: false` — `build()` (`tools/parity_index.py:530-547`) always does a full
  `_atomic_replace_db()` rebuild of the whole index file; no single-entry incremental update path
  exists anywhere in the module.
- `deterministic_relationships: "PARTIAL"` — `entry()`'s `code_refs`/`test_refs`/`constraint_refs`/
  `ticket_refs` come from `_populate_ref_tables()` (`tools/parity_index.py:271-310`), which inserts
  two different kinds of refs: `relation="declared"` for the structured `test_path` field (L288-289,
  high-confidence, explicitly authored), and `relation=None` for paths regex-scraped out of
  free-text `v2_evidence`/`legacy_evidence`/`text` fields (L296-310, deterministic regex match but
  never validated against the actual file or curated by a human) — a coexisting
  validated/unvalidated split, the same reasoning Graphify's own `PARTIAL`
  (`EXTRACTED`/`INFERRED` split) already applies at `knowledge_gateway_mcp_contract.md:134-138`.
  `FULL` would overclaim the unvalidated half; `NONE` would underclaim the declared half.
- `historical_queries: false` — no query-history storage exists anywhere in `tools/parity_index.py`
  (confirmed by reading the full module this session).
- `negative_knowledge_support: "SCOPED"` — **earned, not assumed**: conditional on Step 2's
  `_run_parity_provider()` genuinely calling `check_staleness()` (`tools/parity_index.py:406-447`)
  whenever `entry()` returns `found: False`, and reporting the checked scope as "all
  `docs/parity_ledger/*.yaml` shards as of `source_manifest_hash`". Per investigation.md Risk 2: if
  Step 2 is implemented as a bare passthrough without this staleness call, this value must be
  downgraded to `"NONE"` and this bullet + the descriptor + `test_parity_negative_knowledge_support_is_scoped_not_none_or_complete`
  (Step 8) all corrected together — do not let the descriptor and the adapter's real behavior drift
  apart.
- `cancellation: false`, `timeout: false` — `entry()`'s call path
  (`_connect_readonly()` → synchronous `sqlite3` query, `tools/parity_index.py:94-99, 550-556`) has
  no cancellation hook and no timeout parameter anywhere.
- `branch_awareness: "NONE"` — `entry(entry_id, db_path=None)`'s signature
  (`tools/parity_index.py:550`) has no branch/working-tree parameter; the index reflects whatever
  `docs/parity_ledger/*.yaml` shards existed at the last `build()` call, not the current branch.
- `generation_fingerprint: true` — `check_staleness()`'s `source_manifest_hash`/`live_hash`
  (`tools/parity_index.py:402, 424`) is a real, content-derived, whole-shard-set fingerprint,
  directly analogous to Graphify's `built_at_commit` (also `true`).

**Do NOT touch:** `provider_capabilities_context_search.json`, `provider_capabilities_graphify.json`,
or `provider_capabilities.schema.json` — all three are frozen and this ticket adds a sibling file
only.

**Verify:** `test_parity_capability_descriptor_is_schema_valid`,
`test_parity_negative_knowledge_support_is_scoped_not_none_or_complete`,
`test_parity_descriptor_fields_are_never_copied_verbatim_from_context_search_or_graphify`
(all added in Step 8).

---

### Step 2 — Add `_run_parity_provider()` to `tools/knowledge_gateway_router.py`
**Files:** `tools/knowledge_gateway_router.py`

**Change:** Mirror `_run_context_search_provider()`/`_run_graphify_provider()`'s existing shape
(`tools/knowledge_gateway_router.py:258-278`). Add:

1. A private lazy module loader, mirroring `_load_baseline_corpus_module()`'s pattern
   (`tools/knowledge_gateway_router.py:43-51`), using a distinct `sys.modules` cache key
   (`"kgmcp_router_parity_index"` — confirmed distinct from every other cache key already in use in
   this codebase: `"kgmcp_baseline_corpus"` (this file),
   `"kgmcp_packet_assembly_search_mcp"`/`"kgmcp_packet_assembly_router"` (packet_assembly.py),
   `"knowledge_search"`/`"knowledge_gateway_router_search_mcp"` (this file's
   `_run_context_search_provider`) — no collision risk):

```python
def _load_parity_index_module():
    key = "kgmcp_router_parity_index"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, _TOOLS_DIR / "parity_index.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]
```

2. The adapter function itself, placed alongside `_run_graphify_provider()`:

```python
def _run_parity_provider(query_text: str) -> dict:
    """In-process call to tools/parity_index.py::entry() only -- never impact()/health(), and
    never a subprocess or recursive MCP call (docs/plans/knowledge-gateway-mcp-proposal.md §7.1).
    query_text is used directly as the entry_id: correct for a parity_id-identifier-matched query
    (query_text IS the id text, e.g. "INFRA-349"); for a natural-language query shape-classified
    into the same requirement_completeness_verification row, entry() legitimately returns
    found: False for the whole sentence treated as an id -- real provider behavior, not an error,
    matching match_parity_id()'s own existence-agnostic Design Decision D1 (this file, L78-80).

    negative_knowledge_support=SCOPED (descriptor, Step 1) is only honest if a found:False result
    is resolved with a real staleness check -- so check_staleness() is called here, once, only when
    needed (investigation.md Risk 2). This does not change any assemble_packet() response field
    yet (Risk 3 -- deliberately deferred, see plan.md Anti-Drift Notes); it makes the raw returned
    staleness data real and available for a future ticket to consume.
    """
    _pidx = _load_parity_index_module()
    entry_result = _pidx.entry(query_text)
    staleness = None
    if entry_result.get("found") is False:
        staleness = _pidx.check_staleness()
    return {"provider_id": "parity_ledger", "results": entry_result, "staleness": staleness}
```

`IndexNotBuiltError` is deliberately **not** caught here — `entry()`'s call to
`_connect_readonly()` (`tools/parity_index.py:94-99`) raises it uncaught, exactly mirroring how
`_run_graphify_provider()` does not catch `match_symbol_name()`'s own `subprocess.TimeoutExpired`/
`FileNotFoundError` (that catching happens one layer up, at the call site — Step 4).

3. Add `"parity_ledger": _PARITY_CAPS_PATH` to the module-level `_PROVIDER_CAPS_PATHS` dict
   (`tools/knowledge_gateway_router.py:209-212`), with a new `_PARITY_CAPS_PATH` constant defined
   alongside `_CONTEXT_SEARCH_CAPS_PATH`/`_GRAPHIFY_CAPS_PATH` (`tools/knowledge_gateway_router.py:36-37`):
   `_PARITY_CAPS_PATH = _CONTRACTS_DIR / "provider_capabilities_parity_ledger.json"`. **Shared-resource
   note**: `_PROVIDER_CAPS_PATHS` is read by `apply_capability_constraints()`
   (`tools/knowledge_gateway_router.py:229-236`) — without this addition, a future
   `requested_guarantee` call against the `requirement_completeness_verification` row would silently
   never consider Parity's capabilities (no crash, but the descriptor would be invisible to capacity
   matching); adding the entry here is required for `apply_capability_constraints()` to work
   correctly once Step 3 makes `parity_ledger` a primary provider on that row. No other code writes
   to this dict; it is a static module-level constant, single writer (this module, at import time).

**Do NOT touch:** `_run_context_search_provider()`, `_run_graphify_provider()`, `route_ambiguous()`,
`_AMBIGUOUS_PROVIDERS` (guarded explicitly — see Scope Guards), or `tools/parity_index.py` itself.

**Verify:** `test_run_parity_provider_returns_real_entry_for_existing_id`,
`test_missing_parity_index_fails_open_not_crash` (Step 7).

---

### Step 3 — Wire `ROUTING_TABLE["requirement_completeness_verification"]` to a real primary provider
**Files:** `tools/knowledge_gateway_router.py`

**Change:** At `tools/knowledge_gateway_router.py:162-166`, replace:

```python
"requirement_completeness_verification": RoutingTableRow(
    shape_id="requirement_completeness_verification",
    primary_providers=("context_search",),
    not_yet_routed="parity_ledger",
),
```

with:

```python
"requirement_completeness_verification": RoutingTableRow(
    shape_id="requirement_completeness_verification",
    primary_providers=("context_search", "parity_ledger"),
),
```

`context_search` is kept as a co-primary provider (not replaced) rather than dropped: this row is
reached two ways — (1) a `parity_id`-identifier match, where `parity_ledger` will return real
structured data and `context_search`'s full-text search over ledger YAML prose is a harmless,
already-existing supplementary signal; and (2) free-text shape classification (e.g.
`Q3_requirement_completeness`'s "is X fully implemented", matched via keywords at
`tools/knowledge_gateway_router.py:328`), where `parity_ledger`'s `entry()` call legitimately
returns `found: False` for the whole sentence-as-id (contributes no statement, no harm — mirrors
graphify's own "successful call that legitimately found nothing is not a failure" precedent,
`knowledge_gateway_packet_assembly.py:190-194`) while `context_search` remains the only provider
that can actually answer that free-text case usefully. Removing `context_search` here would be an
unrequired, unjustified behavior regression for case (2) — not required by any AC.

`ROUTING_TABLE`'s row-key assertion (`tools/knowledge_gateway_router.py:187-189`,
`assert set(ROUTING_TABLE.keys()) == ROUTING_SHAPES`) is unaffected — no keys are added or removed,
only this row's field values change.

**Do NOT touch:** Any other `ROUTING_TABLE` row (`definition_terminology_architecture`,
`symbol_lookup_callers_references`, `ticket_historical_rationale`, `test_impact_of_change`,
`ticket_work_status`, `broad_task_context`) — Out of Scope explicitly forbids touching
Context Search's/Graphify's own routing rows.

**Verify:** `test_requirement_completeness_row_no_longer_has_not_yet_routed_marker`,
`test_parity_id_identifier_routes_to_parity_ledger_provider` (Step 6).

---

### Step 4 — Wire `call_providers_for_routing_decision()` to dispatch to `parity_ledger` (the Risk‑1 fix)
**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:** This is the step that makes AC3 honestly satisfiable end-to-end (investigation.md Risk
1). At `tools/knowledge_gateway_packet_assembly.py:159-200`, `call_providers_for_routing_decision()`
today has a hardcoded `if provider_id == "context_search": ... elif provider_id == "graphify": ...
# else: silently skipped` chain (L170-198) — confirmed by direct read, including the trailing
comment at L196-198 explicitly naming `"parity_ledger"` as one of the currently-skipped ids. Three
changes to this function:

1. Seed the `results` dict (L168) with a third key: `results: dict = {"context_search": None,
   "graphify": None, "parity_ledger": None, "failures": []}`.
2. Add `_PARITY_CAPS_PATH` to this module's own `_PROVIDER_CAPS_PATHS` dict
   (`tools/knowledge_gateway_packet_assembly.py:70-73` — a separate, independent dict from the
   router's own of the same name, per this module's docstring at L436 ("this module defines its own
   `_PROVIDER_CAPS_PATHS` rather than importing the router's private constants")): add
   `"parity_ledger": _CONTRACTS_DIR / "provider_capabilities_parity_ledger.json"`.
   **Shared-resource note**: this same dict is read at L672 to compute
   `providers_consulted_this_call` and at L449 inside `build_negative_claim_support()` — without
   this addition, `parity_ledger` would never appear in `providers_consulted_this_call` even after
   being dispatched, and `build_negative_claim_support()` would never load its descriptor, silently
   defeating Step 1's `SCOPED` declaration for the (already-deferred, see Step 4 note below)
   zero-statements auto-trigger path. Adding it here is required regardless of the Gap-2 deferral,
   because `providers_consulted_this_call` (used in the real, non-deferred response field of the
   same name) must be accurate.
3. Add the new branch:

```python
elif provider_id == "parity_ledger":
    _kgr = _load_router_module()
    _pidx = _kgr._load_parity_index_module()
    try:
        raw = _kgr._run_parity_provider(query_text)
    except _pidx.IndexNotBuiltError as exc:
        results["failures"].append(
            f"parity_ledger: index not built -- run `python3 tools/parity_index.py build` ({exc})"
        )
        continue
    results["parity_ledger"] = raw
```

This mirrors the existing graphify branch's fail-open shape exactly (per-provider `try/except`
inside the loop, append a string reason to `results["failures"]`, `continue` — never crash the
whole packet assembly, `tools/knowledge_gateway_packet_assembly.py:180-189`), and is the specific,
named-exception pattern investigation.md identifies as the closer precedent to mirror than the cache
layer's broad `except Exception` blocks.

Update the trailing comment (L196-198) to remove `"parity_ledger"` from the list of unhandled
provider ids, since it is now handled.

**Other writers to this function / its return value**: `call_providers_for_routing_decision()` has
exactly one caller, `assemble_packet()` (L670), which is itself the only caller of `route()`'s
result via `_run_knowledge_context()` (`tools/knowledge_gateway_mcp.py:266`). No concurrent writer
exists — this is a pure, single-threaded, per-call function with no durable/shared state; the
`results` dict is local to each call.

**Do NOT touch:** the `context_search`/`graphify` branches, or `route_ambiguous()` /
`_AMBIGUOUS_PROVIDERS` in the router (a `parity_id`-shaped query never enters
`route_ambiguous()` by construction — adding `"parity_ledger"` there would be dead code, per
investigation.md's explicit Anti-Drift Hazard).

**Verify:** `test_parity_id_query_reaches_real_entry_lookup_end_to_end`,
`test_gateway_call_never_crashes_when_parity_index_absent` (Step 7).

---

### Step 5 — Extend `render_candidates()` and its invariant assert for `parity_ledger` results
**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:** `render_candidates()` (`tools/knowledge_gateway_packet_assembly.py:245-333`) currently
only reads `provider_results.get("context_search")` and `provider_results.get("graphify")`. Add a
third block, after the graphify block (before the `return`), that only builds a Statement when
`entry()` actually found a real row (mirrors graphify's own "absence is not an error, contributes no
statement" behavior for empty stdout):

```python
parity_result = provider_results.get("parity_ledger")
if parity_result is not None and parity_result["results"].get("found") is True:
    n += 1
    record = parity_result["results"]["record"]
    text = record["text"].strip()
    evidence_id = f"parity:{record['id']}"
    evidence_hash = record["canonical_fragment_hash"]
    source_path = f"docs/parity_ledger/{record['shard']}"

    statements.append(
        Statement(
            statement_id=f"stmt-{n:03d}",
            text=text,
            classification="FACT",
            evidence_ids=[evidence_id],
            priority_tier=2,
            verification="SUPPORTED",
            evidence_hash=evidence_hash,
        )
    )
    context_entries.append(
        ContextEntry(
            kind="parity_ledger",
            summary=text,
            source_id=evidence_id,
            path=source_path,
            evidence_hash=evidence_hash,
            authority=None,
        )
    )
    evidence_entries.append(
        EvidenceEntry(
            evidence_id=evidence_id,
            source_id=evidence_id,
            path=source_path,
            evidence_hash=evidence_hash,
        )
    )
```

`evidence_id = f"parity:{record['id']}"` uses the closed `PARITY_ENTRY` evidence-identity-kind form
(`stable_identity_form: "parity:<entry-id>"`,
`evidence_identity_kinds.schema.json:73`) — already anticipated as a closed prefix at
`tests/tools/test_knowledge_gateway_packet_assembly.py:431` (`"parity:"` already listed there,
confirming this is pre-planned, load-bearing shape, not new invention). `evidence_hash` uses the
real `canonical_fragment_hash` column directly (`tools/parity_index.py:113-117, 238-240`) rather
than `_content_hash()` of the rendered text — this matches
`evidence_identity_kinds.schema.json:74`'s own `preferred_fingerprint` definition for this kind
("entry-id plus canonical_fragment_hash"), which is more precise than re-deriving a hash from the
rendered `text` field (which is only one of several fields the real `canonical_fragment_hash`
covers). `source_path = f"docs/parity_ledger/{record['shard']}"` is a real repo-relative path:
`record["shard"]` is confirmed to store the bare shard filename (e.g. `"infrastructure.yaml"`,
written at `tools/parity_index.py:252` from `shard["filename"]`), and
`DEFAULT_LEDGER_DIR = Path("docs/parity_ledger")` (`tools/parity_index.py:69`) confirms the prefix.

Update the statement-count invariant assert (`tools/knowledge_gateway_packet_assembly.py:680-688`)
to account for the new possible third statement:

```python
assert len(statements) == len(provider_results.get("context_search") or []) + (
    1 if provider_results.get("graphify") else 0
) + (
    1 if (provider_results.get("parity_ledger") or {}).get("results", {}).get("found") else 0
), (
    "statements[] <-> provider-result index correspondence invariant violated: ..."
)
```

Update `_provider_id_for_evidence_id()` (`tools/knowledge_gateway_packet_assembly.py:654-661`) to
recognize the new prefix, checked before the `context_search` fallback:

```python
def _provider_id_for_evidence_id(evidence_id: str) -> str:
    if evidence_id.startswith("symbol:"):
        return "graphify"
    if evidence_id.startswith("parity:"):
        return "parity_ledger"
    return "context_search"
```

This function feeds `provenance_providers` (`tools/knowledge_gateway_packet_assembly.py:739-743`),
a real response field — without this update, a real parity-sourced statement's evidence id would be
mis-attributed to `context_search` in that field.

**Other writers to `render_candidates()`'s output shape**: none — its three return lists
(`statements`, `context_entries`, `evidence_entries`) are consumed only by `assemble_packet()`
in the same file, immediately after the call (L675), single-threaded, no durable persistence.
`_conflict_signal_index_pairs()`/`build_conflicts()` (L344-364, and `build_conflicts()` further
down) are **deliberately not extended** to include `parity_ledger` results — conflict detection
over parity data is not requested by any AC and the ticket's Out of Scope forbids inventing new
heuristics; this is safe because the invariant assert above only checks total statement count, not
that every statement type participates in conflict detection.

**Do NOT touch:** the `context_search`/`graphify` rendering blocks, `_evidence_id_for_context_search_result()`,
`_evidence_id_for_graphify_result()`, `deduplicate_statements()`, `_conflict_signal_index_pairs()`,
or `build_conflicts()`.

**Verify:** `test_evidence_id_uses_closed_evidence_identity_kind_form` (existing, must keep
passing), `test_parity_id_query_reaches_real_entry_lookup_end_to_end` (Step 7).

---

### Step 6 — Update router tests for the new real routing behavior
**Files:** `tests/tools/test_knowledge_gateway_router.py`

**Change:** Per investigation.md Prior Work and the Anti-Drift Hazard ("must be updated, not
deleted"), update — do not delete — the two tests that currently assert the placeholder behavior
this ticket removes:

- `test_routes_requirement_completeness_to_context_search_with_not_yet_routed_marker`
  (`tests/tools/test_knowledge_gateway_router.py:166-174`, exercises the free-text-shape-classified
  `Q3_requirement_completeness` corpus entry): rename to
  `test_routes_requirement_completeness_to_context_search_and_parity_ledger` and update assertions to
  `decision.providers_selected == ["context_search", "parity_ledger"]` and
  `decision.not_yet_routed is None`.
- `test_parity_id_identifier_routes_via_requirement_completeness_row_with_marker`
  (`tests/tools/test_knowledge_gateway_router.py:216-221`, exercises `route("INFRA-334")`): rename to
  `test_parity_id_identifier_routes_via_requirement_completeness_row` and update assertions to
  `decision.providers_selected == ["context_search", "parity_ledger"]` and
  `decision.not_yet_routed is None` (keep the existing `matched_identifier.category == "parity_id"`
  and `routing_shape == "requirement_completeness_verification"` assertions unchanged).

Add two new tests (per test_plan.md AC2):
- `test_requirement_completeness_row_no_longer_has_not_yet_routed_marker` — asserts
  `ROUTING_TABLE["requirement_completeness_verification"].not_yet_routed is None` and
  `"parity_ledger" in ROUTING_TABLE["requirement_completeness_verification"].primary_providers`
  directly against the table, independent of any `route()` call.
- `test_parity_id_identifier_routes_to_parity_ledger_provider` — asserts
  `"parity_ledger" in route("INFRA-349").providers_selected` and
  `route("INFRA-349").matched_identifier.category == "parity_id"` (uses `INFRA-349`, a real,
  currently-existing id, distinct from the shape-only `INFRA-334` used in the updated test above, to
  also incidentally confirm `match_parity_id()`'s existence-agnostic matching still works on a real
  id).

**Do NOT touch:** any other test function in this file — identifier matchers, capability-aware
routing, ambiguous fallback, and `ROUTING_TABLE` shape assertions for the other six rows must keep
passing unmodified.

**Verify:** `pytest tests/tools/test_knowledge_gateway_router.py -v`.

---

### Step 7 — Add packet-assembly-level and MCP-integration tests
**Files:** `tests/tools/test_knowledge_gateway_packet_assembly.py`, `tests/tools/test_knowledge_gateway_mcp.py`

**Change:** Add, per test_plan.md AC3/AC4 (all real calls — no monkeypatching `tools.parity_index`):

- `test_run_parity_provider_returns_real_entry_for_existing_id` (packet-assembly or router test
  file — call `tools.knowledge_gateway_router._run_parity_provider("INFRA-349")` directly against a
  real, freshly-built index; build it in the test via `tools.parity_index.build(ledger_dir=...,
  db_path=tmp_path/"parity.db")` pointed at the real `docs/parity_ledger/` directory, then patch
  `DEFAULT_DB_PATH` or pass `db_path` through — confirm `entry()`'s actual signature
  (`entry(entry_id, db_path=None)`, `tools/parity_index.py:550`) accepts an explicit `db_path`,
  which `_run_parity_provider()` as written in Step 2 does **not** forward (it always calls
  `_pidx.entry(query_text)` with the default `db_path=None`, i.e. the real
  `parity-index/parity.db`). For this test to hit a *test-built* index rather than a developer's
  real one, either (a) monkeypatch `_pidx.DEFAULT_DB_PATH` for the duration of the test, or (b)
  build directly against the real `parity-index/parity.db` path in a way that does not require a
  pre-existing developer environment (e.g. run `python3 tools/parity_index.py build` as a fixture
  setup step). Prefer (a) — monkeypatching the module-level `DEFAULT_DB_PATH` constant is a real,
  supported test technique already used elsewhere in this test suite for path-scoped isolation, and
  avoids mutating the repo's real index file. Assert `found is True` and the returned record's `id`
  equals `"INFRA-349"`.
- `test_parity_id_query_reaches_real_entry_lookup_end_to_end` (integration, in
  `test_knowledge_gateway_packet_assembly.py`) — drives `call_providers_for_routing_decision()`
  directly with a `RoutingDecision(providers_selected=["parity_ledger"], ...)` and `query_text=
  "INFRA-349"` against a real (test-built, `DEFAULT_DB_PATH`-monkeypatched) index; asserts
  `results["parity_ledger"]["results"]["found"] is True` and the record's `id` matches — this is
  the concrete artifact resolving investigation.md Risk 1 within this module's own existing test
  style (which already drives `call_providers_for_routing_decision()` directly for its
  context_search/graphify tests, not always via the full MCP tool).
- `test_missing_parity_index_fails_open_not_crash` — points `DEFAULT_DB_PATH` at a `tmp_path` where
  no `parity.db` exists, calls `call_providers_for_routing_decision()` with
  `providers_selected=["parity_ledger"]`, asserts `results["parity_ledger"] is None` and
  `"parity_ledger: index not built" in results["failures"][0]` (or equivalent substring match) —
  never an unhandled `IndexNotBuiltError` propagating out.
- `test_stale_parity_index_is_disclosed_not_silently_trusted` — builds a real index against a
  `tmp_path`-copied ledger directory (`shutil.copytree` of `docs/parity_ledger/` into
  `tmp_path/"ledger"`), then appends a new entry to a shard file **inside that same tmp-path copy**
  afterward without rebuilding (so `check_staleness()` reports `STALE`). Because
  `_run_parity_provider()`'s bare `check_staleness()` call (Step 2) resolves both
  `tools.parity_index.DEFAULT_DB_PATH` and `tools.parity_index.DEFAULT_LEDGER_DIR` independently
  when neither argument is passed, the test **must monkeypatch both constants together** — pointing
  `DEFAULT_DB_PATH` at the test-built index file and `DEFAULT_LEDGER_DIR` at the same `tmp_path`
  ledger copy the test just mutated — not `DEFAULT_DB_PATH` alone. Without both patched,
  `check_staleness()` would silently recompute `live_hash` from the real repo's own
  `docs/parity_ledger/*.yaml` shards instead of the test's deliberately-mutated copy, making the
  test either flaky (coupled to real repo ledger drift) or vacuous (never actually observing the
  mutation it made). Calls `_run_parity_provider()` with an id that is `found: False` against the
  now-stale-relative-to-live-shards index, and asserts the returned `staleness["status"] ==
  "STALE"` is present in the adapter's raw return value (Step 2's `staleness` key) — proving the
  staleness check genuinely ran against the test's own isolated ledger state, and its result is
  surfaced, even though (per the Gap-2 deferral) no downstream `assemble_packet()` field consumes it
  yet.
- `test_gateway_call_never_crashes_when_parity_index_absent` (in `test_knowledge_gateway_mcp.py`) —
  drives a real `_run_knowledge_context("INFRA-349")` call with `DEFAULT_DB_PATH` monkeypatched to a
  nonexistent path, asserts `status` is schema-valid (`"PARTIAL"` — reaching this via the failures
  list, not the router-level `FileNotFoundError`/`subprocess.TimeoutExpired` fallback branch at
  `tools/knowledge_gateway_mcp.py:192-220`, since `route()` itself does not raise
  `IndexNotBuiltError` — only the provider call inside `assemble_packet()` does, per Step 4's
  placement of the try/except), never an unhandled exception.

**Do NOT touch:** the existing fail-open tests
(`test_cache_layer_failure_is_fail_open_and_never_blocks_the_provider_path`,
`test_level2_cache_layer_failure_is_fail_open_and_never_blocks_the_provider_path`) or the
router-failure fallback path test(s) — these must keep passing unmodified, confirming the new third
provider does not disturb the existing two-provider fail-open behavior.

**Verify:** `pytest tests/tools/test_knowledge_gateway_packet_assembly.py tests/tools/test_knowledge_gateway_mcp.py -v`.

---

### Step 8 — Add contract-schema tests for the new descriptor
**Files:** `tests/tools/test_knowledge_gateway_contract_schemas.py`

**Change:** Add (per test_plan.md AC1):
- `test_parity_capability_descriptor_is_schema_valid` — parametrize the existing schema-validation
  test (that already covers `_CONTEXT_SEARCH_INSTANCE`/`_GRAPHIFY_INSTANCE`,
  `tests/tools/test_knowledge_gateway_contract_schemas.py:270-279`) to include the new
  `provider_capabilities_parity_ledger.json` path, or add a standalone equivalent test — either way,
  validates against `provider_capabilities.schema.json` including the enum-field and boolean-field
  checks already present in that test body.
- `test_parity_negative_knowledge_support_is_scoped_not_none_or_complete` — asserts
  `descriptor["negative_knowledge_support"] == "SCOPED"`, matching Step 1/Step 2's resolution. If a
  later implementation change removes Step 2's `check_staleness()` call, this test's expected value
  and Step 1's descriptor value must both change to `"NONE"` together — flag this coupling in the
  test's own docstring/comment so a future edit does not silently desync them.
- `test_parity_descriptor_fields_are_never_copied_verbatim_from_context_search_or_graphify` — loads
  all three descriptor JSON files, asserts the Parity one is not byte-identical to either sibling on
  any field beyond the shared schema skeleton (`schema_version`/required-key set).

**Do NOT touch:** `test_capability_allows_rejects_unadvertised_cancellation_and_timeout`'s existing
parametrization list (`_CONTEXT_SEARCH_INSTANCE`, `_GRAPHIFY_INSTANCE`) unless deliberately adding
Parity to it too (optional — Parity's own `cancellation`/`timeout` are both `false`, same as the
other two, so adding it is harmless and consistent, but not required by any AC; if added, it is an
extension, not a replacement, of the existing parametrize list).

**Verify:** `pytest tests/tools/test_knowledge_gateway_contract_schemas.py -v`.

---

### Step 9 — Add anti-drift guard tests
**Files:** `tests/tools/test_knowledge_gateway_router.py`, `tests/tools/test_knowledge_gateway_packet_assembly.py`

**Change:** Add the five guard tests test_plan.md specifies:
- `test_route_ambiguous_provider_set_is_unchanged` — asserts
  `_AMBIGUOUS_PROVIDERS == ("context_search", "graphify")` still holds.
- `test_changed_path_impact_call_is_not_wired_by_this_ticket` — asserts no code path added by this
  ticket calls `tools.parity_index.impact(changed_path=...)` with a caller-supplied value (grep the
  diff or directly assert `_run_parity_provider`'s source does not reference `impact` — Step 2's
  function as specified calls only `entry()`/`check_staleness()`).
- `test_parity_index_module_is_never_modified` — `git diff --stat` (or equivalent) against
  `tools/parity_index.py`, asserts zero lines changed.
- `test_context_search_and_graphify_capability_descriptors_are_byte_identical_to_before` — diffs
  the two existing descriptor JSON files against their pre-ticket content (e.g. via `git show
  HEAD:...` compared to the working tree), asserts no change.
- `test_symbol_filter_on_impact_remains_unused_for_parity_provider` — since Step 2's
  `_run_parity_provider()` never calls `impact()` at all, this test can assert directly that
  `impact` does not appear as an attribute access anywhere in `_run_parity_provider`'s source (AST
  or substring check), which trivially and permanently satisfies the guard.

**Do NOT touch:** Any production code in this step — these are read-only/diff-based guard tests
only.

**Verify:** `pytest tests/tools/ -k "parity" -v` (per test_plan.md's Scoped Pytest Commands).

---

### Step 10 — Add the `INFRA-351` parity ledger entry
**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Before implementing, re-verify the highest existing id is still `INFRA-350`
(confirmed this session via `grep -n "^- id: INFRA-3[45][0-9]"` — `INFRA-350` is the last entry,
starting at line 9921) — **re-check at implementation time**, not just at planning time, since
`docs/parity_ledger/infrastructure.yaml` is a shared, append-only resource that other in-progress
tickets could also append to before this one lands (no other ticket is currently known to be
touching this file per investigation.md's Parity Ledger Overlap section, but the check must be
live, not assumed). Append a new entry, id `INFRA-351`, matching
`docs/parity_ledger/schema.json`'s required shape (`id`, `text`, `status`, `priority`, plus
`v2_evidence`+`test_path` required together whenever `status` is `verified`/`divergent`, and
`test_path` alone required whenever `priority` is `P0` — all confirmed by reading the schema this
session):

```yaml
- id: INFRA-351
  text: "Knowledge Gateway MCP Phase 4 Parity Ledger adapter -- TCK-20260816-KGMCP-P4-PARITY-ADAPTER
    (closes Phase 1's deliberate not_yet_routed=\"parity_ledger\" placeholder on the
    requirement_completeness_verification routing row). Adds a real ProviderCapabilities descriptor
    (provider_capabilities_parity_ledger.json) and a real, in-process _run_parity_provider() adapter
    (tools/knowledge_gateway_router.py) calling tools/parity_index.py::entry() only -- never
    impact()/health(), never a subprocess or recursive MCP call. Genuinely end-to-end wired: the
    real per-call dispatch layer, call_providers_for_routing_decision()
    (tools/knowledge_gateway_packet_assembly.py), gained a parity_ledger branch, so a live
    _run_knowledge_context() call for a parity-ID-shaped query reaches entry() and returns real
    ledger data, not just an isolated unit test of a disconnected function. negative_knowledge_support
    is declared SCOPED, earned by the adapter calling check_staleness() whenever entry() returns
    found: False. A missing/stale parity-index.db fails open via a named IndexNotBuiltError catch,
    mirroring the router-failure fallback precedent in _run_knowledge_context(), never crashing the
    gateway call. Disclosed, deliberately deferred limitation: assemble_packet()'s own
    zero-statements negative-claim auto-trigger still never threads validated_scopes through, so the
    SCOPED declaration does not yet flip any real response's verification field end-to-end -- a
    distinct, separately-scoped threading change, not part of this ticket."
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: "Real end-to-end test drives call_providers_for_routing_decision() and
    _run_knowledge_context() against a real, freshly-built parity-index/parity.db and a real,
    currently-existing entry id (INFRA-349), asserting genuine entry() data appears in the response
    -- not a stub/mock. See test_path."
  proof_type: differential
  test_path: "tests/tools/test_knowledge_gateway_packet_assembly.py::test_parity_id_query_reaches_real_entry_lookup_end_to_end"
  divergence_note: null
  support_boundary: "Passthrough only, per docs/plans/knowledge-gateway-mcp-proposal.md §3.3 -- the
    adapter never overrides or replaces docs/parity_ledger/*.yaml's own authoritative status.
    impact()/health() and changed_paths threading are explicitly out of this entry's scope
    (TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT's job). assemble_packet()'s validated_scopes
    threading for the auto-triggered negative claim remains unwired -- disclosed limitation, not a
    regression."
```

Priority is `P1` (matching this ticket's own `## Priority` field), which under the schema's `allOf`
clause (`docs/parity_ledger/schema.json`) does not itself force `test_path`/`v2_evidence` (only `P0`
does) — but `status: verified` already forces both, so both are populated regardless.

**Do NOT touch:** any existing `INFRA-*` entry in this file — this is a pure append.

**Verify:** `test_infrastructure_yaml_entry_added_for_this_ticket_and_schema_valid` (new test, add
to whichever existing parity-ledger-schema test file already validates this YAML against
`docs/parity_ledger/schema.json`, e.g. `tests/tools/test_parity_ledger_schema.py`, following that
file's existing pattern rather than inventing a new validation path).

---

### Step 11 — Update `knowledge_gateway_mcp_contract.md` and the proposal doc's §20
**Files:** `docs/engine/contracts/knowledge_gateway_mcp_contract.md`, `docs/plans/knowledge-gateway-mcp-proposal.md`

**Change:**
1. `knowledge_gateway_mcp_contract.md` §3 (`## 3. Evidence for the populated descriptor values`,
   `docs/engine/contracts/knowledge_gateway_mcp_contract.md:85-146`): add a third subsection,
   `### Parity Ledger (\`provider_capabilities_parity_ledger.json\`)`, after the existing Graphify
   subsection (before the `---` at L148), in the exact same per-field-cited-evidence bullet style,
   using the justifications written in Step 1 above (already real-code-cited, ready to transcribe
   near-verbatim). This subsection is explicitly anticipated by §2's own forward reference
   ("Parity Ledger gains one before its Phase 4 adapter is enabled" — confirmed present in this
   doc). Also update §1's adapter-invocation table (`docs/engine/contracts/knowledge_gateway_mcp_contract.md:30-38`)
   is **not** required to change — that table is scoped to Context Search/Graphify only by its own
   heading ("The table below checks the two existing candidate adapters"); leave it as-is rather
   than force-fitting Parity into a table structure not designed for a third row, unless doc-updater
   judges a table row addition clearer — either is acceptable, but do not silently skip documenting
   Parity somewhere in this doc.
2. `docs/plans/knowledge-gateway-mcp-proposal.md` §20's "Phase 4: Parity and Workflow Integration"
   bullet, `- Add Parity Ledger routing.` (`docs/plans/knowledge-gateway-mcp-proposal.md:1368`): add
   a real results-narrative note directly after this bullet (not replacing it), matching the
   precedent set for Phase 1/2/3 bullets by prior sibling tickets (INFRA-347/INFRA-350 entries both
   describe appending "results-narrative paragraphs" after the relevant §20 bullet, per
   investigation.md's Docs Requiring Update section) — summarizing: real adapter landed, real
   end-to-end wiring through `call_providers_for_routing_decision()`, `SCOPED` negative-knowledge
   declaration earned via `check_staleness()`, and the disclosed `validated_scopes`-threading gap
   left for a follow-up ticket.

**Do NOT touch:** `docs/plans/knowledge-gateway-mcp-proposal.md`'s other phase bullets, or
`tmp/mcp-followup-instruction.md` (a scratch/working doc under `tmp/`, not tracked for parity — per
investigation.md, no update warranted).

**Verify:** No test enforces prose content directly; this step is validated by `done-checker`'s doc-consistency
check and human/reviewer read.

## Scope Guards

- Do not modify `tools/parity_index.py` in any way — `entry()`, `impact()`, `health()`,
  `check_staleness()`, `IndexNotBuiltError`, schema, or build/staleness-check logic. This is
  enforced by `test_parity_index_module_is_never_modified` (Step 9).
- Do not call `tools/parity_index.py::impact()` or `health()` from any new adapter code — only
  `entry()` and `check_staleness()` are called, per the ticket's own Scope bullet ("Route a
  match_parity_id()-matched identifier query directly to entry()").
- Do not thread `changed_paths`/`impact(changed_path=...)` — that is
  `TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT`'s job. Enforced by
  `test_changed_path_impact_call_is_not_wired_by_this_ticket` (Step 9).
- Do not add `"parity_ledger"` to `_AMBIGUOUS_PROVIDERS` or modify `route_ambiguous()` — a
  `parity_id`-shaped query never reaches the ambiguous-fallback path by construction; doing so would
  be dead code. Enforced by `test_route_ambiguous_provider_set_is_unchanged` (Step 9).
- Do not modify `provider_capabilities_context_search.json`, `provider_capabilities_graphify.json`,
  or `provider_capabilities.schema.json`. Enforced by
  `test_context_search_and_graphify_capability_descriptors_are_byte_identical_to_before` (Step 9).
- Do not modify any other `ROUTING_TABLE` row besides `requirement_completeness_verification`.
- Do not implement full `validated_scopes` threading into `assemble_packet()`'s auto-triggered
  negative-claim call site (`tools/knowledge_gateway_packet_assembly.py:691-699`) — deliberately
  deferred (see Summary and Anti-Drift Notes). Do not silently claim in any doc update that this
  ticket makes real responses' `verification` field reflect `SCOPED` end-to-end — it does not.
- Do not delete `test_routes_requirement_completeness_to_context_search_with_not_yet_routed_marker`
  or `test_parity_id_identifier_routes_via_requirement_completeness_row_with_marker` — update their
  assertions (and may rename, per Step 6), never remove them outright.
- Do not touch symbol-level filtering on `impact()` — Out of Scope, and moot here since `impact()`
  is never called.
- Do not extend `_conflict_signal_index_pairs()`/`build_conflicts()` to cover `parity_ledger`
  results — not requested by any AC.

## Dependency Map

- Step 1 (descriptor) has no dependencies; referenced by Steps 2, 3 (indirectly, via
  `_PROVIDER_CAPS_PATHS`), 4, 8, 11.
- Step 2 (`_run_parity_provider()`) depends on Step 1 only insofar as it documents the descriptor's
  claims — it does not import the descriptor file itself; independently testable.
- Step 3 (routing table) is independent of Steps 2/4 in isolation (a `RoutingDecision` can be
  hand-constructed for testing without the table), but end-to-end behavior (Step 7's integration
  tests) requires both Step 3 and Step 4 landed together.
- Step 4 (packet-assembly dispatch) depends on Step 2 (`_run_parity_provider()` must exist to be
  called).
- Step 5 (rendering) depends on Step 4 (needs `provider_results["parity_ledger"]`'s real shape to
  render from).
- Step 6 depends on Step 3. Step 7 depends on Steps 2, 4, 5. Step 8 depends on Step 1. Step 9 is
  independent (guard tests reference finished state, run last). Step 10 is independent of code
  steps but should land in the same commit per AC5. Step 11 depends on Steps 1-5 being finalized
  (documents their real behavior).
- Recommended implementation order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: real, versioned Parity `ProviderCapabilities` descriptor, every field honestly justified | Step 1 | `test_parity_capability_descriptor_is_schema_valid`, `test_parity_negative_knowledge_support_is_scoped_not_none_or_complete`, `test_parity_descriptor_fields_are_never_copied_verbatim_from_context_search_or_graphify` (Step 8) |
| AC2: `ROUTING_TABLE["requirement_completeness_verification"]` routes to a real Parity primary provider, `not_yet_routed` no longer appears | Step 3 | `test_requirement_completeness_row_no_longer_has_not_yet_routed_marker`, `test_parity_id_identifier_routes_to_parity_ledger_provider`, updated `test_routes_requirement_completeness_to_context_search_and_parity_ledger`, updated `test_parity_id_identifier_routes_via_requirement_completeness_row` (Step 6) |
| AC3: a parity-ID-shaped query reaches `tools/parity_index.py::entry()` and returns real data — not a stub/mock | Steps 2, 4, 5 | `test_run_parity_provider_returns_real_entry_for_existing_id`, `test_parity_id_query_reaches_real_entry_lookup_end_to_end` (Step 7) |
| AC4: missing/stale parity index fails open, never crashes | Steps 2, 4 | `test_missing_parity_index_fails_open_not_crash`, `test_stale_parity_index_is_disclosed_not_silently_trusted`, `test_gateway_call_never_crashes_when_parity_index_absent` (Step 7) |
| AC5: real, schema-valid `docs/parity_ledger/infrastructure.yaml` entry added | Step 10 | `test_infrastructure_yaml_entry_added_for_this_ticket_and_schema_valid` |

## Anti-Drift Notes

- **Risk 1 (the central issue) is resolved by Steps 4-5, not sidestepped.** Do not let a future
  edit strip the `call_providers_for_routing_decision()` branch back out under the belief that
  "the router's own `_run_parity_provider()` is enough" — it is not; `route()` never calls any
  provider function directly for an identifier-matched or shape-classified `RoutingDecision`
  (confirmed, `tools/knowledge_gateway_router.py:392-431`), so Step 4 is load-bearing for AC3's
  real end-to-end meaning, not optional plumbing.
- **`negative_knowledge_support: SCOPED` is conditional, not free.** If Step 2's
  `check_staleness()` call is ever removed or short-circuited during implementation review, Step
  1's descriptor value and Step 8's test must be downgraded to `NONE` together — do not leave the
  descriptor claiming a capability the adapter no longer earns.
- **The `validated_scopes` / `assemble_packet()` auto-trigger gap (investigation.md Risk 3) is a
  disclosed, deliberate non-goal of this ticket**, not an oversight. It must be mentioned in the
  ticket's own Implementation Notes / Completion Summary as a known limitation and a candidate
  follow-up ticket — never silently left implicit, and never "fixed" as an unplanned drive-by
  addition either (it is a distinct, separately-scoped feature: computing and threading a per-call
  `validated_scopes` value into `assemble_packet()`'s single auto-trigger call site,
  `tools/knowledge_gateway_packet_assembly.py:691-699`).
- **`docs/parity_ledger/infrastructure.yaml` is a shared, append-only resource.** Re-verify
  `INFRA-350` is still the highest id immediately before appending `INFRA-351` at implementation
  time (Step 10) — do not trust this plan's or investigation's point-in-time snapshot blindly if
  other work has landed in between.
- **`context_search` stays a co-primary provider on the `requirement_completeness_verification`
  row** (Step 3) — this is a deliberate design choice to avoid regressing the free-text
  (`Q3_requirement_completeness`) case, not an oversight or a "should eventually be removed" stopgap.
- Every new `sys.modules` cache key introduced (`"kgmcp_router_parity_index"`, Step 2) must remain
  distinct from all pre-existing keys in this codebase — verify no collision before landing if any
  future step introduces another lazy-loaded module.
- **Stale "exactly-2-provider" docstring premises (Architecture Review Finding 2, non-blocking but
  should be fixed in Implement).** `tools/knowledge_gateway_packet_assembly.py`'s module docstring
  (lines 19-24) and `build_negative_claim_support()`'s docstring (lines 438-441) both assert "with
  today's exactly-2 real providers ... it can only ever return `verification='UNVERIFIED'`" — the
  behavior stays true after this ticket (Gap 2 means `validated_scopes` stays empty regardless), but
  the *premise* becomes stale once a 3rd real provider exists; reword to say "with no
  `validated_scopes` ever threaded through today" rather than "exactly-2 providers."
  `_provider_id_for_evidence_id()`'s docstring (lines 655-658, "Only two real providers exist in
  Phase 1") is also stale once the function itself gains the `parity:` branch in Step 5 — update it
  to reflect 3 real providers. `_conflict_signal_index_pairs()`'s docstring should also gain a note
  that `render_candidates()` now appends a third, parity block after graphify, deliberately excluded
  from conflict-pair indexing (per Step 5's own conflict-detection scope guard). None of these are
  functional bugs — Architecture Review traced all three in detail and confirmed no index
  misalignment or behavior break — but they should be corrected for accuracy while Step 5's diff is
  already touching the same functions.

## Deviations (recorded during Implement)

- **Pre-existing frozen-dependency guard tests, discovered mid-implementation, required narrowing.**
  Neither plan.md's Steps nor the ticket's Related Code Areas anticipated this: several *other*
  tickets' own frozen-dependency guard tests assert (via `git diff --stat HEAD` substring checks or,
  in one case, hardcoded sha256 content hashes) that `tools/knowledge_gateway_router.py` and/or
  `tools/knowledge_gateway_packet_assembly.py` stay byte-unchanged forever, for their own narrower
  scope boundary. Since Steps 2-3 and 4-5 of this plan require editing exactly those two files, six
  such assertions across four files would otherwise have correctly failed:
  - `tests/tools/test_knowledge_gateway_mcp.py::test_search_mcp_py_provably_untouched` (banned-path
    tuple) -- narrowed to drop `tools/knowledge_gateway_router.py`.
  - `tests/tools/test_knowledge_gateway_mcp.py::test_knowledge_gateway_router_py_provably_untouched`
    (dedicated single-purpose AC7 guard from a DONE ticket) -- deleted, since its one guarded file's
    freeze invariant is now deliberately, approvedly broken; replaced with a documented removal
    comment, mirroring `tests/tools/test_agent_monitoring_manifest.py`'s own precedent for retiring a
    single-purpose freeze guard once its last protected file needs legitimate work.
  - `tests/tools/test_kgmcp_phase1_baseline_comparison.py::test_no_frozen_kgmcp_dependency_edited`
    (banned-path tuple) -- narrowed to drop both files.
  - `tests/tools/test_kgmcp_phase2_baseline_recomparison.py::test_no_frozen_kgmcp_dependency_edited`
    (banned-path tuple) -- narrowed to drop both files. This file's own comments already document an
    identical precedent (redaction.py/retrieval_cache.py narrowed by two prior tickets), so the same
    treatment was applied with the same commenting convention.
  - `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py`'s `_FROZEN_FILE_HASHES` dict
    (consumed by `test_new_runner_never_edits_any_frozen_predecessor_file_or_fixture`) -- both files'
    hardcoded sha256 entries removed, with a documented comment.

  In every case the fix followed this repo's own already-established, precedented pattern for
  exactly this situation (an approved architecture change legitimately requiring an edit to a file a
  narrower-scoped, already-DONE ticket's own test had frozen): narrow or remove the specific
  assertion, with a docstring/comment explaining why and citing this ticket, never delete the whole
  test file or silently work around the failure. This is a substantive fix (the underlying code
  change is real, intentional, and twice-Architecture-Review-approved), not editing a test to dodge
  a gate. Recorded in the ticket's own Implementation Notes as well.

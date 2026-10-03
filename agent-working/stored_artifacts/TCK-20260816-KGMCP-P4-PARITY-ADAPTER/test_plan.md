---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P4-PARITY-ADAPTER
artifact_type: test_plan
tags: [ai, mcp]
---

# Test Plan — TCK-20260816-KGMCP-P4-PARITY-ADAPTER

## Regression Surface

**Unit / router:**
- `tests/tools/test_knowledge_gateway_router.py` — full file. Two tests must be **updated**
  (not deleted) because they currently assert the placeholder behavior this ticket removes:
  - `test_routes_requirement_completeness_to_context_search_with_not_yet_routed_marker` (L169-174)
  - `test_parity_id_identifier_routes_via_requirement_completeness_row_with_marker` (L216-221)
  Every other test in this file (identifier matchers, capability-aware routing, ambiguous fallback,
  `ROUTING_TABLE` shape assertions) must keep passing unmodified.

**Unit / packet assembly:**
- `tests/tools/test_knowledge_gateway_packet_assembly.py` — full file, especially
  `call_providers_for_routing_decision()`'s existing context_search/graphify tests and the closed
  evidence-id-prefix set at L431 (already includes `"parity:"`).

**Unit / contract schemas:**
- `tests/tools/test_knowledge_gateway_contract_schemas.py` — the local `capability_allows()`
  stand-in and both existing descriptor fixture tests must still pass; the schema itself
  (`provider_capabilities.schema.json`) is not modified by this ticket.

**Integration / MCP gateway:**
- `tests/tools/test_knowledge_gateway_mcp.py` — especially the fail-open tests
  (`test_cache_layer_failure_is_fail_open_and_never_blocks_the_provider_path`,
  `test_level2_cache_layer_failure_is_fail_open_and_never_blocks_the_provider_path`) and the
  router-failure fallback path (`FileNotFoundError`/`subprocess.TimeoutExpired` branch,
  L192-220 in `tools/knowledge_gateway_mcp.py`) — must remain unaffected by adding a third provider.

**Integration / measurement fixtures (read-only check, not expected to require edits):**
- `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py`,
  `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`,
  `tests/tools/test_kgmcp_measurement_baseline.py`,
  `tests/tools/test_kgmcp_phase1_baseline_comparison.py` — these validate structural/byte-identity
  properties of already-committed fixtures (`tests/tools/fixtures/kgmcp_*_results.json`), not a
  live re-derivation of `route()`'s `providers_selected` for `Q3_requirement_completeness` against
  those fixtures. Confirmed no test in this set hard-asserts equality between a fresh `route()` call
  and a fixture's stored `providers_selected` for Q3 specifically (the one live `route()` call found,
  `test_branch_partition_live_direct_call_against_a_real_current_row`, uses `CORPUS[0]`, not Q3).
  Run this suite anyway to confirm no unexpected coupling was missed.

**Parity index (unaffected, run as a sanity check that the interface this ticket calls is intact):**
- `tests/tools/test_parity_index*.py` (whatever exists under this glob) — Out of Scope forbids
  changing `tools/parity_index.py`; these tests should be untouched and still pass.

## New Tests Required

Per AC1 — capability descriptor:
- **`test_parity_capability_descriptor_is_schema_valid`** (unit) — verifies the new
  `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_parity_ledger.json` (or
  equivalent real path chosen in plan.md) validates against `provider_capabilities.schema.json`.
  Lives in `tests/tools/test_knowledge_gateway_contract_schemas.py`.
- **`test_parity_negative_knowledge_support_is_scoped_not_none_or_complete`** (unit) — asserts the
  descriptor's `negative_knowledge_support` field equals the value resolved in investigation.md's
  Risk 2 (`SCOPED`, conditional on the staleness-aware implementation actually landing — if the
  Plan/Implement phases instead ship a bare passthrough, this test's expected value must be `NONE`
  and the descriptor honesty argument in investigation.md re-checked, not silently overridden).
  Lives in `tests/tools/test_knowledge_gateway_contract_schemas.py`.
- **`test_parity_descriptor_fields_are_never_copied_verbatim_from_context_search_or_graphify`**
  (architecture guard) — diffs the three descriptor JSON files and asserts the Parity one is not
  byte-identical to either sibling on any field beyond the shared schema skeleton (guards against
  the ticket's own Scope instruction: "not copied from provider_capabilities_context_search.json/
  provider_capabilities_graphify.json"). Lives in `tests/tools/test_knowledge_gateway_contract_schemas.py`.

Per AC2 — routing table no longer stubs this row:
- **`test_requirement_completeness_row_no_longer_has_not_yet_routed_marker`** (unit) — replaces the
  two tests named in Regression Surface; asserts
  `ROUTING_TABLE["requirement_completeness_verification"].not_yet_routed is None` and
  `"parity_ledger" in ROUTING_TABLE["requirement_completeness_verification"].primary_providers`.
  Lives in `tests/tools/test_knowledge_gateway_router.py`.
- **`test_parity_id_identifier_routes_to_parity_ledger_provider`** (unit) — asserts
  `route("INFRA-349").providers_selected` includes `"parity_ledger"` and
  `matched_identifier.category == "parity_id"`. Lives in `tests/tools/test_knowledge_gateway_router.py`.

Per AC3 — a parity-ID query reaches `entry()` and returns real data, not a stub/mock:
- **`test_run_parity_provider_returns_real_entry_for_existing_id`** (unit, real call — no
  monkeypatching `tools.parity_index`) — calls the ticket's new adapter function directly with a
  real, currently-existing entry ID (`INFRA-349` or `INFRA-350`, both confirmed present in
  `docs/parity_ledger/infrastructure.yaml` this session) against a real, freshly-built
  `parity-index/parity.db` (build it in the test via `tools.parity_index.build()` into a `tmp_path`,
  never depend on a developer's local pre-built index being present) and asserts `found is True` and
  the returned record's `id` matches.
- **`test_parity_id_query_reaches_real_entry_lookup_end_to_end`** (integration — resolves
  investigation.md Risk 1) — drives whichever call path plan.md decides is authoritative
  (either a direct `_run_knowledge_context("INFRA-349")` call if `call_providers_for_routing_decision()`
  is wired, or an explicit `route()` + adapter-call pair if plan.md narrows AC3 to router/adapter
  level only) and asserts real `parity_index.entry()` data appears in the response/return value —
  this test's own shape is the concrete, checkable artifact of whichever Risk-1 resolution the Plan
  phase picks; it must not pass via a monkeypatched/stubbed `tools.parity_index`.

Per AC4 — missing/stale index fails open:
- **`test_missing_parity_index_fails_open_not_crash`** (unit) — points the adapter at a `tmp_path`
  where no `parity.db` exists, asserts the call returns a typed failure/partial result (mirroring
  the `provider_failures`-list precedent) rather than letting `IndexNotBuiltError` propagate.
- **`test_stale_parity_index_is_disclosed_not_silently_trusted`** (unit) — builds an index, then
  edits/adds a shard entry afterward (without rebuilding) so `check_staleness()` reports `STALE`,
  and asserts the adapter's negative-claim path (Risk 2) does not silently claim `found: False` as
  validated — either downgrades verification or surfaces a staleness warning, per whichever design
  plan.md settles on.
- **`test_gateway_call_never_crashes_when_parity_index_absent`** (integration) — drives a real
  `_run_knowledge_context()` call for a parity-ID query against a repo state with no
  `parity-index/parity.db`, asserts `status` is `PARTIAL`/`ERROR`-typed (schema-valid), never an
  unhandled exception.

Per AC5 — parity ledger entry:
- **`test_infrastructure_yaml_entry_added_for_this_ticket_and_schema_valid`** (unit/doc guard) —
  loads `docs/parity_ledger/infrastructure.yaml`, asserts an entry citing this ticket exists and
  validates against `docs/parity_ledger/schema.json` (id pattern `^[A-Z]+-[0-9]{3}$`, e.g.
  `INFRA-351`; if `status` is `verified`/`divergent`, `v2_evidence`+`test_path` are required per the
  schema's `allOf` clause — confirmed in investigation.md).

## Scoped Pytest Commands

```
pytest tests/tools/test_knowledge_gateway_router.py -v
pytest tests/tools/test_knowledge_gateway_packet_assembly.py -v
pytest tests/tools/test_knowledge_gateway_contract_schemas.py -v
pytest tests/tools/test_knowledge_gateway_mcp.py -v
pytest tests/tools/ -k "parity" -v
pytest tests/tools/test_kgmcp_phase1_baseline_comparison.py tests/tools/test_kgmcp_phase2_baseline_recomparison.py tests/tools/test_kgmcp_measurement_baseline.py tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py -v
```

Never: `pytest tests/`. If a `tests/tools/test_parity_index*.py` file exists, include it in the
above run as a sanity check even though `tools/parity_index.py` itself is untouched.

## Anti-Drift Test Guards

- **`test_route_ambiguous_provider_set_is_unchanged`** — asserts
  `_AMBIGUOUS_PROVIDERS == ("context_search", "graphify")` still holds (guards against the
  Anti-Drift Hazard of "fixing" Risk 1 by drive-by-adding `"parity_ledger"` to the ambiguous
  fallback pair, which would be dead code since `match_parity_id()` always short-circuits before
  `route_ambiguous()` is reached).
- **`test_changed_path_impact_call_is_not_wired_by_this_ticket`** — asserts no code path in this
  ticket's diff calls `tools.parity_index.impact(changed_path=...)` with a caller-supplied
  `changed_paths` value (guards the Out-of-Scope boundary with `TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT`).
- **`test_parity_index_module_is_never_modified`** — a diff-scoped guard (e.g. `git diff --stat`
  against `tools/parity_index.py`) asserting zero lines changed in that file, matching this
  ticket's explicit Out of Scope and the "pure caller" design constraint from
  `docs/plans/knowledge-gateway-mcp-proposal.md` §7.1.
- **`test_context_search_and_graphify_capability_descriptors_are_byte_identical_to_before`** —
  guards against accidentally editing the two existing frozen descriptor JSON files while adding
  the third.
- **`test_symbol_filter_on_impact_remains_unused_for_parity_provider`** — if `impact()` is called
  anywhere in the new adapter code, asserts `symbol` is never passed (or if passed, the adapter
  surfaces `impact()`'s own `"warnings"` field rather than silently dropping it) — guards the
  explicit Out-of-Scope boundary on symbol-level parity filtering.

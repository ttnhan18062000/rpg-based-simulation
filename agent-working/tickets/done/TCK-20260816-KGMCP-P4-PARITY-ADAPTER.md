---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260816-KGMCP-P4-PARITY-ADAPTER
phase: done
date: 2026-08-16
tags: [ai, mcp]
---

# TCK-20260816-KGMCP-P4-PARITY-ADAPTER

## Title
Wire a real Parity Ledger provider adapter into the router's already-reserved
`requirement_completeness_verification` routing row

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`tools/knowledge_gateway_router.py`'s `ROUTING_TABLE` already reserves the
`"requirement_completeness_verification"` row with `not_yet_routed="parity_ledger"`
(lines 162-166), and `match_parity_id()` (line 77) already shape-matches parity-ID-looking text into
an `IdentifierMatch(category="parity_id", ...)` (line 377-378) — Phase 1 deliberately stubbed this
out rather than routing it anywhere. `tools/parity_index.py`'s real, already-built, read-only
`entry()`/`impact()`/`health()` interface (lines 550/599/661) is the target this ticket wires that
routing row to, per proposal §7.1's own design decision ("Parity adapter, when Phase 4 begins: call
the existing parity-index Python/query interface").

## Scope
- Add a real, versioned `ProviderCapabilities` descriptor for the Parity Ledger provider (per §8.1's
  schema), with every field honestly assessed against `tools/parity_index.py`'s actual behavior —
  not copied from `provider_capabilities_context_search.json`/`provider_capabilities_graphify.json`.
  Specifically resolve (Investigate phase, not assumed): does `entry()` returning `{"found": False}`
  on a missing ID constitute `negative_knowledge_support` per `tmp/mcp-followup-instruction.md` §5's
  definition ("evidence + validated search scope," not just an absent lookup)? Does
  `check_staleness()` (line 406) provide a real `generation_fingerprint`-equivalent signal?
- Wire the adapter into the router: replace `not_yet_routed="parity_ledger"` with a real
  `primary_providers` entry for the `"requirement_completeness_verification"` row, and implement
  `_run_parity_provider()` (mirroring `_run_context_search_provider()`/`_run_graphify_provider()`'s
  existing shape) that calls `tools/parity_index.py`'s `entry()`/`impact()`/`health()` in-process —
  never a subprocess, never a recursive MCP call, per §7.1's explicit design decision.
- Route a `match_parity_id()`-matched identifier query (e.g. "INFRA-349", a real parity entry ID)
  directly to `entry()`, mirroring how `match_ticket_id()`/`match_source_path()` already route to
  their own specific lookups today (trace the real existing pattern before adding a new one).
- Handle `tools/parity_index.py::IndexNotBuiltError` (line 90) and any other real failure mode
  gracefully — the parity index is a rebuildable-on-demand SQLite file (`make parity-index-build` or
  equivalent), not guaranteed to exist; a missing/stale index must fail open (never provider-crash
  the whole gateway call), consistent with this repo's own established fail-open discipline for
  Context Search/Graphify.
- Real tests: a parity-ID-shaped query reaches the real `tools/parity_index.py` interface (not a
  stub/mock) and returns real data for a real, currently-existing parity entry ID (e.g. `INFRA-349`
  or `INFRA-350`, both real, freshly-written this session); a missing/stale parity index fails open
  correctly; the capability descriptor's fields are honestly justified by real, cited
  `tools/parity_index.py` behavior, not asserted without evidence.

## Out of Scope
- Any change to `tools/parity_index.py` itself, its schema, or its build/staleness-check logic —
  this ticket is a pure caller, reusing the existing interface as-is.
- Any change to Context Search's or Graphify's own routing rows, capability descriptors, or adapter
  functions.
- `changed_paths` caller-option threading — `TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT`'s job,
  though this ticket's own `impact(changed_path=...)` call is a natural candidate for that later
  ticket to route into, once this ticket lands.
- Making the gateway the source of truth for parity status — the adapter is read-only passthrough;
  `docs/parity_ledger/*.yaml` remains authoritative.
- Symbol-level parity filtering — `tools/parity_index.py::impact()` itself already documents (line
  650-654) that `symbol` is accepted but unused in v1 ("no symbol-level reference data"); this ticket
  does not change that.

## Acceptance Criteria
- [x] A real, versioned Parity `ProviderCapabilities` descriptor exists with every field honestly
      justified against real `tools/parity_index.py` behavior — verified by a real test.
- [x] `ROUTING_TABLE["requirement_completeness_verification"]` routes to a real Parity primary
      provider — verified by a real test proving `not_yet_routed="parity_ledger"` no longer appears
      for this row.
- [x] A parity-ID-shaped query (matching `match_parity_id()`) reaches
      `tools/parity_index.py::entry()` and returns real data for a real, currently-existing entry ID
      — verified by a real test, not a stub/mock.
- [x] A missing/stale parity index (`IndexNotBuiltError` or equivalent) fails open — the gateway call
      degrades gracefully, never crashes — verified by a real test.
- [x] A real, schema-valid `docs/parity_ledger/infrastructure.yaml` entry is added for this ticket's
      own behavior change. Added by the Parity phase: `INFRA-351` (verified/P1/differential), via
      the schema-validating writer.

## Related Tickets
- TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE4-EPIC (parent)
- TCK-20260731-PARITY-INDEX-EPIC (DONE; built the real `tools/parity_index.py` interface this ticket
  calls)
- TCK-20260815-KGMCP-P1-QUERY-ROUTER (DONE; built `ROUTING_TABLE`, `match_parity_id()`, and the
  `not_yet_routed` placeholder mechanism this ticket closes)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §7.1, §8, §8.1
- `tmp/mcp-followup-instruction.md` §3-5 (evidence granularity, provider capability contracts,
  negative knowledge)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/parity_index.py` — `entry()` L550, `impact()` L599, `health()` L661, `check_staleness()`
  L406, `IndexNotBuiltError` L90
- `tools/knowledge_gateway_router.py` — `ROUTING_TABLE` L151-180, `match_parity_id()` L77,
  `_run_context_search_provider()`/`_run_graphify_provider()` (existing adapter-call pattern to
  mirror)

## Assumptions / Open Questions
- Whether the Parity capability descriptor's `negative_knowledge_support` should be `NONE` or
  `SCOPED` given `entry()`'s `found: False` behavior is the central open question this ticket's own
  Investigate phase must resolve, per `tmp/mcp-followup-instruction.md` §5's stricter definition.

## Implementation Notes
Implemented exactly per the approved `staging_artifacts/TCK-20260816-KGMCP-P4-PARITY-ADAPTER/plan.md`
(Steps 1-9; Steps 10-11 explicitly deferred to the separate Parity/Document-Update phases per the
orchestrator's instruction for this Implement pass).

- **Step 1**: added `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_parity_ledger.json`,
  byte-identical to plan.md's cited values (`negative_knowledge_support: "SCOPED"`,
  `stable_entity_ids: "FULL"`, `fine_grained_fingerprints: true`, etc.).
- **Step 2**: added `_load_parity_index_module()` (lazy `importlib` loader, `sys.modules` cache key
  `"kgmcp_router_parity_index"`) and `_run_parity_provider()` to `tools/knowledge_gateway_router.py`,
  placed alongside `_run_graphify_provider()`. Calls `entry()` only; calls `check_staleness()`
  exactly once, only when `entry()` returns `found: False`, attaching the result under a `staleness`
  key — this is what earns the `SCOPED` descriptor claim. Added `_PARITY_CAPS_PATH` and registered it
  in `_PROVIDER_CAPS_PATHS`.
- **Step 3**: `ROUTING_TABLE["requirement_completeness_verification"]` now has
  `primary_providers=("context_search", "parity_ledger")` and `not_yet_routed=None` (field omitted,
  defaults to `None`). `context_search` kept as co-primary per plan.md's explicit rationale (free-text
  `Q3_requirement_completeness` case).
- **Steps 4-5**: `tools/knowledge_gateway_packet_assembly.py::call_providers_for_routing_decision()`
  gained a `parity_ledger` results-dict key and an `elif provider_id == "parity_ledger":` branch that
  lazy-loads the router module, calls `_run_parity_provider()`, and catches
  `_pidx.IndexNotBuiltError` (the exact same class object as `_load_parity_index_module()` returns,
  via the shared `sys.modules` cache key — verified: the router module instance loaded from within
  `call_providers_for_routing_decision()` and the one loaded directly in tests both resolve to the
  same cached `IndexNotBuiltError` class). `render_candidates()` gained a parity rendering block
  (evidence_id `parity:<id>`, evidence_hash = real `canonical_fragment_hash`, source_path =
  `docs/parity_ledger/<shard>`) after the graphify block. The statement-count invariant assert gained
  the third `parity_ledger`-found term. `_provider_id_for_evidence_id()` gained a `parity:` branch.
  `_PROVIDER_CAPS_PATHS` (this module's own, independent dict) gained the new descriptor path. Fixed
  the 4 stale "exactly-2-provider" docstring premises Architecture Review flagged (module docstring,
  `build_negative_claim_support()`, `_provider_id_for_evidence_id()`, `_conflict_signal_index_pairs()`)
  — reworded to "no `validated_scopes` ever threaded through today" instead of "exactly-2 providers,"
  with no behavior change.
- **Step 6**: renamed/updated the two placeholder-asserting router tests to assert the real routing
  (`test_routes_requirement_completeness_to_context_search_and_parity_ledger`,
  `test_parity_id_identifier_routes_via_requirement_completeness_row`) and added the two new Step 6
  tests.
- **Step 7**: added all 5 specified tests, including the dual `DEFAULT_DB_PATH`+`DEFAULT_LEDGER_DIR`
  monkeypatch for the staleness test exactly as Architecture Review's fixed plan.md specifies.
- **Step 8**: added the 3 named contract-schema tests, and (optional, low-risk extension per plan.md)
  added the new descriptor to the two existing shared-parametrize tests in the same file.
- **Step 9**: added all 5 anti-drift guard tests. Two of the AST-substring-based guard tests
  (`test_changed_path_impact_call_is_not_wired_by_this_ticket`,
  `test_symbol_filter_on_impact_remains_unused_for_parity_provider`) required an AST-based
  implementation rather than a raw substring check, since `_run_parity_provider()`'s own docstring
  legitimately mentions "impact()"/"symbol" in prose (documenting what it does NOT call) — a naive
  substring check on the whole function source (including its docstring) produced false positives.
  Fixed by walking the function's AST and checking only real `Call`/`keyword` nodes, never docstring
  text. This is a mechanical test-implementation-detail fix, not a scope or behavior change.

**Deviation from plan.md (documented, not silent) — pre-existing frozen-router guard tests in
`tests/tools/test_knowledge_gateway_mcp.py`.** Discovered mid-implementation: two tests unrelated to
this ticket's own scope — `test_search_mcp_py_provably_untouched` (banned-path tuple including
`tools/knowledge_gateway_router.py`) and the dedicated `test_knowledge_gateway_router_py_provably_untouched`
(AC7 of the already-DONE `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`) — assert via
`git diff --stat HEAD` that `tools/knowledge_gateway_router.py` stays byte-unchanged forever. This
ticket's own twice-Architecture-Review-approved plan requires editing exactly that file (Steps 2-3),
so both guards would otherwise correctly fail. Resolved by following this repo's own established,
already-precedented pattern for exactly this situation (see `test_search_mcp_py_provably_untouched`'s
own docstring, which already documents an identical prior narrowing for
`tools/knowledge_gateway_packet_assembly.py` by TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT,
and `tests/tools/test_agent_monitoring_manifest.py`'s own documented removal-not-vacuous-stub
precedent for a single-purpose freeze guard whose last protected file needed legitimate work): (1)
narrowed `test_search_mcp_py_provably_untouched`'s banned-path tuple to drop
`tools/knowledge_gateway_router.py`, with a docstring update explaining why; (2) deleted
`test_knowledge_gateway_router_py_provably_untouched` outright (its single guarded file's own freeze
invariant is now deliberately, approvedly broken — leaving a vacuous stub would be worse than
removal, per the `test_agent_monitoring_manifest.py` precedent), replacing it with a documented
removal comment in the same style. This is a real, substantive fix (following established repo
convention for an approved architecture change), not editing a test to dodge a gate — the underlying
code change is real and intentional, and the test's own invariant was written for a narrower scope
that this later, separately-approved ticket legitimately supersedes. Recorded here and in plan.md's
own Deviations section.

The same discovery, once made, generalized: running the fuller `tests/tools/ -k "parity"` and the
Phase 1/2/3 baseline/pilot scoped commands surfaced 3 more frozen-dependency guards with the
identical shape, in files this ticket never expected to touch:
`tests/tools/test_kgmcp_phase1_baseline_comparison.py::test_no_frozen_kgmcp_dependency_edited`,
`tests/tools/test_kgmcp_phase2_baseline_recomparison.py::test_no_frozen_kgmcp_dependency_edited`
(banned-path tuples, both also banning `tools/knowledge_gateway_packet_assembly.py` in addition to
the router), and `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py`'s `_FROZEN_FILE_HASHES`
dict (hardcoded sha256 content hashes for the same two files). All three were narrowed the same way,
with the same documented-comment convention — `test_kgmcp_phase2_baseline_recomparison.py`'s own file
already contained an in-repo precedent for this exact narrowing pattern (`redaction.py`/
`retrieval_cache.py`, applied by two prior tickets), which was followed directly. Corrected count
(previously miscounted as "6" — flagged by Architecture-Verify as not cleanly reconciling and fixed
here): 5 distinct previously-failing guard functions across these 4 test files
(`test_search_mcp_py_provably_untouched` narrowed, `test_knowledge_gateway_router_py_provably_untouched`
deleted — both in `test_knowledge_gateway_mcp.py` — plus one `test_no_frozen_kgmcp_dependency_edited`
each in the Phase 1/Phase 2 files, and `test_new_runner_never_edits_any_frozen_predecessor_file_or_fixture`
in the Phase 3 file), spanning 8 (test, frozen-path) pairs total (the single-path guard in
`test_search_mcp_py_provably_untouched` and the single-path guard in
`test_knowledge_gateway_router_py_provably_untouched` count as 1 pair each; the Phase 1/Phase 2/Phase 3
guards each bundle both `tools/knowledge_gateway_router.py` and
`tools/knowledge_gateway_packet_assembly.py` into one guard, counting as 2 pairs each: 1+1+2+2+2 = 8).
All 5 guard functions now pass; see Test Summary.

**Known limitation, disclosed per plan.md's Anti-Drift Notes (not fixed here, not silently
ignored):** Gap 2 — `assemble_packet()`'s zero-statements negative-claim auto-trigger
(`tools/knowledge_gateway_packet_assembly.py`, the `if not statements:` block) still never threads a
real `validated_scopes` value through to `build_negative_claim_support()`. This means the new
`parity_ledger` provider's real `SCOPED` descriptor claim does not yet flip any real
`_run_knowledge_context()` response's `verification` field end-to-end — it is honest about the
*adapter's* real capability (earned via the real `check_staleness()` call), not yet wired into the
*response*. This is a distinct, separately-scoped threading change to `assemble_packet()`'s single
auto-trigger call site, deliberately deferred per plan.md, and is a strong candidate for a follow-up
ticket.

**Not done in this Implement pass, per explicit instruction:** Step 10 (the `INFRA-351` parity
ledger entry, AC5) and Step 11 (doc updates to `knowledge_gateway_mcp_contract.md` §3 and the
proposal doc's §20) are left for the separate Parity and Document-Update phases of the pipeline.
AC5 therefore remains unchecked below.

## Test Summary
All real (no monkeypatched `tools.parity_index` internals — only module-level `DEFAULT_DB_PATH`/
`DEFAULT_LEDGER_DIR` path constants are patched for test isolation), scoped runs, all green:

- `pytest tests/tools/test_knowledge_gateway_router.py -v` — 40 passed
- `pytest tests/tools/test_knowledge_gateway_packet_assembly.py -v` — 44 passed
- `pytest tests/tools/test_knowledge_gateway_contract_schemas.py -v` — 24 passed
- `pytest tests/tools/test_knowledge_gateway_mcp.py -v` — 37 passed
- `pytest tests/tools/ -k "parity" -v` — 129 passed, 3 failed (pre-existing, unrelated:
  `test_parity_index_baseline.py`'s 3 failures are caused by a missing file,
  `docs/plans/agent_infrastructure/parity_ledger_sqlite_context/v1_decisions_phase0.md`, that does
  not exist anywhere in the repo and was not touched by this ticket — confirmed pre-existing via
  `git log` on that test file showing no relation to this ticket's changes)
- `pytest tests/tools/test_kgmcp_phase1_baseline_comparison.py tests/tools/test_kgmcp_phase2_baseline_recomparison.py tests/tools/test_kgmcp_measurement_baseline.py tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py -q --resource-budget large` —
  85 passed (run with `--resource-budget large` because these suites include ~30 real, live
  gateway calls that exceed the default 60s per-test budget, per those tests' own docstrings —
  unrelated to this ticket). Confirms no unexpected coupling to the Q3/
  `requirement_completeness_verification` provider list, and confirms the 6 frozen-dependency
  guard fixes (see Deviation above) hold under the real full run.
- `pytest tests/tools/test_knowledge_gateway_failure_semantics.py tests/tools/test_knowledge_gateway_cache.py -q` —
  45 passed (adjacent modules referencing router.py/packet_assembly.py in prose only; no frozen-path
  guards found in either file).

`tools/parity_index.py` confirmed genuinely byte-unchanged: `git diff HEAD -- tools/parity_index.py`
produces zero output (also enforced by the new `test_parity_index_module_is_never_modified` guard
test, which passes).

## Files Changed
- `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_parity_ledger.json` (new)
- `tools/knowledge_gateway_router.py`
- `tools/knowledge_gateway_packet_assembly.py`
- `tests/tools/test_knowledge_gateway_router.py`
- `tests/tools/test_knowledge_gateway_packet_assembly.py`
- `tests/tools/test_knowledge_gateway_contract_schemas.py`
- `tests/tools/test_knowledge_gateway_mcp.py`
- `tests/tools/test_kgmcp_phase1_baseline_comparison.py` (frozen-dependency guard narrowed — deviation, see Implementation Notes)
- `tests/tools/test_kgmcp_phase2_baseline_recomparison.py` (frozen-dependency guard narrowed — deviation, see Implementation Notes)
- `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py` (frozen-dependency hash guard narrowed — deviation, see Implementation Notes)

### Document-Update phase
- `docs/engine/contracts/knowledge_gateway_mcp_contract.md` — added a `### Parity Ledger
  (provider_capabilities_parity_ledger.json)` subsection to §3, per-field cited evidence transcribed
  from plan.md Step 1, in the same style as the Context Search/Graphify subsections; disclosed the
  `validated_scopes` threading gap (investigation.md Risk 3) and a newly-found redaction/cache
  `source_type` labeling gap; extended §5's cross-reference list to name the new descriptor file.
- `docs/plans/knowledge-gateway-mcp-proposal.md` — marked §20 Phase 4's "Add Parity Ledger routing."
  bullet `**Done**` (`TCK-20260816-KGMCP-P4-PARITY-ADAPTER`) with a results-narrative note, matching
  the Phase 3 bullets' citation style; disclosed the same two known limitations.
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` — added a disclosed-gap
  note to §2 (Eligible Source Types): the live `parity_ledger` provider is not yet reflected in
  `tools/knowledge_gateway_redaction.py::ALLOWED_SOURCE_TYPES` or the Level 1/Level 2 cache-write
  `source_type` derivation in `tools/knowledge_gateway_cache.py`, found during verification, not
  fixed here (code change outside this ticket's Scope/Related Code Areas).
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` — verified, not
  edited: already provider-agnostic and already anticipates the `parity:<entry-id>` identity form.
- `staging_artifacts/TCK-20260816-KGMCP-P4-PARITY-ADAPTER/investigation.md` — restructured: moved
  the `docs/parity_ledger/infrastructure.yaml` bullet from "Docs Requiring Update" to a new "Docs
  Considered But Not Required" section (out of doc-updater's scope, `parity-updater`'s territory),
  and recorded the two additional docs checked (one edited, one verified-no-change-needed) that
  weren't in the original flagged list.

## Completion Summary
Wired a real, versioned Parity Ledger `ProviderCapabilities` descriptor
(`provider_capabilities_parity_ledger.json`) and a real, in-process `_run_parity_provider()`
adapter (`tools/knowledge_gateway_router.py:282-312`) into the Knowledge Gateway MCP, closing Phase
1's deliberate `not_yet_routed="parity_ledger"` placeholder on the
`requirement_completeness_verification` routing row (`ROUTING_TABLE` now carries
`primary_providers=("context_search", "parity_ledger")`, `not_yet_routed=None`). The adapter calls
`tools/parity_index.py::entry()` only — never `impact()`/`health()`, never a subprocess or
recursive MCP call — and calls `check_staleness()` exactly once, only on a `found: False` result,
which is what earns the descriptor's `negative_knowledge_support: "SCOPED"` claim. Genuinely
end-to-end wired, not just an isolated unit test of a disconnected function: the real per-call
dispatch layer, `call_providers_for_routing_decision()`
(`tools/knowledge_gateway_packet_assembly.py:200-210`), gained a `parity_ledger` branch that fails
open on `IndexNotBuiltError` (named-exception catch, never an unhandled crash); `render_candidates()`
(`:348-386`) gained a parity rendering block using the closed `PARITY_ENTRY` evidence-identity form;
the statement-count invariant assert (`:742-746`) and `_provider_id_for_evidence_id()` (`:713-723`)
were both extended for the third real provider. 18 new tests were added and verified this session
via direct diff inspection (correcting an initial ~11 estimate, applying the same
verify-don't-trust discipline Test phase itself used on its own miscounted number): 9 in
`test_knowledge_gateway_router.py`, 3 in `test_knowledge_gateway_packet_assembly.py`, 3 in
`test_knowledge_gateway_contract_schemas.py`, 3 in `test_knowledge_gateway_mcp.py` — 15 landed in
Implement (Steps 6-9), 3 in Test phase (full MCP round-trip, free-text co-primary case,
genuine-negative-on-fresh-index case). Also handled, as a documented deviation, 5 pre-existing
frozen-dependency guard tests across 4 files that would otherwise have correctly failed once this
ticket's approved plan required editing `tools/knowledge_gateway_router.py`/
`tools/knowledge_gateway_packet_assembly.py`.

Two disclosed, deliberately deferred limitations, neither fixed in this ticket: (1) the
`validated_scopes` threading gap — `assemble_packet()`'s zero-statements negative-claim
auto-trigger still never threads a real `validated_scopes` value through, so the adapter's earned
`SCOPED` claim does not yet flip any real response's `verification` field end-to-end; a distinct,
separately-scoped threading change, strong candidate for a follow-up ticket. (2) the `source_type`
mislabeling gap, found by Document-Update — the live `parity_ledger` provider is not yet reflected
in `tools/knowledge_gateway_redaction.py::ALLOWED_SOURCE_TYPES` or the Level 1/Level 2 cache-write
`source_type` derivation in `tools/knowledge_gateway_cache.py` (both still binary
context_search/graphify checks), so a packet whose evidence includes real parity content still
gets its cache-write payload labeled `SOURCE_TYPE_CONTEXT_SEARCH` — not incorrect (the write is
allowed and the cached content is unaffected) but an honest provenance-labeling gap, out of this
ticket's Scope/Related Code Areas.

Parity has now run: `INFRA-351` was added to `docs/parity_ledger/infrastructure.yaml`
(verified/P1/differential) via the schema-validating writer, citing real line numbers for every new
symbol and all 18 new tests, with an explicit `support_boundary` disclosing both limitations above.
`INFRA-347` and `INFRA-348`'s own citations into `tools/knowledge_gateway_packet_assembly.py` were
corrected in place (not duplicated) for line-number drift this ticket's own insertions caused
(non-uniform shift, +15 near the top of the file to +64 near the bottom); no citation drift was
possible into `tools/knowledge_gateway_router.py` since no Phase 1-3 entry cites it by line number.
`python3 tools/parity_index.py build` was run as a separate, visible call afterward. AC5 (the
parity ledger entry) is now satisfied — all five Acceptance Criteria are complete.

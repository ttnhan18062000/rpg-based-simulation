---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260814-KGMCP-CONTRACT-SCHEMAS
artifact_type: plan
tags: [ai, schema, mcp]
---

# Implementation Plan — TCK-20260814-KGMCP-CONTRACT-SCHEMAS

## Summary

Freeze the Knowledge Gateway MCP's Phase 0 wire and adapter contracts as documentation-grade
artifacts, mirroring `docs/parity_ledger/schema.json`'s structural pattern (draft-07 JSON Schema,
hand-rolled Python structural assertions in tests, no `jsonschema` library dependency) and
`docs/engine/contracts/context_packet_contract.md`'s role (a prose contract for a not-yet-built
subsystem). Five new frozen `.schema.json`/`.json` files and one prose `.md` contract go under a
new `docs/engine/contracts/knowledge_gateway_mcp/` directory plus a sibling
`docs/engine/contracts/knowledge_gateway_mcp_contract.md`, each carrying an integer
`schema_version: 1` field per `tools/retrieval_events.py:46`'s
`retrieval_event_schema_version: int = 1` convention (confirmed: no `schema_version` field exists
in `docs/parity_ledger/schema.json` itself — only its structural conventions are being mirrored).
`ProviderCapabilities` descriptors are populated as two frozen JSON data files: one for Context
Search, built from `tools/search_mcp.py`'s actual current behavior (no timeout, no cancellation,
no adapter version reported — confirmed by direct read in this session), and one for Graphify,
built from the **actual installed CLI binary's** observable behavior (`graphify --version` →
`graphify 0.8.39`; `graphify -h`'s `query` subcommand takes `--budget N` but no `--timeout` flag;
`graphify-out/graph.json` carries a real `built_at_commit` field and deterministic path-derived
node `id`s) rather than a hypothetical future in-process adapter — see Design Decisions. No
gateway, routing, or live MCP tool code is written. A new test module,
`tests/tools/test_knowledge_gateway_contract_schemas.py`, structurally validates all of the above
and enforces the anti-drift guards (three-dimension non-collapse, forbidden-field exclusion,
enum-disjointness from existing frontmatter/parity vocabularies, no live-code scope creep).

## Design Decisions

### D1 — Graphify `ProviderCapabilities` descriptor describes the real CLI binary today, not a future in-process adapter (resolves investigation.md Risk 2)

**Decision: Option (a).** The Graphify capability descriptor and the "both existing candidate
adapters are checked against [the invocation contract]" acceptance criterion are satisfied by
describing the **actual, already-installed `graphify` CLI binary's** observable behavior when
shelled out to — not a Phase-1-built in-process wrapper.

**Why, with evidence gathered directly in this planning session:**
- The ticket's Out of Scope line is explicit: "Implementing the gateway, routing, or any live MCP
  tool — Phase 0 is contract-only." There is no adapter code to describe under Option (b) without
  writing it, which this ticket forbids.
- AC4 requires a "**tested**" descriptor. A descriptor under Option (b) would describe code that
  does not exist and therefore cannot be tested against real behavior — only against itself
  (circular). A descriptor under Option (a) can be tested against the real, installed `graphify`
  binary today, exactly as the Context Search descriptor is tested against the real
  `tools/search_mcp.py`.
- Verified directly in this session (not inferred): `graphify --version` → `graphify 0.8.39`
  (stdout, exit 0) — real version reporting exists at the CLI level. `graphify -h` lists a `query
  "<question>"` subcommand with `--dfs`, `--context C`, `--budget N` (default 2000), `--graph
  <path>` flags — **no `--timeout` flag exists on `query` or any subcommand**. No `cancel`/`kill`
  subcommand or signal-based cancellation is documented anywhere in `graphify -h`'s full output.
  `graphify-out/graph.json` (read directly: `python3 -c "import json; json.load(open(...))"`) has
  a top-level `built_at_commit` key (value confirmed:
  `"29d78798a1a66296231cede82bcf20de55b93cd8"`, a git commit hash) and node objects with an `id`
  field that is a deterministic slug derived from `source_file`
  (e.g. `"agents_skills_api_design_principles_assets_rest_api_template_py_assets_rest_api_template"`
  for `source_file: ".agents/skills/api-design-principles/assets/rest-api-template.py"`), not a
  random UUID — real evidence of a usable generation fingerprint and a deterministic (if
  unverified-for-uniqueness) entity-ID scheme.
- This deviates from the proposal's own stated *architectural preference* in §7.1 ("local
  deterministic interfaces rather than one MCP server recursively calling another... invoke a
  bounded local Graphify query adapter") — that preference describes a **Phase 1 implementation
  target**, not a Phase 0 contract-freeze requirement. §7.1 itself says "Exact callable boundaries
  and structured Graphify output are Phase 0 contract deliverables," i.e. Phase 0's job is to
  *write down* the target boundary, not claim it already exists. This plan's
  `knowledge_gateway_mcp_contract.md` (Step 6) documents the target in-process interface Phase 1
  must build *as a stated future requirement*, separately from the descriptor's *current,
  testable* values.

**Concrete field values this plan sets** (implementer must cite the same evidence above, not
re-derive it): `timeout: false` (no CLI flag, no wrapping code exists today), `cancellation: false`
(no mechanism), `adapter_version` set to a string that names the wrapped **CLI tool's** version
explicitly (e.g. `"graphify-cli-0.8.39"`, not a bare `"0.8.39"` that could be mistaken for an
adapter's own version — there is no adapter yet), `generation_fingerprint: true` (the
`built_at_commit` field is real and usable). Fields requiring more evidence than was gathered in
planning (`stable_entity_ids`, `evidence_granularities[]`, `fine_grained_fingerprints`,
`incremental_refresh`, `deterministic_relationships`, `historical_queries`,
`negative_knowledge_support`, `branch_awareness`) must be set to the **most conservative truthful
value** (e.g. `stable_entity_ids: PARTIAL` not `FULL`, unless the implementer additionally verifies
node-`id` uniqueness across all 31,422 current nodes before upgrading to `FULL`) and each value's
justification must be written inline in `knowledge_gateway_mcp_contract.md`, citing the specific
`graphify -h` line, `graph.json` key, or command output relied on — never asserted from the field
name alone.

### D2 — Response schema's `conflicts[]` array items carry the §14 shape; §14's top-level example is read as one array item, not a separate response variant

`docs/plans/knowledge-gateway-mcp-proposal.md:397-441` (§9.1 conceptual response) declares
`"conflicts": []` as a top-level array field on the normal response. `docs/plans/knowledge-gateway-mcp-proposal.md:834-856`
(§14) shows a JSON example with `status`, `subject`, `claims[]`, `automatic_resolution`,
`recommended_action` at the top level — but `status` there is already the response's existing
top-level field (set to `CONFLICTED`), so §14's example is read as *one array item shape* for
`conflicts[]` (`subject`, `claims[]`, `automatic_resolution`, `recommended_action` — no repeated
`status`), not a second, incompatible response envelope. This reconciliation is what test 4 in
`test_plan.md` explicitly permits ("however it is expressed... or a `conflicts[]` array item
schema"). Step 4 implements it this way.

### D3 — `evidence_detail` and `cache` stay open string types, not fabricated closed enums

`docs/plans/knowledge-gateway-mcp-proposal.md:384` shows exactly one example value for
`evidence_detail` (`"summary"`) and one for `cache` (`"HIT"`); no closed value set for either is
given anywhere in the proposal. Declaring a closed enum (e.g. inventing `"full"`/`"none"` for
`evidence_detail`, or `"MISS"`/`"PARTIAL"` for `cache`) would assert facts not evidenced by any
source, violating this plan's own fact-verification requirement. Both fields are typed `"type":
"string"` (open) in the schemas below. This is a documented judgment call, not a gap — flag it in
`knowledge_gateway_mcp_contract.md`'s cross-reference notes so `KGMCP-EVIDENCE-CACHE-IDENTITY` does
not assume a closed set exists.

### D4 — `knowledge_context` response's `ERROR` status variant is a minimal, explicitly-flagged best-effort shape

The proposal gives one conceptual response example (`status: "OK"`) and never shows an `ERROR`- or
`PARTIAL`-status example. The ticket scope still requires "response (success/partial/error)"
schemas. This plan adds an optional top-level `error` object (`{code: string, message: string}`,
required only when `status == "ERROR"`, via one `allOf`/`if`-`then` conditional mirroring
`docs/parity_ledger/schema.json`'s conditional pattern) as the minimal shape that satisfies the
acceptance criterion without inventing fields beyond what a status/error convention requires. The
response schema does **not** set `"additionalProperties": false` at the top level (unlike the
request schema) specifically to leave room for this honestly-underspecified error/partial shape;
this is intentional, not an oversight — noted inline in the schema file's own `"description"` key
and in `knowledge_gateway_mcp_contract.md`.

## Steps

### Step 1 — Freeze shared enum definitions
**Files:** `docs/engine/contracts/knowledge_gateway_mcp/shared_enums.schema.json` (new)
**Change:** Create a draft-07 JSON Schema file (mirroring `docs/parity_ledger/schema.json:1-2`'s
`"$schema": "http://json-schema.org/draft-07/schema#"` header) with top-level `schema_version: 1`
(int) and a `definitions` object containing four closed enums, each as its own named definition so
other schema files can `$ref` them:
- `status`: `["OK", "PARTIAL", "CONFLICTED", "UNVERIFIED", "ERROR"]` (source:
  `docs/plans/knowledge-gateway-mcp-proposal.md:447-450`, ticket scope bullet)
- `freshness`: `["FRESH", "NEEDS_REVALIDATION", "STALE", "UNKNOWN"]` (source: ticket scope bullet,
  no proposal line gives this exact list verbatim — ticket body is the citable source here)
- `verification`: `["VERIFIED", "SUPPORTED", "INFERRED", "UNVERIFIED"]` (source:
  `docs/plans/knowledge-gateway-mcp-proposal.md:452-453`)
- `statement_classification`: `["FACT", "INFERENCE", "DECISION"]` (source: ticket scope bullet;
  `FACT` appears in the §9.1 example at `docs/plans/knowledge-gateway-mcp-proposal.md:411`)

Each definition is `{"type": "string", "enum": [...]}`. Confirm none of these four value sets
equals or is a superset of any other value set in this file (direct guard for AC2's "no test or
schema collapses them" — enforced again at the test layer in Step 9's test 2/11, but the schema
author must not, e.g., write `freshness` as a superset of `status`).
**Do NOT touch:** `tools/validate_frontmatter.py`'s `STATUS_VALUES`/`AUTHORITY_VALUES` (confirmed
at `tools/validate_frontmatter.py:44,54`: `{"authoritative","active","historical","archive"}` /
`{"P0","P1","P2"}`) or `docs/parity_ledger/schema.json`'s `status`/`priority` enums — these four new
enums must stay a disjoint, separately-named vocabulary (Anti-Drift Hazards item 3 in
`investigation.md`).
**Verify:** test_plan.md tests 1 (schema_version present), 3 (FACT/INFERENCE/DECISION closed set),
11 (disjointness from `STATUS_VALUES`/`AUTHORITY_VALUES`/parity `status`/`priority`).

### Step 2 — Freeze the `ProviderCapabilities` descriptor schema (structure only, no instances yet)
**Files:** `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities.schema.json` (new)
**Change:** Draft-07 schema, `schema_version: 1`, defining the exact 12-field shape from
`docs/plans/knowledge-gateway-mcp-proposal.md:340-355` (§8.1): `provider_id` (string, required),
`adapter_version` (`["string","null"]`, required — `null` permitted for the honest
not-yet-implemented case), `stable_entity_ids` (enum `NONE|PARTIAL|FULL`, required),
`evidence_granularities` (array of string, required), `fine_grained_fingerprints` (boolean,
required), `incremental_refresh` (boolean, required), `deterministic_relationships` (enum
`NONE|PARTIAL|FULL`, required), `historical_queries` (boolean, required),
`negative_knowledge_support` (enum `NONE|SCOPED|COMPLETE`, required), `cancellation` (boolean,
required), `timeout` (boolean, required), `branch_awareness` (enum
`NONE|CALLER_SCOPED|PROVIDER_NATIVE`, required), `generation_fingerprint` (`["boolean","null"]`,
optional per §8.1's own "optional" annotation on this field). Set `"additionalProperties": false`
so a populated instance cannot silently add an ad hoc field. This is the schema only — the two
populated instances are Steps 7 and 8.
**Do NOT touch:** Do not populate `provider_id`/values here; this step defines shape, not data.
**Verify:** test_plan.md test 9 (all eleven/twelve §8.1 fields present with correct closed-set
types) — this step provides the schema test 9 validates instances against.

### Step 3 — Freeze the `knowledge_context` request schema
**Files:** `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_request.schema.json` (new)
**Change:** Draft-07 schema, `schema_version: 1`. `type: object`, `required: ["query"]`,
`"additionalProperties": false`. Properties, per
`docs/plans/knowledge-gateway-mcp-proposal.md:375-395` (§9.1) and the ticket scope bullet:
- `query`: string
- `mode`: `{"type": "string", "enum": ["answer", "task_context"]}`
- `budget_tokens`: integer
- `changed_paths`: array of string
- `include_history`: boolean
- `evidence_detail`: `{"type": "string"}` — open, per Design Decision D3 (no closed set evidenced)

Do not add `provider_weights`, `cache_level`, `semantic_threshold`, `provider_forcing`/
`force_provider`, or `ranking_policy` (or any equivalent) as properties — `additionalProperties:
false` plus their explicit absence is the direct machine-checkable form of AC5, per
`docs/plans/knowledge-gateway-mcp-proposal.md:392-395`.
**Do NOT touch:** Do not reuse or reference any internal routing-config shape from
`tools/hybrid_retrieval.py` (e.g. `filter_candidates()`'s authority/freshness filter args,
confirmed at `tools/hybrid_retrieval.py:127-156` per investigation.md) as a shortcut for any
request property — that is exactly the "reusing internal routing-config shapes as a shortcut"
hazard investigation.md's Anti-Drift Hazards flags.
**Verify:** test_plan.md tests 5 (forbidden-field absence + closed `additionalProperties`), 6
(field presence/types/required).

### Step 4 — Freeze the `knowledge_context` response schema (success/partial/error, three-dimension, conflicts)
**Files:** `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json` (new)
**Change:** Draft-07 schema, `schema_version: 1`. `type: object`,
`required: ["status", "freshness", "verification", "provenance_providers",
"providers_consulted_this_call"]`. Do **not** set `additionalProperties: false` at the top level
(Design Decision D4). Properties, sourced from
`docs/plans/knowledge-gateway-mcp-proposal.md:397-441` (§9.1 conceptual response):
- `mode`: `{"enum": ["answer", "task_context"]}`
- `status`: `{"$ref": "shared_enums.schema.json#/definitions/status"}`
- `freshness`: `{"$ref": "shared_enums.schema.json#/definitions/freshness"}`
- `verification`: `{"$ref": "shared_enums.schema.json#/definitions/verification"}` — **as three
  separate top-level properties, never merged** (direct implementation of AC2)
- `cache`: `{"type": "string"}` (open, per D3)
- `answer`: string
- `statements`: array of `{statement_id, text, classification: $ref
  shared_enums#/definitions/statement_classification, verification: $ref
  shared_enums#/definitions/verification, evidence_ids: array of string}`, each item
  `required: ["statement_id", "text", "classification", "evidence_ids"]`
- `context`: array of `{kind, summary, source_id, path, evidence_hash, authority}` (all string)
- `evidence`: array of `{evidence_id, source_id, path, evidence_hash}` (all string)
- `conflicts`: array of `{subject, claims, automatic_resolution, recommended_action}` per Design
  Decision D2, where each `claims[]` item is `{value, source_id, authority, valid_from, valid_to}`
  (source: `docs/plans/knowledge-gateway-mcp-proposal.md:840-855`, §14) — `valid_to` explicitly
  `["string", "null"]` since the example shows `"valid_to": null`
- `provenance_providers`, `providers_consulted_this_call`: array of string
- `budget_requested`, `budget_returned`, `cache_key_version`: integer
- `error`: optional object `{code: string, message: string}`, enforced required (via one `allOf`/
  `if`/`then` conditional, mirroring `docs/parity_ledger/schema.json:44-63`'s conditional pattern)
  when `status` is `"ERROR"` (Design Decision D4)

Add a `"description"` key at the schema's top level stating explicitly that `additionalProperties`
is intentionally not restricted at the top level because the `ERROR`/`PARTIAL` response shape is
underspecified by the source proposal (cross-reference D4).
**Do NOT touch:** Do not collapse `status`/`freshness`/`verification` into one property, one enum,
or a single `confidence` field under any circumstance — this is both an explicit acceptance
criterion (AC2) and the single highest-value anti-drift guard test_plan.md names (test 2).
**Verify:** test_plan.md tests 2 (three distinct non-collapsible fields), 4 (`CONFLICTED` shape).

### Step 5 — Freeze the `knowledge_status` response schema
**Files:** `docs/engine/contracts/knowledge_gateway_mcp/knowledge_status_response.schema.json` (new)
**Change:** Draft-07 schema, `schema_version: 1`. `type: object`, `"additionalProperties": false`.
`docs/plans/knowledge-gateway-mcp-proposal.md:463-483` (§9.2) is a **prose bullet list, not a JSON
example** — unlike §9.1, there is no proposal-verbatim field-name mapping to cite. The property
names below are this plan's own best-effort mapping of each prose bullet to a JSON property name;
state this explicitly in the schema's `"description"` key so a future reader does not mistake these
names for a proposal quotation:
- `gateway_version`: string (bullet: "gateway ... version")
- `reported_schema_version`: integer (bullet: "... and schema version" — deliberately named
  differently from this *file's own* `schema_version` top-level key, mirroring the
  `retrieval_event_schema_version` vs. `retrieval_version` distinction documented at
  `tools/retrieval_events.py:44-46` and `docs/agent-monitoring/schema.md:276`, to avoid conflating
  "version of this schema file" with "schema version this running gateway reports")
- `providers`: array of `{provider_id: string, available: boolean, generation: string}`
- `cache_entry_counts`: array of `{kind: string, freshness: string, count: integer}`
- `cache_hit_rate`, `cache_miss_rate`, `cache_stale_rejection_rate`: number
- `latency_summary_ms`: object with `lookup`, `evidence_validation`, `provider_fallback`,
  `packet_assembly`, `end_to_end` keys, each number
- `provider_fallback_rate`: number
- `recent_invalidation_reasons`: array of string
- `branch_scope`: object `{branch: string, working_tree_dirty: boolean}`
- `cache_rebuildable`: boolean

Required: `["gateway_version", "reported_schema_version"]` only — the rest are health-metric
fields that may legitimately be absent before any cache activity exists. `additionalProperties:
false` is the direct enforcement of §9.2's "should not expose provider weights, semantic
thresholds, internal cache-level controls, or provider-selection switches"
(`docs/plans/knowledge-gateway-mcp-proposal.md:480-482`).
**Do NOT touch:** Do not add any field named or shaped like a routing/weighting control — same
forbidden-field list as Step 3 applies here per AC5's "does not expose... provider weights... or
ranking-policy switches" (the ticket's own wording covers both tools, not just `knowledge_context`).
**Verify:** test_plan.md test 7.

### Step 6 — Write the prose provider adapter invocation contract
**Files:** `docs/engine/contracts/knowledge_gateway_mcp_contract.md` (new)
**Change:** New prose doc, frontmatter modeled on `docs/engine/contracts/context_packet_contract.md`'s
own frontmatter (confirmed by direct read: `status: active`, `layer: ai`, `authority: P1`,
`audience: agent`, `tags: [ai, registry, schema]` — no `artifact_type` key, since this is a
`docs/` file, not a `staging_artifacts/` artifact). Content, in order:
1. An opening paragraph stating this is a Phase-0 contract-only document, no implementation exists
   yet, mirroring `context_packet_contract.md:9-19`'s "This document defines a schema contract for
   a future implementation" framing.
2. **Provider adapter invocation contract** section transcribing
   `docs/plans/knowledge-gateway-mcp-proposal.md:288-290` (§7.1)'s requirement verbatim: "All
   adapters must support timeout, cancellation where the underlying interface permits it, version
   reporting, and deterministic fixture tests" — then a table checking Context Search and Graphify
   against each of the four requirements, with an evidence citation per cell (no unsupported
   claims):
   | Requirement | Context Search | Graphify (CLI-shelled) |
   |---|---|---|
   | Timeout | Not supported today — no wrapping timeout anywhere in `tools/search_mcp.py`/`tools/hybrid_retrieval.py` (investigation.md, confirmed this session) | Not supported today — `graphify -h`'s `query` subcommand has no `--timeout` flag (confirmed this session) |
   | Cancellation | Not supported | Not supported |
   | Version reporting | Not supported — `_run_health()` returns `index_version` (SQLite-file mtime), not an adapter/code version | Supported at the CLI level — `graphify --version` → `graphify 0.8.39` (confirmed this session); no *adapter* exists yet to version separately |
   | Deterministic fixture tests | Established pattern exists: `tests/tools/test_search_mcp.py` (15 tests) | No adapter fixture tests exist yet (no adapter code) — this ticket's own `tests/tools/test_knowledge_gateway_contract_schemas.py` fixture-tests the CLI's raw observable behavior instead, as the nearest honest equivalent |
3. **`ProviderCapabilities` descriptor semantics** section: reproduce the §8.1 field list and the
   "routing consequences" bullets verbatim from
   `docs/plans/knowledge-gateway-mcp-proposal.md:357-365`, plus a `capability_allows(descriptor,
   capability_name)` helper contract description (the router "must not claim a capability the
   descriptor does not advertise" — ties directly to AC4 and test 10).
4. **Design Decision D1 writeup** (condensed from this plan's Design Decisions section) explaining
   why the Graphify descriptor documents the CLI binary, not a future in-process adapter, with the
   same evidence citations.
5. Cross-references to all five `.schema.json`/`.json` files under
   `docs/engine/contracts/knowledge_gateway_mcp/` and a note that
   `docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 0's three relevant checklist bullets
   ("Freeze versioned JSON Schemas...", "Define provider adapter invocation...", "Define and test
   provider capability descriptors...") are satisfied by this ticket — do not edit §20 itself in
   this step (see Docs Requiring Update in `investigation.md`; editing the proposal doc is a
   separate, optional follow-up not required by any acceptance criterion here).
**Do NOT touch:** Do not write this doc under `docs/ai/`, `docs/plans/`, or
`tools/mcp_gateway/schemas/` — `investigation.md` Risk 1 recommends `docs/engine/contracts/` and no
competing precedent was found. Do not add a `docs/parity_ledger/` entry (Parity Ledger Overlap in
`investigation.md`: none warranted, same posture as `context_packet_contract.md` §4).
**Verify:** test_plan.md test 8.

### Step 7 — Populate the Context Search `ProviderCapabilities` instance
**Files:** `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_context_search.json` (new)
**Change:** JSON data file (not a schema — validated structurally against Step 2's
`provider_capabilities.schema.json` shape by Step 9's tests), `schema_version: 1`, values grounded
in direct evidence gathered in this session and in `investigation.md`'s Current Behavior section:
- `provider_id`: `"context_search"`
- `adapter_version`: `null` — `_run_health()` (confirmed at `tools/search_mcp.py`, function
  returns `{status, index_version, chunks, model}`) reports `index_version` derived from SQLite
  file mtime, not a code/adapter version; conflating the two would misrepresent current behavior
  (investigation.md, Current Behavior)
- `stable_entity_ids`: `"PARTIAL"` — result rows carry `doc_id` (confirmed:
  `tools/search_mcp.py` result-dict construction includes `doc_id`), but this ticket's
  investigation did not verify `doc_id` uniqueness/stability across index rebuilds; do not upgrade
  to `"FULL"` without that verification
- `evidence_granularities`: `["chunk"]` — results are per-chunk (`doc_id` + `section` + `heading`)
- `fine_grained_fingerprints`: `false` — no per-result hash field exists in the returned dict
  (confirmed fields: `doc_id, title, heading, source_path, section, score, semantic_score,
  keyword_score, excerpt` — no hash)
- `incremental_refresh`: `false` — `_run_search()`'s own error dict says `"action": "run make
  knowledge-index"` on missing index, implying a full rebuild path, no incremental mechanism
  evidenced
- `deterministic_relationships`: `"NONE"` — this is a ranked-retrieval provider, not a
  relationship-graph provider
- `historical_queries`: `false` — no history storage evidenced anywhere in `tools/search_mcp.py`
- `negative_knowledge_support`: `"NONE"` — an empty result list is not evidenced to carry any
  verified-absence guarantee
- `cancellation`: `false` — confirmed, no cancellation hook
- `timeout`: `false` — confirmed, no timeout wrapper anywhere in `_run_search()`'s call path
- `branch_awareness`: `"NONE"` — `_run_search(query, top_k, section, mode)`'s signature has no
  branch/working-tree parameter
- `generation_fingerprint`: `true` — `index_version` (mtime-derived) is a real, if coarse,
  whole-index generation signal, consistent with `fine_grained_fingerprints: false`
**Do NOT touch:** Do not set `timeout`/`cancellation` to `true` by copying the proposal's
aspirational §7.1 language instead of this file's own grounded values — this is the exact failure
mode test_plan.md test 8 exists to catch.
**Verify:** test_plan.md tests 8, 9.

### Step 8 — Populate the Graphify `ProviderCapabilities` instance
**Files:** `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_graphify.json` (new)
**Change:** JSON data file, `schema_version: 1`, values per Design Decision D1:
- `provider_id`: `"graphify"`
- `adapter_version`: `"graphify-cli-0.8.39"` (explicitly CLI-tool-named, not adapter-named — no
  adapter exists; confirmed via `graphify --version` this session)
- `stable_entity_ids`: `"PARTIAL"` — `graph.json` node `id`s are deterministic path-derived slugs
  (confirmed this session, sample cited in Design Decisions), but cross-rebuild uniqueness was not
  verified in this planning session
- `evidence_granularities`: `["node", "edge"]` — `graph.json` has `nodes`/`links`/`hyperedges` keys
  (confirmed this session)
- `fine_grained_fingerprints`: `false` — only one whole-graph `built_at_commit` field was found;
  no per-node/per-edge hash was observed in the sampled node object
- `incremental_refresh`: `false` — `graphify update <path>` exists (confirmed via `graphify -h`)
  but re-extracts and can overwrite `graph.json`; no evidence of a narrower, verified incremental
  path was gathered this session — conservative `false` per this step's stated default rule
- `deterministic_relationships`: `"PARTIAL"` — `graphify -h`'s sample hyperedge in `graph.json`
  carries a `"confidence": "EXTRACTED"` / `"confidence_score": 1.0` field (confirmed this session),
  implying both deterministic (`EXTRACTED`) and (per the proposal's own §7.1/investigation.md
  framing of "Inferred Graphify relationships") non-deterministic (`INFERRED`) edge kinds coexist —
  `"FULL"` would overclaim
- `historical_queries`: `false` — no query-history mechanism evidenced (`save-result` writes Q&A
  memory for the *feedback loop*, not a queryable history — do not conflate the two)
- `negative_knowledge_support`: `"NONE"` — not evidenced
- `cancellation`: `false` — confirmed, no mechanism in `graphify -h`'s full output
- `timeout`: `false` — confirmed, no `--timeout` flag on `query` or any subcommand
- `branch_awareness`: `"NONE"` — `graph.json` is built from whatever was checked out at
  `built_at_commit`; no branch-scoping flag was found on `query`
- `generation_fingerprint`: `true` — `built_at_commit` is a real, confirmed field
**Do NOT touch:** Do not describe any capability as achievable only via a *future* in-process
wrapper as if it is true *today* — every value here must be traceable to a `graphify -h` flag,
`graph.json` key, or direct command output captured during this ticket's work, per Design
Decision D1.
**Verify:** test_plan.md tests 8 (contract-table cross-check), 9.

### Step 9 — Write the contract/schema test module
**Files:** `tests/tools/test_knowledge_gateway_contract_schemas.py` (new)
**Change:** Implement all 12 tests from `test_plan.md`'s "New Tests Required" section, using the
raw-`json.loads()`-and-structurally-assert pattern established by
`tests/tools/test_parity_ledger_schema.py` (no `jsonschema` library import). Key implementation
notes:
- Tests 1–7, 9 load each `.schema.json`/`.json` file from
  `docs/engine/contracts/knowledge_gateway_mcp/` via `pathlib.Path` + `json.loads()` and assert
  structure (required keys, enum value sets, `additionalProperties` where specified).
- Test 8 additionally imports `tools/search_mcp.py`'s `_run_health`/`_run_search` (via the same
  `importlib.util.spec_from_file_location` pattern `search_mcp.py` itself uses for its own sibling
  imports, or a plain module import if `tools/` is already on `sys.path` per existing
  `tests/tools/test_search_mcp.py` conventions) and asserts the returned dict shape does **not**
  contain a `timeout`/`cancellation`/`adapter_version`-style field that would contradict Step 7's
  `false`/`null` values — i.e. a regression guard that today's real code still matches what the
  descriptor claims.
- Test 10 (`capability_allows`) defines the helper function **inline in this test module**, not in
  any `tools/` module — keeping it test-only infrastructure avoids creating a new `tools/` module
  that a future reader could mistake for gateway/router code (direct enforcement of test 12's own
  scope guard). Signature: `capability_allows(descriptor: dict, capability_name: str) -> bool`,
  returning the boolean value of `descriptor[capability_name]` for boolean-typed fields; assert it
  returns `False` for both adapters' `cancellation` and `timeout` given Steps 7/8's values.
- Test 11 imports `tools/validate_frontmatter.py`'s `STATUS_VALUES`/`AUTHORITY_VALUES` (confirmed
  at `tools/validate_frontmatter.py:44,54`) and reads `docs/parity_ledger/schema.json`'s `status`/
  `priority` enum arrays directly, asserting `set.isdisjoint()` against each of the four new
  gateway enums from Step 1.
- Test 12 walks `tools/` (`pathlib.Path("tools").glob("*.py")` or equivalent) asserting no new
  `.py` file defines a top-level callable literally named `knowledge_context` or `knowledge_status`,
  and reads `.mcp.json` asserting no new `mcpServers` key was added beyond what existed before this
  ticket (compare against a fixed known-baseline key set, e.g. just `search-docs` if that is the
  only entry today — verify the current `.mcp.json` content directly while implementing this test,
  do not assume its contents).
**Do NOT touch:** Do not modify `tests/tools/test_search_mcp.py`,
`tests/tools/test_hybrid_retrieval.py`, `tests/tools/test_parity_ledger_schema.py`, or
`tests/tools/test_context_packet_assembler.py` — they must keep passing unmodified per
`test_plan.md`'s Regression Surface. Do not run `pytest tests/`; scope stays within `tests/tools/`
per `test_plan.md`'s Scoped Pytest Commands.
**Verify:** `pytest tests/tools/test_knowledge_gateway_contract_schemas.py -v` (all 12 tests
passing), then the regression command:
`pytest tests/tools/test_search_mcp.py tests/tools/test_hybrid_retrieval.py tests/tools/test_parity_ledger_schema.py tests/tools/test_context_packet_assembler.py tests/tools/test_validate_frontmatter.py -v`.

## Scope Guards

- No implementation of the gateway, routing, or any live `knowledge_context`/`knowledge_status` MCP
  tool — Phase 0 is contract-only (ticket Out of Scope; enforced mechanically by Step 9 test 12).
- No changes to `.mcp.json` (no new `mcpServers` entry).
- No evidence/cache-identity work (evidence kinds, cache-lookup vs. evidence-validity identity,
  branch/working-tree cache-identity contracts) — that is
  `TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`'s scope, not this ticket's.
- No redaction/retention policy, token-counting method, SQLite operational limits, or cache-GC
  defaults — that is `TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY`'s scope.
- No Parity Ledger adapter capability descriptor — explicitly deferred to Phase 4 per the proposal
  (`docs/plans/knowledge-gateway-mcp-proposal.md:366-367`).
- No `docs/parity_ledger/*.yaml` entry added — this ticket's subsystem matches the
  `support_boundary`-null, no-entry posture `context_packet_contract.md` §4 already established
  (investigation.md, Parity Ledger Overlap).
- No new `jsonschema` pip dependency — hand-rolled structural test assertions only, matching
  `tools/parity_ledger_writer.py::validate_entry()`'s established pattern.
- No edits to `docs/plans/knowledge-gateway-mcp-proposal.md` itself in this ticket (Step 6
  cross-references it but does not modify it — a §20 checklist update, if desired, is a separate,
  optional follow-up).
- Do not touch `tools/search_mcp.py` or `tools/hybrid_retrieval.py` logic — this ticket only reads
  and documents their current behavior; any behavior change (e.g. actually adding a timeout) is out
  of scope and would be a different ticket.

## Dependency Map

- Step 4 depends on Step 1 (references `shared_enums.schema.json` via `$ref`).
- Step 9 depends on Steps 1–8 (tests validate every schema/data/doc file produced by them).
- Step 6 should be written last among the doc/schema steps (after Steps 1–5, 7, 8) so its
  cross-reference table and file list are accurate, but its content does not structurally block any
  other step — it may be drafted in parallel and finalized once filenames from Steps 1–5, 7, 8 are
  fixed.
- Steps 2, 3, 5, 7, 8 are otherwise independent of each other and may be done in any order relative
  to one another, but Step 7/8 (instances) are easiest to write correctly after Step 2 (schema
  shape) exists.
- Step 8 depends on Design Decision D1 (already resolved in this plan — no further decision needed
  before implementing).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Versioned JSON Schemas exist for `knowledge_context` request/response, `knowledge_status` response, and the four enums, each with `schema_version` | Steps 1, 3, 4, 5 | test_plan.md test 1 |
| `status`/`freshness`/`verification` stay three distinct, non-collapsible fields | Steps 1, 4 | test_plan.md test 2 |
| Provider adapter invocation contract (timeout, cancellation, version, fixture-test requirement) is written down and both adapters checked against it | Steps 6, 7, 8 | test_plan.md test 8 |
| Tested `ProviderCapabilities` descriptor populated for Context Search and Graphify; router cannot claim an unadvertised capability | Steps 2, 7, 8, 9 | test_plan.md tests 9, 10 |
| Public request schema excludes provider weights/cache-level/semantic-threshold/provider-forcing/ranking-policy fields | Step 3 (request); Step 5 (status, same forbidden-field rule per AC5's wording) | test_plan.md tests 5, 7 |
| Tests added under `tests/tools/` mirroring existing schema/contract test patterns | Step 9 | all of test_plan.md tests 1–12 |

## Anti-Drift Notes

- **Capability honesty is the ticket's central hazard.** Both `investigation.md` and this plan's
  Design Decision D1 exist because it would be easy to default `timeout`/`cancellation` to `true`
  by echoing the proposal's aspirational §7.1 text instead of reading the real code/CLI. Steps 7
  and 8 must be implemented from the cited evidence, not from the proposal's prose.
- **`status`/`freshness`/`verification` are three orthogonal fields — never merge them,** even
  under refactoring pressure to "simplify" the response schema. This is both an explicit
  acceptance criterion and the proposal's own explicit invariant (§12/§13).
- **The new gateway enums (`status`, `freshness`, `verification`, `statement_classification`) are a
  separate vocabulary from `tools/validate_frontmatter.py`'s frontmatter enums and
  `docs/parity_ledger/schema.json`'s `status`/`priority` enums.** Confirmed disjoint in this
  session (`{OK,PARTIAL,CONFLICTED,UNVERIFIED,ERROR}` vs. parity's
  `{verified,divergent,missing,unsupported,legacy_verified}`; `{FRESH,NEEDS_REVALIDATION,STALE,
  UNKNOWN}` / `{VERIFIED,SUPPORTED,INFERRED,UNVERIFIED}` vs. frontmatter's
  `{authoritative,active,historical,archive}` / `{P0,P1,P2}`). Do not alias or reuse.
  `context_packet_contract.md` §3's warning about `parity_ledger_entry` being a "second,
  differently-shaped vocabulary" is the direct precedent for why this matters.
  `KGMCP-EVIDENCE-CACHE-IDENTITY` will cite these exact enum values next — do not rename any value
  in this ticket without checking that sibling ticket has not already started.
  `evidence_detail` and `cache` are deliberately left as open `string` types (Design Decision D3) —
  do not "helpfully" tighten them into invented closed enums; that would assert facts the proposal
  does not evidence.
- **The `knowledge_context` response schema intentionally has no top-level
  `additionalProperties: false`** (Design Decision D4) — this is not an oversight to be "fixed" in
  review; it is because the `ERROR`/`PARTIAL` shape is underspecified by the source proposal. The
  request schema, by contrast, *does* set `additionalProperties: false` — do not make the two
  schemas symmetric by relaxing the request schema's closure, since the forbidden-field guard
  (AC5) specifically depends on the request schema staying closed.
- **No live code changes.** `tools/search_mcp.py` and `tools/hybrid_retrieval.py` are read-only
  references for this ticket. If a future editor is tempted to add a stub `knowledge_context()`
  function "to make the contract concrete," that is explicitly out of scope — test 12 exists to
  catch exactly this drift.

## Deviations

- **Evidence citations placed in the contract doc, not inline in the JSON instance files.** Steps
  7/8's prose describes each field's justification but does not pin down where that justification
  text physically lives. Since Step 2's `provider_capabilities.schema.json` sets
  `"additionalProperties": false`, adding an ad hoc `_evidence` key directly to
  `provider_capabilities_context_search.json`/`provider_capabilities_graphify.json` would make
  those instances violate their own declared schema shape. All evidence citations were written
  into `knowledge_gateway_mcp_contract.md` §3 instead (one subsection per adapter, one bullet per
  field, each citing the specific `graphify -h` line / `graph.json` key / `_run_health()` return
  shape it is grounded in), and the two `.json` instance files carry only `schema_version` plus the
  twelve declared `ProviderCapabilities` fields. `tests/tools/
  test_knowledge_gateway_contract_schemas.py`'s
  `test_provider_capabilities_instance_has_all_fields_with_valid_enum_values` asserts this exact
  closed key set (`schema_version` + the 12 fields, nothing else) for both instances.
- **Graphify CLI evidence re-verified directly during Implement**, not merely re-cited from the
  plan's own investigation: `graphify --version`, `graphify -h`'s full command list, and a direct
  `json.load()` of `graphify-out/graph.json` (confirming `built_at_commit`, node `id` shape, and
  that `links`/`hyperedges` `confidence` values are exactly `{"EXTRACTED", "INFERRED"}` across
  31,422 nodes) were all re-run in this session before the descriptor/contract-doc values were
  written, per the plan's own instruction that "the implementer must cite the same evidence above,
  not re-derive it" — re-verification confirmed no drift from the plan's cited values, so no field
  value changed from what Design Decision D1 specified.
- No other deviations. All 9 steps were implemented as written, including the Step 4
  `additionalProperties`-left-open decision (D4), the Step 3 closed-request-schema decision, and
  the Step 9 test-module scope guards (test 12's `.mcp.json`/`tools/` checks).

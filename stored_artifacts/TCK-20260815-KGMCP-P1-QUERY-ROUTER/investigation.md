---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P1-QUERY-ROUTER
artifact_type: investigation
tags: [ai, mcp]
---

# Investigation — TCK-20260815-KGMCP-P1-QUERY-ROUTER

## Current Behavior

**No router code exists yet.** `grep`/`graphify query` confirm no `tools/*router*`, `*dispatch*`,
class `*Router*`, `def route(`, or `def dispatch(` anywhere under `tools/`. The only "Router" nodes
in the codebase are unrelated domain routers (`InformationQueryRouter`
`src/domains/information/router.py:22`, `AlertRouter` `src/observability/alerts/router.py:19`) —
different subsystems, not a pattern to reuse or a duplication risk.

**`capability_allows()` currently exists only as a test-local helper**, not real `tools/` code:
`tests/tools/test_knowledge_gateway_contract_schemas.py:287-293` —
```python
def capability_allows(descriptor: dict, capability_name: str) -> bool:
    """Test-only contract helper — not tools/ code, since no router exists yet to own it."""
    return bool(descriptor[capability_name])
```
Its own docstring says explicitly this is temporary until a router exists. This ticket is that
router — the capability-consult logic described in §8.1 should become real `tools/` code, and the
test file's docstring will be stale in that one respect once this ticket lands (see Docs Requiring
Update).

**`tools/search_mcp.py`** (264 lines) is the module-layout precedent: single flat file, lazy
`importlib.util`/`sys.modules` loading of sibling files (`knowledge_search.py`, `hybrid_retrieval.py`
at `tools/search_mcp.py:27-42`) rather than a package. No `tools/` subpackage with `__init__.py`
exists anywhere today. This is precedent only — module layout is explicitly deferred to this
ticket's own Plan phase per the ticket's Assumptions/Open Questions.

**Graphify call shape already has a working precedent** —
`tools/agent-monitoring/kgmcp_baseline_runner.py:92-114`, `_run_graphify(query_text)`:
```python
proc = subprocess.run(
    ["graphify", "query", query_text],
    cwd=str(_REPO_ROOT),
    capture_output=True,
    text=True,
    timeout=120,
)
```
List-form `subprocess.run` args (no `shell=True`, no string interpolation) — no shell-injection
surface. `timeout=120` is a **caller-side** safeguard, not a provider capability: both
`provider_capabilities_graphify.json` and `provider_capabilities_context_search.json` declare
`"timeout": false` (the provider itself offers no bounded-latency guarantee), matching §8.1's own
routing-consequence rule: "A provider without cancellation must still be protected by the adapter's
process-level timeout." The router's symbol-name path should shell out identically to this
precedent, not build a new in-process Graphify adapter — confirmed no Python-callable Graphify
interface exists (`python3 -c "import graphify"` raises `ModuleNotFoundError`; only
`tools/graphify_to_html.py` touches `graph.json`, and only to render HTML, not to query).
`run_corpus()` (`kgmcp_baseline_runner.py:117-145`) calls Context Search and Graphify **sequentially
per entry**, not in parallel — there is no existing async/threading precedent in `tools/` for
concurrent provider calls, which matters for the ambiguous-intent "small bounded provider set,
queried in parallel" requirement (see Risks).

**`tools/search_mcp.py`'s own sibling, `tools/knowledge_search.py`**, and `tests/tools/test_search_mcp.py`
(15 tests) are the deterministic-fixture-test precedent this ticket's own tests should mirror in
shape (module import via spec/`importlib.util`, since `tools/` has no `__init__.py` making its
modules importable as a normal package).

## Mechanics / Engine Constraints

None apply. This is agent-orchestration/retrieval tooling, not simulation logic — same posture
`docs/engine/contracts/context_packet_contract.md` §4 already established, and the same judgment
the immediate prior sibling ticket (`TCK-20260814-KGMCP-CONTRACT-SCHEMAS`) recorded for this doc
family. No `docs/mechanics/` chapter or `docs/engine/` runtime contract (kernel, pipeline, combat,
economy) constrains a query router.

The one **frozen contract that does constrain this ticket** is §8.1's own rule, restated in
`docs/engine/contracts/knowledge_gateway_mcp_contract.md` §2: "The router must never claim a
capability the descriptor does not advertise." Concretely: both populated descriptors currently
declare `cancellation: false`, `timeout: false`, `negative_knowledge_support: "NONE"`,
`historical_queries: false`; Graphify declares `deterministic_relationships: "PARTIAL"` (mixed
`EXTRACTED`/`INFERRED` edges — "Inferred Graphify relationships cannot satisfy a deterministic-only
request" per §8.1) while Context Search declares `deterministic_relationships: "NONE"`. Both declare
`stable_entity_ids: "PARTIAL"` (neither is `"FULL"` — cross-rebuild ID stability was never verified
for either provider). This directly affects the symbol/dependency-path routing row: Graphify is the
correct primary for it, but its own `PARTIAL` deterministic_relationships means a request that
specifically needs `FULL` deterministic guarantees cannot be honestly satisfied by either current
provider — the router must surface that as a capability constraint, not silently claim success.

## Docs Requiring Update

- `docs/engine/contracts/knowledge_gateway_mcp_contract.md`: §2 currently states
  `capability_allows()` is "test-only... no router exists yet to own it" (line 61-63). Once this
  ticket adds a real router, that statement becomes inaccurate and must be updated to point at the
  real `tools/` implementation (exact module path is this ticket's own Plan decision).
- `docs/parity_ledger/infrastructure.yaml`: needs a new `INFRA-*` entry once this ticket's code
  lands and its Parity phase runs, following the `INFRA-334` precedent
  (`TCK-20260814-KGMCP-MEASUREMENT-BASELINE` — "this ticket adds real, testable Python code... follows
  the INFRA-281 through INFRA-333 agent-tooling-infrastructure precedent for ledgering this class of
  change"). This router ticket is the same class of change (real, testable `tools/` Python code from
  the KGMCP epic) and should get its own entry rather than being folded into INFRA-334's, which is
  scoped specifically to the measurement-baseline corpus/runner.

`docs/plans/knowledge-gateway-mcp-proposal.md` §20's Phase 1 checklist is **not** listed above:
its immediate KGMCP sibling ticket explicitly treated cross-referencing §20 as "not edited by this
ticket... optional follow-up," and no sibling ticket in this epic has broken that precedent. Router
code satisfies §20's "deterministic routing" bullet in substance; marking the epic-level checklist
is the epic ticket's concern, not this child ticket's.

## Parity Ledger Overlap

None currently exists for a query router — confirmed by direct grep of all 9
`docs/parity_ledger/*.yaml` shards for "router", "routing", "kgmcp", "gateway": the only hits are
unrelated (`adventure_routing`/`ENABLE_ADVENTURE_ROUTING` domain-flag entries in
`strategic_cognition.yaml`/`infrastructure.yaml`, and an unrelated API router mention in
`infrastructure.yaml:2550`). `INFRA-334` (`infrastructure.yaml:8598-8613`, status `verified`,
priority `P2`) is the directly applicable **precedent pattern**, not an overlap — it is the only
existing ledger entry for a KGMCP-epic ticket that shipped real code, and this ticket's own eventual
Parity phase should follow its shape (`status: verified`, `v2_evidence` citing `file:line`,
`test_path` citing the real scoped pytest command). No `P0` entries are implicated.

## Prior Work

- `stored_artifacts/TCK-20260814-KGMCP-CONTRACT-SCHEMAS/` (investigation.md, plan.md, test_plan.md)
  — froze `provider_capabilities.schema.json` and both populated instances this ticket consumes;
  its investigation.md is the source of the `tools/search_mcp.py`/Graphify capability grounding
  reused above.
- `docs/engine/contracts/knowledge_gateway_mcp_contract.md` — §1-§4 (adapter invocation contract,
  descriptor semantics, evidence for populated values, Design Decision D1 on Graphify being
  CLI-shelled not in-process) is the direct design precedent this ticket must stay consistent with.
- `stored_artifacts/TCK-20260814-KGMCP-MEASUREMENT-BASELINE/` — `tools/agent-monitoring/
  kgmcp_baseline_corpus.py` (`CORPUS_VERSION = 1`, `ROUTING_SHAPES` — the 7 canonical routing-shape
  IDs matching proposal §8's table exactly, `USE_CASES` — 5 canonical IDs matching §22) and
  `kgmcp_baseline_runner.py` (`_run_graphify`, `_run_context_search`, `run_corpus`) are real,
  tested precedent for both the routing-shape vocabulary and the Graphify call shape. Note: current
  `docs/REGISTRY.yaml`'s `related_code_areas` for this ticket lists `retrieval_baseline_metrics.py`/
  `generate_retro.py` (older, Aug 14 files) rather than `kgmcp_baseline_corpus.py`/
  `kgmcp_baseline_runner.py` (newer, Aug 15 files this ticket's own prompt named directly) — the
  registry entry appears to predate a later addition to the same ticket's working tree; this
  investigation cites the real, current files directly rather than trusting the registry's stale
  listing for this one ticket.
- `TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE1-EPIC` (parent, OPEN) — Phase 1 scope confirms
  deterministic routing is this phase's first deliverable and explicitly excludes model-based
  classification, caching, and Parity Ledger routing, consistent with this ticket's own Out of
  Scope.
- `tools/agent-monitoring/kgmcp_baseline_corpus.py:23-33` — the exact 7 `ROUTING_SHAPES` string IDs
  (`definition_terminology_architecture`, `symbol_lookup_callers_references`,
  `requirement_completeness_verification`, `ticket_historical_rationale`, `test_impact_of_change`,
  `ticket_work_status`, `broad_task_context`) already exist as a tested, versioned vocabulary for
  the 7 routing-table rows — this ticket's router should reuse these IDs rather than invent new
  names for the same 7 shapes, to keep the epic's baseline corpus and the real router speaking the
  same vocabulary.

## Risks and Open Questions

- **Parity-ID shape vs. membership.** All 2017 current parity IDs across the 9 `docs/parity_ledger/
  *.yaml` shards match the general shape `^[A-Z]+(-[A-Z]+)*-[0-9]+$` (confirmed by direct
  extraction — prefixes are far more varied than `INFRA-\d+`: `COMB`, `FAC`, `FACTION-TENSION`,
  `INFRA`, `INFRA-PACK`, `INFRA-TYPE`, `SIMQ-CALIBRATED`, `PROG`, `SOC`, `SOC-ABAND-TYPE`,
  `SOC-CHRON`, `SOC-CROSS-EP`, `SOC-FAC`, `FACTION-DIR`, `STRAT`, `SUB`, `SUBSTRATE-NEW`, `TOWN`,
  `WORLD`, `WORLD-CULT`, `WORLD-DEMO`). A hardcoded prefix enumeration would be fragile against
  future shards adding new prefixes. Open question for Plan: shape-only regex match (permissive,
  risks false positives on unrelated hyphenated-uppercase strings) vs. full membership check against
  the actual loaded ID set from all 9 shards (accurate, requires loading parity YAML at router
  init/call time). This investigation does not assume an answer — flagging for Plan.
- **Legacy non-`TCK-` ticket names.** `tickets/done/` contains pre-convention ticket files (e.g.
  `adjust-01-action-speed-balance.md`, `adventure-cognition-merge`) that will not match the
  `TCK-YYYYMMDD-SHORT-SCOPE` pattern. This is expected, not a gap: the ticket's own scope says
  "ticket IDs (`TCK-YYYYMMDD-*`)" — the router is not meant to be a full ticket index, only to
  recognize the current, live convention; free text otherwise falls through to Context Search.
- **Source-path check has no branch-awareness.** Both provider capability descriptors declare
  `branch_awareness: "NONE"`, and the sibling evidence-cache-identity contract treats branch/
  working-tree scoping as the gateway's responsibility, not the provider's. A plain
  `Path.exists()` check answers "does this exist in the current working tree," not "in git HEAD" —
  reasonable default, but Plan should confirm this is the intended semantics rather than this
  investigation assuming it silently.
- **Parallel ambiguous-intent fallback has no existing concurrency precedent.** The only existing
  multi-provider caller (`kgmcp_baseline_runner.py::run_corpus`) calls Context Search then Graphify
  **sequentially**, not in parallel. The ticket's acceptance criteria require the ambiguous-intent
  fallback to "query a small bounded provider set in parallel" — Plan must pick a concurrency
  mechanism (e.g. `concurrent.futures.ThreadPoolExecutor`, since both provider calls are
  I/O/subprocess-bound) since none exists in this codebase today to copy.
- **`capability_allows()` duplication.** The test file's own helper is explicitly documented as a
  stand-in until a router exists. Once this ticket adds the real implementation, Plan should decide
  whether the existing test (`test_capability_allows_rejects_unadvertised_cancellation_and_timeout`,
  `tests/tools/test_knowledge_gateway_contract_schemas.py:296-300`) should import and reuse the real
  function (retiring its local copy) or remain an independent contract-level assertion — either is
  defensible, but the decision should be explicit, not accidental drift.

## Anti-Drift Hazards

- **Zero MCP server code.** `.mcp.json`'s `mcpServers` keys are asserted by
  `test_no_live_gateway_tool_code_or_mcp_registration_introduced`
  (`tests/tools/test_knowledge_gateway_contract_schemas.py:338-349`) to be exactly
  `{"knowledge-search", "github"}` — this ticket must not add an entry. The same test also asserts
  no top-level `tools/*.py` file defines `def knowledge_context(` or `def knowledge_status(` (glob
  is **non-recursive**, so a `tools/knowledge_gateway/` subpackage would not even be scanned by it
  — worth Plan's awareness either way, since the router must not define those two names regardless
  of where it lives).
- **Zero packet-assembly code, zero cache code** — explicit ticket Out of Scope; do not reach into
  `tools/context_packet_assembler.py` or `tools/retrieval_cache.py` shapes even though they are
  nearby and tempting reuse targets.
- **Requirement-completeness row must not silently drop to Context Search.** The ticket's own scope
  requires an explicit "Parity-Ledger-shaped intent... not-yet-routed marker" — a plain fallback to
  Context Search without that marker would look like correct routing but would actually be
  information loss (an agent asking a Parity-Ledger-shaped question would get a plausible-looking
  Context Search answer with no signal that the real authoritative source was skipped).
- **Never claim a capability a descriptor does not advertise** — both current descriptors have
  `cancellation: false`/`timeout: false`; router code that calls Graphify or Context Search must not
  assume it can cancel an in-flight call, and any timeout applied must be documented as the
  *caller's* process-level safeguard (mirroring `kgmcp_baseline_runner.py`'s `timeout=120`), not
  advertised as a provider guarantee.
- **No `shell=True`, no string-interpolated subprocess calls** — the symbol-name path shells out to
  a real CLI binary; must use list-form `subprocess.run(["graphify", "query", query_text], ...)`
  exactly as the existing precedent does, never `f"graphify query {query_text}"` through a shell.

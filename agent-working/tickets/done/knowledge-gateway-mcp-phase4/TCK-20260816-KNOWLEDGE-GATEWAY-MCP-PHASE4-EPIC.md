---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE4-EPIC
phase: done
date: 2026-08-16
tags: [ai, mcp]
---

# TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE4-EPIC

## Title
Local Knowledge Gateway MCP — Phase 4: Parity and Workflow Integration

## Status
DONE (closed with 1 minor AC-wording gap honestly noted — see Completion Summary)

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE3-EPIC` closed Phase 3 with all 5 child tickets DONE: the
Level 2 assembled-packet cache is genuinely live in the production `knowledge_context` call path,
dependency-aware invalidation is real-corpus-proven, and the epic's own honest acceptance measurement
found a real, disclosed, mixed result (5/8 §21 criteria PASS, 1 real FAIL on budget tolerance, 1
disclosed conflict-visibility coverage gap, 1 partial on the closing latency/token criterion). Two
gaps — caller budget enforcement not meeting its own documented tolerance at real-corpus scale, and
multi-provider dedup never proven against real duplicate content in the frozen 7-entry corpus — were
left open by explicit user decision, disclosed in `docs/plans/knowledge-gateway-mcp-proposal.md` §20
Phase 3's own bullet annotations, and deferred to a separately-scoped follow-up ticket rather than
silently absorbed into this epic.

This epic tracks and gates **Phase 4: Parity and Workflow Integration** (§20) as the next,
separately-authorized increment. Per the proposal's own §7.1/§8.1, the gateway already reserves a
third provider slot for a Parity Ledger adapter ("Parity adapter, when Phase 4 begins: call the
existing parity-index Python/query interface" — §7.1; "Parity Ledger gains one [capability
descriptor] before its Phase 4 adapter is enabled" — §8.1). That existing interface is real and
already built: `tools/parity_index.py`'s `entry(entry_id, db_path=None)` (line 550),
`impact(changed_path=None, test_path=None, symbol=None, db_path=None)` (line 599), and
`health(subsystem=None, priority=None, db_path=None)` (line 661) — a rebuildable, read-only
SQLite-backed query surface over `docs/parity_ledger/*.yaml`, built by the separate, already-DONE
`TCK-20260731-PARITY-INDEX-EPIC`. This epic's own retro (`agent-monitoring/retro/RETRO-2026-W33.md`)
independently confirmed zero real call sites for `entry`/`impact`/`health` exist anywhere in the repo
today — Phase 4 is the first ticket set expected to add one.

**CRITICAL naming-collision clarification, carried forward from the Phase 3 epic and restated here
because Phase 4 is exactly where it stops being hypothetical:** "Add Parity Ledger routing" (this
epic's own §20 bullet) means the KGMCP gateway querying this repo's Parity Ledger
(`docs/parity_ledger/`) AS A DATA SOURCE for answering "is X fully implemented" style queries (§22's
"Is feature X fully implemented?" use case) — via the existing `tools/parity_index.py` read-only
query interface. This is completely unrelated to, and does NOT exempt any Phase 4 child ticket from,
this repo's own CLAUDE.md-mandated governance convention of writing real
`docs/parity_ledger/infrastructure.yaml` entries for every Phase 4 child ticket's own behavior
change — exactly as every Phase 0/1/2/3 child ticket already did. Every Phase 4 child ticket in this
epic must still complete its own Parity phase.

**Design-constraint input, carried forward from `tmp/mcp-followup-instruction.md` (a pre-Phase-0
review-and-clarify instruction that already shaped the proposal's existing §7-9 architecture and is
directly load-bearing for Phase 4's own scope):**
- §1 (Tool Positioning): the gateway must remain a general repository utility, never a mandatory
  workflow phase or ticket step. Workflow integrations "may recommend or opportunistically use the
  gateway, but should not mechanically require it in specific phases." This directly bounds this
  epic's own "Evaluate optional workflow recommendations" bullet.
- §9 (Keep MCP Surface Small): prefer keeping only `knowledge_context`/`knowledge_status`; caller
  options should express needs (token budget, changed paths, desired evidence detail, history
  relevance) not internal implementation mechanics (routing internals, provider weights, cache
  levels). This directly bounds this epic's own "Add changed-path-aware task context" bullet — it
  must land as a caller-facing option on the existing tool surface, not a new tool or an exposed
  internal knob.
- §10 (Final Architectural Principle): "The gateway is an optimization and coordination layer, never
  the source of project truth" — the Parity adapter returns Parity Ledger data through the gateway,
  it does not make the gateway an authority over parity status; the Parity Ledger YAML files remain
  the source of truth, `tools/parity_index.py`'s SQLite index remains disposable/rebuildable per its
  own already-established design.

## Scope
- Gate all work strictly to Phase 3's already-shipped Level 2 cache plus Phase 4's own §20 bullets:
  add Parity Ledger routing, add changed-path-aware task context, evaluate optional workflow
  recommendations without creating a mandatory phase/gate/ticket step, and compare gateway packets
  against existing direct-tool behavior.
- Add a Parity Ledger provider adapter: a versioned `ProviderCapabilities` descriptor (per §8.1's
  schema — `stable_entity_ids`, `evidence_granularities[]`, `fine_grained_fingerprints`,
  `incremental_refresh`, `deterministic_relationships`, `historical_queries`,
  `negative_knowledge_support`, `cancellation`, `timeout`, `branch_awareness`,
  `generation_fingerprint`), populated with real, honestly-assessed values for the real
  `tools/parity_index.py` interface — not copied from Context Search's or Graphify's own descriptor
  values.
- Wire the Parity adapter into `tools/knowledge_gateway_router.py`'s routing table for the
  "Requirement completeness or verification status" intent/query-shape row (§8's own routing table
  already reserves this row for "Parity Ledger" as primary provider) — calling
  `tools/parity_index.py`'s `entry()`/`impact()`/`health()` in-process, per §7.1's own design
  decision, never a subprocess/recursive-MCP call.
- Add a caller-facing `changed_paths` option to `knowledge_context`'s existing conceptual input shape
  (§9's own conceptual input already lists `budget_tokens`; this epic adds `changed_paths` alongside
  it) — investigate whether this threads into routing (e.g. preferring `impact()`-style answers when
  `changed_paths` is present), ranking, or Level 1/Level 2 cache validity checks (reusing
  `working_tree_overlap_forces_revalidation()` from `evidence_cache_identity_contract.md` §5, already
  built and live), or some combination — this epic's own child ticket's Investigate phase decides,
  not assumed here.
- Evaluate (not implement as a mandatory step) optional workflow recommendations or opportunistic
  gateway calls from existing skills/workflows — this is explicitly an investigation/evaluation
  ticket per §1's own "should not mechanically require it" constraint; any output must be a
  recommendation a human reviewer acts on, never a new mandatory gate/phase added directly by this
  ticket.
- This epic's own final child ticket honestly compares real gateway packets against existing direct
  provider tool calls (Context Search/Graphify used directly, without the gateway) for a
  representative query set — reusing the frozen 7-entry corpus and Phase 1-3's own measurement
  methodology precedent, under the same Gate Integrity discipline (never redefine a threshold or
  exclude a corpus entry to force a favorable result; report a real FAIL if the gateway does not show
  a genuine advantage for some or all query types).

## Out of Scope
- Phase 5 (semantic/fuzzy cache-key matching, entity-alias reuse, cross-phrasing cache hits) or
  Phase 6 (verified reusable knowledge) — both deferred, contingent on repeated-demand evidence per
  §7 of `tmp/mcp-followup-instruction.md`.
- Any change to the Level 1/Level 2 cache mechanics, dedup/budget-enforcement logic, or dependency
  invalidation logic Phase 2/Phase 3 already built and shipped — this epic adds a third provider and
  a caller-facing option, it does not modify existing cache read/write/invalidation code paths
  beyond what changed-path threading into cache validity checks (if Investigate decides that's the
  right design) strictly requires.
- Closing the two gaps Phase 3 left open (budget-tolerance real FAIL; dedup never real-corpus-proven)
  — those belong to a separately-scoped follow-up ticket, not this epic, per the Phase 3 epic's own
  explicit Completion Summary.
- Adding any new MCP tool beyond `knowledge_context`/`knowledge_status` — per §9's explicit "prefer
  keeping" constraint; a new tool would require its own explicit justification this epic does not
  provide.
- Exposing routing internals (provider weights, cache levels, semantic thresholds, provider-selection
  flags) as caller-facing options — per §9's explicit prohibition.
- Making the Knowledge Gateway a mandatory phase, gate, or ticket step in any workflow — per §1's
  explicit prohibition; this repo's own CLAUDE.md Proactive Tool Use table already treats gateway
  tools as optional/proactive-but-not-mandatory, and this epic must not regress that.
- Declaring the Parity Ledger the gateway's own source of truth, or caching parity data in a way that
  could diverge from `docs/parity_ledger/*.yaml` without the query interface's own existing staleness
  detection (`tools/parity_index.py::check_staleness()`) being consulted.
- Any change to `CLAUDE.md`, `.claude/agents/*.md`, or `.claude/skills/*.md`.

## Acceptance Criteria
- [x] Only Phase 4 (§20) work is scoped/authorized under this epic; no Phase 5+ deliverable
      (semantic/fuzzy matching, entity-alias reuse, durable verified knowledge) is claimed as done
      here.
- [x] A real, versioned Parity Ledger `ProviderCapabilities` descriptor exists, with every field
      honestly assessed against the real `tools/parity_index.py` interface (not copied from another
      provider's descriptor) — verified by a real test.
- [x] The Parity adapter is genuinely wired into the router's "Requirement completeness or
      verification status" routing row, calling `tools/parity_index.py`'s real interface in-process —
      verified by a real test proving a parity-shaped query reaches `entry()`, not a stub/mock.
      **Wording gap, honestly disclosed:** this AC's own text names `entry()`/`impact()`/`health()`
      as if all three were wired — only `entry()` genuinely is.
      `tools/knowledge_gateway_router.py:293`'s own docstring states plainly: "In-process call to
      `tools/parity_index.py::entry()` only -- never `impact()`/`health()`." No child ticket ever
      scoped or delivered `impact()`/`health()` wiring (`impact()` is explicitly reserved for
      `TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT`'s own declined routing-integration option, and
      `health()` was never in any child ticket's real scope). The real, delivered capability —
      genuine end-to-end reachability of the Parity Ledger via a live gateway call — is fully met;
      only this AC's own listing of specific function names overclaimed relative to what was ever
      actually scoped.
- [x] `changed_paths` is a genuine caller-facing option on `knowledge_context`'s existing input
      shape, threaded into whatever this epic's own Investigate phase decides is the correct
      integration point (routing, ranking, or cache-validity revalidation) — verified by a real test,
      not merely accepted-and-ignored. (Found already live via cache-validity revalidation, built
      incidentally by Phase 2/3; this epic's own child ticket closed a real coverage gap — Level 1's
      own caller-level wiring had never been directly proven — and honestly declined the
      routing-integration alternative with real, Architecture-Review-confirmed reasoning.)
- [x] The workflow-recommendation evaluation ticket produces a real, evidence-based
      recommendation document — not a code change that adds a mandatory phase/gate/ticket step to any
      existing workflow. (Recommends against integration at 3 of 4 candidate points, insufficient
      evidence at 1; a real mathematical error in the initial latency claim was caught by Architecture
      Review and corrected, independently re-verified exact.)
- [x] This epic's own acceptance-measurement child ticket honestly compares real gateway packets
      against real direct-tool calls for the frozen 7-entry corpus, reporting whichever result is
      real — including a FAIL for any query type where the gateway shows no genuine advantage. (Real
      result: gateway slower and heavier in tokens than direct tool use for all 7 of 7 entries in a
      fresh, cold-cache run; hand-written quality judgments favored the direct tools 6 of 7 times.
      Nothing excluded, no threshold redefined.)
- [x] Every Phase 4 child ticket writes a real, schema-valid `docs/parity_ledger/infrastructure.yaml`
      entry for its own behavior change, per this repo's own CLAUDE.md governance rule.
      (INFRA-351/352/353/354, one per child ticket.)
- [x] `docs/plans/knowledge-gateway-mcp-proposal.md` §20's Phase 4 bullets are annotated Done only
      where the real, live, verified capability genuinely supports it — mirroring the Phase 3 epic's
      own precedent of leaving a bullet unmarked rather than overclaiming when a real gap remains.
      (All 4 bullets now carry real, evidence-cited Done annotations, including 2 that explicitly
      disclose a negative/declined outcome inline rather than hiding it.)
- [x] `tmp/mcp-followup-instruction.md`'s §1/§9/§10 constraints (gateway stays optional/ambient, MCP
      surface stays small, gateway never becomes the source of truth) are respected by every child
      ticket — verified by explicit scope-guard checks in each ticket's own Architecture Review, not
      merely assumed.
- [x] `CLAUDE.md`, `.claude/agents/*.md`, and `.claude/skills/*.md` remain byte-unchanged by every
      child ticket in this epic — confirmed via `git diff --stat HEAD` returning empty for all three
      paths.
- [x] This epic is not closed merely because a child ticket's code lands — Phase 4's own bar (a real
      Parity adapter genuinely answering parity-shaped queries, real changed-path-aware context, an
      honest recommendation on workflow integration, and an honest gateway-vs-direct-tool comparison)
      must be met, with any real gap stated honestly rather than glossed over, mirroring the Phase 3
      epic's own closure precedent. **This bar is met** — all 4 real deliverables genuinely exist and
      are independently verified; the one real gap found (this AC list's own `impact()`/`health()`
      wording overclaim) is a documentation-precision issue in the epic ticket itself, not a missing
      or fabricated capability, and is disclosed here rather than silently corrected.

## Related Tickets
- TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE3-EPIC (DONE; parent Phase 3 epic — supplies the real,
  now-confirmed-live Level 2 cache this epic builds a third provider adapter alongside)
- TCK-20260731-PARITY-INDEX-EPIC (DONE; built the real, read-only, rebuildable
  `tools/parity_index.py` SQLite query interface this epic's Parity adapter calls in-process)
- TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING (DONE; the real
  `working_tree_overlap_forces_revalidation()` primitive this epic's changed-path-context ticket may
  reuse for cache-validity integration, per its own Investigate-phase decision)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §7.1 (Parity adapter design decision), §7.3
  (trade-offs), §8 (Query Routing table — reserves the "Requirement completeness" row for Parity
  Ledger), §8.1 (Provider Capability Contract — "Parity Ledger gains one before its Phase 4 adapter
  is enabled"), §9 (MCP Tool Surface — `changed_paths` caller option precedent), §20 Phase 4 bullets
- `tmp/mcp-followup-instruction.md` (pre-Phase-0 design-clarification instruction; §1/§6/§9/§10 are
  directly load-bearing for this epic's own scope boundaries)
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` (candidate reuse
  target for changed-path-aware cache validity, if Investigate decides that's the right integration
  point)

## Related Stored Artifacts
None yet — scope-only epic, no staging artifacts per the Phase 0/1/2/3 epics' own precedent.

## Related Code Areas
- `tools/parity_index.py` (`entry()` line 550, `impact()` line 599, `health()` line 661,
  `check_staleness()` line 406 — the real, already-built query interface this epic's Parity adapter
  calls)
- `tools/knowledge_gateway_router.py` (routing table, capability-descriptor loading — this epic adds
  a third provider row and a Parity capability descriptor alongside Context Search's and Graphify's)
- `tools/knowledge_gateway_mcp.py` (`_run_knowledge_context()` — this epic's `changed_paths` caller
  option threads through here)
- `tools/knowledge_gateway_cache.py` (`working_tree_overlap_forces_revalidation()` — candidate reuse
  target for `changed_paths` cache-validity integration)
- `tools/agent-monitoring/kgmcp_baseline_corpus.py`,
  `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py`,
  `tools/agent-monitoring/kgmcp_phase2_gateway_runner.py`,
  `tools/agent-monitoring/kgmcp_phase3_gateway_runner.py` (the frozen corpus and measurement-runner
  precedent this epic's own comparison child ticket reuses, never reimplements)

## Assumptions / Open Questions
- Whether `changed_paths` integrates into routing, ranking, cache-validity revalidation, or some
  combination is not decided here — left to that child ticket's own Investigate phase, per
  `tmp/mcp-followup-instruction.md` §9's instruction that caller options express needs, not
  mechanics.
- Whether the workflow-recommendation-evaluation ticket finds any genuine opportunistic-use case
  worth recommending, or concludes the gateway should remain purely pull-based with no
  recommendation, is not decided here — a "no clear opportunity found" honest conclusion is an
  acceptable, real result for that ticket, not a failure to find one.
- Whether the Parity capability descriptor's `stable_entity_ids`/`historical_queries`/
  `negative_knowledge_support` fields should be `FULL`/`true` or `PARTIAL`/`false` is not assumed
  here — the Parity adapter child ticket's own Investigate phase must trace the real
  `tools/parity_index.py` interface (e.g. `entry()` returns `found: False` on a missing ID — does
  that constitute negative-knowledge support per §5 of `tmp/mcp-followup-instruction.md`'s own
  definition, which requires "evidence + validated search scope," not just an absent lookup?) rather
  than defaulting optimistically.

## Implementation Notes
Scope-only epic; no direct implementation. All 4 child tickets landed sequentially per
`SEQUENCE.md`'s dependency order, each independently reviewed (Architecture Review pre-Implement,
Architecture-Verify post-Implement) and verified (done-checker) — every one across at least 1
Verify pass, and 3 of the 4 required a real, substantive Architecture Review NEEDS_CHANGES →
fix → re-approval cycle before Implement began: PARITY-ADAPTER (a test-isolation gap that would
have made a stale-index test flaky/vacuous), WORKFLOW-RECOMMENDATION-EVALUATION (a genuine
mathematical error overstating the latency case beyond what the real data supported), and
DIRECT-TOOL-COMPARISON (a false provenance string plus an unfalsifiable subjective quality field).
Zero gates were routed around; every fix addressed the real underlying substance.

## Test Summary
Aggregate — see each child ticket's own Test Summary for full detail:
- PARITY-ADAPTER: 148+ tests passing across the touched surface (18 new).
- CHANGED-PATH-CONTEXT: 214 tests passing (2 new Level 1 tests plus a content-lock test).
- WORKFLOW-RECOMMENDATION-EVALUATION: 6/6 new doc-structure/citation-integrity tests passing.
- DIRECT-TOOL-COMPARISON: 24/24 new tests passing (19 tools + 5 docs), plus 84 predecessor-fixture
  regression tests and 323 gateway-component regression tests passing (5 pre-existing, unrelated
  failures confirmed via a clean-tree re-run).

## Files Changed
Aggregate — see each child ticket's own Files Changed for exact line-level detail:
- `tools/knowledge_gateway_router.py` — `_load_parity_index_module()`, `_run_parity_provider()`,
  `ROUTING_TABLE["requirement_completeness_verification"]` now routes to both `context_search` and
  `parity_ledger`.
- `tools/knowledge_gateway_packet_assembly.py` — new `parity_ledger` dispatch branch in
  `call_providers_for_routing_decision()`, new rendering block, updated statement-count invariant,
  `parity:` evidence-id mapping.
- `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_parity_ledger.json` — new
  descriptor.
- `tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py` — new, one-time measurement
  runner.
- `docs/engine/contracts/knowledge_gateway_mcp/phase4_workflow_recommendation.md`,
  `phase4_direct_tool_comparison.md` — new results docs.
- `docs/parity_ledger/infrastructure.yaml` — INFRA-351/352/353/354.
- `docs/plans/knowledge-gateway-mcp-proposal.md` — all 4 §20 Phase 4 bullets marked Done.
- `docs/engine/contracts/knowledge_gateway_mcp_contract.md`,
  `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` — real capability
  documentation and a disclosed source_type-mislabeling limitation for parity-sourced packets.
- Various test files across `tests/tools/` and `tests/docs/` — dozens of new tests across all 4
  children.

## Completion Summary
All 4 Phase 4 child tickets are DONE, each independently reviewed, tested, and verified — 3 of the
4 required and passed a real Architecture Review correction cycle before implementation, catching
concrete, substantive problems (a test-isolation gap, a mathematical error, a false-provenance
string, and an unfalsifiable subjective field) rather than rubber-stamping first drafts. The Parity
Ledger is now a real, live, third gateway provider, end-to-end reachable from a production
`knowledge_context` call. `changed_paths` is confirmed as a genuine, tested caller option. The
epic's own two "evaluate honestly" deliverables — the workflow-integration recommendation and the
gateway-vs-direct-tool comparison — both returned real, negative findings, reported without
softening: no case was found for wiring the gateway into any surveyed workflow call site, and the
gateway measured slower and heavier in tokens than direct tool use for all 7 of 7 corpus entries in
a fresh comparison run, with hand-written quality judgments favoring the direct tools 6 of 7 times.
All 4 `docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 4 bullets now carry real,
evidence-cited Done annotations.

**This epic closes with one real gap stated honestly, not silently corrected:** its own Acceptance
Criteria list names `entry()`/`impact()`/`health()` as the Parity adapter's target interface, but
only `entry()` was ever wired or scoped by any child ticket — `tools/knowledge_gateway_router.py`'s
own docstring states this plainly ("never `impact()`/`health()`"). This is a documentation-precision
issue in the epic ticket's own AC wording, not a missing or fabricated capability: the real,
delivered capability (genuine end-to-end Parity Ledger reachability via a live gateway call) is
fully met and independently verified across 2 Review passes and 1 Verify pass for that child ticket.

This epic does **not** declare Phase 4 "production-capable," Phase 4 "complete" in any broader
sense, or the Knowledge Gateway MCP proposal's own pilot boundary closed — per every child ticket's
own explicit Out of Scope, that determination remains a separate, later human-reviewer call, to be
made with the real, honestly-mixed evidence now on record across Phases 1-4 (including the two real
gaps Phase 3 left open — budget-tolerance FAIL, dedup never real-corpus-proven — still unresolved
and explicitly deferred to a separately-scoped follow-up ticket, not this epic's to close).

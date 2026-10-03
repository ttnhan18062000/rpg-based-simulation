---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260729-CONTEXT-PACKET-ASSEMBLY
phase: done
date: 2026-07-28
tags: [ai, schema]
---

# TCK-20260729-CONTEXT-PACKET-ASSEMBLY

## Title
Assemble real ContextPacket from fused/cached retrieval results

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Assemble an actual ContextPacket per the Phase 2 schema from C1's fused retrieval results and C3's cached results, with real included[]/excluded_summary[] population, proving the schema is buildable from real data -- read-only, standalone, never wired into any workflow. Because this ticket consumes the actual return-value shapes of the fusion module (C1) and the cache module (C3), neither of which exists yet, it is hard-blocked on both and must be sequenced strictly last in this batch.

## Scope
- Build a new ContextPacket assembler module that consumes C1's fused retrieval results and C3's cached results and populates included[]/excluded_summary[] per the Phase 2 schema.
- Implement Decision A: code_symbol/test/graphify_node/in-progress-ticket-body kinds get authority=freshness='unrated' sentinel, never defaulted to P2/historical; parity_ledger_entry kind uses its own priority/status fields, never coerced into the REGISTRY enum.
- Implement Decision B: when two included[] entries are both active/authoritative on the same subject, both must be included (never silently dropped), ranked by authority then last_verified, with the lower-ranked entry's inclusion_reason naming the superseding entry.
- Construct/extend real test fixtures mixing REGISTRY-backed and non-registry-backed source kinds, since no such fixture currently exists.
- Stub expansion_policy as a clearly-marked placeholder field, not invented escalation semantics, since Open Decisions 5/6 remain deferred.
- Keep the module read-only and standalone -- must NOT be wired into or referenced from any .claude/workflows/*.js file.

## Out of Scope
- Implementing C1's fusion logic or C3's cache logic itself -- this ticket consumes their output only, does not reimplement them.
- Any new agent-monitoring/*.jsonl event type (Phase 4).
- Shadow packets, workflow adoption, or any .claude/workflows/*.js wiring (Phase 5-6).
- Any external vector/graph DB (Qdrant/Postgres/Neo4j/hosted RAG).
- Any lightweight re-ranker beyond fusion+metadata filtering.
- Force-resolving Open Decisions 5 or 6 (expansion_policy stays a stub).

## Acceptance Criteria
- [x] A candidate set with a code_symbol entry with no REGISTRY entry produces an included[] item with authority=="unrated" and freshness=="unrated".
- [x] Two candidate docs both status:active on the same subject (one P0, one P1) produce BOTH in included[]; the P1 entry's inclusion_reason names the P0 entry's source_id as superseding.
- [x] Every included[] entry has exactly the 10 contract fields; every excluded_summary[] entry has exactly the 4 contract fields; unit-tested against a fixture.
- [x] Assembled packet never contains raw prompt/chunk text in any field.
- [x] Module is not imported by/referenced from any .claude/workflows/ file; grep-based regression test asserts zero references.

## Related Tickets
- TCK-20260728-CONTEXT-PACKET-SCHEMA
- TCK-20260728-CODE-TEST-INDEX-BOUNDARIES
- TCK-20260728-RETRIEVAL-RETENTION-REDACTION
- TCK-20260728-DEFAULT-PACKET-CRITERIA
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
- TCK-20260729-HYBRID-RETRIEVAL-FUSION
- TCK-20260729-RETRIEVAL-CACHE-LEVELS

## Related Docs
- docs/engine/contracts/context_packet_contract.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase3.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/knowledge_search.py
- tools/agent-monitoring/build_index.py
- tools/eval_search.py
- tools/eval/queries.json
- tools/validate_frontmatter.py
- tests/tools/test_knowledge_search.py
- tests/tools/test_eval_search.py
- expected: tools/context_packet_assembler.py
- expected: tests/tools/test_context_packet_assembler.py

## Assumptions / Open Questions
- Hard blocking dependency on C1 (fusion) and C3 (cache) -- neither exists yet at ticket-creation time; this ticket must be sequenced strictly after both land, per SEQUENCE.md ordering.
- Decision B's tie-break rule is advisory/doc-only guidance today; this ticket's test suite is the only place it becomes concretely verifiable -- ACs must test it directly or the Phase 2 schema resolution remains unproven by real code.
- expansion_policy is a listed ContextPacket field with no resolved definition anywhere (Open Decisions 5/6 both deferred) -- must stub with a clearly-marked placeholder.
- No fixture corpus currently mixes REGISTRY-backed and non-registry-backed source kinds -- nontrivial new fixture-authoring work is required.

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260729-CONTEXT-PACKET-ASSEMBLY/plan.md`'s 10 ordered
steps, no deviations.

- `tools/context_packet_assembler.py` (new): `Candidate` frozen dataclass (no raw-text field —
  the structural AC4 guarantee) and `ContextPacket` frozen dataclass (`included`/
  `excluded_summary` as plain dicts). `_hash_content()` mirrors `retrieval_cache.py`'s
  `sha256(...).hexdigest()` convention inline (str -> encode; dict/list ->
  `json.dumps(..., sort_keys=True)`), never importing that module's private `_hash_text`.
  `UNRATED` imported from `hybrid_retrieval` (never re-literaled). `EXPANSION_POLICY_STUB` is a
  plain marker string citing Open Decisions 5/6, never a dict/object.
- `unrated_candidate()` — one shared kind-parametric builder implementing Decision A's
  "code_symbol/test/graphify_node/in-progress-ticket-body get `unrated`" rule for any kind
  value. `candidate_from_code_index_record()` adapts a `code_test_index.py::build_records()`
  dict into a `code_symbol` candidate through it (AC1).
- `candidate_from_hybrid_result()` maps `HybridResult` -> `Candidate`, passing `authority`/
  `freshness` through verbatim (already resolved by C1's `resolve_metadata()`) and resolving
  `last_verified` from a caller-supplied `registry_index` dict. `hash` is computed once from
  `result.text`, which is never otherwise referenced.
- `_resolve_subject_conflicts()` implements Decision B: groups candidates by explicit
  caller-supplied `subject_key` (never auto-derived), keeps only `active`/`authoritative`
  candidates, ranks via a two-pass stable sort (`last_verified` descending — missing sorts last
  as `""` — then `authority` ascending), and returns `{source_id: inclusion_reason}` for every
  candidate in a qualifying group (winner gets `"included"`, losers get
  `"superseded-by:<winner.source_id>"`). Never drops a candidate from `included[]` (AC2).
- `candidate_from_parity_ledger_fixture()` maps a hand-built parity-ledger-schema-shaped dict
  into a `parity_ledger_entry` candidate, using the entry's own `priority`/`status` verbatim as
  `authority`/`freshness` — no lookup against or coercion into REGISTRY's `AUTHORITY_VALUES`/
  `STATUS_VALUES` (Scope item 2, Decision A's parity branch). No live
  `docs/parity_ledger/*.yaml`-scanning ingestion path was built, per the plan.
  `build_included_entry()`/`build_excluded_summary()` produce dicts with exactly the contract's
  10/4 fields; `assemble_context_packet()` orchestrates all of the above (AC3).
- `tests/tools/test_context_packet_assembler.py` (new, 16 tests, all passing): covers AC1-AC5
  plus the Scope-mandated parity-branch and fixture-mixing tests named in the test plan, plus
  one supplementary edge-case test (`test_missing_last_verified_sorts_last_within_authority_tie`)
  exercising Resolved Decision 4's missing-`last_verified` fallback directly.
- `docs/parity_ledger/infrastructure.yaml`: appended `INFRA-296` after `INFRA-295`, following the
  `INFRA-293`/`294`/`295` format verbatim (`status: verified`, `priority: P2`, `support_boundary`
  wording matched).

One test-writing deviation from the AC5 guard test in `test_plan.md`'s literal description: the
static reverse-dependency check (`test_assembler_does_not_import_contextpacket_from_retrieval_cache`)
could not use a raw substring search for `"ContextPacket"` in `retrieval_cache.py`'s source,
because that module's own docstring/Anti-Drift Note text already legitimately contains the
string "ContextPacket" (documenting that it does *not* import it). The test instead AST-parses
`retrieval_cache.py` and asserts `"ContextPacket"` is not a defined class name and not an
imported name — the actual guard the test plan intended (no import/class definition), without
false-failing on prose that discusses the absence of that dependency. Recorded in the staging
plan's Deviations section.

## Test Summary
- `pytest tests/tools/test_context_packet_assembler.py -v` — 16 passed (all new tests: AC1-AC5,
  Scope item 2 parity-branch tests, fixture-mixing test, expansion_policy stub test, one
  supplementary Decision B missing-`last_verified` edge test).
- `pytest tests/tools/test_hybrid_retrieval.py tests/tools/test_retrieval_cache.py tests/tools/test_code_test_index.py -v` — 52 passed (sibling modules unmodified, input shapes unchanged).
- `pytest tests/tools/test_knowledge_search.py tests/tools/test_eval_search.py -m "not slow" -q` — 112 passed, 28 deselected (corpus/routing scope guards unaffected).
- `pytest tests/tools/test_parity_ledger_scan.py -q` — 3 passed (new `INFRA-296` entry validates against schema).
- Import smoke check (`from tools import context_packet_assembler as cpa`) confirmed clean
  module load with no import-time errors (Step 4's specified verification).

## Files Changed
- `tools/context_packet_assembler.py` (new)
- `tests/tools/test_context_packet_assembler.py` (new)
- `docs/parity_ledger/infrastructure.yaml` (appended `INFRA-296`)

## Completion Summary
Built `tools/context_packet_assembler.py`, a standalone, read-only module that assembles a real
`ContextPacket` (per `docs/engine/contracts/context_packet_contract.md` §2) from three
candidate-producing sources — `HybridResult` (C1), `code_test_index.py` records, and
`parity_ledger_entry` fixtures — normalizing all three into a text-free `Candidate` intermediate
that structurally cannot leak raw excerpt text, then builds `included[]`/`excluded_summary[]`
with exactly the contract's 10/4 fields. Implements Decision A's per-kind authority/freshness
rules and Decision B's include-both-and-rank conflict resolution with explicit `subject_key`
grouping. All 5 acceptance criteria are met and directly tested; the module is proven never
referenced from any `.claude/workflows/*.js` file (AC5's grep-based regression test), and never
modifies any of the three sibling modules it consumes. `expansion_policy` remains an explicit,
clearly-marked stub — Open Decisions 5/6 are not force-resolved. New `INFRA-296` parity ledger
entry appended following the `INFRA-293`-`295` precedent. Status: DONE.

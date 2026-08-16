---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE3-EPIC
phase: done
date: 2026-08-16
tags: [ai, mcp]
---

# TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE3-EPIC

## Title
Local Knowledge Gateway MCP — Phase 3: Context-Packet Cache and Token Budgets

## Status
DONE (closed with 2 of 4 §20 bullets honestly left open — see Completion Summary)

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE2-EPIC` closed Phase 2 with a genuinely dual finding: the
Level 1 provider-result cache mechanism is fully built, correctly gated through
`evaluate_write_candidate()`, and tested — but its acceptance-measurement child ticket
(`TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON`) honestly measured **0 of 7** real corpus queries
producing a genuine cache hit, because every real response payload (10.6–30.5 KB) exceeded the
deployed `MAX_PAYLOAD_BYTES = 8192` write-size cap. That miscalibration was not silently absorbed
into this epic; it was fixed separately and first, by
`TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION` (DONE), which raised
`MAX_PAYLOAD_BYTES` to `65536` — a data-derived value (2.15x the real observed max payload size,
not a round-number guess) — and re-ran the exact same measurement methodology, finding genuine
cache hits now occur **7/7** against the real corpus. Level 1 is confirmed to genuinely work before
this epic begins any Level 2 work on top of it.

This epic tracks and gates **Phase 3: Context-Packet Cache and Token Budgets** (§20) as the next,
separately-authorized increment: building proposal §10.2's "Level 2: Assembled context-packet
cache" — deduplicated multi-provider packets, real packet payload storage, real caller-budget
enforcement using measured output size, and packet dependency records with targeted invalidation —
on top of the now-confirmed-working Level 1 cache.

**Per the proposal's own §20 text, completion of Phase 3 is the first production-capable pilot
boundary.** Its provider set is Context Search plus Graphify; the Parity Ledger is explicitly not
required as a gateway data source until Phase 4. "Production-capable" here means an opt-in advisory
tool with an approved payload policy and passing acceptance tests (§21) — not mandatory workflow
use. §21's ~18 pilot acceptance criteria are the bar this epic's final child ticket must honestly
measure against; many are already satisfied by Phase 1/Phase 2 work (fail-open behavior,
evidence-validity/lookup-identity separation, branch-scope correctness, no-sensitive-content-
written). The genuinely NEW criteria this epic's own work must satisfy are: "Returned content
respects the requested budget within a documented tolerance," "Conflicts are visible and never
silently merged," and the closing criterion that evaluation reports lookup/validation/fallback/
assembly/end-to-end latency separately and demonstrates lower median end-to-end latency and fewer
delivered tokens for repeated representative queries without reducing authoritative-source recall.

**CRITICAL naming-collision clarification, stated explicitly here to prevent future confusion:**
proposal §20's Phase 4 bullet "Add Parity Ledger routing" refers to a DOMAIN concept — the KGMCP
gateway querying this repo's Parity Ledger (`docs/parity_ledger/`) AS A DATA SOURCE for answering
"is X fully implemented" style queries (§22's "Is feature X fully implemented?" use case). This is
completely unrelated to this repo's own CLAUDE.md-mandated governance convention of writing real
`docs/parity_ledger/infrastructure.yaml` entries for every behavior change. "Parity Ledger is not
required until Phase 4" means ONLY that the gateway itself does not need to query the Parity Ledger
as a routing source during Phase 3 — it does NOT exempt any Phase 3 child ticket from this repo's
own governance requirement to write real, schema-valid `infrastructure.yaml` parity entries for its
own code changes, exactly as every Phase 0/1/2 child ticket already did. Every Phase 3 child ticket
in this epic must still complete its own Parity phase.

## Scope
- Gate all work strictly to Phase 2's already-shipped Level 1 cache plus Phase 3's own §20 bullets:
  assemble deduplicated multi-provider packets, store and return actual packet payloads, enforce
  caller budgets using measured output size, and add packet dependency records with targeted
  invalidation.
- Build "Level 2: Assembled context-packet cache" per proposal §10.2, storing exactly the row shape
  §10.2 and §10.3's conceptual `CachedPacket` schema specify: answer/task summary, deduplicated
  context items, conflicts, complete evidence dependencies, routing plan, token budget and returned
  estimate, policy and schema versions, and scope/freshness metadata.
- Use `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md`'s already-reserved
  `migration_002_add_level2_tables(conn: sqlite3.Connection) -> None` as the pre-authorized
  migration ordinal/name for the new Level 2 schema — never a different ordinal, never a second
  database (same `knowledge-index/retrieval_cache.db` file per the plan's own design decision).
- Add a NEW real content-bearing table for the packet payload (name TBD by that child ticket's own
  Investigate phase, e.g. `retrieval_context_packet_cache_rows`) — the existing marker-only
  `retrieval_packet_cache_rows` table (from the separate, unrelated, BACKLOG-tier
  `TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC`) must remain completely untouched, mirroring
  exactly how Phase 2's schema ticket added `retrieval_provider_result_cache_rows` alongside the
  existing marker-only `retrieval_query_cache_rows` without modifying it.
- Investigate whether `evidence_cache_identity_contract.md` §5's branch/working-tree/`changed_paths`
  intersection logic can be reused or extended for packet-level dependency invalidation, rather than
  reinventing an equivalent mechanism at the packet layer.
- Wire real Level 2 cache lookup/write into the live `_run_knowledge_context()` call path: Level 2
  is checked first for an exact packet match; a Level 2 miss falls back to Level 1 (already-wired
  provider-result cache) or, on a further miss, live providers — this epic adds a layer, it does not
  redesign Phase 1/Phase 2's existing pipeline.
- This epic's own final child ticket honestly re-runs proposal §21's Phase 3 Pilot Acceptance
  Criteria against the real Level 2 cache-hit path, reusing the frozen 7-entry corpus
  (`tools/agent-monitoring/kgmcp_baseline_corpus.py`) and the Phase 1/Phase 2 measurement
  methodology precedent, under the same Gate Integrity discipline (never redefine a threshold or
  exclude a corpus entry to force a favorable result).

## Out of Scope
- Level 3 (verified reusable knowledge) per §10.2 — deferred to Phase 6, contingent on repeated-
  demand evidence.
- Any Phase 4 work: Parity Ledger routing as a gateway DATA SOURCE, changed-path-aware task context,
  optional workflow recommendations, or comparing gateway packets against existing direct-tool
  behavior. (This does NOT exempt Phase 3 child tickets from this repo's own
  `docs/parity_ledger/infrastructure.yaml` governance requirement — see the naming-collision
  clarification above.)
- Semantic/fuzzy cache-key matching, entity-alias reuse, or cross-phrasing cache hits (Phase 5).
- Any change to `tools/knowledge_gateway_router.py`'s routing decisions beyond what's needed to
  read from and write to the new Level 2 cache layer.
- Modifying the existing marker-only `retrieval_packet_cache_rows` table or any code path that
  reads/writes it today (owned by the separate, unrelated `TCK-20260728-CONTEXT-EFFICIENT-
  RETRIEVAL-EPIC`).
- A second cache database — migrations extend the existing `knowledge-index/retrieval_cache.db`
  file per `cache_migration_plan.md`'s own design decision.
- Reusing `migration_002` for anything other than the Level 2 tables it is already reserved for, or
  skipping/renumbering it.
- Silently assuming any of §21's Phase 3 pilot acceptance criteria pass without a real, honest
  measurement — if a threshold or criterion is missed, that must be reported honestly by this
  epic's own acceptance-measurement child ticket, exactly as Phase 1 and Phase 2 both did, not
  glossed over as "expected to improve."
- Any change to `CLAUDE.md`, `.claude/agents/*.md`, or `.claude/skills/*.md`.

## Acceptance Criteria
- [x] Only Phase 3 (§20) work is scoped/authorized under this epic; no Phase 4+ deliverable
      (Parity Ledger routing as a gateway data source, changed-path-aware task context, entity-alias
      reuse, durable verified knowledge) is claimed as done here.
- [x] The Level 2 schema and migration extend `knowledge-index/retrieval_cache.db` in place via
      `migration_002_add_level2_tables`, per `cache_migration_plan.md`'s already-reserved ordinal —
      no second database, no renumbering, no reuse of the ordinal for anything else.
- [x] The existing marker-only `retrieval_packet_cache_rows` table remains byte-for-byte unmodified
      by every child ticket in this epic — verified by a real test, not merely asserted
      (`tests/tools/test_retrieval_cache.py`, multiple assertions distinguishing it from
      `retrieval_context_packet_cache_rows`).
- [x] Assembled packets are genuinely deduplicated across multiple providers before being stored or
      returned — verified by a real test proving duplicate context items from different providers
      collapse to one (`test_duplicate_fact_across_two_providers_yields_one_statement_two_evidence_ids`).
      **Caveat, honestly disclosed**: this AC's literal text ("real test") is satisfied at the
      unit/fixture level; the real 7-entry corpus never actually exercised genuine duplicate content
      across both providers in the same query (only 1/7 entries queried both providers at all), so
      real-corpus-scale dedup remains structurally proven but not empirically observed — this is why
      the corresponding §20 proposal bullet stays unmarked (see Completion Summary).
- [ ] Caller budgets are enforced using real measured output size (not an estimate), within a
      documented tolerance, and any budget-driven pruning is visible/marked, never silent — per this
      epic's own Phase 3 Pilot Acceptance Criterion "Returned content respects the requested budget
      within a documented tolerance." **NOT MET.** The measured output size and visible-pruning
      mechanism (`budget_truncated`/`omitted_statement_count`) is real, but the real-corpus
      measurement found only 2/7 entries actually stayed within the documented ±20% tolerance,
      because `context[]`/`evidence[]`/`conflicts[]` are structurally unbudgeted by
      `assemble_within_budget()`. A real, measured FAIL — see Completion Summary.
- [x] Conflicts between providers are surfaced structurally and are never silently merged into a
      single answer — per §21's explicit criterion. Structural guarantee proven by a fail-loud
      cardinality assertion and a dedicated non-vacuous (break/restore) guard test. **Caveat**: the
      real 7-entry corpus surfaced zero actual cross-provider conflicts, so this is a proven
      structural guarantee, not an empirically-observed real-corpus behavior — disclosed honestly by
      the acceptance-measurement ticket rather than silently assumed.
- [x] Packet dependency records exist and targeted invalidation genuinely works: a changed cited
      source invalidates the affected cached packet; an unrelated changed source does not — built by
      `TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION`, made live by
      `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`, and independently re-verified at real,
      live-corpus scale by `TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT`.
- [x] A Level 2 cache hit returns a stored packet payload without rerunning any provider — verified
      by a real test proving the provider round-trip is skipped, mirroring Phase 2's own genuine-
      hit verification discipline (spy/counter, not `response["cache"]` alone) —
      `test_identical_repeated_knowledge_context_call_is_a_genuine_level2_cache_hit`, and
      independently dual-signal-verified again by the acceptance-measurement ticket's own real run.
- [x] This epic's own acceptance-measurement child ticket honestly re-measures against proposal
      §21's full Phase 3 Pilot Acceptance Criteria list using the frozen 7-entry corpus, reporting
      whichever result is real — including a FAIL on any criterion, if that is what the real
      measurement shows. `TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT` did exactly this: 5/8
      PASS, 1 real FAIL, 1 disclosed limitation, 1 PARTIAL.
- [x] Every Phase 3 child ticket writes a real, schema-valid `docs/parity_ledger/infrastructure.yaml`
      entry for its own behavior change, per this repo's own CLAUDE.md governance rule — unaffected
      by "Parity Ledger not required until Phase 4," which concerns only the gateway's own routing
      behavior, not this repo's ticket-close governance requirement (see naming-collision
      clarification above). INFRA-346/347/348/349/350, one per child ticket.
- [ ] `docs/plans/knowledge-gateway-mcp-proposal.md` §20's Phase 3 bullets are annotated Done as
      child tickets land, mirroring the Phase 0/1/2 epics' own annotation convention. **PARTIALLY
      MET.** 2 of 4 bullets are marked Done (packet payload storage; dependency records + targeted
      invalidation). 2 remain honestly unmarked for real, specific reasons — see Completion Summary.
- [x] `CLAUDE.md`, `.claude/agents/*.md`, and `.claude/skills/*.md` remain byte-unchanged by every
      child ticket in this epic — confirmed via `git diff --stat HEAD` returning empty for all three
      paths.
- [ ] This epic is not closed merely because a child ticket's code lands — Phase 3's own bar (all
      §20 Phase 3 bullets Done, a real Level 2 cache genuinely producing hits with dependency-aware
      invalidation, and an honest measurement against §21's full Phase 3 Pilot Acceptance Criteria
      list) must be met. **This literal bar is NOT fully met** — 2/4 §20 bullets remain open. The
      epic is closed anyway, by explicit user decision, with both gaps stated honestly rather than
      silently glossed over or worked around — mirroring the Phase 2 epic's own precedent of closing
      on a real, disclosed tension rather than blocking indefinitely. See Completion Summary.

## Related Tickets
- TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS (child 1; Level 2 schema + migration_002 —
  see SEQUENCE.md)
- TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT (child 2; multi-provider dedup + real
  caller-budget enforcement)
- TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION (child 3; packet dependency records +
  targeted invalidation)
- TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING (child 4; Level 2 cache lookup/write wired
  into the real gateway, checked before Level 1/live providers)
- TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT (child 5; honest §21 Phase 3 Pilot Acceptance
  measurement — closes this epic's acceptance loop)
- TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE2-EPIC (DONE; parent Phase 2 epic — supplies the real,
  now-confirmed-working Level 1 cache this epic builds Level 2 on top of)
- TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION (DONE; the hotfix that resolved Phase 2's
  closure finding, raising `MAX_PAYLOAD_BYTES` from 8192 to 65536 and confirming 7/7 genuine cache
  hits against the real corpus — the precondition this epic explicitly builds on rather than
  silently assumes)
- TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS (DONE; the Level 1 schema and
  `migration_001_add_level1_tables` this epic's own schema ticket sits alongside, never modifies)
- TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING (DONE; the Level 1 read/write wiring and evidence-
  validity/lookup-identity separation this epic's own wiring ticket must not collapse or bypass)
- TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON (DONE; supplies the frozen corpus/methodology
  precedent this epic's own acceptance-measurement child ticket reuses)
- TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY (DONE; froze `cache_migration_plan.md`'s
  `migration_002_add_level2_tables` reservation and `evidence_cache_identity_contract.md` §5's
  branch/working-tree/changed_paths logic this epic's dependency-invalidation ticket investigates
  reusing)
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC (BACKLOG; owns the existing marker-only
  `retrieval_packet_cache_rows` table this epic's schema ticket must leave untouched)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §10.2 (Cache Levels), §10.3 (Conceptual Cached
  Packet Schema), §20 (Phase 3 bullets), §21 (Phase 3 Pilot Acceptance Criteria)
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` (reserves
  `migration_002_add_level2_tables`)
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` §5 (branch/
  working-tree/`changed_paths` intersection logic, candidate for packet-level reuse)
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` (write-path
  enforcement Level 2 payloads must also satisfy — verification, not assumption)
- `docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md` (the honest 0/7 →
  7/7 finding this epic's Request Summary carries forward)

## Related Stored Artifacts
None yet — scope-only epic, no staging artifacts per the Phase 0/1/2 epics' own precedent.

## Related Code Areas
- `tools/knowledge_gateway_mcp.py` (`_run_knowledge_context()` — the request-handling hook point
  this epic's wiring ticket extends with a Level 2 check before Level 1)
- `tools/knowledge_gateway_router.py` (read-only unless a specific child ticket's own scope requires
  a minimal cache hook)
- `tools/knowledge_gateway_packet_assembly.py` (`assemble_packet()`,
  `kgmcp_char_heuristic_v1_token_count()` — the extractive packet assembly this epic's dedup/budget
  ticket extends)
- `tools/knowledge_gateway_cache.py` (Level 1 cache orchestration — `perform_cache_lookup()`/
  `perform_cache_write()`/`compute_lookup_identity()` — the pattern this epic's Level 2 orchestration
  mirrors)
- `tools/knowledge_gateway_redaction.py` (write-path enforcement, `MAX_PAYLOAD_BYTES = 65536` —
  this epic's wiring ticket must verify, not assume, that it correctly applies to Level 2 payloads)
- `tools/retrieval_cache.py` (schema/migrations — `migration_002_add_level2_tables` lands here)
- `tools/agent-monitoring/kgmcp_baseline_corpus.py`,
  `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py`,
  `tools/agent-monitoring/kgmcp_phase2_gateway_runner.py` (the frozen corpus and measurement-runner
  precedent the acceptance-measurement child ticket reuses, never reimplements)

## Assumptions / Open Questions
- Exact name of the new Level 2 content-bearing table (`retrieval_context_packet_cache_rows` or
  similar) is not decided here — the schema child ticket's own Investigate phase decides, subject
  only to the hard constraint that it is a NEW table and `retrieval_packet_cache_rows` stays
  untouched.
- Whether "respects budget within documented tolerance" implies dropping lowest-priority context
  items with a visible marker (vs. silent truncation) is explicitly NOT decided here — flagged as
  the dedup/budget-enforcement child ticket's own Investigate-phase question, to be resolved with
  reference to §5's existing "reject, not truncate; never silently incomplete" size-cap philosophy
  already established in Phase 2's redaction work, but not assumed to transfer unchanged.
- Whether `evidence_cache_identity_contract.md` §5's `changed_paths` intersection logic can be
  reused as-is at the packet level, or needs a packet-specific extension, is left to the
  dependency-invalidation child ticket's own Investigate phase.
- Whether Level 1's write-path enforcement (redaction, secret-scan, size cap) automatically covers
  Level 2 packet payloads, or needs its own dedicated verification/extension, is explicitly left
  open here — the read/write-wiring child ticket must verify this, not assume it.

## Implementation Notes
Scope-only epic; no direct implementation. All 5 child tickets landed sequentially per
`SEQUENCE.md`'s dependency order, each independently reviewed (Architecture Review pre-Implement,
Architecture-Verify post-Implement), security-reviewed where tagged, and verified (done-checker) —
in every case across 1-2 Verify passes, with zero gates routed around per this repo's Gate
Integrity hard rule.

After all 5 children closed, a final epic-level doc sweep (this epic's own closure step, not a
child ticket's) re-assessed the 3 of 4 `docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 3
bullets each individual child ticket had left unmarked at the time (before Level 2 was genuinely
live). One (dependency records + targeted invalidation) was found genuinely closable given the
now-complete picture and marked Done, citing all three tickets that built/wired/proved it. Two
(multi-provider dedup; caller budget enforcement) were found to have real, specific, unresolved
gaps and were left honestly unmarked — see Completion Summary.

## Test Summary
Aggregate across all 5 child tickets (each ticket's own Test Summary has the full detail):
- PACKET-CACHE-SCHEMA-MIGRATIONS: 514 tests passing (13 new).
- PACKET-DEDUP-BUDGET-ENFORCEMENT: 130 tests passing (13 new).
- PACKET-DEPENDENCY-INVALIDATION: 138 tests passing (14 new).
- PACKET-CACHE-READ-WRITE-WIRING: 287 tests passing (40 new across Implement + Test-phase gap-check).
- PILOT-ACCEPTANCE-MEASUREMENT: 31 tests passing (new measurement-runner test file), plus the real,
  honest 7-entry-corpus measurement run itself (the actual "test" this ticket exists to perform).

## Files Changed
Aggregate — see each child ticket's own Files Changed for exact line-level detail:
- `tools/retrieval_cache.py` — Level 2 schema (`migration_002`), write-path columns (`migration_004`),
  real Level 2 read/write functions.
- `tools/knowledge_gateway_cache.py` — Level 2 lookup/write/revalidation orchestration
  (`compute_context_packet_lookup_identity()`, `perform_context_packet_cache_lookup()`,
  `perform_context_packet_cache_write()`, `revalidate_context_packet_row()`,
  `_level2_repo_branch_scope()`).
- `tools/knowledge_gateway_packet_assembly.py` — `evidence_dependencies` field, shared
  `_content_hash()` helper, conflict-signal-aware dedup guard, `budget_truncated`/
  `omitted_statement_count` fields.
- `tools/knowledge_gateway_mcp.py` — Level 2 check-then-fall-through wired into
  `_run_knowledge_context()` ahead of Level 1; new `knowledge_status` Level 2 fields.
- `tools/agent-monitoring/kgmcp_phase3_gateway_runner.py` — new real-corpus measurement runner.
- `docs/guidelines/intentional_divergences.md` — §2.44 (Non-collapse rule, Level 2 schema),
  §2.45 (budget_tokens in Level 2 lookup identity).
- `docs/parity_ledger/infrastructure.yaml` — INFRA-346/347/348/349/350.
- `docs/plans/knowledge-gateway-mcp-proposal.md` — §20 Phase 3 bullets (2/4 marked Done), §21
  honest-result narrative paragraph.
- `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md` — new results
  doc.
- Various test files across `tests/tools/` — 111 new tests total across all 5 children.

## Completion Summary
All 5 Phase 3 child tickets are DONE, each independently reviewed, tested, and verified. The Level 2
assembled-packet cache is genuinely real: it is checked before Level 1 in the live
`_run_knowledge_context()` call path, produces genuine cache hits without re-invoking any provider,
correctly enforces branch/working-tree scope, and correctly rejects/refreshes on both a changed
cited source and a provider-generation bump — all independently re-verified at real, live-corpus
scale (not just unit-fixture scale) by this epic's own final acceptance-measurement ticket.

**This epic closes with two gaps stated honestly, not glossed over, per explicit user decision to
close now rather than block on them (mirroring the Phase 2 epic's own precedent of closing on a
real, disclosed tension):**

1. **Caller budget enforcement measurably fails its own documented tolerance at real-corpus scale.**
   The mechanism is real (measured output size, visible `budget_truncated` marker, never silent) —
   but `TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT`'s honest measurement found only 2 of 7
   real corpus entries actually stayed within the documented ±20% tolerance, because
   `context[]`/`evidence[]`/`conflicts[]` are structurally unbudgeted by `assemble_within_budget()`.
   This is a real, specific, measured FAIL against this epic's own stated Phase 3 Pilot Acceptance
   Criterion, not a documentation gap.

2. **Multi-provider deduplication is structurally proven but never empirically observed at real-corpus
   scale.** `deduplicate_statements()`/`assemble_packet()` are real, tested, and reachable from the
   live call path, and the dedup identity/collision-guard logic is unit-tested — but the real 7-entry
   corpus never actually exercised genuine duplicate content across both providers in the same query
   (only 1 of 7 entries even queried both providers). This is a real coverage gap, not a functional
   defect — the mechanism has not been disproven, only unproven at the scale that matters.

Neither gap was worked around, silently assumed closed, or hidden in either the code, the tests, the
parity ledger, or the proposal doc's own annotations — `docs/plans/knowledge-gateway-mcp-proposal.md`
§20 Phase 3 explicitly leaves both corresponding bullets unmarked, with the real reasoning stated
inline. Closing these two gaps is left to a separately-scoped follow-up ticket, for a human reviewer
to prioritize against the rest of the Knowledge Gateway MCP roadmap — this epic does not self-assign
that follow-up ticket's ID or scope.

This epic does **not** declare Phase 3 "production-capable" or the pilot boundary closed — per its
own explicit Out of Scope and the acceptance-measurement ticket's own Out of Scope, that
determination remains a separate, later human-reviewer call based on the real §21 numbers now on
record (`docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`).

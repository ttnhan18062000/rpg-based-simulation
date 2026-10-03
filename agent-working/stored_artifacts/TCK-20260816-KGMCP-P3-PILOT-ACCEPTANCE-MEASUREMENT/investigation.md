---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT
artifact_type: investigation
tags: [ai, mcp, testing]
---

# Investigation — TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT

## Current Behavior

**`tools/knowledge_gateway_mcp.py::_run_knowledge_context()`** (`tools/knowledge_gateway_mcp.py:149-371`)
is the real, live call path. As of the Level 2 wiring sibling ticket, the order is:
1. `route()` (`:193`) — router failure → fail-open `PARTIAL` fallback (`:194-220`).
2. **Level 2 cache-check** (`:228-244`) — `_kgc.perform_context_packet_cache_lookup(request,
   routing_decision, effective_budget)`, wrapped in its own broad `try/except` (fail-open,
   independent of the Level 1 hooks' own try/except). On a genuine hit, returns
   `hit_response["cache"] = "HIT_L2"` **without ever reaching Level 1's lookup or
   `assemble_packet()`**.
3. **Level 1 cache-check** (`:252-264`) — `_kgc.perform_cache_lookup(...)`, only reached on a Level
   2 miss. On a hit, returns `"cache": "HIT"`.
4. `assemble_packet()` (`:266`) — only reached on a double miss (real provider round trip).
5. **Level 2 write** (`:353-360`) then **Level 1 write** (`:364-368`) — both attempted
   independently, fail-open, only on a genuine full miss (`response["cache"] = "MISS"` at `:347`).

**`tools/knowledge_gateway_cache.py`** (619 lines) is pure orchestration for both cache levels.
Level 2's lookup/write orchestrators (`perform_context_packet_cache_lookup` `:496-529`,
`perform_context_packet_cache_write` `:532-619`) compute a `packet_id` hash over
`(normalized_intent, entity_ids_json, repository_id, branch, budget_tokens, query_key_hash)`
(`:420-458`) and delegate revalidation to `revalidate_context_packet_row()` (`:249-283`), which:
performs branch-compatibility (`is_branch_compatible`, hard partition, checked first, `:264-265`),
then working-tree-overlap-forces-revalidation (`:267-268`, `changed_paths ∩
evidence_dependencies`), then, only if `select_validation_basis()` resolves to
`"PROVIDER_GENERATION"` (both real providers today — Investigate confirmed, no
`fine_grained_fingerprints: true` descriptor exists), a per-provider generation-bump comparison
(`:279-283`). If the basis ever resolved to `"FINER"`, Level 2 fails closed (`:270-277`) since its
schema carries no `evidence_fingerprints`-equivalent column — this path is currently unreachable
with the two real provider descriptors but is a real, disclosed design limit, not a gap this ticket
introduces.

**`tools/knowledge_gateway_packet_assembly.py`** (764 lines): `assemble_within_budget()`
(`:585-616`) enforces `budget_returned <= budget_requested` **by construction**, over the
`statements[]` list only (running-cost accumulation, `:605`). This is a hard, always-true guarantee
for the statements sub-array — **it is not a bound on the full response payload**. `context[]`,
`evidence[]`, and `conflicts[]` are not subject to this per-statement budget accounting at all.
`build_conflicts()` (`:558-579`) is real, tested, but purely **structural** (explicit
supersession/deprecation-marker detection in source docs — `_structural_supersession_signal()`),
not automatic cross-provider factual-value comparison.

**Existing per-stage timing instrumentation: none live.** `tools/retrieval_events.py`'s 3 wrapper
functions (`wrap_hybrid_retrieval`, `wrap_retrieval_cache_check`, `wrap_context_packet_assembly`)
remain, confirmed repeatedly across Phase 0/1/2 (`measurement_baseline_contract.md` §2.1/§2.4,
re-confirmed 2026-08-15), **unimported and uninvoked** by `tools/knowledge_gateway_mcp.py`. No
Level 2 lookup/revalidation/write call in the current code path is separately timed either — the
Level 2 hooks at `:228-244`/`:353-360` are bare function calls with no `time.perf_counter()`
wrapping anywhere in `tools/knowledge_gateway_mcp.py` or `tools/knowledge_gateway_cache.py`. This
confirms this ticket's own premise: **per-stage timing (lookup / validation / fallback / assembly /
end-to-end) is not measurable from code-reported numbers today and must be measured externally by
this ticket's own runner**, via `time.perf_counter()` wrapped directly around each real call
boundary the runner itself controls (mirroring `kgmcp_phase1_gateway_runner.py`'s and
`kgmcp_phase2_gateway_runner.py`'s own established external-timing precedent, never editing gateway
code to add instrumentation — that would violate this ticket's Out of Scope). Concretely, the
runner can externally time:
- **lookup** — wrap the Level 2 `perform_context_packet_cache_lookup()` call and, on a Level 2
  miss, the Level 1 `perform_cache_lookup()` call, each independently (both are directly callable,
  already-loaded module functions, mirroring the existing spy pattern on `assemble_packet`/
  `evaluate_write_candidate`).
- **validation** — not independently separable from "lookup" in the *current* code shape:
  `perform_context_packet_cache_lookup()`/`perform_cache_lookup()` call revalidation internally as
  part of the same function body (`:513-529`/`:299-313`), with no call boundary between "lookup"
  and "revalidate" the runner can wrap without editing gateway code. This must be disclosed as a
  genuine instrumentation-granularity limit (see Risks), not silently collapsed into "lookup" and
  presented as if it were the true, disjoint §2.2 measurement point.
- **fallback** — the real provider round trip only happens inside `assemble_packet()` on a double
  miss; timing the `assemble_packet()` call itself (already spied on by both prior runners) doubles
  as this measurement point on a genuine double-miss (cold) call.
- **assembly** — not separable from "fallback" either, for the same structural reason: packet
  assembly happens inside the same `assemble_packet()` call as the provider round trip, with no
  externally-observable call boundary between "provider round trip finished" and "packet assembled"
  in the current code. Reported as a disclosed combined figure, not fabricated as two independent
  numbers.
- **end-to-end** — `time.perf_counter()` wrapped directly around the whole
  `_run_knowledge_context(query_text)` call, exactly as both prior runners already do.

## Mechanics / Engine Constraints

- `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` §2.5's
  reconciliation rule: end-to-end latency is defined as the **sum** of whichever of §2.1–§2.4
  actually execute for a given request — never a 6th, independently measured number. This ticket's
  runner must respect this: end-to-end is `time.perf_counter()` around the whole call, and the
  per-stage figures reported alongside it must be disclosed as a decomposition attempt against that
  same total, honestly noting where two stages could not be separated (see above).
- §21 (`docs/plans/knowledge-gateway-mcp-proposal.md:1352-1380`) is the acceptance bar itself — the
  closing bullet (`:1378-1380`) is the one this ticket's AC1/AC4/AC5 exist to satisfy.
- `redaction_retention_policy.md` §8 (`:220-238`): `kgmcp_char_heuristic_v1` ≈
  `ceil(len(text.encode("utf-8"))/4)`, carrying a **documented ±20% tolerance** against a true
  tokenizer count (`:235-238`) — this is explicitly named as "the standard against which a future
  implementation validates the Phase 3 pilot's 'returned content respects the requested budget
  within a documented tolerance' acceptance bar." This is the concrete, already-ratified tolerance
  AC2 must measure against — no new tolerance number should be invented.
- `evidence_cache_identity_contract.md` §5 rule 2 (branch hard partition) and rule 3
  (working-tree-overlap-only revalidation) are the rules `revalidate_context_packet_row()` (see
  above) implements for Level 2 — cited, not restated, by the dependency-invalidation sibling
  ticket's own investigation.

## Docs Requiring Update

- `docs/plans/knowledge-gateway-mcp-proposal.md`: §21's closing bullet and the Phase 3 bullet list
  (`:1299-1328`) currently describe Phase 3 deliverables as landed but do not yet report this
  ticket's own honest measurement outcome against the closing criterion. This ticket must add a
  short, honestly-worded status note (pass/fail per the real numbers) once the real corpus run
  completes — mirroring how the existing "Store and return actual packet payloads. **Done**" bullet
  already cites its own sibling ticket and named tests.
  **Resolved during Document-Update:** per the Phase 2 recomparison precedent
  (`TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON`, which appended a narrative results paragraph
  after its own phase's bullet list in §20 rather than marking any bullet "Done"), this ticket
  appended two narrative paragraphs — one after §20 Phase 3's closing "first production-capable
  pilot boundary" framing (a factual pointer only, explicitly not declaring Phase 3
  production-capable, per this ticket's own Out of Scope), and one after §21's own criteria list
  (the honest 5 PASS / 1 FAIL / 1 disclosed-limitation / 1 PARTIAL breakdown, pointing to the new
  results doc). No individual §21 criterion or the pilot-boundary bullet was marked Done/achieved —
  the real, mixed result stands as measured.
- A **new** results doc under `docs/engine/contracts/knowledge_gateway_mcp/`, e.g.
  `phase3_pilot_acceptance_measurement.md`, following `phase2_baseline_recomparison.md`'s exact
  precedent shape (headline table, per-criterion sections, honest-verdict section,
  cross-references) — required regardless of outcome, since this is the ticket's primary
  deliverable, not optional.
  **Resolved during Document-Update:** already written by Implement. Sanity-checked against this
  ticket's own Implementation Notes numbers (FAIL 2/7 budget tolerance, 0/7 conflicts, latency
  improved 2521.78→1438.21ms and 1543.32→1438.21ms, tokens 2846/2615→2865, recall 0/7 regressions)
  — accurate and complete, no edits needed.

## Docs Considered But Not Required (resolved during Document-Update, not left open)

- `docs/parity_ledger/infrastructure.yaml`: originally flagged here as requiring a new `INFRA-NNN`
  entry certifying the measurement tool (AC8). **Not touched by Document-Update** — per this
  session's per-family rule, `docs/parity_ledger/*.yaml` is `parity-updater`'s exclusive territory,
  handled in the ticket's own separate, later Parity phase (intended ID `INFRA-350`, per
  `plan.md` Step 12). Investigate's original framing correctly identified the need but the wrong
  phase to discharge it in; corrected here.
- `redaction_retention_policy.md` §8: originally flagged here only to make an already-decided "not
  touched" call explicit, not left ambiguous. Re-confirmed during Document-Update — this ticket
  measures against §8's already-ratified ±20% tolerance (cited verbatim in the results doc's #12
  section) and does not redefine it; no edit needed.

## Parity Ledger Overlap

- `INFRA-344` (`docs/parity_ledger/infrastructure.yaml`) — the Phase 2 recomparison runner's own
  entry. Directly relevant precedent for this ticket's own new entry's shape and "tool-certifies-
  not-performance-certifies" framing, not itself edited by this ticket.
- `INFRA-345` — the hotfix's cache-size-cap recalibration entry. Directly relevant: this ticket's
  real corpus run inherits the post-hotfix `MAX_PAYLOAD_BYTES = 65536` cap live from
  `tools/knowledge_gateway_redaction.py`, not re-derived.
- No P0-priority entries were found overlapping this ticket's scope in a `grep` of `infrastructure.yaml`
  for the KGMCP-related IDs above — both cited entries are P1. No P0 test-path obligation applies
  here beyond this repo's general "every new entry needs a real `test_path`" rule.

## Prior Work

- `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON` (stored, `kgmcp_phase1_gateway_runner.py`) — the
  original cold-path methodology precedent: single call per entry, `time.perf_counter()`-wrapped,
  §4.3 recall normalization helpers (`_normalize_phase1_source_id`, `_path_only`,
  `_compute_threshold_4_3`) this ticket's own runner should import, never reimplement.
- `TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON` (stored, `kgmcp_phase2_gateway_runner.py`) — the
  cold+warm double-call precedent, dual-signal genuine-hit verification (provider-round-trip spy +
  SQL `hit_count` delta, never `response["cache"]` alone), and the honest-FAIL reporting discipline
  this ticket's Gate Integrity obligation directly inherits. Its committed fixture
  (`tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json`) records the **pre-hotfix,
  0/7-genuine-hit** state (every write rejected `oversized_payload` under the old 8192-byte cap) —
  this fixture's per-entry latency/token numbers are **not** representative of a genuine warm-hit
  path and must not be used as this ticket's Level-1-warm comparison baseline without that caveat
  stated explicitly.
- `TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION` (done ticket, no staging artifacts —
  hotfix tier) — recalibrated `MAX_PAYLOAD_BYTES` 8192→65536 and **live-verified 7/7 genuine Level 1
  cache hits** against a manually-cleared cache DB, but explicitly **did not persist** that run's
  per-entry data to any committed fixture (it called `run_corpus()` directly from a throwaway
  scratchpad driver, deliberately avoiding `main()` to not overwrite the frozen Phase 2 fixture).
  The hotfix ticket's own prose additionally discloses that even with genuine 7/7 hits, **§4.1
  (latency), §4.2 (tokens), and §4.3 (recall) all remained FAIL 0/7** in that same clean run — a
  genuine cache hit alone did not clear those thresholds. **This means no committed, real,
  per-entry Level-1-genuine-warm-hit latency/token dataset exists anywhere in this repository
  today** — see Question 2 below and Risks.
- `TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS`, `-DEDUP-BUDGET-ENFORCEMENT`,
  `-DEPENDENCY-INVALIDATION`, `-CACHE-READ-WRITE-WIRING` (all stored/done) — the four sibling
  tickets whose real Level 2 behavior this ticket measures. Their own tests
  (`tests/tools/test_knowledge_gateway_mcp.py:658-950`, `tests/tools/test_knowledge_gateway_cache.py`)
  are confirmed, by direct read, to be **synthetic-query, monkeypatched-provider, single-entry unit/
  integration tests** (e.g. `_patch_small_cacheable_search()`, literal query text like `"level2
  repeat query"`), never the real frozen 7-entry corpus run through the real live gateway and real
  providers. This substantiates the ticket's own AC1/AC6 "must re-verify at real-corpus scale" — it
  genuinely has not been done yet by any prior ticket.

## Risks and Open Questions

### Q1 — New runner file, or extension of `kgmcp_phase2_gateway_runner.py`?

**Resolution: a new file** (recommend `tools/agent-monitoring/kgmcp_phase3_gateway_runner.py`),
mirroring exactly how `kgmcp_phase2_gateway_runner.py` itself related to
`kgmcp_phase1_gateway_runner.py`: a new module that **imports pure helpers** from both predecessors
(`_compute_threshold_4_3`, `_normalize_phase1_source_id`, `_path_only` from Phase 1; potentially the
dual-signal hit-verification pattern's *shape*, though Phase 2's own `_run_single_entry` is not a
pure importable helper — its logic must be mirrored, not imported, since it is entry-point-shaped
around Phase 1's 2-call design, not Phase 3's differently-shaped 3-call design below) rather than
editing either predecessor file in place. Both predecessor runners' own module docstrings
explicitly enumerate the files they "never touch," and `test_kgmcp_phase2_baseline_recomparison.py`'s
`test_no_frozen_kgmcp_dependency_edited`/`test_never_edits_phase1_results_doc` guard tests
structurally enforce this — editing either predecessor file in place would trip an existing,
still-live regression guard for no benefit. A new file also lets this ticket define its own,
differently-shaped per-entry call sequence (see Q2) without contorting Phase 2's fixed 2-call
(cold+warm) shape.

### Q2 — Which baseline: Phase 1 cold, or Phase 2's Level-1-warm?

**Finding, not fully resolved by citation alone — real data does not exist yet.** The ticket's own
Assumptions section suggests Level-1-warm is "likely correct... the immediately prior working state
Level 2 must improve on." This reasoning is sound in principle, but **Prior Work above establishes
that no committed, real, per-entry Level-1-genuine-warm-hit dataset exists** — the only committed
fixture with genuine cache-hit data is pre-hotfix (0/7, all size-cap-rejected), and the post-hotfix
7/7 live run was never persisted to a fixture.

Compounding this: the live code's cache-check order (Level 2 checked strictly *before* Level 1,
`tools/knowledge_gateway_mcp.py:228-264`) means a naive second call after a cold miss is **already a
Level 2 hit**, not a Level 1 hit — Level 1 is now structurally unreachable as a "warm" measurement
point via an ordinary second call, since Level 2's row (written on the same cold miss) always wins
the race. **To produce a genuine, real, same-run Level-1-warm comparison point, the runner would
need to isolate Level 1 explicitly** — e.g. a 3-call-per-entry design: (1) cold call, writing both
Level 1 and Level 2 rows; (2) a real, disclosed, direct SQL `DELETE` of just the Level 2 row for
this identity (a measurement-isolation technique, not a gateway-code edit — mirrors
`kgmcp_phase2_gateway_runner.py::_read_hit_count()`'s own precedent of direct, read-only SQL against
the cache DB, extended here to a disclosed, narrowly-scoped write for isolation purposes only); (3)
a third call, which now genuinely falls through Level 2 (empty) to Level 1 (still populated from
call 1) for a real, same-run, same-entry Level-1-warm measurement, comparable apples-to-apples
against call 2's real Level-2-warm measurement. **This is a real design decision this Investigate
phase surfaces but does not itself make** — a direct DB write from measurement tooling is a step
beyond Phase 1/Phase 2's read-only-SQL precedent, and Plan should weigh it (with Architecture Review
if warranted) against the simpler, weaker alternative: report Level-2-warm against Phase 1's cold
baseline only (the one baseline with real, committed, per-entry numbers), explicitly disclosing that
no real Level-1-warm comparison point could be produced without either this DB-isolation technique
or a fresh full re-run of Phase 2's own runner (which is also legitimate — reusing
`kgmcp_phase2_gateway_runner.py::run_corpus()` as an importable, called-not-reimplemented function
this ticket's own runner could call once, live, to freshly (re)establish a real Level-1-warm dataset
in the same session, before then measuring Level 2 on top of it).

**Recommendation for Plan:** report **both** Phase 1 cold (real, committed,
`kgmcp_phase1_baseline_comparison_results.json`) and a freshly, honestly (re)measured Level-1-warm
number this ticket's own run produces (via one of the two mechanisms above), each clearly labeled,
rather than picking one and silently dropping the other — the ticket's own AC4 requires "a clearly
stated baseline... justified in Implementation Notes," which is best satisfied by presenting the
real comparison landscape rather than asserting a single choice was obviously available when it was
not.

### Q3 — Can the frozen 7-entry corpus exercise every §21 criterion?

**No, not all of them, and this must be disclosed, not worked around.**
- **Real provider conflicts:** `build_conflicts()` is structural (explicit supersession/deprecation
  markers in source docs), not automatic cross-provider factual disagreement detection. Whether any
  of the 7 corpus queries' real, live responses surface a structural conflict is genuinely unknown
  until the real run happens — Investigate did not fabricate an assumption either way. **If the real
  run surfaces zero conflicts across all 7 entries** (plausible, given the corpus was designed
  around §8's routing-shape coverage, not conflict-shape coverage), AC3 must report "0 real
  conflicts observed; the visibility mechanism itself remains unit-tested elsewhere
  (`build_conflicts()`'s own test suite), but this corpus does not naturally exercise a real
  conflict occurrence" — explicitly, not silently marked satisfied.
- **Per-stage latency breakdown:** as established under Current Behavior, "validation" cannot be
  externally separated from "lookup," and "assembly" cannot be externally separated from
  "fallback/provider round trip," in the current code's call-boundary shape, without editing gateway
  code (out of scope). The runner can report 3 real, externally-timed numbers (lookup+validation
  combined, fallback+assembly combined, end-to-end) rather than the full 5 §2.1–§2.4 breakdown the
  proposal's prose names — this is a real, disclosed instrumentation-granularity limit of this
  ticket's own measurement-only mandate, not a shortfall in effort.
- **Branch-partition / uncommitted-change invalidation:** the live 7-entry corpus, run against a
  single real repo checkout on a single real branch, cannot *naturally* produce a second,
  incompatible branch or an uncommitted change mid-run without the runner itself manufacturing that
  condition (e.g. a synthetic second `repo_branch_scope` string passed to a direct
  `revalidate_context_packet_row()` call, or a real `changed_paths` argument on a repeat
  `_run_knowledge_context()` call) — this is legitimate (mirrors the sibling wiring ticket's own
  test technique) but is not "real corpus at real scale" in the same sense as the latency/token
  measurements; it should be reported as a targeted, disclosed real-call verification against the
  real, live cache/revalidation code (not a synthetic unit-test row dict, unlike the sibling
  tickets' own tests), distinct from the pure-wall-clock corpus sweep.

### Q4 — §21 enumeration: new/Level-2-dependent vs. already-settled

18 total criteria (`docs/plans/knowledge-gateway-mcp-proposal.md:1356-1380`), numbered here in
proposal order:

| # | Criterion (abridged) | Status | Basis |
|---|---|---|---|
| 1 | Context Search and Graphify remain independently callable | **SETTLED** | Explicitly named in ticket's own Request Summary; unaffected by L2 (both providers still called directly and unwrapped on any real miss). |
| 2 | A gateway failure never blocks investigation | **SETTLED** | Explicitly named; Phase 1's router-failure fail-open fallback (`:194-220`) is untouched by L2. |
| 3 | `knowledge_context` reports every supporting/queried provider and every evidence source | **VERIFIED-AS-BYPRODUCT** | Schema-shape guarantee (`RESPONSE_VALIDATOR.validate()` runs on every real call this ticket's corpus run makes, including L2 hits at `:243`) — confirmed by every corpus call succeeding schema validation, not a dedicated separate measurement. |
| 4 | A warm hit returns a stored payload without rerunning the provider | **NEW — measure** | This is literally what AC1's per-entry corpus run must demonstrate for the real Level 2 path (mirrors Phase 2's own `assemble_packet`-spy technique, extended to L2). |
| 5 | A cache lookup match never bypasses the separate evidence-validity check | **SETTLED** | Explicitly named ("evidence-validity/lookup-identity separation"); `revalidate_context_packet_row()` structurally always runs before a hit is served (`:518-527`), already unit-tested by the sibling wiring ticket. |
| 6 | Capability-descriptor-bounded routing | **SETTLED** | Explicitly named; Phase 1 behavior, untouched by L2. |
| 7 | A changed cited source causes a stale rejection | **NEW — measure** | Explicitly in AC6's four-item corpus-scale re-verification list. |
| 8 | An unrelated changed source does not invalidate the cached packet | **NEW — measure** | Same, AC6. |
| 9 | Finest-granularity evidence identity, generation as fallback only | **SETTLED (cite, don't re-measure)** | Architectural/design property of `select_validation_basis()`/`revalidate_context_packet_row()`, already unit-tested by the sibling dependency-invalidation ticket; not named in AC6's explicit four-item list, and the real 7-entry corpus does not naturally exercise both identity forms distinctly (both real providers report `fine_grained_fingerprints: False` today — the "FINER" branch is currently unreachable). |
| 10 | Branch-local results not reused across incompatible branches | **NEW — measure** | AC6 ("branch-partition"), even though the general Level-1 branch-scope concept was already settled — Level 2's own branch check (`revalidate_context_packet_row`'s `is_branch_compatible` call) is new code, only unit-tested synthetically so far. |
| 11 | Relevant uncommitted changes invalidate affected cached evidence | **NEW — measure** | AC6 ("uncommitted-change invalidation"). |
| 12 | Returned content respects the requested budget within a documented tolerance | **NEW — measure** | Explicit AC2; ±20% tolerance per `redaction_retention_policy.md` §8. |
| 13 | Conflicts are visible and never silently merged | **NEW — measure (with disclosed corpus-coverage limit, see Q3)** | Explicit AC3. |
| 14 | Negative claims verified only when scopes/dependencies recorded | **SETTLED (cite, don't re-measure)** | Verification-field computation happens identically inside `assemble_packet()` regardless of which cache level ultimately serves/writes the result; L2 only stores/replays the already-computed field verbatim — unaffected by this epic's wiring work. |
| 15 | Pre-Phase-6 conflict reporting stays within §14's structural boundary | **SETTLED (cite, don't re-measure)** | Same reasoning as #14 — `conflicts[]`'s shape is computed once by `build_conflicts()` and stored/replayed verbatim by L2, not recomputed or reshaped by the cache layer. |
| 16 | No prohibited sensitive content is written to the cache | **SETTLED** | Explicitly named in ticket's own Request Summary; L2's own write path was already independently unit-tested to route through `evaluate_write_candidate()` with no bypass (`test_level2_cache_write_calls_evaluate_write_candidate_before_any_insert`, `test_no_raw_insert_statement_bypasses_redaction_anywhere_in_level2_cache_module`), cited not re-derived. |
| 17 | The database can be deleted and rebuilt without losing project truth | **SETTLED** | Explicitly named. |
| 18 | Reports lookup/validation/fallback/assembly/end-to-end latency separately; demonstrates lower median end-to-end latency and fewer delivered tokens without reducing recall | **NEW — measure (central, with disclosed instrumentation-granularity limit, see Q3)** | This is AC1+AC4+AC5 combined — the ticket's own central deliverable. |

**Count check:** 9 SETTLED/cite-only (#1,2,5,6,9,14,15,16,17) + 1 verified-as-byproduct (#3) + 8
NEW/must-measure (#4,7,8,10,11,12,13,18) = 18. Matches the ticket's own "~18" count.

### Other risks

- **Zero-mutation / DB-isolation tension (Q2):** if Plan adopts the 3-call DB-isolation design, this
  is a first-of-its-kind write against the *shared* live cache DB by a measurement runner (Phase 1/
  Phase 2 only ever read it). It must be scoped narrowly (delete only the specific `packet_id` row
  this run itself just wrote, verified by primary key, never a blanket `DELETE FROM
  retrieval_context_packet_cache_rows`) and disclosed explicitly in the runner's own docstring and
  results doc, mirroring the existing "never touches" disclosure convention.
- **Manifest zero-mutation guard:** both prior runners check `knowledge-index/manifest.json`'s
  `built_at` before/after the run and abort if it changed mid-run (concurrent index rebuild). This
  ticket's runner should reuse the same guard (a real risk given the corpus run may take
  significantly longer than Phase 1/2's 2-call design if it grows to 3 calls per entry).
- **Cache DB state going into this run is not neutral:** any developer/agent exploratory use of the
  live gateway in this same working tree since the hotfix leaves real rows in
  `knowledge-index/retrieval_cache.db` (gitignored, untracked, per the hotfix ticket's own finding).
  The runner must either explicitly document the DB's pre-run state (row counts for both tables) or
  require/verify a clean state before the cold-call measurement, exactly as the hotfix ticket had to
  discover and correct for by hand.

## Anti-Drift Hazards

- Do not widen `ROUTING_TABLE`, shrink `budget_tokens` below the gateway's real default, or exclude
  any of the 7 corpus entries to manufacture a passing latency/token/recall result — identical
  discipline to both predecessor tickets' own explicit Out of Scope.
- Do not edit `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_router.py`,
  `tools/knowledge_gateway_packet_assembly.py`, or `tools/knowledge_gateway_cache.py` to add
  instrumentation — this ticket is measurement-only; any per-stage timing gap must be measured
  externally or disclosed as unmeasurable, never patched into the gateway itself.
- Do not overwrite `tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json` or
  `tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json` — both are frozen,
  historical, read-only inputs; this ticket's own output must be a **new**, separately-named fixture
  and results doc.
- Do not silently redefine which criteria count as "settled" to shrink this ticket's own measurement
  burden beyond what Q4's table above justifies — any change to that classification during
  Implementation must be re-justified in the ticket's own Implementation Notes, not applied silently.
- If Plan adopts the Q2 DB-isolation (3-call) design, do not let a raw `DELETE` touch any row this
  run did not itself just write — this is the one place this ticket's own tooling performs a write
  against a shared resource, and it must be exactly as narrowly scoped and disclosed as the
  reasoning above requires.

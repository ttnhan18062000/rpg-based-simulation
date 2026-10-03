---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT
artifact_type: plan
tags: [ai, mcp, testing]
---

# Implementation Plan — TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT

## Summary

This plan builds a new, standalone runner, `tools/agent-monitoring/kgmcp_phase3_gateway_runner.py`,
that runs the real, frozen 7-entry corpus through the real, live `_run_knowledge_context()` gateway
call path with a **4-call-per-entry** design (cold → Level-2-warm → [disclosed, narrowly-scoped SQL
row delete] → Level-1-warm → constrained-budget), captures 3 real externally-timed segments per
call via pass-through spies (never gateway-code edits), and honestly measures the 8 genuinely-new
§21 criteria Investigate identified (criteria #4, #7, #8, #10, #11, #12, #13, #18). It produces a
committed fixture and results doc mirroring Phase 2's own precedent, plus a new `INFRA-350` parity
entry certifying the measurement tool, not the measured performance. The plan resolves the
Level-1-warm-isolation problem by adopting Investigate's option (a) — the 3-call DB-isolation
technique — and explicitly rejects option (b) (calling Phase 2's `run_corpus()` live) as
**structurally broken today**, not merely weaker: Phase 2's own 2-call (cold, warm) design would,
if re-run now, hit the same problem this ticket exists to solve, because Level 2's cache-check
runs unconditionally before Level 1's on every call to `_run_knowledge_context()`
(`tools/knowledge_gateway_mcp.py:228-264`, confirmed by direct read) — a bare second call, whether
issued by Phase 2's runner or a naive caller, is always a Level-2 hit, never a Level-1 hit. Only an
explicit, disclosed removal of the Level-2 row between calls can force a genuine Level-1-warm
measurement in the current code shape.

## Resolution of the Level-1-Warm-Isolation Problem (binding on Step 2)

**Decision: adopt option (a), the 3-call-per-entry design with a disclosed, narrowly-scoped SQL
`DELETE`, as part of the 4-call-per-entry sequence below. Option (b) is rejected as unsound, not
merely as a weaker alternative.**

Reasoning, verified by direct read of the live code cited in `investigation.md`'s Current Behavior
section (`tools/knowledge_gateway_mcp.py:222-264`): the Level 2 cache-check (`:228-244`) runs
**before** the Level 1 cache-check (`:252-264`) on every call to `_run_knowledge_context()`, with no
parameter or code path that lets a caller skip Level 2 and reach Level 1 directly. A cold call
(call 1) writes both the Level 1 row (`perform_cache_write`, `:364-368`) and the Level 2 row
(`perform_context_packet_cache_write`, `:353-360`) on the same miss. Any subsequent call for the
same identity therefore always hits Level 2 first and returns `"cache": "HIT_L2"` at `:243-244`,
**structurally never reaching** Level 1's lookup at `:252`. This is true regardless of which script
issues the second call — Phase 2's own `kgmcp_phase2_gateway_runner.py::run_corpus()`, if invoked
live today (option (b)), would perform exactly this same cold-then-warm 2-call sequence
(`_run_single_entry`, `:194-217` of that file) and its own "warm" call would now be a genuine
Level-2 hit, not a Level-1 hit — the identical structural problem this ticket exists to solve,
merely relocated into a different, already-frozen file. Option (b) does not isolate Level 1; it
cannot, given the current call-order contract. It is not merely weaker than option (a); it is
factually incapable of producing the number it claims to produce.

The only way to observe a genuine, real, same-run Level-1-warm hit is to make Level 2 miss on
purpose between the Level-2-warm measurement and a subsequent call, using a disclosed, narrowly
scoped write against the runner's own just-written row — never a blanket delete, never touching
Level 1's table. `tools/retrieval_cache.py:335-336` confirms
`retrieval_context_packet_cache_rows` has `packet_id TEXT NOT NULL PRIMARY KEY` as its real,
unique primary key — the exact column this plan's `DELETE` targets by value, computed via the
runner's own call to the real, imported `compute_context_packet_lookup_identity()`
(`tools/knowledge_gateway_cache.py:420-458`, cited also for the fact that `packet_id` is a
deterministic hash over `(normalized_intent, entity_ids_json, repository_id, branch, budget_tokens,
query_key_hash)` — the identity is recomputable identically by the runner without needing the row
returned from a query). No other row is ever touched, and the delete is disclosed in the runner's
own module docstring, the results doc, and here.

## Steps

### Step 1 — New runner file skeleton, pure-helper imports only

**Files:** `tools/agent-monitoring/kgmcp_phase3_gateway_runner.py` (new)

**Change:** Create the new module mirroring `kgmcp_phase2_gateway_runner.py`'s own top-of-file
shape (module docstring, `sys.path` setup, `_load_gateway_module()` with a distinct
`sys.modules` key `"kgmcp_phase3_pilot_acceptance_gateway"` — distinct from both Phase 1's
`"kgmcp_phase1_comparison_gateway"` and Phase 2's `"kgmcp_phase2_recomparison_gateway"`, per DD8's
established precedent, `tools/agent-monitoring/kgmcp_phase2_gateway_runner.py:114-124`). Import,
never reimplement:
```python
from kgmcp_baseline_corpus import CORPUS, CORPUS_VERSION
from kgmcp_phase1_gateway_runner import (
    _compute_threshold_4_3,
    _normalize_phase1_source_id,
    _path_only,
)
from tools import knowledge_gateway_redaction as _kgr_redaction
```
Do **not** import anything callable from `kgmcp_phase2_gateway_runner.py` — its `_run_single_entry`
is entry-point-shaped around Phase 2's own fixed 2-call design and is not a pure, reusable helper
(confirmed by direct read, `tools/agent-monitoring/kgmcp_phase2_gateway_runner.py:156-269`: it
mixes spy installation, DB reads, and Phase-2-specific field naming inline, not separable into a
reusable primitive). Only `_read_hit_count`'s *shape* (direct read-only SQL against
`_kgc.rc.CACHE_DB_PATH`) is mirrored, not imported, since this ticket's own DB interaction (a
scoped Level 2 row read/delete against `retrieval_context_packet_cache_rows`) is a different table
than Phase 2's `retrieval_provider_result_cache_rows` read.

Module-level path constants: `_PHASE1_FIXTURE_PATH` (read-only), `_PHASE2_FIXTURE_PATH` (read-only,
`tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json`, consumed **only** for its
recorded `missing_sources` counts per entry — Step 7 — and explicitly **not** as this ticket's
Level-1-warm latency/token baseline, since that fixture's own data is the pre-hotfix 0/7
all-size-cap-rejected state, per `investigation.md`'s Prior Work section), `_OUTPUT_PATH` =
`tests/tools/fixtures/kgmcp_phase3_pilot_acceptance_measurement_results.json` (new, this ticket's
own committed fixture, mirroring `kgmcp_phase2_baseline_recomparison_results.json`'s naming
pattern), `_MANIFEST_PATH` (same `knowledge-index/manifest.json` zero-mutation guard input as both
predecessors).

**Do NOT touch:** `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_router.py`,
`tools/knowledge_gateway_packet_assembly.py`, `tools/knowledge_gateway_cache.py`,
`tools/agent-monitoring/kgmcp_phase1_gateway_runner.py`,
`tools/agent-monitoring/kgmcp_phase2_gateway_runner.py`,
`tools/agent-monitoring/kgmcp_baseline_corpus.py`, or any existing fixture/results doc.

**Verify:** `test_new_runner_never_edits_any_of_the_4_frozen_predecessor_files`,
`test_new_runner_imports_not_reimplements_phase1_and_phase2_pure_helpers`.

---

### Step 2 — 4-call-per-entry sequence with disclosed Level-2-row isolation delete

**Files:** `tools/agent-monitoring/kgmcp_phase3_gateway_runner.py`

**Change:** Implement `_run_single_entry(mod, _kgpa, _kgc, _kgr, corpus_entry: dict) -> dict`, the
per-entry driver. Sequence, all against `request = {"query": corpus_entry["query_text"]}` unless
noted:

1. **Call 1 (cold, default budget).** `routing_decision = _kgr.route(query_text)`;
   `identity = _kgc.compute_context_packet_lookup_identity(request, routing_decision,
   mod.DEFAULT_BUDGET_TOKENS)` (real function, `tools/knowledge_gateway_cache.py:420-458`, gives
   this run's own `packet_id` — recomputed independently by the runner, not read back from a row,
   so it is known correct before any row exists). Time
   `response_cold = mod._run_knowledge_context(query_text)` with `time.perf_counter()` (end-to-end
   segment 3). Expect `response_cold["cache"] == "MISS"`; if not, record a
   `cold_call_anomaly` exactly as Phase 2's own precedent does
   (`kgmcp_phase2_gateway_runner.py:199-206`) — a stale row from a prior manual run is disclosed,
   never silently normalized away. This call also writes both the Level 1 and Level 2 rows for this
   identity (`tools/knowledge_gateway_mcp.py:353-368`), which calls 2–4 below depend on.
2. **Call 2 (Level-2-warm, default budget).** Same `request`. Time
   `response_l2warm = mod._run_knowledge_context(query_text)`. Assert genuinely Level-2-hit via
   `response_l2warm.get("cache") == "HIT_L2"` **plus** a dual-signal check mirroring Phase 2's own
   DD2 discipline: an `assemble_packet` call-count spy (installed exactly like
   `kgmcp_phase2_gateway_runner.py:169-177`) must show **zero** calls across this one call, and a
   direct SQL read of `retrieval_context_packet_cache_rows.hit_count` for this `packet_id` (mirrors
   `_read_hit_count`'s shape, `:135-153`, retargeted at the Level 2 table/primary key) must show a
   delta of exactly 1. If either signal disagrees with `"HIT_L2"`, record a `signal_anomaly` and
   conservatively treat `cache_status_l2warm` as `"MISS"`, never assumed from the string alone. This
   is this ticket's central AC1/AC4 Level-2-hit measurement.
3. **Disclosed isolation delete.** Open a plain `sqlite3.connect(str(_kgc.rc.CACHE_DB_PATH))`
   connection (the same real, live singleton path `_read_hit_count`-style helpers already use) and
   execute exactly:
   ```sql
   DELETE FROM retrieval_context_packet_cache_rows WHERE packet_id = ?
   ```
   with `identity["packet_id"]` as the sole bound parameter — the exact primary key
   (`tools/retrieval_cache.py:336`) of the row this run's own call 1 just wrote for this exact
   identity, never a blanket delete, never a table-wide operation. Assert `cursor.rowcount == 1`
   before proceeding; if not 1 (0 or unexpected >1), record an `isolation_delete_anomaly` and skip
   call 4 for this entry (report `level1_warm_measurement: "SKIPPED — isolation delete did not
   affect exactly one row"` rather than fabricate a number). Commit and close. This is the one place
   this ticket's tooling writes to a shared resource — Level 1's own table
   (`retrieval_provider_result_cache_rows`) is never touched by this delete.
4. **Call 3 (Level-1-warm, default budget, freshly established).** Same `request`. With the Level 2
   row for this identity now gone, `_run_knowledge_context()`'s Level 2 check at `:228-244` misses
   and falls through to the Level 1 check at `:252-264`, which still holds the row call 1 wrote.
   Time `response_l1warm = mod._run_knowledge_context(query_text)`. Assert genuine Level-1-hit via
   `response_l1warm.get("cache") == "HIT"` plus the same dual-signal discipline, retargeted at
   `retrieval_provider_result_cache_rows.hit_count` (mirrors Phase 2's own `_read_hit_count`
   verbatim in shape, since this is exactly Level 1's own table). **This is the freshly,
   honestly (re)measured Level-1-warm number `investigation.md` Q2 found does not exist anywhere
   else in the repository as committed data** — it satisfies AC4's "clearly stated baseline"
   requirement's second half without relying on the stale pre-hotfix Phase 2 fixture.
5. **Call 4 (constrained-budget, distinct identity — Step 4).** See Step 4; a separate identity
   (different `budget_tokens` → different `packet_id`, `tools/knowledge_gateway_cache.py:435-449`)
   so it never interacts with or contaminates the 3-call series above.

Return a single per-entry raw dict carrying every response, every timing, both anomaly fields, and
the isolation-delete outcome — threshold/aggregate computation happens once per-entry raw data
exists, exactly mirroring Phase 2's `_run_single_entry`/`_compute_entry_thresholds` split
(`kgmcp_phase2_gateway_runner.py:156-269` / `:272-340`).

**Do NOT touch:** Any row not matching this run's own just-computed `packet_id`. Never issue a
second, redundant `DELETE` or any `UPDATE`/`INSERT` against `retrieval_context_packet_cache_rows`
or `retrieval_provider_result_cache_rows` outside what `_run_knowledge_context()` itself performs
internally on calls 1/3/4.

**Verify:** `test_per_entry_result_records_lookup_and_end_to_end_timings_as_distinct_fields`,
`test_end_to_end_ms_equals_sum_of_whichever_sub_stages_actually_ran`, plus a new guard test
(this ticket's own, mirroring the anti-drift discipline explicitly): `test_isolation_delete_only_
ever_removes_exactly_the_rows_this_run_itself_wrote` — asserts, via a pre/post row-count read of
`retrieval_context_packet_cache_rows` filtered to `packet_id != <this run's known set>`, that no
other row's count changed across the full corpus run.

---

### Step 3 — Per-stage timing via pass-through spies (3 real segments, not 5)

**Files:** `tools/agent-monitoring/kgmcp_phase3_gateway_runner.py`

**Change:** Per `investigation.md`'s Current Behavior section (confirmed: no
`time.perf_counter()` wrapping exists anywhere in `tools/knowledge_gateway_mcp.py` or
`tools/knowledge_gateway_cache.py` for Level 2, and "validation" is not a separate call boundary
from "lookup" inside `perform_context_packet_cache_lookup()`/`perform_cache_lookup()`, nor is
"assembly" separate from "fallback" inside `assemble_packet()`), only **3 real, externally-timeable
segments** exist without editing gateway code:

1. `lookup_and_validation_ms` — whichever of `_kgc.perform_context_packet_cache_lookup` (Level 2,
   calls 1/2/4) or `_kgc.perform_cache_lookup` (Level 1, call 3, after the Level 2 row is gone)
   actually executes for a given call.
2. `fallback_and_assembly_ms` — `_kgpa.assemble_packet`, only executes on a genuine full miss
   (call 1, and call 4 since it is a fresh identity); `None` on any hit call (2, 3).
3. `end_to_end_ms` — `time.perf_counter()` wrapped directly around the whole
   `_run_knowledge_context(query_text)` call, exactly as both prior runners already do.

Implementation: extend the existing pass-through-spy technique
(`kgmcp_phase2_gateway_runner.py:169-188`, already proven and already trusted by this repo's test
suite) so each spy also records its own elapsed `time.perf_counter()` span, not just a call count.
Install spies on `_kgc.perform_context_packet_cache_lookup`, `_kgc.perform_cache_lookup`, and
`_kgpa.assemble_packet` for the duration of each `_run_knowledge_context()` call, restored in a
`finally` block exactly as Phase 2's precedent does. This avoids any duplicate, timing-only direct
call to those functions (which would double-count Level 2's own `record_context_packet_cache_hit()`
side effect, `tools/knowledge_gateway_cache.py:528`, if the runner instead called the sub-function
directly *and* let `_run_knowledge_context()` call it again) — the spy observes the exact same,
single, real call the gateway itself makes, with zero duplication and zero gateway-code edits.

**This is the disclosed instrumentation-granularity limit relative to §21's closing bullet's "5
stages" wording (lookup, validation, fallback, assembly, end-to-end):** the results doc and the
report dict must state explicitly that "validation" is folded into "lookup" and "assembly" is
folded into "fallback," because no externally observable call boundary separates them in the
current code, and that this is a genuine limit of measurement-only tooling, not a shortfall in
measurement effort. Per `measurement_baseline_contract.md` §2.5's reconciliation rule
(`investigation.md`, Mechanics/Engine Constraints), `end_to_end_ms` for a given call must be
commensurate with the sum of whichever of the other 2 segments actually ran for that call — this is
a tolerance-band assertion in the guard test below, not exact equality (real wall-clock overhead
exists between spy-measured sub-calls and the outer wrap).

**Do NOT touch:** Do not add any `time.perf_counter()` call inside
`tools/knowledge_gateway_mcp.py` or `tools/knowledge_gateway_cache.py` themselves — all timing is
external, via spies installed and restored entirely within the runner process.

**Verify:** `test_per_entry_result_records_lookup_and_end_to_end_timings_as_distinct_fields`,
`test_end_to_end_ms_equals_sum_of_whichever_sub_stages_actually_ran`.

---

### Step 4 — Budget-tolerance measurement against a real constrained request (AC2)

**Files:** `tools/agent-monitoring/kgmcp_phase3_gateway_runner.py`

**Change:** For every corpus entry, issue one additional real call,
`response_constrained = mod._run_knowledge_context(query_text, budget_tokens=1000)` — a value well
below `DEFAULT_BUDGET_TOKENS = 4000` (`tools/knowledge_gateway_mcp.py:91`), timed the same way as
calls 1–3. Because `budget_tokens` is part of Level 2's own identity hash
(`tools/knowledge_gateway_cache.py:435,444`) and Level 1's `budget_class` derivation, this is
structurally guaranteed to be a fresh identity distinct from calls 1–3's, so it never reads or
writes the same row those calls use — no interference with the isolation-delete sequence in Step 2.

Compute `full_payload_tokens = _kgpa.kgmcp_char_heuristic_v1(json.dumps(response_constrained))`
over the **full response payload** — never `response_constrained["budget_returned"]`. Per
`investigation.md`'s Current Behavior citation of `assemble_within_budget()`
(`tools/knowledge_gateway_packet_assembly.py:584-611`), `budget_returned` is a running-cost
accumulation over `statements[]` only (`:598-611`, confirmed by direct read: `running_total` only
ever accumulates `kgmcp_char_heuristic_v1(statement.text)` for included statements) and is
`<= budget_requested` **by construction** — it is not a bound on `context[]`, `evidence[]`, or
`conflicts[]`, so using it here would make AC2 trivially pass regardless of real gateway behavior.

Report `pass = full_payload_tokens <= budget_tokens_requested * 1.2` using the documented ±20%
tolerance from `redaction_retention_policy.md` §8 (`docs/engine/contracts/knowledge_gateway_mcp/
redaction_retention_policy.md:220-238`, "This tolerance is the standard against which a future
implementation validates the Phase 3 pilot's 'returned content respects the requested budget within
a documented tolerance' acceptance bar" — cited verbatim, not a new tolerance invented here) —
**honestly, whatever the result.** Given `context[]`/`evidence[]`/`conflicts[]` are unbudgeted by
construction, a real FAIL here (full payload well over the constrained budget) is a plausible,
legitimate outcome and must be reported as such, not massaged.

**Do NOT touch:** Do not shrink `budget_tokens` below a realistic value to try to force a pass, and
do not substitute `budget_returned` for the full-payload measurement described above (this repo's
existing anti-drift discipline against exactly this substitution, per `test_plan.md`'s
"Budget-tolerance honesty guard").

**Verify:** `test_constrained_budget_request_shape_is_used_for_at_least_one_real_corpus_call`,
`test_full_response_payload_tokens_reported_against_requested_budget_with_documented_tolerance`.

---

### Step 5 — Conflict-visibility measurement, with honest zero-conflict disclosure (AC3)

**Files:** `tools/agent-monitoring/kgmcp_phase3_gateway_runner.py`

**Change:** For every entry, read `len(response_cold.get("conflicts", []))` from call 1's real
response (representative — `build_conflicts()`'s structural detection,
`tools/knowledge_gateway_packet_assembly.py:558-579`, produces identical output regardless of which
call retrieves it, since Level 2/Level 1 replay the value verbatim rather than recompute it,
confirmed by `_context_packet_row_to_response()`'s `json.loads(row["conflicts"])` at
`tools/knowledge_gateway_cache.py:489`). Sum across all 7 entries into
`total_conflicts_observed_in_corpus`. Build a report sub-object:
```python
{
    "total_conflicts_observed_in_corpus": <int>,
    "conflicts_observed_in_corpus": <bool>,  # total > 0
    "per_entry_conflict_counts": {...},
    "limitation_note": (
        "build_conflicts() is structural (explicit supersession/deprecation-marker detection in "
        "source docs, tools/knowledge_gateway_packet_assembly.py:558-579), not automatic "
        "cross-provider factual-value comparison. The frozen 7-entry corpus was designed around "
        "§8 routing-shape coverage, not conflict-shape coverage, so 0 real conflicts across all 7 "
        "entries is a plausible, honest outcome. If total is 0, this criterion's visibility "
        "mechanism itself remains separately unit-tested (build_conflicts()'s own test suite), but "
        "this real corpus does not naturally exercise a real conflict occurrence — this is "
        "disclosed as a genuine corpus-coverage limitation, never silently marked satisfied."
    ) if <total == 0> else None,
}
```
This field must exist and be populated identically whether the true count is 0 or nonzero — it is
never conditionally omitted on a 0 result.

**Do NOT touch:** Do not add a synthetic 8th corpus entry, an embedding/keyword-overlap heuristic,
or any change to `build_conflicts()` to try to manufacture a nonzero result — explicitly
out of scope per the ticket.

**Verify:** `test_conflicts_field_is_inspected_for_every_real_corpus_response`,
`test_zero_observed_conflicts_is_reported_as_a_disclosed_corpus_limitation_not_a_pass`.

---

### Step 6 — Latency/token aggregate vs. justified baseline(s), median-based, honest FAIL-capable (AC4)

**Files:** `tools/agent-monitoring/kgmcp_phase3_gateway_runner.py`

**Change:** Report **both** baselines per `investigation.md` Q2's recommendation (do not silently
pick one):
- **Phase 1 cold** — real, committed, `tests/tools/fixtures/kgmcp_phase1_baseline_comparison_
  results.json`'s per-entry `gateway_wall_time_ms`/`gateway_tokens`.
- **This run's own freshly-measured Level-1-warm** — call 3's `end_to_end_ms` / full-payload token
  count, established in Step 2 (never the stale pre-hotfix Phase 2 fixture, per Step 1's citation).

For each baseline, compute `statistics.median` (not `statistics.mean` — §21's closing bullet says
"median" explicitly, unlike §4.1/§4.2's own mean-based formulas per `test_plan.md`'s median-vs-mean
guard) of this run's call-2 (Level-2-warm) `end_to_end_ms` across all 7 entries, and compare against
the chosen baseline's own median. Same for full-payload token counts. Record, per numeric threshold
reported, a non-empty `derivation` string naming exactly which baseline(s) it was computed against
— mirrors both predecessor runners' own `derivation` field convention
(`kgmcp_phase1_gateway_runner.py:250-258`, `kgmcp_phase2_gateway_runner.py:279-289`).

`pass = (median(l2_warm_end_to_end_ms) < median(baseline_end_to_end_ms)) and
(median(l2_warm_full_payload_tokens) < median(baseline_full_payload_tokens))`, computed
independently against each of the two baselines, reported as two distinct pass/fail pairs (never
merged into one ambiguous flag) — **and reported honestly as FAIL if the real numbers do not show
an improvement**, per AC4's explicit wording. The aggregate-computation function must be
structurally capable of returning `pass: False` (verified by a synthetic-input guard test feeding a
case where Level 2's numbers are worse).

**Do NOT touch:** Do not silently substitute the stale pre-hotfix Phase 2 fixture
(`kgmcp_phase2_baseline_recomparison_results.json`) as if it were a genuine Level-1-warm baseline —
Step 1's citation of `investigation.md`'s Prior Work section established that fixture's own
per-entry numbers are all size-cap-rejected non-hits, not representative of a genuine warm path.

**Verify:** `test_baseline_choice_is_recorded_with_explicit_derivation_string`,
`test_median_not_mean_is_used_for_the_closing_criterion`,
`test_fail_result_is_reported_honestly_when_synthetic_input_shows_no_improvement`.

---

### Step 7 — Recall recomputation vs. both predecessors' recorded counts (AC5)

**Files:** `tools/agent-monitoring/kgmcp_phase3_gateway_runner.py`

**Change:** Using call 1's `response_cold["context"]` and the imported, unmodified
`_compute_threshold_4_3(baseline_sources, gateway_sources_raw)` (never reimplemented — same
function Phase 1 defined and Phase 2 already imports, `kgmcp_phase1_gateway_runner.py:165-207`),
compute this run's own recall result per entry against the Phase 0 fixture's
`context_search.sources_recalled` baseline (same baseline source both predecessors use — read via
`_PHASE0_FIXTURE_PATH`, itself read-only, never edited). Then compare this run's `missing_sources`
count against **both** predecessors' own recorded counts:
- Phase 1's recorded `threshold_4_3_recall.missing_sources` (from
  `kgmcp_phase1_baseline_comparison_results.json`).
- Phase 2's recorded `threshold_4_3_recall_cold.missing_sources` (from
  `kgmcp_phase2_baseline_recomparison_results.json` — its cold-path recall number, which remains a
  valid comparison point regardless of that fixture's own warm-path cache-hit limitation, since
  §4.3 there was explicitly computed from the cold response only).

Record a `recall_missing_count_comparison` string naming this run's count alongside both
predecessors' counts (extends `kgmcp_phase2_gateway_runner.py`'s own
`recall_missing_count_comparison_to_phase1` field precedent, `:400-403`, to compare against both).
**Any regression relative to either predecessor (this run's `missing_sources` count higher than
either recorded count for the same entry) must be flagged explicitly** via a
`recall_regression_flag: true` field on that entry, not glossed over.

**Do NOT touch:** `tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json` or
`tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json` — both read-only inputs.

**Verify:** `test_recall_reuses_compute_threshold_4_3_against_both_phase1_and_phase2_recorded_counts`,
`test_recall_regression_relative_to_either_predecessor_is_flagged_not_glossed_over`.

---

### Step 8 — Real-corpus-scale invalidation re-verification (AC6)

**Files:** `tools/agent-monitoring/kgmcp_phase3_gateway_runner.py`,
`tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py` (new)

**Change:** Four sub-measurements, run once against real corpus entries (not the full 7 — at least
one representative entry each, per `test_plan.md`'s own scoping):

1. **Stale rejection.** Pick one entry whose call 1 `response_cold["context"]` has at least one real
   `path` field. Call `mod._run_knowledge_context(query_text, changed_paths=[that_path])` — a real,
   live call. Assert the response is genuinely refreshed (`cache` is `"MISS"` or a fresh non-`HIT_L2`
   result, not a stale serve) — this exercises `revalidate_context_packet_row()`'s working-tree-
   overlap rule (`tools/knowledge_gateway_cache.py:267-268`) through the real, live gateway, not a
   synthetic row dict.
2. **Unrelated-change non-invalidation.** Same entry, `changed_paths=["<a path known NOT among that
   entry's cited evidence>"]`. Assert the call is still a genuine hit (`HIT_L2` or `HIT`).
3. **Branch partition.** Call `_kgc.revalidate_context_packet_row(row, ..., current_repository_id=
   identity["repository_id"], current_branch="a-different-synthetic-branch", ...)` directly against
   a real, just-written row (real function, real data) with a synthetic incompatible
   `current_branch` argument. Assert `False`. Per `investigation.md` Q3 and `test_plan.md`, this
   must be labeled in its own docstring and in the results doc as testing the real revalidation
   function directly, not a full round trip with an actual second git branch — the 7-entry corpus
   cannot organically produce a second incompatible branch.
4. **Uncommitted-change invalidation.** Reuses sub-measurement 1's mechanism verbatim (`changed_paths`
   is the gateway's only representation of "uncommitted changes" — no separate git-diff mechanism
   exists, confirmed by `investigation.md`'s Mechanics/Engine Constraints citation of the
   `evidence_cache_identity_contract.md` §5 rules `revalidate_context_packet_row()` implements).
   Report this explicitly as sharing sub-measurement 1's evidence, **never double-counted** as two
   independent real-world verifications.

**Do NOT touch:** Do not fabricate a second real git branch or actual uncommitted working-tree
changes to exercise sub-measurement 3 "for real" — the synthetic-argument direct-function call is
the legitimate, disclosed technique per Investigate's own finding, mirroring the sibling wiring
ticket's own test technique.

**Verify:** `test_stale_rejection_verified_against_a_real_changed_cited_source_for_at_least_one_real_entry`,
`test_unrelated_changed_path_does_not_invalidate_a_real_cached_packet`,
`test_branch_partition_verified_with_a_real_but_synthetic_incompatible_branch_scope`,
`test_uncommitted_change_invalidation_verified_with_a_real_changed_paths_argument`.

---

### Step 9 — Zero-mutation guards and pre-run cache-DB state disclosure

**Files:** `tools/agent-monitoring/kgmcp_phase3_gateway_runner.py`

**Change:** Before the corpus loop, read and record `pre_run_manifest_built_at` (same
`_load_manifest_built_at()` pattern as both predecessors) and pre-run row counts for both
`retrieval_context_packet_cache_rows` and `retrieval_provider_result_cache_rows` (a direct
`SELECT COUNT(*)` against each, read-only) — disclosed in the output dict as
`pre_run_cache_db_state`, since `investigation.md`'s Risk section establishes the DB's state going
into this run is not neutral (any prior exploratory gateway use leaves real rows). After the corpus
loop, re-read `manifest_built_at` and raise (never write output) if it changed mid-run, exactly
mirroring `kgmcp_phase2_gateway_runner.py:420-427`'s existing guard.

**Do NOT touch:** Do not pre-clear or seed the cache DB before the run — report its real starting
state honestly instead, exactly as both predecessors do.

**Verify:** Reuses the existing `test_zero_mutation_of_agent_monitoring_and_manifest_across_full_run`
pattern from the Phase 2 test suite, mirrored into the new test file for this runner.

---

### Step 10 — Aggregate assembly, `main()`, committed fixture, results doc

**Files:** `tools/agent-monitoring/kgmcp_phase3_gateway_runner.py`,
`tests/tools/fixtures/kgmcp_phase3_pilot_acceptance_measurement_results.json` (new, committed),
`docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md` (new)

**Change:** `run_corpus()` orchestrates Steps 2–9 across all 7 entries, mirroring
`kgmcp_phase2_gateway_runner.py:343-445`'s own top-level shape (loads fixtures, derives thresholds
live, loops `CORPUS`, raises on manifest drift, computes aggregate, returns the full report dict).
`main()` writes `_OUTPUT_PATH` with `json.dumps(report, indent=2, sort_keys=True) + "\n"`, exactly
mirroring both predecessors' own `main()` (`kgmcp_phase2_gateway_runner.py:470-479`). Run once, by
hand, during Implementation — never wired into pytest's fast loop, per both predecessors' own
documented convention and `test_plan.md`'s Scoped Pytest Commands section.

The new results doc `phase3_pilot_acceptance_measurement.md` follows
`phase2_baseline_recomparison.md`'s exact precedent shape: headline table (per §21 criterion #4,
#7, #8, #10, #11, #12, #13, #18 — the 8 genuinely-new ones from Investigate's Q4 table), per-
criterion sections citing real numbers, an explicit disclosed-limitations section (3-segment timing
vs. the proposal's 5-name wording; conflict-corpus-coverage; branch-partition synthetic-argument
technique), and a plain honest-verdict section stating pass/fail per criterion — never
characterizing Phase 3 as more successful than the real numbers support, per AC7.

**Do NOT touch:** `docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md` or
`phase1_baseline_comparison.md` — both are frozen, historical, never edited by this ticket.

**Verify:** Manual review against AC7's "no criterion redefined, no entry excluded" requirement;
`done-checker`'s frontmatter validation on the new doc.

---

### Step 11 — New test file: architecture guards, unit tests, integration tests

**Files:** `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py` (new)

**Change:** Implement every test named in `test_plan.md`'s "New Tests Required" section (18 tests
across AC1–AC6, plus the Step 2 isolation-delete guard added above), mirroring
`test_kgmcp_phase2_baseline_recomparison.py`'s own structure (frozen-file diff guards via
`git diff --stat HEAD`, pure-helper identity-check guards via `is`, synthetic-input unit tests for
honesty guards, real-call integration tests for corpus-scale re-verification). Scoped pytest
command exactly as `test_plan.md`'s "Scoped Pytest Commands" section specifies.

**Do NOT touch:** `tests/tools/test_kgmcp_phase1_baseline_comparison.py`,
`tests/tools/test_kgmcp_phase2_baseline_recomparison.py`.

**Verify:** The scoped pytest command in `test_plan.md` passes in full.

---

### Step 12 — `INFRA-350` parity ledger entry (tool-certifies, not performance-certifies)

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Append a new entry with `id: INFRA-350` (confirmed next-available: the current highest
observed ID is `INFRA-349`, `docs/parity_ledger/infrastructure.yaml:9787` — re-verify live at
Parity phase since sibling tickets may land entries first). Mirror `INFRA-344`'s exact shape and
framing (`docs/parity_ledger/infrastructure.yaml:9339-9427`): `text` describes the runner's own
4-call design, the disclosed isolation-delete technique, the 3 real timing segments, and states
explicitly **"This entry certifies the measurement tool itself as real, correct, and tested — it
does NOT claim the measured cache/gateway performance succeeded"** (verbatim framing, `INFRA-344`
precedent), followed by the tool's own real, honest output summary (whatever Step 10's real run
produces — not pre-written here). `v2_evidence` cites the new runner file's own function line
ranges (filled in at Parity time from the real, finished file) plus the committed fixture path and
the new results doc path. `status: verified`, `priority: P1` (matching both cited precedents).
`test_path` cites the new test file. `divergence_note: null` unless Step 4's or Step 6's real
results reveal a genuine intentional divergence worth recording separately (unlikely for a
measurement-only ticket — if it arises, route through `docs/guidelines/intentional_divergences.md`
per CLAUDE.md, as a follow-up, not silently folded into this entry).

**Do NOT touch:** `INFRA-344` or `INFRA-345` — cited, never edited.

**Verify:** `test_new_infrastructure_parity_entry_is_schema_valid`.

---

## Scope Guards

- Never edit `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_router.py`,
  `tools/knowledge_gateway_packet_assembly.py`, or `tools/knowledge_gateway_cache.py` — no
  instrumentation, no behavior change, no timing hooks added to any of the four. All timing is
  external (spies + `time.perf_counter()` wraps living entirely in the new runner file).
- Never edit `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py`,
  `tools/agent-monitoring/kgmcp_phase2_gateway_runner.py`, or
  `tools/agent-monitoring/kgmcp_baseline_corpus.py` — import pure helpers only.
- Never edit `tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json`,
  `tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json`,
  `tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json`, or either predecessor's
  results doc under `docs/engine/contracts/knowledge_gateway_mcp/` — all are frozen, historical,
  read-only inputs.
- Never widen `ROUTING_TABLE`, exclude any of the 7 corpus entries, or redefine any §21 criterion to
  manufacture a favorable result.
- The one write this ticket's tooling performs against a shared resource — the Step 2/3
  `DELETE FROM retrieval_context_packet_cache_rows WHERE packet_id = ?` — must never touch a row
  this run did not itself just write, verified by the `rowcount == 1` check and the
  `test_isolation_delete_only_ever_removes_exactly_the_rows_this_run_itself_wrote` guard. Never a
  blanket `DELETE`, never against `retrieval_provider_result_cache_rows`.
- Do not fix any criterion found to fail — this ticket measures and reports only; a fix is a
  separate, later, human-scoped ticket.
- Do not declare Phase 3 "production-capable" or close the parent epic — that is a human reviewer's
  call, not this ticket's.
- Do not add a synthetic 8th corpus entry or fabricate conflict data to satisfy AC3.
- Do not silently reclassify any of Investigate Q4's 9 SETTLED / 1 verified-as-byproduct criteria as
  needing fresh measurement, or any of the 8 NEW criteria as already-settled, without re-justifying
  the change in Implementation Notes.

## Dependency Map

- Step 1 has no dependencies; every other step depends on Step 1's imports/skeleton existing.
- Step 2 (call sequence + isolation delete) must land before Steps 3, 5, 6, 7, and 8, since all of
  them consume per-entry raw data `_run_single_entry` produces.
- Step 3 (timing spies) is implemented inside Step 2's call sequence — practically the same change,
  ordered second only for narrative clarity in this plan.
- Step 4 (budget measurement) is independent of Steps 2/3/5/6/7/8 — a distinct identity, a distinct
  call, addable in any order once Step 1 exists.
- Step 9 (zero-mutation guards) wraps the whole corpus loop and can be added any time before Step
  10's `run_corpus()` is finalized.
- Step 10 depends on Steps 2–9 all being in place (it aggregates their outputs).
- Step 11 (tests) depends on Steps 1–10 all existing, since several tests call the real runner
  functions directly.
- Step 12 (parity entry) depends on Step 10's real, committed output existing — the entry cites
  real numbers, never pre-written speculative ones.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — per-stage timings for all 7 entries, HIT_L2 path | Steps 2, 3 | `test_per_entry_result_records_lookup_and_end_to_end_timings_as_distinct_fields`, `test_end_to_end_ms_equals_sum_of_whichever_sub_stages_actually_ran` |
| AC2 — budget-respecting behavior, constrained `budget_tokens` | Step 4 | `test_constrained_budget_request_shape_is_used_for_at_least_one_real_corpus_call`, `test_full_response_payload_tokens_reported_against_requested_budget_with_documented_tolerance` |
| AC3 — conflict visibility checked and reported | Step 5 | `test_conflicts_field_is_inspected_for_every_real_corpus_response`, `test_zero_observed_conflicts_is_reported_as_a_disclosed_corpus_limitation_not_a_pass` |
| AC4 — median latency/tokens vs. justified baseline, honest FAIL | Steps 2 (Level-1-warm isolation), 6 | `test_baseline_choice_is_recorded_with_explicit_derivation_string`, `test_median_not_mean_is_used_for_the_closing_criterion`, `test_fail_result_is_reported_honestly_when_synthetic_input_shows_no_improvement` |
| AC5 — recall recomputed vs. Phase 1/Phase 2 recorded counts | Step 7 | `test_recall_reuses_compute_threshold_4_3_against_both_phase1_and_phase2_recorded_counts`, `test_recall_regression_relative_to_either_predecessor_is_flagged_not_glossed_over` |
| AC6 — stale-rejection/unrelated-change/branch-partition/uncommitted-change at corpus scale | Step 8 | `test_stale_rejection_verified_against_a_real_changed_cited_source_for_at_least_one_real_entry`, `test_unrelated_changed_path_does_not_invalidate_a_real_cached_packet`, `test_branch_partition_verified_with_a_real_but_synthetic_incompatible_branch_scope`, `test_uncommitted_change_invalidation_verified_with_a_real_changed_paths_argument` |
| AC7 — honest Completion Summary if any criterion missed | Step 10 (results doc), ticket's own Completion Summary | `done-checker` at Finalize (no pytest test) |
| AC8 — schema-valid `INFRA-350` parity entry, tool-certifies not performance-certifies | Step 12 | `test_new_infrastructure_parity_entry_is_schema_valid` |

## Anti-Drift Notes

- The Level 2 cache-check runs **unconditionally before** Level 1's on every
  `_run_knowledge_context()` call (`tools/knowledge_gateway_mcp.py:228-264`) — this is why a bare
  repeated call can never observe a genuine Level-1-warm state, and why Investigate's option (b)
  (calling Phase 2's `run_corpus()` live) does not actually solve the problem: Phase 2's own 2-call
  design would hit the identical structural wall today. Do not reintroduce option (b) as an
  "easier" alternative during Implementation without re-deriving why it fails, stated above.
- `budget_returned` is a `statements[]`-only running total, `<= budget_requested` **by
  construction** (`assemble_within_budget()`, `tools/knowledge_gateway_packet_assembly.py:584-611`)
  — never use it as AC2's compliance signal; always measure the full serialized response payload.
- `build_conflicts()` is purely structural (explicit supersession/deprecation markers), never
  automatic cross-provider factual comparison — a real 0/7 conflict result across the corpus is
  plausible and must be disclosed as a corpus-coverage limitation, not silently marked satisfied.
- The Step 2 isolation `DELETE` is the one place this ticket's tooling writes to a shared resource.
  It must be scoped to exactly one row (`packet_id` primary key, `rowcount == 1` verified) and
  disclosed in the runner's own module docstring, the results doc, and the `INFRA-350` entry — not
  hidden as an implementation detail.
- Do not use the pre-hotfix `kgmcp_phase2_baseline_recomparison_results.json` fixture's own
  latency/token numbers as a genuine Level-1-warm baseline anywhere in this ticket's output — that
  fixture's data is a 0/7 all-size-cap-rejected state, cited only for its still-valid cold-path
  recall numbers (Step 7).
- §21's closing bullet names 5 stages by word ("lookup, validation, fallback, assembly, and
  end-to-end"); this ticket's runner reports 3 real, externally-timed segments
  (`lookup_and_validation_ms`, `fallback_and_assembly_ms`, `end_to_end_ms`) and must disclose this
  explicitly as an instrumentation-granularity limit of measurement-only tooling, never silently
  presented as if 5 independent numbers were produced.

## Deviations (recorded during Implementation)

Two deviations from this plan's literal text, both real, both disclosed here, in the ticket's own
Implementation Notes, and in the results doc — neither changes the plan's substance or intent.

1. **Frozen-file guard technique (Steps 1/11).** This plan and `test_plan.md` describe a
   `git diff --stat HEAD` substring guard, mirroring Phase 1/Phase 2's own test files exactly. At
   Implementation time, the working tree already had several sibling Phase 3 tickets' legitimate,
   Architecture-Review-approved, uncommitted diffs to `tools/knowledge_gateway_cache.py`,
   `tools/knowledge_gateway_mcp.py`, and `tools/retrieval_cache.py` present (from
   `PACKET-CACHE-SCHEMA-MIGRATIONS`, `PACKET-DEDUP-BUDGET-ENFORCEMENT`,
   `PACKET-DEPENDENCY-INVALIDATION`, `PACKET-CACHE-READ-WRITE-WIRING`, all done/stored earlier in
   this same session). A literal `git diff --stat HEAD` substring check would flag these paths
   regardless of whether this ticket itself touched them — confirmed as a real, live false
   positive: Phase 1/Phase 2's OWN `test_no_frozen_kgmcp_dependency_edited` tests independently
   fail today for this exact, unrelated reason. This ticket's own guard test
   (`test_new_runner_never_edits_any_frozen_predecessor_file_or_fixture`) instead snapshots each
   of the 9 frozen dependencies' SHA-256 content hash at the start of Implementation and asserts
   byte-identity — strictly more precise for this ticket's own specific claim, and immune to
   sibling-ticket noise in a shared multi-ticket working tree.

2. **One-time, disclosed corrective clear of the shared cache DB (Step 9).** Step 9 explicitly
   forbids pre-clearing `knowledge-index/retrieval_cache.db`. During Implementation, the
   implementer's own necessary iterative testing of this brand-new runner (validating the 4-call
   sequence and AC6 sub-measurements before committing to a final run) executed the full corpus
   loop 3 times against this exact shared DB before the final run. Because the isolation-delete
   technique has a real, disclosed, one-way side effect (documented in this plan's own Resolution
   section above — once a default-budget identity's Level 2 row is deleted and its Level 1 row
   remains valid, Level 1 satisfies every subsequent lookup, and Level 2 can never be regenerated
   for that identity again within the same uncleared DB), those 3 testing invocations
   progressively degraded the DB into a state where a final, honest, all-fresh measurement was no
   longer achievable without intervention. This is qualitatively different from "someone else's
   prior exploratory use left rows" (which Step 9 correctly forbids working around) — it is the
   implementer's own tool-development testing exhausting the one property the central AC1/AC4
   measurement depends on, with direct precedent in
   `TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION`'s own "discovered and corrected for by
   hand" clearing (cited in `investigation.md`'s own Prior Work section). A one-time,
   unconditional `DELETE FROM` both cache tables (verified by real pre/post row counts) was
   performed once, manually, outside the runner itself, immediately before the single, final
   `main()` invocation that produced the committed fixture and results doc. Fully disclosed in the
   results doc's own dedicated section and in `pre_run_cache_db_state`, not hidden.

---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON
artifact_type: plan
tags: [ai, mcp, testing]
---

# Implementation Plan — TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON

## Summary

This ticket runs the real 7-entry frozen corpus through the now-cache-wired gateway twice per
entry (cold, then warm) and reports §4.1/§4.2/§4.3 against the real numbers — honestly, including
the real possibility that the warm call never becomes a genuine cache hit for some or all entries
because every entry's real response payload (10.6–30.5 KB, per the already-committed Phase 1
fixture) exceeds the §5 `MAX_PAYLOAD_BYTES = 8192` cache-write size cap
(`tools/knowledge_gateway_redaction.py:68,179-184`). The plan's central, load-bearing call —
whether to shrink the per-entry `budget_tokens` request field to try to get under that cap, or to
keep exact request-shape parity with Phase 1 and report whatever fraction of entries genuinely
cache — is **not decided unilaterally here**; DD1 states a reasoned recommendation (keep parity,
option (b)) and flags it explicitly for Architecture Review's ruling before Implement proceeds,
mirroring how the sibling cache-wiring ticket's own DD3/DD4/DD5 were handled. New code: one runner
script (a new sibling file, never an in-place edit to the Phase 1 runner), one fixture, one results
doc, one structural test suite, one parity ledger entry, one appended proposal-doc paragraph. No
frozen gateway/router/packet-assembly/cache/redaction module is edited — every interaction with
those modules is either a plain read-only import/call or a read-only spy (direct attribute
reassignment, restored in `finally`, never `unittest.mock`) on the exact same shared module objects
those modules already use internally.

## Design Decisions

### DD1 — Request shape under the size cap: **RECOMMENDATION is option (b) — exact Phase 1 parity, no `budget_tokens` override — flagged for Architecture Review's explicit ruling**

**The finding, re-confirmed by direct read during Plan (not just inherited from investigation):**
`tools/knowledge_gateway_redaction.py:264-298` (`evaluate_write_candidate`) runs allowlist → redact
→ secret-scan → `check_size_cap(redacted)` (`:287-288`, calling `:179-184`'s `len(redacted_payload
.encode("utf-8")) <= MAX_PAYLOAD_BYTES` where `MAX_PAYLOAD_BYTES = 8192`, `:68`) → never-cache →
ALLOW. A `False` size-cap check returns `WriteDecision(REJECT, "oversized_payload", None, None,
...)` (`:288`) — no truncation, no retry. `tools/knowledge_gateway_cache.py::perform_cache_write()`
(`:262-336`) only calls `rc.write_provider_result_cache(...)` when `decision.verdict == rk.ALLOW`
(`:306-308`); any REJECT is a silent `return` (`:308`), and the caller
(`tools/knowledge_gateway_mcp.py:320-324`) wraps the whole call in `try/except: pass` and always
sets `response["cache"] = "MISS"` beforehand (`:319`) regardless of outcome. Every one of the 7
corpus entries' real `gateway_tokens` under the default 4000-token budget (2649–7633, per the
committed `tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json`) implies a
serialized byte size 10.6–30.5 KB — well over the 8192-byte cap even before subtracting the two
excluded keys or applying `redact_content()`'s near-no-op rewrite for this repo's own
already-relative path content. **Under the default (unmodified) request shape, `perform_cache_write`
will REJECT the write for some or all of the 7 entries, and the "warm" call for those entries will
structurally be a second cold call, not a genuine hit.**

**Option (a) — shrink `budget_tokens` per entry.** `budget_tokens` is a real, existing, optional
keyword argument of the already-frozen `_run_knowledge_context()`
(`tools/knowledge_gateway_mcp.py:149-152`, `165-166`, `190`) — passing a smaller value is a request-
parameter choice, not an edit to any file named in the ticket's Out of Scope bullet ("Any change to
`tools/knowledge_gateway_mcp.py`... or the cache read/write code"). On the letter of that bullet,
option (a) is in-scope. It would also answer a real, narrower, legitimate question — "does the
cache mechanism work at all for a payload within its designed limit" — that is a genuine thing to
disclose and report.

**Option (b) — keep exact Phase 1 parity (no `budget_tokens` override).** Report per entry,
honestly, whichever of {genuine HIT, size-cap-blocked MISS, other-reason MISS} actually occurred —
including the real possibility that 0/7 entries ever reach a genuine warm state.

**Why this plan recommends (b), not (a):**
1. The ticket's own Scope frames this run as "the other half of Phase 2's own bargain" — running
   "the same 7-entry corpus" to get "the fair comparison Phase 1's own cold-only measurement
   couldn't make." The comparability this buys is against Phase 1's own cold numbers and Phase 0's
   own thresholds (935.32 ms / 1263.57 tokens), both of which were computed from full-size,
   default-budget responses. A deliberately smaller-budget response is faster to assemble/serialize
   and smaller to transmit for reasons that have nothing to do with caching — it would make §4.1
   easier to pass and §4.2 easier to satisfy on both the cold *and* warm side for a reason unrelated
   to the thing being measured (cache effectiveness), silently improving the odds of a pass on a
   different axis than the one the epic actually cares about.
2. The ticket's own AC2 text ("§4.1 is computed against the warm-path numbers and reported
   honestly, whatever the result") and the investigation's own framing ("the real possibility that
   0/7 entries ever produce a genuine warm state is itself a legitimate, informative,
   honestly-reportable finding, directly analogous to Phase 1's own 'Phase 1 cannot produce a
   warm-hit state at all' honest caveat") both anticipate and accept a 0/7 outcome as valid — this
   is strong evidence the ticket's authors already priced in this exact possibility rather than
   expecting it to be engineered around.
3. CLAUDE.md's Gate Integrity Hard Rule ("Never edit an artifact to make an automated gate/check
   pass instead of fixing the underlying substance... A gate's blocking result is correct
   information to report, not an obstacle to route around") and this ticket's own Out-of-Scope
   framing ("Redefining any threshold to force a pass... the same Gate Integrity discipline...
   applies here with equal force") are both about *substance*, not just the literal file-edit list.
   `check_size_cap()`'s REJECT is itself a real, correct, informative signal about the deployed
   cache's actual capacity relative to this gateway's actual response sizes — choosing a smaller
   `budget_tokens` specifically because the real one triggers that REJECT is substantively the same
   move as picking easier inputs to dodge a blocking result, even though it is not barred by the
   Out-of-Scope bullet's literal text.

**This plan's Steps below implement option (b) as the primary path.** If Architecture Review rules
for option (a) instead: Step 2's per-entry call loop gains a `budget_tokens=<entry-specific value>`
keyword argument to both the cold and warm `_run_knowledge_context()` calls for that entry (the
same value for both calls in a pair, so the cold/warm comparison within an entry stays
apples-to-apples); the concrete per-entry token value is not something Plan can determine without
running code (per investigation) — Implement must determine it empirically (e.g. binary-search
`budget_tokens` down from 4000 until `gateway_tokens × 4 < 8192`, or a fixed conservative value
like 1500 tried first); the fixture and results doc (Steps 4/5) gain a new, explicitly-labeled
`budget_tokens_used` field per entry and a disclosed-divergence paragraph stating plainly that this
diverges from Phase 1's own default-budget call shape and why. No other step changes. Do not select
option (a) silently — this must be an explicit, recorded Architecture Review ruling before
Implement starts on Step 2.

### DD2 — Cache-hit verification method: adopt investigation's recommendation, both signals required

Confirmed by direct read (not just investigation's summary): `tests/tools/test_knowledge_gateway_mcp.py:308-328`
(`_patch_small_cacheable_search`) patches `pa_search_mod._run_search` via `monkeypatch.setattr` and
`tests/tools/test_knowledge_gateway_mcp.py:331-342` asserts `len(search_calls) == 1` across two
`_run_knowledge_context()` calls — real precedent for "spy proving the provider round-trip was
skipped," but scoped to `context_search` only. Since the corpus routes some entries to `graphify`
only (Q2/Q5) and one to both (Q7, per the Phase 1 plan's own DD4 finding,
`stored_artifacts/TCK-20260815-KGMCP-P1-BASELINE-COMPARISON/plan.md:121-143`), this ticket's own
spy must sit one level higher: on `_kgpa.assemble_packet` itself
(`tools/knowledge_gateway_mcp.py:239`, called only on the miss path — confirmed by direct read,
`:220-238` shows the hit path returns at `:237`, before `:239` is ever reached), obtained via
`mod._load_packet_assembly_module()` — the exact same object `_run_knowledge_context()` calls
through, since `_load_packet_assembly_module()` sibling-loads under a fixed `sys.modules` key and
returns the cached object on repeat calls (mirrors `_load_router_module()`/`_load_cache_module()`,
`tools/knowledge_gateway_mcp.py:106-137`, all read directly and confirmed to follow the identical
"if key not in sys.modules: load; return sys.modules[key]" shape). **Decision:** the runner installs
a plain-Python counting spy (direct attribute reassignment on `_kgpa.assemble_packet`, restored via
`finally`, never `unittest.mock`/`MagicMock`) before an entry's cold call and reads the count after
the warm call: exactly 1 across the pair = genuine hit (assemble_packet skipped on the warm call);
exactly 2 = the warm call also round-tripped a provider (real MISS, whatever the cause). This is
independently corroborated by a direct SQL read of `retrieval_provider_result_cache_rows.hit_count`
(`tools/retrieval_cache.py:136,251,658`, confirmed by direct read: `record_provider_result_cache_hit`
at `:651-` does `SET hit_count = hit_count + 1, last_hit_at = ?` keyed by `(query_hash,
repo_branch_scope)`) taken before and after the warm call — mirrors
`tests/tools/test_retrieval_cache.py`'s own direct-SQL-read pattern for the same function
(cited by investigation, not independently re-verified by Plan since it is a read-only precedent
citation, not a load-bearing new claim). **Both signals are required, not either/or** — `AC1`'s "not
assumed" bar means `response["cache"] == "HIT"` alone (self-reported by the exact code path being
measured) never suffices as the recorded truth; the fixture's `cache_status_warm` field is derived
from the spy count + SQL delta agreeing, not from the response body.

### DD3 (new — not previously identified by investigation) — Capturing `cache_write_rejection_reason` requires a second spy, not `perform_cache_write`'s return value

Confirmed by direct read: `tools/knowledge_gateway_cache.py::perform_cache_write()` (`:262-336`)
has return type `-> None` and every one of its `return` statements (`:283`, `:287`, `:290`, `:308`)
is a bare `return` — it never returns the `WriteDecision` or any reason code to its caller. The
caller, `tools/knowledge_gateway_mcp.py:320-324`, invokes it inside a broad `try/except: pass` and
discards whatever it returns anyway. **There is no way to observe why a write was or wasn't
allowed by reading the response or by calling `perform_cache_write` normally.** The runner must
instead spy on `evaluate_write_candidate` itself — the function whose `WriteDecision.verdict`/
`rejection_category` actually carries this information (`tools/knowledge_gateway_redaction.py:254-261`
`WriteDecision` dataclass; `:264-298` `evaluate_write_candidate`). Confirmed by direct read that
this is safely spyable without touching `tools/knowledge_gateway_cache.py`:
`tools/knowledge_gateway_cache.py:61-62` imports it as `from tools import knowledge_gateway_redaction
as rk` — a **plain package import**, not a sibling-load (the module's own docstring at `:20-27`
explicitly states this was a deliberate choice to avoid "a second, independent instance"). This
means `rk` inside `knowledge_gateway_cache.py` and a runner-level `from tools import
knowledge_gateway_redaction as _kgr_redaction` both resolve to the exact same singleton object in
`sys.modules["tools.knowledge_gateway_redaction"]` — patching `_kgr_redaction.evaluate_write_candidate`
via direct attribute reassignment (restored in `finally`) is observed by every call to
`rk.evaluate_write_candidate(...)` inside `perform_cache_write`, regardless of how
`knowledge_gateway_cache.py` itself was loaded by `_load_cache_module()`. **Decision:** the runner
installs this second spy (wrapping the real function, recording the returned `WriteDecision.verdict`/
`.rejection_category`, then calling through to the real function so behavior is unaffected) around
each entry's *cold* call only (the write is only ever attempted on the miss/cold path — confirmed,
`tools/knowledge_gateway_mcp.py:315-324` runs only after the hit-path early return at `:237`). The
recorded `rejection_category` (e.g. `"oversized_payload"`) becomes the fixture's
`cache_write_rejection_reason` field for that entry; `None` on ALLOW.

### DD4 (new — not previously identified by investigation) — Reproducing `query_hash`/`repo_branch_scope` for the SQL delta check reuses the real `compute_lookup_identity()`, never reimplements it

The SQL check (DD2) needs the same `(query_hash, repo_branch_scope)` key the real call used.
Confirmed by direct read, `tools/knowledge_gateway_mcp.py:162-172` (`request` dict built as
`{"query": query}` plus non-`None` optional fields — under DD1 option (b), the runner's call
supplies only `query`, so `request == {"query": entry["query_text"]}`, no other keys) and
`:188,193,227-228` (`routing_decision = _kgr.route(query)`; `_kgc = _load_cache_module();
_kgc.perform_cache_lookup(request, routing_decision, effective_budget)`). **Decision:** the runner
never re-derives the 6-field lookup identity itself (that would be new, untested, possibly-drifting
logic duplicating a function this ticket has no license to touch). Instead it calls the *same*
`_kgc.compute_lookup_identity(request, routing_decision, effective_budget)` the gateway itself calls
internally (`tools/knowledge_gateway_cache.py:132-` per DD-cache-wiring-plan Step 5, re-confirmed
reachable as a plain function on the module `mod._load_cache_module()` returns — same fixed-key
sibling-load pattern as `_load_packet_assembly_module()`), using: (a) the identical `request` dict
the runner itself builds for its own `_run_knowledge_context(query_text)` call (DD1(b): `{"query":
query_text}` only), (b) a `routing_decision` obtained by the runner calling
`mod._load_router_module().route(query_text)` once per entry — the same read-only, side-effect-free
call the Phase 1 runner already established as safe precedent
(`stored_artifacts/TCK-20260815-KGMCP-P1-BASELINE-COMPARISON/plan.md:167-171`), and (c) the same
`effective_budget` (4000, `DEFAULT_BUDGET_TOKENS`, `tools/knowledge_gateway_mcp.py:91,190` under
DD1(b); or the entry-specific override under DD1(a) if Review selects it). This yields the exact
`query_hash`/`repo_branch_scope` string the real call used, with zero duplicated identity logic.

### DD5 — §4.2 warm-vs-cold prediction: adopted as stated expectation, not as an assumed result

Investigation's code-level reasoning (a genuine hit response = the stored cold payload plus a
`cache_key_version` field the cold response never carries, `tools/knowledge_gateway_mcp.py:232-237`
vs `:319`) is adopted as the plan's stated expectation, not baked in as an assumed outcome. Step 3
computes `threshold_4_2_cold_tokens`/`threshold_4_2_warm_tokens` independently from each call's own
real response (never copies one from the other), and the test suite (Step 6) encodes the
expectation as a falsifiable, loudly-failing check
(`test_warm_tokens_never_smaller_than_cold_tokens_without_a_stated_explanation`, already named in
`test_plan.md`) rather than a silent pass-through.

### DD6 — doc_id fix: confirmed unaffected, no action required

Adopted as investigation resolved it (`investigation.md`'s "The doc_id fix" section): confirmed
still in effect (`tools/knowledge_search.py:285-287`), confirmed absent from the cache-wiring
ticket's diff. No step in this plan touches `tools/knowledge_search.py`.

### DD7 — Runner file layout: confirmed, new sibling file

Adopted as investigation resolved it, for the reasons it gave (Phase 1's own tests assert a
single-cold-call-per-entry shape against `kgmcp_phase1_gateway_runner.py`; extending it in place
would modify a DONE sibling ticket's frozen deliverable). **Decision:** `tools/agent-monitoring/
kgmcp_phase2_gateway_runner.py` (new), importing (not duplicating) `_normalize_phase1_source_id`,
`_path_only`, `_compute_threshold_4_3` from `kgmcp_phase1_gateway_runner.py` (confirmed all three
are pure, module-level, directly importable — `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py:116-162`,
`:165-` — no `self`/module-state dependency).

### DD8 (new — not previously identified by investigation) — This ticket's own gateway-module load uses a NEW `sys.modules` key, distinct from Phase 1's

`kgmcp_phase1_gateway_runner.py::_load_gateway_module()` (`:106-113`) sibling-loads
`knowledge_gateway_mcp.py` under the fixed key `"kgmcp_phase1_comparison_gateway"`, caching the
module object in `sys.modules` for the rest of the process. This ticket's own runner needs its own
module object (to install its own spies on `_kgpa`/`_kgr_redaction` without any chance of
interaction with a different test file's own patches to the Phase 1 runner's module instance, and
to keep the two runners' own pytest files fully independent when run in the same session or CI
job). **Decision:** the new runner defines its own `_load_gateway_module()` (not imported from
Phase 1's — that function is private/module-specific, and DD7 already limits the import list to the
3 pure normalization/threshold helpers) using a distinct key, `"kgmcp_phase2_recomparison_gateway"`,
following the identical `importlib.util.spec_from_file_location` + "if key not in sys.modules"
pattern.

## Steps

### Step 1 — New runner module skeleton: `tools/agent-monitoring/kgmcp_phase2_gateway_runner.py`

**Files:** `tools/agent-monitoring/kgmcp_phase2_gateway_runner.py` (new)

**Change:** Module docstring states DD1's decision plainly at the top (which option is
implemented, and the disclosed-divergence note if Review later selects option (a)), plus a
"what this measures / what it does not" framing mirroring
`tools/knowledge_gateway_redaction.py:1-33`'s convention. Imports:
`from kgmcp_baseline_corpus import CORPUS, CORPUS_VERSION` (unmodified, same import Phase 0/Phase 1
already use); `from kgmcp_phase1_gateway_runner import _normalize_phase1_source_id, _path_only,
_compute_threshold_4_3` (DD7); `from tools import knowledge_gateway_redaction as _kgr_redaction`
(DD3, plain package import — module path confirmed importable this way since
`tools/knowledge_gateway_cache.py:61-62` already imports both `tools.retrieval_cache` and
`tools.knowledge_gateway_redaction` the same way). Defines `_load_gateway_module()` per DD8 (new
key `"kgmcp_phase2_recomparison_gateway"`) and a `_load_manifest_built_at()` helper reading
`knowledge-index/manifest.json`'s `built_at` field fresh (for Risk #6's zero-mutation guard, Step 2).

**Other writers to this resource:** none — brand-new file. `kgmcp_baseline_corpus.py` (read-only
import, shared with Phase 0/Phase 1 runners, never mutated) and `kgmcp_phase1_gateway_runner.py`
(read-only import of 3 pure functions, DD7) are both frozen dependencies this step only reads from.

**Do NOT touch:** `kgmcp_phase1_gateway_runner.py`, `kgmcp_baseline_corpus.py`,
`kgmcp_baseline_runner.py`, any file under `tools/knowledge_gateway_*.py` or `tools/retrieval_cache.py`.

**Verify:** `test_threshold_4_3_reuses_phase1s_own_normalization_functions_not_reimplemented`
(AST-based `ImportFrom` check).

### Step 2 — Per-entry cold+warm double-call loop with both spies and the SQL delta check

**Files:** `tools/agent-monitoring/kgmcp_phase2_gateway_runner.py`

**Change:** `run_corpus()` loops the 7 `CORPUS` entries in order. Per entry:
1. Record `knowledge-index/manifest.json`'s `built_at` (pre-entry snapshot, for the aggregate
   zero-mutation guard — Risk #6).
2. Install the `assemble_packet` spy: `_kgpa = mod._load_packet_assembly_module()`;
   `_orig_assemble = _kgpa.assemble_packet`; `call_count = []`; `_kgpa.assemble_packet = lambda
   *a, **kw: (call_count.append(1), _orig_assemble(*a, **kw))[1]` (or an equivalent named-function
   spy — implementer's choice of exact closure shape, but it must be a plain reassignment, never
   `unittest.mock.patch`, and must be restored in `finally` before the entry ends, per DD2 and the
   AST-guard precedent this ticket's own test suite must not trip:
   `test_new_runner_never_calls_emit_retrieval_event_or_wrap_functions`-style scan, and the general
   repo-wide "never `unittest.mock`/`MagicMock` in this runner" convention DD2 cites).
3. Install the `evaluate_write_candidate` spy on `_kgr_redaction` (DD3): captures
   `(verdict, rejection_category)` from the real returned `WriteDecision`, then returns it unchanged
   (pass-through, never alters behavior).
4. Compute `_kgc = mod._load_cache_module()`; `routing_decision = mod._load_router_module().route(
   entry["query_text"])`; `request = {"query": entry["query_text"]}` (DD1(b) — or with
   `budget_tokens` added if DD1(a) is later selected); `effective_budget` (4000 or the DD1(a)
   override); `identity = _kgc.compute_lookup_identity(request, routing_decision,
   effective_budget)` (DD4) — used only for the SQL key, never passed into
   `_run_knowledge_context()` itself (that function computes its own identity internally; this is a
   read-only, parallel, non-interfering computation for observation purposes only).
5. Read `hit_count` for `(identity["query_hash"], identity["repo_branch_scope"])` from
   `retrieval_provider_result_cache_rows` via a direct, short-lived SQLite connection against
   `tools.retrieval_cache.CACHE_DB_PATH` (read-only `SELECT`, no write) — record as
   `hit_count_before_warm` (may be `0` or the row may not exist yet, both valid pre-states).
6. Cold call: `start = time.perf_counter(); response_cold = mod._run_knowledge_context(
   entry["query_text"])` (DD1(b) — no extra kwargs); `cold_call_wall_time_ms = (time.perf_counter()
   - start) * 1000`. Confirm `response_cold["cache"] == "MISS"` (always true for a first call on an
   unseen identity — if it is ever `"HIT"` on the very first call of a fresh corpus run, that is
   itself an anomaly to record, not silently normalize away, since it would mean a stale row from a
   previous manual run was still present; the runner does not pre-clear the cache DB, per Anti-Drift
   Hazard about not mutating shared resources beyond what a real caller would do).
7. Read `hit_count` again — record as `hit_count_after_cold` (expected unchanged from
   `hit_count_before_warm`, since a cold MISS never calls `record_provider_result_cache_hit`).
8. Warm call: `start = time.perf_counter(); response_warm = mod._run_knowledge_context(
   entry["query_text"])`; `warm_call_wall_time_ms = ...`.
9. Read `hit_count` a third time — `hit_count_after_warm`; `cache_hit_count_delta =
   hit_count_after_warm - hit_count_after_cold`.
10. Restore both spies (`finally`).
11. Derive `cache_status_warm`: `"HIT"` iff `call_count == [1]` (assemble_packet not called again)
    **and** `cache_hit_count_delta == 1`; otherwise `"MISS"` — never derived from
    `response_warm["cache"]` alone (DD2). If the two signals disagree (e.g. spy says 1 call but SQL
    delta is 0), record both raw signals plus an `anomaly` field rather than picking one silently —
    this is itself a reportable, never-hidden finding.
12. Record `cache_write_rejection_reason` = the cold-call spy's captured `rejection_category` (DD3;
    `None` if `verdict == ALLOW`).
13. Record `provider_round_trip_call_count = len(call_count)` (1 or 2, per
    `test_warm_call_cache_hit_independently_verified_via_provider_round_trip_spy`'s naming).
14. After all 7 entries: re-read `knowledge-index/manifest.json`'s `built_at` — if it differs from
    the pre-run snapshot, this is a hard failure the runner itself raises (a mid-run index rebuild
    invalidates every subsequent revalidation per Risk #6 — the run's results would be unusable and
    must not be silently written to the fixture as if clean).

**Other writers to this shared resource (`retrieval_provider_result_cache_rows`, the real on-disk
`knowledge-index/retrieval_cache.db`):** enumerated per DD3's cache-wiring plan citation — the two
real writers are `tools/retrieval_cache.py::write_provider_result_cache()` and
`record_provider_result_cache_hit()`, both invoked *only* through `perform_cache_write()`/
`perform_cache_lookup()` inside the real gateway calls this runner itself makes (Steps 6 and 8
above) — there is no separate, independent writer this step's own SQL reads could race against
within a single-process, single-threaded script run. The runner's own SQL reads (Steps 5, 7, 9) are
`SELECT`-only, never `INSERT`/`UPDATE` — this step adds no new writer to the table, and does not
pre-seed, clear, or otherwise mutate the real cache DB before or between entries (running this
script against the real, possibly-already-populated `knowledge-index/retrieval_cache.db` from a
prior manual run is a real, disclosed confound noted in Anti-Drift Notes, not something this step
papers over by resetting state).

**Do NOT touch:** `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_router.py`,
`tools/knowledge_gateway_packet_assembly.py`, `tools/knowledge_gateway_cache.py`,
`tools/knowledge_gateway_redaction.py`, `tools/retrieval_cache.py` — every interaction is a
read-only call or a spy restored before the function returns.

**Verify:** `test_all_7_corpus_entries_run_cold_and_warm_in_recomparison_fixture`,
`test_warm_call_cache_hit_independently_verified_via_provider_round_trip_spy`,
`test_warm_call_cache_hit_corroborated_by_db_hit_count_delta`,
`test_cache_status_never_reports_hit_when_write_was_rejected_or_row_absent`,
`test_zero_mutation_of_agent_monitoring_and_manifest_across_full_run`.

### Step 3 — Threshold computation: §4.1 warm-only, §4.2 cold+warm separately, §4.3 via imported helper

**Files:** `tools/agent-monitoring/kgmcp_phase2_gateway_runner.py`

**Change:**
- `threshold_4_1_latency`: `{"pass": warm_call_wall_time_ms <= threshold_ms, "warm_call_wall_time_ms":
  ..., "threshold_ms": ..., "derivation": "..."}` where `threshold_ms` is re-derived live as
  `0.5 * mean(fixture entry["combined"]["wall_time_ms"] for all 7 Phase 0 entries)` — read from the
  committed Phase 0 fixture at run time, never hand-typed (same convention as Phase 1's plan Step 3;
  the constant is expected to still compute to `935.32` since neither this ticket nor any of its
  dependencies touches the Phase 0 fixture, but the code must compute it, not assert it).
  **Explicitly per AC2, `cold_call_wall_time_ms` is never used for this threshold's `pass`
  determination** — only `warm_call_wall_time_ms`.
- `threshold_4_2_cold_tokens` / `threshold_4_2_warm_tokens`: each independently computed via
  `_kgpa.kgmcp_char_heuristic_v1(json.dumps(response_cold))` /
  `...(json.dumps(response_warm))` (the packet-assembly module's real heuristic, imported from the
  same `mod._load_packet_assembly_module()` object the spy already uses — never a second, separately
  re-implemented token estimator), each compared against the same live-derived `threshold_tokens`
  (`0.5 * mean(Phase 0 fixture's combined.serialized_tokens_estimate)`, expected `1263.57`, computed
  not hand-typed). Per DD5, `warm_tokens` is expected `>= cold_tokens` for any entry where
  `cache_status_warm == "HIT"` — this is checked as a test assertion (Step 6), not asserted here in
  code.
- `threshold_4_3_recall`: call the imported `_compute_threshold_4_3(baseline_sources, gateway_sources)`
  (DD7) using the Phase 0 fixture's `sources_recalled` as `baseline_sources` and
  `[_normalize_phase1_source_id(x) for x in response's context/evidence source ids]` as
  `gateway_sources` — **computed once per entry against whichever of the cold/warm response is that
  entry's authoritative recall check.** Since a genuine warm `hit_response` is `dict(cached_payload)`
  plus two extra keys (`tools/knowledge_gateway_mcp.py:233-235`) — i.e. the same `context`/`evidence`
  content as the cold response that produced the cached row — recall is identical whether measured
  cold or warm for any entry that reaches a genuine HIT; for entries that never reach a genuine HIT,
  only the cold response's recall is meaningful (the warm-labeled response is itself another cold
  call). **Decision:** compute `threshold_4_3_recall` from the **cold** response always (the one
  response every entry unconditionally has, regardless of cache_status_warm), and record it as
  `threshold_4_3_recall_cold`; do not fabricate a separate warm-labeled recall number for entries
  that never cache, since that number would just be a second independent cold measurement dressed
  up as a warm one. This keeps the Q2/Q5 architectural-miss narrative (DD-inherited from Phase 1)
  reportable regardless of DD1's outcome.
- `aggregate` object mirroring Phase 1's own shape (`pass_count`/`of: 7` per threshold,
  `all_thresholds_pass`), computed the same "False if any entry fails" way as Phase 1's plan Step 3.

**Other writers to this resource:** none new — reads two frozen inputs (Phase 0 fixture, this
ticket's own freshly-computed responses from Step 2), same "no ordering/race concern, single-process
sequential" reasoning as Phase 1's plan Step 3.

**Do NOT touch:** the Phase 0 fixture; the threshold constants' source of truth (always computed
live from that fixture, never hardcoded).

**Verify:** `test_threshold_4_1_computed_against_warm_path_numbers_only`,
`test_threshold_4_1_reports_honestly_whatever_the_real_result_is`,
`test_threshold_4_2_computed_separately_for_cold_and_warm`,
`test_warm_tokens_never_smaller_than_cold_tokens_without_a_stated_explanation`,
`test_q2_q5_recall_still_fails_for_the_documented_architectural_reason`,
`test_non_q2_q5_recall_counts_reported_honestly_against_phase1s_own_recorded_counts`.

### Step 4 — Committed fixture: `tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json`

**Files:** `tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json` (new)

**Change:** Run `kgmcp_phase2_gateway_runner.py::main()` once, by hand, during Implementation
(never wired into pytest's fast loop, same one-time-script convention as both prior runners).
Write, per entry: `id`, `query_text`, `budget_tokens_used` (4000 under DD1(b), or the override under
DD1(a)), `cold_call_wall_time_ms`, `warm_call_wall_time_ms`, `cache_status_warm`,
`provider_round_trip_call_count`, `cache_hit_count_delta`, `cache_write_rejection_reason`,
`threshold_4_1_latency`, `threshold_4_2_cold_tokens`, `threshold_4_2_warm_tokens`,
`threshold_4_3_recall_cold`, plus a top-level `aggregate`. Every entry/sub-object carries a
non-empty `derivation` string (never a bare number/boolean), matching the never-silent convention
both prior fixtures already established. `json.dumps(..., indent=2, sort_keys=True)`.

**Other writers to this resource:** none — new, unique fixture path. The Phase 0
(`kgmcp_measurement_baseline_corpus_results.json`) and Phase 1
(`kgmcp_phase1_baseline_comparison_results.json`) fixtures are separate paths with their own
separate writers, never regenerated or hand-edited by this ticket.

**Do NOT touch:** `tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json`,
`tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json`.

**Verify:** all fixture-based structural tests named in `test_plan.md`; `git status --porcelain`
before/after confirms only the new fixture path is touched.

### Step 5 — Results doc: `docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md`

**Files:** `docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md` (new)

**Change:** Author a results doc mirroring `phase1_baseline_comparison.md`'s own structure, citing
the new fixture path literally, presenting per-threshold (§4.1/§4.2/§4.3) aggregate and per-entry
`PASS`/`FAIL` with real numbers. Must state plainly:
- DD1's resolution: which option Architecture Review selected, and — if option (a) — the explicit
  disclosed-divergence sentence (budget override used, why, and that it diverges from Phase 1's own
  call shape).
- Per-entry `cache_status_warm` and, for any `MISS`, the real `cache_write_rejection_reason` (e.g.
  `"oversized_payload"`) — never a bare "MISS" with no stated mechanism (Anti-Drift Hazard).
- The literal finding if the size cap blocks some/all entries under DD1(b): state the byte-size vs.
  8192-cap comparison explicitly, by entry.
- DD5's confirmation or refutation: state the real cold-vs-warm token numbers for every entry that
  reached `cache_status_warm == "HIT"`, and whether warm ever came in smaller than cold (expected:
  no; if yes, flag as requiring investigation, per the test guard).
- The Q2/Q5 recall narrative, reusing the same honest routing-design framing Phase 1's own doc used
  (not re-explained away), plus the real Q1/Q3/Q4/Q6/Q7 recall-count comparison against Phase 1's
  own recorded counts (4/8, 2/8, 1/8, 3/8, 3/8) — reported, not assumed improved.
- An overall honest verdict sentence per threshold — never a blanket "Phase 2 succeeded"
  characterization if any per-entry threshold misses.

**Other writers to this resource:** none — new file, unique path.

**Do NOT touch:** `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` or
`measurement_baseline_contract.md`'s §4 prose (cited, never edited).

**Verify:** `test_results_doc_cites_real_fixture_and_states_pass_fail_per_threshold`.

### Step 6 — Structural test suite: `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`

**Files:** `tests/tools/test_kgmcp_phase2_baseline_recomparison.py` (new)

**Change:** Implement every test named in `test_plan.md`'s "New Tests Required" section verbatim
(15 tests total across AC1–AC4 plus the 6 frozen-dependency/anti-drift guards). The two AST-based
guards (`test_threshold_4_3_reuses_phase1s_own_normalization_functions_not_reimplemented`,
`test_new_runner_never_calls_emit_retrieval_event_or_wrap_functions`) use `ast.parse()` over the new
runner's source, mirroring `test_kgmcp_measurement_baseline.py`'s established structural-guard
pattern; `test_no_frozen_kgmcp_dependency_edited` and `test_never_edits_phase1_results_doc` use
`git diff --stat HEAD`, mirroring Phase 1's own precedent, extended to cover this ticket's own new
frozen-file list (the 6 gateway/cache/redaction modules, `tools/retrieval_events.py`,
`tools/knowledge_search.py`, both prior runners, both prior fixtures, plus this ticket's own new
runner/fixture once they exist — a file this ticket itself is actively writing during Implement is
of course expected to appear in the diff; the guard's banned list is the *other* ticket's/sibling's
frozen files, not this ticket's own new outputs).

**Other writers to this resource:** none — new test file. Reads (never writes) the Phase 0 fixture,
Phase 1 fixture, this ticket's new fixture, and the runner/gateway module sources.

**Do NOT touch:** `tests/tools/test_kgmcp_phase1_baseline_comparison.py`,
`tests/tools/test_kgmcp_measurement_baseline.py`, `tests/tools/test_knowledge_gateway_mcp.py`,
`tests/tools/test_knowledge_gateway_cache.py`, `tests/tools/test_retrieval_cache.py`,
`tests/tools/test_knowledge_gateway_redaction.py`, `tests/tools/test_knowledge_gateway_router.py`,
`tests/tools/test_knowledge_gateway_packet_assembly.py`,
`tests/tools/test_knowledge_gateway_failure_semantics.py`,
`tests/tools/test_knowledge_gateway_contract_schemas.py`, `tests/tools/test_search_mcp.py` — every
one of these stays exactly as-is; this step only adds a new file.

**Verify:** the full scoped pytest command from `test_plan.md`'s "Scoped Pytest Commands" section.

### Step 7 — Docs: parity ledger `INFRA-344` entry, proposal doc appended paragraph

**Files:** `docs/parity_ledger/infrastructure.yaml`, `docs/plans/knowledge-gateway-mcp-proposal.md`

**Change:**
- `docs/parity_ledger/infrastructure.yaml`: append one new entry, `id: INFRA-344` — confirmed next
  sequential by direct read (`id: INFRA-343` is the current last entry in the file, no `INFRA-344`
  exists yet). `status: verified` (or `divergent`, depending on the real DD1(b) outcome — if 0/7
  entries genuinely cache, this ticket's real behavior structurally cannot demonstrate a working
  warm-hit path against real corpus-sized responses, which may itself be more accurately ledgered as
  a disclosed limitation than a clean `verified` — Implement/Document-Update phase decides the exact
  status word based on the real run's outcome, not this plan). `priority: P2` (matching the
  sibling Phase 2 entries' own priority, none of which is `P0`). Cites this ticket, the new fixture,
  and the new results doc by path.
- `docs/plans/knowledge-gateway-mcp-proposal.md`: confirmed by direct read
  (`docs/plans/knowledge-gateway-mcp-proposal.md:1200-1273`) that the "Add exact normalized-query
  reuse" bullet (Phase 2's 4th and last bullet, already **Done**-annotated by the cache-wiring
  ticket) ends immediately before a `---` separator at line ~1274. Append a new short paragraph
  after that bullet (before the `---`) stating this ticket's real §4.1/§4.2/§4.3 outcome, citing
  `phase2_baseline_recomparison.md` and the new fixture by path — same append-only, never-rewrite-a-
  sibling's-line precedent Phase 1's own Step 7 established for this exact section.

**Other writers to this resource:** `infrastructure.yaml` has one entry per ticket, appended in
sequence by each of `INFRA-334` through `INFRA-343`'s own tickets — this step follows that
convention, never editing an existing entry. `knowledge-gateway-mcp-proposal.md`'s Phase 1/Phase 2
sections have each been edited exactly once per child ticket, always by appending new prose after
the existing content, never rewriting a prior ticket's own paragraph — this step follows that same
pattern.

**Do NOT touch:** any existing `INFRA-*` entry; any of the 6 existing Phase 2 bullets' or Phase 1
section's existing text; the Phase 3/§21 pilot-bar section.

**Verify:** doc-only change; verified by Document-Update/Parity phase review, not a pytest test.

## Scope Guards

- Never edit `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_router.py`,
  `tools/knowledge_gateway_packet_assembly.py`, `tools/knowledge_gateway_cache.py`,
  `tools/knowledge_gateway_redaction.py`, `tools/retrieval_cache.py`, `tools/retrieval_events.py`,
  or `tools/knowledge_search.py` — every interaction is read-only import/call or a spy restored
  before returning.
- Never edit `tools/agent-monitoring/kgmcp_baseline_corpus.py`,
  `tools/agent-monitoring/kgmcp_baseline_runner.py`, or
  `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py` — the new runner only imports 3 named pure
  functions from the last of these (DD7).
- Never edit `tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json` or
  `tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json` — read-only inputs.
- Never edit `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` or
  `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md`'s §4 prose — cited,
  never edited.
- Never pre-clear, reset, or seed `knowledge-index/retrieval_cache.db` before or during the run —
  the run must observe the real cache's real, possibly-already-populated state, and any
  pre-existing row for a corpus query is itself a disclosed confound (Anti-Drift Notes), not
  something to engineer away.
- Never trigger `make knowledge-index-update` or any index rebuild during the run — Risk #6's
  `built_at` guard exists to catch this, not license it.
- Never widen `ROUTING_TABLE` or otherwise cause Q2/Q5 to route to `context_search` — frozen,
  ledgered routing behavior; the Q2/Q5 recall miss is expected and must be reported, not routed
  around.
- Never derive `cache_status_warm` from `response["cache"]` alone — DD2 requires both the spy count
  and the SQL hit_count delta to agree.
- Never silently relabel a size-cap-blocked (or any other) MISS as a HIT, and never omit
  `cache_write_rejection_reason` when a write was rejected.
- Never select DD1's option (a) without an explicit, recorded Architecture Review ruling — this
  plan's default, primary-path Steps implement option (b).
- Never characterize a per-entry or aggregate threshold miss as a pass, and never omit it from the
  Completion Summary or results doc.
- Never edit `CLAUDE.md`, any `.claude/agents/*.md`, or any `.claude/skills/*.md` file.

## Dependency Map

- Step 1 (module skeleton) has no dependency on other steps; it is the foundation, and is where
  DD1's Architecture-Review-confirmed request shape must be finalized before Step 2 is implemented.
- Step 2 (double-call loop + spies + SQL checks) depends on Step 1's skeleton and on DD1's ruling
  being confirmed (the exact `budget_tokens` handling in the call loop differs by outcome).
- Step 3 (threshold computation) depends on Step 2's raw per-entry data (cold/warm responses, spy
  counts, SQL deltas) and on Step 1's imported `_compute_threshold_4_3`.
- Step 4 (fixture) depends on Steps 1–3 being complete and correct — produced by running the
  finished runner once.
- Step 5 (results doc) depends on Step 4's real fixture numbers — write after the fixture exists.
- Step 6 (test suite) depends on Steps 1–5 all existing (tests the fixture, the runner's AST, and
  the results doc's text) — implement last among code/doc steps.
- Step 7 (parity ledger + proposal doc) depends on Step 5 (cites `phase2_baseline_recomparison.md`
  by name) and on the real outcome (for the parity ledger's `status` field) — do last.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Each of the 7 corpus entries run twice (cold+warm), warm cache-hit status independently verified via a real check | Steps 1, 2 | `test_all_7_corpus_entries_run_cold_and_warm_in_recomparison_fixture`, `test_warm_call_cache_hit_independently_verified_via_provider_round_trip_spy`, `test_warm_call_cache_hit_corroborated_by_db_hit_count_delta`, `test_cache_status_never_reports_hit_when_write_was_rejected_or_row_absent` |
| §4.1 computed against warm-path numbers, reported honestly whatever the result | Step 3 | `test_threshold_4_1_computed_against_warm_path_numbers_only`, `test_threshold_4_1_reports_honestly_whatever_the_real_result_is` |
| §4.2 computed against both cold and warm numbers separately, no assumption caching alone satisfies it | Step 3 | `test_threshold_4_2_computed_separately_for_cold_and_warm`, `test_warm_tokens_never_smaller_than_cold_tokens_without_a_stated_explanation` |
| §4.3 recomputed with fixed evidence-ID normalization; Q2/Q5 architectural miss reported honestly, not hidden | Steps 1, 3 | `test_threshold_4_3_reuses_phase1s_own_normalization_functions_not_reimplemented`, `test_q2_q5_recall_still_fails_for_the_documented_architectural_reason`, `test_non_q2_q5_recall_counts_reported_honestly_against_phase1s_own_recorded_counts` |
| If any threshold is missed, Completion Summary states this plainly — no threshold redefined, no entry excluded | Steps 3, 5, 7 (Completion Summary written at ticket close, informed by these) | `test_results_doc_cites_real_fixture_and_states_pass_fail_per_threshold`, `test_no_frozen_kgmcp_dependency_edited`, `test_never_edits_phase1_results_doc` |

## Anti-Drift Notes

- The single most consequential fact from investigation, re-confirmed by direct source read during
  Plan: every one of the 7 corpus entries' real response payload (10.6–30.5 KB) exceeds the
  8192-byte cache-write size cap (`tools/knowledge_gateway_redaction.py:68,179-184,287-288`) under
  the default request shape. Under DD1's recommended option (b), the honest, expected outcome of
  this ticket's real run may well be 0/7 or very few genuine warm hits — this is not a bug in the
  runner or a failure of this ticket; it is the real, current capacity of the deployed cache
  relative to this gateway's real response sizes, and must be reported as exactly that.
- `perform_cache_write()` (`tools/knowledge_gateway_cache.py:262-336`) always returns `None` and its
  caller discards the outcome inside a broad `try/except: pass`
  (`tools/knowledge_gateway_mcp.py:320-324`) — there is no return-value-based way to observe a
  rejection; DD3's `evaluate_write_candidate` spy is the only correct observation point.
- `tools/knowledge_gateway_cache.py` imports `retrieval_cache`/`knowledge_gateway_redaction` as
  plain package imports, not sibling-loads (`:61-62`, confirmed deliberate per its own docstring at
  `:20-27`) — this is exactly what makes DD3's runner-level spy on the same singleton module
  observable inside `perform_cache_write`'s real call; do not "fix" this by sibling-loading a
  private copy of `knowledge_gateway_redaction.py` for the spy, which would create a second,
  unobserved instance and silently break the spy.
- The warm-labeled response for any entry that never reaches a genuine `cache_status_warm == "HIT"`
  is, structurally, a second cold call — its `threshold_4_1_latency`/`threshold_4_2_warm_tokens`
  numbers are real and must still be reported (per AC2/AC3's "whatever the result"), but the results
  doc (Step 5) must not narrate such an entry as if caching had been genuinely exercised.
- If Architecture Review selects DD1's option (a), the runner still performs the SAME cold+warm
  double call and SAME two-spy verification per entry — only the `budget_tokens` value passed to
  both calls of a pair changes, and the fixture/results doc gain the explicit disclosure fields
  named in DD1. No other step's design changes.
- This ticket is measurement-only for a second time in this ticket family (after Phase 1) — its
  Completion Summary must not overstate Phase 2 as unconditionally successful if any per-entry or
  aggregate threshold misses, including (and especially) the central §4.1/§4.2 warm-hit
  measurability question DD1 exists to resolve honestly.

## Deviations (recorded during Implement)

1. **DD1 ruling confirmed: option (b) (exact Phase 1 request-shape parity, no `budget_tokens`
   override).** Architecture Review ruled in favor of the plan's own recommendation before Implement
   began. The real run confirms the plan's own prediction exactly: **0/7 entries reached a genuine
   warm cache hit** — every one of the 7 entries' cold response payload (10.6–30.5 KB, matching the
   Phase 1 fixture's own range within corpus-drift noise) exceeded `MAX_PAYLOAD_BYTES = 8192`, and
   every cache write was rejected with `rejection_category == "oversized_payload"`, captured by the
   `evaluate_write_candidate` spy on every one of the 7 entries. No fallback to option (a) was
   implemented at any point, per DD1's explicit prohibition and the orchestrator's own
   maximum-force instruction on this exact point.

2. **`kgmcp_phase2_gateway_runner.py`'s own module docstring initially spelled out the literal
   string `MagicMock`** (in a "never `unittest.mock`/`MagicMock`" disclaimer, directly copying a
   phrase from this very plan/investigation's own prose). This tripped
   `test_new_runner_never_calls_emit_retrieval_event_or_wrap_functions`'s `"MagicMock" not in
   _RUNNER_SOURCE` guard against the runner's own docstring text (not against any real mocking
   usage — the runner never imports or calls any mocking library). Fixed by rephrasing the
   docstring to "never any attribute-mocking library" (matching `kgmcp_phase1_gateway_runner.py`'s
   own established convention of writing "no mock, no monkeypatch" rather than spelling out the
   literal class name). No behavior change; docstring-only edit.

3. **`test_no_frozen_kgmcp_dependency_edited` (mirroring Phase 1's own `git diff --stat HEAD`
   convention verbatim, per this ticket's own test_plan.md) FAILS today, in this ticket's own test
   run — but this is a pre-existing, non-regression condition, not caused by this ticket's own
   diff.** Direct verification: `git status --porcelain -- tools/knowledge_gateway_mcp.py
   tools/knowledge_gateway_redaction.py tools/knowledge_gateway_cache.py tools/retrieval_cache.py`
   shows these 4 files were already modified/added in the working tree (`M`/`A`) *before* this
   ticket's own work began — legitimate, already-`Done`, uncommitted work from the sibling
   `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`/`TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH`/
   `TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS` tickets, none of which this ticket touched.
   Independently confirmed: running Phase 1's OWN already-`Done`, previously-passing
   `test_kgmcp_phase1_baseline_comparison.py::test_no_frozen_kgmcp_dependency_edited` in isolation
   *also* fails today, for the identical reason, with zero involvement from this ticket. The
   `git diff --stat HEAD` convention (both this ticket's own guard and Phase 1's) implicitly assumes
   `HEAD` reflects the state immediately before the ticket under test began — an assumption that no
   longer holds on this branch now that multiple Phase 2 sibling tickets' real, legitimate work sits
   uncommitted ahead of `HEAD`. This ticket's own diff contributes **zero** changes to any of the 13
   banned paths (confirmed above) — the guard's `FAIL` result is accurately reporting a real
   environmental/workflow-convention limitation, not this ticket's own scope violation. Per
   CLAUDE.md's Gate Integrity Hard Rule, this was left exactly as speced (not weakened, not
   silently made to pass) and is reported here, in the ticket's Test Summary, and in the
   Implementer's structured report, for Architecture-Verify/Test/Verify to assess — e.g. whether the
   guard should instead diff against this ticket's own start-of-work point rather than a fixed
   `HEAD`, a question this ticket has no authority to resolve unilaterally.

4. **Step 7's parity ledger entry (`INFRA-344`) was deferred to the Parity phase, per the
   orchestrator's explicit instruction** ("Defer the parity ledger entry (INFRA-344) to the Parity
   phase, per this epic's established convention — do not write it yourself"), overriding Step 7's
   literal text for that one file only. `docs/parity_ledger/infrastructure.yaml` was not opened or
   edited by Implement. Step 7's other file, `docs/plans/knowledge-gateway-mcp-proposal.md`, WAS
   updated by Implement (a new results-narrative paragraph appended after the Phase 2 section's
   final bullet, before the Phase 3 header) — the deferral instruction named only the parity ledger
   entry, and this append-only edit mirrors Phase 1's own precedent for the identical section.

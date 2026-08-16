---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON
artifact_type: investigation
tags: [ai, mcp, testing]
---

# Investigation — TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON

## Current Behavior

### The real cache orchestrator (`tools/knowledge_gateway_cache.py`)
`perform_cache_lookup(request, routing_decision, effective_budget)` (L226-249): computes the §1
6-field lookup identity via `compute_lookup_identity()` (L132-149: `normalized_intent`,
`resolved_entity_ids_json`, `filters_json`, `budget_class`, `routing_policy_version`,
`repo_branch_scope`, plus derived `query_hash`), calls
`rc.check_provider_result_cache(query_hash, repo_branch_scope, ...)`, and on a raw SQL hit runs
`is_branch_compatible()` (§5 rule 2, hard partition) then `revalidate_cache_row()` (§2/§3/§4,
L204-219). Only on a genuine revalidated hit does it call
`rc.record_provider_result_cache_hit(query_hash, repo_branch_scope)` and return
`json.loads(lookup.row["result_payload"])`. Any other outcome returns `None` (treated as MISS).

`perform_cache_write(request, routing_decision, response, effective_budget)` (L262-336): skips
entirely if `response["status"] == "PARTIAL"`; otherwise builds `raw_payload =
json.dumps({k: v for k, v in response.items() if k not in {"cache", "cache_key_version"}},
sort_keys=True)` and calls `rk.evaluate_write_candidate(source_type=..., raw_content=raw_payload)`
(`tools/knowledge_gateway_redaction.py`). **Only on `decision.verdict == ALLOW`** does it call
`rc.write_provider_result_cache(..., result_payload=decision.redacted_payload, ...)`. Any REJECT
verdict is a silent no-op (fail-open) — the direct-call response the caller sees is unaffected,
but no cache row is ever written for that query.

### The size cap that actually gates every real write (`tools/knowledge_gateway_redaction.py`)
`evaluate_write_candidate()` (L228-258) runs a **fixed order**: allowlist → `redact_content()` →
`scan_for_secrets()` (short-circuits) → `check_size_cap(redacted)` → `check_never_cache_categories()`
→ stamp+hash → ALLOW. `check_size_cap()` (L165-171) returns `True` iff
`len(redacted_payload.encode("utf-8")) <= MAX_PAYLOAD_BYTES` where `MAX_PAYLOAD_BYTES = 8192`
(L74). A `False` result yields `WriteDecision(REJECT, "oversized_payload", None, None, ...)` —
**never truncates**. `redact_content()` (L96-113) only rewrites home-directory prefixes
(`/home/`, `/Users/`, `C:\Users\`) to `<local-user>` and machine-specific absolute paths to either
a repo-relative form or `<local-path>` — for this repo's own response content (paths like
`docs/foo.md`, ticket IDs, symbol names — all already relative/bare strings), `redact_content()` is
a near no-op: `redacted_payload` is essentially the same byte length as `raw_payload`, never
meaningfully smaller.

**Quantified real-world exposure (computed from already-committed, real fixture data — no new
measurement run, per Investigate's read-only mandate):** the committed
`tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json` records real
`gateway_tokens` (= `kgmcp_char_heuristic_v1(json.dumps(response))` = `ceil(utf8_bytes/4)`) for
all 7 corpus entries under the default `budget_tokens` (4000, since the P1 runner never passes an
explicit value, exactly mirroring what this ticket's own Scope implies unless Plan decides
otherwise):

| Entry | gateway_tokens | implied bytes (≈ tokens×4) | vs. 8192-byte cap |
|---|---|---|---|
| Q1_authoritative_state | 2649 | ~10,596 | **+29% over** |
| Q2_symbol_lookup | 4999 | ~19,996 | **+144% over** |
| Q3_requirement_completeness | 2846 | ~11,384 | **+39% over** |
| Q4_historical_rationale | 2734 | ~10,936 | **+33% over** |
| Q5_test_impact | 4934 | ~19,736 | **+141% over** |
| Q6_ticket_status | 2817 | ~11,268 | **+38% over** |
| Q7_negative_knowledge | 7633 | ~30,532 | **+273% over** |

`raw_payload` in `perform_cache_write()` is the same response minus two small keys (`"cache"`,
`"cache_key_version"`) — essentially identical size to `gateway_tokens×4` bytes.
`redact_content()` does not meaningfully shrink it (see above). **Every one of the 7 entries, at
its smallest (Q1, +29% over), already exceeds `MAX_PAYLOAD_BYTES` before redaction is even
applied.** See Risks §1 — this is the single most consequential finding of this investigation.

### The MCP-level hooks (`tools/knowledge_gateway_mcp.py::_run_knowledge_context()`)
Cache-check hook (L220-237): runs after `route()` succeeds, before `assemble_packet()`. On a
non-`None` `perform_cache_lookup()` result, builds `hit_response = dict(cached_payload)`, sets
`hit_response["cache"] = "HIT"` and `hit_response["cache_key_version"] =
_kgc.ROUTING_POLICY_VERSION` (an int), validates against `RESPONSE_SCHEMA`, and returns —
**`assemble_packet()` (the real provider round-trip) is structurally never called on this path.**
Cache-write hook (L315-324): only reached on the miss path (the hit path returns early at L237);
sets `response["cache"] = "MISS"` (no `cache_key_version` key at all on this path — schema does
not require it), then calls `perform_cache_write()` in a broad `try/except: pass` (fail-open).

**Answers Open Question 2 (does §4.2 genuinely differ cold vs. warm?):** a genuine warm
(`hit_response`) payload = the stored redacted cold payload (byte-for-byte, modulo the no-op
redaction above) **plus** the `cache_key_version` field the cold response never carried (cold has
only `"cache": "MISS"`; warm has both `"cache": "HIT"` and `"cache_key_version": <int>`). A genuine
cache hit's serialized response is therefore **never smaller than, and typically a few bytes
larger than**, the corresponding cold response — caching cannot mathematically produce a §4.2
token-reduction win; at best it produces parity. This must be measured and reported honestly (per
Scope), not assumed, but the code-level reasoning above already predicts the direction: warm
`gateway_tokens` ≥ cold `gateway_tokens` for every entry that produces a genuine hit.

### The Phase 1 runner shape to mirror (`tools/agent-monitoring/kgmcp_phase1_gateway_runner.py`)
`_load_gateway_module()` (L106-113): `importlib.util` sibling-loads `knowledge_gateway_mcp.py`
under the fixed `sys.modules` key `"kgmcp_phase1_comparison_gateway"`, cached — repeat calls reuse
the same module object (needed for any monkeypatch/spy to survive across calls). `run_corpus()`
(L210-305) loops `CORPUS`, does exactly **one** `_run_knowledge_context(query_text)` call per
entry, timed externally with `time.perf_counter()` (Design Decision D1: no `retrieval_events.py`
wrapper call sites exist on this path — reconfirmed still true, this ticket does not touch that
module). It also re-derives `threshold_ms`/`threshold_tokens` live from the Phase 0 fixture (never
hand-typed) and computes §4.3 via `_compute_threshold_4_3()` (L165-207), which calls
`_normalize_phase1_source_id()` (L116-152, Design Decision D2's exact normalization rule) and
`_path_only()` (L155-162, Design Decision D3's path-only comparison). These three functions are
pure, still-valid, and directly reusable by import — no change needed to the doc_id/evidence-ID
normalization rule itself.

### The doc_id fix (Open Question 3) — confirmed still in effect, confirmed untouched by the cache ticket
`tools/knowledge_search.py` (current read, L285-287): `doc_id = rel.with_suffix("").as_posix()` —
the full nested relative path under `docs/`, exactly the fix landed by
`TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION` (`git log --oneline -- tools/knowledge_search.py`
shows that ticket's commit `6a63b65d` as the fix, applied *after* the P1 baseline comparison ran).
`git status --porcelain` for the currently-staged `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`
change set (the dependency this ticket measures) lists `tools/knowledge_gateway_cache.py`,
`tools/retrieval_cache.py`, `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_redaction.py`
and doc/test files — **`tools/knowledge_search.py` does not appear anywhere in that diff.** The fix
is genuinely still in effect and genuinely unaffected by the cache-wiring work. Per Phase 1's own
results doc, the doc_id truncation was an *additional* cause of Q1/Q3/Q4/Q6/Q7's recall misses
(beyond Q2/Q5's architectural single-provider-routing cause) — this ticket's own §4.3
recomputation should therefore see improved (though not necessarily perfect, given ongoing corpus
drift — see Risks §6) recall on those 5 entries, and an unchanged, still-expected miss on Q2/Q5.

### Real cache-hit verification precedent already in this repo
`tests/tools/test_knowledge_gateway_mcp.py::_patch_small_cacheable_search()` (L308-328) establishes
the pattern: a plain-Python spy assigned via `monkeypatch.setattr(pa_search_mod, "_run_search",
spy)` that appends to a list on every call — `test_identical_repeated_knowledge_context_call_is_a_
genuine_cache_hit` (L331-342) then asserts `len(search_calls) == 1` after both calls, i.e. the
provider was invoked exactly once despite two `_run_knowledge_context()` calls. This is real,
already-established precedent for "spy proving the provider round-trip was skipped," but it is
`pytest`'s `monkeypatch` fixture, not usable inside a standalone script.
`tests/tools/test_retrieval_cache.py::test_record_provider_result_cache_hit_increments_hit_count_
and_stamps_last_hit_at` (L703-715) is the direct-SQL-read precedent: `SELECT hit_count,
last_hit_at FROM retrieval_provider_result_cache_rows WHERE query_hash = ? AND repo_branch_scope =
?` before/after, asserting `hit_count == 1`.

**Answers Open Question 1:** a plain, non-`unittest.mock` spy (direct attribute reassignment,
restored in a `finally` block — the same idiom `_patch_small_cacheable_search` uses, just without
the `pytest` fixture) on `_kgpa.assemble_packet` (obtained via
`mod._load_packet_assembly_module()`, the same cached module object `_run_knowledge_context()`
itself calls through, since both go through the same `sys.modules` key) gives a real,
code-external-to-the-measured-path signal: count calls across an entry's cold+warm pair; a genuine
warm hit must show exactly 1, not 2. A second, fully independent (does not touch any gateway
module at all) signal is a direct SQL read of the specific row's `hit_count`/`last_hit_at` via
`(query_hash, repo_branch_scope)` derived from `_kgc.compute_lookup_identity()` — before/after the
warm call, expecting a delta of exactly 1 on a genuine hit. **Neither of these requires
`unittest.mock`/`MagicMock`**, consistent with `test_comparison_runner_calls_real_run_knowledge_
context_not_a_mock`'s AST guard (which bans `mock`/`MagicMock` imports/strings in the runner, not
plain attribute-reassignment spies — the same distinction the existing test suite already relies
on). Relying on `response["cache"] == "HIT"` alone does **not** satisfy AC1's "not assumed" bar,
since that field is computed by the exact code path being measured.

## Mechanics / Engine Constraints
This is agent-infrastructure tooling, not simulation-domain logic — no `docs/mechanics/`,
`src/domains/`, or entity/combat/economy law applies. Controlling documents:
- `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` §4.1 (formula:
  warm-hit end-to-end latency ≤ 50% × Phase 0 average `combined.wall_time_ms` = 935.32 ms, fixed),
  §4.2 (formula: packet token count ≤ 50% × Phase 0 average `combined.serialized_tokens_estimate`
  = 1263.57 tokens, fixed — note the formula text says "a future gateway's packet token count,"
  not explicitly "warm-hit," consistent with this ticket's Scope computing it for both cold and
  warm), §4.3 (formula: per-query superset-of-union recall, unchanged).
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` §1-§5 (lookup
  identity, evidence-validity identity, Non-collapse rule, branch/working-tree-scope hard
  partition) — governs what "genuine hit" structurally means; this ticket measures against that
  definition, does not redefine it.
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §5 (the 8192-byte
  cap this investigation's central finding is about) and §9 (SQLite operational limits, not a
  practical constraint at this scale).

## Docs Requiring Update
- `docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md`: new file (mirrors
  `phase1_baseline_comparison.md`'s own pattern) reporting this ticket's real cold-vs-warm §4.1/
  §4.2/§4.3 results, including the honest size-cap finding above if it is confirmed by the real
  run.
- `docs/plans/knowledge-gateway-mcp-proposal.md`: Phase 2's own §20 section (all 4 bullets already
  annotated **Done** by the 3 prior child tickets — confirmed by direct read, lines 1210-1273; this
  ticket satisfies no unannotated bullet, mirroring Phase 1's own precedent) needs a new
  results-narrative paragraph appended after the "Add exact normalized-query reuse" bullet, stating
  this ticket's real §4.1/§4.2/§4.3 outcome, exactly as the Phase 1 section itself received such a
  paragraph (lines ~1192-1208) from `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON`.
- `docs/parity_ledger/infrastructure.yaml`: add a new `INFRA-344` entry (next sequential ID —
  `INFRA-341`/`342`/`343` already exist, uncommitted-but-staged, from the 3 prior Phase 2 child
  tickets), following the same one-entry-per-ticket precedent `INFRA-334` through `INFRA-343`
  already established.

## Parity Ledger Overlap
`docs/parity_ledger/infrastructure.yaml` `INFRA-334` (Phase 0 baseline) through `INFRA-343`
(latest Phase 2 child) are all `status: verified`, priority `P1`/`P2` — none is `P0`, so none
carries a hard `test_path`-required gate this ticket must satisfy. This ticket should add
`INFRA-344` in the same sequence, per that sequence's own established one-entry-per-ticket
convention (each entry records its own ticket's work, never amends a sibling's).

## Prior Work
- `stored_artifacts/TCK-20260815-KGMCP-P1-BASELINE-COMPARISON/` (investigation.md, test_plan.md,
  plan.md) — the direct structural precedent this ticket extends; read in full. Its investigation's
  Risk #1 (ticket-scope factual error about `retrieval_events.py` wiring) and Risk #3 (§4.3 format
  mismatch, resolved by Design Decision D2) do not recur here (both already resolved/still valid);
  its Risk #4 (graphify half of §4.3 union is N/A, no Phase 0 graphify source baseline) still
  applies unchanged — this ticket inherits the same `graphify_half_status: "N/A"` honest limitation.
- `stored_artifacts/TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING/` — the dependency this ticket
  measures; confirms both real provider capability descriptors
  (`provider_capabilities_context_search.json`, `provider_capabilities_graphify.json`) declare
  `fine_grained_fingerprints: false` today, so `revalidate_cache_row()` always uses the
  `PROVIDER_GENERATION` validation basis in practice — the SYMBOL/FILE fingerprint path is untested
  against real live data (a disclosed, pre-existing limitation this ticket inherits, not something
  it needs to resolve).
- `tickets/done/TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION.md` — read in full; confirms the
  fix, its file location, and its independence from the cache-wiring diff (see Current Behavior
  above).
- `tests/tools/test_knowledge_gateway_mcp.py`, `tests/tools/test_retrieval_cache.py` — supply the
  two real verification-signal precedents (spy-via-attribute-reassignment; direct-SQL hit_count
  read) this ticket's own runner and test suite should reuse.

## Risks and Open Questions

1. **[Highest severity — may block AC1 outright for some or all of the 7 entries] Real response
   payloads almost certainly exceed the 8192-byte cache-write size cap under the default request
   shape.** See Current Behavior's quantified table: every one of the 7 corpus entries' real cold
   `gateway_tokens` (as already recorded in the committed Phase 1 fixture, ranging 2649-7633
   tokens ≈ 10.6-30.5 KB) implies a serialized byte size well over `MAX_PAYLOAD_BYTES = 8192`, and
   `redact_content()` does not meaningfully shrink repo-relative-path content. If this holds under
   this ticket's own live re-run, `perform_cache_write()` will REJECT the write
   (`rejection_category == "oversized_payload"`) for some or all entries, `perform_cache_lookup()`
   will find no row on the "warm" second call, and that "warm" call will actually be a second cold
   call — no genuine cache hit, no latency improvement, `§4.1` still measured cold-vs-cold. This
   would make AC1's "each entry's warm call independently verified as a genuine cache hit"
   structurally unsatisfiable for those entries, not because of a bug in this ticket's own runner
   but because of a real property of the real system given real corpus response sizes. **This is a
   genuine, load-bearing open decision for Plan, not something Investigate should resolve by
   assumption:**
   - (a) Request a smaller `budget_tokens` per corpus entry (a legitimate `knowledge_context`
     request-schema field per `knowledge_context_request.schema.json` — not a code change to any
     frozen module) to try to bring the redacted payload under 8 KB. This is a real, in-scope
     choice (a request parameter, not gateway/cache code), but it diverges from Phase 1's own
     exact call shape (no `budget_tokens` override) — if taken, it must be disclosed explicitly as
     a deliberate methodology difference in the new results doc, not silently applied to "make
     caching work." Whether a smaller budget genuinely produces a sub-8KB payload (rather than just
     shrinking `context`/`evidence` while fixed per-field JSON/schema overhead keeps the total over
     cap) is not something Investigate can determine without running code — Plan/Implement must
     test this empirically.
   - (b) Keep exact parity with Phase 1's call shape (no `budget_tokens` override) and honestly
     report, per entry, whichever of {genuine HIT, size-cap-blocked MISS, other-reason MISS}
     actually occurred — including the real possibility that 0/7 entries ever produce a genuine
     warm state, which is itself a legitimate, informative, honestly-reportable finding (directly
     analogous to Phase 1's own "Phase 1 cannot produce a warm-hit state at all" honest caveat, now
     for a different, Phase-2-internal structural reason).
   Either path is legitimate; silently picking (a) without disclosure, or silently treating a
   size-cap-blocked MISS as if it were a "cache didn't help this time" data point without stating
   the mechanism, would both violate the ticket's own honesty bar.

2. **Verifying a genuine hit requires more than trusting `response["cache"]`.** See Current
   Behavior's "Real cache-hit verification precedent" section — recommend the runner use BOTH: (a)
   a plain-Python spy (direct attribute reassignment, restored via `finally`, never
   `unittest.mock`/`MagicMock`) on `_kgpa.assemble_packet` counting invocations per entry across
   its cold+warm pair, and (b) a direct SQL read of `retrieval_provider_result_cache_rows.hit_count`
   /`last_hit_at` for the row keyed by `(query_hash, repo_branch_scope)` (both derivable via
   `_kgc.compute_lookup_identity()`) before/after the warm call. Both are real, code-external (or
   at least measurement-external) signals distinct from the self-reported `response["cache"]`
   field, satisfying AC1's explicit "not assumed" requirement. Neither requires editing any frozen
   module — both are read-only observation techniques the runner applies to itself.

3. **§4.2 warm-path tokens are expected, by direct code-level reasoning (not yet measured), to be
   ≥ cold-path tokens, never smaller — for whichever entries genuinely cache.** See Current
   Behavior: a genuine hit response carries every field the cold response's stored payload had,
   plus a `cache_key_version` field the cold response's `"cache": "MISS"`-only markup never
   carried. This must still be measured and reported with real numbers (per Scope, no assumption
   allowed) — this section only records the code-level prediction so Plan/Implement can treat a
   contradicting real result as worth investigating rather than silently accepting either way.

4. **Runner file layout (the ticket's own stated open question) — recommend a NEW sibling file,
   not an in-place extension of `kgmcp_phase1_gateway_runner.py`.** Reasons: (a) that file's own
   tests (`test_kgmcp_phase1_baseline_comparison.py`) directly `ast.parse()` its source and
   `importlib`-load it under a fixed `sys.modules` key assuming a single-cold-call-per-entry shape
   (`test_comparison_runner_calls_real_run_knowledge_context_not_a_mock`,
   `test_zero_mutation_of_real_agent_monitoring_corpus_from_comparison_runner`) — extending its
   `run_corpus()` in place to do cold+warm double-calling would change the behavior those already-
   passing, DONE tests assert against, effectively modifying a sibling ticket's frozen deliverable;
   (b) `kgmcp_phase1_gateway_runner.py`'s own docstring frames it as specifically the Phase 1
   comparison's one-time script, with Design Decisions (D1-D4) baked into its identity; (c) this
   exactly mirrors how `kgmcp_phase1_gateway_runner.py` itself was created as a NEW sibling of (not
   an edit to) `kgmcp_baseline_runner.py`, reusing only its pure corpus/token-heuristic helpers by
   import. **Recommendation:** create `tools/agent-monitoring/kgmcp_phase2_gateway_runner.py`,
   importing (not duplicating) `_normalize_phase1_source_id`, `_path_only`, and
   `_compute_threshold_4_3` from `kgmcp_phase1_gateway_runner.py` (all three are pure, still-valid,
   unrelated to the cold/warm double-call shape change), writing new `run_corpus()`/`main()`
   functions for the double-call shape, targeting a new fixture path
   (`tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json`) and new results doc
   (`docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md`).

5. **Corpus/index drift across this ticket's own run.** Per Phase 1's own results doc, the live
   `docs/`/`tickets/` corpus continues to evolve after any fixture recording, and Phase 1's own
   comparison already reflected ~7 hours of drift from Phase 0's fixture time. This ticket's run
   will reflect further drift since Phase 1's `2026-08-15T12:08:34Z` recording — an honest,
   disclosed confound on §4.3 numbers, not a defect, to be restated in the new results doc exactly
   as Phase 1 restated it for its own predecessor.

6. **A concurrent index rebuild mid-run would silently force every subsequent warm call to MISS.**
   `revalidate_cache_row()`'s `PROVIDER_GENERATION` basis (the only basis either real provider
   supports today) compares `row["provider_generation_at_validation"]` against
   `rc._corpus_generation()`, which reads `knowledge-index/manifest.json`'s `built_at` fresh on
   every call. If anything rebuilds the index (`make knowledge-index-update` or similar) between an
   entry's cold and warm call, that entry's cache row is correctly treated as stale — a real,
   intended behavior, but the runner must not itself trigger a rebuild mid-run and should verify
   `manifest.json`'s `built_at` is unchanged across the whole corpus run (extending Phase 1's own
   zero-mutation-of-`agent-monitoring/` guard to also cover `knowledge-index/manifest.json`).

7. **`Q3_requirement_completeness`'s own Phase 0 baseline note** (its `notes` field states no
   Parity Ledger adapter existed at Phase 0) still applies unchanged — inherited context, not new.

## Anti-Drift Hazards
- **Never edit `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` or
  `tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json`** — both are explicitly,
  repeatedly named in this ticket's own Related Docs/Scope as records this ticket extends, never
  edits. Test this with a `git diff --stat`-based guard mirroring
  `test_no_frozen_kgmcp_dependency_edited`.
- **Never widen routing or touch `tools/knowledge_gateway_router.py`** to make Q2/Q5's §4.3 recall
  "pass" — the single-primary-provider routing design is frozen, and this ticket's own Scope
  explicitly predicts and accepts the Q2/Q5 miss recurring for the same architectural reason.
- **Never touch `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_router.py`,
  `tools/knowledge_gateway_packet_assembly.py`, `tools/knowledge_gateway_cache.py`,
  `tools/retrieval_cache.py`, or `tools/knowledge_gateway_redaction.py`** — all are frozen
  dependencies this ticket only calls/reads; this ticket's own Scope is measurement-only.
  `tools/knowledge_search.py` (the doc_id fix) is likewise not this ticket's to touch — it is
  already fixed and confirmed unaffected.
- **Never silently reinterpret a size-cap-blocked MISS as "the cache didn't help this time" without
  naming the mechanism** — see Risk #1. A `cache_write_rejection_reason` field (or equivalent)
  should be recorded per entry in the new fixture so a size-cap block is distinguishable from any
  other MISS cause, exactly as `provider_failures` already distinguishes provider errors from
  "provider simply wasn't called."
- **Never assume caching alone fixes §4.2** — the epic's own Request Summary/Out of Scope forbid
  this explicitly; Risk #3's code-level reasoning must be confirmed or refuted with real numbers,
  never asserted as already-proven by this investigation alone.
- **Never let a missing/rejected comparison field degrade silently** — mirror
  `test_kgmcp_phase1_baseline_comparison.py`'s explicit field-presence + non-empty-`derivation`
  convention for every new fixture field this ticket introduces (`warm_call_wall_time_ms`,
  `provider_round_trip_call_count`, `cache_hit_count_delta`, `cache_write_rejection_reason`, etc.).

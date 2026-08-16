#!/usr/bin/env python3
"""One-time recomparison-runner script for the Knowledge Gateway MCP Phase 2 baseline
recomparison (TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON).

**Design Decision DD1 (`staging_artifacts/TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON/plan.md`,
ruled by Architecture Review in favor of option (b)): this script keeps EXACT Phase 1 request-shape
parity.** No `budget_tokens` override is ever passed to `_run_knowledge_context()` — every call
uses the gateway's own `DEFAULT_BUDGET_TOKENS` (4000). This means the script does NOT attempt to
shrink the per-entry request to dodge `tools/knowledge_gateway_redaction.py::check_size_cap()`'s
8192-byte cache-write size cap. Every one of the 7 corpus entries' real response payload
(10.6-30.5 KB per the committed Phase 1 fixture) is expected, honestly, to exceed that cap under
this shape — meaning `perform_cache_write()` will likely REJECT the write (`rejection_category ==
"oversized_payload"`) for some or all entries, and the "warm" second call for those entries will
structurally be a second cold call, not a genuine cache hit. This is the real, current capacity of
the deployed cache relative to this gateway's real response sizes, and this script reports it as
exactly that — not as a bug in this script or a failure of the ticket.

What this measures: for each of `kgmcp_baseline_corpus.CORPUS`'s 7 entries (imported read-only,
never modified or cherry-picked), this script calls the real
`tools/knowledge_gateway_mcp.py::_run_knowledge_context(query_text)` TWICE — once cold (first
call), once warm (second call) — timing both with `time.perf_counter()` wrapped directly around
each call. It independently verifies whether the warm call was a genuine cache hit via TWO real,
code-external signals (never `response["cache"]` alone):
  (a) a plain-Python counting spy (direct attribute reassignment, restored in `finally`, never any
      attribute-mocking library) on `_kgpa.assemble_packet` — the real provider round-trip,
      structurally never called on a genuine hit path (`tools/knowledge_gateway_mcp.py:220-238`);
  (b) a direct, read-only SQL read of `retrieval_provider_result_cache_rows.hit_count` before and
      after the warm call, keyed by `(query_hash, repo_branch_scope)` derived from the real
      `_kgc.compute_lookup_identity()` (never reimplemented).
A second spy, on `tools.knowledge_gateway_redaction.evaluate_write_candidate`, captures the real
write-rejection reason (e.g. `"oversized_payload"`) whenever a write is attempted and rejected, so
a size-cap-blocked MISS is never silently relabeled or reported as a bare, mechanism-less "MISS".

What this does not do: it does not shrink `budget_tokens`, pre-clear/seed the real cache DB, widen
routing, redefine any §4 threshold formula, or drop/substitute any of the 7 corpus entries. §4.1
(latency) is computed against warm-path numbers ONLY. §4.2 (token reduction) is computed
independently for cold AND warm responses, for every entry, honestly (a warm number for an
uncached entry is the second call's real, unmodified number — never fabricated, never copied from
the cold number). §4.3 (no-regression recall) is computed from the cold response, via the imported,
unmodified `_compute_threshold_4_3` — the same normalization rule Phase 1 established, reused, not
reimplemented.

Never touches (all read-only imports/calls or restored spies): `tools/knowledge_gateway_mcp.py`,
`tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`,
`tools/knowledge_gateway_cache.py`, `tools/knowledge_gateway_redaction.py`,
`tools/retrieval_cache.py`, `tools/agent-monitoring/kgmcp_baseline_corpus.py`,
`tools/agent-monitoring/kgmcp_phase1_gateway_runner.py`,
`tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json`,
`tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json`, or
`docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md`.

Run once, by hand, during Implementation — never wired into pytest's fast loop, mirroring
`kgmcp_phase1_gateway_runner.py`'s own one-time-script convention.
"""

from __future__ import annotations

import importlib.util
import json
import sqlite3
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent.parent
_MONITORING_TOOLS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TOOLS_DIR.parent

if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from kgmcp_baseline_corpus import CORPUS, CORPUS_VERSION  # noqa: E402
from kgmcp_phase1_gateway_runner import (  # noqa: E402
    _compute_threshold_4_3,
    _normalize_phase1_source_id,
    _path_only,
)
from tools import knowledge_gateway_redaction as _kgr_redaction  # noqa: E402

_GATEWAY_MODULE_PATH = _TOOLS_DIR / "knowledge_gateway_mcp.py"
_MANIFEST_PATH = _REPO_ROOT / "knowledge-index" / "manifest.json"

_PHASE0_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "tools" / "fixtures" / "kgmcp_measurement_baseline_corpus_results.json"
)
_PHASE1_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "tools" / "fixtures" / "kgmcp_phase1_baseline_comparison_results.json"
)
_OUTPUT_PATH = (
    _REPO_ROOT
    / "tests"
    / "tools"
    / "fixtures"
    / "kgmcp_phase2_baseline_recomparison_results.json"
)

_GRAPHIFY_HALF_NA_NOTE = (
    "No Phase 0 graphify source baseline exists to compare against (inherited from Phase 1's own "
    "Design Decision D3 — the fixture recorded only raw_stdout_bytes, never a source list) — the "
    "graphify half of §4.3's union is reported as N/A here, not silently treated as "
    "empty-and-passing."
)

# DD1(b) — exact Phase 1 parity, no budget_tokens override. Recorded per entry for disclosure.
_BUDGET_TOKENS_USED = 4000  # tools.knowledge_gateway_mcp.DEFAULT_BUDGET_TOKENS, read live below.


def _load_gateway_module():
    """DD8 — this ticket's own `sys.modules` key, distinct from Phase 1's own
    `"kgmcp_phase1_comparison_gateway"` key, so this runner's spies never interact with a
    different sibling-loaded module instance."""
    key = "kgmcp_phase2_recomparison_gateway"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, _GATEWAY_MODULE_PATH)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]


def _load_manifest_built_at() -> str | None:
    """Risk #6's zero-mutation guard input — read fresh every call, never cached across the run,
    so a mid-run index rebuild is genuinely detectable."""
    if not _MANIFEST_PATH.exists():
        return None
    return json.loads(_MANIFEST_PATH.read_text()).get("built_at")


def _read_hit_count(_kgc, query_hash: str, repo_branch_scope: str) -> int:
    """Direct, read-only SQL read of `retrieval_provider_result_cache_rows.hit_count` — DD2's
    second, fully independent verification signal. `_kgc.rc` is the exact same
    `tools.retrieval_cache` singleton module object `perform_cache_lookup`/`perform_cache_write`
    themselves use (DD4/DD8's shared-singleton reasoning), so `_kgc.rc.CACHE_DB_PATH` is guaranteed
    to be the real, live cache DB path, never a second, independent copy."""
    db_path = Path(_kgc.rc.CACHE_DB_PATH)
    if not db_path.exists():
        return 0
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT hit_count FROM retrieval_provider_result_cache_rows "
            "WHERE query_hash = ? AND repo_branch_scope = ?",
            (query_hash, repo_branch_scope),
        ).fetchone()
    finally:
        conn.close()
    return row[0] if row is not None else 0


def _run_single_entry(mod, _kgpa, _kgc, _kgr, corpus_entry: dict) -> dict:
    """Steps 2's per-entry cold+warm double-call loop with both spies and the SQL delta check.
    Returns the raw per-entry measurement dict — threshold computation happens in `run_corpus()`
    once every entry's raw data exists."""
    query_text = corpus_entry["query_text"]
    request = {"query": query_text}  # DD1(b) — {"query": ...} only, no budget_tokens key.
    effective_budget = mod.DEFAULT_BUDGET_TOKENS

    # Step 2 item 4 — real, unwrapped route() call; identity computed via the real
    # compute_lookup_identity(), never reimplemented (DD4).
    routing_decision = _kgr.route(query_text)
    identity = _kgc.compute_lookup_identity(request, routing_decision, effective_budget)

    # Step 2 item 2 — assemble_packet spy (DD2). Plain attribute reassignment, restored in finally.
    _orig_assemble = _kgpa.assemble_packet
    call_count: list[int] = []

    def _assemble_spy(*args, **kwargs):
        call_count.append(1)
        return _orig_assemble(*args, **kwargs)

    _kgpa.assemble_packet = _assemble_spy

    # Step 2 item 3 — evaluate_write_candidate spy (DD3). Pass-through, never alters behavior.
    _orig_evaluate = _kgr_redaction.evaluate_write_candidate
    write_decisions: list = []

    def _evaluate_spy(*args, **kwargs):
        decision = _orig_evaluate(*args, **kwargs)
        write_decisions.append(decision)
        return decision

    _kgr_redaction.evaluate_write_candidate = _evaluate_spy

    try:
        # Step 2 item 5 — pre-cold-call hit_count read.
        hit_count_before_warm = _read_hit_count(_kgc, identity["query_hash"], identity["repo_branch_scope"])

        # Step 2 item 6 — cold call.
        start = time.perf_counter()
        response_cold = mod._run_knowledge_context(query_text)
        cold_call_wall_time_ms = (time.perf_counter() - start) * 1000

        cold_call_anomaly = None
        if response_cold.get("cache") != "MISS":
            cold_call_anomaly = (
                f"first (cold) call reported response['cache'] == {response_cold.get('cache')!r}, "
                "not 'MISS' — a stale row from a previous manual run may already have been present "
                "for this identity; this runner does not pre-clear the cache DB (Anti-Drift Notes), "
                "so this is reported, not silently normalized away."
            )

        # Step 2 item 7 — post-cold-call hit_count read.
        hit_count_after_cold = _read_hit_count(_kgc, identity["query_hash"], identity["repo_branch_scope"])

        # Step 2 item 8 — warm call.
        start = time.perf_counter()
        response_warm = mod._run_knowledge_context(query_text)
        warm_call_wall_time_ms = (time.perf_counter() - start) * 1000

        # Step 2 item 9 — post-warm-call hit_count read.
        hit_count_after_warm = _read_hit_count(_kgc, identity["query_hash"], identity["repo_branch_scope"])
    finally:
        # Step 2 item 10 — restore both spies.
        _kgpa.assemble_packet = _orig_assemble
        _kgr_redaction.evaluate_write_candidate = _orig_evaluate

    provider_round_trip_call_count = len(call_count)
    cache_hit_count_delta = hit_count_after_warm - hit_count_after_cold

    # Step 2 item 11 — cache_status_warm derived from BOTH signals agreeing (DD2), never from
    # response_warm["cache"] alone.
    spy_says_hit = provider_round_trip_call_count == 1
    sql_says_hit = cache_hit_count_delta == 1
    cache_status_warm = "HIT" if (spy_says_hit and sql_says_hit) else "MISS"

    signal_anomaly = None
    if spy_says_hit != sql_says_hit:
        signal_anomaly = (
            f"cache-hit verification signals disagree for this entry: assemble_packet spy count="
            f"{provider_round_trip_call_count} (implies "
            f"{'HIT' if spy_says_hit else 'MISS'}), db hit_count delta={cache_hit_count_delta} "
            f"(implies {'HIT' if sql_says_hit else 'MISS'}). cache_status_warm is conservatively "
            "reported as MISS since both signals are required to agree (DD2) — this disagreement "
            "itself is reported, not silently resolved."
        )

    # Step 2 item 12 — cache_write_rejection_reason from the cold call's own write attempt (the
    # first captured WriteDecision, since the cold call is the first to attempt a write).
    cache_write_rejection_reason = None
    if write_decisions:
        cold_decision = write_decisions[0]
        if cold_decision.verdict != _kgr_redaction.ALLOW:
            cache_write_rejection_reason = cold_decision.rejection_category

    return {
        "corpus_entry": corpus_entry,
        "request": request,
        "routing_decision": routing_decision,
        "identity": identity,
        "response_cold": response_cold,
        "response_warm": response_warm,
        "cold_call_wall_time_ms": cold_call_wall_time_ms,
        "warm_call_wall_time_ms": warm_call_wall_time_ms,
        "cold_call_anomaly": cold_call_anomaly,
        "hit_count_before_warm": hit_count_before_warm,
        "hit_count_after_cold": hit_count_after_cold,
        "hit_count_after_warm": hit_count_after_warm,
        "cache_hit_count_delta": cache_hit_count_delta,
        "provider_round_trip_call_count": provider_round_trip_call_count,
        "cache_status_warm": cache_status_warm,
        "signal_anomaly": signal_anomaly,
        "cache_write_rejection_reason": cache_write_rejection_reason,
    }


def _compute_entry_thresholds(raw: dict, _kgpa, threshold_ms: float, threshold_tokens: float, phase0_entry: dict) -> dict:
    """Step 3 — §4.1 warm-only, §4.2 cold+warm separately, §4.3 via the imported Phase 1 helper."""
    warm_ms = raw["warm_call_wall_time_ms"]
    threshold_4_1_latency = {
        "pass": warm_ms <= threshold_ms,
        "warm_call_wall_time_ms": warm_ms,
        "threshold_ms": threshold_ms,
        "derivation": (
            "warm_call_wall_time_ms = time.perf_counter() wrapped directly around the SECOND "
            "_run_knowledge_context(query_text) call for this entry. threshold_ms = 0.5 * "
            "mean(Phase 0 fixture's combined.wall_time_ms across its 7 entries), per "
            "measurement_baseline_contract.md §4.1, re-derived live from the fixture on every run, "
            "never hand-typed. Per AC2, cold_call_wall_time_ms is never used for this threshold's "
            "pass determination — only warm_call_wall_time_ms, even when cache_status_warm is "
            "'MISS' (i.e. the 'warm' call never became a genuine cache hit for this entry; the "
            "real second-call number is still reported honestly, per AC2's 'whatever the result')."
            " pass = (warm_call_wall_time_ms <= threshold_ms)."
        ),
    }

    cold_tokens = _kgpa.kgmcp_char_heuristic_v1(json.dumps(raw["response_cold"]))
    warm_tokens = _kgpa.kgmcp_char_heuristic_v1(json.dumps(raw["response_warm"]))
    threshold_4_2_cold_tokens = {
        "pass": cold_tokens <= threshold_tokens,
        "gateway_tokens": cold_tokens,
        "threshold_tokens": threshold_tokens,
        "derivation": (
            "gateway_tokens = knowledge_gateway_packet_assembly.kgmcp_char_heuristic_v1("
            "json.dumps(response_cold)) — the full real cold-call response payload. "
            "threshold_tokens = 0.5 * mean(Phase 0 fixture's combined.serialized_tokens_estimate "
            "across its 7 entries), per measurement_baseline_contract.md §4.2, re-derived live, "
            "never hand-typed. pass = (gateway_tokens <= threshold_tokens)."
        ),
    }
    threshold_4_2_warm_tokens = {
        "pass": warm_tokens <= threshold_tokens,
        "gateway_tokens": warm_tokens,
        "threshold_tokens": threshold_tokens,
        "derivation": (
            "gateway_tokens = knowledge_gateway_packet_assembly.kgmcp_char_heuristic_v1("
            "json.dumps(response_warm)) — the full real warm-call (second-call) response payload, "
            "computed independently from the cold measurement above, never copied or assumed from "
            "it — including when cache_status_warm is 'MISS', in which case this is honestly a "
            "second cold call's own real token count (AC3: 'no assumption that caching alone "
            "satisfies it'). threshold_tokens = same live-derived constant as "
            "threshold_4_2_cold_tokens. pass = (gateway_tokens <= threshold_tokens)."
        ),
    }

    baseline_sources = phase0_entry["context_search"]["sources_recalled"]
    gateway_sources_raw = [
        c["source_id"] for c in raw["response_cold"].get("context", []) if "source_id" in c
    ]
    threshold_4_3_recall_cold = _compute_threshold_4_3(baseline_sources, gateway_sources_raw)
    threshold_4_3_recall_cold["derivation"] += (
        " Computed from the cold response only (Plan Step 3 decision): a genuine warm HIT's "
        "context/evidence content is identical to the cold response that produced the cached row, "
        "so recall would be identical either way for a genuine hit; for an entry that never "
        "genuinely caches, the 'warm' response is itself another cold call, so a separately-labeled "
        "warm recall number would just be a second independent cold measurement dressed up as a "
        "warm one — reported as threshold_4_3_recall_cold, not fabricated as a distinct warm value."
    )

    return {
        "threshold_4_1_latency": threshold_4_1_latency,
        "threshold_4_2_cold_tokens": threshold_4_2_cold_tokens,
        "threshold_4_2_warm_tokens": threshold_4_2_warm_tokens,
        "threshold_4_3_recall_cold": threshold_4_3_recall_cold,
    }


def run_corpus() -> dict:
    mod = _load_gateway_module()
    _kgr = mod._load_router_module()
    _kgpa = mod._load_packet_assembly_module()
    _kgc = mod._load_cache_module()

    phase0_fixture = json.loads(_PHASE0_FIXTURE_PATH.read_text())
    phase1_fixture = json.loads(_PHASE1_FIXTURE_PATH.read_text())
    phase0_entries_by_id = {e["id"]: e for e in phase0_fixture["entries"]}
    phase1_entries_by_id = {e["id"]: e for e in phase1_fixture["entries"]}

    threshold_ms = 0.5 * statistics.mean(
        e["combined"]["wall_time_ms"] for e in phase0_fixture["entries"]
    )
    threshold_tokens = 0.5 * statistics.mean(
        e["combined"]["serialized_tokens_estimate"] for e in phase0_fixture["entries"]
    )

    pre_run_manifest_built_at = _load_manifest_built_at()

    entries = []
    for corpus_entry in CORPUS:
        raw = _run_single_entry(mod, _kgpa, _kgc, _kgr, corpus_entry)
        phase0_entry = phase0_entries_by_id[corpus_entry["id"]]
        phase1_entry = phase1_entries_by_id[corpus_entry["id"]]
        thresholds = _compute_entry_thresholds(raw, _kgpa, threshold_ms, threshold_tokens, phase0_entry)

        phase1_missing_count = len(phase1_entry["threshold_4_3_recall"]["missing_sources"])
        phase1_baseline_count = len(phase1_entry["threshold_4_3_recall"]["baseline_sources"])
        this_missing_count = len(thresholds["threshold_4_3_recall_cold"]["missing_sources"])
        this_baseline_count = len(thresholds["threshold_4_3_recall_cold"]["baseline_sources"])

        entry = {
            "id": corpus_entry["id"],
            "query_text": corpus_entry["query_text"],
            "routing_shape": corpus_entry["routing_shape"],
            "budget_tokens_used": mod.DEFAULT_BUDGET_TOKENS,
            "providers_selected": list(raw["routing_decision"].providers_selected),
            "provider_failures_cold": raw["response_cold"].get("provider_failures", []),
            "provider_failures_warm": raw["response_warm"].get("provider_failures", []),
            "cold_call_wall_time_ms": raw["cold_call_wall_time_ms"],
            "warm_call_wall_time_ms": raw["warm_call_wall_time_ms"],
            "cache_status_warm": raw["cache_status_warm"],
            "provider_round_trip_call_count": raw["provider_round_trip_call_count"],
            "hit_count_before_warm": raw["hit_count_before_warm"],
            "hit_count_after_cold": raw["hit_count_after_cold"],
            "hit_count_after_warm": raw["hit_count_after_warm"],
            "cache_hit_count_delta": raw["cache_hit_count_delta"],
            "cache_write_rejection_reason": raw["cache_write_rejection_reason"],
            "cold_call_anomaly": raw["cold_call_anomaly"],
            "signal_anomaly": raw["signal_anomaly"],
            "threshold_4_1_latency": thresholds["threshold_4_1_latency"],
            "threshold_4_2_cold_tokens": thresholds["threshold_4_2_cold_tokens"],
            "threshold_4_2_warm_tokens": thresholds["threshold_4_2_warm_tokens"],
            "threshold_4_3_recall_cold": thresholds["threshold_4_3_recall_cold"],
            "phase1_recall_missing_count": phase1_missing_count,
            "phase1_recall_baseline_count": phase1_baseline_count,
            "recall_missing_count_comparison_to_phase1": (
                f"Phase 2 (this run): {this_missing_count}/{this_baseline_count} missing. "
                f"Phase 1 (recorded): {phase1_missing_count}/{phase1_baseline_count} missing."
            ),
            "derivation": (
                "cold_call_wall_time_ms/warm_call_wall_time_ms = time.perf_counter() wrapped "
                "directly around two successive real _run_knowledge_context(query_text) calls, no "
                "mock, no monkeypatch of the gateway itself. cache_status_warm is derived from BOTH "
                "a plain-Python counting spy on _kgpa.assemble_packet (exactly 1 call across the "
                "cold+warm pair = genuine hit) AND a direct SQL read of "
                "retrieval_provider_result_cache_rows.hit_count before/after the warm call (delta "
                "== 1 = genuine hit) agreeing — never from response['cache'] alone (DD2). "
                "cache_write_rejection_reason is captured via a pass-through spy on "
                "tools.knowledge_gateway_redaction.evaluate_write_candidate around the cold call's "
                "own write attempt (DD3) — perform_cache_write() itself always returns None and "
                "discards this information, so this is the only way to observe it."
            ),
        }
        entries.append(entry)

    post_run_manifest_built_at = _load_manifest_built_at()
    if post_run_manifest_built_at != pre_run_manifest_built_at:
        raise RuntimeError(
            "knowledge-index/manifest.json's built_at changed during this run "
            f"({pre_run_manifest_built_at!r} -> {post_run_manifest_built_at!r}) — a concurrent "
            "index rebuild invalidates every subsequent revalidation (Investigation Risk #6); "
            "this run's results are unusable and must not be written to the fixture."
        )

    aggregate = _compute_aggregate(entries)

    return {
        "corpus_version": CORPUS_VERSION,
        "compared_against_phase0_corpus_version": phase0_fixture["corpus_version"],
        "compared_against_phase1_recorded_at_utc": phase1_fixture["recorded_at_utc"],
        "recorded_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "manifest_built_at_at_run_time": pre_run_manifest_built_at,
        "budget_tokens_used_for_every_entry": mod.DEFAULT_BUDGET_TOKENS,
        "request_shape_note": (
            "DD1(b), Architecture Review ruling: exact Phase 1 request-shape parity — every call "
            "is _run_knowledge_context(query_text) with no budget_tokens override, matching Phase "
            "1's own call shape exactly. No request-shrinking fallback was implemented."
        ),
        "entries": entries,
        "aggregate": aggregate,
    }


def _compute_aggregate(entries: list[dict]) -> dict:
    aggregate: dict = {}
    threshold_keys = (
        ("threshold_4_1_latency", "threshold_4_1"),
        ("threshold_4_2_cold_tokens", "threshold_4_2_cold"),
        ("threshold_4_2_warm_tokens", "threshold_4_2_warm"),
        ("threshold_4_3_recall_cold", "threshold_4_3"),
    )
    for entry_key, aggregate_key in threshold_keys:
        pass_count = sum(1 for e in entries if e[entry_key]["pass"])
        aggregate[aggregate_key] = {"pass_count": pass_count, "of": len(entries)}

    all_thresholds_pass = all(
        entry[entry_key]["pass"] for entry in entries for entry_key, _ in threshold_keys
    )
    aggregate["all_thresholds_pass"] = all_thresholds_pass

    genuine_hit_count = sum(1 for e in entries if e["cache_status_warm"] == "HIT")
    aggregate["genuine_cache_hit_count"] = {"count": genuine_hit_count, "of": len(entries)}
    return aggregate


def main() -> None:
    report = run_corpus()
    _OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {_OUTPUT_PATH} ({len(report['entries'])} entries)")
    print(f"aggregate: {json.dumps(report['aggregate'], indent=2, sort_keys=True)}")


if __name__ == "__main__":
    main()

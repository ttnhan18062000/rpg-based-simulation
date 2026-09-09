#!/usr/bin/env python3
"""One-time comparison-runner script for the Knowledge Gateway MCP Phase 1 baseline comparison
(TCK-20260815-KGMCP-P1-BASELINE-COMPARISON).

Run once, by hand, during Implementation — never wired into the fast pytest loop, mirroring
`kgmcp_baseline_runner.py`'s own one-time-script convention. For each of
`kgmcp_baseline_corpus.CORPUS`'s 7 entries (imported read-only, never modified or cherry-picked),
this script:

1. Loads `tools/knowledge_gateway_mcp.py` in-process via `importlib.util` (the same sibling-loading
   pattern the module itself and `tests/tools/test_knowledge_gateway_mcp.py` already use) and calls
   the real `_run_knowledge_context(query_text)`, timed with `time.perf_counter()` wrapped directly
   around the call.

   Design Decision D1 (`staging_artifacts/TCK-20260815-KGMCP-P1-BASELINE-COMPARISON/plan.md`):
   `tools/retrieval_events.py`'s 3 Wrapper functions (`wrap_hybrid_retrieval`,
   `wrap_retrieval_cache_check`, `wrap_context_packet_assembly`) are confirmed to have zero real
   call sites in the Phase 1 gateway pipeline (`tools/knowledge_gateway_mcp.py` never imports
   `retrieval_events`). This script therefore never imports or calls any of those 3 functions,
   never calls `emit_retrieval_event`, and times the real gateway call externally instead — exactly
   mirroring `kgmcp_baseline_runner.py`'s own external-timing precedent for the Phase 0 direct-tool
   baseline.
2. Calls `knowledge_gateway_router.route(query_text)` directly (read-only, side-effect-free) to
   record the real `providers_selected` list for that entry — the ground truth for whether
   `context_search` was actually consulted, never assumed from the routing table alone.
3. Measures `gateway_tokens` via the real `knowledge_gateway_packet_assembly.kgmcp_char_heuristic_v1`
   callable applied to `json.dumps(response)` — the full real response payload, mirroring Phase 0's
   `combined.serialized_tokens_estimate` measuring the full returned payload.
4. Normalizes each `response["context"][*]["source_id"]` value per Design Decision D2 and compares
   it against the Phase 0 fixture's `context_search.sources_recalled` list for the same corpus
   entry to compute §4.3's per-query no-regression-recall threshold.

   Design Decision D3: the graphify half of §4.3's union ("whatever authoritative sources the
   fixture's `graphify` result for that entry would resolve to") is not computable from the Phase 0
   fixture — it recorded only `raw_stdout_bytes` (a byte count), never a source list. This script
   therefore evaluates §4.3 using the `context_search` half of the union only, for every entry, and
   marks this explicitly via `graphify_half_status` on every `threshold_4_3_recall` sub-object. No
   Phase 0 graphify source baseline exists to compare against.
5. Re-derives §4.1's `threshold_ms` and §4.2's `threshold_tokens` live from the Phase 0 fixture's
   own 7 `combined.wall_time_ms`/`combined.serialized_tokens_estimate` averages (0.5x each,
   per `measurement_baseline_contract.md` §4.1/§4.2) — never hand-typed independently of the
   fixture.
6. Writes `{"corpus_version", "compared_against_phase0_corpus_version", "recorded_at_utc",
   "entries": [...], "aggregate": {...}}` to
   `tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json`.

Design Decision D4 (Q2/Q5 recall miss): the real `route()` selects `graphify` as the sole primary
provider for `Q2_symbol_lookup` and `Q5_test_impact` (`knowledge_gateway_router.ROUTING_TABLE`),
so `response["context"]` structurally contains zero `context_search`-derived items for those two
entries. This script computes `threshold_4_3_recall` for them by the exact same formula as every
other entry — no special-cased exclusion, no widened routing, no substituted looser definition of
recall. The resulting `pass: False` for those two entries is real, expected, honest output, not a
bug in this script.

Zero mutation of `agent-monitoring/`: verified by running `git status --porcelain -- agent-monitoring/`
before and after this script, mirroring `kgmcp_baseline_runner.py`'s own convention — see
`tests/tools/test_kgmcp_phase1_baseline_comparison.py`'s
`test_zero_mutation_of_real_agent_monitoring_corpus_from_comparison_runner` for the permanent
regression guard.

Never touches: `tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`,
`tools/knowledge_gateway_mcp.py`, `tools/retrieval_events.py`,
`tools/agent-monitoring/kgmcp_baseline_corpus.py`, `tools/agent-monitoring/kgmcp_baseline_runner.py`,
or `tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json` — all are frozen inputs,
read-only.
"""

from __future__ import annotations

import importlib.util
import json
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

from kgmcp_baseline_corpus import CORPUS, CORPUS_VERSION  # noqa: E402

_GATEWAY_MODULE_PATH = _TOOLS_DIR / "knowledge_gateway_mcp.py"

_PHASE0_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "tools" / "fixtures" / "kgmcp_measurement_baseline_corpus_results.json"
)
_OUTPUT_PATH = (
    _REPO_ROOT / "tests" / "tools" / "fixtures" / "kgmcp_phase1_baseline_comparison_results.json"
)

_GRAPHIFY_HALF_NA_NOTE = (
    "No Phase 0 graphify source baseline exists to compare against (the fixture recorded only "
    "raw_stdout_bytes, never a source list) — the graphify half of §4.3's union is reported as "
    "N/A here, not silently treated as empty-and-passing. See Design Decision D3, "
    "staging_artifacts/TCK-20260815-KGMCP-P1-BASELINE-COMPARISON/plan.md."
)


def _load_gateway_module():
    key = "kgmcp_phase1_comparison_gateway"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, _GATEWAY_MODULE_PATH)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]


def _normalize_phase1_source_id(evidence_id: str) -> str:
    """Design Decision D2's normalization rule, verbatim per
    `staging_artifacts/TCK-20260815-KGMCP-P1-BASELINE-COMPARISON/plan.md`.

    Phase 1's evidence/source identity is built by
    `knowledge_gateway_packet_assembly._evidence_id_for_context_search_result()`
    (`tools/knowledge_gateway_packet_assembly.py:100-125`) in one of 3 forms:
    - `doc:{source_path}#{anchor}` when `source_path` starts with `docs/` (L111-119)
    - `ticket:{TCK-id}` when `source_path` matches `tickets/(inprogress|done)/(TCK-...).md` (L121-123)
    - `file:{source_path}` otherwise (L125)
    and `_evidence_id_for_graphify_result()` (L128-134) builds `symbol:{query_text}`.

    Phase 0's raw `doc_id` (`tools/search_mcp.py`, via `_run_context_search`'s
    `[r["doc_id"] for r in results]`) carries none of these prefixes and, for doc-shaped sources,
    no `docs/` path prefix or `.md` extension either (e.g.
    `"simulation/quest_contract#authoritative-status-001"`). This function strips each Phase 1
    prefix and the `docs/`/`.md` decoration so the two shapes become directly comparable.
    """
    if evidence_id.startswith("doc:"):
        path = evidence_id[len("doc:"):]
        if path.startswith("docs/"):
            path = path[len("docs/"):]
        if "#" in path:
            body, anchor = path.split("#", 1)
            if body.endswith(".md"):
                body = body[: -len(".md")]
            return f"{body}#{anchor}"
        if path.endswith(".md"):
            path = path[: -len(".md")]
        return path
    if evidence_id.startswith("ticket:"):
        return evidence_id[len("ticket:"):]
    if evidence_id.startswith("file:"):
        return evidence_id[len("file:"):]
    if evidence_id.startswith("symbol:"):
        return evidence_id[len("symbol:"):]
    return evidence_id


def _path_only(source_id: str) -> str:
    """The part before `#`, per DD2 rule 5: anchor re-slugging is a known, accepted source of
    imprecision (Phase 1's anchor is independently re-derived via `_slugify()` and may not
    byte-for-byte match Phase 0's anchor for the same document), so §4.3 recall is matched on
    normalized `path` only — anchor exact-match is reported as an informational, non-blocking
    sub-field instead, never a source of a false miss driven purely by cosmetic anchor drift.
    """
    return source_id.split("#", 1)[0]


def _compute_threshold_4_3(baseline_sources: list[str], gateway_sources_raw: list[str]) -> dict:
    """§4.3's no-regression-recall threshold, evaluated per query (never only in aggregate) per
    `measurement_baseline_contract.md:214-222`. `baseline_sources` is the Phase 0 fixture entry's
    `context_search.sources_recalled` list, read-only. `gateway_sources_raw` is the real Phase 1
    response's `context[*].source_id` list for this same query, normalized via
    `_normalize_phase1_source_id` before comparison.

    Per Design Decision D3, this evaluates the `context_search` half of §4.3's union only — the
    graphify half is reported as N/A via `graphify_half_status`, never silently treated as
    trivially satisfied.
    """
    gateway_sources = [_normalize_phase1_source_id(s) for s in gateway_sources_raw]
    gateway_paths = {_path_only(s) for s in gateway_sources}

    missing_sources: list[str] = []
    anchor_exact_matches: list[str] = []
    for baseline_source in baseline_sources:
        if _path_only(baseline_source) in gateway_paths:
            if baseline_source in gateway_sources:
                anchor_exact_matches.append(baseline_source)
        else:
            missing_sources.append(baseline_source)

    return {
        "pass": len(missing_sources) == 0,
        "baseline_sources": baseline_sources,
        "gateway_sources": gateway_sources,
        "missing_sources": missing_sources,
        "anchor_exact_matches": anchor_exact_matches,
        "graphify_half_status": "N/A",
        "derivation": (
            "context_search half of §4.3's union only (Design Decision D3 — no Phase 0 graphify "
            "source baseline exists to compare against). baseline_sources = Phase 0 fixture's "
            "context_search.sources_recalled for this entry (read-only). gateway_sources = "
            "response['context'][*]['source_id'] from the real _run_knowledge_context() call, "
            "normalized via _normalize_phase1_source_id() (Design Decision D2: strip "
            "doc:/ticket:/file: prefixes and docs/.md decoration). missing_sources = "
            "baseline_sources whose normalized path is absent from the normalized gateway path "
            "set — comparison is on path only (before '#'), anchor exact-match is informational "
            "only (anchor_exact_matches), never a source of a false miss from cosmetic anchor "
            "re-slugging drift. pass = (missing_sources is empty). " + _GRAPHIFY_HALF_NA_NOTE
        ),
    }


def run_corpus() -> dict:
    mod = _load_gateway_module()
    _kgr = mod._load_router_module()
    _kgpa = mod._load_packet_assembly_module()

    phase0_fixture = json.loads(_PHASE0_FIXTURE_PATH.read_text())
    phase0_entries_by_id = {e["id"]: e for e in phase0_fixture["entries"]}

    threshold_ms = 0.5 * statistics.mean(
        e["combined"]["wall_time_ms"] for e in phase0_fixture["entries"]
    )
    threshold_tokens = 0.5 * statistics.mean(
        e["combined"]["serialized_tokens_estimate"] for e in phase0_fixture["entries"]
    )

    entries = []
    for corpus_entry in CORPUS:
        query_text = corpus_entry["query_text"]

        start = time.perf_counter()
        response = mod._run_knowledge_context(query_text)
        latency_ms = (time.perf_counter() - start) * 1000

        routing_decision = _kgr.route(query_text)
        providers_selected = list(routing_decision.providers_selected)

        gateway_tokens = _kgpa.kgmcp_char_heuristic_v1(json.dumps(response))

        gateway_sources_raw = [
            c["source_id"] for c in response.get("context", []) if "source_id" in c
        ]

        phase0_entry = phase0_entries_by_id[corpus_entry["id"]]
        baseline_sources = phase0_entry["context_search"]["sources_recalled"]
        threshold_4_3_recall = _compute_threshold_4_3(baseline_sources, gateway_sources_raw)

        threshold_4_1_latency = {
            "pass": latency_ms <= threshold_ms,
            "gateway_wall_time_ms": latency_ms,
            "threshold_ms": threshold_ms,
            "derivation": (
                "gateway_wall_time_ms = time.perf_counter() wrapped directly around "
                "_run_knowledge_context(query_text) (Design Decision D1 — no "
                "retrieval_events.py wrapper call site exists on this path). threshold_ms = "
                "0.5 * mean(Phase 0 fixture's combined.wall_time_ms across its 7 entries), "
                "per measurement_baseline_contract.md §4.1, re-derived live from the fixture "
                "on every run of this script, never hand-typed. pass = "
                "(gateway_wall_time_ms <= threshold_ms)."
            ),
        }
        threshold_4_2_tokens = {
            "pass": gateway_tokens <= threshold_tokens,
            "gateway_tokens": gateway_tokens,
            "threshold_tokens": threshold_tokens,
            "derivation": (
                "gateway_tokens = knowledge_gateway_packet_assembly.kgmcp_char_heuristic_v1("
                "json.dumps(response)) — the full real response payload, mirroring Phase 0's "
                "combined.serialized_tokens_estimate measuring the full returned payload. "
                "threshold_tokens = 0.5 * mean(Phase 0 fixture's combined.serialized_tokens_estimate "
                "across its 7 entries), per measurement_baseline_contract.md §4.2, re-derived live "
                "from the fixture on every run of this script, never hand-typed. pass = "
                "(gateway_tokens <= threshold_tokens)."
            ),
        }

        entry = {
            "id": corpus_entry["id"],
            "query_text": query_text,
            "routing_shape": corpus_entry["routing_shape"],
            "providers_selected": providers_selected,
            "provider_failures": response.get("provider_failures", []),
            "gateway_wall_time_ms": latency_ms,
            "gateway_tokens": gateway_tokens,
            "threshold_4_1_latency": threshold_4_1_latency,
            "threshold_4_2_tokens": threshold_4_2_tokens,
            "threshold_4_3_recall": threshold_4_3_recall,
            "derivation": (
                "providers_selected from a real, unwrapped knowledge_gateway_router.route"
                "(query_text) call (read-only, side-effect-free) — ground truth for which "
                "providers were actually consulted for this query, not assumed from the routing "
                "table alone. response measured via a single real "
                "knowledge_gateway_mcp._run_knowledge_context(query_text) call, no mock, no "
                "monkeypatch."
            ),
        }
        entries.append(entry)

    aggregate = _compute_aggregate(entries)

    return {
        "corpus_version": CORPUS_VERSION,
        "compared_against_phase0_corpus_version": phase0_fixture["corpus_version"],
        "recorded_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "entries": entries,
        "aggregate": aggregate,
    }


def _compute_aggregate(entries: list[dict]) -> dict:
    aggregate: dict = {}
    threshold_keys = (
        ("threshold_4_1_latency", "threshold_4_1"),
        ("threshold_4_2_tokens", "threshold_4_2"),
        ("threshold_4_3_recall", "threshold_4_3"),
    )
    for entry_key, aggregate_key in threshold_keys:
        pass_count = sum(1 for e in entries if e[entry_key]["pass"])
        aggregate[aggregate_key] = {"pass_count": pass_count, "of": len(entries)}

    all_thresholds_pass = all(
        entry[entry_key]["pass"] for entry in entries for entry_key, _ in threshold_keys
    )
    aggregate["all_thresholds_pass"] = all_thresholds_pass
    return aggregate


def main() -> None:
    report = run_corpus()
    _OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {_OUTPUT_PATH} ({len(report['entries'])} entries)")
    print(f"aggregate: {json.dumps(report['aggregate'], indent=2, sort_keys=True)}")


if __name__ == "__main__":
    main()

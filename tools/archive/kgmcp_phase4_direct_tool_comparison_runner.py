#!/usr/bin/env python3
r"""One-time direct-tool-comparison runner for the Knowledge Gateway MCP Phase 4 epic
(TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON).

Run once, by hand, during Implementation — never wired into the fast pytest loop, mirroring
`kgmcp_baseline_runner.py`/`kgmcp_phase1_gateway_runner.py`/`kgmcp_phase3_gateway_runner.py`'s own
one-time-script convention.

**Step 1 decision (plan.md, restated here per Step 2's requirement): all 7 corpus entries are run
fresh, both the gateway side and the direct-tool side — no Phase 0-3 fixture data is reused as
either side of this comparison.** `INFRA-351` (Parity Adapter) changed
`ROUTING_TABLE["requirement_completeness_verification"]` from a dead-end to a live
`("context_search", "parity_ledger")` row, making every existing fixture's
`Q3_requirement_completeness` gateway-side number stale beyond dispute. More broadly, general
repo-state drift since Phase 1-3 (many other tickets, cache rows, and doc changes have landed in
the meantime) means treating any of the other 6 entries' historical fixture numbers as "still
current" would be an unverified assumption about the current repo state, not a measured fact.
Mixing 6 stale + 1 fresh numbers in one comparison table (even if labeled) would invite exactly the
"assumed, not measured" failure mode Phase 2/3's own Gate Integrity discipline exists to prevent —
a full fresh run is cheap relative to the honesty cost of a mixed table.

For each of `kgmcp_baseline_corpus.CORPUS`'s 7 entries, this script:

1. Calls the real gateway (`tools/knowledge_gateway_mcp.py::_run_knowledge_context(query=query_text)`,
   loaded in-process via `importlib.util`, timed externally with `time.perf_counter()` — Design
   Decision D1 precedent: no `retrieval_events.py` wrapper call site exists on this path), and
   records the real `providers_selected` via a direct, unwrapped
   `knowledge_gateway_router.route(query_text)` call.
2. Calls the real equivalent direct-tool call(s) an agent would make without the gateway: Context
   Search (`tools/search_mcp.py::_run_search`), Graphify (`subprocess.run(["graphify", "query", ...])`),
   and — for `Q3_requirement_completeness` only — the Parity Ledger
   (`tools/parity_index.py::entry(query_text)`, passing the raw query text as `entry_id`, exactly
   mirroring `tools/knowledge_gateway_router.py::_run_parity_provider()`'s own real usage).
3. Computes a two-part quality/completeness axis, kept structurally separate:
   (a) an objective source-completeness proxy — the Context-Search half reuses Phase 1's
   `_compute_threshold_4_3()` (imported, never reimplemented) with its own `"derivation"` key
   overwritten before persistence (see `_compute_context_search_half()`'s own docstring — the
   function's hardcoded derivation string falsely claims Phase 0 fixture provenance once fed this
   ticket's own freshly-run data), and a new Graphify half that closes Design Decision D3's
   3-phase-old N/A by regex-extracting `src=<path>` occurrences
   (`re.findall(r"src=([^\s\]]+)", raw_stdout)`) from both the direct call's own Graphify stdout and
   a second, independent, real `knowledge_gateway_router.match_symbol_name(query_text)` call
   standing in for the gateway's own internal Graphify invocation for the identical query;
   (b) a disclosed, explicitly-labeled `reviewer_judgment` field (`basis:
   "reviewer_judgment_not_a_computed_metric"`), populated by hand during Implementation by reading
   both sides' retained raw content, never computed programmatically from (a).
4. Retains full raw content on both sides (`raw_results`/`raw_stdout`/full `response` dict) — the
   concrete new instrumentation this ticket adds; every predecessor fixture drops this before
   serialization.
5. Writes `{"corpus_version", "recorded_at_utc", "entries": [...], "by_routing_shape": {...}}` to
   `tests/tools/fixtures/kgmcp_phase4_direct_tool_comparison_results.json`.

**Never touches** (frozen, historical, read-only inputs): `tools/agent-monitoring/kgmcp_baseline_corpus.py`,
`kgmcp_baseline_runner.py`, `kgmcp_phase1_gateway_runner.py`, `kgmcp_phase2_gateway_runner.py`,
`kgmcp_phase3_gateway_runner.py`, `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_router.py`,
`tools/knowledge_gateway_packet_assembly.py`, `tools/knowledge_gateway_cache.py`,
`tools/parity_index.py`, `tools/search_mcp.py`, and every existing
`tests/tools/fixtures/kgmcp_*_results.json` fixture — this ticket's own new fixture is a new file,
never a merge into an existing one.

Zero mutation of `agent-monitoring/`: verified by running `git status --porcelain -- agent-monitoring/`
before and after this script, mirroring every predecessor runner's own convention — see
`tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`'s
`test_zero_mutation_of_real_agent_monitoring_corpus_from_comparison_runner` for the permanent
regression guard. Never calls `emit_retrieval_event`, `wrap_hybrid_retrieval`,
`wrap_retrieval_cache_check`, or `wrap_context_packet_assembly`.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS: relocated here from tools/agent-monitoring/
# alongside its own already-archived test; _MONITORING_TOOLS_DIR now points explicitly at that
# original directory (not this file's own parent) so the still-live kgmcp_baseline_corpus.py
# import below keeps resolving after the move. _ARCHIVE_DIR keeps the sibling
# kgmcp_phase1_gateway_runner import below resolving now that both files live here.
_ARCHIVE_DIR = Path(__file__).resolve().parent
_TOOLS_DIR = _ARCHIVE_DIR.parent
_MONITORING_TOOLS_DIR = _TOOLS_DIR / "agent-monitoring"
_REPO_ROOT = _TOOLS_DIR.parent

if str(_ARCHIVE_DIR) not in sys.path:
    sys.path.insert(0, str(_ARCHIVE_DIR))
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from kgmcp_baseline_corpus import (  # noqa: E402
    CORPUS,
    CORPUS_VERSION,
    kgmcp_char_heuristic_v1_token_count,
)
from kgmcp_phase1_gateway_runner import (  # noqa: E402
    _compute_threshold_4_3,
    _normalize_phase1_source_id,
    _path_only,
)
from search_mcp import _run_search  # noqa: E402

_GATEWAY_MODULE_PATH = _TOOLS_DIR / "knowledge_gateway_mcp.py"
_PARITY_INDEX_MODULE_PATH = _TOOLS_DIR / "parity_index.py"

_OUTPUT_PATH = (
    _REPO_ROOT / "tests" / "tools" / "fixtures" / "kgmcp_phase4_direct_tool_comparison_results.json"
)

_GRAPHIFY_SRC_RE = re.compile(r"src=([^\s\]]+)")

_Q3_ENTRY_ID = "Q3_requirement_completeness"


def _load_gateway_module():
    """This ticket's own `sys.modules` key, distinct from every sibling comparison runner's own
    key (`kgmcp_phase1_comparison_gateway`, `kgmcp_phase3_pilot_acceptance_gateway`, etc.), so this
    runner's calls never interact with a different sibling-loaded module instance."""
    key = "kgmcp_phase4_comparison_gateway"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, _GATEWAY_MODULE_PATH)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]


def _load_parity_index_module():
    key = "kgmcp_phase4_comparison_parity_index"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, _PARITY_INDEX_MODULE_PATH)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]


# ── Direct-tool call functions (Step 3) ───────────────────────────────────────

def _run_direct_context_search(query_text: str) -> dict:
    start = time.perf_counter()
    results = _run_search(query_text, top_k=8)
    latency_ms = (time.perf_counter() - start) * 1000

    if isinstance(results, dict):
        results_count = 0
        sources_recalled: list[str] = []
    else:
        results_count = len(results)
        sources_recalled = [r["doc_id"] for r in results]

    return {
        "latency_ms": latency_ms,
        "tool_call_count": 1,
        "results_count": results_count,
        "sources_recalled": sources_recalled,
        "raw_results": results,
        "derivation": "tools/search_mcp.py::_run_search(query_text, top_k=8), called directly "
        "(not through wrap_hybrid_retrieval/wrap_retrieval_cache_check), timed with "
        "time.perf_counter(), mirroring kgmcp_baseline_runner.py::_run_context_search exactly, "
        "except raw_results is retained in the persisted output (this ticket's own new "
        "instrumentation requirement — every predecessor runner drops this field before "
        "serialization).",
    }


def _run_direct_graphify(query_text: str) -> dict:
    start = time.perf_counter()
    proc = subprocess.run(
        ["graphify", "query", query_text],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    latency_ms = (time.perf_counter() - start) * 1000

    raw_stdout = proc.stdout
    return {
        "latency_ms": latency_ms,
        "tool_call_count": 1,
        "raw_stdout_bytes": len(raw_stdout.encode("utf-8")),
        "raw_stdout": raw_stdout,
        "returncode": proc.returncode,
        "derivation": "subprocess.run(['graphify', 'query', query_text]), CLI-shelled per "
        "docs/engine/contracts/knowledge_gateway_mcp_contract.md Design Decision D1 (no "
        "in-process adapter exists), timed with time.perf_counter(), mirroring "
        "kgmcp_baseline_runner.py::_run_graphify exactly, except raw_stdout is retained in the "
        "persisted output (this ticket's own new instrumentation requirement).",
    }


def _run_direct_parity_ledger(query_text: str) -> dict:
    """Only meaningful for `Q3_requirement_completeness` — the one entry whose routing shape now
    genuinely dispatches to `parity_ledger` (`TCK-20260816-KGMCP-P4-PARITY-ADAPTER`). `query_text`
    is passed directly as `entry_id`, never a resolved/looked-up ID — this exactly mirrors the
    gateway's own real usage, `tools/knowledge_gateway_router.py::_run_parity_provider()`: 'for a
    natural-language query shape-classified into the same requirement_completeness_verification
    row, entry() legitimately returns found: False for the whole sentence treated as an id — real
    provider behavior, not an error.' Using a different, 'fairer' resolved-id lookup on the direct
    side would make the two sides exercise different questions, invalidating the comparison's
    honesty."""
    _pidx = _load_parity_index_module()
    start = time.perf_counter()
    entry_result = _pidx.entry(query_text)
    latency_ms = (time.perf_counter() - start) * 1000
    staleness = None
    if entry_result.get("found") is False:
        staleness = _pidx.check_staleness()
    return {
        "latency_ms": latency_ms,
        "tool_call_count": 1 if staleness is None else 2,
        "entry_result": entry_result,
        "staleness": staleness,
        "derivation": "tools/parity_index.py::entry(query_text) called directly, passing "
        "query_text itself as entry_id (not a resolved/looked-up id) — exactly mirrors the "
        "gateway's own real usage in tools/knowledge_gateway_router.py::_run_parity_provider(). "
        "If found is False, check_staleness() is additionally called, mirroring "
        "_run_parity_provider()'s own found:False branch so the direct side's disclosure shape "
        "matches the gateway side's.",
    }


# ── Gateway-side call function (Step 4) ───────────────────────────────────────

def _run_gateway(query_text: str) -> dict:
    mod = _load_gateway_module()
    _kgr = mod._load_router_module()
    _kgpa = mod._load_packet_assembly_module()

    start = time.perf_counter()
    response = mod._run_knowledge_context(query=query_text)
    wall_time_ms = (time.perf_counter() - start) * 1000

    routing_decision = _kgr.route(query_text)
    providers_selected = list(routing_decision.providers_selected)

    gateway_tokens = _kgpa.kgmcp_char_heuristic_v1(json.dumps(response))

    return {
        "response": response,
        "wall_time_ms": wall_time_ms,
        "providers_selected": providers_selected,
        "provider_failures": response.get("provider_failures", []),
        "gateway_tokens": gateway_tokens,
        "derivation": "tools/knowledge_gateway_mcp.py::_run_knowledge_context(query=query_text), "
        "loaded in-process via importlib.util, timed with time.perf_counter() wrapped directly "
        "around the call (no retrieval_events.py wrapper call site exists on this path). "
        "providers_selected from a real, unwrapped knowledge_gateway_router.route(query_text) "
        "call (read-only, side-effect-free) — ground truth for which providers were actually "
        "consulted, never assumed from ROUTING_TABLE alone. gateway_tokens = "
        "knowledge_gateway_packet_assembly.kgmcp_char_heuristic_v1(json.dumps(response)) over the "
        "full real response payload.",
    }


# ── Quality axis, part (a): objective source-completeness proxy (Step 5) ─────

def _extract_graphify_source_paths(raw_stdout: str) -> list[str]:
    r"""`src=([^\s\]]+)` — verified during Plan against a real `graphify query` run: real stdout
    consists of lines shaped `NODE <name>() [src=<path> loc=L<n> community=<n>]`, and this pattern
    captures the path component correctly for every sampled line. Re-verified for real against
    this ticket's own 7 corpus queries during Implementation (not merely re-trusted from Plan's
    single sample)."""
    return _GRAPHIFY_SRC_RE.findall(raw_stdout)


def _compute_context_search_half(direct_context_search: dict, gateway_result: dict) -> dict:
    """Reuses the imported, unmodified `_compute_threshold_4_3()` for its comparison LOGIC only.

    **Provenance-honesty fix (Architecture Review 1st pass):** `_compute_threshold_4_3()`'s own
    returned dict hardcodes a `"derivation"` string reading "baseline_sources = Phase 0 fixture's
    context_search.sources_recalled for this entry (read-only)" — this is a real, false provenance
    claim once fed this ticket's own freshly-run `direct_context_search` data instead of a Phase 0
    fixture. The comparison logic inside `_compute_threshold_4_3()` stays completely untouched
    (frozen, never modified) — only the misleading provenance string in its RETURNED dict is
    overwritten before persistence, below.
    """
    gateway_context_source_ids = [
        c["source_id"] for c in gateway_result["response"].get("context", []) if "source_id" in c
    ]
    result = _compute_threshold_4_3(
        direct_context_search["sources_recalled"], gateway_context_source_ids
    )
    result["derivation"] = (
        "baseline_sources = THIS TICKET's own freshly-run _run_direct_context_search() call for "
        "this entry (not a Phase 0/1 fixture — see TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON "
        "Step 1's full-fresh-run decision), compared via the unmodified, reused "
        "_compute_threshold_4_3() matching logic."
    )
    return result


def _compute_graphify_half(query_text: str, direct_graphify: dict, gateway_result: dict, _kgr) -> dict:
    """New — closes Design Decision D3's 3-phase-old N/A. Only meaningful for entries whose real,
    per-entry `providers_selected` actually includes `"graphify"` — for entries where Graphify was
    never consulted by the gateway, records `graphify_half_status: "not_routed_this_entry"` instead
    of a fabricated comparison."""
    if "graphify" not in gateway_result["providers_selected"]:
        return {
            "graphify_half_status": "not_routed_this_entry",
            "derivation": "This entry's real, per-entry providers_selected "
            f"({gateway_result['providers_selected']!r}) does not include 'graphify' — no "
            "gateway-side graphify invocation exists to compare against, so no comparison is "
            "fabricated.",
        }

    gateway_graphify_call = _kgr.match_symbol_name(query_text)
    gateway_paths = sorted(set(_extract_graphify_source_paths(gateway_graphify_call["stdout"])))
    direct_paths = sorted(set(_extract_graphify_source_paths(direct_graphify["raw_stdout"])))

    missing = sorted(set(gateway_paths) - set(direct_paths))
    extra = sorted(set(direct_paths) - set(gateway_paths))

    return {
        "graphify_half_status": "measured",
        "gateway_side_graphify_source_paths": gateway_paths,
        "direct_side_graphify_source_paths": direct_paths,
        "graphify_missing_sources": missing,
        "graphify_extra_sources": extra,
        "derivation": "gateway-side graphify invocation captured via a second, independent, real "
        "knowledge_gateway_router.match_symbol_name(query_text) call for the identical query_text "
        "(standing in for the gateway's own internal Graphify invocation during "
        "_run_knowledge_context() — a documented latency/redundancy cost, never a correctness "
        "issue, mirroring call_providers_for_routing_decision()'s own documented double-invocation "
        "precedent). direct-side captured via this ticket's own _run_direct_graphify(). Both "
        "sides' raw stdout run through the same _extract_graphify_source_paths() regex "
        "(re.findall(r'src=([^\\s\\]]+)', raw_stdout)). graphify_missing_sources = paths present "
        "in the gateway-side call but absent from the direct-side call — since both calls are for "
        "the identical query against the same repo state, the expected/typical real result is an "
        "empty list; a non-empty result is itself a genuine, real, disclosed finding, not treated "
        "as a bug in the extractor.",
    }


def _compute_source_completeness(query_text: str, direct: dict, gateway_result: dict, _kgr) -> dict:
    return {
        "context_search_half": _compute_context_search_half(direct["context_search"], gateway_result),
        "graphify_half": _compute_graphify_half(
            query_text, direct["graphify"], gateway_result, _kgr
        ),
    }


# ── Assembly (Step 7) ─────────────────────────────────────────────────────────

def _run_direct(corpus_entry: dict) -> dict:
    query_text = corpus_entry["query_text"]
    direct = {
        "context_search": _run_direct_context_search(query_text),
        "graphify": _run_direct_graphify(query_text),
    }
    if corpus_entry["id"] == _Q3_ENTRY_ID:
        direct["parity_ledger"] = _run_direct_parity_ledger(query_text)
    return direct


def _combined_direct_stats(direct: dict) -> dict:
    wall_time_ms = direct["context_search"]["latency_ms"] + direct["graphify"]["latency_ms"]
    tool_call_count = direct["context_search"]["tool_call_count"] + direct["graphify"]["tool_call_count"]
    serialized_text = (
        json.dumps(direct["context_search"]["raw_results"]) + direct["graphify"]["raw_stdout"]
    )
    if "parity_ledger" in direct:
        wall_time_ms += direct["parity_ledger"]["latency_ms"]
        tool_call_count += direct["parity_ledger"]["tool_call_count"]
        serialized_text += json.dumps(direct["parity_ledger"]["entry_result"])

    return {
        "wall_time_ms": wall_time_ms,
        "tool_call_count": tool_call_count,
        "tokens_estimate": kgmcp_char_heuristic_v1_token_count(serialized_text),
    }


def run_corpus() -> dict:
    mod = _load_gateway_module()
    _kgr = mod._load_router_module()

    entries = []
    for corpus_entry in CORPUS:
        query_text = corpus_entry["query_text"]

        gateway_result = _run_gateway(query_text)
        direct = _run_direct(corpus_entry)
        combined_direct = _combined_direct_stats(direct)
        source_completeness = _compute_source_completeness(query_text, direct, gateway_result, _kgr)

        latency_comparison = {
            "gateway_wall_time_ms": gateway_result["wall_time_ms"],
            "direct_combined_wall_time_ms": combined_direct["wall_time_ms"],
            "gateway_faster": gateway_result["wall_time_ms"] < combined_direct["wall_time_ms"],
        }
        token_comparison = {
            "gateway_tokens": gateway_result["gateway_tokens"],
            "direct_combined_tokens_estimate": combined_direct["tokens_estimate"],
            "gateway_lighter": (
                gateway_result["gateway_tokens"] < combined_direct["tokens_estimate"]
            ),
        }

        entry = {
            "id": corpus_entry["id"],
            "query_text": query_text,
            "routing_shape": corpus_entry["routing_shape"],
            "use_case": corpus_entry["use_case"],
            "gateway": {
                "response": gateway_result["response"],
                "wall_time_ms": gateway_result["wall_time_ms"],
                "providers_selected": gateway_result["providers_selected"],
                "provider_failures": gateway_result["provider_failures"],
                "gateway_tokens": gateway_result["gateway_tokens"],
                "derivation": gateway_result["derivation"],
            },
            "direct": direct,
            "direct_combined": combined_direct,
            "latency_comparison": latency_comparison,
            "token_comparison": token_comparison,
            "quality": {
                "source_completeness": source_completeness,
                # Populated by hand during Implementation (Step 6) — the runner itself cannot
                # compute this, it requires reading content. Left null at script-write time, then
                # this fixture is re-serialized with real reviewer_judgment objects before commit.
                "reviewer_judgment": None,
            },
        }
        entries.append(entry)

    by_routing_shape = {
        e["routing_shape"]: {
            "entry_id": e["id"],
            "gateway_faster": e["latency_comparison"]["gateway_faster"],
            "gateway_lighter": e["token_comparison"]["gateway_lighter"],
            "graphify_half_status": e["quality"]["source_completeness"]["graphify_half"][
                "graphify_half_status"
            ],
            "context_search_half_pass": e["quality"]["source_completeness"]["context_search_half"][
                "pass"
            ],
        }
        for e in entries
    }

    return {
        "corpus_version": CORPUS_VERSION,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "entries": entries,
        "by_routing_shape": by_routing_shape,
    }


def main() -> None:
    report = run_corpus()
    _OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {_OUTPUT_PATH} ({len(report['entries'])} entries)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""One-time corpus-runner script for the Knowledge Gateway MCP Phase 0 measurement baseline
(TCK-20260814-KGMCP-MEASUREMENT-BASELINE).

Run once, by hand, during Implementation — never wired into the fast pytest loop and never wired
into `generate_retro.py`'s recurring weekly cadence. For each of `kgmcp_baseline_corpus.CORPUS`'s
7 entries, this script:

1. Calls `tools/search_mcp.py::_run_search(query_text, top_k=8)` directly, timed with
   `time.perf_counter()` (the exact pattern `tools/retrieval_events.py:175-177` already uses).
   Calls `_run_search` directly, never through `wrap_hybrid_retrieval`/`wrap_retrieval_cache_check`
   — those two are the only functions in this repo that call `emit_retrieval_event()`, and this
   script must never write into `agent-monitoring/events.jsonl`.
2. Shells out to `graphify query "<query_text>"`, timed the same way. Graphify is CLI-shelled
   with no in-process adapter (`docs/engine/contracts/knowledge_gateway_mcp_contract.md` Design
   Decision D1) — a plain subprocess call, no monitoring side effect.
3. Computes `combined.wall_time_ms`, `combined.tool_call_count = 2`, and
   `combined.serialized_tokens_estimate` via `kgmcp_char_heuristic_v1_token_count`.
4. On `Q3_requirement_completeness`, records an honest `notes` disclosure: no callable Parity
   Ledger adapter exists yet (`docs/plans/knowledge-gateway-mcp-proposal.md` §20's own Phase-4
   gating), so this entry's direct-tool baseline is Context Search + Graphify only.
5. Writes `{"corpus_version", "recorded_at_utc", "entries": [...]}` to
   `tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json`.

Zero mutation of `agent-monitoring/`: verified by running
`git status --porcelain -- agent-monitoring/` before and after this script, by hand, before
committing the fixture — see `tests/tools/test_kgmcp_measurement_baseline.py`'s
`test_zero_mutation_of_real_agent_monitoring_corpus` for the permanent regression guard.
"""

from __future__ import annotations

import json
import subprocess
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

from kgmcp_baseline_corpus import (  # noqa: E402
    CORPUS,
    CORPUS_VERSION,
    kgmcp_char_heuristic_v1_token_count,
)
from search_mcp import _run_search  # noqa: E402

_OUTPUT_PATH = _REPO_ROOT / "tests" / "tools" / "fixtures" / (
    "kgmcp_measurement_baseline_corpus_results.json"
)

_PARITY_LEDGER_NOT_YET_CALLABLE_NOTE = (
    "docs/plans/knowledge-gateway-mcp-proposal.md §20's own Phase-4 gating states 'Parity Ledger "
    "is not required until Phase 4' — no callable Parity Ledger adapter exists yet at Phase 0, so "
    "this entry's direct-tool baseline covers Context Search + Graphify only. This is an honest "
    "substitution, not a silent omission."
)


def _run_context_search(query_text: str) -> dict:
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
        "time.perf_counter() mirroring tools/retrieval_events.py:175-177's exact pattern.",
    }


def _run_graphify(query_text: str) -> dict:
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
        "in-process adapter exists), timed with time.perf_counter() mirroring "
        "tools/retrieval_events.py's exact pattern.",
    }


def run_corpus() -> dict:
    entries = []
    for corpus_entry in CORPUS:
        query_text = corpus_entry["query_text"]
        context_search = _run_context_search(query_text)
        graphify = _run_graphify(query_text)

        combined_serialized_text = (
            json.dumps(context_search["raw_results"]) + graphify["raw_stdout"]
        )
        combined = {
            "wall_time_ms": context_search["latency_ms"] + graphify["latency_ms"],
            "tool_call_count": context_search["tool_call_count"] + graphify["tool_call_count"],
            "serialized_tokens_estimate": kgmcp_char_heuristic_v1_token_count(
                combined_serialized_text
            ),
            "derivation": "wall_time_ms = context_search.latency_ms + graphify.latency_ms; "
            "tool_call_count = 2 (one context_search call, one graphify call); "
            "serialized_tokens_estimate = kgmcp_char_heuristic_v1_token_count(json.dumps("
            "context_search results) + graphify raw stdout).",
        }

        entry = {
            "id": corpus_entry["id"],
            "query_text": query_text,
            "routing_shape": corpus_entry["routing_shape"],
            "use_case": corpus_entry["use_case"],
            "context_search": {
                "latency_ms": context_search["latency_ms"],
                "tool_call_count": context_search["tool_call_count"],
                "results_count": context_search["results_count"],
                "sources_recalled": context_search["sources_recalled"],
                "derivation": context_search["derivation"],
            },
            "graphify": {
                "latency_ms": graphify["latency_ms"],
                "tool_call_count": graphify["tool_call_count"],
                "raw_stdout_bytes": graphify["raw_stdout_bytes"],
                "derivation": graphify["derivation"],
            },
            "combined": combined,
        }
        if corpus_entry["id"] == "Q3_requirement_completeness":
            entry["notes"] = _PARITY_LEDGER_NOT_YET_CALLABLE_NOTE

        entries.append(entry)

    return {
        "corpus_version": CORPUS_VERSION,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "entries": entries,
    }


def main() -> None:
    report = run_corpus()
    _OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {_OUTPUT_PATH} ({len(report['entries'])} entries)")


if __name__ == "__main__":
    main()

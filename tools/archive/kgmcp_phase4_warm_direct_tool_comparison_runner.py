#!/usr/bin/env python3
r"""One-time warm-gateway-vs-direct-tool comparison runner
(TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON).

Run once, by hand, during Implementation — never wired into the fast pytest loop, mirroring every
prior KGMCP comparison runner's own one-time-script convention.

**What this adds over `kgmcp_phase4_direct_tool_comparison_runner.py`:** that runner's own
`_run_gateway()` calls `_run_knowledge_context()` exactly once per entry, against whatever cache
state happened to exist at the time (its own docstring's Step 1 decision only concerns fixture
reuse, not cache state) — in practice a cold/near-cold run. It never demonstrated whether a
genuinely warm, cache-hit gateway changes the verdict against direct tool calls. This script does
exactly that comparison, reusing every other piece of Phase 4's frozen methodology unmodified
(direct-tool call functions, quality-axis computation, corpus, combined-direct-stats) — imported,
never reimplemented — and only replacing the gateway-side call with a real cold-priming pass
(discarded) followed by a real warm-measured pass, with genuine-hit status verified via
`kgmcp_phase3_gateway_runner.py`'s own `_install_timing_spy()` technique (imported, never
reimplemented): `assemble_packet`'s call count on the measured call must be 0 (no fresh assembly
ran — a structural proof of a genuine hit, not an assumption from `response["cache"]` alone).

Both cache tables (`retrieval_provider_result_cache_rows`, `retrieval_context_packet_cache_rows`)
are cleared once before the run (gitignored, untracked local dev-machine state — same disclosed
hygiene precedent as the recalibration hotfix and this epic's own budget-json-overhead-accounting
ticket), so every entry's priming call is a genuine cold write, not an accidental leftover hit
from earlier session activity.

Writes a NEW fixture (`tests/tools/fixtures/kgmcp_phase4_warm_direct_tool_comparison_results.json`)
— never overwrites or merges into the historical cold-cache fixture.

**Never touches** (frozen, historical, read-only inputs): everything
`kgmcp_phase4_direct_tool_comparison_runner.py` itself declares frozen, plus that runner module
itself and `kgmcp_phase3_gateway_runner.py` (both imported from, never edited).
"""
from __future__ import annotations

import importlib.util
import json
import sqlite3
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
from kgmcp_phase3_gateway_runner import _install_timing_spy  # noqa: E402
from kgmcp_phase4_direct_tool_comparison_runner import (  # noqa: E402
    _combined_direct_stats,
    _compute_source_completeness,
    _run_direct,
)

_CACHE_DB_PATH = _REPO_ROOT / "knowledge-index" / "retrieval_cache.db"
_OUTPUT_PATH = (
    _REPO_ROOT / "tests" / "tools" / "fixtures"
    / "kgmcp_phase4_warm_direct_tool_comparison_results.json"
)

_GATEWAY_MODULE_PATH = _TOOLS_DIR / "knowledge_gateway_mcp.py"


def _load_gateway_module():
    """This script's own `sys.modules` key, distinct from every sibling comparison runner's own
    key, so this runner's calls never interact with a different sibling-loaded module instance."""
    key = "kgmcp_phase4_warm_comparison_gateway"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, _GATEWAY_MODULE_PATH)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]


def _clear_both_cache_tables() -> dict:
    """Gitignored, untracked local dev-machine state — same disclosed environment-hygiene
    precedent as TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION and this epic's own
    TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING. Never a tracked-file edit."""
    con = sqlite3.connect(str(_CACHE_DB_PATH))
    try:
        l1 = con.execute("DELETE FROM retrieval_provider_result_cache_rows")
        l2 = con.execute("DELETE FROM retrieval_context_packet_cache_rows")
        con.commit()
        return {"l1_rows_deleted": l1.rowcount, "l2_rows_deleted": l2.rowcount}
    finally:
        con.close()


def _run_gateway_warm(query_text: str, mod, _kgr, _kgpa) -> dict:
    """Cold priming call (discarded — writes both cache rows for this identity), then a real,
    timed, spied warm call. `warm_verified` is True only if the spy structurally proves zero
    `assemble_packet` invocations on the measured call — never assumed from `response["cache"]`
    alone (same discipline as `kgmcp_phase3_gateway_runner.py`'s own AC1 measurement)."""
    mod._run_knowledge_context(query=query_text)  # priming, discarded

    restore_asm, asm_calls = _install_timing_spy(_kgpa, "assemble_packet")
    try:
        start = time.perf_counter()
        response = mod._run_knowledge_context(query=query_text)
        wall_time_ms = (time.perf_counter() - start) * 1000
    finally:
        restore_asm()

    warm_verified = len(asm_calls) == 0

    routing_decision = _kgr.route(query_text)
    providers_selected = list(routing_decision.providers_selected)

    gateway_tokens = _kgpa.kgmcp_char_heuristic_v1(json.dumps(response))

    return {
        "response": response,
        "wall_time_ms": wall_time_ms,
        "providers_selected": providers_selected,
        "provider_failures": response.get("provider_failures", []),
        "gateway_tokens": gateway_tokens,
        "cache_status_reported": response.get("cache"),
        "warm_verified": warm_verified,
        "assemble_packet_call_count_on_measured_call": len(asm_calls),
        "derivation": "Cold priming call to tools/knowledge_gateway_mcp.py::"
        "_run_knowledge_context(query=query_text) (discarded), then a second, real, timed call "
        "to the same function with knowledge_gateway_packet_assembly.assemble_packet wrapped in "
        "a pass-through timing spy (kgmcp_phase3_gateway_runner.py::_install_timing_spy(), "
        "imported not reimplemented) for the duration of the measured call only. warm_verified "
        "= (assemble_packet call count on the measured call == 0) -- a structural proof of a "
        "genuine cache hit, not an assumption from response['cache'] alone. gateway_tokens = "
        "knowledge_gateway_packet_assembly.kgmcp_char_heuristic_v1(json.dumps(response)) over "
        "the full real warm response payload.",
    }


def run_corpus() -> dict:
    mod = _load_gateway_module()
    _kgr = mod._load_router_module()
    _kgpa = mod._load_packet_assembly_module()

    cache_clear_report = _clear_both_cache_tables()

    entries = []
    for corpus_entry in CORPUS:
        query_text = corpus_entry["query_text"]

        gateway_result = _run_gateway_warm(query_text, mod, _kgr, _kgpa)
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
                "cache_status_reported": gateway_result["cache_status_reported"],
                "warm_verified": gateway_result["warm_verified"],
                "assemble_packet_call_count_on_measured_call": gateway_result[
                    "assemble_packet_call_count_on_measured_call"
                ],
                "derivation": gateway_result["derivation"],
            },
            "direct": direct,
            "direct_combined": combined_direct,
            "latency_comparison": latency_comparison,
            "token_comparison": token_comparison,
            "quality": {
                "source_completeness": source_completeness,
                # Populated by hand during Implementation, same as
                # kgmcp_phase4_direct_tool_comparison_runner.py's own convention — the runner
                # itself cannot compute this, it requires reading content.
                "reviewer_judgment": None,
            },
        }
        entries.append(entry)

    by_routing_shape = {
        e["routing_shape"]: {
            "entry_id": e["id"],
            "gateway_faster": e["latency_comparison"]["gateway_faster"],
            "gateway_lighter": e["token_comparison"]["gateway_lighter"],
            "warm_verified": e["gateway"]["warm_verified"],
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
        "cache_clear_report": cache_clear_report,
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

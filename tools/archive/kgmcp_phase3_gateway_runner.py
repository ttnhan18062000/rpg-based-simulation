#!/usr/bin/env python3
"""One-time pilot-acceptance-measurement runner for the Knowledge Gateway MCP Phase 3 epic
(TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT).

Measurement-only: never edits `tools/knowledge_gateway_mcp.py`,
`tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`, or
`tools/knowledge_gateway_cache.py`. Imports pure helpers from
`kgmcp_phase1_gateway_runner.py` (never reimplemented); does NOT import anything callable from
`kgmcp_phase2_gateway_runner.py` — that module's own `_run_single_entry` is entry-point-shaped
around Phase 2's fixed 2-call (cold, warm) design, not a pure, reusable helper (Investigate Q1).
Only `kgmcp_phase2_gateway_runner.py::_read_hit_count`'s *shape* (direct, read-only SQL against
the live cache DB) is mirrored below, retargeted at Level 2's own table/primary key, since this
ticket's own DB interaction is against a different table than Phase 2's.

**Why a 4-call-per-entry design, not Phase 1/2's 2-call design (plan.md's "Resolution of the
Level-1-Warm-Isolation Problem"):** the live gateway's Level 2 cache-check runs unconditionally
*before* Level 1's on every `_run_knowledge_context()` call
(`tools/knowledge_gateway_mcp.py:228-264`) — a bare repeated call is always a Level-2 hit, never a
Level-1 hit, once Level 2 has a row for that identity. To produce a genuine, real, same-run
Level-1-warm measurement (the second half of AC4's "clearly stated baseline"), this runner issues,
per corpus entry:

1. **Call 1 (cold, default budget).** Writes both the Level 1 and Level 2 rows for this identity.
2. **Call 2 (Level-2-warm, default budget).** Same request — the real, central AC1/AC4 Level-2-hit
   measurement, verified via dual-signal (an `assemble_packet` call-count spy AND a direct SQL
   `hit_count` delta read against `retrieval_context_packet_cache_rows`), never
   `response["cache"]` alone.
3. **A disclosed, narrowly-scoped SQL delete** —
   `DELETE FROM retrieval_context_packet_cache_rows WHERE packet_id = ?`, bound to this run's own,
   independently recomputed `packet_id` (never read back from a row) — removes only the one row
   this run's own call 1 just wrote for this exact identity. `cursor.rowcount == 1` is asserted
   before proceeding. This is the one place this ticket's tooling writes to a shared resource;
   Level 1's own table (`retrieval_provider_result_cache_rows`) is never touched by this delete.
4. **Call 3 (Level-1-warm, default budget).** With the Level 2 row now gone, the same call
   structurally falls through to Level 1's still-populated row — the freshly, honestly
   (re)measured Level-1-warm number `investigation.md` Q2 found does not exist anywhere else in
   this repository as committed data.
5. **Call 4 (constrained budget, distinct identity).** `budget_tokens=1000` — a fresh identity
   (budget is part of Level 2's own identity hash), never interacting with or contaminating calls
   1-3's isolation-delete sequence. Feeds AC2's budget-tolerance measurement.

For one representative corpus entry (the first whose cold response carries a real cited `path`),
two additional real, live calls are inserted between calls 2 and 3 to re-verify AC6's
Level-2-specific stale-rejection and unrelated-change-non-invalidation criteria through the real
gateway (not a synthetic row dict) — see `_verify_ac6_invalidation()`. Branch-partition is verified
via a direct, disclosed call to the real `revalidate_context_packet_row()` with a synthetic
incompatible `current_branch` argument (the 7-entry corpus cannot organically produce a second,
real, incompatible git branch — investigation.md Q3). Uncommitted-change invalidation shares the
stale-rejection sub-measurement's own evidence verbatim (`changed_paths` is the gateway's only
representation of "uncommitted changes"), never double-counted as a second independent
verification.

**Per-stage timing — 3 real segments, not the proposal's 5-name wording (disclosed
instrumentation-granularity limit, investigation.md Current Behavior / Q3):**
`lookup_and_validation_ms` (whichever of `perform_context_packet_cache_lookup`/
`perform_cache_lookup` actually runs, timed via a pass-through spy — "validation" is not a
separate call boundary from "lookup" in the current code), `fallback_and_assembly_ms`
(`assemble_packet`, `None` on any genuine hit), and `end_to_end_ms`
(`time.perf_counter()` wrapped directly around the whole `_run_knowledge_context()` call). No
`time.perf_counter()` call is ever added inside the gateway modules themselves — all timing is
external, via spies installed and restored entirely within this process.

Never touches: `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_router.py`,
`tools/knowledge_gateway_packet_assembly.py`, `tools/knowledge_gateway_cache.py`,
`tools/agent-monitoring/kgmcp_phase1_gateway_runner.py`,
`tools/agent-monitoring/kgmcp_phase2_gateway_runner.py`,
`tools/agent-monitoring/kgmcp_baseline_corpus.py`, or any existing fixture/results doc — all are
frozen, historical, read-only inputs.

Run once, by hand, during Implementation — never wired into pytest's fast loop, mirroring both
predecessor runners' own documented one-time-script convention.
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
# Read-only, consumed only for its recorded per-entry missing_sources counts (Step 7) — NOT as
# this ticket's Level-1-warm latency/token baseline, since that fixture's own data is the
# pre-hotfix 0/7 all-size-cap-rejected state (investigation.md Prior Work).
_PHASE2_FIXTURE_PATH = (
    _REPO_ROOT
    / "tests"
    / "tools"
    / "fixtures"
    / "kgmcp_phase2_baseline_recomparison_results.json"
)
_OUTPUT_PATH = (
    _REPO_ROOT
    / "tests"
    / "tools"
    / "fixtures"
    / "kgmcp_phase3_pilot_acceptance_measurement_results.json"
)

_DEFAULT_BUDGET_TOKENS_FALLBACK = 4000  # tools.knowledge_gateway_mcp.DEFAULT_BUDGET_TOKENS, read live below.
_CONSTRAINED_BUDGET_TOKENS = 1000  # AC2 — well below DEFAULT_BUDGET_TOKENS (4000).
_BUDGET_TOLERANCE_MULTIPLIER = 1.2  # documented ±20% tolerance, redaction_retention_policy.md §8.

_UNRELATED_PATH_FOR_AC6 = (
    "docs/this_path_is_intentionally_unrelated_to_any_corpus_entrys_cited_evidence_"
    "for_ac6_testing.md"
)

_GRAPHIFY_HALF_NA_NOTE = (
    "No Phase 0 graphify source baseline exists to compare against (inherited from Phase 1's own "
    "Design Decision D3) — the graphify half of §4.3's union is reported as N/A here, not "
    "silently treated as empty-and-passing."
)


def _load_gateway_module():
    """This ticket's own `sys.modules` key, distinct from Phase 1's own
    `"kgmcp_phase1_comparison_gateway"` and Phase 2's own `"kgmcp_phase2_recomparison_gateway"`
    (plan.md Step 1), so this runner's spies never interact with a different sibling-loaded
    module instance."""
    key = "kgmcp_phase3_pilot_acceptance_gateway"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, _GATEWAY_MODULE_PATH)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]


def _load_manifest_built_at() -> str | None:
    if not _MANIFEST_PATH.exists():
        return None
    return json.loads(_MANIFEST_PATH.read_text()).get("built_at")


def _read_hit_count_level2(_kgc, packet_id: str) -> int:
    """Direct, read-only SQL read of `retrieval_context_packet_cache_rows.hit_count` — mirrors
    `kgmcp_phase2_gateway_runner.py::_read_hit_count()`'s *shape*, retargeted at Level 2's own
    table/primary key (not imported — that function reads Level 1's differently-keyed table)."""
    db_path = Path(_kgc.rc.CACHE_DB_PATH)
    if not db_path.exists():
        return 0
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT hit_count FROM retrieval_context_packet_cache_rows WHERE packet_id = ?",
            (packet_id,),
        ).fetchone()
    finally:
        conn.close()
    return row[0] if row is not None else 0


def _read_hit_count_level1(_kgc, query_hash: str, repo_branch_scope: str) -> int:
    """Level 1 sibling of `_read_hit_count_level2()` — same shape as
    `kgmcp_phase2_gateway_runner.py::_read_hit_count()`, against Level 1's own table."""
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


def _read_cache_db_row_counts(_kgc) -> dict:
    """Step 9 — pre-run cache-DB state disclosure (investigation.md Risk: 'the DB's state going
    into this run is not neutral'). Read-only; never pre-clears or seeds the DB."""
    db_path = Path(_kgc.rc.CACHE_DB_PATH)
    if not db_path.exists():
        return {
            "db_exists": False,
            "retrieval_context_packet_cache_rows": 0,
            "retrieval_provider_result_cache_rows": 0,
        }
    conn = sqlite3.connect(str(db_path))
    try:
        counts = {"db_exists": True}
        for table in ("retrieval_context_packet_cache_rows", "retrieval_provider_result_cache_rows"):
            try:
                counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            except sqlite3.OperationalError:
                counts[table] = 0
    finally:
        conn.close()
    return counts


def _fetch_l2_row_dict(_kgc, packet_id: str) -> dict | None:
    """Direct, read-only SQL read of a single `retrieval_context_packet_cache_rows` row, by its
    real primary key — used only for AC6's branch-partition sub-measurement's direct call to the
    real `revalidate_context_packet_row()`."""
    db_path = Path(_kgc.rc.CACHE_DB_PATH)
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute(
            "SELECT * FROM retrieval_context_packet_cache_rows WHERE packet_id = ?", (packet_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [d[0] for d in cursor.description]
    finally:
        conn.close()
    return dict(zip(columns, row))


def _install_timing_spy(obj, attr_name: str):
    """Plain-Python pass-through spy (direct attribute reassignment, never any mocking library),
    extending `kgmcp_phase2_gateway_runner.py:169-188`'s established technique so each call also
    records its own elapsed `time.perf_counter()` span. Returns `(restore_fn, elapsed_ms_list)`.
    """
    orig = getattr(obj, attr_name)
    elapsed_ms: list[float] = []

    def _spy(*args, **kwargs):
        start = time.perf_counter()
        result = orig(*args, **kwargs)
        elapsed_ms.append((time.perf_counter() - start) * 1000)
        return result

    setattr(obj, attr_name, _spy)

    def _restore() -> None:
        setattr(obj, attr_name, orig)

    return _restore, elapsed_ms


def _timed_call(mod, _kgc, _kgpa, query_text: str, **request_kwargs) -> dict:
    """Times one real `_run_knowledge_context()` call, wrapping `_kgc.perform_context_packet_cache_lookup`
    (Level 2), `_kgc.perform_cache_lookup` (Level 1), and `_kgpa.assemble_packet` with pass-through
    timing spies for the duration of this one call only, restored in a `finally` block (never a
    duplicate, timing-only direct call to any of the three — that would double-count Level 2's own
    `record_context_packet_cache_hit()` side effect, plan.md Step 3). `lookup_and_validation_ms` is
    whichever of the two lookup spies actually fired (at most one fires per call, structurally);
    `fallback_and_assembly_ms` is `None` on any genuine hit call, since `assemble_packet` never
    runs on a hit path.
    """
    restore_l2, l2_calls = _install_timing_spy(_kgc, "perform_context_packet_cache_lookup")
    restore_l1, l1_calls = _install_timing_spy(_kgc, "perform_cache_lookup")
    restore_asm, asm_calls = _install_timing_spy(_kgpa, "assemble_packet")
    try:
        start = time.perf_counter()
        response = mod._run_knowledge_context(query_text, **request_kwargs)
        end_to_end_ms = (time.perf_counter() - start) * 1000
    finally:
        restore_l2()
        restore_l1()
        restore_asm()

    lookup_and_validation_ms = sum(l2_calls) + sum(l1_calls)
    fallback_and_assembly_ms = sum(asm_calls) if asm_calls else None

    return {
        "response": response,
        "end_to_end_ms": end_to_end_ms,
        "lookup_and_validation_ms": lookup_and_validation_ms,
        "fallback_and_assembly_ms": fallback_and_assembly_ms,
        "l2_lookup_call_count": len(l2_calls),
        "l1_lookup_call_count": len(l1_calls),
        "provider_round_trip_call_count": len(asm_calls),
    }


def _verify_ac6_invalidation(mod, _kgc, identity: dict, request: dict) -> dict | None:
    """AC6 — stale-rejection and unrelated-change-non-invalidation, re-verified through the real,
    live gateway (not a synthetic row dict) for one real corpus entry, plus a direct,
    disclosed branch-partition call. `changed_paths` is not part of Level 2's own identity hash
    (plan.md Step 2 item 5's citation of `compute_context_packet_lookup_identity`'s 6-field shape),
    so both calls below reuse the exact same `identity`/`packet_id` this entry's calls 1-2 already
    established — this must run BEFORE the isolation delete (Step 2/3) so the Level 2 row these
    calls revalidate against still exists.

    Returns `None` if the entry's cold response carries no real cited `path` (a genuine, disclosed
    corpus-coverage limitation for this one entry — the caller tries the next entry instead).
    """
    l2_row_before = _fetch_l2_row_dict(_kgc, identity["packet_id"])
    if l2_row_before is None:
        return None
    cited_paths = [c["path"] for c in json.loads(l2_row_before["context_items"]) if c.get("path")]
    if not cited_paths:
        return None

    query_text = request["query"]
    real_cited_path = cited_paths[0]

    # Sub-measurement 1 (also covers sub-measurement 4, uncommitted-change invalidation — see
    # module docstring and plan.md Step 8 item 4: changed_paths IS the gateway's only
    # representation of "uncommitted changes", so this single real call jointly demonstrates both).
    start = time.perf_counter()
    response_stale = mod._run_knowledge_context(query_text, changed_paths=[real_cited_path])
    stale_call_ms = (time.perf_counter() - start) * 1000
    stale_rejection = {
        "changed_path_used": real_cited_path,
        "cache_status": response_stale.get("cache"),
        "genuinely_refreshed": response_stale.get("cache") != "HIT_L2",
        "call_ms": stale_call_ms,
    }

    # Sub-measurement 2 — unrelated changed path must NOT invalidate the (now freshly rewritten,
    # by sub-measurement 1's own miss-path write) cached packet.
    assert _UNRELATED_PATH_FOR_AC6 not in cited_paths
    start = time.perf_counter()
    response_unrelated = mod._run_knowledge_context(
        query_text, changed_paths=[_UNRELATED_PATH_FOR_AC6]
    )
    unrelated_call_ms = (time.perf_counter() - start) * 1000
    unrelated_change_non_invalidation = {
        "changed_path_used": _UNRELATED_PATH_FOR_AC6,
        "cache_status": response_unrelated.get("cache"),
        "genuine_hit_preserved": response_unrelated.get("cache") in ("HIT_L2", "HIT"),
        "call_ms": unrelated_call_ms,
    }

    # Sub-measurement 3 — branch partition. Direct, disclosed call to the real
    # revalidate_context_packet_row() against a real, just-rewritten row, with a synthetic
    # incompatible current_branch argument — not a full round trip with an actual second git
    # branch (investigation.md Q3: the 7-entry corpus cannot organically produce one).
    l2_row_now = _fetch_l2_row_dict(_kgc, identity["packet_id"])
    branch_partition = None
    if l2_row_now is not None:
        provider_ids = list(json.loads(l2_row_now["provider_generations"]).keys())
        current_generations = _kgc._current_provider_generations_for(provider_ids)
        capability_descriptor = _kgc._capability_descriptor_for(provider_ids)
        still_valid = _kgc.revalidate_context_packet_row(
            l2_row_now,
            capability_descriptor=capability_descriptor,
            current_provider_generations=current_generations,
            current_repository_id=identity["repository_id"],
            current_branch="a-different-synthetic-branch-for-ac6-testing",
            changed_paths=[],
        )
        branch_partition = {
            "synthetic_incompatible_branch": "a-different-synthetic-branch-for-ac6-testing",
            "revalidate_context_packet_row_result": still_valid,
            "pass": still_valid is False,
            "technique_disclosure": (
                "Direct call to the real revalidate_context_packet_row() against a real, "
                "just-rewritten row, with a synthetic incompatible current_branch argument — not "
                "a full _run_knowledge_context() round trip with an actual second git branch, "
                "since the 7-entry corpus cannot organically produce a second incompatible branch "
                "(investigation.md Q3)."
            ),
        }

    return {
        "stale_rejection": stale_rejection,
        "unrelated_change_non_invalidation": unrelated_change_non_invalidation,
        "branch_partition": branch_partition,
        "uncommitted_change_invalidation_note": (
            "changed_paths is the gateway's only representation of 'uncommitted changes' (no "
            "separate git-diff-based mechanism exists) — this criterion shares "
            "stale_rejection's evidence verbatim, never double-counted as a second, independent "
            "real-world verification (plan.md Step 8 item 4)."
        ),
    }


def _compute_budget_compliance(_kgpa, response: dict, budget_tokens_requested: int) -> dict:
    """AC2 — measures the FULL response payload, never `response["budget_returned"]` (which,
    per `assemble_within_budget()`, `tools/knowledge_gateway_packet_assembly.py:584-611`, is a
    `statements[]`-only running total, `<= budget_requested` by construction — using it here would
    make this criterion trivially pass regardless of real gateway behavior)."""
    full_payload_tokens = _kgpa.kgmcp_char_heuristic_v1(json.dumps(response, sort_keys=True))
    tolerance_threshold_tokens = budget_tokens_requested * _BUDGET_TOLERANCE_MULTIPLIER
    return {
        "budget_tokens_requested": budget_tokens_requested,
        "full_payload_tokens": full_payload_tokens,
        "tolerance_multiplier": _BUDGET_TOLERANCE_MULTIPLIER,
        "tolerance_threshold_tokens": tolerance_threshold_tokens,
        "pass": full_payload_tokens <= tolerance_threshold_tokens,
        "derivation": (
            "full_payload_tokens = knowledge_gateway_packet_assembly.kgmcp_char_heuristic_v1("
            "json.dumps(response)) over the FULL response payload — never "
            "response['budget_returned'], which is a statements[]-only running total, "
            "<= budget_requested by construction (assemble_within_budget(), "
            "tools/knowledge_gateway_packet_assembly.py:584-611), and would trivially 'pass' "
            "regardless of real gateway behavior. tolerance_threshold_tokens = "
            "budget_tokens_requested * 1.2, the documented ±20% tolerance ratified in "
            "redaction_retention_policy.md §8 as 'the standard against which a future "
            "implementation validates the Phase 3 pilot's returned content respects the "
            "requested budget within a documented tolerance acceptance bar' — cited verbatim, "
            "not a new tolerance invented here. pass = (full_payload_tokens <= "
            "tolerance_threshold_tokens). context[]/evidence[]/conflicts[] are unbudgeted by "
            "construction, so a real FAIL here is a plausible, legitimate outcome."
        ),
    }


def _compute_conflicts_report(response_cold: dict) -> dict:
    """AC3 — real measurement, not a documentation claim. This field must exist and be populated
    identically whether the true count is 0 or nonzero (never conditionally omitted on a 0
    result)."""
    conflicts = response_cold.get("conflicts", [])
    total = len(conflicts)
    return {
        "conflicts_observed": total,
        "conflicts_observed_in_corpus": total > 0,
        "limitation_note": (
            "build_conflicts() is structural (explicit supersession/deprecation-marker detection "
            "in source docs, tools/knowledge_gateway_packet_assembly.py:558-579), not automatic "
            "cross-provider factual-value comparison. The frozen 7-entry corpus was designed "
            "around §8 routing-shape coverage, not conflict-shape coverage, so 0 real conflicts "
            "across all 7 entries is a plausible, honest outcome. If total is 0, this criterion's "
            "visibility mechanism itself remains separately unit-tested (build_conflicts()'s own "
            "test suite), but this real corpus does not naturally exercise a real conflict "
            "occurrence — this is disclosed as a genuine corpus-coverage limitation, never "
            "silently marked satisfied."
            if total == 0
            else "At least one real, structural conflict was observed by this run's own live "
            "corpus call — see per_entry counts."
        ),
    }


def _compute_recall_report(
    corpus_entry: dict, response_cold: dict, phase0_entry: dict, phase1_entry: dict,
    phase2_entry: dict, cold_call_anomaly: str | None,
) -> dict:
    """AC5 — reuses the imported, unmodified `_compute_threshold_4_3` (never reimplemented),
    compared against BOTH predecessors' own recorded counts.

    Honesty disclosure discovered during the real corpus run: when `cold_call_anomaly` is set
    (this entry's "cold" call 1 was actually a cache hit — leftover state from an earlier
    invocation of this same runner against the shared, gitignored, non-resettable
    `knowledge-index/retrieval_cache.db`), `response_cold` is a *cached, already-redacted*
    payload, not a fresh, unredacted provider response. `tools/knowledge_gateway_redaction.py`'s
    `LOCAL_PATH_PLACEHOLDER` (`"<local-path>"`) replaces real local paths before any cache write —
    so a cache-hit-contaminated `response_cold`'s `context[*].source_id` values are genuinely
    obscured, producing an apparent (but not real, in the sense of reflecting the live provider's
    current content) recall regression for that entry only. This is reported explicitly via
    `computed_from_contaminated_cache_hit`, never silently absorbed into an unqualified
    `recall_regression_flag`.
    """
    baseline_sources = phase0_entry["context_search"]["sources_recalled"]
    gateway_sources_raw = [
        c["source_id"] for c in response_cold.get("context", []) if "source_id" in c
    ]
    recall = _compute_threshold_4_3(baseline_sources, gateway_sources_raw)
    recall["derivation"] += (
        " Computed from the cold (call 1) response only, per Phase 2's own established precedent "
        "(a genuine hit's content is identical to the cold response that produced it)."
    )

    phase1_missing = len(phase1_entry["threshold_4_3_recall"]["missing_sources"])
    phase2_missing = len(phase2_entry["threshold_4_3_recall_cold"]["missing_sources"])
    this_missing = len(recall["missing_sources"])

    recall_regression_flag = (this_missing > phase1_missing) or (this_missing > phase2_missing)
    computed_from_contaminated_cache_hit = cold_call_anomaly is not None

    recall["phase1_recall_missing_count"] = phase1_missing
    recall["phase2_recall_missing_count"] = phase2_missing
    recall["recall_missing_count_comparison"] = (
        f"Phase 3 (this run): {this_missing} missing. "
        f"Phase 1 (recorded): {phase1_missing} missing. "
        f"Phase 2 (recorded, cold): {phase2_missing} missing."
    )
    recall["recall_regression_flag"] = recall_regression_flag
    recall["computed_from_contaminated_cache_hit"] = computed_from_contaminated_cache_hit
    recall["contamination_note"] = (
        "This entry's 'cold' call was actually a cache hit (leftover state from an earlier "
        "invocation of this runner against the shared, non-resettable cache DB), so "
        "response_cold is a cached, already-redacted payload — LOCAL_PATH_PLACEHOLDER "
        "('<local-path>') has replaced real local paths, genuinely degrading this entry's "
        "recall count without reflecting the live provider's actual current content. "
        "recall_regression_flag is real and honestly computed, but this caveat qualifies its "
        "interpretation for this entry specifically."
        if computed_from_contaminated_cache_hit
        else None
    )
    return recall


def _compute_ac4_result(
    l2_warm_end_to_end_ms: list[float], l2_warm_tokens: list[int],
    baseline_end_to_end_ms: list[float], baseline_tokens: list[int], baseline_name: str,
) -> dict:
    """AC4 — median-based (§21's closing bullet says 'median' explicitly, unlike §4.1/§4.2's own
    mean-based formulas), structurally capable of returning `pass: False` — this function must
    never be structurally incapable of reporting FAIL (Gate Integrity guard)."""
    l2_median_latency = statistics.median(l2_warm_end_to_end_ms)
    l2_median_tokens = statistics.median(l2_warm_tokens)
    baseline_median_latency = statistics.median(baseline_end_to_end_ms)
    baseline_median_tokens = statistics.median(baseline_tokens)

    latency_improved = l2_median_latency < baseline_median_latency
    tokens_improved = l2_median_tokens < baseline_median_tokens

    return {
        "baseline_name": baseline_name,
        "l2_warm_median_end_to_end_ms": l2_median_latency,
        "baseline_median_end_to_end_ms": baseline_median_latency,
        "latency_improved": latency_improved,
        "l2_warm_median_full_payload_tokens": l2_median_tokens,
        "baseline_median_full_payload_tokens": baseline_median_tokens,
        "tokens_improved": tokens_improved,
        "pass": latency_improved and tokens_improved,
        "derivation": (
            f"pass = (statistics.median(l2_warm end_to_end_ms across 7 entries) < "
            f"statistics.median({baseline_name} end_to_end_ms across 7 entries)) AND "
            f"(statistics.median(l2_warm full-payload tokens across 7 entries) < "
            f"statistics.median({baseline_name} full-payload tokens across 7 entries)). "
            "statistics.median, never statistics.mean, per §21's closing bullet's explicit "
            "'median' wording (distinct from §4.1/§4.2's own mean-based formulas). Reported "
            "honestly as FAIL if either median comparison does not show improvement — this "
            "function is structurally capable of returning pass: False, not only ever PASS."
        ),
    }


def _run_single_entry(mod, _kgpa, _kgc, _kgr, corpus_entry: dict, attempt_ac6: bool) -> dict:
    """Steps 2-4's per-entry 4-call sequence, plus AC6's optional real-call re-verification
    (inserted between calls 2 and 3, before the isolation delete, so the Level 2 row it
    revalidates against still exists). Returns the raw per-entry measurement dict."""
    query_text = corpus_entry["query_text"]
    request = {"query": query_text}
    effective_budget = mod.DEFAULT_BUDGET_TOKENS

    routing_decision = _kgr.route(query_text)
    identity_l2 = _kgc.compute_context_packet_lookup_identity(request, routing_decision, effective_budget)
    identity_l1 = _kgc.compute_lookup_identity(request, routing_decision, effective_budget)
    identity_l2_constrained = _kgc.compute_context_packet_lookup_identity(
        request, routing_decision, _CONSTRAINED_BUDGET_TOKENS
    )

    # ---- Call 1 (cold) ----
    hit_count_l2_before_call2 = None  # filled in after call 1
    call1 = _timed_call(mod, _kgc, _kgpa, query_text)
    cold_call_anomaly = None
    if call1["response"].get("cache") != "MISS":
        cold_call_anomaly = (
            f"call 1 (cold) reported response['cache'] == {call1['response'].get('cache')!r}, "
            "not 'MISS' — a stale row from a previous manual run may already have been present "
            "for this identity; this runner does not pre-clear the cache DB, so this is "
            "reported, not silently normalized away."
        )
    hit_count_l2_before_call2 = _read_hit_count_level2(_kgc, identity_l2["packet_id"])

    # ---- Call 2 (Level-2-warm) ----
    call2 = _timed_call(mod, _kgc, _kgpa, query_text)
    hit_count_l2_after_call2 = _read_hit_count_level2(_kgc, identity_l2["packet_id"])
    cache_hit_count_delta_l2 = hit_count_l2_after_call2 - hit_count_l2_before_call2
    spy_says_hit_l2 = call2["provider_round_trip_call_count"] == 0
    sql_says_hit_l2 = cache_hit_count_delta_l2 == 1
    string_says_hit_l2 = call2["response"].get("cache") == "HIT_L2"
    cache_status_l2warm = "HIT_L2" if (spy_says_hit_l2 and sql_says_hit_l2) else "MISS"
    signal_anomaly_l2warm = None
    if spy_says_hit_l2 != sql_says_hit_l2 or spy_says_hit_l2 != string_says_hit_l2:
        signal_anomaly_l2warm = (
            f"cache-hit verification signals disagree for call 2: assemble_packet spy calls="
            f"{call2['provider_round_trip_call_count']} (implies "
            f"{'HIT' if spy_says_hit_l2 else 'MISS'}), db hit_count delta="
            f"{cache_hit_count_delta_l2} (implies {'HIT' if sql_says_hit_l2 else 'MISS'}), "
            f"response['cache']={call2['response'].get('cache')!r}. cache_status_l2warm is "
            "conservatively reported as MISS unless both spy and SQL signals agree — this "
            "disagreement itself is reported, not silently resolved."
        )

    # ---- AC6 real-call re-verification (before the isolation delete, on this entry only if
    #      requested and its cold response carries a usable cited path) ----
    ac6_result = _verify_ac6_invalidation(mod, _kgc, identity_l2, request) if attempt_ac6 else None

    # ---- Disclosed, narrowly-scoped isolation delete ----
    db_path = Path(_kgc.rc.CACHE_DB_PATH)
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute(
            "DELETE FROM retrieval_context_packet_cache_rows WHERE packet_id = ?",
            (identity_l2["packet_id"],),
        )
        isolation_delete_rowcount = cursor.rowcount
        conn.commit()
    finally:
        conn.close()
    isolation_delete_anomaly = None
    if isolation_delete_rowcount != 1:
        isolation_delete_anomaly = (
            f"isolation DELETE affected {isolation_delete_rowcount} rows, not exactly 1, for "
            f"packet_id={identity_l2['packet_id']!r} — call 3 (Level-1-warm) is SKIPPED for this "
            "entry rather than fabricating a number."
        )

    # ---- Call 3 (Level-1-warm), skipped on an isolation-delete anomaly ----
    call3 = None
    cache_status_l1warm = None
    signal_anomaly_l1warm = None
    if isolation_delete_anomaly is None:
        hit_count_l1_before_call3 = _read_hit_count_level1(
            _kgc, identity_l1["query_hash"], identity_l1["repo_branch_scope"]
        )
        call3 = _timed_call(mod, _kgc, _kgpa, query_text)
        hit_count_l1_after_call3 = _read_hit_count_level1(
            _kgc, identity_l1["query_hash"], identity_l1["repo_branch_scope"]
        )
        cache_hit_count_delta_l1 = hit_count_l1_after_call3 - hit_count_l1_before_call3
        spy_says_hit_l1 = call3["provider_round_trip_call_count"] == 0
        sql_says_hit_l1 = cache_hit_count_delta_l1 == 1
        string_says_hit_l1 = call3["response"].get("cache") == "HIT"
        cache_status_l1warm = "HIT" if (spy_says_hit_l1 and sql_says_hit_l1) else "MISS"
        if spy_says_hit_l1 != sql_says_hit_l1 or spy_says_hit_l1 != string_says_hit_l1:
            signal_anomaly_l1warm = (
                f"cache-hit verification signals disagree for call 3: assemble_packet spy calls="
                f"{call3['provider_round_trip_call_count']} (implies "
                f"{'HIT' if spy_says_hit_l1 else 'MISS'}), db hit_count delta="
                f"{cache_hit_count_delta_l1} (implies {'HIT' if sql_says_hit_l1 else 'MISS'}), "
                f"response['cache']={call3['response'].get('cache')!r}. cache_status_l1warm is "
                "conservatively reported as MISS unless both spy and SQL signals agree."
            )

    # ---- Call 4 (constrained budget, distinct identity) ----
    call4 = _timed_call(
        mod, _kgc, _kgpa, query_text, budget_tokens=_CONSTRAINED_BUDGET_TOKENS
    )

    return {
        "corpus_entry": corpus_entry,
        "request": request,
        "routing_decision": routing_decision,
        "identity_l2": identity_l2,
        "identity_l1": identity_l1,
        "identity_l2_constrained": identity_l2_constrained,
        "call1_cold": call1,
        "call2_l2warm": call2,
        "call3_l1warm": call3,
        "call4_constrained": call4,
        "cold_call_anomaly": cold_call_anomaly,
        "cache_status_l2warm": cache_status_l2warm,
        "signal_anomaly_l2warm": signal_anomaly_l2warm,
        "cache_hit_count_delta_l2": cache_hit_count_delta_l2,
        "isolation_delete_rowcount": isolation_delete_rowcount,
        "isolation_delete_anomaly": isolation_delete_anomaly,
        "cache_status_l1warm": cache_status_l1warm,
        "signal_anomaly_l1warm": signal_anomaly_l1warm,
        "ac6_result": ac6_result,
    }


def _compute_entry_report(
    raw: dict, _kgpa, phase0_entry: dict, phase1_entry: dict, phase2_entry: dict,
) -> dict:
    corpus_entry = raw["corpus_entry"]
    call1, call2, call3, call4 = (
        raw["call1_cold"], raw["call2_l2warm"], raw["call3_l1warm"], raw["call4_constrained"],
    )

    l2_warm_full_payload_tokens = _kgpa.kgmcp_char_heuristic_v1(
        json.dumps(call2["response"], sort_keys=True)
    )
    l1_warm_full_payload_tokens = (
        _kgpa.kgmcp_char_heuristic_v1(json.dumps(call3["response"], sort_keys=True))
        if call3 is not None
        else None
    )

    budget_compliance = _compute_budget_compliance(
        _kgpa, call4["response"], _CONSTRAINED_BUDGET_TOKENS
    )
    conflicts_report = _compute_conflicts_report(call1["response"])
    recall_report = _compute_recall_report(
        corpus_entry, call1["response"], phase0_entry, phase1_entry, phase2_entry,
        raw["cold_call_anomaly"],
    )

    return {
        "id": corpus_entry["id"],
        "query_text": corpus_entry["query_text"],
        "routing_shape": corpus_entry["routing_shape"],
        "providers_selected": list(raw["routing_decision"].providers_selected),
        "cold_call_anomaly": raw["cold_call_anomaly"],
        "cold_end_to_end_ms": call1["end_to_end_ms"],
        "cold_lookup_and_validation_ms": call1["lookup_and_validation_ms"],
        "cold_fallback_and_assembly_ms": call1["fallback_and_assembly_ms"],
        "l2_warm_end_to_end_ms": call2["end_to_end_ms"],
        "l2_warm_lookup_and_validation_ms": call2["lookup_and_validation_ms"],
        "l2_warm_fallback_and_assembly_ms": call2["fallback_and_assembly_ms"],
        "l2_warm_full_payload_tokens": l2_warm_full_payload_tokens,
        "cache_status_l2warm": raw["cache_status_l2warm"],
        "signal_anomaly_l2warm": raw["signal_anomaly_l2warm"],
        "cache_hit_count_delta_l2": raw["cache_hit_count_delta_l2"],
        "isolation_delete_rowcount": raw["isolation_delete_rowcount"],
        "isolation_delete_anomaly": raw["isolation_delete_anomaly"],
        "l1_warm_end_to_end_ms": call3["end_to_end_ms"] if call3 is not None else None,
        "l1_warm_lookup_and_validation_ms": (
            call3["lookup_and_validation_ms"] if call3 is not None else None
        ),
        "l1_warm_fallback_and_assembly_ms": (
            call3["fallback_and_assembly_ms"] if call3 is not None else None
        ),
        "l1_warm_full_payload_tokens": l1_warm_full_payload_tokens,
        "cache_status_l1warm": raw["cache_status_l1warm"],
        "signal_anomaly_l1warm": raw["signal_anomaly_l1warm"],
        "constrained_budget_end_to_end_ms": call4["end_to_end_ms"],
        "constrained_budget_cache_status": call4["response"].get("cache"),
        "budget_compliance": budget_compliance,
        "conflicts_report": conflicts_report,
        "recall_report": recall_report,
        "ac6_result": raw["ac6_result"],
        "instrumentation_granularity_note": (
            "3 real, externally-timed segments (lookup_and_validation_ms, "
            "fallback_and_assembly_ms, end_to_end_ms), not the proposal's 5-name wording "
            "(lookup, validation, fallback, assembly, end-to-end) — 'validation' is not a "
            "separate call boundary from 'lookup' inside perform_context_packet_cache_lookup()/"
            "perform_cache_lookup(), and 'assembly' is not separate from 'fallback' inside "
            "assemble_packet(), in the current gateway code. This is a genuine, disclosed "
            "instrumentation-granularity limit of measurement-only tooling, not a shortfall in "
            "measurement effort."
        ),
    }


def run_corpus() -> dict:
    mod = _load_gateway_module()
    _kgr = mod._load_router_module()
    _kgpa = mod._load_packet_assembly_module()
    _kgc = mod._load_cache_module()

    phase0_fixture = json.loads(_PHASE0_FIXTURE_PATH.read_text())
    phase1_fixture = json.loads(_PHASE1_FIXTURE_PATH.read_text())
    phase2_fixture = json.loads(_PHASE2_FIXTURE_PATH.read_text())
    phase0_entries_by_id = {e["id"]: e for e in phase0_fixture["entries"]}
    phase1_entries_by_id = {e["id"]: e for e in phase1_fixture["entries"]}
    phase2_entries_by_id = {e["id"]: e for e in phase2_fixture["entries"]}

    pre_run_manifest_built_at = _load_manifest_built_at()
    pre_run_cache_db_state = _read_cache_db_row_counts(_kgc)

    entries: list[dict] = []
    all_touched_packet_ids: set[str] = set()
    ac6_result = None
    ac6_entry_id = None

    for corpus_entry in CORPUS:
        want_ac6 = ac6_result is None
        raw = _run_single_entry(mod, _kgpa, _kgc, _kgr, corpus_entry, attempt_ac6=want_ac6)
        all_touched_packet_ids.add(raw["identity_l2"]["packet_id"])
        all_touched_packet_ids.add(raw["identity_l2_constrained"]["packet_id"])

        if want_ac6 and raw["ac6_result"] is not None:
            ac6_result = raw["ac6_result"]
            ac6_entry_id = corpus_entry["id"]

        entry = _compute_entry_report(
            raw, _kgpa,
            phase0_entries_by_id[corpus_entry["id"]],
            phase1_entries_by_id[corpus_entry["id"]],
            phase2_entries_by_id[corpus_entry["id"]],
        )
        entries.append(entry)

    if ac6_result is None:
        ac6_result = {
            "disclosed_limitation": (
                "No corpus entry's cold response contained a context item with a real 'path' "
                "field usable for AC6's stale-rejection/unrelated-change real-round-trip "
                "sub-measurements — disclosed explicitly, not silently marked satisfied."
            ),
        }

    l2_warm_latencies = [e["l2_warm_end_to_end_ms"] for e in entries]
    l2_warm_tokens = [e["l2_warm_full_payload_tokens"] for e in entries]

    phase1_cold_latencies = [
        phase1_entries_by_id[e["id"]]["gateway_wall_time_ms"] for e in entries
    ]
    phase1_cold_tokens = [phase1_entries_by_id[e["id"]]["gateway_tokens"] for e in entries]

    l1_warm_latencies_by_id = {e["id"]: e["l1_warm_end_to_end_ms"] for e in entries}
    l1_warm_tokens_by_id = {e["id"]: e["l1_warm_full_payload_tokens"] for e in entries}
    l1_warm_measurable = all(
        l1_warm_latencies_by_id[e["id"]] is not None and l1_warm_tokens_by_id[e["id"]] is not None
        for e in entries
    )

    ac4_vs_phase1_cold = _compute_ac4_result(
        l2_warm_latencies, l2_warm_tokens, phase1_cold_latencies, phase1_cold_tokens,
        "phase1_cold",
    )
    ac4_vs_level1_warm = (
        _compute_ac4_result(
            l2_warm_latencies, l2_warm_tokens,
            [l1_warm_latencies_by_id[e["id"]] for e in entries],
            [l1_warm_tokens_by_id[e["id"]] for e in entries],
            "this_run_level1_warm",
        )
        if l1_warm_measurable
        else {
            "baseline_name": "this_run_level1_warm",
            "pass": False,
            "derivation": (
                "At least one entry's Level-1-warm measurement is missing (isolation-delete "
                "anomaly skipped call 3 for that entry) — this baseline comparison cannot be "
                "computed and is honestly reported as FAIL/unavailable, not silently omitted."
            ),
        }
    )

    post_run_manifest_built_at = _load_manifest_built_at()
    if post_run_manifest_built_at != pre_run_manifest_built_at:
        raise RuntimeError(
            "knowledge-index/manifest.json's built_at changed during this run "
            f"({pre_run_manifest_built_at!r} -> {post_run_manifest_built_at!r}) — a concurrent "
            "index rebuild invalidates every subsequent revalidation; this run's results are "
            "unusable and must not be written to the fixture."
        )

    aggregate = _compute_aggregate(entries, ac4_vs_phase1_cold, ac4_vs_level1_warm)

    return {
        "corpus_version": CORPUS_VERSION,
        "compared_against_phase1_recorded_at_utc": phase1_fixture["recorded_at_utc"],
        "compared_against_phase2_recorded_at_utc": phase2_fixture["recorded_at_utc"],
        "recorded_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "manifest_built_at_at_run_time": pre_run_manifest_built_at,
        "pre_run_cache_db_state": pre_run_cache_db_state,
        "default_budget_tokens_used": mod.DEFAULT_BUDGET_TOKENS,
        "constrained_budget_tokens_used": _CONSTRAINED_BUDGET_TOKENS,
        "concurrent_write_risk_note": (
            "This runner opens its own short-lived sqlite3 connections for reads and for the "
            "one disclosed isolation DELETE. Concurrent writes to knowledge-index/retrieval_cache.db "
            "from another live process during this run are a low-probability, undetected residual "
            "risk this runner cannot itself observe or guard against (Architecture Review "
            "advisory note) — disclosed here, not silently assumed away."
        ),
        "ac6_entry_id": ac6_entry_id,
        "ac6_result": ac6_result,
        "ac4_vs_phase1_cold": ac4_vs_phase1_cold,
        "ac4_vs_level1_warm": ac4_vs_level1_warm,
        "all_touched_packet_ids": sorted(all_touched_packet_ids),
        "entries": entries,
        "aggregate": aggregate,
    }


def _compute_aggregate(entries: list[dict], ac4_vs_phase1_cold: dict, ac4_vs_level1_warm: dict) -> dict:
    genuine_l2_hit_count = sum(1 for e in entries if e["cache_status_l2warm"] == "HIT_L2")
    genuine_l1_hit_count = sum(1 for e in entries if e["cache_status_l1warm"] == "HIT")
    budget_pass_count = sum(1 for e in entries if e["budget_compliance"]["pass"])
    total_conflicts_observed = sum(e["conflicts_report"]["conflicts_observed"] for e in entries)
    recall_regressions = [e["id"] for e in entries if e["recall_report"]["recall_regression_flag"]]

    return {
        "genuine_l2_hit_count": {"count": genuine_l2_hit_count, "of": len(entries)},
        "genuine_l1_hit_count": {"count": genuine_l1_hit_count, "of": len(entries)},
        "ac2_budget_compliance": {"pass_count": budget_pass_count, "of": len(entries)},
        "ac3_total_conflicts_observed_in_corpus": total_conflicts_observed,
        "ac3_conflicts_observed_in_corpus": total_conflicts_observed > 0,
        "ac4_vs_phase1_cold_pass": ac4_vs_phase1_cold["pass"],
        "ac4_vs_level1_warm_pass": ac4_vs_level1_warm["pass"],
        "ac5_recall_regressions": recall_regressions,
        "ac5_recall_regression_free": len(recall_regressions) == 0,
    }


def main() -> None:
    report = run_corpus()
    _OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {_OUTPUT_PATH} ({len(report['entries'])} entries)")
    print(f"aggregate: {json.dumps(report['aggregate'], indent=2, sort_keys=True)}")


if __name__ == "__main__":
    main()

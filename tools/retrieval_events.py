"""
tools/retrieval_events.py — Additive, versioned retrieval-event field set appended to the
existing `agent-monitoring/events.jsonl` file, plus one thin instrumentation wrapper per Phase 3
module (`tools/hybrid_retrieval.py`, `tools/retrieval_cache.py`,
`tools/context_packet_assembler.py`).

What this is: a single-source-of-truth field-shape constant (`RETRIEVAL_EVENT_FIELDS`),
`emit_retrieval_event()` (validates via `record_events.validate_record()`, writes via
`writer.write_lines()` — the exact same append path `record_events.py` itself uses), and the 3
`wrap_*()` functions that time + observe a Phase 3 module's own public entry point and emit one
event per call.

What this is not: no `execution_id`/`provider` field (still out of scope, per
`docs/ai/monitoring_writer_decision.md` §2), no reference to any real-time workflow orchestrator
file or existing automation entry point, no new lock/queue/journal writer mechanism — this module
reuses `writer.py`'s `write_lines()` exclusively via `record_events.validate_record()`'s existing
gate, never opens a file directly and never imports `fcntl`.

Built for TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT, the deferred "Phase 4" event-emission work
`TCK-20260729-HYBRID-RETRIEVAL-FUSION`/`TCK-20260729-RETRIEVAL-CACHE-LEVELS`/
`TCK-20260729-CONTEXT-PACKET-ASSEMBLY` each explicitly left out of scope.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

_MONITORING_DIR = _TOOLS_DIR / "agent-monitoring"
if str(_MONITORING_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_DIR))
import record_events  # noqa: E402
from writer import write_lines  # noqa: E402

# Distinct from tools/retrieval_cache.py::RETRIEVAL_VERSION (the cache *key*-versioning constant,
# bumped on cache-key/invalidation logic changes). This constant versions the retrieval-event
# *field shape itself* — a different concept, never conflated with the cache module's constant.
retrieval_event_schema_version: int = 1

# Single source-of-truth field-name set for the retrieval-specific fields this module adds on top
# of events.jsonl's existing 7 REQUIRED base fields (run_id, seq, ts, phase, agent, summary,
# status — untouched, see record_events.REQUIRED). Deliberately excludes execution_id, provider,
# and any of the 7 REQUIRED names — this constant is retrieval-specific fields only.
RETRIEVAL_EVENT_FIELDS: frozenset[str] = frozenset(
    {
        "retrieval_version",
        "corpus_generation",
        "cache_level",
        "cache_status",
        "latency_ms",
        "candidate_count",
        "selected_count",
        "source_kind_counts",
        "authority_counts",
        "freshness_counts",
        "exclusion_reason_counts",
        "cited_source_hashes",
        "adequacy_verdict",
        "expansion_reason",
        "expansion_count",
        "scenario",
        "risk_tier",
        "retrieval_event_schema_version",
    }
)

# Deliberately simple, tunable placeholder heuristic (ticket's own Out of Scope: "no re-ranker, no
# sophisticated evaluation") — not a claim of real relevance/quality assessment.
NOISY_RATIO_THRESHOLD: int = 5


def compute_adequacy_verdict(selected_count: int, candidate_count: int) -> str:
    """3-branch placeholder verdict: "insufficient" if nothing was selected, "noisy" if the
    candidate pool dwarfs what was selected (>= NOISY_RATIO_THRESHOLD x), "sufficient" otherwise.
    """
    if selected_count == 0:
        return "insufficient"
    if candidate_count >= NOISY_RATIO_THRESHOLD * selected_count:
        return "noisy"
    return "sufficient"


def emit_retrieval_event(
    *,
    run_id: str,
    seq: int,
    phase: str,
    agent: str,
    summary: str,
    status: str = "ok",
    events_file: Path | None = None,
    ts: str | None = None,
    **retrieval_fields,
) -> bool:
    """Build, validate, and append one retrieval-event record.

    Validation and the actual append both reuse record_events.py's/writer.py's existing,
    already-stress-tested paths verbatim — this function adds no new lock/queue/journal mechanism
    of its own. Never raises on a write failure (write_lines()'s bool is returned as-is, matching
    CLAUDE.md's "monitoring write failure must never fail the workflow"); it DOES raise on a
    caller-usage error (an unknown retrieval field, or a record validate_record() itself would
    reject) — fail loud on bad caller input, fail soft on infra write failure.

    `ts` defaults to None, preserving the historical datetime.now(timezone.utc) behavior. A
    caller-supplied `ts` is used verbatim (e.g. backfilling a record's real event-time when it
    differs from write-time) — this never mutates an already-written record, since this function
    only ever appends.
    """
    unknown_fields = set(retrieval_fields) - RETRIEVAL_EVENT_FIELDS
    if unknown_fields:
        raise ValueError(
            f"unknown retrieval field(s) not in RETRIEVAL_EVENT_FIELDS: {sorted(unknown_fields)}"
        )

    record = {
        "run_id": run_id,
        "seq": seq,
        "ts": ts
        if ts is not None
        else datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "phase": phase,
        "agent": agent,
        "summary": summary,
        "status": status,
        "retrieval_event_schema_version": retrieval_event_schema_version,
        **retrieval_fields,
    }

    errors = record_events.validate_record(record)
    if errors:
        raise ValueError(errors)

    if events_file is not None:
        target = events_file
    else:
        # Matches record_events.py::main()'s own write-time iso_week/events_file computation
        # verbatim (tools/agent-monitoring/record_events.py:153-154) — record_events.EVENTS_FILE
        # no longer exists as a module attribute (TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY),
        # so this default must reproduce record_events.py's own current-week target rather than
        # reference a removed constant.
        iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
        target = Path("agent-monitoring/data") / iso_week / "events.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    return write_lines(target, [json.dumps(record, separators=(",", ":"))])


# ---------------------------------------------------------------------------
# wrap_hybrid_retrieval() — instruments tools/hybrid_retrieval.py::hybrid_fuse_and_filter()
# ---------------------------------------------------------------------------

RUN_ID_HYBRID = "RETRIEVAL-EVENT-hybrid-retrieval"
AGENT_HYBRID = "hybrid-retrieval-wrapper"


def wrap_hybrid_retrieval(
    *,
    seq: int,
    summary: str,
    run_id: str = RUN_ID_HYBRID,
    status: str = "ok",
    events_file: Path | None = None,
    ts: str | None = None,
    expansion_reason: str | None = None,
    expansion_count: int | None = None,
    **hybrid_kwargs,
):
    """Times and observes one hybrid_fuse_and_filter() call, emits exactly one retrieval event,
    and returns the wrapped call's real return value unchanged.

    `expansion_reason`/`expansion_count` are optional pass-through fields: forwarded to
    `emit_retrieval_event()` only when the caller supplies them, never fabricated or defaulted
    (TCK-20260804-EXPANSION-RATE-WIRING). No caller in this codebase supplies them today.
    """
    from hybrid_retrieval import candidate_k, hybrid_fuse_and_filter

    start = time.perf_counter()
    results = hybrid_fuse_and_filter(**hybrid_kwargs)
    latency_ms = (time.perf_counter() - start) * 1000

    selected_count = len(results)
    # Upper-bound approximation of the pre-fusion candidate pool: hybrid_fuse_and_filter()'s
    # return shape does not expose the exact post-union count, and this wrapper must not alter
    # that function's signature/return shape to add one (Resolved Decision 7).
    candidate_count = candidate_k(hybrid_kwargs["top_k"])
    source_kind_counts = Counter(r.kind for r in results)
    authority_counts = Counter(r.authority for r in results)
    freshness_counts = Counter(r.freshness for r in results)

    optional_expansion_fields = {}
    if expansion_reason is not None:
        optional_expansion_fields["expansion_reason"] = expansion_reason
    if expansion_count is not None:
        optional_expansion_fields["expansion_count"] = expansion_count

    emit_retrieval_event(
        run_id=run_id,
        seq=seq,
        phase="Retrieval",
        agent=AGENT_HYBRID,
        summary=summary,
        status=status,
        events_file=events_file,
        ts=ts,
        latency_ms=latency_ms,
        candidate_count=candidate_count,
        selected_count=selected_count,
        source_kind_counts=dict(source_kind_counts),
        authority_counts=dict(authority_counts),
        freshness_counts=dict(freshness_counts),
        adequacy_verdict=compute_adequacy_verdict(selected_count, candidate_count),
        **optional_expansion_fields,
    )
    return results


# ---------------------------------------------------------------------------
# wrap_retrieval_cache_check() — instruments tools/retrieval_cache.py's 3 check_*_cache() fns
# ---------------------------------------------------------------------------

RUN_ID_CACHE = "RETRIEVAL-EVENT-retrieval-cache"
AGENT_CACHE = "retrieval-cache-wrapper"


def wrap_retrieval_cache_check(
    cache_level: str,
    *,
    seq: int,
    summary: str,
    run_id: str = RUN_ID_CACHE,
    status: str = "ok",
    events_file: Path | None = None,
    ts: str | None = None,
    expansion_reason: str | None = None,
    expansion_count: int | None = None,
    **check_kwargs,
):
    """Dispatches to check_index_cache/check_query_cache/check_packet_cache by `cache_level`
    (one of retrieval_cache.INDEX_CACHE_CATEGORY/QUERY_CACHE_CATEGORY/PACKET_CACHE_CATEGORY),
    emits exactly one retrieval event whose cache_status is the imported HIT/MISS/STALE_REJECTED
    constant verbatim (never re-literaled), and returns the wrapped call's real result unchanged.

    `expansion_reason`/`expansion_count` are optional pass-through fields: forwarded to
    `emit_retrieval_event()` only when the caller supplies them, never fabricated or defaulted
    (TCK-20260804-EXPANSION-RATE-WIRING). No caller in this codebase supplies them today.
    """
    from retrieval_cache import (
        INDEX_CACHE_CATEGORY,
        PACKET_CACHE_CATEGORY,
        QUERY_CACHE_CATEGORY,
        check_index_cache,
        check_packet_cache,
        check_query_cache,
    )

    dispatch = {
        INDEX_CACHE_CATEGORY: check_index_cache,
        QUERY_CACHE_CATEGORY: check_query_cache,
        PACKET_CACHE_CATEGORY: check_packet_cache,
    }
    start = time.perf_counter()
    result = dispatch[cache_level](**check_kwargs)
    latency_ms = (time.perf_counter() - start) * 1000

    retrieval_fields = {
        "cache_level": cache_level,
        "cache_status": result.status,
        "latency_ms": latency_ms,
    }
    if "corpus_generation" in check_kwargs:
        retrieval_fields["corpus_generation"] = check_kwargs["corpus_generation"]
    if "retrieval_version" in check_kwargs:
        retrieval_fields["retrieval_version"] = check_kwargs["retrieval_version"]
    if expansion_reason is not None:
        retrieval_fields["expansion_reason"] = expansion_reason
    if expansion_count is not None:
        retrieval_fields["expansion_count"] = expansion_count

    emit_retrieval_event(
        run_id=run_id,
        seq=seq,
        phase="Retrieval",
        agent=AGENT_CACHE,
        summary=summary,
        status=status,
        events_file=events_file,
        ts=ts,
        **retrieval_fields,
    )
    return result


# ---------------------------------------------------------------------------
# wrap_context_packet_assembly() — instruments context_packet_assembler.py::assemble_context_packet()
# ---------------------------------------------------------------------------

RUN_ID_PACKET = "RETRIEVAL-EVENT-context-packet"
AGENT_PACKET = "context-packet-wrapper"


def wrap_context_packet_assembly(
    *,
    seq: int,
    summary: str,
    run_id: str = RUN_ID_PACKET,
    status: str = "ok",
    events_file: Path | None = None,
    ts: str | None = None,
    expansion_reason: str | None = None,
    expansion_count: int | None = None,
    **assemble_kwargs,
):
    """Times and observes one assemble_context_packet() call, emits exactly one retrieval event,
    and returns the wrapped call's real ContextPacket unchanged.

    candidate_count has no natural pre-assembly analogue exposed by assemble_context_packet()'s
    signature, so it is omitted here rather than fabricated — adequacy_verdict degenerates to
    "sufficient"/"insufficient" only at this layer (Resolved Decision 4/7).

    `expansion_reason`/`expansion_count` are optional pass-through fields: forwarded to
    `emit_retrieval_event()` only when the caller supplies them, never fabricated or defaulted
    (TCK-20260804-EXPANSION-RATE-WIRING). No caller in this codebase supplies them today.
    """
    from context_packet_assembler import assemble_context_packet

    start = time.perf_counter()
    packet = assemble_context_packet(**assemble_kwargs)
    latency_ms = (time.perf_counter() - start) * 1000

    selected_count = len(packet.included)
    cited_source_hashes = [entry["hash"] for entry in packet.included]
    exclusion_reason_counts = {
        f'{row["kind"]}:{row["reason"]}': row["count"] for row in packet.excluded_summary
    }

    optional_expansion_fields = {}
    if expansion_reason is not None:
        optional_expansion_fields["expansion_reason"] = expansion_reason
    if expansion_count is not None:
        optional_expansion_fields["expansion_count"] = expansion_count

    emit_retrieval_event(
        run_id=run_id,
        seq=seq,
        phase="Retrieval",
        agent=AGENT_PACKET,
        summary=summary,
        status=status,
        events_file=events_file,
        ts=ts,
        latency_ms=latency_ms,
        selected_count=selected_count,
        cited_source_hashes=cited_source_hashes,
        exclusion_reason_counts=exclusion_reason_counts,
        corpus_generation=packet.corpus_generation,
        retrieval_version=packet.retrieval_version,
        adequacy_verdict=compute_adequacy_verdict(selected_count, selected_count),
        **optional_expansion_fields,
    )
    return packet

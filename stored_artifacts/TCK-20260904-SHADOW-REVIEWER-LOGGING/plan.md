---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-SHADOW-REVIEWER-LOGGING
artifact_type: plan
tags: [ai, agent-monitoring, security]
---

# Implementation Plan — TCK-20260904-SHADOW-REVIEWER-LOGGING

## Summary

Add an advisory, env-gated "shadow candidate reviewer" call alongside the existing production
`architecture-reviewer` call (`.claude/workflows/implement-ticket.js:992`, Architecture-Verify
phase) and the existing production `security-reviewer` call (`:1364`, Security-Review phase). Each
shadow call runs the same `agentType` against the same diff/evidence as the production call, but on
a genuinely different model (`opts.model: 'claude-fable-5-1'` — a distinct model family, not a
Claude-Sonnet size variant, chosen specifically to de-correlate failure modes from whatever model
the main-loop/production call inherits). The shadow call's verdict is written to
`agent-monitoring/data/<week>/events.jsonl` as a **separate, joinable record** (same `run_id`+`phase`,
distinguished by a negative `seq` and a `-shadow`-suffixed `agent` value) via a new emission module,
`tools/agent-monitoring/shadow_reviewer_events.py` — modeled on `tools/retrieval_events.py`'s
`emit_retrieval_event()` *pattern* (validate via `record_events.validate_record()`, write via
`writer.write_lines()`) but **not** a call to that function itself, because
`emit_retrieval_event()`'s own `unknown_fields` guard (`tools/retrieval_events.py:117-121`) rejects
any field outside `RETRIEVAL_EVENT_FIELDS` — this ticket's new `candidate_*` field family would be
rejected outright if routed through it. The shadow call's own tool-call footprint is attributed to
its own `(run_id, negative_seq)` bucket via the existing `writeSidecar()` helper
(`implement-ticket.js:274-283`), so its `cost_proxy_score`/`tool_call_count` never merge into the
production call's bucket. A new bounded-window function,
`tools/agent-monitoring/shadow_reviewer_window.py::is_shadow_window_open()`, gates whether the
shadow call fires at all — independent per-reviewer thresholds (50 for `architecture-reviewer`, 10
for `security-reviewer`), sized from the real historical volume split confirmed in this session
(478 `Architecture-Verify` events vs. 14 `Security-Review` events in
`agent-monitoring/data/*/events.jsonl` today — a ~34:1 ratio). Neither shadow call's verdict ever
reaches `pushEvent(..., 'failed', ...)`, `writeMonitoring(...)`, or an early `return` — those three
remain wired exclusively to the production `agent()` call's own `archVerify`/`securityReview`
variables, untouched by this plan. `tests/tools/test_current_run_sidecar_orchestrator.py`'s
hard-coded `writeSidecar()` count moves from 11 to 13, with a **second, separate regex** for the two
new negative-seq shadow sites (they cannot use the existing `events.length + 1 + seqOffset`
positive-seq regex, since a positive-seq shadow call would collide with the enclosing production
phase's own `(run_id, seq)` bucket — this is a deliberate, cited deviation from `test_plan.md`'s
literal "regex count from 11 to 13" phrasing, reconciled below in Step 6).

## Judgment Calls Resolved (the 5 open questions from investigation.md / the planning brief)

1. **Candidate model:** `claude-fable-5-1` (Fable 5.1). Production reviewers inherit the
   main-loop's model (no `model:` override today, confirmed 0/16 agent files declare one) — this
   session's own main-loop model is Sonnet 5, so the production call effectively runs Sonnet 5.
   Fable is a genuinely different model family in this environment's model roster (`sonnet` /
   `opus` / `haiku` / `fable` are peer options, not size variants of one lineage) — this maximizes
   de-correlation of failure modes versus picking a same-family size variant (e.g. Haiku 4.5, which
   is still a Claude-Sonnet-lineage model at a different size, sharing more training/architecture
   ancestry with the production Sonnet-5 call than a cross-family model would).
2. **`EVENTS_FILE` bug (Investigate-phase shadow-packet, `implement-ticket.js:597`):** **not fixed
   in this ticket.** It is a pre-existing, different call site (`TCK-20260729-SHADOW-PACKET-CALL-SITE`'s
   own code, gated by a different env var, `SHADOW_CONTEXT_PACKET_ENABLED`, which this ticket's
   investigation confirms has never been set to `1` anywhere in production — so the bug has zero
   live blast radius today). Fixing it is unrelated to this ticket's own scope (wiring
   architecture-reviewer/security-reviewer shadow calls) and would silently expand this ticket's
   diff into another ticket's call site. **This plan's own new code never copies the buggy pattern**
   — every prior-count lookup below uses `validate.load_data_glob(Path("agent-monitoring/data"),
   "events")`, never `record_events.EVENTS_FILE`. Recommend filing a separate one-line hotfix ticket
   for the `EVENTS_FILE` bug itself; out of scope here.
3. **Prompt content for the candidate call:** **identical to the production prompt**, verbatim,
   for both call sites. Rationale: the ticket's entire purpose is isolating the *model* as the only
   variable between the two verdicts — introducing a second variable (a different prompt) would
   confound any observed verdict divergence, making it impossible to attribute a difference to the
   candidate model rather than to prompt wording. This does carry the accepted limitation flagged
   in investigation.md (the static-check-results framing was tuned for the production model) — not
   solved here, consistent with the ticket's Out of Scope (no promotion/comparison-decision logic).
4. **Per-reviewer sample-window thresholds:** `architecture-reviewer`: **50**. `security-reviewer`:
   **10**. Computed directly against real corpus volume (this session ran
   `python3 -c "..."` over every `agent-monitoring/data/*/events.jsonl` shard, counting
   `phase in {'Architecture-Verify','Security-Review'}`): **478** historical `Architecture-Verify`
   events vs. **14** historical `Security-Review` events — confirms the ~34:1 asymmetric
   accumulation-rate risk investigation.md flagged is real, not speculative. 50 gives
   `architecture-reviewer` a meaningful pilot sample without an indefinite dual-model-call tail
   (closes within roughly the pace of recent standard/epic-tier throughput). 10 is deliberately a
   much smaller floor for `security-reviewer` — at 14 real events *ever* recorded, a threshold of 50
   would likely never close; 10 is achievable while still being large enough to be a non-trivial
   pilot sample. Both are pilot-window sizes, not scientifically derived — flagged as adjustable via
   a single dict constant (`SHADOW_MAX_SAMPLES` in `shadow_reviewer_window.py`), never hardcoded at
   more than one call site.
5. **Negative-seq formula:** `shadow_seq(reviewer, run_id) = -(SHADOW_SEQ_BASE[reviewer] +
   prior_count_this_run_this_reviewer)`, where `SHADOW_SEQ_BASE = {"architecture-reviewer": 100,
   "security-reviewer": 200}` and `prior_count_this_run_this_reviewer` is a **per-run_id** count
   (scanning `agent-monitoring/events.jsonl` for prior rows with this exact `run_id` AND
   `agent == f"{reviewer}-shadow"`) — see Step 1 for the full function. Verified disjoint from:
   (a) **the real per-run positive-seq range** — real seq is always `>= 1`
   (`events.length >= 0`, `seqOffset >= 0`), shadow seq is always `<= -100`, provably disjoint
   regardless of run length/resume count (same proof shape as INFRA-299's own `seq <= 0` argument,
   just with a larger negative floor). (b) **INFRA-299's own shadow-packet formula**
   (`-(1 + prior_shadow_count)`, `agent == 'context-packet-wrapper'`) — that mechanism's own count
   is scoped to a *different* `agent` literal filter, so its own prior-count value is computed
   independently and never sees this ticket's rows; the **numeric** ranges are additionally kept
   non-overlapping on purpose (INFRA-299 only ever produces small values like -1..-5; this ticket's
   values start at -100/-200) so a human reading raw `seq` values in `events.jsonl` for one `run_id`
   can tell the two mechanisms apart by inspection alone, not just by `agent` field. Also: the
   INFRA-299 shadow-packet mechanism never calls `writeSidecar()` (confirmed — its whole action is
   one already-open `bash()` call with no nested tool calls to attribute), so there is no
   `tools.jsonl` `(run_id, seq)`-bucket collision risk even in the (only theoretical) case of an
   identical raw seq number — only an `events.jsonl` visual-inspection concern, which the distinct
   100/200 base ranges resolve. (c) **`implement-epic.js`/`create-tickets.js`'s `-1..-4` range** —
   confirmed not a real collision risk: those are different files producing different `run_id`
   prefixes (`EPIC-`/`FOLDER-`/`CREATE-TICKETS-` vs. this ticket's `TCK-...`), and `(run_id, seq)` is
   the actual uniqueness key everywhere seq is used (tools.jsonl grouping, events.jsonl provenance) —
   a shared raw seq number across different `run_id`s is never ambiguous. (d) **the two reviewers
   from each other, within one run_id** — the 100 vs. 200 base keeps `architecture-reviewer-shadow`'s
   and `security-reviewer-shadow`'s own seq ranges disjoint even before either one's own
   `prior_count` grows past a handful, and each one's `prior_count` scan filters on its own distinct
   `agent` literal, so the two reviewers' counts are computed independently regardless.

## Unresolved Questions

None — all 5 judgment calls investigation.md deferred to Plan are resolved with rationale above.

## Steps

### Step 1 — Add `tools/agent-monitoring/shadow_reviewer_window.py` (bounded sample window + seq)
**Files:** `tools/agent-monitoring/shadow_reviewer_window.py` (new)
**Change:** New module, no existing file touched. Mirrors `seq_offset.py`'s shape (pure functions +
a `MARKER:`-prefixed-JSON `__main__` entrypoint callable via `bash()` from `implement-ticket.js`,
per that file's established convention — confirmed at `seq_offset.py:43-44`).

```python
#!/usr/bin/env python3
"""Bounded shadow-reviewer sample window + collision-free negative-seq assignment
(TCK-20260904-SHADOW-REVIEWER-LOGGING). Two independent counting scopes, never conflated:
  - is_shadow_window_open(): counts prior shadow samples ACROSS ALL run_ids, for the
    bounded-sample stop condition (AC #4). Not the promotion/"enough evidence" decision —
    purely a mechanical cap on how many candidate calls this pilot ever makes.
  - compute_shadow_seq(): counts prior shadow samples for THIS run_id only, for negative-seq
    collision avoidance across resumed sessions (mirrors seq_offset.py's own resume-lookup
    precedent, scoped further to one reviewer's own agent literal).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import load_data_glob  # noqa: E402

DATA_DIR = Path("agent-monitoring/data")

# Pilot-window sizes (TCK-20260904-SHADOW-REVIEWER-LOGGING plan.md Judgment Call 4): sized from
# real corpus volume (478 historical Architecture-Verify events vs. 14 Security-Review events,
# confirmed by direct count against agent-monitoring/data/*/events.jsonl at plan time) — NOT a
# promotion/statistical-significance threshold, purely a cap on total candidate model calls this
# pilot ever makes. Adjust here only — never duplicate this literal at any call site.
SHADOW_MAX_SAMPLES = {
    "architecture-reviewer": 50,
    "security-reviewer": 10,
}

# Disjoint negative-seq base per reviewer (Judgment Call 5) — keeps the two reviewers' shadow
# ranges apart from each other AND from INFRA-299's own small -1..-5 shadow-packet range, even
# though the actual uniqueness key everywhere seq is consumed is (run_id, seq), not seq alone.
SHADOW_SEQ_BASE = {
    "architecture-reviewer": 100,
    "security-reviewer": 200,
}


def _shadow_agent_name(reviewer: str) -> str:
    return f"{reviewer}-shadow"


def count_prior_shadow_samples(reviewer: str) -> int:
    """Across ALL run_ids -- bounds the total pilot sample window (AC #4), never scoped to one
    run_id. Pure/read-only."""
    agent_name = _shadow_agent_name(reviewer)
    return sum(
        1 for e in load_data_glob(DATA_DIR, "events") if e.get("agent") == agent_name
    )


def is_shadow_window_open(reviewer: str, max_samples: int) -> bool:
    """True if fewer than max_samples prior shadow events exist for this reviewer, across all
    run_ids. False means: skip the candidate call entirely for this run (AC #4)."""
    return count_prior_shadow_samples(reviewer) < max_samples


def count_prior_shadow_samples_for_run(reviewer: str, run_id: str) -> int:
    """Scoped to ONE run_id -- for negative-seq collision avoidance across resumed sessions of
    the SAME ticket, never for the sample-window gate above. Pure/read-only."""
    agent_name = _shadow_agent_name(reviewer)
    return sum(
        1
        for e in load_data_glob(DATA_DIR, "events")
        if e.get("agent") == agent_name and e.get("run_id") == run_id
    )


def compute_shadow_seq(reviewer: str, run_id: str) -> int:
    """seq = -(SHADOW_SEQ_BASE[reviewer] + prior_count_this_run_this_reviewer). Always <= -100,
    provably disjoint from the real per-phase seq range (>= 1) for any run length/resume count,
    and from the other reviewer's own range (bases 100 vs. 200 apart)."""
    base = SHADOW_SEQ_BASE[reviewer]
    return -(base + count_prior_shadow_samples_for_run(reviewer, run_id))


if __name__ == "__main__":
    reviewer, run_id = sys.argv[1], sys.argv[2]
    result = {
        "window_open": is_shadow_window_open(reviewer, SHADOW_MAX_SAMPLES[reviewer]),
        "shadow_seq": compute_shadow_seq(reviewer, run_id),
    }
    print("SHADOW_WINDOW_JSON:" + json.dumps(result))
```
**Do NOT touch:** `seq_offset.py` itself (a separate, unrelated resume-seq-offset mechanism for the
*real* per-run positive seq range — do not merge these two concerns into one file/function).
`tools/agent-monitoring/validate.py` (only imported from, never edited — `load_data_glob` already
exists at `validate.py:238-245`, confirmed by direct read).
**Verify:** `test_shadow_window_closed_skips_candidate_call`,
`test_shadow_window_thresholds_are_independent_per_reviewer` (both in new
`tests/tools/test_shadow_reviewer_window.py`, per test_plan.md).

### Step 2 — Add `tools/agent-monitoring/shadow_reviewer_events.py` (event emission + cost attribution)
**Files:** `tools/agent-monitoring/shadow_reviewer_events.py` (new)
**Change:** New module. **Not** a thin wrapper around `tools/retrieval_events.py::emit_retrieval_event()`
— confirmed by reading `retrieval_events.py:117-121` that function raises `ValueError` on any field
outside its own `RETRIEVAL_EVENT_FIELDS` frozenset, which this ticket's `candidate_*` fields are not
part of and must never be added to (that frozenset is retrieval-specific, per its own docstring at
`retrieval_events.py:48-51`, and `test_shadow_packet_call_site.py::test_no_new_field_in_retrieval_event_fields`
already pins its exact membership — widening it would break that unrelated regression test). Instead
this module independently reproduces the *pattern* `emit_retrieval_event()` follows (validate via
`record_events.validate_record()`, write via `writer.write_lines()`), confirmed at
`record_events.py:19-29` (validates only the 7 base `REQUIRED` fields + `status` enum — no rejection
of extra keys, so a new field family is safe to attach directly). Also confirmed by reading
`record_events.py:151-160`: `tool_call_count`/`cost_proxy_score` auto-computation
(`compute_tool_stats()`) happens **only** inside `record_events.py::main()`'s own CLI batch-write
path — `emit_retrieval_event()` never calls it, so a naive mirror of that function would silently
ship shadow events with no cost/tool-count data at all, violating AC #3. This module computes its
own `candidate_tool_call_count`/`candidate_cost_proxy_score` inline, reusing
`cost_proxy.compute_cost_proxy_score()` (formula untouched, per Anti-Drift Test Guard) against
`tools.jsonl` rows filtered to this shadow call's own `(run_id, seq)` — the same rows `writeSidecar()`
(Step 3/4) attributed to it.

**Calling-convention note (post-architecture-review fix, consistent with Steps 4/5 below):** the
function's own signature stays exactly as originally designed — keyword-only, one parameter per
field — but Steps 4/5's `bash()` call sites no longer invoke it with 8 separate positional
`sys.argv` fields interpolated as separate double-quoted argv elements (a shell-injection risk for
the free-text `summary`/`verdict` fields, since those are model-generated). Instead Steps 4/5 build
one JSON payload object in JS, shell-single-quote-escape it, and pass it as a single argv element;
the one-liner in each call site parses it with `json.loads(sys.argv[1])` and calls
`emit_shadow_reviewer_event(**json.loads(sys.argv[1]))`. Because `emit_shadow_reviewer_event()`
already takes exactly these fields as keyword arguments (see signature below), no change to this
module's function signature is needed for that fix — only Steps 4/5's own call-site code changes.

```python
"""
tools/agent-monitoring/shadow_reviewer_events.py — advisory shadow-candidate-reviewer event
emission (TCK-20260904-SHADOW-REVIEWER-LOGGING).

Deliberately NOT built on top of tools/retrieval_events.py::emit_retrieval_event() -- that
function's own unknown-field guard (RETRIEVAL_EVENT_FIELDS) would reject every field this module
adds. Reproduces its underlying pattern directly: validate via record_events.validate_record(),
write via writer.write_lines() -- no new lock/queue/journal mechanism of its own.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_MONITORING_DIR = Path(__file__).resolve().parent
if str(_MONITORING_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_DIR))

import record_events  # noqa: E402
from cost_proxy import compute_cost_proxy_score  # noqa: E402
from validate import load_data_glob  # noqa: E402
from writer import write_lines  # noqa: E402

shadow_reviewer_event_schema_version: int = 1

# Additive field family on top of events.jsonl's 7 base REQUIRED fields (record_events.REQUIRED)
# -- never replaces or narrows that set, mirrors RETRIEVAL_EVENT_FIELDS's own precedent.
SHADOW_REVIEWER_EVENT_FIELDS: frozenset[str] = frozenset(
    {
        "shadow_reviewer_event_schema_version",
        "candidate_model",
        "candidate_verdict",
        "candidate_violations_count",
        "candidate_tool_call_count",
        "candidate_cost_proxy_score",
        "candidate_wall_time_ms",
        "workflow_wall_time_ms",
    }
)


def _compute_candidate_tool_stats(run_id: str, seq: int) -> tuple[int, float]:
    """Reads real tools.jsonl ground truth for this shadow call's own (run_id, seq) bucket --
    same shape as record_events.py::compute_tool_stats(), scoped to one key instead of a batch."""
    rows = [
        r
        for r in load_data_glob(Path("agent-monitoring/data"), "tools")
        if r.get("run_id") == run_id and r.get("seq") == seq
    ]
    return len(rows), compute_cost_proxy_score(rows)


def emit_shadow_reviewer_event(
    *,
    run_id: str,
    seq: int,
    phase: str,
    agent: str,
    summary: str,
    candidate_model: str,
    candidate_verdict: str,
    candidate_violations_count: int,
    candidate_wall_time_ms: int,
    workflow_wall_time_ms: int,
    status: str = "ok",
    ts: str | None = None,
    events_file: Path | None = None,
) -> bool:
    """Build, validate, and append one shadow-reviewer event record. Never raises on a write
    failure (write_lines()'s bool returned as-is, per CLAUDE.md's "monitoring write failure must
    never fail the workflow"); DOES raise on a record validate_record() itself rejects (base-schema
    misuse), same fail-loud/fail-soft split as emit_retrieval_event()."""
    candidate_tool_call_count, candidate_cost_proxy_score = _compute_candidate_tool_stats(run_id, seq)

    record = {
        "run_id": run_id,
        "seq": seq,
        "ts": ts if ts is not None else datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "phase": phase,
        "agent": agent,
        "summary": summary,
        "status": status,
        "shadow_reviewer_event_schema_version": shadow_reviewer_event_schema_version,
        "candidate_model": candidate_model,
        "candidate_verdict": candidate_verdict,
        "candidate_violations_count": candidate_violations_count,
        "candidate_tool_call_count": candidate_tool_call_count,
        "candidate_cost_proxy_score": candidate_cost_proxy_score,
        "candidate_wall_time_ms": candidate_wall_time_ms,
        "workflow_wall_time_ms": workflow_wall_time_ms,
    }

    errors = record_events.validate_record(record)
    if errors:
        raise ValueError(errors)

    if events_file is not None:
        target = events_file
    else:
        # Matches record_events.py's own current-week target (record_events.py:153-154) --
        # EVENTS_FILE no longer exists as a module attribute (TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY).
        iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
        target = Path("agent-monitoring/data") / iso_week / "events.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    return write_lines(target, [json.dumps(record, separators=(",", ":"))])
```
**Do NOT touch:** `tools/retrieval_events.py` (`RETRIEVAL_EVENT_FIELDS` must stay exactly as pinned
by `test_no_new_field_in_retrieval_event_fields`), `tools/agent-monitoring/record_events.py`'s
`compute_tool_stats()` (reused via `cost_proxy.compute_cost_proxy_score()` directly, not modified —
`compute_tool_stats()` itself is scoped to the 3-workflow membership check documented at
`record_events.py:60-72` and this module deliberately does not call it, to avoid also re-triggering
its `implement-ticket`/`implement-epic`/`create-tickets` workflow-membership filtering for a
single-key lookup it wasn't designed for).
**Verify:** a direct in-process test (mirrors `test_shadow_packet_call_site.py`'s item 4 technique —
import the module, call `emit_shadow_reviewer_event()` against a `tmp_path` events file, assert the
written record's shape/field values) — part of `tests/tools/test_shadow_reviewer_call_site.py`
(`test_candidate_call_cost_and_timing_labeled_separately_from_production`, per test_plan.md).

### Step 3 — Add `workflowStartMs` capture helper (implement-ticket.js)
**Files:** `.claude/workflows/implement-ticket.js`
**Change:** Add a new `captureEpochMs()` orchestrator helper immediately after the existing
`captureTs()` definition (confirmed at `implement-ticket.js:289-296` — `const captureTs = async ()
=> { const out = await bash('date -u +%Y-%m-%dT%H:%M:%SZ'); return (out || '').trim() || null }`),
and one `const workflowStartMs = await captureEpochMs()` call placed directly after it, before
`resolveScopeTicketLocation`'s definition:

```js
const captureEpochMs = async () => {
  const out = await bash('date +%s%3N')
  const parsed = parseInt((out || '').trim(), 10)
  return Number.isFinite(parsed) ? parsed : null
}

// Workflow-start epoch-ms, captured once, for the shadow-reviewer mechanism's
// `workflow_wall_time_ms` field (TCK-20260904-SHADOW-REVIEWER-LOGGING) -- distinct from
// `startTs` (an ISO string, used for run-record start_ts) and from any per-phase `captureTs()`
// call. Read-only downstream; never mutated after this point.
const workflowStartMs = await captureEpochMs()
```
**Do NOT touch:** the existing `captureTs()` function body or its call sites (9 existing
`const <phase>Ts = await captureTs()` sites per `test_step0_ts_orchestrator.py`'s own coverage
list) — `captureEpochMs()` is additive, never a replacement. Do not touch `startTs`/`scopeTs` (the
existing ISO-string run-start value used by `writeMonitoring()`/the run record) — `workflowStartMs`
is a separate, epoch-ms-typed value used only by this ticket's new shadow emission calls.
**Verify:** a static-shape assertion in `tests/tools/test_shadow_reviewer_call_site.py` (new test,
not separately named in test_plan.md — folded into the fail-open/env-gate shape test) confirming
`captureEpochMs` is defined exactly once, after `captureTs`, and `workflowStartMs` is captured
exactly once, before the Investigate phase begins.

### Step 4 — Wire the Architecture-Verify shadow call site
**Files:** `.claude/workflows/implement-ticket.js`
**Change:** Insert a new block immediately after the existing production call
`const archVerify = await agent(...)` closes (confirmed this spans `implement-ticket.js:992-1009`)
and **before** the existing `if (archVerify.verdict !== 'APPROVED') {` check at `:1011` — this
placement is deliberate: it never sits between any existing `writeSidecar()`→`agent()` pair (so
`test_sidecar_bash_write_precedes_each_covered_agent_call`'s adjacency strings are untouched), and
it runs unconditionally on `archVerify.verdict` (so a production failure vs. success never gates
whether the shadow sample gets logged — maximizing coverage of "every review-eligible run," per AC
#1), while structurally guaranteeing the shadow verdict is never read by the `if` block that follows
it (satisfying the "candidate-only failure must never trigger `pushEvent(..., 'failed', ...)`"
constraint by construction, not by a conditional check).

Two fixes applied here after architecture-review of an earlier draft of this plan:
(1) **Exception isolation** — the entire `if (archShadowWindow && archShadowWindow.window_open) { ... }`
body (the `agent()` call, every read of its `.verdict`/`.violations`/`.summary`, and the
event-emission `bash()` call) is wrapped in one JS `try { ... } catch (e) { }` that swallows any
exception and does nothing. Without this, a thrown error from the candidate model call (API error,
timeout, or any other JS exception — not just a bad verdict) would propagate up and abort the whole
phase/workflow, which is strictly worse than the `pushEvent(...,'failed',...)` scenario this ticket
exists to keep advisory-only. (2) **Injection-safe payload** — the free-text, model-generated
`archVerifyShadow.summary`/`.verdict` fields are no longer interpolated as separate double-quoted
argv elements into the `python3 -c "..."` template literal (a `"`, `` ` ``, or `$()` inside
model-generated text could break out of the intended argv boundary). Instead, following this
codebase's own existing convention for passing structured/free-text data through a `bash()`-invoked
Python one-liner — `writeMonitoring`'s `--data '<json>'` pattern
(`implement-ticket.js:387/390: record_events.py --data '<final JSON array>'`) — all fields are
assembled into one JSON object in JS, shell-single-quote-escaped
(`payload.replace(/'/g, "'\\''")`), and passed as ONE single-quoted argv element
(`sys.argv[1]`), which the Python side parses with `json.loads()` and unpacks via
`emit_shadow_reviewer_event(**json.loads(sys.argv[1]))` — matching that function's existing
keyword-only signature (Step 2) unchanged.

```js
  // ─── Shadow candidate reviewer (advisory, TCK-20260904-SHADOW-REVIEWER-LOGGING) ──────────────
  // Runs a candidate model (claude-fable-5-1) against the SAME diff/evidence the production
  // architecture-reviewer just judged, purely for logging -- this block never reads or writes
  // archVerify.verdict, and nothing below it reads this block's own verdict. Gated by
  // SHADOW_REVIEWER_LOGGING_ENABLED=1 AND a bounded per-reviewer sample window
  // (tools/agent-monitoring/shadow_reviewer_window.py::is_shadow_window_open) -- a run outside the
  // window makes zero extra model calls. Fail-open at every level -- shell (`2>/dev/null || true`),
  // Python (`try/except Exception: pass`), AND this entire JS block (`try/catch`) -- because the
  // shadow candidate path is advisory-only and must never propagate ANY failure (API error,
  // timeout, thrown exception -- not just a bad verdict) to the production gate outcome, same
  // convention as SHADOW_CONTEXT_PACKET_ENABLED (INFRA-299).
  const archShadowWindowOutput = await bash(
    `if [ "$SHADOW_REVIEWER_LOGGING_ENABLED" = "1" ]; then python3 tools/agent-monitoring/shadow_reviewer_window.py "architecture-reviewer" "${tid}" 2>/dev/null; fi`
  )
  let archShadowWindow = null
  const archShadowWindowMarker = (archShadowWindowOutput || '').indexOf('SHADOW_WINDOW_JSON:')
  if (archShadowWindowMarker !== -1) {
    try { archShadowWindow = JSON.parse(archShadowWindowOutput.slice(archShadowWindowMarker + 'SHADOW_WINDOW_JSON:'.length).trim()) }
    catch (e) { archShadowWindow = null }
  }

  if (archShadowWindow && archShadowWindow.window_open) {
    // Advisory-only fail-open: nothing in this block -- including agent() throwing on an API
    // error/timeout, or any other exception -- may ever propagate to the enclosing
    // Architecture-Verify phase or its production gate outcome.
    try {
      const archShadowSeq = archShadowWindow.shadow_seq
      const archShadowStartMs = await captureEpochMs()
      await writeSidecar(archShadowSeq, 'Architecture-Verify', 'architecture-reviewer-shadow')
      const archVerifyShadow = await agent(
        `Post-implementation architecture verification for ticket ${tid}.

Files changed: ${implementation.files_changed.join(', ')}

Deterministic static-check results (tools/gate_checks/architecture_reviewer_static.py::run_architecture_checks, already run against the files above):
${archCheckResults !== null ? JSON.stringify(archCheckResults) : 'UNPARSEABLE — treat as inconclusive, do not silently pass'}

This is a narrow verification, not a full re-review. The plan was already judged APPROVED in the pre-Implement Review phase — do not re-litigate strategic/tactical boundary soundness or abstraction-premature-ness here. Your job:
1. For each FAIL item above, read the actual file/line cited and decide: real violation, or false positive (state which, and why).
2. For each SKIP item, note it as unchecked (not clean) — do not treat a SKIP as a passing result.
3. Address any confirmed real violation by describing what must change, or explain why it's a false positive.

Return: APPROVED (no confirmed real violations) / NEEDS_CHANGES (fixable violations confirmed) / BLOCKED (fundamental conflict),
violations (empty if APPROVED), summary (one sentence: verdict + key reason, ≤200 chars),
verified_by (list which findings came from the static script vs. independent judgment, e.g. ["static:architecture_reviewer_static", "llm"]).`,
        { label: 'architecture-verify-shadow', schema: ARCH_VERIFY_SCHEMA, agentType: 'architecture-reviewer', model: 'claude-fable-5-1' }
      )
      const archShadowEndMs = await captureEpochMs()

      const archShadowPayload = JSON.stringify({
        run_id: tid,
        seq: archShadowSeq,
        phase: 'Architecture-Verify',
        agent: 'architecture-reviewer-shadow',
        summary: (archVerifyShadow.summary || '').toString().slice(0, 200),
        candidate_model: 'claude-fable-5-1',
        candidate_verdict: archVerifyShadow.verdict,
        candidate_violations_count: archVerifyShadow.violations.length,
        candidate_wall_time_ms: archShadowEndMs - archShadowStartMs,
        workflow_wall_time_ms: archShadowEndMs - workflowStartMs,
      })
      // Single-quote-escape for safe embedding as ONE single-quoted argv element -- avoids
      // interpolating free-text, model-generated fields (summary/verdict) as separate
      // double-quoted argv pieces, which a `"`, backtick, or `$()` in model output could break out of.
      const archShadowPayloadEscaped = archShadowPayload.replace(/'/g, "'\\''")

      await bash(
        `timeout 15s python3 -c "
import sys, json
sys.path.insert(0, 'tools/agent-monitoring')
from shadow_reviewer_events import emit_shadow_reviewer_event
try:
    emit_shadow_reviewer_event(**json.loads(sys.argv[1]))
except Exception:
    pass
" '${archShadowPayloadEscaped}' 2>/dev/null || true`
      )
    } catch (e) {
      // Fail-open: swallow any exception from the shadow candidate path (agent() throwing on an
      // API error/timeout, JSON encoding, etc.) -- it must never propagate to the production gate.
    }
  }

```
This is inserted directly before the existing `if (archVerify.verdict !== 'APPROVED') {` line.
**Do NOT touch:** `archVerify`, the `if (archVerify.verdict !== 'APPROVED')` block, either
`pushEvent('Architecture-Verify', ...)` call, `ARCH_VERIFY_SCHEMA`, `archCheckResults`/
`archCheckOutput`, or the `tier !== 'hotfix'` guard wrapping the whole phase (the shadow block
inherits it for free by living inside the same `if (tier !== 'hotfix') { ... }` body — do not
duplicate that tier check).
**Verify:** `test_architecture_verify_shadow_call_emits_distinct_joinable_event`,
`test_candidate_only_architecture_verify_failure_does_not_trigger_gate_failure`,
`test_shadow_reviewer_seq_never_collides_with_real_phase_seq`,
`test_shadow_reviewer_call_site_is_fail_open_and_env_gated` (all in
`tests/tools/test_shadow_reviewer_call_site.py` — this test now also covers the JS-level
`try/catch` wrapping and the single-JSON-argv-payload escaping, in addition to the shell/Python-level
fail-open it already covered), plus
`test_sidecar_bash_write_precedes_each_covered_agent_call` (Step 6) and
`test_ts_capture_bash_precedes_each_covered_agent_call` (unmodified — confirm it still passes).

### Step 5 — Wire the Security-Review shadow call site
**Files:** `.claude/workflows/implement-ticket.js`
**Change:** Same structural pattern as Step 4, inserted immediately after the existing production
call `const securityReview = await agent(...)` closes (confirmed `implement-ticket.js:1364-1376`)
and before the existing `if (securityReview.verdict !== 'APPROVED') {` check at `:1378`. Reuses the
production's own `SECURITY_REVIEW_SCHEMA` (no `verified_by` field, unlike architecture-reviewer's
schema — confirmed by reading `implement-ticket.js:1350-1358`) and the same file-list-based prompt
text (no `archCheckResults`-equivalent static-check payload exists for Security-Review, confirmed by
reading the production prompt at `:1366-1373` — it has none to reuse).

Same two fixes as Step 4, applied here too (this call site is more security-sensitive than most,
since it is the Security-Review call site itself): (1) **exception isolation** — the whole
`if (securityShadowWindow && securityShadowWindow.window_open) { ... }` body is wrapped in a JS
`try/catch` that swallows any exception (API error, timeout, or otherwise) and does nothing, so the
candidate model call can never crash/abort the phase. (2) **injection-safe payload** — the free-text
`securityReviewShadow.summary`/`.verdict` fields are assembled into one JS object, `JSON.stringify`'d,
shell-single-quote-escaped (`payload.replace(/'/g, "'\\''")`), and passed as ONE single-quoted argv
element to the `python3 -c "..."` one-liner, which parses it with `json.loads(sys.argv[1])` and calls
`emit_shadow_reviewer_event(**json.loads(sys.argv[1]))` — the same pattern as `writeMonitoring`'s
existing `--data '<json>'` convention (`implement-ticket.js:387/390`), and the same shape as Step 4's
own payload, just with `phase='Security-Review'`/`agent='security-reviewer-shadow'`.

```js
  // ─── Shadow candidate reviewer (advisory, TCK-20260904-SHADOW-REVIEWER-LOGGING) ──────────────
  // Same mechanism as the Architecture-Verify shadow block above -- see its comment for the full
  // rationale. This block never reads or writes securityReview.verdict. Fail-open at every level --
  // shell (`2>/dev/null || true`), Python (`try/except Exception: pass`), AND this entire JS block
  // (`try/catch`) -- the shadow candidate path is advisory-only and must never propagate ANY
  // failure to the production gate outcome.
  const securityShadowWindowOutput = await bash(
    `if [ "$SHADOW_REVIEWER_LOGGING_ENABLED" = "1" ]; then python3 tools/agent-monitoring/shadow_reviewer_window.py "security-reviewer" "${tid}" 2>/dev/null; fi`
  )
  let securityShadowWindow = null
  const securityShadowWindowMarker = (securityShadowWindowOutput || '').indexOf('SHADOW_WINDOW_JSON:')
  if (securityShadowWindowMarker !== -1) {
    try { securityShadowWindow = JSON.parse(securityShadowWindowOutput.slice(securityShadowWindowMarker + 'SHADOW_WINDOW_JSON:'.length).trim()) }
    catch (e) { securityShadowWindow = null }
  }

  if (securityShadowWindow && securityShadowWindow.window_open) {
    // Advisory-only fail-open: nothing in this block -- including agent() throwing on an API
    // error/timeout, or any other exception -- may ever propagate to the enclosing
    // Security-Review phase or its production gate outcome.
    try {
      const securityShadowSeq = securityShadowWindow.shadow_seq
      const securityShadowStartMs = await captureEpochMs()
      await writeSidecar(securityShadowSeq, 'Security-Review', 'security-reviewer-shadow')
      const securityReviewShadow = await agent(
        `Security review for ticket ${tid}.

Read:
- ${ticketInfo.ticket_path}
- Files changed: ${implementation.files_changed.join(', ')}

This ticket is tagged \`security\` (its frontmatter tags include \`security\`, or suggested_skills includes /security-review). Review the actual diff/changed files for: injection, unsafe deserialization, path traversal, subprocess/command injection, secrets-in-code, raw-domain-model API exposure.

Return: APPROVED / NEEDS_CHANGES (fixable violations) / BLOCKED (fundamental vulnerability),
violations (empty if APPROVED), summary (one sentence: verdict + key reason, ≤200 chars).`,
        { label: 'security-review-shadow', schema: SECURITY_REVIEW_SCHEMA, agentType: 'security-reviewer', model: 'claude-fable-5-1' }
      )
      const securityShadowEndMs = await captureEpochMs()

      const securityShadowPayload = JSON.stringify({
        run_id: tid,
        seq: securityShadowSeq,
        phase: 'Security-Review',
        agent: 'security-reviewer-shadow',
        summary: (securityReviewShadow.summary || '').toString().slice(0, 200),
        candidate_model: 'claude-fable-5-1',
        candidate_verdict: securityReviewShadow.verdict,
        candidate_violations_count: securityReviewShadow.violations.length,
        candidate_wall_time_ms: securityShadowEndMs - securityShadowStartMs,
        workflow_wall_time_ms: securityShadowEndMs - workflowStartMs,
      })
      // Single-quote-escape for safe embedding as ONE single-quoted argv element -- avoids
      // interpolating free-text, model-generated fields (summary/verdict) as separate
      // double-quoted argv pieces, which a `"`, backtick, or `$()` in model output could break out of.
      const securityShadowPayloadEscaped = securityShadowPayload.replace(/'/g, "'\\''")

      await bash(
        `timeout 15s python3 -c "
import sys, json
sys.path.insert(0, 'tools/agent-monitoring')
from shadow_reviewer_events import emit_shadow_reviewer_event
try:
    emit_shadow_reviewer_event(**json.loads(sys.argv[1]))
except Exception:
    pass
" '${securityShadowPayloadEscaped}' 2>/dev/null || true`
      )
    } catch (e) {
      // Fail-open: swallow any exception from the shadow candidate path (agent() throwing on an
      // API error/timeout, JSON encoding, etc.) -- it must never propagate to the production gate.
    }
  }

```
This is inserted directly before the existing `if (securityReview.verdict !== 'APPROVED') {` line.
**Do NOT touch:** the `if ((ticketInfo.tags && ...) || (ticketInfo.suggested_skills && ...))` trigger
condition at `:1347-1348` (the shadow block lives inside this same `if`, inheriting the trigger for
free — do not widen or duplicate the condition), `securityReview`, either
`pushEvent('Security-Review', ...)` call, `SECURITY_REVIEW_SCHEMA`. Do not add a shadow call to the
pre-Implement Review phase's separate architecture-reviewer call against `plan.md`
(`implement-ticket.js:618-644`) — explicitly out of scope, different call site/input shape.
**Verify:** `test_security_review_shadow_call_emits_distinct_joinable_event`,
`test_candidate_only_security_review_failure_does_not_trigger_gate_failure`, plus a static test
asserting the Security-Review trigger condition text at `:1347-1348` is byte-for-byte unchanged
(Anti-Drift Test Guard, `tests/tools/test_shadow_reviewer_call_site.py`) — this file's
fail-open/env-gate coverage (`test_shadow_reviewer_call_site_is_fail_open_and_env_gated`) now also
exercises the JS-level `try/catch` and single-JSON-argv-payload escaping at this call site, mirroring
Step 4's.

### Step 6 — Update `test_current_run_sidecar_orchestrator.py` (11 → 13, second regex for shadow sites)
**Files:** `tests/tools/test_current_run_sidecar_orchestrator.py`
**Change:** `test_plan.md` describes this as "the regex count... changes from `== 11` to `== 13`,"
but the existing regex at line 106
(`r"await writeSidecar\(events\.length \+ 1 \+ seqOffset, '[^']+', '[^']+'\)"`) can only ever match
the **positive**-seq expression. This plan's Steps 4/5 deliberately use `writeSidecar(archShadowSeq,
...)`/`writeSidecar(securityShadowSeq, ...)` — a **different, negative-seq** expression, on purpose
(see Judgment Call 5: reusing the positive expression would collide with the enclosing production
phase's own `(run_id, seq)` bucket, corrupting cost attribution — the exact Anti-Drift Hazard this
ticket must not introduce). Reconciling this: the existing `== 11` assertion at line 106 **stays
unchanged at `== 11`** (no existing production site's expression changes, so its own count is
stable), and a **new, second** assertion is added for the two shadow sites' own distinct literal
form:
```python
    # Two additional writeSidecar() calls for the shadow-reviewer mechanism
    # (TCK-20260904-SHADOW-REVIEWER-LOGGING) use a NEGATIVE seq expression on purpose — reusing
    # the positive events.length + 1 + seqOffset idiom here would collide with the enclosing
    # production phase's own (run_id, seq) tools.jsonl bucket. Counted separately from the
    # positive-seq assertion above.
    assert len(re.findall(
        r"await writeSidecar\((archShadowSeq|securityShadowSeq), '[^']+', '[^']+-shadow'\)", source
    )) == 2
```
`_COVERED_SITE_ADJACENCY` (lines 55-67) gains 2 new literal entries for the shadow
`writeSidecar()`→`agent()` pairs, appended to the list (order matches the file's phase order, so
these two go after the `'Security-Review'` entry at line 64, before `'Verify'` at line 65). Indented
at 6 spaces, not the 2/4-space indent an earlier draft used — both shadow blocks now live one level
deeper, inside the `try { ... }` that Steps 4/5's exception-isolation fix wraps around them:
```python
    "      await writeSidecar(archShadowSeq, 'Architecture-Verify', 'architecture-reviewer-shadow')\n      const archVerifyShadow = await agent(",
    "      await writeSidecar(securityShadowSeq, 'Security-Review', 'security-reviewer-shadow')\n      const securityReviewShadow = await agent(",
```
The module-level docstring (lines 1-29) gets one clause noting the 2 new shadow sites use a
distinct negative-seq form (not part of the original 11) — keeps the file's own self-documentation
accurate for the next reader.
**Do NOT touch:** any of the other assertions in this file (`test_no_step_0b_agent_prompt_sidecar_text_remains`,
`test_finalize_call_site_still_registers_sidecar`, `test_writeMonitoring_call_has_no_preceding_sidecar_write`,
`test_scope_phase_has_sidecar_coverage`, `test_new_ticket_branch_seq_offset_is_zero_not_null`) — none
of these are affected by this ticket's changes; a failure in any of them after this edit is a real
placement mistake, not something to loosen.
**Verify:** `pytest tests/tools/test_current_run_sidecar_orchestrator.py -v` — every existing test
plus the new `== 2` assertion, all green.

### Step 7 — Confirm `test_step0_ts_orchestrator.py` needs no edits
**Files:** none changed; `tests/tools/test_step0_ts_orchestrator.py` read-only verification step.
**Change:** No code change. This step exists to make explicit that Steps 4/5's placement (shadow
block inserted strictly *after* each existing `captureTs()`→`writeSidecar()`→`agent()` triple, never
spliced between its three lines) leaves every substring this file asserts (lines 40-49) fully
intact — confirmed by direct read of the file: it has no total-occurrence-count assertion analogous
to Step 6's regex counts, only substring-presence checks.
**Do NOT touch:** this file. If a run of it fails after Steps 4/5 land, that is real signal that the
shadow block was spliced in the wrong place (between an existing triple's lines) — fix the
placement, do not edit this test to route around it.
**Verify:** `pytest tests/tools/test_step0_ts_orchestrator.py -v` — passes unmodified.

### Step 8 — New test file `tests/tools/test_shadow_reviewer_call_site.py`
**Files:** `tests/tools/test_shadow_reviewer_call_site.py` (new)
**Change:** Mirrors `tests/tools/test_shadow_packet_call_site.py`'s established shape (static
`Path.read_text()` parsing of `implement-ticket.js`, plus direct in-process calls against the new
Python modules for behavioral coverage — same technique that file's own item 4 and items 11 use).
Covers, per test_plan.md's New Tests Required section:
- `test_architecture_verify_shadow_call_emits_distinct_joinable_event` /
  `test_security_review_shadow_call_emits_distinct_joinable_event`: call
  `shadow_reviewer_events.emit_shadow_reviewer_event()` directly against a `tmp_path` events file
  with a fixed `(run_id, phase)`, and separately assert a production-shaped record with the same
  `run_id`/`phase` but positive `seq` — confirm both are readable from the same file, joinable on
  `(run_id, phase)`, and mechanically distinguishable by `seq` sign and `agent` suffix.
- `test_candidate_only_architecture_verify_failure_does_not_trigger_gate_failure` /
  `..._security_review_...`: static-shape assertion that the shadow `agent()` call's result variable
  (`archVerifyShadow`/`securityReviewShadow`) never appears inside the production `if
  (archVerify.verdict !== 'APPROVED')` / `if (securityReview.verdict !== 'APPROVED')` block bodies —
  i.e. grep the exact text of each `if` block (from `if (` to its matching close, located via the
  existing `pushEvent(..., 'failed', ...)` / `return {` landmarks already in the file) and assert
  `archVerifyShadow`/`securityReviewShadow` is absent from it.
- `test_shadow_reviewer_seq_never_collides_with_real_phase_seq`: behavioral — call
  `shadow_reviewer_window.compute_shadow_seq()` across a range of `prior_count` values for both
  reviewers and assert every result is `<= -100`, and that the two reviewers' ranges never overlap
  for any `prior_count` pair in a reasonable bound (mirrors
  `test_shadow_packet_call_site.py::test_shadow_event_seq_never_collides_with_any_real_phase_seq`'s
  shape).
- `test_shadow_reviewer_call_site_is_fail_open_and_env_gated`: static — both new blocks are gated on
  `SHADOW_REVIEWER_LOGGING_ENABLED`, wrapped in `timeout`, end in `2>/dev/null || true`, and the
  inner Python is wrapped in `try/except Exception: pass`.
- `test_candidate_call_cost_and_timing_labeled_separately_from_production` (from Step 2): synthetic
  `tools.jsonl` rows split across a production positive-seq group and a shadow negative-seq group;
  assert `_compute_candidate_tool_stats()` / `compute_cost_proxy_score()` produce two independent,
  never-summed figures.
- A static assertion that the Security-Review trigger condition text (`:1347-1348`) is unchanged
  (Anti-Drift Test Guard), and one asserting the pre-Implement Review phase's architecture-reviewer
  call site (`:618-644`, `Review` phase) gains no shadow block (scope-creep guard).
**Do NOT touch:** `tests/tools/test_shadow_packet_call_site.py` (a different call site's own
regression suite — read for pattern reuse only, never edited by this ticket).
**Verify:** `pytest tests/tools/test_shadow_reviewer_call_site.py -v` — all new tests pass.

### Step 9 — New test file `tests/tools/test_shadow_reviewer_window.py`
**Files:** `tests/tools/test_shadow_reviewer_window.py` (new)
**Change:** Pure-function unit tests against Step 1's module, using a `tmp_path`-based
`agent-monitoring/data/<week>/events.jsonl` fixture (never the real corpus):
- `test_shadow_window_closed_skips_candidate_call`: seed `count_prior_shadow_samples()`'s backing
  fixture with `>= max_samples` prior `architecture-reviewer-shadow` rows; assert
  `is_shadow_window_open('architecture-reviewer', 50)` returns `False`; with `< max_samples` rows,
  returns `True`. Also assert (via `tests/tools/test_shadow_reviewer_call_site.py`'s static check,
  cross-referenced here) that the `bash()` gate in Steps 4/5 is structured so `window_open: false`
  in the parsed JSON causes the surrounding `if` block — and therefore the candidate `agent()` call
  — to be skipped entirely.
- `test_shadow_window_thresholds_are_independent_per_reviewer`: seed 60
  `architecture-reviewer-shadow` rows (window closed) and 2 `security-reviewer-shadow` rows (window
  open); assert `is_shadow_window_open('architecture-reviewer', 50)` is `False` while
  `is_shadow_window_open('security-reviewer', 10)` is `True` in the same fixture — directly guards
  the asymmetric-accumulation-rate risk from investigation.md.
- A test asserting `count_prior_shadow_samples_for_run()` is correctly scoped to one `run_id` (two
  different `run_id`s each with shadow rows must not influence each other's count), distinct from
  `count_prior_shadow_samples()`'s cross-run_id scope.
**Do NOT touch:** the real `agent-monitoring/data/` corpus — every test in this file must use a
`tmp_path` fixture / monkeypatched `DATA_DIR`, never read or write the live directory.
**Verify:** `pytest tests/tools/test_shadow_reviewer_window.py -v` — all pass.

### Step 10 — Update `docs/agent-monitoring/schema.md`
**Files:** `docs/agent-monitoring/schema.md`
**Change:** Two additions, mirroring the existing "Retrieval-event field family" section's
established shape (confirmed at `schema.md:300-365`):
1. A new `### Shadow-reviewer-event field family (additive)` section (placed directly after the
   existing Retrieval-event field family section, before the `---` at line 367), documenting the 8
   new fields (table matching `SHADOW_REVIEWER_EVENT_FIELDS`), and a Provenance paragraph explaining:
   the `run_id` is always the real `tid` (never a synthetic prefix, unlike the two
   standalone-invocation Phase-3 retrieval modules); `seq` is always `<= -100`
   (`SHADOW_SEQ_BASE`-derived, disjoint from both the real per-phase range and INFRA-299's own
   `-1..-5` shadow-packet range); `phase` is reused verbatim from the production phase (`Architecture-Verify`
   / `Security-Review` — both already canonical in `vocabulary.WORKFLOW_PHASES["implement-ticket"]`,
   confirmed at `vocabulary.py:21-24`, so **phase never shows as drift**, only `agent` does — this is
   a deliberate difference from the shadow-packet precedent, where `phase="Retrieval"` is itself
   non-canonical); `agent` is `architecture-reviewer-shadow` / `security-reviewer-shadow` (neither in
   `WORKFLOW_AGENTS["implement-ticket"]`, confirmed at `vocabulary.py:40-51` — expected to show under
   `compute_drift_report()`'s "Non-canonical agent values," same non-gating precedent as
   `context-packet-wrapper`).
2. Extend the existing `seq` field-table exception note at `schema.md:174` (currently: "the advisory
   context-packet shadow-call site... emits `seq <= 0` values") to also name the shadow-reviewer
   mechanism and its own `<= -100` floor, so a reader of that single row learns about both
   exceptions rather than only the first.
**Do NOT touch:** the existing Retrieval-event field family table/text itself, `RETRIEVAL_EVENT_FIELDS`'s
documentation, or any `phase`/`agent` vocabulary table for a workflow other than `implement-ticket`.
**Verify:** `tools/gate_checks/doc_staleness_check.py::check_doc_staleness()` (per the doc-staleness
gate that already runs in Document-Update/Verify) sees this path in `files_changed` and returns
`PASS` for this behavior-changing diff — mirrors `test_shadow_packet_call_site.py::test_docs_path_present_in_the_same_diff`'s
own check.

### Step 11 — New parity ledger entry `INFRA-409`
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** Append one new entry after `INFRA-408` (confirmed the last entry in the file, ending at
`docs/parity_ledger/infrastructure.yaml`'s tail — read in full to confirm no `INFRA-409` already
exists), mirroring `INFRA-299`'s shape/level of detail (confirmed at `infrastructure.yaml:7005-7045`):
id, exact call-site line references (Architecture-Verify + Security-Review, both in
`implement-ticket.js`), env-var gate name (`SHADOW_REVIEWER_LOGGING_ENABLED`), the negative-seq
formula and its disjointness proof (summarizing Judgment Call 5), the candidate model
(`claude-fable-5-1`), the bounded-window thresholds (50 / 10) and their source (478/14 real
historical event counts), `status: verified`, `priority: P1` (matches this ticket's own P1
priority), `test_path` listing all 3 new/updated test files from Steps 6/8/9, `divergence_note:
null`, `support_boundary` noting this is agent-orchestration/monitoring-pipeline tooling only, same
category as INFRA-299/402-408.
**Do NOT touch:** `INFRA-299`'s own entry text (it documents a different call site — Investigate
phase shadow-packet — and stays valid/unmodified; this ticket's own investigation confirmed its
line-number citations don't shift).
**Verify:** `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"`
parses cleanly (schema validity), and the ticket's own Parity phase (`parity-updater` agent, not
part of this plan) cross-references this entry against `files_changed` at Implement time.

## Scope Guards

Explicit list of what this plan must NOT touch, restated from the ticket's Out of Scope and
investigation.md's Anti-Drift Hazards:

- **Never let a candidate-only verdict reach `pushEvent(..., 'failed', ...)`, `writeMonitoring(...)`,
  or an early `return`.** Both shadow blocks (Steps 4/5) are inserted *before* the production `if`
  check and never reference `archVerify`/`securityReview`'s own verdict variables at all — this is a
  structural guarantee, not a conditional one.
- **Never fold the shadow call's own tool activity into the production call's `(run_id, seq)`
  bucket.** Enforced by the negative-seq `writeSidecar()` call in Steps 4/5 — never reuse
  `events.length + 1 + seqOffset` for a shadow site.
- **Never widen the Security-Review trigger condition** (`implement-ticket.js:1347-1348`). Step 5's
  shadow block lives *inside* the existing `if` body, inheriting the trigger — it is never
  duplicated or loosened.
- **Never add a shadow call to the pre-Implement Review phase's architecture-reviewer call**
  (`:618-644`, against prose `plan.md`) — a different call site/input shape, explicitly out of scope.
- **Never build the promotion/"enough evidence" decision milestone.** `is_shadow_window_open()` is a
  pure stop-condition gate — it never compares the two verdicts against each other or decides
  anything about promoting the candidate model to production.
- **Never widen `RETRIEVAL_EVENT_FIELDS`** (`tools/retrieval_events.py`) to accommodate this
  ticket's new fields — they live in a wholly separate `SHADOW_REVIEWER_EVENT_FIELDS` frozenset in a
  new module (Step 2).
- **Never change `pushEvent()`'s call signature** (`phaseLabel, agentName, status, summary, ts,
  toolCallCount, reasonCode`) — the new `candidate_*` fields are carried exclusively by the separate
  `emit_shadow_reviewer_event()` write path, never smuggled through `pushEvent`.
- **Never recalibrate `cost_proxy.compute_cost_proxy_score()`'s weights** (`W_BASH=0.001,
  W_AGENT=50, W_EDIT=1`) — reused verbatim.
- **Never fix the pre-existing `EVENTS_FILE` bug** at `implement-ticket.js:597` (Investigate-phase
  shadow-packet mechanism) in this ticket — Judgment Call 2 above; file a separate hotfix ticket.
- **Never touch `tests/tools/test_shadow_packet_call_site.py`** — a different call site's own
  regression suite, read for pattern reuse only.

## Dependency Map

- Step 1 (`shadow_reviewer_window.py`) and Step 2 (`shadow_reviewer_events.py`) are independent of
  each other — both are pure new modules with no shared code, can be implemented/tested in either
  order or in parallel.
- Step 3 (`captureEpochMs`/`workflowStartMs`) has no dependency on Steps 1-2; it is pure JS.
- Step 4 (Architecture-Verify wiring) depends on Steps 1, 2, and 3 (calls
  `shadow_reviewer_window.py` and `shadow_reviewer_events.py` via `bash()`, and uses
  `captureEpochMs()`/`workflowStartMs`).
- Step 5 (Security-Review wiring) depends on the same Steps 1/2/3 as Step 4, but is otherwise
  independent of Step 4 itself (a different call site, different `if` guard) — can be implemented
  before or after Step 4.
- Step 6 (sidecar test update) depends on Steps 4 and 5 both being wired (needs the real literal
  `writeSidecar(archShadowSeq, ...)`/`writeSidecar(securityShadowSeq, ...)` text to exist in the
  file to assert against).
- Step 7 (confirm no edit needed) depends on Steps 4/5 for its own verification, but requires no
  code change itself.
- Step 8 (new call-site test file) depends on Steps 1-5 all being complete (asserts against the real
  wired JS text plus the real Python modules).
- Step 9 (window unit tests) depends only on Step 1.
- Step 10 (schema.md) and Step 11 (infrastructure.yaml) depend on Steps 1-5 being finalized (cite
  exact line numbers/field names) but have no code dependency on each other — can be done in either
  order, ideally last so line-number citations are stable.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: both models' verdicts recorded as distinct joinable records for the same (run_id, phase, diff), for both reviewers | Steps 2, 4, 5 (phase reused verbatim from production; `agent` suffix + negative `seq` distinguish; `emit_shadow_reviewer_event()` writes to the same `events.jsonl`) | `test_architecture_verify_shadow_call_emits_distinct_joinable_event`, `test_security_review_shadow_call_emits_distinct_joinable_event` (Step 8) |
| AC #2: workflow gate outcome driven exclusively by production verdict; candidate-only failure never triggers `pushEvent('failed')`/early return | Steps 4, 5 (shadow block placed before and structurally decoupled from the production `if` check) | `test_candidate_only_architecture_verify_failure_does_not_trigger_gate_failure`, `test_candidate_only_security_review_failure_does_not_trigger_gate_failure` (Step 8) |
| AC #3: candidate call count, review-phase wall time, workflow wall time, and cost_proxy_score recorded and labeled by which reviewer produced them | Step 2 (`candidate_tool_call_count`, `candidate_cost_proxy_score`, `candidate_wall_time_ms`, `workflow_wall_time_ms` fields, computed per-`(run_id, seq)` and attached to a record whose `agent` field already names the reviewer) | `test_candidate_call_cost_and_timing_labeled_separately_from_production` (Step 8) |
| AC #4: bounded window/sample condition a run can check to skip the candidate call once closed; sidecar-adjacency test still passes | Step 1 (`is_shadow_window_open`), Steps 4/5 (gate the candidate call on it) | `test_shadow_window_closed_skips_candidate_call`, `test_shadow_window_thresholds_are_independent_per_reviewer` (Step 9); `test_sidecar_bash_write_precedes_each_covered_agent_call` (Step 6) |

## Anti-Drift Notes

- **`emit_retrieval_event()`'s field-restriction guard is a hard wall, not a style choice** — do not
  attempt to route the new `candidate_*` fields through it even for convenience; it will raise
  `ValueError` (`retrieval_events.py:117-121`) and the correct fix is the separate module built in
  Step 2, not widening `RETRIEVAL_EVENT_FIELDS`.
- **`compute_tool_stats()`/`tool_call_count`/`cost_proxy_score` auto-attachment is a `record_events.py::main()`-only
  behavior** — `emit_retrieval_event()` (and, by the same reasoning, this ticket's own
  `emit_shadow_reviewer_event()`) never gets this for free; Step 2's inline
  `_compute_candidate_tool_stats()` exists specifically because this auto-attachment does not happen
  automatically for a direct `write_lines()` call outside `record_events.py`'s CLI path.
- **The two reviewers' shadow ranges are asymmetric on purpose** (50 vs. 10 sample-window; 100 vs.
  200 seq base) — do not "simplify" this to one shared constant; the 478-vs-14 real historical event
  count split is the empirical reason both numbers differ, confirmed in this planning session, not
  a stylistic choice.
- **The sidecar test's `== 11` assertion must NOT be changed to `== 13`** by widening the existing
  regex to also match the new sites — the two new sites are deliberately NOT the same expression
  shape as the original 11 (see Judgment Call 5 / Step 6); a correct implementation adds a *second*,
  separate assertion for exactly 2 shadow-site occurrences, keeping the original regex/count
  unchanged at 11.
- **Placement of both shadow blocks matters mechanically, not just stylistically**: inserted after
  the production `agent()` call closes and before the production `if (...verdict !== 'APPROVED')`
  check — never between an existing `writeSidecar()`/`captureTs()`/`agent()` triple (would break
  Step 7's existing test), and never inside the production `if` block itself (would break AC #2's
  isolation guarantee).
- **A failing test after this ticket's changes (Steps 6-9) is real signal**, per CLAUDE.md's Gate
  Integrity rule — do not loosen an assertion to make it pass; fix the placement/logic instead.

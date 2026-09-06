---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-SHADOW-REVIEWER-LOGGING
artifact_type: test_plan
tags: [ai, agent-monitoring, security]
---

# Test Plan — TCK-20260904-SHADOW-REVIEWER-LOGGING

## Regression Surface

Existing tests that must keep passing after this change — all are static, raw-source-text-parsing
tests against `.claude/workflows/implement-ticket.js` and `tools/agent-monitoring/*`; none execute
the JS file itself (no JS test runner exists for `.claude/workflows/*.js` in this repo).

**Unit (agent-monitoring tooling):**
- `tests/tools/test_current_run_sidecar_orchestrator.py` — will need direct edits in this ticket
  (see New Tests Required); every *other* assertion in the file (Step 0b prompt-text absence, etc.)
  must still pass unchanged.
- `tests/tools/test_step0_ts_orchestrator.py` — must pass **unmodified**. Confirmed by reading it in
  full: `test_ts_capture_bash_precedes_each_covered_agent_call` only asserts specific
  `captureTs()`→`writeSidecar()`→`agent()` triple substrings exist (including the existing
  `Architecture-Verify`/`Security-Review` ones) — it has no total-occurrence-count assertion, so new
  shadow-call blocks appended *after* the existing production triples (not spliced between
  `captureTs`/`writeSidecar`/`agent()`) leave every existing substring match intact.
- `tests/tools/test_architecture_reviewer_static.py` — unaffected; tests `run_architecture_checks()`
  itself, not the workflow call sites.
- `tests/agent-monitoring/test_record_events.py` (or wherever `record_events.py`'s
  `validate_record()`/`compute_tool_stats()` are covered) — must still pass; a new additive field
  family must not violate `record_events.REQUIRED`'s base-7-field contract (mirrors
  `RETRIEVAL_EVENT_FIELDS`'s own "never replace or narrow the base REQUIRED set" precedent).
- `tests/tools/test_shadow_packet_call_site.py` (INFRA-299's own regression suite) — unaffected;
  covers the Investigate-phase shadow-packet block only, a different call site.
- Any test covering `tools/agent-monitoring/cost_proxy.py::compute_cost_proxy_score()` — must still
  pass unmodified; this ticket reuses the function, does not change its formula.
- `tests/tools/test_agent_monitoring_schema*.py` (whichever file asserts `docs/agent-monitoring/
  schema.md`'s field tables/enums match `vocabulary.py`/`record_events.py`) — must still pass; the
  new additive field family/phase-agent literals must be documented in a way that doesn't break any
  existing schema/vocabulary cross-check.

**Integration:**
- Any `tests/tools/test_*.py` exercising `implement-ticket.js`'s Architecture-Verify/Security-Review
  phase gate logic via static source parsing (verdict-triggers-early-return pattern) — confirm none
  currently hardcodes an assumption that only one `agent()` call exists per phase.

**Arena-combat:** none — this ticket touches no `src/` simulation code.

## New Tests Required

- **`test_sidecar_bash_write_precedes_each_covered_agent_call` — updated in place** (not a new test,
  but a required edit per the ticket's own scope)
  - Category: unit (static source-text parsing)
  - What it verifies: the regex count of `await writeSidecar(events.length + 1 + seqOffset, ...)`
    occurrences changes from `== 11` to `== 13` (10 pre-existing two-line sites + Finalize + 2 new
    shadow sites for Architecture-Verify-shadow and Security-Review-shadow), and
    `_COVERED_SITE_ADJACENCY` gains 2 new adjacency strings for the new
    `writeSidecar(...)`-then-`agent(...)` shadow call pairs, in the exact literal form they appear in
    the real file.
  - Where it lives: `tests/tools/test_current_run_sidecar_orchestrator.py` (existing file, edited)

- **Shadow verdict recorded as a distinct joinable record — architecture-reviewer**
  - Name: `test_architecture_verify_shadow_call_emits_distinct_joinable_event`
  - Category: unit
  - What it verifies: given a fixed `(run_id, phase='Architecture-Verify', diff)`, the shadow
    emission function writes a record sharing that `run_id`/`phase`, distinguishable from the
    production `pushEvent()` record by a `seq <= 0` (or equivalent negative/marker convention) and by
    carrying the new `candidate_model`/`candidate_verdict` additive fields — i.e., both records are
    joinable (same `run_id`+`phase`) yet mechanically distinguishable as "production" vs "candidate."
  - Where it lives: `tests/tools/test_shadow_reviewer_call_site.py` (new file, mirroring
    `test_shadow_packet_call_site.py`'s existing shape/conventions for this ticket's mechanism)

- **Shadow verdict recorded as a distinct joinable record — security-reviewer**
  - Name: `test_security_review_shadow_call_emits_distinct_joinable_event`
  - Category: unit
  - What it verifies: same shape as above, scoped to the Security-Review call site, including that it
    only fires when the production Security-Review phase itself fires (tag-gated).
  - Where it lives: `tests/tools/test_shadow_reviewer_call_site.py`

- **Candidate-only failure never affects the gate outcome — Architecture-Verify (AC #2, explicit)**
  - Name: `test_candidate_only_architecture_verify_failure_does_not_trigger_gate_failure`
  - Category: unit / architecture guard
  - What it verifies: stubs a scenario where the candidate model's verdict is `NEEDS_CHANGES`/
    `BLOCKED` while the production verdict is `APPROVED` — asserts `pushEvent(...)` is never called
    with `status: 'failed'` attributable to the candidate's verdict, `writeMonitoring()` is never
    called with the candidate's verdict value, and no early `return` happens on the candidate's
    verdict alone. Since `implement-ticket.js` is not executed by a JS test runner in this repo, this
    is necessarily a static-source-shape test (asserting the candidate `agent()` call's result is
    never passed into the `if (archVerify.verdict !== 'APPROVED')` gate-branch, and is consumed only
    by the shadow-emission call) — mirroring how `test_sidecar_bash_write_precedes_each_covered_agent_call`
    already verifies control-flow-adjacent JS shape via raw text/regex rather than execution.
  - Where it lives: `tests/tools/test_shadow_reviewer_call_site.py`

- **Candidate-only failure never affects the gate outcome — Security-Review (AC #2, explicit)**
  - Name: `test_candidate_only_security_review_failure_does_not_trigger_gate_failure`
  - Category: unit / architecture guard
  - What it verifies: same shape as above, scoped to the Security-Review call site's
    `if (securityReview.verdict !== 'APPROVED')` gate-branch.
  - Where it lives: `tests/tools/test_shadow_reviewer_call_site.py`

- **Bounded sample window — skip behavior when closed (AC #4, explicit)**
  - Name: `test_shadow_window_closed_skips_candidate_call`
  - Category: unit
  - What it verifies: the new window-check function (e.g. `shadow_reviewer_window.py::
    is_shadow_window_open(reviewer, max_samples)`) returns `False` once a reviewer's prior
    shadow-event count meets/exceeds its own threshold, and that `implement-ticket.js`'s candidate
    `bash()`/`agent()` block is conditioned on this check (static-shape assertion that the check
    precedes the candidate `agent()` call, mirroring how `SHADOW_CONTEXT_PACKET_ENABLED` gates
    INFRA-299's block).
  - Where it lives: `tests/tools/test_shadow_reviewer_window.py` (new file) for the pure-function
    unit test; a static-shape assertion in `tests/tools/test_shadow_reviewer_call_site.py` for the
    gating-precedes-call-site check.

- **Bounded sample window — independent per-reviewer thresholds (AC #4 + Risk #5)**
  - Name: `test_shadow_window_thresholds_are_independent_per_reviewer`
  - Category: unit
  - What it verifies: `architecture-reviewer`'s window closing does not affect
    `security-reviewer`'s own independent count/threshold, and vice versa — directly guards against
    a single shared counter silently starving the slower-accumulating `security-reviewer` sample
    (the asymmetric-trigger risk flagged in investigation.md).
  - Where it lives: `tests/tools/test_shadow_reviewer_window.py`

- **Cost/timing attribution correctness (AC #3, explicit)**
  - Name: `test_candidate_call_cost_and_timing_labeled_separately_from_production`
  - Category: unit
  - What it verifies: given synthetic `tools.jsonl` rows split across two distinct `(run_id, seq)`
    groups (one for the production call's seq, one for the shadow call's negative seq),
    `compute_cost_proxy_score()`/`compute_tool_stats()` (reused unmodified) produce two independent
    scores, and the shadow emission record carries its own `candidate_cost_proxy_score`/
    `candidate_wall_time_ms` fields distinct from the production event's `cost_proxy_score` — i.e.,
    the two are never summed or overwritten into one figure.
  - Where it lives: `tests/tools/test_shadow_reviewer_call_site.py` or
    `tests/agent-monitoring/test_cost_proxy.py` (co-locate with whichever already covers
    `compute_cost_proxy_score()`'s grouping behavior)

- **Sample window / negative-seq disjointness from the real per-phase range**
  - Name: `test_shadow_reviewer_seq_never_collides_with_real_phase_seq`
  - Category: unit
  - What it verifies: the shadow-reviewer negative-seq computation is provably `<= 0` (mirroring
    INFRA-299's `seq = -(1 + prior_shadow_count)` proof — real per-phase seq is always `>= 1`), and
    is scoped independently per reviewer type so `architecture-reviewer`'s and `security-reviewer`'s
    shadow counters never collide with each other either.
  - Where it lives: `tests/tools/test_shadow_reviewer_call_site.py`

- **Fail-open behavior (mirrors INFRA-299's own tested contract)**
  - Name: `test_shadow_reviewer_call_site_is_fail_open_and_env_gated`
  - Category: unit (static-shape)
  - What it verifies: the new `bash()` block(s) are gated behind an explicit env var (strict string
    equality, off by default), wrapped in `timeout <n>s`, and fail open at both the shell level
    (`2>/dev/null || true`) and the Python level (`try/except: pass`) — same shape as INFRA-299's own
    tested contract.
  - Where it lives: `tests/tools/test_shadow_reviewer_call_site.py`

## Scoped Pytest Commands

```
pytest tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_step0_ts_orchestrator.py \
  tests/tools/test_shadow_reviewer_call_site.py tests/tools/test_shadow_reviewer_window.py \
  tests/tools/test_shadow_packet_call_site.py tests/tools/test_architecture_reviewer_static.py -v
```

```
pytest tests/agent-monitoring/ -v -k "cost_proxy or record_events or schema"
```

Never `pytest tests/` — scope to the `tools/agent-monitoring/` + `.claude/workflows/*.js`-adjacent
static-test domain listed above.

## Anti-Drift Test Guards

- A test asserting `Security-Review`'s trigger condition (`ticketInfo.tags.includes('security') ||
  ticketInfo.suggested_skills.includes('/security-review')` at :1347-1348) is untouched by this
  ticket — guards against silently widening/narrowing when the shadow call is threaded through.
- A test asserting the pre-Implement Review phase's architecture-reviewer call (plan.md review,
  :618-644) gains **no** shadow call site — guards against scope creep into the explicitly
  out-of-scope third architecture-reviewer call site.
- A test asserting `pushEvent()`'s call signature (`phaseLabel, agentName, status, summary, ts,
  toolCallCount, reasonCode`) is unchanged — guards against smuggling shadow-specific fields into the
  base event schema instead of the new additive family, which would violate the base-7-field
  contract every other consumer (`record_events.validate_record()`, `vocabulary.py`,
  `generate_retro.py`) already relies on.
- A test asserting `tools/agent-monitoring/cost_proxy.py::compute_cost_proxy_score()`'s formula
  (`W_BASH=0.001, W_AGENT=50, W_EDIT=1`) is byte-for-byte unchanged — this ticket must reuse, never
  recalibrate, the existing weights.
- A test asserting the two reviewers' shadow calls do not share a single sample-window counter (see
  New Tests Required above) — the single most likely silent regression given the asymmetric
  accumulation-rate risk already flagged in investigation.md.

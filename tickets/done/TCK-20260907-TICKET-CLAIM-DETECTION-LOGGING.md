---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING
phase: done
date: 2026-09-07
tags: [ai, agent-monitoring, workflows]
---

# TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING

## Title
Ticket-claim detection logging — Experiment Specification + log-only instrumentation (roadmap item 14, Bucket B)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Roadmap item 14 (`docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` row 14,
sourced from `workflow_reliability_epic.md`'s M2) is a Bucket-B (experiment/measurement) item. Per
the epic doc, it "becomes an Experiment Specification (Hypothesis/Baseline/Method/Metrics/Exit/
Kill Criteria) before any ticket is written" and the deliverable is **log-only** instrumentation
that flags when two sessions touch the same ticket ID within a short window — explicitly no
blocking, no lock file, just a detection signal, with a 30-day decision gate on whether to later
build an actual claim lock.

**Tier/scope decision and reasoning**: this ticket covers two things, not one — (1) writing the
Experiment Specification document itself, matching item 13's
(`agent_evaluation_foundation_experiment.md`) structural template exactly (Why this is an
experiment / Hypothesis / Baseline / Method / Metrics / Exit criteria / Kill criteria / Out of
scope / References), and (2) implementing the actual log-only detection instrumentation the spec's
own Method section describes, since "add log-only instrumentation... no blocking, no lock file,
just a detection signal" is itself a small, concrete, buildable piece of work, not just planning
prose. This is scoped `standard` (not `hotfix`) because it requires real design decisions with more
than one valid shape (where the detection check runs, what "short window" means, where the
detection record is written) that a self-evident one-line fix would not — it needs an
investigation/plan pass, not just an edit.

**Investigation findings that shape this scope**:
- `tools/agent_codex_pilot_executor/claims.py` (`acquire_claim()`/`terminalize_claim()`) is
  **confirmed unrelated prior art, not reusable infrastructure for this ticket.** It is a per-ticket
  Linux advisory-lock (`fcntl.flock`) claim/terminal-state marker scoped to a caller-injected
  `scratch_root` for the Codex pilot-execution harness's synthetic/disposable pilot-lifecycle
  fixtures (`tools/agent_codex_pilot_executor/simulation.py`'s `simulate_pilot()`) — it actively
  *blocks* a second claim (`ClaimRefusedError: unfinished claim exists for {ticket_id}`), which is
  exactly the "build a lock" behavior this roadmap item's kill-criteria decision gate says not to
  build yet. It operates on a disposable scratch directory, never on the real `tickets/inprogress/`
  directory or a real multi-session Claude Code working tree. Do not extend or reuse it here.
- The real, already-available session-identity signal for "two sessions touching the same ticket
  ID" is the session-scoped run sidecar: `implement-ticket.js`'s `writeSidecar()` (line ~274) writes
  both the legacy unscoped `.claude/current_run` and a session-scoped
  `.claude/current_run.<CLAUDE_CODE_SESSION_ID>` file, each containing `{run_id, seq, phase, agent,
  execution_id, provider}` — `run_id` is the ticket ID for `implement-ticket` runs. `CLAUDE_CODE_SESSION_ID`
  is confirmed (via `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`) to be a stable per-session
  identifier already used to disambiguate concurrent sessions. This is the real signal the Method
  section must name — no new identity mechanism needs to be invented.
- `agent-monitoring/data/*/runs.jsonl` / `events.jsonl` (see `docs/agent-monitoring/schema.md`) have
  no `session_id` field of their own — `run_id` there is the ticket ID, not a session identifier.
  The sidecar files (not the JSONL shards) are the only place a session identifier currently exists
  in written-to-disk form.
- No historical incident evidence of a real double-claim was found in `tickets/done/`,
  `agent-monitoring/retro/`, or `tickets/inprogress/` — this repo does run many concurrent worktrees
  today (8 active worktrees confirmed via `git worktree list` at scoping time, each on its own
  branch), so the *opportunity* for a double-claim is real and ongoing, but no report of one
  actually happening was found. This is the Baseline section's "zero known historical incidents"
  starting point — consistent with, not contradicted by, real concurrency already existing.
- This item is already tracked at epic level by `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC`
  (`EPIC_SCOPED`, held deliberately without child tickets/specs). That epic's own acceptance
  criteria require any future session picking up one of its Bucket-B items to link the resulting
  Experiment Specification/ticket back to it — this ticket does that (see Related Tickets). This is
  expected, non-blocking follow-through, not duplicate or conflicting work.

## Scope
- Write the Experiment Specification document at
  `docs/plans/agent_infrastructure/ai_first_hardening_epics/ticket_claim_detection_experiment.md`,
  matching `agent_evaluation_foundation_experiment.md`'s section shape: Why this is an experiment /
  Hypothesis / Baseline / Method / Metrics / Exit criteria / Kill criteria / Out of scope /
  References — populated with the real findings above (claims.py non-relevance, the sidecar signal,
  the zero-incident baseline), not placeholder text.
- Implement log-only detection instrumentation that:
  - Reads the real, already-available signal: session-scoped `.claude/current_run.<SESSION_ID>`
    sidecar files (or their `run_id`/ticket-ID contents) — not a new identity mechanism.
  - Flags (does not block) when it detects more than one distinct active session touching the same
    `run_id`/ticket ID within a short time window.
  - Writes a detection record to a durable, inspectable log location for later analysis (exact
    location/format is an implementation-phase decision — see Assumptions/Open Questions — but it
    must not silently mutate or overwrite `tickets/inprogress/`, `runs.jsonl`, or `events.jsonl`
    schemas without a ledger/schema-doc update).
  - Never raises, blocks, refuses, or otherwise changes `implement-ticket.js`'s control flow —
    a detection is observability only.
- Wire the instrumentation into a real invocation point in the existing workflow (e.g. the Scope
  phase of `implement-ticket.js`, where a `run_id`/ticket ID is first established) so it runs on
  real, not synthetic, sessions.
- Add tests proving: (a) two concurrent sessions writing session-scoped sidecars for the same
  ticket ID produce a detection log entry, (b) a single session touching a ticket ID produces no
  detection, (c) the instrumentation never raises/blocks regardless of detection outcome.

## Out of Scope
- Building an actual ticket-claim lock (blocking behavior, refusal, or any lock file) — explicitly
  deferred per the epic's own kill-criteria decision gate; only revisit if real double-claim
  incidents are observed within 30 days of this instrumentation going live.
- Modifying, extending, or reusing `tools/agent_codex_pilot_executor/claims.py` — confirmed a
  structurally different, unrelated mechanism (Codex pilot-execution scratch-root claim lock, not
  general session/ticket-claim detection); do not couple this work to it.
- Running the 30-day observation window itself or making the "build a lock" vs. "keep as
  documented convention" decision — that decision explicitly happens *after* this instrumentation
  has been live for a full quarter (per the epic doc), not as part of shipping the instrumentation.
- Any change to `.claude/current_run` sidecar *write* semantics (session-scoping already shipped
  under `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`) — this ticket only *reads* the existing sidecar
  signal, it does not change how/where sidecars are written.
- Phase-level workflow resume design (roadmap item 15 / `workflow_reliability_epic.md` M3) — a
  separate Bucket-B item, not part of this ticket.
- Extending detection coverage to `implement-epic.js` or `create-tickets.js` — scope this to
  `implement-ticket.js` first (where the sidecar mechanism is fullest-featured and best evidenced);
  note as a follow-on if found necessary during implementation, don't silently widen scope here.

## Acceptance Criteria
- [x] `docs/plans/agent_infrastructure/ai_first_hardening_epics/ticket_claim_detection_experiment.md`
      exists with all of: Why this is an experiment, Hypothesis, Baseline, Method, Metrics, Exit
      criteria, Kill criteria, Out of scope, References — matching
      `agent_evaluation_foundation_experiment.md`'s section shape and rigor.
- [x] The Method section names the real `CLAUDE_CODE_SESSION_ID` / session-scoped
      `.claude/current_run.<SESSION_ID>` sidecar mechanism as the detection signal, not an invented
      one.
- [x] Log-only detection instrumentation is implemented and wired into a real
      `implement-ticket.js` invocation point (cite the exact line/function in Implementation Notes
      once landed).
- [x] A test demonstrates two concurrent sessions (real or simulated session-scoped sidecar files)
      touching the same ticket ID produce exactly one detection log entry; a test demonstrates a
      single session produces zero detection log entries.
- [x] A test demonstrates the instrumentation cannot raise an exception that interrupts
      `implement-ticket.js`'s control flow (e.g. malformed/missing sidecar file is handled
      gracefully, logged or skipped, never propagated).
- [x] No blocking behavior, refusal, or lock file is introduced anywhere in this change (verified
      by code review against the diff, and stated explicitly in Completion Summary).
- [x] `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC`'s `## Related Tickets` section is updated to
      link this ticket, per that epic's own acceptance criterion requiring future Bucket-B work to
      cross-reference back to it. (Confirmed already present, lines 79-82, added by a concurrent
      scoping pass — no edit was needed; verified per plan.md Step 7.)

## Related Tickets
- `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC` (in progress, `EPIC_SCOPED`) — the tracking epic
  this Bucket-B item is enumerated under; this ticket is the real work that epic anticipated.
- `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` (done) — shipped the session-scoped
  `.claude/current_run.<SESSION_ID>` sidecar mechanism this ticket's detection signal depends on.
- `TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE` (done) — closed the last sidecar-consumer straggler
  gap (`workflow_reliability_epic.md` M1), confirming the sidecar mechanism is now consistently
  session-scoped across all known consumers as of this ticket's scoping date.
- `TCK-20260731-CODEX-PILOT-EXECUTOR` (done) — origin of `tools/agent_codex_pilot_executor/claims.py`,
  investigated and ruled out as reusable prior art for this ticket (see Request Summary).

## Related Docs
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/workflow_reliability_epic.md` (M2) —
  the source spec this ticket implements.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/agent_evaluation_foundation_experiment.md` —
  structural template for the Experiment Specification this ticket must produce.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` (row 14) — inventory entry
  and Horizon-1 placement.
- `docs/agent-monitoring/schema.md` — confirms `runs.jsonl`/`events.jsonl` carry no `session_id`
  field; the sidecar file is the only existing session-identity artifact.
- `docs/guidelines/subsystem_ownership_lifecycle.md` — referenced by the epic doc for this
  subsystem's ownership/lifecycle row once instrumentation ships.

## Related Stored Artifacts
None found covering this exact scope. `stored_artifacts/TCK-20260731-CODEX-PILOT-EXECUTOR/` and
`stored_artifacts/TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE/` (if present) are adjacent prior
investigations worth reading during the Investigate phase for mechanism detail, not directly
reusable as this ticket's own artifacts.

## Related Code Areas
- `.claude/workflows/implement-ticket.js` (`writeSidecar()` ~line 274, Scope-phase section ~line
  34-75) — the real invocation point this instrumentation wires into.
- `tools/agent_codex_pilot_executor/claims.py` — investigated, ruled out as unrelated (Codex
  pilot-execution scratch-root lock, not general session/ticket-claim detection).
- `tools/agent-monitoring/` — likely home for the new detection-logging module, following this
  directory's existing conventions (`record_events.py`, `record_run.py` as write-path precedent).
- `docs/agent-monitoring/schema.md` — update if the detection log introduces any new
  schema-documented field or file.

## Assumptions / Open Questions
- **Layer choice**: `layer: ai` was chosen to match the parent epic doc's own frontmatter
  (`workflow_reliability_epic.md`, `agent_evaluation_foundation_experiment.md` both use `layer: ai`)
  since this is Claude agent/orchestration tooling, not gameplay simulation. `observability` was
  considered (agent-monitoring/telemetry) but `ai` was preferred for consistency with the epic
  grouping this ticket belongs to. If this proves wrong during implementation, re-derive rather than
  force-fit.
- **Detection log location/format is not yet decided** — Scope deliberately leaves this open for
  the Investigate/Plan phase. Candidates to evaluate: a new dedicated JSONL
  (`agent-monitoring/data/YYYY-Www/claim_detections.jsonl` or similar, kept separate from the
  schema-validated `runs`/`events`/`tools` shards to avoid coupling an experimental signal to
  production schema validation) vs. a structured log line. Whichever is chosen must be documented
  in `docs/agent-monitoring/schema.md` if it lives under `agent-monitoring/data/`.
- **"Short window" duration is not yet defined** — the source spec says "within a short window" but
  does not name a number. Plan phase must pick a concrete value (e.g. sidecar file still present /
  session still active) with a stated rationale, since detection must not fire on stale/leftover
  sidecar files from crashed sessions that were never cleaned up.
  **Resolved during Plan/Implement**: 900 seconds (15 minutes), a module-level constant
  (`CLAIM_DETECTION_WINDOW_SECONDS` in `tools/agent-monitoring/ticket_claim_detection.py`) —
  deliberately far below `post_tool_hook.py`'s unrelated 24-hour prune threshold (which answers a
  different question: safe-to-delete, not currently-active). **The rationale carries a real,
  accepted tradeoff, not just the chosen number**: the window is measured against the *other*
  session's sidecar's last phase-transition write, not its continuous activity — `writeSidecar()`
  only updates mtime once per phase transition, and real Implement/Investigate/Plan-phase
  dispatches have been observed running 20-30+ minutes with no sidecar write in between. A session
  mid-way through one such long phase can therefore look stale to this check well before it is
  actually done — a genuine false negative, not a hypothetical edge case. This is not fixed by
  widening the window (a wider window would misflag an already-finished session as still active
  instead, since nothing in a sidecar distinguishes "ended cleanly" from "mid-phase") — it is
  accepted and documented in full in
  `docs/plans/agent_infrastructure/ai_first_hardening_epics/ticket_claim_detection_experiment.md`'s
  Known Limitations section and in `docs/agent-monitoring/schema.md`'s `claim_detections` section.
- Assumes `implement-ticket.js`'s Scope phase (where `run_id`/ticket ID is first established) is
  the correct single wiring point for a first pass — extending to `implement-epic.js`/
  `create-tickets.js` is explicitly out of scope for this ticket (see Out of Scope) but may be a
  natural follow-on if this proves valuable.
- If wrong about any of the above narrowing this scope incorrectly (e.g. if `claims.py` actually
  does need extending, or if a session-identity signal other than `CLAUDE_CODE_SESSION_ID` turns
  out to be more appropriate), that would invalidate this ticket's Scope section and should trigger
  a re-scope, not a silent workaround during implementation.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING/plan.md`,
with one small deviation (see below).

1. **Experiment Specification** written at
   `docs/plans/agent_infrastructure/ai_first_hardening_epics/ticket_claim_detection_experiment.md`,
   matching `agent_evaluation_foundation_experiment.md`'s section shape (Why this is an
   experiment / Hypothesis / Baseline / Method / Metrics / Exit criteria / Kill criteria / Known
   Limitations / Out of scope / References), including the honest false-negative caveat: the
   900-second window is measured against the *other* session's sidecar's last phase-transition
   write, not continuous activity, so a session mid-way through one long phase can look stale
   before it is actually done — documented as an accepted, un-fixed limitation, not silently
   patched by widening the window.
2. **Detection module**: `tools/agent-monitoring/ticket_claim_detection.py` (new). Core function
   `_find_concurrent_claimants(tid, *, claude_dir, own_session_id, window_seconds, now)` globs
   `.claude/current_run.*`, excludes the current session's own scoped file and the legacy unscoped
   `current_run` file, and requires BOTH `run_id == tid` AND `now - mtime <= window_seconds` for a
   match. `check_and_log()` wraps this, writes one JSON record (if any match) to
   `agent-monitoring/data/<iso-week>/claim_detections.jsonl` via the shared
   `writer.py::write_line()` primitive, and never raises (outer `try/except Exception: return
   None`). `CLAIM_DETECTION_WINDOW_SECONDS = 900` is a module-level constant, per plan — not
   widened.
3. **Wiring**: one line inserted into `.claude/workflows/implement-ticket.js` immediately after
   `const tid = ticketInfo.ticket_id` (confirmed still at line 213 in the live file at
   implementation time — unchanged from the plan's citation) and before the
   `TCK-20260730-CLAUDE-EXECUTION-IDENTITY` comment block: a single fail-open
   `await bash(\`python3 tools/agent-monitoring/ticket_claim_detection.py "${tid}" 2>/dev/null || true\`)`
   call, always-on (no env-var gate, per plan's decision — negligible-cost local glob/JSON-parse,
   unlike the shadow-reviewer-logging precedent's gated extra LLM call).
4. **Tests**: `tests/tools/test_ticket_claim_detection.py` (new, 11 tests, imports the module
   directly and drives it against `tmp_path` fixtures — never the real `.claude/` or
   `agent-monitoring/data/`), plus one new static-source-string test added to
   `tests/tools/test_current_run_sidecar_orchestrator.py`
   (`test_scope_phase_wires_detection_call_at_tid_confirmation_point`) asserting the call site sits
   strictly between `const tid = ticketInfo.ticket_id` and `writeSidecar`'s own definition.
5. **Schema doc**: new top-level `## claim_detections (agent-monitoring/data/YYYY-Www/claim_detections.jsonl)`
   section added to `docs/agent-monitoring/schema.md`, inserted immediately before `## Join
   Example` (the file had shifted since planning due to concurrent unrelated edits from sibling
   tickets — re-located the insertion point by anchor text, not a cached line number, per
   Anti-Drift Notes).
6. **Parity ledger**: added `INFRA-411` to `docs/parity_ledger/infrastructure.yaml` via the
   sanctioned `tools/parity_ledger_writer.py::write_entry()` (schema-validating write path, not a
   raw YAML edit) — re-ran the max-ID grep fresh immediately before writing and confirmed
   `INFRA-410` was still the max (no drift since planning), so `INFRA-411` was correct as planned.
7. **Epic cross-reference**: re-read `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC.md`'s Related
   Tickets section — the bullet linking this ticket was already present (lines 79-82), added by a
   concurrent scoping pass. No edit was needed or made.

**Deviation from plan.md's literal code listing**: added one line,
`target.parent.mkdir(parents=True, exist_ok=True)`, immediately before the `write_line(...)` call
in `check_and_log()`. `writer.py::write_line()` acquires its `O_CREAT|O_EXCL` lock *before* its own
internal `mkdir`, so the parent week-directory must already exist for lock acquisition to succeed
— this is the same pre-`write_line()` `mkdir` convention `record_run.py` and `post_tool_hook.py`
already both follow for their own targets (confirmed by reading their source). Without this line,
the first-ever write in a new ISO week fails silently (write_line() returns False, diagnostic
logged, no exception) — caught by
`test_two_concurrent_session_sidecars_for_same_ticket_produce_one_detection` and
`test_detection_record_written_to_dedicated_jsonl_not_runs_or_events` failing against a fresh
`tmp_path` during Test phase. This is a bug-fix-during-implementation matching an established
convention, not a scope change — noted in `plan.md`'s Deviations section per CLAUDE.md's
traceability rule.

## Test Summary

Ran (via `.venv/bin/python3 -m pytest`, since bare `python3` in this sandbox lacks `pydantic`):

```
pytest tests/tools/test_ticket_claim_detection.py tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_post_tool_hook.py tests/tools/test_epic_create_tickets_sidecar_orchestrator.py tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py -v
```

**Result: 68 passed, 0 failed.**

- `test_ticket_claim_detection.py`: 11/11 passed (two concurrent sessions → exactly one detection;
  single session → zero; malformed/missing-field sidecar never raises; grep-based
  never-raises/never-refuses architecture guard; stale (30-min) sidecar does not false-positive;
  own-session sidecar excluded; null-sentinel sidecar never counted; detection lands in
  `claim_detections.jsonl` only, never `runs.jsonl`/`events.jsonl`; direct
  `_find_concurrent_claimants` unit test proving both conditions — `run_id` match AND window
  match — are required together; empty-`tid` no-op case).
- `test_current_run_sidecar_orchestrator.py`: all 22 cases passed, including the new
  `test_scope_phase_wires_detection_call_at_tid_confirmation_point` and, critically, the two
  pre-existing regression guards this ticket was warned not to disturb —
  `test_sidecar_bash_write_precedes_each_covered_agent_call` (all 13
  `writeSidecar()`→`agent()` adjacency pairs unchanged) and
  `test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure` — both still
  pass unmodified, confirming the new call site (well before `writeSidecar`'s own definition) does
  not disturb either.
- `test_post_tool_hook.py`, `test_epic_create_tickets_sidecar_orchestrator.py`,
  `test_settings_json_edit_write_hook_sidecar_scope.py`: all passed unmodified, confirming zero
  interference with the other sidecar consumers/writers and zero scope creep into
  `implement-epic.js`/`create-tickets.js`.

## Files Changed

- `docs/plans/agent_infrastructure/ai_first_hardening_epics/ticket_claim_detection_experiment.md` (new)
- `tools/agent-monitoring/ticket_claim_detection.py` (new)
- `.claude/workflows/implement-ticket.js` (edited — one call site added after `const tid = ...`)
- `tests/tools/test_ticket_claim_detection.py` (new)
- `tests/tools/test_current_run_sidecar_orchestrator.py` (edited — one new test case added)
- `docs/agent-monitoring/schema.md` (edited — new `claim_detections` top-level section added)
- `docs/parity_ledger/infrastructure.yaml` (edited — new `INFRA-411` entry, via
  `tools/parity_ledger_writer.py::write_entry()`)
- `staging_artifacts/TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING/plan.md` (edited — Deviations
  section appended, documenting the `mkdir`-before-`write_line()` fix)
- `tickets/inprogress/TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING.md` (this file — Implementation
  Notes/Test Summary/Files Changed/Completion Summary/Status/Acceptance Criteria updated)
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/workflow_reliability_epic.md`
  (Document-Update phase — M2 section header, body, Acceptance-signal bullet, and References
  updated to reflect the shipped instrumentation, matching the doc's own M1/M3 shipped-status
  convention)

No edit was made to `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC.md` (Related Tickets link
already present), `.gitattributes` (existing glob already covers the new file), or
`staging_artifacts/.../investigation.md`/`test_plan.md` (both remained accurate as written during
this ticket's own Investigate phase; no rewrite was needed during Implement).

Not this ticket's own edits, pre-existing in this shared worktree from the just-Finalized sibling
ticket `TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN`, left staged/uncommitted per this
batch's own convention of accumulating commits until the batch closes: `docs/REGISTRY.yaml`,
`docs/ai/phase_resume_validation_rule_decision.md`.

## Completion Summary

Implemented the Experiment Specification document and the log-only ticket-claim detection
instrumentation it describes, per the approved plan (1 review round). The detection module
(`tools/agent-monitoring/ticket_claim_detection.py`) is read-only over `.claude/current_run.*`
sidecars, wired into `implement-ticket.js`'s Scope phase right after the ticket ID is confirmed
real, and writes to a brand-new dedicated `claim_detections.jsonl` shard — never into
`runs.jsonl`/`events.jsonl`, never blocking, never raising, and never touching sidecar write
semantics. **No blocking behavior, refusal, or lock file was introduced anywhere in this change**
— confirmed both by the module's own design (no exception type analogous to `ClaimRefusedError`,
every failure path returns `None`) and by a dedicated architecture-guard test grepping for its
absence. All 68 scoped tests pass, including the 13-pair `writeSidecar()`→`agent()` adjacency
regression guard, confirmed unmodified. The documented false-negative gap (mtime only advances on
phase transitions, not continuously) is an accepted, evidence-grounded limitation, not a defect —
recorded in the Experiment Specification's Known Limitations section and in the schema doc, and
deliberately not "fixed" by widening the 900-second window, per explicit out-of-scope instruction.

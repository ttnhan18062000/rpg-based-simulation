---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-CODEX-REPLAY-PROOF
artifact_type: investigation
tags: [ai, workflows, agent-monitoring, process-improvement]
---

# Investigation — TCK-20260721-CODEX-REPLAY-PROOF

## Current Behavior

### The workflow to be "replayed": `.claude/workflows/implement-ticket.js` (1301 lines, read in full)

This is a JS orchestrator script with no JS test runner in this repo (confirmed — no `.js` test
files under `tests/`, and `tests/tools/test_monitoring_bypass_fix.py`'s own docstring states this
explicitly: "The workflow files are never executed (no JS test runner exists in this repo for
`.claude/workflows/*.js`)"). Its 11 phases (`implement-ticket.js:4-16`) are: Scope, Investigate,
Plan, Review, Implement, Architecture-Verify, Test, Parity, Security-Review (conditional), Verify,
Finalize.

Two structurally distinct kinds of logic are interleaved in this file:

1. **LLM-driven `agent()` calls** — 10 of them (`ticket-scoper`, `investigator`, `planner`,
   `architecture-reviewer` ×2, `implementer`, `test-scoper`, `parity-updater`,
   `security-reviewer` (conditional), `done-checker`, `finalizer`, plus the internal
   `monitoring-write` agent). Each takes a large free-text prompt and returns structured JSON
   validated against an inline JSON-schema (`TICKET_SCHEMA` line 55, `REVIEW_SCHEMA` line 535,
   `IMPL_SCHEMA` line 604, `ARCH_VERIFY_SCHEMA` line 721, `TEST_SCHEMA` line 779, `PARITY_SCHEMA`
   line 919, `SECURITY_REVIEW_SCHEMA` line 1024, `DONE_SCHEMA` line 1074). **These cannot be
   literally replayed without a live LLM** — there is no deterministic way to reproduce an
   `agent()` call's output from its prompt alone.

2. **Deterministic orchestrator-side logic** — branch decisions, event construction, and gate
   invocations, all pure JS/Python with no LLM in the loop:
   - `pushEvent(phase, agent, status, summary, ts, toolCallCount, reasonCode)` (line 207) —
     builds the event record shape written to `agent-monitoring/events.jsonl`.
   - `writeSidecar(seq, phase, agent)` (line 229) and `captureTs()` (line 244) — orchestrator-run
     `bash()` calls, no LLM.
   - Every gate check invoked via `bash('python3 -c "..."')` against a **real, already-tested,
     importable Python module** in `tools/gate_checks/`: `tag_registry.check_tags_registered`
     (line 340), `plan_gate_static.plan_has_unresolved_questions_heading` (line 505),
     `architecture_reviewer_static.run_architecture_checks` (line 709),
     `parity_ledger_scan.find_p0_intersection` (line 906),
     `parity_updater_static.expected_subsystems_for_files` / `cross_reference_touched` (lines
     938, 976), `doc_staleness_check.py` (line 660, invoked as a standalone script, not import),
     `done_checker_static.run_static_precheck` / `classify_checklist_failure` (mirrored by hand
     at line 274, marked "kept in sync by hand") / `clean_data_runs_early` (line 852) /
     `run_finalize_selfcheck` (line 1211) / `check_monitoring_write_recorded` (line 1269).
   - The **branch decisions themselves** (e.g. `if (ticketInfo.conflicts.length > 0) return
     CONFLICTS_DETECTED`, `if (hasUnresolvedQuestions) return NEEDS_HUMAN_INPUT`, `if
     (review.verdict !== 'APPROVED') return ...`, the Security-Review trigger condition line
     1020, the Parity skip-eligibility computation lines 887-888) are inline JS control flow with
     **no separate importable module** — this logic exists only inside `implement-ticket.js`
     itself, the same situation `classifyChecklistFailure` (line 274) already accepted and
     solved by hand-mirroring into a small local re-implementation, with an explicit code comment
     documenting the sync-by-hand precedent.

**Key finding**: the deterministic half of this workflow is already substantially factored into
real, pure, already-unit-tested Python functions under `tools/gate_checks/`. A replay runner can
*genuinely* re-execute this half — by importing and calling the exact same functions the real
orchestrator calls — without needing to run the `.js` file or invoke an LLM. Only the outer
branch-sequencing logic (which phase follows which, given a recorded outcome) needs hand-mirroring,
exactly like `classifyChecklistFailure` already does.

### The 4 forbidden scripts (read in full)

- `tools/agent-monitoring/pre_tool_hook.py` (19 lines) — reads stdin JSON, writes
  `.claude/.tool_start` + `.claude/.current_session_id`. Top-level script, executes on import
  (reads `sys.stdin` at module scope) — cannot be safely imported, only subprocess-invoked.
- `tools/agent-monitoring/post_tool_hook.py` (87 lines) — reads stdin JSON, appends one record to
  `agent-monitoring/tools.jsonl` under `fcntl.flock`. Same top-level-script shape.
- `tools/agent-monitoring/record_run.py` (73 lines) — `argparse` CLI, `--data '<json>'`, appends
  to `agent-monitoring/runs.jsonl`. Callable only via subprocess (has `if __name__ == "__main__"`
  but its `main()` is trivially importable and callable too — **both** paths (subprocess AND
  `from record_run import main`) must be treated as forbidden, not just the subprocess form).
- `tools/agent-monitoring/record_events.py` (152 lines) — same CLI shape, appends to
  `agent-monitoring/events.jsonl`, also imports `cost_proxy.py` and `vocabulary.py` internally
  (those two are *not* forbidden — they're pure read/compute helpers with no write path — a
  replay runner may import them freely).

### `test_post_tool_hook.py` (167 lines, read in full) — isolation technique only

Every test here drives the **real** `post_tool_hook.py` as a subprocess with `cwd=tmp_path`,
because the hook is a top-level script under test *for its own behavior* (file-locking,
sidecar-reading). This is explicitly the wrong precedent to reuse for invoking the hook itself in
this ticket — the ticket's own Assumptions call this out directly, and the ticket text embedded in
this investigation's own instructions repeats the warning. The **only** reusable piece is the
*mechanism*: `subprocess.run([...], cwd=str(tmp_path), ...)` to isolate filesystem side effects.
This ticket's replay runner and its no-mutation snapshot test should use `tmp_path`-style isolation
for the *snapshot mechanism itself* (or run against the real repo tree with a git-status diff, see
Test Plan) — never to redirect an argument into the real hook scripts and call that "isolated."

### `test_monitoring_bypass_fix.py` (122 lines, read in full) — static source-text precedent

Confirms the established, working pattern in this repo for testing a `.js` workflow file's logic
without a JS runtime: `Path.read_text()` on the `.js` file, then `str.find()`/index-ordering
assertions (e.g. "the guard block's `record_run.py` call must appear before its `return {`"). No
execution, ever. This is directly reusable for the required "no subprocess/import call to \[the
4 forbidden scripts\] exists anywhere in the replay runner's own code path" verification — but
applied to the **replay runner's own new Python source file**, not to `implement-ticket.js` (that
file is unchanged by this ticket; nothing in Scope touches it).

### `docs/agent-monitoring/schema.md` (read in full) — why truncated telemetry is insufficient

`events.jsonl`'s `summary` field is capped at 200 chars (line 112, silently re-truncated to
197+"..." by `record_events.py:117-120` if a longer string is passed) and `tools.jsonl`'s
`input_summary` at 120 chars (line 249). Neither field carries: the full `agent()` prompt, the
full structured JSON return value (e.g. `TICKET_SCHEMA`'s `ticket_path`/`tags`/`suggested_skills`,
or `IMPL_SCHEMA`'s full `files_changed` list and `implementation_summary` paragraph), or which
specific branch was taken and why. This confirms the ticket's own Assumptions/AC: telemetry alone
cannot drive a replay; the fixture must carry the actual recorded phase input/output data.

### Codex capability matrix / monitoring-writer decision / orchestration-contract ADR (all read in full)

- `docs/ai/codex_capability_matrix.md` — Codex has 10 verified lifecycle hooks including
  `PostToolUse`/`PreToolUse`, and (§6, "Deferred") explicitly names a future
  `CODEX-REPLAY-PROOF` child ticket as the place to do a stdin-payload-capture experiment — this
  is that child ticket, but its own §6 explicitly did **not** perform that experiment (would
  consume real API usage under the user's account). This ticket's replay proof does not depend on
  or require that deferred experiment; it replays the deterministic orchestrator slice only, no
  live Codex hook payload capture involved.
- `docs/ai/monitoring_writer_decision.md` §2 (lines 91-142) — **already decides** the
  `execution_id = f"{provider}-{ticket_id}-{unix_ts_ms}-{secrets.token_hex(4)}"` format,
  `run_id` retained as display, `ticket_id` promoted to an explicit top-level join field. This is
  a **future schema for the real monitoring writer**, not yet implemented anywhere
  (`tools/agent-monitoring/*.py` unchanged by that ticket, confirmed by its own text: "no
  production monitoring writer path... changes as part of landing this document"). A fixture
  envelope for this ticket may *reference* this shape (e.g. include a `provider: "claude-code"`
  field) for forward-consistency, but must not present it as if it were already the real
  production schema.
- `docs/architecture/agent_orchestration_contract.md` (ADR, status: Proposed, **ticket status:
  DONE** — confirmed via `tickets/done/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.md:18`) — decides
  **Contract Representation and Format: YAML, for human-reviewable definitions, with generated
  Python validation models** (Decided). This ticket's own AC #5 requires evaluating the fixture
  envelope's shape against this decision — see Risks/Open Questions below for the concrete
  recommendation. **The ADR ticket is DONE, not merely approved-pending** — this ticket's own
  blocking Assumption ("if that ADR is not yet approved when this ticket starts, this ticket is
  blocked") does **not** apply; the dependency is satisfied.

### `src/engine/replay_manager.py` / `replay_buffer.py` / `replay_sink.py` — confirmed different domain

Read all three. `ReplayManager` orchestrates non-blocking, bounded, chunked persistence of
`TraceEvent` simulation-tick objects (`ReplayBuffer.record(event: TraceEvent)`,
`ReplaySink.persist_chunk` writing `chunk_NNNN.json` files under a run directory, governed by "M6
Law"/"M7 Law" from the Mechanics Bible / Engine Contracts). This is **entity/world game-tick state
replay** for simulation forensics — a completely different domain from Claude/Codex agent-workflow
phase replay. No code, pattern, or API from this module is reusable here. Confirms the ticket's own
Assumption verbatim.

### `agent-monitoring/runs.jsonl` / `events.jsonl` sample rows (read live)

Confirmed real shape matches schema.md exactly. Notably, `TCK-20260721-ORCHESTRATION-CONTRACT-ADR`
(same discovery batch, already `DONE`) has a small, complete, real `events.jsonl` slice (11 events,
seq 1-11, spanning Scope through Finalize, including a genuine gate-failure-then-retry pair: seq 9
`failed`/`dod_condition_failed` followed by seq 10 `ok` at Verify) and a real `runs.jsonl` row. Its
`stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-ADR/` (investigation.md, plan.md,
test_plan.md) and `tickets/done/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.md` are permanent,
already-landed, real files — a strong, ready-made candidate source for "at least one real recorded
fixture set" (see Risks/Open Questions).

## Mechanics / Engine Constraints

Not applicable. This ticket concerns dev-tooling/agent-orchestration infrastructure (a replay
runner and fixture spec for the `implement-ticket` workflow), not simulation engine mechanics. No
chapter of `docs/mechanics/` or contract in `docs/engine/` constrains this work — consistent with
the identical finding in all four sibling `TCK-20260721-*` discovery-batch investigations
(`AGENTS-DIR-DISPOSITION`, `CODEX-CAPABILITY-MATRIX`, `MONITORING-WRITER-DECISION`,
`ORCHESTRATION-CONTRACT-ADR`), and confirmed independently here via `search_docs` (no
mechanics/engine hits for "replay fixture envelope workflow phase") and `graphify query` (returned
only simulation-engine `TraceEvent`/`AuthoritativeState`/`WorldRepository` replay/fixture nodes —
none relevant to agent-workflow replay).

## Parity Ledger Overlap

None. No `docs/parity_ledger/*.yaml` subsystem (substrate, combat_movement, strategic_cognition,
town_resource, progression, social_narrative, world_dynamics, infrastructure) covers
agent-orchestration/dev-tooling decision or proof artifacts. No parity ledger entry needs updating.

## Prior Work

- **`stored_artifacts/TCK-20260721-AGENTS-DIR-DISPOSITION/`, `.../CODEX-CAPABILITY-MATRIX/`,
  `.../MONITORING-WRITER-DECISION/`, `.../ORCHESTRATION-CONTRACT-ADR/`** — same discovery batch,
  all DONE. Establish this batch's evidence-density and containment precedent: exact file:line
  citations, "read in full" verification discipline, explicit "What this doc does not do" closing
  sections. This ticket's deliverables should follow the same discipline, and (per this ticket's
  own child-position in the sequence) explicitly cite all three prior decision docs as inputs, the
  way the ADR ticket cited its own three inputs.
- **`tests/tools/test_monitoring_bypass_fix.py`** — the direct, working precedent for
  static-source-text testing of `.claude/workflows/*.js` files without execution; reusable
  *pattern*, not reusable *target* (nothing in this ticket touches `implement-ticket.js` itself).
- **`tools/gate_checks/*.py`** (esp. `plan_gate_static.py`, `architecture_reviewer_static.py`,
  `parity_ledger_scan.py`, `parity_updater_static.py`, `done_checker_static.py`,
  `doc_staleness_check.py`) — the single most important prior-art find: these are the *real*,
  already-tested, pure-Python deterministic gate functions the orchestrator itself calls. A replay
  runner should import and call these directly (read-only use, never modify them) rather than
  reinventing gate logic — this is what makes "replay" more than a hollow no-op shell.
- **`TCK-20260716-AGENTOPS-REPLAY-TIMELINE`** (`tickets/done/`) — tangential, different concern: a
  dashboard UI feature (`experiments/agent_ops_dashboard/`, `src/api/routes/history.py`) for
  scrubbable *visual playback* of a run's recorded `runs.jsonl`/`events.jsonl` timeline. Not a
  workflow-logic replay runner, but confirms this repo already treats "recorded run data as a
  replayable timeline" as a valid concept in an adjacent context — reinforces that this ticket's
  request is a natural, not speculative, extension.
- **No prior art exists for agent-workflow phase replay itself** — confirmed by `search_docs`
  (all top hits are either the sim-engine replay domain, `docs/ai/ticket-lifecycle.md`, or
  working_log.csv entries about *instrumenting* the workflow, not *replaying* it) and by
  `graphify query`, which returned zero nodes related to Claude/Codex workflow-phase replay. This
  ticket is genuinely first-of-kind design work, as its own Assumptions state.

## Risks and Open Questions

**These require an explicit Plan-phase decision — not assumed here, per the "vague leads stay
vague" rule:**

1. **Exact phase-slice scope is undecided.** `implement-ticket.js` has 11 phases, ~10 distinct
   JSON schemas, and dozens of branch outcomes (11 different `final_status` early-return shapes
   alone). Replaying *all* of them with full fidelity is a large surface for a "proof." The source
   plan (`idea_provider_agnostic_agent_orchestration.md:359`) only requires "run `implement-ticket`
   contract and phase replay against recorded Claude fixtures" — it does not mandate 100% phase
   coverage. **Recommendation** (for Plan phase to confirm or override): scope the "implement-ticket
   slice" to **Scope → Investigate → Plan → Review**, the four phases before Implement. Rationale:
   (a) they are the phases with the richest, most self-contained deterministic gate logic
   (tag-registry check, unresolved-questions gate, architecture-review verdict branch) that is
   already real, importable Python; (b) they include at least one full "gate blocks, then a
   retry succeeds" pair if the chosen real fixture ticket has one (see finding above re:
   `ORCHESTRATION-CONTRACT-ADR`'s seq 9/10 Verify retry — though that's a *later*-phase example;
   Plan should pick a fixture ticket, or splice in a second synthetic-but-labeled-as-such example,
   that demonstrates a gate-block-then-continue transition within the chosen phase range); (c) it
   avoids requiring a fixture to carry a full `git diff`/`files_changed` implementation payload,
   which Implement/Architecture-Verify/Test/Parity would need and which is a much heavier fixture
   surface. This is a recommendation, not a decision — Plan phase must explicitly state and justify
   whatever slice it picks, and Implement must not silently expand it later.
2. **Real fixture source ticket is undecided.** `staging_artifacts/{ticket_id}/` is deleted at
   Finalize (moved to `stored_artifacts/`) — so a real fixture's rich phase-output content must be
   sourced from a **`tickets/done/` + `stored_artifacts/{ticket_id}/`** pairing (permanent), joined
   with the matching real `agent-monitoring/events.jsonl` slice for that `run_id` (also permanent,
   append-only). **Recommendation**: use `TCK-20260721-ORCHESTRATION-CONTRACT-ADR` itself — same
   discovery batch, small, complete, real, and its full real `events.jsonl` seq 1-11 slice and
   `stored_artifacts/` content are already read and cited above. Plan phase should confirm this
   choice or pick a different completed ticket.
3. **Is deriving a new fixture file from a real completed ticket's already-`done`/`stored_artifacts`
   content "modifying a live ticket artifact"?** Scope forbids modifying live ticket artifacts;
   it does not forbid *reading* them to construct a new, separate fixture file. Reading (not
   writing) `tickets/done/*.md` and `stored_artifacts/*/*.md` and copying excerpts into a new file
   under a new fixture path is consistent with "isolated... fixture... work" in Scope's first
   bullet. Flagged for explicit Plan-phase confirmation to avoid ambiguity, since the wording is
   close enough to warrant stating the reasoning explicitly rather than assuming it.
4. **Fixture envelope encoding (YAML vs JSON) is undecided.** The ADR's Contract Representation
   decision (YAML + generated Python validation models) governs the **shared orchestration
   contract** (`agent-orchestration/contract.yaml` et al.), not fixture *data* specifically — the
   ADR's own Source Ownership section describes a `agent-orchestration/` directory this ticket
   explicitly must not create (Out of Scope: "no runtime migration or production code change").
   **Recommendation**: the fixture *specification document* (the markdown doc defining the
   envelope schema) is prose/markdown per this repo's `docs/` convention (not YAML) — that's AC #1's
   "specification document." The fixture *data* itself should default to YAML for the top-level
   envelope (aligning with the ADR's general reviewability preference and enabling multi-line
   prose fields like `implementation_summary` without JSON-escaping pain), with a hand-written
   (not code-generated — no codegen tooling exists yet in this repo) Python dataclass/validator
   loading and checking it, which is the same practical shape the ADR's "generated Python
   validation models" aspires to, adapted to what's actually buildable today. Plan phase must state
   this explicitly as AC #5 requires, not silently pick a format.
5. **Full 11-phase branch-logic mirroring vs. the chosen slice's branches only is undecided.**
   Given decision #1 above, only the branches relevant to the chosen phase slice need hand-mirroring
   (following the `classifyChecklistFailure` "kept in sync by hand" precedent) — Plan phase should
   enumerate exactly which `implement-ticket.js` line ranges/branches are mirrored, to keep the
   surface bounded and auditable.

## Anti-Drift Hazards

- **The "no production hooks" containment is unconditional, not merely "isolated."** Per the
  ticket's own explicit correction (citing Codex's 2026-07-21 review): even a `tmp_path`/redirected
  argument invocation of `post_tool_hook.py`/`pre_tool_hook.py`/`record_run.py`/`record_events.py`
  is forbidden. The replay runner must define its own fake/no-op recording+hook functions inline —
  never subprocess or import the real scripts, under any argument or cwd configuration. This is the
  single most sensitive constraint in this ticket; violating it even in a test fixture defeats the
  entire proof.
- **`record_run.py`/`record_events.py` are importable, not just subprocess-callable** — a
  static source-text check for "no invocation" must catch both `subprocess`-based calls (string
  literal `"record_run.py"` / `"record_events.py"` / `"post_tool_hook.py"` / `"pre_tool_hook.py"`
  appearing in a shell-command string) **and** `import`/`from ... import` statements referencing
  those four module names — a narrower check that only greps for `subprocess.run(...)` would miss
  a direct `from record_run import main` bypass.
- **"Verified by process-level evidence... not merely by output-diffing"** — the required test must
  assert on the replay runner's own *source code* (no reachable call site), not merely observe that
  `agent-monitoring/*.jsonl` didn't change after a run (that's a different, weaker signal already
  covered separately by the snapshot/no-mutation test). Conflating the two tests would under-satisfy
  AC #2.
- **`tests/tools/test_post_tool_hook.py`'s `tmp_path`-isolated-cwd subprocess pattern is for
  isolating the *hook itself under test* — reusing that pattern to invoke the real hook scripts
  "safely" from inside the replay runner is exactly the trap this ticket's own text warns against.**
  Only the isolation *technique* (temp directories, subprocess with controlled `cwd`) may be reused,
  and only for the runner's own snapshot mechanism or fixture-loading — never to make a real-hook
  invocation "safe."
- **Do not silently expand into a live Codex adapter, a live LLM replay, or any provider-runtime
  code.** Out of Scope explicitly blocks this until the parent epic's 5 discovery outputs are all
  approved. This ticket's own proof runner must never call a live LLM API — recorded fixture outputs
  stand in for `agent()` return values.
- **Do not let "fails clearly on missing required fixture field" degrade into a caught-and-logged
  warning.** The AC is explicit: "no partial/best-effort replay that masks missing data" — the
  runner must raise/exit non-zero, not print a warning and continue (the opposite of this repo's
  `agent-monitoring` write-path convention, which is deliberately fail-open — this ticket's replay
  runner must be fail-closed instead, and that inversion should be called out explicitly in
  Implement, not left implicit).
- **Do not modify `tools/gate_checks/*.py` to "make replay easier."** These are real, shared,
  already-tested production modules the live orchestrator also calls — the replay runner must treat
  them as read-only dependencies, imported exactly as-is.

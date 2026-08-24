---
status: active
layer: ai
authority: P1
audience: developer
---

# Workflows

Workflows are multi-agent orchestration scripts in `.claude/workflows/*.js`. They coordinate subagents across phases, carry structured state between steps, and enforce hard gates (architecture review, test pass, DoD check) before proceeding.

**Invocation — from a user prompt:**
```
/implement-ticket request="add pagination to world listing"
/implement-epic folder=tickets/todos/monitoring/
```
Type the skill name as a slash command with args. Do **not** type `/workflow` — that is a Claude-internal tool name, not a user command.

**Invocation — from Claude's tools (internal):**
```js
Workflow({ name: "workflow-name", args: { key: value } })
```

**Resuming after a gate failure:** Most workflows return a structured failure with a `ticket_id` or `session_id`. Fix the blocking issue, then re-run passing that ID to skip completed phases.

---

## Development Workflows

### `create-tickets`

**Purpose:** Parse a detailed markdown document into individual `TCK-*.md` ticket files. The natural first step before `/implement-epic`.

**Phases:**

| Phase | What happens |
|---|---|
| Comprehend | Reads the source doc and extracts one task per discrete concern; no codebase investigation yet |
| Investigate | Per-concern, in parallel: `tools/knowledge_search.py`, `graphify query`, `docs/REGISTRY.yaml` lookups, a `working_log.csv` grep, code/test reads, and a tier assessment |
| Structure | One synthesis agent produces ticket fields from the investigation evidence only, handling merge/split/short-scope dedup across concerns; orchestrator then runs `tools/tag_registry.py::check_tags_registered` across all tasks' tags — any task with an unregistered tag is skipped (not written), reported in the final `tags_not_registered` field, and excluded from the `SEQUENCE.md` dependency graph, while the rest of the batch proceeds (`TCK-20260706-CREATE-TICKETS-TAG-CHECK`) |
| Write | Per ticket (only those that passed the tag-registry check), parallel `ticket-scoper` invocations write `TCK-YYYYMMDD-<SHORT-SCOPE>.md` into the output folder, plus a conditional `SEQUENCE.md` when intra-batch dependencies are detected |
| Link | If `epic_id` given, appends new ticket IDs to the epic's `## Related Tickets` section |

**Args:**

| Arg | Type | Required | Description |
|---|---|---|---|
| `source` | string | Yes | Path to the source markdown document |
| `structure` | string | No | Path to a ticket plan structure / template doc — guides task granularity |
| `output` | string | No | Output folder override; inferred from doc content if omitted |
| `epic_id` | string | No | Epic ticket ID to link created tickets to |

**Usage:**
```
/create-tickets source=docs/plans/another_repair_phase_20_28.md
/create-tickets source=docs/plans/my_feature_plan.md structure=docs/plans/ticket_plan_structure.md
/create-tickets source=docs/plans/my_feature_plan.md output=tickets/todos/my-feature/
/create-tickets source=docs/plans/my_feature_plan.md epic_id=TCK-20260608-MY-FEATURE-EPIC
```

**Typical full flow:**
```
/create-tickets source=docs/plans/my_feature_plan.md structure=docs/plans/ticket_plan_structure.md
        ↓  (review generated tickets, adjust if needed)
/implement-epic folder=tickets/todos/my-feature/
```

**Artifacts produced:**
- `tickets/todos/<folder>/TCK-YYYYMMDD-<SHORT-SCOPE>.md` — one per task that passed the tag-registry check, Status: OPEN, all required sections filled
- Epic `## Related Tickets` updated (if `epic_id` provided)
- Return value includes `tags_not_registered`: tasks skipped for an unregistered tag, alongside the existing `scope_dupes_dropped` field

---

### `implement-ticket`

**Purpose:** Full ticket lifecycle from request to closed ticket. Orchestrates all development subagents in sequence with hard gates.

**Phases:**

| Phase | Agent used | Gate condition |
|---|---|---|
| Scope | `ticket-scoper` | Stops if conflicts detected, or if any ticket tag isn't in `registries/tag_registry.jsonl` (orchestrator-run check via `tools/tag_registry.py::check_tags_registered`, after the agent call returns); when resuming an existing `ticket_id`, an orchestrator-run `resolveScopeTicketLocation()` step (via `tools/agent-monitoring/scope_ticket_relocate.py::resolve_and_relocate_ticket`) resolves `ticket_path`/`tier`/`todos_source_path` deterministically before the agent call, replacing the former agent-prompt-text file search — for a `tickets/todos/` original it moves (copy-then-delete) the file when `## Tier` is `epic`, or copies it (leaving the original in place, as before) otherwise, so an epic ticket — which never reaches Finalize's cleanup — never ends up permanently duplicated on disk |
| Investigate | `investigator` | — |
| Plan | `planner` | Stops if unresolved questions in plan |
| Review | `architecture-reviewer` | Stops if NEEDS_CHANGES or BLOCKED |
| Implement | `implementer` | — |
| Document-Update | `doc-updater` | Runs unconditionally, every tier; its `docs_updated` paths merge into `implementation.files_changed` before the doc-staleness gate evaluates them; a doc-updater blocker is reported via a `failed`-status event but does not stop the pipeline — Verify's `check_docs_to_update_coverage` remains the actual backstop for standard/epic tier |
| Architecture-Verify | `architecture-reviewer` | Second, post-Implement call; runs `tools/gate_checks/architecture_reviewer_static.py::run_architecture_checks` before the agent call and injects its JSON output; narrowly scoped to judging flagged items, not re-reviewing the plan; stops if NEEDS_CHANGES or BLOCKED (same vocabulary as Review); skipped for hotfix |
| Test | `test-scoper` | Stops if any test fails |
| Parity | `parity-updater` | Skipped when `files_changed` has no `src/` path and `behavior_changed` is false; a P0 ledger safeguard forces the full run instead if any P0 entry's `v2_evidence` would go stale; when not skipped, runs `tools/gate_checks/parity_updater_static.py::expected_subsystems_for_files` and `::next_available_id` (per candidate shard) before the agent call and `::cross_reference_touched` after it returns, surfacing any untouched-mapped-subsystem miss; a genuine miss now hard-blocks the phase (returns `PARITY_INCOMPLETE`); an unparseable cross-ref result remains non-blocking |
| Security-Review | `security-reviewer` | Fires when the ticket's tags include `security` (ground truth) or suggested_skills includes /security-review; stops if NEEDS_CHANGES or BLOCKED |
| Verify | `done-checker` | Runs `tools/gate_checks/done_checker_static.py::run_static_precheck` first and cites its output for 6 machine-checked conditions (3, 4, 7, 10, 12, plus `ticket_field_values_valid` — no dedicated DoD number yet, see `docs/ai/agents.md`'s `done-checker` section); stops if any DoD condition fails |
| Finalize | inline | Moves ticket, writes working_log.csv, migrates artifacts; then runs `run_finalize_selfcheck` via `bash()` to confirm the migration actually landed — returns `FINALIZE_INCOMPLETE` instead of `DONE` if a discrepancy is found; separately, after `writeMonitoring('DONE')`, runs three advisory-only Finalize-tail checks (`implement-ticket.js:1502-1581`) — `check_monitoring_write_recorded` (confirms the agent-monitoring write, `runs.jsonl`/`events.jsonl`, for this run landed), `check_tag_drift` (flags a possible mismatch between the ticket's declared `tags:` and its `Files Changed`/`Related Code Areas` content; `CLEAN`/`FLAGGED`, never `PASS`/`FAIL`), and `check_workflow_meta_conformance` (aggregated via `summarize_conformance_results`, `Security-Review` filtered out at this call site; flags a declared `meta.phases` title that fired zero events during this run — added by `TCK-20260804-SKILL-DRIFT-DETECTION`, wiring in the verifier `TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK` had built but left unwired) — all three are loud but non-blocking (a `failed`-status event plus a `WARNING` in the returned `message`), `status` always stays `DONE` (CLAUDE.md's Hard Rule that a monitoring write failure — and, by the same precedent, these checks — must never fail the workflow) |

`mechanics-auditor` is not one of the phases above — it is an ad hoc agent (`Agent(subagent_type: "mechanics-auditor")`, no `implement-ticket.js` call site) that now has its own static pre-check (`tools/gate_checks/mechanics_auditor_static.py`), self-invoked rather than orchestrator-run; see `docs/ai/agents.md`'s `mechanics-auditor` section for detail.

`check_skill_doc_covers_meta_phases()` (`tools/gate_checks/workflow_meta_conformance.py`, added by `TCK-20260804-SKILL-DRIFT-DETECTION`) is also not one of the phases above and not wired into any workflow's Finalize tail — it runs as a pytest test (`tests/tools/test_workflow_meta_conformance.py`) that asserts every hand-orchestration `SKILL.md` mentions all of its own workflow's declared `meta.phases` titles, catching doc-vs-code drift on every test-suite run rather than only at ticket-close time.

**Args:**

| Arg | Type | Required | Description |
|---|---|---|---|
| `request` | string | If no `ticket_id` | Free-text description of the task to implement |
| `ticket_id` | string | If resuming | Full `TCK-YYYYMMDD-...` ID of an existing ticket |

**Usage:**
```js
// New task:
Workflow({ name: 'implement-ticket', args: { request: 'Implement Task 28.1 — relation projection into combat classification' } })

// Resume after fixing a failing gate:
Workflow({ name: 'implement-ticket', args: { ticket_id: 'TCK-20260606-PHASE28-RUNTIME-RELATION' } })
```

**Return values:**

| Status | Meaning | Next action |
|---|---|---|
| `CONFLICTS_DETECTED` | Duplicate or conflicting tickets found | Review conflicts, adjust scope, re-run |
| `TAGS_NOT_REGISTERED` | A ticket tag isn't in `registries/tag_registry.jsonl` | Register it (`python3 tools/tag_registry.py add <tag> --category <cat> --note "..."`) or edit the ticket to use an existing registered tag, then re-run with `ticket_id` |
| `SCOPE_AGENT_FAILED` | The Scope-phase `ticket-scoper` agent call returned null or malformed output with no `ticket_id` | Re-run; if it persists, investigate the agent call itself |
| `EPIC_SCOPED` | Ticket tier is `epic` — scoped only, no implementation performed | Create child tickets, implement them individually or via `implement-epic` |
| `NEEDS_HUMAN_INPUT` | Plan has unresolved questions | Read `staging_artifacts/{id}/plan.md`, resolve, re-run with `ticket_id` |
| `NEEDS_CHANGES` | Architecture review rejected the plan (Review phase) or a post-Implement diff (Architecture-Verify phase) — same status string, distinguish by which phase logged it | Review: fix `plan.md` violations. Architecture-Verify: fix the flagged code. Re-run with `ticket_id` either way |
| `BLOCKED` | Architecture fundamental conflict — plan (Review phase) or diff (Architecture-Verify phase) | Review: revisit scope. Architecture-Verify: fix the flagged code. Re-run with `ticket_id` either way |
| `DOC_STALENESS_BLOCKED` | A behavior-changing `src/` or `.claude/workflows/*.js` diff has no `docs/` path in `files_changed` (`tools/gate_checks/doc_staleness_check.py`) | Add a `docs/` update reflecting the behavior change, re-run with `ticket_id` |
| `TESTS_FAILED` | One or more tests failing | Fix failing tests, re-run with `ticket_id` |
| `DATA_RUNS_CLEAN_FAILED` | Post-Test auto-clean of `data/runs/*`/`reports/release_proof/*` failed | Resolve manually (check permissions/locks), re-run with `ticket_id` |
| `SECURITY_BLOCKED` | Security review rejected the change | Fix violations, re-run with `ticket_id` |
| `DOD_BLOCKED` | DoD conditions not met | Fix listed items, re-run with `ticket_id` |
| `PARITY_INCOMPLETE` | A `src/` file mapped to a parity-ledger subsystem had no corresponding `docs/parity_ledger/*.yaml` entry touched in this diff (`tools/gate_checks/parity_updater_static.py::cross_reference_touched`) | Read `failing_items`, update the missing `docs/parity_ledger/*.yaml` entry, re-run with `ticket_id` |
| `FINALIZE_INCOMPLETE` | Finalize ran its steps, but the post-migration self-check (`run_finalize_selfcheck`) found a discrepancy — e.g. `stored_artifacts/` incomplete, `staging_artifacts/` not cleaned, ticket not moved, or the working_log row is missing/duplicated | Read `failing_items`, fix the discrepancy manually, re-run with `ticket_id` |
| `DONE` | Ticket closed, artifacts migrated | — |

**Artifacts produced:**
- `tickets/done/{ticket_id}.md`
- `stored_artifacts/{ticket_id}/` (investigation.md, plan.md, test_plan.md)
- `tickets/working_log.csv` (one new row)
- `agent-monitoring/runs.jsonl` + `events.jsonl` (one run record + per-phase events)

**`lane-architecture` coverage boundary:** `make lane-architecture` (`pytest tests/ -m "architecture"`)
is a `src/`-simulation-code guard lane only — durable-state mutation discipline, cross-domain import
bans, unstable-sort detection. It has **zero overlap** with the 4 gate-checker modules in
`tools/gate_checks/` (`done_checker_static.py`, `parity_updater_static.py`,
`mechanics_auditor_static.py`, `architecture_reviewer_static.py`): none of
`tests/tools/test_*_static.py` carry `@pytest.mark.architecture`, by deliberate design
(`tickets/done/gate-determinism-followups/SEQUENCE.md` decision 1) — these are agent-workflow
hygiene checks, not simulation-code architecture guards, and are intentionally not folded into
`lane-architecture`. Whether `lane-architecture` itself is wired into CI is a separate,
already-resolved question (audit finding D18 F3); this note is strictly about content-coverage
boundary.

---

### `implement-epic`

**Purpose:** Implement all tickets in a folder or epic sequentially. Calls `implement-ticket` for each ticket in order, stops on any gate failure, skips already-done tickets on re-run.

**Phases:**

| Phase | What happens |
|---|---|
| Discover | Lists tickets in the folder or reads the epic's Related Tickets section; filters out already-done |
| Implement | Runs `implement-ticket` for each ticket sequentially — stops on first gate failure |
| Report | Summarises results: DONE count, gate failures, remaining tickets |

**Args:**

| Arg | Type | Required | Description |
|---|---|---|---|
| `folder` | string | One of three | Path to a folder of TCK-*.md files, e.g. `tickets/todos/monitoring/` |
| `epic_id` | string | One of three | Existing epic ticket ID — reads its `## Related Tickets` section |
| `request` | string | One of three | Natural language — creates an epic ticket, returns `EPIC_CREATED` for user to add children |
| `tier_override` | string | No | Overrides the tier for every child ticket (`hotfix` / `standard`) |

**Usage:**
```
/implement-epic folder=tickets/todos/monitoring/
/implement-epic epic_id=TCK-20260607-MY-EPIC
/implement-epic request="add a full caching layer to the world registry"
/implement-epic folder=tickets/todos/my-feature/ tier_override=hotfix
```

**Return values:**

| Status | Meaning | Next action |
|---|---|---|
| `EPIC_CREATED` | `request` mode — epic ticket created | Add child tickets to `## Related Tickets`, re-run with `epic_id` |
| `NOTHING_TO_DO` | All tickets already done | — |
| `DONE` | All tickets implemented | — |
| Any gate status | A child ticket failed (e.g. `TESTS_FAILED`) | Fix the blocking ticket, re-run same command — done tickets skip automatically |

**Re-running after a failure:**
```
# Batch stopped at TCK-20260607-C (TESTS_FAILED). Fix it, then:
/implement-epic folder=tickets/todos/my-feature/
# → skips TCK-20260607-A (done) and TCK-20260607-B (done), resumes at TCK-20260607-C
```

**Artifacts produced:**
- All artifacts from each child `implement-ticket` run (tickets, stored_artifacts, working_log)
- `agent-monitoring/runs.jsonl` — one batch run record (`EPIC-{id}` or `FOLDER-{path}`)
- `agent-monitoring/events.jsonl` — one event per child ticket

---

## Simulation Workflows

### `generate-simulation-setup`

**Purpose:** Generate world specs, scenario configs, and experiment parameters for a new simulation run.

**Phases:** Scan → Draft → Validate

**Args:**

| Arg | Type | Description |
|---|---|---|
| `world_type` | string | World archetype to generate (e.g. `frontier`, `dungeon`) |
| `scenario` | string | Scenario name |
| `experiment` | string | Experiment variant |
| `profile` | string | Config profile (`default`, `stress`, etc.) |

**Outputs:** `generation/draft_specs/world.yaml`, `scenario.yaml`, `experiment.yaml`

**When to use:** Starting a new simulation experiment. Follow with `prepare-simulation-execution` once specs are reviewed.

---

### `prepare-simulation-execution`

**Purpose:** Validate specs, estimate run budget (ticks, time, disk), and produce the exact shell command to trigger the simulation.

**Phases:** Resolve → Estimate → Generate

**Args:**

| Arg | Type | Description |
|---|---|---|
| `target` | string | Spec path or name (defaults to most recent approved draft) |
| `profile` | string | Config profile override |
| `mode` | string | `generic` or `specific` |

**Outputs:**
- Readiness report: `READY` / `READY_WITH_WARNINGS` / `NOT_READY`
- Shell command block ready to copy-paste
- Expected output paths (event log, telemetry, snapshots)

**When to use:** Before manually triggering a simulation run. This workflow does not run the simulation — it prepares and validates everything so the user can trigger it with confidence.

---

### `register-simulation-result`

**Purpose:** Register a completed simulation run into the lab index with diagnostic scorecard.

**Phases:** Validate → Index → Score

**Args:**

| Arg | Type | Description |
|---|---|---|
| `session_id` | string | Run ID or directory name under `data/runs/` |
| `mode` | string | `specific` (session_id required) or `generic` (most recent unregistered run) |

**Outputs:**
- `registration/lab_run_manifest.json` — artifact inventory, validation status, tags
- `registration/lab_summary.json` — key metrics (tick count, population arc, combat volume)
- Diagnostic scorecard (markdown) — grades per dimension: Data Integrity, Run Stability, Balance Health, Coverage, Regressions

**When to use:** After a simulation run completes, before analyzing results. Grades below B trigger recommended follow-up actions.

---

### `investigate-simulation-result`

**Purpose:** Deep multi-agent investigation of balance anomalies in a completed simulation run.

**Phases:** Load → Analyze → Report

**Args:**

| Arg | Type | Description |
|---|---|---|
| `session_id` | string | Run ID to investigate |
| `focus` | string | Optional: specific anomaly type to focus on (`economy`, `combat`, `population`) |

**Outputs:**
- `investigation/investigation_report.md` — findings, severity, evidence per anomaly
- `investigation/investigation_report.json` — structured anomaly list for `propose-simulation-enhancements`

**When to use:** After `register-simulation-result` returns a grade below B on Balance Health or after the `simulation-analyst` agent flags CRITICAL anomalies. This is the full diagnosis — use `simulation-analyst` for a lightweight first pass.

---

### `propose-simulation-enhancements`

**Purpose:** Generate hypotheses for anomalies and propose concrete config/rule patches and next experiments.

**Phases:** Read → Hypothesize → Propose

**Args:**

| Arg | Type | Description |
|---|---|---|
| `session_id` | string | Session whose investigation report to use |
| `mode` | string | `generic` (most recent) or `specific` |

**Outputs:**
- Ranked hypotheses per anomaly (evidence, confidence, testability)
- Proposed YAML patches (human-review only — not applied automatically)
- Next experiment YAML drafts
- Enhancement proposals document: `RECOMMENDED` / `EXPERIMENTAL` / `HIGH_RISK` per proposal

**When to use:** After `investigate-simulation-result`. Never apply patches without human review — this workflow explicitly marks proposals as proposals, not changes.

---

### `compact-simulation-result`

**Purpose:** Compress heavy event log files and archive unnecessary telemetry from past simulation runs to recover disk space.

**Phases:** Scan → Compact → Archive

**Args:**

| Arg | Type | Description |
|---|---|---|
| `session_id` | string | Specific run to compact, or omit for all uncompacted runs |
| `keep_summary` | boolean | Whether to keep a summary log after compaction |

**When to use:** After a run has been registered and investigated. Safe to run at any time on registered runs — raw data is preserved in the archive, summaries are kept.

---

### `update-knowledge-store`

**Purpose:** Synthesize approved simulation enhancement proposals into the long-term knowledge graph.

**Phases:** Verify → Synthesize → Commit

**Args:**

| Arg | Type | Description |
|---|---|---|
| `session_id` | string | Session whose proposals to commit |
| `mode` | string | `generic` or `specific` |

**Approval gate checks (all must pass before synthesis):**
1. Enhancement proposals document exists and is not a draft
2. Each `RECOMMENDED` proposal has been reviewed (approval marker in doc or tickets)
3. No CRITICAL-severity open tickets block the contribution
4. Proposed patches don't contradict the Mechanics Bible
5. No `HIGH_RISK` proposals without explicit approval marker

**Outputs:**
- Structured knowledge contribution (rule statements, evidence, confidence, scope, exceptions)
- Graph update description (new nodes and edges for `graphify-out/`)
- Audit log JSON (what was included, excluded, approved)

**Revert:** `RevertSimulationKnowledgeWorkflow.run(session_id)` (`src/lab/workflows/revert_simulation_knowledge.py`) reverts the
most recent sync for that session. It removes exactly the insight/known-issue/rule files recorded
in that sync's `files_written` audit event, matches and removes the corresponding
`decision_log.jsonl` line by exact content equality (never by timestamp alone), and rejects with
`LabKnowledgeRevertError` if any target file was modified by a later sync. The revert action itself
is logged as a `knowledge_reverted` audit event. It does not regenerate or revert
`knowledge_update_report.md` — that report is a derived artifact, not source-of-truth knowledge
state.

**When to use:** Only after the approval gate passes. This is the final step in the simulation learning loop, committing validated insights into the long-term knowledge graph.

---

### `simq-audit`

**Purpose:** A narrow calibration and anchor-drift maintenance lane for the 10-pillar SimQ grading system — recalibrates against `grade_anchors.json`, classifies drift, and either closes out cleanly or spawns a follow-up ticket. Never changes SimQ scoring formulas or pillar logic (`src/simulation_quality/*` is out of scope for every phase).

**Phases:**

| Phase | What happens |
|---|---|
| Recalibrate | Runs `make simq-full-audit` (or `-full`/`-slow` per `mode`) — diffs current calibration data against anchors, runs fast-tier grade regression tests, and cross-checks anchor/parity coverage gaps |
| Classify Drift | Classifies each flagged item as `EXPECTED_DRIFT` (must cite a specific commit/ticket), `REGRESSION`, `DA_NEEDED`, or `NO_ACTION`, and computes a rollup verdict: `no_regression` / `regression` / `needs_da_decision` |
| Update Anchors | Edits `grade_anchors.json` and `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` for `EXPECTED_DRIFT` items only; gates on `ANCHORS_STILL_FAILING` |
| Sync Docs | Updates `docs/simulation_quality/eval_matrix_results.md` and `docs/audits/D20_simq_integration.md`; conditionally `event_type_coverage.md` and `v2_intentional_divergences.md` |
| Parity Check | Updates `docs/parity_ledger/*.yaml` entries flagged by the coverage/parity gap scan |
| Verify | DoD-style gate: fast-tier regression tests pass, zero uncovered anchor keys, every instructed doc touched or explicitly skipped; `BLOCKED` on failure |
| Report | Deterministic branch on the Classify Drift verdict — no ticket for `no_regression`, one spawned ticket otherwise |

**Args:**

| Arg | Type | Required | Description |
|---|---|---|---|
| `mode` | string | No | `fast` (default) — dry-run diff only; `full` — re-runs the engine for fast scenarios first; `slow` — fast tier then the slow (1000t/2000t) tier |
| `worlds` | string | No | Optional comma-separated scope for calibration re-runs; only meaningful with `mode=full` |

**Outputs:**
- Updated `grade_anchors.json` / `FAST_ANCHOR_KEYS` / `SLOW_ANCHOR_KEYS` (Update Anchors phase, `EXPECTED_DRIFT` items only)
- Updated `docs/simulation_quality/eval_matrix_results.md` and `docs/audits/D20_simq_integration.md`, conditionally `event_type_coverage.md` and `v2_intentional_divergences.md` (Sync Docs phase)
- Updated `docs/parity_ledger/*.yaml` entries (Parity Check phase)
- Either a suggested no-ticket chore-commit message or one spawned follow-up ticket (Report phase, see Return values below)

**Return values:**

| Status | Meaning | Next action |
|---|---|---|
| `DONE_NO_TICKET` | Verdict was `no_regression` — no ticket created, suggested chore-commit message emitted | — |
| `NEEDS_TICKET` | Verdict was `regression` or `needs_da_decision` — one ticket spawned via `ticket-scoper` | Hand off with `/implement-ticket ticket_id=<new-id>` |

**When to use:** After a SimQ-related uplift ticket lands, or on a recalibration cadence, to check anchor/grade drift without re-deriving the manual process by hand (see [`audit_workflow.md`](../simulation_quality/audit_workflow.md) §1 for the manual sequence this replaces).

---

## Simulation Workflow Order

For a complete simulation experiment cycle:

```
generate-simulation-setup
        ↓
prepare-simulation-execution
        ↓
[user triggers simulation manually]
        ↓
register-simulation-result
        ↓
investigate-simulation-result      ← or simulation-analyst for lightweight check
        ↓
propose-simulation-enhancements
        ↓
[human reviews and approves proposals]
        ↓
update-knowledge-store
        ↓
compact-simulation-result          ← cleanup
```

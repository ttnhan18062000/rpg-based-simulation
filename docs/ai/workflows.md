# Workflows

Workflows are multi-agent orchestration scripts in `.claude/workflows/*.js`. They coordinate subagents across phases, carry structured state between steps, and enforce hard gates (architecture review, test pass, DoD check) before proceeding.

**Invocation:**
```
Workflow({ name: "workflow-name", args: { key: value } })
```
Or via skill shortcut: `/workflow-name`

**Resuming after a gate failure:** Most workflows return a structured failure with a `ticket_id` or `session_id`. Fix the blocking issue, then re-run passing that ID to skip completed phases.

---

## Development Workflow

### `implement-ticket`

**Purpose:** Full ticket lifecycle from request to closed ticket. Orchestrates all development subagents in sequence with hard gates.

**Phases:**

| Phase | Agent used | Gate condition |
|---|---|---|
| Scope | `ticket-scoper` | Stops if conflicts detected |
| Investigate | `investigator` | — |
| Plan | `planner` | Stops if unresolved questions in plan |
| Review | `architecture-reviewer` | Stops if NEEDS_CHANGES or BLOCKED |
| Implement | `implementer` | — |
| Test | `test-scoper` | Stops if any test fails |
| Parity | `parity-updater` | — |
| Verify | `done-checker` | Stops if any DoD condition fails |
| Finalize | inline | Moves ticket, writes working_log.csv, migrates artifacts |

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
| `NEEDS_HUMAN_INPUT` | Plan has unresolved questions | Read `staging_artifacts/{id}/plan.md`, resolve, re-run with `ticket_id` |
| `NEEDS_CHANGES` | Architecture review rejected plan | Fix `plan.md` violations, re-run with `ticket_id` |
| `BLOCKED` | Architecture fundamental conflict | Revisit scope, re-run with `ticket_id` |
| `TESTS_FAILED` | One or more tests failing | Fix failing tests, re-run with `ticket_id` |
| `DOD_BLOCKED` | DoD conditions not met | Fix listed items, re-run with `ticket_id` |
| `DONE` | Ticket closed, artifacts migrated | — |

**Artifacts produced:**
- `tickets/done/{ticket_id}.md`
- `stored_artifacts/{ticket_id}/` (investigation.md, plan.md, test_plan.md)
- `tickets/working_log.csv` (one new row)

---

## Simulation Workflows

### `generate-simulation-setup`

**Purpose:** Generate world specs, scenario configs, and experiment parameters for a new simulation run.

**Phases:** Spec Draft → Validation → Promotion

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

**Phases:** Load → Analyze → Correlate → Report

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

**Phases:** Inventory → Compact → Archive

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
- Audit log JSON (what was included, excluded, approved, and how to revert)

**When to use:** Only after the approval gate passes. This is the final step in the simulation learning loop, committing validated insights into the long-term knowledge graph.

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

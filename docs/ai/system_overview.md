---
status: active
layer: ai
authority: P1
audience: developer
---

# AI Agent System — Technical Overview

## 1. Overview and Purpose

This document is a single technical narrative tying together the AI agent system used to build and
test this project: the three-layer model of agents, workflows, and skills; the full ticket-lifecycle
and implementation pipeline; the simulation-testing and quality lanes; and observability. It exists for
readers who want the full picture without reading eight or more separate files first: `docs/ai/README.md`,
`docs/ai/agents.md`, `docs/ai/workflows.md`, `docs/ai/skills.md`, `docs/ai/ticket-lifecycle.md`,
`docs/ai/agent_infrastructure_audit.md`, `docs/simulation/lab_contract.md`,
`docs/simulation_quality/audit_workflow.md`, `docs/agent-monitoring/schema.md`, and
`docs/guides/agent_monitoring.md`.

This document narrates; it is not the source of truth for exact schemas, field lists, or argument
signatures — follow the links for those.

## 2. The Three-Layer Model

The agent system has three layers:

- **Agents** — `.claude/agents/*.md`. A focused subagent for one role in a task. Spawned automatically
  by workflows, or invoked directly via `Agent(subagent_type: "name")`.
- **Workflows** — `.claude/workflows/*.js`. Multi-agent orchestration across many phases, with gates and
  resumability. Invoked via `Workflow({ name: "workflow-name", args: {...} })` or `/workflow-name`.
- **Skills** — `.claude/skills/*/SKILL.md`, plus a set of built-in Claude Code skills. A slash command
  for a well-defined, single-session task pattern. Invoked via `/skill-name`.

Counts, verified directly against the filesystem and source docs rather than assumed:

- **11 subagents** exist under `.claude/agents/`, matching `docs/ai/agents.md`'s catalog exactly.
- **11 workflow files** exist under `.claude/workflows/`. **10** of them are documented with phase
  tables in `docs/ai/workflows.md`. The 11th, `simq-audit.js`, is covered later in this document
  (Section 5) and has its own dedicated doc, `docs/simulation_quality/audit_workflow.md`, but is not yet
  listed in `workflows.md`'s catalog.
- **16 skill folders** exist under `.claude/skills/`.

When to use which: reach for a **workflow** when the task spans multiple phases with gates (scope →
implement → test → close). Use an **agent** directly for one focused task in the middle of a
conversation — e.g., checking whether a plan violates architecture rules. Use a **skill** for a
well-defined single-session pattern that doesn't need multi-agent orchestration — e.g., `/graphify` or
`/code-review`.

For the full per-agent role/input/output table, see [`agents.md`](agents.md). For full per-workflow
args/phase/return-value tables, see [`workflows.md`](workflows.md). For the complete skill catalog, see
[`skills.md`](skills.md).

## 3. Ticket Lifecycle and the Development Pipeline

Work enters the system through `create-tickets` (turning a proposal or backlog item into one or more
tickets) or through direct ticket authoring. Either way, a ticket is then carried through
`implement-ticket` (single ticket) or `implement-epic` (a folder or epic of child tickets).

**`create-tickets` has 5 phases**: Comprehend → Investigate → Structure → Write → Link. This is sourced
directly from `.claude/workflows/create-tickets.js`'s `phase(...)` calls, not from
`docs/ai/workflows.md`'s prose (which documents only 3 phases there — see Section 6's dated note).
- **Comprehend** reads the proposal and extracts discrete concerns; no codebase investigation happens
  yet.
- **Investigate** runs per-concern, in parallel: `tools/knowledge_search.py`, `graphify query`,
  `docs/REGISTRY.yaml` lookups, a `working_log.csv` grep, code and test reads, and a tier assessment.
- **Structure** runs one synthesis agent that produces ticket fields from the investigation evidence
  only, handling merge/split/short-scope dedup across concerns.
- **Write** runs, per ticket, parallel `ticket-scoper` invocations that produce the actual `TCK-*.md`
  file plus a conditional `SEQUENCE.md` when intra-batch dependencies are detected.
- **Link** runs only when an `epic_id` is given.

`docs/agent-monitoring/schema.md`'s `events.jsonl` phase list for `create-tickets` already lists these
same 5 phases, independently confirming them.

**The 9-phase `implement-ticket` pipeline** (standard tier): Scope (`ticket-scoper`) → Investigate
(`investigator`) → Plan (`planner`) → Review (`architecture-reviewer`, gate: `NEEDS_CHANGES`/`BLOCKED`)
→ Implement (`implementer`) → Test (`test-scoper`, gate: `TESTS_FAILED`) → Parity (`parity-updater`) →
**Security-Review (`security-reviewer`, conditional: fires when the ticket's `tags` include `security`
or `suggested_skills` includes `/security-review`; gate: `SECURITY_BLOCKED`)** → Verify (`done-checker`,
gate: `DOD_BLOCKED`) → Finalize (inline, no agent). Security-Review is a 10th, conditional phase — it
does not run for every ticket, so the pipeline is still described as 9 standing phases plus this one
conditional gate. This matches `docs/ai/workflows.md` and `docs/ai/ticket-lifecycle.md`, both of which
match `.claude/workflows/implement-ticket.js` exactly.

Tier routing, matching this repository's own `CLAUDE.md` "Tier Routing" table:

| Tier | Phases run | Use when |
|---|---|---|
| `hotfix` | Scope → Implement → Test → Parity → Verify → Finalize | Bug fix or minimal targeted change with self-evident intent |
| `standard` | Full 9-phase pipeline | Any new feature, refactor, or substantive repair |
| `epic` | Scope only — tracks child tickets | Large multi-ticket initiative; no direct implementation |

**`implement-epic` has 3 phases**: Discover → Implement → Report, matching `docs/ai/workflows.md` and
`.claude/workflows/implement-epic.js`. It takes one of `folder` | `epic_id` | `request`, plus an
optional `tier_override`. Its return values include `EPIC_CREATED`, `NOTHING_TO_DO`, `DONE`, or any
child ticket's gate status.

Across these workflows, the literal gate/return-status vocabulary is: `CONFLICTS_DETECTED`,
`NEEDS_HUMAN_INPUT`, `NEEDS_CHANGES`, `BLOCKED`, `TESTS_FAILED`, `SECURITY_BLOCKED`, `DOD_BLOCKED`, `DONE`.

The Verify phase (`done-checker`) checks **12 substantive Definition-of-Done conditions**, plus a
13th — agent monitoring — that is pre-marked PASS and guaranteed by the workflow itself rather than
independently checked by `done-checker`.

For the full worked example — a real ticket walked end to end, plus the manual-execution fallback
without the workflow — see [`ticket-lifecycle.md`](ticket-lifecycle.md).

## 4. Simulation Testing: the Lab Workflow Chain and the Lab Session Contract

Simulation testing has two layers of the same underlying process, described by two different documents
at two different levels of abstraction.

**Layer A — the Claude Code workflow sequence** (7 workflows, from
[`workflows.md`](workflows.md)'s Simulation Workflows section):
`generate-simulation-setup` → `prepare-simulation-execution` → [user triggers the run manually] →
`register-simulation-result` → `investigate-simulation-result` → `propose-simulation-enhancements` →
[human reviews and approves] → `update-knowledge-store` → `compact-simulation-result` (cleanup, can run
any time on already-registered runs).

Phase names, per workflow:
- `generate-simulation-setup`: **Scan → Draft → Validate**, sourced directly from
  `.claude/workflows/generate-simulation-setup.js` (not `workflows.md`, whose prose here is stale — see
  Section 6).
- `investigate-simulation-result`: **Load → Analyze → Report** (3 phases), sourced directly from
  `.claude/workflows/investigate-simulation-result.js` (not `workflows.md`, which lists an extra,
  nonexistent 4th phase — see Section 6).
- `compact-simulation-result`: **Scan → Compact → Archive**, sourced directly from
  `.claude/workflows/compact-simulation-result.js` (not `workflows.md`, whose first phase name is stale
  there — see Section 6).
- `prepare-simulation-execution` (Resolve → Estimate → Generate), `register-simulation-result`
  (Validate → Index → Score), `propose-simulation-enhancements` (Read → Hypothesize → Propose), and
  `update-knowledge-store` (Verify → Synthesize → Commit) all match code as documented, so these four are
  cited directly from `workflows.md`.

**Layer B — the Agentic Simulation Lab session contract** ([`lab_contract.md`](../simulation/lab_contract.md),
backed by `src/lab/`): a 6-stage session lifecycle — GENERATION → EXECUTION_SUPPORT → REGISTRATION →
INVESTIGATION → ENHANCEMENT → KNOWLEDGE_UPDATE — with session states ACTIVE → WAITING_FOR_USER → ... →
COMPLETED / FAILED / ARCHIVED. Three of the six stages — GENERATION, EXECUTION_SUPPORT, and ENHANCEMENT
— are human-gated: each requires an explicit `approval_status: APPROVED` before the session may advance
past `WAITING_FOR_USER`, and a `REJECTED` status terminates progression. `ScenarioLabOrchestrator` is
the central engine: it loads and validates a spec, runs an isolated instance under
`data/lab_sessions/` that never shares `AuthoritativeState` with the live world, drives the Kernel
single-threaded, and performs post-run analysis. `BudgetGuardrail` is a second, budget-specific gate
(`OK` / `WARNING` / `BLOCKED`) layered on top of the three stage-level approval gates. The mutation
pipeline operates on a copy of the spec and rolls back on failure — the original is never mutated.
Metamorphic testing has 3 relation classes (symmetry, monotonicity, equivalence); a failing relation is
recorded, not treated as an abort.

The workflow sequence in Layer A drives the lab session state machine in Layer B — for example, running
`generate-simulation-setup` and `prepare-simulation-execution` corresponds to progressing a lab session
through its GENERATION and EXECUTION_SUPPORT stages. No source document states an exact 1:1 mapping
between the 7 workflows and the 6 stages, and this document does not assert one; read
[`lab_contract.md`](../simulation/lab_contract.md) for the authoritative session-state-machine view and
[`workflows.md`](workflows.md) for the authoritative per-workflow args/returns.

## 5. Quality Lanes: Test, Lab, and SimQ Audit

There are **three distinct quality/testing lanes** in this system:

1. **The dev-pipeline Test phase** — `test-scoper` runs scoped pytest inside `implement-ticket` and
   `implement-epic`, gating on `TESTS_FAILED`. This checks code correctness only.
2. **The simulation lab workflow chain** (Section 4 above) — simulation *behavior* discovery, hypothesis
   generation, and knowledge capture, human-gated at 3 stages.
3. **SimQ audit** (`simq-audit`, below) — a narrow calibration and anchor-drift maintenance lane for the
   10-pillar SimQ grading system specifically.

**SimQ audit** runs 7 phases, invoked via `/simq-audit`: Recalibrate → Classify Drift → Update Anchors →
Sync Docs → Parity Check → Verify → Report.
- **Recalibrate** runs `make simq-full-audit`/`-full`/`-slow` — the only non-judgment phase.
- **Classify Drift** classifies each flagged item as `EXPECTED_DRIFT` (must cite a specific commit or
  ticket), `REGRESSION`, `DA_NEEDED`, or `NO_ACTION`, and computes a rollup verdict of `no_regression`,
  `regression`, or `needs_da_decision`.
- **Update Anchors** edits `grade_anchors.json` and the anchor key lists, for `EXPECTED_DRIFT` items
  only; it gates on `ANCHORS_STILL_FAILING`.
- **Sync Docs**, **Parity Check**, and **Verify** (a DoD-style gate, `BLOCKED` on failure) follow, then
  **Report** branches deterministically on the verdict: `no_regression` returns `DONE_NO_TICKET`;
  otherwise it spawns one ticket via `ticket-scoper` and returns `NEEDS_TICKET`.

`simq-audit` never changes SimQ scoring formulas or pillar logic — `src/simulation_quality/*` is out of
scope for it; it only maintains calibration anchors and drift classification. It is standalone-invocable
and does not require or by default create a ticket — only the regression/DA-needed branch spawns one.

See [`audit_workflow.md`](../simulation_quality/audit_workflow.md) for the full phase-by-phase mechanics
and Do-Not list.

## 6. Observability and Where to Go Deeper

Agent activity is recorded in 3 append-only JSONL files under `agent-monitoring/`, joined by `run_id`
(and additionally by `seq` for `tools.jsonl`):

- **`runs.jsonl`** — one record per workflow invocation (`run_id`, `start_ts`, `end_ts` nullable,
  `workflow`, `tier`, `final_status`, `agent_count`, `duration_s`). Token and cost telemetry are
  explicitly not recorded — a documented gap.
- **`events.jsonl`** — one record per agent call, keyed by `run_id` and `seq` (`phase`, `agent`,
  `summary` capped at 200 characters, `status`, `tool_call_count`).
- **`tools.jsonl`** — one record per tool call, keyed to events via `run_id`+`seq` through a
  `.claude/current_run` sidecar file (`tool`, `input_summary` capped at 120 characters, `status`,
  `duration_ms`).

A retro process runs against this data on a cadence (5+ completed tickets, weekly, or before changing
agent prompts or tier rules, nudged by a `PostToolUse` hook), producing a report via
`generate_retro.py`. `validate.py` performs correspondence checks between the working log and the run
records.

A recent fix, `TCK-20260705-MONITORING-RUNID-JOIN`, audited 107 previously-flagged incomplete-looking
runs and confirmed all 107 were genuinely done (98 by direct match, 9 by terminal-status/child match),
leaving exactly 1 permanent documented exception (`TCK-20260623-TYPE-CHECKER`).

`docs/ai/agent_infrastructure_audit.md` scores the agent orchestration layer **8.0/10 — "Mature, gated,
not yet deterministic."** See that document for the full category breakdown, strengths, and risks; this
overview does not re-derive or re-score it.

**Note (as of 2026-07-05):** `docs/ai/workflows.md` does not yet document `simq-audit` as an 11th
workflow, and its phase lists for `create-tickets`, `generate-simulation-setup`,
`investigate-simulation-result`, and `compact-simulation-result` do not match the current
`.claude/workflows/*.js` phase arrays (this document cites the `.js` files directly for those four).
`docs/ai/skills.md` similarly does not yet list a `/simq-audit` skill entry. These are candidates for a
future documentation-maintenance ticket; this document does not modify those files.

### Where to go deeper

**Agents / Workflows / Skills**
- [`docs/ai/agents.md`](agents.md) — all 11 subagents: role, inputs, outputs, when to invoke
- [`docs/ai/workflows.md`](workflows.md) — per-workflow args, phase, and return-value tables
- [`docs/ai/skills.md`](skills.md) — full skill catalog

**Ticket Lifecycle**
- [`docs/ai/ticket-lifecycle.md`](ticket-lifecycle.md) — complete flow from request to closed ticket, worked example

**Simulation Lab**
- [`docs/simulation/lab_contract.md`](../simulation/lab_contract.md) — the lab session contract and `src/lab/`

**SimQ Audit**
- [`docs/simulation_quality/audit_workflow.md`](../simulation_quality/audit_workflow.md) — full phase mechanics and Do-Not list

**Observability**
- [`docs/agent-monitoring/schema.md`](../agent-monitoring/schema.md) — JSONL schemas and known limitations
- [`docs/guides/agent_monitoring.md`](../guides/agent_monitoring.md) — the retro process and query patterns
- [`docs/ai/agent_infrastructure_audit.md`](agent_infrastructure_audit.md) — scored technical audit (2026-07-03)

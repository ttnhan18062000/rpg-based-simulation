---
status: active
layer: ai
authority: P2
audience: developer
maturity: ready-for-discovery-epic
date: 2026-07-20
tags: [ai, workflows, hooks, agent-monitoring, schema, process-improvement]
---

# Idea: Provider-Agnostic Agent Orchestration (Claude Code + Codex)

> **Maturity: READY FOR DISCOVERY EPIC.** This plan may be approved to create a
> gated discovery epic only. It does not authorize a change to the current
> Claude Code workflow, monitoring corpus, or user entry points; implementation
> child tickets remain blocked until the decision-gate outputs below are approved.

## Problem

The repository has a mature agent-working system, but its executable surface is
primarily Claude Code-specific:

- `CLAUDE.md` is the principal durable instruction file.
- `.claude/agents/*.md` defines the project roles.
- `.claude/workflows/*.js` implements multi-agent orchestration.
- `.claude/skills/*/SKILL.md` exposes user-facing task patterns.
- `.claude/settings.json` supplies permissions and lifecycle hooks.
- Hook payload handling and `.claude/current_run` sidecars assume Claude Code.

The project wants Codex to execute the same development and simulation-agent
work without creating two independently evolving processes. Copying the Claude
configuration into a second provider tree would initially look equivalent but
would make prompt, phase, gate, and monitoring drift inevitable.

The desired outcome is **semantic parity**, not superficial file parity:

1. A request should follow the same lifecycle, artifact requirements, gate
   decisions, and recovery paths regardless of provider.
2. Claude Code and Codex should write comparable, attributable monitoring data
   to one shared corpus.
3. Platform differences (workflow invocation syntax, hook payloads, approval
   model, and subagent APIs) must be isolated behind adapters.
4. Any provider-specific behavior must be explicit, documented, and tested as
   an intentional divergence.

## Current-State Inventory

### Claude-owned entry points

| Concern | Current authoritative/executable location | Provider coupling |
|---|---|---|
| Global working rules | `CLAUDE.md` | Claude instruction filename and tool names |
| Role prompts | `.claude/agents/*.md` | Claude `Agent(...)` invocation conventions |
| Workflow runtime | `.claude/workflows/*.js` | Claude workflow/agent/bash APIs |
| Skills | `.claude/skills/*/SKILL.md` | Claude slash-command conventions |
| Hook registration | `.claude/settings.json` | Claude settings and hook payload shape |
| Hook state | `.claude/current_run`, `.claude/.tool_start` | Claude session/workflow lifecycle |
| Earlier cross-provider scaffolding | `.agents/` | Existing but stale; must be disposed of before new Codex work |
| Monitoring writers | `tools/agent-monitoring/*.py` | Mostly portable; sidecar payload is coupled |
| Gates | `tools/gate_checks/*.py` | Already portable Python checks |
| Project artifacts | `tickets/`, `staging_artifacts/`, `stored_artifacts/`, `docs/` | Provider-neutral |

### Existing `.agents/` precedent — mandatory disposition gate

`.agents/` already contains rules, skills, workflows, and task scaffolding. It predates the current Claude-centered system and is not a valid Codex adapter as-is: its rules and ticket shape are materially older, at least one workflow is a placeholder, and some skills are historic copies of their Claude equivalents. Leaving it unclassified would create a third, ambiguous source of agent instructions.

Before any provider-neutral implementation begins, a dedicated audit must classify every `.agents/` path as one of:

- **retain and migrate** — current enough to become a generated/shared asset;
- **replace** — still needed, but superseded by a canonical contract output;
- **archive/retire** — historic material that must no longer be discovered as active provider guidance.

The audit must decide the final Codex skill location. It may retain `.agents/skills/` only after its content is regenerated or brought into conformance; it must not be treated as an already-working Codex layer.

### Roles to preserve

The provider-neutral role catalog must include every role currently present in
`.claude/agents/`:

- `ticket-scoper`, `investigator`, `concern-investigator`, and `planner`
- `architecture-reviewer`, `mechanics-auditor`, `parity-updater`, and
  `security-reviewer`
- `implementer`, `test-scoper`, and `done-checker`
- `world-debugger` and `simulation-analyst`

### Workflows to preserve

The migration covers all existing project workflows, not only the main ticket
pipeline:

- Development: `create-tickets`, `implement-ticket`, `implement-epic`, and
  `simq-audit`.
- Simulation/lab: `generate-simulation-setup`,
  `prepare-simulation-execution`, `register-simulation-result`,
  `investigate-simulation-result`, `propose-simulation-enhancements`,
  `compact-simulation-result`, and `update-knowledge-store`.

### Hooks to preserve semantically

The current hooks implement five concerns:

1. Pre/post-tool telemetry and duration capture.
2. Context-search/Graphify guidance before raw repository search.
3. Incremental Graphify update after relevant edits.
4. Retro-cadence advisory nudge.
5. Epic-staleness advisory nudge.

Codex supports ten documented lifecycle hooks through trusted project `.codex/` configuration: `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`, `UserPromptSubmit`, `SubagentStop`, `Stop`, `SessionStart`, and `SubagentStart`. This was verified against the current [Codex Hooks documentation](https://learn.chatgpt.com/docs/hooks.md) on 2026-07-20. The current Claude-hook mapping uses only the subset relevant to its five concerns; the adapter design must nevertheless validate actual event payload shape, matcher behavior, trust requirements, and timing with provider fixtures before treating any hook mapping as equivalent.

## Proposed Architecture

### 0. Preconditions and decision gate

No runtime, hook, or monitoring write-path migration starts until these decisions are recorded in an ADR or the parent epic:

1. `.agents/` disposition and the final Codex instruction/skill locations.
2. The contract representation (reviewable YAML, validated Python models, or both).
3. Execution identity: immutable execution key, human-readable run reference, and ticket linkage.
4. Cross-platform concurrent-write strategy for the shared monitoring corpus.
5. The replay-only initial Codex validation method and the explicit criteria that must be met before any isolated live run.

This gate makes the delivery sequence executable rather than treating unresolved schema and ownership questions as implementation details.

### Approval model and exit gate

This proposal is approvable now as a **discovery epic**, with an intentionally
narrow mandate: produce evidence, decision records, and isolated replay
harness code only. It does not authorize production provider runtime changes.
The discovery epic is complete only when it has delivered:

1. A `.agents/` disposition report and an approved active-location map.
2. A contract-format ADR, including source ownership and adapter-generation or
   conformance strategy.
3. An execution-identity and monitoring-writer ADR, backed by portability and
   concurrent-write test evidence.
4. A Codex capability matrix, verified from current official documentation and
   provider fixture experiments.
5. A replay-fixture specification and proof that the first Codex slice can run
   without editing tickets, invoking production hooks, or appending monitoring
   records.

Only after those five outputs are reviewed and approved may a follow-on
**implementation epic** be created. That implementation epic starts with the
replay-only vertical slice; it does not inherit permission to alter the live
Claude workflow merely because this discovery plan was approved.

### Tier compatibility and containment

The parent remains an ordinary `epic`-tier ticket: it scopes and tracks child
work but performs no direct implementation. Its children are ordinary scoped
tickets with an additional, one-time containment rule for this initiative:
they may create only isolated contract, replay, fixture, or diagnostic code;
they may not modify provider production workflows, hooks, monitoring writers,
or durable ticket artifacts. This proposal does not create a new global tier.
If this constrained-discovery pattern is reused after this initiative, promote
it to `docs/guidelines/` and the global workflow rules before reuse.

### 1. Shared contract first

Add a provider-neutral contract under a new repository-owned location, proposed
as `agent-orchestration/`. This directory is a source specification, not a
second implementation:

```text
agent-orchestration/
  README.md                         # ownership and compatibility policy
  contract.yaml                     # version, providers, global invariants
  agents/<role>.yaml                # role inputs, outputs, gates, tool intent
  workflows/<workflow>.yaml         # phases, tiers, transitions, statuses
  skills.yaml                        # skill-to-workflow/role mappings
  monitoring-schema.yaml            # current + next schema generation
  hook-events.yaml                  # normalized lifecycle event contract
  intentional-divergences.md        # provider-specific, reviewed differences
```

The contract owns semantics: names, inputs/outputs, phases, transition rules,
statuses, artifact obligations, and monitoring fields. It must not embed Claude
or Codex invocation syntax.

### 2. Thin provider adapters

Keep provider-owned configuration separate and deliberately small:

```text
.claude/                            # Claude Code adapter
.codex/                             # Codex adapter
AGENTS.md                           # shared Codex-readable project guidance
```

Adapters translate the shared contract into provider-native configuration:

| Shared intent | Claude adapter | Codex adapter |
|---|---|---|
| Durable project guidance | `CLAUDE.md` | `AGENTS.md` |
| Subagent role | `.claude/agents/*.md` | Codex role config / subagent instruction files |
| Workflow entry point | `.claude/workflows/*.js` | Codex command/skill adapter calling shared runtime |
| Reusable skill | `.claude/skills/*/SKILL.md` | **TBD by `.agents/` disposition audit**; then a generated Codex skill or repository-local plugin skill |
| Lifecycle hook | `.claude/settings.json` | `.codex/hooks.json` or `.codex/config.toml` |

The adapters may contain provider-specific payload parsing, invocation,
permissions, and hook registration. They may not silently redefine workflow
phases, terminal statuses, gate policy, or artifact requirements.

### 3. Shared workflow runtime

Move orchestration decisions that are currently embedded in Claude JavaScript
into a provider-neutral runtime, proposed as Python under
`tools/agent-orchestration/` and always invoked with `.venv/bin/python`.

The runtime should own:

- ticket/tier resolution and phase-state persistence;
- phase transition and resume decisions;
- gate execution and structured results;
- artifact checks and finalization self-checks;
- normalized monitoring writes;
- provider-agnostic exit statuses.

It should not own model invocation. A provider adapter dispatches a named role,
receives a response matching the role contract, and returns it to the runtime.
This keeps platform API differences at the edge.

### 4. One monitoring corpus, versioned schema

Continue using the existing append-only files:

```text
agent-monitoring/runs.jsonl
agent-monitoring/events.jsonl
agent-monitoring/tools.jsonl
```

Do **not** create Claude-only and Codex-only primary stores. Both providers
should append records using one schema so the existing validator, retros, and
dashboard can compare outcomes directly.

The next schema generation must add, for every new record where applicable:

| Field | Purpose |
|---|---|
| `provider` | `claude-code` or `codex` |
| `runtime` | surface/version, such as CLI or desktop app |
| `execution_id` | unique workflow invocation identifier |
| `ticket_id` | stable work-item ID, distinct from an execution |
| `workflow_version` | shared orchestration-contract version |
| `hook_schema_version` | normalized hook payload generation, on tool records |

`run_id` currently often doubles as a ticket identifier. That cannot remain
the sole execution key once the same ticket can be run by both providers. The
migration must make `(provider, execution_id)` unique and preserve `ticket_id`
as the cross-run join key. The exact key format is a precondition, not an implementation-time choice. Old records are read as `provider: claude-code` and retain their existing identifier shape; no destructive history rewrite is required.

#### Concurrent-write and portability requirement

The shared corpus has a real concurrent-write failure history. The current `tools.jsonl` writer uses POSIX `fcntl.flock`, which was introduced after interleaved JSONL writes and has no Windows equivalent. A Codex adapter must not become another writer until a cross-provider write contract is proven.

The design investigation must compare at least:

1. A platform-neutral lock-file protocol with bounded retry and stale-lock recovery;
2. A single local monitoring-writer process/queue that owns JSONL appends;
3. Provider-local append journals with a deterministic merger into the shared corpus.

The chosen design must preserve append-only source data, reject malformed partial lines, handle concurrent Claude/Codex writers, and have a tested failure/recovery story on every supported development platform.

### 5. Normalized hook event boundary

Create a shared hook-event model and provider-specific parsers:

```text
provider payload -> provider adapter -> normalized hook event -> shared hook logic
```

The normalized event carries provider, provider session, execution ID, phase,
role, event name, tool name, safe input summary, timestamp, duration, and
result status. Shared code performs logging, sidecar/state updates, retro
checks, stale-epic checks, and Graphify decisions.

Monitoring must remain best-effort: a failed monitoring append cannot fail a
user workflow. However, failures should be observable through a separately
recorded local diagnostic or explicit warning whenever possible.

## Work Breakdown

### Workstream A — Baseline and contract

1. Audit and dispose of the legacy `.agents/` tree before creating any new Codex adapter files; record retained, replaced, and retired paths.
2. Freeze and inventory the current Claude behavior: agents, skills,
   workflows, phases, statuses, hooks, permissions, artifacts, and commands.
3. Reconcile existing count/document drift before making it canonical (for
   example, actual role and status lists versus older summary tables).
4. Verify Codex capability claims from current official documentation and provider-level fixture experiments; record the resulting capability matrix.
5. Define the shared contract format, ownership, versioning, and change rules.
6. Write an intentional-divergence policy: allowed difference, justification,
   approval, expiry/review date, and test coverage.

### Workstream B — Shared policies and prompts

1. Extract platform-neutral rules from `CLAUDE.md` into shared policy documents.
2. Create `AGENTS.md` that references the same policy without Claude-specific
   tool names.
3. Convert every role into a shared role specification plus concise provider
   prompt wrappers.
4. Centralize tag-to-skill and path-to-skill routing in executable shared data
   rather than maintaining parallel prose tables.

### Workstream C — Workflow runtime and gates

1. Define a phase-state model and role-response schema that support new, resumed, failed, and completed executions without relying on a provider session.
2. Build a replay runner that evaluates recorded Claude workflow inputs/outputs against the shared contract without changing the live Claude workflow.
3. Extract provider-neutral transition and status logic into pure, testable models; do not redirect production Claude workflow calls during this workstream.
4. Reuse existing `tools/gate_checks/` modules as the authoritative mechanical gate layer.
5. Use the current Claude workflow as the behavioral reference and require contract/replay conformance before any live Codex dispatch.

### Workstream D — Codex adapter

1. Add trusted project `.codex/config.toml` and/or `.codex/hooks.json` with
   only necessary repo-scoped settings.
2. Add Codex role configuration and Codex skills corresponding to the shared
   catalog.
3. Implement a replay-only Codex workflow adapter for `implement-ticket`; it must not edit tickets, write monitoring records, or invoke production hooks.
4. Map Codex tool/approval and subagent behavior to the contract; record any
   deliberate differences in `intentional-divergences.md`.
5. Require `.venv/bin/python` for all project Python actions and adapters.

### Workstream E — Hooks and monitoring migration

1. Treat monitoring normalization as its own bounded discovery and migration effort. Inventory all historical run/event/tool schema generations, legacy timestamp shapes, identifier conventions, and known attribution defects.
2. Define the normalized hook-event schema and versioned provider payload
   parsers.
3. Choose and test the cross-platform concurrent-write design before adding a Codex writer to the shared JSONL corpus.
4. Extract shared telemetry, nudge, and Graphify hook logic from the current Claude hook scripts.
5. Install matching Claude and Codex hook adapters only after the normalized event and writer contracts pass fixture and concurrency tests.
6. Introduce schema-generation fields and one shared read-normalization module; remove duplicated legacy interpretation where feasible.
7. Update query, validation, retro generation, dashboard ingestion, and API models to filter/group by provider and execution ID.
8. Fix current query compatibility for legacy non-string timestamps as part of the reader-normalization work.
9. Preserve historical Claude records via read-time defaults and document all legacy interpretation rules in one shared normalization module.

### Workstream F — Verification and operations

1. Add contract conformance tests for both provider adapters.
2. Add fixture-based tests that feed equivalent Claude and Codex normalized
   events and assert identical monitoring records.
3. Test the main standard, hotfix, epic, failure, resume, security, parity, and
   finalization paths in both adapters.
4. Add a CI target that fails when the shared contract and an adapter diverge.
5. Update the dashboard and retro reports with a provider filter plus a clear
   mixed-provider aggregate view.
6. Publish a concise operator guide for setup, hook trust, provider selection,
   fallback behavior, and rollback.

## Delivery Order

The work should be implemented as a sequenced epic, not one broad migration:

0. **Preconditions and disposition** — resolve the five decision-gate items, especially the `.agents/` audit and execution identity.
1. **Capability/baseline inventory** — no production runtime behavior change.
2. **Monitoring discovery** — choose and prove a portable concurrent-write and read-normalization design before adding a Codex writer.
3. **Shared policy and role contracts** — generate/validate adapters while the production Claude workflow remains unchanged.
4. **Codex replay-only vertical slice** — run `implement-ticket` contract and phase replay against recorded Claude fixtures; do not edit tickets, write monitoring records, invoke production hooks, or redirect the live Claude pipeline.
5. **Codex parity test suite** — prove main lifecycle and monitoring parity.
6. **Shared workflow state/gate runtime** — adopt it behind the proven Claude and Codex adapters only when shadow parity demonstrates that it is safer than maintaining the existing Claude runtime.
7. **Remaining development and simulation workflows**.
8. **Dashboard/retro provider views and operational documentation**.
9. **Cutover review** — decide whether provider-specific legacy workflows can
   be retired.

The first Codex vertical slice is deliberately narrow: `implement-ticket`
with standard and hotfix tiers, shared gate checks, shared artifacts, and
provider-attributed monitoring. It validates the core architecture before the
simulation workflows add scope.

## Discovery-Epic Acceptance Criteria

- The five Approval model and exit gate outputs are complete, evidence-backed, and approved.
- The `.agents/` audit leaves exactly one documented active Codex instruction/skill location.
- The replay-only `implement-ticket` slice proves it does not edit tickets, invoke production hooks, or append monitoring records.
- No implementation ticket is opened until discovery approval is recorded.

## Target Implementation Acceptance Criteria

- A documented, versioned shared contract exists and names every current role,
  workflow, phase, tier, status, skill, hook concern, and artifact obligation.
- Claude and Codex both run `implement-ticket` through the same lifecycle and
  shared gate checks for standard and hotfix tickets.
- The same ticket can have distinct Claude and Codex executions without
  monitoring-key collision.
- All new monitoring records identify provider, runtime, execution, ticket, and
  contract version; legacy records remain readable without rewriting JSONL.
- Existing monitoring validation, query, retro, and dashboard views remain
  functional and gain provider-aware behavior.
- Claude and Codex hook adapters produce equivalent normalized telemetry for
  equivalent lifecycle events.
- CI includes provider-adapter contract conformance and fixture parity tests.
- Intentional provider differences are visible in one reviewed registry; no
  undocumented workflow/phase/status differences remain.
- Codex setup is documented, including project trust and hook-review steps.
- Discovery-epic approval is explicitly distinguished from implementation
  authorization, and each decision-gate output has an assigned acceptance
  artifact before implementation tickets can be created.

## Non-Goals

- Replacing Claude Code immediately or deleting the current `.claude/` tree.
- Rewriting historical monitoring records in place.
- Making provider session IDs, tool payloads, or approval UIs identical.
- Forcing every Codex feature to mimic a Claude API when the shared contract
  can express the intent more safely.
- Altering simulation engine behavior or the mechanics/parity source of truth.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Two sources of truth emerge | Shared contract is the only semantic authority; CI checks both adapters. |
| Provider terminology leaks into policy | Keep provider syntax in adapter files only; review shared docs for tool-name coupling. |
| Monitoring joins collide across providers | Separate `ticket_id` from unique execution identity before Codex writes. |
| Existing `.agents/` scaffolding becomes a third source of truth | Complete its retain/replace/archive disposition before enabling Codex discovery. |
| Claude and Codex concurrently corrupt JSONL | Select and stress-test a portable writer protocol before Codex appends to the shared corpus. |
| Hook behavior differs by payload/timing | Normalize at the adapter boundary and use shared fixtures. |
| Migration breaks stable Claude flow | Keep it untouched through contract, fixture, and Codex shadow validation; migrate only after parity evidence. |
| Overbuilding the shared runtime | Start with one vertical slice; leave simulation workflows on existing adapters until proven. |
| Discovery work expands into production migration | Enforce the child-ticket containment rule; only isolated contract, replay, fixture, or diagnostic code is in scope until the exit gate is approved. |
| Historic data quality masks new regressions | Centralize legacy normalization and distinguish legacy warnings from current-schema failures. |
| Untrusted Codex project skips hooks | Document trust as a prerequisite and expose hook health in diagnostics. |

## Open Decisions

1. Should the shared contract be YAML, Python data models, or both (YAML for
   reviewable definitions with generated Python validation is the initial
   recommendation)?
2. Should the provider-neutral runtime call providers directly, or should it
   emit phase requests for provider wrappers to execute? The latter keeps
   provider APIs outside the runtime and is preferred.
3. Which stable format should replace ticket-ID-as-run-ID: UUID execution IDs,
   deterministic provider/ticket/attempt identifiers, or both? A deterministic
   human-readable ID plus a generated UUID is likely best for operations.
4. Are Codex project hooks configured directly in `.codex/hooks.json` or
   packaged as a repository-local plugin? Start with `hooks.json`; package only
   if reusable outside this repository.
5. Which concurrent-write strategy is portable and operationally simplest for
   the shared JSONL corpus?

### Resolved Decision

- **Initial Codex slice:** replay-only. An isolated live ticket is deferred until the execution-identity and portable-writer decisions are implemented and replay parity passes.

## Related Material

- `CLAUDE.md`
- `docs/ai/system_overview.md`
- `docs/ai/agents.md`
- `docs/ai/workflows.md`
- `docs/ai/skills.md`
- `docs/ai/ticket-lifecycle.md`
- `docs/agent-monitoring/schema.md`
- `docs/guides/agent_monitoring.md`
- `docs/guidelines/agent_working_environment.md`
- `docs/plans/archive/agent_infrastructure/idea_agent_monitoring_derived_index.md` (archived — shipped)
- `docs/ai/agent_infrastructure_audit.md`
- `docs/architecture/agent_orchestration_contract.md`

---

*Raised: 2026-07-20, after a current-state audit of the Claude Code-oriented
agent system and a provider-capability review for Codex. This proposal is ready
for a **gated discovery epic**. Implementation tickets may be created only
when the Approval model and exit gate outputs are approved.*

# Project Instructions

## Priority Order

1. Safety and user instruction
2. Repository architecture integrity
3. Traceability and workflow discipline
4. Tests and verification
5. Local convenience

---

## Hard Rules

* Do not act without validating context.
* Do not guess when uncertainty affects behavior or architecture.
* Do not ask questions already answered by repo patterns.
* Do not create hidden or implicit durable behavior.
* Do not mutate durable state outside authoritative flows.
* Do not break determinism.
* Do not expose raw domain models from APIs.
* Do not leave changes untested or untraceable.
* Every implement-ticket workflow run (including hotfix) must record a run entry and at least one event entry to `agent-monitoring/`. Monitoring write failure must never fail the workflow.

---

## Context Scan (Mandatory)

Before any implementation, check:

* `tickets/`
* `docs/` (especially the Mechanics Bible in `docs/mechanics/`)
* `stored_artifacts/`
* relevant code and tests

Detect and stop on duplicate work, conflicting requirements, or architectural mismatch.

---

## Clarification Rule

Ask only if it changes outcomes:

* multiple valid implementations
* unclear acceptance criteria
* conflict with existing system
* missing critical context

Otherwise, follow existing patterns.

---

## Workflow Rule

### Before Work

- Scan tickets, docs, stored artifacts, relevant code, and tests.
- Identify reuse opportunities and conflicts.
- Create `tickets/inprogress/{ticket_id}.md`.
- **Standard/epic only:** Create `staging_artifacts/{ticket_id}/` with `plan.md`, `investigation.md`, `test_plan.md`.
- **Hotfix:** No staging artifacts required — self-evident intent is captured in the ticket itself.

### Required Artifacts (standard/epic only)

At minimum: `plan.md`, `investigation.md`, `test_plan.md`.

Ticket must include: title, summary, scope, out of scope, acceptance criteria, related docs/tickets/artifacts, assumptions/open questions, current status.

### During Work

- Keep ticket and artifacts aligned with actual work.
- Update plan when implementation changes.
- Update investigation when new findings appear.
- Validate continuously against repo patterns and architecture.

### After Work

- Finish ticket, move to `tickets/done/`.
- Append to the **bottom** of `tickets/working_log.csv` (never insert after the header).
- **Standard/epic only:** Move staging artifacts to `stored_artifacts/`.
- Update related docs.
- Clean up: `rm -rf data/runs/* reports/release_proof/*`.
- Verify no leftover staging/temp files remain.

### Commit Convention

Reference the ticket ID in every commit for this ticket's work:

```
TCK-YYYYMMDD-SHORT-SCOPE: Brief description of change
```

### Tier Routing

| Tier | Pipeline | Use when |
|---|---|---|
| `hotfix` | Scope → Implement → Test → Parity → Verify → Finalize | Bug fix or minimal targeted change with self-evident intent |
| `standard` | Full 9-phase pipeline | Any new feature, refactor, or substantive repair |
| `epic` | Scope only — tracks child tickets | Large multi-ticket initiative; no direct implementation |

---

## Ticket Format

**File name:** `TCK-YYYYMMDD-SHORT-SCOPE.md` (uppercase, hyphen-separated)

**Location:** `tickets/inprogress/{ticket_id}.md` → `tickets/done/{ticket_id}.md`

**Required sections (in order):**

```
# TCK-YYYYMMDD-SHORT-SCOPE

## Title
## Status         (OPEN | INPROGRESS | BLOCKED | DONE)
## Tier           (hotfix | standard | epic)
## Type           (bug | feature | refactor | chore | repair)
## Priority       (P0 | P1 | P2)
## Request Summary
## Scope
## Out of Scope
## Acceptance Criteria
## Related Tickets
## Related Docs
## Related Stored Artifacts
## Related Code Areas
## Assumptions / Open Questions
## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
```

---

## Testing Rule

- Run relevant existing tests before claiming completion. Do not run the entire suite (`pytest tests/`) — scope to the domain under modification or use `pytest -m "not slow"`.
- Add or update tests whenever behavior changes.
- Prefer deterministic, isolated, readable tests.
- Test meaningful behavior, not superficial coverage.

**Required coverage:** normal flow, edge cases, failure modes, regression-prone paths.

**Architecture tests:** verify read-only logic did not mutate live state, authoritative application path was used, typed records serialize/deserialize correctly.

---

## Architecture Rule

### Core Boundaries

- Decision logic reads state. It does not authoritatively mutate durable state.
- Durable changes must be represented through typed records/updates.
- Authoritative application is the only place durable state should be committed.
- Shared world behavior should go through systems/registries, not scattered local hacks.
- API/routes present shaped read models through presenters/schemas, not raw domain objects.

### Durable State Rule

If something survives beyond the current tick or current function call, it must have a typed model, a stable location in entity/world/registry state, a defined lifecycle, inspection/debug visibility, and tests.

Do not store durable meaning in `reason` strings, free-form `metadata`, comments, or temporary local variables.

### Strategic/Tactical Rule

- Strategy owns enduring direction. Tactics own immediate execution.
- Do not solve strategic problems by stacking more tactical goal scoring.

### Uncertainty Rule

- Vague leads stay vague until evidence narrows them.
- Do not collapse investigation into exact coordinates too early.

---

## Definition of Done

A task is not done unless all are true:

- Implementation matches accepted scope
- Architecture constraints were respected
- Ticket is updated and moved to `tickets/done/`
- Staging artifacts are complete and migrated to `stored_artifacts/`
- Tests were run and updated
- Docs were updated if behavior changed
- Working log entry was added (`tickets/working_log.csv`)
- No important decision is undocumented
- Repo state is consistent
- Temporary run data cleaned: `data/runs/`, `reports/release_proof/`
- No known material gap is left unstated
- Agent monitoring records written: run entry in `agent-monitoring/runs.jsonl`, at least one event in `agent-monitoring/events.jsonl` _(guaranteed by workflow — not verified by done-checker)_

---

## Authoritative Mechanics Rule

The **Mechanics Bible** (`docs/mechanics/`) and the **Engine Contracts** (`docs/engine/`) are the definitive sources for simulation laws, formulas, and pipeline behavior.

- **Consistency**: All logic changes MUST be consistent with the laws defined in the Mechanics Bible.
- **Parity**: Documentation and source code must remain in 100% semantic parity. If logic changes, update the corresponding doc AND the parity ledger entry (`docs/parity_ledger/`) in the same session.
- **Reference**: When explaining or implementing mechanics, cite the specific chapter in `docs/mechanics/` or the contract ID in `docs/engine/`.
- **Divergence**: Any intentional behavior change that differs from the Mechanics Bible MUST be recorded in `docs/guidelines/v2_intentional_divergences.md` with a rationale class and verification path.
- **Precedence**: In case of ambiguity between legacy behavior and the V2 Mechanics Bible, the Mechanics Bible takes precedence.

### Mechanics Bible — `docs/mechanics/`

All chapters are Certified Level 1 (Authoritative). Every formula is verified for bit-identical parity with source code.

| Chapter | File | Covers |
|---|---|---|
| 01 | `01_entity_anatomy.md` | Core attributes, derived stats, biological pressures, XP scaling |
| 02 | `02_combat_laws.md` | Damage formula, tactical modifiers, durability decay, victory outcomes |
| 03 | `03_economic_laws.md` | Atomic conservation, harvesting, trade, crafting |
| 04 | `04_strategic_cognition.md` | Goal hierarchy, interruption resistance, knowledge management, perception |
| 05 | `05_world_evolution.md` | Tick-to-day time, regional trauma, ecology, calamities |
| 06 | `06_worldbuilding_foundation.md` | Declarative topology, sovereignty, distribution, integrity validation |

Also: `content_usage_matrix.md` (content resolution rules), `regional_sovereignty.md` (region boundaries).

### Engine Contracts — `docs/engine/`

The master index is `project_lawbook_m10.md`. Key contracts:

| File | Covers |
|---|---|
| `kernel.md` | 6-phase deterministic loop (Init → Governance → Scheduling → Packetization → Resolution → Persistence) |
| `authoritative_pipeline.md` | 17-phase refinement sequence for world mutation |
| `authoritative_mutation_pipeline_contract.md` | Mutation rules and apply-path law |
| `governance_logic.md` | Governance and eligibility rules |
| `performance_contract.md` | Hardware classes (A/B/C) and scaling limits |
| `known_limitations.md` | Current scope boundaries |

### Core State — `docs/core/`

| File | Covers |
|---|---|
| `state.md` | Immutability law, authoritative vs non-authoritative state partitioning |
| `entities.md` | Entity lifecycle and identity |
| `attributes_and_classes.md` | Attribute definitions and class rules |

### Parity Ledger — `docs/parity_ledger/`

Machine-readable parity tracking. One YAML file per subsystem, schema in `schema.json`.

Each entry has: `id`, `text`, `status` (`verified` / `divergent` / `missing` / `unsupported` / `legacy_verified`), `priority` (`P0`/`P1`/`P2`), `v2_evidence`, `test_path`, `divergence_note`.

**When a behavior changes:** find the relevant parity ledger entry and update `status` and `v2_evidence`. If no entry exists, add one. `P0` entries require a passing `test_path`.

| File | Subsystem |
|---|---|
| `substrate.yaml` | World generation, authoritative objects, determinism |
| `combat_movement.yaml` | Combat resolution, movement, legality |
| `strategic_cognition.yaml` | AI goal hierarchy, leads, attention bounds |
| `town_resource.yaml` | Resource nodes, harvesting, crafting, economy |
| `progression.yaml` | XP, rewards, skill advancement |
| `social_narrative.yaml` | Reputation, relationships, social events |
| `world_dynamics.yaml` | World evolution, ecology, calamities |
| `infrastructure.yaml` | Replay, telemetry, observability, workers |

### Intentional Divergences — `docs/guidelines/v2_intentional_divergences.md`

The canonical record of V2 behavior shifts from legacy. Any new divergence must be added here with a rationale class (`Hardened` / `Enforced` / `Unified` / `Stabilized` / `Bounded` / `Bug Fix` / `Intentional Gameplay Change`) and a `Verification` test path.

### Other Active Doc Areas

- `docs/architecture/` — ADRs (adr-004 watchdog, adr-005 performance, world assembly, world repository layout)
- `docs/combat/` — Combat rulebooks per milestone (m1–m7)
- `docs/strategy/` — Bounded cognition contracts and test matrices
- `docs/guidelines/design_patterns.md` — Coding and design conventions
- `docs/compliance/checklist.md` + `gap_analysis.md` — Compliance tracking
- `docs/testing/v2_test_taxonomy.md` — Test classification rules

---

## Proactive Tool Use

Some tools should be invoked automatically based on the task — the user does not need to mention them.

### Always auto-invoke (no user prompt required)

| Trigger | Action |
|---|---|
| "how does X work?" or explaining an unfamiliar module | Read `graphify-out/GRAPH_REPORT.md`, then `graphify explain "<X>"` |
| "how does X relate to Y?" or cross-module question | `graphify path "<X>" "<Y>"` |
| "where is X defined/used?" | `graphify query "<X>"` |
| Searching across more than 3 files | Spawn `Explore` agent instead of sequential Bash greps |
| Starting implementation on an unfamiliar module | Read `GRAPH_REPORT.md` for community structure before touching code |
| `docs/REGISTRY.yaml` exists + user asks about prior work or related docs | Query registry by `related_code_areas` or `layer` — do not scan raw directories |

### Require explicit user opt-in (never auto-invoke)

| Tool | Why |
|---|---|
| `Workflow` (`implement-ticket`, `investigate-simulation-result`, etc.) | Spawns many agents, costs real tokens — user must request the scale |
| `git push`, PR creation, external service calls | Irreversible or visible to others |

The boundary is: **single read/query tools are free to invoke proactively; multi-agent orchestration requires the user to ask**.

---

## Graphify Integration

This project has a graphify knowledge graph at `graphify-out/`.

- Before answering architecture or codebase questions, read `graphify-out/GRAPH_REPORT.md` for god nodes and community structure.
- For cross-module questions ("how does X relate to Y"), prefer `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` over grep — these traverse extracted and inferred edges instead of scanning files.
- After modifying files under `src/` or `tests/`, run `graphify update .` to keep the graph current (AST-only, no API cost). Do not run if changes are only to docs, configurations, or non-code files.
- Use `/graphify` to build or rebuild the full graph.

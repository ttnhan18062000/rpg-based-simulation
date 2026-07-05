---
status: active
layer: ai
authority: P1
audience: developer
---

# Subagents

Subagents are focused system-prompt files in `.claude/agents/*.md`. Each agent owns exactly one responsibility in the task pipeline. They are invoked by workflows or directly from the main session.

**Invocation pattern:**
```python
Agent(subagent_type="agent-name", prompt="task description with all needed context")
```

Within a workflow script, the `agentType` option loads the agent's system prompt:
```js
await agent("do X", { agentType: 'agent-name' })
```

---

## Ticket Lifecycle Agents

These agents handle the pre-implementation and post-implementation phases of a development ticket.

### `ticket-scoper`

**Role:** Creates a correctly-formatted ticket and scans for conflicts before any work begins.

**What it does:**
- Scans `tickets/inprogress/`, `tickets/done/`, `docs/`, `stored_artifacts/`, and relevant source files for duplicate work, conflicting requirements, or architectural mismatches
- Produces `tickets/inprogress/TCK-YYYYMMDD-SHORT-SCOPE.md` with all required sections
- Creates `staging_artifacts/{ticket_id}/`

**Inputs:** A request description (free text) or an existing ticket path.

**Outputs:**
- Ticket file at `tickets/inprogress/{ticket_id}.md`
- Staging directory
- Conflict report (if any)
- `suggested_skills` list (skill/agent invocations mapped from the ticket's `Process/Skill-signal` tags — e.g. `debugging` -> `/debugging-strategies` or `world-debugger`; empty if no tag maps)

**When to invoke directly:** When you want to draft a ticket for human review before running the full `implement-ticket` workflow.

---

### `investigator`

**Role:** Deep-reads the affected codebase and produces the two mandatory pre-plan artifacts.

**What it does:**
- Reads the ticket, all "Related Code Areas" files, relevant `docs/mechanics/` and `docs/engine/` chapters, and `docs/parity_ledger/` for overlapping entries
- Searches `stored_artifacts/` and `tickets/done/` for prior work in the same area (including tag-based matches against `docs/REGISTRY.yaml`, per `docs/guides/ticket_tagging.md`)

**Inputs:** Ticket ID. Reads `tickets/inprogress/{ticket_id}.md`.

**Outputs:**
- `staging_artifacts/{ticket_id}/investigation.md` — current behavior at `file:line`, mechanics constraints, parity ledger overlap, risks, anti-drift hazards
- `staging_artifacts/{ticket_id}/test_plan.md` — regression surface, new tests required per AC, scoped pytest commands

**When to invoke directly:** When an existing ticket needs a fresh investigation before planning (e.g., investigation.md is stale after scope change).

---

### `planner`

**Role:** Converts investigation findings into an ordered, implementer-ready plan.

**What it does:**
- Reads the ticket + investigation.md + test_plan.md
- Produces ordered steps, each naming specific files and changes, with scope guards and dependency map
- Maps every step to one or more acceptance criteria
- Flags unresolved questions rather than deciding them unilaterally

**Inputs:** Ticket ID + investigation artifacts already written.

**Outputs:** `staging_artifacts/{ticket_id}/plan.md`

**When to invoke directly:** When the investigation is done but the plan needs revision without re-investigating.

**Critical rule:** If plan.md contains "Unresolved Questions", the `implement-ticket` workflow pauses for human input before proceeding to implementation.

---

### `architecture-reviewer`

**Role:** Validates a plan against architecture rules before any code is written.

**What it checks:**
- Durable state rule (no direct mutation, no meaning in `reason`/`metadata` strings)
- API boundary (no raw domain models, shaped read models only)
- Systems/registries (shared behavior through registries, not local hacks)
- Strategy/tactics boundary
- Mechanics Bible compliance (reads relevant `docs/mechanics/` chapters)
- Engine contract compliance (`docs/engine/authoritative_pipeline.md` for pipeline changes)
- Parity ledger impact — flags P0 entries that will be affected

**Inputs:** `staging_artifacts/{ticket_id}/plan.md` + ticket.

**Outputs:** `APPROVED` / `NEEDS_CHANGES` / `BLOCKED` verdict with violation list and parity entries affected.

**Gate behavior:** The `implement-ticket` workflow halts on `NEEDS_CHANGES` or `BLOCKED` and returns the violations. Fix the plan, then re-run with `ticket_id`.

---

### `done-checker`

**Role:** Verifies all 11 Definition-of-Done conditions before a ticket can close.

**The 11 conditions:**
1. Implementation matches accepted scope
2. Architecture constraints respected
3. Ticket updated and in `tickets/inprogress/`
4. Staging artifacts complete (`plan.md`, `investigation.md`, `test_plan.md`)
5. Tests run and updated
6. Docs updated if behavior changed
7. `tickets/working_log.csv` entry added
8. No undocumented decisions
9. Repo state consistent
10. `data/runs/` and `reports/release_proof/` cleaned
11. No material gaps unstated

**Inputs:** Ticket ID. Reads the ticket, staging artifacts, test results, and parity ledger.

**Outputs:** `READY_TO_CLOSE` or `BLOCKED` with a per-condition table showing evidence.

**When to invoke directly:** Before manually closing a ticket that was implemented outside the workflow.

---

## Implementation Agents

### `implementer`

**Role:** Writes the code changes described in `plan.md`.

**Constraints pre-loaded:**
- Decision logic reads state only — never mutates durable state directly
- All durable changes through typed records and the authoritative application path
- No raw domain models from APIs
- No unnecessary abstractions, no half-finished implementations
- No comments unless WHY is non-obvious

**Inputs:** Approved `staging_artifacts/{ticket_id}/plan.md` + investigation.md.

**Outputs:**
- Code changes in `src/`
- Implementation Notes written back to the ticket's `Implementation Notes` section
- Deviations from the plan written to `staging_artifacts/{ticket_id}/plan.md`
- Structured report: files changed, `behavior_changed` boolean, parity subsystems affected, implementation summary

**When to invoke directly:** When re-running a single implementation step after a plan correction (use the workflow's resume feature instead where possible).

---

### `test-scoper`

**Role:** Maps changed files to relevant tests, builds a scoped `pytest` command, executes it, and reports results.

**What it does:**
1. Maps each changed `src/X/` file to `tests/unit/X/`
2. Expands to transitive test dependents for changes in `src/core/`, `src/systems/`, `src/engine/`
3. Checks `test_plan.md` for new tests that should have been added
4. Builds and executes the scoped `pytest` command via Bash
5. Reports pass count, fail count, failing test names, and coverage gaps

**Inputs:** List of changed source files. Reads `staging_artifacts/{ticket_id}/test_plan.md`.

**Outputs:** Pytest command used, pass/fail counts, failing test names, coverage gaps.

**Rule:** Never outputs `pytest tests/` — always scopes to specific paths.

---

## Quality and Compliance Agents

### `parity-updater`

**Role:** Keeps `docs/parity_ledger/` accurate after a behavior change.

**Ledger files it manages:**

| File | Subsystem |
|---|---|
| `substrate.yaml` | World generation, determinism |
| `combat_movement.yaml` | Combat, movement |
| `strategic_cognition.yaml` | AI goal hierarchy |
| `town_resource.yaml` | Resources, harvesting, crafting |
| `progression.yaml` | XP, rewards, skills |
| `social_narrative.yaml` | Reputation, relationships |
| `world_dynamics.yaml` | Ecology, calamities |
| `infrastructure.yaml` | Replay, telemetry, observability |

**Entry update rules:**
- Behavior matches Mechanics Bible → `status: verified`, update `v2_evidence` and `test_path`
- Intentional divergence → `status: divergent`, set `divergence_note`, add to `docs/guidelines/intentional_divergences.md`
- New behavior with no entry → add with next available ID
- P0 entries must have a non-null `test_path` pointing to a passing test

**When to invoke directly:** After any manual code change that affects simulation behavior.

---

### `mechanics-auditor`

**Role:** Compares a Mechanics Bible chapter to the source implementation and reports divergences.

**Mechanics Bible chapters:**

| Ch | File | Covers |
|---|---|---|
| 01 | `01_entity_anatomy.md` | Attributes, derived stats, XP |
| 02 | `02_combat_laws.md` | Damage formula, modifiers, durability |
| 03 | `03_economic_laws.md` | Conservation, harvesting, trade, crafting |
| 04 | `04_strategic_cognition.md` | Goals, interruption, perception |
| 05 | `05_world_evolution.md` | Tick/time, trauma, ecology |
| 06 | `06_worldbuilding_foundation.md` | Topology, sovereignty, distribution |

**Output classification:**
- `PARITY` — implementation matches documented formula
- `DIVERGENT` — implementation differs (describes what's different)
- `MISSING` — law is documented but has no implementation
- `UNDOCUMENTED` — implementation exists but has no corresponding law

**When to invoke directly:** Before modifying a simulation subsystem, or after a `parity-updater` run to verify the ledger is consistent with the actual implementation.

---

### `world-debugger`

**Role:** Traces world assembly and content resolution failures through the authoritative pipeline.

**Scope:** Failures in `src/worldassembly/`, `src/worldbuilding/`, `src/worldmodules/`, `src/worldgeneration/`, `src/content/`, `src/core/registries.py`.

**Common failure patterns it diagnoses:**
- Missing content reference (entity references unregistered content)
- Schema validation failure (input doesn't match pipeline stage schema)
- Resolver conflict (multiple content items compete for same slot)
- Registry inconsistency (entity state diverges from authoritative state)
- Normalization failure (`src/worldmodules/normalizer.py`)
- Path resolution failure (`src/content/paths.py`)

**Output:** Root cause at `file:line`, upstream state, pipeline stage that failed, fix recommendation, regression risk.

**When to invoke directly:** Any time world assembly, content loading, or resolver fails with an unclear error.

---

## Analysis Agents

### `simulation-analyst`

**Role:** Lightweight single-pass analysis of a completed simulation run against Mechanics Bible ranges.

**Scope:** This is the fast check — anomaly spotting, severity classification, law reference. For deep multi-agent investigation with hypothesis generation and enhancement proposals, use the `investigate-simulation-result` workflow.

**Analysis dimensions:**
- Entity population arc (population crash/explosion detection)
- Combat formula spot-checks against Ch02
- Economic conservation check against Ch03
- Goal distribution and interruption patterns against Ch04
- Tick-to-day and regional trauma against Ch05

**Anomaly severity:** `CRITICAL` (law violated) / `HIGH` (severe imbalance) / `MEDIUM` (trending unstable) / `LOW` (minor deviation).

**Escalation rule:** If CRITICAL anomalies are found, recommend running the `investigate-simulation-result` workflow for full diagnosis.

---

## Agent Summary Table

| Agent | Phase in lifecycle | Primary output |
|---|---|---|
| `ticket-scoper` | Pre-work | `tickets/inprogress/{id}.md` |
| `investigator` | Pre-work | `investigation.md`, `test_plan.md` |
| `planner` | Pre-work | `plan.md` |
| `architecture-reviewer` | Gate before implementation | APPROVED / NEEDS_CHANGES verdict |
| `implementer` | Implementation | Code changes + implementation notes |
| `test-scoper` | Post-implementation | Test results (pass/fail) |
| `parity-updater` | Post-implementation | Updated `docs/parity_ledger/*.yaml` |
| `done-checker` | Closure gate | READY_TO_CLOSE / BLOCKED verdict |
| `mechanics-auditor` | Quality / compliance | PARITY/DIVERGENT/MISSING table |
| `world-debugger` | Debugging | Root cause + fix recommendation |
| `simulation-analyst` | Analysis | Anomaly table + severity |

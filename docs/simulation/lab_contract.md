---
status: authoritative
layer: simulation
authority: P1
audience: agent
last_verified: 2026-06-12
tags: [lab, simulation, agentic, contract, scenario]
---

# Agentic Simulation Lab Contract

**Source:** `src/lab/` (18 files)  
**Authoritative status:** Shadow state — lab sessions are isolated from `AuthoritativeState`. Session data is stored in `data/lab_sessions/` (file-based), not in the simulation hash.

For historical context only: `docs/archive/observability/agentic_lab.md` (a historical report — not a contract).

---

## Purpose

The agentic simulation lab provides a human-gated workflow for running isolated simulation experiments, applying world mutations, comparing results, and surfacing findings for knowledge update. It wraps the simulation engine in a structured session with explicit approval gates.

---

## Compliance ID Index

| ID(s) | File | Description |
|---|---|---|
| SCENARIO-001, 002, 003 | src/lab/schema.py | Core schemas: LabRunManifest, LabSessionManifest, ExperimentSpec |
| SCENARIO-004, 005, 006 | src/lab/validator.py | ScenarioValidator, ExperimentValidator |
| SCENARIO-007, 008, 009 | src/lab/repository.py | ScenarioRepository, ExperimentRepository, LabRunRepository |
| SCENARIO-010 | src/lab/__init__.py | Module public interface |
| SCENARIO-012 | src/lab/orchestrator.py | ScenarioLabOrchestrator — lab workflow coordination |
| SCENARIO-013 | src/lab/orchestrator.py | World + Scenario + Experiment load and validation pipeline |
| SCENARIO-014 | src/lab/orchestrator.py | Lab run instantiation and isolation contract |
| SCENARIO-015 | src/lab/orchestrator.py | Post-run analysis and summary compilation |
| METAMORPHIC-RULE-001, 002, 003 | src/lab/metamorphic.py | Metamorphic testing property rules |
| MUTATION-ENGINE-001, 002, 003 | src/lab/mutation.py | Mutation engine application rules |
| MUTATION-ORCHESTRATOR-001, 002, 003 | src/lab/mutation_orchestrator.py | Mutation orchestration pipeline |
| BALANCE-COMPARE-001, 002, 003 | src/lab/comparison.py | Balance comparison methodology |

---

## Session Lifecycle

```
ACTIVE → WAITING_FOR_USER → ACTIVE → ... → COMPLETED
                                         → FAILED
                          → ARCHIVED (at any stage, by user action)
```

**States:**

| State | Meaning |
|---|---|
| `ACTIVE` | Session is running or ready to advance |
| `WAITING_FOR_USER` | Approval gate reached — session paused until human approves or rejects |
| `COMPLETED` | All stages finished successfully |
| `FAILED` | Session encountered an unrecoverable error |
| `ARCHIVED` | Session preserved for record-keeping; no further progression |

**Stages (in order):**

| Stage | Description |
|---|---|
| `GENERATION` | Generate world, scenario, and experiment specs |
| `EXECUTION_SUPPORT` | Prepare execution environment; validate budget |
| `REGISTRATION` | Register the lab run in the repository |
| `INVESTIGATION` | Run simulation; collect results |
| `ENHANCEMENT` | Apply mutations or improvements based on results |
| `KNOWLEDGE_UPDATE` | Surface findings to the knowledge base |

**Human approval gates:** Stages `GENERATION`, `EXECUTION_SUPPORT`, and `ENHANCEMENT` require explicit human approval before the session may advance. Each has an `approval_status` of `PENDING`, `APPROVED`, or `REJECTED`. A `REJECTED` status terminates progression.

---

## Orchestrator Contract (SCENARIO-012 through 015)

`ScenarioLabOrchestrator` is the central workflow engine:

1. **Load and validate** (`SCENARIO-013`): Load `WorldSpec`, `ScenarioSpec`, and `ExperimentSpec` from their respective repositories. Run `WorldValidator` and `ScenarioValidator` before proceeding. Any validation failure aborts the run.

2. **Instantiate isolated run** (`SCENARIO-014`): Create an isolated `LabRun` with its own state namespace under `data/lab_sessions/`. The lab run must not share `AuthoritativeState` with any other run or the primary simulation.

3. **Drive simulation ticks** (`SCENARIO-012`): Execute Kernel ticks for the configured tick budget. Lab runs are always single-threaded.

4. **Post-run analysis** (`SCENARIO-015`): After final tick, run comparison, metamorphic checks, and mutation analysis. Compile summary.

---

## Safety Guardrails Contract

`src/lab/guardrails.py` — `BudgetGuardrail` is the enforcement gate before any lab run begins.

**BudgetEstimation** (computed pre-run):
- `run_count`, `total_ticks`, `expected_entity_count`, `expected_event_volume`, `expected_artifact_mb`, `expected_runtime_minutes`

**BudgetCheckResult** statuses:

| Status | Meaning | Action |
|---|---|---|
| `OK` | Within all limits | Proceed |
| `WARNING` | Soft limit approached | Requires explicit human confirmation before proceeding |
| `BLOCKED` | Hard limit exceeded | `BudgetBlockedError` raised — run cannot proceed regardless of human input |

`BudgetBlockedError` is a hard stop: no override path exists.  
`BudgetWarningError` requires human acknowledgement: session transitions to `WAITING_FOR_USER`.

---

## Mutation Pipeline Contract

`src/lab/mutation.py` (MUTATION-ENGINE-001/002/003) — applies parameterised mutations to a world spec before a lab run.

`src/lab/mutation_orchestrator.py` (MUTATION-ORCHESTRATOR-001/002/003) — orchestrates multi-mutation sequences: applies mutations in order, validates the result after each, rolls back on validation failure.

**Mutation rules:**
1. Each mutation is applied to a copy of the spec — the original is never mutated.
2. After each mutation, `WorldValidator` is re-run. A mutation that produces an invalid world spec is rejected and rolled back.
3. The final mutated spec is what the lab run executes — not the original.

---

## Metamorphic Testing Contract

`src/lab/metamorphic.py` (METAMORPHIC-RULE-001/002/003) — defines metamorphic relations: properties that must hold between the output of two related inputs.

Rules:
- Each metamorphic relation is a named property with a source input transformation and an expected output invariant.
- A metamorphic test failure is recorded in the session's result — it does not abort the run.
- Three classes of metamorphic relations are defined (001: symmetry, 002: monotonicity, 003: equivalence).

---

## Resource Budget and Storage

| Resource | Policy |
|---|---|
| Session storage | `data/lab_sessions/<session_id>/` — isolated per session |
| Max artifact size | Enforced by `BudgetGuardrail.expected_artifact_mb` — blocked if exceeded |
| Retention | Sessions in `ARCHIVED` state are retained indefinitely; `COMPLETED`/`FAILED` sessions may be cleaned up by tooling |
| Path security | `LabSessionStore` enforces strict absolute path guards — no path traversal allowed |

---

## Validation Rules Reference

`src/lab/validator.py` (SCENARIO-004/005/006) defines:

| Rule ID | Validator | What it checks |
|---|---|---|
| `SCENARIO-REF-001` | `ScenarioValidator` | All cross-references in a scenario spec point to existing world elements |
| `SCENARIO-LIMIT-001` | `ScenarioValidator` | Tick budget and entity count are within configured limits |
| `SCENARIO-SIGNAL-001` | `ScenarioValidator` | At least one observable signal is defined (required for post-run analysis) |
| `SCENARIO-ANOMALY-001` | `ExperimentValidator` | Anomaly detection parameters are within valid bounds |

Any `ERROR`-severity validation issue raises `CatalogValidationError` and aborts the lab setup.

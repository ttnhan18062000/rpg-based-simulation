---
trigger: always_on
---

# Engine Contracts Rule

Covers all agent work on the **engine layer**: kernel loop, authoritative pipeline, subsystems,
performance/optimization, architecture decisions, resource bounds, data-driven config, and
concurrency. This rule is separate from `authoritative_mechanics.md`, which covers RPG simulation
laws (Mechanics Bible). Engine-layer changes have their own doc update requirements.

The master index of all engine contracts is `docs/engine/project_lawbook.md`.
The extension and maintenance laws are in `docs/engine/engineering_playbook.md`.

---

## 1. Kernel Loop Changes

**Triggers:** any change to phase order, phase count, concurrency model, tick lifecycle,
stability guard behavior, or the hard-law compliance guard in `src/engine/kernel.py` or equivalent.

**Required updates:**
- `docs/engine/kernel.md` — update the phase table, any law descriptions, concurrency notes
- `docs/parity_ledger/infrastructure.yaml` — update the entry whose `v2_evidence` points to
  the changed code; set `status: verified` or `status: divergent` as appropriate
- **If the change is a structural decision** (phase added/removed, concurrency model changed):
  write or update an ADR in `docs/architecture/` — see §6

---

## 2. Authoritative Pipeline Changes

**Triggers:** add, remove, reorder, or materially change a phase in the 17-phase
`AuthoritativeApplyPipeline`; change which Logic ID owns a responsibility; change
rejection or sliding-state semantics.

**Required updates:**
- `docs/engine/authoritative_pipeline.md` — update the phase table (Phase #, Name, Logic ID,
  Responsibility); assign a new Logic ID for any new phase using the pattern `<SUBSYS>-<NNN>`
  (next sequential unused number for that subsystem prefix)
- `docs/engine/authoritative_mutation_pipeline_contract.md` — if the Proposal→Refine→Apply
  split or the Refinement/Apply responsibilities change
- `docs/engine/authoritative_refinement_contract.md` or `authoritative_apply_contract.md`
  — if the specific stage contract changes
- `docs/parity_ledger/substrate.yaml` — update entries whose evidence or test_path changes

**Logic ID assignment rule:**
Every pipeline phase must carry a Logic ID. Format: `<SUBSYS>-<NNN>` where SUBSYS is one of:
`RPG-AUTH`, `TOWN`, `SOC`, `COMB`, `STRAT`, `PROG`, `INFRA`, `LEG-RPG`.
New IDs must be the next unused integer for that prefix, verified by grepping existing contracts.

---

## 3. New Subsystem

**Triggers:** any new module under `src/systems/`, `src/engine/`, or `src/core/` that introduces
durable state, a tick-path hook, a worker type, or an internal buffer/queue.

**Required updates:**
- Write a subsystem contract doc at `docs/engine/<subsystem_name>_contract.md` using the
  Subsystem Contract Template from `docs/engine/engineering_playbook.md`. Must declare:
  - **Authoritative Status**: YES if state participates in the hash; NO for shadow/telemetry
  - **Resource Budget**: max RSS (MB) and max compute (ms/tick) per hardware class
  - **Retention / Overflow Policy**: what happens when internal buffers hit their ceiling
  - **Degradation Laws**: behavior under CONSTRAINED, DEGRADED, SURVIVAL modes
- Add the new contract to the Table of Contents in `docs/engine/project_lawbook.md`
- Add at least one entry to `docs/parity_ledger/infrastructure.yaml` for the new subsystem
- Run `make docs-registry` after writing the contract so REGISTRY.yaml picks it up

---

## 4. Performance and Optimization Changes

**Triggers:** any change to tick-path code (anything called inside `Kernel.tick_once()`),
caching strategy, serialization format, worker batching, concurrency model, or memory layout.

**Required verification before closing (not optional):**
- **Parity Invariant** (`docs/engine/performance_contract.md §4.1`): optimization must not
  change the semantic outcome. If the `AuthoritativeState` hash differs from the pre-change
  baseline on the same seed and scenario, the change is a failure regardless of speed gains.
- **Bounded Overhead** (`§4.2`): timing instrumentation added as part of the change must
  stay under 1% of total tick time.
- **Regression Threshold** (`§5`): if `avg_tick_compute_ms` increases >5% on any stable
  certification scenario, it must be flagged — write a "Divergence Reason" entry in a new
  or existing ADR, do not silently accept the regression.

**Required updates:**
- `docs/engine/performance_contract.md` — if measured baseline TPS or tick cost changes,
  update the benchmark numbers; keep hardware class labels accurate
- **If the optimization is structural** (batching model, worker topology, serialization format):
  write an ADR in `docs/architecture/` — see §6

**Measurement protocol** (from `performance_contract.md §3`):
Claims are only valid with: Runtime Profile + Hardware Class + Scenario + Execution Mode.
Never write "faster" without the (Profile, Scenario, HardwareClass) bundle.

---

## 5. Resource and Concurrency Bounds Changes

**Triggers:** change to max worker count, buffer ceiling, queue retention policy, memory pool
size, thread count, or degradation-mode thresholds in the `ResourceGovernor`.

**Required updates:**
- The specific substrate contract that owns the changed bound:
  - Worker bounds → `docs/engine/contracts/worker_contract.md`
  - Resource governor thresholds → `docs/engine/contracts/resource_governor_contract.md`
  - Scheduler eligibility or work model → `docs/engine/contracts/scheduler_contract.md`
  - Replay retention → `docs/engine/contracts/replay_contract.md`
  - Observability budgets → `docs/engine/contracts/observability_contract.md`
  - Runtime state partition → `docs/engine/contracts/runtime_state_contract.md`
- Update `docs/engine/runtime_profiles.md` if the Runtime Profile envelope (Max RAM,
  Max CPU, Max Worker Count) changes for any hardware class
- `docs/parity_ledger/infrastructure.yaml` for affected entries

---

## 6. Architectural Decisions

**Triggers:** any decision that changes how the engine is structured rather than what it
computes. Examples: new concurrency model, state partition boundary change, new subsystem
category, new degradation mode, new pipeline stage type, new inter-service protocol.

**Required:** write an ADR at `docs/architecture/adr-<NNN>-<kebab-title>.md`.

ADR number: next sequential unused integer — check `ls docs/architecture/adr-*.md`.

**Required ADR sections:**
- **Status**: `Proposed` | `Accepted` | `Deprecated` | `Superseded by ADR-NNN`
- **Context**: why this decision was needed; what was observed or measured
- **Decision**: what was decided and what it replaces or adds
- **Rationale**: why this option over alternatives
- **Trade-offs**: what is gained and what is lost
- **Consequences**: positive, negative, and mitigations
- **Revisit Trigger**: the condition that should cause this decision to be re-evaluated

Reference the ADR from the relevant contract doc. Update `docs/architecture/README.md`
if one exists to include the new ADR in the index.

---

## 7. Data-Driven Config and Runtime Profile Changes

**Triggers:** add or modify a runtime profile (hardware class envelope), a certification
scenario definition, a sweep configuration, a governance policy parameter, or any value
that controls engine behavior through configuration rather than code.

**Required updates:**
- `docs/engine/runtime_profiles.md` — add or update the profile using the Runtime Profile
  Template from `docs/engine/engineering_playbook.md`
- The relevant certification or test matrix doc for the milestone (e.g., `certification_matrix.md`)
  if scenario definitions or expected outcomes change
- `docs/engine/performance_contract.md` if hardware class TPS targets change
- If the config is a new engine feature surface: document it in `docs/engine/known_limitations.md`
  under "supported" or remove a "not yet supported" entry as appropriate

---

## 8. World Pipeline and Simulation System Contract Maintenance

These modules sit outside `src/engine/` and `src/systems/` but each has (or will have, per pending
tickets) a binding contract doc. When code in any of these paths changes materially — behavior,
pipeline phase, schema, lifecycle rule, compliance ID — the corresponding contract doc **must** be
updated in the same commit/session.

| Source path | Contract doc | Parity ledger file | Compliance namespace |
|---|---|---|---|
| `src/worldassembly/` | `docs/world/assembly_contract.md` | `infrastructure.yaml` | `WORLD-ASM-*` |
| `src/worldbuilding/` | `docs/world/compiler_contract.md` | `substrate.yaml` | `WORLD-*` |
| `src/worldmodules/` | `docs/world/modules_contract.md` | `infrastructure.yaml` | `WORLD-MOD-*` |
| `src/worldgeneration/` | `docs/world/generator_contract.md` | `substrate.yaml` | — |
| `src/lab/` | `docs/simulation/lab_contract.md` | `infrastructure.yaml` | `SCENARIO-*` |
| `src/domains/` | `docs/simulation/domains/domain_ownership_map.md` + relevant domain contract | — | — |
| `src/content/` | `docs/content/pipeline_contract.md` | — | — |
| `src/content_semantics/` | `docs/content/content_semantics_contract.md` | — | — |
| `src/town/` | `docs/simulation/town_contract.md` | — | — |
| `src/quests/` | `docs/simulation/quest_contract.md` | — | — |

**Rule:** If the contract doc listed above does not yet exist (tickets are open), note the gap in
the Implementation Notes of the ticket you are working and do not invent content — wait for the
contract ticket to be executed first, or execute it as a prerequisite.

**Compliance ID rule:** If you add a new `# Compliance: SUBSYS-NNN` comment to source code in any
of these modules, you must also add a corresponding parity ledger entry with `v2_evidence` pointing
to the source file and line. Do not add a Compliance ID comment without a parity ledger entry.

---

## 9. Forbidden Pattern Check (Pre-Close Gate)

Before closing any engine-layer ticket, verify none of these patterns were introduced.
If any are present, the ticket is not done — fix before closing.

| Forbidden pattern | Where defined | Check |
|---|---|---|
| Unbounded collection (list/dict with no `max_size` or retention policy) | `engineering_playbook.md §Forbidden` | grep new collections in changed files |
| Alternate authority (static var or global registry influencing simulation outcome) | `engineering_playbook.md §Forbidden` | grep module-level state in changed files |
| Dishonest performance claim (speed claim without Profile+Scenario+HardwareClass) | `performance_contract.md §3.1` | check any doc or comment claiming TPS/ms |
| Ad-hoc threading (Thread/asyncio outside Scheduler and WorkerPool bounds) | `engineering_playbook.md §Forbidden` | grep `threading.Thread`, `asyncio.create_task` in changed files |
| Durable meaning in `reason` strings or free-form metadata | `architecture.md §Durable State Rule` | review new fields added to state models |

---

## Summary: Trigger → Required Action

| What changed | Contract to update | Parity ledger | ADR required |
|---|---|---|---|
| Kernel loop phase / stability guard | `kernel.md` | `infrastructure.yaml` | If structural |
| Pipeline phase / Logic ID | `authoritative_pipeline.md` | `substrate.yaml` | If structural |
| New subsystem | New `<name>_contract.md` + Lawbook TOC | `infrastructure.yaml` | No (contract is sufficient) |
| Tick-path optimization | `performance_contract.md` (verify + update numbers) | `infrastructure.yaml` | If structural |
| Resource / concurrency bounds | Relevant substrate contract + `runtime_profiles.md` | `infrastructure.yaml` | If structural |
| Architectural decision | ADR in `docs/architecture/` | — | Yes, always |
| Data-driven config / profile | `runtime_profiles.md` + scenario matrix | — | No |
| `src/worldassembly/` behavior | `docs/world/assembly_contract.md` | `infrastructure.yaml` | If structural |
| `src/worldbuilding/` behavior | `docs/world/compiler_contract.md` | `substrate.yaml` | If structural |
| `src/worldmodules/` behavior | `docs/world/modules_contract.md` | `infrastructure.yaml` | If structural |
| `src/worldgeneration/` behavior | `docs/world/generator_contract.md` | `substrate.yaml` | If structural |
| `src/lab/` behavior | `docs/simulation/lab_contract.md` | `infrastructure.yaml` | If structural |
| `src/domains/<name>/` behavior | `docs/simulation/domains/<name>_contract.md` | — | If structural |
| `src/content/` or `src/content_semantics/` | `docs/content/pipeline_contract.md` or `content_semantics_contract.md` | — | If structural |
| `src/town/` behavior | `docs/simulation/town_contract.md` | — | If structural |
| `src/quests/` behavior | `docs/simulation/quest_contract.md` | — | If structural |
| Any of the above | Run `make docs-registry` after writing new docs | — | — |

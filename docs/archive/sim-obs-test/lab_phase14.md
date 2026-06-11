---
status: archive
authority: P2
audience: historical
layer: engine
original_date: unknown
---

# Phase 14 — Human-Gated Agentic Simulation Lab

Corrected scope:

```text id="eh9goy"
All workflows are manually triggered by the user.
No workflow automatically triggers the next workflow.
The agent assists, validates, prepares, investigates, and proposes.
The user controls execution and approval.
```

Phase 14 is not “full automation”.

It is:

```text id="ip8xz2"
Human-Gated Agentic Simulation Lab
```

---

# Main objective

Build a workflow layer where Antigravity or another AI Agent can help the user:

```text id="mh3tdn"
generate simulation setup
validate specs
prepare execution command
register manually executed results
compact large simulation data
investigate results
propose improvements
store reusable insights
```

But the agent must not:

```text id="o1d935"
run long simulations automatically
chain workflows automatically
rerun failed simulations repeatedly
promote drafts without approval
modify trusted rules without approval
read unlimited raw data into context
```

---

# Phase 14 core design

The system should have three major storage areas:

```text id="fvd5ba"
data/lab_sessions/
data/lab_runs/
data/lab_knowledge/
```

## 1. `lab_sessions`

Stores the human/agent workflow history.

```text id="b4pbsr"
generation request
draft specs
review packs
execution support package
manual execution notes
registration reports
investigation reports
enhancement proposals
approval decisions
```

## 2. `lab_runs`

Stores actual simulation execution output.

```text id="xj97pu"
run manifests
simulation events
metric windows
anomalies
reports
evidence packs
summaries
```

## 3. `lab_knowledge`

Stores reusable long-term knowledge.

```text id="kab34k"
rules
principles
known issues
insights
decision logs
indexes
previous lessons
```

---

# Phase 14 milestones

```text id="gn2j0b"
M92 — Lab Session Model and Storage
M93 — Workflow Registry and Skill Contracts
M94 — Generic / Specific Input Parameter Model
M95 — Context Pack Builder
M96 — GenerateSimulationSetup Workflow
M97 — PrepareSimulationExecution Workflow
M98 — RegisterSimulationResult Workflow
M99 — CompactSimulationData Workflow
M100 — InvestigateSimulationResult Workflow
M101 — ProposeSimulationEnhancements Workflow
M102 — UpdateSimulationKnowledge Workflow
M103 — Approval Gate and Audit Trail
M104 — Token, Time, and Storage Guardrails
M105 — Phase 14 End-to-End Tests
```

---

# M92 — Lab Session Model and Storage

## Purpose

Track the full user-agent workflow history.

This is different from `lab_runs`.

A `lab_run` is the actual simulation output.

A `lab_session` is the process around it.

---

## Directory layout

```text id="ogps7b"
data/lab_sessions/
  session_0001/
    session_manifest.json

    generation/
      generation_request.json
      context_pack.json
      draft_specs/
      generation_review_pack.md
      validation_reports/

    execution_support/
      execution_request.json
      execution_readiness_report.md
      execution_command.sh
      expected_output_paths.json
      budget_report.json

    manual_execution/
      user_notes.md
      actual_lab_run_path.txt

    registration/
      registration_request.json
      result_integrity_report.md
      artifact_index.json
      compact_summary.json

    investigation/
      investigation_request.json
      context_pack.json
      investigation_report.md
      issue_backlog.json
      missing_signals.json
      insight_candidates.json

    enhancement/
      enhancement_request.json
      enhancement_plan.md
      proposed_patches/
      next_experiment_drafts/

    knowledge_update/
      approved_insights.jsonl
      approved_decisions.jsonl
      update_report.md
```

---

## Session-Scoped Absolute Isolation

To prevent concurrent user/agent sessions from interleaving and causing hard-to-diagnose data collisions, the system enforces a strict isolation boundary:
- **Root Directory**: `data/lab_sessions/session_{session_id}/`
- **Output Alignment**: Every output artifact produced by any workflow (e.g., draft specs, context packs, readiness reports, validation outputs, registration indexes, and executive summaries) **MUST** be written directly inside the respective session subfolder. 
- **Path Guardrails**: Absolute paths or relative paths attempting to break out of the `data/lab_sessions/session_{session_id}/` boundaries via double-dot traversal (e.g., `../../`) are strictly blocked at the file API level with path validation checks.

---

## `session_manifest.json`

```json id="j6lqit"
{
  "session_id": "session_0001",
  "status": "ACTIVE",
  "created_at": "...",
  "updated_at": "...",
  "current_stage": "GENERATION",
  "linked_lab_runs": [],
  "linked_worlds": [],
  "linked_scenarios": [],
  "linked_experiments": [],
  "approval_status": {
    "generation": "PENDING",
    "execution_support": "PENDING",
    "enhancement": "PENDING"
  }
}
```

---

## Status values

```text id="r47sl0"
ACTIVE
WAITING_FOR_USER
COMPLETED
FAILED
ARCHIVED
```

---

## Required tests

```text id="27az9f"
tests/unit/lab_agent/test_lab_session_store.py
```

Test cases:

```text id="q9hm0j"
[ ] creates new lab session
[ ] writes session_manifest.json
[ ] updates current_stage
[ ] records linked lab_run path
[ ] does not overwrite existing session
[ ] rejects unsafe session_id path traversal
[ ] can load previous session
```

---

# M93 — Workflow Registry and Skill Contracts

## Purpose

Each Antigravity workflow/skill must have a strict contract.

The agent should not perform arbitrary actions.

---

## Generic Workflow & Skill Spec Registry

Instead of maintaining a separate static config file (like `workflow_registry.yaml`), we adopt the identical **Antigravity-Style Markdown Spec & Skill Model**. Each workflow and its contract is defined as a standard Markdown file in the project's native automation folders:
- **Workflows**: Defined in `.agents/workflows/<workflow-kebab-case>.md`
- **Skills**: Defined in `.agents/skills/<skill-kebab-case>/SKILL.md`

The Python `WorkflowRegistry` dynamically scans and parses the YAML frontmatter from these Markdown files at startup. This guarantees zero drift between the agent's instructions and the Python backend's enforcement gates!

### Antigravity-Style Workflow Spec Format
Each `.agents/workflows/<workflow-name>.md` file defines its contract directly in the frontmatter metadata block:

```markdown
---
name: GenerateSimulationSetup
description: Generate draft world/scenario/experiment specifications from user intent.
allowed_actions:
  - read_indexes
  - read_rules
  - create_draft_specs
  - run_validators
  - write_review_pack
forbidden_actions:
  - run_simulation
  - promote_trusted_specs
  - update_rulebooks_directly
input_schema:
  mode: "generic | specific"
  user_goal: "string (required in generic)"
  constraints: "object (optional)"
output_artifacts:
  - generation/draft_specs/world.yaml
  - generation/draft_specs/scenario.yaml
  - generation/draft_specs/experiment.yaml
  - generation/generation_review_pack.md
---

# GenerateSimulationSetup Workflow
Detailed steps and guidelines for setup generation...
```

### Antigravity-Style Skill Spec Format
Each `.agents/skills/<skill-name>/SKILL.md` file defines its capability and rules:

```markdown
---
name: generate-simulation-setup
description: "Trigger when generating new sandbox scenarios or world templates from text."
allowed_actions:
  - read_indexes
  - read_rules
  - create_draft_specs
  - run_validators
forbidden_actions:
  - run_simulation
---

# Generate Simulation Setup Skill
Skill rules and parameter mapping details...
```

---

## WorkflowSkill contract

The Python engine loads the dynamic registry and exposes a validated `WorkflowSkill` contract with:

```text id="fg43dv"
name: str
purpose: str
input_schema: dict
allowed_actions: List[str]
forbidden_actions: List[str]
output_artifacts: List[str]
approval_required: bool
context_budget: dict
failure_behavior: str
```

---

## Required tests

```text id="j9mqno"
tests/unit/lab_agent/test_workflow_registry.py
```

Test cases:

```text id="fgdaj3"
[ ] scans .agents/workflows/ and loads markdown contracts
[ ] extracts YAML frontmatter metadata accurately
[ ] unknown workflow command is rejected
[ ] workflow has allowed_actions validated
[ ] workflow has forbidden_actions validated
[ ] workflow declares output artifacts verified
[ ] PrepareSimulationExecution forbids execute_simulation_command
[ ] GenerateSimulationSetup forbids trusted promotion
```

---

# M94 — Generic / Specific Input Parameter Model

## Purpose

Every workflow must support two modes:

```text id="qgs8m7"
generic mode
specific mode
```

This gives the user control without forcing complexity.

---

# Generic mode

User gives high-level intent.

Example:

```text id="9keage"
Generate a medium resource economy stress setup.
```

Agent resolves:

```text id="3gy980"
template
world scale
scenario type
experiment default
budget profile
required signals
```

---

# Specific mode

User gives exact control.

Example:

```text id="t8copv"
world_type: resource_valley
workers: 300
resources: wood, stone
pressure: inventory_full, pathing_bottleneck
ticks: 50000
seeds: [1, 2, 3]
observability: LONG_RUN
```

---

## Shared request model

```json id="nq7l40"
{
  "workflow": "GenerateSimulationSetup",
  "mode": "generic",
  "user_goal": "Create a resource economy stress setup",
  "specific_inputs": {},
  "constraints": {
    "budget_profile": "local_dev",
    "max_entities": 500,
    "max_ticks": 50000
  }
}
```

---

## Required tests

```text id="spce3q"
tests/unit/lab_agent/test_workflow_request_model.py
```

Test cases:

```text id="zzu06i"
[ ] generic request validates with user_goal
[ ] specific request validates with required fields
[ ] missing workflow is rejected
[ ] unknown mode is rejected
[ ] constraints are preserved
[ ] generic mode does not require detailed fields
[ ] specific mode rejects incomplete required fields
```

---

# M95 — Context Pack Builder

## Purpose

Control token usage.

The agent should not read all files.

Each workflow should get a compact context pack.

---

# Context pack principle

```text id="0pf1rn"
summary first
index second
evidence third
raw data only by explicit request
```

---

## Generation context pack

Reads:

```text id="ca8pmf"
world index
scenario index
experiment index
current worldbuilding rules
current testing principles
known issues relevant to goal
similar previous setups
budget profile
```

Writes:

```text id="16ksh9"
generation/context_pack.json
generation/context_pack.md
```

---

## Investigation context pack

Reads:

```text id="uwmr47"
lab summary
issue index
signal coverage
top N evidence packs
known issues
investigation rules
missing signal report
```

Does not read raw event logs unless requested.

---

## Context pack limits

Each pack should include:

```text id="l338t8"
max_rules
max_known_issues
max_previous_runs
max_evidence_packs
max_raw_windows
max_tokens_estimate
```

---

## Required tests

```text id="e2z9br"
tests/unit/lab_agent/test_context_pack_builder.py
```

Test cases:

```text id="1v0ap7"
[ ] generation context uses indexes, not raw reports
[ ] investigation context includes top N evidence packs only
[ ] context pack respects max item limits
[ ] missing index produces warning, not crash
[ ] raw logs are excluded by default
[ ] known issues are filtered by domain/tag
```

Critical test:

```text id="8lwboy"
[ ] context pack builder does not load simulation_events.jsonl by default
```

---

# M96 — GenerateSimulationSetup Workflow

## Purpose

Create draft world/scenario/experiment data from user intent.

This workflow does not run simulation.

---

## Input

Generic:

```json id="8ox27i"
{
  "mode": "generic",
  "user_goal": "Create a resource economy stress setup",
  "constraints": {
    "budget_profile": "local_dev",
    "scale": "medium"
  }
}
```

Specific:

```json id="m9mc6n"
{
  "mode": "specific",
  "world_type": "resource_valley",
  "regions": ["village", "forest", "quarry"],
  "workers": 300,
  "resources": ["wood", "stone"],
  "pressures": ["inventory_full", "pathing_bottleneck"],
  "ticks": 50000,
  "seeds": [1, 2, 3],
  "observability_mode": "LONG_RUN"
}
```

---

## Processing steps

```text id="z7a6mo"
1. Create lab session or use existing session.
2. Build generation context pack.
3. Check duplication against world/scenario/experiment indexes.
4. Load current rules/principles.
5. Generate draft WorldSpec.
6. Generate draft ScenarioSpec.
7. Generate draft ExperimentSpec.
8. Run validators.
9. Estimate budget.
10. Write generation review pack.
```

---

## Output artifacts

```text id="y35xmb"
generation/draft_specs/world.yaml
generation/draft_specs/scenario.yaml
generation/draft_specs/experiment.yaml
generation/validation_reports/world_validation.json
generation/validation_reports/scenario_validation.json
generation/validation_reports/experiment_validation.json
generation/budget_report.json
generation/duplication_report.json
generation/generation_review_pack.md
```

---

## Review pack contents

```text id="w6jknj"
purpose
generated files
world summary
entities/populations
regions/topology
resources/buildings/quests
expected behavior
required observability signals
budget estimate
similar existing setups
validation errors/warnings
assumptions
risks
next manual step
```

---

## Required tests

```text id="wjzkkq"
tests/integration/lab_agent/test_generate_simulation_setup_workflow.py
```

Test cases:

```text id="mag5rw"
[ ] generic generation creates draft specs
[ ] specific generation respects user parameters
[ ] validators run after generation
[ ] review pack is created
[ ] duplication report is created
[ ] budget report is created
[ ] generated drafts are not promoted to trusted folders
[ ] workflow does not run simulation
```

Anti-misdirection tests:

```text id="p4e4qt"
[ ] invalid generated spec remains draft only
[ ] workflow cannot write directly to data/worlds
[ ] workflow cannot call rpg-lab run
```

---

# M97 — PrepareSimulationExecution Workflow

## Purpose

Prepare everything the user needs to manually execute the simulation.

The agent does not run the command.

---

## Input

Generic:

```json id="3d8wod"
{
  "mode": "generic",
  "target": "latest_approved_or_latest_valid_draft",
  "profile": "local_dev"
}
```

Specific:

```json id="29fuej"
{
  "mode": "specific",
  "experiment_path": "data/lab_sessions/session_0001/generation/draft_specs/experiment.yaml",
  "output_path": "data/lab_runs/manual_resource_test_001",
  "profile": "local_dev"
}
```

---

## Processing steps

```text id="ei5i4w"
1. Resolve target experiment.
2. Resolve referenced world/scenario.
3. Re-run validators.
4. Check output path safety.
5. Check budget.
6. Check required signal configuration.
7. Check no active run lock.
8. Prepare command.
9. Write readiness report.
```

---

## Output artifacts

```text id="s4vhsb"
execution_support/execution_readiness_report.md
execution_support/execution_readiness_report.json
execution_support/execution_command.sh
execution_support/expected_output_paths.json
execution_support/budget_report.json
```

---

## Command file example

```bash id="mkexcr"
#!/usr/bin/env bash
set -euo pipefail

rpg-lab run \
  --experiment "data/lab_sessions/session_0001/generation/draft_specs/experiment.yaml" \
  --output "data/lab_runs/manual_resource_test_001" \
  --profile "local_dev"
```

---

## Blocking behavior

If validation fails:

```text id="m2alf2"
do not generate execution_command.sh
```

Write:

```text id="pye7n8"
execution_support/execution_blocked_report.md
```

---

## Required tests

```text id="e93g4i"
tests/integration/lab_agent/test_prepare_simulation_execution_workflow.py
```

Test cases:

```text id="m7hdnq"
[ ] valid experiment creates execution_command.sh
[ ] invalid experiment creates blocked report
[ ] output path conflict is detected
[ ] budget violation blocks or warns based on profile
[ ] command uses provided experiment path
[ ] command uses provided output path
[ ] workflow does not execute command
```

Critical test:

```text id="ealua7"
[ ] PrepareSimulationExecution never calls subprocess/run CLI execution
```

---

# M98 — RegisterSimulationResult Workflow

## Purpose

After the user manually runs the simulation, the user tells the agent where the result is.

The workflow checks completeness and registers it into the session.

---

## Input

Generic:

```json id="fvz632"
{
  "mode": "generic",
  "target": "latest_expected_output_path"
}
```

Specific:

```json id="8sxjk6"
{
  "mode": "specific",
  "lab_run_path": "data/lab_runs/manual_resource_test_001"
}
```

---

## Processing steps

```text id="qv8zeo"
1. Resolve lab_run path.
2. Check manifest exists.
3. Check status.
4. Check expected artifacts.
5. Check reports.
6. Check errors/crash files.
7. Build artifact index.
8. Link lab_run to lab_session.
9. Write result integrity report.
```

---

## Output artifacts

```text id="h8cy60"
registration/result_integrity_report.md
registration/result_integrity_report.json
registration/artifact_index.json
registration/actual_lab_run_path.txt
```

---

## Result classifications

```text id="5xqx6z"
COMPLETE
PARTIAL
FAILED
CORRUPTED
MISSING
UNKNOWN
```

---

## Required tests

```text id="gxmw08"
tests/integration/lab_agent/test_register_simulation_result_workflow.py
```

Test cases:

```text id="6zkvqy"
[x] complete lab_run registers successfully
[x] partial lab_run is marked PARTIAL
[x] missing manifest is marked MISSING
[x] corrupted JSON is marked CORRUPTED
[x] failed run keeps crash/error reference
[x] lab_run path is linked into session manifest
[x] path traversal is blocked
```

---

# M99 — CompactSimulationData Workflow

## Purpose

Convert large raw simulation data into compact summaries and indexes.

This is required before investigation.

---

## Input

Generic:

```json id="uj8b95"
{
  "mode": "generic",
  "target": "latest_registered_lab_run"
}
```

Specific:

```json id="s4qphz"
{
  "mode": "specific",
  "lab_run_path": "data/lab_runs/manual_resource_test_001",
  "focus_domains": ["resource", "movement", "strategy"],
  "top_n": 10
}
```

---

## Processing steps

```text id="off2tg"
1. Load lab_run manifest.
2. Load run summaries.
3. Load anomaly summaries.
4. Build issue index.
5. Build evidence pack index.
6. Build metric digest.
7. Build entity hotspot index.
8. Build signal coverage report.
9. Write compact summary.
```

---

## Output artifacts

```text id="fpu4ek"
registration/compact_summary.json
registration/compact_summary.md
registration/issue_index.json
registration/evidence_pack_index.json
registration/metric_digest.json
registration/entity_hotspots.json
registration/signal_coverage.json
```

---

## Important data rule

Do not copy full raw data into compact summaries.

Compact summaries should contain:

```text id="l38hpp"
counts
top issues
references
file paths
tick ranges
entity ids
short evidence summaries
```

Not:

```text id="kzqcxn"
full event logs
full timelines
full metric windows
```

---

## Required tests

```text id="yvlbic"
tests/integration/lab_agent/test_compact_simulation_data_workflow.py
```

Test cases:

```text id="xa4tbs"
[ ] compact summary is created
[ ] issue index is created
[ ] evidence pack index is created
[ ] metric digest is created
[ ] signal coverage is created
[ ] raw simulation_events.jsonl is not copied into summary
[ ] top_n limit is respected
```

---

# M100 — InvestigateSimulationResult Workflow

## Purpose

Analyze registered and compacted simulation data.

The agent reads compact data first, then selected evidence.

---

## Input

Generic:

```json id="y3eqt9"
{
  "mode": "generic",
  "target": "latest_compacted_lab_run",
  "analysis_depth": "standard"
}
```

Specific:

```json id="tgb0tj"
{
  "mode": "specific",
  "lab_run_path": "data/lab_runs/manual_resource_test_001",
  "focus_domains": ["resource", "movement"],
  "focus_issues": ["ResourceProductionZero", "NavigationStuck"],
  "seeds": [42],
  "tick_range": [10000, 30000],
  "analysis_depth": "deep"
}
```

---

## Analysis depth

```text id="4o8bfy"
light
standard
deep
```

## Light

Reads:

```text id="xxdjhy"
lab summary
issue index
top 3 issues
```

## Standard

Reads:

```text id="zww8no"
lab summary
issue index
top 10 issues
top evidence packs
signal coverage
known issues
```

## Deep

Reads:

```text id="5f9v6i"
standard data
selected event windows
selected metric windows
selected entity/cognition evidence
```

Still does not read all raw data.

---

## Output artifacts

```text id="57opw7"
investigation/investigation_report.md
investigation/investigation_report.json
investigation/issue_backlog.json
investigation/missing_signals.json
investigation/insight_candidates.json
investigation/next_experiment_suggestions.json
```

---

## Investigation report structure

```text id="4d43r9"
1. Executive summary
2. Data quality
3. Signal coverage
4. Critical issues
5. Domain issues
6. Balance concerns
7. Liveness concerns
8. Runtime/performance concerns
9. Entity/cognition evidence
10. Missing data
11. Likely causes vs confirmed facts
12. Recommended next steps
13. Evidence references
```

---

## Required tests

```text id="ko26be"
tests/integration/lab_agent/test_investigate_simulation_result_workflow.py
```

Test cases:

```text id="55d0qe"
[ ] light investigation reads summary only
[ ] standard investigation reads top evidence packs
[ ] deep investigation reads selected windows only
[ ] report is created
[ ] missing signal section is created
[ ] issue backlog is created
[ ] unsupported lab_run state is rejected
[ ] raw event log is not fully loaded
```

Anti-misdirection tests:

```text id="fczav0"
[ ] confirmed facts require evidence reference
[ ] likely causes are not labeled as confirmed
[ ] missing data produces INSUFFICIENT_DATA, not pass
```

---

# M101 — ProposeSimulationEnhancements Workflow

## Purpose

Create proposals based on an investigation report.

It should not apply changes automatically.

---

## Input

Generic:

```json id="33vteq"
{
  "mode": "generic",
  "target": "latest_investigation_report"
}
```

Specific:

```json id="6bkswr"
{
  "mode": "specific",
  "investigation_report_path": "data/lab_sessions/session_0001/investigation/investigation_report.md",
  "allowed_change_types": [
    "ScenarioSpec",
    "ExperimentSpec",
    "ObservabilityRules",
    "KnownIssues"
  ],
  "forbidden_change_types": [
    "EngineCode"
  ]
}
```

---

## Enhancement targets

```text id="35j8tj"
WorldSpec updates
ScenarioSpec updates
ExperimentSpec updates
MutationSpec updates
required signal updates
observability rule updates
investigation rule updates
balance envelope updates
known issue creation
principle updates
next experiment drafts
```

---

## Output artifacts

```text id="f0gf37"
enhancement/enhancement_plan.md
enhancement/proposed_patches/
enhancement/next_experiment_drafts/
enhancement/insight_candidates.json
enhancement/change_risk_report.json
```

---

## Patch format

Use structured patch files:

```yaml id="6jy4hi"
patch_id: add_resource_target_score_signal
target_type: ScenarioSpec
target_file: data/scenarios/resource_economy_basic/scenario.yaml
operation: add
path: required_signals.events
value: ResourceTargetSelected.score_breakdown
reason: Investigation found ResourceProductionZero but target selection score data was missing.
evidence:
  - investigation/missing_signals.json#resource_target_score_breakdown
```

---

## Required tests

```text id="gdtt44"
tests/integration/lab_agent/test_propose_simulation_enhancements_workflow.py
```

Test cases:

```text id="sx49gi"
[ ] enhancement plan is created
[ ] proposed patches are created
[ ] next experiment drafts are created
[ ] forbidden change type is respected
[ ] patch contains evidence reference
[ ] patch is not automatically applied
[ ] invalid patch fails validation
```

Critical tests:

```text id="aw7iss"
[ ] workflow cannot modify trusted specs directly
[ ] workflow cannot propose unsupported patch operation
[ ] workflow cannot create evidence-free critical rule update
```

---

# M102 — UpdateSimulationKnowledge Workflow

## Purpose

Store approved insights, known issues, rule updates, and decisions.

This workflow should require explicit user approval.

---

## Input

Generic:

```json id="yf3oj0"
{
  "mode": "generic",
  "target": "approved_items_from_latest_enhancement"
}
```

Specific:

```json id="xu0vl4"
{
  "mode": "specific",
  "approved_insights": [
    "insight_candidates/resource_targeting_gap.json"
  ],
  "approved_patches": [
    "proposed_patches/add_resource_target_score_signal.yaml"
  ],
  "decision_note": "We will add ResourceTargetSelected.score_breakdown before next resource economy run."
}
```

---

## Output locations

```text id="x21w59"
data/lab_knowledge/insights/
data/lab_knowledge/known_issues/
data/lab_knowledge/rules/
data/lab_knowledge/principles/
data/lab_knowledge/decisions/decision_log.jsonl
```

---

## Insight record

```json id="5bqvju"
{
  "insight_id": "INSIGHT-RESOURCE-0001",
  "type": "OBSERVABILITY_GAP",
  "title": "Resource target scoring is needed for resource freeze investigation",
  "source_lab_run": "manual_resource_test_001",
  "source_report": "...",
  "evidence_refs": [],
  "status": "APPROVED",
  "created_at": "..."
}
```

---

## Required tests

```text id="ftv6w6"
tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py
```

Test cases:

```text id="m32yn0"
[ ] approved insight is stored
[ ] known issue is stored
[ ] decision log is appended
[ ] rulebook update records version
[ ] unapproved item is rejected
[ ] duplicate insight is detected
[ ] evidence reference is preserved
```

Anti-misdirection test:

```text id="tuii9f"
[ ] workflow cannot update rules/principles without approval marker
```

---

# M103 — Approval Gate and Audit Trail

## Purpose

Make every critical action traceable.

---

# Approval gates

Required approval before:

```text id="2e7y39"
using generated setup for execution
promoting draft specs
applying proposed patches
updating rulebooks
updating principles
marking insight as approved
```

---

## Approval record

```json id="gvx5pr"
{
  "approval_id": "approval_0001",
  "session_id": "session_0001",
  "stage": "GENERATION",
  "approved_artifacts": [
    "generation/draft_specs/world.yaml",
    "generation/draft_specs/scenario.yaml",
    "generation/draft_specs/experiment.yaml"
  ],
  "approved_by": "user",
  "approved_at": "...",
  "notes": "Approved for manual local_dev execution."
}
```

---

## Audit log

```text id="8ayy23"
data/lab_sessions/session_0001/audit_log.jsonl
```

Every workflow writes:

```text id="ta08e1"
workflow_started
workflow_completed
files_read
files_written
validators_run
approval_required
approval_recorded
blocked_action
```

---

## Required tests

```text id="wj3nbb"
tests/unit/lab_agent/test_approval_gate.py
tests/unit/lab_agent/test_audit_trail.py
```

Test cases:

```text id="8xhvob"
[ ] approval record is written
[ ] unapproved execution support can be blocked by policy
[ ] audit log is append-only
[ ] workflow start/end are logged
[ ] blocked forbidden action is logged
[ ] approval cannot reference unsafe path
```

---

# M104 — Token, Time, and Storage Guardrails

## Purpose

Prevent the agent workflow from becoming too expensive or too slow.

---

# Token guardrails

Each workflow defines a context budget.

Example:

```yaml id="h0nr55"
context_budget:
  max_known_issues: 10
  max_previous_runs: 5
  max_evidence_packs: 10
  max_raw_windows: 3
  raw_logs_allowed: false
```

---

# Time guardrails

Workflow should estimate:

```text id="7xyosd"
validator time
compaction time
investigation depth
expected file size
```

Investigation should support:

```text id="lf7q8f"
light
standard
deep
```

---

# Storage guardrails

Before preparing execution, estimate:

```text id="4t2gms"
run count
total ticks
entity count
event volume
artifact size
retention cost
```

---

# Required tests

```text id="6f7sty"
tests/unit/lab_agent/test_agent_guardrails.py
```

Test cases:

```text id="l5enax"
[ ] context pack respects max evidence packs
[ ] raw logs blocked by default
[ ] deep analysis requires explicit parameter
[ ] oversized experiment creates warning/block
[ ] storage estimate is included in readiness report
[ ] guardrail violations are recorded in audit log
```

---

# M105 — Phase 14 End-to-End Tests

## Purpose

Verify the manual workflow chain without full automation.

---

## E2E test flow

```text id="wgrr11"
1. Trigger GenerateSimulationSetup.
2. Verify draft specs and review pack.
3. Manually mark generation approved in test.
4. Trigger PrepareSimulationExecution.
5. Verify execution command is created but not run.
6. Test manually simulates execution by creating fake/mini lab_run output.
7. Trigger RegisterSimulationResult.
8. Trigger CompactSimulationData.
9. Trigger InvestigateSimulationResult.
10. Trigger ProposeSimulationEnhancements.
11. Manually mark selected insight approved in test.
12. Trigger UpdateSimulationKnowledge.
13. Verify knowledge store updated.
```

---

## Test file

```text id="8fjgen"
tests/integration/lab_agent/test_human_gated_agentic_lab_e2e.py
```

Required assertions:

```text id="gvwc85"
[ ] no workflow auto-triggers next workflow
[ ] simulation command is not executed by agent
[ ] each workflow writes expected artifacts
[ ] approval gate is respected
[ ] investigation uses compact data
[ ] enhancement produces patches only
[ ] knowledge update requires approval
[ ] audit trail contains all workflow actions
```

---

# Antigravity skill definitions

You can expose these skills to Antigravity:

```text id="cz8vq2"
GenerateSimulationSetup
PrepareSimulationExecution
RegisterSimulationResult
CompactSimulationData
InvestigateSimulationResult
ProposeSimulationEnhancements
UpdateSimulationKnowledge
```

Each skill should accept:

```text id="az7e18"
mode: generic | specific
session_id optional
input_path optional
constraints optional
focus optional
depth optional
budget_profile optional
```

---

# Example user-facing workflow

## 1. Generate

```text id="t9k0gl"
Workflow: GenerateSimulationSetup
Mode: generic
Goal: Create a resource economy stress setup for medium scale local testing.
Budget: local_dev
```

Output:

```text id="eynjro"
generation_review_pack.md
draft world/scenario/experiment
validation reports
```

---

## 2. Prepare execution

```text id="6ylrtx"
Workflow: PrepareSimulationExecution
Mode: specific
Experiment path: data/lab_sessions/session_0001/generation/draft_specs/experiment.yaml
Output path: data/lab_runs/resource_test_001
```

Output:

```text id="b7swjq"
execution_command.sh
readiness report
```

User manually runs:

```bash id="8z36xj"
bash data/lab_sessions/session_0001/execution_support/execution_command.sh
```

---

## 3. Register

```text id="j4c98a"
Workflow: RegisterSimulationResult
Mode: specific
Lab run path: data/lab_runs/resource_test_001
```

Output:

```text id="z6km40"
result_integrity_report.md
artifact_index.json
```

---

## 4. Investigate

```text id="r6kdhk"
Workflow: InvestigateSimulationResult
Mode: specific
Lab run path: data/lab_runs/resource_test_001
Focus: resource, movement, strategy
Depth: standard
```

Output:

```text id="2buhb0"
investigation_report.md
issue_backlog.json
missing_signals.json
```

---

## 5. Enhance

```text id="hnmirl"
Workflow: ProposeSimulationEnhancements
Mode: specific
Investigation report: investigation_report.md
Allowed changes: ScenarioSpec, ExperimentSpec, ObservabilityRules, KnownIssues
Forbidden changes: EngineCode
```

Output:

```text id="kc54pg"
enhancement_plan.md
proposed patches
next experiment drafts
```

---

## 6. Update knowledge

```text id="moxpkt"
Workflow: UpdateSimulationKnowledge
Mode: specific
Approved insights: [...]
Decision note: ResourceTargetSelected score breakdown required for future resource scenarios.
```

Output:

```text id="4iyh63"
known issue
insight
decision log
updated indexes
```

---

# Implementation order

```text id="ov52lh"
1. M92 Lab Session Model and Storage
2. M93 Workflow Registry and Skill Contracts
3. M94 Generic / Specific Input Model
4. M95 Context Pack Builder
5. M96 GenerateSimulationSetup
6. M97 PrepareSimulationExecution
7. M98 RegisterSimulationResult
8. M99 CompactSimulationData
9. M100 InvestigateSimulationResult
10. M101 ProposeSimulationEnhancements
11. M102 UpdateSimulationKnowledge
12. M103 Approval Gate and Audit Trail
13. M104 Guardrails
14. M105 End-to-End Tests
```

---

# Final acceptance criteria

```text id="m3bntc"
[ ] All workflows are manually triggered.
[ ] No workflow automatically triggers another workflow.
[ ] Agent does not execute simulation command.
[ ] Execution workflow only prepares command and readiness report.
[ ] Generic and specific modes exist for each workflow.
[ ] Lab session stores workflow history.
[ ] Lab run stores simulation result.
[ ] Knowledge store preserves approved insights/rules/decisions.
[ ] Context packs control token usage.
[ ] Investigation uses compact summaries and evidence packs.
[ ] Enhancements are proposed as patches only.
[ ] Approval gates protect critical updates.
[ ] Audit trail records all workflow actions.
[ ] End-to-end human-gated lab test passes.
```

# Phase 14 final name

```text id="25l7xz"
Human-Gated Agentic Simulation Lab
```

This gives you the right balance:

```text id="bvgg47"
agent assistance
manual workflow control
safe execution boundary
structured history
low token waste
future extensibility
```

---

# Human-Gated Simulation Lab CLI & Operations Cheatsheet

This cheatsheet provides a quick-reference for the CLI commands, input schema payloads, and anticipated data paths for manually triggering and managing the workflow stages.

### Workflow Command Reference

Every workflow is invoked using the standard `rpg-lab workflow run` command.

| Phase / Workflow | CLI Command / Invocation | Inputs (Generic / Specific) | Output Location | Expected Result |
| --- | --- | --- | --- | --- |
| **1. Generate Setup** | `rpg-lab workflow run GenerateSimulationSetup` | `mode: generic`, `user_goal: "Create a resource economy stress setup"` | `data/lab_sessions/session_{id}/generation/` | Draft specs (`world.yaml`, `scenario.yaml`, `experiment.yaml`), budget, & review pack |
| **2. Prepare Execution** | `rpg-lab workflow run PrepareSimulationExecution` | `mode: specific`, `experiment_path: "..."`, `profile: "local_dev"` | `data/lab_sessions/session_{id}/execution_support/` | `execution_command.sh` and readiness check report |
| **3. Manual Execution** | `bash data/lab_sessions/session_{id}/execution_support/execution_command.sh` | (Manually executed by user) | `data/lab_runs/{run_name}/` | Raw simulation events, metrics, and evidence packs |
| **4. Register Run** | `rpg-lab workflow run RegisterSimulationResult` | `mode: specific`, `lab_run_path: "data/lab_runs/..."` | `data/lab_sessions/session_{id}/registration/` | Integrity report linking the run output to the active session |
| **5. Compact Data** | `rpg-lab workflow run CompactSimulationData` | `mode: generic` | `data/lab_sessions/session_{id}/registration/compact_summary.json` | Token-safe, O(1) indices, hotspot stats, and issue digests |
| **6. Investigate** | `rpg-lab workflow run InvestigateSimulationResult` | `mode: specific`, `analysis_depth: deep` | `data/lab_sessions/session_{id}/investigation/` | Investigation report, issue backlog, and missing signal maps |
| **7. Propose Patches** | `rpg-lab workflow run ProposeSimulationEnhancements` | `mode: generic` | `data/lab_sessions/session_{id}/enhancement/` | Standardized YAML patches and next experiment drafts |
| **8. Update Knowledge** | `rpg-lab workflow run UpdateSimulationKnowledge` | `mode: specific`, `approved_insights: [...]` | `data/lab_knowledge/` | Permanent long-term rules, insights, known issues, and decision log |

### Practical Workflow CLI Examples

#### 1. Invoking GenerateSimulationSetup (Generic Mode)
The user provides a high-level description, letting the agent determine scales and templates:
```bash
rpg-lab workflow run GenerateSimulationSetup \
  --session-id "session_0001" \
  --input '{
    "mode": "generic",
    "user_goal": "A heavy combat congestion and pathfinding stress test with 300 actors",
    "constraints": {
      "budget_profile": "local_dev"
    }
  }'
```

#### 2. Invoking PrepareSimulationExecution (Specific Mode)
Once the setup is manually reviewed and approved, prepare the execution script:
```bash
rpg-lab workflow run PrepareSimulationExecution \
  --session-id "session_0001" \
  --input '{
    "mode": "specific",
    "experiment_path": "data/lab_sessions/session_0001/generation/draft_specs/experiment.yaml",
    "output_path": "data/lab_runs/combat_stress_001",
    "profile": "local_dev"
  }'
```

#### 3. Registering the Manual Simulation Result
After manually executing the prepared command script, register the generated run folder into the active session:
```bash
rpg-lab workflow run RegisterSimulationResult \
  --session-id "session_0001" \
  --input '{
    "mode": "specific",
    "lab_run_path": "data/lab_runs/combat_stress_001"
  }'
```

---

# Post-Implementation Documentation and Workflow Evolution Playbook

Since the Human-Gated Simulation Lab creates a multi-workflow orchestrator layer, it is vital to formalize how these workflows are documented, tuned, and updated in the future.

### Required Post-Implementation Documentation Pack

Immediately after implementing Phase 14, three definitive documentation files must be written and committed under `docs/engine/`:

1. **`docs/engine/lab_workflows_playbook.md` — The Tuning and Parameterization Playbook**
   - Documents the exact token and context budget coefficients (e.g. standard token bounds, time estimation scaling factors, and memory footprint ratios).
   - Details the pre-flight budget profiling configs (`local_dev`, `large_scale`, `stress_profile`).
   
2. **`docs/engine/lab_workflows_customization.md` — Workflow & Skill Customization Guide**
   - The definitive developer onboarding guide showing how to create a new custom workflow or register a new agent capability.
   - Documents how to format and register the `.agents/workflows/*.md` and `.agents/skills/*/SKILL.md` markdown contracts.
   
3. **`docs/engine/lab_workflows_troubleshooting.md` — Incident and Recovery Guide**
   - Outlines recovery procedures for failed or stuck sessions (e.g. manual status overrides in `session_manifest.json`).
   - Describes how to clean up orphaned locks, reset corruption status markers, or execute force-registration of simulation folders.

### Extensibility Rules: How to Update or Add Workflows in the Future

When requirements evolve, developers should follow these rules to update or introduce new workflows:

- **Strict Schema Enforcement**: Any new inputs must be mapped inside a corresponding Pydantic request model (`GenericSpecificRequestModel`).
- **Markdown Parity Rule**: The YAML contract parsed by the backend and the `.agents/workflows/<new-workflow>.md` frontmatter file **MUST** remain in 100% semantic parity.
- **Strict Isolation Verification**: Ensure that the new workflow only writes to session subfolders `data/lab_sessions/session_{session_id}/{stage_name}/` and does not mutate any long-term knowledge indexes without a validated user approval marker.


# Implementation Plan: Workflow Registry and Skill Contracts (M93)

We will introduce `src/lab/registry.py` and populate the `.agents/workflows/` automation specs.

## Proposed Changes

### [Component: Workflow Registry]

#### [NEW] [registry.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/registry.py)
*   **`WorkflowSkill` (Pydantic Model)**:
    Validates dynamic contracts loaded from YAML frontmatter:
    - `name`: str
    - `purpose`: str
    - `input_schema`: dict = Field(default_factory=dict)
    - `allowed_actions`: List[str] = Field(default_factory=list)
    - `forbidden_actions`: List[str] = Field(default_factory=list)
    - `output_artifacts`: List[str] = Field(default_factory=list)
    - `approval_required`: bool = Field(False)
    - `context_budget`: dict = Field(default_factory=dict)
    - `failure_behavior`: str = Field("STOP")
*   **`WorkflowRegistry`**:
    - `__init__(self, workflows_dir: str | Path, skills_dir: str | Path)`
    - `scan_and_register() -> None`: Scans and parses MD files in both directories.
    - `get_workflow(name: str) -> WorkflowSkill`: Fetches workflow. Raises `ValueError` for unknown names.
    - `get_skill(name: str) -> WorkflowSkill`: Fetches skill. Raises `ValueError` for unknown names.

#### [NEW] Phase 14 Workflows
- `.agents/workflows/generate-simulation-setup.md`
- `.agents/workflows/prepare-simulation-execution.md`
- `.agents/workflows/register-simulation-result.md`
- `.agents/workflows/compact-simulation-result.md`
- `.agents/workflows/investigate-simulation-result.md`
- `.agents/workflows/propose-simulation-enhancements.md`
- `.agents/workflows/update-knowledge-store.md`

## Verification Plan

### Automated Tests
- Run `pytest tests/unit/lab_agent/test_workflow_registry.py`
- Verify markdown YAML parsing, Pydantic type validation, contract enforcement, and forbidden action validation rules.

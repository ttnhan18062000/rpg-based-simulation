---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260524-LAB-REQUEST-CONTEXT
artifact_type: plan
tags: [lab, request, context]
---

# Implementation Plan: Input Request Model and Context Pack Builder (M94-M95)

We will introduce two new modules: `src/lab/request.py` and `src/lab/context.py`.

## Proposed Changes

### [Component: Request Models]

#### [NEW] [request.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/request.py)
*   **`WorkflowRequest` (Pydantic Model)**:
    - `workflow`: str
    - `mode`: Literal["generic", "specific"]
    - `user_goal`: Optional[str] = Field(None)
    - `specific_inputs`: dict = Field(default_factory=dict)
    - `constraints`: dict = Field(default_factory=dict)
    - `@model_validator(mode="after")` to enforce that:
      - If `mode == "generic"`, `user_goal` must be non-empty.
      - If `mode == "specific"`, `specific_inputs` must contain key-value inputs.

### [Component: Context Pack Builder]

#### [NEW] [context.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/context.py)
*   **`ContextPackBuilder`**:
    - `__init__(self, workspace_root: str | Path)`
    - `build_generation_pack(session_id: str, request: WorkflowRequest, limits: dict) -> dict`:
      Assembles rules, indices, and similar setups. Writes to `{session_dir}/generation/context_pack.json` and Markdown `context_pack.md`.
    - `build_investigation_pack(session_id: str, request: WorkflowRequest, limits: dict) -> dict`:
      Assembles scorecard aggregates, missing signal reports, and top N evidence packs. Writes to `{session_dir}/investigation/context_pack.json` and Markdown `context_pack.md`.

## Verification Plan

### Automated Tests
- Run `pytest tests/unit/lab_agent/test_workflow_request_model.py`
- Run `pytest tests/unit/lab_agent/test_context_pack_builder.py`
- Verify that request validation triggers correctly on modes and that raw log files are excluded by default in context packs.

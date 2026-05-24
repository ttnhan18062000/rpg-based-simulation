# Investigation: Input Request Model and Context Pack Builder (M94-M95)

We need to implement a structured input verification layer (`WorkflowRequest`) and a token-efficient context compilation engine (`ContextPackBuilder`).

## Request Specifications
The `WorkflowRequest` model must support:
- `workflow`: str (must not be empty, must correspond to a valid registered workflow name if registry is loaded).
- `mode`: `generic` or `specific`.
- `user_goal`: str (required when `mode == "generic"`).
- `specific_inputs`: dict (can represent exact parameters like `world_type`, `workers`, etc.).
- `constraints`: dict (contains budgets, entities cap, ticks cap, etc.).

## Context Packaging Strategy
To conserve LLM tokens and ensure high-density prompt packaging, we implement a **Summary First, Index Second, Evidence Third** hierarchy.

### 1. Generation Context Pack
*   **Target output**: `generation/context_pack.json` & `generation/context_pack.md`
*   **Inputs**:
    - Central indices: loaded via standard repository managers (`world_index.json`, etc.).
    - Worldbuilding rules and testing principles.
    - Tag-filtered known issues (e.g. filtered by domain or intent).
    - Similar successful setups.

### 2. Investigation Context Pack
*   **Target output**: `investigation/context_pack.json` & `investigation/context_pack.md`
*   **Inputs**:
    - Lab run manifests and scorecard aggregates.
    - Issue indices and signal coverages.
    - Top N evidence packs (from child runs).
*   **Constraint**: *Excludes heavy event logs (like `simulation_events.jsonl` or raw execution details) by default unless explicitly requested.*

## Component Safety & Path Resolution
All context pack assembly operations must resolve indices and rule files securely using standard traversal checks relative to project root or the session folder.
Missing files or indices should raise clear warnings/logs instead of crashing, ensuring maximum runtime resilience.

# Implementation Plan: Lab Session Model and Storage (M92)

We will introduce a dedicated module `src/lab/session.py` containing Pydantic models for the session manifest and the main controller `LabSessionStore`.

## Proposed Changes

### [Component: Lab Session Management]

#### [NEW] [session.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/session.py)
*   **`LabSessionManifest` (Pydantic Model)**:
    Exposes:
    - `session_id`: str (alphanumeric + hyphen/underscore)
    - `status`: str (ACTIVE, WAITING_FOR_USER, COMPLETED, FAILED, ARCHIVED)
    - `created_at`: str (ISO 8601 UTC timestamp)
    - `updated_at`: str (ISO 8601 UTC timestamp)
    - `current_stage`: str (GENERATION, EXECUTION_SUPPORT, REGISTRATION, INVESTIGATION, ENHANCEMENT, KNOWLEDGE_UPDATE)
    - `linked_lab_runs`: List[str]
    - `linked_worlds`: List[str]
    - `linked_scenarios`: List[str]
    - `linked_experiments`: List[str]
    - `approval_status`: Dict[str, str]
*   **`LabSessionStore` (Core Controller)**:
    Exposes:
    - `create_session(session_id: str) -> LabSessionManifest`
    - `load_session(session_id: str) -> LabSessionManifest`
    - `save_session(manifest: LabSessionManifest) -> None`
    - `list_sessions() -> List[str]`
    - `resolve_session_dir(session_id: str) -> Path`
    - `get_stage_dir(session_id: str, stage: str) -> Path`

## Verification Plan

### Automated Tests
- Run `pytest tests/unit/lab/test_lab_session_store.py`
- Verify 100% path coverage for normal path resolution, creation, validation errors, and directory traversal rejection.

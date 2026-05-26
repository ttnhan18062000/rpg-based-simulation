# Investigation: Lab Session Model and Storage (M92)

We need to implement a secure, robust file-based storage layer for Phase 14 Lab Sessions under `data/lab_sessions/session_{session_id}/`.

## Existing Patterns to Reuse

1. **Path Safety & Directory Guardrails**:
   In `src/lab/store.py` (`LabResultStore`), safe directory resolution is implemented using:
   ```python
   def _resolve_run_dir(self, lab_run_id: str) -> Path:
       self._validate_lab_run_id(lab_run_id)
       resolved = (self.lab_runs_dir / lab_run_id).resolve()
       ...
       if not resolved.is_relative_to(self.lab_runs_dir):
           raise PermissionError(...)
   ```
   We must reuse this exact pattern for `LabSessionStore` to prevent path traversal attempts.

2. **Schema & Serialization**:
   All specifications and results in `src/lab/schema.py` use Pydantic models. We will define a `LabSessionManifest` Pydantic model for session manifests to leverage automated type coercion, validation, and JSON serialization.

3. **Session Subdirectories**:
   As defined in the updated `lab_phase14.md` isolation boundary, every session requires specific subdirectories for absolute workspace segregation:
   - `generation/`
   - `execution_support/`
   - `manual_execution/`
   - `registration/`
   - `investigation/`
   - `enhancement/`
   - `knowledge_update/`

## Risks and Mitigation

- **Risk**: Concurrent sessions writing to overlapping directory structures.
  - *Mitigation*: The root directory `data/lab_sessions/session_{session_id}/` is resolved securely, and all subfolders are strictly scoped under it. Any write operation outside of this session path is blocked.
- **Risk**: Unsafe/malformed session IDs.
  - *Mitigation*: Validate `session_id` using a strict regular expression `^[a-zA-Z0-9_-]+$`. Reject empty, double-dot, or absolute path inputs immediately.

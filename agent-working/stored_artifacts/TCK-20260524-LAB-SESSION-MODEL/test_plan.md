---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260524-LAB-SESSION-MODEL
artifact_type: test_plan
tags: [lab, session, model]
---

# Test Plan: Lab Session Model and Storage (M92)

We will implement isolated unit tests in `tests/unit/lab/test_lab_session_store.py` using `pytest`.

## Automated Unit Tests

### Normal Operations
- **`test_create_session_success`**: Creating a session creates `session_manifest.json` and all 7 subdirectories cleanly under `data/lab_sessions/session_{session_id}/`.
- **`test_load_session_success`**: Validates loading a saved session manifest returns a populated `LabSessionManifest` model.
- **`test_save_session_success`**: Modifying a manifest and saving it writes the correct updated fields to disk.
- **`test_list_sessions`**: Scans the sessions folder and lists active session IDs correctly.

### Boundary and Error Cases
- **`test_duplicate_session_fails`**: Attempting to create an existing session ID raises an exception.
- **`test_missing_session_fails`**: Attempting to load a non-existent session ID raises `FileNotFoundError`.
- **`test_invalid_session_id_fails`**: Session IDs containing symbols or trailing slashes are strictly rejected at validation time.
- **`test_path_traversal_blocked`**: Malformed session IDs with traversal sequences like `../../` or absolute roots raise a `PermissionError` and do not touch disk.
- **`test_manifest_corruption_fails`**: Corrupted manifest JSON structures are safely caught and raise standard parsing errors.

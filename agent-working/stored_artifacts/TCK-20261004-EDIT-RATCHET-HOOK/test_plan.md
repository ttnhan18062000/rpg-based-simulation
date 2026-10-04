---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-EDIT-RATCHET-HOOK
artifact_type: test_plan
tags: [architecture, hooks]
---

# Test plan — TCK-20261004-EDIT-RATCHET-HOOK

`tests/codebase/test_edit_ratchet_hook.py` (scratch-repo fixtures, hook run via `main(stdin)` and once as a subprocess for exit code and stdout):
- new violation in the edited file: JSON with `hookSpecificOutput.additionalContext`, exit 0
- grandfathered-only (row within ceiling): no output
- output over 20 lines is capped with a count
- non-`src` path, non-`.py`, nonexistent file, path outside the repo (including `..` traversal and a symlink), non-edit tool, malformed or empty stdin: no output, exit 0
- ruff missing / ruff exit 2 / registry missing / time budget exceeded (monkeypatched slow ruff): no output, exit 0
- unexpected exception inside the hook: no output, exit 0
- `staged_ratchet`: existing tests unchanged and green; new test that `timeout` and `python` default to prior behaviour and that a timeout becomes `HookSkipped` (pre-commit prints the skip line, exit 0); pre-commit still rejects NEW/WORSE
- wiring test for the settings entry (after owner yes)
Run under the 2 GB cap, venv python, own `--basetemp`.

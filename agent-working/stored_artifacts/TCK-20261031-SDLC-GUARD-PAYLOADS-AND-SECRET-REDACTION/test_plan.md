---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION
artifact_type: test_plan
tags: [ai, governance, security]
---

# Test plan

| Check | Test |
|---|---|
| Each of the four bypass forms asks; ordinary commands stay allowed | `tests/tools/test_session_guard_payloads.py` (wrapper, interpreter, `gh api` writes by method, field and GraphQL, `--delete-branch`; read-only forms stay allowed) plus the existing `test_session_classify.py` and `test_session_guard*.py` |
| A token-shaped string never reaches a shard row or a transit bundle; redaction failure writes nothing raw | `tests/tools/test_secret_redact.py` (positive control, every field of the hook row, bundle bytes, non-UTF-8, failed file left out; fake tokens built by concatenation; a final scan with the repository's own `scan_for_secrets`) |
| The ConfigChange script notifies only with allowlisted sequences, strips control characters, logs one line with only the listed fields, still notifies when the log fails, exits 0 silently on malformed input | `tests/tools/test_config_change_warning.py` |
| The wiring is the approved shape, fails open, runs from the repo, writes no line into the real `tmp/`, and is registered | `tests/tools/test_config_change_warning.py` (wiring tests) and `test_capability_envelope_baseline.py` |
| The settings file shape tests are unaffected | `test_settings_json_hooks_wiring.py`, `test_bash_secret_scan_hook.py`, `test_monitoring_hook_subdirectory_cwd.py`, `test_settings_json_edit_write_hook_sidecar_scope.py` |
| Real-event behaviour | the owner's live test (results in the ticket's Implementation Notes) |
| Whole suite | full `tests/tools` in a lead-planner slot |

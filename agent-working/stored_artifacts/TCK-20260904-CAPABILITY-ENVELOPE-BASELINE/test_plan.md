---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-CAPABILITY-ENVELOPE-BASELINE
artifact_type: test_plan
tags: [governance, ai, security]
---

# Test Plan — TCK-20260904-CAPABILITY-ENVELOPE-BASELINE

## Regression Surface

This ticket adds new files only (a new `registries/`-convention baseline plus a new diff script and
its own tests); it modifies no existing production module. The regression surface is "prove the
existing registry convention and the same-day sibling ticket's own tooling are undisturbed," not
"re-verify existing behavior changed correctly."

**Unit (must keep passing unmodified):**
- `tests/tools/test_tag_registry.py` — the registry convention this ticket's Scope explicitly names
  as its template; must pass unmodified, proving this ticket does not touch `tools/tag_registry.py`
  or `registries/tag_registry.jsonl` itself.
- `tests/tools/test_layer_registry.py` — same, for `tools/layer_registry.py` /
  `registries/layer_registry.jsonl`.

**Integration:**
- `tests/tools/test_agent_tool_usage_baseline.py` — the same-day, same-epic M1 sibling ticket's own
  test suite (`TCK-20260904-AGENT-TOOL-USAGE-BASELINE`). Must keep passing unmodified, proving this
  ticket's new files (likely also under `tools/` and with their own new `tests/tools/test_*.py` file)
  do not collide with or accidentally import/monkeypatch anything that ticket's tooling depends on.

**Arena-combat:** not applicable — this ticket touches no `src/` simulation code.

## New Tests Required

Per this ticket's 4 acceptance criteria (test file path assumed as
`tests/tools/test_capability_envelope_baseline.py`, mirroring the 1:1
`tools/<name>.py` ↔ `tests/tools/test_<name>.py` naming convention already used by every sibling
registry/audit script in this repo — planner should confirm the exact module name):

- **Test name:** `test_baseline_schema_covers_all_four_settings_local_fields`
  **Category:** unit
  **Verifies:** the baseline file's schema/loader recognizes `permissions.allow` entries plus all 3
  MCP fields (`enableAllProjectMcpServers`, `enabledMcpjsonServers`, `disabledMcpjsonServers`) — not
  only `permissions.allow`. Regression guard against silently narrowing back to the smaller,
  incorrect scope. Covers AC1.
  **Where:** `tests/tools/test_capability_envelope_baseline.py`

- **Test name:** `test_diff_script_runs_against_real_settings_local_json_produces_real_report`
  **Category:** integration
  **Verifies:** invoking the diff script against the real main-checkout `settings.local.json` (114
  live `permissions.allow` entries as of this investigation, computed live by the test, never
  hardcoded) produces a real, populated report — not an empty stub or a placeholder count. Covers
  AC2 directly.
  **Where:** `tests/tools/test_capability_envelope_baseline.py`

- **Test name:** `test_diff_script_handles_missing_settings_local_json_gracefully`
  **Category:** unit / integration
  **Verifies:** running the diff script against a directory with no `settings.local.json` at all
  (this worktree is a real, live instance of exactly this condition — see investigation.md) reports a
  clean "no local file to audit" condition rather than raising an unhandled exception. Covers a
  real negative-path gap identified in investigation.md's Risks section.
  **Where:** `tests/tools/test_capability_envelope_baseline.py`

- **Test name:** `test_diff_script_output_states_audit_only_no_enforcement`
  **Category:** unit
  **Verifies:** the diff script's own docstring and/or printed report output contains an explicit,
  unambiguous audit-only / no-runtime-enforcement disclaimer. Covers AC3.
  **Where:** `tests/tools/test_capability_envelope_baseline.py`

- **Test name:** `test_clean_baseline_input_produces_empty_result`
  **Category:** unit
  **Verifies:** a synthetic `settings.local.json` fixture whose every entry is already within a
  synthetic baseline produces an empty/clean diff result (positive control). Covers AC4's first half.
  **Where:** `tests/tools/test_capability_envelope_baseline.py`

- **Test name:** `test_out_of_envelope_entry_produces_flagged_result`
  **Category:** unit
  **Verifies:** a synthetic `settings.local.json` fixture containing exactly one entry outside a
  synthetic baseline produces a report flagging exactly that one entry (negative control). Covers
  AC4's second half.
  **Where:** `tests/tools/test_capability_envelope_baseline.py`

- **Test name:** `test_baseline_registry_rejects_or_governs_duplicate_or_conflicting_entries`
  **Category:** architecture guard
  **Verifies:** whichever baseline shape the planner chooses (append-only registry vs. versioned
  snapshot manifest — see investigation.md's Risks), a test enforcing that shape's own invariant:
  either rejects re-adding an already-present entry (mirrors
  `test_tag_registry.py::test_add_tag_rejects_duplicate_tag`) or requires an explicit version marker
  on any wholesale replacement (mirrors the `manifest.py` capture/compare precedent). Prevents the
  baseline file itself from silently drifting into an ambiguous or duplicated state.
  **Where:** `tests/tools/test_capability_envelope_baseline.py`

- **Test name:** `test_diff_script_is_read_only_against_settings_local_json_and_baseline`
  **Category:** architecture guard
  **Verifies:** `git status --porcelain` (or a direct byte-comparison) shows zero change to
  `.claude/settings.local.json`, the committed baseline file, and `registries/` before vs. after
  running the diff script — mirrors the sibling M1 ticket's `_porcelain_snapshot()` read-only-guard
  pattern and this project's Durable State Rule (an audit script must never mutate what it audits).
  **Where:** `tests/tools/test_capability_envelope_baseline.py`

## Scoped Pytest Commands

```bash
# This ticket's new test file (primary — exact filename to be confirmed by planner):
pytest tests/tools/test_capability_envelope_baseline.py -v

# Registry-convention regression surface (this ticket's own named template):
pytest tests/tools/test_tag_registry.py tests/tools/test_layer_registry.py -v

# Same-day, same-epic sibling ticket's tests — proves no collision:
pytest tests/tools/test_agent_tool_usage_baseline.py -v

# Final scoped sweep across the touched domain (never the bare `pytest tests/`):
pytest tests/tools/ -k "capability_envelope or tag_registry or layer_registry or agent_tool_usage" -v
```

## Anti-Drift Test Guards

- **`test_diff_script_is_read_only_against_settings_local_json_and_baseline`** is the direct
  enforcement of this project's Durable State Rule for this ticket: an audit-only script must never
  mutate the file it audits or the baseline it audits against — proven against the real files, not a
  mocked filesystem.
- **`test_diff_script_output_states_audit_only_no_enforcement`** guards against the single most
  consequential scope-creep risk named in both the ticket and the parent epic doc: presenting this
  tooling as more than auditable — i.e., silently implying or claiming a runtime-enforcement
  guarantee that does not exist.
- **`test_diff_script_handles_missing_settings_local_json_gracefully`** guards against the script
  assuming `settings.local.json` always exists — a real, currently-true-in-this-worktree condition,
  not a hypothetical.
- **`test_baseline_schema_covers_all_four_settings_local_fields`** guards against silently narrowing
  scope back to `permissions.allow` only, which the ticket's AC1 explicitly calls out as an
  insufficient, previously-considered-and-rejected scope.
- **`test_clean_baseline_input_produces_empty_result`** / **`test_out_of_envelope_entry_produces_flagged_result`**
  together guard against a stub diff script that always reports "clean" regardless of input — a
  known failure mode for audit tooling that silently never fires and gives false confidence.
- **`test_baseline_registry_rejects_or_governs_duplicate_or_conflicting_entries`** guards against the
  baseline file itself silently drifting into an inconsistent or ambiguous state, mirroring the
  append-only-uniqueness invariant `tag_registry.py`/`layer_registry.py` already enforce for their
  own registries.

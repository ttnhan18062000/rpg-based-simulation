---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260730-PROVIDER-HOOK-POLICY
phase: done
date: 2026-07-30
tags: [ai, hooks, workflows, documentation, testing]
---

# TCK-20260730-PROVIDER-HOOK-POLICY

## Title
Define the provider hook-surface policy and Codex activation boundary

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Make hook terminology precise before Codex hooks can be activated. Codex exposes more lifecycle events than the shared contract normalizes, while only `PostToolUse` has direct payload-capture evidence. The contract needs an enforceable distinction between a provider capability being available, a shared event being normalized, and an event actually being enabled in project configuration.

## Scope
- Add a contract-owned, validator-covered provider hook-surface policy that separately represents `available`, `normalized`, and `enabled` events.
- Record the current truth: Claude enables `PreToolUse` and `PostToolUse`; Codex has ten documented available events; the committed Codex project configuration enables zero hooks.
- Keep Codex's other eight events out of normalized/enabled status. `PreToolUse` remains schema-valid but is not an evidenced first Codex activation candidate.
- Declare `PostToolUse` as the sole possible first Codex enabled event, constrained to the existing evidenced writer functions `write_line` and `write_lines`.
- Define later activation prerequisites: contemporaneous human approval, scratch-first payload/schema verification, project and hook trust review, failure/timeout fail-open behavior, redacted output, out-of-band diagnostics, reviewed config diff, and one-action rollback.
- Add tests that reject conflating availability with support or enabled configuration and retain proof that committed `.codex/config.toml` is hook-free.

## Out of Scope
- Registering any actual Codex hook or changing committed `.codex/config.toml` into a hook-bearing configuration.
- Invoking Codex, running a paid/live pilot, or adding a subprocess execution path to guardrail tooling.
- Expanding normalized hook vocabulary merely because a provider documents an event.
- Replacing existing pilot guardrails or their no-live-execution-path tests.

## Acceptance Criteria
- [x] Contract validation independently checks available, normalized, and enabled hook status or another equally machine-checkable representation.
- [x] The policy accurately represents Claude's two enabled events, Codex's ten available events, Codex's zero enabled events, and the shared normalized vocabulary without falsely claiming broader Codex support.
- [x] Only Codex `PostToolUse` is approved as a future initial activation candidate; its evidenced writer subset is explicitly bound to `write_line`/`write_lines`.
- [x] Tests prove a committed Codex config remains hook-free and guardrail code retains no live Codex invocation path.
- [x] Future activation requirements are explicit enough for a later ticket to consume without reinterpreting consent, rollback, redaction, or failure behavior.

## Related Tickets
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC (parent)
- TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE (DONE; payload evidence)
- TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS (DONE; enabled-surface and rollback mechanisms)

## Related Docs
- docs/plans/archive/agent_infrastructure/current_codex_runtime_status_and_activation_plan.md
- docs/ai/codex_capability_matrix.md
- agent-orchestration/hook-events.yaml
- agent-orchestration/intentional-divergences.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE/

## Related Code Areas
- agent-orchestration/hook-events.yaml
- agent-orchestration/contract.yaml
- agent-orchestration/README.md
- .claude/settings.json
- .codex/config.toml
- tools/agent_codex_pilot_guardrails/enabled_surface.py
- tools/agent_replay_codex/codex_config_guard.py
- tests/agent_orchestration_codex_adapter/test_no_production_hook_enabled.py
- tests/agent_codex_pilot_guardrails/test_enabled_surface.py
- tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py
- tests/tools/test_codex_hook_payload_fixture.py

## Assumptions / Open Questions
- The policy structure may be a new contract file rather than an overloaded extension of `hook-events.yaml`; Investigate must choose the smallest validated shape.
- Project trust and hook trust remain distinct checks and must not be assumed satisfied by a committed config alone.

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260730-PROVIDER-HOOK-POLICY/plan.md`'s 11 ordered
steps, exactly as specified, with no deviations:

1. Created `agent-orchestration/hook-surface-policy.yaml` (new sibling contract file,
   `hook_surface_policy_version: 1`) with `providers.claude.enabled_events` (2 events),
   `providers.codex.available_events` (the 10-event capability-matrix list) +
   `providers.codex.enabled_events: []`, a single `activation_candidates` entry (Codex
   `PostToolUse`, `writer_functions: [write_line, write_lines]`), and an
   `activation_prerequisites` list of the 9 named future-activation requirements (each a
   stable `id` + still-required `description`, never worded as already-satisfied). No
   `approved`/`granted`/`authorized` key anywhere in the file.
2. Added `_load_hook_surface_policy_yaml(path, hook_events)` to
   `tools/agent_orchestration/loader.py`, mirroring `_load_hook_events_yaml`'s idiom exactly.
   Enforces: required top-level keys; per-provider `enabled_events` (list[str], may be empty)
   with `available_events` optional; `enabled_events ⊆ hook-events.yaml.hook_types` ids
   (normalized check); `enabled_events ⊆ available_events` where declared; each
   `activation_candidates` entry's `event` must be in that provider's `available_events`;
   each `activation_prerequisites` entry requires a unique `id` + non-empty `description`;
   and a hard reject (via `_reject_authorization_implying_keys`) of any `approved`/`granted`/
   `authorized` key with a `true` value on any `activation_candidates` or
   `activation_prerequisites` entry. Added `hook_surface_policy: dict[str, Any]` to
   `ContractBundle` and wired the new load as the 7th call in `load_contract()`, after
   `_load_hook_events_yaml` (rule 3 needs its already-loaded value). Updated the module
   docstring's "six files" → "seven files" for accuracy.
3. Added 11 table-driven error-path tests to
   `tests/agent_orchestration/test_validator_errors.py`, one per Step 2 validation rule
   (missing version, missing providers, provider missing `enabled_events`, enabled-not-
   normalized, enabled-not-available, candidate-event-not-available, prerequisite missing
   `id`/`description`, duplicate `id`, and `approved`/`granted`/`authorized`=`true` on both
   prerequisite and candidate entries), each asserting the exact file path + field appear in
   the raised `ContractValidationError`.
4. Wired `tools/agent_orchestration/generator.py`'s `generate()` with a 7th write step
   (`hook-surface-policy.yaml` sourced from `bundle.hook_surface_policy`, same
   `_assert_write_allowed` guard as the other 6 writes), matching the existing per-file
   pattern exactly.
5. Added a 6th `governs:` entry to `agent-orchestration/contract.yaml`
   (`hook-surface-policy.yaml` / `hook_surface_policy_version`), left `contract.yaml`'s own
   `version` unmodified (additive, per the plan's Design Decision 2). Added a Layout table
   row and a versioning-scheme bullet to `agent-orchestration/README.md`, and fixed its
   "five sibling files" → "six sibling files" prose per the reviewer's minor observation.
   Added `test_new_contract_file_wired_into_readme_and_manifest`.
6. Added `test_policy_represents_claude_two_enabled_events`,
   `test_policy_represents_codex_ten_available_events` (matched against the 10-event set from
   `docs/ai/codex_capability_matrix.md` §1), and `test_policy_represents_codex_zero_enabled_events`
   (cross-checked against `.codex/config.toml` parsing to `{}` via `tomllib.load`).
7. Added `test_policy_normalized_vocabulary_matches_hook_events_yaml` (asserts every
   provider's real `enabled_events` ⊆ `hook-events.yaml`'s real `hook_types` ids, and that the
   new file never re-declares its own `hook_types`/`normalized_events` key) and
   `test_hook_events_yaml_unchanged_normalized_vocabulary` (pins `hook-events.yaml`'s
   `hook_types` ids to exactly `{PreToolUse, PostToolUse}`).
8. Added `test_only_codex_post_tool_use_is_an_activation_candidate` and
   `test_activation_candidate_writer_subset_is_write_line_and_write_lines`, the latter
   importing `tools.agent_codex_pilot_guardrails.enabled_surface.EVIDENCED_WRITER_FUNCTIONS`
   directly (read-only cross-check; zero lines added to that package or its tests).
9. Added `test_activation_prerequisites_cover_all_nine_named_items` (matched by stable `id`,
   not prose) and `test_activation_prerequisites_do_not_imply_authorization` (real-file
   positive check; the negative/rejection case is covered by Step 3's
   `approved`/`granted`/`authorized` table-driven cases).
10. Added `test_committed_codex_config_still_hook_free` to
    `tests/agent_replay_codex/test_codex_config_guard.py`, reusing
    `codex_config_guard.snapshot_config_bytes` and comparing its sha256 digest against a
    constant recorded from `.codex/config.toml`'s bytes before this ticket's implementation
    began (`74074efc3b2be3a08803b658c6a086dce1548c3901071488c317da96e961c758`) — stronger than
    the existing structural hooks-key walk, since it also catches non-`hooks`-key edits.
11. Ran the full scoped regression (`tests/agent_orchestration/`,
    `tests/agent_orchestration_claude_adapter/`, `tests/agent_orchestration_codex_adapter/`,
    `tests/agent_replay_codex/`, `tests/agent_codex_pilot_guardrails/`,
    `tests/tools/test_codex_hook_payload_fixture.py`,
    `tests/tools/test_codex_capability_diagnostics.py`): 184 passed, 5 skipped, exactly the
    same 3 pre-existing unrelated failures by name
    (`test_terminal_status_conformance_finalize_incomplete_appears_once_on_both_sides`,
    `test_extract_all_terminal_statuses_dedupes_by_value_not_call_site_count`,
    `test_provider_field_coverage_against_real_corpus_is_currently_zero`). Also ran
    `test_generator_write_guard.py` + `test_generator_traceability.py` directly: 12 passed.

`agent-orchestration/hook-events.yaml` and `.codex/config.toml` were not modified at any point
(confirmed via `git status`/`git diff` — zero changes to either). No code was added to
`tools/agent_codex_pilot_guardrails/`; `test_no_live_execution_path.py` passed unmodified.

## Test Summary
New tests added: 1 (file exists/parses) + 1 (load_contract includes field) + 11
(table-driven validator error paths) + 1 (README/manifest wiring) + 3 (provider
representation) + 2 (normalized-vocabulary consistency + hook-events.yaml immutability) + 2
(activation-candidate) + 2 (activation-prerequisite coverage + anti-authorization) + 1
(byte-identity `.codex/config.toml` regression) = 24 new tests, all passing. Full scoped
regression command (per `test_plan.md`) run twice (mid-implementation and final): 184
passed, 5 skipped, 3 pre-existing unrelated failures unchanged in count and identity.

## Files Changed
- agent-orchestration/hook-surface-policy.yaml (new)
- agent-orchestration/contract.yaml
- agent-orchestration/README.md
- tools/agent_orchestration/loader.py
- tools/agent_orchestration/generator.py
- tests/agent_orchestration/test_contract_structure.py
- tests/agent_orchestration/test_validator_errors.py
- tests/agent_replay_codex/test_codex_config_guard.py

## Completion Summary
All 5 acceptance criteria satisfied: (1) contract validation independently and structurally
checks available/normalized/enabled hook status via `loader.py`'s new load function, not just
via tests; (2) the policy accurately represents Claude's 2 enabled events, Codex's 10
available events, Codex's 0 enabled events, and stays consistent with — without duplicating
— `hook-events.yaml`'s normalized vocabulary; (3) only Codex `PostToolUse` is an activation
candidate, its writer subset bound to `write_line`/`write_lines` and cross-checked against
`enabled_surface.EVIDENCED_WRITER_FUNCTIONS`; (4) tests prove the committed Codex config
stays hook-free (structural walk, `== {}` parse, and new byte-identity sha256 check) and the
pilot guardrails package retains zero live-execution path, entirely untouched by this
ticket; (5) all 9 future activation requirements are declared as explicit, stable,
machine-checkable, still-required entries, structurally guarded against ever reading as
already-granted authorization. `agent-orchestration/hook-events.yaml` and
`.codex/config.toml` remain byte-for-byte unmodified throughout.

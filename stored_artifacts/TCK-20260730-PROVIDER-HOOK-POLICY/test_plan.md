---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260730-PROVIDER-HOOK-POLICY
artifact_type: test_plan
tags: [ai, hooks, workflows, documentation, testing]
---

# Test Plan — TCK-20260730-PROVIDER-HOOK-POLICY

## Regression Surface

All unit-level (no `arena-combat`/simulation-integration surface applies — this ticket
touches only `agent-orchestration/` contract data and `tools/agent_orchestration/`,
`tools/agent_codex_pilot_guardrails/`, `tools/agent_replay_codex/` tooling).

### Contract loader/generator (must stay green — direct consumers of any new file)
- `tests/agent_orchestration/test_contract_structure.py` — including
  `test_agent_orchestration_dir_has_required_files` and
  `test_load_contract_succeeds_against_the_real_contract`, both of which must be extended
  (see New Tests) rather than left stale.
- `tests/agent_orchestration/test_validator_errors.py` — table-driven
  `ContractValidationError` cases; the new loader function must follow the same
  named-file/named-field error-message convention these tests assert.
- `tests/agent_orchestration/test_validator_no_network_calls.py`
- `tests/agent_orchestration/test_skills_catalog.py`
- `tests/agent_orchestration/test_bootstrap_vocabulary_equality.py`

### Codex/Claude adapters and generation
- `tests/agent_orchestration_codex_adapter/` (all 8 files) — especially
  `test_no_production_hook_enabled.py` (AC #4's direct proof) and
  `test_generator_write_guard.py`/`test_generator_traceability.py` (generator behavior
  must stay correct once a 6th file is added to its fixed write sequence).
- `tests/agent_orchestration_claude_adapter/` — conformance tests comparing the contract
  to the live `.claude/workflows/implement-ticket.js`. Note: 2 of these
  (`test_terminal_status_conformance.py::test_terminal_status_conformance_finalize_incomplete_appears_once_on_both_sides`,
  `test_terminal_status_extractor.py::test_extract_all_terminal_statuses_dedupes_by_value_not_call_site_count`)
  are **currently failing on `main`/this branch already**, on stale hardcoded line numbers
  unrelated to this ticket (see investigation.md Risks). Do not treat their continued
  failure as a regression this ticket caused; do not "fix" them either — out of scope.

### Pilot guardrails and evidenced-surface guards
- `tests/agent_codex_pilot_guardrails/test_enabled_surface.py` — must stay green
  unmodified unless implementation adds an optional cross-check function (additive only,
  see investigation.md); the existing hardcoded
  `EVIDENCED_HOOK_EVENTS`/`EVIDENCED_WRITER_FUNCTIONS` constants must not change value.
- `tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py` — the
  highest-priority anti-drift guard in this domain; must pass with zero weakening.
- `tests/agent_codex_pilot_guardrails/test_baseline_manifest_gate.py`,
  `test_pilot_manifest.py`, `test_signoff_gate.py`, `test_ticket_selection.py`,
  `test_config_rollback.py`.
- Note: `tests/agent_codex_pilot_guardrails/test_concurrent_claim.py::test_provider_field_coverage_against_real_corpus_is_currently_zero`
  is **currently failing already** (real value is now 1, not 0, following
  `TCK-20260730-CLAUDE-EXECUTION-IDENTITY`) — pre-existing, unrelated, not a regression to
  fix here.

### Replay/config-guard tooling
- `tests/agent_replay_codex/test_codex_config_guard.py` and the rest of
  `tests/agent_replay_codex/` (containment, consent gate, no-forbidden-calls, phase
  parity, shadow-mode comparison) — none of these read the new policy file directly today,
  but they share `codex_config_guard.py`'s hook-free assertion this ticket must not weaken.

### Fixture/capability evidence
- `tests/tools/test_codex_hook_payload_fixture.py` — must stay green unmodified; this
  ticket only *reads* this fixture's evidence (the `PostToolUse`-is-the-only-evidenced-event
  fact), it does not touch the fixture itself.
- `tests/tools/test_codex_capability_diagnostics.py` — same: read-only source of truth for
  the Codex 10-event claim's "capability enabled" corroboration; not modified by this
  ticket.

## New Tests Required

Per acceptance criteria (AC numbers per the ticket's own list):

1. **`test_hook_surface_policy_file_exists_and_parses`** — unit — verifies the new
   `agent-orchestration/hook-surface-policy.yaml` (or whatever exact filename Plan settles
   on) exists and parses to a YAML mapping. Lives in
   `tests/agent_orchestration/test_contract_structure.py` (extend
   `test_agent_orchestration_dir_has_required_files`'s `required_files` list, following its
   existing pattern exactly).

2. **`test_load_contract_includes_hook_surface_policy`** — unit — extends
   `test_load_contract_succeeds_against_the_real_contract` (or a new sibling test) to assert
   `ContractBundle` carries the new field and it is non-empty/well-typed. Lives in
   `tests/agent_orchestration/test_contract_structure.py`.

3. **`test_hook_surface_policy_missing_required_field_raises_named_error`** (and sibling
   malformed-value cases, table-driven like the existing 3 cases) — unit — proves
   `load_contract` raises `ContractValidationError` naming the exact file/field for the new
   file, mirroring `test_contract_yaml_missing_version_raises_named_error`'s
   copy-and-mutate-a-tmp-contract pattern exactly. Lives in
   `tests/agent_orchestration/test_validator_errors.py`. (AC #1: "Contract validation
   independently checks... or another equally machine-checkable representation.")

4. **`test_policy_represents_claude_two_enabled_events`** — unit — asserts the new file's
   `providers.claude.enabled_events` (or equivalent field) is exactly
   `{"PreToolUse", "PostToolUse"}`, matching `.claude/settings.json`'s real hook keys.
   Lives alongside test 1/2, `tests/agent_orchestration/test_contract_structure.py`.
   (AC #2.)

5. **`test_policy_represents_codex_ten_available_events`** — unit — asserts the new file's
   `providers.codex.available_events` is exactly the 10-event set from
   `docs/ai/codex_capability_matrix.md` §1 (`PreToolUse`, `PermissionRequest`,
   `PostToolUse`, `PreCompact`, `PostCompact`, `UserPromptSubmit`, `SubagentStop`, `Stop`,
   `SessionStart`, `SubagentStart`). (AC #2.)

6. **`test_policy_represents_codex_zero_enabled_events`** — unit — asserts
   `providers.codex.enabled_events == []` (or equivalent empty representation),
   cross-checked against `.codex/config.toml` parsing to `{}` (reuse
   `codex_config_guard.assert_committed_config_hook_free` or an equivalent read). (AC #2,
   AC #4 overlap.)

7. **`test_policy_normalized_vocabulary_matches_hook_events_yaml`** — unit,
   **architecture guard** — asserts the new file's normalized-vocabulary
   representation (however it cross-references `hook-events.yaml`) stays consistent with
   `hook-events.yaml`'s real `hook_types` ids, and does **not** duplicate/re-declare a
   second independent list that could drift. This is the single most important new
   anti-drift test for the "smallest validated shape" design decision. Lives in
   `tests/agent_orchestration/test_contract_structure.py`.

8. **`test_only_codex_post_tool_use_is_an_activation_candidate`** — unit — asserts the new
   file's activation-candidate list contains exactly one entry, provider `codex`, event
   `PostToolUse`, and that no other Codex event (in particular `PreToolUse`, the schema-
   valid-but-unevidenced one) appears as a candidate. (AC #3.)

9. **`test_activation_candidate_writer_subset_is_write_line_and_write_lines`** — unit —
   asserts the `PostToolUse` candidate's constrained writer-function subset is exactly
   `{"write_line", "write_lines"}`, matching `enabled_surface.EVIDENCED_WRITER_FUNCTIONS`
   value-for-value (cross-check against the existing constant, not merely a hardcoded
   literal in the new test, to catch future drift between the two). (AC #3.)

10. **`test_hook_events_yaml_unchanged_normalized_vocabulary`** — unit, **anti-drift
    guard** — asserts `hook-events.yaml`'s `hook_types` still contains exactly
    `{PreToolUse, PostToolUse}`, i.e. the new file's addition did not smuggle any of the
    8 Codex-only events into the existing normalized list. Lives in
    `tests/agent_orchestration/test_contract_structure.py`.

11. **`test_committed_codex_config_still_hook_free`** — integration — a first-class
    assertion in this ticket's own scope (not merely inherited) that after this ticket's
    changes, `.codex/config.toml` is byte-for-byte unchanged from its pre-ticket content
    (snapshot-and-compare, reusing
    `codex_config_guard.snapshot_config_bytes`/`assert_config_bytes_unchanged`). (AC #4.)
    Lives in `tests/agent_orchestration_codex_adapter/` or
    `tests/agent_replay_codex/test_codex_config_guard.py`, alongside the existing
    hook-free-walk tests.

12. **`test_guardrail_package_still_has_no_live_execution_path`** — architecture guard —
    if any code is added to `tools/agent_codex_pilot_guardrails/` (e.g. an optional
    cross-check function reading the new policy file), re-run
    `test_no_live_execution_path.py`'s existing AST scans against the new/changed file(s)
    — this should fall out "for free" from the existing test's `_package_py_files()` glob
    scan, but explicitly verify the new file is included in that glob's discovered list
    rather than assuming it. (AC #4, anti-drift.)

13. **`test_activation_prerequisites_cover_all_nine_named_items`** — unit — asserts the
    new file's `activation_prerequisites` list contains machine-checkable entries for all
    nine items named in the ticket's Scope: contemporaneous human approval, scratch-first
    payload/schema verification, project trust review, hook trust review,
    failure/timeout fail-open behavior, redacted output, out-of-band diagnostics, reviewed
    config diff, one-action rollback — by stable `id`, not by prose-matching free text.
    (AC #5.)

14. **`test_activation_prerequisites_do_not_imply_authorization`** — unit, **anti-drift
    guard** — asserts no `activation_prerequisites` or `activation_candidates` entry
    contains an `approved`/`granted`/`authorized` truthy field or equivalent — the file may
    declare *what* is required, never assert it has already been satisfied. Guards against
    the specific "this is not authorization" hazard the current status plan doc calls out
    explicitly.

15. **`test_new_contract_file_wired_into_readme_and_manifest`** — unit — asserts
    `agent-orchestration/contract.yaml`'s `governs:` list contains an entry for the new
    file with a `version_field`, and (string-search or structured, Plan's discretion) that
    `agent-orchestration/README.md`'s Layout table names the new file. Guards against the
    documentation/manifest drift the versioning-scheme section explicitly requires.

## Scoped Pytest Commands

Never `pytest tests/`. Use exactly the domain-scoped set (mirrors the baseline commands
already documented in
`docs/plans/archive/agent_infrastructure/current_codex_runtime_status_and_activation_plan.md`,
extended with the fixture/diagnostics tests this ticket's facts depend on):

```bash
.venv/bin/python3 -m pytest \
  tests/agent_orchestration/ \
  tests/agent_orchestration_claude_adapter/ \
  tests/agent_orchestration_codex_adapter/ \
  tests/agent_replay_codex/ \
  tests/agent_codex_pilot_guardrails/ \
  tests/tools/test_codex_hook_payload_fixture.py \
  tests/tools/test_codex_capability_diagnostics.py \
  -v
```

Run this exact command as the pre-implementation baseline (confirmed during this
investigation: 3 pre-existing failures unrelated to this ticket, 158 passed, 5 skipped —
see investigation.md Risks for the exact 3 failing test names) and again post-implementation
to confirm: (a) the same 3 pre-existing failures remain isolated and unchanged in count/
identity, and (b) every new test above passes.

If the new policy file's loader wiring is added to `tools/agent_orchestration/generator.py`,
also run any existing generator-specific test file directly for a tighter feedback loop:

```bash
.venv/bin/python3 -m pytest tests/agent_orchestration_codex_adapter/test_generator_write_guard.py tests/agent_orchestration_codex_adapter/test_generator_traceability.py -v
```

## Anti-Drift Test Guards

- **`hook-events.yaml` normalized-vocabulary immutability** (New Test 10 /
  `test_hook_events_yaml_unchanged_normalized_vocabulary`): the single test most likely to
  catch a well-intentioned but scope-violating "just add the Codex events to
  `hook_types` too" shortcut during implementation.
- **`test_no_live_execution_path.py` (existing, unmodified)**: catches any accidental
  subprocess/dynamic-import/execution-shaped-function scope creep if implementation touches
  `tools/agent_codex_pilot_guardrails/` at all. Must keep passing with literally zero edits
  to its assertions.
- **New Test 14 (`test_activation_prerequisites_do_not_imply_authorization`)**: catches the
  specific hazard of the new contract file accidentally reading as a live approval record
  rather than a declared-requirements list — a subtle drift the ticket's Scope/Out-of-Scope
  boundary depends on staying correct.
- **New Test 9 (writer-subset cross-check against `enabled_surface.EVIDENCED_WRITER_FUNCTIONS`)**:
  catches silent divergence between the new contract-declared activation candidate and the
  pre-existing, independently-authored evidenced-surface guardrail — two sources of truth
  for the same fact must not be allowed to drift apart undetected.
- **New Test 11 (`test_committed_codex_config_still_hook_free`, byte-snapshot form)**:
  stronger than a structural hooks-key walk alone — catches any change at all to
  `.codex/config.toml`, including a change that adds no `hooks` key but alters other
  content in a way that could later enable one.
- **Existing 3 pre-existing failures must stay exactly 3, by name**: any scoped test run
  during this ticket's implementation that shows a *different* failure count or a *new*
  failing test name (beyond the two terminal-status line-number tests and the
  provider-field-coverage test named in investigation.md) signals a real regression this
  ticket introduced, not baseline noise, and must be investigated before Verify.

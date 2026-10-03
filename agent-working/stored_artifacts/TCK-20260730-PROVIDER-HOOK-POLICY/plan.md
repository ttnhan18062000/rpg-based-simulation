---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260730-PROVIDER-HOOK-POLICY
artifact_type: plan
tags: [ai, hooks, workflows, documentation, testing]
---

# Implementation Plan — TCK-20260730-PROVIDER-HOOK-POLICY

## Summary

Add one new, sibling contract file, `agent-orchestration/hook-surface-policy.yaml`,
governed by `agent-orchestration/contract.yaml` alongside the existing five governed
files. The file declares, per provider, `enabled_events` (required) and `available_events`
(optional, populated only for Codex where an in-repo evidenced capability matrix exists),
plus an `activation_candidates` list constrained to Codex `PostToolUse` and its evidenced
writer-function subset, and an `activation_prerequisites` list of the nine named future
activation requirements. `hook-events.yaml` stays completely untouched — it remains the
single source of truth for "normalized," and the new file's loader function structurally
enforces `enabled_events ⊆ hook-events.yaml.hook_types` (the "normalized" check) plus
`enabled_events ⊆ available_events` where `available_events` is declared, giving AC #1's
"contract validation independently checks available/normalized/enabled" real teeth in
`tools/agent_orchestration/loader.py`, not just in tests. `tools/agent_codex_pilot_guardrails/`
is deliberately left untouched — the writer-function drift check (New Test 9) cross-checks
`enabled_surface.EVIDENCED_WRITER_FUNCTIONS` by importing the existing constant from a test
file, not by adding a new function to that package, keeping the ticket's footprint fully
outside the guardrails package and the `test_no_live_execution_path.py` blast radius.

## Design Decisions (Resolved Open Questions)

### Open Question 1 — does the new file declare `claude.available_events`?
**Decision: Option (a) — omit `available_events` for Claude entirely; make the key
Codex-only/optional in the schema.** Rationale: no in-repo evidenced Claude capability
matrix exists (unlike `docs/ai/codex_capability_matrix.md` for Codex), and CLAUDE.md's Hard
Rule "Do not guess when uncertainty affects behavior or architecture" plus the investigation's
own anti-drift hazard ("Do not silently invent Claude's available hook count") both argue
against fabricating a number without citation — even a caveated one. Setting
`claude.available_events = enabled_events` (option b) would still read as an authoritative
claim that Claude has exactly 2 available events, which is not evidenced in this repo and
would repeat, for Claude, the exact conflation-of-available-with-supported mistake this
ticket exists to prevent for Codex. The loader's schema therefore requires every provider
entry to have `enabled_events` (list, may be empty) but treats `available_events` as
optional per-provider — present and required-populated for `codex`, absent for `claude`.

### Open Question 2 — does adding a `governs:` entry bump `contract.yaml`'s own version?
**Decision: additive, no version bump.** `README.md`'s bump rule (line 31) explicitly names
"a new role/skill entry" as a non-breaking addition that does not bump a counter. A new
`governs:` list entry is the direct structural analog for `contract.yaml` itself — `governs:`
is a list, not a fixed key set, existing entries are untouched, and no existing consumer's
expectation of any current `governs:` entry changes. `contract.yaml`'s own top-level
`version` field (if present) is therefore left unmodified by this ticket; only the new file's
own `hook_surface_policy_version: 1` counter is introduced, starting at 1 per the
established pattern for new files.

## Steps

### Step 1 — Create `agent-orchestration/hook-surface-policy.yaml` with full content
**Files:** `agent-orchestration/hook-surface-policy.yaml` (new), `tests/agent_orchestration/test_contract_structure.py`
**Change:** Create the file with complete real content:
```yaml
hook_surface_policy_version: 1
providers:
  claude:
    enabled_events: [PreToolUse, PostToolUse]
  codex:
    available_events: [PreToolUse, PermissionRequest, PostToolUse, PreCompact, PostCompact, UserPromptSubmit, SubagentStop, Stop, SessionStart, SubagentStart]
    enabled_events: []
activation_candidates:
  - provider: codex
    event: PostToolUse
    status: candidate
    writer_functions: [write_line, write_lines]
activation_prerequisites:
  - id: human_approval
    description: Contemporaneous human sign-off recorded before any Codex hook is enabled.
  - id: scratch_first_verification
    description: Payload/schema verified in a scratch environment before any committed config change.
  - id: project_trust_review
    description: Project-level trust reviewed and recorded independently of hook trust.
  - id: hook_trust_review
    description: Hook-level trust reviewed and recorded independently of project trust.
  - id: failure_timeout_fail_open
    description: Hook failure or timeout must fail open, never block the run.
  - id: redacted_output
    description: Hook output must be redacted before storage or display.
  - id: out_of_band_diagnostics
    description: Diagnostics for a live hook must be captured out-of-band from the run's own state.
  - id: reviewed_config_diff
    description: The exact config diff enabling the hook must be reviewed before commit.
  - id: one_action_rollback
    description: A single action must fully roll back the enabled hook to the pre-activation state.
```
(Verbatim `description` prose above is a drafting baseline; the implementer may tighten
wording as long as each `id` stays stable and each entry stays a requirement-not-yet-met, per
the Anti-Drift Notes below.) Add `agent-orchestration/hook-surface-policy.yaml` to
`test_agent_orchestration_dir_has_required_files`'s `required_files` list, following its
existing pattern exactly. Add New Test 1, `test_hook_surface_policy_file_exists_and_parses`.
**Do NOT touch:** `agent-orchestration/hook-events.yaml` (any field, any value) — it is not
modified by this step or any later step.
**Verify:** New Test 1 (`test_hook_surface_policy_file_exists_and_parses`).

### Step 2 — Implement loader validation in `tools/agent_orchestration/loader.py`
**Files:** `tools/agent_orchestration/loader.py`, `tests/agent_orchestration/test_contract_structure.py`
**Change:** Add `_load_hook_surface_policy_yaml()` following the exact idiom of
`_load_hook_events_yaml` (required-keys check via `_require_keys`, structural assertions,
`ContractValidationError` naming exact file/field on violation). Structural rules to enforce:
1. Top-level requires `hook_surface_policy_version` (int), `providers` (mapping), `activation_candidates` (list), `activation_prerequisites` (list).
2. Every `providers.<name>` entry requires `enabled_events` (list of str, may be empty). `available_events` is optional per entry.
3. For every provider, every id in `enabled_events` must appear in `hook-events.yaml`'s `hook_types` ids (loaded via the existing `hook_events` bundle field) — this is the "enabled ⊆ normalized" law (AC #1's "normalized... independently checks").
4. Where `available_events` is present for a provider, every id in `enabled_events` must also appear in that provider's `available_events` (enabled ⊆ available).
5. Each `activation_candidates` entry requires `provider`, `event`, `status`, `writer_functions` (list of str); `event` must appear in that provider's `available_events`.
6. Each `activation_prerequisites` entry requires `id` (unique across the list) and `description`; reject (raise `ContractValidationError`) if any prerequisite or activation-candidate entry contains a key named `approved`, `granted`, or `authorized` with a truthy value — this is the machine-checkable form of the "does not imply authorization" hazard, enforced structurally, not just by test.
Add a new field to the `ContractBundle` dataclass, e.g. `hook_surface_policy`, and call the
new load function from `load_contract()`'s fixed sequence (7th load, after
`_load_hook_events_yaml`, since rule 3 above needs the already-loaded `hook_events` value).
Extend/add New Test 2, `test_load_contract_includes_hook_surface_policy`, asserting the
bundle carries the new field and it round-trips the real file's content.
**Do NOT touch:** `_load_hook_events_yaml`, the `hook_events` field's existing shape, or any
of the other 5 existing load functions.
**Verify:** New Test 2; existing `test_load_contract_succeeds_against_the_real_contract`
stays green.

### Step 3 — Validator error-path coverage in `tests/agent_orchestration/test_validator_errors.py`
**Files:** `tests/agent_orchestration/test_validator_errors.py`
**Change:** Add table-driven cases mirroring the existing copy-and-mutate-a-tmp-contract
pattern (e.g. `test_contract_yaml_missing_version_raises_named_error`), one per Step 2 rule:
missing `hook_surface_policy_version`; missing `providers`; a provider entry missing
`enabled_events`; an `enabled_events` id not present in `hook-events.yaml`'s `hook_types`
(normalized-violation case); an `enabled_events` id not present in that provider's declared
`available_events` (available-violation case); an `activation_candidates` entry whose `event`
is not in the provider's `available_events`; an `activation_prerequisites` entry missing
`id`/`description`; an `activation_prerequisites` entry with a duplicate `id`; an
`activation_prerequisites` or `activation_candidates` entry carrying a truthy
`approved`/`granted`/`authorized` key. This is New Test 3 (as a table, not a single test).
**Do NOT touch:** the existing 3 non-hook-surface-policy cases already in this file.
**Verify:** New Test 3 (all sub-cases raise `ContractValidationError` naming the exact
file/field).

### Step 4 — Wire `tools/agent_orchestration/generator.py`
**Files:** `tools/agent_orchestration/generator.py`
**Change:** Add a 7th write step to `generate()`'s fixed sequence, mirroring the existing
6-file pattern exactly: write `agent-orchestration/hook-surface-policy.yaml` via
`_write_yaml`, sourced from `ContractBundle.hook_surface_policy`, under the same
`_assert_write_allowed` guard used by the other 6 writes.
**Do NOT touch:** the write-guard logic itself (`_assert_write_allowed`), or any of the other
6 existing write steps' ordering or content.
**Verify:** existing `tests/agent_orchestration_codex_adapter/test_generator_write_guard.py`
and `test_generator_traceability.py` stay green (run explicitly — no new test required for
this step per test_plan.md).

### Step 5 — Wire `agent-orchestration/contract.yaml` and `agent-orchestration/README.md`
**Files:** `agent-orchestration/contract.yaml`, `agent-orchestration/README.md`, `tests/agent_orchestration/test_contract_structure.py`
**Change:** In `contract.yaml`'s `governs:` list, add a 6th entry for
`hook-surface-policy.yaml` with `version_field: hook_surface_policy_version`, following the
existing entries' exact shape. Do not modify `contract.yaml`'s own top-level `version` field
(per the Design Decision above). In `README.md`: add one row to the Layout table naming the
new file, and one bullet to the versioning-scheme enumeration naming
`hook_surface_policy_version` alongside the other 5 counters. Add New Test 15,
`test_new_contract_file_wired_into_readme_and_manifest`, asserting `contract.yaml`'s
`governs:` list contains the new entry with a `version_field`, and that `README.md`'s Layout
table names the new file (string-search is acceptable per test_plan.md's discretion note).
**Do NOT touch:** any of the other 5 existing `governs:` entries, the Layout table's other 5
rows, or `contract.yaml`'s own `version` field.
**Verify:** New Test 15.

### Step 6 — Provider-representation tests (AC #2)
**Files:** `tests/agent_orchestration/test_contract_structure.py`
**Change:** Add New Test 4 (`test_policy_represents_claude_two_enabled_events`, asserts
`providers.claude.enabled_events == {"PreToolUse", "PostToolUse"}`), New Test 5
(`test_policy_represents_codex_ten_available_events`, asserts `providers.codex.available_events`
equals the 10-event set from `docs/ai/codex_capability_matrix.md` §1, matched literally), and
New Test 6 (`test_policy_represents_codex_zero_enabled_events`, asserts
`providers.codex.enabled_events == []`, cross-checked against `.codex/config.toml` parsing to
`{}` via a direct `tomllib.load` read or `codex_config_guard.assert_committed_config_hook_free`).
**Do NOT touch:** `.codex/config.toml`, `docs/ai/codex_capability_matrix.md`.
**Verify:** New Tests 4, 5, 6.

### Step 7 — Normalized-vocabulary consistency and immutability tests
**Files:** `tests/agent_orchestration/test_contract_structure.py`
**Change:** Add New Test 7 (`test_policy_normalized_vocabulary_matches_hook_events_yaml`),
proving the Step 2 loader rule (`enabled_events ⊆ hook-events.yaml.hook_types`) is actually
exercised against the real files — assert every provider's real `enabled_events` is a subset
of the real `hook-events.yaml`'s `hook_types` ids, and that the new file does not re-declare
its own independent copy of the normalized list anywhere. Add New Test 10
(`test_hook_events_yaml_unchanged_normalized_vocabulary`), asserting `hook-events.yaml`'s
`hook_types` still contains exactly `{PreToolUse, PostToolUse}` — i.e. this ticket's changes
did not smuggle any Codex-only event into the existing normalized list.
**Do NOT touch:** `agent-orchestration/hook-events.yaml` in any way — these are read-only
consistency/immutability assertions.
**Verify:** New Tests 7, 10.

### Step 8 — Activation-candidate tests (AC #3), no touch to pilot guardrails package
**Files:** `tests/agent_orchestration/test_contract_structure.py`
**Change:** Add New Test 8 (`test_only_codex_post_tool_use_is_an_activation_candidate`),
asserting `activation_candidates` contains exactly one entry: provider `codex`, event
`PostToolUse` — and explicitly that no other Codex event (in particular `PreToolUse`, which
is schema-valid-but-unevidenced per `enabled_surface.py`'s existing test) appears. Add New
Test 9 (`test_activation_candidate_writer_subset_is_write_line_and_write_lines`), asserting
the `PostToolUse` candidate's `writer_functions` equals
`tools.agent_codex_pilot_guardrails.enabled_surface.EVIDENCED_WRITER_FUNCTIONS` — import the
existing constant directly in the test rather than hardcoding a literal, so a future change
to the constant is caught as a real test failure instead of silent drift.
**Do NOT touch:** `tools/agent_codex_pilot_guardrails/enabled_surface.py` or any other file
in that package. Investigation flagged an "optional, not required" cross-check function as
a possible addition to `enabled_surface.py` — this plan explicitly declines it: the drift
check is achieved from the test side by importing the existing constant, which satisfies New
Test 9's intent without adding any code to the guardrails package, keeping this ticket's
footprint entirely outside `test_no_live_execution_path.py`'s scan surface. As a direct
consequence, test_plan.md's New Test 12
(`test_guardrail_package_still_has_no_live_execution_path`) is not applicable — no code is
added to `tools/agent_codex_pilot_guardrails/` by this ticket, so the existing
`test_no_live_execution_path.py` continues to cover that package unmodified, verified by
Step 11's full regression run rather than by a new test.
**Verify:** New Tests 8, 9.

### Step 9 — Activation-prerequisite tests (AC #5), anti-authorization guard
**Files:** `tests/agent_orchestration/test_contract_structure.py` (or `tests/agent_orchestration/test_validator_errors.py` for the negative case, implementer's discretion — keep with whichever file already hosts the analogous positive/negative pair from Step 3)
**Change:** Add New Test 13 (`test_activation_prerequisites_cover_all_nine_named_items`),
asserting `activation_prerequisites` contains entries with exactly the nine stable ids from
Step 1's content (`human_approval`, `scratch_first_verification`, `project_trust_review`,
`hook_trust_review`, `failure_timeout_fail_open`, `redacted_output`,
`out_of_band_diagnostics`, `reviewed_config_diff`, `one_action_rollback`), matched by `id`,
not by prose. Add New Test 14
(`test_activation_prerequisites_do_not_imply_authorization`), asserting no
`activation_prerequisites` or `activation_candidates` entry in the real file contains an
`approved`/`granted`/`authorized` truthy field, and (if not already covered by Step 3's
negative case) that injecting such a key into a tmp copy trips the Step 2 loader's hard
rejection.
**Do NOT touch:** wording of any `activation_prerequisites` entry that would make it read as
already-satisfied rather than still-required.
**Verify:** New Tests 13, 14.

### Step 10 — Byte-identity regression proving `.codex/config.toml` untouched (AC #4)
**Files:** `tests/agent_replay_codex/test_codex_config_guard.py`
**Change:** Add New Test 11 (`test_committed_codex_config_still_hook_free`), reusing
`codex_config_guard.snapshot_config_bytes`/`assert_config_bytes_unchanged` (or an equivalent
byte-comparison against a recorded pre-ticket snapshot) to prove `.codex/config.toml` is
byte-for-byte unchanged by this ticket's full changeset — stronger than the existing
structural hooks-key walk alone, since it also catches non-`hooks`-key edits.
**Do NOT touch:** `.codex/config.toml` itself, or `codex_config_guard.py`'s existing
`assert_committed_config_hook_free`/`snapshot_config_bytes`/`assert_config_bytes_unchanged`
functions — read-only reuse only.
**Verify:** New Test 11.

### Step 11 — Full scoped regression run
**Files:** none (verification only)
**Change:** Run the exact scoped pytest command from `test_plan.md`:
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
Confirm: (a) exactly the same 3 pre-existing failures remain, by name —
`test_terminal_status_conformance_finalize_incomplete_appears_once_on_both_sides`,
`test_extract_all_terminal_statuses_dedupes_by_value_not_call_site_count`,
`test_provider_field_coverage_against_real_corpus_is_currently_zero` — with no new failing
test name and no changed failure count; (b) all New Tests 1–11, 13, 14, 15 pass (New Test 12
is N/A per Step 8); (c) `test_no_live_execution_path.py` passes with zero edits to its own
assertions.
**Do NOT touch:** the 3 pre-existing failing tests, in an attempt to "fix" them as a
drive-by — explicitly out of scope.
**Verify:** the full command above; manual diff of the failure list against
investigation.md's documented baseline.

## Scope Guards

- Do not add any entry to `agent-orchestration/hook-events.yaml` — its `hook_types` list
  stays exactly `{PreToolUse, PostToolUse}` throughout every step. (Steps 1, 7, 10 have
  explicit "Do NOT touch" lines reinforcing this.)
- Do not modify `.codex/config.toml` — it stays the same 9-line comment-only file,
  byte-for-byte, proven by Step 10's New Test 11.
- Do not add a subprocess execution path, a live Codex invocation, or any function whose
  name matches `run_pilot`/`execute_pilot`/`invoke_codex` anywhere this ticket touches.
- Do not add code to `tools/agent_codex_pilot_guardrails/` — the "optional" cross-check
  function investigation.md floated is explicitly declined (Step 8); the package is
  untouched by this ticket in its entirety.
- Do not weaken, edit, or add an exemption to
  `tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py`.
- Do not expand the normalized vocabulary in any file beyond `{PreToolUse, PostToolUse}` —
  Codex's other 8 documented events land only in `providers.codex.available_events`, never
  in `hook-events.yaml` and never in any provider's `enabled_events`.
- Do not fabricate a `claude.available_events` count — per Design Decision 1, the key is
  omitted entirely for Claude.
- Do not word any `activation_prerequisites` or `activation_candidates` entry as
  already-satisfied — every entry is a requirement still to be met by a later ticket.
- Do not modify `contract.yaml`'s own top-level `version` field — per Design Decision 2, the
  `governs:` list addition is additive/non-breaking.
- Do not "fix" the 3 pre-existing unrelated test failures as a side effect of this ticket.
- Do not touch `tools/agent_replay_codex/codex_config_guard.py`'s existing functions beyond
  reusing them read-only in Step 10.

## Dependency Map

- Step 1 has no dependencies; it is the root artifact every later step reads or extends.
- Step 2 depends on Step 1 (needs the real file to load and to validate against) and reads
  the already-existing `hook_events` bundle field (unmodified, pre-existing).
- Step 3 depends on Step 2 (the loader function and its rules must exist before error-path
  cases can exercise them).
- Step 4 depends on Step 2 (`generate()`'s new write step sources `ContractBundle.hook_surface_policy`,
  which Step 2 introduces).
- Step 5 depends on Step 1 (the file must exist to be named in `governs:`/README) but is
  otherwise independent of Steps 2–4; it can run in parallel with them.
- Steps 6, 7, 8, 9 each depend on Steps 1 and 2 (they assert facts about the real file's
  content and the loader's enforced rules) but are independent of each other and of Step 4/5
  — they may be done in any order relative to one another.
- Step 10 depends only on Step 1 having landed (so a "post-ticket" snapshot exists to prove
  unchanged) — independent of Steps 2–9.
- Step 11 depends on all prior steps being complete.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — Contract validation independently checks available, normalized, and enabled hook status | Step 2 (loader structural rules) | New Test 2, New Test 3 (all sub-cases), New Test 7 |
| AC #2 — Policy accurately represents Claude's 2 enabled, Codex's 10 available, Codex's 0 enabled, and normalized vocabulary without false broader-support claims | Steps 1, 6, 7 | New Tests 4, 5, 6, 7, 10 |
| AC #3 — Only Codex `PostToolUse` is an activation candidate, writer subset bound to `write_line`/`write_lines` | Steps 1, 8 | New Tests 8, 9 |
| AC #4 — Tests prove committed Codex config stays hook-free and guardrail code retains no live invocation path | Steps 1 (no touch), 6, 10 | New Test 6, New Test 11, existing `test_no_production_hook_enabled.py` and `test_no_live_execution_path.py` (Step 11 confirms both green, N/A note on New Test 12) |
| AC #5 — Future activation requirements explicit enough for a later ticket to consume without reinterpreting consent/rollback/redaction/failure behavior | Steps 1, 9 | New Tests 13, 14 |

## Anti-Drift Notes

- The single highest-value guard in this plan is New Test 10
  (`test_hook_events_yaml_unchanged_normalized_vocabulary`, Step 7) — it is the test most
  likely to catch a well-intentioned "just add the Codex events to `hook_types` too"
  shortcut during implementation. Do not let any step touch `hook-events.yaml` to make this
  test pass; if it fails, the fix is always in the new file, never in `hook-events.yaml`.
- `tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py` must pass with zero
  edits to its own assertions. Since Step 8 explicitly avoids adding any code to
  `tools/agent_codex_pilot_guardrails/`, this should require no interaction with that test at
  all — if implementation finds itself needing to touch that package to satisfy some other
  step, stop and re-check against this plan's Step 8 decision before proceeding.
- `enabled_surface.py`'s "evidenced" concept (⊆ normalized, proven safe by direct
  experiment) is a fourth, narrower concept than this ticket's available/normalized/enabled
  triad — New Test 9 cross-checks against it by import, but the new file's schema must never
  use the word "evidenced" as if it were a formal field of its own; `writer_functions` on the
  `activation_candidates` entry is the correct field name, matching the existing constant's
  meaning without renaming or duplicating it.
- Every `activation_prerequisites` entry is a requirement, never a completed checkbox — the
  loader's Step 2 hard-reject rule on `approved`/`granted`/`authorized` keys exists precisely
  so a later, careless edit to this file cannot silently flip it into looking like
  authorization already happened.
- The 3 pre-existing test failures documented in investigation.md
  (`test_terminal_status_conformance...`, `test_extract_all_terminal_statuses_dedupes...`,
  `test_provider_field_coverage_against_real_corpus_is_currently_zero`) are baseline noise
  unrelated to any file this plan touches — Step 11 confirms they remain exactly 3, by name,
  and treats any deviation (new failure, different count) as a real regression requiring
  investigation before Verify, not as more baseline noise to wave through.

## Deviations

None. All 11 steps were implemented exactly as specified, including both Design Decisions
(Claude's `available_events` omitted entirely; `contract.yaml`'s own `version` left
unmodified). `hook-events.yaml` and `.codex/config.toml` were never touched (confirmed via
`git diff` showing zero changes to either at implementation end). Step 11's regression run
reproduced the exact same 3 pre-existing failures by name, with no new failures.

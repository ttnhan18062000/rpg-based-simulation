---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS
phase: done
date: 2026-07-21
tags: []
---

# TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS

## Title
Isolated live Codex pilot with rollback guardrails

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Once replay/shadow evidence is clean, permit exactly one recoverable, low-risk live Codex ticket run: a human-owned ticket with a rollback plan and no concurrent same-work execution by both providers, only the hooks/writer already proven safe in earlier phases enabled, pre/post snapshots of the ticket and monitoring corpus required alongside normal gates, and disabling Codex afterward limited to a configuration rollback — never a data repair. This matters because this is the only concern touching genuinely irreversible-risk territory, and it is doubly blocked: on all prior phases landing, and separately on the documented .agents/skills quarantine gate.

## Scope
- Design and build a ticket-selection step that programmatically rejects candidates lacking a recorded human owner + rollback plan, or where the same ticket is concurrently claimed by both providers
- Build a rollback mechanism achievable via a single config/flag flip (Codex-adapter disable), verified by a test that performs the rollback and asserts zero bytes differ across agent-monitoring/*.jsonl and the pilot ticket file
- Build pre/post baseline-manifest capture and diff tooling for the pilot (consuming the baseline-monitoring-manifest ticket's tooling rather than rebuilding it), failing closed if any pre-existing line's hash changes
- Build an explicit, programmatically-checked human sign-off gate immediately before live pilot execution itself (not just before ticket designation) that the pilot workflow refuses to proceed without
- Restrict the enabled hook/writer set for the pilot to only what the Codex-guidance and monitoring-writer-unification tickets' evidence has proven safe, with a test enumerating the enabled set as a subset of that evidence

## Out of Scope
- Does not begin actual live pilot execution until the orchestration-contract-core, Claude-conformance-adapter, Codex-guidance-fixture-capture, monitoring-writer-unification, and Codex-replay-parity tickets have all landed and passed their own exit criteria, AND the separate legacy .agents/skills/ quarantine gate (owned by the Codex-guidance-fixture-capture ticket) is independently satisfied — this ticket's scope is limited to designing and building the guardrail/rollback/sign-off mechanisms; live execution itself remains blocked pending those preconditions
- Rollback logic never deletes output or modifies historic JSONL records — only additive quarantine or reader-side exclusion; no data-repair-via-deletion mechanism is built
- Does not re-implement baseline-manifest tooling already delivered by the baseline-monitoring-manifest ticket — this ticket consumes it

## Acceptance Criteria
- [x] Ticket-selection step programmatically rejects candidates lacking a recorded human owner and rollback plan, verified against actual ticket/run state (not just doc convention)
- [x] Ticket-selection step programmatically rejects a candidate that is concurrently claimed by both providers for the same work
- [x] Only Phase-2/Phase-3-evidenced hook events are registered as enabled for the pilot; a test enumerates the enabled set as a subset of that evidence
- [x] Pre/post baseline manifests are captured and diffed for the pilot; the pilot workflow fails closed if any pre-existing line's hash changes
- [x] Codex-adapter disable is achievable via a single config/flag flip; a test performs the rollback and asserts zero bytes differ across agent-monitoring/*.jsonl and the pilot ticket file
- [x] An explicit, programmatically-checked human sign-off gate exists immediately before live pilot execution (distinct from and later than ticket designation); the pilot workflow refuses to proceed without it
- [x] This ticket's own scope explicitly states that live pilot execution is blocked pending the prior 5 tickets AND the .agents/skills quarantine gate, and that only guardrail/rollback/sign-off design-and-build work is in scope now (confirmed unchanged in this ticket's Out of Scope section; mechanically re-asserted by `tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py`, which proves no code path in the new package can import `tools.agent_replay_codex.invoker`, dynamically load it, spawn any subprocess, or expose an execution-shaped function — and independently re-confirms the real committed `.codex/config.toml` stays hook-free)

## Related Tickets
- TCK-20260721-PROVIDER-AGNOSTIC-EPIC
- TCK-20260721-ORCHESTRATION-CONTRACT-ADR
- TCK-20260721-MONITORING-WRITER-DECISION
- TCK-20260721-CODEX-CAPABILITY-MATRIX
- TCK-20260721-CODEX-REPLAY-PROOF
- TCK-20260721-AGENTS-DIR-DISPOSITION
- TCK-20260721-AGENTS-DISPOSITION-FIX
- TCK-20260721-AGENTS-DISPOSITION-DISCOVERABILITY-FIX

## Related Docs
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md
- docs/ai/agents_dir_disposition.md
- docs/ai/monitoring_writer_decision.md
- docs/ai/codex_capability_matrix.md
- docs/architecture/agent_orchestration_contract.md
- docs/ai/replay_fixture_spec.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md
- docs/ai/agents_dir_disposition.md
- docs/ai/monitoring_writer_decision.md
- docs/ai/codex_capability_matrix.md
- docs/architecture/agent_orchestration_contract.md
- docs/ai/replay_fixture_spec.md
- tools/agent-monitoring/post_tool_hook.py
- tests/tools/test_monitoring_writer_lockfile_candidate.py
- tests/agent_replay/test_runner_no_forbidden_calls.py
- tests/agent_replay/test_no_mutation_snapshot.py

## Assumptions / Open Questions
- No rollback/feature-flag mechanism exists yet for agent-orchestration/Codex-adapter enablement; the only existing feature_flag precedent (src/domains/optimization/feature_flags.py) is an unrelated simulation-engine per-tick mechanism and cannot be reused as-is
- Doubly blocked: hard sequencing dependency on the 5 prior tickets all landing, plus a separate independent precondition (legacy .agents/skills/ quarantine, owned by the Codex-guidance-fixture-capture ticket) — both must be satisfied before live execution, not just this ticket's own build work
- Assumes the baseline-monitoring-manifest ticket delivers reusable baseline-manifest tooling this ticket should consume rather than rebuild

## Implementation Notes

Implemented `tools/agent_codex_pilot_guardrails/` exactly per `staging_artifacts/
TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS/plan.md`'s 7 ordered steps (architecture-reviewed,
approved). Every step's own "Do NOT touch" list was respected — no edits to `tools/agent-monitoring/
*.py`, `tools/agent_replay_codex/*.py`, `tools/agent_orchestration*/*.py`,
`agent-orchestration/*.yaml`/`*.md`, `.agents/`, `.claude/workflows/*.js`, `.claude/agents/*.md`,
`.claude/skills/*`, or `CLAUDE.md` — all consumed by import/read only.

- **Step 1** (`pilot_manifest.py`, `errors.py`, `__init__.py`): `PilotRequest(ticket_id, human_owner,
  rollback_plan_summary)` frozen dataclass + `load_pilot_request(path)`. Strict fail-clear: missing
  file → `PilotManifestValidationError`; missing/empty (post-`.strip()`) `human_owner` →
  `MissingHumanOwnerError`; missing/empty `rollback_plan_summary` → `MissingRollbackPlanError`. Reads
  only structured YAML keys — a fixture whose free-text `notes` field mentions "owner"/"rollback" in
  prose without the structured fields still raises (test coverage proves this). New
  `pilot_requests/` top-level sidecar directory with `README.md` documenting the schema; ships with
  no real candidate `.yaml` file, per plan.
- **Step 2** (`ticket_selection.py`): `select_pilot_candidate(ticket_id, pilot_requests_dir)` raises
  a named `PilotManifestValidationError` (never a bare `FileNotFoundError`) on a missing request
  file, then delegates field validation to Step 1's loader. `assert_no_concurrent_claim(ticket_id,
  run_records)` raises `ConcurrentProviderClaimError` when 2+ in-progress (`end_ts` falsy) synthetic
  records for the same `ticket_id` carry different `provider` values. `provider_field_coverage
  (agent_monitoring_dir)` streams `runs.jsonl` line-lazily (mirrors `manifest.py::_scan_file`'s
  technique) and counts `provider`-bearing records — a companion test asserts this returns `0`
  against the real `agent-monitoring/runs.jsonl` today, keeping the Risk #3 gap
  (`.claude/workflows/implement-ticket.js` never populates `provider`) visible rather than silently
  assumed away. Not fixed here — explicitly out of scope.
- **Step 3** (`enabled_surface.py`): `EVIDENCED_HOOK_EVENTS = frozenset({"PostToolUse"})`,
  `EVIDENCED_WRITER_FUNCTIONS = frozenset({"write_line", "write_lines"})`, sourced from the
  investigation's direct-read trace. `assert_evidenced_events_are_schema_valid()` cross-checks
  against `agent-orchestration/hook-events.yaml`'s broader schema-declared vocabulary (which also
  includes `PreToolUse`). `assert_enabled_surface_subset(...)` raises
  `EnabledSurfaceExceedsEvidenceError` on any input exceeding either evidenced set — proven with a
  `PreToolUse`-included failing case, not just a hardcoded equality check.
- **Step 4** (`baseline_manifest_gate.py`): loads `tools/agent-monitoring/manifest.py` via
  `importlib.util.spec_from_file_location` (mirrors `containment.py`'s precedent, since
  `agent-monitoring` has a hyphen and can't be dotted-imported) and imports `capture_lines`/
  `assert_prefix_preserved` unmodified — zero edits, zero reimplementation.
  `capture_pilot_baseline`/`assert_pilot_baseline_preserved` are thin wrappers; the latter catches
  `AssertionError` and re-raises as `PilotManifestDriftError`. Negative-control test confirms a
  mutated pre-existing line is caught by the wrapper (not just the underlying function).
- **Step 5** (`config_toggle.py`): `render_enabled_config` appends the empirically-discovered
  `[[hooks.PostToolUse]]`/`[[hooks.PostToolUse.hooks]]` block recorded in
  `tickets/done/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE.md`'s Implementation Notes, using a
  deliberate no-op `command = "true"` placeholder (this mechanism is never wired to a real Codex
  invocation). `_assert_scratch_target` refuses to operate whenever the target path resolves to
  `repo_root/.codex/config.toml`; `enable`/`disable` both call it first, before any read/write.
  `snapshot_rollback_scope`/`assert_rollback_scope_unchanged` do strict whole-file SHA-256 across
  `runs.jsonl`/`events.jsonl`/`tools.jsonl` + the pilot ticket file (narrower than
  `containment.py`'s all-of-`tickets/` scope, per plan). Reused `codex_config_guard.py`'s
  `snapshot_config_bytes`/`assert_config_bytes_unchanged` directly (import, not reimplement). Full
  round-trip test (enable → verify `hooks` key present → disable → zero-byte-diff across rollback
  scope + config) passes against a scratch area; a suite-level test independently confirms the real
  committed `.codex/config.toml` is still hook-free and byte-identical to its state at module
  collection time.
- **Step 6** (`signoff_gate.py`): `require_pilot_signoff(env)` mirrors `consent_gate.py`'s strict,
  non-coercive `env.get(VAR) != "1"` pattern exactly, with its own env var
  (`CODEX_LIVE_PILOT_HUMAN_SIGNOFF`) — reused by re-implementation (new, conceptually distinct
  gate), not by import, per plan. Takes no argument derived from `select_pilot_candidate`'s result;
  a dedicated test proves a successful selection does not itself satisfy sign-off.
- **Step 7** (`tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py`, test-only): AST
  scan asserting (a) no static import of `tools.agent_replay_codex.invoker`; (b) no
  `importlib.util.spec_from_file_location`/`importlib.import_module` call with a string argument
  containing `"invoker"` or `"agent_replay_codex"`; (c) a blanket, unconditional ban on
  `subprocess.run`/`Popen`/`call`/`check_call`/`check_output`/`os.system` calls anywhere in the
  package — not scoped to a `"codex"` substring, per the architecture-review fix — plus a stronger
  companion test banning any `import subprocess` statement at all (mirrors `consent_gate.py`'s own
  "zero dependency on subprocess" precedent); (d) no top-level function named
  `run_pilot`/`execute_pilot`/`invoke_codex` or containing those substrings; (e) an independent
  re-check that the real committed `.codex/config.toml` remains hook-free via
  `codex_config_guard.assert_committed_config_hook_free(repo_root)`, beyond Step 5's own
  suite-level check.

**Deviation note (test-writing only, not a plan deviation):** the first draft of
`test_config_rollback.py`'s round-trip test built a scratch "fake repo" whose `.codex/config.toml`
path was structurally identical to the real repo's own relative layout, then passed that fake repo
as `repo_root` — which made `_assert_scratch_target` correctly (and expectedly, on reflection)
refuse the target, since `repo_root/.codex/config.toml` trivially resolved to the scratch file
itself. Fixed by redesigning the test fixture: `repo_root` is always the real project root (as
every real caller would pass), and the scratch config lives at an unrelated path
(`tmp_path/scratch/config.toml`) never nested under a `.codex/` directory. This confirms
`_assert_scratch_target`'s design is correct as specified in plan.md — the fix was to the test's own
fixture shape, not to `config_toggle.py`'s implementation, which was written exactly to plan and
never changed.

**Flagged, not fixed (out of this ticket's own scope):** while reading the three already-DONE
sibling tickets in this batch for pattern precedent (`tickets/done/
TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER.md`, `tickets/done/TCK-20260721-CODEX-GUIDANCE-FIXTURE-
CAPTURE.md`, `tickets/done/TCK-20260721-MONITORING-WRITER-UNIFICATION.md`), all three were found to
still carry a stale `## Status` body field reading `OPEN` despite being complete, closed, and
migrated to `tickets/done/`. This is a pre-existing hygiene gap in those tickets' own files, not
touched here — fixing it would mean editing three closed sibling tickets' files, which is outside
this ticket's own scope (this ticket only reads them for precedent). Noted here for visibility.

## Test Summary

`.venv/bin/python3 -m pytest tests/agent_codex_pilot_guardrails/ -v --resource-budget off` — **40
passed** (this ticket's own new suite, Steps 1-7 combined).

Regression surface (per test_plan.md's Scoped Pytest Commands), all run with
`--resource-budget off`:
- `tests/agent_replay/ tests/agent_replay_codex/ tests/agent_orchestration/
  tests/agent_orchestration_claude_adapter/ tests/agent_orchestration_codex_adapter/` — **129
  passed, 5 skipped, 1 failed**. The 1 failure is
  `tests/agent_orchestration/test_contract_structure.py::
  test_contract_yaml_has_versioning_field_and_documented_scheme` (`FileNotFoundError` on a stale
  `staging_artifacts/` path) — this is the known, pre-existing, unrelated failure tracked by
  `tickets/todos/TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH.md`, carried forward from every
  predecessor ticket in this batch per plan.md's Anti-Drift Notes. Not introduced or touched by
  this ticket.
- `tests/tools/test_monitoring_writer.py tests/tools/test_monitoring_writer_lockfile_candidate.py
  tests/tools/test_post_tool_hook.py tests/tools/test_record_run.py tests/tools/test_record_events.py
  tests/tools/test_agent_ops_dashboard_ingest.py` — **91 passed**.
- `tests/tools/test_agent_monitoring_manifest.py` — **6 passed** (confirms Step 4's dynamically-
  loaded `manifest.py` dependency is unaffected).

Confirmed via `git status`/`git diff` that `.codex/config.toml` has zero diff against its
pre-Implement committed state throughout.

`pytest tests/` was never run, per plan.md's Scope Guards.

## Files Changed

New files only — no existing file was edited:
- `tools/agent_codex_pilot_guardrails/__init__.py`
- `tools/agent_codex_pilot_guardrails/errors.py`
- `tools/agent_codex_pilot_guardrails/pilot_manifest.py`
- `tools/agent_codex_pilot_guardrails/ticket_selection.py`
- `tools/agent_codex_pilot_guardrails/enabled_surface.py`
- `tools/agent_codex_pilot_guardrails/baseline_manifest_gate.py`
- `tools/agent_codex_pilot_guardrails/config_toggle.py`
- `tools/agent_codex_pilot_guardrails/signoff_gate.py`
- `pilot_requests/README.md`
- `tests/agent_codex_pilot_guardrails/__init__.py`
- `tests/agent_codex_pilot_guardrails/test_pilot_manifest.py`
- `tests/agent_codex_pilot_guardrails/test_ticket_selection.py`
- `tests/agent_codex_pilot_guardrails/test_concurrent_claim.py`
- `tests/agent_codex_pilot_guardrails/test_enabled_surface.py`
- `tests/agent_codex_pilot_guardrails/test_baseline_manifest_gate.py`
- `tests/agent_codex_pilot_guardrails/test_config_rollback.py`
- `tests/agent_codex_pilot_guardrails/test_signoff_gate.py`
- `tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py`

## Completion Summary

Built the guardrail/rollback/sign-off *mechanisms* for a future live Codex pilot, as a new,
self-contained `tools/agent_codex_pilot_guardrails/` package, following this batch's established
one-ticket-one-package convention: a typed human-owner/rollback-plan pilot-request manifest +
loader with a new `pilot_requests/` sidecar directory; a ticket-selection step rejecting
missing-owner/missing-rollback-plan and concurrent-provider-claim candidates (plus a
`provider_field_coverage` helper documenting, not fixing, the real gap that no real
`implement-ticket.js` call site populates `provider` today); an evidenced-subset guard restricting
the pilot's enabled hook-event/writer-function surface to exactly what Phase 2/3 proved safe
(`PostToolUse`; `write_line`/`write_lines`); a pre/post baseline-manifest fail-closed gate reusing
`tools/agent-monitoring/manifest.py`'s `capture_lines`/`assert_prefix_preserved` unmodified; a
scratch-only Codex-adapter config enable/disable toggle with a full round-trip zero-byte-diff
rollback proof that never targets the real committed `.codex/config.toml`; and a human sign-off
gate structurally independent of, and later than, ticket selection. All 7 acceptance criteria are
satisfied, including AC #7's self-asserted scope boundary, mechanically proven (not just stated)
by `tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py` — the single most important
test in this ticket's suite, per plan.md's own Anti-Drift Notes, since this is "the only concern
touching genuinely irreversible-risk territory" in the whole 7-ticket batch. This ticket builds
readiness tooling only: no code path anywhere in the new package can invoke a real `codex exec`,
enable a hook in the real `.codex/config.toml`, or write Codex output to any real ticket file. Live
pilot execution itself remains blocked, exactly as this ticket's own Out of Scope text states — this
ticket does not, and was never meant to, lift that block. This closes the 7-ticket
provider-agnostic-implementation batch (7/7).

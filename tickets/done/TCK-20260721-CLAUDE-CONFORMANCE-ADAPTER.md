---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER
phase: done
date: 2026-07-21
tags: []
---

# TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER

## Title
Claude contract conformance adapter and tests, with no behavior change

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Generate a read-only Claude adapter representation from the canonical contract and diff it against the existing live .claude/workflows/implement-ticket.js behavior; any mismatch must be logged as an intentional divergence and human-approved, while the live Claude pipeline stays authoritative and unchanged until shadow parity is proven. This matters because the Provider-Adapter Boundary bars adapters from redefining phases/statuses/gates/artifacts, and Phase 1's exit criteria requires every divergence to be intentional and reviewed with no live workflow behavior change.

## Scope
- Build a read-only generator that renders a Claude adapter representation from the canonical contract (from the orchestration-contract-core ticket)
- Build a conformance test extracting the LIVE phase order from .claude/workflows/implement-ticket.js's meta.phases block (reusing workflow_meta_conformance.py's extraction approach) and asserting it is byte-identical to the rendered representation
- Build a conformance test extracting the LIVE terminal-status vocabulary (every writeMonitoring('STATUS') literal, ~13 call sites + 2 verdict-derived) and asserting full representation against the contract
- Define an operational meaning of "human-approved" divergence (e.g. required reviewer/date field format) enforced by the conformance test
- Create agent-orchestration/intentional-divergences.md (new file, distinct from docs/guidelines/intentional_divergences.md) to log any mismatch with an explicit human-approval marker
- Add an AST-based test asserting zero write-mode file opens / subprocess calls against implement-ticket.js by the generator/conformance tooling

## Out of Scope
- Does not modify .claude/workflows/implement-ticket.js or change any live Claude pipeline behavior
- Does not write to docs/guidelines/intentional_divergences.md (the existing mechanics-bible log) — divergences from this ticket go only in the new agent-orchestration/intentional-divergences.md
- Does not implement the Codex-side adapter (owned by the Codex guidance/fixture-capture and Codex replay tickets)

## Acceptance Criteria
- [x] Read-only generator renders a Claude adapter representation from the contract; running it produces zero git diff under .claude/ before/after
- [x] Conformance test extracts the LIVE phase order from implement-ticket.js's meta.phases block and asserts byte-identical match to the rendered representation
- [x] Conformance test extracts the LIVE terminal-status vocabulary (all writeMonitoring('STATUS') call sites, ~13 literal + 2 verdict-derived) and asserts full match to the contract's status representation
- [x] Any mismatch between live behavior and the rendered representation fails the test UNLESS a matching entry exists in agent-orchestration/intentional-divergences.md (the new file, explicitly distinguished from docs/guidelines/intentional_divergences.md) carrying an explicit human-approval marker (e.g. reviewer + date field) parsed and enforced by the test
- [x] AST-based test asserts zero write-mode file opens and zero subprocess calls against implement-ticket.js by any tool built in this ticket
- [x] Every divergence found during this ticket's own build is intentional and reviewed before the ticket closes

## Related Tickets
- TCK-20260721-ORCHESTRATION-CONTRACT-ADR
- TCK-20260721-CODEX-REPLAY-PROOF
- TCK-20260721-PROVIDER-AGNOSTIC-EPIC
- TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK
- TCK-20260720-GATE-CHECK-WIRING-DECISIONS

## Related Docs
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md
- docs/architecture/agent_orchestration_contract.md
- docs/ai/replay_fixture_spec.md
- docs/guidelines/intentional_divergences.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/workflows/implement-ticket.js
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md
- docs/architecture/agent_orchestration_contract.md
- docs/ai/replay_fixture_spec.md
- docs/guidelines/intentional_divergences.md
- tools/agent_replay/runner.py
- tools/agent_replay/fixture_envelope.py
- tools/gate_checks/workflow_meta_conformance.py
- tests/agent_replay/test_runner_no_forbidden_calls.py
- tests/agent_replay/test_no_mutation_snapshot.py
- tests/tools/test_workflow_meta_conformance.py

## Assumptions / Open Questions
- Hard dependency on the orchestration-contract-core ticket delivering agent-orchestration/ first — this ticket cannot start meaningfully until that lands
- "Human-approved" enforcement mechanism (reviewer/date field format, where it's recorded) is not yet defined anywhere in the repo — this ticket's Plan phase must define it, not assume an existing convention
- Terminal-status vocabulary extraction reliability (~13 scattered string literals) is flagged as the largest implementation risk; exact extraction technique to be resolved during Investigate/Plan
- `layer: ai` used per docs/guidelines/layer_registry.jsonl ("Claude agent/orchestration tooling") since this ticket builds Claude-adapter/conformance tooling, not gameplay cognition

## Implementation Notes

Implemented all 9 steps of `staging_artifacts/TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER/plan.md` in
dependency order (1 → 2+3 → 4+5 → 6 → 7/8/9).

- **Step 1**: `agent-orchestration/terminal-statuses.yaml` — 15 terminal-status entries
  (`literal`/`verdict_derived`/`bypass` kinds), authored directly from a fresh line-by-line re-grep
  of `.claude/workflows/implement-ticket.js` (read-only) confirming the investigation's numbers
  exactly (13 literal call sites / 12 distinct literal values, 2 verdict-derived, 1 bypass = 15
  distinct total).
- **Step 2**: `tools/agent_orchestration_claude_adapter/terminal_status_extractor.py` —
  `extract_literal_statuses`, `extract_verdict_derived_statuses` (fixed constant) +
  `count_verdict_derived_call_sites` (live confirmation), `extract_bypass_statuses`,
  `extract_all_terminal_statuses` (dedupe-by-value aggregator). One bug found and fixed during
  implementation: the bypass regex needed narrowing from `[^"]+` to `[^"$]+` to avoid a false
  match on `writeMonitoring()`'s own prompt text (`"final_status":"${finalStatus}"` at line ~319,
  which also contains the string `record_run.py`) — see plan.md Deviations #1.
- **Step 3**: `tools/agent_orchestration_claude_adapter/terminal_status_loader.py`
  (`validate_terminal_statuses`/`TerminalStatusValidationError`/`load_terminal_statuses`, Review
  Fix A) and `generator.py` (`build_claude_adapter_representation`/`render_claude_adapter`, its own
  independent write-guard `ClaudeAdapterWriteGuardError`, never importing the predecessor
  package's private `_assert_write_allowed`). Ran `render_claude_adapter()` once for real against
  the actual repo root and committed the output at
  `agent-orchestration/rendered/claude-adapter.yaml`. Added a `"phases"` field to the rendered
  output beyond the plan's literal 4-key example dict, to satisfy the plan's own Anti-Drift
  requirement that `tiers`/`condition`/`if_false` pass through unmodified — see plan.md
  Deviations #2.
- **Step 4**: `tests/agent_orchestration_claude_adapter/test_phase_order_conformance.py` — reuses
  `workflow_meta_conformance.extract_meta_phases` directly, runs `render_claude_adapter()` against
  `tmp_path`. Zero divergence found (11/11 phases match).
- **Step 5**: `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py` — set
  comparison of `(value, kind)` pairs, both directions. Zero divergence found (15/15 match).
- **Step 6**: `tools/agent_orchestration_claude_adapter/divergence_log.py`
  (`Divergence`/`load_divergences`/`is_approved`) and `agent-orchestration/intentional-divergences.md`
  (format documented, zero entries). Wired `is_approved()` into Steps 4 and 5's tests as the
  approval-check-before-hard-fail path. One implementation detail not spelled out in the plan's
  dataclass field list: the parser must skip content inside fenced (\`\`\`) code blocks in
  `intentional-divergences.md`, since the file's own header documents the entry format using a
  literal `## <axis>:<value-or-id>` example inside a fence — without masking, the parser mistook
  that example for a real entry. Fixed via a length-preserving fence-mask before the heading regex
  runs (`_mask_fenced_code_blocks`).
- **Step 7**: `tests/agent_orchestration_claude_adapter/test_no_forbidden_calls_against_implement_ticket_js.py`
  — AST scan of `tools/agent_orchestration_claude_adapter/*.py` for write-mode `open()` and any
  `subprocess`/`os.system` call referencing the live workflow file, plus a whole-file
  string-constant scan. The whole-file scan required removing the literal `implement-ticket.js`
  string from this ticket's own tool-package docstrings (they now say "the live Claude workflow
  source file" instead) — see plan.md Deviations #4.
- **Step 8**: `tests/agent_orchestration_claude_adapter/test_claude_containment.py` — real-tree
  (not tmp_path) zero-git-diff-under-`.claude/` proof with clean/dirty fallback, plus a content-hash
  guard proving `docs/guidelines/intentional_divergences.md` is untouched by this ticket's tooling.
- **Step 9**: `tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py` — scans only
  `tools/agent_orchestration_claude_adapter/` + the three new `agent-orchestration/` files (not its
  own `tests/` directory, mirroring the predecessor's exact `_SCOPE_CREEP_MARKERS` scan scope) —
  see plan.md Deviations #3 for why the tests/ directory is excluded.

Self-confirmed both containment properties directly: `git status --porcelain -- .claude/` is empty
both before and after every test run in this session, and
`git diff --stat -- docs/guidelines/intentional_divergences.md` is empty (file untouched).

## Test Summary

`pytest tests/agent_orchestration_claude_adapter/ -v` — **43 passed, 0 failed**.

Regression surface (`pytest tests/agent_orchestration/ tests/agent_replay/
tests/tools/test_workflow_meta_conformance.py tests/agent_orchestration_claude_adapter/ -q`) — 101
passed, 1 xfailed (pre-existing, unrelated — `test_workflow_meta_conformance.py`'s own documented
known plan conflict from TCK-20260710), 1 failed: `test_contract_structure.py::test_contract_yaml_has_versioning_field_and_documented_scheme`,
a **pre-existing failure not caused by this ticket** — it reads
`staging_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/plan.md`, but that ticket's staging
artifacts were already migrated to `stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/`
when it closed (confirmed: this ticket never touched that test file or either artifacts
directory; `git log` shows the test file last changed by the predecessor ticket's own closing
commit). Flagged here as a known gap for a separate ticket to fix — out of this ticket's scope
(different owning ticket, different file).

## Files Changed

New files only — no existing file modified:
- `agent-orchestration/terminal-statuses.yaml`
- `agent-orchestration/rendered/claude-adapter.yaml`
- `agent-orchestration/intentional-divergences.md`
- `tools/agent_orchestration_claude_adapter/__init__.py`
- `tools/agent_orchestration_claude_adapter/terminal_status_extractor.py`
- `tools/agent_orchestration_claude_adapter/terminal_status_loader.py`
- `tools/agent_orchestration_claude_adapter/generator.py`
- `tools/agent_orchestration_claude_adapter/divergence_log.py`
- `tests/agent_orchestration_claude_adapter/__init__.py`
- `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py`
- `tests/agent_orchestration_claude_adapter/test_terminal_status_schema.py`
- `tests/agent_orchestration_claude_adapter/test_generator_containment.py`
- `tests/agent_orchestration_claude_adapter/test_phase_order_conformance.py`
- `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py`
- `tests/agent_orchestration_claude_adapter/test_divergence_log.py`
- `tests/agent_orchestration_claude_adapter/test_no_forbidden_calls_against_implement_ticket_js.py`
- `tests/agent_orchestration_claude_adapter/test_claude_containment.py`
- `tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py`

`staging_artifacts/TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER/plan.md` updated with a Deviations
section (4 entries, none touching file layout/package boundaries/Do-NOT-touch lists).

## Completion Summary

Built a read-only Claude conformance adapter on top of the `agent-orchestration/` contract shipped
by the predecessor ticket (`TCK-20260721-ORCHESTRATION-CONTRACT-CORE`). The investigation found
that contract had zero terminal-status representation, blocking this ticket's own AC #3; resolved
by extending the contract itself with a new sibling file, `agent-orchestration/terminal-statuses.yaml`
(this ticket's own Step 1, per a Plan-phase decision reviewed and approved by architecture-reviewer).
Shipped: a terminal-status extractor and rendered-representation generator (new package,
`tools/agent_orchestration_claude_adapter/`, kept structurally separate from the predecessor's
`tools/agent_orchestration/`), phase-order and terminal-status conformance tests, an
approval-aware divergence log (`agent-orchestration/intentional-divergences.md`, zero entries —
this ticket's own build produced zero real divergences by construction), an AST no-write/no-subprocess
guard against `.claude/workflows/implement-ticket.js`, a real-tree containment proof, and a
Codex-side scope-creep guard. 18 new files, zero existing files modified. All 6 ACs satisfied and
independently verified at Architecture-Verify (APPROVED) and Verify.

Test results: 43/43 passed in this ticket's own suite; 101 passed / 1 xfailed (pre-existing,
unrelated) / 1 failed across the full regression surface. The 1 failure
(`tests/agent_orchestration/test_contract_structure.py::test_contract_yaml_has_versioning_field_and_documented_scheme`)
is a pre-existing bug introduced by the predecessor ticket's own closing commit (`b1b2555a`) — that
test reads a `staging_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/plan.md` path which the
same commit's Finalize phase relocated to `stored_artifacts/`. Confirmed via `git log` this ticket
never touched that test file. Follow-up hotfix ticket filed to track the fix:
`TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH` (`tickets/todos/`).

Zero divergences found or logged during this ticket's own build. Zero `.claude/` diff and zero
`docs/guidelines/intentional_divergences.md` diff confirmed independently at every phase
(Implement, Architecture-Verify, Test, Verify).

---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260804-DOC-UPDATER-ROLE-FILE
phase: done
date: 2026-08-04
tags: [workflows, process-improvement, agent-monitoring]
---

# TCK-20260804-DOC-UPDATER-ROLE-FILE

## Title
Add missing agent-orchestration/roles/doc-updater.yaml — provider-neutral contract is missing the doc-updater role file

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`agent-orchestration/workflows/implement-ticket.yaml` (the provider-neutral orchestration contract,
distinct from the Claude-specific `.claude/workflows/implement-ticket.js`) already lists
`Document-Update` in its `phases:` and `doc-updater` in its `agents:` — added during
TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION as a documented deviation fix. But every *other* agent
in that `agents:` list has a matching `agent-orchestration/roles/<name>.yaml` file (10 role files
for 10 agents: `role_version`, `role_id`, `description`, `phases`, `has_agent_file`) — `doc-updater`
is the only one missing its role file. `tools/agent_orchestration/loader.py::load_contract()` does
not cross-validate `agents:` membership against role-file existence, so nothing currently fails —
but a non-Claude provider consuming this contract (e.g. the Codex adapter under
`tests/agent_orchestration_codex_adapter/`) has no per-role metadata to read for doc-updater, unlike
every other agent. This was a known, explicitly disclosed gap at the time
(VOCAB-REGISTRATION's Implementation Notes: "No `roles/*.yaml` file was added (confirmed no test or
loader cross-references `agents:` membership against role-file existence)") — this ticket closes it.

## Scope
- Add `agent-orchestration/roles/doc-updater.yaml`, mirroring `parity-updater.yaml`'s shape (the
  closest structural precedent — both are post-Implement, non-gating, docs-writing specialist
  agents with a real `.claude/agents/*.md` file):
  ```yaml
  role_version: 1
  role_id: doc-updater
  description: <one line, mirroring .claude/agents/doc-updater.md's own frontmatter description>
  phases: [Document-Update]
  has_agent_file: true
  ```
- Update `tests/agent_orchestration/test_contract_structure.py::test_load_contract_succeeds_against_the_real_contract`'s
  hardcoded `assert len(bundle.roles) == 10` to `== 11` (11 role files after this fix: the 10
  existing + doc-updater).
- Re-run the full `agent_orchestration`/`agent_orchestration_claude_adapter`/
  `agent_orchestration_codex_adapter` test suites to confirm no other hardcoded role-count literal
  needs updating (VOCAB-REGISTRATION already found and fixed several such literals — this ticket
  must not repeat that miss by assuming only the one known assertion needs a change).

## Out of Scope
- No change to `.claude/agents/doc-updater.md`, `.claude/workflows/implement-ticket.js`, or any
  Claude-specific wiring — that is already correctly registered (verified directly this session).
- No change to `agent-orchestration/workflows/implement-ticket.yaml`'s `phases:`/`agents:` entries
  themselves — those are already correct; only the missing `roles/` file is being added.
- No change to `docs/architecture/doc_updater_agent.md`'s Status (already `Accepted`, closed by the
  parent epic TCK-20260803-DOC-UPDATER-EPIC).
- No new loader-level cross-validation (agents: vs. roles/ existence) — that would be a behavior
  change to `loader.py` beyond this hotfix's scope of "add the missing file to match the existing
  pattern"; if wanted, it should be raised as its own separate ticket.

## Acceptance Criteria
- [x] `agent-orchestration/roles/doc-updater.yaml` exists, following the same shape/keys as the
      other 10 role files, with `phases: [Document-Update]` and `has_agent_file: true`.
- [x] `tools/agent_orchestration/loader.py::load_contract()` succeeds against the real repo root and
      `bundle.roles` includes an entry with `role_id == "doc-updater"`. Verified directly via
      `test_load_contract_succeeds_against_the_real_contract`, which loads the real contract.
- [x] `test_load_contract_succeeds_against_the_real_contract`'s role-count assertion updated to match
      the new real count (11) and passes.
- [x] Full `tests/agent_orchestration/`, `tests/agent_orchestration_claude_adapter/`,
      `tests/agent_orchestration_codex_adapter/` suites pass with no other stale count/list literal
      left unfixed. Verified directly: 124 passed; grepped for every `== 10`/`10 role` literal
      across all three suites and `agent-orchestration/` before declaring done — found and fixed one
      additional literal (line 81) beyond the originally-scoped line 147.

## Related Tickets
- TCK-20260803-DOC-UPDATER-EPIC (done) — parent epic; this ticket closes a gap discovered
  post-close while auditing whether the new phase/agent were registered in provider-agnostic data,
  not just Claude-specific data.
- TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION (done) — added `Document-Update`/`doc-updater` to
  `agent-orchestration/workflows/implement-ticket.yaml`'s `phases:`/`agents:` as an in-session
  deviation fix, and explicitly documented (not silently skipped) that the corresponding
  `roles/*.yaml` file was left out of that ticket's scope.
- TCK-20260803-DOC-UPDATER-CORE-WIRING (done) — original phase/agent wiring on the Claude side.
- TCK-20260721-ORCHESTRATION-CONTRACT-CORE / TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER — built the
  `agent-orchestration/` contract and its Claude-adapter conformance tests this ticket touches.

## Related Docs
- `docs/architecture/agent_orchestration_contract.md` — the ADR establishing `agent-orchestration/`
  as the provider-neutral source specification.
- `agent-orchestration/README.md` — describes the contract's file manifest and bootstrap-once
  (not ongoing-sync) relationship to `tools/agent-monitoring/vocabulary.py`.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION/` — contains the original deviation
  writeup this ticket completes.

## Related Code Areas
- `agent-orchestration/roles/` (new file: `doc-updater.yaml`)
- `agent-orchestration/roles/parity-updater.yaml` (structural precedent)
- `tools/agent_orchestration/loader.py` (`load_contract()`, `_load_role_yaml()` — read-only, not
  modified)
- `tests/agent_orchestration/test_contract_structure.py`

## Assumptions / Open Questions
- Assumes `parity-updater.yaml` (not `finalizer.yaml`'s `has_agent_file: false` +
  `inline_prompt_exception` shape) is the correct structural precedent, since doc-updater has a real
  `.claude/agents/doc-updater.md` file, same as parity-updater — confirmed by direct read of both
  role files and both `.claude/agents/*.md` files before writing this ticket.

## Implementation Notes
Added `agent-orchestration/roles/doc-updater.yaml` matching `parity-updater.yaml`'s shape exactly
(`role_version: 1`, `role_id: doc-updater`, `description` copied verbatim from
`.claude/agents/doc-updater.md`'s frontmatter, `phases: [Document-Update]`, `has_agent_file: true`).

Per the ticket's own scope warning (informed by VOCAB-REGISTRATION's prior miss), grepped for
every other hardcoded role-count literal before declaring done, not just the one known assertion.
Found and fixed 2, not 1: `test_contract_structure.py` line 81
(`test_agent_orchestration_dir_has_required_files`, `len(role_paths) == 10`) in addition to the
originally-scoped line 147 (`test_load_contract_succeeds_against_the_real_contract`,
`len(bundle.roles) == 10`). Also found and fixed 2 stale "10" mentions in
`agent-orchestration/README.md` (lines 17-18, prose describing the role count) — outside this
ticket's originally-listed `## Related Code Areas` but directly downstream of the same fix, so
corrected as part of the same pass rather than left stale.

## Test Summary
```
pytest tests/agent_orchestration/ tests/agent_orchestration_claude_adapter/ tests/agent_orchestration_codex_adapter/ -q
```
All passed, no other stale count/list literal found.

## Files Changed
- `agent-orchestration/roles/doc-updater.yaml` (new)
- `tests/agent_orchestration/test_contract_structure.py`
- `agent-orchestration/README.md`
- `docs/parity_ledger/infrastructure.yaml` (INFRA-316 follow-up note)

## Completion Summary
`agent-orchestration/roles/doc-updater.yaml` added, bringing the provider-neutral contract's role
files to parity with its own `agents:` list (11/11, was 10/11). Two stale hardcoded role-count
literals in `test_contract_structure.py` and two stale prose mentions in
`agent-orchestration/README.md` corrected alongside it. `doc-updater`/`Document-Update` are now
fully registered on both the Claude-specific side (verified in the parent epic's close) and the
provider-neutral side (this ticket).

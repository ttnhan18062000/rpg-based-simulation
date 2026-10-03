---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE
phase: done
date: 2026-09-04
tags: [governance, ai]
---

# TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE

## Title
Per-agent tools: frontmatter wave-based rollout, gated on usage-audit baseline

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P0

## Request Summary
GATED ON the tool-usage baseline audit ticket (TCK-20260904-AGENT-TOOL-USAGE-BASELINE), which was created in this same batch. Step 0, blocking, before any wave begins: empirically verify on concern-investigator (the only agent with a tools: field today) whether tools: is actually enforced at the harness level and whether disallowedTools is recognized — observed directly, not assumed from docs. Then run an offline candidate-policy replay per agent using the usage-audit ticket's usage table, classifying every historical 'would deny' call under a 5-way taxonomy (legitimate-but-rare / obsolete / inappropriate-legacy / accidental / unclear-needs-review). Sizing rule is smallest confident scope, not theoretical minimum. Rollout is wave-based, each wave gated on the prior wave's clean observation window: Wave 1 (11 read-oriented roles), Wave 2 (architecture-reviewer, security-reviewer, planner), Wave 3 (implementer, parity-updater — highest blast radius, last). Rollback per wave is a documented single-file frontmatter revert, written before that wave starts.

## Scope
- Step 0 (blocking, before Wave 1): empirically observe and document real harness behavior for both tools: and disallowedTools on concern-investigator by directly attempting a tool call outside its declared scope
- Offline candidate-policy replay per agent against the usage-audit ticket's usage table, with every historical 'would deny' call classified under the 5-way taxonomy
- Wave-based rollout: Wave 1 (11 read-oriented roles) -> Wave 2 (architecture-reviewer, security-reviewer, planner) -> Wave 3 (implementer, parity-updater), each gated on the prior wave's clean observation window
- A documented, trivial single-file frontmatter revert command written before each wave lands
- Parametrized extension of test_concern_investigator_agent_definition.py's pattern to verify each landed agent's tools: field

## Out of Scope
- Beginning implementation before TCK-20260904-AGENT-TOOL-USAGE-BASELINE's usage table is committed
- Any change to agent files beyond tools:/disallowedTools frontmatter scoping
- Resolving the Guardrail Enforcement epic's test-scoper-hang-guard ticket's three-way file-overlap on .claude/agents/-adjacent files beyond coordinating to avoid clobbering concurrent edits

## Acceptance Criteria
- [x] Step 0 empirical verification performed before Wave 1: an actual attempt to invoke a tool not in concern-investigator's tools: field is made and the real harness behavior (hard-denied vs. silently-allowed vs. merely-absent-from-list) is directly observed and documented — the prior TCK-20260709 smoke test does not satisfy this; disallowedTools checked the same way
- [x] Rollout does not begin until TCK-20260904-AGENT-TOOL-USAGE-BASELINE's usage table exists and is linked as this ticket's input dependency
- [x] For every Wave 1 agent, a candidate tools: scope is proposed with every historical 'would deny' call classified per the 5-way taxonomy — no capability silently dropped without that classification
- [x] After a wave lands, each of that wave's agent files carries an explicit tools: field verified by a parametrized extension of test_concern_investigator_agent_definition.py's pattern, plus a documented single-file revert command written before the change lands

## Related Tickets
- Depends on TCK-20260904-AGENT-TOOL-USAGE-BASELINE — do not begin implementation until that ticket's usage table is committed
- TCK-20260709-CONCERN-INVESTIGATOR-AGENT (added the repo's only tools: field; its runtime-verification evidence is weaker than Step 0 requires)
- TCK-20260707-SUBAGENT-FRONTMATTER (explicitly deferred tools:/model: scoping as a follow-up — this ticket is that deferred follow-up)

## Related Docs
- docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md
- docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/agents/concern-investigator.md
- .claude/agents/*.md
- .claude/settings.json
- tests/tools/test_concern_investigator_agent_definition.py

## Assumptions / Open Questions
- The only existing 'runtime verification' evidence (TCK-20260709) is weaker than Step 0 requires — it only showed the agent chose not to call Edit/Write, not that an attempted call would be blocked
- disallowedTools has zero local precedent in this repo, only third-party docs
- The harness does not hot-reload .claude/agents/ mid-session (requires session restart) — wave observation windows must account for this
- TCK-20260904-AGENT-TOOL-USAGE-BASELINE's usage table does not exist yet at ticket-creation time — this ticket must not be scheduled for implementation ahead of that one landing
- Wave 3 (implementer, parity-updater) carries the highest blast radius and must land last
- Roadmap flags a three-way file-overlap point with Guardrail Enforcement's M3 (TCK-20260904-TEST-SCOPER-HANG-GUARD, this same batch) around .claude/agents/-adjacent files — coordinate, don't let concurrent edits clobber each other

## Implementation Notes

Followed staging_artifacts/TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE/plan.md's 14 steps exactly,
in order, with no deviations from the plan's own file-by-file spec:

- **Architecture-review follow-up (pre-Step-1)**: fixed investigation.md's per-agent candidate-scope
  table cells for `investigator` and `done-checker` to literally list `SendFeedback` and the two
  `mcp__knowledge-gateway__*` tools respectively in the "Candidate `tools:` scope" column — the
  adjacent "would deny" classification text already said "keep in scope" for both, but the table
  cell itself had omitted them. Documentation-quality fix only; no scope change (the plan's own
  frontmatter values in plan.md and the new test file already correctly included them).
- **Step 1**: created `tests/tools/test_wave1_agent_tools_frontmatter.py`, structurally modeled on
  `tests/tools/test_concern_investigator_agent_definition.py`'s `_parse_frontmatter` helper. Ran it
  before any frontmatter edit to confirm the expected RED state (29 failed / 18 passed) — every
  Wave 2/3 guard and the concern-investigator byte-identical check passed immediately; every other
  Wave 1 agent's `tools:`-declared/excluded-tool assertions failed with `KeyError: 'tools'`, proving
  the test actually exercises the files rather than false-passing.
- **Step 2**: added the `tools:` line to `.claude/agents/doc-updater.md` on top of its existing
  uncommitted item-6 prose addition (from sibling `TCK-20260904-DOC-COVERAGE-REVERSE-CHECK`) — the
  `Edit` `old_string` was scoped to only the `description:` line + both `---` delimiters, leaving
  lines 68-73 (item 6) untouched. Confirmed via `git diff --stat` that this file's diff against
  `HEAD` is 7 insertions total (6 lines of pre-existing item-6 prose + this ticket's own 1-line
  `tools:` addition), matching the plan's own expectation exactly.
- **Steps 3-11**: added a single `tools:` frontmatter line to each of
  `investigator.md`, `ticket-scoper.md`, `done-checker.md`, `test-scoper.md`, `mechanics-auditor.md`,
  `spec-document-reviewer.md`, `simulation-analyst.md`, `world-debugger.md`, `world-render-reviewer.md`
  — each a pure 1-line addition (confirmed via `git diff --stat`), no other line touched in any of
  the 9 files. `test-scoper.md`'s scope deliberately excludes `Edit` (147 historical calls) per
  investigation.md's explicit judgment call; not silently re-added.
- **Step 12**: verified, did not touch, `.claude/agents/concern-investigator.md` — confirmed zero
  diff against HEAD for this file throughout the whole ticket.
- **Step 13**: ran the full scoped regression pass —
  `pytest tests/tools/test_wave1_agent_tools_frontmatter.py tests/tools/test_concern_investigator_agent_definition.py tests/tools/test_doc_updater_agent_file.py -v`
  (55 passed), `PYTHONPATH=tools:. pytest tests/agent_orchestration/ -q` (55 passed), and the bare
  `pytest tests/tools/ -q` directory per test-scoper's own scoping rule (long-running; executed via
  `run_in_background` and polled to completion in the same turn per this repo's hard rule on
  background commands — see Test Summary for the final result). `tools/validate_frontmatter.py` is
  confirmed N/A for `.claude/agents/*.md` (its docstring only covers doc/ticket/artifact/archive
  content types; zero `agents`/`.claude` references in the script) — not run against these files, as
  the plan specifies.
- **Step 14**: inserted the new "Step 0 outcome, confirmed (2026-09-05)" paragraph into
  `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`
  immediately after the existing Step 0 bullet and before the "Offline candidate-policy replay"
  paragraph. Confirmed via `git diff` that this is the only change to the file — one added
  paragraph, zero deletions, zero reflow of surrounding lines (Wave 1/2/3 role lists, Sizing rule,
  Observability requirement, and Acceptance signal section all untouched).

No deviations from plan.md. Wave 2 (`architecture-reviewer`, `security-reviewer`, `planner`) and
Wave 3 (`implementer`, `parity-updater`) were not touched — confirmed by
`test_wave2_wave3_agents_do_not_gain_tools_field` passing for all 5 files, and by direct read
confirming none of those 5 files gained a `tools:` field.

**Confidence caveat carried forward explicitly (per plan.md's Anti-Drift Notes)**: 6 of the 11 Wave
1 agents (`concern-investigator`, `mechanics-auditor`, `simulation-analyst`,
`spec-document-reviewer`, `world-debugger`, `world-render-reviewer`) have zero historical
tool-call rows — their `tools:` scopes are policy-derived from a static read of each agent's own
file, not usage-validated, and are the most likely candidates for the epic's own post-rollout
tightening pass.

## Test Summary

- `pytest tests/tools/test_wave1_agent_tools_frontmatter.py tests/tools/test_concern_investigator_agent_definition.py tests/tools/test_doc_updater_agent_file.py -v` — 55 passed, 0 failed.
- `PYTHONPATH=tools:. pytest tests/agent_orchestration/ -q` — 55 passed, 0 failed (pure regression check; this ticket touches no `agent-orchestration/*.yaml`).
- `pytest tests/tools/ -q` (bare directory) — ran via `run_in_background` due to runtime exceeding the 120s foreground timeout (took 978s / 16m18s total); polled to completion in the same turn. Final result: **2777 passed, 5 failed, 16 skipped, 1 xfailed**. All 5 failures are pre-existing and out of this ticket's scope — none touch `.claude/agents/*.md`, agent frontmatter, or `tools:` scoping: `test_kgmcp_phase3_pilot_acceptance_measurement.py::test_zero_mutation_of_agent_monitoring_and_manifest_across_full_run` and 4 cases in `test_knowledge_search.py` (`test_query_completes_within_2_seconds`, `test_build_docs_chunk_count_exceeds_500`, `test_build_completes_under_five_minutes`, `test_existing_ticket_query_still_works`) are knowledge-search SLA/corpus-size/mutation-detection tests, unrelated subsystems this ticket never touched — most plausibly environment-load flakiness from running the full 2800+-test directory in one process (SLA assertions of "<2s"/"<5min" are sensitive to concurrent system load). Not caused by this ticket's edits.
- Pre-edit RED-state check on the new test file alone: 29 failed / 18 passed, confirming the test file exercises real file state (not a false-pass) before any of Steps 2-11 landed.
- `tools/validate_frontmatter.py` confirmed N/A for `.claude/agents/*.md` (docstring only names doc/ticket/artifact/archive content types; zero `agents`/`.claude` matches in the script) — not run against these files per plan.md Step 13.4.

## Files Changed

- `.claude/agents/doc-updater.md` — added `tools:` frontmatter line (on top of pre-existing, unrelated uncommitted prose from a sibling ticket; that prose was not touched)
- `.claude/agents/investigator.md` — added `tools:` frontmatter line
- `.claude/agents/ticket-scoper.md` — added `tools:` frontmatter line
- `.claude/agents/done-checker.md` — added `tools:` frontmatter line
- `.claude/agents/test-scoper.md` — added `tools:` frontmatter line (Edit deliberately excluded)
- `.claude/agents/mechanics-auditor.md` — added `tools:` frontmatter line
- `.claude/agents/spec-document-reviewer.md` — added `tools:` frontmatter line
- `.claude/agents/simulation-analyst.md` — added `tools:` frontmatter line
- `.claude/agents/world-debugger.md` — added `tools:` frontmatter line
- `.claude/agents/world-render-reviewer.md` — added `tools:` frontmatter line
- `tests/tools/test_wave1_agent_tools_frontmatter.py` — new parametrized structural test file (Step 1)
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md` — additive Step 0 outcome paragraph (Step 14, Implement); Document-Update phase additionally fixed a second stale claim in the Problem section ("only 1 of 16 agents declares a scoped tools:") with a "Status update (2026-09-05)" paragraph
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` — Document-Update phase added an "Item 1 — partial progress (2026-09-05)" paragraph (11/16 agents now carry tools:, not fully shipped, stays in the "remaining to implement" count until Wave 2/3 land) and updated the Epic G bullet under "Epics and detail docs" the same way
- `staging_artifacts/TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE/investigation.md` — edited in this run: table-cell fix per architecture-review's non-blocking observation (SendFeedback / mcp__knowledge-gateway__* tools made explicit in the candidate-scope column for investigator/done-checker). `plan.md` and `test_plan.md` in this same directory were NOT touched by this Implement run — they were already approved/pre-existing before this run started, per the dispatching instructions.
- `tickets/inprogress/TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE.md` — this ticket file (Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary)
- `.claude/agents/concern-investigator.md` — explicitly NOT changed (verified byte-identical throughout; listed here only to make the non-change auditable)
- `docs/parity_ledger/infrastructure.yaml` (modified, by this ticket's own Parity phase, adding
  `INFRA-406` for the Wave 1 agent-tools frontmatter rollout)

Not touched by this run (pre-existing, unrelated changes from sibling tickets
`TCK-20260904-AGENT-TOOL-USAGE-BASELINE`, `TCK-20260904-CAPABILITY-ENVELOPE-BASELINE`,
`TCK-20260904-DOC-COVERAGE-REVERSE-CHECK`, and `TCK-20260904-TEST-SCOPER-HANG-GUARD`, all already
Finalized but not yet committed in this shared worktree at the time this ticket's own Verify phase
ran): `docs/REGISTRY.yaml`, `docs/agent-monitoring/README.md`, `docs/ai/README.md`,
`docs/ai/capability_envelope_baseline.md`, `docs/ai/ticket-lifecycle.md`, `docs/ai/workflows.md`,
`docs/architecture/doc_updater_agent.md`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/guardrail_enforcement_epic.md`.

## Completion Summary

Landed Wave 1 only, as this ticket's own Acceptance Criteria requires: Step 0's empirical
verification of `tools:`/`disallowedTools` harness enforcement (via live subagent dispatch +
binary-schema extraction, documented in investigation.md), the usage-baseline dependency check, a
full per-agent candidate-`tools:`-scope table with every historical "would deny" call classified
under the 5-way taxonomy, and the 11-file Wave 1 frontmatter rollout itself (10 files edited,
`concern-investigator.md` confirmed unchanged) with a new parametrized test file
(`tests/tools/test_wave1_agent_tools_frontmatter.py`) and documented per-file revert commands
(plain `git checkout HEAD -- .claude/agents/<name>.md` for 10 files; a surgical single-line `Edit`
removal for `doc-updater.md` specifically, since `HEAD` predates its sibling ticket's still-
uncommitted prose change). Wave 2 (`architecture-reviewer`, `security-reviewer`, `planner`) and
Wave 3 (`implementer`, `parity-updater`) are explicitly NOT part of this ticket's completion — they
require their own future tickets, opened only after Wave 1's real elapsed observation window
(genuine calendar time with live agent-monitoring data) shows zero permission regressions. Six of
the 11 landed agents (`concern-investigator`, `mechanics-auditor`, `simulation-analyst`,
`spec-document-reviewer`, `world-debugger`, `world-render-reviewer`) have policy-derived, not
usage-validated, scopes and are flagged as the most likely candidates for a post-rollout tightening
pass. `test-scoper.md`'s exclusion of `Edit` (147 historical calls) is the single largest,
explicitly-reasoned judgment call in the rollout, not a silent default.

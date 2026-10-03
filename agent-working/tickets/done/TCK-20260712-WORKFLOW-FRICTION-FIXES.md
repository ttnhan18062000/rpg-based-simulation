---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260712-WORKFLOW-FRICTION-FIXES
phase: done
date: 2026-07-12
tags: [ai, agent-monitoring, process-improvement, frontmatter]
---

# TCK-20260712-WORKFLOW-FRICTION-FIXES

## Title
Fix two recurring agent-workflow friction points from the 2026-W28 monitoring retro: late-caught staging-artifact frontmatter/Completion-Summary omissions, and implementer ending its turn on a still-running `run_in_background` command

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
`agent-monitoring/retro/RETRO-2026-W28.md`'s Notes section (items 1 and 3, "What failed most?" /
"What to change?") documents two distinct, independently-observed friction points from this week's
runs, both self-evidently fixable by adding standing reminder text to existing prompt/agent-definition
files — no runtime logic, schema, or architecture change required:

1. **Late-caught staging-artifact hygiene defects.** Three separate `DOD_BLOCKED` gate failures this
   week were each a one-line fix: a new `staging_artifacts/{ticket_id}/*.md` file missing its
   frontmatter block, one with an invalid `artifact_type` enum value, and one ticket left with a blank
   `## Completion Summary` section. All three were only caught at Verify (`done-checker`'s static
   pre-check), costing a full round-trip each time, when they could have been prevented at the point
   the file was authored (Investigate/Implement phases of `.claude/workflows/implement-ticket.js`).
2. **Implementer ending its turn on an unfinished background command.** Three times within one ticket
   this week, the `implementer` subagent launched a long-running Bash command via `run_in_background`
   and then ended its own turn before the command finished, apparently believing it would be
   auto-resumed the way the top-level orchestrator is. Each time required the orchestrator to manually
   detect the still-running process (via `ps`/`Monitor`) and re-send the implementer a status update
   before it could continue. This has no corresponding gate-failure metric — it was only caught by
   direct observation — but is a real wall-clock cost and plausibly a contributor to this week's
   slowest `Implement`-phase runs (593.2 avg spend-proxy, the most expensive phase).

Both fixes are pure prompt-text / agent-standing-instruction additions to existing files. Bundled into
one hotfix ticket per explicit request, as two distinct, independently-verifiable sub-items rather than
two separate tickets.

## Scope
**Sub-item A — staging-artifact / Completion-Summary reminder text:**
- In `.claude/workflows/implement-ticket.js`'s Investigate-phase agent prompt (the block that
  instructs writing `staging_artifacts/${tid}/investigation.md` and
  `staging_artifacts/${tid}/test_plan.md`, currently around lines 438-446), add an explicit reminder
  that each new file must begin with a valid frontmatter block matching sibling files' format, with
  `artifact_type` drawn from `tools/validate_frontmatter.py`'s `ARTIFACT_TYPE_VALUES` enum
  (`investigation`, `plan`, `test_plan` — the same enum `done_checker_static.py` enforces via
  `validate_directory`).
- In the Implement-phase agent prompt's post-Implement "update the ticket" instructions (currently
  around line 606, "Update the 'Implementation Notes' section..."), add an explicit reminder to never
  leave the ticket's `## Completion Summary` section blank when the ticket is later moved to done —
  and, if the Implement-phase agent is also the one authoring or amending
  `staging_artifacts/{tid}/plan.md`'s "Deviations" section (line 607), the same frontmatter-validity
  reminder as sub-item A's first bullet applies there too.
- Wording only — reuse the retro's own proposed action text (`RETRO-2026-W28.md` Notes item 3, first
  bullet) as the basis; do not invent new requirements beyond what the enum/schema already enforce.

**Sub-item B — implementer standing instruction on `run_in_background`:**
- Add an explicit standing instruction to `.claude/agents/implementer.md` (its own file, not a
  per-call prompt) stating the implementer must not end its turn while a `run_in_background` command
  it started is still running — it must either run the command in the foreground, or poll for the
  command's own completion within the same turn before returning control.
- Evaluate whether any other subagent role definition under `.claude/agents/` exhibits the same
  pattern risk (the retro's proposed action says "the `implementer` agent (and any other subagent
  role)") — if another agent definition's own instructions plausibly invite launching a long-running
  background command (e.g. `investigator`, `test-scoper`), add the same standing instruction there.
  Do not add it to agent definitions that have no plausible reason to run long background commands.

## Out of Scope
- Any change to `done_checker_static.py`, `validate_frontmatter.py`, or the `ARTIFACT_TYPE_VALUES` /
  `LAYER_VALUES` enums themselves — those are already correct and are the source of truth this ticket
  points prompt text at, not a target for modification.
- Any change to the `Workflow`/`run_in_background` tool's actual runtime semantics, or to how the
  orchestrator detects/resumes a stalled background process — this ticket only changes what the
  implementer (and other agents, if applicable) is told to do, not the harness's own behavior.
- The broader "port `.claude/workflows/*.js` to real runtime execution instead of LLM narration"
  effort — that is `TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME` (backlog, deliberately deprioritized,
  not this ticket's layer; see Related Tickets).
- Any change to `agent-monitoring/` schema or gate-failure metrics to make the background-process
  pattern visible in `runs.jsonl`/`events.jsonl` — the retro flags this as invisible in the data, but
  instrumenting it is a distinct, larger scope than a standing-instruction text fix.
- Any change to other `.claude/workflows/*.js` files (`implement-epic.js`, `create-tickets.js`, etc.)
  beyond `implement-ticket.js` — the retro's concrete findings are scoped to `implement-ticket.js`
  runs only; if the same staging-artifact pattern exists in `implement-epic.js`, that is a follow-up,
  not silently bundled here.
- Retroactively fixing the three already-completed tickets whose Verify round-trips prompted this
  retro finding — those already passed Verify and are in `tickets/done/`.

## Acceptance Criteria
- [ ] `.claude/workflows/implement-ticket.js`'s Investigate-phase prompt text explicitly instructs
      that new `staging_artifacts/${tid}/*.md` files must include a frontmatter block with
      `artifact_type` set to one of `investigation`, `plan`, `test_plan` (verifiable by reading the
      updated prompt string in the file).
- [ ] `.claude/workflows/implement-ticket.js`'s Implement-phase "update the ticket" instructions
      explicitly instruct never leaving `## Completion Summary` blank (verifiable by reading the
      updated prompt string in the file).
- [ ] `.claude/agents/implementer.md` contains a standing instruction (not conditional on a specific
      ticket) that the agent must not end its turn while a `run_in_background` command it started is
      still running, and must either run foreground or poll to completion within the same turn
      (verifiable by reading the file).
- [ ] A decision is recorded (in Implementation Notes) on whether any other `.claude/agents/*.md` file
      received the same `run_in_background` standing instruction, with a one-line reason per file
      considered.
- [ ] `tests/tools/test_step0_ts_orchestrator.py` and any other existing static/raw-source-text tests
      against `.claude/workflows/implement-ticket.js` still pass unmodified (this ticket adds prompt
      text, it does not change phase sequencing, schema, or control flow those tests assert on).
- [ ] No `src/` file is touched; `behavior_changed=false` is reportable at Implement (pure prompt/agent
      instruction text — no runtime engine behavior).

## Related Tickets
- TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME (backlog — related but distinct layer: that ticket is
  about porting `.claude/workflows/*.js` off LLM narration entirely onto a real execution surface;
  this ticket stays within the current narrate+gate strategy and only edits prompt text within it.
  Not a duplicate; flagged per the mandatory backlog-conflict check).
- TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC (done — same general anti-pattern class, "agent
  prompt Step 0/0b text carrying a mechanical instruction the agent must reproduce verbatim", but its
  three child tickets fixed a different concrete bug: `tool_call_count`/`cost_proxy_score`/`ts`
  sidecar-capture corruption in `implement-ticket.js`/`implement-epic.js`/`create-tickets.js`. No file
  overlap with this ticket's specific prompt blocks; related precedent, not a conflict.)
- TCK-20260705-GATE-DET-DONE-CHECKER (done — introduced `done_checker_static.py`'s deterministic
  pre-check, including the frontmatter/`REQUIRED_ARTIFACT_FILES` check this ticket's sub-item A is
  trying to satisfy earlier in the pipeline; this ticket does not modify that checker, only points
  prompt text at the enum it already enforces.)

## Related Docs
- `agent-monitoring/retro/RETRO-2026-W28.md` — Notes items 1 and 3 are the evidentiary basis for this
  ticket's scope; reuse that text, do not re-derive independently.
- `docs/guides/agent_monitoring.md` — retro process and cadence context (no changes needed here).
- `docs/agent-monitoring/schema.md`, `docs/agent-monitoring/README.md` — reviewed for constraints; no
  overlap (this ticket does not touch monitoring schema or bookkeeping fields, only prompt text).

## Related Stored Artifacts
- None found covering this exact scope (workflow-prompt-text staging-artifact reminders, or
  implementer background-process standing instructions). Nearest-neighbor stored artifacts reviewed:
  `stored_artifacts/TCK-20260705-GATE-DET-DONE-CHECKER/` area (not present as a separate folder;
  ticket is fully closed) and the agent-bookkeeping-determinism epic's artifacts — neither covers this
  specific text.

## Related Code Areas
- `.claude/workflows/implement-ticket.js` (Investigate-phase prompt ~lines 414-451; Implement-phase
  prompt ~lines 568-613)
- `.claude/agents/implementer.md`
- `.claude/agents/` (other role files, to be evaluated per sub-item B's scope — no specific file
  committed to yet)
- `tools/gate_checks/done_checker_static.py` (reference only — source of `REQUIRED_ARTIFACT_FILES`
  and the frontmatter check this ticket's reminder text targets; not modified)
- `tools/validate_frontmatter.py` (reference only — source of `ARTIFACT_TYPE_VALUES`; not modified)

## Assumptions / Open Questions
- Assumes `.claude/workflows/implement-ticket.js` line numbers cited above (~414-451, ~568-613) are
  still accurate at implementation time; the file may have shifted since this scoping pass — the
  implementer should locate the blocks by content (the `staging_artifacts/${tid}/investigation.md`
  and "Update the 'Implementation Notes' section" strings), not by line number.
- Assumes "any other subagent role" from the retro's proposed action (item 3, second bullet) means
  evaluating existing `.claude/agents/*.md` files for the same risk pattern, not creating new agent
  roles. If evaluation finds no other agent plausibly launches long-running background commands, it is
  acceptable to add the instruction only to `implementer.md` and record that reasoning.
- Assumes `layer: ai` is correct per this repo's established convention (Claude agent-orchestration
  tooling, not gameplay AI/cognition) — consistent with `TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC`
  and `TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK`, both scoping near-identical agent-prompt-text
  fixes with the same layer value.
- If the static test `tests/tools/test_step0_ts_orchestrator.py` (or a similar raw-source-text test)
  turns out to assert an exact substring range of the Investigate/Implement prompt blocks this ticket
  is adding text to, that assumption would be invalidated and the test would need a corresponding
  update — flagged for the Investigate phase to confirm, not assumed resolved here.

## Implementation Notes

**Sub-item A — `.claude/workflows/implement-ticket.js`:**
- Investigate-phase prompt (the block producing `staging_artifacts/${tid}/investigation.md` and
  `staging_artifacts/${tid}/test_plan.md`, found by content match): added a paragraph after the
  "FILE 2" section listing requiring both new files to begin with a valid frontmatter block matching
  sibling files' format, with `artifact_type` set to one of `investigation`, `plan`, `test_plan` (the
  enum `tools/validate_frontmatter.py`'s `ARTIFACT_TYPE_VALUES` defines and
  `done_checker_static.py` enforces), and noting a missing/invalid frontmatter is a `DOD_BLOCKED`
  failure caught late at Verify.
- Implement-phase prompt's post-Implement "update the ticket" instructions (found by content match
  on `Update the "Implementation Notes" section...`): item 1 now also instructs filling in the
  ticket's `## Completion Summary` section at the same time, with an explicit "never leave it blank
  ... a blank Completion Summary is a DOD_BLOCKED failure caught late at Verify" reminder. Item 2
  (non-hotfix only — amending `staging_artifacts/{tid}/plan.md`'s "Deviations" section) got the
  parallel reminder to keep that file's existing frontmatter block valid (same `ARTIFACT_TYPE_VALUES`
  enum) when amending it.
- Verified with `node --check .claude/workflows/implement-ticket.js` (syntax OK) and confirmed no
  raw-source-text test asserts an exact substring range across either edited block: grepped all tests
  under `tests/tools/` referencing `implement-ticket.js` for `staging_artifacts|investigation.md|
  test_plan.md|Completion Summary|Implementation Notes|frontmatter` — only
  `test_workflow_meta_conformance.py` had one unrelated string hit (a different quoted phrase, not
  in either edited block). `tests/tools/test_step0_ts_orchestrator.py`'s exact adjacency-string
  assertions (`captureTs()` → `writeSidecar()` → `agent(` sequences) are untouched — both new
  reminder paragraphs were inserted inside the prompt string argument to `agent(...)`, not between
  those lines.

**Sub-item B — `.claude/agents/implementer.md` and per-agent-file evaluation:**
- Added a new "Background Commands" section to `.claude/agents/implementer.md` stating the agent
  must not end its turn while a `run_in_background` Bash command it started is still running — must
  run foreground or poll to completion within the same turn.
- Evaluated every other file under `.claude/agents/*.md` for the same risk pattern (does the agent's
  own role instructions plausibly involve launching a long-running background command?):
  - `architecture-reviewer.md` — no addition. Reviews a plan/diff by reading files; never instructed
    to execute commands.
  - `concern-investigator.md` — no addition. Runs `python3 tools/knowledge_search.py`, `graphify
    query`, and `grep`/`find` — all short, single-shot lookups, not long-running processes an agent
    would plausibly background.
  - `done-checker.md` — no addition. Runs one `python3 -c "..."` static pre-check one-liner; quick,
    deterministic, not backgroundable.
  - `investigator.md` — no addition. Reads code/docs and cross-references parity `test_path`
    entries for existence; never instructed to execute a test suite itself.
  - `mechanics-auditor.md` — no addition. Runs a `python3 -c "..."` static check one-liner per
    parity entry; quick, not long-running.
  - `parity-updater.md` — no addition. Edits YAML entries by reading/writing files; no command
    execution instructed.
  - `planner.md` — no addition. Produces `plan.md` from reading files; no command execution.
  - `security-reviewer.md` — no addition. Reviews a diff by reading files; no command execution.
  - `simulation-analyst.md` — no addition. Analyzes an already-completed run's existing output data
    under `data/runs/`; does not launch simulation runs itself.
  - `test-scoper.md` — **added**. Its own Output section explicitly instructs "Execute the command
    via Bash and capture the full output" for a scoped `pytest` run — the same
    launch-a-test-suite-then-not-wait pattern the retro's proposed action names as an example risk.
    Added the same "Background Commands" standing instruction as `implementer.md`.
  - `ticket-scoper.md` — no addition. Scans tickets/docs/registry by reading files; no command
    execution.
  - `world-debugger.md` — no addition. Traces root cause by reading code/schemas; its Output section
    only recommends which tests to run as a follow-up, it does not itself execute them.

## Test Summary
`pytest tests/tools/ -k "workflow or implement_ticket or step0" -v` — 30 passed, 1 xfailed (pre-existing,
unrelated), 757 deselected. Also ran the three files identified via
`grep -rln "implement-ticket.js" tests/tools/` that weren't matched by the `-k` filter
(`test_scope_orphan_fix.py`, `test_tag_skill_mapping_check.py`,
`test_current_run_sidecar_orchestrator.py`) as an extra safety net: 28 passed, 0 failed. No test
required modification.

## Files Changed
- `.claude/workflows/implement-ticket.js`
- `.claude/agents/implementer.md`
- `.claude/agents/test-scoper.md`
- `tickets/inprogress/TCK-20260712-WORKFLOW-FRICTION-FIXES.md`

## Completion Summary
Both friction points from `RETRO-2026-W28.md` Notes items 1 and 3 are fixed as pure prompt-text /
agent-standing-instruction additions, matching the ticket's hotfix scope exactly. Sub-item A added
frontmatter-validity and Completion-Summary reminders to `implement-ticket.js`'s Investigate- and
Implement-phase agent prompts, pointing at the existing `ARTIFACT_TYPE_VALUES` enum and
`done_checker_static.py` checks without modifying either. Sub-item B added a standing
"don't end your turn on a still-running `run_in_background` command" instruction to
`implementer.md`, and after evaluating all 12 other `.claude/agents/*.md` files for the same risk
pattern, added the identical instruction to `test-scoper.md` only (the one other agent explicitly
instructed to execute a `pytest` run via Bash) — reasoning for all 13 files recorded in
Implementation Notes above. No `src/` file was touched, no runtime/schema/architecture behavior
changed, and the existing raw-source-text tests against `implement-ticket.js`
(`tests/tools/test_step0_ts_orchestrator.py` and 3 sibling test files) pass unmodified.

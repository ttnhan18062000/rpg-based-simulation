---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT
phase: done
date: 2026-09-29
tags: [workflows, create-tickets, agent-monitoring, process-improvement]
---

# TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT

## Title
Pilot: run create-tickets.js on the native Workflow tool instead of LLM narration

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
The Claude Code `Workflow` tool exists in this harness now. It runs a JS orchestration script
with `agent()`, `pipeline()`, `parallel()`, `phase()`, `log()`, `args`, resume, and `/workflows`
progress. The repo still assumes the tool is missing. `docs/ai/skills.md` and
`.claude/skills/create-tickets/SKILL.md` (per `TCK-20260708-SKILL-CREATE-TICKETS-WORKFLOW-TOOL-STALE`)
say "not available", so every `/create-tickets` run hand-translates the script phase by phase. The
backlog ticket `TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME` names this surface as its unblock
condition, and that condition is now met.

The user approved a single-script pilot on 2026-09-29, with `create-tickets.js` going first. The
goal is to make it run natively and measure the result against a hand-run baseline. That
measurement decides whether `implement-epic.js` and later `implement-ticket.js` get ported.

Blockers were confirmed by trying on 2026-09-29, so don't re-derive them:
1. `Workflow({name:'create-tickets'})` fails with a **parse error**. The named lookup reads the
   main checkout's copy. Unescaped backticks inside template-literal prompts break acorn at
   `create-tickets.js:613` and `:778`. The same defect class exists at `implement-ticket.js:182,1753`
   and `simq-audit.js:475`, which are out of scope here except as a check (see AC 7).
2. `Workflow({scriptPath})` fails at runtime with **"bash is not defined"**. The runtime has no
   `bash()`, no filesystem or Node APIs, and `Date.now()`, `Math.random()` and argless `new Date()`
   throw.
3. `create-tickets.js` has **5 `bash()` sites**:
   - `captureTs` (~l.131)
   - `writeSidecar` (~l.161), called 4x (comprehend, structure, write-sequence, link-epic)
   - `clearSidecar` (~l.187)
   - the tag-registry check (~l.679)

## Scope
1. **Syntax.** Escape the template-literal backticks in `create-tickets.js` so it parses under
   acorn with `sourceType:'module'`, `allowReturnOutsideFunction` and `allowAwaitOutsideFunction`.
   That is the same config the Workflow runtime accepts. The known acorn copy is
   `frontend/node_modules/acorn`.
2. **Timestamps via args.** Replace `captureTs()`/`bash('date …')` with a required `args.start_ts`,
   which the invoking skill supplies. Don't use `Date.now()` or `new Date()`. `end_ts` stays the
   `<END_TS>` placeholder that the monitoring agent resolves, which is already how it works.
3. **Shell steps through a narrow command-runner.** Add a local `runCommand(cmd, label)` helper
   that dispatches one `agent()` at `effort:'low'` with a fixed schema
   `{exit_code: integer, stdout: string}`. The agent is told to run exactly the given command
   verbatim and report its output, with no interpretation. It replaces the `bash()` calls in
   `writeSidecar`, `clearSidecar` and the tag-registry check. The existing marker parsing
   (`WRITESIDECAR_EXIT:`, `CLEARSIDECAR_EXIT:`, `TAG_CHECK_JSON:`) and the fail-open `log()`
   WARNING behavior stay as they are.
4. **`execution_mode` for native runs.** The run record written by `writeMonitoring` gets
   `"execution_mode":"workflow"`, a third value alongside `pipeline`/`hand` (from
   `TCK-20260929-RUN-EXECUTION-MODE-FIELD`). `generate_retro.py`'s split (~l.814) learns the new
   value. Without it, native runs are indistinguishable from narrated `pipeline` runs, and the
   pilot's comparison can't be read from the retro.
5. **Skill + docs.** Rewrite `.claude/skills/create-tickets/SKILL.md` so it invokes
   `Workflow({scriptPath: '.claude/workflows/create-tickets.js', args:{source, structure, output,
   epic_id, start_ts}})` as the primary path. Keep hand-translation only as a documented fallback
   for when the tool errors. Update the Workflow-availability statements in `docs/ai/skills.md`
   (and the create-tickets rows in `docs/ai/system_overview.md` / `ticket-lifecycle.md` if they
   repeat the "not available" claim; define once, don't duplicate). Use `scriptPath` rather than
   `name`, because the named lookup reads the main checkout and would run a stale copy from a
   worktree. Document that reason.
6. **Pilot run + measurement.** Run `/create-tickets` natively once on a real, small proposal.
   Record the comparison in `stored_artifacts/<this ticket>/pilot_measurement.md` against the
   baseline, the hand-run `CREATE-TICKETS-DOCS-PLANS-SCRIPTS-TOOLS-GOVERNANCE-EPIC` (DONE, 9
   events, W40 shards). The hand run skipped the write-sequence and link agents. Measure:
   - total tokens (and cost_proxy_score, if it's populated)
   - main-session context consumed
   - **tool-call attribution:** do workflow subagents' tool calls land in `tools.jsonl`
     attributed to the run through `.claude/current_run.<session_id>`? This is the open unknown.
     If subagent hooks carry a different session_id, or none, the cost proxy goes dark for native
     runs. That's a finding to record, not a reason to fail the pilot.
   - step fidelity, meaning which phases and agents actually ran, compared with the narrated run
7. **Recommendation.** End `pilot_measurement.md` with a go/no-go for porting `implement-epic.js`
   (11 `bash()` sites) and the specific decision `implement-ticket.js` needs (~50 `bash()` sites
   plus 1 `Date.now()`/`new Date()`). Include a one-line acorn parse status for all
   `.claude/workflows/*.js` so the later ports start from a known list.

## Out of Scope
- Porting `implement-epic.js`, `implement-ticket.js`, `simq-audit.js` or any other workflow
  script, including their backtick fixes. The pilot only reports on them.
- Changing the gate-check architecture of any workflow.
- The Claude Agent SDK standalone-program path described in `TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME`.
- Fixing a native-run attribution gap if the pilot finds one. File a follow-up ticket instead.

## Acceptance Criteria
1. `create-tickets.js` parses with acorn under the runtime's options. A test pins this, e.g. in
   `tests/tools/test_workflow_meta_conformance.py` or a new sibling test. The test skips cleanly
   if acorn/node is absent.
2. `create-tickets.js` contains no `bash(`, `Date.now(`, `Math.random(` or argless `new Date(`.
   A test pins this.
3. `writeSidecar`/`clearSidecar`/tag-check go through `runCommand`. Their fail-open WARNING paths
   are preserved, and the existing tests are updated rather than deleted:
   - `test_create_tickets_sidecar_reset_and_failure_visibility.py`
   - `test_sidecar_clear_reaches_scoped_file.py`
   - `test_epic_create_tickets_sidecar_orchestrator.py`
   - `test_step0_ts_orchestrator.py`
   - `test_create_tickets_tag_scope.py`
   The writeMonitoring agent still has no preceding `writeSidecar`, and `clearSidecar` still
   precedes it.
4. A missing `args.start_ts` returns a structured `INVALID_ARGS` result and doesn't throw. The
   `source` check already works this way.
5. `execution_mode:"workflow"` is written for native runs, and `generate_retro.py`'s split shows
   it, with a test for the new bucket.
6. `create-tickets/SKILL.md` and `docs/ai/skills.md` describe the native path as primary and
   narration as the fallback. No doc still claims the Workflow tool is unavailable for
   create-tickets.
7. One real native `/create-tickets` run completed, and `pilot_measurement.md` records all four
   measurements from Scope 6, the go/no-go, and the acorn parse status list.
8. `TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME` (backlog) gets a dated note saying its first AC
   (an in-harness surface exists) is now satisfied, with a pointer to this pilot's measurement.
   It stays in backlog.

## Related Tickets
- TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME (backlog; the long-horizon parent whose unblock
  condition this pilot confirms)
- TCK-20260708-SKILL-CREATE-TICKETS-WORKFLOW-TOOL-STALE (done; wrote the "not available" text
  being reversed here)
- TCK-20260929-RUN-EXECUTION-MODE-FIELD (done; the `execution_mode` field extended here)
- TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED, TCK-20260928-SIDECAR-CLEAR-MISSES-SESSION-SCOPED-FILE,
  TCK-20260904-COST-PROXY-EPIC-TICKETS (done; sidecar semantics that must survive the port)
- TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH (done; the `captureTs` being replaced)
- TCK-20260706-CREATE-TICKETS-TAG-CHECK (done; the tag check being re-routed)
- TCK-20260911-COST-PROXY-EPIC-TICKETS-RUN-CONFIRMATION (can be checked against the pilot run)

## Related Docs
- `docs/ai/skills.md` ("Skills vs. Workflows — How Invocation Works")
- `docs/ai/system_overview.md`, `docs/ai/ticket-lifecycle.md`, `docs/ai/agents.md`
- `docs/agent-monitoring/schema.md` (`execution_mode` field)
- `docs/plans/agent_infrastructure/idea_workflow_execution_determinism.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME/`
- Baseline: the `CREATE-TICKETS-DOCS-PLANS-SCRIPTS-TOOLS-GOVERNANCE-EPIC` run in
  `agent-monitoring/data/2026-W40/`

## Related Code Areas
- `.claude/workflows/create-tickets.js`
- `.claude/skills/create-tickets/SKILL.md`
- `tools/agent-monitoring/generate_retro.py`, `tools/agent-monitoring/post_tool_hook.py` (read-only
  unless attribution needs a fix, which would be a follow-up)
- `tests/tools/test_*create_tickets*`, `test_sidecar_clear_reaches_scoped_file.py`,
  `test_step0_ts_orchestrator.py`, `test_workflow_meta_conformance.py`, `test_run_execution_mode_field_wiring.py`

## Assumptions / Open Questions
- **Key trade-off (accepted for this pilot, a real decision for implement-ticket):** gate checks
  run orchestrator-side on purpose, so that an agent never reports "gate passed".
  `runCommand()` routes shell through an agent, which weakens that. It returns
  `{exit_code, stdout}` and the script parses the markers, but the agent could still misreport.
  For create-tickets the exposure is small: only sidecar bookkeeping and the tag check. For
  implement-ticket, with most of its gate layer on `bash()`, it's the central decision, and the
  pilot's recommendation must address it explicitly.
- **Sidecar session scope:** `writeSidecar` writes `.claude/current_run.$CLAUDE_CODE_SESSION_ID`
  from inside the runner agent's shell. Whether that env var in a workflow subagent equals the
  session_id that hook payloads carry for the other subagents is the attribution unknown in
  Scope 6. Measure it, don't assume it.
- The `runCommand` agent's own tool calls are bookkeeping and get attributed to whatever the
  sidecar holds. That's the same class as the writeMonitoring exclusion, so note it in the
  measurement.

## Implementation Notes
- Loaded the `workflow-authoring` skill before editing.
- `captureTs()`/`bash('date ...')` was removed entirely, not kept as unreachable dead code, since
  `args.start_ts` fully replaces it and the native runtime has no `bash()` for it to call anyway.
- `execution_mode:"workflow"` is an unconditional literal in `create-tickets.js`'s own
  `record_run.py` call — this file's code only ever executes for real via the native `Workflow`
  tool (hand-narration never runs the literal JS), so no runtime branching was needed. The
  hand-translation fallback documented in `SKILL.md` is told explicitly to use `"pipeline"`
  instead when that fallback path is actually taken.
- Ran the native pilot from the worktree with `scriptPath` (not `name`, which reads the main
  checkout).
- Full details, numbers, and the go/no-go recommendation:
  `stored_artifacts/TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT/pilot_measurement.md`.

## Test Summary
`pytest tests/tools/ -k "create_tickets or generate_retro or workflow or sidecar or step0 or
tag_scope or execution_mode"` — 438 passed. New test file
`tests/tools/test_workflow_runtime_acorn_parse.py` (2 tests) skips cleanly in this worktree (acorn
not installed under `frontend/node_modules/` here) and was manually verified to pass against the
main checkout's real acorn install via a local, gitignored symlink. Updated 3 existing test files
(`test_run_execution_mode_field_wiring.py`, `test_generate_retro.py`,
`test_step0_ts_orchestrator.py`) for the intentional behavior changes (per-file `execution_mode`
literal, fourth "workflow" bucket, `captureTs()` removal); the 5 AC3-named sidecar/tag-scope tests
required zero changes, passing unmodified — confirming the `runCommand()` refactor is behavior-
preserving at the structural level those tests check.

## Files Changed
- `.claude/workflows/create-tickets.js` — backtick escapes (613, 778); `args.start_ts` replaces
  `captureTs()`; new `runCommand()` helper; `writeSidecar`/`clearSidecar`/tag-check rerouted
  through it; `execution_mode:"workflow"`.
- `.claude/skills/create-tickets/SKILL.md` — native `Workflow({scriptPath, args})` as primary,
  hand-translation as documented fallback.
- `docs/ai/skills.md` — reversed the "Workflow tool not available" claim; states what's actually
  ported so far.
- `docs/agent-monitoring/schema.md` — `execution_mode` field row documents the third value.
- `tools/agent-monitoring/generate_retro.py` — execution-mode split gains the "workflow" bucket
  (grouping dict, summary loop, rendered table).
- `tests/tools/test_run_execution_mode_field_wiring.py`,
  `tests/tools/test_generate_retro.py`, `tests/tools/test_step0_ts_orchestrator.py` — updated for
  the intentional behavior changes above.
- `tests/tools/test_workflow_runtime_acorn_parse.py` — new.
- `tickets/backlogs/TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME.md` — dated note (AC8).
- `docs/plans/idea_stale_planning_doc_status_after_ship.md` — new; the real, small proposal the
  pilot ran against.
- `stored_artifacts/TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT/pilot_measurement.md` — new.
- Pilot side effect (real output, not implemented here):
  `tickets/todos/planning-doc-status-drift/TCK-20260930-PLANNING-DOC-STALENESS-DETECTOR.md`.

## Completion Summary
`create-tickets.js` is now the first `.claude/workflows/*.js` script to actually execute on the
native Claude Code `Workflow` tool instead of being LLM-narrated: its acorn-breaking backticks are
fixed, its 4 `bash()` sites are rerouted through a narrow `runCommand()` agent, its timestamp comes
in via `args.start_ts`, and it records `execution_mode:"workflow"` so `generate_retro.py` can tell
native runs apart from hand-narrated ones. One real native pilot run confirmed tool-call
attribution works correctly for every site the sidecar mechanism already covered (the ticket's
open unknown), produced one real, well-formed ticket, and surfaced a quantified "runCommand() tax"
finding that grounds the recommendation: port `implement-epic.js` next (already parses cleanly,
same bounded tax expected), but `implement-ticket.js` needs an explicit per-call-site
gate-vs-bookkeeping classification decision before any porting attempt, not a mechanical repeat of
this same pattern at ~50 sites. Full numbers in `pilot_measurement.md`.

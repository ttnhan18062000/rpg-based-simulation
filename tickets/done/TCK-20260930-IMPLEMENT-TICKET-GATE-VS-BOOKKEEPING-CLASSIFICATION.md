---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION
phase: done
date: 2026-09-30
tags: [ai, agent-monitoring]
---

# TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION

## Title
Classify every `bash()` site in `implement-ticket.js` as gate or bookkeeping before any native port

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
The `create-tickets` pilot found that routing shell through `runCommand()` (an agent) weakens the
orchestrator-side guarantee that an agent never reports "gate passed". `implement-ticket.js` has
about 50 `bash()` sites, most of them gate checks, so a mechanical port is unsafe. Produce the
per-site classification and a decision on each class. This ticket is the decision only; it ports
nothing.

## Scope
1. Enumerate every `bash()` site (`grep -c` shows 50 at the time of filing) with line, purpose,
   and the decision it feeds (blocking verdict, advisory WARN, timestamp, sidecar/monitoring write,
   git/status read).
2. Classify each as **gate** (result decides pass/fail), **advisory** (never blocks), or
   **bookkeeping** (no verdict).
3. For each class, decide the native-port route: stays orchestrator-side, goes through
   `runCommand()` with script-parsed `{exit_code, stdout}` markers, or becomes an `args`-supplied
   value. Record the residual misreport risk for any gate routed through an agent.
4. Measure, don't assume, whether the native runtime offers any non-agent shell path usable for
   gates. Cite the pilot measurement.
5. Output: a classification table in a stored artifact, plus a recommended port sequence as
   follow-up tickets (filed, not folded in).

6. Record the standing parse blocker as a fact the classification starts from: the native `Workflow`
   tool rejects `implement-ticket.js` today (`Script parse error: Unexpected token (182:78)`, a raw
   backtick inside a prompt template literal at line 182; reported by test-architecture-implementer
   on 2026-10-01 and re-checked by reading line 182). `simq-audit.js` is pinned unparseable too in
   `tests/tools/test_workflow_runtime_acorn_parse.py`. List every unescaped backtick site, since
   fixing one may reveal the next. The fix itself ships in the port tickets, not here.
7. The reporter says that parse test also fails on clean main. Reproduce it in an environment that
   has the repo's dependencies and acorn before treating it as fact; it was not reproduced in the
   design worktree (missing `pydantic`).

## Out of Scope
- Porting `implement-ticket.js` or editing it.
- `implement-epic.js` (`TCK-20260930-IMPLEMENT-EPIC-NATIVE-WORKFLOW-PORT`).

## Acceptance Criteria
1. The table covers every `bash(` site; a test or script check confirms the count matches the file.
2. Every row has a class and a route, and every gate-class row states its misreport risk.
3. The non-agent shell path question is answered with evidence.
4. Follow-up port tickets are filed for each route that needs code.

## Related Tickets
- TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT (done; the finding behind this)
- TCK-20260930-IMPLEMENT-EPIC-NATIVE-WORKFLOW-PORT (sibling)
- TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME (backlog parent)

## Related Docs
- `stored_artifacts/TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT/pilot_measurement.md`
- `docs/ai/skills.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT/`

## Related Code Areas
- `.claude/workflows/implement-ticket.js`
- `tools/gate_checks/`

## Assumptions / Open Questions
- Open: is there any non-agent shell path in the native runtime? The pilot suggests not.

## Implementation Notes
**The "50" is a grep over-count.** `grep -c 'bash('` matches 12 comments; there are **38 real call sites** (`tools/workflow_bash_sites.py` counts them; a test fails if the table and the file disagree). Classification (`stored_artifacts/<this ticket>/classification.jsonl` and `.md`): 7 gate, 3 control, 5 input, 12 advisory, 11 bookkeeping; routes: 3 `args`, 20 `runcommand`, 9 `runcommand-attested`, 6 `defer`.

**Measured, not assumed (scope 4; zero-agent probe `wf_df41616a-229`, user opt-in 2026-10-01):** the native script runtime exposes only `log, phase, console, budget, setTimeout, agent, parallel, pipeline, workflow, args` plus plain JS built-ins. There is **no shell, `require`, `process`, `fetch` or `fs`**, so "stays orchestrator-side" is not a route that exists: every command is an `args` value or an agent dispatch. `workflow()` nests one level (parent to child, args pass) and throws inside a child.

**What follows for the gates.** The 7 gate sites (and 2 control/input sites that feed a gate or can silently skip a required step) can only be run by an agent that reports `{exit_code, stdout}`, which an agent can misreport. Per-row misreport risk is recorded; the highest-consequence are the Finalize self-check (a fabricated all-PASS lets a ticket be reported DONE) and the P0 parity scan (a fabricated no-intersection skips a required parity update). Recommended route is attestation a script can verify without trusting prose (design in a follow-up), not plain `runCommand`.

**Cost.** 13 `writeSidecar` and 11 `captureTs` invocations would each become an agent dispatch: about 40 extra dispatches per full-tier ticket versus +4 measured for create-tickets, and the one real native implement-epic run spent 234,551 subagent tokens on 5 agents (4 of them command runners) for a no-op epic, so the dispatch tax is not small in tokens either.

**Scope 6 (standing parse blocker), listed exhaustively:** implement-ticket.js lines **182** and **1753** only (every other backtick parses); simq-audit.js line 475; implement-epic.js line 247 (a regression from after the pilot, fixed by the sibling ticket); create-tickets.js line 855 (same class, added by #267, fixed in this batch).
**Scope 7 (reproduce):** reproduced in an environment with the repo's dependencies and acorn: `test_acorn_parse_status_matches_pilot_recorded_baseline` fails on clean origin/main because of implement-epic.js line 247 and (after #267) create-tickets.js line 855, not because of implement-ticket.js.

**Follow-ups filed** (not folded in): `TCK-20260930-IMPLEMENT-TICKET-PARSE-AND-NONDETERMINISM-FIX`, `TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN`, `TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT` (blocked by the other two).

## Test Summary
`tests/tools/test_implement_ticket_bash_site_classification.py`, 7 tests: row count equals real call sites (not grep matches); comment mentions are not counted; every row has a class, route and risk; gate and attested rows state a real misreport risk; every anchor occurs in the script; gate rows are never routed to plain runcommand or args; the site finder ignores comments and block comments. All pass.

## Files Changed
- `tools/workflow_bash_sites.py` (new), `tests/tools/test_implement_ticket_bash_site_classification.py` (new)
- `stored_artifacts/<this ticket>/` (classification.jsonl/.md, runtime_probe/, plan/investigation/test_plan)
- three follow-up tickets in `tickets/todos/`; this ticket

## Completion Summary
Done, decision only: nothing in implement-ticket.js was edited. AC1: the table covers all 38 call sites and a test pins the count. AC2: every row has a class and route, and every gate row states its misreport risk. AC3: no non-agent shell path exists in the native runtime, with the probe output as evidence. AC4: three follow-up tickets filed for the routes that need code.

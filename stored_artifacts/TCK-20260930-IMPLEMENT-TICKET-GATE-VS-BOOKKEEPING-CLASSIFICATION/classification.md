---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION
artifact_type: report
tags: [ai]
---

# Classification of implement-ticket.js bash() sites

Source: `.claude/workflows/implement-ticket.js` at origin/main `f2d807c35`. `grep -c 'bash('` says 50; **38 are real call
sites** (12 matches are comments). `tools/workflow_bash_sites.py` counts them and `tests/tools/test_implement_ticket_bash_site_classification.py`
fails if this table and the file disagree. Machine-readable table: `classification.json`.

## Summary
| class | sites | meaning |
|---|---|---|
| gate | 7 | result decides pass/fail and returns a blocking status |
| control | 3 | result picks a branch (skip/run, which blocking status) |
| input | 5 | computes a value handed to an agent or to a gate |
| advisory | 12 | warn/log/shadow only, never blocks |
| bookkeeping | 11 | monitoring, sidecar, timestamps, ids, file moves, reindex |

| route | sites | meaning |
|---|---|---|
| args | 3 | a value the caller supplies in `args` (timestamp, execution id) |
| runcommand | 20 | an agent runs the command; the script parses `{exit_code, stdout}` markers, as in the create-tickets pilot |
| runcommand-attested | 9 | gate-shaped: an agent runs it, and the result must be verifiable (design in the follow-up ticket) |
| defer | 6 | shadow-reviewer paths; omit natively, no consequence |

## Native-runtime facts the routes rest on (measured 2026-10-01, `runtime_probe/`)
- The script runtime exposes `log, phase, console, budget, setTimeout, agent, parallel, pipeline, workflow, args` and plain JS
  built-ins. **There is no `bash`, `require`, `process`, `fetch`, `fs` or `child_process`.** So "stays orchestrator-side"
  does not exist as a route: every command is either an `args` value or an agent dispatch.
- `workflow()` works one level (parent to child, args pass through) and **throws inside a child**, so a native
  implement-epic can call a native implement-ticket, but only once implement-ticket itself parses and has no `bash(`.
- Standing parse blocker: implement-ticket.js fails acorn at lines **182** and **1753** (raw backticks in prompt template
  literals); those are the only two (every other backtick parses). `implement-epic.js` also fails today at line 247 (a raw-backtick line added after the pilot; the file was last touched by #265), `simq-audit.js` at 475; the pilot recorded implement-epic as parsing, so that is a regression on main.

## Decisions per class
- **gate (7)**: never `runcommand` alone. A gate routed through an agent can be misreported ("passed" without running). Route
  `runcommand-attested`: the command prints a payload plus an attestation the script can check without trusting prose (candidate: a
  hash over the payload and an `args`-supplied nonce, which an agent cannot produce without running the tool; JS has no crypto, so
  the check is a small inline implementation). Residual risk is stated per row and is the lower bound of what the follow-up must remove.
- **control (3)**: same risk class as a gate when the wrong branch silently skips work (the P0 parity scan is the worst), so routed
  attested where it can skip a required step, plain `runcommand` where a wrong answer only changes which blocking status returns.
- **input (5)**: `runcommand`; failure is visible to the agent that receives it. The `git status` of the parity ledger feeds a gate,
  so it is attested.
- **advisory (12)**: `runcommand` or `defer`; a misreport changes a warning.
- **bookkeeping (11)**: `args` for what can be supplied up front (start timestamp, execution id), `runcommand` otherwise. Cost,
  not safety, is the issue here: 13 `writeSidecar` and 11 `captureTs` invocations would each become an agent dispatch per run.

## Cost
A mechanical port adds roughly one agent dispatch per `runcommand` invocation actually reached. Counting invocations rather than
sites: 13 writeSidecar + 11 captureTs + the gate and advisory calls on the path is about 40 extra dispatches per full-tier ticket
(the pilot measured +4 for create-tickets). Batching (per-phase timestamps stamped by the existing writeMonitoring agent, sidecar writes
folded into the agent they precede) is a design item in the follow-up, not assumed.

## Recommended port sequence (filed as tickets, not folded in)
1. `TCK-20260930-IMPLEMENT-TICKET-PARSE-AND-NONDETERMINISM-FIX`: fix the two backtick sites, remove `Date.now()`, take
   `start_ts`/`execution_id` from `args`; no behavior change.
2. `TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN`: design and prototype attested gate results on one gate; prove or refute
   that an agent cannot forge it.
3. `TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT`: port in this order once 1 and 2 land: advisory and bookkeeping sites, input sites, then
   gates with attestation; includes the dispatch-cost batching decision. Blocked by 1 and 2.

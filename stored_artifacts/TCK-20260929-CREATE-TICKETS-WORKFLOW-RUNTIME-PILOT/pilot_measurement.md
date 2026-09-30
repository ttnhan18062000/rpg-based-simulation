---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT
artifact_type: report
date: 2026-09-30
tags: [workflows, create-tickets, agent-monitoring, process-improvement]
---

# Pilot Measurement — `create-tickets.js` on the Native `Workflow` Tool

One real invocation: `Workflow({scriptPath: '.claude/workflows/create-tickets.js', args: {source:
'docs/plans/idea_stale_planning_doc_status_after_ship.md', start_ts: '2026-09-30T02:59:58Z'}})`,
run ID `wf_a1e1ba90-01a`. Compared against the hand-narrated baseline `CREATE-TICKETS-DOCS-PLANS-
SCRIPTS-TOOLS-GOVERNANCE-EPIC` (`agent-monitoring/data/2026-W40/`, DONE, 9 events — the hand run
skipped the write-sequence and link agents per its own record, though in fact it did run both;
see below).

The two runs are not perfectly matched (baseline: 3 concerns → 2 tickets, `write-sequence` +
`Link` ran, epic-linked; pilot: 1 concern → 1 ticket, no intra-batch deps so no
`write-sequence`, no `epic_id` so no `Link`) — noted throughout rather than glossed over.

## 1. Total tokens / cost_proxy_score

| | Baseline (hand-narrated) | Pilot (native `Workflow`) |
|---|---|---|
| Real token count | Not recorded by this monitoring system (`docs/agent-monitoring/schema.md`: "Token counts are not recorded") | **535,634** — reported directly by the `Workflow` tool's own usage block (`subagent_tokens`). This is strictly better introspection than pipeline-mode ever had. |
| `cost_proxy_score` (tool-call-weighted proxy) | 406.752 (summed across 9 events) | 42.809 (summed across 4 events) |
| `tool_call_count` (summed across events) | 111 | 40 |
| Real `tool_uses` (harness-reported, all 9 agents) | n/a (not reported this way for hand-narration) | 54 |
| `agent_count` | 9 | 9 (harness) / 4 (pushEvent'd — see §4) |

`cost_proxy_score`/`tool_call_count` are **not directly comparable** between the two runs as an
efficiency ratio — the pilot did genuinely less work (1 concern vs. 3, no write-sequence, no
link). The one number that *is* directly informative on its own: 535,634 real tokens were spent
on this run, and essentially none of them reached the orchestrating session's own context (§2).

## 2. Main-session context consumed

**Qualitative result, not a token count, and this is the real headline finding.** Hand-narration
(baseline) means the orchestrating LLM turn itself performs every `Agent()`/`Bash()` call in the
JS's translation and receives every result directly into its own context — the full text of every
comprehend/investigate/structure/write dispatch and response lives in that session's transcript.
The native pilot's orchestrating turn made exactly one tool call (`Workflow({scriptPath, args})`),
which returned immediately with a task ID, and the *only* thing that later entered this session's
context was a compact JSON result (`{"status":"DONE","output_folder":...,"ticket_count":1,...}`)
plus a small diagnostics/usage block — not any of the 9 subagents' actual work. The 535,634 real
tokens above were spent entirely in isolated subagent turns this session never saw.

This is the single clearest efficiency win the native tool offers for this class of work, and it
holds regardless of how the raw token/cost_proxy_score numbers compare.

## 3. Step fidelity

Every phase that should have run, ran; nothing was silently skipped:

| Phase | Baseline | Pilot |
|---|---|---|
| Comprehend | ran | ran |
| Investigate | ran ×3 (3 concerns) | ran ×1 (1 concern) |
| Structure | ran | ran |
| Write | ran ×2 (2 tickets) + `write-sequence` (intra-batch dep detected) | ran ×1 (1 ticket), no `write-sequence` (no intra-batch dep — correct, not a bug) |
| Link | ran (epic_id given) | did not run (no epic_id given — correct, not a bug) |

Both runs correctly exercised the conditional logic (write-sequence only when deps exist, Link
only when `epic_id` is passed) rather than one of them silently omitting a step it should have run.

## 4. Tool-call attribution — the pilot's open unknown, now answered

**Answer: yes, workflow subagents' tool calls land in `tools.jsonl` correctly attributed to the
run, for every call site this file's sidecar mechanism was already designed to cover — no new gap,
no special-casing needed.**

Direct evidence, from `agent-monitoring/data/2026-W40/create-tickets-workflow-pilot.tools.jsonl`:

- Every row in the shard — this session's own prior tool calls *and* every one of the workflow's
  9 subagents' tool calls — carries the **same** `session_id`
  (`a8fa23b8-d880-43d7-bd06-33f638fd3a71`). This directly answers the ticket's "Sidecar session
  scope" open question: `$CLAUDE_CODE_SESSION_ID` inside a native workflow subagent's own shell
  **is** the same session_id hook payloads carry for the orchestrating session. No divergence.
- 40 rows are attributed to the pilot's own `run_id`
  (`CREATE-TICKETS-DOCS-PLANS-IDEA-STALE-PLANNING-DOC-STATUS-AFTER-SHIP`), split 27
  (`comprehend`) + 13 (`structure`) — an **exact** match to the `tool_call_count` values
  (27 and 13) recorded in `create-tickets-workflow-pilot.events.jsonl`. The sidecar correctly
  switched from this session's own prior value to the workflow's value at the right moment, and
  correctly re-attributed as the workflow moved from Comprehend into Structure.
- 21 rows carry `run_id: null` / `agent: null` — matching the file's own **pre-existing, by-design
  exclusion** of `Investigate`'s and `Write`'s pipeline fan-out sites, the `runCommand()`-wrapped
  plumbing calls (`writeSidecar`/`clearSidecar`/tag-check), and `writeMonitoring`'s own call —
  the exact same set excluded before this pilot, now confirmed to still be excluded (not newly
  broken) under native execution. Some of these 21 rows are also this session's own tool calls
  made *after* the workflow's `clearSidecar()` blanked the sidecar and before this session
  re-established its own — a real, actionable finding: **an orchestrating session must
  re-establish its own sidecar after a native workflow run completes**, or its own subsequent
  tool calls go unattributed too. Done for this session (`.claude/current_run` rewritten,
  seq 2, immediately after reading the completion notification).

`execution_mode: "workflow"` was written correctly in the resulting run record
(`create-tickets-workflow-pilot.runs.jsonl`) — confirmed by direct read, not assumed from the code.

## 5. Real output (not synthetic)

The pilot ran against a genuinely real, small, previously-unticketed proposal —
`docs/plans/idea_stale_planning_doc_status_after_ship.md` — found while checking two other
candidate proposals and discovering both were already fully shipped (itself the finding the piloted
proposal is about: `idea_agent_monitoring_active_duration.md` and `standalone_items.md` items 3–4
both still claim open/ready status for work that shipped weeks ago). The pilot produced one real,
well-formed ticket: `tickets/todos/planning-doc-status-drift/TCK-20260930-PLANNING-DOC-STALENESS-DETECTOR.md`
— correctly scoped as report-only/advisory, correctly found two real existing precedents
(`tools/gate_checks/doc_staleness_check.py`, `tools/agent-monitoring/epic_staleness_check.py`) to
model the new detector on, and correctly flagged both open design questions from the source doc as
required Acceptance Criteria rather than silently picking an answer. This ticket is left in
`tickets/todos/` for a future batch, not implemented here (out of this ticket's scope).

## 6. Real, incidental finding: shared-worktree test runs fold other sessions' monitoring shards

Running the full test suite (specifically `test_generate_retro.py`'s real-corpus tests) as part of
this ticket's own verification folded 10 *other* sessions' pending per-branch monitoring shards
into the canonical week files and deleted the originals — a known, previously-documented trap
(`.claude/handover/agent-working-design.md`'s "Traps" section). Restored via `git checkout --`;
their content was already safely folded into the canonical files, so nothing was lost. Noted here
because it will recur for whoever next runs this same test file in this shared worktree, and the
fix (`git checkout --` the deleted per-branch shard paths, leave the canonical files' fold in
place) is quick once you know to look for it.

## 7. Acorn parse status — all `.claude/workflows/*.js`

Checked with `frontend/node_modules/acorn` (v8.15.0), `{ecmaVersion: 'latest', sourceType:
'module', allowReturnOutsideFunction: true, allowAwaitOutsideFunction: true}` — the exact options
the native runtime itself uses:

| File | Status |
|---|---|
| `create-tickets.js` | **OK** (fixed by this ticket — was `FAIL (613:10)`) |
| `implement-epic.js` | OK (already parsed cleanly, untouched) |
| `implement-ticket.js` | **FAIL** `(182:78)` — same nested-backtick defect class, unfixed |
| `simq-audit.js` | **FAIL** `(475:78)` — same defect class, unfixed |
| `compact-simulation-result.js` | OK |
| `generate-simulation-setup.js` | OK |
| `investigate-simulation-result.js` | OK |
| `prepare-simulation-execution.js` | OK |
| `propose-simulation-enhancements.js` | OK |
| `register-simulation-result.js` | OK |
| `update-knowledge-store.js` | OK |

## 8. A cost the pilot surfaced that the ticket didn't anticipate in these terms: the `runCommand()` tax

The harness reports **9** total `agent()` dispatches for this run, but only **4** are
`pushEvent()`-tracked "real work" phases (comprehend, investigate:C1, structure, write:<ticket>).
The other 5 are: `writeMonitoring`'s own always-existing bookkeeping agent (1, pre-existing, not
new), plus **4 new `runCommand()`-wrapped dispatches** this ticket introduced
(`writeSidecar:Comprehend`, `writeSidecar:Structure`, `clearSidecar`, the tag-registry check) —
each one a full agent dispatch replacing what used to be a free, instant `bash()` call.

For `create-tickets.js`, with only 4 real `bash()` call *sites* (`writeSidecar`/`clearSidecar`/tag-
check, `captureTs` removed entirely), this tax is small and bounded: at most 4 extra dispatches per
run, regardless of batch size (writeSidecar's 4 *invocations* don't all fire in a small single-
ticket run — only the sites the run's own control flow actually reaches do).

**This does not extend safely to `implement-ticket.js`.** That file has **~50** `bash()` sites —
mechanically applying the same pattern would add up to ~50 extra agent dispatches to a single
ticket's implementation run, not 4. That is the concrete, quantified shape of "the pilot's own
recommendation must treat implement-ticket.js's gate layer as the central decision" the ticket's
Assumptions section asks for — it is not just an architectural-purity concern (agents self-
reporting gate results), it is also a real, large multiplication of agent-dispatch count and real
token spend for the file where that matters most.

## 9. Recommendation

### `implement-epic.js` — **GO**, with conditions
Already parses cleanly under acorn (no backtick fix needed) and has no `Date.now()`/
`Math.random()`/argless `new Date()` issue. Has 11 `bash()` sites and an existing `writeSidecar`
mechanism (added by `TCK-20260904-COST-PROXY-EPIC-TICKETS`, same shape as `create-tickets.js`'s),
so the `runCommand()` pattern piloted here should port with the same shape and the same small,
bounded tax. Before porting: explicitly verify (don't assume from this pilot) that none of
`implement-epic.js`'s 11 `bash()` sites produce a pass/fail gate verdict — if any do, treat them
under the same caution as `implement-ticket.js`'s gate layer below, not as safe-by-default because
`create-tickets.js`'s own 4 sites happened to be safe.

### `implement-ticket.js` — **NO-GO for a mechanical same-pattern port; needs an explicit design decision first**
Two independent blockers, not one:
1. **Syntax**: still fails acorn parse (line 182, plus a second site at 1753 per the ticket's own
   pre-investigation) — same backtick-escaping fix as this ticket made, straightforward on its own.
2. **Architecture**: ~50 `bash()` sites, most of them the orchestrator-side gate layer (Verify/
   Parity/Security-Review/etc.) that exists specifically so an agent can never itself report "gate
   passed." Routing those through `runCommand()` means an agent executes the gate check and
   *reports* the result — the same mechanism this pilot used safely for sidecar bookkeeping and one
   tag filter, but at a scale (~50 sites) and a risk class (real pass/fail verdicts, not
   bookkeeping) where a misreporting agent has real consequences: a broken ticket could close.

**Recommended next step, not a straight go/no-go**: a dedicated classification pass over
`implement-ticket.js`'s ~50 `bash()` sites, sorting each into (a) pure bookkeeping/plumbing —
safe for the same `runCommand()` pattern piloted here, and (b) gate-verdict-producing — needs a
different, stricter design (e.g. a schema-validated `agent()` call whose result is cross-checked
against an independent signal, or deferring native execution for just those sites until such a
design exists) before any of (b) is ported. Do not attempt a full mechanical port in one pass.
Also fix the 1 `Date.now()`/`new Date()` use with the same `args`-supplied-timestamp pattern this
ticket used for `start_ts`, independent of the gate-layer decision.

## Recorded per AC8
`TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME` (backlog) updated with a dated note confirming its
first Acceptance Criterion (an in-harness execution surface exists) is now satisfied, pointing
here. It stays in `tickets/backlogs/` — this measurement does not itself decide whether/when to
port the remaining files; that's the next pickup's call, now informed by real numbers instead of
"unknown."

---
status: idea
layer: ai
authority: P2
audience: developer
maturity: scheduled
date: 2026-07-10
tags: [idea, agent-infrastructure, observability, determinism, data-quality]
---

# Idea: Compute Bookkeeping at the Source — Stop Trusting Agent Prompts to Remember It

> **Maturity: SCHEDULED.** Raised 2026-07-10 during a review of the `implement-ticket` pipeline and
> agent-monitoring process, reproduced live in the same session (see Problem below) while running
> `TCK-20260710-SECURITY-REVIEWER-AGENT-DOC`. Scheduled 2026-07-10 under
> [`TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC`](../../../tickets/todos/agent-bookkeeping-determinism/TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC.md),
> tracking three child tickets that cover only the concrete core of this doc (the "Where this pattern
> already shows up" table) — `TCK-20260710-CURRENT-RUN-SIDECAR-BASH` (sidecar registration),
> `TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH` (per-phase `ts` capture), and
> `TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT` (`verified_by` enforcement). The 4 "related, smaller
> ideas" below remain unscheduled by deliberate scope decision, not oversight.

---

## Problem

`TCK-20260709-AGENT-MONITORING-DURATION` already diagnosed and fixed one instance of a general
failure mode: `duration_s` was documented as a required run-record field but was never actually
computed, because every call site (`implement-ticket.js`, `implement-epic.js`, `create-tickets.js`,
manual `record_run.py --data` invocations) was expected to compute and pass it itself, and none of
them did. The fix moved the computation into `record_run.py` itself, at write time, so it can no
longer be "forgotten" by a caller.

The same failure mode still exists, unfixed, one layer up — in how `tool_call_count` and
`cost_proxy_score` get attributed to an agent event. Per
`docs/agent-monitoring/schema.md`'s "How tool calls are attributed to agent events": *"Each agent
prompt includes an early Bash step that writes `{"run_id": "...", "seq": N}` to
`.claude/current_run`."* This is a free-text instruction embedded in every agent-call prompt
(`implement-ticket.js`'s "Step 0b" blocks) — the orchestrator constructs the exact bash command as a
string and asks the agent to run it as its first action, verbatim, every single time.

This was reproduced live, not hypothetically: while manually orchestrating
`TCK-20260710-SECURITY-REVIEWER-AGENT-DOC` in this same session, the Step 0b sidecar-registration
instruction was omitted from every one of the 5 agent prompts issued (`ticket-scoper`,
`implementer`, `test-scoper`, `done-checker` ×2). The result: querying `tools.jsonl` for that
run's `tool_call_count`/`cost_proxy_score` at Finalize returned `{"counts": {}, "scores": {}}` —
completely empty, silently, with no error and no warning anywhere in the pipeline. Every event for
that run was written with `tool_call_count: 0, cost_proxy_score: 0.0`, indistinguishable in the
data from "this agent genuinely made zero tool calls." This is exactly the same shape of bug
`duration_s` had — a field whose correctness depends on a caller (here, an LLM agent, not even a
deterministic JS call site) remembering to do something mechanical — just one layer further from
the orchestrator and therefore even less reliable.

---

## Idea

**General principle:** any monitoring/bookkeeping field whose correctness depends on an agent's
prompt text including a specific mechanical instruction — and the agent actually executing it,
literally, before doing anything else — is the same anti-pattern `TCK-20260709-AGENT-MONITORING-DURATION`
already rejected for one field. Treat it as a systemic property of the whole `agent-monitoring/`
write path, not a queue of field-by-field fixes discovered one retro at a time.

**Concrete fix for the reproduced instance:** move `.claude/current_run` sidecar registration out
of agent prompt text entirely. The orchestrator (`implement-ticket.js`) already knows `run_id` and
the upcoming `seq` (`events.length + 1`) at the exact point it constructs each `agent()` call — there
is no information in the Step 0b prompt text that the orchestrator doesn't already have. Write the
sidecar via `bash()` immediately before each `agent()` call, the same way the Parity phase's
`p0ScanOutput` and Architecture-Verify's static pre-check already run orchestrator-side `bash()`
calls ahead of their agent invocations. This removes the dependency on an LLM correctly reproducing
a copy-pasted bash snippet as a literal first action, for every one of the ~9 agent-call sites across
`implement-ticket.js` (and the mirrored pattern in `implement-epic.js`/`create-tickets.js`).

**Broader ask:** audit every `Step 0`/`Step 0b` block in these workflow files for content that is
pure mechanical side-effect (timestamp capture, sidecar write, file existence check) with zero
judgment content, and move each one to an orchestrator-side `bash()` call. Reserve agent prompts for
steps that actually require reading code/docs and exercising judgment — that's the resource an LLM
call is for; a `date -u` capture or a JSON sidecar write isn't.

### Where this pattern already shows up

| Site | Current mechanism | Risk |
|---|---|---|
| `duration_s` (run record) | **Fixed** — `record_run.py` computes it at write time from `start_ts`/`end_ts` | None — resolved by `TCK-20260709-AGENT-MONITORING-DURATION` |
| `tool_call_count` / `cost_proxy_score` (event record) | Agent prompt "Step 0b" bash snippet, run by the agent itself | **Reproduced this session** — silently zeroes for the whole run if any single agent call skips it; indistinguishable from a genuine zero-tool-call event |
| Per-phase `ts` fields | Agent prompt "Step 0" (`date -u ...`), agent must echo it back as the first line of its response | Same class, lower stakes today (used for display/ordering, not scored) — but `generate_retro.py`'s Slow Runs / Avg Duration sections read `runs.jsonl`'s `duration_s`, not these, so the blast radius is currently smaller |
| `verified_by` provenance field (architecture-reviewer, done-checker, parity-updater, mechanics-auditor) | Agent self-reports whether its verdict came from a static script or independent judgment | Compliance depends on the agent actually running and honestly citing the static check — `docs/ai/agents.md`'s `mechanics-auditor` entry explicitly admits *"this Step 0 has no orchestrator-side enforcement... compliance depends entirely on the agent actually running the script and citing it honestly"* |

---

## Related, smaller ideas raised in the same review (not written up separately yet)

Named here for traceability; each would need its own investigation before becoming a ticket:

1. **Asymmetric gate coverage.** Only the `security` tag has an enforced pipeline gate
   (`Security-Review` / `SECURITY_BLOCKED`). `api-design`, `debugging`, `performance` map to
   `suggested_skills` but nothing checks whether the suggested skill was actually followed —
   `docs/agent-monitoring/schema.md`'s retro-report section calls this "deliberately asymmetric."
   The `security-reviewer` pattern is a proven, cheap-to-replicate template.
2. **Cross-retro trend detection.** Each `RETRO-<week>.md` is an independent snapshot with
   hand-written Notes; nothing automatically compares consecutive reports to flag a drifting DONE
   rate or a rising per-agent failure rate.
3. **Duplicated tag→skill mapping logic.** The tag→skill table is independently re-implemented in
   at least 4 places in `implement-ticket.js` alone (`ticket-scoper`'s two Scope-phase branches, the
   `mistag_warning` check) — `implement-ticket.js`'s own inline comment flags this
   ("`mistag_warning` is a 4th place in this file independently computing tag-related logic").
   A single source-of-truth module (mirroring what `tools/agent-monitoring/vocabulary.py` already
   does for phase/agent names) would remove the drift risk.
4. **`working_log.csv` malformed-row normalization.** Explicitly named-but-not-created as a
   follow-up by `TCK-20260705-WORKING-LOG-BACKFILL`: 83 non-canonical rows across 7 distinct
   column-count shapes, currently permanently excluded from `validate.py`'s cross-check via
   documented allowlists rather than actually cleaned up.

---

## Natural Integration Points

| Existing component | How this idea attaches |
|---|---|
| `.claude/workflows/implement-ticket.js` | Every `agent()` call site currently embeds a "Step 0b" sidecar-write instruction in its prompt string — replace with a `bash()` call issued by the orchestrator immediately before `agent()`, mirroring the existing `p0ScanOutput`/`archCheckOutput` pattern already used ahead of the Parity and Architecture-Verify agent calls |
| `.claude/workflows/implement-epic.js`, `create-tickets.js` | Same pattern, if/where they register their own sidecar (per `docs/agent-monitoring/schema.md`, `create-tickets` currently does not register a sidecar at all, so `tool_call_count` is always `null` there — worth confirming whether that's intentional or the same gap by omission) |
| `tools/agent-monitoring/record_events.py` | No change needed — it already accepts `tool_call_count`/`cost_proxy_score` as passed; the fix is entirely about *how reliably* the orchestrator can compute correct values before calling it |
| `idea_agent_monitoring_schema_enforcement.md` (sibling, SHIPPED) | Same underlying principle — that idea made drifted *values* visible at write time; this idea is about making an entire *category* of field (agent-dependent mechanical bookkeeping) unable to silently go missing in the first place |
| `docs/ai/agents.md` → `mechanics-auditor` entry | Already documents the weakest instance of this pattern (no orchestrator enforcement of Step 0 compliance) — a natural first candidate to extend if this idea is scheduled |

---

## Open Questions

- Is there any Step 0/0b content that genuinely needs the *agent's own* timestamp (e.g. capturing
  the moment the agent actually began reasoning, not just when the orchestrator dispatched the
  call) — or can every current instance be replaced by an orchestrator-side capture without losing
  meaning?
- For `create-tickets.js`'s already-`null` `tool_call_count`: is that a deliberate scope decision
  (documented as such in `schema.md`) or simply the same gap this idea describes, never fixed there
  because no one hit it the way this session hit the `implement-ticket` case?
- Should the four "related, smaller ideas" above be split into their own `idea_*.md` files before
  any of them is scheduled, following this folder's one-idea-per-file convention — or is a single
  combined follow-up ticket sufficient given none of them, on its own, is large?

---

*Raised: 2026-07-10, during a review of the agent-monitoring/implement-ticket process
(`docs/guides/agent_monitoring.md`, `docs/agent-monitoring/schema.md`, `docs/ai/ticket-lifecycle.md`,
`docs/ai/agents.md`) and confirmed live while manually executing
`TCK-20260710-SECURITY-REVIEWER-AGENT-DOC` in the same session. Not yet scoped as a ticket.*

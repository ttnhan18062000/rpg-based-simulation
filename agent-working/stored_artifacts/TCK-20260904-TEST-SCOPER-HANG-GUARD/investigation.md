---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-TEST-SCOPER-HANG-GUARD
artifact_type: investigation
tags: [testing, ai, hooks, debugging]
---

# Investigation — TCK-20260904-TEST-SCOPER-HANG-GUARD

## Current Behavior

### `.claude/settings.json` (this repo's real, currently-enabled hook surface)
Lines 54-132: `hooks` has exactly two top-level event keys, `PreToolUse` (4 matcher groups) and
`PostToolUse` (4 matcher groups). No `Stop`, `SubagentStop`, or any other event key is present.
Every wired hook is **advisory-only**: each `command` either writes monitoring data
(`pre_tool_hook.py`, `post_tool_hook.py`) or emits `additionalContext` nudges (graphify/context-
search reminders, sidecar-check warning, retro/staleness nudges). None of the four existing
matcher groups ever return a blocking decision — confirmed by reading every `command` string in
the file and by `epic_staleness_check.py`'s own module docstring ("Advisory only... Never mutates
a ticket file, never raises past its own entry points, never blocks a tool call").

### `agent-orchestration/hook-events.yaml` and `agent-orchestration/hook-surface-policy.yaml`
`hook-events.yaml`'s header comment is explicit: "Normalizes exactly the two hook types actually
wired in `.claude/settings.json` today. No speculative SessionStart/Stop/other hook type — this
file documents the real, current vocabulary only." `hook-surface-policy.yaml` (shipped by
`TCK-20260730-PROVIDER-HOOK-POLICY`) states `providers.claude.enabled_events: [PreToolUse,
PostToolUse]` — **this is a statement about what this project's committed config currently
enables, not a claim about what Claude Code as a product supports.** That prior ticket's own
investigation explicitly flagged the open question it left unresolved: "no `docs/ai/
claude_capability_matrix.md` or equivalent was found... Claude Code's real product surface is
known to expose more hook types than `PreToolUse`/`PostToolUse` in general, e.g. `Stop`,
`SessionStart`, `Notification` — but none of those are evidenced or wired in *this repo's*
`.claude/settings.json`" (`stored_artifacts/TCK-20260730-PROVIDER-HOOK-POLICY/investigation.md`,
"Risks and Open Questions"). This ticket resolves that exact open question for `Stop`/
`SubagentStop` specifically, below.

### `tools/agent-monitoring/pre_tool_hook.py` / `post_tool_hook.py` (existing hook-script pattern)
Both are top-level scripts (not importable modules — `sys.stdin` is read unconditionally at
import time), invoked by Claude Code as a subprocess with the tool-call JSON payload piped to
stdin. `pre_tool_hook.py` (19 lines) writes a start-timestamp/session-id sidecar file. `post_tool_
hook.py` (165 lines) reads the sidecar, appends a JSONL record under `agent-monitoring/data/
<ISO-week>/tools.jsonl` via a file-locked writer, and is wrapped end-to-end in a bare
`try/except: pass` so any internal failure fails silently rather than blocking the tool call —
the load-bearing convention every hook script in this repo follows (`retro_nudge_hook.py`,
`epic_staleness_check.py` documented identically). Any new hook script this ticket's Plan/
Implement phase adds should follow this exact shape: stdin JSON in, `try/except: pass` around
all logic, structured JSON (or a bare exit code) out.

### `.claude/agents/test-scoper.md` (current mitigation — prose only)
Lines 126-128, `## Background Commands` section (verbatim): "Never end your turn while a
`run_in_background` Bash command you started (e.g. the scoped `pytest` run above) is still
running. Either run it in the foreground, or poll for its own completion within the same turn
before returning control. You are not auto-resumed the way the top-level orchestrator is." This
exact wording (originating in `implementer.md`) was propagated verbatim to 14 more of the 16
`.claude/agents/*.md` files by `TCK-20260902-AGENT-BACKGROUND-TASK-TURN-END-DEFENSE-IN-DEPTH`
(done 2026-09-02) — **and that ticket's own Completion Summary states this propagation "does not
by itself guarantee the underlying recurrence... is fully prevented," and its Related Docs/
motivation directly cites a 4th real recurrence observed on `test-scoper.md` even though the
prose warning was already present there.** `docs/plans/agent_infrastructure/ai_first_hardening_
epics/guardrail_enforcement_epic.md` (M3) restates this as this ticket's direct motivation and
sets an explicit invariant: "Any rule promoted into this epic because of repeated prose-only
failure must gain a deterministic enforcement or verification mechanism where technically
feasible... Rewriting the prose more strongly is not a fix for a failure class that prose has
already been proven not to prevent."

## Feasibility Finding — Stop/SubagentStop Hook (the ticket's central question)

**Answer: Stop and SubagentStop are real, currently-documented Claude Code hook events that CAN
block a turn/subagent from ending — but no documented payload field from any Claude Code hook
event exposes live liveness state of a `run_in_background` Bash command. A real deterministic
guard is feasible, but only via a transcript-derived proxy signal, not via a direct "is it still
running" field — and that proxy is currently unverified by direct experiment in this repo.**

This corrects a wrong first-pass finding. A `claude-code-guide` sub-agent dispatched during this
investigation initially concluded "Stop/SubagentStop exist only in Codex, not Claude Code,"
reasoning entirely from this repo's own `hook-surface-policy.yaml`/`codex_capability_matrix.md` —
which document what this *project* enables and what *Codex* documents, respectively, neither of
which is authoritative on what the *Claude Code product* itself supports. That sub-agent's own
WebFetch attempts failed (`self signed certificate` — the same Fortinet/Fortiguard-class sandbox
TLS-interception issue CLAUDE.md's own CI-Failure-Triage section already documents), so it never
actually reached Claude Code's official docs. This investigation re-ran the research directly:

- **`WebSearch` (worked)**: "Claude Code converts a Stop hook to SubagentStop, the event it
  fires when a subagent completes... Stop and SubagentStop fire at the end of the turn."
  `stop_hook_active` is a documented boolean field, "true when the subagent is already continuing
  as a result of a stop hook" (loop-prevention, same purpose as Codex's own field of the same
  name per `codex_capability_matrix.md`). Events running inside a subagent add `agent_id` and
  `agent_type` to the payload.
- **`WebFetch https://code.claude.com/docs/en/hooks` (worked — different host than the blocked
  `docs.claude.com`)**: confirms `Stop` and `SubagentStop` as two of a documented ~32-event
  vocabulary (also includes `SessionStart`, `PreToolUse`, `PermissionRequest`, `PostToolUse`,
  `Notification`, `SubagentStart`, `PreCompact`, `PostCompact`, and others this repo's committed
  config does not use). Common input fields: `session_id`, `prompt_id`, `transcript_path`, `cwd`,
  `permission_mode`, `effort`, `hook_event_name`, plus `agent_id`/`agent_type` when firing inside
  a subagent. A worked `PreToolUse` example shows `tool_input.run_in_background` as a field
  **echoed on the Bash tool call itself, recorded at invocation time** — not a live status flag.
- **Exit-code table (direct quote from the fetch)**: `Stop` → exit code 2 "Prevents Claude from
  stopping, continues the conversation"; `SubagentStop` → exit code 2 "Prevents the subagent from
  stopping." **Both hook events genuinely support blocking.** This is the deterministic control
  surface AC #2 asks for: an event key that "did not previously exist in this repo's settings.json
  hooks block" and that structurally can prevent (not just flag) the violating turn-end.
- **No liveness field anywhere**: the same fetch, asked directly whether any documented field
  (`shell_id`, a background-task registry, `BashOutput` correlation, or any enumeration of live
  background processes) exists in any hook event's payload, returned: "No such fields are
  documented anywhere in the provided page content... no mechanism to query or enumerate active
  background processes." This matches the ticket's own Assumptions section verbatim: "Detection
  state may only be knowable from harness-internal bookkeeping not exposed via documented stdin
  payload fields."

### The buildable proxy signal (not yet fixture-verified — flagged as the required next step)

Neither Stop nor SubagentStop needs a *live* liveness field to build a real guard, because the
observed failure mode is transcript-derivable rather than process-state-derivable: the pattern
CLAUDE.md's Hard Rule and this ticket's own Acceptance Criteria describe is "a subagent's last
tool action was launching (or polling and finding still-running) a `run_in_background` Bash
call, with no subsequent poll/foreground-wait before the turn ends" — and `transcript_path` (a
documented, real field on every `Stop`/`SubagentStop` payload) is the session's own JSONL tool-
call history. A hook script at `Stop`/`SubagentStop` time can parse that transcript and check:
does the most recent Bash tool_use with `tool_input.run_in_background == true` have a later
`BashOutput`/`Monitor` tool_use whose `tool_response` shows a completed (not still-running)
status? If not, exit 2 (block) with a `systemMessage` telling the agent to poll/wait before
stopping. This requires **no OS process-table inspection and no undocumented field** — only the
already-documented `transcript_path` plus Claude Code's own tool-call recording, which by
necessity already distinguishes a still-running background shell from a completed one (the
`BashOutput`/`Monitor` tools' own contract, per this environment's own tool descriptions, exist
specifically to report that distinction back to the calling agent).

**This is documentation-citation-grade evidence, not direct-experiment-grade** — this repo has no
captured real `Stop`/`SubagentStop` payload fixture and no captured real transcript JSONL shape
for a Bash/`BashOutput`/`Monitor` sequence (unlike Codex's `PostToolUse`, which has both, per
`tests/fixtures/codex_hook_payloads/post_tool_use_stdin_capture.json` and
`stored_artifacts/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE/`). Per this repo's own established
evidentiary standard (that prior ticket's own scratch-first-capture methodology, and
`hook-surface-policy.yaml`'s own `scratch_first_verification` activation prerequisite), Plan/
Implement must not commit to an exact transcript-parsing schema without first running an
isolated scratch-directory experiment (a throwaway hook registered in a scratch `.claude/
settings.json` outside this repo's trust boundary, or — more cheaply — instrumenting a real
`SubagentStop` firing against *this very investigation's own* dispatched sub-agents, since a
`Stop` hook registered for a subagent is automatically treated as `SubagentStop`) to capture:
(a) the real JSON shape of a `SubagentStop` payload in this harness, (b) the real transcript
JSONL entry shape for a `Bash` tool_use with `run_in_background: true` and its corresponding
`BashOutput`/`Monitor` entries, and (c) confirmation that `stop_hook_active` behaves as the
loop-prevention field the docs describe (needed so the guard's own exit-2 retry does not itself
create an infinite Stop→resume→Stop loop for a genuinely-never-finishing background command).

### Conclusion for this ticket's Assumptions/Open Questions

- **Not the documented-fallback case.** A real, wireable, blocking hook event key exists
  (`Stop`/`SubagentStop`), satisfying AC #2's "not previously existing" requirement, and a
  liveness-independent, transcript-derived deterministic check is architecturally sound —
  the fallback format the ticket's Request Summary specifies should **not** be invoked.
- **But Plan/Implement cannot skip the scratch-first fixture capture.** Committing to an exact
  hook script implementation before that capture would repeat the exact mistake
  `TCK-20260730-PROVIDER-HOOK-POLICY`'s own Anti-Drift Hazards warn against for Codex
  ("Do not silently invent Claude's 'available' hook count... fabricating... without a citation
  would repeat exactly the mistake this ticket exists to prevent"). This ticket's own
  investigation is documentation-citation-grade only; the fixture-capture step is a hard
  prerequisite for Plan, not optional polish.
- **`.claude/settings.json`'s hooks block is a real multi-ticket edit collision point**, per this
  ticket's own Assumptions — `TCK-20260904-BASH-SECRET-SCAN-HOOK` (same batch) is also expected
  to touch this file's `hooks` key. Adding a new top-level `SubagentStop` (and/or `Stop`) key is
  additive relative to the existing `PreToolUse`/`PostToolUse` keys and should not structurally
  conflict, but Plan should sequence the two edits as a single coordinated merge, not two
  independent unreviewed writes to the same JSON block.

## Mechanics / Engine Constraints

None. This ticket touches agent-infrastructure tooling (`.claude/agents/`, `.claude/settings.json`,
`tools/agent-monitoring/`) entirely outside `src/` simulation code. No `docs/mechanics/` chapter
or `docs/engine/` contract governs this area — same conclusion the prior, closely-related
`TCK-20260730-PROVIDER-HOOK-POLICY` investigation reached for the sibling hook-policy ticket.

## Docs Requiring Update

- `docs/plans/agent_infrastructure/ai_first_hardening_epics/guardrail_enforcement_epic.md`: this
  epic doc's M3 section and "Acceptance signal for this epic" both explicitly gate M3's
  completion on this ticket's outcome ("the background-hang guard is a real deterministic
  hook/state-check... If implementation genuinely cannot achieve deterministic detection, the
  documented fallback format... exists in this doc before M3 is considered complete"). Whichever
  way Plan/Implement lands (real hook shipped, or fallback invoked after the fixture-capture
  spike proves it genuinely infeasible), this doc's M3 status must be updated to record the
  actual outcome — it is currently written as an open milestone awaiting exactly this ticket.

The `docs/ai/codex_capability_matrix.md` doc (path: `docs/ai/codex_capability_matrix.md`, under
`docs/`) is not required to change for this ticket: it documents Codex's hook surface, a
different provider from the one this ticket investigates, and this ticket's findings about
Claude Code's own `Stop`/`SubagentStop` support are new content this ticket's own investigation
and any resulting implementation notes carry — not a correction to that doc's existing Codex-
scoped claims, which remain accurate for Codex.

A `docs/ai/claude_capability_matrix.md` (the Claude-side sibling of the Codex capability matrix,
an open question `TCK-20260730-PROVIDER-HOOK-POLICY`'s own investigation explicitly left
unresolved) is not created by this ticket: producing a full, evidenced capability matrix for
Claude Code's entire ~32-event hook surface (mirroring the Codex matrix's rigor) is a
substantially larger, separate scope than this ticket's narrow test-scoper-hang-guard goal, and
would duplicate/preempt that other ticket's own deferred work rather than being a natural
byproduct of this one. This ticket's own investigation only evidences the two events (`Stop`,
`SubagentStop`) it actually needs.

`agent-orchestration/hook-events.yaml` and `agent-orchestration/hook-surface-policy.yaml` are not
under `docs/` (they live at repo root), so they fall outside this section's docs-bullet mechanism
by definition — but Plan should be aware that if a `Stop`/`SubagentStop` hook is actually wired
into `.claude/settings.json`, `hook-events.yaml`'s normalized-vocabulary list and `hook-surface-
policy.yaml`'s `providers.claude.enabled_events` list both become stale the moment that happens
(both currently hard-pin `{PreToolUse, PostToolUse}` via `test_hook_events_yaml_unchanged_
normalized_vocabulary` and `test_policy_represents_claude_two_enabled_events` in
`tests/agent_orchestration/test_contract_structure.py`). Updating those two non-`docs/` files (and
their pinned tests) is real follow-on work this ticket's implementation must account for even
though it is not tracked through this section's docs-bullet mechanism.

## Parity Ledger Overlap

**None.** Grepped all `docs/parity_ledger/*.yaml` for "hook" and "test-scoper"/"run_in_background"
— the only hits are existing `infrastructure.yaml` entries about the already-shipped `PreToolUse`/
`PostToolUse` monitoring writers (`post_tool_hook.py` sidecar-attribution entries, e.g. lines
5634-5679), none of which this ticket modifies (Out of Scope explicitly excludes changing the
existing hook writers beyond pattern reuse). No `docs/parity_ledger/` entry needs to be added —
this is agent-workflow tooling, outside the Parity Ledger's documented simulation-subsystem scope
(same conclusion `TCK-20260730-PROVIDER-HOOK-POLICY`'s own investigation reached for the same
reason).

## Prior Work

- `stored_artifacts/TCK-20260730-PROVIDER-HOOK-POLICY/` — sibling investigation that established
  `hook-events.yaml`/`hook-surface-policy.yaml`'s narrow-scope-by-design policy and explicitly
  left open the question this ticket resolves ("Claude Code's real product surface is known to
  expose more hook types... but none of those are evidenced or wired in this repo's
  `.claude/settings.json`"). Its `loader.py`/`generator.py`/contract-file wiring pattern (fixed
  6-step, now 7-step, sequence) is the precedent for adding any new contract-governed file.
- `tickets/done/TCK-20260902-AGENT-BACKGROUND-TASK-TURN-END-DEFENSE-IN-DEPTH.md` — the immediate
  predecessor hotfix. Its own Completion Summary and Assumptions explicitly anticipate this
  ticket's premise: propagating prose alone "does not by itself guarantee the underlying
  recurrence... is fully prevented... that remains a product-level consideration outside this
  repository's control surface" — this investigation's finding (a real Stop/SubagentStop hook
  IS wireable) means the "product-level" framing was too pessimistic; the control surface exists,
  it was simply never wired.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/guardrail_enforcement_epic.md` (M3) —
  the epic this ticket implements a milestone of; its stated invariant ("deterministic
  enforcement... where technically feasible... rewriting the prose more strongly is not a fix")
  is directly satisfied by this investigation's YES finding.
- `tests/tools/test_post_tool_hook.py` / `test_retro_nudge_hook.py` — the established test
  pattern for driving a top-level stdin-reading hook script as a subprocess (`subprocess.run`
  with `input=json.dumps(payload)`, asserting on `returncode`/stdout/stderr/side-effect files).
  Any new test for a `Stop`/`SubagentStop` hook script should follow this exact pattern.
- `stored_artifacts/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE/` — the direct-experiment fixture-
  capture methodology (isolated scratch directory, throwaway hook config, real payload captured
  to a committed JSON fixture) this ticket's own recommended next step should mirror for
  `SubagentStop`.

## Risks and Open Questions

- **Open, blocking for Plan/Implement (not this ticket to resolve unilaterally): the exact
  transcript-parsing schema is unverified.** This investigation establishes the *architecture*
  (transcript-derived proxy, not a live-liveness field) is sound and grounded in real documented
  fields, but has not captured a real `SubagentStop` payload or a real transcript JSONL excerpt
  in this environment. Plan must schedule a scratch-first capture experiment as its first
  concrete step, per Prior Work above — do not assume the exact field names/shapes without it.
- **`stop_hook_active` loop-prevention semantics need direct confirmation before the guard blocks
  anything.** If the guard's own exit-2 block re-triggers `Stop` immediately and the background
  command never finishes (or the harness re-fires `Stop` faster than the command can complete),
  an unverified loop-prevention behavior risks turning a helpful guard into an infinite-block
  hang — a worse failure than the one being fixed. This must be verified, not assumed, during the
  fixture-capture spike.
- **Multi-session collision risk on `.claude/settings.json`** — flagged already in the ticket's
  own Assumptions; confirmed real by this investigation's direct read of the file (a single
  shared JSON blob, no per-ticket namespacing). `TCK-20260904-BASH-SECRET-SCAN-HOOK` is the named
  same-batch collision point.
- **Does `SubagentStop`'s `matcher` field support filtering by subagent/agent type in
  `.claude/settings.json` the way `PreToolUse`'s matcher filters by tool name?** Not confirmed
  either way by the two fetches performed here (the Codex-side capability matrix documents
  subagent-type matcher support for Codex's `SubagentStop`, but that is not evidence for Claude
  Code's own matcher semantics). If unsupported, the guard must filter by `agent_type` inside the
  hook script body itself (matching every existing hook in this repo's own convention of
  branching on parsed stdin content rather than relying on settings.json's matcher) rather than
  narrowing via the settings.json matcher field — this changes AC's framing of "test-scoper-
  shaped" from a config-level filter to a script-level one, worth a plan-level decision, not a
  blocker.

## Anti-Drift Hazards

- **Do not let the "prose vs. hook" framing this ticket's Assumptions apply to `run_in_background`
  Hard Rule enforcement generalize into converting other CLAUDE.md prose rules to hooks.** The
  epic doc's own Out-of-Scope line is explicit: "only the two with direct, repeated, repository-
  native evidence of failure (M2, M3) are in scope here... converting it without evidence would
  be exactly the 'preventive hardening without justification' pattern the freeze pass was built
  to catch."
- **Do not silently delete `test-scoper.md`'s existing `## Background Commands` prose section.**
  Per this ticket's own Out of Scope and Acceptance Criteria: keep it as defense-in-depth
  alongside any new hook (a hook that fails open — per this repo's universal `try/except: pass`
  convention — still needs the prose as a backstop when the hook itself errors), or explicitly
  supersede it with documented rationale. Never a silent removal either way.
- **Do not conflate "not enabled in this project's committed `.claude/settings.json`" with "does
  not exist in Claude Code."** This is the exact error the first-pass sub-agent research made in
  this investigation — `hook-events.yaml`/`hook-surface-policy.yaml` document project-local
  policy, not product capability. Any doc or ticket text written from this point forward should
  keep that distinction explicit, mirroring how `codex_capability_matrix.md` already keeps
  Codex's "available" vs. "enabled" axes separate.
- **Do not invent an exact transcript/payload schema without the scratch-first capture.** Writing
  hook-script parsing logic against a guessed field name (e.g. assuming `tool_response.status ==
  "running"` without having seen a real `BashOutput`/`Monitor` tool_response) is the same class of
  mistake `TCK-20260730-PROVIDER-HOOK-POLICY`'s Anti-Drift Hazards warn against for Codex's
  "available" count — get the fixture first.
- **Do not let this ticket's new hook become a second, uncoordinated writer to `.claude/
  settings.json`'s `hooks` block alongside `TCK-20260904-BASH-SECRET-SCAN-HOOK`.** Both are
  same-batch, additive-expected edits to the same JSON file; sequence them as one merge.

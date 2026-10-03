---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME
artifact_type: investigation
tags: [ai, agent-monitoring, determinism]
---

# Investigation — TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME

## Blocking Condition Re-Verification (primary purpose of this Investigate pass)

**Blocking condition CONFIRMED STILL TRUE as of 2026-07-11T03:12:08Z.**

This ticket's Request Summary is explicit that the first step of any future Investigate phase is
to re-check — not assume — whether a real `Workflow`/`tool_runner` execution surface has appeared.
Two independent lines of evidence were checked; both say no.

### 1. `.claude/skills/*/SKILL.md` wording — unchanged since 2026-07-10

Every workflow-backed skill still contains the identical "Workflow tool is not available" clause.
Exact current text, with file:line:

- `.claude/skills/implement-ticket/SKILL.md:26` — `**Do not call the Workflow tool — it is not available.** Execute the workflow directly:`
- `.claude/skills/implement-epic/SKILL.md:26` — `**Do not call the Workflow tool — it is not available.** Execute the workflow directly:`
- `.claude/skills/implement-epic/SKILL.md:31` — `   - Do not call a Workflow tool.` (inside the nested-`implement-ticket`-call instructions for step 3 of the Action section)
- `.claude/skills/create-tickets/SKILL.md:27` — `**Do not call the Workflow tool — it is not available.** Execute the workflow directly:`
- `.claude/skills/simq-audit/SKILL.md:29` — `**Do not call the Workflow tool — it is not available.** Execute the workflow directly:` (a fifth workflow-backed skill not named in the ticket's own text — it did not exist, or was not yet noticed, when the ticket was drafted on 2026-07-10; it carries the identical clause)

No other `SKILL.md` in `.claude/skills/` (15 total directories as of this session: `agent-monitoring-retro`, `api-design-principles`, `architecture`, `backend-testing`, `brainstorming`, `create-tickets`, `debugging-strategies`, `doc-coauthoring`, `frontend-design`, `implement-epic`, `implement-ticket`, `prompt-builder`, `python-performance-optimization`, `python-testing-patterns`, `simq-audit`, `test-driven-development`) contains this clause or any softened/changed variant — `agent-monitoring-retro/SKILL.md:17` uses the word "workflow" only in the generic English sense ("Before changing any agent prompt, workflow phase, or tier routing rule") and is not one of the `.claude/workflows/*.js`-backed skills.

Also newly observed: `.claude/workflows/` contains 11 `.js` files total, not just the 4-5 with a matching `SKILL.md`: `compact-simulation-result.js`, `generate-simulation-setup.js`, `investigate-simulation-result.js`, `prepare-simulation-execution.js`, `propose-simulation-enhancements.js`, `register-simulation-result.js`, `update-knowledge-store.js` have no corresponding skill directory under `.claude/skills/` and are invoked through some other path (not resolved in this investigation — flagged under Risks/Open Questions and Anti-Drift Hazards, since it affects how big the eventual porting surface actually is if this ticket is ever unblocked).

### 2. Direct empirical evidence from this exact session/harness

This investigation was run as an agent inside this exact harness, this exact session. The tool
surface available to this session (top-level tools plus the deferred-tool list surfaced via
`ToolSearch`) is: `Agent`, `Artifact`, `Bash`, `Edit`, `Read`, `Skill`, `ToolSearch`, `Write`, and
(deferred) `EnterWorktree`, `ExitWorktree`, `Monitor`, `NotebookEdit`, `SendMessage`, `TaskStop`,
`WebFetch`, `WebSearch`, plus `mcp__github__*` and `mcp__knowledge-search__*`. There is no tool
named `Workflow`, and no Agent-SDK `tool_runner`-style construct.

To rule out a tool existing but simply not surfaced in this conversation's initial listing,
`ToolSearch` (which semantically searches *all* available tools, including ones not yet loaded)
was queried directly with `"Workflow tool_runner execute workflow orchestration runtime"`. It
returned exactly one match: `EnterWorktree` — a git-worktree-isolation tool that matches only on
the substring "workt(ree)" coincidence with "runtime"/"orchestration" keywords, and has nothing to
do with executing `.claude/workflows/*.js` as real code. No `Workflow` tool exists in this harness's
tool catalog as of this session.

This is exactly the situation the idea doc's Open Questions section anticipated as one of two
possible permanent answers ("an LLM narrates a `.js` spec into tool calls is the permanent shape of
this system") — still true today, one day after the ticket was drafted. Given the sample size (one
day, one harness snapshot), this does not prove permanence, only that nothing has changed yet.

**Conclusion: the ticket must remain BLOCKED. No Plan or Implement phase should follow this
Investigate. This investigation does not recommend proceeding.**

## Second Independent Confirmation (this pass, 2026-07-11T07:00:16Z)

This Investigate pass is an explicit RE-CHECK of the prior pass above (same session, ~3h48m
earlier, timestamped 2026-07-11T03:12:08Z), performed fresh per the ticket's own instruction: "don't
assume it from this ticket's text alone." No new information was supplied suggesting the blocking
condition had changed. Both lines of evidence were re-run independently rather than re-cited:

1. **Fresh grep of `.claude/skills/*/SKILL.md`**, run directly in this pass (not copied from the
   prior pass's output):
   ```
   .claude/skills/implement-ticket/SKILL.md:26:**Do not call the Workflow tool — it is not available.** Execute the workflow directly:
   .claude/skills/implement-epic/SKILL.md:26:**Do not call the Workflow tool — it is not available.** Execute the workflow directly:
   .claude/skills/implement-epic/SKILL.md:31:   - Do not call a Workflow tool.
   .claude/skills/create-tickets/SKILL.md:27:**Do not call the Workflow tool — it is not available.** Execute the workflow directly:
   .claude/skills/simq-audit/SKILL.md:29:**Do not call the Workflow tool — it is not available.** Execute the workflow directly:
   ```
   Byte-identical to the prior pass's findings, same 4 files / 5 line numbers. `.claude/skills/`
   still contains exactly 16 `SKILL.md` files (confirmed via fresh `ls` this pass); no new
   workflow-backed skill has appeared since the prior pass's 15-directory count (the earlier pass's
   listing predates this session noticing `agent-monitoring-retro` was already present — directory
   count difference is a counting artifact, not a real change; the same 5 "Workflow tool" lines are
   the load-bearing fact and they are unchanged).

2. **Fresh empirical probe of this exact session's own tool surface**, independent of the prior
   pass's probe: `ToolSearch` was queried twice this pass —
   `"Workflow tool_runner execute workflow orchestration runtime agentic loop"` (broad semantic
   query) returned `EnterWorktree` and `Monitor` as the only matches, neither of which executes
   `.claude/workflows/*.js` as real code; and `"select:Workflow"` (direct exact-name lookup) returned
   **"No matching deferred tools found."** There is no tool named `Workflow` in this harness's
   catalog, confirmed by direct name lookup, not just semantic proximity. `.claude/workflows/`
   still contains exactly 11 `.js` files (re-confirmed via fresh `ls` this pass), unchanged from the
   prior pass.

**Blocking condition CONFIRMED STILL TRUE as of 2026-07-11T07:00:16Z. This is the SECOND
independent confirmation within this same session** (first at 03:12:08Z, second at 07:00:16Z, ~3h48m
apart) — both textual and empirical evidence collected fresh each time, both times returning the
same answer, zero drift. This strengthens (does not merely repeat) the prior pass's conclusion:
the absence has now been observed at two distinct points in time within the same session, using
independently-run checks rather than a single cached observation.

**Conclusion unchanged: the ticket must remain BLOCKED. No Plan or Implement phase should follow
this Investigate. This investigation does not recommend proceeding.**

## Current Behavior

Because the blocking condition holds, "current behavior" below describes the *narration* pattern
this ticket would eventually replace — not a target for change in this session.

- `.claude/workflows/implement-ticket.js`, `.claude/workflows/implement-epic.js`,
  `.claude/workflows/create-tickets.js`, `.claude/workflows/simq-audit.js`, and 7 other `.js` files
  under `.claude/workflows/` are prose/pseudocode files. They are never executed by a JS engine.
- Each corresponding `SKILL.md`'s Action section (see file:line list above) instructs the invoking
  LLM to read the `.js` file in full, then manually translate JS constructs (`phase()`, `log()`,
  `agent()`, gate `if` conditions, `writeMonitoring()`, `return`) into real tool calls
  (`Agent(...)`, text output, `Bash(...)` for monitoring writes) — see the translation tables at
  `implement-ticket/SKILL.md` lines ~26-38, `create-tickets/SKILL.md` lines ~27-35, and
  `simq-audit/SKILL.md` lines ~29-37.
- `implement-epic/SKILL.md:31-34` additionally instructs the LLM to recursively narrate
  `implement-ticket.js` from inside the epic loop for each child ticket, rather than calling any
  nested `Workflow` tool — i.e. the narration is not just single-level, it nests.
- Per `docs/plans/agent_infrastructure/idea_workflow_execution_determinism.md` (Problem section),
  this narration failure mode was reproduced live twice in the 2026-07-10 session that drafted this
  idea/ticket: a `Step 0b` sidecar-registration instruction omitted across 5 agent prompts
  (`TCK-20260710-SECURITY-REVIEWER-AGENT-DOC`), and a `## Test Summary`/`## Files Changed`
  bookkeeping omission caught only because `done-checker` happened to gate on it
  (`TCK-20260710-EPIC-STALENESS-CHECK`).
- The sibling near-horizon mitigation is already shipped: `tools/gate_checks/workflow_meta_conformance.py`
  (added by `TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK`, now in `tickets/done/`) statically
  cross-references each workflow's declared `meta.phases` array against `agent-monitoring/events.jsonl`
  for a given `run_id`, flagging phases with zero matching events. This detects one *symptom* of
  narration unreliability after the fact; it does not make the orchestrator itself executed rather
  than narrated. It is out of scope here (see ticket's Out of Scope) and already done — it is not
  something this ticket needs to redo or extend.

## Mechanics / Engine Constraints

None. This ticket concerns Claude agent-orchestration tooling (`layer: ai`, per the tag registry's
definition of `ai` as "the Claude agent system, not gameplay AI/cognition") — it does not touch
`docs/mechanics/` simulation laws or `docs/engine/` kernel/pipeline contracts. No chapter or
contract constrains or is constrained by this ticket's scope.

## Parity Ledger Overlap

None found, and this absence was itself verified rather than assumed. `docs/parity_ledger/` was
grepped for `workflow`/`orchestrat` (case-insensitive) across all 9 ledger YAML files. Matches
exist only in `infrastructure.yaml`, and every one of them is a false positive relative to this
ticket's scope — they refer to a *different, unrelated* `Workflow` concept:

- `src/lab/workflows.py`'s `Workflow.run()` classes (simulation-lab agentic workflows — e.g.
  `INFRA-225`, `INFRA-261`, and the `TCK-2026052x-LAB-*` / `TCK-20260627-P2I-WORKFLOW-TYPES` family)
  — a Python module of typed simulation-lab operations, unrelated to `.claude/workflows/*.js`.
  `docs/parity_ledger/faction.yaml`, `progression.yaml`, `social_narrative.yaml`, `town_resource.yaml`,
  and `world_dynamics.yaml` also only match on generic prose use of "workflow" in event-emission
  narrative, not this ticket's subject.
- `.github/workflows/test.yml` (GitHub Actions CI) — e.g. `INFRA-227`, referenced from
  `TCK-20260627-P2M-CI-ARTIFACTS` — a completely different "workflow" (CI YAML), not
  `.claude/workflows/*.js`.
- One entry (around `INFRA-183`/registry-related, `src/lab/orchestrator.py`) references
  `.claude/workflows/implement-ticket.js` only incidentally, as `v2_evidence` for a Finalize-phase
  registry self-check (`run_finalize_selfcheck`) — a different ticket's (`TCK-20260709-REGISTRY-REGEN-ON-CLOSE`)
  concern, not this one's.

**No parity ledger entry needs updating by this ticket, now or if/when it is ever unblocked** — the
orchestrator-narration-vs-execution distinction is not simulation behavior and has no ledger
subsystem home. No P0 entries are implicated.

## Prior Work

- `TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK` (DONE, `tickets/done/`, artifacts in
  `stored_artifacts/TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK/`) — this is the idea doc's
  near-horizon half, already shipped. It is the sibling this ticket's Out of Scope section
  correctly excludes; nothing here should re-touch `tools/gate_checks/workflow_meta_conformance.py`.
- `TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC` and its child
  `TCK-20260710-CURRENT-RUN-SIDECAR-BASH` / `TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH` (all DONE,
  archived to `tickets/done/agent-bookkeeping-determinism/`) — the sub-agent-layer sibling this
  ticket is explicitly one layer above. That epic moved mechanical bookkeeping (sidecar
  registration, timestamp capture) from sub-agent-prompt text into the orchestrator's own `Bash()`
  calls. It assumed, but did not itself require, that the orchestrator executing those `Bash()`
  calls is deterministic — this ticket's premise is that the orchestrator itself is still an LLM
  narrator, which is a distinct, one-layer-higher concern per the idea doc.
- `TCK-20260708-SKILL-CREATE-TICKETS-WORKFLOW-TOOL-STALE` (DONE) — prior work that rewrote
  `create-tickets/SKILL.md`'s Action section to explicitly state the Workflow tool is unavailable
  (i.e. this is the origin of the current wording being checked above, not new work this ticket
  should redo).
- `TCK-20260708-SKILL-IMPLEMENT-TICKET-PHASE-DRIFT` (DONE) — separate concern (keeping
  `SKILL.md`'s narrated phase list in sync with `implement-ticket.js`'s `meta.phases`), not this
  ticket's scope.
- `TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR` (DONE, artifacts in
  `stored_artifacts/TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR/`) — general workflow-doc hygiene,
  predates and is unrelated to the execution-surface question.
- `docs/ai/workflows.md` (`docs/ai/workflows.md#body-000`) already documents, as current fact: "Workflows
  are multi-agent orchestration scripts in `.claude/workflows/*.js`. They coordinate subagents
  across phases..." — consistent with, not contradicting, the narrated-execution model.
- `docs/ai/skills.md`'s "Skills vs. Workflows — How Invocation Works" section documents the
  skill-narrates-workflow relationship as the current, intended architecture, not a stopgap awaiting
  replacement — useful context for Plan phase (if ever reached) on how deeply this pattern is
  load-bearing elsewhere in the docs.

## Risks and Open Questions

- **Primary risk already covered above and resolved for this pass**: is the blocking condition
  still true? Yes, confirmed by both textual (SKILL.md) and empirical (this session's own tool
  surface) evidence. This is not a decision this investigation is authorized to override.
- **Unresolved from the ticket's own Assumptions/Open Questions** (carried forward, not resolved
  here, per the ticket's own instruction not to assume an answer):
  - Whether a real `Workflow`/`tool_runner` execution surface is on any roadmap for this harness at
    all, or whether narration is the permanent shape of the system. Still genuinely unknown from
    inside this repo.
  - Whether this work should be its own epic when/if scheduled (the parent epic
    `TCK-20260710-WORKFLOW-EXECUTION-DETERMINISM-EPIC` already exists and currently tracks this as
    one of (originally) 2 draft children — the sibling child is now DONE, so the epic today tracks
    only this one open, blocked child). Not decided here.
- **New gap surfaced this pass, not previously flagged**: `.claude/workflows/` contains 7 `.js`
  files with no corresponding `SKILL.md` (`compact-simulation-result.js`,
  `generate-simulation-setup.js`, `investigate-simulation-result.js`,
  `prepare-simulation-execution.js`, `propose-simulation-enhancements.js`,
  `register-simulation-result.js`, `update-knowledge-store.js`). This ticket's Related Code Areas
  (`.claude/workflows/*.js`) technically globs all 11 files, but the ticket's own Scope text only
  discusses `implement-ticket.js` by name as an example ("`.claude/workflows/implement-ticket.js`
  ported to real executable code"). If/when this ticket is ever unblocked, Plan will need to decide
  explicitly whether porting scope is "all `.claude/workflows/*.js`" or "the skill-backed subset" —
  flagged here, not assumed.
- No file listed in "Related Code Areas" is missing — both globs (`.claude/workflows/*.js`,
  `.claude/skills/*/SKILL.md`) resolve to real, readable files.

## Anti-Drift Hazards

- **Do not treat this Investigate pass as license to Plan.** The ticket's own acceptance criteria
  are explicit that AC1 ("confirm whether a surface has become available") is the entire actionable
  scope right now, and AC2 is provisional/contingent on AC1 flipping true. AC1 remains false. Do not
  produce a `plan.md` for AC2's porting work in this cycle.
- **Do not port `.claude/workflows/implement-ticket.js` speculatively "just to see."** The Out of
  Scope section explicitly forbids "any speculative implementation against a hypothetical execution
  surface before one is confirmed to exist." No code changes belong to this ticket right now.
- **Do not fold in the already-done near-horizon conformance check** (`workflow_meta_conformance.py`)
  as if it were unfinished work for this ticket — it is a different ticket, already DONE, and is
  explicitly Out of Scope here.
- **Do not conflate this with the sub-agent bookkeeping-determinism epic's scope** (also DONE) —
  that fixed sub-agent mechanical-step reliability; this ticket is one architectural layer above
  (orchestrator-as-narrator), a distinction the ticket itself insists on preserving.
- **If a future session finds a `Workflow`/`tool_runner`-shaped tool has appeared**, re-verify with
  the same two-pronged method used here (grep the current `SKILL.md` wording + empirically probe
  this session's own tool surface via `ToolSearch`/tool listing) before trusting any single source —
  a stale doc claiming a surface exists, or a tool that exists but isn't wired to this harness's
  skill-invocation path, would both be false positives.
- **This ticket has now been re-verified twice in the same session (2026-07-11T03:12:08Z and
  2026-07-11T07:00:16Z) with zero drift in the answer.** Do not let repeated confirmation of the
  same negative result be mistaken for growing evidence that the surface will never appear — it is
  only evidence that it has not appeared *yet*, as of this session's two sampling points. Each future
  re-check still needs to be run fresh (per the ticket's own instruction), not skipped because "it
  was already checked twice and always comes back false."

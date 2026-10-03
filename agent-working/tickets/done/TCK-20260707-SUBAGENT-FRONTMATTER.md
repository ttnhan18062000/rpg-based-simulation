---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260707-SUBAGENT-FRONTMATTER
phase: done
date: 2026-07-07
tags: [workflows]
---

# TCK-20260707-SUBAGENT-FRONTMATTER

## Title
Register `.claude/agents/*.md` role files as real Claude Code subagents

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Discovered while running `/implement-epic folder=tickets/todos/simq-corpus-tiers/`: calling
`Agent(subagent_type="ticket-scoper", ...)` fails with `Agent type 'ticket-scoper' not found.
Available agents: claude, claude-code-guide, Explore, general-purpose, Plan, statusline-setup`.
`docs/ai/agents.md` and `docs/ai/ticket-lifecycle.md` (`## Manual Execution (Without the Workflow)`)
both explicitly document `Agent(subagent_type="ticket-scoper", ...)`,
`Agent(subagent_type="investigator", ...)`, etc. as the intended invocation pattern for all 12 files
under `.claude/agents/`, and `implement-ticket.js`/`implement-epic.js` pass the same names via the
`agentType` option to their internal `agent()` helper. None of the 12 `.claude/agents/*.md` files
have the YAML frontmatter (`name`, `description`) Claude Code requires to register a file as a
callable `subagent_type` — they are plain `# Title` + body markdown. This is a real, documented-but-
broken invocation path, not a misunderstanding of intended design: the fix is additive frontmatter
only, no prose/body changes, so every existing role instruction stays byte-identical.

## Scope
1. Add a YAML frontmatter block (`name`, `description`) to the top of each of the 12 files under
   `.claude/agents/`: `architecture-reviewer.md`, `done-checker.md`, `implementer.md`,
   `investigator.md`, `mechanics-auditor.md`, `parity-updater.md`, `planner.md`,
   `security-reviewer.md`, `simulation-analyst.md`, `test-scoper.md`, `ticket-scoper.md`,
   `world-debugger.md`.
2. `name` = the filename minus `.md` in every case (matches the `agentType` strings already hardcoded
   in `implement-ticket.js`/`implement-epic.js` and the `subagent_type` strings already hardcoded in
   `docs/ai/agents.md`/`docs/ai/ticket-lifecycle.md` — no JS/doc changes needed if this convention is
   followed exactly).
3. `description` = a one-sentence summary of the role's job, drawn from that file's own opening
   sentence / `docs/ai/agents.md`'s existing "Role:" line for that agent (already-authored source of
   truth — no new judgment calls about what each agent does).
4. Do not add `tools:`, `model:`, or any other optional frontmatter field — omitting them means the
   subagent inherits the parent session's full tool access and model, which is exactly the behavior
   these roles already have today via the ad hoc `general-purpose` + embedded-prompt workaround. Tool/
   model scoping per role is a plausible follow-up improvement but is out of scope here — this ticket
   is additive-frontmatter-only, to keep the fix minimal and byte-for-byte behavior-preserving.
5. Do not change any body content (the existing `# Title` heading and all prose stay exactly as
   written) — frontmatter is prepended, nothing else moves.
6. Smoke-test a representative sample (or all 12, cost permitting) of the newly-registered
   `subagent_type` values with a trivial prompt to confirm each resolves without the
   "Agent type ... not found" error.

## Out of Scope
- Adding `tools:`/`model:`/`color:`/other optional frontmatter fields to scope each subagent's
  capabilities — separate follow-up if wanted, not required to fix the reported bug
- Changing `implement-ticket.js`, `implement-epic.js`, `docs/ai/agents.md`, or
  `docs/ai/ticket-lifecycle.md` — their existing `agentType`/`subagent_type` strings already match the
  `name` values this ticket adds, so no reference needs updating
- Resuming or fixing `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY` (paused mid-Implement when this bug
  was hit; tracked separately, resumes after this hotfix lands)
- Any change to simulation/gameplay code under `src/` — this ticket only touches `.claude/agents/`
  tooling files

## Acceptance Criteria
- [ ] All 12 files under `.claude/agents/` have a valid YAML frontmatter block with `name` (matching
      filename minus `.md`) and `description` fields
- [ ] No existing body content in any of the 12 files was altered beyond frontmatter insertion
- [ ] `Agent(subagent_type="ticket-scoper", ...)` (and the other 11) resolves without the
      "Agent type ... not found" error in a live smoke test
- [ ] No `src/` files touched; no simulation/parity behavior change

## Related Tickets
- (discovered during, but not part of) `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC` /
  `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY` — the epic run that surfaced this bug; paused pending
  this fix

## Related Docs
- `docs/ai/agents.md` — documents the intended `Agent(subagent_type="<name>", ...)` invocation pattern
  and each agent's Role/Inputs/Outputs (source of `description` text for this ticket)
- `docs/ai/ticket-lifecycle.md` — `## Manual Execution (Without the Workflow)` section, same
  documented-but-broken pattern
- `.claude/skills/implement-ticket/SKILL.md`, `.claude/skills/implement-epic/SKILL.md` — translation
  tables referencing `agentType`

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `.claude/agents/architecture-reviewer.md`
- `.claude/agents/done-checker.md`
- `.claude/agents/implementer.md`
- `.claude/agents/investigator.md`
- `.claude/agents/mechanics-auditor.md`
- `.claude/agents/parity-updater.md`
- `.claude/agents/planner.md`
- `.claude/agents/security-reviewer.md`
- `.claude/agents/simulation-analyst.md`
- `.claude/agents/test-scoper.md`
- `.claude/agents/ticket-scoper.md`
- `.claude/agents/world-debugger.md`

## Assumptions / Open Questions
- Assumes Claude Code's custom-subagent discovery watches `.claude/agents/` and picks up frontmatter
  changes without requiring a session restart (per official docs: file watching picks up new/edited
  agent files within seconds). If the live smoke test shows otherwise, this ticket's Implementation
  Notes will record the discrepancy and what was needed instead (e.g. session restart).
- Not adding `tools`/`model` scoping now (see Scope item 4) is a deliberate minimality choice, not an
  oversight — flagged here in case a reviewer wants that folded in instead of left as a follow-up.

## Implementation Notes
Added a `name`/`description` YAML frontmatter block to all 12 `.claude/agents/*.md` files, as pure
insertions (5 lines each, `git diff --stat` confirms `12 files changed, 60 insertions(+)`, `0
deletions`) — no existing body content was altered. `name` matches the filename minus `.md` in every
case, exactly matching the `agentType`/`subagent_type` strings already hardcoded in
`implement-ticket.js`, `implement-epic.js`, `docs/ai/agents.md`, and `docs/ai/ticket-lifecycle.md`, so
no other file needed a corresponding reference update. `description` text was drawn from each file's
own opening sentence / `docs/ai/agents.md`'s existing "Role:" line. No `tools`/`model` fields were
added, per Scope item 4 (inherit parent session's full tool access and model — behavior-preserving).

## Test Summary
Static validation: PASS. A Python check parsed the frontmatter block of all 12 files with `yaml.safe_load`,
confirmed each `name` field exactly matches its filename, confirmed each has a non-empty `description`,
and confirmed via `git diff` that only frontmatter was inserted (no body content touched, no deletions).

Live smoke test, attempt 1 (same session as implementation): **FAIL.** Calling
`Agent(subagent_type="<name>", ...)` for all 12 newly-registered names still returned
`Agent type '<name>' not found. Available agents: claude, claude-code-guide, Explore,
general-purpose, Plan, statusline-setup` — identical to the pre-fix error. Confirmed: this harness's
Agent-tool subagent registry is populated at session start and does not hot-reload `.claude/agents/`
mid-session, contrary to the general file-watching behavior described in Claude Code's docs for a
long-running process.

Live smoke test, attempt 2 (after user exited and resumed the session): **PASS, 12/12.** Once the
session was restarted, the Agent tool's available-agents list included all 12 new names. Each was
invoked with a trivial "reply with SMOKE_OK <name>, do nothing else" prompt and every one resolved
and returned the expected string:
`ticket-scoper`, `investigator`, `planner`, `architecture-reviewer`, `implementer`, `test-scoper`,
`parity-updater`, `security-reviewer`, `done-checker`, `mechanics-auditor`, `world-debugger`,
`simulation-analyst` — all `SMOKE_OK <name>`, no errors.

**Acceptance criterion "resolves without the 'Agent type ... not found' error in a live smoke test"
is now SATISFIED.** Finding for future runs: a session restart (`/exit` + resume, or a fresh session)
is required after editing `.claude/agents/*.md` frontmatter before the new subagent types become
callable — this harness does not hot-reload the agent registry mid-session.

## Files Changed
- `.claude/agents/architecture-reviewer.md` (+5 frontmatter lines)
- `.claude/agents/done-checker.md` (+5 frontmatter lines)
- `.claude/agents/implementer.md` (+5 frontmatter lines)
- `.claude/agents/investigator.md` (+5 frontmatter lines)
- `.claude/agents/mechanics-auditor.md` (+5 frontmatter lines)
- `.claude/agents/parity-updater.md` (+5 frontmatter lines)
- `.claude/agents/planner.md` (+5 frontmatter lines)
- `.claude/agents/security-reviewer.md` (+5 frontmatter lines)
- `.claude/agents/simulation-analyst.md` (+5 frontmatter lines)
- `.claude/agents/test-scoper.md` (+5 frontmatter lines)
- `.claude/agents/ticket-scoper.md` (+5 frontmatter lines)
- `.claude/agents/world-debugger.md` (+5 frontmatter lines)

## Completion Summary
Added `name`/`description` YAML frontmatter to all 12 `.claude/agents/*.md` files (additive only, 60
lines inserted / 0 deleted across the 12 files), matching the `subagent_type`/`agentType` strings
already hardcoded in `implement-ticket.js`, `implement-epic.js`, `docs/ai/agents.md`, and
`docs/ai/ticket-lifecycle.md`. Discovered and confirmed one operational finding along the way: this
harness does not hot-reload the Agent tool's subagent registry mid-session — a session restart
(`/exit` + resume) is required after editing `.claude/agents/*.md` before new/changed subagent types
become callable. Live smoke test after restart: 12/12 `Agent(subagent_type=<name>, ...)` calls
resolved correctly. `done-checker` verdict: READY_TO_CLOSE, 13/13 DoD conditions PASS or NA, 0
failing. No `src/` files touched; no simulation/parity behavior change.

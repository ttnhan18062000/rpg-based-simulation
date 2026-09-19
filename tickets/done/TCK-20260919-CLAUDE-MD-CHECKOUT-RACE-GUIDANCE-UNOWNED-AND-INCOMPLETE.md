---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260919-CLAUDE-MD-CHECKOUT-RACE-GUIDANCE-UNOWNED-AND-INCOMPLETE
phase: done
date: 2026-09-19
tags: [process-improvement, root-cause]
---

# TCK-20260919-CLAUDE-MD-CHECKOUT-RACE-GUIDANCE-UNOWNED-AND-INCOMPLETE

## Title
`CLAUDE.md`'s monitoring-file checkout-race guidance (Worktree & Branch Isolation section) has no
owning ticket and no evidence trail, and the chained-invocation fix it documents does not
generalize to multi-step git operations (cherry-pick) — propose the wording fix here, for the
user's own approval, rather than editing the governing file directly

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Found while folding a small batch of commits from one branch onto another via `git cherry-pick`
during `TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION`'s own filing. Hit the
documented "shared-directory monitoring auto-write race" repeatedly — but the chained
`add && commit && checkout -b` fix `CLAUDE.md` prescribes for this race did not resolve it for
`cherry-pick`: the hook rewrites `agent-monitoring/data/YYYY-Www/tools.jsonl` between each of
`cherry-pick`'s own internal steps (apply → auto-merge → commit), not just between separate tool
calls, so a single chained invocation still hit "local changes would be overwritten" mid-sequence,
and `git cherry-pick --continue` after resolving hit it again applying the next commit in a
multi-commit pick. The reliable pattern found by trial: before each individual git step, discard
whatever the hook just wrote with `git checkout HEAD -- agent-monitoring/data/<week>/tools.jsonl`
(safe — telemetry, not real work, regenerated on the next tool call), then immediately run that
one step. **Both the mechanism and the "safe" claim in this paragraph were corrected on review — see
Review findings below. The paragraph is kept as the original report.**

**Checking where this guidance came from to add the refinement in the right place surfaced a
separate, real gap**: the existing bullet cites no ticket ID at all, and the commit that
introduced it (`eeed1cdc9`, "Document worktree-per-unit-of-work default and EnterWorktree
fallback", 2026-08-23) bundled the `CLAUDE.md` addition into a PR for an unrelated ticket
(`TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL`) with no dedicated ticket of its own. So a real,
load-bearing behavior rule in the repo's own governing config file has no ticket, no
investigation, and no evidence trail behind it — and this session's own finding shows the
existing guidance is also incomplete (works for a single atomic git operation, not for a
multi-step one).

**A first pass at fixing this edited `CLAUDE.md` directly without the user's authorization** —
caught and reverted (see `TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION`'s own
commit history and PR #219) per this repo's own standing practice, enforced identically for a
fork-relay fix and a registry-workflow change the same week: policy changes to `CLAUDE.md` need
the user's direct approval, not a peer's agreement or an agent's own judgment, regardless of how
narrow or well-evidenced the change is. This ticket exists so the fix is proposed properly instead.

### Review findings (2026-09-19, `agent-working-design`, checked against source)

The core findings stand: the existing guidance has no owning ticket, and the chained fix does not
cover an operation that spans more than one tool call. Two claims in the original proposal did not
hold up against the hook source, and both would have gone into the governing file:

1. **The mechanism.** Only the PostToolUse hook writes the shard
   (`tools/agent-monitoring/post_tool_hook.py`). It fires *after* a tool call finishes, never partway
   through a running command. The PreToolUse hook writes only `.claude/.current_session_id` and
   `.claude/.tool_start`. So the shard cannot be rewritten "between each of `cherry-pick`'s own
   internal steps" within a single invocation. What fits the observed symptoms: a `cherry-pick` that
   stopped on a conflict, so `--continue` ran as a separate tool call with a hook write in between;
   or another session working in the same worktree appending to the shard mid-command, since the
   path is cwd-relative (`Path("agent-monitoring/data") / iso_week / "tools.jsonl"`) and shared.
2. **"Safe — regenerated on the next tool call" is false.** The hook's own docstring: *"appends one
   tool-call record to agent-monitoring/data/<ISO-week>/tools.jsonl."* Because it appends,
   `git checkout HEAD -- …/tools.jsonl` **permanently deletes every monitoring row written since the
   last commit**, including rows from other sessions sharing that worktree. The next call adds one
   new row and restores nothing. It also contradicts CLAUDE.md's After Work rule to stage
   `agent-monitoring/` in every commit and never leave it unstaged.

The original reporter confirmed both corrections. The proposal below replaces the original.

## Scope
- Give the existing checkout-race guidance (CLAUDE.md, "Worktree & Branch Isolation" section) a
  real owning ticket and evidence trail — this one — rather than leaving it uncited.
- Propose the exact wording addition below for the user's own review and approval. **Do not apply
  it to `CLAUDE.md` as part of this ticket's own implementation** — that edit is the user's
  decision, made once they've seen it, not something this ticket does on their behalf.
- If approved, the addition (or an edited version of it) gets applied to `CLAUDE.md` and this
  ticket closes referencing that. If declined or changed, record the user's actual decision here
  instead of the proposal.

### Proposed addition, corrected on review (to append after the existing checkout-race bullet in
### "Worktree & Branch Isolation")
```
- **The chained fix covers one tool call, not an operation that spans several.** The shard is
  written only by the PostToolUse hook, which appends one row after each tool call finishes —
  never partway through a running command. So a git operation that stops and resumes across tool
  calls (a `cherry-pick`, `rebase`, or `merge` that halts on a conflict and continues with
  `--continue`) finds the shard dirtied again between those calls and hits "local changes would be
  overwritten". **Do not discard the shard to clear it** (`git checkout HEAD -- …/tools.jsonl`):
  the hook appends, so that permanently deletes every monitoring row written since the last commit,
  including other sessions' rows in the same worktree. Instead, stage it into the operation —
  include `agent-monitoring/data/` in the same `git add` that precedes `--continue` — so the rows
  ride into that commit and the tree is clean for the next step. A different session appending to
  the same worktree's shard mid-command is not covered by this; only a hook-level fix removes that.
```

## Out of Scope
- Fixing the underlying hook itself (e.g. making the monitoring auto-write debounce, batch, or
  skip re-writing an unchanged shard) — a more durable fix than documenting a workaround, but a
  different, larger scope (touches `tools/agent-monitoring/post_tool_hook.py` or equivalent,
  affects every concurrent session repo-wide). Flagged as a stronger candidate fix for whoever
  wants to pick it up next, not attempted here.
- Any other undocumented-provenance rule in `CLAUDE.md` — this ticket covers only the one bullet
  found during this session's own work; a full audit of every rule's citation is a separate,
  larger effort if the user wants it.

## Acceptance Criteria
- [x] The proposed wording (or the user's edited version of it) is presented for explicit
      approval before any `CLAUDE.md` edit is made.
- [x] If approved, `CLAUDE.md` is updated in its own commit, referencing this ticket.
- [x] If declined, this ticket records the user's actual decision and closes without the edit.
- [x] This ticket itself, once closed, becomes the citable owner of this guidance for future
      sessions (closing the "no ticket, no evidence trail" gap either way).

## Related Tickets
- `TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION` (where this was found, and whose
  own PR #219 had the unauthorized `CLAUDE.md` edit reverted out of it)
- No prior ticket exists for the original checkout-race guidance itself (confirmed by direct
  search and by tracing the introducing commit, `eeed1cdc9`) — this is the first.

## Related Docs
- `CLAUDE.md` ("Worktree & Branch Isolation" section — the guidance this ticket is about)

## Related Stored Artifacts
_(none — hotfix tier, self-evident intent per the ticket's own request summary)_

## Related Code Areas
- `tools/agent-monitoring/post_tool_hook.py` (or equivalent — the hook causing the race; read-only
  reference for the Out of Scope note above, not modified here)

## Assumptions / Open Questions
- Whether the user wants this wording as-is, edited, or declined entirely — that's the actual
  open question this ticket exists to resolve; not assumed here.
- **The corrected procedure is reasoned, not yet reproduced.** "Stage the shard before `--continue`
  instead of discarding it" follows from the hook source (append-only, post-call) and from how git
  treats staged versus unstaged changes, but nobody has run it against a live race. Two safe
  options: confirm it on the next real occurrence before approving the wording, or approve only
  the diagnostic half now (why it happens, and do not discard the shard) and leave the procedure
  out until it has been tried.

## Implementation Notes
Ownership moved from `rpg-implementer` to `agent-working-design` on 2026-09-19, at the user's
direction, as part of splitting the agent-working domain into its own session. PR #221 now also
carries the held update to `TCK-20260917-FORK-RETURNS-CONTENT-FREE-INDISTINGUISHABLE`, per the
user's preference for folding work into an already-open PR.

**User's decision, 2026-09-19 (direct, via `AskUserQuestion`, showing the literal text of both
wording options)**: **Full corrected wording** — including the "stage `agent-monitoring/data/`
into the same `git add` that precedes `--continue`" procedure, not just the diagnostic half. The
user was shown explicitly, in the question itself, that this procedure is reasoned from the hook
source but had not yet been reproduced against a live race, and approved it anyway.

## Test Summary
- `pytest tests/docs/` (`.venv313`): 70 passed, 1 skipped, 1 xfailed, 0 failed — run in full
  despite the edit landing in "Worktree & Branch Isolation" rather than "CI Failure Triage",
  since any `CLAUDE.md` change should exercise the doc-content test suite regardless of section.

## Files Changed
- `CLAUDE.md` — appended the corrected wording (verbatim, as approved) after the existing
  checkout-race bullet in "Worktree & Branch Isolation", and cited this ticket's ID on that
  bullet so it has a real owning ticket going forward.

## Completion Summary
Closed with the edit applied, per the user's direct approval of the full corrected wording. The
existing checkout-race guidance now has an owning ticket for the first time, and the new addition
covers the multi-step-git-operation case (`cherry-pick`/`rebase`/`merge` with `--continue`) the
original guidance didn't reach — with the "do not discard the shard" correction and the staging
procedure both included, exactly as approved. The cross-session-mid-command case remains
explicitly out of scope, per the wording's own final sentence.

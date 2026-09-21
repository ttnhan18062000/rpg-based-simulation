---
status: active
layer: guidelines
authority: P1
audience: agent
tags: [ai, process-improvement, agent-monitoring]
---

# Agent Session Reset Boundaries

Read at every reset-eligible point — every line here is paid for repeatedly. Kept short on
purpose.

**HARD** — everything that matters is durable (ticket/artifact files, a pushed branch, the PR,
memory) and nothing is in flight. Write the handover note, then say "safe to `/clear`."

**SOFT** — durable artifacts already hold the working state, so compaction is harmless. Don't
propose a full `/clear`.

**NEVER** — state lives only in the conversation, or something is still running.

## Universal blockers (any one forces NEVER, overriding the map below)

- A finding or decision that exists only in chat — write it to a ticket, artifact, or memory first.
- A running background task or `Workflow`.
- An unanswered user question.
- A mid-git operation (conflict, rebase).
- An unpushed commit.
- A durable lesson not yet saved to memory.

## Boundary map

| Process | HARD | SOFT | NEVER |
|---|---|---|---|
| PR lifecycle | Merged + synced. PR open, CI green, awaiting merge — only if the handover records PR#/branch. | — | CI still polling; conflict resolution in progress. |
| Hand-orchestrated ticket | Finalize closed + pushed. | After Investigate/Plan, with `investigation.md`/`plan.md` written to `staging_artifacts/`. | Mid Implement/Test. |
| Formal `Workflow` run (`implement-ticket`, `implement-epic`, `create-tickets`, `investigate-simulation-result`, `simq-audit`, etc.) — the orchestrating session | Workflow finished, results reviewed and recorded. Phase agents already run in fresh contexts of their own — this row is about the orchestrator only. | — | While running. **Unknown, recorded as unknown, not assumed**: whether a background completion notice survives a `/clear`. |
| Epic | Between children: each child closed + pushed, `SEQUENCE.md` updated. | — | Mid-child. |
| Planning/design | Plan/tickets filed and handed off. | — | Mid decision thread. |
| Investigation/retro | Findings written to a ticket or retro notes and committed. | — | Chat-only. |
| Cross-session wait (awaiting a peer) | Only if the handover names what's awaited, from whom, and for which ticket. | — | Handover doesn't name all three. |
| CI triage | Conclusion recorded (ticket/report). | — | — |
| Simulation run (RPG side) | Result registered. | — | — |

Any shape not listed defaults to the Universal Blockers above; if none apply, treat it as SOFT,
never HARD — don't propose `/clear` for an uncovered case.

## Handover note format

One file per **role name**, not `cwd` — several sessions share the main checkout (the same hazard
shape as the confirmed `.claude/current_run` sidecar contamination). Target ~2k tokens. Standing
rules are never restated here; `CLAUDE.md` and memory already hold them — this is only *this
session's* current open state.

```markdown
# Handover — <role name>
Updated: <date>

## Open
- Branch: <name> · PR: #<n> or none
- Pending user decisions: <...> or none
- Awaiting: <peer/ticket>, or none

## Pointers
- <ticket/doc paths relevant to resuming>
```

## Reachability

`.claude/handover/*.md` (gitignored, one file per role). A `SessionStart` hook (`source: "clear"`)
lists file paths + first-line titles only — never injects the note bodies themselves, keeping the
per-clear cost small regardless of how many roles have one.

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
| Hand-orchestrated ticket | Finalize closed + pushed. | After Investigate/Plan, with `investigation.md`/`plan.md` written to `agent-working/staging_artifacts/`. | Mid Implement/Test. |
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
shape as the confirmed `.claude/current_run` sidecar contamination). The three header lines under the
title say what the note belongs to (role, domain and worktree, branch and PR); the title stays first so the
SessionStart listing is unchanged, and `tools/handover_transit.py` records the same facts per file in its
bundle (`belongs_to`: role, domain, ticket, branch, kind). Target ~2k tokens. Standing
rules are never restated here; `CLAUDE.md` and memory already hold them — this is only *this
session's* current open state.

```markdown
# Handover — <role name>
Role: <role id> · Domain/worktree: <domain> / <worktree>
Branch / PR: <branch> · #<n> or none
Updated: <date>

## Open
- Branch: <name> · PR: #<n> or none
- Pending user decisions: <...> or none
- Awaiting: <peer/ticket>, or none

## Pointers
- <ticket/doc paths relevant to resuming>
```

## Reachability

`.claude/handover/*.md` (gitignored, one file per role). The `SessionStart` hook
`tools/sessions/session_start_hook.py` (`startup`, `resume`, `clear`, `compact`) resolves the session's role
from the harness signals, binds the session to it and injects that role's card and **only that role's**
handover note. A session that resolves no role (a plain `claude`, or disagreeing signals) gets the older
fallback instead: file paths and first-line titles only, on `clear`, never the note bodies, plus one line
saying how to launch with a role. Everything fails open.

## Launching a role (`cc`)

`python3 tools/sessions/launch.py <role>` resolves the role from `registries/session_roles.yaml`, makes sure
its worktree exists (a missing one is recreated from the role's recorded branch, never from scratch), then
`exec claude --name <role> --agent session-<role>` with `SESSION_ROLE=<role>`. A role with `max_sessions: N`
may run `<role>-2` .. `<role>-N`. Runtime state lives in `<git-common-dir>/session-roles/` (see
`tools/sessions/state.py`); liveness is computed from `/proc`, never stored.

- a **live** role is refused; a **released** or unknown one starts fresh;
- an **orphaned** role (its process is gone, no clean end) is never started or resumed silently: the launcher
  prints the evidence (transcript age, dirty and unpushed state, any git operation left in progress, handover
  age and "Awaiting", candidate transcripts) and asks for `--action resume|replace|inspect`; non-interactive
  runs exit 3 instead of choosing. Resume is always by session id, and only of the dead holder's own session
  by default; replace keeps the old transcript.
- `--dry-run` prints the exact command and changes nothing.

One-line shell alias (installing it is the owner's step): `alias cc='python3 tools/sessions/launch.py'`.

## Moving sessions between machines

A transcript does not cross machines; the handover note is the only continuity that can.
`tools/handover_transit.py` carries notes, the untracked `.claude/handover/drafts/` tree and the
project memory through `agent-working/handover-transit/<host>/` (one rolling bundle per source
host; files stored with a `.txt` suffix so registry and validators ignore them).

**A transit bundle carries only OPEN handover state:** role notes, unmerged drafts and memory. Completed
work, merged drafts and probe evidence are never exported. `export` skips a draft whose ticket is in
`agent-working/tickets/done/` or tracked on `origin/main`, anything under an `evidence` directory, a folder
whose ticket drafts are all finished, and a file whose bytes are already on `origin/main` (`--include-all`
turns this off). A role also removes its own completed drafts from `.claude/handover/drafts/` when it closes
the work, so the next export has nothing stale to skip. Every manifest row records what it belongs to
(role, domain, ticket, branch, kind); drafts take the exporting session's role (`--role`, or `SESSION_ROLE`
from the launcher, never guessed: unresolved is listed as `unattributed`).

1. On the machine being left: `python3 tools/handover_transit.py export` (`--roles a,b`,
   `--no-drafts`, `--no-memory`, `--role <role>` narrow or attribute it), commit and push the branch (a
   PR's own export step does this already — see `delivery_process.md`).
2. On the new machine: pull, then `python3 tools/handover_transit.py import <host> --role <your role>`
   (only that role's notes and drafts plus memory; unattributed and other roles' items are listed as
   skipped, never silently dropped; `--dry-run` first if unsure). Every sha256 is verified before any write; a differing local file is backed up
   as `<name>.local-backup-<ts>` and reported.
3. Start a fresh session per role and read its note. A `SessionStart` hook (`startup`, `resume`,
   `clear`) names any bundle this host has not imported.
4. When every machine that needs it has imported: `python3 tools/handover_transit.py discard <host>`
   (refuses without an `.imported-*` marker unless `--force`). `status` lists bundles.

Export on the machine you are leaving, then import on the new one; importing an older bundle over
a newer local note is the one way to lose work, which is why differing files are backed up.

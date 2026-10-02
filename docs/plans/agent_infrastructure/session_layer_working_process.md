---
status: active
layer: ai
authority: P2
audience: agent
date: 2026-10-02
tags: [ai, process-improvement, delivery, agent-monitoring]
---

# Session-Layer Working Process — Roles, Launch, Routing, Batches, Worktrees

**Purpose**: today several interactive Claude Code sessions cooperate on this repo, and the user
hand-orchestrates them: tells each who it is, what it may touch, who to ask, when to `/clear`, which
worktree to use. This plan makes that **configuration, not conversation**: a session is launched
with a role, learns its boundaries from the repo, routes out-of-boundary questions by a table, and
the user keeps only the decisions that are genuinely theirs.

This is a plan, not a commitment. Nothing here changes behaviour until a child ticket ships. It
extends the agent-working track (`agent_working_direction.md`); it does not replace the agent
layer (`.claude/agents/`, workflows), it adds the missing layer above it.

## 1. The problem, with evidence

All observed 2026-09 to 2026-10-02 in this repo.

| Symptom | What happened | Root cause |
|---|---|---|
| Role knowledge is scattered | Roles live in ~7 per-machine memory files (`project_session_role_division`, `project_semantic_control_plane_role_division`, `project_test_architecture_reviewer_role`, `project_mechanism_registry_ownership_split`, `feedback_route_work_via_rpg_feature_planning`, `feedback_implementer_owns_all_commits`, `feedback_worktree_by_default`), handover notes, and prompts the user types | no single repo-versioned source |
| Stale role note causes a misroute | `rpg-feature-planning` told `agent-working-design` a `derived_stats` registry decision was its call; its own note said agent-working owned `mechanisms.yaml` (true of tooling, false of content) | ownership recorded as prose, at whole-file grain |
| Role ambiguity after context loss | a shared memory note ("planner never implements") was read by `rpg-implementer` after compaction and surfaced a false rule; the user had to be asked | memory is shared by every session in the directory, a role is not |
| The hook cannot tell a session who it is | `session_start_handover_hook.py` lists **all** handover notes and says "read the one matching your role" | the harness gave it no role to match |
| Git cannot settle ownership | every agent commit is authored by the user | authorship carries no role |
| Batch discipline lives in the implementer's head | PR #276 merged its `src/` change while all four tickets stayed in `tickets/inprogress/` (Finalize never ran), found only by a peer reading it | no role-level "a batch is not done until..." contract |
| Worktree and branch sprawl | 307 local and 273 remote branches, ~7.6 GB of worktrees, disk hit 100% on 2026-10-02 and blocked a push; cleaned by hand (240 local, 161 remote deleted) | no owner, no inventory, no retirement rule for worktrees or branches |
| Role name leaks into data | closure events carrying the session name as `agent` tripped the `vocabulary_drift` ratchet (174 vs 162) | no separate field for session role |
| The user is the router and the clock | idle sessions need a typed prompt to start (observed repeatedly; see 9.5 for the unresolved platform question) | no routing table, no wake convention |

**Non-goals.** No new orchestration engine. No replacement for `Workflow` or the agent layer. No
removal of the user's authority over push, merge, governing files. No attempt to make sessions
autonomous of the user; the goal is fewer *repeated* instructions, not fewer decisions.

**Architecture invariant (added after external review).** The session layer is a *thin control
plane* for long-lived interactive sessions. It knows identity, responsibility, authority, routing,
placement, lifecycle and handover state. It does **not** own feature decomposition, implementation,
domain decisions, test strategy, workflow phases or simulation semantics; those stay in the existing
planning, ticket, workflow and agent layers. It is not a second workflow engine.

## 2. Concepts

- **Domain**: a slice of the repo with an owning track. Three work today: `rpg` (simulation and game
  logic, including the world-rule catalog), `agent-working` (pipeline, monitoring, delivery tooling,
  agent definitions) and `testing` (test architecture). More (UI, assets, ...) are added later with
  one domain overlay and three seats. `world-rules` is not a domain: its design work is the `rpg`
  designer seat.
- **Function** (owner decision, 2026-10-02): what a session does, independent of domain. Exactly three:
  - **`designer`** (designer / brainstormer): crafts plans from the user's requests and from major
    issues; proposes directions to the planner. Advisory; never dispatches, never commits.
  - **`planner`** (planner / reviewer): turns confirmed plans and epics into detail tickets, dispatches
    batches to the implementer, answers the implementer's questions, reviews PRs. The domain's hub.
  - **`implementer`**: code, tests, commits, CI, PR, Finalize.
- **Role (seat)** = (domain, function). **Every domain has the full set of three seats.** The **role id**
  (`<domain>-<function>`) is the **permanent identity**; it never depends on which session holds it.
  A seat is held by a session or is explicitly **unstaffed** (a seat property in the manifest). Who holds
  a seat is **runtime state**, not manifest content: a session may end, crash or be replaced, and a new
  instance takes the same seat. A session may temporarily hold two seats while one is unstaffed; the
  roster check reports it.
- **Session (instance)**: one running Claude Code instance holding a seat, bound to a worktree, named by
  the role id (`--name <role-id>`). Instances are disposable; roles are not.
- **Role card**: the short text a session receives at start and after `/clear`.
- **Batch**: the unit of delivery, one branch and one PR (`delivery_process.md`).

**Composition, not N x M cards.** A role card is `function template` + `domain overlay` + `role
entry`. Three function templates and one overlay per domain (three now) cover the matrix; adding a
domain such as UI or assets costs one overlay plus three seats, not a new set of cards.

- Function template: what the function may do (commit? push? open PR? edit outside drafts?),
  its reset boundaries (the HARD/SOFT/NEVER map in `agent_session_reset_boundaries.md`), its
  hand-off format, its batch obligations.
- Domain overlay: owned path globs (with content-vs-tooling splits), the docs to read first
  (Mechanics Bible, engine contracts, the atlas), domain skills (`combat-mechanics`,
  `systems-economy`, ...), domain-specific gates.
- Role entry: the session name, worktree name, who it routes to, standing grants, handover file.

## 3. Roster: three seats per domain

Owner decision (2026-10-02): every domain has the full set of three seats.

**The table lists seats (permanent role ids) and, in the last column, the session that holds each one
*today*.** Those session names are the current **instances**, not the future identity: a seat is
identified by its role id, instances come and go, and from the first launch through `cc <role>` a seat's
session is named by its role id. Existing sessions keep running under their old names until they are
next relaunched; the manifest keeps the old name as `legacy_session_name` only so the migration can find
them.

| Seat (role id) | Domain | Function | Held today by (instance) |
|---|---|---|---|
| `rpg-designer` | rpg | designer | `world-rule-catalog-design` |
| `rpg-planner` | rpg | planner / reviewer | `rpg-feature-planning` (also owns the semantic-control-plane epic and the mechanism-registry content) |
| `rpg-implementer` | rpg | implementer | `rpg-implementer` |
| `agent-working-designer` | agent-working | designer | `agent-working-design` |
| `agent-working-planner` | agent-working | planner / reviewer | **unstaffed**; `agent-working-design` holds it for now |
| `agent-working-implementer` | agent-working | implementer | `agent-working-implementer` |
| `testing-designer` | testing | designer | **unstaffed** (the roadmap's author became the reviewer) |
| `testing-planner` | testing | planner / reviewer | `test-architecture-reviewer` |
| `testing-implementer` | testing | implementer | `test-architecture-implementer` |

How to read it:
- `world-rules` is not a domain; its briefs go from the `rpg` designer to the `rpg` planner, as today.
- Two seats are unstaffed today (`agent-working-planner`, `testing-designer`). The manifest marks a seat
  `unstaffed`; who holds it meanwhile is runtime state, and the roster check reports a seat held by a
  session that does not own it, so it is staffed deliberately and not by drift.
- **Practice changes the model implies** (to confirm, 12.3): detail tickets belong to the planner, so
  `test-architecture-implementer` stops writing them; `agent-working-design` stops planning and
  reviewing once `agent-working-planner` exists.
- A new domain (UI, assets, ...) arrives as one overlay plus three seats, each staffed or explicitly
  unstaffed with a named holder.

## 4. The role manifest (single source of truth)

**Where**: `registries/session_roles.yaml` (machine fields, validated) plus prose in
`docs/guidelines/session_roles/` (`functions/<f>.md`, `domains/<d>.md`). The
`--agent` files `.claude/agents/session-<role>.md` are **generated** from these (never hand-written);
M0d may force a separate directory (12.3).

**Why a registry, not memory**: memory is per-user, per-machine, shared by every session in the
directory, and unversioned. A role is per-session and must survive a machine change, a review, and
a diff. Memory files keep pointers only ("see `session_roles.yaml`"); the define-once rule applies.

**Canonical location and the existing orchestration contract.** There is exactly one source of truth:
`registries/session_roles.yaml` plus `registries/session_authority.yaml`. `agent-orchestration/` was
considered as the home and **rejected on repo evidence**: its README scopes it to "the provider-neutral
semantic contract for the `implement-ticket` workflow", states it has zero consumers today, and marks
its authority direction as future ("one-way future-authority"). A session roster is neither
implement-ticket-specific nor yet consumed, so it does not belong in that contract. The session layer
only **references** agent roles (`agent-orchestration/roles/*.yaml`, delegated subagent roles) by id and
never redefines them. Name the two apart everywhere: **agent role** (delegated subagent) versus
**session role** (long-lived interactive peer). If a provider-neutral rendering of the roster is wanted
later (for a Codex session), it is *generated* from the registry, never a second definition.

The manifest separates five kinds of information that were mixed in the first sketch (external
review, Appendix I). They may share a physical file, except authority:

1. **Identity**: role, domain, functions, `session_name`.
2. **Responsibility**: `owns` / `owns_not` globs and `routes` (who owns what is outside this role).
3. **Capability**: tool allowlist, `may_write` paths (what the role *can* touch).
4. **Placement**: the worktree a role works in and `max_sessions`. The **writer slot is a property of
   the worktree, not of a role** (see the `worktrees:` resource below).
5. **Authority**: what needs the user, standing grants. **Lives in its own file,
   `registries/session_authority.yaml`, treated as a governing file** (see 10).

A role can own a *decision* without being allowed to implement it, and the reverse; the schema keeps
the two apart instead of relying on prose.

```yaml
- role: agent-working-designer
  identity:   {domain: agent-working, function: designer, session_name: agent-working-designer,  # = role id
               legacy_session_name: agent-working-design,   # today's holder, until it is relaunched via `cc`
               seat_status: staffed}                         # staffed | unstaffed
  responsibility:                      # `owns` is normally inherited from the domain overlay
    owns: [tools/agent-monitoring/**, tools/delivery/**, docs/agent-monitoring/**, docs/plans/agent_infrastructure/**]
    owns_not: [registries/mechanisms.yaml]   # content -> rpg-feature-planning; the tooling stays here
    routes: {"registries/mechanisms.yaml": rpg-feature-planning, "src/**": rpg-feature-planning,
             "tests/architecture/**": test-architecture-reviewer}
    accepts_dispatch_from: [user]          # who may assign work to this role (section 9.0)
  capability: {may_write: [".claude/handover/drafts/**", "docs/plans/agent_infrastructure/**"]}
  placement: {worktree: agent-working, max_sessions: 1}   # per-role policy, not "role == process"
  handover: .claude/handover/agent-working-designer.md   # keyed by role id; the legacy note is migrated at first relaunch
```

```yaml
# registries/session_roles.yaml, resource section: exclusive resources are modelled as resources
worktrees:
  agent-working:                        # one worktree per domain, shared by its three seats (as today)
    writer: agent-working-implementer   # exactly one role may commit/push here; must hold `implementer`
    # the writer slot is taken as a lease at SessionStart (see section 5), not inferred from process names
```

```yaml
# registries/session_authority.yaml  (governing-file class: user confirms the literal diff)
authority:
  agent-working-design:
    needs_user: [push, merge, governing_file_edit, workflow_run, delete_remote_branch]
    grants: []                        # dated, quoted, revocable
```

Rules the validator enforces: every `owns` glob resolves to files; no two roles own the same path
without a stated split; every role has a handover file and a worktree; every `routes` target is a
real role; `session_name` is unique within the roster; every worktree declares exactly one `writer`,
and that role holds the `implementer` function (planners and designers hand drafts, as today). It also
**reports** (never blocks) per-role complexity: number of role-level overrides, routes unique to one
role, authority exceptions, so composition does not quietly decay into seven hand-written roles.

**Staleness**: reuse the planning-doc staleness sweep so a manifest entry that cites a deleted
path, ticket, or role is reported, not trusted. This is the exact failure from section 1.

## 5. Launch: configuration instead of typing

Platform facts (documented, per the Claude Code docs; verify in the spike, section 12.1):
`--name` fixes a session name visible as `session_title` to hooks and to `ListAgents`, surviving
`/clear` and `--resume`; `--agent <name>` runs the main session as a `.claude/agents/<name>.md`
definition with its prompt, tool allowlist and model; `SessionStart` receives `session_id`,
`source`, `session_title`, `agent_type` and can inject `additionalContext`; environment variables
set before launch reach hooks.

`tools/sessions/launch.py <role>` (plus a one-line shell alias `cc <role>`):

1. Resolve the role from the manifest. Unknown role: list the roster, exit.
2. Ensure the worktree exists (section 8); create off `origin/main` if missing; `cd` into it.
3. Compose the role card from function template + domain overlay + role entry (<= ~400 tokens).
4. `exec claude --name <role-id> --agent session-<role>` with `SESSION_ROLE=<role>` in the
   environment as one *input signal* (not the sole source of identity, see Binding).
   `--resume` is a flag on the launcher for continuing a named session.
5. **Concurrency.** `max_sessions` is a per-role policy checked best-effort at launch (the launcher
   cannot call `ListAgents`; it may inspect the process table, which is advisory only). The *exclusive
   resource* is the **writer slot of a worktree**, enforced by an explicit **writer lease**, not by
   process names: at `SessionStart`, the role named as a worktree's `writer` takes a lease record in
   that worktree (role, session_id, ts, untracked). A commit/push-class operation by any other role in
   that worktree is an authority-class event (section 10: deny or ask). A stale lease (the holder is
   gone) is released by the user or by the same role re-taking it after `/clear`; it is never silently
   stolen. "One role = one process" stays a v1 policy value; read-only clones or overflow investigators
   come later by raising `max_sessions`, without touching the lease model. The lease mechanism itself
   (file versus git-native) is decided in M2 from M0 evidence.
6. **Existing instance?** Read the role's `instance.json` (6.1). A **live** instance: refuse and say
   so. An **orphaned** one (the process is gone and it did not end cleanly): do not start blindly; run the
   recovery flow in 6.1. None, or cleanly released: start fresh.

**Binding (revised in round 2).** Three identities are kept apart, and **none of the human-readable
ones is the root of identity**: the **role** (logical), the **session id** (the current runtime
instance) and the **session name / title** (a UX and recovery *signal*). `/clear` allocating a new
session id with no parent link (verified 2026-09-27) is **not a problem**: the role is simply resolved
again for the new instance. Continuity does not come from a permanent process identifier but from
`role configuration + role handover + batch state`.

`SessionStart` runs one resolution step: gather the trustworthy signals the harness actually supplies
(`agent_type` from `--agent session-<role>`, `session_title`, the `SESSION_ROLE` environment variable
set by the launcher, the worktree path), resolve the role, bind the **current** `session_id` to it, and
write a **binding record** (`session_id`, `role`, `manifest_digest`, `worktree`, `source`, `signals`,
`ts`) next to the existing per-session `current_run.<session_id>` sidecar. The record is runtime state,
not a role definition. If the signals **disagree** or none resolves, the hook does not guess: it injects
nothing privileged and says how to launch with a role. **Which signal wins is an M0 result** (12.1 a, f,
k, m), not a planning assertion; the plan assumes only that at least one harness-supplied signal
(`agent_type` first candidate) survives start, resume and clear.

**Manifest revision.** The card carries the manifest digest. On resume or clear, if the digest
differs from the previous binding record, the hook says what changed in a line or two; an authority
*reduction* is flagged for explicit re-evaluation before any privileged action. Re-injecting a card
cannot remove stale policy already in a resumed context, so the diff is what makes staleness visible.

**Name collisions.** The plan does **not** rely on `session_name` being unique. The official docs say
two things that must both be tested: starting, resuming or renaming an interactive session with a name
another live local session already holds renames the new one to a variant, **and** sessions can still
share a name (an older Claude Code version, or a name Claude Code generated), in which case other
identifiers disambiguate. Either behaviour would break a name-keyed lookup, which is why the name is a
signal and not the key. M0m records what actually happens.

**Launcher bypass.** A native `claude --resume` outside the launcher does not set `SESSION_ROLE`; the
hook then resolves from `agent_type` and `session_title` (and the worktree) with the same disagreement
rule; if nothing resolves it injects nothing and says how to launch with a role. The resolved binding
record, not the environment variable, is what monitoring reads (section 11).

The `SessionStart` hook (`startup`, `resume`, `clear`, `compact`) injects the card and **only that
role's** handover, not every role's title (cheaper than today and unambiguous). Unknown or missing
role (a plain `claude`): inject nothing and say once how to launch with a role. This is a context hook, not an
authority one, so it fails open (injects nothing), as the current hook does.

## 6. Session lifecycle and `/clear`

States: `launching -> active -> (batch work) -> handover -> clear/resume -> active ... -> retired`.

- **Start / resume / clear / compact**: all re-resolve the role and re-inject the card (section 5).
  `/clear` creates a new session id; the role is re-resolved, and role configuration plus the handover
  note carry the state. (`reference_clear_breaks_session_resume`: only the note crosses a clear.)
- **Reset boundaries**: the existing HARD/SOFT/NEVER map is per *process*; this plan adds it per
  *function* in the function template (an implementer's HARD is "batch merged and synced"; a
  designer's is "drafts handed off and acknowledged"; a planner's is "tickets filed and dispatched").
  The hook does not decide to clear; it reminds the role of its own boundaries and the
  token break-even (`/clear` pays off only past ~150k context).
- **Handover note**: one file per role (already true), with a fixed head: Role, Branch/PR,
  Pending user decisions, Awaiting (who), Next. The launcher creates a stub for a new role.
  Stale handover notes (role retired, branch merged) are reported by the roster check.
- **Idle**: a session with nothing in flight and an empty queue says so in its handover and is
  not asked to "continue"; the user wakes it by message or prompt (section 9.5).
- **Retire**: manifest entry `status: retired`, worktree kept until its last branch merges, then
  eligible for removal (section 8). Memory pointers to a retired role are removed in the same change.

### 6.1 Persistence and recovery after an unexpected termination

**Principle: the role id is the permanent identity; a session is a disposable instance.** Whatever is
needed to find, resume or replace an instance after a crash must therefore be recoverable **from the role
id alone**, without the owner remembering a session id, a worktree path or a name.

**What is persisted** (runtime state, per user and per machine, never committed). It lives in the **git
common directory**, `<git-common-dir>/session-roles/<role-id>/`, so it is shared by every worktree and
survives the removal of any one of them (`git rev-parse --git-common-dir` resolves to the same `.git` from
every worktree here, checked 2026-10-02):

- `bindings.jsonl` (append-only): the binding record of section 5, one per `SessionStart`:
  `session_id`, `role`, `source`, `worktree`, `branch`, `transcript path`, `process id`,
  `manifest_digest`, `ts`. This is the role's history of instances.
- `instance.json`: the current holder (the last binding) and its `state`: `live`, `orphaned` or
  `released` (set when an instance ends cleanly or the seat is retired).
- the writer lease (section 5), so a dead holder's lease is recognizably stale.

**Not stored by us, because it is derivable:** branch and open PR (`gh pr list --head <branch>`), dirty
files, unpushed commits, a git operation left in progress (merge, rebase and cherry-pick state), the
handover note (a file), batch status (section 11), and the **transcripts** Claude Code itself writes to
`~/.claude/projects/<slug of the worktree path>/<session-id>.jsonl`.

**Evidence already in this repo** (verified 2026-09-27): a transcript persists after its process ends;
`/clear` allocates a new session id and transcript with no link to the old one but **keeps the same custom
title**; `--resume` restores one side of a clear, never a merged view; the resume picker lists only the
sessions of the worktree it is launched from; `claude --resume <session-id>` works from anywhere. So the
recovery key is the **role id used as the session title**, which every instance of a role shares across
clears, and not a session id.

**Detect.** `cc <role>` and `status.py` read `instance.json`: process alive -> `live` (a second launch is
refused); process gone and not `released` -> **orphaned**. How liveness is checked (process id,
inbox socket) is an M0 item (q).

**Recover.** On an orphan, `cc <role>` never silently starts or resumes. It shows the evidence: last
activity (the transcript's modification time), worktree and branch, dirty and unpushed state, any **git
operation left in progress** (a NEVER-boundary state in `agent_session_reset_boundaries.md`), the open
PR and batch, the handover note's age and its "Awaiting", and the candidate transcripts for the role
(title = role id, newest first). It then offers three choices:

1. **resume** the newest transcript (`claude --resume <session-id>`), re-bound by the normal
   `SessionStart` resolution (section 5);
2. **replace**: start a fresh instance that reads the handover note and the git state; the old
   transcript is kept, never deleted;
3. **inspect** only.

The suggested default is *resume* when the transcript is newer than the handover note and *replace*
otherwise; the choice is the owner's (12.3). A resumed or replacing instance retakes the writer lease; a
stale lease is never stolen silently (section 5).

**What cannot be recovered, stated plainly:** in-flight background tasks and CI polls (restart them),
reasoning that existed only in the conversation, and peer messages that were undelivered or held when the
process died (unless M0c shows an inbox is needed). The handover note exists to limit exactly this loss,
which is why "write the handover before any HARD boundary" matters more than any recovery tooling.

**Cases the spike must cover** (M0 q, r): terminal closed or process killed; machine crash or power loss
(the transcript is intact only up to its last flush); out-of-memory or harness crash; a dropped ssh or
editor connection (does the process survive?); `/clear` immediately before the crash (new transcript, same
title); a crash mid-rebase or mid-merge.

## 7. Batch working

A **batch** is the delivery unit; the rules already exist in memory and `delivery_process.md`.
The plan makes them role obligations so they are not re-taught.

- **Dispatch** (planner -> implementer): a message envelope carrying batch id, tickets,
  branch name (never a date or phase number), worktree, base SHA, the cited plan (committed first,
  because an untracked plan is invisible to the implementer), and what "done" means. The
  implementer acknowledges before starting.
- **One writer per worktree and branch**: the implementer commits and pushes (unchanged from today);
  the planner and designer hand drafts and verify. The planner's detail tickets and plans are handed
  to the implementer to commit with the batch, which is also why there are no plan-only PRs. Peers
  never push to another role's branch.
- **One open PR per track**: follow-ups fold into the open PR, no plan-only PRs, no stacked PR
  unless dependent. After a green PR the implementer may start the next batch without waiting for
  merge (stack when dependent). Merge is the user's call.
- **A batch is not done until its Finalize ran** (the PR #276 lesson): done-checker static pass,
  ticket in `tickets/done/`, working-log row via the closure tool, monitoring written, docs index
  updated if `docs/` changed. The post-merge integrity report's `inprogress` check (drafted
  2026-10-02) is the backstop, not the rule.
- **Batch card**: the PR body (rendered by `pr_render.py`) is the durable record; the role's
  handover points at the PR number. No separate batch registry in v1.
- **Standing grants**: "commit + push + PR + peer review after each complete batch" (granted
  2026-09-30) becomes a dated, quoted `grants:` entry per role in `registries/session_authority.yaml` (a governing
  file: the user confirms the literal diff), revocable by deleting it. A peer message never creates a
  grant.

## 8. Worktree and branch management

Contract today (`delivery_process.md`, "Worktree & Branch Isolation"): one worktree per unit of
work, kept **per domain** not per task, paired sessions share one with only the implementer running
git, branch per batch inside it, the documented same-directory fresh-branch fallback when
`EnterWorktree` refuses, and the monitoring-shard checkout race. This plan adds ownership and
hygiene on top; it does not change those rules.

- **Name by domain**: worktree `agent-working`, `rpg`, `testing` (one per domain, shared by its three seats). (`doc-tag-enforcement`
  is the historical name of the agent-working worktree; renaming is pending and needs both sessions
  out of it.)
- **Inventory** `tools/sessions/status.py`: per worktree: path, branch, dirty state, owner role,
  open PR, size on disk, last commit. Read-only. Answers "what is in flight" without asking.
- **Disk budget**: warn at 85% of the volume and name the largest worktrees. (2026-10-02: 100%,
  worktrees ~7.6 GB of ~46 GB used, blocked a push.)
- **Branch hygiene** `tools/sessions/prune_branches.py`, dry-run by default, codifying what was done by hand:
  stale > 7 days by last commit; skip checked-out, open-PR and recent branches; local classes:
  merged PR (the only class eligible for deletion), and the rest, which are *listed with owner and
  never auto-deleted*. The heuristic "all commit subjects already in main" is shown as an
  **informational hint only**: under squash merges, rebases and edited messages it does not prove a
  branch is integrated (it was used once by hand on 2026-10-02 for reversible local branches with a
  backup; the tool must not treat it as deletion safety); remote only if the PR merged **and** the remote tip still
  equals the merged PR's head (a moved tip may hold later work); always write a name-to-SHA backup
  first; push deletions with `--force-with-lease` per branch. Execution stays user-approved (a
  remote delete is visible to everyone).
- **Worktree self-heal.** A role's worktree is named in the manifest. If `cc <role>` finds it missing or
  marked prunable (`git worktree list`), it recreates it from the role's branch (`git worktree prune`, then
  `git worktree add`), never from scratch, and tells the owner. Commits live in the shared object store, so
  a removed worktree loses only uncommitted files; the branch-backup file (below) covers a deleted branch.
- **Worktree retirement**: a worktree with no open PR and no unmerged unique commits, whose owning
  role is retired or idle past N days, is *reported* as removable. Removal is the user's call.
- **Shared-directory rules stay**: never bare `git stash`; shards are not discarded to clear a
  checkout; `git worktree add --detach` for throwaway checks, removed after, and never under `/tmp`
  for path-sensitive tests.

## 9. Routing and cross-session communication

### 9.0 Topology and message authorization: information may bypass the hub, work assignment may not
The documented patterns split into orchestrator-worker (workers never talk to each other; the
orchestrator decides everything) and open mesh. This repo is a **hybrid**: inside a domain the **planner** is the hub that dispatches to the implementer and takes its questions,
the **designer** is an advisory source of directions (not a dispatcher), across domains the planners
talk to each other, and the user is the supervisor above all hubs. The rule is: **information may bypass the hub; work
assignment may not.**

Three questions are kept apart, because answering one does not answer the others:

- **Delivery**: did the message arrive? (the harness; inbound controls, section 9.5)
- **Routing**: who owns the subject? (the manifest, 9.1)
- **Authorization**: may this sender assign this work to that role? (the receiving role's
  `accepts_dispatch_from`, in its function template and role entry)

| Message class | May be sent by | May be received by | Effect |
|---|---|---|---|
| `finding`, `fyi`, `ack` | any known session role | any role | no obligation to act; the receiver verifies before acting |
| `question` | any role, **directly to the named semantic owner**, across domains | the owner | the owner answers, or bounces once (9.3) |
| `request`, `handoff`, `dispatch` (anything that adds to or reorders another role's queue) | only roles in the receiver's `accepts_dispatch_from` (normally its own planner, or the user) | that role | actionable; from anyone else it is treated as an `fyi` and the receiver asks its own upstream |
| authority decision (push, merge, governing files, grants) | **the user only** | - | a peer message never creates user authority |

**A designer's output reaches its planner as a `handoff` only after the user has confirmed the
direction.** Until then it is a `finding` or a `question`: input the planner may use, not a work order.

Evidence in this repo, so this codifies practice instead of inventing it: findings and questions
already flow directly across domains (`test-architecture-implementer` and `rpg-feature-planning` to
`agent-working-design`; implementers reporting agent-process issues straight to the design session is a
recorded working agreement), while briefs and dispatch go through the planner (the `rpg` designer,
`world-rule-catalog-design`, sends briefs only to `rpg-feature-planning`; the user's standing rule is
to route work via the planner). The rule removes
the planner as a bottleneck for purely informational traffic and keeps it as the gate for work.

**v1 enforcement is advisory** (role card plus a logged `role_boundary` event). Classifying an ordinary
message as dispatch or information is a semantic judgement, so a hard block would need evidence of
harm first. `crossSessionInbound = accept` fixes *delivery only*; it does not authorize anything.

### 9.1 Who owns this?
`tools/sessions/route.py <path>` (or `--route-key <key>` for a named entry in `routes:`) answers from
the manifest: longest matching `owns` glob
wins; `owns_not` and `routes` carry the content-vs-tooling splits (`mechanisms.yaml` content ->
rpg, the advisory tooling -> agent-working). Liveness stays a model-side `ListAgents` call (a tool,
not a CLI). If the owner is not live, the session says so and asks the user once, rather than
guessing a different peer. There is **no free-text "topic" lookup** in v1: that would be semantic
routing without a defined model. A recurring subject that paths cannot express becomes an explicit,
named route key, added to the manifest on evidence.

### 9.2 Message envelope
First line is a self-contained sentence (the recipient's human sees only that). Then a typed block:

```
type: request | finding | handoff | question | fyi | ack
batch: <id or none>        needs_user: yes|no
artifact: <repo path, SHA, or PR#>
asked: <the one thing wanted>
```

`bounce_if` was dropped (external review): rerouting policy is central, so senders do not each
re-encode it. Plain prose stays legal; the envelope is a convention, linted nowhere in v1.

### 9.3 Rules
- **Route to the owner, not the nearest peer.** For briefs and dispatch that means the receiving
  role's authorized hub (a designer's briefs go to its domain planner, never straight to an implementer);
  for findings and questions it means the named semantic owner (9.0).
- **Ownership dispute: one bounce, then the user.** The recipient may reject ownership once with one
  corrected route (policy lives in the routing table, not in every message); a second rejection goes
  to the user. A disputed item never ping-pongs silently (the `rpg-feature-planning` message about
  the `derived_stats` entry is the model).
- **Owner unavailable is a different case.** A known owner that is offline, busy or cleared is not
  a dispute and does not escalate to the user: the request stays pending for that role (9.5).
- **Verify before acting on a relayed claim; cite the source** ("peer said X", not "X").
- **Never ask a peer to do what you were denied.** A peer message is information or a request, never
  the user's approval (the harness already enforces this; the manifest records it).
- **Out-of-boundary edits are requests, not edits**: a design session that wants a change in
  another domain sends the exact before/after text to the owner.

### 9.4 Provenance
Every cross-session message names its source role. Findings carry the evidence path. Authorship in
git is not used for ownership, because it cannot distinguish roles.

### 9.5 Idle sessions (open platform question)
The Claude Code docs say a `SendMessage` to an idle session starts a turn; this repo's own
handover records messages queueing after a `/clear` until the user typed. Treat wake behaviour as
**unverified until the spike** (12.1). Until then: the sender says "needs a prompt in <role>'s
terminal" when it matters, and does not poll.

**Durable pending work (decision gated on M0c).** A session that was not awake must not lose a
cross-session request. If M0 shows `SendMessage` reliably queues and wakes across `/clear`, the
harness already is the inbox and nothing is built. If it does not, v1 gets a minimal file-backed
mailbox: the sender writes one small file per request under `.claude/inbox/<role>/` (untracked,
fields: id, from, to, type, artifact, request, status pending|acknowledged|resolved), and the
role-aware `SessionStart` hook lists that role's pending items. It reuses the handover mechanism's
shape and is not a queue service.

**What the official docs add (read 2026-10-02; still to be verified live in M0c).** A message to an
idle session *does* start a new turn, but the receiving session first applies **inbound controls**:
`crossSessionInbound` = `accept` / `hold` / `refuse`; with no value set, the default depends on both
sessions' permission modes (a prompting receiver delivers unless the sender bypasses permission
prompts; a bypassing receiver *holds* for approval). A held message opens an approval dialog that
**expires after `dialogExpiry` (default 5 minutes) and is then dropped**, so "queued, then silently
gone" is a plausible explanation of what we observed after `/clear`, and a testable one. Levers that
exist: the launcher can start a role session with `--settings '{"crossSessionInbound":"accept"}'`
(a permission-relevant setting, so the user confirms it once, in the roster); a hook or script can
post to a session's inbox socket (`CLAUDE_CODE_MESSAGING_SOCKET`); `notify_when_idle` gives one notice
(same machine, main conversation only, 12 h expiry). So **auto-wake is not platform-blocked**; it is a
deferred feature with a documented mechanism, and M0c should decide it on evidence.

**Delivery is not authorization.** Setting `crossSessionInbound = accept` for role sessions only makes
delivery reliable; it does not make a received `request` actionable. The receiver still applies 9.0.

## 10. Authority and boundaries

Default authority by function; the manifest overrides per role, with `needs_user` always winning.

| Action | designer | planner | implementer |
|---|---|---|---|
| Edit files in own `owns` | drafts only | ticket and plan drafts, review notes | yes |
| Edit outside own `owns` | request to owner | request to owner | request to owner |
| Commit / push own branch | no (hands drafts) | no (hands drafts to the implementer) | yes, with grant |
| Open / update PR | no | no (comments on PRs) | yes, with grant |
| Review a PR, answer implementer questions | no | **yes** (comment; the merge stays with the user) | no |
| Merge | **user** | **user** | **user** |
| Governing files (`CLAUDE.md`, `settings.json`, hooks) | **user, literal diff** | same | same |
| Run `Workflow` / spawn at scale | **user opt-in** | same | same |
| Delete remote branches, worktrees, data | **user** | same | same |

**Threat model (stated so it is not over-read).** v1 is a **guardrail, not a sandbox.** It protects
against agent mistakes, stale role context, accidental destructive commands, permission drift, and
ordinary model behaviour taking an action outside its configured authority. It does **not** claim to
stop a process with arbitrary shell execution that is deliberately bypassing the hook (indirect
commands, wrappers, scripts, another executable, edited policy files). That is an OS-level isolation
problem (sandboxing, separate OS users) outside this plan; nothing here is an adversarial boundary.

**Enforcement is split in two:**

- **Authority and destructive boundaries: deterministic guardrails from v1, once M0e shows what the
  hook can do.** Classes: merge without authority, remote-branch deletion, commit or push by a role
  that is not the worktree's writer, governing-file edits, and edits to `registries/session_authority.yaml`
  (a subject must not silently rewrite the policy that constrains it). For an operation the hook can
  classify:
  - forbidden for the role -> **deny**;
  - requires the user -> **ask** (the user confirms);
  - allowed -> continue per policy;
  - classification or parsing **uncertain** (a command that partly matches an authority pattern, or
    shell indirection such as `eval`, `bash -c`, a variable-expanded `git` or `gh`) -> **ask, never
    silently allow**.

  If the hook API cannot return "ask", the fallback is **deny with a message telling the session to
  ask the user**. What the harness does when the hook itself fails (crash, unparseable input) is an M0e
  result; **this plan does not claim "fail-closed" until that is shown.** Because it is unproven, the
  authority-class command patterns are *also* declared as harness-native permission rules
  (`permissions` ask and deny lists for `git push`, `gh pr merge`, remote-branch deletion), which the
  harness enforces by itself whether or not the hook runs; the hook adds the role-conditional logic
  (who is the writer, which grants exist) on top. Any edit that touches `settings.json` needs the
  user's literal-text confirmation.
- **Authority-file integrity: governing-file class, no external pin in v1.** Changes to
  `registries/session_authority.yaml` go through the user's literal-diff confirmation (as `CLAUDE.md`
  and `settings.json` do today), a hook deny or ask on any Edit, Write or Bash touching it, and normal
  git review. **Decision (round 2): the home-directory digest pin is deferred.** A session running as the
  same OS user can write both the repo file and a pin under that user's home, so these are two
  locations, not two principals: it would give tamper *evidence*, not isolation, at the cost of a
  user-maintained secret and a new failure mode. If adopted later it should digest a **canonical
  session-policy bundle** (roles, authority, function templates, domain overlays and the generated
  agent files, since authority decisions depend on all of them), be described as tamper evidence, and
  remain defense in depth. What stays in v1: the generated `session-<role>.md` agent files are checked
  by **regeneration** (a drift check in the M1 validator), a cheap integrity check for derived artifacts.
- **Semantic and organisational boundaries: advisory first.** Wrong semantic owner, editing a
  neighbouring domain, an unusual route, handoff formatting, responsibility overlap, message
  classification (9.0): context-dependent and prone to false positives. Warn, log a `role_boundary`
  monitoring event, and harden only what recurs after a measured window (target 4 weeks of retro data);
  hardening is its own ticket and needs the user's literal-text confirmation of any `settings.json`
  change.
- **Free hard boundary**: a `--agent` tool allowlist makes pure review roles read-only.

## 11. Observability and roster management

- **`session_role` field** on monitoring events and runs, taken from the **resolved per-session binding
  record** that `SessionStart` writes (section 5), **separate from `agent`** (the `vocabulary_drift`
  ratchet governs `agent`; the closure-event incident shows why they must not share a field).
  `SESSION_ROLE` is one *input* to that resolution, not what monitoring reads, so a session resumed
  outside the launcher is still attributed correctly, or recorded as `unresolved`. Use the existing
  per-session `current_run.<session_id>` sidecar, not the shared one (the cross-session contamination
  ticket).
- **Headline metric: manual orchestration actions per completed batch**, the direct measure of whether
  this layer works. It counts **categories of repeated instruction**: role reminder, routing
  correction, manual wake, worktree correction, boundary reminder, handover recovery. It does **not**
  count genuine owner decisions, design feedback or new requirements: the goal is fewer *repeated*
  instructions, not fewer decisions, so a raw count of user prompts is explicitly *not* the metric.
  How the categories are tagged is an M0j/M6a question (a prompt-submit hook payload may allow sampling;
  failing that, a one-line owner-side tally per batch). The aim is that it falls.
- **Batch latency is three measures, never "PR green = done"**: dispatch to PR green is
  *implementation latency*; PR green to finalized is *finalization latency*; dispatch to finalized is
  *batch cycle time*. Batch status is derived (dispatched, acknowledged, implementing, PR open, PR
  green, finalized, merged) from existing PR and ticket artifacts, with no batch registry.
- **Secondary retro measures** (added to the retro, not a new report): misroutes (a message answered
  "not mine"), bounces, idle stall (message sent to first reply), handoff latency, `role_boundary`
  warnings, `/clear` count and tokens re-read after clear.
- **Roster ownership**: the manifest is owned by `agent-working-design` (draft) and
  `agent-working-implementer` (commit); **changes to roles, grants and authority need the user's
  confirmation of the literal diff** (a governing-file-class edit).
- **Roster check** (report-only, run by the retro hook): stale role citations, roles with no
  handover, worktrees with no role, sessions live under an unknown name, **orphaned instances**
  (with their in-flight work), one session holding two seats, an unstaffed seat with no named
  holder.
- **Review cadence**: the roster is reviewed at each retro; a role that did not act for two retros
  is proposed for `retired`.

## 12. Plan, phasing, and open questions

### 12.1 M0 - spike (verify before building)
One day, no tickets filed beyond one investigation. Verify against the real harness, with positive
controls: (a) `--name` survives `/clear` and `--resume` and appears as `session_title` in
`SessionStart`; (b) `--agent session-x` applies the tool allowlist to the **main** session; (c)
`SendMessage` to an idle session in a clean launch wakes it (and what changes after `/clear`); (d)
an agent file named `session-*` does not pollute the Agent-tool subagent roster in a way that makes
the model spawn it; (e) a `PreToolUse` hook receives `session_id` and can match an Edit path and a
Bash command (this gates the hard boundaries in section 10); (f) a session started by the launcher
and then resumed *outside* it keeps its name and role signal; (g) renaming a live session after
launch; (h) forking a session: which identity the fork inherits; (i) changing the manifest between
launch and resume, and what the hook sees; (j) the prompt-submit hook payload (for the headline
metric); (k) confirm `/clear` yields a new session id while the name persists; (l) `crossSessionInbound` and
permission-mode combinations: which sender/receiver pairs deliver, hold or drop, and what the 5-minute
`dialogExpiry` does to a message sent to an idle role session; (m) the duplicate-name behaviour (variant rename
*and* shared names) and what `session_title` reports; (n) what a `PreToolUse` hook can return for an
authority-class operation (deny / ask / allow), and what the harness does on a classification failure,
unparseable input or a hook error: this decides whether any section 10 guarantee can be stated; (o) a
**signal-precedence table**: for `agent_type`, `SESSION_ROLE`, `session_title` and `session_id`, whether
each is present and stable across start, resume, clear, compact, fork and rename;
(p) persistence facts: the session title is written into the transcript and survives `/clear`, the
transcript path convention holds for a worktree, and `claude --resume <id>` works from another cwd;
(q) liveness: how to tell a live instance from a dead one (process id of the harness, inbox socket);
(r) the crash cases listed in 6.1, with what survives each.
If official documentation and a local observation disagree, the local behaviour is recorded and the plan
is updated from it.
Outcome: a go / adjust decision on sections 5, 9.5, 10, before M1, plus the signal-precedence table.

### 12.2 Milestones (epic children)

| M | Child | Delivers | Depends |
|---|---|---|---|
| M0 | Harness spike | a recorded result for every item a to r in 12.1, written to `investigation.md` | - |
| M1 | Manifest + validator | `registries/session_roles.yaml` and `registries/session_authority.yaml`, function templates, domain overlays, validator (globs resolve, no overlap, handover exists, one writer per worktree, generated agent files match the manifest), the 7 memory files migrated to pointers | M0 |
| M2 | Launcher + role-aware SessionStart | `tools/sessions/launch.py`, `cc` alias, signal-based role resolution and binding record, card injection, own-handover-only, writer lease, the role-state directory and the orphan recovery flow (6.1), worktree self-heal | M1 |
| M3 | Route + message classes | `tools/sessions/route.py <path>` and `--route-key`, the message-class convention (9.0), advisory rules in the function templates | M1 |
| M4 | Worktree + branch hygiene | `status.py` (also shows each seat's instance state: live / orphaned / none), `prune_branches.py` (dry-run, backup, lease), disk-budget warning, retirement report | M1 (parallel with M2/M3) |
| M5 | Authority guardrails + advisory semantic boundaries | harness permission rules for authority-class commands, role-conditional `PreToolUse` hook (deny / ask), `--agent` allowlists for read-only roles, advisory `role_boundary` events | M2 |
| M6a | Minimum measurement | resolved `session_role` on monitoring events, headline-metric categories, the batch-latency triplet | M2, M5 |
| M6b | Analytics and roster check | expanded retro analytics, roster staleness report | M6a (optional; after M7) |
| M7 | Review of the first month | harden or retire advisory rules on measured evidence | M6a + 4 weeks |

M1 + M2 are the value core (they remove most of what the user types and fix the stale-note class).
M4 can start immediately after M1 and is independently useful (the 2026-10-02 disk incident).

**Recommended v1 scope (external review, accepted).** Prove the hypothesis with the smallest slice:
role schema + validator (M1); launcher, binding, role-aware `SessionStart`, own-handover-only (M2);
path routing and the message classes (M3); the **authority guardrails** from section 10 plus advisory
semantic ones (M5); the minimum measurement (M6a); durable pending work only if M0c says it is needed. **Off the
critical path, in parallel**: worktree and branch hygiene (M4) is operations, justified by the
2026-10-02 disk incident but not part of the control-plane proof. Expanded analytics and the roster
check (M6b), ratchets, auto-wake (decided on M0c evidence) and advanced concurrency come after M7; M6a
is the minimum measurement M7 needs.

**Acceptance for the epic**: a new session launched with `cc <role>` starts with its boundaries,
its worktree, its routing and its own handover, with zero typed instructions; the user can answer
"who owns X" and "what is in flight" from a command; a misroute like the 2026-10-02 `derived_stats`
case is caught by the validator or the staleness report; **a session killed mid-batch can be found and
resumed or replaced from the role id alone**, with its worktree, branch, batch and handover shown.

### 12.3 Decisions and open questions

**Decided by the owner (2026-10-02):** one launcher command, `cc <role>`; the launcher may start role
sessions with `--settings '{"crossSessionInbound":"accept"}'` (delivery only; it authorizes nothing);
agent-working drafts and implements the manifest and authority files and the user confirms every
authority diff; standing grants have no default expiry and are revoked by deletion; **three functions
(designer, planner/reviewer, implementer) and a full set of three seats per domain**, with `rpg`,
`agent-working` and `testing` today and UI, assets and others later.

**Decided in this plan (not open):** the **role id is the permanent identity**, sessions are disposable
instances that hold a seat, and recovery after an unexpected termination is keyed by the role id
(sections 2, 3, 6.1); the canonical home is `registries/` (section 4); authority and
destructive boundaries are deterministic guardrails from v1 and semantic ones advisory (section 10);
the home-directory digest pin is deferred (section 10); message authorization is advisory in v1 (9.0);
role identity is resolved from signals at `SessionStart`, with the name a signal and not the key
(section 5); the writer slot belongs to the worktree, one worktree per domain, the implementer the
only committer (sections 4, 5, 7); `.claude/agents/session-<role>.md` files are *generated* from the
manifest (M0d may force a separate directory).

**Open, for the owner:**
1. Staffing: `agent-working-planner` and `testing-designer` are unstaffed. Who holds them, and when?
   (Until then `agent-working-design` holds the first; the testing designer seat stays empty.)
2. Confirm the practice changes in section 3: detail tickets move to the planner
   (`test-architecture-implementer` stops writing them), and the implementer keeps committing the
   drafts the planner hands over, with no plan-only PRs.
3. When a new domain (UI, assets) is added, may a seat start unstaffed with a named holder, or must all
   three be staffed first?

4. Recovery default on an orphaned instance: offer resume and replace with evidence and let the owner
   choose, suggesting *resume* when the transcript is newer than the handover and *replace* otherwise
   (proposed). Confirm, or choose a fixed default.

**Open, for the spike or a reviewer:** the M0 items a to r; whether a hook can return "ask"; which
identity signal is stable; whether a minimal inbox is needed (M0c).

### 12.4 Risks
- **Over-formalising**: three seats per domain (nine now), one short card each, composed from three function templates. If the manifest grows faster than the
  roster, stop and simplify.
- **Roles change fast** (a role note went stale within a day): the manifest is the only definition,
  everything else links to it, and the staleness report runs at retro.
- **Platform gaps** (path and command matching, hook failure semantics, wake behaviour, `--agent`
  pollution): M0 exists to find these before code is written. If hook matching proves weak, the
  authority guardrails fall back to harness-native permission rules plus advisory logging, not to nothing.
- **Over-reading the guardrail**: v1 is a guardrail against mistakes, not an adversarial sandbox
  (section 10 threat model); a deliberate bypass needs OS-level isolation, which is out of scope.
- **Governing-file edits**: the manifest, hook wiring and `settings.json` changes each need the
  user's confirmation of the literal text; M2 and M5 will touch `settings.json` for hooks.
- **Two sessions, one role** (a clone launched by mistake): `max_sessions` is checked best-effort; the
  **writer lease** is what prevents two writers in one worktree; the roster check reports the rest.

### 12.5 Deferred on purpose
Auto-wake of idle sessions (a documented mechanism exists; decided on M0c evidence); automatic dispatch
without a planner; **hardening of semantic boundaries beyond advisory** (the authority guardrails
themselves are in v1); the home-directory authority-digest pin; cross-machine sessions; a batch
registry separate from PR bodies; expanded retro analytics (M6b); any change to agent definitions or
`Workflow` scripts.

## 13. Related

- `docs/plans/agent_infrastructure/agent_working_direction.md` (the track this extends)
- `docs/guides/agent_session_reset_boundaries.md` (handover format, HARD/SOFT/NEVER)
- `docs/guides/delivery_process.md` (worktree and branch contract, PR lifecycle, `pr_render`)
- `tools/agent-monitoring/session_start_handover_hook.py` (the hook this replaces the listing of)
- Epics: `tickets/todos/session-layer/INDEX.md` (A foundation, B communication and authority, C operations,
  D measurement and review)
- External review record: `stored_artifacts/TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION/external_reviews/`
- Evidence tickets: `TCK-20260921-SESSION-CONTEXT-RESET-TRIAL`, `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`,
  `TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE` (content-vs-tooling split),
  `TCK-20261001-POST-MERGE-MAIN-INTEGRITY-REPORT`

---

# Appendix - context for an external reviewer

Written for a reader who has **not** seen this repository. Everything above refers to repo paths;
this appendix explains the project and the working environment well enough to judge the design
without access to the code. Numbers were measured on 2026-10-02 unless marked otherwise. Claims
about Claude Code come from its public documentation as relayed by a documentation-lookup agent and
are **not yet verified against the running harness** (that is milestone M0).

## A. What the project is

A deterministic, tick-based RPG world simulation in Python (about 740 source files, 1,500 test files,
about 90 tool scripts, roughly 2,300 closed tickets, about 320 squash-merged commits on `main`).
Entities (heroes, enemies, factions) act inside a world governed by written "laws": a Mechanics
Bible (6 chapters: entity anatomy, combat, economy, strategic cognition, world evolution,
worldbuilding) and engine contracts (a 7-phase kernel loop; a 39-phase authoritative mutation
pipeline). Determinism is a hard requirement. Documentation and code must stay in semantic parity,
tracked by a machine-readable parity ledger.

Most of the *engineering effort* is done by AI agents (Claude Code), coordinated by a human owner.
This plan concerns that coordination, not the simulation itself.

## B. How work is organised today

**Tickets.** Every unit of work is a markdown ticket (`TCK-YYYYMMDD-SHORT-SCOPE`) that moves
`tickets/todos/` -> `tickets/inprogress/` -> `tickets/done/`, with required sections (scope, out of
scope, acceptance criteria, related docs, test summary, files changed, completion summary). Closed
tickets append one row to a working log (`tickets/working_log.csv`) through a single sanctioned
writer.

**Tiers.** `hotfix` (self-evident, minimal): Scope -> Implement -> Test -> Parity -> Verify ->
Finalize. `standard` (feature, refactor, substantive repair): full 10-phase pipeline plus a
conditional Security-Review. `epic`: scope only, tracks child tickets; no direct implementation.

**Gates.** A `done-checker` verifies a Definition of Done (13 conditions) before a ticket may move
to `done/`; a static script covers the script-checkable ones. Repository rules: never edit an
artifact to make a gate pass instead of fixing the substance; report a blocking result truthfully;
do not guess when uncertainty affects behaviour; every workflow run must write monitoring records
(a monitoring failure must never fail the workflow).

**Agent layer (what exists *below* this plan).** 16 subagent definitions in `.claude/agents/`
(architecture-reviewer, security-reviewer, implementer, investigator, planner, done-checker,
ticket-scoper, test-scoper, doc-updater, parity-updater, world-debugger, and others); 11 scripted
`Workflow` pipelines in `.claude/workflows/` (implement-ticket, implement-epic, create-tickets,
and simulation-analysis workflows); 22 skills in `.claude/skills/`. Workflows fan out many
subagents deterministically and cost real tokens, so they require the owner's explicit opt-in.
**This is orchestration of agents inside one session.** The plan adds orchestration *across
sessions*, which has no equivalent today.

**Monitoring.** Per-run, per-event and per-tool-call records are written as JSONL shards under
`agent-monitoring/data/YYYY-Www/`, a retro report summarises them, and ratchet checks guard data
quality. A `vocabulary` registry constrains the `agent` field. A shared sidecar file
(`.claude/current_run`) once cross-contaminated attribution between concurrent sessions; a
per-session variant (`current_run.<session_id>`) now exists.

**Delivery.** Branch -> PR -> CI -> owner merges (squash). One git worktree per unit of work
(documented in `docs/guides/delivery_process.md`); PR title and body are *rendered* by
`tools/delivery/pr_render.py` from ticket files, not hand-written; the body ends with a
`Closes:` line.

**Knowledge tools.** A semantic doc search (MCP tool `search_docs`), a code knowledge graph
(`graphify`), and a flat registry of docs and closed tickets (`docs/REGISTRY.yaml`). Repository
rules require consulting these before grep.

## C. The current "session layer" (what is being formalised)

About 7 long-lived interactive Claude Code sessions run in parallel, each a separate conversation
in its own terminal, started and steered by the owner. They share one repository directory tree
via several git worktrees and talk to each other through the harness's cross-session messaging
(`SendMessage`; `ListAgents` shows live sessions by name). They are *not* subagents: each is a
full session with its own context window, memory, and tools, and each can be idle, busy, or
cleared.

| Session | Domain | Function(s) | Observed behaviour |
|---|---|---|---|
| `rpg-feature-planning` | game simulation | plan; dispatches work; reviews | owns an epic end to end; hands briefs to `rpg-implementer`; peer-reviews |
| `rpg-implementer` | game simulation | implement | hand-orchestrates tickets, commits, opens PRs |
| `agent-working-design` | agent infrastructure | design, review, plan | **the session that wrote this plan**; hands drafts to its implementer; does not commit |
| `agent-working-implementer` | agent infrastructure | implement | commits, pushes, opens PRs, polls CI for the shared worktree |
| `test-architecture-reviewer` | testing | review | direction authority for a test-architecture roadmap |
| `test-architecture-implementer` | testing | implement (+ writes child tickets) | one PR per batch of small tickets |
| `world-rule-catalog-design` | world rules | design | sends briefs only to the RPG planner |

Typical interaction (a real example): the design session verifies a defect, builds a patch in a
throwaway worktree, writes a README with exact before/after text into a "drafts" directory, and
messages the implementer; the implementer applies it, runs the closure tool, pushes, opens a PR and
reports the CI result; the owner merges. Peers routinely send each other findings, review
comments and ownership corrections.

**Roles are currently defined in:** ~7 per-user, per-machine, unversioned memory files; one
handover note per role under `.claude/handover/`; and instructions the owner types. A
`SessionStart` hook (on `/clear`) lists the handover notes by title. Nothing tells a session which
role it is.

## D. Incident evidence behind the design (all real, all recent)

1. **Stale role note -> misroute.** Session A told session B a registry decision was B's; A's own
   note said B owned the whole file. True for the tooling, false for the content. B declined and
   the error surfaced. (The registry's content is RPG-domain; only its advisory tooling is
   agent-working's.)
2. **Role confusion after context loss.** A shared memory note written for the planning session
   ("never implements") was read by the implementation session after compaction and applied to it;
   the owner had to be asked.
3. **A batch merged without finalising.** One PR changed `src/` while all four of its tickets stayed
   in `tickets/inprogress/` (their Finalize never ran). Found only because a peer read the PR.
4. **Disk exhaustion.** The volume reached 100% (worktrees about 7.6 GB; 307 local and 273 remote
   branches), which blocked a `git push`. Cleaned by hand: 240 local and 161 remote branches
   deleted with a name-to-SHA backup.
5. **Role name leaked into data.** A session wrote its own name as the `agent` value in closure
   events and tripped a vocabulary-drift ratchet (174 vs ceiling 162).
6. **Wrong PR bodies.** Three variants of one defect (a PR's `Closes:` line listing a ticket it only
   filed, only cited, or could not render at all for a docs-only branch) reached review, each caught
   by a human peer reading, not by tooling.
7. **Idle sessions.** Cross-session messages to a session sitting idle after `/clear` were observed
   to queue until the owner typed in its terminal. The documentation says a message wakes an idle
   session. The conflict is unresolved.

## E. Claude Code concepts the plan relies on

- **Session**: one interactive conversation; has a context window that is compacted automatically
  or reset with `/clear`.
- **`--name`** (documented): names a session at launch; visible to hooks as `session_title` and
  to other sessions via `ListAgents`; survives `/clear` and `--resume`.
- **`--agent <name>`** (documented): runs the *main* session as a custom agent defined in
  `.claude/agents/<name>.md` (system prompt, tool allowlist, model).
- **Hooks**: scripts run on events. `SessionStart` (payload includes `session_id`, `source` of
  startup/resume/clear/compact/fork, `session_title`, `agent_type`) can inject extra context.
  `PreToolUse` can warn on or deny a tool call (for example `git push`, or an edit to a path).
  Path matching for denial is shown in examples, not specified.
- **Memory**: markdown files per project directory, loaded into every session in that directory
  (hence the cross-session bleed in D2). **`CLAUDE.md`**: repo instructions every session reads.
- **Governing files** (`CLAUDE.md`, `settings.json`, hooks): the owner must confirm the literal text
  of any change, each time.
- **Permission model**: a message from a peer session is information, never the owner's approval;
  a session may not ask a peer to perform an action it was itself denied.
- **Worktrees**: separate working directories and branches over one git object store; two
  worktrees cannot collide at the git level. A session already in a worktree cannot create a second
  (a documented limitation with an accepted fallback).

## F. Constraints any design must respect

- The owner keeps authority over: merge, push (outside a granted batch), governing-file edits,
  large agent workflows, deleting remote branches. Standing grants exist and are dated.
- **One writer per branch**; the implementer commits, the designer hands drafts.
- **Define information once**: a fact lives in one document, others link to it.
- **No process labels in identifiers** (no ticket or phase numbers in names).
- **Report-only before blocking**: tooling checks over monitoring data are advisory first;
  ratchets guard historical debt without gating on it; never "fix" a gate by editing the artifact
  it checks.
- **Token efficiency is preferred over speed**: a design costing ~50% more time for ~30% fewer
  tokens is acceptable; context re-reading after `/clear` has a measured break-even (pays off only
  past ~150k tokens of context).
- Docs, tickets and registries carry validated frontmatter; layers and tags come from append-only
  registries.

## G. What I would like reviewed

**Is the design right?**
1. Is **domain x function composition** (4 templates + 4 overlays + a small per-role entry) the
   right decomposition, or does it hide real per-role differences? Where would it break first?
2. Is a **repo-versioned manifest** the right single source for ownership, or is the path-glob
   grain still too coarse (the motivating failure was a *content-versus-tooling* split inside one
   file)? Is `owns` / `owns_not` / `routes` sufficient, or is a different model needed?
3. **Advisory-first enforcement**: is it correct to defer hard denial until measured violations
   exist, given that sessions can already ignore advice? What is the cheapest hard boundary that
   is not brittle?
4. **Launch-time role binding** via a launcher plus `--name` / `--agent` / an environment variable:
   what failure modes exist (stale name collisions, forks, resumed sessions with a changed manifest,
   two sessions claiming one role)?
5. **Routing**: static ownership table plus model-side liveness. Is "one bounce, then the owner" a
   sound anti-ping-pong rule? What should happen when the owning session is busy for hours?
6. **Grants and authority**: modelling the owner's standing permissions as dated manifest entries
   that only the owner edits. Does this create a new prompt-injection or permission-laundering
   surface?
7. **Worktree and branch hygiene** automation scope: is dry-run-plus-backup-plus-owner-approval
   the right ceiling, or too timid or too bold?
8. **Observability**: are the proposed measures (misroutes, bounces, idle stall, handoff latency,
   batch cycle time, boundary warnings, `/clear` cost) the right ones, and which would you drop?
9. **Phasing**: is M0 (spike) -> manifest -> launcher the right order? What would you cut to
   shrink v1?

**Known weak points (I would rather you attack these):** wake-on-message behaviour is unverified;
`PreToolUse` path matching is unspecified; the heuristic "all commit subjects already in main" for
branch deletion can be wrong under squash merges; the manifest could itself go stale within days
(a role note did, in one day); the roster is small (7 sessions), so a registry may be heavier than
the problem; nothing here removes the owner as the final authority, by design.

**Out of scope for this review:** the simulation's game logic; the internals of the 11 workflows;
replacing Claude Code; cross-machine sessions; automatic dispatch without a planner.

## H. Glossary

- **Batch**: the delivery unit, one branch and one PR containing one or more tickets.
- **Closure tool**: the script that records a hand-orchestrated ticket's run, events and log row.
- **Done-checker / Finalize**: the gate and the closing phase that move a ticket to `done/`.
- **Handover note**: a per-role file a session writes before `/clear`, read after it.
- **Ratchet**: a check pinned to today's measured historical count so it can only improve, used so
  historical debt does not block live work.
- **Parity ledger**: machine-readable record that docs and code agree.
- **Peer**: another live session on the same machine; **owner**: the human operator.
- **Sidecar**: a small state file recording the current run, used to attribute tool calls.
- **Shard**: a per-week (and per-batch) JSONL file of monitoring records.

---

# Appendix I - disposition of the external review (2026-10-02)

An external AI reviewed the plan from the document alone (no repo, no live harness). Its review is in
`stored_artifacts/TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION/external_reviews/round1_review.md`. Each point was checked against the repo's own records before
being accepted. "Adopted" means the plan text above changed.

| # | Review point | Disposition | Reason |
|---|---|---|---|
| 1 | Keep domain x function composition; watch per-role override creep | **Adopted** | validator now *reports* override, unique-route and authority-exception counts (section 4) |
| 2 | Do not make the manifest a god registry; separate identity / responsibility / capability / authority (/ placement) | **Adopted** | section 4 regrouped into five kinds |
| 3 | Authority and grants need a stronger trust boundary; a subject must not edit its own policy | **Adopted** (strongest point) | authority moved to `registries/session_authority.yaml`, governing-file class, with a hard deny on edits to it (section 10) |
| 4 | Enforcement split: semantic advisory-first, authority/destructive hard from the start | **Adopted**, gated on M0e | deterministic, high-consequence boundaries gain little from a 4-week wait; "hard" waits only for proof that hook matching works |
| 5 | Role vs session instance; concurrency policy | **Adopted** | `concurrency: {max_sessions, writer_slots}`; exclusive resources are the writer slot and active batch (section 5) |
| 6 | Bind `session_id -> role`, not name | **Adapted** (partly declined) | the repo's notes record that `/clear` allocates a new session id (verified 2026-09-27) while the name persists, so the id cannot be the key across a clear; the name is the key, the id lives in a per-session binding record (section 5). Distinction between role, name and id adopted. |
| 7 | Resume outside the launcher | **Adopted** | M0f; role recovered from `session_title` / `agent_type` |
| 8 | Bind session to manifest revision; show what changed on resume | **Adopted** (lightweight) | digest in card and binding record; authority reductions flagged (section 5) |
| 9 | Semantic `subjects` for ownership beyond path globs | **Declined for v1** | the motivating case was *different paths* (content `registries/mechanisms.yaml` vs tooling `tools/mechanism_registry/**`), which `owns_not` + `routes` already express; no demonstrated failure globs cannot handle. Revisit if one appears. |
| 10 | Separate ownership dispute from owner unavailable | **Adopted** | section 9.3 |
| 11 | Durable inbox before auto-wake | **Adapted** | gated on M0c: if `SendMessage` already queues and wakes across `/clear`, the harness is the inbox; otherwise a minimal file mailbox (9.5) |
| 12 | Drop `bounce_if` from the envelope | **Adopted** | rerouting policy is central (9.2) |
| 13 | Derive batch lifecycle (dispatched ... finalized ... merged); PR green != complete | **Adopted** (as derived status, not a registry) | surfaced by the status command (section 8), no new batch store |
| 14 | Commit-subject equivalence must not establish deletion safety | **Adopted** | demoted to an informational hint; only merged-PR branches are deletion-eligible (section 8) |
| 15 | Worktree/branch hygiene is operations, not session-layer core | **Adopted** | M4 moved off the critical path, in parallel |
| 16 | Headline metric: manual orchestration actions per completed batch | **Adopted** | section 11; proxy via a prompt-submit hook, verified in M0j |
| 17 | More M0 lifecycle cases (bypass-resume, rename, fork, manifest change) | **Adopted** | M0f-k |
| 18 | Smaller v1 scope | **Adopted** | "Recommended v1 scope" in 12.2 |
| 19 | State "control plane, not workflow engine" as an invariant | **Adopted** | section 1 |

**Superseded in round 2** (see `stored_artifacts/TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION/external_reviews/round2_summary.md`): row 3 (the pinned
digest is deferred; v1 uses the governing-file class plus deny/ask), row 5 (the writer slot moved from
the role to the worktree), row 6 (the session name is a signal resolved at `SessionStart`, not the
identity key; the session id changes at `/clear` and the role is re-resolved). The rows above are kept
as the round-1 record.

**Not accepted wholesale, and why.** The reviewer's own listed assumptions (A1 to A10) were treated as
assumptions: it could not know that `/clear` changes the session id (point 6), nor that the content/
tooling split it wanted a new primitive for was a cross-path split (point 9). Where its reasoning rests
on harness behaviour, the plan routes the question to M0 instead of deciding it here.

**Still open after review.** Wake-on-message (M0c); whether `PreToolUse` can match paths and Bash
commands as the hard boundaries need (M0e); whether `--agent` files pollute the subagent roster (M0d);
the roster table and launcher shape (section 12.3, owner decisions).


---

# Appendix J - prior art and what it changed (web research, 2026-10-02)

Sources are the official Claude Code documentation (high confidence, read in full) and third-party
articles via search results (lower confidence, used for framing only). Two arXiv papers whose titles
match this plan's thesis (2606.26924 and 2605.03310, rows below) were read through the alphaxiv mirror
because arxiv.org itself is unreachable from this network; the mirror returns a **small-model summary**,
so treat their rows as secondary and read the originals before the M1 design review. Neither paper's
claims are load-bearing for the design.

| Source | What it says | Effect on this plan |
|---|---|---|
| Claude Code **Agent Teams** (experimental, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`): a lead spawns teammates with a shared task list and per-agent JSON mailboxes | one team per session, lead fixed, in-process teammates not resumable, no nested teams, **no project-level team config**; reusable roles are **subagent definitions** (`tools`, `model`, body applied; `skills` not applied) | Our topology is different (long-lived, user-launched peers, no lead), so Agent Teams are not a substitute. Confirms (a) roles as `.claude/agents` files is the supported way to define a role, (b) a file mailbox with validated entries is first-party precedent for the inbox, (c) `TeammateIdle` / `TaskCompleted` hooks with exit 2 are a precedent for the quality-gate hooks in section 10. A planner could later use a team *inside* a batch; orthogonal. |
| Claude Code **cross-session messaging** | names, `ListAgents`, idle receiver starts a turn, inbound `accept/hold/refuse`, 5-minute held-dialog expiry, own-child socket posting, loop throttling, plain text only, cannot approve or change config | resolves most of the M0c wake question and gives the launcher real levers (section 9.5); confirms the "peer message is never approval" rule is enforced by the harness, not only by us |
| Anthropic multi-agent research system (orchestrator-worker; ~15x tokens) | workers never talk to each other; the key decision is the *isolation boundary*; multi-agent costs far more tokens | section 9.0 topology; supports "advisory first, measure cost" and the token-efficiency constraint |
| MAST failure taxonomy (arXiv 2503.13657, via search summaries) | 42% of multi-agent failures are specification issues (role mis-specification), 37% inter-agent misalignment, 21% weak verification | independent support for the plan's thesis: our incidents map onto it (stale role note = specification; misroute = misalignment; PR #276 merged unfinalized = verification/termination) |
| OpenAI Agents SDK / LangGraph / CrewAI / AutoGen comparisons | handoff = explicit transfer with context; supervisor is the most supported pattern; CrewAI = role + goal + backstory per agent | our envelope is a handoff; role card = role/goal/backstory; none of them models *ownership by path* or *user-held authority*, so nothing is adopted wholesale |
| **CODEOWNERS** | path -> owning *team* (not person), "every path has an owner", owner review required via branch protection | same grain as `owns`; adopt the "role not individual" idea (already ours) and add a validator report of unowned top-level paths; semantics to state explicitly (CODEOWNERS is last-match-wins; this plan said longest-match: pick one and document it) |
| **AGENTS.md** (nested, nearest file wins; keep short) | instructions as nested files, closest takes precedence, split past ~150-200 lines | supports short role cards; our overlays compose by *role*, not directory, so precedence is explicit, not by nesting |
| **A2A** Agent Card (identity, skills, endpoint, auth, discoverable) | a card describes an agent so peers can discover and address it | the role card is our analogue; the protocol itself is unnecessary on one machine (and the repo already recorded A2A as not recommended) |
| Nechepurenko & Shuvalov, *Coordination as an Architectural Layer for LLM-Based Multi-Agent Systems* (arXiv 2605.03310; mirror summary) | splits a system into an **information layer**, a **coordination layer** (topology, authority distribution, synchronisation, aggregation, termination rules, failure policies) and an **agent layer**; coordination should be a configurable layer separable from agent logic; five coordination configurations tested on 100 forecasting questions with the model, tools and prompts held fixed; failure signatures: minority-view collapse, midpoint anchoring, false-confidence cascades in pipelines | independent statement of this plan's thesis and layering (the session layer = the coordination layer; domain overlays = information; function templates and agent files = agent). Termination rules and failure policies map to "Finalize" and the one-bounce rule. **Caution**: the experiments are forecasting tasks, not coding, so the consensus findings are not transferable evidence; the *pipeline error-amplification* signature is the relevant one, and is a reason to keep reviewers independent and to verify relayed peer claims. Reviews should not require consensus (a lone correct reviewer must not be outvoted). |
| *A Deterministic Control Plane for LLM Coding Agents* (arXiv 2606.26924; mirror summary of a system named Rel(AI)Build) | agent configuration treated as a supply-chain artifact: SHA-256 content addressing, HMAC-stamped lockfiles, hash-chained audit logs, **tier-based permissions with fail-closed allowlists**, prompt-drift detection against an approved baseline, a phase-gated state machine with mandatory human checkpoints, governance compiled from one canonical format to several tool targets; principle: non-deterministic agents need deterministic controls, not prose rules | strongest support for the section 10 split and for **generating** `.claude/agents/session-<role>.md` from the manifest (and a Codex target) instead of hand-writing it. Originally adopted as a home-directory digest pin on the authority file; **deferred in round 2** (a same-OS-user session can write both locations, so it is tamper evidence, not isolation; section 10). Kept: the regeneration drift check for generated agent files. Not adopted: HMAC lockfiles for every file, hash-chained audit logs (existing monitoring shards suffice for v1), Jaccard drift scoring (the manifest digest check covers this plan's staleness case). |
| Third-party worktree session managers (parallel-code, claude-squad style tools; `claude --worktree`) | one worktree per session is the common convention | confirms section 8's worktree-per-role-or-domain default; none handles ownership or roles |

**Net effect.** The plan's direction matches the documented first-party grain (subagent-definition
roles, named sessions, inbox, hooks as gates). The research changed five things in the text above: a
name-collision rule (section 5), a stated topology (9.0), a corrected wake analysis with real levers
(9.5), alignment with the existing `agent-orchestration/` contract (section 4), and more M0 cases
(12.1 l and m). It did not change the milestone structure. The two papers added supporting framing; the one mechanism
they suggested (a pinned authority digest) was deferred in round 2.

---

# Appendix K - brief for a second review round

*(Round-two brief, answered in `stored_artifacts/TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION/external_reviews/round2_summary.md` (the brief itself is `round2_review_brief.md` beside it); kept for provenance. The "changed since round one" list and items 2 to 4 below describe round one; round 2 then revised sections 4, 5, 6, 7, 9, 10, 11 and 12.)*

This is the second external review. The first review (`stored_artifacts/TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION/external_reviews/round1_review.md`) is
summarised and answered in **Appendix I**. Prior art that changed the text is in **Appendix J**. Please
do not re-raise the points Appendix I marks "Adopted" unless you think the adoption is wrong; spend the
review on what is new or contested.

**Changed since round one (sections to re-read):** 1 (control-plane invariant); 4 (five-kind manifest,
separate authority file, relation to the existing `agent-orchestration/` contract); 5 (binding by name,
binding record, manifest digest, name-collision rule, launcher bypass); 9.0 (topology), 9.2/9.3
(`bounce_if` dropped, dispute vs availability), 9.5 (inbound controls, inbox gate, auto-wake levers);
10 (hard/advisory split, pinned authority digest, fail-closed authority); 11 (headline metric); 12.1
(M0 a-m); 12.2 (recommended v1 scope).

**Please attack these specifically:**
1. **Declined or adapted points** (Appendix I rows 6, 9, 11): is the reasoning sound? Especially row 6
   (name, not session id, as the key across `/clear`) and row 9 (no semantic `subjects` in v1).
2. **Hard authority boundaries from day one** (section 10), gated on M0e: what is the weakest assumption,
   and what is the cheapest fallback if hook matching proves unreliable?
3. **Pinned authority digest outside the worktree** (section 10): does a user-held pin actually stop a
   session editing its own authority, or does it only move the problem? What would you pin instead?
4. **Inbound controls and wake** (section 9.5): the plan proposes launching role sessions with
   `crossSessionInbound` = `accept`. What does that open up, and is a narrower setting possible?
5. **Topology** (section 9.0): hub-and-spoke per domain with the user above. Where does it fail (a
   planner that is offline for a day, a cross-domain emergency, two planners disagreeing)?
6. **The agent-role vs session-role split** and placing the roster under `agent-orchestration/`: right
   home, or a source of confusion?
7. **Scope**: with the v1 slice in 12.2, what would you still cut?

**Things that remain unverified and should not be treated as fact:** everything under M0 (12.1);
wake behaviour; `PreToolUse` path and command matching; whether `--agent` files affect the subagent
roster; the two arXiv papers' claims (read via a mirror summary only).

**Please structure the answer as:** (a) agree/disagree per item above with one-paragraph reasoning;
(b) any new risk not in Appendix I or this plan; (c) a ranked list of at most five changes you would
make before ticketing, each with the failure it prevents.

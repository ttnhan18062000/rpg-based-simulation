---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Project sync (dry run, `--init`, `--apply`)

`tools/sessions/project_sync.py` derives the GitHub Project items for ticket state from ticket files on `origin/main`, this host's
worktrees and open PRs. By default it is a dry run: it prints a create / update / archive plan and writes nothing to GitHub or the repo. `--init` and `--apply` (P1b) write to the Project only.

Run it from any checkout: `python3 tools/sessions/project_sync.py` (or `python3 -m tools.sessions.project_sync`). `--host` defaults to
`host_names[hostname]` in `registries/session_project.yaml`, else the hostname. 

Read-only by construction: git goes through a verb allowlist, and `gh` is limited to `pr list` and `gh api repos/...` with only
`--paginate`, `--jq`/`-q` and `--header`/`-H`. `gh api graphql` and every other flag are refused.

Status, first match wins: Done, In review, Blocked, In progress, To do. **Stale** replaces In progress only: every branch working the
ticket is older than `stale_branch_days` (default 14). A branch's age is the newer of its last commit and its index mtime, so it is
approximate: anything that refreshes the index counts as activity. A fresh filing branch does not keep an abandoned working branch In progress.

**Known gap, `<domain> (seat not recorded)`:** the Seat is the one the launcher recorded for the worktree. Worktrees made by hand with
`git worktree add` have no record, so they show the branch-prefix domain and this label. It is a gap in the records, not a sync fault.
Filed as `TCK-20261112-HAND-ADDED-WORKTREES-ARE-NOT-RECORDED-AGAINST-A-SEAT`.

## Writing to the Project (`--init`, `--apply`)

Needs `project.number` in `registries/session_project.yaml` (the org Project `rpg-sim-lab/<number>`; `0` means exit 2) and the token file.

- **Token:** `~/.config/rpg-project-sync/token`, mode exactly 600, read only by `ProjectClient` (`tools/sessions/project_client.py`) and set as
  `GH_TOKEN` in the env of its own `gh api graphql` child process. It is never in argv (the query goes on stdin), never printed or logged, never
  exported, and is redacted from any error text. A missing, empty or looser-than-600 file is refused with a plain message. Never run
  `gh auth refresh -s project`: that widens the login every seat uses.
- **Live read:** when the Project is configured and the token is readable, the current items are read from the Project (paginated, archived
  items skipped). `--items <file>` replaces that for offline runs. A run with neither flag is still a dry run.
- **`python3 tools/sessions/project_sync.py --init`:** creates the missing fields by name (text `Ticket ID`, `Domain`, `Seat`, `Host`, `Branch`,
  `PR`, `Source`, `Sync hash`; single-select `Tier`) and sets the built-in `Status` options to the six statuses. Every check comes before any
  write: a same-named field of the wrong type, or a missing `Status` field, is reported with nothing written (exit 1). Replacing `Status`
  options clears each item's Status, so on a Project that already has items it is refused unless `--replace-status-options` is given.
  A second `--init` reports nothing created or updated.
- **`--apply`** (not with `--init` or `--items`): prints the plan, then carries it out. Create = draft item, then `Ticket ID` first and `Sync hash`
  last; update = changed fields, `Sync hash` last; archive = `archiveProjectV2Item`. A failing step stops the run and prints what was done
  and what was not; the next run reconciles. Items and fields are found by id read on each run; none is stored.
- **`--apply` needs known PR facts:** if `gh pr list` fails, or any PR's file list cannot be read, `--apply` exits 1 and writes nothing (a dry run only notes it), because In review and PR would be written wrong.
- **Never deleted:** the module has no delete mutation. Items without a `Ticket ID`, duplicates of one `Ticket ID`, and items whose ticket
  file is gone are archived, by their own item id.

## Layer, Epic, Priority and Tags (P1c)

`--init` also creates four fields, and `--apply` fills them from the ticket's own files:

- **Layer** (single-select, options = `registries/layer_registry.jsonl`) from frontmatter `layer:`; **Priority** (single-select P0-P3) from `## Priority`
  (a leading `P2 (...)` takes `P2`); **Tags** (text) from frontmatter `tags:`, joined by spaces in `registries/tag_registry.jsonl` order, unknown tags last. A value not in
  the registry or not P0-P3 leaves the field empty and prints a finding; it is never guessed.
- **Epic** (text), first match wins: (a) the ticket sits in an epic folder (`todos/<folder>/` or `done/<folder>/`): the folder's ticket whose `## Tier` is `epic`
  (an epic's own Epic is its own id); no epic ticket -> the folder name; several -> the folder name plus a finding; (b) exactly one folder's `SEQUENCE.md` (exact
  basename) names the ticket, in `## Order` if that section exists, else anywhere in the file: that folder's epic; named in more than one folder -> `standalone` plus a
  finding; (c) otherwise `standalone`. `## Related Tickets` is not read.
- **Option ids are kept.** `--init` adds a missing option (a newly registered layer) by sending every existing option with its id, so items keep their value. Probe on
  Project 1 (2026-11-14): a single-select with options a, b, an item set to `a`, options updated to a, b, c passing the existing ids: the ids of a and b stayed and the
  item still read `a`. Status on a Project that has items is append-only too (an option not in `STATUSES` is kept and reported, not dropped).
  `--replace-status-options` sends exactly `STATUSES` in order with existing ids, so only items on an option left out lose their Status (the next `--apply` restores them),
  and a rename is a remove plus an add, so only that option's items blank.
- **Sync hash** is versioned: `v2:<sha>` over the nine P1b fields plus these four; an unprefixed value is the P1b (v1) hash. A v1 item is not a hand edit; it is updated once and carries `v2:` afterwards. P2 adds `v3:` (the v2 fields plus `Host facts`); a v1 or v2 item is not a hand edit and is rewritten once.

## Two hosts (P2, `TCK-20261114-PROJECT-SYNC-SECOND-HOST`)

Ubuntu and u24 both write Project 1. Each host rewrites only its own facts and derives every shared field from the union of all hosts' facts, so both derive the same value
and a run on one host never undoes the other's. This corrects design section 5, which said Status rules 1, 2, 3 and 5 depend only on origin: that holds for Done and In review only.

- **`Host facts`** (text, created by `--init`, in the v3 hash) holds one segment per host, joined by `; `: `u24desktop: state=progress seat=a,b domain=rpg; ubuntu: state=blocked seat=c domain=rpg`.
  `state` is `filing | progress | stale | blocked` from that host's own branch copies; `seat` is the seat names the launcher recorded (a placeholder such as `rpg (seat not recorded)` is made when the
  Seat is shown and never stored; a filing segment gives no seat); `domain` comes from every branch the host has. A host with no copy of the ticket has no segment. A malformed segment is skipped with a finding.
- **Holder:** a host with a segment on the item, in any state. A host that wrote its segment with P1c code (a `Branch` entry and no segment) counts as a holder through a **legacy segment**, derived on read, never written,
  never for the host running the sync. While one exists, Seat and Domain keep their current entries and add this host's (they do not shrink until that host writes its own segment).
- **Status** from the union: Blocked if any segment is blocked (origin's BLOCKED copy counts only when no host holds the ticket); Stale only when every non-filing segment is stale; In progress when any is progress or stale; else To do.
  `stale` is set only by the host that wrote it, from its own branches' age.
- **Seat and Domain** are the sorted union of the segments, and shrink when a host drops its segment.
- **Title, Tier, Layer, Priority, Tags, Epic, Body:** no holder: origin's copy. One holder that is this host: its own copy. One holder that is another host: keep the current value (origin's copy if there is no item yet).
  Two or more holders: origin's copy if origin has one, on every host; with no origin copy only the holder with the lowest host tag (string sort) writes its own copy and the others keep the current value. The plan prints a note naming the rule.
- **Archive guard:** "no ticket file for this ID" never archives an item that carries another host's segment (or a legacy entry); it prints a finding naming the host.
- **Known gaps:** a host that stops running leaves its segment saying `progress`; the stale-host flag that would catch it is P3. Until u24 runs P2 code, u24's Blocked and Stale cannot be seen from ubuntu. So when this host has no copy of a ticket and every other holder is a legacy segment, Status stays the item's current value
  (Done and In review from origin still win); it clears when u24 writes its own segment. **Limit: with only legacy u24 segments, Status freezes until u24 runs P2 code**; the hold on u24 `--apply` lifts only after u24's first P2 `--apply`, which should follow soon after the merge. If this host has its own segment, the normal union applies. The current Status is never copied into a legacy segment's state. P1c code reads `v3:` as an unknown version, so a P1c-code dry run reports a hand edit on every v3 item; do not run `--apply` from a checkout on P1c code.
  Hiding `Host facts` in the Project views is an owner step in the view settings (the API cannot do it); the sync does not depend on it.

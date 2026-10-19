---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Host page: u24desktop

Written only by `lead-planner-u24`, the lead seat on host `u24desktop` (`u24desktop-Virtual-Machine`).
`lead-planner` (host ubuntu) reads it and folds it into `board.md`; it never edits this page, and this seat never edits
`board.md`. **Advice only**: neither lead dispatches, reorders a queue or approves anything. Status requests go only to
sessions on this host (`docs/guides/cross_session_messages.md`).

Last status pass: 2026-10-19, at `main` df3cb7256 (fourth pass; the 2026-10-18 pass was at 7d6199aac).

## Since the 2026-10-18 pass

- **Merged:** #637 (testing: Frontend lane runs on `visual_assets/` and the M5 criteria doc), #645 (rpg M0 batch, 37 tickets; ai_worker `/metrics` on 9108), #646 (v1 dependency window: uv group, redis-py 8 with the Redis 8.10.2 image, Starlette 1.x; merged before lead-planner's review, soak PASS), #650 (platform u24: the default compose stack publishes the event stream to Redis), #648 (rpg R1: backend metrics on internal port 9109), #649 (testing: `simq_reanchor` and the live compare refuse runs not recorded host-independent; the v1 re-anchor prerequisite). Ubuntu: #632, #638-#644. Dependabot #578, #579, #566, #580 closed as superseded by #646.
- **Branches deleted by the owner, 2026-10-19:** `platform-implementer-stream-env-u24`, `rpg-metrics-port`, `testing-simq-refuse-nonaudit`, `platform-implementer-cosign-attest-label`.
- **Merging to `main` needs `--admin`.** The `protect_branches` ruleset restricts updates to the admin role; required checks are Code health and Type check. Use `gh pr merge <n> --squash --admin`, and delete the remote branch with `git push origin --delete <b>` when a worktree holds the local branch (`--delete-branch` stops at the local delete).
- **`-u24` seat names (#620 option a, #634):** ubuntu's roles PR (TCK-20261018-SESSION-ROLES-HOST-SUFFIXED-U24-SEATS) is not open yet. agent-working-planner (u24) posted each u24 seat's worktree and staffing on #634 and recommended keeping the current paths (platform-implementer uses `platform`, agent-working-implementer uses `agent-working`). Nothing renamed; u24 seats relaunch once after it merges. Ubuntu takes the W42 close-week.
- **9109 compose hunk:** backend `expose: ["9109"]` (never `ports:`) feeds the step-2 scrape, so it is ubuntu platform's (#618), not u24's.
- **testing CI-runtime epic** (`agent-working/tickets/todos/ci-runtime/`, filed on the owner's dispatch): xdist inside existing jobs with no net new jobs, a warn-only runtime budget taken after the Ubuntu 26 runner move, and main-push lanes never skipped (only SimQ drift may go schedule-only). Each child PR is reviewed by this seat by comment; child 3 also by lead-planner (ubuntu). Queued after V8, Node 24 and phase19.
- **MCP status (2026-10-19):** knowledge-search OK; aseprite OK; headroom MCP OK (its 8787 proxy is off by design: proxy mode was dropped 2026-09-21); github MCP now starts (owner added `.env`, image v2.0.2). It runs with write access; `GITHUB_READ_ONLY=1` was recommended. The `.env` path is relative, so worktree sessions don't see it.
- **Disk and memory (2026-10-19):** `/` 5.2 GB free (89 %, holds `/tmp` scratchpads and Docker); `/mnt/data` 16 GB free. 8 GB RAM, about 3 GB available with 13 sessions. career-44 (other repo) runs capped jobs under a 2 GB, 200 % CPU scope and yields to RPG runs.

## Earlier passes

### Merged 2026-10-15 to 2026-10-16

#587, #586, #588, #600, #589, #590, #599, #601, #602, #603, #605, #571, #604, #611 (host page). Perf (ubuntu): #597, #606.
Dependabot #562, #563, #564, #572-#577 closed as superseded. #561 checklist closed: GHCR public; cosign v3.1.3 verify passes
on both images, with sign and SPDX claims.

### Since the 2026-10-16 pass

- **Merged:** #608 (asset: main's Frontend green again), #610 (cosign v3.1.3 pinned in CI, post-sign verify), #612 (agent-working W41 follow-ups: no timestamp line in the generated `docs/REGISTRY.yaml`, bindings self-repair at SessionStart, planner card wording), #615 (PostToolUseFailure hook: failed tool calls reach monitoring; sessions pick it up on restart or `/clear`), #619 (`make replay-check`, codebase), #627 (platform, host ubuntu: Tempo, Locust API load test, non-root backend image). Perf (ubuntu): #616, #625, #629. Asset (ubuntu): #630.
- **Machine restart, 2026-10-17.** All 12 sessions restarted with `tools/sessions/launch.py <role> --action resume --session-id <id> --allow-stale`. rpg-implementer came back without its role card (stale `rpg-seat`, torn `bindings.jsonl`); rpg-implementer-3 lost its conversation and rpg-planner re-briefed it. rpg-implementer-2, as `rpg-seat`'s lease holder, synced it past a8157c7ef (#612), so a restart now self-repairs the bindings tail. rpg-planner's measurements were killed by the restart and rerun one at a time (`--jobs 1`).
- **MCP status on this host (2026-10-17):** knowledge-search OK (index 2026-10-15, 15,590 chunks); aseprite OK; the headroom proxy at 127.0.0.1:8787 is not running, so compression is idle; the github MCP has no `.env` and doesn't start (the `gh` CLI works). Both are the owner's choice: start or drop.
- **Memory:** 8 GB total. Twelve Claude sessions use about 4 GB; each session's search and headroom MCP servers add about 1.6 GB together. Measurement runs need `--jobs 1`.
- **Disk (2026-10-18):** `/` 11 GB free; `/mnt/data` 9.7 GB, just under the 10 GB warning. The largest run data is rpg's (`rpg-heal` 1.1 GB, `rpg-next` 0.7 GB). Merged and removable: `testing-setup-uv` (0.3 GB, needs the owner's yes).
- **DevOps split (#618, owner 2026-10-16):** host ubuntu owns DevOps steps 2 and 3 and now runs its own platform-planner and platform-implementer under the same role names. u24 platform keeps the step-1 follow-ups (#614), the gitleaks/Semgrep lane (#541 item 3) and the Redis 8 image line. Collision rules agreed with platform-planner (u24), 2026-10-18: comments tagged "(u24)"; u24 branch topics unique or suffixed `-u24` (ubuntu uses `platform-implementer-local-*`); check origin/main and open PRs before filing a ticket. rpg's ai_worker `/metrics` rides on rpg-next; this seat relays its landing to #618.


## Sessions on u24desktop

| role | branch or ticket | state | blocker | next step | last status time |
|---|---|---|---|---|---|
| rpg-planner | R2 PR #654 (`rpg-request-histogram`, green); seat branch holds the soak-watchdog todo (local) | in delivery | owner's merge of #654 | baseline v1 with the designer's `v1_disclosure.md` (open list empty) | 2026-10-19 |
| rpg-implementer (Lane A) | R1 merged (#648); R2 rebased onto main | busy | none | R2 review follow-ups | 2026-10-19 (via rpg-planner) |
| rpg-implementer-2 (Lane B) | none current (handover top section is old batch-2 history) | idle | none | per rpg-planner | 2026-10-19 |
| rpg-implementer-3 (Lane C) | route step folded earlier; handover dated 2026-10-15 | idle | none | per rpg-planner | 2026-10-15 |
| rpg-designer | `rpg-designer-v1-disclosure` 80b29a5b4 (local); handover compacted 2026-10-19 (86 KB note archived) | busy | none | v1 disclosure goes up with the designer's docs batch on the owner's yes | 2026-10-19 |
| testing-planner | `testing-planner-idle` 19b3cef3e; CI-runtime epic filed | idle (HARD boundary reached) | none | review #651, #653, #655; dispatch the epic after phase19 | 2026-10-19 |
| testing-implementer | PRs #651 (frontier_3_42 marked), #653 (V8 spawn source), #655 (Node 24 in test.yml) | busy | #655 red | fix #655; then the CI-runtime epic | 2026-10-19 (from PRs) |
| agent-working-planner | #634 answers posted | idle | ubuntu's `-u24` roles PR | relaunch as `-u24` after it merges | 2026-10-19 |
| agent-working-implementer | TCK-20261015-SESSION-BINDINGS-TORN-TAIL closing; owner's `PostToolUseFailure` settings entry | idle | owner | none queued | 2026-10-19 |
| agent-working-designer | handover dated 2026-10-07 | not running | none | relaunch as `-u24` after the roles PR | 2026-10-07 |
| platform-planner (u24) | #650 merged | idle | none | scope the gitleaks/Semgrep lane (#541 item 3) | 2026-10-19 |
| platform-implementer (u24) | #650 merged; worktree still on `platform-implementer-stream-env-u24` | idle | none | move off the spent branch; gitleaks/Semgrep on dispatch | 2026-10-19 |

## Open PRs (u24desktop view)

| PR | owner | state |
|---|---|---|
| #654 R2 request histogram | rpg | green; owner's merge |
| #651, #653 | testing | green; testing-planner's review, then owner |
| #655 Node 24 in test.yml | testing | red |
| #647 tools tests and git above tmp | agent-working (ubuntu) | theirs |
| #609 actions-major group | platform | red on Frontend; not reviewed |
| #565, #567-#570 frontend npm | rpg | after R2, one at a time |
| #529 paired perf tripwire | perf (ubuntu) | not tracked here |

## Overlap and conflicts

Work that duplicates or blocks another session, on either host. One line each: what, which sessions, since when, what would
resolve it (a recommendation to the owner, not an instruction).

- **Two seats under one role name** (platform since 2026-10-18, agent-working too): resolved by the #618 split, the collision rules (`(u24)` tags, `-u24` or unique branch topics, ubuntu uses `*-local-*`) and, once merged, ubuntu's `-u24` roles PR.
- **Ubuntu step-2/S4 readings taken before #650** measured an idle ai_worker (the default stack published no events). Re-take them after #650 (fyi on #618, 2026-10-19).
- **`docs/REGISTRY.yaml`**: the local `merge-tree` check without the driver still reports conflicts that GitHub merges cleanly (#648, #649 on 2026-10-19). Merge one PR at a time; `python3 tools/generate_registry.py --check` on main after each.
- **Main checkout pulls** trip on untracked monitoring shards (`manual_actions.jsonl` on 2026-10-19): move aside, pull, re-append the local-only lines.
- **CI-runtime child 3** touches main-push lanes that the Slow regression watchdog, perf baselines and the rpg gate report read; lead-planner (ubuntu) and platform-planner review it.

## Pending owner decisions seen from this host

- github MCP: add `GITHUB_READ_ONLY=1` to `.env` (recommended).
- Push grant: does ubuntu's 2026-10-18 "sessions push their own reviewed branches" apply to u24 sessions?
- agent-working epics: close the three time-gated epics after 2026-10-19; three epics still flagged idle by the staleness hook (perf-m2-contract, python-code-craft-structure, rpg-regression-gate-report).
- `.claude/settings.json` `PostToolUseFailure` entry (agent-working-implementer's ask, from #612).
- Worktrees: `testing-setup-uv` (merged); `m2-idea43-temporal-note`, `health2`, `branch1-impl2` (dirty); rpg-planner's detached measurement bases; leftover `test-arch-*` worktrees.
- Handover notes to trim: `rpg-implementer-2.md` (70 KB); stale: `testing-implementer.md` (2026-10-07 header), `agent-working-designer.md`; legacy `test-architecture-*.md` to archive.

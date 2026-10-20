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

Last status pass: 2026-10-20, at `main` f6c7bc795 (fifth pass; the 2026-10-19 pass was at df3cb7256).

## Since the 2026-10-19 pass

- **Merged (u24 sessions):** #654 (rpg R2 request histogram), #662 (rpg: 0.3 s histogram bucket for the API SLO alert), #653, #658 (rpg pre-v1 batch; owner accepted the D74 override), #651, #655 (Node 24 in test.yml; the merge needed the `workflow` token scope), #659 (CI-runtime child 1: xdist inside existing jobs), #660, #663, #664, #666 (rpg gate per-level and per-reference), #665 (platform u24: `security-scan.yml`, gitleaks plus Semgrep, report-only), #667 (testing: workflows pass the github context through `env`), #675 (testing: actions pinned by SHA), #668 (platform u24: deploy-docs pins, frontend image non-root on 8080, the code-scanning upload drops in-source-suppressed results). Ubuntu: #647, #661, #670 (asset rc-0012), #671, #674. #609 closed.
- **`-u24` seats are live (#661, 710473fb5):** platform-planner-u24, platform-implementer-u24 and agent-working-{planner,implementer,designer}-u24, each relaunched once with `tools/sessions/launch.py <role>-u24 --worktree <path>` after syncing its worktree to origin/main (the role card is read from the worktree).
- **Owner decision, 2026-10-19: every workflow pins each action by full commit SHA with a `# vX.Y.Z` comment**, GitHub-owned actions included; Dependabot keeps them current, grouped monthly. Recorded in `docs/guides/delivery_process.md` ("Action pin rule"). Each owner converts its own files: testing (#675) and platform (#668) are done; agent-working's `pr-body-lint.yml` is the last one. After that, testing widens the pin guard to every workflow (TCK-20261020-WORKFLOW-PIN-GUARD-COVERS-EVERY-WORKFLOW).
- **Security-scan lane:** main's scan after #668 has 23 open Semgrep alerts, none on a `# nosemgrep` line. Still to do: the three junit XML alerts (#244-#246, `tools/ci_junit_*`, testing's TCK-20261020-CI-JUNIT-TOOLS-ACCEPT-DEFUSED-XML-FINDINGS, blocked on the roles ticket that gives the unowned paths an owner) and the `src/lab` findings (rpg, after v1).
- **Import contracts block `Code health` since #671 (309715a72).** A PR that removes an import listed in `codebase/structure/import_layers_baseline.txt` must delete that line in the same PR (guide: issue #673; #674 makes CI name the stale entry). rpg's pre-v1 branch already passes `import_contracts ci`.
- **Frontend container port:** #668 moves the frontend from 80 to 8080 (unprivileged nginx). Ubuntu's DevOps steps 2-3 were told on #618. `deploy-docs.yml` runs only when dispatched and Pages is disabled, so its two major action bumps are unproven until the owner dispatches it.
- **RPG (summary):** baseline v1 waits on the pre-v1 fixes. The owner ruled V3 (a starving character must treat starvation as a present threat) is fixed before v1, with no known red. Lane B's `rpg-pre-v1-fixes` carries the real-kernel gate positives, V4 and V1; Lane A builds V3; then one combined PR. testing's v1 re-anchor date is 2026-10-31.
- **Disk (2026-10-20):** `/` fell to 2.2 GB free; personal-career (other repo) removed its orphaned 2.3 GB scratchpad, so `/` is at 4.9 GB, and `~/.cache/uv` (4.2 GB) can be pruned. `/mnt/data` 15 GB free after the owner pruned 11 merged worktrees (backup `~/Working/worktree-backup-2026-10-19.txt`).

## Earlier passes

### Since the 2026-10-18 pass (written 2026-10-19)
- **Merged:** #637 (testing: Frontend lane runs on `visual_assets/` and the M5 criteria doc), #645 (rpg M0 batch, 37 tickets; ai_worker `/metrics` on 9108), #646 (v1 dependency window: uv group, redis-py 8 with the Redis 8.10.2 image, Starlette 1.x; merged before lead-planner's review, soak PASS), #650 (platform u24: the default compose stack publishes the event stream to Redis), #648 (rpg R1: backend metrics on internal port 9109), #649 (testing: `simq_reanchor` and the live compare refuse runs not recorded host-independent; the v1 re-anchor prerequisite). Ubuntu: #632, #638-#644. Dependabot #578, #579, #566, #580 closed as superseded by #646.
- **Branches deleted by the owner, 2026-10-19:** `platform-implementer-stream-env-u24`, `rpg-metrics-port`, `testing-simq-refuse-nonaudit`, `platform-implementer-cosign-attest-label`.
- **Merging to `main` needs `--admin`.** The `protect_branches` ruleset restricts updates to the admin role; required checks are Code health and Type check. Use `gh pr merge <n> --squash --admin`, and delete the remote branch with `git push origin --delete <b>` when a worktree holds the local branch (`--delete-branch` stops at the local delete).
- **`-u24` seat names (#620 option a, #634):** ubuntu's roles PR (TCK-20261018-SESSION-ROLES-HOST-SUFFIXED-U24-SEATS) is not open yet. agent-working-planner (u24) posted each u24 seat's worktree and staffing on #634 and recommended keeping the current paths (platform-implementer uses `platform`, agent-working-implementer uses `agent-working`). Nothing renamed; u24 seats relaunch once after it merges. Ubuntu takes the W42 close-week.
- **9109 compose hunk:** backend `expose: ["9109"]` (never `ports:`) feeds the step-2 scrape, so it is ubuntu platform's (#618), not u24's.
- **testing CI-runtime epic** (`agent-working/tickets/todos/ci-runtime/`, filed on the owner's dispatch): xdist inside existing jobs with no net new jobs, a warn-only runtime budget taken after the Ubuntu 26 runner move, and main-push lanes never skipped (only SimQ drift may go schedule-only). Each child PR is reviewed by this seat by comment; child 3 also by lead-planner (ubuntu). Queued after V8, Node 24 and phase19.
- **MCP status (2026-10-19):** knowledge-search OK; aseprite OK; headroom MCP OK (its 8787 proxy is off by design: proxy mode was dropped 2026-09-21); github MCP now starts (owner added `.env`, image v2.0.2). It runs with write access; `GITHUB_READ_ONLY=1` was recommended. The `.env` path is relative, so worktree sessions don't see it.
- **Disk and memory (2026-10-19):** `/` 5.2 GB free (89 %, holds `/tmp` scratchpads and Docker); `/mnt/data` 16 GB free. 8 GB RAM, about 3 GB available with 13 sessions. career-44 (other repo) runs capped jobs under a 2 GB, 200 % CPU scope and yields to RPG runs.


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
| rpg-planner | runs Lanes A-C toward the combined pre-v1 PR | busy | V3 fix (Lane A) | combined pre-v1 PR, then baseline v1 | 2026-10-20 |
| rpg-implementer (Lane A) | V3 starvation-as-threat on `rpg-v3-starvation-threat` | busy | none | paired measurement, seeds 42-46; a stop goes to the owner | 2026-10-20 (via rpg-planner) |
| rpg-implementer-2 (Lane B) | `rpg-pre-v1-fixes` (pushed, no PR) | busy | V3 and the designer's docs | fold them, full checks, open the combined PR on the owner's yes | 2026-10-20 |
| rpg-implementer-3 (Lane C) | real-kernel gate positives (merged into Lane B) | idle | none | per rpg-planner | 2026-10-20 (via rpg-planner) |
| rpg-designer | 4 rule docs for V3 and the disclosure | busy | none | review Lane A's Bible 04 section | 2026-10-20 |
| testing-planner | `testing-planner-idle`; pin and junit follow-ups filed | idle | roles ticket (junit) | review #676; CI-runtime children 2-3 | 2026-10-20 |
| testing-implementer | #676 (harness run-dir race under xdist) | busy | 1 red check on #676 | fix, then next dispatch | 2026-10-20 (from PRs) |
| agent-working-planner-u24 | roles ticket TCK-20261019-SESSION-ROLES-OWN-UNOWNED-SEMGREP-PATHS | waiting | owner's OK to dispatch | dispatch; pr-body-lint pin; Semgrep baseline in its paths | 2026-10-20 |
| agent-working-implementer-u24 | native-refusal hotfix (committed, unpushed) | idle | owner's push yes | push, open the PR | 2026-10-19 |
| agent-working-designer-u24 | handover dated 2026-10-07 | not running | none | on demand | 2026-10-07 |
| platform-planner-u24 | #665, #668 merged | idle | none | watch the first dispatched deploy-docs run | 2026-10-20 |
| platform-implementer-u24 | #668 merged | idle | none | next dispatch | 2026-10-20 |

## Open PRs (u24desktop view)

| PR | owner | state |
|---|---|---|
| #676 harness run-dir race | testing | 1 check red; testing-planner's review |
| (unopened) native-refusal hotfix | agent-working | waits on the owner's push yes |
| (unopened) combined pre-v1 | rpg | waits on V3 |
| #565, #567-#570 frontend npm | rpg | after v1, one at a time |
| #529 paired perf tripwire | perf (ubuntu) | not tracked here |

## Overlap and conflicts

Work that duplicates or blocks another session, on either host. One line each: what, which sessions, since when, what would
resolve it (a recommendation to the owner, not an instruction).

- **Unowned paths** (`tools/ci_junit_*`, `tools/handover_transit.py`, `tools/search/**`, `.github/workflows/rpg-gate-report.yml`) since 2026-10-19: findings on them have no owner. Resolves when the owner OKs the roles ticket (testing and agent-working agreed on the split).
- **`docs/REGISTRY.yaml`**: the local `merge-tree` check without the driver still reports hunks that GitHub merges cleanly (#668 on 2026-10-20). Merge one PR at a time and watch main's registry test after each.
- **Main checkout pulls** trip on modified monitoring shards (`manual_actions.jsonl`, 2026-10-20): save the added lines, restore the file, pull, re-append.
- **CI-runtime child 3** touches main-push lanes that the Slow regression watchdog, perf baselines and the rpg gate report read; lead-planner (ubuntu) and platform-planner review it.

## Pending owner decisions seen from this host

- Code scanning "Check runs failure threshold" set to None (`delivery_process.md` describes it as the repo setting).
- OK to dispatch the roles ticket TCK-20261019-SESSION-ROLES-OWN-UNOWNED-SEMGREP-PATHS (agent-working-planner-u24's terminal).
- Push yes for agent-working-implementer-u24's native-refusal hotfix.
- github MCP: add `GITHUB_READ_ONLY=1` to `.env` (recommended).
- `.claude/settings.json` `PostToolUseFailure` entry (agent-working-implementer's ask, from #612).
- rpg Lane A's 377 old run dirs (about 0.2 GB); rpg-planner to name which unmerged rpg worktrees are folded and removable.
- Handover notes to trim: `rpg-implementer-2.md` (72 KB), `testing-implementer.md` (2026-10-07 header).

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

Last status pass: 2026-10-25, at `main` 54b1dcf85 (sixth pass; the 2026-10-20 pass was at f6c7bc795).

## Since the 2026-10-20 pass

- **Baseline v1 recorded:** #725 merged as 341f700d0 (2026-10-23). The `src/**` freeze is over. Gate run 39799337778: V2 15/15, V3 exactly the 3 known cases.
- **Merged (u24 sessions):** #718, #719, #720, #722, #725, then #726 (M1 done criteria and freeze rule, roadmap §12.5, owner-approved, 6c1373951), #727 (known entries scoped by `cases:`; N14 and N15 V3 entries expire 2026-11-05, 0a3df6159) and #728 (memo row 89 and the §12.5 Base clarification, c6ff5149f). Ubuntu and other hosts since then: #723, #724, #529, #736-#741, #742 (Remote Control between the two leads), #743 and #744. #745 is open.
- **Owner rulings logged on #715:** 6356123802 (§12.5 approved; the D73 step is separate; D68 waits on per-subject records), 6356212656 (memo row 88: "acting" is an act, scope S1, step B goes first) and 6356509993 (the repairs HUNGER B, then A, then F4, then the D73 step sit on one cumulative watch; the D73 record is v1.1 and is recorded even if D73 is neutral).
- **Repo security (2026-10-23):** the owner turned on Dependabot alerts and private vulnerability reporting. Dependabot security-update PRs stay off on purpose. The 17 Semgrep alerts are triaged by owner: 14 in `src/` go to rpg's TCK-20261019-SEMGREP-BASELINE-FINDINGS-IN-SRC-TRIAGE (CORS read from config, `usedforsecurity=False` on 7 md5 sites, read `src/lab` #232/#234). That ticket sits only on the unpushed `rpg-planner-seat` branch, and rpg-planner was asked on 2026-10-25 to note it on #593. Agent-working's 2 alerts (#247, #248) are fixed by #729, merged 2026-10-25 as 8c7ead02b by ubuntu's agent-working pair. The policy lives at `.github/SECURITY.md`, owned by platform. Asset's #243 waits until asset's seats are live. The convention from #701: suppress a false positive in code with `# nosemgrep: <rule>` plus a reason, never in the Security tab.
- **Session stop, 2026-10-24:** every u24 seat except this one stopped uncleanly at about the same time. The machine itself did not reboot. On 2026-10-25 the owner resumed rpg-planner, rpg-designer, rpg-implementer 1-3, testing-planner, testing-implementer and architecture-planner-u24 with `tools/sessions/launch.py <role> --resume`. The agent-working-u24 and platform-u24 seats can't launch: the worktree each has on record is missing, and the fallback worktree's `.claude` differs from origin/main.
- **Remote Control (#742):** the two leads message each other directly with SendMessage. #715 stays the approvals log, and `for:<role>` issues stay the durable handoff.
- **Host queue (one heavy run at a time):** Lane C's H2 hash check, then the HUNGER step B paired run (running 2026-10-26; perf ruled on 10-24, owner-approved: `last_hit_tick` ships unhashed under flat-sha256-v2 and becomes F1's 7th field; #593 6384425767, #715 6384423281), then the H1 hash check, then the HUNGER step A paired run (about 11-04), then the F4 paired run (about 11-06/07), then the D73 step, which is recorded as v1.1. The N14 and N15 entries expire 11-05, and rpg raises a renewal with the owner by 11-03 if the dates slip.
- **Disk and memory (2026-10-25):** `/mnt/data` has 5.3 GB free (warning below 10 GB) and `/` has 7.0 GB. 8 GB RAM, about 4 GB available. Old worktrees that could be pruned, with the owner's yes: baseline-pre, baseline-post, health2, redis-pin, lane-a-tactical-path-batch, m2-idea43-temporal-note and others (`python3 -m tools.sessions.prune_branches --worktrees`).

## Earlier passes

### Since the 2026-10-19 pass (written 2026-10-20)

- **Merged (u24 sessions):** #654 (rpg R2 request histogram), #662 (rpg: 0.3 s histogram bucket for the API SLO alert), #653, #658 (rpg pre-v1 batch; owner accepted the D74 override), #651, #655 (Node 24 in test.yml; the merge needed the `workflow` token scope), #659 (CI-runtime child 1: xdist inside existing jobs), #660, #663, #664, #666 (rpg gate per-level and per-reference), #665 (platform u24: `security-scan.yml`, gitleaks plus Semgrep, report-only), #667 (testing: workflows pass the github context through `env`), #675 (testing: actions pinned by SHA), #668 (platform u24: deploy-docs pins, frontend image non-root on 8080, the code-scanning upload drops in-source-suppressed results). Ubuntu: #647, #661, #670 (asset rc-0012), #671, #674. #609 closed.
- **`-u24` seats are live (#661, 710473fb5):** platform-planner-u24, platform-implementer-u24 and agent-working-{planner,implementer,designer}-u24, each relaunched once with `tools/sessions/launch.py <role>-u24 --worktree <path>` after syncing its worktree to origin/main (the role card is read from the worktree).
- **Owner decision, 2026-10-19: every workflow pins each action by full commit SHA with a `# vX.Y.Z` comment**, GitHub-owned actions included; Dependabot keeps them current, grouped monthly. Recorded in `docs/guides/delivery_process.md` ("Action pin rule"). Each owner converts its own files: testing (#675) and platform (#668) are done; agent-working's `pr-body-lint.yml` is the last one. After that, testing widens the pin guard to every workflow (TCK-20261020-WORKFLOW-PIN-GUARD-COVERS-EVERY-WORKFLOW).
- **Security-scan lane:** main's scan after #668 has 23 open Semgrep alerts, none on a `# nosemgrep` line. Still to do: the three junit XML alerts (#244-#246, `tools/ci_junit_*`, testing's TCK-20261020-CI-JUNIT-TOOLS-ACCEPT-DEFUSED-XML-FINDINGS, blocked on the roles ticket that gives the unowned paths an owner) and the `src/lab` findings (rpg, after v1).
- **Import contracts block `Code health` since #671 (309715a72).** A PR that removes an import listed in `codebase/structure/import_layers_baseline.txt` must delete that line in the same PR (guide: issue #673; #674 makes CI name the stale entry). rpg's pre-v1 branch already passes `import_contracts ci`.
- **Frontend container port:** #668 moves the frontend from 80 to 8080 (unprivileged nginx). Ubuntu's DevOps steps 2-3 were told on #618. `deploy-docs.yml` runs only when dispatched and Pages is disabled, so its two major action bumps are unproven until the owner dispatches it.
- **RPG (summary):** baseline v1 waits on the pre-v1 fixes. The owner ruled V3 (a starving character must treat starvation as a present threat) is fixed before v1, with no known red. Lane B's `rpg-pre-v1-fixes` carries the real-kernel gate positives, V4 and V1; Lane A builds V3; then one combined PR. testing's v1 re-anchor date is 2026-10-31.
- **Disk (2026-10-20):** `/` fell to 2.2 GB free; personal-career (other repo) removed its orphaned 2.3 GB scratchpad, so `/` is at 4.9 GB, and `~/.cache/uv` (4.2 GB) can be pruned. `/mnt/data` 15 GB free after the owner pruned 11 merged worktrees (backup `~/Working/worktree-backup-2026-10-19.txt`).

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
| rpg-planner | #746: 17 seat tickets to main, including the src Semgrep triage ticket | live | none | review the Lane B and C PRs | 2026-10-26 |
| rpg-implementer (Lane A) | `rpg-hunger-retreat-one-scale`: HUNGER step B built with perf's ruling (ii) | busy: probe and paired run on the host (base 341f700d0) | none | step A after step B | 2026-10-26 |
| rpg-implementer-2 (Lane B) | `rpg-v1-calibration-d76`: calibration ticket closed | PR approved (#715 6406571536) | none | H1 on `rpg-hostility-projection-cost`, plan-only until the host frees | 2026-10-26 |
| rpg-implementer-3 (Lane C) | `rpg-cooperation-candidates-index`: H2 done and proven byte-identical, cooperation phase about 2.8x faster, carries 12 tickets | PR approved (#715 6406571536) | none | F3 | 2026-10-26 |
| rpg-designer | `rpg-designer-m1-base` (#728 merged) | resumed | none | on demand | 2026-10-25 |
| testing-planner | `testing-planner-v1-followups`: T1 run ledger and T2 filed | resumed | none | scope T3; review testing's PRs | 2026-10-25 |
| testing-implementer | `testing-implementer-simq-reanchor-v1` | resumed | none | per testing-planner | 2026-10-25 |
| architecture-planner-u24 | engine-modes step 1 is scheduled: H2 on Lane C, H1 on Lane B | resumed | none | review the H1 and H2 PRs | 2026-10-25 |
| agent-working-planner-u24 | none (#729 merged by ubuntu, 2026-10-25) | not running | worktree on record is missing | relaunch only when there is work | 2026-10-24 |
| agent-working-implementer-u24 | none (#729 merged by ubuntu, 2026-10-25) | not running | worktree on record is missing | relaunch only when there is work | 2026-10-24 |
| platform-planner-u24 | owns `.github/SECURITY.md` (#729); may rewrite the stub when back | not running | worktree on record is missing | relaunch only when there is work | 2026-10-22 |
| platform-implementer-u24 | idle | not running | worktree on record is missing | relaunch only when there is work | 2026-10-22 |
| agent-working-designer-u24 | none | not running | none | on demand | 2026-10-07 |

## Ubuntu's items for rpg-planner (relayed 2026-10-25, answered 2026-10-26)

| item | state |
|---|---|
| T06 docs/engine lift for #735 (#593 6386482656; owner wording #715 6386636889, 6386816236) | GRANTED: §3.3/§5 only, no src outside src/perf, owner OK in the PR, rpg-planner reviews (#593 6406593752) |
| Lane split U2-U4 for ubuntu's rpg seats (#593 6393498282, correction 6393509350) | U2 batch 1 RELEASED, U3 and U4 YES, with conditions: hash-neutral proof per PR; ubuntu is the only mechanisms.yaml editor during batch 1; stay out of the u24 lanes' files and data/worlds (#593 6406593752) |
| #617 `--entities`: make it work, warn, or remove | REMOVE `--entities` from cli as an rpg hotfix; #617 closes when it lands |
| #721 asset entity-marker icon mapping | answered (#721 6406594384): a client-side table keyed on kind, re-keyed at M1; the asset lane may edit useCanvas' entity layer |

## Open PRs (u24desktop view)

| PR | owner | state |
|---|---|---|
| #746 seat tickets to main; Lane B calibration and Lane C H2 PRs follow | rpg | owner approved the pushes (#715 6406571536); lead comments on cross-domain impact only |

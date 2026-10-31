---
status: active
layer: ai
authority: P2
audience: agent
date: 2026-10-30
tags: [ai, audit, governance, delivery, planning]
---

# AI-First SDLC: Decision Summary and Evidence Refresh

Status: proposal, nothing implemented. It summarises `AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md`, written at `1f749c1aa` and revised in Round 2 on 2026-10-31. Numbers here were re-measured at `ba7aa11bd` from host ubuntu on 2026-10-30. W44 is partial: it holds only rows already on main, and the week runs to 11-01.

**How far to trust this.** The plan's citations do not cover an operating model like this one (about 20 long-lived seats, two hosts, one owner), and no experiment has tested the proposed design. The one experiment run, E1, read the current system's history. Some sources were read second-hand, because arxiv and openai were blocked from the host (plan §7).

## The proposal

Keep what delivers: seats, worktrees, batch PRs, tickets and the recorder. Add three hard boundaries, then freeze and remove the dormant pipeline:
- **Identity:** agents use a machine user with write access and no admin, and your credentials leave both hosts.
- **Integration:** only you can merge, and one always-run CI job shows you the verdict.
- **Evidence:** one close command records what's known at close. PR, CI and merge facts come from GitHub later.

Separately, a small evaluation track starts with a Sonnet/Opus pilot (plan Part IX). Production never depends on it.

## What the proposal rests on

Basis: **measured** here, **platform docs** (how GitHub or Claude Code says it behaves), **cited advice** (research or guidance about other settings), or **reasoned** (argued, no data).

| Claim | Basis | Tested here? | What would prove it wrong |
|---|---|---|---|
| The shared admin login is the main defect; a separate agent identity fixes it (OD-2, OD-10) | Measured for the defect; cited advice and platform docs for the fix | No: E6a, Phase 1 | After revocation, an agent can still act as you |
| M1 keeps merge yours on GitHub (OD-3) | Platform docs, from a delegated pass | No: E6b pending | E6b: the machine user can merge, or your merge fails |
| Merging from outside the VMs won't hurt delivery (OD-7) | Reasoned | No: first read in Phase 2's 2-week window | Merges slow or batch up in that window |
| Design D beats a rebuild, an orchestration engine or ephemeral workers | Reasoned | No: E2a, E2c, E4, opt-in, Phase 6 | A thin pipeline gives materially fewer defects at similar cost, or interruption losses are large (plan §61) |
| A close check, evidence layers and a gate job catch what matters at fair cost (OD-4, OD-11, OD-13) | Reasoned, on a measured baseline (1-2 of 84 closes premature) | No: E1-replay, Phase 2 | Replay finds little, or false positives slow delivery |
| Removing the pipeline loses nothing in use (OD-5, OD-6) | Measured non-use, which doesn't show removal is safe | No; tags keep it recoverable | A later comparison favours it |
| Delivery today is healthy | Measured to 10-26, by CI green and reverts | E1, read-only | Those can't see outcome movement: a green PR can move simulation results, which then get re-anchored, not reverted |
| An evaluation track will give usable answers (OD-16 to OD-21) | Cited advice and reasoned | No: R1 pilot | The pilot can't tell the models apart at its budget |

OD-8 and OD-9 are "measure first", so they carry no claim yet.

## What the refresh changed

| Plan's claim | Now | Effect |
|---|---|---|
| 100% of closes by hand (W42-W43) | 319 of 319 in W42-W44. At least 113 came from ubuntu seats and 94 from u24 seats; 112 can't be placed | Holds on both hosts. Supports OD-1 and OD-5 |
| Ubuntu behaves like u24 (unverified) | Same GitHub admin login. Local permission setups differ in some respects; details withheld by your condition (#715 6528807751) | Mostly holds. OD-2 must cover both hosts' setups |
| Every merge bypasses the ruleset, so the required checks bind no one | Ruleset unchanged. The latest 40 merges all came from your login with no review decision | Holds |
| Four guard bypass forms | All four still classify as no action when run through `tools/sessions/classify.py` on its own; the full guard and live auto-mode were not run | Holds |
| Messages per close: 3.8, 7.7, 11.8 | 3.7, 8.5, 17.8 (W41-W43); 18.1 so far in W44 | **Worse than stated.** W43's message rows are now 2,006; the plan's rate implies about 1,400, so it probably predates late shards (inferred) |
| About 30% of closes have no seat | W41 52%, W42 11%, W43 0%, W44 0% | **P-4 partly fixed.** No model, PR or commit link yet |

**On messages:** the total rose with the number of sessions (26, 62, 41 for W42-W44). Messages per session fell (49, 32, 24). So the cause may be more seats, not noisier seats. This is a correlation only, and it's the main input for OD-9.

**New gaps:**
- Run rows have no host field, so host share comes only from seat names. 112 of 319 closes can't be placed.
- Ubuntu used 15,135 requests and 3.46 B cache-read tokens since 10-16, with a 233k average context. That's the same order as u24's 15-day figure, so the plan's u24-only token figure leaves out a large share of real use.

**Host stability:** ubuntu ran through the Windows hypervisor until 10-30, with 19 soft lockups in the prior 30 h and a kernel panic, and that setup has now changed (#715 6527003378). This summary cites no ubuntu timings. Any later time comparison should not use ubuntu data from before 10-30 as its baseline. Whether the crash or stalls affected the token counts was not checked.

**Not re-measured:** CI green at merge, reverts, premature closes and lead time remain as of 10-26. Claude Code behaviour is still from docs only, and live auto-mode was not tested. No experiments ran.

## What Round 2 changed

An external review (ChatGPT, advisory) and your research problem led to these changes. Plan: Resolution Matrix at its top.
- **Credentials (F1):** the plan's separate `GH_CONFIG_DIR` is no boundary, because agent processes can reach your credentials. You'd review and merge from outside the VMs, and old tokens get revoked.
- **Merge (new):** a personal-repo collaborator can merge an approved PR, so the first ruleset design would have broken your owner-only merge. The recommended M1 keeps it, with no approval step. The prices: checks stay advisory on the server, because your merge is the check; merges leave the VM terminal for your own shell on the physical machine, a real cost at about 87 a week; and merges must keep `--match-head-commit`, since the server won't stop a late push.
- **Evidence (F2):** three linked layers, so no record names a commit that doesn't exist yet.
- **Claims (F3):** advisory by default, with ref creation for cross-host work. Duplicates are rare (1 of 318 tickets).
- **CI (F4):** one always-run gate job. A PR can still edit its own workflow on a personal repo, and that residual risk is stated.
- **Rollback (F5):** if the machine user fails, agent publishing stops. Agents never get your token back.
- **Retirement (F6):** freeze as git tags first; then remove. Replay's sampler is kept for research.

**Not yet tested:** several GitHub behaviours, including M1 itself, need a throwaway-repo test (E6b). You ran u24's credential check, with the same finding as ubuntu. Credential details stay out of this public file by your condition (#715 6528807751).

## Your decisions

**Decided 2026-10-31 (#715 6529263880):** OD-1 yes; OD-2 + OD-10 yes; OD-3 as M1, subject to E6b; OD-14 yes; OD-15 yes; E6b yes. No credential or ruleset change is authorised by this: each gets its own ask, by ticket.

**Still open:**

| # | Decision | Recommendation | When |
|---|---|---|---|
| OD-7 | Review load | Follows OD-3; M1 adds no approval, but moves every merge out of the VM (87 merges in W43, 45 in 5 days of W44) | With E6b's result |
| OD-4, OD-11, OD-12, OD-13 | Machine-proven close; evidence layers; claims; gate job | As in the plan | Phase 2 entry |
| OD-5, OD-6 | Remove pipeline; Codex track | Remove from production after tagging; decide Codex at R2 | Phase 4 entry |
| OD-16 to OD-21 | Evaluation budget and execution; framework; scope; research-only search; promotion; thresholds | Budget after R0; hybrid framework; search stays research-only | R1 entry onward; lead-planner advises R1 wait until Phase 2 lands, to keep your attention on authority and completion |
| OD-8 | Token budget | Measure first; needs both hosts | Phase 3 exit |
| OD-9 | Coordination target, and one queue for asks across hosts | Measure per session as well as per close, then decide | M7, on or after 11-04 |

Before any credential change: a ruleset export as the rollback point, and an inventory of credential stores and tools that assume your login (plan §54, §27a).

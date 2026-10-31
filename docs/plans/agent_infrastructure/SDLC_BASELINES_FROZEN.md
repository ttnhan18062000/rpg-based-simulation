---
status: active
layer: ai
authority: P2
audience: agent
date: 2026-10-31
tags: [ai, governance, delivery, planning]
---

# AI-First SDLC: Frozen Baselines

The baseline table of `AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md` section 46, frozen as a dated record so later phases compare against fixed values.

- **Frozen:** 2026-10-31. **Ref:** `origin/main` at `1ccaba303` (the commit that put the plan on main). Values are copied as written in section 46 at that SHA; nothing was re-measured for this record, so each row's measurement window is the one in the plan's Value column.
- **Refreshable rows** (the plan marks them "refreshed"): hand versus pipeline share, unattributed `session_role`, messages per closure. A later refresh is a new dated record with its own ref and SHA; it does not edit this one.
- **Every row's ref and SHA:** plan section 46 at `1ccaba303`. The plan names no commit for the measurement itself, except that the summary re-measured at `ba7aa11bd` (host ubuntu, 2026-10-30) the rows it refreshes.
- This record does not name a budget or a threshold (OD-8, OD-21 are undecided).

| Metric | Value | Source | Quality | Ref and SHA |
|---|---|---|---|---|
| Closures per week, DONE runs (std/hotfix/epic) | W40 241 (158/71/9) · W41 276 (194/71/9) · W42 151 (87/52/12) · W43 112–120 (36/76/0) | runs shards | Late rows arrive; tier is self-declared | plan §46 @ `1ccaba303` |
| PRs merged per week | W40 79 · W41 164 · W42 66 · W43 90 | git first-parent | Good | plan §46 @ `1ccaba303` |
| Lead time, ticket first in git → merge (n=84) | median 4.1 h; p75 36 h; p90 83 h | git + `gh` | Lower bound (tickets filed at close) | plan §46 @ `1ccaba303` |
| CI first-pass rate (PR "Tests") | 72% (43 of 60) | `gh api actions/runs` | Includes REGISTRY-drift failures | plan §46 @ `1ccaba303` |
| CI red at merge | 0 of 51 closing PRs | `statusCheckRollup` | Head only | plan §46 @ `1ccaba303` |
| Reverts in 60 days | 0 of 550 | git | Good | plan §46 @ `1ccaba303` |
| Provably premature closes | 1–2 of 84 | follow-up ticket text | Heuristic | plan §46 @ `1ccaba303` |
| Finalize self-check PASS on closes | 79 of 84; 93.5% coverage since 10-07 | gate_verdicts | Certifies bookkeeping only | plan §46 @ `1ccaba303` |
| Hand vs pipeline share W42–W44 (refreshable) | 100% hand (319 of 319; W44 partial) | runs, refreshed 10-30 | Good | plan §46 @ `1ccaba303`; refreshed at `ba7aa11bd` |
| Unattributed `session_role` (refreshable) | W41 52%, W42 11%, W43 0%, W44 0% | runs | Good | plan §46 @ `1ccaba303`; refreshed at `ba7aa11bd` |
| Messages per closure (refreshable) | 3.7 → 8.5 → 17.8 (W41 → W43), 18.1 W44 so far | tools shards | Trend | plan §46 @ `1ccaba303`; refreshed at `ba7aa11bd` |
| Messages per session | 49 → 32 → 24 (W42 → W44) | tools shards | Correlation only | plan §46 @ `1ccaba303` |
| Approvals log volume | 110 comments in 5 days | #715 | Good | plan §46 @ `1ccaba303` |
| Tokens (u24 host, 15 days) | 20,726 requests; 4.25 B cache-read; 12.1 M output; avg context 210k; 92 compactions; 92% main-session | `real_token_usage.py` | Host-local, no $ | plan §46 @ `1ccaba303` |
| Dormant code | ~9.2k Python + 5.5k JS | plan §32 | Good | plan §46 @ `1ccaba303` |

## Host ubuntu timings before 2026-10-30 are not a baseline

Host ubuntu had a guest kernel panic and repeated soft lockups before 2026-10-30. The owner then changed the Windows host's virtualisation setup (#715 comment 6527003378, 2026-10-30), which changed timing, and the comment states that old perf records are not comparable. So **no ubuntu wall-clock, perf or throughput timing taken before 2026-10-30 is a baseline**. The rows above that touch ubuntu seats (counts of closures, messages and sessions) are counts from shards, not timings, and are unaffected. Any timing baseline for ubuntu is measured after that change and after the owner's judgement of the soft-lockup count, as its own record.

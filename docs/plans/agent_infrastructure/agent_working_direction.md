---
status: active
layer: ai
authority: P2
audience: agent
date: 2026-10-01
tags: [ai, agent-monitoring, data-quality, delivery]
---

# Agent-Working Direction — Observable, Self-Diagnosing, Adaptable Delivery

**Purpose**: a living index of where the agent-working track is heading and why, so a new session can
resume without the chat history. It states the goal and the open directions once. Details live in the
linked tickets and docs, not here. The frozen H0–H3 hardening program stays in
[`ai_first_hardening_epics/roadmap.md`](ai_first_hardening_epics/roadmap.md); this doc covers what grew
after it.

**Goal** (user, 2026-10-01): AI-first, fully automated development up to the deliberate human points
(push, PR creation, merge, workflow opt-in), with three properties:

1. **Observable**: every run leaves trustworthy recorded data.
2. **Self-diagnosing**: the data shows where the workflow is inefficient or wrong.
3. **Adaptable**: the workflow fits different kinds of work instead of being bypassed.

## Where we stand (measured, W40 retro, 2026-10-01)

| Pillar | What exists | Gap, with evidence |
|---|---|---|
| Observable | Per-run, per-phase and per-tool records, weekly shards, retro | About 94% of runs since early September are hand closures with zero duration. The spend proxy covers 18.3% of events. Much of the data measures the recording tool, not the work. |
| Self-diagnosing | Slow-run, outlier, gate-failure and skip tables | Symptoms, not causes. One run was 100% idle waiting on a human. Parity was skipped 49 of 51 times and Security-Review 6 of 6. A plan-gate false negative was caught only because a human read the plan. |
| Adaptable | Tier routing, phase skipping, hand-orchestration path | The formal pipeline has barely run since early September, so flexibility came from bypassing it. The data cannot yet say whether the pipeline is too heavy or hand-orchestration simply fits better. |

## Directions

Status values: `shipped`, `in flight`, `next`, `idea`, `held`.

### Observable

| Direction | Status | Tickets / notes |
|---|---|---|
| Native-runtime decision for the formal pipeline | in flight | shipped (PR #274): `TCK-20260930-IMPLEMENT-TICKET-PARSE-AND-NONDETERMINISM-FIX`, `TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN` (nonce-hash attestation forged first try: adopt for gates only plus an orchestrator re-run), and 3 of 5 children of `TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT` (bookkeeping/advisory sites, input sites, orchestrator backstop). Deferred by user decision until the cheap children's cost is seen: the attested-gate and native-run children |
| Week-close: fold a finished week's shards into the three canonical files, explicitly | shipped | `TCK-20261001-MONITORING-WEEK-CLOSE-COMMAND` (PR #274): `make agent-monitoring-close-week WEEK=...`, report-only nudge via the retro hook; W40 is not closed yet, that is the user's call |
| Retro report is read-only | shipped | `TCK-20261001-RETRO-REPORT-READ-ONLY` (PR #274): the retro no longer folds shards; consolidation is the week-close command's job |
| Post-merge integrity check against `origin/main` | shipped | `TCK-20261001-POST-MERGE-MAIN-INTEGRITY-REPORT` (PR #274): `make agent-monitoring-main-integrity`, on demand and report-only; wiring it into a post-merge hook stays open. First real triage 2026-10-02: 311 findings on `fe6a2f564` (probe as shipped in #274), 263 after PR #277 (`TCK-20261001-WORKING-LOG-BYTE-DUPLICATE-DEBT` removed 56 byte-identical working_log lines and the pair ceiling went 46 to 19; `TCK-20261001-INTEGRITY-REPORT-EPIC-TIER-FALSE-POSITIVES` stopped flagging epics that close as EPIC_SCOPED); 263 re-measured on `78ea7c465`. What remains is known: 119 historical `event_seq` findings (multi-invocation restarts, already explained by `TCK-20260915-EVENT-SEQ-INTEGRITY`), 13 cited-evidence (one real, a gitignored `.json` for `TCK-20260907-FILTERED-REPLAY-EVAL-PILOT`), 7 epics with no working_log row (not backfilled: a hand-written row would be invented history), and 124 "no DONE row" tickets, 122 of them pre-September |
| Real time and cost for hand-closed work | idea | changes how every later retro reads, so it needs its own design |

### Self-diagnosing

| Direction | Status | Tickets / notes |
|---|---|---|
| Cited evidence must be tracked in git | shipped | `TCK-20260930-CITED-EVIDENCE-PATH-GITIGNORE-CHECK` (PR #272), advisory only |
| Planning-doc staleness sweep, Proof Plan advisory | shipped | PR #268 |
| Delivery rework rate (first-pass CI, failure class) | shipped on fixtures; no real reading yet | `TCK-20261001-DELIVERY-REWORK-RATE-MEASUREMENT` (PR #274): `delivery_cost_measurement.py --rework`, baseline only; the real-corpus run timed out on `gh` twice, retry from a healthier network |
| Gate override ledger (verdict, inputs, human stop) | idea | measures gate precision without waiting for a person to notice |
| Finding-to-ticket-to-merge funnel | held | needs a stable finding-id convention first |
| PR body `Closes:` must reflect ticket location | shipped | `TCK-20261002-PR-RENDER-CLOSES-LISTS-FILED-FOLLOWUPS` (PR #280): a ticket under `todos/` or `inprogress/` is left out of `Closes:` with a warning, so a PR that files a follow-up no longer claims to close it; found twice by a peer reading the body (PRs #276, #279), not by `--check` |

### Adaptable

| Direction | Status | Tickets / notes |
|---|---|---|
| Record which path each ticket took and why | idea | invisible today |
| Tier-based routing for phases that are almost always skipped | idea | depends on the path record and on trustworthy data |

## Rules this track keeps

- Advisory checks are report-only. No blocking gates over monitoring data (agent tooling checks stay
  proportionate).
- Monitoring write failure never fails the workflow.
- Never edit an artifact to change a gate result; report the gate's verdict.
- Measure from a git ref, not the working tree, and treat a closed week as a snapshot: late shards can
  still arrive after a week ends (see `delivery_cost_measurement.py`).

## Hygiene batch: design findings

- The retro's `consolidate_all()` call was a **deliberate** trigger ("the retro cadence becomes the
  default consolidation trigger"), so removing it needs a replacement first: a week-close command plus
  a report-only nudge when a finished week still has shards.
- The retro already reads through the shard-aware loaders (`load_data_glob`, `shard_paths`), so it does
  not need the fold to see the data.
- Week-close refuses the current ISO week, and a late shard from a branch that merges after its week
  ended is re-folded by the next close.

## Decisions pending

- When the close runs: manual plus a report-only nudge (recommended), or scheduled.
- Whether the first real close is W40, at the start of W41.
- Which comes after the hygiene batch: real cost for hand closures, or the gate override ledger.

## Update protocol

Change a row's status here in the same batch that ships or re-scopes it. Do not copy ticket detail into
this doc; link the ticket. Review at each retro.

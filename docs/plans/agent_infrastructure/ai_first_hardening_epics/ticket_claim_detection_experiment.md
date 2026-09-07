---
status: active
layer: ai
authority: P1
audience: agent
date: 2026-09-07
tags: [ai, agent-monitoring, workflows]
---

# Experiment Specification — Ticket-Claim Detection Logging

**Tracking ticket**: `TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING` — unlike item 13
(`agent_evaluation_foundation_experiment.md`, "none"), this Bucket-B item converted directly into a
real ticket that both writes this spec document and implements the log-only instrumentation the
Method section below describes, per that ticket's own Request Summary reasoning (the "add log-only
instrumentation... no blocking, no lock file, just a detection signal" language in the source spec
is itself a small, concrete, buildable piece of work, not just planning prose).
**Source**: `workflow_reliability_epic.md`, milestone M2.
**Roadmap**: `roadmap.md`, row 14, Horizon 1.
**Priority**: P1.

## Why this is an experiment, not an epic

No agent behavior changes as a result of this instrumentation. It is purely additive observability:
a read-only check that flags (never blocks) when it detects another session apparently working the
same ticket ID. The entire output is evidence for a later decision — whether double-claims are real
and frequent enough in this repo's multi-worktree workflow to justify building an actual claim lock.
Per the epic's own kill-criteria decision gate, building that lock is explicitly deferred until this
instrumentation has run for a full 30-day/quarter observation window.

## Hypothesis

Two sessions independently resuming/continuing the same ticket ID within a short window is a real,
occasionally-occurring event in this repo's multi-worktree workflow, and a cheap, read-only
detection signal — built entirely from already-available session-identity data — can surface it
without meaningful false-positive noise from crashed or abandoned sessions' stale sidecars.

## Baseline

- **Zero known historical double-claim incidents.** Checked `tickets/done/`,
  `agent-monitoring/retro/`, and `tickets/inprogress/` at scoping time (2026-09-07) — no report of
  two sessions actually colliding on the same ticket ID was found.
- **Real concurrency opportunity already exists today.** `git worktree list` showed 8 active
  worktrees at scoping time, each on its own branch — this repo already runs many concurrent
  sessions routinely, so the zero-incident baseline is a starting point consistent with real
  concurrency, not evidence that concurrency itself is rare.
- **No reusable prior art.** `tools/agent_codex_pilot_executor/claims.py`
  (`acquire_claim()`/`terminalize_claim()`) was investigated and confirmed structurally unrelated:
  it is a per-ticket `fcntl.flock`-guarded advisory lock over a caller-injected `scratch_root`,
  built exclusively for the Codex pilot-execution harness's synthetic/disposable fixtures
  (`tools/agent_codex_pilot_executor/simulation.py::simulate_pilot()`). It actively **raises**
  `ClaimRefusedError` on a second claim — exactly the "build a lock" behavior this roadmap item's
  kill-criteria gate defers — and it never operates against the real `tickets/inprogress/`
  directory or a real multi-session Claude Code working tree. Not extended or reused here.

## Method

**The real signal**: `CLAUDE_CODE_SESSION_ID` — a stable, per-process environment variable the
Claude Code harness sets once per session, already confirmed present in every Bash subprocess
(`.claude/workflows/implement-ticket.js:280`) — and the session-scoped sidecar file it keys,
`.claude/current_run.<CLAUDE_CODE_SESSION_ID>`. This file is written by `writeSidecar()`
(`implement-ticket.js:274-285`) at every phase transition, and inline by the Scope-phase resume
branch (`implement-ticket.js:61-73`) before the ticket-scoper agent call. No new identity mechanism
is invented; this is the only on-disk session-identity artifact this repo already has
(`agent-monitoring/data/*/runs.jsonl`/`events.jsonl` carry no `session_id` field of their own).

**The check**: wired into `implement-ticket.js`'s Scope phase, immediately after
`const tid = ticketInfo.ticket_id` (line ~213) — the earliest point common to both the new-ticket
and resume branches where the ticket ID is confirmed real. A new module,
`tools/agent-monitoring/ticket_claim_detection.py::check_and_log()`, enumerates every other
session's `.claude/current_run.*` sidecar file (reusing `post_tool_hook.py`'s own
`Path(".claude").glob("current_run.*")` enumeration pattern, not its function) and flags a
detection only when **both** of the following hold for another session's scoped sidecar:

1. its `run_id` field equals this session's own `tid`, **and**
2. its file mtime is within `CLAUDE_DETECTION_WINDOW_SECONDS` (900 seconds / 15 minutes) of now.

Both conditions are required together — an `run_id` match alone would false-positive on a stale,
long-abandoned sidecar for the identical ticket; a recency match alone would false-positive on any
sidecar merely touched recently for an unrelated ticket. The legacy unscoped `.claude/current_run`
file is excluded from candidate matching (no reliable single-session identity), and the calling
session's own scoped sidecar is excluded by name.

**Important: what "within 15 minutes" actually measures.** The window is compared against the
*other* session's sidecar's last **phase-transition write**, not its continuous activity —
`writeSidecar()` is called once per phase transition, not on any regular heartbeat, so a sidecar's
mtime does not advance while a session is still working mid-phase. See Known Limitations below for
the specific gap this creates; do not read the 900-second figure as a guarantee this mechanism
catches every real concurrent-claim scenario.

A detection (if any) is written to a brand-new dedicated JSONL,
`agent-monitoring/data/YYYY-Www/claim_detections.jsonl`, via the shared
`tools/agent-monitoring/writer.py::write_line()` primitive — never into `runs.jsonl`/`events.jsonl`,
keeping this experimental, unvalidated-shape signal fully separate from the schema-validated
production shards. The check is always-on (no env-var gate — a local file glob plus JSON parse has
negligible cost, unlike the shadow-reviewer-logging precedent's gated extra LLM call), fully
fail-open (every failure mode — malformed JSON, missing file, a file vanishing mid-scan — is caught
and skipped, never propagated), and never blocks, refuses, or otherwise changes
`implement-ticket.js`'s control flow.

## Metrics

- **Detection count** over the observation period — a plain row count of
  `claim_detections.jsonl` across the 30-day/quarter window.
- **False-positive rate is explicitly not claimable** without a human-labeled ground truth of which
  detections were genuine double-claims vs. coincidental — mirroring
  `agent_evaluation_foundation_experiment.md`'s own "Terminology discipline" section, this spec does
  not claim a rate it cannot produce.
- **False-negative rate is even less claimable than the false-positive rate.** See Known
  Limitations below — the mechanism's own design leaves a real, evidence-grounded gap for a session
  mid-way through one long phase, so this spec does not discuss only the false-positive side and
  imply by omission that false negatives are not a concern.

## Exit criteria

The instrumentation runs in production for the epic's stated 30-day/quarter window without ever
raising an exception into `implement-ticket.js`'s control flow, and produces at least enough log
volume — **even zero detections is a valid, informative result, subject to the false-negative
caveat below** — to inform the later lock-vs-convention decision.

## Kill criteria

Pulled from the epic's own kill-criteria decision gate: if zero detections are logged after the
full observation window, the "build a lock" option is dropped and the convention (session-scoped
sidecars plus this log) stays as documentation, not enforcement.

**Caveat, load-bearing for whoever makes this call:** "zero detections" means "zero double-claims
this mechanism was able to catch," not "zero double-claims occurred." As Known Limitations below
documents, the check has a real false-negative gap for a session mid-way through a single long
phase, so a zero-detection result is weaker evidence of "no collisions ever happened" than a literal
zero would otherwise imply. The kill decision should weigh this explicitly, not treat the raw count
as ground truth.

## Known Limitations

Read this before treating a "zero detections" result as proof of "zero double-claims" — this is the
single most important caveat in this spec.

The window check compares "now" against the *other* session's sidecar's last **phase-transition**
timestamp, not its continuous activity. `writeSidecar()` (`implement-ticket.js:274-285`) is called
once per phase transition, not on any regular heartbeat, so a sidecar's mtime does not advance while
a session is still working mid-phase. Real Implement-phase (and Investigate/Plan-phase) dispatches
have been directly observed taking 20-30+ minutes — well over the 900-second window — with no
sidecar update for that entire span.

**Consequence**: if session A is 20 minutes into a single long phase on ticket X, and session B's
check runs more than 15 minutes after session A's *last* phase transition (not after session A
actually stopped), session A's sidecar already reads as stale (mtime delta > 900s) even though
session A is still genuinely, actively working — a real, plausible **false negative** on a genuine
concurrent-claim collision, not a hypothetical edge case.

This is deliberately **not** fixed by widening the window: a wider window (e.g. 30+ minutes) would
reduce this false-negative risk but increase the opposite failure mode, since nothing in the sidecar
distinguishes "session ended cleanly" from "session still mid-phase" — a wider window makes an
already-finished, genuinely-stale session more likely to be misflagged as still active. Consistent
with this epic's own "detect before prevent" framing, this asymmetry is accepted and documented as
an inherent limitation of a log-only, best-effort signal — not something to resolve by silently
retuning the `900` constant without new evidence justifying a different tradeoff point.

A second, separate accepted gap: two independent sessions coincidentally creating a **brand-new**
ticket with the identical slug are not addressed by this design at all (see Out of scope) — the
resume/continue scenario this mechanism targets is the one the source spec and this ticket's own
Baseline describe.

## Out of scope

- Building the actual claim lock (blocking behavior, refusal, or any lock file) — explicitly
  deferred per the epic's own kill-criteria decision gate; only revisit if real double-claim
  incidents are observed within the 30-day/quarter window.
- Extending detection coverage to `implement-epic.js` or `create-tickets.js` — scoped to
  `implement-ticket.js` only for this first pass.
- The two-sessions-independently-creating-a-brand-new-ticket-with-a-coincidentally-identical-ID
  scenario — an accepted, documented gap (see Known Limitations), not addressed by this design.
- Running the 30-day/quarter observation window itself, or making the eventual lock-vs-convention
  decision — that happens after this instrumentation has been live for the full period, not as part
  of shipping it.
- Widening the 900-second window or adding continuous sidecar-updating to close the false-negative
  gap — an accepted tradeoff, not a defect to silently patch.

## References

- `workflow_reliability_epic.md` (M2) — the source spec this experiment implements.
- `agent_evaluation_foundation_experiment.md` — structural template this document follows.
- `roadmap.md` (row 14) — inventory entry and Horizon-1 placement.
- `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` — the session-scoped sidecar mechanism this
  detection signal depends on.
- `TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP` — the directly analogous prior precedent
  for framing a mechanism explicitly as "detects, does not prevent," with its own accepted,
  documented coverage gap.
- `docs/agent-monitoring/schema.md` — new `claim_detections` section documenting this signal's
  record shape.
- `docs/parity_ledger/infrastructure.yaml` — parity ledger entry for this observable
  pipeline-behavior change.

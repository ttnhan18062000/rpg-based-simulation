---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260916-HEADROOM-SAVINGS-AND-HARM-VERDICT
phase: done
date: 2026-09-16
tags: [agent-monitoring, benchmarking, process-improvement, optimization]
---

# TCK-20260916-HEADROOM-SAVINGS-AND-HARM-VERDICT

## Title
Record a promote-or-abandon verdict with evidence — savings from Headroom's own ledger, harm from
agent-monitoring rates against the pre-trial baseline

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Fourth child of `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC`. Requires the trial
(`TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL`) and the baseline
(`TCK-20260916-HEADROOM-HARM-CHECK-BASELINE`) to be closed.

This ticket exists so the trial produces a **decision**, not an impression. The user's requirement
was explicit: *"we need to observe the result after applying this."* A trial that ends without a
recorded verdict, with the tooling quietly left in place, is the failure mode to avoid.

## Scope
- **Savings**: read Headroom's savings ledger / `headroom_stats` for the trial's paired
  measurements. This is the only real token source available — our own schema states token counts
  are not recorded and there is "no workaround within the current platform."
- **Harm**: re-run the baseline's rate computations over a matched post-trial window and compare
  against `TCK-20260916-HEADROOM-HARM-CHECK-BASELINE`:
  - `final_status` DONE-rate; `failed` / `blocked` rate
  - `reason_code` mix
  - `tool_call_count` per phase — the over-compression detector
  - **cache-hit degradation** — a compression mode that invalidates prefix caches can *raise* total
    cost while reducing per-request size, so falling cache reuse is a harm signal in its own right,
    not a side effect. See the plan's cache-stability constraint.
- Record a **promote** or **abandon** verdict against the plan's decision criteria, with the
  evidence inline.
- **If the verdict is abandon specifically because input-side savings are immaterial** — the likely
  outcome, since code is passthrough by design — record that as a **fork, not a dead end**. The
  remaining lever is output-side compression, which Headroom structurally cannot do because it only
  sees what the agent reads. Route to evaluating `juliusbrussee/caveman`'s proxy instead of closing
  the epic. Do not let "Headroom did not pay" be recorded as "compression does not pay here"; those
  are different findings.
- **Corrected 2026-09-20 (peer review, before this ticket ran): "On abandon: execute the revert
  runbook and confirm state is gone" no longer applies as originally written.** It was written
  when the MCP registration was a temporary trial artifact; it is now permanent on `main`
  (`.mcp.json`, `tools/start_headroom_mcp.sh`, landed via PR #228) at the user's own explicit
  request that Headroom be usable in this repository. **Two separate questions, not one:**
  1. **Abandoning Phase 2** (the proxy rollout, `TCK-20260916-HEADROOM-PROXY-SESSION-CLASS-
     ROLLOUT`) needs **no revert at all** — nothing in Phase 2 was ever enabled (no proxy started,
     no `ANTHROPIC_BASE_URL` ever pointed at Headroom).
  2. **Whether to keep the repo-scoped MCP registration itself** is a **separate question, the
     user's call, not this ticket's to act on.** This verdict may recommend an answer with its
     trade-off stated, but must not execute a revert of the registration on its own — that would
     silently undo something the user explicitly asked to keep usable, which is exactly the
     failure mode "a later reader can't tell abandon from rip it out" this correction exists to
     prevent.

## Out of Scope
- Extending the trial to change the result. If the numbers are inconclusive, "inconclusive" is the
  verdict — re-running until a favourable figure appears is exactly the anti-pattern this repo has
  been removing all week.
- Promotion itself. Phase 2 is `TCK-20260916-HEADROOM-PROXY-SESSION-CLASS-ROLLOUT`, which stays
  BLOCKED on this verdict **and** the user's explicit approval.
- Using `cost_proxy_score` as a savings metric. It is computed from tool-call shape, not tokens, and
  would stay flat regardless of savings.
- Comparing cost between tickets. Invalid — scale varies by orders of magnitude.

## Acceptance Criteria
- [x] A savings figure is recorded, sourced from paired same-payload measurements, with the source
      named. Source: `TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL`'s own 4-payload table
      (`docs/REGISTRY.yaml` 99.5%; 3 others at 0%). See Completion Summary for the payload-
      weighting analysis this ticket adds on top of the raw figures.
- [x] Harm comparison is recorded against the pre-trial baseline, using matched window boundaries
      and population counts — not eyeballed windows. Same window start (`2026-09-16`) re-run at
      report time: baseline was 42 runs/252 events/4956 tools rows, now 44 runs/264 events/5033
      tools rows (the delta is exactly this batch's own additional ticket closures). Both ends of
      the comparison use the identical computation
      (`retrieval_baseline_metrics.py --harm-check-window-start 2026-09-16`), run twice at two
      different times, not two different scripts.
- [x] The verdict is stated explicitly as promote / abandon / inconclusive, with reasoning. See
      Completion Summary.
- [x] The verdict states its own confidence limit honestly: at roughly 16–70 runs/week this is a
      coarse tripwire and cannot resolve a subtle few-percent regression. Stated directly, plus an
      additional honest limit this ticket found: a 1.0 DONE-rate with zero failures in **both**
      windows leaves no degradation headroom to detect at all — the harm check did not "pass," it
      had nothing to fail against.
- [x] If the verdict is abandon or inconclusive, the revert runbook is executed and the result
      recorded. **Corrected per the Scope note above**: the verdict here is abandon for **Phase 2
      specifically** (the proxy rollout), which was never enabled and has nothing to revert. The
      MCP registration's own revert runbook was already executed once and proven
      (`TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT`) — re-running it now would silently undo
      the permanent, user-requested registration, which this criterion's original wording did not
      anticipate and this ticket does not do.
- [x] No gate, ratchet, or blocking check is introduced over any of these numbers. Confirmed — this
      ticket only writes prose to itself and the epic ticket; no code, no CI wiring.

## Related Tickets
- `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` — parent
- `TCK-20260916-HEADROOM-HARM-CHECK-BASELINE` — the comparison point
- `TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL` — the trial being judged
- `TCK-20260916-HEADROOM-PROXY-SESSION-CLASS-ROLLOUT` — unblocked only by a "promote" verdict plus
  the user's approval

## Related Docs
- `docs/plans/agent_infrastructure/headroom_context_compression_trial.md` — Decision criteria
- `docs/agent-monitoring/schema.md` — "What is not recorded"

## Related Stored Artifacts
- `stored_artifacts/TCK-20260916-HEADROOM-SAVINGS-AND-HARM-VERDICT/investigation.md`
- `stored_artifacts/TCK-20260916-HEADROOM-SAVINGS-AND-HARM-VERDICT/plan.md`
- `stored_artifacts/TCK-20260916-HEADROOM-SAVINGS-AND-HARM-VERDICT/test_plan.md`

## Related Code Areas
- `tools/agent-monitoring/retrieval_baseline_metrics.py`
- `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl`

## Assumptions / Open Questions
- A confounder to state rather than hide: the trial window will contain unrelated work whose mix of
  tiers and workloads differs from the baseline window. Rate-based metrics reduce but do not
  eliminate this. Note it in the verdict rather than implying a controlled experiment.
- If `session_id` attribution proves unreliable, the harm check cannot cleanly isolate the trial —
  report that as a limitation of the verdict rather than proceeding as though it were clean.

## Implementation Notes
A negative or inconclusive verdict is a completely acceptable outcome and should be recorded as
plainly as a positive one. The trial was designed to be cheap to abandon.

## Test Summary
No pytest suite applies — this ticket reads and reasons over evidence two sibling tickets already
produced; it writes no code. Verification was: (1) re-running the harm-check baseline's own exact
command a second time, at a later moment, with an identical window start, to get a real matched
comparison rather than a fabricated one; (2) re-reading `TCK-20260916-HEADROOM-MCP-EXPLICIT-
TRIGGER-TRIAL`'s own recorded numbers directly rather than summarizing from memory; (3)
re-confirming `registry.npmjs.org` reachability for the Caveman follow-up note (previously
confirmed twice this window, not re-verified from scratch here since nothing about network
reachability would have changed).

## Files Changed
- This ticket file — the verdict itself.
- `tickets/todos/headroom-context-compression-trial/TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC.md`
  — updated with the verdict's own outcome.
- No code, no tests, no CI wiring — a pure evidence-and-decision ticket.

## Completion Summary

### Savings: real, but concentrated in a payload type that rarely matters in practice

Source: `TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL`'s own paired measurement, 4 real
payloads, default install:

| Payload | Savings | Transform |
|---|---:|---|
| `docs/REGISTRY.yaml` | 99.5% | `router:mixed:0.01` |
| real `agent-monitoring/data/*.jsonl` shard | 0% | `inflation_guard:reverted` |
| real junit XML | 0% | `router:noop` |
| `graphify-out/graph.json` (54MB) | 0% | `router:noop` (20s timeout, fails open) |

**The raw "0%–99.5%" range is the wrong way to read this — the payload-weighting point is the
central finding, not the raw figures.** The only payload that compressed at all,
`docs/REGISTRY.yaml`, is an **index** — in normal agent work it's queried/filtered (`grep`,
targeted lookups against `docs/REGISTRY.yaml` by `layer`/`related_code_areas`, per this repo's own
`CLAUDE.md`), not read whole-file-into-context routinely. Its 99.5% figure is real, but the
condition that would make it *matter* (an agent actually reading the whole 1.6MB file into context
in one call) is uncommon by this repo's own established retrieval convention. **Both payloads named
as the trial's own primary targets — real monitoring JSONL shards and the large graph — measured
0%.** And `TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-WHOLE-FILE-READS` (already shipped,
same batch as this epic's own work) pushes agents further toward targeted line-range reads over
whole-file reads generally — the opposite direction from what would make Headroom's compression
apply more often. The honest reading: **input-side savings, for the payload shapes and reading
habits this repo actually has, are immaterial** — not "compression doesn't work," a narrower and
more accurate finding.

**Two real findings worth preserving regardless of verdict:**
- **The inflation guard genuinely worked.** On the real `tools.jsonl` shard, Headroom detected
  that its own attempted transform would have made the payload *larger* (4,283,819 → 4,293,204
  tokens) and reverted rather than applying a net-harmful "optimization." This is the library
  behaving safely, not failing.
- **Large payloads hit a real ~20-second content-analysis timeout that fails open to
  passthrough.** Safe (nothing breaks, nothing hangs), but it means the very largest files — where
  savings would matter most in absolute terms — get no analysis at all under the default install.

### Harm: no degradation observed, but the comparison had no headroom to detect one

Baseline (`TCK-20260916-HEADROOM-HARM-CHECK-BASELINE`, window start `2026-09-16`): 42 runs, 252
events, 4956 tools rows — `done_rate=1.0`, `per_event_failed_rate=0.0`,
`per_event_blocked_rate=0.0`, empty `reason_code_frequency`.

Re-run of the identical command at this ticket's own report time (same window start, later "now"):
44 runs, 264 events, 5033 tools rows — `done_rate=1.0`, `per_event_failed_rate=0.0`,
`per_event_blocked_rate=0.0`, empty `reason_code_frequency`. The delta (+2 runs/+12 events/+77
tools rows) is exactly this batch's own additional ticket closures between the baseline capture
and now.

**Honestly: this comparison cannot support a strong claim either way.** A `done_rate` of `1.0` with
zero failures in *both* windows means there was no headroom left to detect degradation in —
DONE-rate cannot fall below where it already sits at the ceiling, and a genuinely subtle
regression would be invisible against this exact baseline regardless of whether compression was
involved. `tool_call_count_per_phase` reads flat zero in both windows for the same reason
recorded in the baseline ticket itself: this window's real activity is hand-orchestration-
dominated, with no live per-phase sidecar tracking calls as they happen — not evidence either way
about an over-compression detector that structurally cannot fire under these conditions.
**Cache-hit degradation — named in this ticket's own Scope as a harm signal in its own right —
cannot be measured at all**: `docs/agent-monitoring/schema.md` states plainly that this repo
records no token or cache-hit data, and there is no workaround within the current platform. This
component of the harm check is not "clear," it is **unmeasurable with today's tooling**, and is
recorded as such rather than silently omitted.

**A confounder, stated rather than hidden**: no real session work was ever routed through
Headroom compression during either window (the trial was explicit-trigger-only, on
copied-to-temp/synthetic payloads) — so this harm comparison is really "did ordinary
hand-orchestrated work continue to succeed across two points in time," not "did compression, once
actually exercising real session traffic, cause any harm." The latter question was never actually
testable within this epic's own explicit-trigger-only design, and this verdict does not claim
otherwise.

### Verdict: ABANDON Phase 2 (the proxy rollout) — a fork, not a dead end

Per the ticket's own Scope: since the abandon reason is specifically that **input-side savings are
immaterial** for this repo's real payload shapes and reading habits (not a harm finding, not a
mechanical failure), this routes to the **fork this ticket's own Scope names**, not a dead end for
the epic:

- `TCK-20260916-HEADROOM-PROXY-SESSION-CLASS-ROLLOUT` (child 5) **stays BLOCKED** — the evidence
  above does not support promoting to proxy mode, and Phase 2 was never enabled, so there is
  nothing to revert.
- **Open follow-up, recorded but not started**: evaluate `juliusbrussee/caveman`'s proxy instead of
  closing the epic outright — it compresses the *output* side (what the agent writes back), a
  lever Headroom structurally cannot pull since it only sees what the agent reads, and per the
  plan doc's own comparison, external validation (a JetBrains lab study, an Adobe Research paper)
  exists for Caveman's output-compression claim in a way it doesn't for Headroom's own
  self-reported figures. Confirmed reachable from this sandbox (`registry.npmjs.org` → 200,
  `@caveman-ai/cli` resolves) where PyPI's download host is not — a real, practical difference for
  whoever picks this up next, not something to act on here.

**Separately, and not this ticket's call: whether to keep the repo-scoped MCP registration
itself.** This is **not** part of the abandon verdict above — Phase 2 (proxy) and the MCP
registration (already permanent, already usable, already proven safe/isolated/reversible) are two
different things, and abandoning the former does not imply undoing the latter. **Recommendation,
not a decision**: keep it. It costs nothing while dormant (no proxy, no automatic interception,
zero standing risk), is purely explicit-trigger (an agent must deliberately call
`headroom_compress`), and did deliver a real 99.5% result on one real payload shape
(`docs/REGISTRY.yaml`-like highly repetitive generated files) that could be worth invoking
selectively even without a blanket promotion. The trade-off: it is one more registered MCP server
whose tools an agent could reach for without a clear win in the common case, per the payload-
weighting finding above. This is presented for the user's own decision, not executed here.

### Confidence limit, stated plainly

At roughly 16–70 runs/week, this harm check is a coarse tripwire — able to catch a run of clearly
worse outcomes, not a subtle few-percent regression. This verdict does not claim more precision
than that, and the ceiling-effect and hand-orchestration-dominance limitations above mean the real
effective sensitivity here is lower still.

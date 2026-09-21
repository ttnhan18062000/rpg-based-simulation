---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260916-HEADROOM-PROXY-SESSION-CLASS-ROLLOUT
phase: done
date: 2026-09-16
tags: [ai, process-improvement, optimization]
---

# TCK-20260916-HEADROOM-PROXY-SESSION-CLASS-ROLLOUT

## Title
Phase 2 — run Headroom in proxy mode for one data-heavy session class, on its own port and its own
isolated state

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Fifth child of `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC`, filed BLOCKED **by design** so that
a successful Phase 1 trial does not quietly become a default-on rollout without a decision.

Phase 1 (MCP, explicit trigger) is deliberately limited: it only compresses payloads the agent
chooses to hand it, so it can never deliver the automatic savings that motivated the evaluation.
Proxy mode is where real savings would come from — and where real risk lives, because Claude Code
can only set `ANTHROPIC_BASE_URL`, making compression **all-or-nothing for that session** with no
per-tool exclusion and no observe-only mode.

**Why it is blocked:** unblocking requires `TCK-20260916-HEADROOM-SAVINGS-AND-HARM-VERDICT` to
record a **promote** verdict *and* the user's explicit approval. Neither a green trial, nor CI
state, nor an agent's own judgement is sufficient. This mirrors
`TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING`, whose unblock condition is likewise a user judgement
rather than a measurable one.

## Scope
When unblocked:

- Run a dedicated proxy instance on its own port with its own `HEADROOM_WORKSPACE_DIR` /
  `HEADROOM_CONFIG_DIR`, so it cannot share state with concurrent sessions.
- Point **only** a named data-heavy session class at it — monitoring retro, corpus/JSONL analysis,
  graph work.
- Use **`--mode cache`**, not `--mode token`, unless measurement overturns it — see Assumptions for
  the evidence. Record `--code-aware`'s setting and the reasoning either way.
- Continue the harm check over the rollout window, comparing against the same baseline.
- Keep the revert runbook current and re-verify it still works against the proxy configuration.

## Out of Scope
- **Gate, CI, and review verification sessions — permanently, not merely for now.** The lossy
  compressors keep anomalies and drop normality, while verification evidence *is* the absence of
  anomaly. This exclusion is not revisited by a good Phase 1 result.
- `headroom learn` — still off; it auto-writes to `CLAUDE.md`.
- Making the proxy the default for all sessions, or setting it machine-wide.
- Any change to `CLAUDE.md`, `.claude/settings.json`, or agent definitions without the user's own
  separate authorization.

## Acceptance Criteria

**None checked. Closed 2026-09-21 as abandoned by decision, not delivered — see Completion
Summary.** Left unchecked deliberately rather than marked N/A, so a reader sees that nothing was
built rather than reading a closed ticket as done.

- [ ] Unblocked only by a recorded **promote** verdict plus the user's explicit approval, both cited.
      — **Not met, and cannot be met under the recorded verdict.**
      `TCK-20260916-HEADROOM-SAVINGS-AND-HARM-VERDICT` recorded **abandon**, not promote — this
      ticket's own unblock condition is therefore permanently unsatisfied unless a future session
      reopens the question with new evidence, which is out of this closure's scope.
- [ ] Exactly one named session class is routed through the proxy; every other session is unaffected,
      verified rather than assumed. — **Not attempted.** No proxy work began; unblocking never
      occurred.
- [ ] Proxy state is isolated, demonstrated by observed writes. — **Not attempted.**
- [ ] Harm metrics over the rollout window show no degradation against the baseline. — **Not
      attempted.** No rollout window exists.
- [ ] Revert has been re-verified against the proxy configuration, not only the MCP one. — **Not
      attempted.** Only the MCP-mode revert (`TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT`) was
      ever exercised.
- [ ] Claude subscription auth through the proxy is confirmed working, or the rollout is stopped —
      this is an open upstream question and a hard blocker. — **Left genuinely unresolved.** Moot
      under the abandon verdict; no longer a blocker for a ticket that will not proceed.

## Related Tickets
- `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` — parent
- `TCK-20260916-HEADROOM-SAVINGS-AND-HARM-VERDICT` — the verdict that can unblock this
- `TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT` — the isolation and revert basis
- `TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING` (BLOCKED) — same shape: a user-judgement unblock
  condition, deliberately not self-authorizable

## Related Docs
- `docs/plans/agent_infrastructure/headroom_context_compression_trial.md` — Phase 2

## Related Stored Artifacts
- `stored_artifacts/TCK-20260916-HEADROOM-PROXY-SESSION-CLASS-ROLLOUT/` — `investigation.md`,
  `plan.md`, `test_plan.md`, documenting why this closes without ever having had staging artifacts
  from active work (never unblocked, never picked up).

## Related Code Areas
- No repository source is expected to change; configuration is environmental
  (`ANTHROPIC_BASE_URL`, `HEADROOM_WORKSPACE_DIR`, `HEADROOM_CONFIG_DIR`)

## Assumptions / Open Questions
- **Unblock is a judgement call, not a measurable one.** Do not self-authorise it from a favourable
  Phase 1 number.
- Whether Claude subscription accounts work through the proxy is unresolved upstream and actively
  discussed. If it requires an API key this repo does not use, Phase 2 may be infeasible regardless
  of Phase 1's result — which is a legitimate outcome, not a problem to engineer around.
- **`--mode cache` is now the evidence-backed default** (changed 2026-09-17; previously recorded
  here as undecided). An external review of this account's usage measured ~48.8B cache-read against
  ~815.6M cache-write — roughly **60:1 reuse**, meaning prefix caching is already working extremely
  well. `--mode token` explicitly "maximizes visible per-request compression **at the cost of cache
  stability**", and cache reads bill at a fraction of fresh input, so trading cached tokens for
  compressed-but-uncached ones can cost *more* than it saves. A compression win measured per-request
  can still be a net loss. `--mode token` therefore needs positive evidence before use, not merely
  a better per-request number.

## Implementation Notes
Closed without implementation. No code, config, or environment change of any kind was made under
this ticket — its own scope was entirely gated on an unblock condition that was never met.

## Test Summary
_Not applicable — nothing was built._

## Files Changed
_None. This ticket's file itself moved from `tickets/todos/headroom-context-compression-trial/` to
`tickets/done/`._

## Completion Summary
Closed 2026-09-21, abandoned per `TCK-20260916-HEADROOM-SAVINGS-AND-HARM-VERDICT`'s recorded
**abandon** verdict on Phase 2. This ticket's own unblock condition — a **promote** verdict plus the
user's explicit approval — was not met and cannot be met under that verdict; leaving it open would
keep the epic in an indefinitely-pending state for a decision that has already been made. Not
implemented: no proxy instance was ever run, no session class was ever routed, no proxy-mode revert
was ever exercised. The user decided to close the epic (and this ticket with it) on 2026-09-21. This
is a closure by decision, not a delivery — see the unchecked Acceptance Criteria above for what was
never attempted and why.

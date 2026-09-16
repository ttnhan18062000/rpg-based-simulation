---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260916-HEADROOM-PROXY-SESSION-CLASS-ROLLOUT
phase: open
date: 2026-09-16
tags: [ai, process-improvement, optimization]
---

# TCK-20260916-HEADROOM-PROXY-SESSION-CLASS-ROLLOUT

## Title
Phase 2 — run Headroom in proxy mode for one data-heavy session class, on its own port and its own
isolated state

## Status
BLOCKED

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
- Choose and record `--mode` (`cache` versus `token`) with the reasoning, and whether `--code-aware`
  is enabled.
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
- [ ] Unblocked only by a recorded **promote** verdict plus the user's explicit approval, both cited.
- [ ] Exactly one named session class is routed through the proxy; every other session is unaffected,
      verified rather than assumed.
- [ ] Proxy state is isolated, demonstrated by observed writes.
- [ ] Harm metrics over the rollout window show no degradation against the baseline.
- [ ] Revert has been re-verified against the proxy configuration, not only the MCP one.
- [ ] Claude subscription auth through the proxy is confirmed working, or the rollout is stopped —
      this is an open upstream question and a hard blocker.

## Related Tickets
- `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` — parent
- `TCK-20260916-HEADROOM-SAVINGS-AND-HARM-VERDICT` — the verdict that can unblock this
- `TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT` — the isolation and revert basis
- `TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING` (BLOCKED) — same shape: a user-judgement unblock
  condition, deliberately not self-authorizable

## Related Docs
- `docs/plans/agent_infrastructure/headroom_context_compression_trial.md` — Phase 2

## Related Stored Artifacts
- None yet.

## Related Code Areas
- No repository source is expected to change; configuration is environmental
  (`ANTHROPIC_BASE_URL`, `HEADROOM_WORKSPACE_DIR`, `HEADROOM_CONFIG_DIR`)

## Assumptions / Open Questions
- **Unblock is a judgement call, not a measurable one.** Do not self-authorise it from a favourable
  Phase 1 number.
- Whether Claude subscription accounts work through the proxy is unresolved upstream and actively
  discussed. If it requires an API key this repo does not use, Phase 2 may be infeasible regardless
  of Phase 1's result — which is a legitimate outcome, not a problem to engineer around.
- Whether `--mode cache` (prefix-cache stability) or `--mode token` (maximum visible compression) is
  the better fit is genuinely undecided and should be measured, not assumed.

## Implementation Notes
Blocked. Do not pick this up without both the promote verdict and the user explicitly saying to
proceed.

## Test Summary
_Blocked._

## Files Changed
_Blocked._

## Completion Summary
_Blocked._

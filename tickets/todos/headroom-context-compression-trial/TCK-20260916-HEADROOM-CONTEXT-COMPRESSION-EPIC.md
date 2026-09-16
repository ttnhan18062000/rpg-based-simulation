---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC
phase: open
date: 2026-09-16
tags: [ai, agent-monitoring, process-improvement, optimization]
---

# TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC

## Title
Bounded, reversible trial of Headroom context compression — measure real token savings, prove no
correctness regression, and gain the repo's first real token telemetry

## Status
OPEN

## Tier
epic

## Type
chore

## Priority
P2

## Request Summary
Requested by the user 2026-09-16 after reviewing
[headroomlabs-ai/headroom](https://github.com/headroomlabs-ai/headroom): *"go with B [MCP-triggered
first] but make sure we can revert the change if observe the result is not good enough, also, we
need to observe the result after applying this, like using agent monitoring records or something."*

Full reasoning, evidence, and decision criteria: `docs/plans/agent_infrastructure/headroom_context_compression_trial.md`.

**Two motivations, and the second is the stronger one.**

1. Token cost reduction, consistent with the user's standing preference for token efficiency over
   speed.
2. **Token *measurability*.** `docs/agent-monitoring/schema.md`'s "What is not recorded" states that
   token counts are "consumed internally by the Claude Code runtime and not forwarded to the
   workflow script. There is no field for it and no workaround within the current platform."
   `retrieval_baseline_metrics.py::build_context_tokens_section()` returns `"unavailable"` for this
   reason. Headroom sits in the API path and therefore sees real token counts — adopting it would
   produce the first real token telemetry this repo has ever had.

**The constraint that shapes the whole epic:** Claude Code can only set `ANTHROPIC_BASE_URL` — no
headers, no per-request parameters. `headroom_mode="audit"` and per-tool `skip_compression` are
SDK-only; `headroom proxy --mode` accepts only `cache` and `token`, with **no proxy-level audit
mode**. So proxy mode is all-or-nothing per session, and an "observe first" rollout is unavailable
by that route. MCP mode (explicit `headroom_compress` invocation) is therefore the only way to get a
measured, zero-exposure trial — a correctness requirement, not caution.

## Scope
- A reversible, opt-in trial of Headroom in **MCP mode** (explicit trigger) on JSON/log-shaped
  payloads, with isolation from concurrent sessions and a proven revert path.
- Measurement of real savings via Headroom's own ledger/`headroom_stats` (a paired,
  scale-invariant measurement), and of *harm* via agent-monitoring rates.
- A recorded promote/abandon decision against the criteria in the plan.

## Out of Scope
- **Making compression a default, or wrapping any session automatically.** Phase 2 (proxy for one
  session class) is a separate child, BLOCKED on this epic's evidence plus the user's approval.
- **`headroom learn`.** It auto-writes to `CLAUDE.md`, which requires the user's direct
  authorization by repeated precedent in this repo. Stays off for the entire trial.
- **Compression anywhere near gate/CI/review verification work.** The lossy compressors keep
  anomalies and drop normality, while verification evidence *is* the absence of anomaly
  (`273 passed, 0 failed`; an empty `uniq -d`; an identical `diff`). Scope boundary, not preference.
- Building our own compression. Not proposed, not in scope.
- The context-packet work in
  `context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`. That
  plan decides *what to retrieve*; this compresses *what was already retrieved*. Complementary,
  neither supersedes the other.
- Any new mandatory workflow gate or monitoring-writer change — the same boundary that plan sets.

## Acceptance Criteria
- [ ] All child tickets are closed, or explicitly abandoned with the reason recorded.
- [ ] A measured savings figure exists for real repo payloads, from a paired measurement — never a
      cross-ticket cost comparison, which is invalid given ticket-scale variance.
- [ ] A harm check over the trial window shows no degradation in DONE-rate, failure/blocked rate,
      `reason_code` mix, or `tool_call_count`-per-phase.
- [ ] The revert runbook has been **executed at least once**, not merely written.
- [ ] A promote/abandon decision is recorded against the plan's decision criteria, with evidence.
- [ ] `CLAUDE.md` is unmodified by this epic unless the user separately and directly authorizes it.

## Related Tickets
- `TCK-20260708-AGENT-COST-OBSERVABILITY` (done) — established that real token data is
  platform-blocked; the reason `cost_proxy_score` is a proxy
- `TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT` (done) — precedent for read-time-only derived metrics
  that never mutate the source JSONL
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (done) — prior epic in this area; its ratchet
  discipline and measured-baseline conventions apply here

## Related Docs
- `docs/plans/agent_infrastructure/headroom_context_compression_trial.md` — this epic's plan
- `docs/agent-monitoring/schema.md` — "What is not recorded" (token unavailability authority)
- `docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`
- `docs/plans/archive/agent_infrastructure/idea_agent_cost_observability.md` (archived)

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `tools/agent-monitoring/retrieval_baseline_metrics.py` (`build_context_tokens_section`, currently
  returning `"unavailable"` — the natural landing place for real token data)
- `tools/agent-monitoring/generate_retro.py`
- `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl`
- `.mcp.json` (MCP server registration for the trial)

## Assumptions / Open Questions
- **Headroom state is machine-wide, not per-session.** `~/.headroom` (`HEADROOM_WORKSPACE_DIR`),
  `~/.headroom/config` (`HEADROOM_CONFIG_DIR`), plus savings-ledger and TOIN paths are per-user, and
  config "applies globally to the proxy instance or SDK client." With several concurrent sessions
  across worktrees this is structurally the same hazard as the confirmed `.claude/current_run`
  sidecar contamination — isolation must be explicit.
- Whether `ccr_store.db` / `HEADROOM_CCR_BACKEND=memory` exist as described is **unconfirmed** —
  found only in third-party search summaries, absent from authoritative pages. Verify from source or
  `--help` before relying on either.
- Whether MCP mode shares `~/.headroom` with proxy mode, or is independently isolatable.
- Whether Claude subscription auth works through the proxy — open upstream, a hard blocker for
  Phase 2 if unresolved.
- The 20% coding-agent savings figure is **not** expected to apply here: code is passthrough by
  design ("Compressing function bodies would remove exactly what they need"). Expect savings
  concentrated in JSON/JSONL.

## Implementation Notes
Do not install, enable, or point any session at Headroom before
`TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT` lands — isolation and a proven revert path come
first, because Headroom's state is machine-wide and would otherwise affect every concurrent session.

Verify claims from source or `--help` rather than from documentation or from this ticket; several
details in the upstream docs are absent or contradicted between pages, and at least two claims here
are explicitly marked unconfirmed.

## Test Summary
_Epic tier — no direct implementation. See child tickets._

## Files Changed
_Epic tier — no direct implementation._

## Completion Summary
_Open._

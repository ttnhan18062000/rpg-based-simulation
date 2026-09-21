# Sequence — Headroom context-compression trial

Epic: `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` — **DONE, closed 2026-09-21.**
Plan: `docs/plans/agent_infrastructure/headroom_context_compression_trial.md` — concluded, see its
own status block.

**Outcome: Phase 1 delivered, Phase 2 abandoned on measured evidence.** All 5 children are closed —
4 delivered evidence, the 5th (`TCK-20260916-HEADROOM-PROXY-SESSION-CLASS-ROLLOUT`, Phase 2) closed
abandoned-by-decision, its own unblock condition unmeetable under the recorded abandon verdict. The
MCP registration stays on `main`; see the epic's own Completion Summary for the full outcome.

Unlike the monitoring-anomaly epic, **this sequence is a real dependency chain, not a leverage
ordering**. Ticket 1 gates everything: Headroom's state is machine-wide (`~/.headroom`), so
installing or enabling it before isolation and a proven revert path exist would affect every
concurrent session on this machine at once.

| # | Ticket | Why this order |
|---|---|---|
| 1 | `TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT` | **Blocks all others.** Establishes per-session `HEADROOM_WORKSPACE_DIR`/`HEADROOM_CONFIG_DIR` isolation and a revert runbook that is *executed*, not just written. Machine-wide state is the same hazard shape as the confirmed `.claude/current_run` sidecar contamination. |
| 2 | `TCK-20260916-HEADROOM-HARM-CHECK-BASELINE` | Capture the **pre-trial** baseline before anything is enabled. A baseline measured after the change is worthless, and this epic cannot reuse an old one — the corpus moved substantially this week. |
| 3 | `TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL` | The trial itself: MCP mode only, explicit `headroom_compress` on JSON/JSONL payloads. Depends on 1 for safety and 2 for a comparison point. |
| 4 | `TCK-20260916-HEADROOM-SAVINGS-AND-HARM-VERDICT` | Reads the savings ledger and re-runs the harm check against ticket 2's baseline, then records a promote/abandon decision with evidence. |
| 5 | `TCK-20260916-HEADROOM-PROXY-SESSION-CLASS-ROLLOUT` | **BLOCKED by design.** Phase 2. Unblocks only on ticket 4 recording "promote" *and* the user's explicit approval — never on CI state, a green trial, or an agent's own judgement. |

## Measurement discipline

Two instruments measuring two different things. Do not substitute one for the other.

- **Savings → Headroom's own ledger / `headroom_stats`.** The only real token source: our schema
  states token counts are "consumed internally by the Claude Code runtime … no workaround within the
  current platform." It is a *paired* measurement (same payload, compressed vs not), so ticket-scale
  variance cancels.
- **Harm → agent-monitoring, as a tripwire.** `cost_proxy_score` is computed from tool-call shape,
  not tokens — it would stay flat regardless of savings. Using it to measure savings measures the
  wrong thing.

**Never compare cost between two tickets.** A hotfix and a 95-file epic differ by orders of
magnitude; that variance dwarfs a 20% effect. Every savings claim must be paired on identical input.

**The over-compression detector**: `tool_call_count` per phase. If compression drops something the
agent needed, the agent calls `headroom_retrieve` to recover it — which shows up as extra tool
calls. This is the axis agent-monitoring measures well, and the one most likely to catch real harm.

**Honest limit:** at roughly 16–70 runs/week this is a coarse tripwire, not a statistical result. It
catches "noticeably worse"; it will not resolve a subtle few-percent regression. No promotion
decision may claim otherwise.

## Hard boundaries for every child

Adopted from the governing principle in
`context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`:

> A context-budget reduction is successful only when correctness signals hold or improve.

1. **No compression in gate/CI/review verification work.** The lossy compressors keep anomalies and
   drop normality (`LogCompressor` "keeps failures, errors, warnings. Drops passing noise";
   `DiffCompressor` drops unchanged context), while verification evidence *is* the absence of
   anomaly. Scope boundary, not preference.
2. **`headroom learn` stays off** for the whole trial — it auto-writes to `CLAUDE.md`, which
   requires the user's direct authorization.
3. **No default-on anything.** Every child is opt-in and reversible.
4. **Verify upstream claims from source or `--help`**, not from docs and not from these tickets.
   The CCR page documents behaviour but no storage paths; `ccr_store.db` and
   `HEADROOM_CCR_BACKEND=memory` appear only in third-party summaries and are explicitly unconfirmed.

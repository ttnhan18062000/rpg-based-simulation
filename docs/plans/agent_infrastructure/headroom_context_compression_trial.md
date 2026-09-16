---
status: active
layer: ai
authority: P2
audience: developer
maturity: proposed-bounded-trial
date: 2026-09-16
tags: [ai, workflows, agent-monitoring, process-improvement, optimization]
---

# Plan: Headroom Context-Compression Bounded Trial

> **Maturity: PROPOSED BOUNDED TRIAL.** This authorizes a reversible, opt-in evaluation of a
> third-party compression layer and the measurement needed to judge it. It does **not** authorize
> making compression a default, wrapping any session by default, enabling `headroom learn`, or
> putting compression in the path of gate/CI verification work. Promotion beyond the trial
> requires recorded evidence and the user's explicit approval.

## Problem

Agent token cost is a standing concern for this repo, and the user's own standing preference is
token efficiency over speed (accepting materially slower work for materially fewer tokens). But
this repo currently has **no way to measure token use at all**.

`docs/agent-monitoring/schema.md`'s "What is not recorded" section states it plainly:

> **Token counts** are not recorded. The workflow `agent()` call returns the agent's structured
> output only; API usage metadata (`input_tokens`, `output_tokens`) is consumed internally by the
> Claude Code runtime and is not forwarded to the workflow script. There is no field for it and
> no workaround within the current platform.

`tools/agent-monitoring/retrieval_baseline_metrics.py::build_context_tokens_section()` encodes the
same conclusion as a runtime value, returning `{"status": "unavailable", ...}`. This is why
`cost_proxy_score` exists as a *proxy* at all (`TCK-20260708-AGENT-COST-OBSERVABILITY`, whose
originating plan now sits in `docs/plans/archive/agent_infrastructure/idea_agent_cost_observability.md`).

So the problem is two problems, and the second is the more interesting one:

1. Token spend is high and unoptimized.
2. **Token spend is unmeasurable**, which means any optimization claim — including this one —
   cannot currently be verified from our own data.

## Candidate

[Headroom](https://github.com/headroomlabs-ai/headroom) (Apache-2.0, Python, ~72k stars, actively
maintained as of 2026-09-16) compresses what an agent *reads* — tool outputs, logs, JSON, diffs,
search results — before it reaches the model. Claimed: 20% fewer tokens for coding agents, 60–95%
for JSON.

**The non-obvious benefit.** Headroom sits in the API path as a proxy, so it observes real token
counts. Adopting it — even in a limited mode — would produce the **first real token telemetry this
repo has ever had**, closing a gap our own schema documents as having "no workaround within the
current platform." That capability is arguably worth more than the cost saving, and it is the
reason this trial is worth running even if the savings turn out to be modest.

## Why this is not a duplicate of context-efficient retrieval

`context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`
(maturity: proposed-future-epic) addresses a different layer and is **not** superseded by this:

| | That plan | This trial |
|---|---|---|
| Mechanism | Builds a bounded, cited `ContextPacket` — decides *what to retrieve* | Compresses payloads already being read — shrinks *what was retrieved* |
| Ownership | Ours, built in-repo | Third-party dependency |
| Status | Sequenced after provider-agnostic orchestration | Independently runnable now |

They are complementary. That plan explicitly withholds authorization for "a new mandatory workflow
gate, a production monitoring writer change, or a new external retrieval service" — this trial
respects the same boundary and adds none of those.

**Its governing principle is adopted here verbatim**, because it is exactly right for this work:

> The dashboard must not reward smaller packets by themselves. A context-budget reduction is
> successful only when correctness signals hold or improve.

## The integration constraint that shapes everything

Claude Code can only set `ANTHROPIC_BASE_URL`. It cannot pass request headers or per-request
parameters. Therefore:

- `headroom_mode="audit"` and per-tool `skip_compression` profiles are **SDK-only** and
  unreachable from Claude Code.
- `headroom proxy --mode` accepts only `cache` and `token` — **there is no proxy-level audit or
  observe-only mode**.
- `x-headroom-bypass` applies only to the `/v1/compress` endpoint, not `/v1/messages`.

So proxy mode is **all-or-nothing per session**, fixed at proxy startup. An "observe first, commit
later" rollout is therefore *not available* via the proxy path — which is what makes MCP mode the
correct first step rather than merely the cautious one.

## Approach: MCP-triggered first, proxy-per-session-class only on evidence

**Phase 1 — explicit trigger (MCP).** Headroom exposes `headroom_compress`, `headroom_retrieve`,
and `headroom_stats` as MCP tools. Nothing is intercepted; compression happens only when
deliberately invoked on a chosen payload. This gives a real measured number with zero exposure for
work where lossy compression is dangerous.

Target payloads — the JSON/log-shaped content where 60–95% actually applies:

- `agent-monitoring/data/**/*.jsonl` shards during retro and corpus analysis
- `graphify-out/graph.json` (~50MB, local-only)
- `docs/REGISTRY.yaml`, junit XML under `reports/junit/`

**Phase 2 — proxy for one session class,** only if Phase 1's numbers justify it: its own port, its
own `HEADROOM_WORKSPACE_DIR`/`HEADROOM_CONFIG_DIR`, restricted to data-heavy sessions.

## Where compression must not go

The lossy compressors keep anomalies and drop normality: `LogCompressor` "keeps failures, errors,
warnings. Drops passing noise"; `DiffCompressor` drops unchanged context; `SearchCompressor`
rank-filters to top matches; `SmartCrusher` drops non-anomalous JSON rows.

That is precisely inverted for verification work, where the evidence **is** the absence of anomaly:
`273 passed, 0 failed`; a `uniq -d` returning empty; a `diff` reporting identical; an empty
protected-ratchet diff. Gate, CI, and review sessions must stay out of the compression path for the
duration of this trial. This is a scope boundary, not a preference.

`headroom learn` stays **off**: it auto-writes to `CLAUDE.md`, which requires the user's direct
authorization per repeated precedent in this repo.

## Isolation and reversibility

Headroom state is **per-user and machine-wide**, not per-session or per-worktree:

| State | Location | Scope |
|---|---|---|
| Workspace / read-write state | `~/.headroom` (`HEADROOM_WORKSPACE_DIR`) | Per-user, machine-wide |
| Config | `~/.headroom/config` (`HEADROOM_CONFIG_DIR`) | Per-user, machine-wide |
| Savings ledger | `HEADROOM_SAVINGS_PATH` | Per-user |
| Learned TOIN patterns | `HEADROOM_TOIN_PATH` | Per-user |

Config "applies globally to the proxy instance or SDK client — not per-user, per-project, or
per-directory." With several concurrent sessions across worktrees, one shared store and one shared
learned-pattern set is structurally the same hazard as the confirmed `.claude/current_run` sidecar
contamination, which misattributed monitoring data for two days. Isolation must therefore be
explicit, not assumed.

Revert is clean and total: stop pointing at the proxy / remove the MCP server, then
`rm -rf ~/.headroom/`. Nothing is written into the repository.

## Measurement

Two instruments, deliberately measuring different things.

**Savings — Headroom's own ledger / `headroom_stats`.** This is the only real token source
available (see Problem). It is a *paired* measurement: the same payload, compressed versus not, so
differences in ticket scale cancel by construction. This matters because **cross-ticket cost
comparison is invalid** — a hotfix and a 95-file epic differ by orders of magnitude, and that
variance dwarfs a 20% effect.

**Harm — agent-monitoring, as a tripwire, not a cost metric.** `cost_proxy_score` is computed from
tool-call shape, not tokens, so it would stay flat regardless of savings; using it to measure
savings would measure the wrong thing entirely. Its real value is detecting degradation, via
scale-invariant rates:

| Signal | Source | Why |
|---|---|---|
| `final_status` DONE-rate; per-event `failed`/`blocked` rate | `runs.jsonl`, `events.jsonl` | Direct quality regression |
| `reason_code` frequency | `events.jsonl` | Shifts in *why* things fail |
| **`tool_call_count` per phase** | `events.jsonl` + `tools.jsonl` | **Over-compression detector**: if compression drops something needed, the agent calls `headroom_retrieve` to recover it, inflating tool calls per phase |
| `session_id` filtering | `tools.jsonl` | Isolates trial-session rows from concurrent sessions |

**Honest limit:** at roughly 16–70 runs/week this is a coarse tripwire, not a statistical result.
It will catch "noticeably worse." It will not resolve a subtle few-percent quality regression, and
no promotion decision should claim otherwise.

## Decision criteria

Promote to Phase 2 only if all hold:

1. Measured savings on real payloads are material (target: ≥30% on JSON/JSONL; the 20% coding-agent
   figure is *not* expected here, since code is passthrough by design).
2. No degradation in DONE-rate, failure rate, or `reason_code` mix over the trial window.
3. No unexplained `tool_call_count`-per-phase inflation.
4. The isolation and revert runbook has been executed successfully at least once.

Abandon — and revert — if savings are immaterial, any correctness signal degrades, or isolation
proves unreliable across concurrent sessions.

## Open questions

- Whether `ccr_store.db` / `HEADROOM_CCR_BACKEND=memory` exist as documented. These appeared only in
  third-party search summaries and **could not be confirmed** on any authoritative page; the CCR
  documentation describes behaviour but no storage paths, TTL, or purge command. Confirm from source
  or `--help` before relying on either.
- Whether MCP mode shares `~/.headroom` state with proxy mode, or is independently isolatable.
- Whether Claude *subscription* auth works through the proxy — an open, actively-discussed upstream
  integration question, and a hard blocker for Phase 2 if unresolved.

## Related

- `docs/agent-monitoring/schema.md` — "What is not recorded"; the token-unavailability authority
- `tools/agent-monitoring/retrieval_baseline_metrics.py` — existing baseline harness;
  `build_context_tokens_section()` is the natural place for real token data to land
- `docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`
- `docs/plans/archive/agent_infrastructure/idea_agent_cost_observability.md` (archived) and
  `TCK-20260708-AGENT-COST-OBSERVABILITY`

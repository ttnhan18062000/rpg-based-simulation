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
- [ ] All child tickets are closed, or explicitly abandoned with the reason recorded. **4 of 5
      closed** (isolation-and-revert, harm-check-baseline, MCP-explicit-trigger-trial, savings-
      and-harm-verdict). Remaining: `TCK-20260916-HEADROOM-PROXY-SESSION-CLASS-ROLLOUT` (child 5),
      which **stays `BLOCKED` by design** — its own unblock condition (a "promote" verdict plus
      the user's explicit approval) was not met, so it is neither closed nor further actioned, per
      its own already-correct wording.
- [x] A measured savings figure exists for real repo payloads, from a paired measurement — never a
      cross-ticket cost comparison, which is invalid given ticket-scale variance.
      `TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL`: 4 real payloads, paired on identical
      input — `docs/REGISTRY.yaml` 99.5%, 3 others at 0% (each with a different diagnosed real
      cause, not a repeated failure). Recorded exactly as measured.
- [x] A harm check over the trial window shows no degradation in DONE-rate, failure/blocked rate,
      `reason_code` mix, or `tool_call_count`-per-phase.
      `TCK-20260916-HEADROOM-SAVINGS-AND-HARM-VERDICT`: re-ran the baseline's exact command at a
      later moment (same window start) — no degradation observed, but stated honestly that the
      comparison had a ceiling effect (baseline was already `done_rate=1.0`/zero failures) and
      could not test real compressed-traffic harm at all, since the trial was explicit-trigger-
      only throughout.
- [x] The revert runbook has been **executed at least once**, not merely written.
      `TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT`: two paired git commits with exactly
      symmetric diffs, plus a real package uninstall.
- [x] A promote/abandon decision is recorded against the plan's decision criteria, with evidence.
      **Verdict: abandon Phase 2** (the proxy rollout) — input-side savings are immaterial for
      this repo's real payload shapes and reading habits (the one payload that compressed is an
      index this repo's own conventions already push agents to query rather than read whole; both
      named primary targets measured 0%). Per the ticket's own fork clause, routed to an open
      follow-up (evaluate Caveman's output-side proxy) rather than a dead end. **The MCP
      registration itself is a separate question, not decided by this abandon verdict** —
      recommended to keep (costs nothing dormant, explicit-trigger only, did deliver a real result
      on one payload shape), but left as the user's own call, not executed here.
- [x] `CLAUDE.md` is unmodified by this epic unless the user separately and directly authorizes it.
      Confirmed throughout — no child ticket in this epic has touched `CLAUDE.md`.

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
  sidecar contamination — isolation must be explicit. **Source-verified 2026-09-20**: every state
  path in `headroom/paths.py` derives from these two env-overridable roots — isolation is
  achievable in principle, from a 2-of-~26-file spot check, not an exhaustive audit.
- ~~Whether `ccr_store.db` / `HEADROOM_CCR_BACKEND=memory` exist as described~~ — **resolved
  2026-09-20 from source**: both real. See the plan doc's Open Questions section for the exact
  citation.
- ~~Whether MCP mode shares `~/.headroom` with proxy mode, or is independently isolatable~~ —
  **resolved 2026-09-20 from source**: shared, not independent (`mcp_server.py` calls the same
  `get_compression_store()` the proxy uses). See the plan doc for detail.
- Whether Claude subscription auth works through the proxy — open upstream, a hard blocker for
  Phase 2 if unresolved.
- The 20% coding-agent savings figure is **not** expected to apply here: code is passthrough by
  design ("Compressing function bodies would remove exactly what they need"). Expect savings
  concentrated in JSON/JSONL.
- **New (2026-09-20): `HEADROOM_STATELESS`** — a real, separate no-workspace-writes mechanism found
  in source, not previously known to this epic. See the plan doc.
- **New (2026-09-20): `headroom wrap` installs Serena into `~/.claude.json` at user scope** — a
  real risk for any future `wrap`-based phase, same hazard shape as the sidecar contamination
  precedent. Not relevant to the current MCP-mode-only Phase 1 scope. See the plan doc.

## Implementation Notes
Do not install, enable, or point any session at Headroom before
`TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT` lands — isolation and a proven revert path come
first, because Headroom's state is machine-wide and would otherwise affect every concurrent session.

Verify claims from source or `--help` rather than from documentation or from this ticket; several
details in the upstream docs are absent or contradicted between pages, and at least two claims here
are explicitly marked unconfirmed.

**Epic-wide blocker — resolved (2026-09-20), with two honest caveats, not simply "fixed."**
`TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT` found that `files.pythonhosted.org` (the
package-download CDN, not the `pypi.org` index) is unreachable from this account's Claude Code
sandbox specifically — confirmed general via an unrelated trivial package, not Headroom-specific.
The user's own shell is not behind the same block and ran the install directly
(`.venv/bin/python3 -m pip install headroom-ai`) twice: once during that ticket's own work
(later uninstalled again as part of proving the revert), and again afterward, which is the install
still present in `.venv` today (`headroom-ai==0.37.0`, confirmed importable and runnable, and
functionally exercised via a real MCP client smoke test in `TCK-20260916-HEADROOM-MCP-EXPLICIT-
TRIGGER-TRIAL`).

- **Caveat (a): the second install resolved entirely from pip's local cache** ("Using cached" on
  every wheel) — it did not re-prove network access to the blocked host. If that cache is ever
  cleared, the same `files.pythonhosted.org` block would need to be worked around again (i.e., the
  user's shell again, not this sandbox), not assumed fixed.
- **Caveat (b): the install is machine-level state, not a repository artifact.** Nothing about
  it is checked into git or reproducible by cloning this repo elsewhere — any future session on a
  *different* machine, or this same machine after the venv is rebuilt, depends on that install
  still being present, exactly like caveat (a).

Not deleting this blocker's own original history — it's the reason
`TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT` closed the way it did (safety envelope proven
via `git merge-tree`-free source-reading and a hermetic clean-clone repro, not via installing
anything in this sandbox). **Registration itself** (the `.mcp.json` entry, the launcher) **is a
version-controlled file change and can be re-applied by an agent session directly** — only the
`pip install` step needs the user, and only when the cache/machine-state caveats above don't
already cover it.

## Test Summary
_Epic tier — no direct implementation. See child tickets._

## Files Changed
_Epic tier — no direct implementation._

## Completion Summary
_Open._

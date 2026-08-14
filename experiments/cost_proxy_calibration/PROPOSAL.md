# Proposal: Calibrate `cost_proxy_score` Against Real Local Token-Usage Data

**Status:** proposed, not built
**Location:** `experiments/cost_proxy_calibration/` (lightweight sandbox — exempt from the ticket/staging-artifact workflow per project convention; only a validated calibration ever graduates into a real ticket)
**Date:** 2026-07-17

---

## 1. Origin

Traced to its actual source, not invented fresh: `docs/agent-monitoring/README.md`'s "What It Does NOT
Capture" section and `tools/agent-monitoring/cost_proxy.py`'s own module docstring both state real
token/cost telemetry is "platform-blocked" — the workflow `agent()` call never receives
`input_tokens`/`output_tokens` from the runtime. `TCK-20260708-AGENT-COST-OBSERVABILITY` shipped a
Tier 1 proxy (`cost_proxy_score`) instead, explicitly scoping real telemetry out as a future Tier 3,
"no action possible until Anthropic forwards usage data" (per `TCK-20260708-AGENT-INFRA-HARDENING-EPIC`).

This session's own conversation surfaced the question again while discussing the state of this
project's AI-agent tooling more broadly (see `docs/ai/agent_infrastructure_audit.md`,
`docs/ai/system_overview.md`). Rather than accept "platform-blocked" as closed without checking, this
proposal exists because that check had never actually been run against what's available *on this
machine*, only against what the `agent()` runtime API forwards.

## 2. What this session verified directly — a decisive negative, and an unexpected positive

**Negative, confirmed not assumed:** `agent()` (and `bash()`, `phase()`) are functions injected into
`.claude/workflows/*.js` by the Claude Code harness itself — they are not repo-side wrappers around a
raw SDK/API call (grepped every workflow file; none defines or imports `agent`). The harness is closed,
external to this repository. There is no local artifact anywhere under `~/.claude/` that records
per-subagent usage keyed to a workflow phase/agent identity:

- `~/.claude/telemetry/*.json` — exists, but is a stale (2026-07-02, not appended since) queue of
  *failed analytics events* (`tengu_bash_command_timeout_backgrounded`, etc.) — zero token/usage fields
  of any kind, confirmed by direct field-name grep across every record.
- `~/.claude/sessions/*.json` — process metadata only (`pid`, `cwd`, `status`) — no usage data.
- `~/.claude/projects/-home-u24desktop-Working-rpg-based-simulation/*.jsonl` (21 files, 171MB) — the
  local session transcripts. Every record with a real `usage` block (`input_tokens`, `output_tokens`,
  `cache_creation_input_tokens`, `cache_read_input_tokens`) belongs to the **main interactive session**
  turn-by-turn. Checked specifically for a link between `usage` and any subagent-identifying field
  (`agentName`, `isSidechain`, `sourceToolUseID`) in the same record — **zero co-occurrences found**.
  `isSidechain` is `false` on every one of ~thousands of records in this project's transcripts; the 469
  `"name":"Task"`-adjacent `"name":"Agent"` tool-use hits mark where a subagent was *spawned* from the
  main transcript, but the spawned subagent's own turns and their token cost are not present in these
  files at all. `agentName`-tagged records (360 found) turned out to be background-task naming labels
  (`"Implement_simq"`, `"experiment-rendering"`), not the ticket pipeline's own agent identities
  (`ticket-scoper`, `implementer`, etc.), and carry no `usage` field regardless.

**This confirms, with direct evidence rather than inherited assumption, that real per-subagent token
telemetry is not recoverable from any local artifact on this machine.** The existing "platform-blocked"
conclusion was correct — this closes the open question definitively rather than leaving it as an
unverified inherited claim, and means nobody needs to re-open this specific question again.

**The unexpected positive:** the main session's own transcripts *do* contain real, accurate
`input_tokens`/`output_tokens`/cache-token data, per turn, for the orchestrating conversation itself —
21 files, spanning real work on this exact project. `cost_proxy_score`'s own module docstring
(`tools/agent-monitoring/cost_proxy.py:8-10`) states its weights (`W_BASH=0.001`, `W_AGENT=50`,
`W_EDIT=1`) were "sized from the real aggregate distribution of `agent-monitoring/tools.jsonl` (543
sampled event-groups)" — i.e., calibrated against **tool-call volume**, never against any real cost
ground truth, because none was thought to be available. That premise is now falsifiable: real cost
ground truth exists locally for at least one execution context (the main session), even though it
doesn't exist for the subagent context the proxy is actually scoring.

## 3. What this does NOT solve — stated plainly, not glossed over

- **Does not recover real per-subagent token costs.** That remains genuinely platform-blocked, per §2's
  negative result. This proposal does not contradict or reopen that finding.
- **Generalizing main-session token/tool-call ratios to subagent calls is an assumption, not a proven
  transfer.** The main session accumulates large `cache_read_input_tokens` (19k-38k+ observed) from
  long-running conversation context; a freshly spawned subagent (e.g. `ticket-scoper`, `implementer`)
  starts with a narrower, task-scoped context and a different cache profile. A regression fit on
  main-session data risks systematically over- or under-estimating subagent cost if applied naively.
  This is the central open risk the validation step (§5) exists to test, not assume away.
- **Does not produce a real dollar figure with confidence**, only a better-grounded *relative* weighting
  than the current volume-only calibration — same caveat discipline `experiments/model_routing/PROPOSAL.md`
  already applies to `cost_proxy_score` today.

## 4. Proposed approach

| Step | What |
|---|---|
| 1 | Build a local script (`experiments/cost_proxy_calibration/extract_transcript_usage.py`) that walks this project's `~/.claude/projects/-home-u24desktop-Working-rpg-based-simulation/*.jsonl`, and for each assistant turn, pairs its real `usage` block with the tool-use records that immediately preceded it in the same turn (Bash duration, Read/Edit/Write/MultiEdit count, Agent-spawn count) — the same feature set `cost_proxy_score` already uses. |
| 2 | Fit a simple linear regression (real `input_tokens + output_tokens`, or a pricing-weighted token cost, as the target) against the existing three features (`bash_ms`, `agent_spawn_count`, `edit_count`) — producing evidence-derived weights to compare against the current `W_BASH=0.001`/`W_AGENT=50`/`W_EDIT=1`. |
| 3 | Report the fit quality (R², residual spread) honestly — if the fit is weak, that itself is a real, useful finding (it would mean tool-call counts alone don't predict token cost well even in-sample, which bears directly on whether `cost_proxy_score`'s whole approach is sound, not just its constants). |
| 4 | **Validation gate before any change to `tools/agent-monitoring/cost_proxy.py` itself:** compare the *rank order* of phases/agents cost_proxy_score already produces (via `make agent-monitoring-retro`) under the current weights vs. regression-derived weights. If the rank order doesn't change materially, recalibration isn't worth the churn — report that as the outcome. If it does change, that's a real, actionable finding for `experiments/model_routing/PROPOSAL.md`'s §6 validation plan, which explicitly depends on `cost_proxy_score`'s per-phase numbers being trustworthy. |

## 5. Guardrails

- **Read-only against `~/.claude/`.** This experiment only reads local transcript files; it never
  writes to or modifies anything under `~/.claude/`.
- **No change to `tools/agent-monitoring/cost_proxy.py` from this experiment directly.** Per the
  established `experiments/` convention (see `experiments/loop/PROPOSAL.md`, `experiments/model_routing/PROPOSAL.md`),
  only a validated result graduates into a real ticket — this sandbox produces evidence, not a landed change.
- **The main-session-to-subagent generalization risk (§3) must be stated in any output this experiment
  produces**, not silently assumed away — a regression fit that looks clean in-sample is not evidence
  it transfers to a structurally different execution context.
- **Transcript content may include prior conversation text.** The extraction script must only emit
  aggregate numeric features (token counts, tool-call counts/durations) — never raw message content —
  into any result file, consistent with not distributing conversation content beyond its original context.

## 6. Explicitly out of scope for v1

- Any live change to `cost_proxy.py`'s shipped weights — this is an investigation producing evidence
  for a future, separate decision.
- Solving the subagent-telemetry gap itself — confirmed genuinely platform-blocked in §2.
- Real dollar-cost modeling — even with a calibrated token estimate, converting to $ requires
  per-model pricing assumptions not verified in this pass.
- Touching `experiments/model_routing/`'s own validation plan directly — this is a prerequisite input
  to it (better-grounded `cost_proxy_score` weights), not a replacement for its historical-replay approach.

## 7. Open decisions before building

- [ ] Confirm this project's 21 local transcript files provide enough real assistant turns with both
      `usage` and immediately-preceding tool-use records to fit a meaningful regression (not yet counted).
- [ ] Decide whether a weak/noisy fit (§4 step 3) should be reported as a standalone negative finding
      even if no weight change follows — recommended yes, since "tool-call counts don't predict token
      cost well" is itself valuable evidence for `docs/ai/agent_infrastructure_audit.md`'s determinism
      discussion, independent of whether recalibration happens.
- [ ] Decide the pricing-conversion question (§6) only if the token-level fit itself proves strong
      enough to be worth extending — not before.

## Related

- `docs/agent-monitoring/README.md` — "What It Does NOT Capture" section, origin of the platform-blocked claim this proposal verifies rather than re-assumes
- `tools/agent-monitoring/cost_proxy.py` — the formula and weights this proposal evaluates for recalibration
- `docs/plans/archive/agent_infrastructure/idea_agent_cost_observability.md` — Tier 3 (real telemetry), the item this proposal's negative finding closes
- `TCK-20260708-AGENT-COST-OBSERVABILITY`, `TCK-20260708-AGENT-INFRA-HARDENING-EPIC` — where Tier 1/2 shipped and Tier 3 was scoped out
- `experiments/model_routing/PROPOSAL.md` — the sibling proposal whose §6/§7 validation plan depends on `cost_proxy_score` being trustworthy; this proposal's output is a direct input to that one
- `experiments/loop/PROPOSAL.md`, `experiments/audit_expansion/PROPOSAL.md` — sibling `experiments/` proposals this follows the same sandbox convention as
- `~/.claude/projects/-home-u24desktop-Working-rpg-based-simulation/*.jsonl` — the real local usage-data source this proposal's approach depends on (machine-local, not part of this git repo)

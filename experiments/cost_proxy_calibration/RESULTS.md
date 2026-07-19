---
status: historical
layer: observability
authority: P2
audience: developer
date: 2026-07-19
tags: [observability, agent-monitoring]
---

# Results: cost_proxy_score calibration experiment

**Ran:** 2026-07-19, per PROPOSAL.md §4's steps 1-4. Sandbox output — no change made to
`tools/agent-monitoring/cost_proxy.py`. This is evidence for a future, separate decision, not a
landed change (per the proposal's own guardrails).

**Scripts:** `extract_transcript_usage.py` (read-only against `~/.claude/projects/-home-vboxuser-Work-rpg-based-simulation/*.jsonl`,
33 files, emits only aggregate numeric features — never raw content — to
`extracted_usage_features.jsonl`), `fit_regression.py` (fits the regression,
`regression_fit_result.json`), `validate_rank_order.py` (the §4 step 4 validation gate against real
`agent-monitoring/tools.jsonl`/`events.jsonl`).

## 1. Extraction

26,911 assistant turns with a real `usage` block found across 33 local transcript files (14,460 of
which made at least one tool call). **Independently reconfirmed the proposal's platform-blocked
finding on this machine's own data**: `isSidechain` is `false` on all ~56K sidechain-flagged
records — zero subagent-turn transcripts exist locally, matching the proposal's finding on a
different machine. This experiment's token/tool-call data is therefore entirely from the
**orchestrating (interactive) session**, never from a spawned subagent — the same structural gap
the proposal names as its central open risk (§3), confirmed again here rather than just inherited.

## 2. Regression fits — two granularities, two very different outcomes

**Turn-level (Fit A/B) — decisive negative, near-zero signal:**

| Fit | n | R² | bash_ms coef | agent_count coef | edit_count coef |
|---|---|---|---|---|---|
| A — all turns w/ usage | 26,911 | **0.0001** | -0.000006 | -2.99 | 49.67 |
| B — turns w/ ≥1 tool call | 14,460 | **0.0000** | -0.000008 | ~0 | ~0 |

Pearson r vs. `total_tokens`: `bash_ms` -0.002, `agent_count` 0.32, `edit_count` 0.02. Essentially no
linear relationship. **Mechanistically explainable, not just a noisy fit**: a turn's own token cost
reflects what that turn is *about to ask for* (thinking + the tool_use request itself), not a
property of the tool call's own execution — there's no reason a single Bash call's wall-clock time
or an Edit call's existence would predict how many tokens the *preceding* generation cost. This
pairing (one turn ↔ that same turn's own tool_use blocks) is a mechanistic mismatch, not evidence
that tool-call volume never predicts cost.

**Session-level aggregate (Fit C) — strong signal, but domain-mismatched:**

| Fit | n | R² | bash_ms coef | agent_count coef | edit_count coef |
|---|---|---|---|---|---|
| C — per-session totals | 31 sessions | **0.9265** | 0.0127 | 7032.11 | 2393.55 |

Single-feature Pearson r: `bash_ms` 0.70, `agent_count` 0.75, `edit_count` **0.91** (dominant).
Summing each session's total tool-call footprint against its total token spend produces a strong
fit — but **this is not the population `cost_proxy_score` actually scores**. `cost_proxy_score` is
computed per `(run_id, seq)` group — one subagent's execution during one ticket-pipeline phase.
Fit C's "session" mixes the orchestrator's own direct tool calls (this interactive session, not a
ticket-pipeline run) with occasional `Agent`-spawn requests, at a much coarser grain (a whole
multi-hour session, not one phase's footprint). **Generalizing Fit C's ratios to subagent-scoped
scoring is an assumption, not a proven transfer** — exactly the risk PROPOSAL.md §3 requires be
stated, not assumed away.

## 3. Validation gate (§4 step 4) — real, material rank-order changes

Recomputed `cost_proxy_score` for all 928 real `(run_id, seq)` groups with a matching phase/agent
event, under shipped weights (`W_BASH=0.001, W_AGENT=50, W_EDIT=1`) vs. Fit C's ratios
(`W_BASH=0.0127, W_AGENT=7032, W_EDIT=2394`), and compared mean-score rank order.

- **Spend-by-phase**: Spearman rank correlation **0.76** (not 1.0). Largest mover: `Plan` jumps from
  rank 13 (near-cheapest, shipped) to rank 6 (mid-pack, Fit C) — a 7-rank shift. `Test` drops 5
  ranks. `Investigate`/`Scope` each rise 2 ranks.
- **Spend-by-agent**: Spearman rank correlation **0.85**. `planner` mirrors `Plan`'s 7-rank jump.
  `test-scoper` drops 5 ranks. `ticket-scoper`/`investigator`/`done-checker` each rise 2-3 ranks.
- (Several buckets — `Sync Docs`, `Classify Drift`, `Parity Check`, `Update Anchors` — have n=1 and
  are too small to trust either ranking; excluded from the "material" judgment above.)

**Per the proposal's own decision rule**: this is a *material* rank-order change, not a trivial
reshuffling — recalibration is not a wash. `Plan`/`planner` in particular look meaningfully
under-ranked by the shipped weights' current `edit_count`-vs-`agent_count` ratio.

## 4. Honest bottom line

- The **platform-blocked** finding (no real per-subagent token telemetry recoverable locally) is
  reconfirmed, independently, on this machine's own data.
- Turn-level pairing (the most literal reading of the proposal's step 1) produces **no usable
  signal** — a real negative result, not a failed experiment.
- Session-level aggregation produces a **strong but domain-mismatched** signal — real evidence that
  tool-call volume and token cost correlate *in general*, but not evidence for what the *correct*
  per-tool-call weight ratios are for a subagent-scoped execution, since no local data exists at that
  grain (same platform-blocked gap).
- The validation gate shows shipped weights and Fit C's weights **would** materially reorder
  spend-by-phase/agent — so the choice of weights is not inconsequential, which argues *for* further
  calibration work being worthwhile, while simultaneously showing Fit C itself is not yet the
  trustworthy source for that recalibration.

## 5. Recommendation

**Do not change `cost_proxy.py`'s shipped weights based on this experiment alone** — Fit C's
domain mismatch (orchestrator-session vs. subagent-phase scoring) is disqualifying for direct
adoption, exactly per the proposal's own stated risk. But the validation gate's result (real,
material rank-order sensitivity to the weight choice) means this is worth a real follow-up, not a
dead end:

- The productive next step is **not** "trust Fit C's numbers" — it's finding (or building) a data
  source at the *correct* grain: per-subagent, per-phase token cost. That remains platform-blocked
  locally; the only path is either (a) future harness-level telemetry from Anthropic (Tier 3, already
  tracked as blocked in `docs/plans/archive/agent_infrastructure/idea_agent_cost_observability.md`),
  or (b) a narrower proxy validated against something other than raw session totals.
- `edit_count` was by far the strongest single predictor in Fit C (r=0.91 vs. 0.70/0.75) — worth
  treating as a weak prior that `W_EDIT` may be relatively under-weighted vs. `W_AGENT` in the
  shipped formula, without committing to Fit C's exact ratio.
- If a future ticket does revisit these weights, it should re-run this experiment's
  `validate_rank_order.py` gate against any candidate weights before shipping — the gate itself
  (comparable to real `tools.jsonl` data) is reusable, independent of Fit C's own validity.

## Related

- `experiments/cost_proxy_calibration/PROPOSAL.md` — the experiment this results doc reports on.
- `tools/agent-monitoring/cost_proxy.py` — the shipped formula evaluated, unchanged by this experiment.
- `docs/plans/archive/agent_infrastructure/idea_agent_cost_observability.md` — Tier 3 (real telemetry), still platform-blocked, reconfirmed here.
- `experiments/audit_expansion/PROPOSAL.md` D25 — independently found related agent-monitoring data-quality gaps (phase-vocabulary fragmentation, low duration/cost field coverage, unexplained outliers).

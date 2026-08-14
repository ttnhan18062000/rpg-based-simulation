---
status: historical
layer: observability
authority: P2
audience: developer
maturity: shipped
date: 2026-07-19
archived: 2026-07-19
tags: [idea, agent-infrastructure, observability, agent-monitoring, data-quality]
---

# Proposal: Agent-monitoring data-quality epic — normalize, cover, flag, and stop re-deriving the same signals by hand

**Archived:** 2026-07-19 — all five concerns shipped the same day, via `tickets/todos/agent-monitoring-data-quality/`
(all now `tickets/done/`): `TCK-20260719-PHASE-AGENT-CASE-FOLD` (concern 1, casing-variant
normalization in `generate_retro.py`, new `phase_status_distribution` report section), `TCK-20260719-COST-PROXY-WRITE-PATH`
(concern 2 — investigation found the coverage question was **not** a pure audit: `duration_s` is
already resolved at 99.13% coverage, but `cost_proxy_score`/`tool_call_count` had a real, ongoing
~30-37% null rate since 2026-07-11, root-caused to the same LLM-executed-bookkeeping anti-pattern
already fixed for `duration_s` — fixed by moving the compute into `record_events.py`),
`TCK-20260719-RETRO-OUTLIER-FLAGS` (concern 3, new `## Outliers` retro-report section, scoped to
CLI/Markdown only after investigation found the dashboard would **not** benefit automatically as
this proposal assumed — see that ticket's own correction), `TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE`
(concern 4, `experiments/cost_proxy_calibration/validate_rank_order.py` promoted to
`tools/agent-monitoring/weight_sensitivity_check.py`), `TCK-20260719-COST-PROXY-CALIBRATION-NOTE`
(concern 5, dated finding recorded in `cost_proxy.py`'s docstring and
`docs/agent-monitoring/README.md`). Direct weight recalibration of `cost_proxy.py` remained
deliberately out of scope throughout, per this proposal's own "Explicitly deferred" section below —
no weight constant was changed by any of the five tickets. This document is the historical design
reference.

**Maturity: SHIPPED** — direct follow-up to `experiments/cost_proxy_calibration/`'s just-completed
extraction/regression experiment (see `RESULTS.md` in that folder). That experiment set out to
recalibrate `cost_proxy_score`'s shipped weights against real local token-usage data and returned a
**disciplined negative for direct weight adoption** (the only fit with real signal comes from a
domain-mismatched population — whole-session totals, not per-subagent/per-phase scoring), but along
the way surfaced — and, via `experiments/audit_expansion/PROPOSAL.md`'s independent D25 dimension,
corroborated — several real, fixable data-quality gaps in `agent-monitoring/*.jsonl` that don't
require solving the platform-blocked telemetry problem at all. This proposal scopes those into a
real epic, and explicitly keeps weight recalibration itself **out** of the actionable set until
better ground-truth data exists.

## Background investigation (already done, feed this to Investigate — do not redo)

**From `experiments/cost_proxy_calibration/RESULTS.md` (2026-07-19):**
- Reconfirmed, independently, on this machine's own 33 local transcripts: zero subagent-turn
  transcripts exist locally (`isSidechain` is `false` on all ~56K flagged records) — real
  per-subagent token cost remains genuinely platform-blocked, not just inherited belief.
- Turn-level regression (pairing a turn's own tokens against that turn's own tool calls): R²≈0.0000,
  a real negative, mechanistically explained (a turn's cost reflects what it's about to ask for, not
  a property of the tool call itself).
- Session-level regression (summing whole-session totals): R²=0.93, but this population mixes the
  orchestrator's own direct tool calls with occasional Agent-spawns, at the wrong grain
  (whole session, not one phase's footprint) — not a valid stand-in for subagent-scoped scoring.
  `edit_count` was the strongest single predictor (r=0.91) — noted as a weak, unconfirmed prior that
  `W_EDIT` may be under-weighted relative to `W_AGENT` in the shipped formula, not adopted.
- The validation-gate script (`validate_rank_order.py`) proved real, material rank-order sensitivity
  to weight choice on the actual 928 `(run_id, seq)` groups in `agent-monitoring/tools.jsonl` today
  (Spearman 0.76 phase / 0.85 agent, `Plan`/`planner` moving 7 ranks) — meaning the *tooling* to judge
  a future candidate weight change is now real and reusable, even though this pass's specific
  candidate weights aren't trustworthy enough to ship.

**From `experiments/audit_expansion/PROPOSAL.md`'s D25 (Pipeline Throughput & Rework Economics,
computed directly from live `agent-monitoring/events.jsonl`/`runs.jsonl`, 2,901 events / 609 runs /
51,549 tool calls, 2026-07-14) — independent corroborating evidence, not re-derived here:**
- **F1 — phase/agent vocabulary fragmented 2-3 ways per label**: `Verify`/`verify`/`VERIFY`,
  `Implement`/`implement`/`IMPLEMENT`, and 6 more phases each split into separate buckets — this
  silently *undercounts* real failure rates when read naively (`Review`'s true failure rate, only
  visible after merging casing variants, is 18.2% — the highest of any phase).
- **F2/F3 — real, unexplained outliers with zero recorded investigation**: `duration_s` shows a
  ~2000x spread (25s to ~14h) with no flagging mechanism; `cost_proxy_score` shows a >10x spread
  within the same phase/agent pair, also unflagged.
- **Coverage gap, dated**: only 193/2,901 events (6.7%) carry `cost_proxy_score`, only 56/609 runs
  (9.2%) carry `duration_s`, as of 2026-07-14 — expected for historical rows predating
  `TCK-20260708-AGENT-COST-OBSERVABILITY` (2026-07-08), **not yet verified whether coverage has
  actually improved for new rows since**, which is the real open question this proposal turns into
  an actionable audit rather than leaving as a stale snapshot number.

## Explicitly deferred, not actionable yet

**Direct weight recalibration of `tools/agent-monitoring/cost_proxy.py`.** The only fit with real
signal (Fit C, session-level) is domain-mismatched to what the formula actually scores — adopting
it would trade one unvalidated assumption (today's volume-only weights) for another (whole-session
ratios applied to subagent-phase scoring), not a genuine improvement. Blocked on either real
harness-level per-subagent token telemetry (Tier 3, `docs/plans/archive/agent_infrastructure/idea_agent_cost_observability.md`,
still platform-blocked) or a narrower proxy validated against something other than raw session
totals — neither of which this epic's concerns below require.

## Architectural constraints (carry forward from prior agent-monitoring work)

- `agent-monitoring/*.jsonl` stays append-only, hook-written — no change to the write path's
  synchronous, must-never-fail-the-workflow guarantee (CLAUDE.md hard rule). Every concern below is
  a **read-time** normalization/reporting change, or a **going-forward coverage audit**, never a
  historical backfill (matching this subsystem's established no-backfill precedent, e.g.
  `TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT`).
- Phase/agent normalization belongs at the same read-time layer `generate_retro.py`'s existing
  `_resolve_status()`/`_is_legacy_event()`/`_is_gate_fail()` already occupy — extend that
  established normalization point, don't invent a second one. Cross-check against
  `docs/plans/agent_infrastructure/idea_agent_monitoring_derived_index.md` (SCHEDULED, 4 draft
  tickets already queued in `tickets/todos/agent-monitoring-derived-index/`) before touching this —
  that idea's `build_index.py` is explicitly designed to centralize exactly this kind of
  once-per-reader-duplicated normalization logic; if its first ticket (`TCK-20260713-MONITORING-SQLITE-INDEX`)
  lands before this epic's normalization concern is scoped, the normalization may belong in the
  index's build step instead of (or in addition to) `generate_retro.py` directly — a real
  sequencing decision for Investigate, not assumed here.
- `tools/agent-monitoring/cost_proxy.py`'s own module docstring is the established place this
  subsystem records calibration provenance ("weights... sized from the real aggregate distribution
  of `agent-monitoring/tools.jsonl`... not guessed") — any doc update recording this experiment's
  findings should extend that docstring's spirit, not create a disconnected second record.
- `experiments/cost_proxy_calibration/validate_rank_order.py` was written against real
  `agent-monitoring/tools.jsonl`/`events.jsonl` already (not a fixture) — promoting it should
  preserve that real-data default while still allowing tests to exercise it against a `tmp_path`
  fixture, mirroring how every other `tools/agent-monitoring/*.py` module is tested.

## Concerns for Comprehend/Investigate to turn into child tickets

1. **Phase/agent vocabulary normalization at read time.** Extend `generate_retro.py`'s existing
   normalization point (or `build_index.py`'s build step, per the sequencing note above — Investigate
   decides) to fold `Verify`/`verify`/`VERIFY`-style casing variants into one canonical bucket for
   all 8 affected phases, closing D25 F1. Add a regression test proving the previously-undercounted
   failure rate (e.g. `Review`'s real 18.2%) is now computed correctly from raw fragmented input.

2. **Duration/cost-proxy field coverage audit, going forward.** Re-run D25's coverage measurement
   (`duration_s` on `runs.jsonl`, `cost_proxy_score`/`tool_call_count` on `events.jsonl`) scoped to
   records written **after** `TCK-20260708-AGENT-COST-OBSERVABILITY` (2026-07-08) only, to determine
   whether the 9.2%/6.7% figures are purely historical (expected, no action needed) or whether some
   current workflow entry points (`implement-epic`, `create-tickets` — both named in
   `idea_agent_monitoring_derived_index.md` as having "incomplete or zero sidecar registration") are
   still failing to populate these fields on new runs. If a real ongoing gap is found, fix the
   specific write path; if not, close this concern with the measurement as evidence, no code change
   needed.

3. **Outlier flagging in the retro report.** Add a per-run/per-event outlier flag (e.g.
   `duration_s > 3x` the phase median, or `cost_proxy_score > Nx` the phase/agent median) surfaced as
   a visible line in `make agent-monitoring-retro`'s output, closing D25 F2/F3's "zero recorded
   investigation" gap. Does not need to explain *why* an outlier occurred — just make it visible
   instead of silently sitting in the data, matching this session's own "investigate before
   assuming" discipline for whoever reviews the next retro report.

4. **Promote `validate_rank_order.py` into a real, tested tool.** Move
   `experiments/cost_proxy_calibration/validate_rank_order.py` into `tools/agent-monitoring/` (e.g.
   `weight_sensitivity_check.py`), parameterize the two weight sets it compares (currently
   hardcoded shipped-vs-Fit-C) as CLI args, add `tests/tools/test_*` coverage, and document it in
   `docs/agent-monitoring/README.md` as the required check before ever proposing a `cost_proxy.py`
   weight change — this is the one piece of reusable infrastructure this experiment produced that
   outlives its own inconclusive result.

5. **Record the experiment's finding, don't let it get re-derived from scratch later.** Extend
   `tools/agent-monitoring/cost_proxy.py`'s module docstring and/or
   `docs/agent-monitoring/README.md`'s "What It Does NOT Capture" section with a short, dated note:
   platform-blocked reconfirmed 2026-07-19 against real local transcripts; `edit_count` is a weak,
   unconfirmed prior for being under-weighted; recalibration remains blocked on better ground-truth
   data, not on missing investigation. Link `experiments/cost_proxy_calibration/RESULTS.md` as the
   evidence trail.

## Explicitly out of scope

- Any change to `cost_proxy.py`'s shipped `W_BASH`/`W_AGENT`/`W_EDIT` constants — see "Explicitly
  deferred" above.
- Solving the subagent-token-telemetry platform-blocked gap itself — not newly investigated here,
  only reconfirmed.
- The SQLite derived-index work itself (`tickets/todos/agent-monitoring-derived-index/`'s 4 already-
  scheduled tickets) — this proposal only asks Investigate to check sequencing against it, not to
  duplicate or re-scope it.
- Backfilling historical `duration_s`/`cost_proxy_score`/normalized-phase data — append-only,
  no-backfill precedent holds throughout.
- Any UI/dashboard change — this proposal is about the underlying `agent-monitoring/*.jsonl` data
  and its CLI/report consumers, not the Agent Ops Dashboard's Stats tab (which already consumes
  whatever `generate_retro.py` computes, per `TCK-20260718-RETRO-STATS-REFACTOR`, and would benefit
  from this epic's fixes automatically without needing its own ticket).

## Related

- `experiments/cost_proxy_calibration/PROPOSAL.md`, `RESULTS.md` — the experiment this proposal's
  concerns 4-5 directly follow up on.
- `experiments/audit_expansion/PROPOSAL.md` — D25 (Pipeline Throughput & Rework Economics), source
  of concerns 1-3's evidence.
- `docs/plans/agent_infrastructure/idea_agent_monitoring_derived_index.md` — SCHEDULED, adjacent
  normalization-centralization work; sequencing dependency for concern 1.
- `docs/plans/archive/agent_infrastructure/idea_agent_cost_observability.md` — Tier 3, the
  platform-blocked telemetry gap this proposal's deferred item remains blocked on.
- `tools/agent-monitoring/cost_proxy.py`, `tools/agent-monitoring/generate_retro.py` — the two
  modules concerns 1 and 4-5 touch.

---

*Raised: 2026-07-19, directly from `experiments/cost_proxy_calibration/`'s completed experiment and
its cross-reference to `experiments/audit_expansion/PROPOSAL.md`'s independently-computed D25
findings against the same underlying data. Turned into 5 real tickets via `/create-tickets` the same
day — see the Archived note at the top of this document.*

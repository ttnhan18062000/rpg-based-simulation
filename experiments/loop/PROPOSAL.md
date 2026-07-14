# Proposal: A Minimal Autonomous Loop for Mechanical Optimization Problems

**Status:** proposed, not built
**Location:** `experiments/loop/` (lightweight sandbox — exempt from the ticket/staging-artifact workflow per project convention; only a *result* the loop finds ever graduates into a real ticket)
**Date:** 2026-07-14

---

## 1. Origin

Two reference points were reviewed:

- **[karpathy/autoresearch](https://github.com/karpathy/autoresearch)** — a minimal 3-file pattern for autonomous ML research: `prepare.py` (fixed, not touched), `train.py` (the one file the agent edits), `program.md` (agent instructions). Fixed 5-minute time budget per trial, one metric (`val_bpb`), git commit before verify, keep on improvement / revert on regression. ~12 experiments/hour, ~100 overnight. The repo itself is nanochat-specific — not reusable code — but the **loop shape** (one scoped file, one mechanical metric, git as memory, automatic rollback, bounded iterations) is the transferable idea.
- **[uditgoenka/autoresearch](https://github.com/uditgoenka/autoresearch)** — generalizes that loop into a 14-command Claude Code skill (`/autoresearch`, `:debug`, `:fix`, `:security`, `:ship`, `:reason`, `:regression`, etc.), with safety hooks, bounded defaults, TSV result logging, and `handoff.json` chaining between commands.

## 2. Decision: build a minimal custom version, not import either

- Karpathy's repo is literally an ML training script; nothing in it is reusable outside nanochat.
- uditgoenka's skill is generic-codebase tooling that duplicates capability this repo already has purpose-built agents/workflows for (`:security` ≈ `security-reviewer`, `:ship` ≈ the Finalize phase, `:fix`/`:debug` ≈ `test-scoper`/`world-debugger`), and it has zero awareness of this repo's ticket lifecycle, parity ledger, or Mechanics Bible rules — installing it wholesale would let an autonomous loop commit changes that bypass every gate this project relies on.
- What's actually missing from this project is narrower: an **unattended search/optimization primitive** for the specific class of problems that are pure numeric tuning, not judgment calls. That's worth ~150 lines of project-specific code, not a 14-command plugin.

## 3. What the current process already covers vs. what's missing

This project's agent system (11 subagents, 11 workflows, 16 skills — see `docs/ai/system_overview.md`) already has a 10-phase gated ticket pipeline, a 7-phase `/simq-audit` calibration lane, and `agent-monitoring/` observability. It scores 8.0/10 on its own infrastructure audit ("Mature, gated, not yet deterministic").

What it does not have, structurally:

| Gap | Why the existing pipeline can't fill it |
|---|---|
| Parameter search, not single-shot guessing | The ticket pipeline is built for "implement a known, scoped change correctly," not "try 20-30 variants and compare." |
| Unattended/overnight execution | Every phase needs a live agent call in an active session — nothing here runs while a human is away. |
| Per-trial trend logging | `agent-monitoring/` logs *workflow runs*; nothing logs *experiment trials* with a metric delta and keep/discard verdict. |
| Automatic revert bookkeeping | Reverting a bad experimental change today is a manual, human-decided `git revert`. |

**What this does not replace:** architecture review, security review, DoD verification, Mechanics Bible/parity-ledger consistency. A loop-found result is a *candidate*, not a landed change — it still goes through one normal ticket to reach `simulation_quality`/`main`.

## 4. Architecture — three pieces, mirroring Karpathy's split

| File | Role |
|---|---|
| `experiments/loop/spec.md` | Per-run declaration: Goal, Scope (single file or narrow glob), Metric (a shell command emitting one number), Direction (higher/lower is better), Guard (a safety command that must not regress), Iterations (bounded default). Edited per experiment. |
| `experiments/loop/runner.py` | Fixed harness, not touched by the agent mid-run. Per iteration: propose a change to the scoped file(s) → commit → run Metric → run Guard → keep, or `git reset --hard HEAD~1` on regression/guard failure → append a row to `results.tsv`. Stops at N iterations or on convergence, reports the best commit. |
| `experiments/loop/results.tsv` | Per-trial log: `iteration, commit, metric, delta, guard_status, verdict, description`. Gives the trend/plateau visibility the project currently lacks. |

### Guardrails (non-negotiable for v1)

- **Isolation via `git worktree`, never `checkout`/`stash`/`reset` on a live working directory.** A worktree starts clean from a specified commit and is blind to any uncommitted changes elsewhere — this is what makes it safe to run alongside another concurrent session's in-progress, uncommitted ticket work.
- **Scope is always narrow and non-durable-adjacent for v1** — tuning values and isolated modules, not core `src/engine/` orchestration files.
- **Guard command reuses real project tooling** (e.g. the existing perf-baseline tolerance check, or SimQ anchor-stability check) rather than reinventing verification.
- **The loop never commits to shared history.** Its output is exactly one artifact — the best diff plus `results.tsv` evidence — which becomes the input to one normal ticket, carrying a real `TCK-YYYYMMDD-...` commit. The dozens of intermediate experimental commits stay on the disposable branch/worktree and are discarded (or kept locally for reference, never pushed).

## 5. Concurrent-session finding (2026-07-14 investigation)

At the time this was scoped, another session was actively working `TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE` (Phase 3 of the SimQ roadmap — COGNITION pipeline wiring) on this same branch (`simulation_quality`), with 18 uncommitted files including `src/engine/pipeline.py`, `phase_graph.py`, `feature_flags.py`.

Checked against `tickets/working_log.csv` and `git log`: 4 of 5 SimQ roadmap tickets had already landed in commit `5c51dca2` (`SIMQ-EVAL-PROFILE-BUG`, `SIMQ-SCORE-CEILING-FIX`, `SIMQ-RAWSCORE-PERSIST`, `SIMQ-ECONOMY-CONTENT-DEPTH`) — including the exact weight-tuning proof-of-concept originally proposed for this loop (`SCORE-CEILING-FIX` already recalibrated `config/simulation_quality/scoring_weights.yaml`). Only Phase 3 (COGNITION wiring) remains, it's a one-time structural wiring task (not a numeric-tuning problem, so not a good loop candidate anyway), and it was actively in flight — a direct collision target to avoid.

Cross-referenced perf test imports (`grep -rl "engine.pipeline\|phase_graph\|optimization.feature_flags" tests/perf/*.py`): only 2 of ~20 perf test files (`bench_capacity.py`, `test_phase10_integrated_enhanced_stack_budget.py`) overlap the files being concurrently edited. Everything else in `tests/perf/` is a safe, non-colliding scope.

## 6. Candidate metrics, ranked

1. **Performance** (`tools/perf_guard.py measure` vs `perf_baselines.json`) — **current pick**. Lower-is-better, mechanical, already has a measure/tolerance-check tool, zero overlap with in-flight work once the 2 colliding perf files are excluded.
2. **A future SimQ roadmap round** — see §7. Not runnable yet; the current roadmap is essentially closed (4/5 done, 5th in flight elsewhere).
3. **Test suite health** (failing/skipped count in one module) — simplest, lowest domain risk, least interesting result. Fallback if performance turns out not to have enough tunable headroom.
4. **SimQ ECONOMY content depth / COGNITION wiring** — explicitly ruled out as loop candidates: both are judgment-heavy (content authoring, architectural call-site placement), not mechanical numeric optimization.

## 7. Concrete first run (proposed)

- **Scope:** `src/domains/adventure/phase.py`
- **Metric:** `python3 tools/perf_guard.py measure --test tests/perf/test_phase3_adventure_decision_budget.py` → `time_ms`, lower is better
- **Guard:** re-run `tests/perf/` minus `bench_capacity.py` and `test_phase10_integrated_enhanced_stack_budget.py` (the 2 files overlapping in-flight work); reject any change that flips another test's status to `REGRESSION`
- **Isolation:** `git worktree add ../rpg-perf-loop -b loop/perf-adventure-phase simulation_quality`
- **Iterations:** bounded default, e.g. 20

## 8. A dedicated branch/worktree for a future SimQ roadmap round

When a next SimQ roadmap emerges (post Phase 3 closeout), the same pattern applies at the "roadmap" level, not just per-run:

```
git worktree add ../rpg-simq-loop -b loop/simq-roadmap2 simulation_quality
```

- Forked from `simulation_quality` HEAD (not `main` — `simulation_quality` is 234 commits ahead and holds all the finished SimQ work; branching from `main` would lose that context).
- The original directory keeps running the normal ticket-gated pipeline untouched (finishing `TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE` and beyond).
- The new worktree directory accumulates the loop's own experimental commit history in isolation.
- Only a winning result is ever ported back to `simulation_quality` as a proper ticket — never merged wholesale, since the loop's per-iteration commits won't carry `TCK-YYYYMMDD-...` IDs per the commit convention.

## 9. Explicitly out of scope for v1

- Anything touching `src/engine/` orchestration files or other durable simulation behavior directly.
- Installing the uditgoenka 14-command skill wholesale.
- Making the loop a permanent `.claude/` skill/command — a later decision, gated on whether this first run actually proves valuable, and if so, going through the normal ticket pipeline itself (since new durable agent tooling is exactly the kind of change that pipeline exists to gate).
- Re-opening any SimQ pillar declared complete by the archived roadmap's Phase 5 gate (FACTION/INFORMATION/SOCIAL/AGENCY corpus depth) or any of `quality_scoring_contract.md` §14's Non-Goals.

## 10. Open decisions before building

- [ ] Confirm the performance target (§7) as the first real run, or pick a different scoped file.
- [ ] Confirm bounded iteration default (proposed: 20).
- [ ] Confirm `runner.py`'s change-proposal step: does the agent itself write the code diff per iteration (LLM-in-the-loop, like Karpathy's design), or does `runner.py` drive a scripted parameter sweep for the first pass (simpler, fully mechanical, no agent judgment needed per-iteration)?

## Related

- `docs/ai/system_overview.md` — the existing agent/workflow/skill system this loop supplements, not replaces
- `docs/plans/simq_scoring_improvement_roadmap.md` — the (now largely closed) roadmap that originally motivated the SimQ use case
- `tools/perf_guard.py`, `perf_baselines.json` — the tooling the first run's Metric/Guard reuse
- `tickets/working_log.csv` — source of truth for what SimQ roadmap work has actually landed

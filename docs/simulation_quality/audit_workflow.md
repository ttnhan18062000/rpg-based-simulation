---
status: active
layer: observability
authority: P1
audience: developer
tags: [simulation-quality, workflow, audit, tooling, process]
---

# SimQ Audit Workflow

**Ticket:** TCK-20260703-SIMQ-UPLIFT3-AUDIT-WORKFLOW
**Last updated:** 2026-07-04

---

## 1. What this replaces

Across SimQ Uplift Batches 1-3 (`TCK-20260702-SIMQ-UPLIFT2-FACTION`, `-INFORMATION`,
`TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`, `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`, and others),
the same manual sequence was repeated by hand each time: re-run the calibration corpus, diff grade
movement against `tests/simulation_quality/fixtures/grade_anchors.json`, decide which movements were
expected vs. genuine regressions, update `docs/simulation_quality/eval_matrix_results.md` and
`docs/audits/D20_simq_integration.md`, and check `docs/parity_ledger/*.yaml` for staleness. The process
had no single entry point — it was re-derived by whoever picked up the next SimQ ticket, and at least one
step (updating `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` whenever a new anchor key was added) was never
written down anywhere and was only caught by reading the test file directly.

This workflow — `make simq-full-audit` (mechanical phase) + `.claude/workflows/simq-audit.js` /
`.claude/skills/simq-audit/SKILL.md` (full 7-phase orchestration) — formalizes that sequence so a future
session can trigger `/simq-audit` and get the same complete, consistent result without re-deriving the
process or missing a step.

## 2. The 7-phase pipeline

Defined in `.claude/workflows/simq-audit.js`; invoked via `/simq-audit` (see `.claude/skills/simq-audit/SKILL.md`).

1. **Recalibrate** — runs `make simq-full-audit` (or `-full`/`-slow` per `mode`) via Bash. This is the
   workflow's only non-judgment phase: it diffs current calibration data against anchors
   (`tools/evaluate_simq.py --dry-run`), runs the fast-tier grade regression tests, and cross-checks
   anchor/parity coverage gaps (`tools/simq_audit_gaps.py`). Captures REGRESS rows, pytest pass/fail
   counts, uncovered anchor keys, and parity ledger candidates verbatim for the next phase.
2. **Classify Drift** — for every REGRESS row, uncovered anchor key, and parity candidate, an agent
   classifies it as `EXPECTED_DRIFT` (must cite a specific commit/ticket ID — never "matches a recent
   pattern"), `REGRESSION`, `DA_NEEDED`, or `NO_ACTION`, then computes a rollup `verdict`:
   `no_regression` / `regression` / `needs_da_decision`.
3. **Update Anchors** — edits `grade_anchors.json` and, for genuinely new run_keys,
   `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` in `tests/simulation_quality/test_grade_regression.py`, for
   `EXPECTED_DRIFT` items only. Re-runs a targeted pytest subset as a gate
   (`targeted_test_passed: boolean`) — if it fails, the workflow stops with `ANCHORS_STILL_FAILING`.
   `REGRESSION`/`DA_NEEDED` items are never anchor-edited — their anchor value is left as-is so the
   regression test keeps failing/flagging them until the spawned follow-up ticket resolves them.
4. **Sync Docs** — updates `docs/simulation_quality/eval_matrix_results.md` (dated NOTE callouts + grade
   distribution counts), `docs/audits/D20_simq_integration.md` (Dimension Profile date, new
   `## SimQ Uplift Batch N` section, Module Health rows), conditionally
   `docs/simulation_quality/event_type_coverage.md` (only if calibration_hits counts changed), and
   conditionally `docs/guidelines/v2_intentional_divergences.md` (only if a DA ruling is made in the same
   run — in the common case this is instead updated by the spawned follow-up ticket).
5. **Parity Check** — updates `docs/parity_ledger/*.yaml` entries flagged by `tools/simq_audit_gaps.py`'s
   candidate scan, using the same verified/divergent/missing status semantics and P0 `test_path`
   requirement as `implement-ticket.js`'s Parity phase.
6. **Verify** — a DoD-style check: fast-tier regression tests pass, `tools/simq_audit_gaps.py` reports
   zero uncovered anchor keys, every doc file Sync Docs was instructed to touch was actually touched or
   explicitly skipped with a stated reason. `BLOCKED` stops the workflow for human resolution.
7. **Report** — a deterministic branch on `verdict` (no `agent()` call for the branch decision itself).
   See the governance decision below.

## 3. Governance decision

`simq-audit` is invocable standalone — it does not require an open ticket, and by default does not
create one. The **Report** phase (7) branches on the Classify Drift verdict:

- **`no_regression`** — every flagged item was classified `EXPECTED_DRIFT` (cites a named, already-landed
  change) or `NO_ACTION`, with no `REGRESSION` or `DA_NEEDED` items. The workflow does **not** create a
  ticket. It emits a suggested lightweight commit message —
  `` chore: SimQ audit <date> — <N> anchors refreshed, no regressions `` — and returns `DONE_NO_TICKET`.
  This mirrors the historical precedent of three doc-sync passes (`79ba7d05`, `cf53674c`, `85922428`)
  that landed with no ticket ID at all.
- **`regression` or `needs_da_decision`** — at least one item was classified `REGRESSION` (unexplained
  grade drop, no known cause) or `DA_NEEDED` (a design-acknowledged ruling is required, e.g. an
  archetype-correctness call like the historical `AGENCY=C` precedent). The workflow does **not** attempt
  to fix the regression or make the DA ruling itself. It spawns one ticket via the `ticket-scoper` role
  (same `TICKET_SCHEMA` shape `implement-ticket.js`'s Scope phase uses), pre-seeded with the specific
  run_key/pillar/cause items Classify Drift found, and returns `NEEDS_TICKET` with a
  `/implement-ticket ticket_id=<new-id>` hand-off instruction.

This choice does **not** change *when* docs/anchors get updated — Update Anchors and Sync Docs still run
for every `EXPECTED_DRIFT`-classified item regardless of the overall verdict. It only changes *how the
run is finalized*: a direct chore commit vs. a full ticket-workflow hand-off for the unresolved items.

## 4. Usage

```
/simq-audit
/simq-audit mode=full
/simq-audit mode=slow
/simq-audit mode=full worlds=frontier_extended,wilderness_survival
```

- `mode=fast` (default) — `--dry-run` diff only; assumes `data/calibration/` is already populated from a
  recent local run. If `data/calibration/` is empty or every `quality_report.json` is stale (>24h), the
  Recalibrate phase auto-escalates to `mode=full` for that run rather than silently diffing against
  nothing.
- `mode=full` — re-runs the engine for all fast (<=500t) scenarios first.
- `mode=slow` — runs the fast tier, then the slow (1000t/2000t) tier.
- `worlds` — optional comma-separated scope for calibration re-runs (only meaningful with `mode=full`).

### Mechanical-only path (no agent session)

A human or CI can run the mechanical phase alone, without any Claude Code session:

```
make simq-full-audit        # fast diff + fast-tier regression tests + coverage/parity scan
make simq-full-audit-full   # same, but re-runs the engine for fast scenarios first
make simq-full-audit-slow   # slow-tier (1000t/2000t) regression check
```

`tools/evaluate_simq.py`'s engine re-run mode (no `--scenario`, no `--dry-run`) defaults to
fast-tier scenarios only (<=500t), matching `simq-full-audit-full`'s own contract above — pass
`--include-slow` to also re-run the SLOW tier in the same invocation (expect a much longer wall
-clock time; `TCK-20260810-SIMQ-EVALUATE-SLOW-TIER-SCOPE-LEAK` found the un-scoped SLOW-tier
re-run alone adds ~450s+ of engine compute across the corpus).

`tools/simq_audit_gaps.py` can also be run directly for just the coverage/parity scan:

```
python3 tools/simq_audit_gaps.py
```

It always exits 0 — it is an informational gap-finder, not a pass/fail gate (the pytest step in
`make simq-full-audit` is the gate). It never writes to `grade_anchors.json`, `test_grade_regression.py`,
or any `docs/parity_ledger/*.yaml` file.

## 5. Do not

- Do not use this workflow to change SimQ scoring formulas, pillar logic, or grade thresholds
  (`src/simulation_quality/*` is out of scope for every phase).
- Do not let the Update Anchors phase edit anchors for a `REGRESSION`- or `DA_NEEDED`-classified item —
  its anchor value must stay as-is so the regression test keeps flagging it until a follow-up ticket
  resolves it.
- Do not skip the `cause`-citation requirement in Classify Drift — every `EXPECTED_DRIFT` classification
  must name a specific commit/ticket ID, never "matches a recent pattern."
- Do not assume `data/calibration/` is committed to git — it is not tracked (matching the repo's
  `data/runs/` cleanup convention); `mode=fast` requires a recent local calibration run to already exist.

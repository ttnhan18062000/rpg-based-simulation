# TCK-20260703-SIMQ-UPLIFT3-AUDIT-WORKFLOW — Investigation

**Date:** 2026-07-04
**Ticket:** TCK-20260703-SIMQ-UPLIFT3-AUDIT-WORKFLOW
**Phase:** Investigation (seq 2)

---

## 1. Current Behavior — the manual process as actually performed (Batches 1-3)

Reconstructed from `git log --all -- docs/audits/D20_simq_integration.md docs/simulation_quality/eval_matrix_results.md`
(15 commits) plus the tools/docs those commits touch. The process has no single entry point today —
it is re-derived by whoever picks up the next SimQ ticket.

### 1.1 Exact commands run, in order

1. **(Conditional) Content/code fix first.** Several batches required a source or content fix before
   recalibration was meaningful (e.g. `TCK-20260701-HAZARD-NATIVE-IMMUNITY`, `TCK-20260702-SIMQ-UPLIFT2-FACTION`'s
   `WorldCompiler` extension, `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`'s `hazard_kind` content additions).
   This step is **ticket-specific implementation work**, not part of the repeatable audit — out of scope
   for this workflow, but the audit must be able to run *after* such a fix lands.
2. **(Conditional) Recompile affected worlds.** `WorldCompiler`/world resolver re-run for any world whose
   module content changed (`make world-compile` / resolver invocation) — required before recalibration
   picks up the fix. Confirmed in `33cf044d`: 8 stale-compiled worlds recompiled before calibration.
3. **Run calibration** for every affected `(world, seed, ticks)` triple:
   `python3 tools/calibrate_simq.py --ticks <N> --seed <S> --name <world> [--profile <profile>]`
   — writes `data/calibration/{name}_seed{seed}_{ticks}t/quality_report.json`. Seen run in batches at
   matrix scale (3 seeds × 2-3 tick counts × N worlds) via `TCK-20260702-SIMQ-EVAL-MATRIX` and
   `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`.
4. **Diff against committed anchors**: `make evaluate` (`python3 tools/evaluate_simq.py --dry-run`,
   no engine re-run — reads existing `data/calibration/*/quality_report.json`) or `make evaluate-full`
   (re-runs the engine for all fast ≤500t scenarios first). Produces a PASS/REGRESS/MISSING table per
   `(run_key, pillar)`, exit code 1 if any REGRESS.
5. **Judgment: classify each REGRESS/drift.** Human/agent decides, per pillar-key delta, whether the
   movement is *expected* (attributable to a known, already-landed code/content/formula change — e.g.
   the D2 grade-decay formula fix, the hazard-kind recompile, a feature-flag activation) or a *genuine
   regression* needing its own investigation/ticket. This is the one step in the whole process that is
   not mechanical — it requires correlating the diff against recent `git log`/`tickets/done/` context.
6. **Update `tests/simulation_quality/fixtures/grade_anchors.json`** — hand-edit committed grades for
   every key whose movement was classified as expected in step 5.
7. **Update `tests/simulation_quality/test_grade_regression.py`'s `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS`
   lists** whenever a *new* run_key is added to the anchor file (not just an existing key's grade
   changing). This step is **not mentioned anywhere in the ticket's own Scope section** but is
   unambiguously part of the real process — confirmed by reading `test_grade_regression.py` itself:
   `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` added 15 new keys to `FAST_ANCHOR_KEYS` (lines 59-74) in the
   same commit that added them to `grade_anchors.json`. A workflow that only touches the JSON file would
   silently leave new anchors unenforced by the regression test — a real drift risk this ticket exists to
   close.
8. **Run the regression test to confirm the new anchors are self-consistent**:
   `pytest tests/simulation_quality/test_grade_regression.py -m "not slow"` (fast tier) and, for slow-tier
   changes, the full file (`-m` filter omitted) or explicitly the `SLOW_ANCHOR_KEYS`-parametrized tests.
9. **Update `docs/simulation_quality/eval_matrix_results.md`**: refresh/add per-world grade tables
   (per tick-count, per-seed), append a dated `> **NOTE (...)**` callout block explaining *why* grades
   moved (formula fix / content recompile / feature activation), update the "Corpus before/after" counts
   table, update "Newly-Anchored Worlds" section for new worlds, update DA/design-note sections
   (e.g. "AGENCY — Cross-World Design Note") when a zero-pillar finding is reclassified as archetype-correct
   rather than a gap.
10. **Update `docs/audits/D20_simq_integration.md`**:
    - Frontmatter/Dimension Profile `State` and `Audit date` fields (append new date + one-line summary).
    - Add a new `## SimQ Uplift Batch N (...)` section: table of tickets in the batch, what changed, outcome.
    - Update the batch's "Grade distribution" table (S/A/B/C counts per pillar across all calibration runs).
    - Resolve/append "Open follow-up work" bullet list — strike through resolved items with a pointer to
      the ticket that closed them, add any new follow-ups the batch surfaced.
    - Update "Module Health" table rows for any component whose status changed (e.g. "Calibration corpus"
      row's run-count and world list).
11. **Update `docs/simulation_quality/event_type_coverage.md`** when calibration surfaced new
    `calibration_hits` counts for previously-zero event emitters (not touched in every batch — only when
    emitter activity changed, e.g. Batch 1's `progression_plateau_detected` count, Batch 2's
    `belief_assimilated`/`diplomatic_transition` counts).
12. **Check `docs/parity_ledger/*.yaml` for staleness** — search for entries whose `divergence_note`/
    `v2_evidence` references the SimQ subsystem or the specific tickets in the batch; update `status`,
    `v2_evidence`, or `divergence_note` if the underlying behavior changed. Confirmed pattern: `SOC-237`,
    `SOC-238` (`social_narrative.yaml`), `INFRA-251`, `INFRA-258` (`infrastructure.yaml`) were all added or
    edited in lockstep with a SimQ batch. New entries get the next available ID for the file's prefix.
13. **(Conditional) Update `docs/guidelines/v2_intentional_divergences.md`** when a batch produces a DA
    (design-acknowledged) decision — e.g. `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`'s "AGENCY=C is
    archetype-correct" ruling, `TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG`'s ECONOMY/COGNITION ruling.
14. **(Conditional) File a follow-up ticket** rather than silently marking something verified, when the
    audit surfaces an unrelated, out-of-scope defect (e.g. `33cf044d`'s `ResourceRegistry: STONE` crash →
    `TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP`). This is a judgment call, not mechanical.
15. **Stage and commit** — `agent-monitoring/tools.jsonl` always included; commit message references the
    driving ticket ID(s). Some historical doc-sync passes were committed as plain `chore:` commits with
    **no ticket ID at all** (`79ba7d05`, `cf53674c`, `85922428`) — i.e. not every doc-sync pass in this
    repo's history went through the full ticket-workflow ceremony. This matters for the design decision
    below (§3).

### 1.2 Files touched, by step

| File | Touched when |
|---|---|
| `data/calibration/{run_key}/quality_report.json` | Every calibration run (step 3) — reproducible, not committed to git (verify: not tracked) |
| `tests/simulation_quality/fixtures/grade_anchors.json` | Any classified-expected grade movement or new anchor key (step 6) |
| `tests/simulation_quality/test_grade_regression.py` | Any *new* run_key added to the anchor file (step 7) — commonly missed |
| `docs/simulation_quality/eval_matrix_results.md` | Every batch with a calibration-visible outcome (step 9) |
| `docs/audits/D20_simq_integration.md` | Every batch (step 10) — the canonical "what happened" record |
| `docs/simulation_quality/event_type_coverage.md` | Only when emitter coverage/hit-counts changed (step 11) |
| `docs/parity_ledger/*.yaml` | Any batch touching a subsystem with an existing or new-worthy parity entry (step 12) |
| `docs/guidelines/v2_intentional_divergences.md` | Only when a new DA/archetype ruling is made (step 13) |
| `agent-monitoring/tools.jsonl` | Every commit (project-wide rule, not SimQ-specific) |

Confirmed **not** part of the calibration data itself: `data/calibration/` is not `git`-tracked (verified:
no `data/calibration/*` paths appear in any of the 15 commits' file lists above) — only the *anchor*
JSON (`grade_anchors.json`) and docs are committed. This means a future audit run always needs step 3
(regenerate the calibration reports locally) before step 4 can diff anything — `data/calibration/` is
ephemeral working data, matching the repo's `data/runs/` cleanup convention.

### 1.3 Mechanical vs. judgment classification

| Step | Mechanical | Judgment |
|---|---|---|
| 2. Recompile stale worlds | Mechanical (given a list of affected worlds) | Deciding *which* worlds are stale requires reading module/content diffs |
| 3. Run calibration matrix | Fully mechanical | — |
| 4. Diff vs anchors (`evaluate_simq.py`) | Fully mechanical | — |
| 5. Classify drift (expected vs regression) | — | Fully judgment |
| 6. Update `grade_anchors.json` | Mechanical (once step 5 decided) | — |
| 7. Update `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` | Mechanical (once new keys known) | — |
| 8. Run regression test | Fully mechanical | — |
| 9-10. Update `eval_matrix_results.md` / `D20_simq_integration.md` | — | Fully judgment (narrative synthesis, table authoring) |
| 11. Update `event_type_coverage.md` | Partially mechanical (hit counts) | Deciding significance |
| 12. Parity ledger staleness check | Partially mechanical (grep for SimQ-tagged entries) | Deciding what changed and updating notes |
| 13. Intentional divergences doc | — | Fully judgment |
| 14. File follow-up ticket for out-of-scope findings | — | Fully judgment |

This split is the load-bearing fact for the design decision in §3: **the mechanical steps (2-4, 6-8) are
cleanly scriptable and have zero ambiguity; the doc-authoring and classification steps (5, 9-14) require
reading recent history and writing coherent narrative prose** — exactly the kind of task this repo already
delegates to an `agent()` phase with a schema-validated return, not to a shell script.

---

## 2. Mechanics/Engine Constraints

- `tools/calibrate_simq.py` and `tools/evaluate_simq.py` are read/decision-support tooling — they do not
  mutate durable simulation state; they replay committed `simulation_events.jsonl` through `QualityHub`
  offline. No architecture-boundary risk from invoking them more often or in a new wrapper.
- `docs/parity_ledger/schema.json` governs the required fields for any new/edited parity entry (`id`,
  `text`, `status`, `priority`, `v2_evidence`, `test_path`, `divergence_note`) — any workflow phase that
  touches the ledger must preserve this schema.
- No Mechanics Bible chapter governs the audit *process* itself (it's tooling/observability, not
  simulation law) — `docs/simulation_quality/quality_scoring_contract.md` is the closest authoritative
  doc (scoring formulas, pillar definitions) and should be read, not edited, by this workflow unless a
  scoring bug is found (out of scope per the ticket).

## 3. Design Decision — (c): both, with the make target embedded as the workflow's mechanical phase

**Recommendation: build both — `make simq-full-audit` (mechanical parts only) AND
`.claude/workflows/simq-audit.js` + `.claude/skills/simq-audit/SKILL.md` (full orchestration, calling the
make target internally for its mechanical phase).**

Reasoning:

1. **The mechanical/judgment split in §1.3 is real and clean** — steps 2-4 and 6-8 have zero ambiguity and
   no benefit from an LLM in the loop; wrapping them in `agent()` calls (as the ticket's Related Docs
   hints at "(a) mirror implement-ticket.js") would burn tokens on tasks a shell script does deterministically
   and faster. Conversely, steps 5 and 9-14 are narrative synthesis and judgment that this repo already
   handles via schema-validated `agent()` phases in `implement-ticket.js` — there is no shell-scriptable
   substitute for "write the paragraph explaining why FACTION moved C→A and cross-reference the ticket."
2. **A pure make target (option b alone) is insufficient** per the ticket's own explicit acceptance
   criteria — item 4 requires the workflow to "produce the same kind of output this session produced by
   hand" for docs, and item 5 requires it to be discoverable/usable without re-deriving the process. A
   make target that only re-runs calibration and diffs anchors does not touch a single doc file — a future
   session would still have to re-derive steps 9-14 from scratch, defeating the ticket's purpose.
3. **A pure agent workflow (option a alone) without a make target is also worse than (c)**: it would
   either (i) inline the mechanical bash commands directly into agent prompts (works, but then the
   commands live only inside a JS string with no standalone entry point a human/CI can run without
   invoking Claude Code at all), or (ii) require the agent to remember to run 5+ separate commands in the
   right order every time. Recorded history shows exactly this kind of step-skipping is what created this
   ticket in the first place (step 7 — updating `FAST_ANCHOR_KEYS` — was never written down anywhere and
   was only caught by reading the test file directly). Codifying the mechanical sequence as one
   `make` target removes that failure mode permanently, independent of whether an agent or a human invokes it.
4. **This mirrors an existing repo precedent**: `implement-ticket.js`'s Test phase does not reimplement
   pytest-scoping logic in JS — it delegates to a `test-scoper` agent that runs a real `pytest` invocation
   via Bash and reports structured results back. The same shape applies here: the workflow's mechanical
   phase should shell out to one make target and parse/relay its output, not reimplement calibration
   orchestration in JS.
5. **Historical evidence that not every audit pass needs the full ticket ceremony** (§1.1 step 15 — three
   `chore:` commits with no ticket ID) suggests the *workflow* should be invocable standalone (as its own
   `/simq-audit` skill), not folded into `implement-ticket.js`'s tier system. A future session should be
   able to run "audit SimQ state" on its own cadence, independent of whether a specific ticket is open.

### What the make target should NOT try to do

Do not attempt to script steps 5, 9-14 as shell/Python logic (e.g. templated markdown generation from a
diff). Every historical doc update in D20/eval_matrix_results.md contains attributed, evidence-specific
prose ("was A pre-recompile; hazard-kind fix to `old_mine_resource_loop` changed `old_mine_spider_cluster`
survival dynamics") that a template cannot produce without already knowing the root cause — which is
exactly the investigation work an agent phase does.

---

## 4. Proposed `make simq-full-audit` target (mechanical phase)

```makefile
simq-full-audit: ## Mechanical SimQ audit: re-run fast calibration matrix, diff vs anchors, run regression tests, flag corpus/parity gaps
	@echo "[simq-full-audit] Step 1/4: diff current calibration data against anchors (no engine re-run)"
	-$(PYTHON) tools/evaluate_simq.py --dry-run
	@echo "[simq-full-audit] Step 2/4: run fast-tier grade regression tests"
	$(PYTHON) -m pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q
	@echo "[simq-full-audit] Step 3/4: cross-check anchor keys vs FAST_ANCHOR_KEYS/SLOW_ANCHOR_KEYS coverage"
	$(PYTHON) tools/simq_audit_gaps.py
	@echo "[simq-full-audit] Step 4/4: done. See output above for REGRESS rows, uncovered anchor keys, and any parity/doc staleness flags."

simq-full-audit-full: ## Same as simq-full-audit but re-runs the engine for all fast scenarios first (slower, authoritative)
	$(PYTHON) tools/evaluate_simq.py
	$(PYTHON) -m pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q
	$(PYTHON) tools/simq_audit_gaps.py

simq-full-audit-slow: ## Slow-tier (1000t/2000t) regression check — run after simq-full-audit passes
	$(PYTHON) -m pytest tests/simulation_quality/test_grade_regression.py -q
```

**New small tool required: `tools/simq_audit_gaps.py`** (does not exist yet — net-new, ~80-120 lines).
Purely mechanical cross-checks that were, until now, done by eyeballing files:
1. Load `tests/simulation_quality/fixtures/grade_anchors.json` keys (excluding `_note`/`_instructions`/
   `_grade_order`), and `FAST_ANCHOR_KEYS` + `SLOW_ANCHOR_KEYS` from `test_grade_regression.py` (import
   the module directly — same technique `evaluate_simq.py::_run_calibration` already uses for
   `tools.calibrate_simq`). Print any anchor key present in the JSON but absent from both lists
   ("UNCOVERED — regression test will never check this key").
2. Grep `docs/parity_ledger/*.yaml` for entries whose `text`/`divergence_note` mention `SimQ`,
   `calibrat`, `QualityHub`, or any pillar scorer name, and print their `status` + last-touched-looking
   evidence string, so the agent's Parity-Check phase has a ready-made candidate list instead of
   re-scanning ~4000 lines of YAML from scratch.
3. Exit code 0 always (this is an informational gap-finder, not a pass/fail gate — the pytest step above
   is the gate).

This keeps the make target itself trivial (three tool invocations) and puts the one piece of genuinely
new logic in a small, testable Python file rather than Makefile shell scripting.

---

## 5. Proposed `.claude/workflows/simq-audit.js` phase structure

Mirrors `implement-ticket.js`'s `phase()`/`agent()`/`pushEvent()`/`writeMonitoring()` machinery exactly
(same monitoring contract, same schema-validated `agent()` calls). Args: `{ mode?, worlds? }` where
`mode` is `'fast'` (default, dry-run diff only) or `'full'` (re-run engine first) or `'slow'` (include
1000t/2000t tier); `worlds` optionally restricts the mechanical phase to specific `--name` values.

```js
export const meta = {
  name: 'simq-audit',
  description: 'Refresh SimQ calibration corpus, diff against grade anchors, classify drift, sync D20/eval-matrix/parity docs',
  phases: [
    { title: 'Recalibrate', detail: 'Run make simq-full-audit (mechanical): calibration diff, regression tests, corpus/parity gap scan' },
    { title: 'Classify Drift', detail: 'For each REGRESS/new/uncovered key, decide expected-drift vs genuine-regression vs needs-follow-up-ticket' },
    { title: 'Update Anchors', detail: 'Edit grade_anchors.json + FAST_ANCHOR_KEYS/SLOW_ANCHOR_KEYS for classified-expected movements; re-run regression tests as a gate' },
    { title: 'Sync Docs', detail: 'Update eval_matrix_results.md, D20_simq_integration.md, event_type_coverage.md (if hit-counts changed), v2_intentional_divergences.md (if new DA ruling)' },
    { title: 'Parity Check', detail: 'Update docs/parity_ledger/*.yaml entries flagged by simq_audit_gaps.py; add new entries for newly-verified behavior' },
    { title: 'Verify', detail: 'Confirm: regression tests pass, every REGRESS is either fixed/explained/ticketed, no doc left stale' },
    { title: 'Report', detail: 'Summarize batch outcome; list any new follow-up tickets filed' },
  ],
}
```

Phase-by-phase behavior:

1. **Recalibrate** (no `agent()` — direct `Bash` call, same as any tool-invocation step in existing
   workflows): run `make simq-full-audit` (or `-full`/`-slow` per `mode`). Capture stdout: REGRESS rows,
   UNCOVERED anchor keys, candidate stale parity entries. This is the workflow's only non-agent phase —
   it is pure mechanical delegation to §4's make target, consistent with how `implement-ticket.js`'s Test
   phase runs pytest directly via the `test-scoper` agent's Bash tool rather than reimplementing test
   discovery in JS.

2. **Classify Drift** — `agent()` call, schema: `{ classifications: [{run_key, pillar, verdict: EXPECTED_DRIFT|REGRESSION|UNCOVERED_KEY, cause, ticket_needed: bool}], summary, ts }`. Prompt gives it the Recalibrate
   phase's raw output plus instructions to check `tickets/done/` (recent SimQ tickets) and `git log
   --oneline -20` for correlated recent changes, mirroring step 5's actual historical practice. If any
   `verdict == REGRESSION` with `ticket_needed == true` and no existing ticket reference, this phase
   creates a `tickets/inprogress/TCK-...` scoping stub (ticket-scoper role) rather than silently proceeding
   — matches the historical `TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP` precedent (§1.1 step 14).

3. **Update Anchors** — `agent()` edits `grade_anchors.json` for `EXPECTED_DRIFT` keys and
   `test_grade_regression.py`'s key lists for genuinely new run_keys, then re-runs
   `pytest tests/simulation_quality/test_grade_regression.py -m "not slow"` (gate: non-zero exit →
   `ANCHORS_STILL_FAILING`, return early like `implement-ticket.js`'s `TESTS_FAILED` gate).

4. **Sync Docs** — `agent()`, no schema validation needed beyond files-changed list; writes the dated
   `> **NOTE (...)**` callout + grade tables in `eval_matrix_results.md`, the new
   `## SimQ Uplift Batch N` section + Dimension Profile date + Module Health rows in
   `D20_simq_integration.md`, and conditionally `event_type_coverage.md` /
   `v2_intentional_divergences.md`.

5. **Parity Check** — `agent()`, reuses the exact prompt shape of `implement-ticket.js`'s Parity phase
   (same rules: verified/divergent/missing status semantics, P0 test_path requirement), seeded with the
   candidate list from `simq_audit_gaps.py`.

6. **Verify** — schema-validated `agent()` DoD-style check: regression tests pass, every REGRESS
   accounted for (fixed, explained-as-drift, or ticketed), Recalibrate-phase UNCOVERED keys are now zero.

7. **Report** — plain summary, same shape as `implement-epic.js`'s Report phase; write monitoring records
   (`record_run.py`/`record_events.py`, `workflow: "simq-audit"`) exactly as `implement-ticket.js` does —
   this workflow is a new `workflow` value, agent-monitoring's existing schema already supports arbitrary
   workflow name strings (verify: `record_run.py --data` takes freeform `workflow` field, confirmed by
   reading its call sites in both existing workflow files — no schema change needed there).

Skill wrapper: `.claude/skills/simq-audit/SKILL.md`, following `implement-ticket/SKILL.md`'s exact
translation-table pattern (`phase()`→announce, `agent()`→spawn+validate, gate→check+writeMonitoring+stop).
Usage: `/simq-audit`, `/simq-audit mode=full`, `/simq-audit mode=slow`.

## 6. Prior Work

- `TCK-20260702-SIMQ-EVAL-MATRIX` (done) — built the multi-seed/multi-tick corpus this workflow audits;
  its own `investigation.md` documents the corpus-refresh pattern in miniature (single ticket, not yet
  formalized as a standing tool).
- `TCK-20260701-SIMQ-CALIBRATE-REFRESH`, `TCK-20260701-SIMQ-LOOP-WINDOW-TUNE` — established
  `calibrate_simq.py`'s `--window-size`/`--loop-threshold` CLI override pattern this investigation reused
  as precedent for "run-scoped override, no YAML mutation" (same principle §4's tool should follow: no
  destructive edits without an explicit agent decision).
- `implement-ticket.js` / `implement-epic.js` — direct structural precedent for §5's design; `implement-epic.js`'s
  `folder`/`epic_id` discovery pattern is not reused here (this workflow isn't ticket-driven by default),
  but its "stop on first gate failure, resumable" pattern for the Update Anchors gate is.

## 7. Risks and Open Questions

- **Open question requiring a human/process decision** (the ticket explicitly flags this as needing
  architecture-review-level judgment, so it is surfaced rather than silently decided):
  Should every invocation of `simq-audit` require its own ticket (full standard-tier ticket-workflow
  ceremony), or should routine no-regression audit passes be allowed to land as lightweight `chore:`
  commits (as 3 of the 15 historical doc-sync commits actually did — `79ba7d05`, `cf53674c`, `85922428`),
  reserving full ticket treatment only for passes that surface a genuine regression or new DA decision?
  This investigation's recommendation (§3, §5) assumes the latter — the workflow is invocable standalone
  via its own skill, and only spawns a ticket when Classify Drift finds a `REGRESSION` needing follow-up —
  but this is a governance choice about ticket-workflow discipline (CLAUDE.md's Hard Rules), not a
  technical one, and should be confirmed by whoever reviews this plan rather than assumed by the
  implementer.
- **Anti-drift hazard**: if a future scoring-formula change (like the D2 grade-decay fix) invalidates a
  large fraction of anchors at once, the Classify Drift phase's default heuristic (correlate against
  recent `git log`) could over-attribute unrelated regressions to the same recent change. The phase
  prompt should require it to cite the *specific* commit/ticket for each `EXPECTED_DRIFT` classification,
  not just "matches the pattern of a recent change" — mirroring how every historical D20 update names the
  exact ticket and mechanism for every grade movement (never just "grades changed").
- **`data/calibration/` is not git-tracked** (confirmed §1.2) — the workflow's Recalibrate phase must
  actually execute calibration runs locally before diffing; it cannot assume committed data is present.
  This makes `mode=fast` (dry-run only, no engine re-run) require that calibration reports already exist
  from a very recent local run — first-time invocation in a fresh checkout should default to `mode=full`
  or clearly warn when `data/calibration/` is empty/stale, similar to `evaluate_simq.py --dry-run`'s
  existing `WARNING: no calibration report ... — skipping` behavior (verified present at
  `tools/evaluate_simq.py:171`).

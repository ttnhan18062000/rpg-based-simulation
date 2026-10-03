# TCK-20260703-SIMQ-UPLIFT3-AUDIT-WORKFLOW — Implementation Plan

**Date:** 2026-07-04
**Ticket:** TCK-20260703-SIMQ-UPLIFT3-AUDIT-WORKFLOW
**Phase:** Plan (seq 3)

Design basis: investigation.md §3 recommendation **(c)** — a `make simq-full-audit` target (+ new
`tools/simq_audit_gaps.py`) for the zero-ambiguity mechanical steps, plus a full
`.claude/workflows/simq-audit.js` + `.claude/skills/simq-audit/SKILL.md` agent-orchestrated pass for
the judgment steps, mirroring `implement-ticket.js`'s exact `phase()`/`agent()`/schema/`writeMonitoring`
pattern. Not re-litigated here.

## Governance Decision (given — encoded, not re-decided)

The investigation's §7 open question ("does every `simq-audit` run need a full ticket, or can routine
no-regression passes land as lightweight `chore:` commits?") is **resolved**: adopt the lighter-weight
path.

- The workflow is invocable **standalone** — it does not require an open ticket to run, and by default
  does not create one.
- **Classify Drift** (phase 2) produces a top-level rollup `verdict` field:
  `"no_regression" | "regression" | "needs_da_decision"`.
  - `no_regression`: every flagged delta/uncovered-key/parity-staleness item was classified
    `EXPECTED_DRIFT` (attributable to an already-landed, named change) with **no** `REGRESSION` or
    `DA_NEEDED` items. Downstream phases proceed to sync anchors/docs, and the **Report** phase (phase 7)
    emits a lightweight chore-style summary + a suggested `chore: SimQ audit <date> — <N> anchors
    refreshed, no regressions` commit message. No `tickets/inprogress/TCK-*.md` is created. This mirrors
    the historical `79ba7d05`/`cf53674c`/`85922428` precedent (3 of 15 historical doc-sync passes landed
    with no ticket ID).
  - `regression` or `needs_da_decision`: at least one item was classified `REGRESSION` (unexplained grade
    drop, no known cause) or `DA_NEEDED` (a design-acknowledged ruling is required, e.g. an
    archetype-correctness call like the AGENCY=C precedent). The workflow does **not** attempt to fix the
    regression or make the DA ruling itself. It spawns a ticket via the same `ticket-scoper` role and
    `TICKET_SCHEMA` shape `implement-ticket.js`'s Scope phase uses (agent prompt population differs: pre-seeded
    with the specific run_key/pillar/cause found by Classify Drift instead of a free-text `request`), and the
    Report phase tells the caller to continue with
    `/implement-ticket ticket_id=<new-id>` rather than silently proceeding.
- This governance choice does **not** change anything about *when docs/anchors get updated* — Update
  Anchors and Sync Docs still run for every `EXPECTED_DRIFT`-classified item regardless of the overall
  verdict. It only changes *how the change is finalized*: direct chore commit vs. full ticket workflow
  hand-off for the un-resolved items.
- Items classified `REGRESSION`/`DA_NEEDED` are deliberately **not** anchor-edited (their
  `grade_anchors.json` value is left as-is) so the regression test continues to fail/flag them until the
  spawned ticket resolves them — anchors must never be silently updated to paper over an unexplained
  regression.

No other item in investigation.md's §7 is a genuinely open human-decision question — the anti-drift
citation requirement and the `data/calibration/` non-tracked-data handling are both resolved by design
below (steps 3, 5).

---

## Step List

### Step 1 — `tools/simq_audit_gaps.py` (new file)

**Files:** `tools/simq_audit_gaps.py` (new, ~100-130 lines)

Read-only, informational, always exits 0 (per investigation §4 point 3 and test_plan.md's
`test_exit_code_always_zero`). Three responsibilities:

1. **Anchor coverage scan.**
   - `load_anchor_keys(path=Path("tests/simulation_quality/fixtures/grade_anchors.json")) -> list[str]`:
     load JSON, return keys excluding `_note`, `_instructions`, `_grade_order` (confirmed these are the
     only non-run-key top-level keys — verified: `grade_anchors.json` has 43 top-level keys, 3 are these
     meta keys, 40 are real run keys).
   - Import `FAST_ANCHOR_KEYS` / `SLOW_ANCHOR_KEYS` directly from
     `tests.simulation_quality.test_grade_regression` (verified importable: both `tests/__init__.py` and
     `tests/simulation_quality/__init__.py` exist, so `sys.path.insert(0, <repo root>)` +
     `import tests.simulation_quality.test_grade_regression as tgr` works standalone, same technique
     `evaluate_simq.py:66` already uses for `tools.calibrate_simq`).
   - `find_uncovered_anchor_keys(anchor_keys, fast_keys, slow_keys) -> list[str]`: pure set-difference
     logic — every anchor key not present in `set(fast_keys) | set(slow_keys)`.
   - Verified current state (2026-07-04): 40 real anchor keys, `len(FAST_ANCHOR_KEYS)==29`,
     `len(SLOW_ANCHOR_KEYS)==11`, `29+11==40` — **zero uncovered keys today**. This is the expected
     baseline for the Step 6 dry-run (the WORLD-CORPUS ticket already closed the gap this tool guards
     against; the tool's job is to catch the *next* time it happens).
2. **Parity ledger candidate scan.**
   - `scan_parity_ledger_candidates(ledger_dir=Path("docs/parity_ledger")) -> list[dict]`: parse each
     `*.yaml` file with `yaml.safe_load` (list of entry dicts per `schema.json`), and for each entry check
     `text`, `divergence_note`, `v2_evidence` (case-insensitive) for any of: `simq`, `calibrat`,
     `qualityhub`, or a pillar name — `AGENCY`, `COMBAT`, `COGNITION`, `ECONOMY`, `FACTION`,
     `INFORMATION`, `NARRATIVE`, `SOCIAL`, `WORLD` (confirmed exhaustive list from
     `src/simulation_quality/pillars.py::PillarId`). Entry-level matching only — **do not** whole-file
     grep (a whole-file grep matches nearly every parity file since most mention "SimQ" somewhere; the
     tool must scope to individual entries so the candidate list is actually short and useful).
   - Return each match as `{id, file, status, divergence_note_excerpt}`.
   - Verified this design surfaces the four known candidates: `SOC-237`, `SOC-238` (in
     `social_narrative.yaml`), `INFRA-251`, `INFRA-258` (in `infrastructure.yaml`) — confirmed present with
     SimQ-referencing `divergence_note` text as of this session.
3. **CLI entry point** (`if __name__ == "__main__":`): print two sections — `UNCOVERED ANCHOR KEYS`
   (empty-list case prints `"None — all N anchor keys covered."`) and `PARITY LEDGER CANDIDATES`
   (grouped by file). Always `sys.exit(0)`.

**Scope guard:** this script must never write to `grade_anchors.json`, `test_grade_regression.py`, or any
`docs/parity_ledger/*.yaml` file — read-only by construction (no `open(..., "w")` anywhere in the file).

**Verification:** `tests/unit/tools/test_simq_audit_gaps.py` (Step 2) exercises this directly.

### Step 2 — `tests/unit/tools/test_simq_audit_gaps.py` (new file)

**Files:** `tests/unit/tools/test_simq_audit_gaps.py` (new), `tests/unit/tools/__init__.py` (new, if the
directory doesn't already exist as a package — check first)

Implements the four tests test_plan.md specifies:
- `test_flags_uncovered_anchor_key` — synthetic fixture dict with a key absent from both lists →
  reported uncovered.
- `test_no_false_positive_for_covered_keys` — run `find_uncovered_anchor_keys` against the **real**
  `tests/simulation_quality/fixtures/grade_anchors.json` + real `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` →
  assert empty list. This is the live regression guard the whole ticket exists to add.
- `test_parity_ledger_candidate_scan_finds_known_entries` — run `scan_parity_ledger_candidates` against
  the real `docs/parity_ledger/` → assert `SOC-237`, `SOC-238`, `INFRA-251`, `INFRA-258` all present in
  the returned IDs.
- `test_exit_code_always_zero` — invoke the CLI entry point as a subprocess (or call `main()` directly if
  refactored to return instead of exit) and assert exit code 0 even when uncovered keys are injected via a
  monkeypatched fixture path.

**Dependency:** requires Step 1 complete first (imports the module under test).

**Verification:**
`python3 -m pytest tests/unit/tools/test_simq_audit_gaps.py -q`

### Step 3 — `Makefile` target `simq-full-audit` (+ `-full` / `-slow` variants)

**Files:** `Makefile`

Add three targets adjacent to the existing `evaluate`/`evaluate-full` targets (~line 286-290), following
their exact `$(PYTHON)` invocation style and `.PHONY` list update at line 1:

```makefile
simq-full-audit: ## Mechanical SimQ audit: diff calibration vs anchors, run fast regression tests, scan anchor/parity coverage gaps
	@echo "[simq-full-audit] Step 1/3: diff current calibration data against anchors (no engine re-run)"
	-$(PYTHON) tools/evaluate_simq.py --dry-run
	@echo "[simq-full-audit] Step 2/3: run fast-tier grade regression tests"
	$(PYTHON) -m pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q; test_status=$$?; \
	echo "[simq-full-audit] Step 3/3: cross-check anchor key coverage + parity ledger candidates"; \
	$(PYTHON) tools/simq_audit_gaps.py; \
	exit $$test_status

simq-full-audit-full: ## Same as simq-full-audit but re-runs the engine for all fast (<=500t) scenarios first
	-$(PYTHON) tools/evaluate_simq.py
	$(PYTHON) -m pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q; test_status=$$?; \
	$(PYTHON) tools/simq_audit_gaps.py; \
	exit $$test_status

simq-full-audit-slow: ## Slow-tier (1000t/2000t) regression check -- run after simq-full-audit passes
	$(PYTHON) -m pytest tests/simulation_quality/test_grade_regression.py -q
```

Leading `-` on the `evaluate_simq.py --dry-run`/`evaluate_simq.py` lines only (not the pytest lines) matches
this Makefile's existing convention for the one genuinely non-fatal, decision-support step whose output the
*next* step interprets — confirmed by checking how `evaluate`/`evaluate-full` already invoke
`tools/evaluate_simq.py` with no leading dash at all (`Makefile:286-290`) and by confirming
`grep -n '^\t-' Makefile` returns **zero matches** anywhere in the current Makefile — there is no
"non-fatal step" convention for the pytest regression-test line, and the `evaluate`/`evaluate-full` targets
do not dash their pytest-equivalent step either. The pytest line is therefore written as a normal, fatal
shell command: its exit code is captured explicitly as `test_status`, `simq_audit_gaps.py` still runs
afterward for diagnostic purposes (so the coverage/parity scan output is always available even when the
regression test fails), and the recipe's final `exit $$test_status` ensures the overall target still returns
non-zero when the regression test failed — a bare trailing dash on the pytest line would have silently
defeated this gate (since `simq_audit_gaps.py` always exits 0 by design, a dashed pytest line ahead of it
would mean `make simq-full-audit`/`-full` could never report failure). `simq-full-audit-slow` has no
subsequent step, so its pytest line needs no exit-code capture — it is left as a plain, fatal command whose
own exit code is `make`'s exit code. Add all three target names to the `.PHONY:` line.

**Scope guard:** do not add engine re-run logic, scoring changes, or anything beyond shelling out to the
three existing/new tools above — this target is intentionally "dumb" (investigation §4's explicit
constraint).

**Dependency:** the `-full`/base targets depend on Step 1 (`simq_audit_gaps.py` must exist).

**Verification:** `make simq-full-audit` runs to completion (exit 0) — this is also Step 6's smoke test.

### Step 4 — `.claude/workflows/simq-audit.js` (new file)

**Files:** `.claude/workflows/simq-audit.js` (new)

Mirror `implement-ticket.js`'s exact machinery: `export const meta = { name, description, phases: [...] }`
at top, `phase(...)`/`log(...)`/`agent(prompt, opts)`/`pushEvent(...)`/`writeMonitoring(finalStatus)`
calls, JSON-schema-validated `agent()` returns for phases whose output downstream logic branches on,
plain-text `PHASE_TS:`-prefixed `agent()` returns for phases that are narrative-only (same split
`implement-ticket.js` uses: Scope/Review/Test/Verify are schema-validated; Investigate/Plan/Parity are
plain-text).

```js
export const meta = {
  name: 'simq-audit',
  description: 'Refresh SimQ calibration corpus, diff against grade anchors, classify drift, sync docs/parity, and finalize via chore-commit or ticket hand-off',
  phases: [
    { title: 'Recalibrate', detail: 'Run make simq-full-audit (or -full/-slow per mode) -- mechanical calibration diff, regression tests, coverage scan' },
    { title: 'Classify Drift', detail: 'Classify each REGRESS/UNCOVERED/parity-candidate item as EXPECTED_DRIFT, REGRESSION, or DA_NEEDED; compute rollup verdict' },
    { title: 'Update Anchors', detail: 'Edit grade_anchors.json + FAST_ANCHOR_KEYS/SLOW_ANCHOR_KEYS for EXPECTED_DRIFT items only; re-run regression tests as a gate' },
    { title: 'Sync Docs', detail: 'Update eval_matrix_results.md, D20_simq_integration.md, event_type_coverage.md (if hit-counts changed), v2_intentional_divergences.md (if DA ruling)' },
    { title: 'Parity Check', detail: 'Update docs/parity_ledger/*.yaml entries flagged by simq_audit_gaps.py candidates' },
    { title: 'Verify', detail: 'Confirm regression tests pass and every REGRESS/DA item is accounted for (fixed, explained, or ticketed)' },
    { title: 'Report', detail: 'Branch on verdict: no_regression -> chore-commit-message suggestion; regression/needs_da_decision -> spawn ticket + hand-off instruction' },
  ],
}

// Args: { mode?, worlds? }
// mode: 'fast' (default; --dry-run diff only, assumes data/calibration/ already populated),
//       'full' (re-run engine for fast scenarios first), 'slow' (also run 1000t/2000t tier).
// worlds: optional comma-separated list to scope calibration re-runs (mode=full only).
```

Phase-by-phase (full detail; implementer follows this, does not re-derive from investigation.md alone):

1. **Recalibrate** — `agent()` call, plain-text (`PHASE_TS:`-prefixed), **no schema, no `agentType`** —
   the same lightweight shape `implement-ticket.js`'s own `writeMonitoring` function uses for its
   `agent()` call (`{ label: 'monitoring-write' }`, no schema, no `agentType`). This is required, not
   optional: every `Step 0`/`Step 0b` bash call in `implement-ticket.js` runs *inside* an `agent()`
   prompt, executed by the spawned agent — no workflow file in this repo has the orchestrator shell out
   to an external command directly. The tool-call-count sidecar (`.claude/current_run`) only records
   tool calls an agent makes; a bare orchestrator `Bash` call would leave Recalibrate's `tool_call_count`
   at 0/null, unlike every schema-validated or plain-text phase in the pipeline.

   `Step 0b` (tool-tracking registration) is intentionally **omitted** here, mirroring
   `implement-ticket.js`'s own Scope/ticket-creation `agent()` call (lines 63-105 of `implement-ticket.js`),
   which also has no `Step 0b` — for the same reason: this workflow's synthetic `run_id`
   (`SIMQ-AUDIT-<ts>`) is *derived from* this phase's own `Step 0` timestamp, so no `run_id` exists yet to
   register against when the prompt is constructed. Every later phase (Classify Drift onward) does include
   `Step 0b` once `runId` is known, same as `implement-ticket.js`'s post-Scope phases.

   ```js
   phase('Recalibrate')

   const mode = (args && args.mode) || 'fast'

   const recalOutput = await agent(
     `Run the mechanical SimQ audit and report the raw results verbatim.

   Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\`. Your response MUST begin with this exact line (nothing before it):
   PHASE_TS: <result>

   Mode: ${mode}

   - If mode is 'fast' (default): check whether data/calibration/ is empty or every quality_report.json
     is >24h stale. If so, log a warning and escalate to mode=full for this run (a fresh checkout must
     not silently diff against nothing — per investigation §7's anti-drift-hazard resolution). Otherwise
     run: make simq-full-audit
   - If mode is 'full': run: make simq-full-audit-full
   - If mode is 'slow': run: make simq-full-audit && make simq-full-audit-slow

   Run the chosen command via Bash. Capture the full stdout and the exit code. Report the exit code, then
   the complete stdout verbatim below the PHASE_TS line — REGRESS rows, pytest pass/fail counts, the
   UNCOVERED ANCHOR KEYS section, and the PARITY LEDGER CANDIDATES section. Do not summarize or truncate;
   Classify Drift needs the full detail.`,
     { label: 'recalibrate' }
   )

   const recalTs = recalOutput.toString().match(/^PHASE_TS: (\S+)/m)?.[1] || null
   const recalText = recalOutput.toString().replace(/^PHASE_TS: \S+\n?/, '').trim()
   pushEvent('Recalibrate', 'workflow', 'ok', recalText.slice(0, 200), recalTs)
   ```

2. **Classify Drift** — `agent()`, schema-validated:
   ```js
   const CLASSIFY_SCHEMA = {
     type: 'object',
     required: ['classifications', 'verdict', 'summary', 'ts'],
     properties: {
       classifications: {
         type: 'array',
         items: {
           type: 'object',
           required: ['item', 'kind', 'classification', 'cause'],
           properties: {
             item: { type: 'string', description: 'run_key+pillar, anchor key, or parity entry ID' },
             kind: { type: 'string', enum: ['GRADE_DELTA', 'UNCOVERED_ANCHOR_KEY', 'PARITY_CANDIDATE'] },
             classification: { type: 'string', enum: ['EXPECTED_DRIFT', 'REGRESSION', 'DA_NEEDED', 'NO_ACTION'] },
             cause: { type: 'string', description: 'Specific commit/ticket ID this traces to -- never "matches a recent pattern"' },
           },
         },
       },
       verdict: { type: 'string', enum: ['no_regression', 'regression', 'needs_da_decision'] },
       summary: { type: 'string' },
       ts: { type: 'string' },
     },
   }
   ```
   Prompt: give the agent `recalOutput` verbatim, plus instructions to run `git log --oneline -20` and
   check `tickets/done/` for recent SimQ tickets to correlate causes (mirrors historical practice per
   investigation §1.1 step 5). **Require a specific commit/ticket ID per `EXPECTED_DRIFT` item** —
   investigation §7's anti-drift-hazard guard, enforced via the `cause` field description plus an explicit
   instruction sentence in the prompt, not by JSON-schema pattern matching (schema can't verify a commit
   hash exists). `verdict` computation rule stated explicitly in the prompt: `no_regression` iff every
   `classifications[].classification` is `EXPECTED_DRIFT` or `NO_ACTION`; `needs_da_decision` if any item
   is `DA_NEEDED` and none are `REGRESSION`; `regression` if any item is `REGRESSION` (regression takes
   precedence over DA-needed if both present).

3. **Update Anchors** — `agent()`, **schema-validated**. The orchestrator branches on this phase's output
   (gating on whether the targeted regression subset still fails), so per this plan's own rule — phases
   whose output the orchestrator branches on need JSON-schema validation, exactly like
   `implement-ticket.js`'s `TEST_SCHEMA` with its structured `passed: boolean` field — a plain-text gate
   is not sufficient here. (The Parity phase's plain-text pattern does not apply: Parity's output is
   narrative-only and nothing downstream branches on it; Update Anchors' output *is* branched on.)

   ```js
   const UPDATE_ANCHORS_SCHEMA = {
     type: 'object',
     required: ['files_edited', 'targeted_keys_tested', 'targeted_test_passed', 'summary', 'ts'],
     properties: {
       files_edited: { type: 'array', items: { type: 'string' } },
       targeted_keys_tested: { type: 'array', items: { type: 'string' } },
       targeted_test_passed: { type: 'boolean' },
       summary: { type: 'string' },
       ts: { type: 'string' },
     },
   }
   ```

   Instructions: for every `classifications[]` item with `kind: GRADE_DELTA` or `UNCOVERED_ANCHOR_KEY`
   and `classification: EXPECTED_DRIFT`, edit `tests/simulation_quality/fixtures/grade_anchors.json` (new
   grade, or new key) and, for genuinely new run_keys, add them to `FAST_ANCHOR_KEYS` or
   `SLOW_ANCHOR_KEYS` in `test_grade_regression.py` (tier determined by the run_key's `_<N>t` suffix:
   ≤500t → fast, ≥1000t → slow). **Do not touch** any item classified `REGRESSION` or `DA_NEEDED` — leave
   its anchor value as-is so the regression test continues to flag it. After edits, re-run `pytest
   tests/simulation_quality/test_grade_regression.py -m "not slow" -k "<space-joined list of the specific
   EXPECTED_DRIFT run_keys just edited>"` as a **targeted** gate (not the whole file — a
   `REGRESSION`-classified key is expected to still fail the whole-file run, and that must not trip this
   gate). Return `files_edited`, `targeted_keys_tested` (the run_keys used in the `-k` filter),
   `targeted_test_passed` (boolean — true iff the targeted pytest invocation exited 0), `summary`, `ts`.

   Orchestrator gate — branches on the structured `targeted_test_passed` field (matching `TEST_SCHEMA`'s
   `passed` field convention exactly), not plain-text parsing for an "ANCHORS_STILL_FAILING" string:

   ```js
   const updateAnchorsResult = await agent(
     `...instructions above...`,
     { label: 'update-anchors', schema: UPDATE_ANCHORS_SCHEMA, agentType: 'anchor-updater' }
   )

   if (!updateAnchorsResult.targeted_test_passed) {
     pushEvent('Update Anchors', 'anchor-updater', 'failed', updateAnchorsResult.summary || 'Targeted anchor regression test still failing', updateAnchorsResult.ts)
     await writeMonitoring('ANCHORS_STILL_FAILING')
     return {
       status: 'ANCHORS_STILL_FAILING',
       run_id: runId,
       files_edited: updateAnchorsResult.files_edited,
       targeted_keys_tested: updateAnchorsResult.targeted_keys_tested,
       message: 'Fix the anchor edit for the listed keys, then re-run.',
     }
   }

   pushEvent('Update Anchors', 'anchor-updater', 'ok', updateAnchorsResult.summary || 'Anchors updated', updateAnchorsResult.ts)
   ```

   (same gate shape as `implement-ticket.js`'s `TESTS_FAILED` gate on `testResult.passed`) — this is a
   genuine bug in the edit itself, not an expected-regression case.

4. **Sync Docs** — `agent()`, plain-text. Instructions enumerate exactly which doc sections to touch,
   sourced from investigation §1.1 steps 9-11 and the real section headers confirmed in this session:
   - `docs/simulation_quality/eval_matrix_results.md`: append a dated `> **NOTE (<date>)**` callout under
     the relevant world's `#### <tier>` subsection citing the specific `cause` from Classify Drift; update
     `## Grade Distribution Tables` counts if S/A/B/C mix shifted.
   - `docs/audits/D20_simq_integration.md`: update `## Dimension Profile` `Audit date` field; add/extend a
     `## SimQ Uplift Batch N (...)` section (find the highest existing `N` — currently "Batch 2" per this
     session's `grep`, so a new batch is "Batch 3" unless this run *is* recorded as part of an existing
     open batch); update `## Module Health` row for "Calibration corpus" run-count.
   - `docs/simulation_quality/event_type_coverage.md`: only if Recalibrate's output shows a
     previously-zero `calibration_hits` count now non-zero — conditional, skip silently otherwise.
   - `docs/guidelines/v2_intentional_divergences.md`: only if `verdict == needs_da_decision` **and** the
     DA ruling is made in *this same run* (only applies if a human/architecture-reviewer resolves the DA
     question before Report — see Step 4 phase's interaction with the governance branch below; in the
     common case this file is updated by the spawned follow-up ticket instead, not by this phase).
   No schema — `pushEvent('Sync Docs', ..., 'ok', <files touched, ≤200 chars>, ts)`.

5. **Parity Check** — `agent()`, plain-text, reuses `implement-ticket.js`'s Parity phase prompt shape
   (verified/divergent/missing status semantics, P0 `test_path` requirement) but seeded with
   `simq_audit_gaps.py`'s candidate list instead of asking the agent to re-scan ~4000 lines of YAML from
   scratch.

6. **Verify** — `agent()`, schema-validated:
   ```js
   const VERIFY_SCHEMA = {
     type: 'object',
     required: ['verdict', 'unaccounted_items', 'checklist', 'summary', 'ts'],
     properties: {
       verdict: { type: 'string', enum: ['CLEAN', 'BLOCKED'] },
       unaccounted_items: { type: 'array', items: { type: 'string' } },
       checklist: { type: 'array', items: { type: 'object', required: ['condition', 'status', 'evidence'], properties: { condition: { type: 'string' }, status: { type: 'string', enum: ['PASS', 'FAIL', 'NA'] }, evidence: { type: 'string' } } } },
       summary: { type: 'string' },
       ts: { type: 'string' },
     },
   }
   ```
   Conditions checked: fast-tier regression tests pass (or, if `verdict != no_regression`, every
   remaining failure maps to a `REGRESSION`/`DA_NEEDED` item that now has a ticket reference);
   `simq_audit_gaps.py` reports zero uncovered anchor keys; every doc file Sync Docs was instructed to
   touch was actually touched (or explicitly skipped with a stated reason). `BLOCKED` → same gate pattern
   as `implement-ticket.js`'s `DOD_BLOCKED`.

7. **Report** — no `agent()` call for the branch decision itself (deterministic JS `if` on
   `classifyResult.verdict`, computed from phase 2's already-validated output):
   - `verdict === 'no_regression'`: log a chore-style summary and a suggested commit message string,
     e.g. `` `chore: SimQ audit ${dateStamp} — ${expectedDriftCount} anchors refreshed, no regressions` ``.
     Do **not** create a ticket. `writeMonitoring('DONE_NO_TICKET')`. Return
     `{ status: 'DONE_NO_TICKET', verdict, suggested_commit_message, files_changed, summary }`.
   - `verdict === 'regression' || verdict === 'needs_da_decision'`: spawn one `agent()` call using the
     `ticket-scoper` role with the **same `TICKET_SCHEMA`** `implement-ticket.js` uses for its Scope phase
     (import/duplicate the schema object; do not invent a new one), pre-seeded with the specific
     regression/DA items from Classify Drift as the `request` text (not free text from the caller — the
     workflow constructs the request string itself from `classifyResult.classifications` filtered to
     non-`EXPECTED_DRIFT` items). `writeMonitoring('NEEDS_TICKET')`. Return
     `{ status: 'NEEDS_TICKET', verdict, ticket_id: <new TCK id>, message: 'Continue with /implement-ticket ticket_id=' + ticket_id, files_changed, summary }`.
   `pushEvent('Report', 'workflow', 'ok', ...)` in both branches before `writeMonitoring`.

`writeMonitoring` reuses the **exact** block from `implement-ticket.js` (same `record_events.py`/
`record_run.py` invocations), with two differences: `workflow: "simq-audit"` (confirmed no schema change
needed — `record_run.py`'s `REQUIRED` set is `{run_id, start_ts, workflow, tier, final_status}`, `workflow`
is a freeform string, verified by reading `tools/agent-monitoring/record_run.py` directly), and `run_id`
is a synthetic ID since no ticket necessarily exists yet at Recalibrate time: `SIMQ-AUDIT-<UTC
timestamp from Recalibrate's date call, colons/dashes stripped>` (e.g. `SIMQ-AUDIT-20260704T063723Z`). If
Report spawns a real ticket, monitoring's `run_id` stays the synthetic audit-run ID (the ticket gets its
own separate `run_id` if/when `/implement-ticket` is later invoked on it — this workflow's monitoring
record is about the audit run, not the ticket).

**Scope guard:** this file must not embed calibration orchestration logic in JS (investigation §3 point
4) — Recalibrate only shells out to the Step 3 `make` target and parses its stdout.

**Dependency:** requires Steps 1-3 complete (the `make` target and `simq_audit_gaps.py` must exist before
Recalibrate can run).

### Step 5 — `.claude/skills/simq-audit/SKILL.md` (new file)

**Files:** `.claude/skills/simq-audit/SKILL.md` (new)

Mirror `.claude/skills/implement-ticket/SKILL.md`'s structure exactly: Usage examples, Input parsing
(`mode`, `worlds`), Action section with "Do not call the Workflow tool — execute directly" instruction and
the same JS-construct translation table, a Pipeline section listing all 7 phases with one line each, and
a Notes section covering: `writeMonitoring` called at every exit (`DONE_NO_TICKET`, `NEEDS_TICKET`,
`ANCHORS_STILL_FAILING`, `DOD_BLOCKED`-equivalent `BLOCKED`); the governance branch behavior (state
plainly: "no_regression → suggests a chore commit, does not touch `tickets/`; regression/needs_da_decision
→ creates a ticket and stops — this workflow never fixes a regression or makes a DA ruling itself.").

Usage examples to include:
```
/simq-audit
/simq-audit mode=full
/simq-audit mode=slow
/simq-audit mode=full worlds=frontier_extended,wilderness_survival
```

**Dependency:** requires Step 4 (references `.claude/workflows/simq-audit.js` by exact path).

### Step 6 — Dry-run / smoke-test (scoped, non-destructive)

**Files:** none changed by this step — verification only. Evidence captured into
`staging_artifacts/TCK-20260703-SIMQ-UPLIFT3-AUDIT-WORKFLOW/plan.md` "Deviations" section or the
ticket's Test Summary (implementer's choice, per repo convention).

Explicit scope guard (per ticket Out of Scope + task instructions): **do not** actually execute the full
7-phase agent-orchestrated `simq-audit.js` pipeline against the live repo as this ticket's own
implementation step — that would spawn a real Classify Drift/ticket-hand-off cycle for a ticket whose
job is to *build the tool*, not *run an audit*. Instead:

1. Run `make simq-full-audit` directly (Step 3's target, already verified in this planning session to
   execute cleanly: `evaluate_simq.py --dry-run` against current `data/calibration/`, fast-tier
   `pytest tests/simulation_quality/test_grade_regression.py -m "not slow"`, and
   `tools/simq_audit_gaps.py`) — confirms the **mechanical** phase works end-to-end.
   Expected baseline (confirmed during planning, 2026-07-04): 40 real anchor keys, 29 in
   `FAST_ANCHOR_KEYS`, 11 in `SLOW_ANCHOR_KEYS`, 0 uncovered. If `data/calibration/` reports are stale or
   missing for any anchor key, `evaluate_simq.py --dry-run` will print `MISSING` rows (non-fatal, per its
   own exit-code contract) — that is expected and acceptable for this smoke test; it does not require
   re-running `calibrate_simq.py` across the whole corpus (that would be "re-running a full audit",
   explicitly out of scope).
2. Run the new `tests/unit/tools/test_simq_audit_gaps.py` suite — confirms Step 1/2's tool logic against
   the real fixture/ledger data.
3. **Do not** invoke the `simq-audit` skill/workflow's agent phases (Classify Drift onward) as part of
   this ticket. The workflow's *design* is validated by code review + the mechanical dry-run above; its
   end-to-end agent-orchestrated behavior gets its first real exercise the next time a SimQ batch actually
   needs auditing (a future ticket/session), which is the intended usage pattern, not a burden this ticket
   must discharge.

**Dependency:** requires Steps 1-3 complete.

### Step 7 — `docs/simulation_quality/audit_workflow.md` (new file)

**Files:** `docs/simulation_quality/audit_workflow.md` (new)

Mirrors the doc-density and structure of `docs/simulation_quality/quality_scoring_contract.md` /
`eval_matrix_results.md` (frontmatter block per this repo's doc convention, then sections). Contents:
- What this workflow replaces (the ad-hoc Batch 1-3 manual process, cited by ticket ID).
- The 7-phase pipeline (one paragraph per phase, cross-referencing `.claude/workflows/simq-audit.js`).
- The governance decision (verbatim summary of this plan's "Governance Decision" section) — this is the
  single authoritative place a future session reads to understand why some runs produce a chore commit
  and others produce a ticket.
- Usage: the same `/simq-audit [mode=...] [worlds=...]` examples as the SKILL.md.
- Pointer to `tools/simq_audit_gaps.py --help`-equivalent (its CLI output) for the mechanical-only path
  (a human/CI running just `make simq-full-audit` without any agent session).
- A short "Do not" list: do not use this workflow to change scoring formulas/thresholds; do not let
  Update Anchors touch a `REGRESSION`-classified key; do not skip the `cause`-citation requirement in
  Classify Drift.

**Dependency:** best written last (Step 8), after the actual implementation is settled, so it documents
what was built rather than what was planned — but content is fully determined by Steps 1-6, no new
decisions.

**Also required:** this ticket creates/modifies files under `docs/` → per CLAUDE.md, run
`make knowledge-index-update` during Finalize.

### Step 8 — Update the ticket itself

**Files:** `tickets/inprogress/TCK-20260703-SIMQ-UPLIFT3-AUDIT-WORKFLOW.md`

Fill "Implementation Notes" (what was built, referencing Steps 1-7), "Test Summary" (Step 6's actual
captured output — pass/fail counts, uncovered-key count), "Files Changed" (the full list from Steps 1-5,
7). This is done by the Implement-phase agent per `implement-ticket.js`'s existing convention, not a
separate step this plan needs to schedule differently — listed here only so the implementer doesn't treat
Step 7 as the final step.

---

## Dependency Map

```
Step 1 (simq_audit_gaps.py)
   |
   +--> Step 2 (tests for simq_audit_gaps.py)
   |
   +--> Step 3 (Makefile target, calls Step 1's tool)
           |
           +--> Step 4 (simq-audit.js, Recalibrate phase calls Step 3's make target)
           |       |
           |       +--> Step 5 (SKILL.md, references Step 4's file path)
           |
           +--> Step 6 (dry-run smoke test, exercises Steps 1-3 only, NOT Step 4's agent phases)

Step 7 (docs/audit_workflow.md) — depends on Steps 1-6 being settled (documents final shape)
Step 8 (ticket update) — last, standard Finalize-phase work
```

No step requires re-running a full SimQ audit or touching scoring/calibration internals.

## Explicit Scope Guards (repeated from ticket + investigation, binding for implementation)

- Do NOT modify `src/simulation_quality/*` (scoring logic, pillar formulas, grade thresholds).
- Do NOT modify `tools/calibrate_simq.py` or `tools/evaluate_simq.py` internals — Step 3's make target
  only *invokes* them with existing CLI flags.
- Do NOT run `calibrate_simq.py` across the full corpus as part of this ticket's own verification — Step
  6 explicitly scopes the smoke test to the mechanical diff/test/scan path only.
- Do NOT require an agent/Claude Code session for `make simq-full-audit` itself — it must run standalone
  via plain `bash`/`pytest`/`python3` (confirmed achievable: Step 3's target has no agent-dependent step).
- Do NOT let `tools/simq_audit_gaps.py` write to any file — read-only by construction.
- Do NOT let the Update Anchors phase (Step 4, phase 3) edit anchors for `REGRESSION`/`DA_NEEDED`-
  classified items.
- Do NOT skip the mandatory `agent-monitoring/` writes — `writeMonitoring` is called at every exit path
  in Step 4's workflow, same as `implement-ticket.js`.

## Acceptance Criteria Mapping

| Ticket Acceptance Criterion | Satisfied by |
|---|---|
| Every manual step from Batch 1-3 enumerated with exact commands/files | investigation.md §1 (already complete, not re-done in this plan) |
| Design decision made and documented with reasoning | investigation.md §3 (already complete); this plan's header restates + adds the governance sub-decision |
| Workflow implemented and dry-run successfully against current repo state | Steps 1-6 |
| Usage documented in a discoverable `docs/` location | Step 7 |
| Future session invoking this workflow does not need to re-read this ticket/transcript | Step 5 (SKILL.md) + Step 7 (audit_workflow.md) together are self-contained: phase list, governance branch, usage examples, all inline |

## Unresolved Questions

None. The one open question investigation.md flagged (§7, ticket-ceremony governance) was resolved by
explicit instruction before this planning phase started and is encoded above. The two secondary risks
investigation.md raised (anti-drift citation requirement; `data/calibration/` non-tracked-data handling)
are resolved by design in Step 4 (phase 2's `cause`-citation requirement; phase 1's empty-dir
auto-escalation to `mode=full`) rather than left open.

## Deviations

Minor implementation-time deviations from this plan, none affecting scope or architecture:

- **Step 1**: `scan_parity_ledger_candidates` verified against real data returns ~356 of 1882 total
  parity entries (per-file ratios 9%-100%, `faction.yaml` matching 100% since every entry in that
  10-entry file mentions "faction"). This is broader than the plan's aspirational "short and useful"
  framing, but it is the exact matching design the plan specified (pillar-name + `simq`/`calibrat`/
  `qualityhub` substring match against `text`/`divergence_note`/`v2_evidence`), it is materially
  narrower than a whole-file grep (which the plan explicitly ruled out), and it correctly surfaces the
  four verification-required IDs (`SOC-237`, `SOC-238`, `INFRA-251`, `INFRA-258`) with no false
  negatives. Not changed — this is the approved design, not a bug.
- **Step 2**: `test_exit_code_always_zero` calls `main()` directly (monkeypatching
  `simq_audit_gaps.load_anchor_keys` to inject a synthetic uncovered key) rather than the plan's
  "subprocess" alternative, per the plan's own "(or call `main()` directly if refactored to return
  instead of exit)" fallback clause — `main()` was written to `return` an int and `sys.exit(main())`
  only at the `if __name__ == "__main__":` guard, so the direct-call path was available and is faster/
  more precise (it asserts the specific injected key appears in stdout, not just exit code).
- **Step 2**: created `tests/unit/tools/__init__.py` (the `tests/unit/tools/` directory did not exist
  yet) — anticipated as a conditional step in the plan, confirmed needed.
- No other deviations. Steps 3-7 were implemented exactly as specified, including the corrected
  Makefile shell logic (no leading dash on the pytest line, `test_status=$$?` capture, `exit
  $$test_status`), the Recalibrate phase's schema-less `agent()` call, and the Update Anchors phase's
  `UPDATE_ANCHORS_SCHEMA` with `targeted_test_passed: boolean` gate.

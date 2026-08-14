---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260714-DATA-RUNS-VERIFY-REGEN
artifact_type: plan
tags: [ai, workflows, process-improvement]
---

# Implementation Plan — TCK-20260714-DATA-RUNS-VERIFY-REGEN

## Summary

The investigation found the ticket's original hypothesis wrong but the underlying problem real and
worse than assumed: the post-Test `clean_data_runs_early()` checkpoint added by
`TCK-20260708-DATA-RUNS-CLEANUP-TIMING` has **never fired in any observed run** — it is a bare,
non-`phase()`-anchored `bash()` block in `.claude/workflows/implement-ticket.js`, a file that is not
executed by any interpreter but hand-transcribed, phase-by-phase, by an LLM orchestrating agent per
`.claude/skills/implement-ticket/SKILL.md`'s fixed 6-row translation table — a table with no row for
a standalone `bash()` call and no textual anchor pointing the orchestrator at this specific one.

This plan does **not** add a second instance of that same failure-prone shape. Instead it moves the
pre-Verify sweep into `done-checker`'s own agent prompt (`.claude/agents/done-checker.md`) as a new
Step 0a, immediately before the existing Step 0 static pre-check (`run_static_precheck`, renamed
Step 0b). This mirrors the one call-shape in this codebase with a demonstrated, evidenced-reliable
execution record: `run_static_precheck` itself, embedded directly in `done-checker.md` and confirmed
firing in all three cited runs' `tools.jsonl` slices. Because the orchestrator's existing Phase 8
`agent(prompt, {agentType: 'done-checker', schema: DONE_SCHEMA})` call (line 1052 of
`implement-ticket.js`) already reliably spawns `done-checker` on every standard-tier run — that call
shape *is* in the translation table's row 3 — no change to `implement-ticket.js` is needed at all.
This single new sweep runs after everything else in the pipeline (Test, Parity, and any of
`done-checker`'s own preceding re-verification activity) and immediately before condition 10 is
judged, so it structurally subsumes both the original post-Test purpose and the newly-identified
Parity/Verify-regeneration gap: it does not matter which phase produced a leftover file, only that
none can survive between this sweep and the DoD read. No new Python logic is required —
`clean_data_runs_early` and `check_data_runs_clean` are reused exactly as they exist today, only a
new call site (inside `done-checker.md`) is added.

## Design Decisions

### 1. Fix location — adopted: `done-checker.md` agent-prompt Step 0a, not a second `implement-ticket.js` block

The investigation flagged this as the central open question and recommended, but did not pre-decide,
the agent-prompt route. Adopting it here, for two independent reasons:

- **Direct evidence of reliability.** `run_static_precheck`'s Step 0 call — embedded in
  `done-checker.md`, not in `implement-ticket.js` pseudocode — is confirmed executing at the start of
  `done-checker`'s own turn in all three cited runs (investigation.md, Prior Work section). A second
  `implement-ticket.js` block would carry the *exact* risk profile that caused the original
  checkpoint's total non-execution: no translation-table row, no `phase()` anchor.
- **The investigation's own proposed mitigation for the `.js` route doesn't hold up under direct
  verification, which strengthens this decision further.** The investigation attributed Parity's bare
  `bash()` calls' reliability to "SKILL.md's own '### Parity' prose section (lines 323–329)... giving
  the orchestrating agent an explicit instruction anchored to the Parity phase." I re-checked this
  directly: `.claude/skills/implement-ticket/SKILL.md` has **no `### Parity` section and no per-phase
  prose narration for any phase** (`grep -n "^#" SKILL.md` shows only `# implement-ticket`, `##
  Usage`, `## Input`, `## Action`, `## Pipeline (standard tier)`, `## Notes` — a flat 12-line phase
  list plus the 6-row translation table, nothing more). The "### Parity" Step 0 narration the
  investigation quoted is real, but it lives in `docs/ai/ticket-lifecycle.md`, a reference doc SKILL.md's
  own Action section never instructs the orchestrator to read. This means the investigation's suggested
  remedy for the `.js`-block route ("add SKILL.md prose mirroring Parity's Step 0 narration") has no
  existing pattern to mirror — it would require inventing a new per-phase-prose convention in SKILL.md
  from scratch, which is materially more scope and more unverified risk than the plan's own root-cause
  finding accounted for. This does not invalidate the investigation's primary finding (zero real
  `clean_data_runs_early` invocations, established independently via direct `tools.jsonl` evidence) —
  only its secondary explanation of *why* Parity's sibling calls work. The more likely structural
  explanation, consistent with all evidence: Parity's `bash()` output is consumed as direct input to
  the very next `agent()` prompt in the same phase block (`docs/ai/ticket-lifecycle.md`: "injects...
  into the prompt preamble"), which an LLM transcribing the file naturally treats as required
  setup for the following step, whereas the dead cleanup checkpoint's output only gates a conditional
  return with no downstream prompt consumer — easy to skip when hand-transcribing a long file. The
  `done-checker.md` Step 0a design below deliberately reproduces the "output must be cited in what I
  report next" shape: the sweep's status/evidence is required input to condition 10's evidence string,
  not a side effect.

**Consequence for the ticket's Related Code Areas / AC #2:** `implement-ticket.js` is **not** modified
by this plan, despite being named in the ticket's Related Code Areas and despite AC #2's verification
method ("verifiable by diffing `.claude/workflows/implement-ticket.js`'s phase ordering before/after")
assuming a `.js`-side change. This is a deliberate, evidence-driven divergence, not an oversight — see
the refined Acceptance Criteria Map below for the restated verification method. The implementer must
record this divergence explicitly in the ticket's Implementation Notes when closing.

### 2. SKILL.md update — not needed, and explicitly not attempted

The investigation's Risk #2 said SKILL.md must be updated *if* the orchestrator-`.js`-block route is
chosen. It is not chosen (Decision 1). Per the direct check above, SKILL.md also has no per-phase prose
structure to extend even if it were needed — its Pipeline list is a flat, one-line-per-phase index, and
`done-checker`'s reliability does not depend on SKILL.md prose at all (it depends on `agent()`
being a translation-table row 3 construct, which it already is, unconditionally, for every phase).
**Do not touch `.claude/skills/implement-ticket/SKILL.md` in this ticket.**

### 3. Checkpoint topology — adopted: single new sweep at Verify Step 0a; existing post-Test block left in place, unmodified, with a documentation caveat added

Three options were available: (a) fix the post-Test checkpoint's non-execution and add a second,
independent pre-Verify sweep; (b) relocate the sweep entirely to pre-Verify, removing/deprecating the
post-Test one; (c) add a pre-Verify sweep and leave the post-Test one exactly as-is.

Adopted: **(c)**. Reasoning:
- The post-Test checkpoint's code is Out-of-Scope to remove or weaken (ticket Scope: "must not be
  reverted or weakened"; prior ticket's related-ticket constraint). Deleting or restructuring it is
  not this ticket's mandate.
- Actually repairing the post-Test checkpoint's execution (e.g. wrapping it in a `phase()` call) is
  **not required to satisfy any AC** — the new Step 0a sweep runs strictly after every phase that
  could regenerate artifacts (Test, Parity, and `done-checker`'s own prior activity in the same turn),
  so it alone closes the gap regardless of whether the post-Test checkpoint ever fires. Attempting to
  also repair the post-Test checkpoint's execution would be additional, unscoped work per "never plan
  more work than the ticket scope" — noted below as a candidate future ticket, not undertaken here.
- Leaving the dead code silently in place without documenting its actual reliability would be
  misleading to future readers of `docs/ai/ticket-lifecycle.md` (which currently describes it as if it
  reliably runs). Step 3 below adds a caveat paragraph to that doc section — this is an accuracy
  correction, not a weakening of the checkpoint's role (its code, its backstop framing, and its
  `DATA_RUNS_CLEAN_FAILED` status all remain exactly as they are).

**Final topology:** two sweep call sites exist in the codebase after this change —
`clean_data_runs_early`'s post-Test `bash()` call site in `implement-ticket.js` (unmodified,
now documented as unreliable / defense-in-depth-only) and a new pre-Verify call site inside
`done-checker.md`'s Step 0a (the load-bearing one). `check_data_runs_clean` / `run_static_precheck`
remain the Verify-phase backstop, reading state *after* Step 0a has already run.

**Candidate future ticket (not undertaken here):** repair the post-Test checkpoint's own execution
(e.g. by wrapping it in a `phase()` call, accepting the `meta.phases` schema change the original ticket
avoided) so it provides genuine early feedback rather than being purely aspirational documentation. Out
of scope for this ticket since Step 0a alone satisfies every AC.

## Steps

### Step 1 — Add pre-Verify cleanup sweep as `done-checker`'s new Step 0a
**Files:** `.claude/agents/done-checker.md`
**Change:** Replace the existing `## Step 0 — Run the Static Pre-Check Script First` section (current
lines 10–36) with a two-part `## Step 0 — Sweep data/runs/, Then Run the Static Pre-Check Script`
section:

```markdown
## Step 0 — Sweep `data/runs/`, Then Run the Static Pre-Check Script

Before evaluating conditions 3, 4, 7, 10, and 12 by hand, do two things in order.

**Step 0a — pre-Verify cleanup sweep (TCK-20260714-DATA-RUNS-VERIFY-REGEN).** Run:

```
python3 -c "import sys; sys.path.insert(0,'.'); from tools.gate_checks.done_checker_static import clean_data_runs_early; status, evidence = clean_data_runs_early('<start_ts>'); print(status + '|' + evidence)"
```

Substitute `<start_ts>` with this run's actual value (same one used in Step 0b below). This
auto-cleans any `data/runs/*` / `reports/release_proof/*` files this session has produced up to this
point — including artifacts regenerated by Parity's re-verification work or by your own preceding
Verify-phase activity (e.g. re-running pytest to confirm a cited `test_path`), not only Test phase's
original run. It reuses the exact same `mtime >= start_ts` definition `check_data_runs_clean` (Step
0b) uses, so the two can never disagree on what counts as "this session's own file."

- If the result is `PASS` or `CLEANED`: proceed to Step 0b. Do not report this as a separate
  checklist item — fold its result into condition 10's evidence string (e.g. "Step 0a: 3 file(s)
  auto-cleaned before this check; Step 0b: PASS"). If files were cleaned, include
  `"static:clean_data_runs_early"` in your `verified_by` list alongside `"static:done_checker_static"`.
- If the result is `FAIL` (deletion itself errored — e.g. permission/lock): mark condition 10 `FAIL`
  directly, citing the Step 0a evidence string verbatim, and do not let Step 0b's separate
  `data_runs_clean` result override it — a failed sweep means the directories are not provably clean
  regardless of what `run_static_precheck` reports.

**Step 0b — static pre-check script.** Run the deterministic static pre-check script and cite its
JSON output directly for conditions 3, 4, 7, 10 (unless already marked `FAIL` by Step 0a above), and
12 — do not re-derive them yourself:

```
python3 -c "import sys; sys.path.insert(0,'.'); from tools.gate_checks.done_checker_static import run_static_precheck; import json; print(json.dumps(run_static_precheck('<ticket_id>', '<tier>', '<start_ts>')))"
```

Substitute `<ticket_id>`, `<tier>`, and `<start_ts>` with this run's actual values. The script returns
a JSON list of `{"condition": <name>, "status": "PASS"|"FAIL"|"NA", "evidence": <str>}` objects, mapping
to the checklist below:

| script `condition` | checklist # |
|---|---|
| `staging_artifacts_complete` | 4 |
| `data_runs_clean` | 10 |
| `ticket_location` | 3 |
| `working_log_no_row_yet` | 7 |
| `frontmatter_valid` | 12 |

Use the script's `status`/`evidence` verbatim for these 5 conditions in the checklist table (except
condition 10 if Step 0a already set it `FAIL`). Conditions 1, 2, 5, 6, 8, 9, 11 remain pure LLM
judgment calls — the script does not touch them. Condition 13 stays pre-marked PASS per its own rule
below.

In your final output, include a `verified_by` field listing which conditions came from the static
script(s) vs. pure judgment, e.g. `["static:clean_data_runs_early", "static:done_checker_static", "llm"]`.
```

Also update the Definition of Done Checklist item 10 (current line 90–92) with a short parenthetical:
`10. **Temporary run data cleaned** (Step 0a auto-cleans immediately before this check — see Step 0
above)` — the two existing bullet lines under it (`data/runs/` clear, `reports/release_proof/` clear)
are unchanged.

**Do NOT touch:** Conditions 1–9, 11, 13 and their existing prose; the Tier-Aware Checking section;
the Output section's table/verdict format. Do not add `clean_data_runs_early` as a 6th entry inside
`run_static_precheck` itself (`tools/gate_checks/done_checker_static.py` is not touched by this
step at all — only its existing, already-tested `clean_data_runs_early` function gains a new caller).
**Verify:** No unit test can exercise a live agent prompt (per test_plan.md's Anti-Drift guard) — this
step is verified by Step 2's doc-guard test asserting the new Step 0a text is present in
`done-checker.md`, and by manual read-through confirming the two-part Step 0a/0b structure is
unambiguous and self-contained.

### Step 2 — Add doc-guard test proving the new call site is discoverable
**Files:** `tests/tools/test_done_checker_static.py`
**Change:** Add a new test immediately after the existing
`test_data_runs_clean_status_appears_in_failure_recovery_reference_table` (current lines 306–309),
following its exact pattern:

```python
def test_data_runs_clean_pre_verify_sweep_documented_in_done_checker_prompt():
    doc_path = Path(__file__).parent.parent.parent / ".claude" / "agents" / "done-checker.md"
    content = doc_path.read_text(encoding="utf-8")
    assert "clean_data_runs_early" in content
    assert "Step 0a" in content
```

This is the direct, evidence-motivated countermeasure test_plan.md's New Test #2 calls "not optional"
— it exists specifically to prevent a repeat of this ticket's own root-cause failure mode (a correct
function whose call site is invisible to the orchestrating agent's actual instructions). It is a
static string-presence check only, per the Anti-Drift guard against asserting on prompt text as
behavioral proof — it proves the instruction exists in the file `done-checker`'s agent definition is
built from, not that a live agent turn will act on it.

No new test is added for the cleaning logic itself: the existing
`test_clean_data_runs_early_detects_and_removes_leftover_artifacts` and
`test_clean_data_runs_early_preserves_files_older_than_start_ts` already prove
`clean_data_runs_early` cleans any file with `mtime >= start_ts` regardless of which phase produced
it — the function has no phase-awareness, so a file representing a Parity- or Verify-regenerated
artifact is indistinguishable, in the test, from a Test-phase one. Creating a near-duplicate test
under a new name would violate test_plan.md's own instruction to skip redundant coverage.

**Do NOT touch:** Any of the 52 existing tests in this file — no existing test's body, fixture, or
assertion changes. `run_static_precheck`'s two existing tests
(`test_run_static_precheck_all_pass_eligible`, `test_run_static_precheck_surfaces_fail_not_masked`)
must show zero diff, proving the 5-check aggregation tuple did not grow to 6.
**Verify:** `pytest tests/tools/test_done_checker_static.py -v` — new test passes, all 52 existing
tests pass unmodified (53 total).

### Step 3 — Update `docs/ai/ticket-lifecycle.md`
**Files:** `docs/ai/ticket-lifecycle.md`
**Change:**

1. **Test section, Post-Test cleanup checkpoint paragraph** (current lines 307–315): append a new
   paragraph immediately after it (before the `---` separator at line 317):
   > **Reliability caveat (added by TCK-20260714-DATA-RUNS-VERIFY-REGEN):** direct evidence from
   > `agent-monitoring/tools.jsonl` across 5+ weeks of runs found this checkpoint's own `bash()` call
   > has never been observed to execute — as a bare, non-`phase()`-anchored block, the LLM orchestrator
   > reading `implement-ticket.js` has no reliable translation-table anchor for it (see
   > `stored_artifacts/TCK-20260714-DATA-RUNS-VERIFY-REGEN/investigation.md`). Its code and this
   > paragraph are kept as documentation of intent and as a defense-in-depth no-op if the orchestrator
   > ever does execute it, but it must not be relied on as the load-bearing cleanup mechanism. The
   > Verify section below (`done-checker`'s Step 0a) carries the evidenced-reliable sweep that actually
   > closes this gap, and subsumes this checkpoint's original post-Test purpose as well as covering
   > later-phase (Parity/Verify) regeneration.
2. **Verify (Definition of Done) section, Step 0 prose** (current lines 360–363): replace with:
   > **Step 0a (added by TCK-20260714-DATA-RUNS-VERIFY-REGEN):** before anything else, `done-checker`
   > runs `tools/gate_checks/done_checker_static.py::clean_data_runs_early(start_ts)` and auto-cleans
   > any `data/runs/*` / `reports/release_proof/*` this session has produced up to this point —
   > including artifacts Parity's or `done-checker`'s own re-verification pytest runs regenerated after
   > the post-Test checkpoint (above) ran or was skipped. A deletion-error result here is folded
   > directly into condition 10 rather than raising a separate blocking status.
   >
   > **Step 0b:** Before judging conditions 3, 4, 7, 10 (if not already marked `FAIL` by Step 0a), 12 by
   > hand, `done-checker` runs
   > `tools/gate_checks/done_checker_static.py::run_static_precheck(ticket_id, tier, start_ts)` and
   > cites its PASS/FAIL/NA + evidence output verbatim for those five conditions, then self-reports a
   > `verified_by` field listing which condition(s) came from which script(s) vs. pure judgment.
3. **13-condition table, row 10** (current line 382): replace with:
   > `| 10 | data/runs/ cleaned | — script-checked; primary cleanup now happens immediately before this check, inside done-checker's own Step 0a (as of TCK-20260714-DATA-RUNS-VERIFY-REGEN) — closes the gap where Parity/Verify's own re-verification work could regenerate artifacts after the post-Test checkpoint (Test section above, now a documented-intent no-op — see its Reliability caveat) had already run. `run_static_precheck`'s data_runs_clean check (Step 0b) remains the backstop confirmation read. |`

**Do NOT touch:** The Failure Recovery Reference table (line 528, `DATA_RUNS_CLEAN_FAILED` row) —
its trigger condition (the post-Test checkpoint's own deletion-error path) is unchanged by this
ticket, so the row's text stays exactly as-is, per test_plan.md's instruction to reuse rather than
duplicate when the status's meaning hasn't changed. Do not touch the Parity section prose, the
Architecture-Verify Step 0 prose, the Finalize section, or any other Failure Recovery row.
**Verify:** Manual read-through (no automated test covers Verify-section prose beyond Step 2's
doc-guard test, which covers `done-checker.md` specifically, not `ticket-lifecycle.md`).

### Step 4 — Run scoped regression
**Files:** none (verification-only step)
**Change:** N/A.
**Do NOT touch:** N/A.
**Verify:** `pytest tests/tools/test_done_checker_static.py -v` — full file green, 53 tests
(52 existing + 1 new from Step 2), zero modified existing test bodies (confirm via `git diff` on the
test file showing only an addition).

## Scope Guards

- Do not modify `check_data_runs_clean`'s or `clean_data_runs_early`'s mtime/`start_ts` *definition*
  of "clean" — reused exactly as-is; no change to `tools/gate_checks/done_checker_static.py` at all in
  this plan.
- Do not add `clean_data_runs_early` to `run_static_precheck`'s aggregation tuple — it stays a
  separately-invoked function with its own call site (now two call sites: the unmodified post-Test
  one, and the new Step 0a one), never folded into the 5-check aggregate.
- Do not remove or weaken the post-Test checkpoint's code, its `DATA_RUNS_CLEAN_FAILED` status, or its
  existing doc paragraph — only append the Reliability caveat (Step 3.1); no deletion, no
  restructuring, no `phase()` wrapping (that is the explicitly-deferred candidate future ticket in
  Design Decision 3).
- Do not touch `.claude/workflows/implement-ticket.js` — no line in this file changes. This is a
  deliberate divergence from the ticket's Related Code Areas list; see Design Decision 1.
- Do not touch `.claude/skills/implement-ticket/SKILL.md` — confirmed unnecessary and confirmed to
  have no existing per-phase-prose structure to extend; see Design Decision 2.
- Do not touch `run_finalize_selfcheck`, `check_migration_complete`, `check_ticket_finalized`,
  `check_working_log_exactly_one_row`, or any Part B (post-Finalize) function in
  `done_checker_static.py` — unrelated, Out of Scope.
- Do not modify conditions 1–9, 11, or 13 of `done-checker.md`'s Definition of Done Checklist, or its
  Tier-Aware Checking / Output sections — only condition 10's parenthetical note and the Step 0 section
  change.
- Do not touch the Failure Recovery Reference table's `DATA_RUNS_CLEAN_FAILED` or `DOD_BLOCKED` rows,
  the Parity section prose, or any other section of `docs/ai/ticket-lifecycle.md` beyond the three
  specific edits in Step 3.
- Do not attempt to make the second retro-flagged failure category (empty Completion
  Summary/Files-Changed/Test-Summary sections) part of this ticket — separate concern, explicitly Out
  of Scope per the ticket.
- Do not change what Parity/Verify agents are asked to verify (their verification mandate) — this plan
  only adds a cleanup sweep, it does not constrain re-verification behavior (the ticket's own Scope
  marks that as a "consider, not prescribed" item; not undertaken in this plan — see Anti-Drift Notes).

## Dependency Map

- Step 1 (`done-checker.md`) has no code dependency on any other step — it reuses
  `clean_data_runs_early` exactly as it exists today.
- Step 2 (new test) depends on Step 1's exact wording ("Step 0a", `clean_data_runs_early`) being final
  before the test's substring assertions are written — sequence Step 2 after Step 1.
- Step 3 (`docs/ai/ticket-lifecycle.md`) depends on Step 1's final Step 0a/0b naming and behavior
  (PASS/CLEANED/FAIL handling) being settled — sequence Step 3 after Step 1, independent of Step 2
  (could run in parallel with Step 2, both depending only on Step 1).
- Step 4 (regression run) depends on Steps 1–3 all being complete.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: Root cause confirmed before fix designed | Investigate phase (investigation.md) — confirmed the assumption wrong and identified the true mechanism | N/A — investigation artifact |
| AC2: A cleanup sweep runs after which no further data/runs/-writing agent work occurs before Verify's DoD check reads its result — **refined**: verification method changed from "diffing `implement-ticket.js`'s phase ordering" to "diffing `done-checker.md`'s Step 0 section," since Design Decision 1 places the sweep inside the agent prompt that Verify's existing (unmodified) `agent()` call already reliably invokes, not inside a new `.js` block | Step 1 | Manual diff of `done-checker.md` before/after; Step 2's doc-guard test confirms the sweep text is present |
| AC3: `check_data_runs_clean` / `run_static_precheck` still exist and still run at Verify as backstop, unchanged in role | Step 1 (Step 0b unchanged logic, sequenced after Step 0a); Step 3 item 3 (doc clarifies backstop role) | `pytest tests/tools/test_done_checker_static.py -v` — `test_run_static_precheck_all_pass_eligible`, `test_run_static_precheck_surfaces_fail_not_masked` pass unmodified |
| AC4: A new/updated test demonstrates artifacts created during a simulated Parity/Verify step (not just Test) are cleaned or fail-fast before Verify's DoD check judges cleanliness | Existing `test_clean_data_runs_early_detects_and_removes_leftover_artifacts` / `test_clean_data_runs_early_returns_fail_on_deletion_error` (reused, unmodified — the function is phase-agnostic) prove the cleaning logic; Step 2's new doc-guard test proves the call site is wired into the actual pre-Verify instruction sequence | `test_clean_data_runs_early_detects_and_removes_leftover_artifacts`, `test_clean_data_runs_early_returns_fail_on_deletion_error`, `test_data_runs_clean_pre_verify_sweep_documented_in_done_checker_prompt` |
| AC5: `docs/ai/ticket-lifecycle.md` updated to reflect corrected checkpoint timing | Step 3 | Manual read-through |
| AC6: Scoped pytest run against changed test file(s) passes | Step 4 | `pytest tests/tools/test_done_checker_static.py -v` |
| AC7: Next 5 completed standard-tier runs show zero Verify-phase failures citing uncleaned `data/runs/` — follow-up signal, not a hard gate on this ticket's closure | N/A — tracked post-closure at next weekly retro (`agent-monitoring-retro` skill), per test_plan.md's Anti-Drift Test Guards | Not pytest-verifiable; monitoring/retro follow-up only |

## Anti-Drift Notes

- **The refactor-free nature of this plan is deliberate and load-bearing.** `clean_data_runs_early`
  and `check_data_runs_clean` are reused byte-for-byte; if implementation finds itself editing
  `tools/gate_checks/done_checker_static.py`, stop — that is a signal of scope drift back toward the
  Out-of-Scope mtime-definition boundary both this ticket and the prior one protect.
- **`done-checker` performing deletion (`f.unlink()` via `clean_data_runs_early`) is not a durable-state
  architecture violation.** `data/runs/*` / `reports/release_proof/*` are ephemeral workflow/telemetry
  byproducts explicitly required to be cleaned per CLAUDE.md's Definition of Done ("Temporary run data
  cleaned"), not simulation domain state. The prior ticket already established the precedent of an
  automated caller invoking this exact function to delete these paths; this plan only changes which
  caller (agent prompt vs. orchestrator pseudocode), not the nature of the operation. Flagging this
  explicitly for the Review/Architecture-Verify phases so it is not mistaken for a new class of risk.
- **Do not conflate `data/runs/{run_id}/simulation_events.jsonl`** (simulation telemetry convention)
  **with the agent-workflow `data/runs/` cleanup** this ticket addresses — same recurring distinction
  from prior tickets in this area (investigation.md, Mechanics/Engine Constraints section).
- **The investigation's citation of SKILL.md's "### Parity" section was incorrect** (that narration
  lives in `docs/ai/ticket-lifecycle.md`, confirmed by direct `grep -n "^#"` against SKILL.md showing
  no per-phase headers at all). This plan's Design Decision 1 accounts for the correction and does not
  depend on the original citation being accurate — the core "zero real invocations" finding is
  independently evidenced via `tools.jsonl` and unaffected by this correction. Implementer/reviewer
  should not be surprised if grepping SKILL.md for "Parity" turns up only the one-line Pipeline-list
  entry, not prose — that is expected and consistent with this plan.
- **Residual Risk: dead post-Test checkpoint remains in the codebase, now documented as unreliable
  rather than fixed.** This is an accepted tradeoff, not a mitigated one — see Design Decision 3. If a
  future retro or investigation finds evidence the post-Test checkpoint *does* fire in some runs (which
  would partially contradict this investigation's "zero invocations" finding), that does not change
  this ticket's fix (Step 0a is unconditional and runs regardless), but should prompt revisiting whether
  the Reliability caveat added in Step 3.1 needs softening. The candidate future ticket (repairing the
  post-Test checkpoint's own execution via a `phase()` wrapper) is explicitly not undertaken here.
- **The ticket's Scope also flagged, as a "consider, not prescribed" item, constraining Parity/Verify's
  own re-verification commands to avoid regenerating `data/runs/` artifacts in the first place** (e.g.
  steering toward `pytest --collect-only`-style dry verification). This plan does not attempt that —
  it is explicitly optional in the ticket's own wording, orthogonal to closing the timing gap (Step 0a
  closes the gap regardless of how much or how little Parity/Verify re-runs), and would touch agent
  verification mandates that Out of Scope explicitly protects ("Any change to what Parity/Verify agents
  are asked to verify, beyond constraining how they verify it... is out of scope"). Noting as a
  candidate future ticket alongside the post-Test-checkpoint repair, not undertaken here.
- **No test should assert on `.claude/workflows/implement-ticket.js`'s or `.claude/agents/done-checker.md`'s
  literal prompt text as proof of live-agent behavior** — Step 2's new test is a static string-presence
  check only (proving the instruction exists in the file the agent is built from), never a claim that a
  live orchestrating turn will act on it. This mirrors and extends test_plan.md's own guard, which in
  turn mirrors the prior ticket's identical caution.

## Unresolved Questions

None. All three open questions the investigation flagged for Plan (fix location; SKILL.md
applicability; checkpoint topology) have concrete decisions above, each grounded in direct evidence
gathered during planning (the `done-checker.md`/`tools.jsonl` precedent for Decision 1; the direct
SKILL.md structure check for Decision 2; the AC-coverage analysis for Decision 3). None of these turn
on a genuine multi-way product/architecture tradeoff requiring human input — each has one evidence-backed
answer once the investigation's findings are taken at face value.

## Deviations

None. Implementation followed Steps 1-4 exactly as specified:

- Step 1: `.claude/agents/done-checker.md`'s Step 0 section was replaced with the two-part Step
  0a/0b structure verbatim (including the condition-10 checklist parenthetical), with no other
  section touched.
- Step 2: The new doc-guard test
  (`test_data_runs_clean_pre_verify_sweep_documented_in_done_checker_prompt`) was added verbatim,
  immediately after `test_data_runs_clean_status_appears_in_failure_recovery_reference_table`, with
  no existing test body modified.
- Step 3: All three `docs/ai/ticket-lifecycle.md` edits (Test-section Reliability caveat,
  Verify-section Step 0a/0b rewrite, condition-10 table row) were applied exactly as specified; the
  Failure Recovery Reference table, Parity section, Architecture-Verify section, and Finalize section
  were left untouched.
- Step 4: `pytest tests/tools/test_done_checker_static.py -v` returned 53 passed (52 existing + 1
  new), confirmed via `git diff --stat` showing only a 7-line addition to the test file.

All Scope Guards held: `tools/gate_checks/done_checker_static.py`,
`.claude/workflows/implement-ticket.js`, and `.claude/skills/implement-ticket/SKILL.md` were not
modified (confirmed via `git diff --stat` against each, zero changes).

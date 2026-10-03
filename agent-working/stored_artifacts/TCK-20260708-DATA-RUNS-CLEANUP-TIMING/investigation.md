---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260708-DATA-RUNS-CLEANUP-TIMING
artifact_type: investigation
tags: [ai, workflows, process-improvement]
---

# Investigation — TCK-20260708-DATA-RUNS-CLEANUP-TIMING

## Current Behavior

### Phase order and where `data/runs/`/`reports/release_proof/` actually gets touched

`.claude/workflows/implement-ticket.js` phases run in this order for `standard` tier: Scope →
Investigate → Plan → Review → **Implement** → Architecture-Verify → **Test** → Parity →
Security-Review (conditional) → **Verify** → **Finalize**.

- **Implement phase** (`phase('Implement')` at line 499, agent call lines 514–542): the prompt only
  instructs the `implementer` agent to write code, update `Implementation Notes`, and update
  `plan.md`'s Deviations section. **It contains zero instruction to run tests, pytest, or any
  simulation.** Cross-checked against `.claude/agents/implementer.md` (read in full) — that agent
  definition's "After Writing Code" section only lists: update ticket, update staging artifacts,
  report structured JSON. No Bash-execution-of-tests step anywhere in either the workflow prompt or
  the agent definition. **Conclusion: Implement is not a source of `data/runs/`/`release_proof/`
  artifacts under normal operation** (an implementer *could* technically run something ad hoc via
  Bash, but it is neither instructed nor incentivized to).
- **Test phase** (`phase('Test')` at line 631, agent call lines 648–668, agent type `test-scoper`):
  Step 3 says "Build the scoped pytest command," Step 4 says "**Run the command via Bash. Capture
  stdout/stderr.**" `.claude/agents/test-scoper.md` (read in full) confirms this in its own "Output"
  section, item 3: "**Execute the command via Bash** and capture the full output." The scoped
  command can include `tests/unit/lab/`, `tests/unit/kernel/`, arena/simulation-invoking tests, or
  (per the ticket's own cited evidence case, `TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS`, a
  long-run calibration-anchor ticket) potentially many long simulation runs — each of which can
  write to `data/runs/` and `reports/release_proof/` as a byproduct. **This confirms the ticket's own
  open question: test-scoper (Test phase), not the Implement-phase agent, is the actual runtime
  source of new `data/runs/`/`release_proof/` artifacts.**
- No other phase (Architecture-Verify, Parity, Security-Review, Verify) executes pytest or any
  simulation — all of their `bash()` calls are pure Python one-liners against
  `tools/gate_checks/*.py` / `tools/*.py` (AST scans, YAML scans, frontmatter validation). Confirmed
  by reading each phase's code block in full (lines 553–627, 690–810, 812–868, 870–949).

### The real ordering defect: the cleanliness check runs *before* the only cleanup step

This is the load-bearing finding, beyond what the ticket's own Request Summary states explicitly:

- `check_data_runs_clean` is invoked from **Verify** (phase 8, via `run_static_precheck` inside the
  `done-checker` agent prompt, line 921).
- The only step that actually deletes `data/runs/*` / `reports/release_proof/*` is **Finalize**
  (phase 9, step 6, line 994: `"Clean data/runs/* and reports/release_proof/* only if they contain
  artifacts from this work session (check modification times before deleting)."`) — a **prose
  instruction inside the Finalize agent's free-text prompt**, not a deterministic `bash()` call.
- **Phase order is Verify → Finalize, i.e. the check runs strictly before the cleanup step it is
  checking for.** If Test phase (phase 6) generated any `data/runs/` artifact with
  `mtime >= start_ts`, nothing between Test and Verify (Parity, Security-Review) removes it, so
  `check_data_runs_clean` at Verify is essentially guaranteed to FAIL whenever Test produced any run
  artifact at all — independent of whether those artifacts are from "a prior session" as the ticket's
  Open Question frames it. The retro's 6/11 failures this week are much better explained by *this
  session's own Test-phase output not yet being cleaned* than by leftover debris from an unrelated
  prior session (139/44/37/19 leftover directories in a single run is consistent with one ticket's
  own long-run Test-phase execution, not with accumulated cross-session litter).
- Practical implication for the insertion-point decision: a precondition placed **before** Test
  (as the ticket's second candidate proposes) only defends against genuinely stale prior-session
  debris — it cannot address the dominant failure mode, because Test hasn't produced its own
  artifacts yet at that point. A cleanup/check placed **after Test** (before Parity, or as Parity's
  first orchestrator-run step) directly targets the actual generator and closes the phase-order gap
  described above. Both are legitimate defenses for different threats and are not mutually
  exclusive; see Risks and Open Questions for how this bears on the AC's "left to Investigate/Plan"
  language.

### `check_data_runs_clean` exact shape (`tools/gate_checks/done_checker_static.py:92-118`)

```python
def check_data_runs_clean(
    start_ts: str | None,
    runs_dir: Path = Path("data/runs"),
    proof_dir: Path = Path("reports/release_proof"),
) -> tuple[str, str]:
```

- Parses `start_ts` (ISO 8601, `Z`-suffixed) to an epoch float. If `start_ts` is `None` or
  unparsable, `start_epoch` stays `None`.
- Walks both `runs_dir` and `proof_dir` with `.rglob("*")`, considering only files (`f.is_file()`).
- A file is **flagged** if `start_epoch is None` (unparsable/missing start_ts — treated as "not
  evidence of cleanliness," not as a pass) **or** `f.stat().st_mtime >= start_epoch`.
- Returns `("FAIL", "<flagged file list>")` if any flagged file exists, else `("PASS", ...)`.
- `run_static_precheck(ticket_id, tier, start_ts)` (lines 173-188) calls this as one of 5 aggregated
  checks, invoked from Verify's `done-checker` prompt (line 921) via
  `python3 -c "... run_static_precheck('${tid}', '${tier}', '${startTs}') ..."`.
- **`start_ts` provenance**: `const startTs = ticketInfo.ts || null` at line 142 of
  `implement-ticket.js` — captured once, at Scope-phase completion, and threaded unchanged through
  the rest of the run (also reused at line 194 for the monitoring `record_run.py` call, and at line
  921 for the Verify static pre-check). **Any earlier check/cleanup step should reuse this exact
  same `startTs` value** — it is already in JS scope at every point after line 142, including
  immediately after Test phase — rather than deriving a new timestamp, to preserve one single
  consistent definition of "this session's own files" across the whole pipeline (the ticket's Out of
  Scope line explicitly forbids changing that definition).
- This mtime-based, `start_ts`-relative approach is itself the same convention already written into
  Finalize step 6's own prose ("check modification times before deleting") — confirmed as
  intentional precedent by `stored_artifacts/TCK-20260705-GATE-DET-DONE-CHECKER/investigation.md`
  (see Prior Work below), not something this ticket needs to newly invent.

### Workflow-level (`.js`) test coverage — none exists

`grep -rl "implement-ticket.js\|implement_ticket" tests/` returns **zero results**. There is no
workflow-level test harness for `.claude/workflows/implement-ticket.js` at all — no JS test runner
is wired into this repo's `tests/` tree, and no Python test imports or exercises the `.js` file
directly (it's a Claude-internal `Workflow()` DSL file, not an importable module).

The **only** testable surface for anything this ticket touches is `tools/gate_checks/*.py` and any
new sibling pure-Python module under `tools/gate_checks/` — exactly the same shape as every prior
gate-determinism ticket (`TCK-20260705-GATE-DET-DONE-CHECKER`,
`TCK-20260706-SCOPE-TAG-REGISTRY-CHECK`, `TCK-20260705-WORKFLOW-PARITY-SKIP`). **Practical
consequence for AC #3 ("A new test... demonstrates that run artifacts left over...are either cleaned
automatically or cause a fail-fast signal")**: this AC is only satisfiable if the new
cleanup/precondition logic is implemented as a plain, importable Python function (consumed from the
`.js` file via `bash(python3 -c "...")`, mirroring `check_tags_registered`,
`find_p0_intersection`, `check_data_runs_clean` itself) — not as free-text instructions added to an
agent's prompt string. Prose-only changes to the Implement or Test agent prompts (the ticket's first
candidate) would be **untestable by pytest** and would repeat exactly the failure mode already
diagnosed above for Finalize step 6 (a prose cleanup instruction that is being missed on the first
pass). This is a strong argument, not just a testability nicety, for implementing the new checkpoint
as a deterministic `bash()`-invoked function.

### `tests/tools/test_done_checker_static.py` — existing coverage for `check_data_runs_clean`

580 lines total. Four existing tests cover `check_data_runs_clean` directly (lines 135-193):
`test_data_runs_clean_empty_dirs_passes`, `test_data_runs_clean_file_before_start_ts_passes`,
`test_data_runs_clean_file_at_or_after_start_ts_fails_naming_path`,
`test_data_runs_clean_unparsable_start_ts_flags_any_file`. These pin the exact PASS/FAIL contract
described above via `tmp_path` fixtures and `os.utime()` to control mtime — a strong, reusable
pattern for testing any new function built on the same primitive. `run_static_precheck` also has two
tests (`test_run_static_precheck_all_pass_eligible`, `test_run_static_precheck_surfaces_fail_not_masked`,
lines 360-388) using `monkeypatch` to stub individual checks.

### Failure Recovery Reference table row format (`docs/ai/ticket-lifecycle.md:475-486`)

Existing rows follow a strict 4-column shape: `| Return status | What failed | Fix | Re-run |`. Every
existing row's "Re-run" column is either `Re-run with request (new scope)` (only `CONFLICTS_DETECTED`)
or `Re-run with ticket_id` (all others) — the resumable-with-`ticket_id` pattern is the norm. The most
directly analogous row, `TAGS_NOT_REGISTERED` (line 478), reads:

```
| `TAGS_NOT_REGISTERED` | A ticket tag isn't in `docs/guidelines/tag_registry.jsonl` | Register it (`python3 tools/tag_registry.py add <tag> --category <cat> --note "..."`) or edit the ticket's tags to use an existing registered one | Re-run with `ticket_id` |
```

If a new status is introduced (e.g. an auto-clean failure, or a human-actionable "leftover artifacts
detected, could not auto-clean" signal), it must follow this exact 4-column shape and slot into the
table in phase order (between the existing `TESTS_FAILED`/`SECURITY_BLOCKED` row and `DOD_BLOCKED`,
if placed after Test, or earlier if placed before Test).

## Mechanics / Engine Constraints

Not applicable. This ticket touches only `.claude/workflows/implement-ticket.js`,
`tools/gate_checks/done_checker_static.py` (or a new sibling module), and
`docs/ai/ticket-lifecycle.md` — agent-workflow-hygiene tooling, not simulation mechanics. No
`docs/mechanics/` chapter or `docs/engine/` contract governs pipeline cleanup timing. Confirmed
consistent with the identical conclusion reached by
`stored_artifacts/TCK-20260705-GATE-DET-DONE-CHECKER/investigation.md`'s own "Mechanics / Engine
Constraints" section for the same code area.

## Parity Ledger Overlap

**None.** Confirmed by grep of all 8 canonical `docs/parity_ledger/*.yaml` files for
`data/runs|release_proof|done-checker|finaliz` — no entry references `.claude/workflows/`,
`tools/gate_checks/`, or `data/runs/`/`reports/release_proof/` as agent-workflow artifacts (any
`data/runs/{session_id}/` hits found elsewhere in the repo belong to the unrelated
*simulation*-run-output convention referenced by `.claude/agents/simulation-analyst.md`, not this
agent-workflow cleanup concern — same distinction already drawn and confirmed by the prior
`TCK-20260705-GATE-DET-DONE-CHECKER` investigation). This matches the ticket's own Assumption
("no parity ledger entry applies") — **confirmed, not merely assumed.**

## Prior Work

- `stored_artifacts/TCK-20260705-GATE-DET-DONE-CHECKER/` (investigation.md, plan.md, test_plan.md) —
  built `check_data_runs_clean` and established the mtime-vs-`start_ts` convention this ticket must
  reuse unchanged. Its own investigation explicitly derived that convention from Finalize step 6's
  prose ("check modification times before deleting") — i.e. the *check's* logic was written to match
  an *already-existing* cleanup instruction, not the other way around. This ticket now closes the
  loop the other direction: making an earlier point in the pipeline enforce that same logic
  deterministically instead of relying on prose.
- `TCK-20260706-SCOPE-TAG-REGISTRY-CHECK` (referenced in ticket-lifecycle.md lines 137-143) — the
  direct architectural precedent: moved `frontmatter_valid`'s tag-registration sub-check from a
  late, LLM-judged Verify condition to an early, deterministic, **orchestrator-run `bash()` call**
  immediately after the Scope agent returns (not a change to the Scope agent's own prompt), returning
  a **new status** (`TAGS_NOT_REGISTERED`) that halts the run with a human-actionable fix and
  re-run-with-`ticket_id` path. This is architecturally the closest match to what this ticket needs:
  a `bash()`-invoked pure-Python check inserted between two existing phases, not a prompt-text
  addition to an agent.
- `TCK-20260705-WORKFLOW-PARITY-SKIP` (referenced in ticket-lifecycle.md lines 328-331) — established
  the pattern of the **orchestrating session itself** running a `bash()` call directly (not spawning a
  new `agent()`) for a lightweight, deterministic scan (`find_p0_intersection`), explicitly to avoid
  the cost of a sub-agent call for something a pure function can decide. The same shape (`bash()` in
  the orchestrator, not a new agent) is directly reusable for a data/runs cleanup/check step.
- `TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS` (done) — the concrete 139-leftover-directory case;
  its own domain (long-run calibration anchors) is exactly the kind of ticket whose Test-phase pytest
  run would legitimately execute many long simulation runs, supporting the "Test phase is the actual
  generator" finding above rather than "prior session leftovers."
- No prior stored artifact addresses cleanup *timing* specifically — confirmed, this is the first
  ticket targeting the ordering defect directly (matches the ticket's own claim).

## Risks and Open Questions

1. **Insertion point — the ticket's two named candidates are each necessary but neither is
   sufficient alone.** A pre-Test precondition (candidate 2) only catches genuinely stale
   prior-session debris; it cannot catch the dominant failure mode (this session's own Test-phase
   output, generated *after* the precondition would have already run). A prompt addition to
   Implement (candidate 1) targets a phase that does not generate these artifacts under normal
   operation. The evidence above points to a **post-Test, pre-Parity deterministic cleanup step**
   (reusing `check_data_runs_clean`'s exact mtime/`start_ts` logic, either to auto-delete flagged
   files or to fail fast) as the insertion point that actually closes the Verify-runs-before-Finalize
   ordering gap. This is a materially different point than either literal candidate — the ticket's
   own Assumptions section explicitly permits this ("If Investigate finds a materially different and
   better insertion point... that is in scope as long as the Finalize-phase backstop and
   `done_checker_static.py`'s `data_runs_clean` condition are preserved"). **This is a genuine
   Plan-phase decision, not resolved here** — flagging it rather than assuming it, per the
   Uncertainty Rule.
2. **Auto-clean vs. fail-fast is not decided by the ticket and materially changes the new status
   design.** AC #3 explicitly allows either "cleaned automatically" or "cause a fail-fast,
   human-actionable signal" — these produce very different implementations (a silent `bash()` `rm`
   of flagged files with a logged event vs. a new blocking status added to the Failure Recovery
   table, mirroring `TAGS_NOT_REGISTERED`). Auto-clean best matches the retro's own recommendation
   ("cut the 42% first-pass DoD failure rate... without touching any of the real gap conditions") and
   requires no new status; fail-fast better matches the literal AC #4 language ("if a new
   failure/return status was introduced, it appears in the Failure Recovery Reference table" — which
   is written conditionally, i.e. also permits "no new status" as a valid outcome). **Recommend Plan
   phase choose auto-clean-and-log as the primary path** (lowest-friction, matches retro's own stated
   goal, avoids adding pipeline friction for a hygiene issue) **with a fail-fast fallback only if
   auto-clean itself fails** (e.g. permission error) — but this is a recommendation, not a
   pre-decided answer.
3. **Concurrent-session safety.** Any earlier cleanup step must keep gating on
   `mtime >= start_ts` (never a blind `rm -rf`) — a second `implement-ticket` run executing
   concurrently could have its own in-flight `data/runs/` artifacts with an earlier `start_ts` that
   must not be deleted by this ticket's run. `check_data_runs_clean`'s existing signature already
   handles this correctly; a new caller must not regress it into an unconditional wipe.
4. **`start_ts` variable name inside the `.js` file is `startTs`**, already in scope from line 142
   onward — confirm the new insertion point (wherever chosen) is placed after line 142 so it can read
   `startTs` directly without re-deriving it.

## Anti-Drift Hazards

- **Do not touch `check_data_runs_clean`'s mtime-based flagging logic** (lines 92-118) — explicitly
  Out of Scope. Any new earlier check must call the existing function (or a thin wrapper around it),
  not reimplement its own competing definition of "clean."
- **Do not remove or weaken the Finalize-phase backstop** (step 6, line 994) or
  `run_finalize_selfcheck` / `FINALIZE_INCOMPLETE` — both explicitly Out of Scope and both must
  remain as the safety net even after an earlier checkpoint is added.
- **Do not implement the new checkpoint as prose added to an agent prompt.** As shown above, this
  both fails the "add/update tests" AC (untestable) and repeats the exact failure mode already
  diagnosed for Finalize step 6 (a prose cleanup instruction being missed). It must be a
  deterministic, `bash()`-invoked pure Python function, mirroring the `TAGS_NOT_REGISTERED` /
  P0-parity-scan precedents.
- **Do not conflate `data/runs/{session_id}/` (simulation-run output convention, referenced by
  `.claude/agents/simulation-analyst.md`) with the agent-workflow `data/runs/` cleanup this ticket
  addresses** — same distinction the prior GATE-DET-DONE-CHECKER investigation already drew; carry it
  forward, don't re-litigate it.
- **Do not silently swallow a new precondition/cleanup failure.** If auto-clean fails or a new status
  is introduced, it must be visible (pushed event + Failure Recovery Reference table row), never a
  logged-but-ignored warning — matches the Finalize-selfcheck precedent's own stated design goal
  ("report the discrepancy explicitly rather than silently returning DONE").
- **Do not scope-creep into the second retro-flagged category** (stale `make knowledge-index-update`,
  3/11 failures) — explicitly Out of Scope, has its own separate fix path.
- **Do not modify `run_finalize_selfcheck` or the `FINALIZE_INCOMPLETE` status** — explicitly Out of
  Scope, a distinct post-Finalize-migration concern.
- `scripts/cleanup_tests.py` (found via graphify traversal) is an unrelated sibling tool — it kills
  orphaned `pytest`/`ai_worker_daemon`/`arena_runner` **processes**, not files, and has no file-level
  overlap with `data/runs/`/`release_proof/` cleanup. Do not conflate the two or attempt to merge
  them; flagging only so it isn't mistaken for prior art on this exact concern.

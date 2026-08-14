---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260714-DATA-RUNS-VERIFY-REGEN
artifact_type: investigation
tags: [ai, workflows, process-improvement]
---

# Investigation — TCK-20260714-DATA-RUNS-VERIFY-REGEN

## Current Behavior

### The checkpoint code exists, unmodified, since 2026-07-08

`.claude/workflows/implement-ticket.js:757-800` contains the post-Test cleanup checkpoint block added
by `TCK-20260708-DATA-RUNS-CLEANUP-TIMING` (landed in commit `9b0d09f` on 2026-07-08T22:43:23+07:00 /
2026-07-08T15:43:23Z). `git log --follow -p -- .claude/workflows/implement-ticket.js` shows five later
commits touching the file (07-09 through 07-12), none of which touch lines 757-800 — the block is
byte-identical to what the prior ticket shipped. It is a bare, non-`phase()`-anchored block:

```js
const cleanupOutput = await bash(
  `python3 -c "
import sys
sys.path.insert(0, 'tools')
from gate_checks.done_checker_static import clean_data_runs_early
status, evidence = clean_data_runs_early(${JSON.stringify(startTs || null)})
print(status + '|' + evidence)
"`
)
```
(lines 771-779), deliberately not wrapped in a new `phase()` call — the prior ticket's plan.md is
explicit about this: "No new `phase()` call / `meta.phases` entry — keep the checkpoint's events
attributed to the `Test` phase label to minimize blast radius on the monitoring schema."

`tools/gate_checks/done_checker_static.py::clean_data_runs_early` (lines 163-211),
`check_data_runs_clean` (148-160), and their shared primitive `_find_flagged_data_run_files` (115-146)
are all present, unmodified, and covered by 4 pre-existing tests
(`test_clean_data_runs_early_detects_and_removes_leftover_artifacts`,
`test_clean_data_runs_early_preserves_files_older_than_start_ts`,
`test_clean_data_runs_early_reuses_check_data_runs_clean_definition`,
`test_clean_data_runs_early_returns_fail_on_deletion_error`) plus a doc-guard test
(`test_data_runs_clean_status_appears_in_failure_recovery_reference_table`) —
`tests/tools/test_done_checker_static.py` currently has 52 test functions total.

### Direct evidence: the checkpoint's own bash() call has never actually executed

`agent-monitoring/tools.jsonl` (52,319 rows, 2026-06-13 → 2026-07-14, no rotation gap in this window)
logs every `Bash` tool invocation from every session, including bare orchestrator-run `bash()` calls
embedded directly in `implement-ticket.js` (not just agent-spawned ones) — confirmed by cross-checking
Parity phase's own orchestrator-run calls (`expected_subsystems_for_files`, the P0 scan, and
`cross_reference_touched`), which appear 33 times across the file's history and specifically inside all
three cited runs' own transcripts (e.g. `TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE` seq 6,
`2026-07-14T04:10:37.693716Z`, `"from gate_checks.parit..."`, `duration_ms: 1338`).

Searching the **entire** `tools.jsonl` history for `clean_data_runs_early` returns exactly 2 hits:
1. `2026-07-08T13:05:49Z` — a `grep` for the function's own test names, run by the `implementer` agent
   *while building the original checkpoint* (not an invocation of the function itself).
2. `2026-07-14T15:19:55Z` — this investigation's own `grep -c "clean_data_runs_early" ...` a few minutes
   ago.

**Zero real invocations.** Correspondingly, `grep -c "DATA_RUNS_CLEAN_FAILED" agent-monitoring/events.jsonl`
returns 1, but that single hit is the *implementer's own commit-summary text* from the original
2026-07-08 ticket ("Moved data/runs+release_proof cleanup to a new post-Test orchestrator checkpoint
(DATA_RUNS_CLEAN_FAILED on deletion error only)...") — not a real fired status. The `DATA_RUNS_CLEAN_FAILED`
gate has never actually returned, and — more importantly — the `CLEANED`/`PASS` success path (which
would also require the same `bash()` call to run) has never been observed either.

Traced directly in all three cited runs' `tools.jsonl` slices: in every case, the last orchestrator/agent
activity attributed to the Test-phase `seq` bucket runs right up to the moment the Parity-phase (or
Verify-phase, when Parity is skipped) `current_run` marker write appears, with **no intervening
`clean_data_runs_early` bash call** in between — e.g. `PIPELINE-WIRE`: Test's last activity
(`evaluate_simq.py --dry-run`, ending `04:10:34Z`) is followed 3 seconds later directly by Parity's own
`expected_subsystems_for_files` call (`04:10:37.693716Z`) — no checkpoint call in between.

### Root cause: `implement-ticket.js` is not executed by a JS runtime — it is read and manually
### transcribed by an LLM orchestrating agent, per a translation table that has no row for this call shape

`.claude/skills/implement-ticket/SKILL.md`'s "Action" section (lines 24-41) is explicit: **"Do not call
the Workflow tool — it is not available. Execute the workflow directly: 1. Read
`.claude/workflows/implement-ticket.js` in full... 2. Execute each phase block in order, translating JS
constructs to tool calls..."** — followed by a fixed translation table covering exactly six construct
shapes: `phase('Name')`, `log(msg)`, `await agent(prompt, {agentType, schema})`, `await agent(prompt,
{label})`, a gate condition (`if (x.verdict !== ...) {...return...}`), `await writeMonitoring(status)`,
and `return {...}`. **There is no row for a bare, standalone `const x = await bash(...)` statement that
is not itself inside an `agent()` call, and no general "execute every `bash()` call you encounter"
instruction.** This matches the prior investigation's independent finding
(`stored_artifacts/TCK-20260708-DATA-RUNS-CLEANUP-TIMING/investigation.md`) that no JS test harness or
interpreter exists for this file — the file is pseudocode read and hand-executed by an LLM, not run by
`node`.

This does not mean *all* bare `bash()` calls are silently skipped — Parity's own bare `bash()` calls
(`expected_subsystems_for_files`, the P0 scan, `cross_reference_touched`) reliably execute (33
occurrences). The decisive difference: SKILL.md's own "### Parity" prose section (lines 323-329)
*explicitly narrates* those calls — "Step 0: When the full agent call is not skipped, the orchestrator
runs `tools/gate_checks/parity_updater_static.py::expected_subsystems_for_files(...)` via `bash()`
before the agent call..." — giving the orchestrating agent an explicit instruction anchored to the
Parity phase it is already executing. **SKILL.md's "Pipeline (standard tier)" list (lines 43-63) is a
strict 0-11 phase-numbered enumeration** (Context search, Scope, Investigate, Plan, Review, Implement,
Architecture-Verify, Test, Parity, Security-Review, Verify, Finalize) that the orchestrating agent
treats as its operating checklist across a multi-hour run. **The post-Test cleanup checkpoint is not a
`phase()` and is not mentioned anywhere in SKILL.md** — neither in the numbered Pipeline list nor in any
prose section — precisely because the prior ticket deliberately chose not to add a new `phase()` entry
to avoid touching `meta.phases`/the monitoring schema (a locally sound decision that had the unintended
side effect of making the checkpoint invisible to the one document that governs how the orchestrating
agent actually behaves). `docs/ai/ticket-lifecycle.md` (lines 307-315) *does* document the checkpoint
correctly, but that file is a reference doc, not part of the "read `implement-ticket.js`, execute per
SKILL.md's Action section" instruction chain a live run follows.

`TCK-20260708-SKILL-IMPLEMENT-TICKET-PHASE-DRIFT` (done, same day) is directly on point: it fixed
SKILL.md's Pipeline list for a *different*, earlier drift (missing Architecture-Verify/Security-Review
phase names) and explicitly reasoned "since SKILL.md's own Action section instructs the executing agent
to... execute each phase block directly from the .js, this is unlikely to cause a functional pipeline
skip" for named phases — but a non-`phase()` inline block is exactly the shape that ticket's own
reasoning doesn't cover, and that ticket never touched (out of scope, filed for phase-name drift only).

**Conclusion:** the ticket's own Assumption ("assumes the regenerating agent is `parity-updater` and/or
`done-checker` itself") is **not confirmed** by direct evidence, and the balance of evidence points to a
different, more fundamental mechanism: **the post-Test checkpoint has structurally never executed in
any observed run since it shipped**, independent of which phase or agent's own Bash activity later
populates `data/runs/`. This fully explains all three cited runs uniformly without needing a
per-run-specific "which agent regenerated it" story, and explains why the retro's AC #6 follow-up signal
("next 5 runs show zero Verify-phase failures citing uncleaned `data/runs/`") never held — the fix never
ran, not even once.

### Secondary, compounding finding: agents *do* independently re-run pytest, but this is not the gap

Not fully ruled out and worth carrying forward as a secondary factor: `tools.jsonl` for all three runs
shows `test-scoper` (via its own `git stash push/pop` re-verification dance),
`parity-updater` (re-running specific test files to confirm cited `test_path`s, e.g.
`.venv/bin/python3 -m pytest tests/unit/tactical/test_objective_pursuit_co...` at `11:41:12Z` in the
`ECONOMY-INTENT-GENERATION-GAP` run), and `done-checker` (re-running pytest during its own first Verify
pass in `PIPELINE-WIRE`, e.g. `04:20:37Z`/`04:20:52Z`) all independently execute pytest beyond their
documented minimum mandate — confirming the ticket's observation about a "pipeline culture that rewards
independently confirming claims." **This is real, but it is not necessary to explain the observed
failures**, since Test phase's own documented, mandatory scoped-pytest run (never in dispute) is already
sufficient to populate `data/runs/` — the checkpoint that was supposed to clean that up immediately
after simply never fires. If Plan chooses to insert a second checkpoint immediately before Verify's DoD
check (per the ticket's Scope), it additionally needs to account for this secondary source, but the
primary, load-bearing gap is the first checkpoint's total non-execution.

### An unrelated, likely session-interleaving artifact in the LOOPDET-NONDETERMINISM run

`TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`'s `tools.jsonl` slice between Test (`07:15:53Z`)
and Verify (`07:38:42Z`) — a 23-minute gap — contains substantial activity with no plausible connection
to this ticket: an `AskUserQuestion` about formalizing "D21" in an audit program, multiple
`pytest tests/simulation_quality/test_grade_regression.py` and `test_accumulator.py` runs, exploration
of frontend structure/security surface/deployment maturity/resilience testing, and writes to
`experiments/audit_expansion/PROPOSAL.md` (matching this repository's own most recent commit,
`a4319e24`, "Add experiments/ sandbox proposals... 11-dimension audit expansion"). This reads as
unrelated, tangential work in the same Claude Code session getting attributed to this run's `seq`
bucket because `.claude/current_run` was last set by the Test phase and doesn't update until Verify's
own write. It is flagged here as a data-quality caveat on this one run's evidence (its
`test_grade_regression.py`/`test_accumulator.py` executions plausibly wrote `data/runs/` artifacts too,
independent of anything phase-related) — not as a mechanism this ticket needs to fix, and out of scope
per the ticket's own boundaries. It does NOT change the primary finding above, which rests on the
`PIPELINE-WIRE` and `ECONOMY-INTENT-GENERATION-GAP` runs' cleaner evidence as well.

## Mechanics / Engine Constraints

Not applicable — confirmed by grep of all `docs/parity_ledger/*.yaml` for
`data/runs|release_proof|done-checker|clean_data_runs_early|implement-ticket`. The only hits are in
`docs/parity_ledger/infrastructure.yaml` (INFRA-263/264/265/~4082/4094 region) and are unrelated:
citations of `implement-ticket.js`'s registry-regen bash() call site (`run_finalize_selfcheck`), the
scope-ticket-relocate helper, and the *simulation*-run-output convention
(`data/runs/{run_id}/simulation_events.jsonl`) — the same distinction the prior investigation already
drew between agent-workflow `data/runs/` cleanup and simulation telemetry output. This is Claude
agent-workflow tooling, not gameplay simulation code; no `docs/mechanics/` chapter or `docs/engine/`
contract applies. Matches and confirms the ticket's own Assumption.

## Parity Ledger Overlap

**None.** No parity ledger entry references this mechanism. Same conclusion, same method, as the prior
`TCK-20260708-DATA-RUNS-CLEANUP-TIMING` investigation.

## Prior Work

- `stored_artifacts/TCK-20260708-DATA-RUNS-CLEANUP-TIMING/` — built `clean_data_runs_early`,
  `_find_flagged_data_run_files`, and the post-Test insertion point this ticket must not weaken. Its own
  "Residual Risk: Concurrent-Session Overlap Window" section anticipated a *second, literally concurrent*
  `implement-ticket` session as the failure mode for the mtime-lower-bound logic — it did not anticipate
  (and could not have, from static reading alone) that the checkpoint's own `bash()` invocation would
  never fire at all. That gap is orthogonal to anything that ticket's own tests or code review could have
  caught, since there is no JS test harness (confirmed again here) and static code review cannot detect
  "an LLM orchestrator will skip a non-`phase()`-anchored construct its translation table doesn't name."
- `TCK-20260708-SKILL-IMPLEMENT-TICKET-PHASE-DRIFT` (done) — fixed a different SKILL.md/`.js` drift
  (missing phase names in the Pipeline list) the same day. Its own reasoning ("since SKILL.md instructs
  the agent to execute each phase block directly from the .js, this is unlikely to cause a functional
  pipeline skip") is specifically about *named phases* and does not cover non-`phase()` inline blocks —
  this ticket's finding is a new, adjacent failure mode that ticket did not anticipate or address.
- `TCK-20260705-WORKFLOW-PARITY-SKIP` — established the "orchestrator runs `bash()` directly, not a new
  `agent()`" pattern that both the Parity phase's `expected_subsystems_for_files`/P0-scan calls *and* the
  now-apparently-non-executing `clean_data_runs_early` call use. The Parity instance of this pattern
  works reliably (confirmed by 33 tools.jsonl occurrences) specifically because SKILL.md's own prose
  narrates it under the Parity phase — a distinction not previously drawn out until this investigation.
- `TCK-20260705-GATE-DET-DONE-CHECKER` — built `run_static_precheck`, which `done-checker`'s own agent
  prompt (`.claude/agents/done-checker.md`, "Step 0") is instructed to run as its first action. This
  Step-0 pattern *does* reliably execute (confirmed: `python3 -c "...run_static_precheck..."` appears at
  the start of `done-checker`'s own turn in all three cited runs, e.g. `PIPELINE-WIRE` `04:19:51Z`)
  because it is embedded directly in the *agent's own* `.md` definition, not the orchestrator's `.js`
  pseudocode read and hand-transcribed by a separate LLM turn. This is the strongest available precedent
  for "what actually gets executed reliably" and is directly relevant to the fix-location decision below.

## Risks and Open Questions

1. **Fix-location decision, materially reframed by this investigation — flagging for Plan, not
   pre-deciding.** The ticket's Scope assumes the fix is "move or duplicate the `clean_data_runs_early()`
   sweep... so it also runs immediately before `done-checker`'s DoD check" as a *second orchestrator-run
   `bash()` block* in `implement-ticket.js`, mirroring the first. Given the evidence above, inserting a
   second checkpoint in the *same shape* (bare `bash()`, no `phase()`, unmentioned in SKILL.md's
   Pipeline/prose) carries a strong risk of repeating the exact non-execution failure this investigation
   found — the diff would look correct and pass architecture review, but the retro would likely show the
   same zero-effect outcome in five weeks. The evidence instead favors embedding the cleanup call as a
   mandatory Step 0 action inside `done-checker`'s *own* agent prompt (`.claude/agents/done-checker.md`),
   parallel to how `run_static_precheck` is already Step 0 there and demonstrably executes reliably
   (confirmed above) — i.e., make the cleanup part of what the agent itself is instructed to do, not part
   of orchestrator pseudocode a separate LLM turn must remember to transcribe. This is a genuine
   plan-phase decision with two structurally different implementations (orchestrator `.js` block vs.
   agent-prompt Step 0) and should not be pre-decided here, per the Uncertainty Rule — but Investigate
   flags a strong evidence-based recommendation for the second option, and any choice of the first option
   should additionally require a corresponding SKILL.md prose update (see Risk 2) to have a chance of
   actually executing.
2. **If the orchestrator-`.js`-block shape is chosen anyway, SKILL.md must be updated in the same
   change**, adding an explicit prose sentence narrating the new checkpoint the same way Parity's `Step 0`
   calls are narrated — otherwise this ticket will ship a second checkpoint with the same class of defect
   its own root-cause finding just diagnosed. This directly extends the ticket's own Scope item ("Update
   `docs/ai/ticket-lifecycle.md`'s Verify/Finalize phase documentation...") to also cover
   `.claude/skills/implement-ticket/SKILL.md`, which the ticket's Related Docs list did not originally
   name — flagging as a likely Scope gap for Plan to confirm.
3. **This finding cannot be fully closed with certainty from historical logs alone.** The evidence (zero
   real `clean_data_runs_early` invocations across 5+ weeks and 3+ cited runs, contrasted with 33 reliable
   sibling-shape invocations that ARE narrated in SKILL.md) is strong and consistent, but it is inference
   about how a *separate, already-completed* LLM orchestrating turn behaved, not a direct transcript of
   its reasoning. If Plan or a future retro finds a run where `clean_data_runs_early` demonstrably did
   fire (a `CLEANED` or explicit `PASS`-with-nothing-to-clean log line, or a real `DATA_RUNS_CLEAN_FAILED`
   status), that would falsify this investigation's primary finding and the fix should be reconsidered.
4. **Whether the LOOPDET-NONDETERMINISM run's tangential activity represents a genuine
   concurrent/interleaved-session risk worth a follow-up ticket** (distinct from this ticket's scope) —
   flagging only, not resolving; `.claude/current_run`'s lack of true session/PID scoping for
   `data/runs/` mtime attribution is the same pre-existing, explicitly-accepted tradeoff from the prior
   ticket's plan.md, now observed to also cause misattribution inside `tools.jsonl`'s own `seq` field
   when unrelated work happens mid-run in the same terminal. Out of scope for this ticket; noting for a
   possible future ticket.

## Anti-Drift Hazards

- **Do not implement a second checkpoint as a bare, unnarrated `bash()` block and consider the ticket
  done.** Per this investigation's primary finding, that repeats the original defect's exact shape. If
  Plan adopts the orchestrator-`.js` approach despite the recommendation above, it must ship together
  with a SKILL.md prose update in the same change.
- **Do not touch `check_data_runs_clean`'s or `clean_data_runs_early`'s mtime/`start_ts` definition** —
  same Out-of-Scope boundary as the prior ticket; this ticket is about *whether the call happens*, not
  *what counts as clean*.
- **Do not remove or weaken the first (post-Test) checkpoint, the Finalize-phase prose backstop, or
  `check_data_runs_clean`'s Verify-phase role** — all explicitly required to remain, per Scope.
- **Do not conflate `data/runs/{run_id}/simulation_events.jsonl`** (simulation telemetry convention) **with
  the agent-workflow `data/runs/` cleanup** this ticket addresses — same recurring distinction from prior
  tickets in this area, reconfirmed here.
- **Do not assume `tools.jsonl` is a complete, gapless record of every historical Bash call** — it is
  strong circumstantial evidence (cross-validated via the 33 reliably-firing sibling calls), not a
  formal execution trace with guaranteed completeness; treat the "zero invocations" finding as
  well-supported but not metaphysically certain (see Risk 3).
- **Any new test asserting "the checkpoint executes" must be a static, deterministic check** (e.g. of
  `clean_data_runs_early`/its call site's presence and, if the agent-prompt approach is chosen, of
  `done-checker.md`'s own Step 0 text) — not an attempt to literally simulate an LLM orchestrator's
  turn-by-turn behavior, which is not something pytest can do. Mirrors the prior ticket's own Anti-Drift
  guard ("No test should assert on `implement-ticket.js`'s literal prompt text... testing prose, not
  behavior") — extend that same caution to any new SKILL.md/agent-prompt text this ticket adds.

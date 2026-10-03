---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260711-EPIC-SCOPE-ORPHAN-FIX
artifact_type: investigation
tags: [epic, scope, orphan, workflow]
---

# Investigation — TCK-20260711-EPIC-SCOPE-ORPHAN-FIX

## Current Behavior

**`.claude/workflows/implement-ticket.js` — Scope phase, ticketId-provided branch (current file, lines 53-134).**

- Step 1 (lines 57-62) locates the ticket file: check `tickets/inprogress/{id}.md` (1a), then
  `tickets/done/{id}.md` (1b), then `find tickets/todos -name "{id}.md"` (1c). Step 1c's exact
  current text (line 61): `Copy it to tickets/inprogress/${ticketId}.md so it enters the standard
  workflow location, then use that as ticket_path.` — this runs **unconditionally**, with no tier
  check, because tier is not read until the next step.
- Step 2 (line 64): `read the file at ticket_path. Extract the ## Tier field` — this happens
  **inside the same agent() call**, after the copy already executed as part of the same prompt's
  instructions.
- Orchestrator JS (line 137): `const tier = tierOverride || ticketInfo.tier || 'standard'` — the
  orchestrator itself only learns `tier` after `await agent(...)` resolves (line 53-134 spans the
  single `agent()` call).
- Epic branch (lines 340-348): `if (tier === 'epic') { ... await writeMonitoring('EPIC_SCOPED');
  return {...} }` — returns immediately. No Finalize phase, no cleanup call, nothing downstream of
  this `return` ever touches `tickets/todos/` or `tickets/inprogress/` again for this ticket_id.
- Finalize phase (lines 1021-1069), step 3 (lines 1039-1049): the **only** site in the file that
  removes a `tickets/todos/` original (`rm "${ticketInfo.todos_source_path}"`), conditioned on
  `ticketInfo.todos_source_path` being non-empty. Finalize is unreachable from the epic branch —
  confirmed by tracing execution from line 340's `return` forward; there is no other call to
  Finalize logic or to `rm`/`mv` of a todos file anywhere else in the 1172-line file.
- Net effect confirmed: for an epic-tier ticket originating under `tickets/todos/**`, Step 1c's
  copy creates a permanent second on-disk copy the moment Scope returns `EPIC_SCOPED` — this
  matches the ticket's root-cause claim exactly, re-verified against current line numbers (shifted
  only slightly from the ticket's cited "~60-62" / "~340-348" / "~1040-1043" to the current
  61 / 340-348 / 1039-1049 — no material drift).

**Live repo state right now** (`ls tickets/inprogress/`): exactly two files —
`TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME.md` (tier=standard, legitimately paused — its todos
original also still exists at `tickets/todos/workflow-execution-determinism/`, which is the
**expected, normal** mid-workflow dual-presence state for a non-epic ticket pending Finalize
reconciliation) and `TCK-20260711-EPIC-SCOPE-ORPHAN-FIX.md` itself (tier=standard, this ticket,
same expected mid-flight dual state — its todos original is at
`tickets/todos/epic-scope-orphan-cleanup/`). Neither is an orphan under the ticket's own
definition (dual presence is only a defect for epic tier, since only epic tier never reaches
Finalize). `TCK-20260710-WORKFLOW-EXECUTION-DETERMINISM-EPIC.md` (the one confirmed-live epic
orphan instance) is absent from `tickets/inprogress/` — confirmed manually cleaned in a prior
session, consistent with the ticket's own Assumption.

**`tools/agent-monitoring/epic_staleness_check.py::discover_candidate_epics()` (lines 119-163).**
Epic_id-mode loop (lines 121-136) scans `tickets/inprogress/*.md`, filters `## Tier` == `epic`,
and uses that as the sole discovery path for epic tickets resting there. This is why the ticket's
Assumptions section correctly supersedes the original "skip the copy for epic tier" framing —
skipping the copy would make todos-originated epics permanently invisible to this scan.

**`tools/gate_checks/done_checker_static.py` — confirmed current signatures:**
```python
def check_ticket_location(
    ticket_id: str, inprogress_dir: Path = Path("tickets/inprogress")
) -> tuple[str, str]:                                          # lines 214-220

def check_ticket_finalized(ticket_id: str) -> tuple[str, str]: # lines 350-362
    # checks done_path exists AND inprogress_path does NOT exist

def run_finalize_selfcheck(ticket_id: str, tier: str) -> list[dict]:  # lines 461-472
    # aggregates 4 Part-B (post-Finalize) checks: migration_complete, ticket_finalized,
    # working_log_exactly_one_row, registry_entry_regenerated
```
Both `check_ticket_location` (used by `run_static_precheck`, Verify-phase pre-check) and
`check_ticket_finalized`/`run_finalize_selfcheck` (Finalize-phase self-check) are **never invoked
for epic tier** — epic returns at line 340-348, before Verify or Finalize phases run. Neither
function today detects the dual-presence orphan signature (todos original + inprogress copy for
the same epic-tier ticket_id simultaneously) — that check does not exist yet.

**`tools/gate_checks/workflow_meta_conformance.py`** (most recently added gate_checks module,
this same repo, immediately prior commit) establishes the CLI pattern to mirror: a single
aggregate function returning `list[dict]` with `{"condition"/"phase": ..., "status": "PASS"/"FAIL"/
"NA", "evidence": ...}` shape, plus a standalone `if __name__ == "__main__": print("MARKER:" +
json.dumps(result))` entrypoint — explicitly built "ready for a future ticket to wire in without an
interface change," i.e. not called from any workflow phase yet. This is the closer structural
precedent for the new check than `run_finalize_selfcheck`, since the new check likewise has no
natural in-pipeline call site for epic tier (see Risks below).

## Mechanics / Engine Constraints

This ticket is agent-infrastructure/ticket-lifecycle tooling only — it does not touch simulation
state, entities, combat, economy, strategy, or world-generation code. No chapter of
`docs/mechanics/` or contract in `docs/engine/` governs this behavior. The applicable constraints
are CLAUDE.md's own process rules:
- "Repo state is consistent" (Definition of Done) — the defect being fixed is a direct violation
  of this rule (a permanent byte-identical duplicate on disk).
- `docs/ai/ticket-lifecycle.md:440` (epic staleness check description) confirms `tickets/inprogress/`
  is the legitimate, documented resting place for `epic_id`-mode epic tickets — the fix must
  preserve this placement, not remove it (ticket's own Out of Scope item 3 makes this explicit).

## Parity Ledger Overlap

None. Searched all `docs/parity_ledger/*.yaml` for `workflow`, `ticket-scoper`, `implement-ticket`
substrings. The only hits are in `infrastructure.yaml`: CI workflow file references
(`.github/workflows/test.yml`), `src/lab/workflows.py` (`Workflow.run()` simulation-lab entries,
unrelated), and one entry (~line 3712-3735) about `run_finalize_selfcheck`'s 4th tuple element
(`registry_entry_regenerated`) explicitly scoped "Ticket-closing workflow tooling only -- no
simulation behavior is involved." None reference Scope-phase todos→inprogress transfer or
epic-tier cleanup. No existing entry needs its `status`/`v2_evidence` updated, and no new entry is
needed — consistent with every sibling ticket in this same family (`TCK-20260710-STEP0-TS-
ORCHESTRATOR-BASH`, `TCK-20260710-CURRENT-RUN-SIDECAR-BASH`, `TCK-20260710-WORKFLOW-META-
CONFORMANCE-CHECK`), none of which touched `docs/parity_ledger/`.

## Prior Work

- **TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC** (epic, done, folder
  `tickets/done/agent-bookkeeping-determinism/`) established the precedent this ticket's Scope
  bullet 2 explicitly invokes: move agent-prompt-text "remember to do this mechanical thing"
  instructions into orchestrator-side `bash()`/`captureTs()`/`writeSidecar()` calls, when the
  orchestrator already has, or can deterministically derive, the needed value *before* the
  `agent()` call — never requiring the agent to interpret content to produce it.
- **Key finding from re-reading this precedent against implement-ticket.js's actual current
  structure:** the ticket's own Assumptions/Open Questions frames the cp/rm decision as blocked by
  an ordering deadlock — "tier isn't known until AFTER the ticket-scoper agent call returns... but
  the copy/move decision needs to happen inside the Scope agent's own file-location logic, which
  runs before tier is known within the SAME agent call." Re-verifying this against the live file:
  **this framing is only true for the create-new-ticket branch** (lines 88-132), where tier is
  genuinely inferred by agent judgment from free-text request content — correctly out of this
  ticket's scope, confirmed unaffected. **It is not true for the ticketId-provided (load-existing)
  branch** (lines 53-87), where `## Tier` is a static fact already written to disk in the ticket
  file, located via the same mechanical Step 1a/1b/1c search the agent currently performs. The
  orchestrator can perform that same file-location + tier-grep itself, in `bash()`, before ever
  calling `agent()` — this is the same shape as `captureTs()`/`writeSidecar()`: a value the
  orchestrator can compute deterministically without agent interpretation. See Risks #1 for the
  concrete recommendation.
- **TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH** (done) and its sibling
  **TCK-20260710-CURRENT-RUN-SIDECAR-BASH** are the two completed children of the epic above —
  both replaced 10-15 agent-prompt "Step 0/0b" sites with orchestrator `bash()` calls placed
  immediately before each corresponding `agent()` call. Their own regression test file,
  `tests/tools/test_step0_ts_orchestrator.py`, asserts **exact literal adjacency strings** between
  the new orchestrator-side capture and the `agent()` call — this is the single highest-risk
  collision point for this ticket's fix (see Risks #2).
- **TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK** (done, most recent `gate_checks/` addition)
  established the standalone `MARKER:`-prefixed CLI shape for a static check not wired into any
  workflow phase — the closest structural precedent for the new orphan-detection check, since (like
  it) the new check has no natural in-pipeline call site for epic tier.
  `tests/tools/test_workflow_meta_conformance.py` establishes the exact test-file pattern
  (`import gate_checks.<module> as X`; `from gate_checks.<module> import fn1, fn2`; `tools/` on
  `sys.path`) to mirror.

## Risks and Open Questions

1. **RESOLVED — the ordering deadlock the ticket poses as an open question is not actually a
   deadlock for the branch Step 1c lives in.** See Prior Work above. Recommendation: add an
   orchestrator-side `bash()` call (a Python one-liner, individually-quoted argv args, following
   the established `writeSidecar`/`p0ScanOutput` convention of never JSON-embedding into the `-c`
   string) that performs the Step 1a/1b/1c file-location search and, if found under `tickets/todos/`,
   greps its `## Tier` line directly, then does `cp`+`rm` (move) if `epic`, or `cp`-only otherwise
   (preserving existing Finalize-reconciliation behavior for hotfix/standard). The orchestrator then
   interpolates the already-known `ticket_path` / `tier` / `todos_source_path` into the prompt as
   stated facts for the agent to echo back verbatim in its Return contract (satisfying
   `TICKET_SCHEMA`'s required fields without asking the agent to re-derive them) — leaving only
   Steps 3/3a/3b (tag→skill mapping, mistag warning) as genuinely agent-interpreted work. This
   should be confirmed with the planner/architecture-reviewer since it changes prompt shape beyond
   the ticket's literal "make it a move" framing, but is the only way to satisfy Scope bullet 2's
   explicit ask ("out of the ticket-scoper prompt's LLM-interpreted text and into deterministic
   orchestrator-side bash()"). A narrower, lower-risk alternative exists (leave Step 1c as
   agent-prompt text but resequence it to run after Step 2's tier read, with the agent choosing
   cp-only vs. cp+rm based on the tier it just read) — this satisfies "move not copy" but not Scope
   bullet 2's "relocate out of agent-prompt text" ask literally. **Flagging as a decision for
   planning**, not assuming which of the two the planner should pick — the ticket's own wording
   leans toward the orchestrator-side version.

2. **Placement relative to `captureTs()` is load-bearing.**
   `tests/tools/test_step0_ts_orchestrator.py:31` asserts the exact literal adjacency string
   `"const scopeTs = await captureTs()\nconst ticketInfo = await agent("` with zero intervening
   lines (verified: this is item 0 of `_IMPLEMENT_TICKET_ADJACENCY`, checked by
   `test_ts_capture_bash_precedes_each_covered_agent_call`). If the new orchestrator-side cp/rm
   `bash()` call is inserted between `scopeTs` capture and the `agent()` call, this existing,
   passing regression test breaks. **The new bash() call must be placed before `const scopeTs =
   await captureTs()`** — there is no semantic reason the ts-capture must follow the cp/rm logic,
   and this ordering leaves the existing adjacency string, and its test, untouched.

3. **The prompt's Return contract still needs `ticket_path`/`tier`/`todos_source_path`** even under
   the orchestrator-side approach, since `TICKET_SCHEMA.required` includes `tier` and the
   orchestrator reads `ticketInfo.ticket_path`/`ticketInfo.todos_source_path` downstream. Simplest
   path: keep the schema fields; change the prompt text so these three are stated as pre-computed
   facts to echo back, not values to derive — no schema change needed.

4. **The new static check cannot be folded into `run_finalize_selfcheck`, `check_ticket_location`,
   or `check_ticket_finalized`** — all three are Finalize/Verify-adjacent and structurally
   unreachable for epic tier (confirmed: epic branch returns before either phase runs). The new
   check must be a standalone aggregate function + standalone `MARKER:`-prefixed CLI (mirroring
   `workflow_meta_conformance.py`'s shape), doing a direct repo-wide sweep of
   `tickets/inprogress/*.md` cross-referenced against `tickets/todos/**/*.md` — not run_id-scoped
   like `workflow_meta_conformance.py` (this check has no run_id input; it's closer in shape to
   `epic_staleness_check.py`'s advisory, repo-wide sweep). **Open question for planning:** should
   this new module live in `tools/gate_checks/` (ticket's own Related Code Areas implies this, by
   analogy to `done_checker_static.py`) even though it is never wired into `done-checker`'s own
   pipeline call site — or should it live alongside `epic_staleness_check.py` in
   `tools/agent-monitoring/` given its repo-wide-sweep shape is closer to that module than to any
   `gate_checks/` module? The ticket's Related Code Areas names `tools/gate_checks/
   done_checker_static.py` as the mirror target for shape only ("mirroring... check_ticket_location's
   (status, evidence) tuple shape"), not necessarily the target file/package — flagging as a
   decision, not assuming placement.

5. **Sweep logic must still be built and tested even though zero live orphans exist right now** —
   per the ticket's own Assumption, explicitly re-confirmed true in this investigation (see Current
   Behavior — live repo state). Test coverage must use a synthetic fixture (tmp_path-based, mirroring
   `test_workflow_meta_conformance.py`'s fixture-builder pattern), not rely on the live repo alone.

6. **Live-repo dual-presence for non-epic tickets is not a bug and must not be flagged.** Two
   tickets exist in this exact dual-presence shape right now
   (`TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME`, and this ticket itself) — both tier=standard,
   both legitimately mid-workflow pending Finalize. Any new check that flags dual presence
   regardless of tier would immediately false-positive against the live repo today. This is the
   single highest-value regression/anti-drift test to write (see test_plan.md).

## Anti-Drift Hazards

- Do not touch the create-new-ticket branch (lines 88-132) — Out of Scope explicitly excludes it,
  and it is confirmed correctly unaffected (tier is genuinely agent-inferred there; no todos file
  ever pre-exists for a brand-new ticket).
- Do not change `check_ticket_location`'s or `check_ticket_finalized`'s existing signatures or
  return shapes — both have direct call sites (`run_static_precheck`, `run_finalize_selfcheck`)
  exercised by many existing tests in `test_done_checker_static.py`; the new check must be
  additive, never a modification of either.
- Do not insert any new logic between `const ticketInfo = await agent(` and `{ label: 'scope',` —
  `test_current_run_sidecar_orchestrator.py::test_scope_phase_call_site_has_no_preceding_sidecar_write`
  (lines 134-144) asserts no `writeSidecar(` call in that exact span. A plain cp/rm `bash()` call
  placed before `captureTs()` (per Risk #2's recommendation) naturally avoids this span entirely.
- Do not break `epic_staleness_check.py`'s epic_id-mode discovery — it depends on tier=epic tickets
  continuing to land at `tickets/inprogress/{id}.md` after the fix. "Move" preserves this; "skip the
  copy entirely" (the superseded original framing) would have broken it.
- Do not remove or weaken the Finalize-phase `rm` step (lines 1039-1049) for hotfix/standard
  tickets — it remains the correct, sole cleanup mechanism for non-epic tiers; the new epic-tier
  move logic is additive/parallel, not a replacement.
- Do not fold in the sibling `epic_staleness_check.py::discover_candidate_epics()` double-discovery
  dedupe fix — explicitly tracked separately in `TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK`, a
  distinct file with its own test file, created in parallel.
- Do not expand the orchestrator-side determinism move beyond the cp/rm decision into Steps
  3/3a/3b's tag→skill mapping logic — that consolidation is separately named as an out-of-scope
  "related idea" in `TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC`'s own Out of Scope section.
  Resist the temptation to "clean up" more of the Scope prompt than this ticket's own bullets ask
  for.
- Do not skip the AC #4 live-repo verification just because the synthetic-fixture tests pass —
  synthetic tests alone satisfy AC #1-3 but not AC #4's literal "running this new check against the
  live repo post-fix returns zero orphans."

---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260927-PHASE-PROMPTS-OMIT-GATE-PRECONDITIONS
phase: done
date: 2026-09-27
tags: [process-improvement, testing, agent-monitoring]
---

# TCK-20260927-PHASE-PROMPTS-OMIT-GATE-PRECONDITIONS

## Title

implement-ticket's Test and Verify phase prompts omit the precondition their own gate enforces

## Status

DONE

## Tier

hotfix

## Type

repair

## Priority

P2

## Request Summary

The W39 retro (`agent-monitoring/retro/RETRO-2026-W39.md`, § "What failed most?") recorded two
known gate patterns that recurred even though both were already written down. The retro's proposed
action was "put both preconditions where the agent that trips them will see them". Scoping showed
that for one of them this is **already done and did not work**, and the real cause is in
`.claude/workflows/implement-ticket.js`'s own phase prompts in both cases.

**1. test-scoper under-scopes or cherry-picks files; `test_scope_coverage_static` rejects them.**
7 rejection events all-time, latest `TCK-20260923-SHADOW-REVIEWER-VOCABULARY-GAP` seq 8. 6 of the 7
are a required directory missing entirely (`tests/unit/domains/` 3 times, plus `observability/`,
`world/`, `core/`); only 1 is cherry-picked files. An injected floor fixes both shapes.
The bare-directory rule has been in `.claude/agents/test-scoper.md` (§ Scoping Rules, "Once a test
directory is in scope, always pass its bare directory path") since
`TCK-20260831-HOTFIX-TEST-SCOPER-BARE-DIRECTORY-RULE`. It recurred 3 times after that fix landed
(2 on 2026-09-04, 1 on 2026-09-23).
The Test phase's task prompt (`implement-ticket.js`, `phase('Test')`) says nothing about it:
- Step 1 says "Map each changed src/ file to its tests/unit/ counterpart", and "counterpart" reads
  per-file.
- Step 3 says only "Build the scoped pytest command".

The orchestrator already owns the exact answer. `tools/gate_checks/test_scope_coverage_static.py`
exposes `expected_test_dirs_for(path)`, and the orchestrator calls that module right *after* the
agent returns, to reject it. The required set is computed deterministically, but only after the
agent has guessed.

**2. done-checker blocks on the `tickets/todos/` copy that the pipeline itself leaves there.**
6 BLOCKs all-time of this exact shape, latest
`TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE` seq 10. This is not an operator slip:
- Scope *deliberately* copies a non-epic ticket from `tickets/todos/` to `tickets/inprogress/` and
  leaves the original in place (`resolveScopeTicketLocation` and its comment; prompt text "copied,
  with the todos original left in place, otherwise").
- Finalize deletes it (`phase('Finalize')` step 3, `rm "${ticketInfo.todos_source_path}"`).
- Verify runs between them. Its prompt never mentions `todos_source_path`, and neither
  `.claude/agents/done-checker.md` nor `tools/gate_checks/done_checker_static.py` mentions
  `tickets/todos/` at all.

So done-checker's LLM judgment of "repo state is consistent" sees an unexplained duplicate that the
pipeline is guaranteed to create. It blocks some of the time, which matches the "inconsistently
flags it" wording in the operator note. Every block costs a Verify round-trip. The operator
workaround (delete the copy before Verify) races the pipeline's own Finalize step.

## Scope

1. **Test phase:** before the test-scoper `agent()` call, compute the required test directories from
   `implementation.files_changed` using `expected_test_dirs_for()`, the same function the
   post-agent gate uses. Do not reimplement its mapping in JS. State the result in the prompt as a
   floor: the command must include at least these directories, as bare paths. Also reword Steps 1
   and 3 so that "counterpart" means a directory, not a file.
2. **Verify phase:** when `ticketInfo.todos_source_path` is non-empty, pass it into the done-checker
   prompt as an expected, pipeline-owned copy that Finalize deletes after Verify. Tell done-checker
   that this exact path is not a repo-consistency failure.
3. **`.claude/agents/done-checker.md`:** one rule saying that a `tickets/todos/` copy of the ticket
   under check fails only when the caller has *not* declared it as pending Finalize cleanup. A
   hand-orchestrated caller that did not declare it still gets flagged, which is correct: on that
   path nothing else will delete it.
4. **Tests:** cover both prompt changes with the repo's existing `implement-ticket.js` prompt-text
   test pattern. If none exists for these phases, add tests that assert the rendered prompt contains
   the computed directories and the declared todos path.

## Out of Scope

- **Removing or weakening either gate.** `test_scope_coverage_static` and done-checker both catch
  these correctly. The fix is to show the agent the precondition before it acts, not to relax the
  check (CLAUDE.md: never edit an artifact to make a gate pass).
- **Changing Scope's copy-not-move behavior for non-epic tiers.** It is a documented choice
  (`resolveScopeTicketLocation`'s comment: "preserving existing Finalize-reconciliation behavior"),
  and it presumably keeps the todos original intact if a run fails partway. Re-deciding it needs its
  own investigation. This ticket only makes Verify aware of it.
- Changing `expected_test_dirs_for()`'s mapping.
- `test-scoper.md`'s existing bare-directory rule stays as it is. Do not duplicate it into more
  places. The prompt should cite the computed list, not restate the rule's prose.

## Acceptance Criteria

1. The Test phase prompt contains the required directory list, computed by the orchestrator via
   `expected_test_dirs_for()` from `files_changed` before the agent runs. No JS copy of the mapping
   exists (grep-verifiable).
2. For any `files_changed`, the directories injected into the Test prompt are exactly the ones the
   post-agent gate then requires. A command made only of the injected bare directories passes
   `check_test_scope_coverage()`. Pin this with a test.
3. When `todos_source_path` is non-empty, the Verify prompt names that exact path as expected and
   deleted by Finalize. When it is empty, the prompt says nothing about todos (no unconditional
   text).
4. `done-checker.md` states the declared-vs-undeclared rule in one place. An undeclared
   `tickets/todos/` duplicate is still reported.
5. Scoped tests for the changed workflow and agent-prompt areas pass.
6. Record a before/after measurement in the ticket's Completion Summary. Before: 7 test-scoper
   scope-rejection events and 6 done-checker todos-duplicate BLOCKs all-time, from this ticket's
   Request Summary. After: re-count from the corpus at the next retro. Put a dated placeholder for
   the "after" figure in `agent-monitoring/retro/` notes rather than claiming zero now.

## Related Tickets

- `TCK-20260831-HOTFIX-TEST-SCOPER-BARE-DIRECTORY-RULE`: added the agent-file rule. It recurred 3
  times after that, which is the evidence for this ticket.
- `TCK-20260902-HOTFIX-TEST-SCOPE-COVERAGE-AI-SYSTEMS-ALLOWLIST-GAP`: the gate's mapping.
- `TCK-20260711-EPIC-SCOPE-ORPHAN-FIX`: introduced orchestrator-side ticket-location resolution
  (copy for non-epic).
- `TCK-20260705-GATE-DET-DONE-CHECKER`: the deterministic done-checker companion.

## Related Docs

- `agent-monitoring/retro/RETRO-2026-W39.md` § "What failed most?". Its "put the bare-directory
  requirement in test-scoper's own prompt" action was already in place. This ticket supersedes that
  half of the action.
- `docs/guides/agent_monitoring.md`

## Related Stored Artifacts

None.

## Related Code Areas

- `.claude/workflows/implement-ticket.js`: `phase('Test')`, `phase('Verify')`,
  `resolveScopeTicketLocation`, `phase('Finalize')` step 3
- `.claude/agents/done-checker.md`, `.claude/agents/test-scoper.md` (read-only reference)
- `tools/gate_checks/test_scope_coverage_static.py`: `expected_test_dirs_for`,
  `check_test_scope_coverage`

## Assumptions / Open Questions

- Assumption: done-checker's todos-duplicate BLOCKs come from its LLM "repo state is consistent"
  judgment, not a scripted condition. Supported by the absence of any `todos` reference in
  `done_checker_static.py`. Verify from one of the 7 events' checklist evidence if it is still
  available.
- Open: is there an existing test harness that renders `implement-ticket.js` phase prompts? If not,
  the implementer chooses the lightest faithful way to pin AC1–AC3. Asserting on the script source
  alone is acceptable only if it is honestly labelled as such.

## Implementation Notes

Scoped by agent-working-design 2026-09-27. Counts come from
`agent-monitoring/data/*/events.jsonl` in the design worktree at `origin/main` `04f911110`:
- test-scoper: `status == failed` with a summary matching scope-coverage wording.
- done-checker: `status == failed` with a summary mentioning `todos`.

Counts corrected after independent re-derivation. The first scan's regexes gave 8 and 7, and each
included one false match:
- `TCK-20260923-SHADOW-REVIEWER-VOCABULARY-GAP` seq 9 is a real test failure found *after*
  re-scoping. It is not a rejection; its summary only contains the word "bare".
- `TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR` seq 9 is the folder-archival step (an empty
  `tickets/todos/ai-docs-followups/` skeleton), not a same-ticket duplicate. The implementer caught
  this one.

Match on summary meaning, not keywords.

## Test Summary
- `python3 -m pytest tests/tools/test_phase_prompts_gate_preconditions.py -v` — **11 passed** (new
  file): AC1 (computed-before-agent-call placement, no JS mapping copy, prompt states the floor,
  Steps 1/3 reworded), AC2 (injected dirs alone satisfy `check_test_scope_coverage()`, empty for
  unmapped files), AC3 (Verify prompt declares `todos_source_path` conditionally, positioned
  inside the Verify prompt not the Test phase), AC4 (`done-checker.md` states the rule once, still
  reports an undeclared duplicate).
- `python3 -m pytest tests/tools/test_step0_ts_orchestrator.py tests/tools/test_scope_orphan_fix.py tests/tools/test_test_scope_coverage_static.py tests/tools/test_done_checker_static.py tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_epic_create_tickets_sidecar_orchestrator.py tests/tools/test_classify_checklist_failure_js_mirror.py tests/tools/test_phase_prompts_gate_preconditions.py` (every existing test touching the same orchestrator regions) — **220 passed**, confirming the new pre-agent `bash()` call's placement (before `captureTs()`, never between `writeSidecar()` and `agent()`) preserves `test_step0_ts_orchestrator.py`'s exact literal-adjacency assertion for the Test phase.
- `node --check .claude/workflows/implement-ticket.js` — syntax OK.
- `pytest tests/tools/ -m "not slow"` (full scoped regression) — **3143 passed, 1 failed** (only
  `test_agent_monitoring_manifest.py::test_build_manifest_reproducible_byte_identical_direct_call`,
  confirmed a pre-existing, unrelated live-file-growth race: it calls `build_manifest()` twice
  directly against the real, actively-appended `agent-monitoring/data/` directory, and this
  session's own concurrent tool calls appended one row between the two reads during the full-suite
  run; passes cleanly in isolation, re-confirmed after this ticket's changes), 25 skipped, 28
  deselected, 1 xfailed.

## Files Changed
- `.claude/workflows/implement-ticket.js` — Test phase: computes the required test-directory
  floor via `expected_test_dirs_for()` (shelled out, no JS mapping copy) before the test-scoper
  `agent()` call, states it in the prompt, rewords Steps 1/3 to mean directory not file. Verify
  phase: declares `ticketInfo.todos_source_path` to done-checker when non-empty.
- `.claude/agents/done-checker.md` — condition 9 gains the declared-vs-undeclared
  `tickets/todos/` rule.
- `tests/tools/test_phase_prompts_gate_preconditions.py` (new) — 11 tests.

## Completion Summary
Both W39 retro gate patterns traced to `implement-ticket.js`'s own phase *task* prompts omitting a
precondition their post-agent gate already enforces, not to the agents' own instruction files
(`test-scoper.md`'s bare-directory rule was already correct and unchanged). The Test phase now
computes the exact required test-directory set via `expected_test_dirs_for()` — the same function
the post-agent `test_scope_coverage_static` check uses — before the agent runs, and states it in
the prompt as a floor; no JS reimplementation of the mapping. The Verify phase now tells
done-checker, when `todos_source_path` is non-empty, that the pipeline's own `tickets/todos/` copy
is expected and Finalize-owned, not a repo-consistency failure; `done-checker.md` gained the
matching declared-vs-undeclared rule so an undeclared duplicate (e.g. a hand-orchestrated closure)
is still correctly flagged. Neither gate was weakened.

Both figures in this ticket's own Request Summary were independently re-derived from scratch by
the implementer and design peer, each catching a different false match the other's first scan had
missed (a real test failure matched on the word "bare"; a folder-archival BLOCK matched on the
word "todos") — corrected to **7 test-scoper rejections / 6 done-checker todos-BLOCKs all-time**
before this ticket's own numbers were used anywhere in the implementation.

Before: 7 test-scoper scope-rejection events, 6 done-checker todos-duplicate BLOCKs, all-time (see
Request Summary). After: to be re-counted at the next retro — placeholder recorded in
`agent-monitoring/retro/RETRO-2026-W39.md`'s Notes (this ticket's own W39 report, generated as the
"before" snapshot per the retro cadence rule, before this commit).

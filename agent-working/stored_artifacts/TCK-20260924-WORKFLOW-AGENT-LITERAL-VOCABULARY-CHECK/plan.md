---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260924-WORKFLOW-AGENT-LITERAL-VOCABULARY-CHECK
artifact_type: plan
tags: [agent-monitoring, workflows, data-quality]
---

# Plan: TCK-20260924-WORKFLOW-AGENT-LITERAL-VOCABULARY-CHECK

## Resolved Open Questions (from ticket's Assumptions section)

1. **Regex vs JS parser**: regex, following `workflow_meta_conformance.py`'s precedent. Confirmed
   in `investigation.md` that all real `writeSidecar(...)` call sites in all 11 files are
   single-line — no multi-line coverage gap exists to guard against with a heavier parser.
2. **Are all 29 literals intentional**: yes, confirmed during investigation re-derivation. Each
   gets its own justifying comment in `vocabulary.py` (Implementation step 3 below), matching the
   `claude`/`orchestrator` precedent standard.
3. **Pipeline wiring vs pytest-only**: pytest-only, per the ticket's own stated smaller/more
   proportionate default. No Finalize-tail wiring in this ticket.
4. **`simq-audit.js`'s 4 agents not grep-confirmed by either literal shape**: left as a documented
   module-docstring note, not solved here (ticket says explicitly "not this ticket's problem").
5. **`is_known_phase()` accessor**: add it (see investigation.md's Decision section) — small,
   symmetrical, and the new check needs it to avoid reaching into `WORKFLOW_PHASES` directly.

## Implementation steps

1. **`tools/agent-monitoring/vocabulary.py`** — additive only:
   - Add `is_known_phase(workflow: str, phase: str) -> bool` immediately after `is_known_agent()`.
   - Add the 6 agent literals to `WORKFLOW_AGENTS["create-tickets"]` (`comprehend`) and
     `WORKFLOW_AGENTS["implement-epic"]` (`batch-monitoring-write`, `discover`, `epic-close`,
     `folder-cleanup`, `tracking-doc-update`), each with a one-line justifying comment (real
     `writeSidecar`/`agent:` call sites in the corresponding `.js` file — `comprehend` additionally
     cites `docs/agent-monitoring/schema.md`'s existing by-name documentation of it).
   - Add 7 new keys to `WORKFLOW_PHASES` for the currently-unkeyed workflows
     (`compact-simulation-result`, `generate-simulation-setup`, `investigate-simulation-result`,
     `prepare-simulation-execution`, `propose-simulation-enhancements`, `register-simulation-result`,
     `update-knowledge-store`), each populated with that workflow's real phase literals (the 23
     total, 21 from these 7 files + `implement-epic`'s `Discover`/`Report` added to its existing
     key), each set carrying a module-header-level comment (matching the file's existing
     per-block-comment convention, not per-literal, since these are plain simulation-lab phase
     names with no individual drift history to narrate) recording that they were grep-confirmed via
     this ticket's own reproduction script.
   - No removals, no renames — diffed at Verify time (AC9).

2. **`tools/gate_checks/workflow_vocabulary_check.py`** (new module) — mirrors
   `monitoring_anomaly_validator.py`'s shape but exits 0 always:
   - `extract_literals_from_workflow_file(path) -> tuple[set[str], set[str]]` — the same
     comment-stripping + 5-call-site-shape scan built in `investigation.md`'s `vocab_scan.py`,
     moved into production code (not reused by import — the investigation script stays a frozen,
     standalone repro artifact per the ticket's own Related Stored Artifacts note; this module is
     its test-covered production twin, kept in sync manually since they answer the same question
     from two different lifecycles: one-time proof vs. ongoing check).
   - `check_workflow_vocabulary(workflows_dir=DEFAULT_WORKFLOWS_DIR) -> List[dict]`:
     - First pass: every `.js` file present in neither `WORKFLOW_PHASES` nor `WORKFLOW_AGENTS` is
       one `FAIL` result naming the file (AC1) — computed independently of the literal-extraction
       pass below, never derived by asking `infer_workflow` anything.
     - Second pass, per file: every extracted agent literal not resolved by `is_known_agent(workflow,
       literal)` is one `FAIL` result (family="agent"); every extracted phase literal not resolved
       by `is_known_phase(workflow, literal)` is one `FAIL` result (family="phase"). Families are
       tagged in the result dict, never merged into one count (AC2).
     - A workflow with zero findings across both families contributes one `PASS` result (so a test
       can assert "zero findings" as an actual empty FAIL list, not an empty result list — matches
       AC3's "reports zero findings" wording most literally as "no FAIL-status rows").
   - `__main__`: `MARKER:` + `json.dumps(result)`, then **always** `sys.exit(0)` regardless of FAIL
     count (AC8) — the one deliberate divergence from `monitoring_anomaly_validator.py`'s exit(1),
     documented in the module docstring so a future reader does not "fix" it into matching that
     sibling.

3. **Tests** — `tests/tools/test_workflow_vocabulary_check.py`, fixture-driven (temp
   `.claude/workflows/`-shaped directory + temp registries passed as function args, never touching
   the real `vocabulary.py` module state) per the sibling tests' own established pattern:
   - AC1: fixture directory with one `.js` file whose stem is absent from both a passed-in
     `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` -> asserts a FAIL naming that file.
   - AC2 (pre-registration state): run `check_workflow_vocabulary()` against the real
     `.claude/workflows/` + a snapshot of pre-registration-state registries (constructed inline in
     the test from the investigation's own recorded literals, not by parsing git history) ->
     asserts exactly 6 agent FAILs + 23 phase FAILs, counted separately.
   - AC3 (post-registration state): run against the real `.claude/workflows/` + the real,
     now-updated `vocabulary.py` -> asserts zero FAIL rows.
   - AC4: fixture file with a commented-out `writeSidecar(...)`, a commented `phase('...')`, a
     commented `agent: '...'` -> asserts none produce a finding.
   - AC5: fixture `writeSidecar(1, 'ThePhase', 'the-agent')` with phase/agent set to visibly
     distinguishable strings -> asserts the phase finding names `'ThePhase'` and the agent finding
     (if unregistered) names `'the-agent'`, never swapped.
   - AC6: fixture literal registered under workflow A's registry key, but appearing in workflow B's
     `.js` file -> asserted as a finding, for both an agent-family and a phase-family fixture.
   - AC7: fixture `create-tickets` agent literal `investigate:some-concern` -> asserts no finding
     (goes through `is_known_agent`, honors the prefix family).
   - AC8: any fixture with at least one finding -> assert the function call itself doesn't raise
     and (separately) that running the module as a subprocess exits 0.
   - AC9: `git diff`-style assertion is out of a unit test's reach (that's a Verify-phase manual
     diff read, see Test Summary), but a test does assert every pre-existing `WORKFLOW_AGENTS`/
     `WORKFLOW_PHASES` entry (captured as a literal snapshot dict in the test file, dated to before
     this ticket's edit) is still present as a subset of the post-edit registries — catches an
     accidental removal even though it can't catch a rename by itself.
   - AC10: recorded as the actual `pytest` invocation + result in the ticket's `## Test Summary`
     at Verify time.

4. **No changes** to `monitoring_anomaly_validator.py` or `AGENT_DRIFT_CEILING` (Scope guard,
   AC9's other half) — grepped for at Verify time to confirm the diff never touches that file.

## Scope guards (explicit, from ticket's Out of Scope)
- No tier-literal check, no `.claude/agents/*.md` check, no literal family outside
  `.claude/workflows/*.js`.
- No pipeline/Finalize wiring.
- No dynamic-agent-name detection.
- `vocabulary.py` edits are additive-only — verified by direct diff read at Verify, not just by a
  test (a test can assert supersetting but a human diff read is the actual AC9 gate).

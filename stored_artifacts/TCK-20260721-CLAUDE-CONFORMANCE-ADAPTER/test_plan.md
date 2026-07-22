---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER
artifact_type: test_plan
tags: [ai, workflows]
---

# Test Plan — TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER

## Regression Surface

Existing tests that must keep passing (nothing in this ticket's scope should touch their targets):

**Unit / tooling:**
- `tests/tools/test_workflow_meta_conformance.py` — all tests, especially
  `test_parses_meta_phases_from_implement_ticket_js` (the exact 11-title live-extraction result this
  ticket's phase-order conformance test must reuse/agree with, not reimplement differently).
- `tests/agent_orchestration/test_contract_structure.py`, `test_bootstrap_vocabulary_equality.py`,
  `test_skills_catalog.py`, `test_validator_errors.py`, `test_validator_no_network_calls.py` — the
  contract's own structural/AST guards must remain green; this ticket reads the contract via
  `load_contract()` but must never modify `agent-orchestration/`'s existing six files' validated
  shape in a way that breaks these.

**Integration (agent replay):**
- `tests/agent_replay/test_runner_no_forbidden_calls.py` — all 5 tests, the AST no-forbidden-calls
  precedent this ticket's own AC #6 guard is modeled on.
- `tests/agent_replay/test_no_mutation_snapshot.py` — both tests, the zero-diff/content-hash
  precedent this ticket's own AC #1 zero-diff-under-`.claude/` proof is modeled on.
- Remaining `tests/agent_replay/` and `tests/fixtures/agent_replay/`-dependent tests (run the full
  `tests/agent_replay/` directory — small, fast, no reason to sub-scope further).

**No `src/` regression surface** — this ticket touches no simulation code; `tests/unit/`,
`tests/parity/`, `tests/integration/` outside the above are out of scope for this ticket's own
verification pass (still covered by CI generally, not re-run here per CLAUDE.md's domain-scoping
rule).

## New Tests Required

Per acceptance criteria (exact file locations are Plan-phase decisions pending the open question in
investigation.md #1/#2 on where the generator output and terminal-status source-of-truth live —
paths below assume a `tools/agent_orchestration_claude_adapter/` or similarly-scoped new package;
adjust to whatever Plan actually names it, but keep it structurally separate from
`tools/agent_orchestration/` since that package is owned by the predecessor ticket):

1. **`test_generator_produces_zero_git_diff_under_claude_before_and_after`**
   Category: integration (containment / no-mutation)
   Verifies: running the read-only "Claude adapter representation" generator against the real repo
   tree produces a `git status --porcelain -- .claude/` output that is identical before and after
   the run (empty-before → still-empty-after; dirty-before → identical porcelain string after, per
   `test_no_mutation_snapshot.py`'s clean-vs-dirty fallback pattern, since a naive
   must-start-clean gate would false-skip in this actively-developed repo).
   Location: new test file under `tests/agent_orchestration/` or a ticket-scoped subpackage's test
   dir — mirrors `tests/agent_replay/test_no_mutation_snapshot.py:73-97`'s two-branch structure,
   watched pathspec swapped to `[".claude/"]`.

2. **`test_phase_order_conformance_byte_identical_to_live_meta_phases`**
   Category: unit / conformance test (AC #2)
   Verifies: the rendered Claude adapter representation's phase-order list equals
   `workflow_meta_conformance.extract_meta_phases(Path(".claude/workflows/implement-ticket.js"))`
   exactly (same list, same order, same string values) — reuse `extract_meta_phases` directly, do
   not reimplement the bracket-depth-scan/regex technique a second time.
   Location: new test module, imports `tools.gate_checks.workflow_meta_conformance.extract_meta_phases`.

3. **`test_terminal_status_extractor_finds_all_13_literal_call_sites`**
   Category: unit (new extractor — genuinely new tooling, no existing precedent to reuse per
   investigation.md)
   Verifies: a new `extract_writemonitoring_literals(workflow_js_path)`-shaped function returns the
   13 literal `writeMonitoring('STRING')` call-site values found in `implement-ticket.js` today:
   `CONFLICTS_DETECTED, TAGS_NOT_REGISTERED, EPIC_SCOPED, NEEDS_HUMAN_INPUT,
   DOC_STALENESS_BLOCKED, TESTS_FAILED, DATA_RUNS_CLEAN_FAILED, PARITY_INCOMPLETE,
   SECURITY_BLOCKED, DOD_BLOCKED, FINALIZE_INCOMPLETE (×2 call sites, same literal — must not be
   deduped away silently or double-counted as a conflict), DONE`. Assert both the multiset (11
   distinct values, 13 call sites) and dedupe correctly to the intentional-duplicate.
   Location: new extractor module + this test.

4. **`test_terminal_status_extractor_finds_verdict_derived_needs_changes_and_blocked`**
   Category: unit
   Verifies: the extractor (or a paired analysis step) also surfaces the 2 verdict-derived call
   sites (`writeMonitoring(review.verdict)` at `:582`, `writeMonitoring(archVerify.verdict)` at
   `:760`) as producing `NEEDS_CHANGES`/`BLOCKED` from the `REVIEW_SCHEMA`/`ARCH_VERIFY_SCHEMA`
   verdict enums — a fixture-based test (not scraping the real enum text, which is fragile) proving
   the extractor's design explicitly accounts for non-literal call sites rather than silently
   missing them.
   Location: same extractor test module.

5. **`test_scope_agent_failed_handling_is_an_explicit_documented_decision`**
   Category: unit / architecture guard
   Verifies: given `SCOPE_AGENT_FAILED` bypasses `writeMonitoring()` entirely (raw `bash()`-embedded
   `record_run.py --data` call, not a JS string literal argument to a named helper), the extractor
   either (a) explicitly captures it via a second, documented extraction pattern, or (b) explicitly
   excludes it with an assertion/comment naming the exclusion and its reason — this test fails if
   the vocabulary this ticket asserts conformance against silently omits `SCOPE_AGENT_FAILED`
   without either path being true. Prevents the extractor's design from silently under-reporting the
   true 15-value (or 16-including-SCOPE_AGENT_FAILED) vocabulary.
   Location: same extractor test module or a dedicated guard test.

6. **`test_human_approved_divergence_marker_is_parsed_and_enforced`**
   Category: unit (per AC #4)
   Verifies: a divergence entry in `agent-orchestration/intentional-divergences.md` lacking the
   defined reviewer+date marker format does NOT suppress a conformance failure (test still fails);
   an entry WITH a correctly-formatted marker DOES suppress it. Needs both a positive and a negative
   fixture case (a malformed/missing-marker divergence entry must not silently pass) — this is the
   single largest net-new behavior this ticket defines, per investigation.md risk #3, so it needs
   the most explicit fixture coverage of any new test here.
   Location: new test module for the divergence-log parser/enforcer.

7. **`test_ast_zero_write_mode_opens_against_implement_ticket_js`**
   Category: architecture guard (AC #6)
   Verifies: an AST scan (mirroring
   `tests/agent_replay/test_runner_no_forbidden_calls.py`'s `_dotted_call_name`/
   `_string_constants_in`/whole-file-string-constant-scan technique) of every `.py` file this
   ticket's own tooling adds finds zero `open(..., "w"...)`/`open(..., mode="w"...)` (and `"a"`,
   `"x"`, `"w+"`, etc. — any write-capable mode) calls whose path argument references
   `implement-ticket.js`, and zero `subprocess.run`/`Popen`/`call`/`check_call`/`check_output`/
   `os.system`/`os.popen` calls referencing it at all (read or write) — subprocessing the file for
   any reason is disallowed by this ticket's containment constraint, not just write-mode opens.
   Location: new test module, structurally parallel to
   `tests/agent_replay/test_runner_no_forbidden_calls.py`.

8. **`test_generator_output_matches_representation_schema_shape`**
   Category: unit (AC #1, generator correctness)
   Verifies: the rendered Claude adapter representation is structurally well-formed (has a phase
   list and a terminal-status list/mapping, per whatever shape Plan decides) and is derivable
   purely from `load_contract()` output plus this ticket's own terminal-status source-of-truth (per
   investigation.md open question #1's eventual resolution) — no ad-hoc string literals duplicating
   contract data outside the loader path.
   Location: same as generator module's test file.

## Scoped Pytest Commands

```
pytest tests/agent_orchestration/ tests/agent_replay/ tests/tools/test_workflow_meta_conformance.py -v
```

Plus, once this ticket's own new test module(s) exist (exact path(s) pending Plan-phase package
naming decision):

```
pytest tests/agent_orchestration/ tests/agent_replay/ tests/tools/test_workflow_meta_conformance.py \
       tests/<new_module_path_for_this_ticket>/ -v
```

Never `pytest tests/` — scoped to the `agent_orchestration`/`agent_replay`/`workflow_meta_conformance`
domain per CLAUDE.md's Testing Rule.

## Anti-Drift Test Guards

- **Duplicate-literal guard** (`FINALIZE_INCOMPLETE` at two call sites): a test must assert the
  extractor's output correctly represents this as one distinct value with two call sites, not as a
  false "conflict" or a silently-deduped single-call-site fact — catches an extractor
  implementation that assumes "one status string → one call site."
- **Verdict-derived-not-literal guard**: a test must assert `NEEDS_CHANGES`/`BLOCKED` are captured
  even though they never appear as a quoted string literal argument to `writeMonitoring(...)` in
  the source — catches an extractor that only handles the literal-string-argument case and silently
  drops the two verdict-derived call sites (which would silently shrink the true vocabulary from 15
  to 13).
- **`SCOPE_AGENT_FAILED` non-silent-omission guard** (test #5 above): catches an extractor design
  that only looks for `writeMonitoring(...)` calls and never considers the raw-`bash()`-embedded
  path, which would otherwise permanently and invisibly exclude this status from all future
  conformance checks.
- **Containment/no-mutation guard against `.claude/`** (test #1): catches any future change to the
  generator that accidentally starts writing a rendered file into `.claude/` instead of a
  contract-adjacent location — this is the ticket's single most important safety property per its
  own AC #1 wording.
- **Scope-boundary guard against the other divergence log**: a test should assert
  `docs/guidelines/intentional_divergences.md`'s file content/mtime is unchanged by any tool this
  ticket builds (mirrors the git-diff-under-`.claude/` proof, applied to the one existing file this
  ticket must never write into) — catches an accidental path collision between the new
  `agent-orchestration/intentional-divergences.md` and the pre-existing mechanics-bible log.
- **`.codex/`/Codex-adapter scope-creep guard**: mirroring
  `test_validator_no_network_calls.py::test_no_conformance_or_provider_adapter_code_in_this_tickets_tree`'s
  `_SCOPE_CREEP_MARKERS` substring scan, applied to this ticket's own new tree — catches this
  ticket's tooling accidentally starting the out-of-scope Codex-side adapter work.
- **`skipped_event` vs. `conditional_absent` distinction guard**: a test asserting the rendered
  representation preserves this distinction (not collapsing both into a generic "skipped") for at
  least one phase of each kind (e.g. `Investigate` for hotfix-tier `skipped_event`,
  `Security-Review` for `conditional_absent`) — catches a rendering bug that silently misrepresents
  Security-Review's real (fully-absent) behavior as merely skipped.

---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE
artifact_type: test_plan
tags: [governance, ai, frontmatter]
---

# Test Plan — TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE

## Scope Note

Per this ticket's own Acceptance Criteria (re-confirmed in `investigation.md`'s Risks section with
direct evidence), this ticket's closable scope is **Step 0 + the usage-baseline dependency check +
the per-agent candidate-scope/taxonomy proposal + Wave 1's rollout** (11 agents:
`doc-updater`, `investigator`, `ticket-scoper`, `done-checker`, `mechanics-auditor`,
`spec-document-reviewer`, `concern-investigator`, `simulation-analyst`, `world-debugger`,
`world-render-reviewer`, `test-scoper`). Wave 2/Wave 3 are explicitly out of scope for this ticket
— no tests below cover them, and no test should be added that assumes their frontmatter exists yet.

## Regression Surface

Existing tests that must keep passing — grouped by domain:

**Unit / structural (agent definition + frontmatter parsing):**
- `tests/tools/test_concern_investigator_agent_definition.py` — the exact pattern this ticket's
  AC #4 parametrizes; must keep passing unmodified in its own right (concern-investigator's
  existing `tools:` field is being kept as-is, not changed, per investigation.md's finding that
  zero usage evidence exists to justify changing it).
- `tests/tools/test_doc_updater_agent_file.py` — pre-existing structural test over
  `doc-updater.md` (already touched by the concurrent, uncommitted
  `TCK-20260904-DOC-COVERAGE-REVERSE-CHECK` sibling ticket's self-check-step addition). Adding a
  `tools:` frontmatter field to this same file must not break this test's existing assertions about
  the file's prose/structure.
- `tools/validate_frontmatter.py` and its test suite (`tests/tools/test_validate_frontmatter.py`) —
  every Wave 1 agent file remains valid frontmatter after the change; run to confirm the new
  `tools:` key doesn't trip any schema validation this script performs on `.claude/agents/*.md`
  (confirm first whether this script even scans `.claude/agents/` — if it only scans `docs/`/
  `tickets/`, this is N/A and should be noted as such rather than assumed).

**Agent-orchestration / contract structure (unaffected, but shares file-family risk):**
- `tests/agent_orchestration/test_contract_structure.py` — run with
  `PYTHONPATH=tools:. pytest tests/agent_orchestration/ -q` (per the sibling
  `TCK-20260904-TEST-SCOPER-HANG-GUARD`'s documented environment note: this file only imports
  successfully with `PYTHONPATH=tools:.`, not the bare `pythonpath=["."]` pytest config). This
  ticket does not touch `agent-orchestration/*.yaml`, so this is a pure regression check, not a
  file this ticket should need to modify.

**Agent-monitoring (read-only check on the shared worktree, since this ticket writes zero code
under `src/` and touches no monitoring write-path):**
- No `tools.jsonl`/`events.jsonl`/`runs.jsonl` regression tests are directly implicated — this
  ticket is a static frontmatter change to `.claude/agents/*.md`, not a monitoring schema/write-path
  change. Included here only to explicitly rule it out, not because a specific test needs running.

## New Tests Required

Per AC #4 ("a parametrized extension of `test_concern_investigator_agent_definition.py`'s
pattern... verify each landed agent's `tools:` field") and AC #3 (candidate-scope documentation):

1. **`test_wave1_agent_files_declare_tools_field`**
   - Category: unit / architecture guard
   - Verifies: for each of the 11 Wave 1 agent filenames, `.claude/agents/{name}.md` (a) exists,
     (b) starts with a valid YAML frontmatter block, (c) that frontmatter includes a non-empty
     `tools:` key, (d) `tools:` parses (comma-split) into a list of known tool names (cross-check
     against a small allowlist of valid tool-name strings — reuse whatever list
     `test_concern_investigator_agent_definition.py` implicitly relies on, or the harness's own
     documented tool names, rather than inventing a new one).
   - Parametrized over the 11 Wave 1 agent names — a single test function, not 11 copy-pasted ones.
   - Where it lives: `tests/tools/test_wave1_agent_tools_frontmatter.py` (new file — distinct from
     `test_concern_investigator_agent_definition.py`, which stays concern-investigator-specific per
     its own existing scope and its `_DISALLOWED_TOOLS`/`_EXPECTED_SCHEMA_REQUIRED_FIELDS`
     constants that are specific to that one agent's create-tickets.js dispatch contract).

2. **`test_wave1_candidate_scope_excludes_known_denied_tools`**
   - Category: unit / architecture guard
   - Verifies: per-agent, the declared `tools:` list does NOT include a small, explicitly-named set
     of tools this investigation classified as excluded (currently: `test-scoper` excludes `Edit`;
     `mechanics-auditor`/`spec-document-reviewer`/`simulation-analyst`/`world-debugger` exclude
     `Write`/`Edit`/`Agent`; `world-render-reviewer` excludes everything except `Read`). Parametrize
     as a table of `(agent_name, forbidden_tool)` pairs sourced directly from investigation.md's
     candidate-scope table so the test and the documented rationale cannot silently drift apart.
   - Where it lives: same new file as test 1, or a second test function in it.

3. **`test_wave1_agents_do_not_declare_disallowed_tools_field`**
   - Category: unit / architecture guard
   - Verifies: none of the 11 Wave 1 agent files declare a `disallowedTools:` key — per
     investigation.md's Step 0 conclusion, Wave 1 uses the `tools:` allowlist pattern exclusively
     (matching the one working local precedent), not the unprecedented-in-`.md`-frontmatter
     `disallowedTools:` denylist. This guards against a future edit accidentally introducing the
     untested field shape.
   - Where it lives: same new file.

4. **`test_agent_tool_usage_baseline_script_still_runs_and_confirms_wave1_gap`** (optional,
   defensive — flag as nice-to-have, not blocking)
   - Category: unit
   - Verifies: `tools/agent-monitoring/agent_tool_usage_baseline.py` still runs cleanly post-Wave-1
     (this ticket does not modify that script, but a defensive re-run test guards against an
     unrelated regression silently breaking the very tool this ticket's own evidence depended on).
   - Where it lives: `tests/tools/test_agent_tool_usage_baseline.py` already exists (per `git
     status`, from the sibling baseline ticket) — check whether this assertion already exists there
     before adding a duplicate; only add if genuinely missing.

## Scoped Pytest Commands

```
pytest tests/tools/test_wave1_agent_tools_frontmatter.py tests/tools/test_concern_investigator_agent_definition.py tests/tools/test_doc_updater_agent_file.py -v
```

```
PYTHONPATH=tools:. pytest tests/agent_orchestration/ -q
```

```
pytest tests/tools/ -q
```
(full `tests/tools/` directory — required per `test-scoper.md`'s own scoping rule for any
flat-`tools/*.py`-adjacent change: this ticket's new file lives in `tests/tools/`, and per that
rule's documented incident history, cherry-picking individual files within an otherwise-correctly-
identified directory is the single most common `test_scope_coverage_static` failure mode across
this project — always run the bare directory.)

Never: `pytest tests/`.

## Anti-Drift Test Guards

- **`test_wave1_candidate_scope_excludes_known_denied_tools`** is itself the primary anti-drift
  guard against silently widening a Wave 1 agent's scope back to "everything" during
  implementation — it pins the exact exclusions investigation.md argued for (especially
  `test-scoper`'s `Edit` exclusion, flagged there as the single most consequential judgment call in
  this ticket).
- A test asserting **no Wave 2/3 agent** (`architecture-reviewer`, `security-reviewer`, `planner`,
  `implementer`, `parity-updater`) gained a `tools:` field as a side effect of this ticket — guards
  against exactly the scope-creep this investigation's Risks section flags as tempting but wrong
  ("since we're already in here"). Simple assertion: for each of those 5 names, either the file has
  no `tools:` key, or if it unexpectedly does, the test fails loudly rather than silently passing —
  this ticket must not be the one that adds it.
- A test confirming `concern-investigator.md`'s `tools:` value is **byte-identical** to its
  pre-ticket value — investigation.md's explicit finding is "keep as-is, zero evidence to change
  it," so any diff to this one file's `tools:` line during Wave 1 implementation is itself a
  regression signal, not an improvement.

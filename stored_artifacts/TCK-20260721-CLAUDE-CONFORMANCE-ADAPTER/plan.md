---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER
artifact_type: plan
tags: [ai, workflows]
---

# Implementation Plan — TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER

## Summary

The investigation found a blocking gap: `agent-orchestration/` (built by the DONE
`TCK-20260721-ORCHESTRATION-CONTRACT-CORE`) has zero terminal-status representation, so this
ticket's own AC #3 has nothing to diff against. This plan resolves that by extending the contract
itself — adding a new sibling file `agent-orchestration/terminal-statuses.yaml` — as this ticket's
own Step 1, and amending the ticket's Related Code Areas to include `agent-orchestration/`
accordingly. All new tooling lives in a fresh package, `tools/agent_orchestration_claude_adapter/`,
kept structurally separate from `tools/agent_orchestration/` (owned by the predecessor ticket,
whose `loader.py`/`generator.py` are read-only reused via `load_contract()` but never edited here).
The plan builds, in order: the contract extension; a new terminal-status extractor for
`.claude/workflows/implement-ticket.js`; a rendered-representation generator that writes only under
`agent-orchestration/rendered/`; a phase-order conformance test reusing
`workflow_meta_conformance.extract_meta_phases` directly; a terminal-status conformance test; the
`agent-orchestration/intentional-divergences.md` divergence log plus approval-aware conformance
logic; an AST no-write/no-subprocess guard against `implement-ticket.js`; a zero-diff-under-`.claude/`
containment test; and a Codex-side scope-creep guard mirroring the predecessor ticket's own
`_SCOPE_CREEP_MARKERS` pattern. No file under `.claude/` or `docs/guidelines/intentional_divergences.md`
is ever touched. Because Step 1 populates the new contract file directly from the same live
extraction Step 2 performs, this ticket's own build produces zero real divergences — the divergence
log ships with the format defined but no entries, satisfying AC #5 by construction rather than by
after-the-fact reconciliation.

## Related Code Areas — Amendment

The ticket's original "Related Code Areas" section does not list `agent-orchestration/`. Per the
investigation's explicit instruction, this plan amends that section to add:
- `agent-orchestration/terminal-statuses.yaml` (new file, created by Step 1)
- `agent-orchestration/rendered/` (new directory, created by Step 3)
- `agent-orchestration/intentional-divergences.md` (new file, created by Step 6)

`agent-orchestration/`'s existing six files (`contract.yaml`, `workflows/implement-ticket.yaml`,
`roles/*.yaml`, `skills.yaml`, `monitoring-schema.yaml`, `hook-events.yaml`) and
`tools/agent_orchestration/{loader.py,generator.py}` are read-only reused, never edited, by this
plan.

## Steps

### Step 1 — Extend the contract with terminal-status data
**Files:** `agent-orchestration/terminal-statuses.yaml` (new file)

**Change:** Add a new sibling file to the six existing contract files, at
`agent-orchestration/terminal-statuses.yaml`. Not a field on `workflows/implement-ticket.yaml`
because the shape is fundamentally different — phases are an ordered sequence, terminal statuses
are an unordered set reachable through three distinct emission mechanisms. Per the investigation's
own versioning note, a new sibling file needs no `workflow_version` bump. Content (own
`terminal_status_schema_version: 1`, all 15 distinct values confirmed by investigation's
line-by-line re-read of `implement-ticket.js`, cross-checked against `docs/agent-monitoring/schema.md`'s
`final_status` table):

```yaml
terminal_status_schema_version: 1
workflow_id: implement-ticket
statuses:
  - value: CONFLICTS_DETECTED
    kind: literal
    phases: [Scope]
  - value: TAGS_NOT_REGISTERED
    kind: literal
    phases: [Scope]
  - value: EPIC_SCOPED
    kind: literal
    phases: [Scope]
  - value: SCOPE_AGENT_FAILED
    kind: bypass
    phases: [Scope]
  - value: NEEDS_HUMAN_INPUT
    kind: literal
    phases: [Investigate]
  - value: NEEDS_CHANGES
    kind: verdict_derived
    phases: [Review, Architecture-Verify]
  - value: BLOCKED
    kind: verdict_derived
    phases: [Review, Architecture-Verify]
  - value: DOC_STALENESS_BLOCKED
    kind: literal
    phases: [Architecture-Verify]
  - value: TESTS_FAILED
    kind: literal
    phases: [Test]
  - value: DATA_RUNS_CLEAN_FAILED
    kind: literal
    phases: [Test]
  - value: PARITY_INCOMPLETE
    kind: literal
    phases: [Parity]
  - value: SECURITY_BLOCKED
    kind: literal
    phases: [Security-Review]
  - value: DOD_BLOCKED
    kind: literal
    phases: [Verify]
  - value: FINALIZE_INCOMPLETE
    kind: literal
    phases: [Finalize]
  - value: DONE
    kind: literal
    phases: [Finalize]
```

`kind` vocabulary: `literal` (single `writeMonitoring('STRING')` call site), `verdict_derived`
(`writeMonitoring(<var>.verdict)`, value not a source literal, shared across two phases),
`bypass` (never passed through `writeMonitoring()` — currently only `SCOPE_AGENT_FAILED`, written
via a raw `bash()`-embedded `record_run.py --data` call). Include a header comment citing this
ticket's investigation.md as the extraction source and the line numbers as of 2026-07-22.

**Do NOT touch:** `agent-orchestration/contract.yaml`, `workflows/implement-ticket.yaml`,
`roles/*.yaml`, `skills.yaml`, `monitoring-schema.yaml`, `hook-events.yaml` — none of the six
existing files change shape or content. Do NOT modify `tools/agent_orchestration/loader.py` to
teach `ContractBundle` about this new file — it stays a standalone file read by this ticket's own
new package (Step 2), keeping `ContractBundle`'s dataclass shape (and every test asserting it,
e.g. `test_contract_structure.py`) untouched.

**Verify:** `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py` (Step 2)
reads this file and asserts its 15 entries match the live extraction exactly — cross-file
comparison is verified transitively by Steps 2 and 5. In addition (Review-phase Fix A, required):
this step now also gets its own standalone schema/shape validation, independent of the live
comparison, so a malformed entry surfaces as a named validation error rather than an opaque
downstream mismatch:

- `terminal_status_loader.py::validate_terminal_statuses(data: dict) -> None` (added in Step 3's
  file, since that's where the loader lives) — raises a new `TerminalStatusValidationError`
  (mirrors `tools/agent_orchestration/errors.py`'s flat-exception style) naming the exact offending
  entry when: `terminal_status_schema_version` is missing or not `1`; `workflow_id` is missing;
  `statuses` is missing, empty, or not a list; any entry is missing `value`, `kind`, or `phases`;
  any entry's `kind` is not one of `literal`/`verdict_derived`/`bypass`; any entry's `phases` is
  empty or not a list of strings; any two entries share the same `value` (duplicate).
- New test file `tests/agent_orchestration_claude_adapter/test_terminal_status_schema.py`
  (independent of Step 2's live-extraction tests) exercises this validator against: (a) the real
  committed `agent-orchestration/terminal-statuses.yaml` (must pass cleanly), and (b) a table of
  synthetic malformed fixtures — missing `kind`, invalid `kind` enum value, duplicate `value`,
  missing `terminal_status_schema_version` — each asserted to raise `TerminalStatusValidationError`
  naming the specific field/entry at fault.

---

### Step 2 — Build the terminal-status extractor
**Files:** `tools/agent_orchestration_claude_adapter/__init__.py` (new),
`tools/agent_orchestration_claude_adapter/terminal_status_extractor.py` (new),
`tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py` (new)

**Change:** New package `tools/agent_orchestration_claude_adapter/` (kept separate from
`tools/agent_orchestration/`). `terminal_status_extractor.py` provides, mirroring
`workflow_meta_conformance.py::extract_meta_phases`'s read-only `Path.read_text()` + regex
technique exactly (no JS parser, no subprocess):

- `extract_literal_statuses(workflow_js_path: Path) -> list[dict]` — regex
  `writeMonitoring\('([^']+)'\)` over the full file text, returning `{"value": str, "kind": "literal"}`
  per match, in source order. Finds all 13 literal call sites (12 distinct values —
  `FINALIZE_INCOMPLETE` appears at two call sites).
- `extract_verdict_derived_statuses() -> list[dict]` — returns a **fixed, documented constant**
  `[{"value": "NEEDS_CHANGES", "kind": "verdict_derived"}, {"value": "BLOCKED", "kind": "verdict_derived"}]`,
  not scraped from `REVIEW_SCHEMA`/`ARCH_VERIFY_SCHEMA` enum text (per test_plan's explicit
  "fixture-based, not scraping the real enum text, which is fragile" instruction). A companion
  regex `writeMonitoring\((\w+)\.verdict\)` confirms (in a separate, documented step) that the
  live file still contains exactly 2 such call sites, so a future edit that adds/removes a
  verdict-derived call site is caught, without the *value set* itself depending on parsing the
  enum.
- `extract_bypass_statuses(workflow_js_path: Path) -> list[dict]` — regex targeting the
  `bash()`-embedded `record_run.py --data` JSON payload, e.g.
  `"final_status"\s*:\s*"([^"]+)"` scoped to lines containing `record_run.py`, returning
  `{"value": "SCOPE_AGENT_FAILED", "kind": "bypass"}`. Captures `SCOPE_AGENT_FAILED` explicitly
  per investigation risk #6 — decided in-scope (not silently excluded).
- `extract_all_terminal_statuses(workflow_js_path: Path) -> list[dict]` — aggregates all three,
  deduping by `value` (not by call-site count), so `FINALIZE_INCOMPLETE`'s two call sites collapse
  to one entry with `call_sites: [line, line]`. Returns exactly 15 distinct entries against the
  live file today.

All functions are read-only (`Path.read_text()` only) — no `open(..., "w")`, no `subprocess`, no
`os.system`.

**Do NOT touch:** `.claude/workflows/implement-ticket.js` (read-only diff target only — never
opened in write mode, never subprocessed). Do NOT put this module under `tools/agent_orchestration/`.

**Verify:** `test_terminal_status_extractor_finds_all_13_literal_call_sites`,
`test_terminal_status_extractor_finds_verdict_derived_needs_changes_and_blocked`,
`test_scope_agent_failed_handling_is_an_explicit_documented_decision` (test_plan items 3, 4, 5) —
all in `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py`.

---

### Step 3 — Build the rendered-representation generator (reusing `load_contract()` read-only)
**Files:** `tools/agent_orchestration_claude_adapter/terminal_status_loader.py` (new),
`tools/agent_orchestration_claude_adapter/generator.py` (new),
`agent-orchestration/rendered/claude-adapter.yaml` (new, generated + committed),
`tests/agent_orchestration_claude_adapter/test_generator_containment.py` (new),
`tests/agent_orchestration_claude_adapter/test_terminal_status_schema.py` (new — Fix A's
standalone schema/shape validation test for `terminal_status_loader.py::validate_terminal_statuses`)

**Change:**
- `terminal_status_loader.py::load_terminal_statuses(repo_root: Path) -> list[dict]` — plain
  `yaml.safe_load(path.read_text())` of `agent-orchestration/terminal-statuses.yaml` (Step 1's
  file), calling `validate_terminal_statuses()` (Step 1's Fix-A addition, defined in this same
  file) before returning. Standalone reader, not a `ContractBundle` field — mirrors `loader.py`'s
  "only `yaml.safe_load` + stdlib, no network" philosophy without editing `loader.py` itself.
- `terminal_status_loader.py::TerminalStatusValidationError` (new, flat exception per Step 1's
  Fix-A) and `validate_terminal_statuses(data: dict) -> None` (schema/shape validation, detailed
  in Step 1).
- `generator.py::render_claude_adapter(repo_root: Path, target_dir: Path, *, allow_outside_contract: bool = False) -> Path`:
  1. Calls `tools.agent_orchestration.loader.load_contract(repo_root)` (existing, imported
     read-only) to get `bundle.workflow["phases"]`; extracts `phase_order = [p["name"] for p in bundle.workflow["phases"]]`.
  2. Calls `load_terminal_statuses(repo_root)` for the terminal-status list.
  3. Builds `{"claude_adapter_schema_version": 1, "source_workflow_id": bundle.workflow["workflow_id"], "phase_order": phase_order, "terminal_statuses": statuses}`.
  4. Writes it as YAML to `target_dir / "claude-adapter.yaml"`, guarded by this package's **own**
     write-guard function (a fresh `_assert_write_allowed`-equivalent scoped to
     `repo_root / "agent-orchestration" / "rendered"` — do not import the private
     `tools.agent_orchestration.generator._assert_write_allowed`, since that couples this ticket to
     an internal implementation detail of the predecessor's package). Default caller (this ticket's
     own build step) targets `repo_root / "agent-orchestration" / "rendered"`; refuses to write
     outside it without `allow_outside_contract=True`, exactly mirroring the existing precedent's
     behavior but as an independent implementation.
  5. Run it once for real during implementation to produce and commit
     `agent-orchestration/rendered/claude-adapter.yaml`.

No ad-hoc string literals duplicating contract data — every field in the rendered output traces to
`load_contract()` or `load_terminal_statuses()`.

**Do NOT touch:** `tools/agent_orchestration/generator.py` (do not import or reuse its private
`_assert_write_allowed`; do not add a new `generate()` call site there). Never write outside
`agent-orchestration/rendered/` without the explicit opt-in flag, and never write into `.claude/`
under any circumstance (no flag makes that allowed).

**Verify:** `test_generator_output_matches_representation_schema_shape` (test_plan item 8), run with
`target_dir=tmp_path` (Review-phase Fix B: this test does not need to touch the real
`agent-orchestration/rendered/` directory — it only checks output shape — so it runs against a
`tmp_path` target to avoid rewriting the committed file as a side effect of a schema-shape test).
The zero-git-diff-under-`.claude/` proof (test_plan item 1) moves entirely to Step 8, which is the
one test in this ticket that legitimately must run the generator against the real repo root.

---

### Step 4 — Build the phase-order conformance test (reusing `extract_meta_phases` directly)
**Files:** `tests/agent_orchestration_claude_adapter/test_phase_order_conformance.py` (new)

**Change:** Import `tools.gate_checks.workflow_meta_conformance.extract_meta_phases` directly (no
reimplementation of the bracket-depth scan). Test asserts:
`extract_meta_phases(Path(".claude/workflows/implement-ticket.js"))` == the `phase_order` list
produced by `render_claude_adapter()` (run against a `tmp_path` target, not the committed file, so
the test is self-contained and does not depend on the committed file being fresh — freshness is
Step 8's concern) — same list, same order, same 11 string values, byte-identical per element.

**Do NOT touch:** `tools/gate_checks/workflow_meta_conformance.py` — imported, never edited.

**Verify:** `test_phase_order_conformance_byte_identical_to_live_meta_phases` (test_plan item 2).

---

### Step 5 — Build the terminal-status conformance test
**Files:** `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py` (new)

**Change:** Test asserts `terminal_status_extractor.extract_all_terminal_statuses(Path(".claude/workflows/implement-ticket.js"))`
(Step 2's live extraction, 15 entries) matches `load_terminal_statuses(repo_root)` (Step 1's
contract data, also 15 entries) as a **set of `(value, kind)` pairs** (order-independent — terminal
statuses are not sequential like phases) — full match per AC #3, both directions (no live value
missing from contract, no contract value absent from live). Because Step 1's contract file was
authored directly from this same extraction, this test is expected to pass with zero divergence
entries needed. This test does not yet contain divergence-approval logic — that is added in Step 6
so the diff/approval concerns stay in one place.

**Do NOT touch:** `.claude/workflows/implement-ticket.js`.

**Verify:** New test asserting full match; also exercises `test_terminal_status_extractor_finds_all_13_literal_call_sites`'s
dedupe behavior transitively (`FINALIZE_INCOMPLETE` must appear once on both sides).

---

### Step 6 — Build `agent-orchestration/intentional-divergences.md` + divergence-approval-aware conformance logic
**Files:** `agent-orchestration/intentional-divergences.md` (new file),
`tools/agent_orchestration_claude_adapter/divergence_log.py` (new),
`tests/agent_orchestration_claude_adapter/test_divergence_log.py` (new); extends
`tests/agent_orchestration_claude_adapter/test_phase_order_conformance.py` (Step 4) and
`tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py` (Step 5)

**Change:**
- Divergence entry format (decided, parseable): one `##`-level markdown section per divergence in
  `agent-orchestration/intentional-divergences.md`, each with plain `Key: value` lines (no
  per-entry YAML frontmatter — simpler regex parse, consistent with this file being a human-edited
  log rather than machine-generated data):

  ```markdown
  ## <axis>:<value-or-id>
  Axis: terminal_status | phase_order | gate_policy | artifact_requirements
  Contract-value: <what the contract says>
  Live-value: <what implement-ticket.js actually does>
  Rationale: <free text explaining why this is intentional>
  Approved-by: <reviewer name>
  Approved-date: YYYY-MM-DD
  Status: RATIFIED
  ```

  A divergence only suppresses a conformance failure when its `Axis` + identifying value matches
  the mismatch, `Approved-by` and `Approved-date` (valid `YYYY-MM-DD`) are both present and
  non-empty, and `Status: RATIFIED` (a `DEFERRED` or missing-field entry does NOT suppress —
  mirrors `docs/guidelines/intentional_divergences.md`'s own RATIFIED/DEFERRED status vocabulary
  for terminology consistency, without sharing the file).
- `divergence_log.py::load_divergences(path) -> list[Divergence]` — frozen dataclass
  (`axis, contract_value, live_value, rationale, approved_by, approved_date, status`), line-based
  regex parser (`^Approved-by:\s*(.+)$` etc.), read-only.
- `divergence_log.py::is_approved(divergences, axis, value) -> bool` — the single function both
  Step 4's and Step 5's conformance tests call before failing on a mismatch: if a matching,
  fully-approved entry exists, the test records the divergence as intentional (e.g. via a soft
  assertion / xfail-style branch) instead of hard-failing.
- Wire this into Step 4 and Step 5's tests: both diffs run first; any mismatch is checked against
  `is_approved()` before the test fails.
- Ship `agent-orchestration/intentional-divergences.md` with the format documented in a header
  comment and **zero divergence entries** — Step 1's contract data was authored directly from Step
  2's live extraction, and Step 4 found no phase-order divergence, so this ticket's own build has
  nothing to log. This satisfies AC #5 ("every divergence found during this ticket's own build is
  intentional and reviewed") by construction: there are none.

**Do NOT touch:** `docs/guidelines/intentional_divergences.md` (Out of Scope, explicit — different
file, different subsystem, different field format). Do not let any generator/test code
accidentally resolve a path into that file; the AST/path-guard in Step 7's spirit should also cover
this (see Step 8).

**Verify:** `test_human_approved_divergence_marker_is_parsed_and_enforced` (test_plan item 6) —
both a positive fixture (well-formed entry suppresses a synthetic mismatch) and a negative fixture
(missing `Approved-by`/`Approved-date`, or `Status: DEFERRED`, does NOT suppress).

---

### Step 7 — Build the AST no-write-mode/subprocess guard test against `implement-ticket.js`
**Files:** `tests/agent_orchestration_claude_adapter/test_no_forbidden_calls_against_implement_ticket_js.py` (new)

**Change:** AST scan (mirroring `tests/agent_replay/test_runner_no_forbidden_calls.py`'s
`_dotted_call_name`/`_string_constants_in`/whole-file-string-constant-scan pattern exactly) of
every `.py` file under `tools/agent_orchestration_claude_adapter/` (all files from Steps 2, 3, 6),
asserting:
- Zero `open(..., "w"|"a"|"x"|"w+"|...)` calls whose path argument's string constants contain
  `implement-ticket.js`.
- Zero `subprocess.run`/`Popen`/`call`/`check_call`/`check_output`/`os.system`/`os.popen` calls
  anywhere that reference `implement-ticket.js` in any string constant in the call (read or write —
  subprocessing the file for any reason is disallowed, not just write-mode).
- Whole-file string-constant scan (not just call-argument-scoped), per the precedent's own
  documented rationale, so an indirect `PATH = "...implement-ticket.js"` followed by a dynamic call
  is also caught.

Run this scan against the full new package once Steps 2, 3, and 6 exist, so it covers everything
built in this ticket.

**Do NOT touch:** `tests/agent_replay/test_runner_no_forbidden_calls.py` — read as a pattern only,
not imported or modified.

**Verify:** New test module; this step's own tests are self-verifying (they are the guard).

---

### Step 8 — Zero-diff-under-`.claude/` containment test (+ divergence-log path isolation guard)
**Files:** `tests/agent_orchestration_claude_adapter/test_claude_containment.py` (new)

**Change:** Mirrors `tests/agent_replay/test_no_mutation_snapshot.py`'s clean-vs-dirty
porcelain/content-hash fallback pattern exactly, watched pathspec swapped to `[".claude/"]`. This
is the one test in the ticket that legitimately runs the generator against the real repo root
(Review-phase Fix B moved the schema-shape check in Step 3 off the real tree, onto `tmp_path`, so
only this containment proof still touches the committed `agent-orchestration/rendered/` output):
- If `git status --porcelain -- .claude/` is empty before, run `render_claude_adapter()` against
  the real repo root (target_dir defaulted to `agent-orchestration/rendered/`), then assert
  porcelain is still empty after.
- If dirty before (uncommon for `.claude/` but must not false-skip), take a content hash of every
  file under `.claude/` before and after, assert identical.
- Additionally assert `docs/guidelines/intentional_divergences.md`'s mtime and content hash are
  unchanged after running every tool built in this ticket (test_plan's "Scope-boundary guard
  against the other divergence log") — proves no accidental path collision between the new
  `agent-orchestration/intentional-divergences.md` and the pre-existing mechanics-bible log.

**Do NOT touch:** Do not use a `tmp_path` copy for this specific test — it must run against the
real `.claude/` directory to be a meaningful containment proof (per the precedent's own stated
rationale for using the real tree).

**Verify:** `test_generator_produces_zero_git_diff_under_claude_before_and_after` (test_plan item
1, AC #1) and the scope-boundary guard from test_plan's Anti-Drift Test Guards section.

---

### Step 9 — Codex-side scope-creep guard
**Files:** `tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py` (new)

**Change:** Decided in-scope (cheap, closes the loop the predecessor ticket started from its own
side). Mirrors `tests/agent_orchestration/test_validator_no_network_calls.py::test_no_conformance_or_provider_adapter_code_in_this_tickets_tree`'s
`_SCOPE_CREEP_MARKERS` substring scan, applied to this ticket's own new tree
(`tools/agent_orchestration_claude_adapter/`, `tests/agent_orchestration_claude_adapter/`,
`agent-orchestration/terminal-statuses.yaml`, `agent-orchestration/rendered/`,
`agent-orchestration/intentional-divergences.md`): asserts no `.codex/` path reference, and no
`conformance_diff`/`claude_conformance` module-name string appears anywhere in this ticket's own
`.py`/`.yaml`/`.md` files (scoped to avoid false-positiving on this ticket's own legitimate
self-description, e.g. this plan.md itself is not scanned — only the shipped code/contract tree is).

**Do NOT touch:** No `.codex/` files created. Do not implement any Codex-side adapter logic.

**Verify:** New test module; self-verifying guard, run once all other steps' files exist.

## Scope Guards

- Never open, write, or subprocess-touch `.claude/workflows/implement-ticket.js` from any tool
  built in this ticket (Steps 2, 3, 6's tooling) — read-only `Path.read_text()` only.
- Never write to `docs/guidelines/intentional_divergences.md` — Out of Scope, explicit. All
  divergence logging in this ticket goes only to the new `agent-orchestration/intentional-divergences.md`.
- Never implement the Codex-side adapter — no `.codex/` files, no `conformance_diff`/
  `claude_conformance` module names (Step 9 enforces this from this ticket's own side).
- Never modify `tools/agent_orchestration/{loader.py,generator.py}` or any of `agent-orchestration/`'s
  original six files (`contract.yaml`, `workflows/implement-ticket.yaml`, `roles/*.yaml`,
  `skills.yaml`, `monitoring-schema.yaml`, `hook-events.yaml`) — read via `load_contract()` only.
- Never write outside `agent-orchestration/rendered/` from the new generator without an explicit
  `allow_outside_contract=True` opt-in, and never write into `.claude/` under any flag combination.
- Do not conflate `skipped_event` with `conditional_absent` in the rendered representation — Step
  3's `render_claude_adapter()` must pass through `workflows/implement-ticket.yaml`'s existing
  `tiers`/`condition`/`if_false` fields unmodified (via `load_contract()`), not collapse them.
- Do not treat `NEEDS_CHANGES`/`BLOCKED` as belonging to a single call site or a single phase —
  Step 1 and Step 2 both model them as `phases: [Review, Architecture-Verify]`.
- Do not assume "one status string → one call site" — `FINALIZE_INCOMPLETE`'s two call sites must
  dedupe to one entry (Step 2), never double-counted as a conflict.
- No `src/` simulation code, `docs/mechanics/` chapter, or `docs/engine/` contract is touched by
  any step — confirmed not applicable per investigation's Mechanics/Engine Constraints section.

## Dependency Map

- Step 1 (contract extension) blocks Step 2 (extractor needs contract data to compare against in
  its own tests) and Step 3 (generator reads `terminal-statuses.yaml`).
- Step 2 (extractor) blocks Step 5 (terminal-status conformance test needs the live-extraction
  function) and Step 7 (AST guard scans Step 2's files).
- Step 3 (generator) blocks Step 4 (phase-order test calls `render_claude_adapter()`) and Step 8
  (containment test runs the generator against the real tree).
- Steps 4 and 5 (the two conformance tests) block Step 6 (divergence-approval logic extends both).
- Step 6 blocks Step 7 and Step 9 only in the trivial sense that they scan/guard its files too —
  no logical dependency.
- Step 8 depends on Step 3 (needs `render_claude_adapter()` to exist to run the containment check)
  and conceptually follows Step 6 (asserts the other divergence log's isolation).
- Step 9 has no dependency beyond "run after all other steps' files exist" (it scans the whole new
  tree).
- Steps 1, 2, 3 must land in that order (1 before 2 and 3; 2 can proceed in parallel with 3 once 1
  is done). Steps 4 and 5 can proceed in parallel once 3 (and 2, respectively) are done. Step 6
  requires 4 and 5. Steps 7, 8, 9 are last, in any order relative to each other, once 1–6 are done.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Read-only generator renders a Claude adapter representation from the contract; zero git diff under `.claude/` before/after | Step 3 (generator), Step 8 (containment proof) | `test_generator_produces_zero_git_diff_under_claude_before_and_after` |
| Conformance test extracts LIVE phase order from `meta.phases` and asserts byte-identical match to rendered representation | Step 4 | `test_phase_order_conformance_byte_identical_to_live_meta_phases` |
| Conformance test extracts LIVE terminal-status vocabulary (~13 literal + 2 verdict-derived) and asserts full match to the contract's status representation | Step 1 (contract data), Step 2 (extractor), Step 5 (conformance test) | `test_terminal_status_extractor_finds_all_13_literal_call_sites`, `test_terminal_status_extractor_finds_verdict_derived_needs_changes_and_blocked`, `test_scope_agent_failed_handling_is_an_explicit_documented_decision`, new terminal-status conformance test |
| Any mismatch fails UNLESS a matching human-approved entry exists in `agent-orchestration/intentional-divergences.md` | Step 6 | `test_human_approved_divergence_marker_is_parsed_and_enforced` |
| AST-based test asserts zero write-mode opens and zero subprocess calls against `implement-ticket.js` | Step 7 | new AST guard test module (Step 7) |
| Every divergence found during this ticket's own build is intentional and reviewed before close | Step 1 + Step 6 (zero divergences by construction; format + enforcement mechanism exists and is tested) | `test_human_approved_divergence_marker_is_parsed_and_enforced`; manual confirmation that `intentional-divergences.md` has zero unapproved entries at Finalize |

## Anti-Drift Notes

- **`SCOPE_AGENT_FAILED` is explicitly included, not silently dropped.** It bypasses
  `writeMonitoring()` structurally (raw `bash()`-embedded `record_run.py --data` call at
  `implement-ticket.js:178-183`). Step 1 models it with `kind: bypass`; Step 2's extractor captures
  it via a second, distinct regex pattern targeting the JSON payload, documented as its own
  function (`extract_bypass_statuses`) rather than folded into the `writeMonitoring(...)` literal
  scan. Omitting it would under-report the true vocabulary and violate AC #3's "full match" wording.
- **`FINALIZE_INCOMPLETE` has two call sites (`:1234`, `:1246`), one value.** Every extractor and
  conformance function dedupes by `value`, never asserts exactly-one-call-site-per-value. Tests
  must assert this is represented as one entry with two recorded call sites, not silently deduped
  away and not flagged as a false conflict.
- **`NEEDS_CHANGES`/`BLOCKED` are shared across two phases via two distinct verdict variables**
  (`review.verdict` at `:582`, `archVerify.verdict` at `:760`), not literal call-site strings. The
  extractor uses a fixed, documented constant for these two values rather than scraping
  `REVIEW_SCHEMA`/`ARCH_VERIFY_SCHEMA` enum text — scraping the enum would be fragile and was
  explicitly rejected by the test plan.
- **`skipped_event` vs. `conditional_absent` must stay distinct** in the rendered representation
  (`Security-Review` is `conditional_absent` — zero events when its trigger is false;
  `Investigate`/`Plan`/`Review`/`Architecture-Verify` under hotfix tier are `skipped_event` — an
  explicit `skipped`-status event is still written). Step 3's generator passes these fields through
  from `load_contract()` unmodified; collapsing them into one generic "skipped" concept would
  misrepresent real behavior per `workflows/implement-ticket.yaml`'s own header comment (lines 8-14).
- **This ticket's own build must produce zero real divergences.** Step 1's contract data is
  authored directly from Step 2's live extraction (not independently guessed), and Step 4 confirmed
  no phase-order divergence exists. If, during implementation, any unexpected mismatch surfaces
  (e.g. a line-number drift between investigation time and implementation time), do not silently
  patch the contract to match — treat it as a signal to re-verify the extraction is correct first,
  then either fix the contract (if the contract was wrong) or log a genuine, human-approved
  divergence entry (if the live behavior is the outlier and the mismatch is intentional).
- **Package boundary discipline:** every new file in this ticket lives under
  `tools/agent_orchestration_claude_adapter/`, `tests/agent_orchestration_claude_adapter/`, or as a
  new file directly under `agent-orchestration/` (`terminal-statuses.yaml`, `rendered/`,
  `intentional-divergences.md`). Nothing is added to `tools/agent_orchestration/`,
  `tests/agent_orchestration/`, or `.claude/` — this keeps the predecessor ticket's package and its
  regression tests (`test_contract_structure.py`, `test_bootstrap_vocabulary_equality.py`,
  `test_skills_catalog.py`, `test_validator_errors.py`, `test_validator_no_network_calls.py`)
  entirely undisturbed.

## Deviations (added during Implement)

1. **`extract_bypass_statuses`'s regex narrowed from `[^"]+` to `[^"$]+`.** During implementation,
   the literal-`[^"]+` regex specified in Step 2 produced a false positive: `writeMonitoring`'s own
   function body (line ~319) contains a *documentation/prompt* string
   `"final_status":"${finalStatus}"` describing the normal (non-bypass) `record_run.py --data`
   call shape — this line also contains the substring `record_run.py`, so the scoped-to-lines-
   containing-`record_run.py` regex matched it, extracting a spurious 16th "status"
   (`${finalStatus}`) alongside the genuine `SCOPE_AGENT_FAILED` bypass at line 182. Fixed by
   excluding `$` from the captured character class (`[^"$]+`), which correctly distinguishes a
   bare string literal (a genuine bypass value) from a `${...}`-interpolated template (the normal
   call's own self-documentation). Verified via `test_extract_all_terminal_statuses_dedupes_by_value_not_call_site_count`
   asserting exactly 15 total entries.
2. **`render_claude_adapter()`'s output dict carries a `"phases"` field in addition to the 4 keys
   Step 3's literal example showed** (`claude_adapter_schema_version`, `source_workflow_id`,
   `phase_order`, `terminal_statuses`). The plan's own Anti-Drift Notes require
   `workflows/implement-ticket.yaml`'s `tiers`/`condition`/`if_false` fields to "pass through...
   unmodified, not collapse them" (preserving the `skipped_event` vs. `conditional_absent`
   distinction) — `phase_order` alone (a flat list of names) has nowhere to carry that data, so a
   `"phases"` field (the full `bundle.workflow["phases"]` list, unmodified) was added to satisfy
   that explicit requirement. Verified by
   `test_build_claude_adapter_representation_derives_purely_from_load_paths`, which asserts
   `Security-Review`'s `if_false: conditional_absent` and `Investigate`'s
   `tiers.hotfix: skipped_event` both survive into the rendered output.
3. **Test-file scoping for the `.codex/` scope-creep guard (Step 9) excludes this ticket's own
   `tests/agent_orchestration_claude_adapter/` directory from the scanned tree** (scans only
   `tools/agent_orchestration_claude_adapter/` + the three new `agent-orchestration/` files), not
   `tests/agent_orchestration_claude_adapter/` as the plan's Step 9 file list loosely implied.
   Mirrors the predecessor ticket's own `test_validator_no_network_calls.py` precedent exactly
   (`search_dirs = [_TOOL_DIR, _REPO_ROOT / "agent-orchestration"]`, never its own tests/
   directory) — this guard test's own docstring legitimately discusses `.codex/` as a concept it
   is asserting the *absence* of, which would otherwise self-trigger a false positive.
4. **`tools/agent_orchestration_claude_adapter/*.py` docstrings deliberately never spell out the
   literal string `implement-ticket.js`** (Step 7's whole-file string-constant scan, mirrored
   "exactly" per the plan, bans this substring from appearing anywhere in the scanned package,
   including comments/docstrings — the same discipline `tests/agent_replay/runner.py` already
   follows for its own four forbidden script names). Docstrings instead say "the live Claude
   workflow source file" / "the live workflow source" — functionally identical documentation,
   just without the literal filename as a string constant. Test files (which legitimately need the
   real path to call functions with) are unaffected — the guard only scans
   `tools/agent_orchestration_claude_adapter/`.

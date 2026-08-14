---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-GATE-DET-PARITY-UPDATER
artifact_type: plan
tags: [ai, workflows, determinism]
---

# Implementation Plan — TCK-20260705-GATE-DET-PARITY-UPDATER

## Summary

Add `tools/gate_checks/parity_updater_static.py`, a general-purpose module that derives a `src/` path →
set-of-ledger-subsystem-filenames mapping from `docs/parity_ledger/*.yaml`'s own `v2_evidence` citations
(reusing `CANONICAL_LEDGER_FILES` from `tools/parity_ledger_scan.py` by import, never redefining it), and
a cross-reference function that flags any `src/` file whose candidate subsystem(s) were not touched in
the same Implement pass. Semantics are ANY-of-candidates (ticket-level decision 1) and unmapped files
return an explicit `NA` (decision 2), never a silent pass. The causality problem the investigation
flagged (decision 3) is resolved by having the **agent itself** invoke the module twice in a single
turn — once at the start (compute the expected-subsystem todo-list from `implementation.files_changed`,
which needs only the diff and is available immediately) and once at the end (re-derive the same mapping
and cross-reference it against `git status --porcelain docs/parity_ledger/` to see what it actually
touched, citing the JSON verbatim and explaining/addressing any flagged file before returning).

**Revised per architecture review round 1 (CONFIRMED finding):** the agent-self-invokes design above is
unenforced — an agent that skips or fabricates its own self-check would go undetected, unlike the
sibling `GATE-DET-DONE-CHECKER` ticket's own Finalize self-check, which the *orchestrator* runs directly
via `bash()` after the agent's turn ends specifically so nothing the agent says or omits can prevent it
from running. Since this ticket's own scope guard already rules out a new blocking verdict/retry loop for
Parity (a flagged miss is visibility-only, never a pipeline halt), there is no "chance to react within the
same turn" being traded away by moving enforcement to the orchestrator — that justification for
agent-self-invocation does not hold once blocking is off the table. **Corrected design:** the orchestrator
runs `expected_subsystems_for_files` via `bash()` *before* the `agent()` call (mirroring the existing
`p0ScanOutput` `bash()` call at lines 561-571 in this exact phase) and injects the plain-text result into
the prompt's shared preamble as read-only context (not as an instruction for the agent to compute it
itself). The orchestrator then runs `cross_reference_touched` via `bash()` *after* `agent()` returns
(mirroring `run_finalize_selfcheck`'s JSON-marker-prefix + try/catch-with-fallback parsing pattern
exactly, since there is no established contract in this repo that `bash()` output is safe for a bare
`JSON.parse()`), and surfaces any FAIL via the `pushEvent` evidence text — non-blocking, per scope guard,
consistent with Parity having no verdict enum. This also resolves architecture review's second finding
(the Step 1/Step 2 prompt-text placement was ambiguous inside the `implementation.behavior_changed`
ternary, which only has `Rules:` bullets in its true branch — risking the check never firing on the
false-branch/`src/`-touched-without-behavior-change path, arguably the highest-risk case): since the
computed context is now injected into the shared preamble (same place as the existing `Behavior changed:`/
`Parity subsystems affected:` lines, which sit *outside* and *before* the ternary), it is present
identically regardless of which ternary branch renders. A new minimal `PARITY_SCHEMA` (decision 4) mirrors `DONE_SCHEMA`'s shape and replaces the current
`PHASE_TS:`-line regex-extraction hack with the standard schema `ts` field every other phase already
uses. The mapping-derivation function is written schema-agnostic and Parity-name-decoupled so
`GATE-DET-MECHANICS-AUDITOR` (ticket 3) can import it directly (decision 5). No new blocking/verdict
status is introduced for Parity — a flagged miss is visible via `log()` + the pushEvent evidence text,
not a pipeline halt, since the ticket's ACs ask for visibility/backstop, not a new gate that returns
early (Parity has no verdict enum today, unlike Review/Test/Security/Verify).

## Steps

### Step 1 — Mapping-derivation and cross-reference module
**Files:** `tools/gate_checks/parity_updater_static.py` (new)
**Change:**
- Module docstring explaining purpose, mirroring `done_checker_static.py`'s docstring style (cites the
  ticket ID, explains why the module exists, notes the shared-package convention from SEQUENCE.md
  decision 1).
- `from parity_ledger_scan import CANONICAL_LEDGER_FILES` via the same `sys.path` shim pattern
  `done_checker_static.py` uses (`_TOOLS_DIR = Path(__file__).resolve().parent.parent`, insert into
  `sys.path` if absent) — do not redefine the 8-file tuple.
- `derive_mapping(ledger_dir: Path | str = "docs/parity_ledger") -> dict[str, set[str]]`: for each
  filename in `CANONICAL_LEDGER_FILES` (skip silently if the file doesn't exist under `ledger_dir` —
  legacy-data-scope convention, mirrors `find_p0_intersection`'s `if not path.exists(): continue`), load
  YAML (`yaml.safe_load(...) or []`), wrapped in a `try/except Exception: continue`-per-file guard so a
  malformed/legacy-format YAML file never crashes the whole derivation (legacy-data-scope convention
  from Ticket 1). For each entry, read `entry.get("v2_evidence") or ""` and extract every `src/...py`
  substring via `re.findall(r'src/[\w\-./]+\.py', evidence)`. Build and return `{src_path: {filename,
  ...}}` — a file cited in multiple ledger YAMLs accumulates multiple filenames in its set (this is the
  16%-overlap case from investigation.md; must never collapse to a single value).
- `expected_subsystems_for_files(files_changed: list[str], ledger_dir="docs/parity_ledger") ->
  dict[str, list[str] | None]`: filter `files_changed` to only paths starting with `src/` (non-`src/`
  paths excluded entirely from the returned dict, not just marked NA — mirrors test #8's exclusion
  semantics). For each remaining path, look up `derive_mapping(ledger_dir)`; return `sorted(candidates)`
  if found, else `None` (renders as `NA` by the caller/agent, never omitted from the dict — keys for
  every `src/` file in `files_changed` must be present). This is the "Step 0, can run first" half of the
  two-step design — pure function of `files_changed` and the ledger's current `v2_evidence` text, no
  dependency on what the agent has or hasn't touched yet.
- `cross_reference_touched(files_changed: list[str], touched_ledger_files: list[str],
  ledger_dir="docs/parity_ledger") -> list[dict]`: normalize each entry of `touched_ledger_files` to its
  basename (`Path(x.strip().split()[-1]).name` — tolerates raw `git status --porcelain` lines like
  `" M docs/parity_ledger/combat_movement.yaml"` as well as plain `git diff --name-only` output or bare
  filenames) into a set. Call `expected_subsystems_for_files(files_changed, ledger_dir)`. For each
  `(path, candidates)`:
  - `candidates is None` → `{"file": path, "status": "NA", "evidence": "no v2_evidence citation found in any canonical ledger file"}`
  - `any(c in touched_basenames for c in candidates)` → `{"file": path, "status": "PASS", "evidence": f"touched: {[c for c in candidates if c in touched_basenames]}"}`
  - else → `{"file": path, "status": "FAIL", "evidence": f"mapped to {candidates}, none touched"}`
  ANY-of-candidates semantics — a file with 2+ candidates only needs one touched to clear (decision 1).
  This is the "final step before returning" half of the two-step design.
**Do NOT touch:** `tools/parity_ledger_scan.py` (import from it, never edit its function or the
`CANONICAL_LEDGER_FILES` tuple itself) — SEQUENCE.md decision 1 requires a sibling module, not a folded-in
change.
**Verify:** `tests/tools/test_parity_updater_static.py::test_derive_mapping_reads_v2_evidence_paths`,
`test_derive_mapping_handles_multi_subsystem_file`, `test_reuses_canonical_ledger_files_constant`.

### Step 2 — Coverage-honesty test suite
**Files:** `tests/tools/test_parity_updater_static.py` (new)
**Change:** Implement all 9 tests from `test_plan.md` exactly as specified there (names,
verifies-clauses). Mirror `tests/tools/test_parity_ledger_scan.py`'s fixture convention: a
`_write_ledger(tmp_path, filename, entries)` helper that `yaml.safe_dump`s a Python list-of-dicts to a
file (no frontmatter template needed — ledger files are plain YAML lists), plus the same `sys.path` shim
pattern both existing `tests/tools/` files use. Group tests with `# ---` section-divider comments by
function under test (mirrors `test_done_checker_static.py`'s grouping style). File stays unmarked (no
`pytest.mark.architecture`) per SEQUENCE.md decision 1 — this is agent-workflow hygiene, not a
simulation-code architecture guard.
- Test 1 `test_derive_mapping_reads_v2_evidence_paths` — 2+ fixture YAMLs, each with an entry citing a
  distinct `src/...py` path in `v2_evidence`; assert `derive_mapping(tmp_path)` maps each path to its
  correct owning filename.
- Test 2 `test_derive_mapping_handles_multi_subsystem_file` — same `src/` path cited in two fixture
  YAMLs' `v2_evidence`; assert the returned mapping's value for that path is a set/collection containing
  both filenames (not a single string).
- Test 3 `test_flags_untouched_mapped_subsystem` — `files_changed=['src/engine/foo.py']` cited only in a
  fixture `combat_movement.yaml`; `touched_ledger_files=[]`; assert `cross_reference_touched(...)`
  returns a `FAIL` entry naming `combat_movement.yaml` for `src/engine/foo.py`.
- Test 4 `test_does_not_flag_when_mapped_subsystem_touched` — identical setup to Test 3 but
  `touched_ledger_files=['docs/parity_ledger/combat_movement.yaml']`; assert no `FAIL` entry for that
  path (status `PASS`).
- Test 5 `test_any_of_candidate_subsystems_touched_clears_flag` — a `src/` path cited in two fixture
  YAMLs (`file_a`, `file_b`); `touched_ledger_files=[file_a]` only; assert the path is **not** flagged
  (`PASS`) — the anti-drift guard against ANY-to-ALL regression.
- Test 6 `test_unmapped_file_is_not_a_failure` — a `files_changed` path with zero citations anywhere in
  the fixture ledger; assert its result `status == "NA"`, present in the output (not dropped), not
  `"FAIL"`.
- Test 7 `test_excludes_faction_yaml` — fixture directory has a `faction.yaml` alongside canonical files,
  with a `src/` path cited only in `faction.yaml`; assert `derive_mapping(tmp_path)` does not map that
  path to anything (mapping only scans `CANONICAL_LEDGER_FILES`).
- Test 8 `test_non_src_paths_ignored` — `files_changed` includes `tests/...` and `docs/...` paths; assert
  neither appears as a key in `expected_subsystems_for_files(...)`'s returned dict.
- Test 9 `test_reuses_canonical_ledger_files_constant` — `from gate_checks.parity_updater_static import
  CANONICAL_LEDGER_FILES` (re-exported or imported directly) and assert identity/equality against
  `tools.parity_ledger_scan.CANONICAL_LEDGER_FILES` — prevents the two modules' file lists drifting
  apart.
**Do NOT touch:** `tests/tools/test_parity_ledger_scan.py`, `tests/tools/test_done_checker_static.py`,
`tests/tools/test_done_checker_audit.py` — regression surface only, must keep passing unmodified.
**Verify:** `pytest tests/tools/test_parity_updater_static.py -v` (all 9 pass), then
`pytest tests/tools/ -v` (full regression surface, confirms no cross-module import breakage).

### Step 3 — `PARITY_SCHEMA` + Parity phase prompt rewiring
**Files:** `.claude/workflows/implement-ticket.js` (Parity phase, currently lines ~540-608)
**Change:**
- Inside the `else` branch (full-call path only — never touch the `if (paritySkipEligible &&
  !parityForceFullRun)` branch or `find_p0_intersection` call above it), add a new schema constant
  directly above the `agent(...)` call:
  ```js
  const PARITY_SCHEMA = {
    type: 'object',
    required: ['entries_updated', 'p0_missing_test_path', 'summary'],
    properties: {
      entries_updated: { type: 'array', items: { type: 'string' } },
      p0_missing_test_path: { type: 'array', items: { type: 'string' } },
      summary: { type: 'string', description: 'One sentence: what was updated (≤200 chars)' },
      ts: { type: 'string', description: 'ISO timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ` at start of this phase' },
      verified_by: { type: 'array', items: { type: 'string' }, description: 'Agent self-report of which findings came from tools/gate_checks/parity_updater_static.py vs. pure LLM judgment, e.g. ["static:parity_updater_static", "llm"].' },
    },
  }
  ```
  This is the exact minimal shape resolution #4 specifies — do not add extra fields (e.g. no
  `flagged_files`; the cross-reference detail is prose inside `summary`/the agent's own explanation, not
  a new schema property).
- Add `{ label: 'parity-update', schema: PARITY_SCHEMA, agentType: 'parity-updater' }` to the `agent(...)`
  call options (currently `{ label: 'parity-update', agentType: 'parity-updater' }` with no schema).
- Replace the current `Step 0: run \`date...\`. Your response MUST begin with this exact line...
  PHASE_TS: <result>` instruction with the standard `Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\` and
  include result as the \`ts\` field.` wording every other schema-bearing phase uses (Review, Implement,
  Test, Security-Review, Verify all use this exact phrasing) — this hack existed only because Parity had
  no schema to carry `ts` in; once `PARITY_SCHEMA` exists, the hack is no longer needed.
- Delete the post-call `parityTs = parity.toString().match(/^PHASE_TS: .../)` / `parityText =
  parity.toString().replace(...)` regex-extraction lines. Replace with direct schema field reads:
  `pushEvent('Parity', 'parity-updater', 'ok', parity.summary || 'Parity ledger updated', parity.ts)`.
- **Orchestrator-run, before the `agent()` call** (added just above the `const parity = await agent(`
  line, inside the `else` branch, mirroring the existing `p0ScanOutput` `bash()` call's shape at lines
  561-571 in this same phase — args passed as individually quoted argv elements, never JSON-embedded in
  the `-c` string):
  ```js
  const filesChangedArgs = implementation.files_changed.map(f => `"${f}"`).join(' ')
  const expectedSubsystemsOutput = await bash(
    `python3 -c "
  import sys, json
  sys.path.insert(0, 'tools')
  from gate_checks.parity_updater_static import expected_subsystems_for_files
  print(json.dumps(expected_subsystems_for_files(sys.argv[1:])))
  " ${filesChangedArgs}`
  )
  ```
  Inject `expectedSubsystemsOutput` as a new line in the prompt's **shared preamble** (alongside the
  existing `Behavior changed: ...` / `Parity subsystems affected: ...` lines, which sit outside and before
  the `implementation.behavior_changed` ternary — not inside either of its branches, so it is present
  identically regardless of which branch renders): `Expected parity-ledger files per changed src/ file
  (NA = no existing citation found): ${expectedSubsystemsOutput}`.
- **Orchestrator-run, after the `agent()` call returns** (mirroring `run_finalize_selfcheck`'s
  JSON-marker-prefix + try/catch-with-fallback parsing pattern exactly, since there is no established
  contract that `bash()` output is safe for a bare `JSON.parse()`):
  ```js
  const touchedOutput = await bash(`git status --porcelain -- docs/parity_ledger/`)
  const crossRefOutput = await bash(
    `python3 -c "
  import sys, json
  sys.path.insert(0, 'tools')
  from gate_checks.parity_updater_static import cross_reference_touched
  files_changed = json.loads(sys.argv[1])
  touched = sys.argv[2].splitlines()
  results = cross_reference_touched(files_changed, touched)
  print('PARITY_CHECK_JSON:' + json.dumps(results))
  " '${JSON.stringify(implementation.files_changed)}' "${touchedOutput}"`
  )
  let parityCrossRef = null
  const parityMarkerIndex = crossRefOutput.indexOf('PARITY_CHECK_JSON:')
  if (parityMarkerIndex !== -1) {
    try { parityCrossRef = JSON.parse(crossRefOutput.slice(parityMarkerIndex + 'PARITY_CHECK_JSON:'.length).trim()) }
    catch (e) { parityCrossRef = null }
  }
  const parityCrossRefFailures = (parityCrossRef || []).filter(r => r.status === 'FAIL')
  ```
  If `parityCrossRef === null` (unparseable) or `parityCrossRefFailures.length > 0`: include the detail in
  the `pushEvent` evidence text (e.g. `(parity.summary || 'Parity ledger updated').slice(0,150) + ' | cross-ref: ' + (parityCrossRef ===
  null ? 'unparseable' : parityCrossRefFailures.map(f => f.file + ': ' + f.evidence).join('; ')).slice(0,
  200)`) — **visibility only, no status change, no early return** (per this ticket's own scope guard: no
  new blocking verdict for Parity). This is deliberately weaker enforcement than Finalize's
  `FINALIZE_INCOMPLETE` (which does block) because no AC here asks for a new gate — but it is still
  orchestrator-run and unconditionally executed, unlike the previous agent-self-invoked design, so a
  flagged miss is always visible in `agent-monitoring/events.jsonl`, never dependent on the agent choosing
  to check.
- The agent's own prompt keeps the existing Rules bullets and "Then report..." line **unchanged** beyond
  asking for `verified_by` (the agent still explains/addresses ledger updates using the injected
  expected-subsystems context as guidance, but the orchestrator — not the agent's own say-so — is what
  determines whether the cross-reference actually passed).
- Update `Then report: entries updated (by ID and what changed), any P0 entries missing a test_path.` to
  additionally ask for `verified_by` (matching schema's required shape) — describing which of its own
  judgments were informed by the injected expected-subsystems context vs. independent reasoning.
**Do NOT touch:** the `parityNoSrcChange`/`paritySkipEligible`/`parityForceFullRun` computation, the
`find_p0_intersection` bash() call, or anything inside the `if (paritySkipEligible &&
!parityForceFullRun) { ... }` skip branch — all explicitly out of scope (`TCK-20260705-WORKFLOW-PARITY-SKIP`'s
territory). Do not add a new blocking `verdict`/status enum to `PARITY_SCHEMA` or an early `return` after
this agent call — Parity stays a non-blocking phase per this ticket's scope (no AC asks for a new gate).
**Verify:** No JS test harness exists in this repo (confirmed in investigation.md — no `.test.js` files,
`package.json` has no test runner). Verification is manual/structural: re-read the edited block, confirm
`PARITY_SCHEMA`'s shape matches `DONE_SCHEMA`'s precedent field-for-field, confirm the `PHASE_TS` hack is
fully removed with no dangling reference, confirm no bracket/quote imbalance in the new template-literal
sections. This mirrors how the done-checker ticket verified its own equivalent JS change.

### Step 4 — `.claude/agents/parity-updater.md` standing instructions
**Files:** `.claude/agents/parity-updater.md`
**Change:** Add a new `## Step 0 — Expected-Subsystem Context` section immediately after the intro
paragraph and before `## Parity Ledger Files` (structurally lighter than `done-checker.md`'s Step 0, since
here the orchestrator — not the agent — runs the static script; revised per architecture review round 1's
orchestrator-enforced design). Content: explain that the prompt's preamble includes an `Expected
parity-ledger files per changed src/ file` line, computed by the orchestrator via
`tools/gate_checks/parity_updater_static.py::expected_subsystems_for_files` before this agent is invoked —
use it as guidance for which YAML file(s) each changed `src/` file is expected to touch (`NA` = no
existing citation found, use judgment for whether a new entry is warranted). Also explain that after this
agent's turn ends, the orchestrator independently re-runs `cross_reference_touched` against the actual
`git status` diff of `docs/parity_ledger/` and records any discrepancy in `agent-monitoring/events.jsonl`
— the agent does not need to run this verification itself, but should treat the injected expected-subsystem
context as a strong hint rather than optional flavor text, since a mismatch will be visible regardless.
Add to `## Output` (currently the last section): `Include a verified_by field listing which of your
findings were informed by the injected expected-subsystem context vs. independent judgment, e.g.
["static:parity_updater_static", "llm"]` — mirrors done-checker.md's own `## Output` section's
`verified_by` line.
**Do NOT touch:** the `## Parity Ledger Files` table, `## Entry Schema` block, or the existing `## What
to Do` numbered steps 1-5 — those describe the LLM-judged status-decision logic this ticket explicitly
does not re-decide (Out of Scope).
**Verify:** manual/structural review only (same as Step 3 — no JS/prompt-file test harness exists).

### Step 5 — `docs/ai/agents.md` parity-updater section
**Files:** `docs/ai/agents.md` (`### \`parity-updater\`` section, currently lines 188-213)
**Change:** Add a "Step 0 — static pre-check" paragraph immediately after the section's `**Role:**` line
(if one exists) or as the first paragraph, mirroring the `done-checker` section's own paragraph at lines
112-116 verbatim in structure: name the script
(`tools/gate_checks/parity_updater_static.py::expected_subsystems_for_files` /
`::cross_reference_touched`), state that the agent runs it at the start (todo-list) and end
(self-check) of its turn, and that it self-reports `verified_by`.
**Do NOT touch:** the `### mechanics-auditor` section immediately following (line 215+) — out of scope,
belongs to sibling Ticket 3.
**Verify:** manual review; no automated doc test exists for this file's prose content.

### Step 6 — Shared doc trio: `workflows.md`, `system_overview.md`, `ticket-lifecycle.md`
**Files:**
- `docs/ai/workflows.md` (Parity table row, currently line 86)
- `docs/ai/system_overview.md` (Parity pipeline paragraph, currently ~lines 79-88)
- `docs/ai/ticket-lifecycle.md` (`### Parity` section, currently lines 265-279)
**Change:** In each file, extend the existing Parity description with one clause naming the new static
module, mirroring exactly how each file's own done-checker entry already names
`tools/gate_checks/done_checker_static.py::run_static_precheck` inline in prose (table cell / pipeline
paragraph / "Step 0" sub-paragraph respectively — `ticket-lifecycle.md`'s `### Verify` section at lines
296-301 is the closest structural twin to mirror for the `### Parity` section specifically). Do not
create a new standalone script-reference subsection — the done-checker precedent embeds the script name
inline in existing prose, not as a separate heading, in these 3 files (only `agents.md` gets a dedicated
subsection, per Step 5).
**Do NOT touch:** any other phase's rows/paragraphs/sections in these 3 files (Review, Test, Security,
Verify, Finalize) — this ticket only extends Parity's own description.
**Verify:** manual review; these are prose docs with no automated test, consistent with how the
done-checker ticket verified its own doc updates.

### Step 7 — Ticket bookkeeping
**Files:** `tickets/inprogress/TCK-20260705-GATE-DET-PARITY-UPDATER.md`
**Change:** Fill in Implementation Notes, Test Summary, Files Changed sections per the standard
after-work convention. No parity ledger entry update is needed for this ticket itself (this ticket
builds tooling around the ledger, does not change simulation behavior — confirmed in investigation.md's
"Parity Ledger Overlap" section).
**Do NOT touch:** `docs/parity_ledger/*.yaml` — this ticket's own changes are `.claude/`, `tools/`,
`tests/`, `docs/ai/` only; none of them are `src/` files, so the new check does not even apply
recursively to this ticket's own Parity phase run.
**Verify:** `pytest tests/tools/ -v` passes in full; done-checker's own static pre-check (already shipped)
passes when this ticket runs through Verify.

## Scope Guards

- Do not fold `parity_updater_static.py` into `tools/parity_ledger_scan.py` — sibling module, per
  SEQUENCE.md decision 1.
- Do not touch the `paritySkipEligible`/`parityForceFullRun`/`find_p0_intersection` skip-branch logic —
  `TCK-20260705-WORKFLOW-PARITY-SKIP`'s territory, explicitly Out of Scope.
- Do not re-decide `status: verified`/`divergent` semantics anywhere — stays LLM-judged.
- Do not add `faction.yaml` as a 9th canonical file.
- Do not add a new blocking verdict/status enum to Parity — no AC asks for a new gate; a flagged miss is
  visibility-only (log + pushEvent evidence), not a pipeline halt.
- Do not require ALL candidate subsystems touched for a multi-mapped file — ANY-of-candidates only.
- Do not silently drop or auto-pass unmapped `src/` files — must return explicit `NA`.
- Do not invent a JS test framework/harness — none exists in this repo; JS-side changes are verified
  manually/structurally, consistent with the done-checker ticket's own precedent.
- Do not bundle token/cost telemetry — explicitly deferred per SEQUENCE.md decision 5.
- The mapping-derivation function (`derive_mapping`/`expected_subsystems_for_files`) must stay
  general-purpose and importable independent of Parity-specific naming — Ticket 3
  (`GATE-DET-MECHANICS-AUDITOR`) is expected to import it directly.

## Dependency Map

- Step 1 has no dependencies — build the module first.
- Step 2 depends on Step 1 (tests import the module's functions).
- Step 3 depends on Step 1 (the prompt text references the module's function names/import path) but not
  on Step 2.
- Step 4 depends on Step 1 conceptually (references the same function names) but can be written in
  parallel with Step 3 — no code dependency between them, both just need Step 1's function names to be
  final.
- Step 5 and Step 6 depend on Steps 3 and 4 being finished (docs describe the final wiring, not a
  moving target) but have no code dependency — can be done in either order relative to each other.
- Step 7 is last, after Steps 1-6 and their verification all pass.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `tools/gate_checks/parity_updater_static.py` exists with documented mapping derivation + diff-cross-reference function | Step 1 | `test_derive_mapping_reads_v2_evidence_paths`, `test_derive_mapping_handles_multi_subsystem_file`, `test_reuses_canonical_ledger_files_constant` |
| Parity phase's prompt (when not skip-eligible) instructs parity-updater to run this check first and address any flagged file | Step 3, Step 4 | Manual/structural review (no JS test harness) |
| Confirmed no conflict with Parity-skip logic from `TCK-20260705-WORKFLOW-PARITY-SKIP` | Already confirmed in investigation.md (Current Behavior point 3); Step 3's "Do NOT touch" guard preserves it | N/A — confirmed by investigation, preserved structurally by scope guard |
| At least one coverage-honesty test per check function | Step 2 | `test_any_of_candidate_subsystems_touched_clears_flag` (ANY-semantics), `test_unmapped_file_is_not_a_failure` (NA-not-silent), `test_excludes_faction_yaml` (scope guard) |
| `docs/ai/agents.md`'s `parity-updater` section and the other 3 shared docs updated | Step 5, Step 6 | Manual review |

## Anti-Drift Notes

- **The single most important hazard**: do not let the multi-subsystem semantics regress from ANY to
  ALL. `test_any_of_candidate_subsystems_touched_clears_flag` (Step 2) is the guard; if it's ever
  deleted or weakened, a routine change to `src/engine/apply.py` or `src/core/state.py` (cited in 5+
  ledger files each) would spuriously FAIL almost every ticket that touches shared infra.
- **Do not silently treat unmapped files as passing.** `NA` must be a visible, distinct status value
  from `PASS`/`FAIL` in every function's output — this is the same anti-silent-failure principle
  `done_checker_static.py`'s `check_data_runs_clean` already established for unparsable timestamps.
- **The causality fix is real, not cosmetic.** A check that only runs *before* `parity-updater`'s turn
  would trivially "pass" by finding nothing touched yet — worthless as a gate. Both the todo-list
  computation (start) and the cross-reference (end) must exist for the check to mean anything; do not
  simplify this down to a single call site during implementation review.
- **`v2_evidence` path extraction is a text-mining heuristic, not a guaranteed-complete index.** A brand
  new `src/` file, or an existing file whose evidence citation uses a different path form (backslashes,
  absolute paths, a line-number suffix the regex doesn't anticipate), will show as `NA` even though a
  human might consider it "obviously" belonging to a subsystem. This is intentional and matches the
  ticket's own Out-of-Scope framing (not re-deciding what counts as mapped) — do not try to make the
  regex "smarter" with heuristics beyond straightforward `src/....py` substring extraction; that's scope
  creep into judgment territory this ticket deliberately leaves to the LLM.
- **Legacy-data tolerance**: any per-file YAML parse failure in `derive_mapping` must be caught and
  skipped (continue to the next canonical file), never raised — matches the established convention from
  `GATE-DET-DONE-CHECKER` of not investigating/crashing on old-format data, just gracefully skipping it.
- **No new blocking status for Parity.** Resist the temptation to add a `verdict` enum or an early
  `return` mirroring Review/Test/Security/Verify's blocking pattern — none of this ticket's ACs ask for
  it, and Parity has never blocked the pipeline; this ticket adds visibility (schema fields, log output),
  not a new gate.

## Unresolved Questions

None. All 5 risks flagged in `investigation.md` were resolved by the orchestrating session before this
plan (ANY-of-candidates semantics; NA for unmapped; two-step causality design; `PARITY_SCHEMA` added with
the exact minimal shape specified; general-purpose reusable mapping function for Ticket 3).

The one mechanical choice investigation.md explicitly left open — prompt-instructed re-run vs.
JS-orchestrated dual `bash()` calls — was initially decided in favor of prompt-instructed re-run (agent
self-invokes the module at both ends of its turn), but **architecture review round 1 found this
unenforced** (an agent that skips or fabricates its own self-check goes undetected, unlike the sibling
Finalize self-check precedent which the orchestrator runs unconditionally) **and reversed it**: the
corrected design (now reflected in Step 3/Step 4 above) has the orchestrator run both `bash()` calls
itself — `expected_subsystems_for_files` before `agent()`, injected as read-only preamble context, and
`cross_reference_touched` after `agent()` returns, surfaced via `pushEvent` evidence only (no blocking
status, since no AC asks for a new gate). This also incidentally fixed round 1's second finding (the
original Step 1/Step 2 prompt-text placement was ambiguous inside the `implementation.behavior_changed`
ternary, which only has `Rules:` bullets in its true branch) by moving the injected context to the shared
preamble, present regardless of ternary branch.

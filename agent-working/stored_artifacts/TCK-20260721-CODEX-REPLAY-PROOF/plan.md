---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-CODEX-REPLAY-PROOF
artifact_type: plan
tags: [ai, workflows, agent-monitoring, process-improvement]
---

# Implementation Plan — TCK-20260721-CODEX-REPLAY-PROOF

## Summary

Build a narrow, deterministic-logic-only replay proof for the `implement-ticket` workflow's
Scope → Investigate → Plan → Review slice (the four phases before Implement). The proof consists
of five new, isolated artifacts: (1) a fixture-envelope specification doc
(`docs/ai/replay_fixture_spec.md`), (2) one real fixture data file derived read-only from
`TCK-20260721-ORCHESTRATION-CONTRACT-ADR`'s permanent `tickets/done/` + `stored_artifacts/` +
`agent-monitoring/{events,runs}.jsonl` content, (3) a fixture loader/validator
(`tools/agent_replay/fixture_envelope.py`), (4) a replay runner
(`tools/agent_replay/runner.py`) that imports and calls the **real** `tools/gate_checks/*.py` and
`tools/tag_registry.py` deterministic functions read-only, hand-mirrors the handful of inline
branch decisions in `implement-ticket.js` that have no importable module (the same
`classifyChecklistFailure`-precedent shape), and injects fake/no-op stand-ins wherever the real
orchestrator would call `writeMonitoring`/the pre/post-tool hooks, and (5) five new tests under a
new `tests/agent_replay/` directory proving: schema validation, real-fixture load, full-slice
completion, zero forbidden-script invocation (source-level, AST-based), zero repo mutation
(snapshot), and fail-closed behavior on a missing fixture field.

`tests/replay/` already exists in this repo for a **different** domain (simulation-engine
tick/state replay — `test_authoritative_outcome_truth.py`, `test_replay_fidelity.py`,
`test_event_replay.py`, backing `src/engine/replay_manager.py`). This plan deliberately places all
new files under `tools/agent_replay/` and `tests/agent_replay/` instead, to avoid conflating two
unrelated "replay" concepts in one directory — this is the Plan-phase decision the investigation's
Open Question #1 (phase-slice scope) and the test_plan's own hedge ("whichever path Plan phase
assigns the runner") both anticipated needing.

Five Plan-phase decisions from the investigation's Risks/Open Questions section are resolved
directly below, from repo evidence, per the ticket's instruction — none require stakeholder input:

1. **Phase-slice boundary confirmed: Scope → Investigate → Plan → Review** (4 phases), matching
   the investigation's recommendation. Implement/Architecture-Verify/Test/Parity/Security-Review/
   Verify/Finalize are out of scope for this replay slice — they require a `files_changed`/diff
   payload this ticket does not build.
2. **Real fixture source ticket confirmed: `TCK-20260721-ORCHESTRATION-CONTRACT-ADR`.** Verified
   live: `agent-monitoring/events.jsonl` has a real, complete `run_id: TCK-20260721-ORCHESTRATION-
   CONTRACT-ADR` slice with `seq 1-4` covering exactly Scope/Investigate/Plan/Review, all
   `status: ok`; `agent-monitoring/runs.jsonl` has the matching row (`final_status: DONE`,
   `tier: standard`); `tickets/done/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.md` and
   `stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-ADR/{investigation,plan,test_plan}.md`
   are permanent, real, already-landed files.
3. **Reading a done ticket's permanent artifacts to build a new, separate fixture file is
   isolated fixture work, not "modifying a live ticket artifact."** Scope's containment rule
   forbids writes into `tickets/`, `stored_artifacts/`, or the monitoring corpus — it does not
   forbid read-only traversal of already-permanent, already-closed records to populate a new file
   under a new path (`tests/fixtures/agent_replay/`). No file under `tickets/done/`,
   `stored_artifacts/`, or `agent-monitoring/` is opened in write mode anywhere in this plan.
4. **Fixture data encoding: YAML**, per the investigation's recommendation and the ADR's general
   human-reviewability preference (`docs/architecture/agent_orchestration_contract.md`, Contract
   Representation and Format: Decided). The fixture *specification document* is prose/markdown
   (this repo's standing `docs/` convention — confirmed by every sibling doc under `docs/ai/` and
   `docs/architecture/`). PyYAML is already a resolvable dependency in this environment (confirmed
   `python3 -c "import yaml"` succeeds) — no new dependency is introduced.
5. **Branches hand-mirrored (no importable `tools/gate_checks/` module backs the decision itself):**
   - Scope: `ticketInfo.conflicts.length > 0` → `CONFLICTS_DETECTED` (`implement-ticket.js` inline,
     around the block following the Scope `agent()` call and its null-check guard).
   - Scope: `unregisteredTags.length > 0` → `TAGS_NOT_REGISTERED` (the *check* — `tag_registry.
     check_tags_registered` — is a real importable function and IS imported read-only by the
     runner; only the `.length > 0` branch decision itself is inline and hand-mirrored).
   - Plan: `hasUnresolvedQuestions` (computed by the real, imported `gate_checks.plan_gate_static.
     plan_has_unresolved_questions_heading`) → `NEEDS_HUMAN_INPUT` (the check is real/imported;
     only the branch decision is inline and hand-mirrored).
   - Review: `review.verdict !== 'APPROVED'` → early-return with that verdict as final status
     (fully inline — no `tools/gate_checks/` module backs the pre-Implement Review-phase verdict
     branch at all; `architecture_reviewer_static.run_architecture_checks` is a **different**,
     later gate, invoked only at the post-Implement Architecture-Verify phase, which is out of this
     slice).
   Each hand-mirrored branch is a 1-3 line `if` in `tools/agent_replay/runner.py`, documented with
   an inline comment citing the mirrored `implement-ticket.js` region by name (Scope conflicts
   block / Scope tag-check branch / Plan unresolved-questions branch / Review verdict branch),
   following the exact precedent `classifyChecklistFailure` in `implement-ticket.js` already set
   and documents in its own comment ("kept in sync by hand").

## Steps

### Step 1 — Author the replay-fixture specification document
**Files:** `docs/ai/replay_fixture_spec.md` (new)
**Change:** Write the versioned fixture-envelope specification. Sections:
- **Envelope shape** — top-level `version` (int, currently `1`), `source` block (`ticket_id`,
  `ticket_path`, `stored_artifacts_dir`, `events_run_id`, `events_seq_range`), and a `phases` list.
  Each phase entry requires: `phase` (one of `Scope`/`Investigate`/`Plan`/`Review`), `agent`
  (matching `docs/agent-monitoring/schema.md`'s `WORKFLOW_AGENTS` vocabulary), `input` (a small
  dict of the real, structured data the orchestrator's deterministic logic needs at that phase —
  e.g. Scope's real frontmatter `tags` list, Plan's real `plan_path` pointing at the permanent
  `stored_artifacts/.../plan.md`), `output` (the recorded stand-in for the phase's `agent()` JSON
  return — at minimum the real `summary` string sourced verbatim from `agent-monitoring/
  events.jsonl`, plus, for Review, the `verdict`/`violations` fields reconstructed from that same
  real event's `status`/`summary` — see Step 2's explicit reconstruction-provenance note), and
  `transition` (the outcome actually taken: `ok`, `CONFLICTS_DETECTED`, `TAGS_NOT_REGISTERED`,
  `NEEDS_HUMAN_INPUT`, or the Review verdict value).
- **Why telemetry alone is insufficient** — cite `docs/agent-monitoring/schema.md`'s 200/120-char
  truncation caps directly (this is AC #1's explicit rationale, restated here for traceability).
- **Phase-slice scope statement** — explicitly states the slice is Scope→Review only and why
  (references this plan's Summary reasoning).
- **Contract-representation evaluation (AC #5)** — a dedicated subsection that explicitly cites
  `docs/architecture/agent_orchestration_contract.md`'s Decided "Contract Representation and
  Format: YAML... with generated Python validation models" section, states that this fixture
  envelope follows the YAML-for-data / hand-written-validator half of that decision (since no
  codegen tooling exists in this repo yet — the "generated" half is not yet buildable), and states
  explicitly that this fixture envelope is **not** the same artifact as the ADR's own future
  `agent-orchestration/contract.yaml` (that directory is Out of Scope for this ticket per the ADR's
  Source Ownership section) — it is a separate, replay-specific data shape that merely follows the
  same format preference.
- **Unconditional containment law** — a subsection stating, verbatim-equivalent to the ticket's own
  wording, that the replay runner must never subprocess or import
  `pre_tool_hook.py`/`post_tool_hook.py`/`record_run.py`/`record_events.py` under any condition,
  including from an isolated/sandboxed cwd, and that fake/no-op stand-ins are injected instead.
- **Fail-closed law** — states the runner raises on any missing required envelope field, inverting
  this repo's dominant fail-open monitoring-write convention, and states this inversion explicitly
  (not left implicit).
**Do NOT touch:** `docs/architecture/agent_orchestration_contract.md` (read/cite only, never
edited), `docs/agent-monitoring/schema.md` (read/cite only), any file under `docs/ai/` other than
this new one.
**Verify:** `tests/agent_replay/test_fixture_spec_doc.py::test_spec_doc_cites_adr_contract_representation`
(new — asserts the doc's text contains a citation to
`docs/architecture/agent_orchestration_contract.md`) and
`test_spec_doc_states_unconditional_hook_prohibition` (asserts the doc's text names all four
forbidden scripts and the word "unconditional" or equivalent).

### Step 2 — Build the real fixture data file
**Files:** `tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml` (new)
**Change:** Populate the envelope defined in Step 1, sourced by **read-only** reads of:
- `tickets/done/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.md` (frontmatter `tags`, ticket path)
- `stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-ADR/{investigation,plan,test_plan}.md`
  (referenced by path in the `input` blocks — e.g. Plan's `input.plan_path`, Review's
  `input.plan_path`/`input.investigation_path` — the fixture stores the real path, not a copy of
  the file content, so the runner reads the actual permanent file at replay time)
- `agent-monitoring/events.jsonl` filtered to `run_id: TCK-20260721-ORCHESTRATION-CONTRACT-ADR`,
  `seq 1-4` (real `phase`, `agent`, `status`, `summary`, `ts` values — copied verbatim into each
  phase entry's `output.summary` and `transition`)
- `agent-monitoring/runs.jsonl` filtered to the matching `run_id` row (`source.events_run_id`,
  overall `final_status: DONE`, `tier: standard`)

For the **Review** phase entry specifically: `agent-monitoring/events.jsonl` does not persist the
full `REVIEW_SCHEMA` JSON (`verdict`/`violations` fields) — only `status`/`summary`. Reconstruct
`output.verdict: APPROVED` and `output.violations: []` from the real seq-4 event's `status: ok` and
its `summary` text (which begins "APPROVED - ..."), and record this reconstruction explicitly as a
YAML comment in the fixture file itself (e.g. `# verdict/violations reconstructed from real
events.jsonl seq=4 status=ok + summary text; full REVIEW_SCHEMA JSON was never persisted — see
replay_fixture_spec.md`). This is real-derived data, not invented data — every field traces to a
real, permanent, cited source — and the comment makes that traceability explicit for reviewers.
**Do NOT touch:** the source files themselves (`tickets/done/TCK-20260721-ORCHESTRATION-CONTRACT-
ADR.md`, `stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-ADR/*`, `agent-monitoring/
events.jsonl`, `agent-monitoring/runs.jsonl`) — open in read mode only, never write mode, anywhere
in this step's tooling or by hand.
**Verify:** `tests/agent_replay/test_fixture_envelope.py::test_real_fixture_set_loads_and_validates`
(new — loads this exact file, asserts it validates against Step 3's loader, and asserts its
`source.ticket_id` matches a real row in `agent-monitoring/runs.jsonl` and a real file under
`tickets/done/`, per the test_plan's anti-drift guard against a synthetic fixture masquerading as
real).

### Step 3 — Build the fixture envelope loader/validator
**Files:** `tools/agent_replay/__init__.py` (new, empty), `tools/agent_replay/fixture_envelope.py`
(new)
**Change:** Define `FixtureValidationError(Exception)`, a `PhaseEntry` dataclass (`phase`, `agent`,
`input`, `output`, `transition`), a `FixtureEnvelope` dataclass (`version`, `source`, `phases:
list[PhaseEntry]`), and `load_fixture(path: str | Path) -> FixtureEnvelope`. `load_fixture` reads
the YAML file (`yaml.safe_load`), then validates: `version` key present; `source` dict present with
`ticket_id`/`ticket_path`/`events_run_id` keys; `phases` is a non-empty list; every phase entry has
non-null `phase`, `agent`, `input`, `output`, `transition` keys. On any missing/null required field,
raise `FixtureValidationError` naming the exact field and phase index — never substitute a default,
never log-and-continue. This function is the single validation entry point both the real-fixture
test and the missing-field test call.
**Do NOT touch:** `tools/gate_checks/*.py`, `tools/tag_registry.py` — this module has no
dependency on them; it only parses/validates the fixture shape.
**Verify:** `tests/agent_replay/test_fixture_envelope.py::test_fixture_envelope_schema_validates_
required_fields` and `::test_replay_runner_fails_clearly_on_missing_required_fixture_field`
(parametrized over at least 3 distinct removed fields: `version`, one phase's `output`, one phase's
`transition` — each must raise `FixtureValidationError`, never a silently-accepted partial load).

### Step 4 — Build the replay runner with injected fake hook/monitoring boundary
**Files:** `tools/agent_replay/runner.py` (new)
**Change:** Import, read-only: `tag_registry.check_tags_registered` (via `sys.path`-relative
import matching `implement-ticket.js`'s own `sys.path.insert(0, 'tools')` convention, or a direct
package import if `tools` is already import-rooted) and `gate_checks.plan_gate_static.
plan_has_unresolved_questions_heading`. Define two fake/no-op functions with names that make their
purpose unambiguous: `_fake_write_monitoring(final_status: str) -> dict` (returns `{"status":
"fake-recorded", "final_status": final_status}`, performs no I/O to `agent-monitoring/*.jsonl` or
`.claude/current_run`/`.claude/.tool_start`/`.claude/.current_session_id` — pure in-memory return)
and `_fake_hook_boundary(event_name: str) -> None` (no-op, does not write any sidecar file). Define
`replay_slice(fixture: FixtureEnvelope) -> ReplayOutcome` (a small dataclass with `final_status:
str`, `phases_completed: list[str]`) that iterates `fixture.phases` in order and, per phase, calls
`_fake_hook_boundary` in place of where the real orchestrator would touch a hook/sidecar, then:
- **Scope**: re-executes `check_tags_registered(entry.input['tags'])` against the real function;
  hand-mirrors the two inline branches (conflicts-present → `CONFLICTS_DETECTED`, unregistered-tags
  → `TAGS_NOT_REGISTERED`) using `entry.input.get('conflicts', [])` and the just-computed
  unregistered-tags result — never trusting a fixture-precomputed branch outcome for these two,
  since re-deriving them from the real function call is what makes this a genuine replay rather
  than a fixture playback.
- **Investigate**: no gate check exists at this phase in the real orchestrator (confirmed during
  Investigate-phase reading of `implement-ticket.js`) — this phase entry is accepted as-is with no
  branch logic, matching real behavior exactly.
- **Plan**: re-executes `plan_has_unresolved_questions_heading(entry.input['plan_path'])` against
  the **real, permanent** `stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-ADR/plan.md` file
  on disk (not a fixture-embedded copy); hand-mirrors the `NEEDS_HUMAN_INPUT` branch on the real
  function's return.
- **Review**: hand-mirrors the `verdict !== 'APPROVED'` branch against `entry.output['verdict']`
  (the recorded/reconstructed stand-in for the LLM's return, per Step 2 — there is no live
  architecture-reviewer LLM call in a replay run, and no importable gate module backs this
  particular branch).
On any non-`ok` transition, `replay_slice` stops iterating further phases and returns that phase's
outcome as `final_status`, calling `_fake_write_monitoring(final_status)` exactly once — mirroring
the real orchestrator's one-`writeMonitoring`-call-per-early-return shape, but with the injected
fake in place of the real agent-driven monitoring write.
**Do NOT touch:** `tools/gate_checks/*.py`, `tools/tag_registry.py` (import and call, never edit);
`.claude/workflows/implement-ticket.js` (read for reference only, never edited — nothing in this
step changes that file); never construct a `subprocess`/`bash`/`os.system` call anywhere in this
file that references `pre_tool_hook.py`, `post_tool_hook.py`, `record_run.py`, or
`record_events.py` by filename string, and never `import`/`from ... import`/
`importlib.import_module` any of those four module names, under any circumstance — this holds
regardless of cwd, sandboxing, or argument redirection; there is no conditional form of this rule.
**Verify:** `tests/agent_replay/test_runner.py::test_replay_runner_completes_against_real_fixture`
(loads Step 2's real fixture via Step 3's loader, calls `replay_slice`, asserts `final_status ==
'ok'` — or whatever the real recorded outcome was — and `phases_completed == ['Scope',
'Investigate', 'Plan', 'Review']`) and
`tests/agent_replay/test_runner_no_forbidden_calls.py::test_replay_runner_never_calls_forbidden_
monitoring_scripts` (see Step 6 — the process-level source scan).

### Step 5 — No-mutation snapshot test
**Files:** `tests/agent_replay/test_no_mutation_snapshot.py` (new)
**Change:** Against the **real repository tree** (never a `tmp_path` copy — a copy would make the
assertion vacuously true, per the test_plan's explicit anti-drift guard), run `git status
--porcelain -- tickets/ agent-monitoring/*.jsonl` (subprocess, `cwd` = real repo root — mirrors
`implement-ticket.js`'s own existing `touchedOutput = await bash('git status --porcelain --
docs/parity_ledger/')` precedent) and capture the output as a pre-snapshot. If the pre-snapshot is
non-empty (ambient dirty state from unrelated work), the test either `pytest.skip`s with a clear
message or asserts against a content-hash of the affected paths taken immediately before/after
instead of relying on ambient cleanliness — implementer's choice, but must not silently pass a
dirty-tree false-negative. Invoke Step 4's `replay_slice` against Step 2's real fixture. Re-run the
same `git status --porcelain` (or content-hash) command as a post-snapshot. Assert the two
snapshots are byte-for-byte identical. Additionally assert the runner's own no-mutation guarantee
targets resolve to the real `tickets/` and `agent-monitoring/` directories relative to repo root
(not merely "some directory"), per the test_plan's guard against a vacuous isolation loophole.
**Do NOT touch:** this test must never redirect the replay run's target paths into a `tmp_path` —
that is the exact trap the ticket's own text and the investigation's Anti-Drift Hazards section
warn against reusing from `test_post_tool_hook.py`'s isolation pattern.
**Verify:** itself — `pytest tests/agent_replay/test_no_mutation_snapshot.py -v`. This is also the
test that concretely proves AC #3.

### Step 6 — Process-level no-forbidden-calls source scan (AC #2's mechanical proof)
**Files:** `tests/agent_replay/test_runner_no_forbidden_calls.py` (new)
**Change:** For every `.py` file under `tools/agent_replay/` (Step 3's and Step 4's new files,
plus any future file added to that package): read its source text via `Path.read_text()`, then
`ast.parse()` it. Walk the AST and assert:
1. No `ast.Import`/`ast.ImportFrom` node has a module/alias name equal to, or dotted-ending-in, any
   of `record_run`, `record_events`, `post_tool_hook`, `pre_tool_hook` (catches both `import
   record_run` and `from tools.agent_monitoring.record_run import main` forms).
2. No `ast.Call` node whose `func` resolves (by name or attribute chain) to `subprocess.run`,
   `subprocess.Popen`, `subprocess.call`, `subprocess.check_call`, `subprocess.check_output`,
   `os.system`, or `os.popen` has any string-literal or f-string-literal argument (walking
   `ast.Constant`/`ast.JoinedStr` nodes within that call's arguments) containing the substring
   `"record_run.py"`, `"record_events.py"`, `"post_tool_hook.py"`, or `"pre_tool_hook.py"`.
3. No `ast.Call` to `importlib.import_module` has a string-literal argument containing any of those
   four module-name substrings.
4. A positive control: `runner.py`'s AST contains `FunctionDef` nodes named `_fake_write_monitoring`
   and `_fake_hook_boundary`, and `replay_slice`'s own `FunctionDef` body contains at least one
   `ast.Call` to each — proving the fake stand-ins are actually wired in, not merely present-but-
   unused.
This is source-code/AST-level evidence — a structurally distinct assertion from Step 5's
git-status/content-hash snapshot, satisfying the ticket's explicit "process-level evidence... not
merely by output-diffing" wording for AC #2. The AST approach (rather than plain substring `grep`)
follows this repo's own existing precedent in `tools/gate_checks/architecture_reviewer_static.py`,
which already uses `ast` for structural source checks — chosen here over `test_monitoring_bypass_
fix.py`'s plain `str.find()` substring style because this is the single most containment-sensitive
check in the ticket and AST resolves both literal-string and import forms unambiguously, including
across string concatenation/f-strings that a substring scan could miss.
**Do NOT touch:** `.claude/workflows/implement-ticket.js` — this test scans only the new
`tools/agent_replay/` source, never that file (which legitimately does reference the four forbidden
script names, by design, in its own real code path — scanning it would produce a false positive and
is explicitly not what AC #2 asks for).
**Verify:** itself — `pytest tests/agent_replay/test_runner_no_forbidden_calls.py -v`. This is the
concrete mechanical answer to AC #2's "process-level evidence" requirement.

## Scope Guards

Explicit list of what this plan must never touch, in addition to each step's own "Do NOT touch":

- **`tools/agent-monitoring/pre_tool_hook.py`, `post_tool_hook.py`, `record_run.py`,
  `record_events.py` — never subprocessed, never imported, never edited, under any condition,
  including from a sandboxed/isolated/`tmp_path` working directory.** This holds with zero
  exceptions anywhere in `tools/agent_replay/`, its tests, or any helper it imports. Step 6 exists
  specifically to make this mechanically checkable rather than merely asserted.
- `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`, `agent-monitoring/tools.jsonl` —
  never opened in write/append mode by any file this plan creates. `_fake_write_monitoring` and
  `_fake_hook_boundary` (Step 4) are pure in-memory/no-op — they must never construct a path string
  pointing at any of these three files for a write.
- `.claude/current_run`, `.claude/.tool_start`, `.claude/.current_session_id` — never written by the
  fake hook boundary; the real orchestrator's sidecar-writing behavior is not replicated at all.
- `.claude/workflows/implement-ticket.js`, `.claude/workflows/implement-epic.js` — read-only
  reference for hand-mirroring; never edited.
- `tools/gate_checks/*.py`, `tools/tag_registry.py`, `tools/agent-monitoring/cost_proxy.py`,
  `tools/agent-monitoring/vocabulary.py` — imported and called read-only; never modified, "to make
  replay easier" or otherwise.
- `tickets/inprogress/**`, `tickets/done/**` (including
  `tickets/done/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.md`), `staging_artifacts/**`,
  `stored_artifacts/**` (including `stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-ADR/*`) —
  read-only sources for Step 2's fixture; never opened in write mode.
- `tests/replay/` (existing directory) — do not add files here; it is the simulation-engine
  tick/state-replay domain (`src/engine/replay_manager.py` et al.), unrelated to this ticket's
  agent-workflow replay. All new tests go under the new `tests/agent_replay/` directory instead.
- No provider-runtime Codex adapter, no live LLM API call, no code under a new `src/` path — this
  ticket is a replay-only proof against recorded fixtures. Out of Scope per the ticket and per the
  parent epic's discovery-gate (`TCK-20260721-PROVIDER-AGNOSTIC-EPIC`).
- Implement, Architecture-Verify, Test, Parity, Security-Review, Verify, Finalize phase logic — not
  replayed by this ticket. Do not silently expand `replay_slice`'s phase coverage beyond Scope→
  Review.
- `docs/architecture/agent_orchestration_contract.md` — cited, never edited.

## Dependency Map

- Step 1 (spec doc) → informs Step 2 (fixture shape) and Step 3 (loader schema). No code
  dependency; can be drafted first or in parallel with early Step 2 research, but its content must
  be finalized before Step 3's validator is written against it.
- Step 2 (real fixture data) depends on Step 1 (needs the envelope shape defined) and is a pure
  data-authoring step — no code dependency on Steps 3/4.
- Step 3 (loader/validator) depends on Step 1 (schema) — independent of Step 2's actual data
  content (Step 3's own tests can use a small hand-built well-formed fixture for the schema-shape
  test, separate from Step 2's real one).
- Step 4 (runner) depends on Step 3 (needs `load_fixture`/`FixtureEnvelope`) and Step 2 (its
  "completes against real fixture" test needs real data to run against).
- Step 5 (snapshot test) depends on Step 4 (invokes `replay_slice`) and Step 2 (real fixture).
- Step 6 (no-forbidden-calls scan) depends only on Step 3 and Step 4 existing as files to scan —
  independent of Step 2's fixture content and of Step 5.
- Steps 5 and 6 are independent of each other and can be done in either order once Step 4 lands.

Recommended build order: 1 → 2 → 3 → 4 → (5, 6 in either order).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — fixture spec doc + versioned envelope + ≥1 real fixture checked in | Steps 1, 2 | `test_fixture_spec_doc.py`, `test_fixture_envelope.py::test_real_fixture_set_loads_and_validates` |
| AC #2 — runner executes slice, never invokes the 4 forbidden scripts (process-level evidence, not output-diffing), fake boundary injected | Steps 4, 6 | `test_runner.py::test_replay_runner_completes_against_real_fixture`, `test_runner_no_forbidden_calls.py::test_replay_runner_never_calls_forbidden_monitoring_scripts` |
| AC #3 — snapshot test: zero diff in `tickets/**` and `agent-monitoring/*.jsonl` | Steps 4, 5 | `test_no_mutation_snapshot.py` |
| AC #4 — fails clearly (raises), never silent/partial, on missing required fixture field | Step 3 | `test_fixture_envelope.py::test_replay_runner_fails_clearly_on_missing_required_fixture_field` (parametrized ≥3 fields) |
| AC #5 — fixture envelope shape evaluated against the ADR's Contract Representation decision, written down | Step 1 | `test_fixture_spec_doc.py::test_spec_doc_cites_adr_contract_representation` |

## Anti-Drift Notes

- **The unconditional hook prohibition is the single highest-stakes constraint in this ticket.**
  Every step touching `tools/agent_replay/` must be reviewed against it individually; Step 6's
  AST scan is the mechanical backstop, but the constraint applies from the first line of code
  written in Step 4, not just at test time.
- **`record_run.py`/`record_events.py` are importable, not just subprocess-callable** — Step 6's
  scan explicitly covers both invocation shapes; a reviewer or implementer must not treat a
  subprocess-only grep as sufficient.
- **Do not conflate Step 5 (snapshot/no-mutation) with Step 6 (no-forbidden-calls).** They prove
  different things and must remain two separate test files/assertions — the ticket's AC #2 wording
  ("not merely by output-diffing") exists specifically to prevent Step 5 alone from being cited as
  satisfying AC #2.
- **The fail-closed behavior (Step 3/AC #4) is a deliberate inversion of this repo's dominant
  fail-open monitoring-write convention** (CLAUDE.md: "Monitoring write failure must never fail the
  workflow"). Do not let a test author or implementer reflexively copy that convention into
  `fixture_envelope.py` — this module must raise, not warn-and-continue.
- **The Review phase's `verdict`/`violations` fixture fields are reconstructed from real
  `events.jsonl` `status`/`summary` fields, not literally persisted anywhere as full JSON.** Step 2
  makes this traceable via an explicit in-file comment; this is a known, documented, real-fixture
  limitation (not a synthetic-data violation) and must not be silently smoothed over as if the full
  `REVIEW_SCHEMA` return had been recorded verbatim somewhere.
- **`tests/replay/` vs `tests/agent_replay/` naming is a deliberate, documented Plan-phase choice**
  (see Summary) — an implementer should not "helpfully" consolidate the new tests into the existing
  `tests/replay/` directory; that would reintroduce the domain-conflation problem this plan
  explicitly avoids.
- **Do not expand `replay_slice` to cover Implement or later phases**, even if it looks like a
  small addition once Scope→Review works — that requires a `files_changed`/diff fixture payload
  this ticket's Out of Scope section does not authorize building.
- **`docs/REGISTRY.yaml` regeneration**: this ticket creates a new file under `docs/ai/`
  (`replay_fixture_spec.md`), so Finalize's mandatory `make knowledge-index-update` /
  `docs/REGISTRY.yaml` regeneration step applies — do not skip it because the rest of this ticket's
  work is under `tools/`/`tests/`.

## Deviations

- **Step 6's AST scan widened per architecture-review advisory (non-blocking, applied as
  instructed).** In addition to the plan's 3 scoped checks (forbidden imports,
  subprocess/os.system call-argument literals, `importlib.import_module` calls), added a 4th
  scan — `test_no_forbidden_filename_substring_in_any_string_constant_in_the_file` — that walks
  every `ast.Constant` string node in each `tools/agent_replay/*.py` file, not just
  call-argument-scoped ones. This catches indirect variable-based construction (e.g. `SCRIPT =
  "record_run.py"` then `subprocess.run([sys.executable, SCRIPT])`) that the plan's 3 narrower
  checks would miss, per the architecture review's own reasoning. Consequence: `runner.py`'s
  module docstring, which originally (in the first draft written during Implement) named the four
  forbidden scripts with their literal `.py` filenames in prose, had to be rewritten to describe
  them without the `.py` suffix and defer the full filenames to
  `docs/ai/replay_fixture_spec.md` instead — otherwise the widened scan would flag the runner's own
  legitimate documentation prose as a false positive. This is a strictly more conservative check,
  consistent with the ticket's fail-closed philosophy, and was cheap to add — no scope expansion
  beyond what the architecture review explicitly asked for.
- No other deviations. All 6 steps, file locations (`tools/agent_replay/`, `tests/agent_replay/`,
  `tests/fixtures/agent_replay/`), and the 5 Plan-phase decisions in this document's Summary were
  followed as written.

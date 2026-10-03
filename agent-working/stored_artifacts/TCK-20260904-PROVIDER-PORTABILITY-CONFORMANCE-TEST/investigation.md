---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST
artifact_type: investigation
tags: [testing, ai, architecture]
---

# Investigation — TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST

## Current Behavior

### `agent-orchestration/` contract — the 2 existing axes vs. the 2 new axes

`agent-orchestration/contract.yaml` (top-level manifest) `governs:` 7 sibling files today:
`workflows/implement-ticket.yaml`, `roles/` (11 files), `skills.yaml`, `monitoring-schema.yaml`,
`hook-events.yaml`, `hook-surface-policy.yaml`, `terminal-statuses.yaml`. There is no
`gate-policy.yaml`, no `artifact-requirements.yaml`, and no `governs:` entry naming either
concept.

`agent-orchestration/workflows/implement-ticket.yaml` (`workflow_version: 2`) declares, per phase,
only `name` and `tiers: {standard: <mode>, hotfix: <mode>}` (+ optional `condition`/`if_false` for
the 2 conditional phases, Parity/Security-Review) — e.g.:
```yaml
- name: Review
  tiers: {standard: full, hotfix: skipped_event}
- name: Security-Review
  tiers: {standard: conditional, hotfix: conditional}
  condition: security_tag_or_suggested_skill
  if_false: conditional_absent
```
`condition`/`if_false` here describe **whether the phase runs at all per tier** (the
phase-order/tier-applicability axis TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER already covers), not
**what makes the phase pass or fail once it runs**. There is no field anywhere in this file, or in
any of the 11 `agent-orchestration/roles/*.yaml` files (all read: each carries only
`role_version`, `role_id`, `description`, `phases: [...]`, `has_agent_file`, optionally
`inline_prompt_exception` — confirmed by reading `architecture-reviewer.yaml`, `done-checker.yaml`,
`investigator.yaml` and the schema in `tools/agent_orchestration/loader.py`'s
`_REQUIRED_ROLE_KEYS`), that records a gate condition (e.g. "Review requires
architecture-reviewer verdict == APPROVED" or "Verify requires done-checker's static precheck to
report zero failing items").

**Confirmed absence, with direct evidence**: `tools/agent_orchestration/loader.py`'s
`ContractBundle`/`RoleEntry` dataclasses and every `_REQUIRED_*_KEYS` tuple (lines 22-39) contain
no `gate_policy` or `artifact_requirements` key anywhere across all 7 validated files. This
matches the ticket's own Assumption exactly — these 2 axes do **not** exist as structured,
diffable fields in `agent-orchestration/` today.

The one place these two axis *names* already appear is
`agent-orchestration/intentional-divergences.md`'s `## Entry Format` documentation block (not
`contract.yaml`'s validated data): `Axis: terminal_status | phase_order | gate_policy |
artifact_requirements`, with an explicit forward-reference: "`<value-or-id>` is the specific
phase name or terminal-status value the divergence concerns (or a short slug for
`gate_policy`/`artifact_requirements` divergences, **once those axes gain conformance tests**)."
This means the divergence-approval mechanism (`tools/agent_orchestration_claude_adapter/divergence_log.py`)
already accepts these two axis strings today with zero code change — `is_approved(divergences,
axis="gate_policy", value=<slug>)` works as soon as a matching `## gate_policy:<slug>` section
exists in that file. Reuse is genuinely available for the *approval mechanism*; it is the
*contract data* side that is missing.

### Gate policy — the live JS side (`.claude/workflows/implement-ticket.js`, 1711 lines)

The live gate logic is heterogeneous across phases, in 3 distinct mechanisms:

1. **Agent-verdict gates** (Review :690-745, Architecture-Verify :980-1027, Security-Review
   :1353-1380-ish). Each phase's agent-call schema declares
   `verdict: { type: 'string', enum: ['APPROVED', 'NEEDS_CHANGES', 'BLOCKED'] }`; the gate itself
   is a plain JS conditional, e.g. `if (review.verdict !== 'APPROVED') { ... await
   writeMonitoring(review.verdict) ... return }` (line 729) / `if (archVerify.verdict !==
   'APPROVED')` (line 1011). `NEEDS_CHANGES`/`BLOCKED` are exactly the 2 `verdict_derived`
   terminal-status entries `agent-orchestration/terminal-statuses.yaml` already records — but that
   file records only the *resulting status value*, never the *enum + gate condition* that produced
   it. The enum + `!== 'APPROVED'` check is a **stable, literal, regex-extractable pattern** in
   the JS source (3 near-identical schema blocks + 3 near-identical `if (X.verdict !== 'APPROVED')`
   guards).

2. **Orchestrator-run static-script gates** (no agent call at all): doc-staleness gate
   (Implement phase, :865-943, wraps `tools/gate_checks/doc_staleness_check.py::check_doc_staleness`,
   fails to `DOC_STALENESS_BLOCKED`); Test phase's 3 sub-gates (`tools/gate_checks/test_scope_coverage_static.py::check_test_scope_coverage`
   → `TEST_SCOPE_COVERAGE_FAILED`, the test-scoper's own pass/fail → `TESTS_FAILED`,
   `tools/gate_checks/done_checker_static.py::clean_data_runs_early` → `DATA_RUNS_CLEAN_FAILED`);
   Parity phase's `tools/gate_checks/parity_updater_static.py::cross_reference_touched` (:1303-1338,
   fails to `pushEvent('Parity', ..., 'failed', ...)`, no dedicated terminal-status literal —
   folds into the generic Parity failure path) plus its separate **skip-eligibility** condition
   (files_changed has no `src/` path AND `behavior_changed` is false → skip the parity-updater
   agent call entirely, with a P0-ledger-safeguard override, :1191-1222); Verify phase's
   `tools/gate_checks/done_checker_static.py::run_static_precheck` (:1452), which itself aggregates
   the ~13 named Definition-of-Done conditions (`check_staging_artifacts_complete`,
   `check_frontmatter_valid`, `check_docs_to_update_coverage`, etc., lines 679+) into one
   `DOD_BLOCKED` value on any failure — already documented as "the one gate status that collapses
   multiple distinct DoD conditions into a single value" (implement-ticket.js comment, line 240).

3. **Conditional-trigger gates** (Parity's skip-eligibility above, and Security-Review's own
   *entry* condition — distinct from its *pass/fail* condition — `tags.includes('security') ||
   suggested_skills.includes('/security-review')`, line 1348).

**Is a Python test parsing the JS source text mechanically feasible for gate_policy, matching the
existing 2 tests' static-text-parsing pattern?** Yes, but only as a **narrower-scoped extraction**
than a naive "replicate every script's internal branch logic in YAML" approach would require.
The existing precedent (`extract_meta_phases`'s bracket-depth scan for `title:` strings,
`extract_all_terminal_statuses`'s 3-mechanism regex/literal-scan) already establishes that this
codebase's convention for extracting structured data from `implement-ticket.js` is: identify a
small number of stable literal patterns (a JSON-schema-shaped enum block, a `writeMonitoring('...')`
call, a `from gate_checks.X import Y` line) and regex/text-scan for them — never a full JS parser.
The same approach mechanically works for gate_policy **at the granularity of "which mechanism
backs this phase's gate, and which script/module + terminal-status value(s) result"** — e.g.
`{"phase": "Review", "gate_type": "agent_verdict", "verdict_enum": ["APPROVED","NEEDS_CHANGES","BLOCKED"], "pass_value": "APPROVED", "on_fail_status": ["NEEDS_CHANGES","BLOCKED"]}` and
`{"phase": "Implement", "gate_type": "static_check", "check_module": "gate_checks.doc_staleness_check", "check_function": "check_doc_staleness", "on_fail_status": ["DOC_STALENESS_BLOCKED"]}`.
Attempting to *also* re-derive each static script's internal pass/fail predicate (e.g. every one
of `done_checker_static.py`'s ~13 DoD sub-conditions) into the YAML contract itself would
duplicate business logic that already lives correctly in those scripts — an architecture
anti-pattern per this repo's own "shared behavior goes through systems/registries, not scattered
local hacks" principle, and the same restraint the ADR's own Conformance Mechanism decision
already modeled ("stating only the principle ... rather than inventing test shape ... avoids
over-specifying an implementation detail"). **This module-name/status-mapping granularity is the
recommended design** — it is genuinely diffable (the `from gate_checks.X import Y` lines and
`writeMonitoring('STATUS')` calls are both already-extracted-elsewhere literal patterns) without
requiring the contract to re-implement gate internals.

### Artifact requirements — the live Python side

`tools/gate_checks/done_checker_static.py:53`:
```python
REQUIRED_ARTIFACT_FILES = ("plan.md", "investigation.md", "test_plan.md")
```
and `check_staging_artifacts_complete(ticket_id, tier, base_dir=Path("staging_artifacts"))`
(line 148): `if tier == "hotfix": return ("NA", "hotfix tier — staging artifacts not required")`,
else checks all 3 files in `REQUIRED_ARTIFACT_FILES` exist and are non-blank under
`staging_artifacts/{ticket_id}/`. This is a single tuple constant plus one tier branch — by far
the simplest of the 2 new axes to extract (import the module and read the constant directly, or
regex the literal tuple — either works; importing is more robust and is already the pattern
`tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py` uses for its
contract-side load via `terminal_status_loader.load_terminal_statuses`). `CLAUDE.md`'s own
"Required Artifacts (standard/epic only)" section documents the same 3 files in prose, and
`.claude/workflows/implement-ticket.js:171` gates staging-directory creation on
`tier !== 'hotfix'` identically. All 3 documented sources already agree — there is no live
ambiguity to resolve for this axis, unlike gate_policy.

### `.codex/config.toml` vs. `AGENTS.md` — confirmed

`.codex/config.toml` (read in full, 12 lines) is confirmed deliberately inert: "This file
deliberately contains ZERO hook registrations — no `[hooks]` table, no per-event hook arrays, at
any nesting level" (its own header comment, referencing `TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE`).
It carries no phase, gate, or artifact content whatsoever — the ticket's claim is correct.

`AGENTS.md` (read in full, 72 lines, generated by
`tools/agent_orchestration_codex_adapter/generator.py::build_agents_md`) is the real translated
Codex artifact. Reading its generator (`build_agents_md`, lines 40-51) and the generated file
itself confirms it currently renders: an `## Engine Authority` note, a `## Workflow:
implement-ticket` phase-name list (bare names only — no tier/condition/gate data), a `##
Workflow Continuation` section (the optional `continuation_policy` prose), a `## Roles` list
(`role_id` + `description` only — no `phases` mapping rendered, despite `RoleEntry.phases`
existing in the loaded bundle), and a `## Skills` list. **There is no gate-policy or
artifact-requirements content in `AGENTS.md` today** — confirming the ticket's own hedge ("probably
nothing yet, requiring the Codex-side generator to also be extended"). A Codex-side conformance
test that diffs "AGENTS.md content" against the new axes therefore requires `build_agents_md` to
first be extended to render whatever new `gate_policy`/`artifact_requirements` sections
`load_contract()` gains — this is a second, smaller extension task (mirrors the existing
`## Roles`/`## Skills` list-rendering pattern already in the function) layered on top of the
contract-schema-extension prerequisite, not a separate design problem.

### Existing conformance pattern (must be extended, not reinvented)

- `tests/agent_orchestration_claude_adapter/test_phase_order_conformance.py` — diffs
  `extract_meta_phases(live .js)` against `render_claude_adapter(...)['phase_order']`, checked
  against `divergence_log.is_approved(axis="phase_order", value="phase_order")` before hard-failing.
- `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py` — diffs
  `extract_all_terminal_statuses(live .js)` (3-mechanism extractor: literal / verdict_derived /
  bypass, in `terminal_status_extractor.py`) against `load_terminal_statuses(repo_root)` (contract
  side), as a set of `(value, kind)` pairs, per-value approval via
  `is_approved(axis="terminal_status", value=<status value>)`.
- Both tests diff **live code → contract** (never the reverse), matching this ticket's own Scope
  instruction, and both route any mismatch through `divergence_log.load_divergences` +
  `is_approved` before hard-failing — this is the exact reusable mechanism this ticket's 2 new
  tests must also use.
- `tools/agent_orchestration_claude_adapter/generator.py::render_claude_adapter` writes only under
  `agent-orchestration/rendered/` (structural write-guard, `ClaudeAdapterWriteGuardError`), never
  under `.claude/` — the new axes' data should be added to this same render function's output dict
  (`build_claude_adapter_representation`), not a new generator.

## Mechanics / Engine Constraints

None. This ticket is agent-orchestration developer tooling only — no `src/` simulation code,
`docs/mechanics/`, or `docs/engine/` contract is touched or constrains this work. Confirmed via
`docs/parity_ledger/infrastructure.yaml`'s existing entries for this same subsystem (e.g.
INFRA-316's `support_boundary`: "Agent-orchestration/monitoring-pipeline tooling only — no
simulation behavior is involved").

## Docs Requiring Update

- `docs/architecture/agent_orchestration_contract.md`: the ADR's "Conformance Mechanism" section
  is `Status: Proposed-pending-implementation-evidence` and its "Revisit Trigger" section says
  "Conformance Mechanism is revisited once the first provider adapter conformance test is actually
  written" — the 2 existing tests (TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER) already triggered a
  partial revisit for `phase_order`/`terminal_status`; this ticket extends coverage to
  `gate_policy`/`artifact_requirements` and should update this section's status/evidence
  accordingly once both new tests exist and pass.
- `agent-orchestration/README.md`: its "Layout" table must gain a row for whatever new sibling
  file(s) this ticket adds (e.g. a `gate-policy.yaml` analogous to `terminal-statuses.yaml`, and/or
  an `artifact_requirements` field/file) — the table currently lists exactly the 7 files
  `contract.yaml` `governs:`, and is the single documented index of "what's here."

The `docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md` doc
(under `docs/plans/`) is not required to change for this ticket: it is the original discovery-tier
plan already fully consumed by the ADR and by `TCK-20260721-ORCHESTRATION-CONTRACT-CORE`'s
implementation; this ticket is downstream conformance-test work within the already-decided
contract shape, not a plan revision.

`agent-orchestration/intentional-divergences.md` is not required to change for this ticket's own
sake: its `## Entry Format` documentation already names `gate_policy`/`artifact_requirements` as
valid axis values (see Current Behavior above) — no doc edit is needed there unless this ticket's
deliberately-introduced-mismatch fixture (AC #3) is itself committed as a real, permanent
`RATIFIED` divergence entry rather than a transient test fixture, which Plan should decide.

## Parity Ledger Overlap

`docs/parity_ledger/infrastructure.yaml` is the relevant subsystem file (all prior
agent-orchestration/provider-adapter tickets recorded entries here — e.g. `INFRA-316`, status
`verified`, priority `P2`, `test_path: tests/tools/test_glossary_registry.py,tests/agent_orchestration/test_bootstrap_vocabulary_equality.py::test_bootstrap_phase_agent_vocabulary_matches_vocabulary_py,tests/agent_orchestration/test_contract_structure.py`).
No existing entry specifically covers gate_policy/artifact_requirements conformance — this ticket
should add a new `INFRA-*` entry (next available id via
`tools/gate_checks/parity_updater_static.py::next_available_id("infrastructure.yaml", ...)`) once
implemented, at `priority: P2` (matching every sibling agent-orchestration-tooling entry; none of
these are P0 — this subsystem has never carried a P0 entry, since it does not touch simulation
behavior). No P0 entries are implicated, so no `test_path` is hard-required for merge, but one
should still be recorded per the ledger's normal discipline.

## Prior Work

- `stored_artifacts/TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER/` (`investigation.md`, `plan.md`,
  `test_plan.md`) — the direct predecessor this ticket extends; its `test_plan.md`'s New-Tests
  structure (numbered test entries with Category/Verifies/Location, an Anti-Drift Test Guards
  section per new behavior) is the template this ticket's own `test_plan.md` follows.
- `TCK-20260817-STANDARD-AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT` (registry-matched via
  `related_code_areas` containing `tools/agent_orchestration_codex_adapter/generator.py`) —
  confirms `AGENTS.md`'s phase-count rendering has drifted before and has its own regression test;
  any change to `build_agents_md`'s phase-list rendering in this ticket must not reintroduce that
  class of drift.
- `TCK-20260804-DOC-UPDATER-ROLE-FILE` (registry-matched) — precedent for "a
  `agent-orchestration/roles/*.yaml` gap discovered post-close, fixed by adding the missing file
  and correcting stale count literals across `test_contract_structure.py` + README" — same shape
  of fix this ticket's gate_policy prerequisite may need if it adds new role-file fields.
- `TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH` (registry-matched) — a `tests/agent_orchestration/test_contract_structure.py`
  staleness fix; this ticket must re-run that test (and its sibling structural guards) since it
  is expected to add a new required field to schemas that test may assert against structurally.
- `TCK-20260730-PROVIDER-HOOK-POLICY` — precedent for adding a **new sibling contract file**
  (`hook-surface-policy.yaml`) to `agent-orchestration/` as a non-breaking addition (new
  `governs:` entry, own independent version counter) — directly analogous to how a new
  `gate-policy.yaml` (or equivalent) should be added for this ticket's gate_policy axis.

## Risks and Open Questions

1. **Open question (blocking Plan, not assumed here): what exact structural shape should
   `gate_policy` take?** Two real options exist and this investigation does not pick one:
   (a) the module/function + on-fail-status-mapping granularity recommended above (diffable,
   avoids duplicating script internals), or (b) a fuller per-check breakdown (e.g. naming each of
   `done_checker_static.py`'s ~13 DoD sub-conditions individually under Verify). Option (b) is
   more complete but risks becoming a second, YAML-shaped copy of `done_checker_static.py`'s own
   condition list that then itself needs a conformance test to stay in sync — a regress. Plan must
   pick one explicitly; this ticket's Scope note ("if that representation doesn't exist yet, add
   it ... or explicitly scope that as a prerequisite") is satisfied either way, but the two options
   have materially different implementation size.
2. **Versioning bump — corrects the ticket's own Scope wording.** The ticket's Scope says a
   schema extension needs "a versioning bump per `agent-orchestration/README.md`'s bump rule."
   Direct evidence from the README's own bump rule contradicts this as a blanket requirement: "A
   non-breaking addition (**a new optional field, a new role/skill entry**) does not bump the
   counter." Adding `gate_policy` as a new optional field to `workflows/implement-ticket.yaml`'s
   phase entries, or adding a new sibling file (`gate-policy.yaml`) to `contract.yaml`'s `governs:`
   list (directly precedented by `TCK-20260730-PROVIDER-HOOK-POLICY`'s `hook-surface-policy.yaml`
   addition, which did not bump `contract.yaml`'s `version`), is a **non-breaking addition** by
   this same rule — no version bump is required unless Plan's chosen shape requires renaming or
   restructuring an *existing* required field (which none of the options above do). Do not bump
   `workflow_version`/`contract.yaml`'s `version` unless Plan's concrete design turns out to need a
   breaking reshape.
3. **`AGENTS.md` rendering gap for `## Roles`.** `build_agents_md` already loads `RoleEntry.phases`
   into the bundle but does not render it in `AGENTS.md`'s `## Roles` section today (only
   `role_id`/`description` are rendered). If gate_policy or artifact_requirements end up
   role-scoped in the new schema, the Codex-side conformance test's fixture-fed AGENTS.md content
   will need this rendering gap closed too — a small, in-scope addition to `build_agents_md`, not
   a design risk, but worth flagging so it isn't discovered as a surprise mid-Implement.
4. **Deliberately-introduced-mismatch fixture (AC #3) must not corrupt real contract state.**
   Both existing conformance tests render against `tmp_path`, never the committed
   `agent-orchestration/rendered/claude-adapter.yaml` (that freshness is a separate test's
   concern, `test_claude_containment.py`). The new axes' mismatch fixtures must follow the same
   discipline — mutate a `tmp_path`-rendered copy or an in-memory dict, never
   `agent-orchestration/`'s real committed YAML.

## Anti-Drift Hazards

- **Do not let gate_policy re-derive `done_checker_static.py`'s internal DoD logic into YAML.**
  The contract should record *which check backs which phase's gate and which terminal status
  results*, not duplicate each check's internal pass/fail predicate — duplicating logic here is
  exactly the "second, possibly-inconsistent" drift class this ADR and its sibling tickets have
  repeatedly hit (see `INFRA-316`'s own history of a vocabulary site falling out of sync).
- **Do not conflate `condition`/`if_false` (existing phase-order/tier-applicability fields) with
  the new gate_policy axis.** They answer different questions ("does this phase run at all for
  this tier" vs. "what makes this phase pass/fail once it runs") and must not be merged into one
  field or one test.
- **Do not touch `docs/guidelines/intentional_divergences.md`** (the separate mechanics-bible
  divergence log) — only `agent-orchestration/intentional-divergences.md` is in scope, exactly as
  the existing `test_claude_containment.py` already guards for the 2 existing axes.
- **Do not let the Codex-side test compare against `.codex/config.toml`** — it is confirmed inert;
  any Codex-side axis-2/axis-3 test must target `AGENTS.md` (or explicitly document why not, per
  AC #4), never `.codex/config.toml`.
- **Do not widen scope into rebuilding the phase_order/terminal_status axes** — both are already
  fully covered by `TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER`'s tests; this ticket adds exactly 2
  new axes alongside them, reusing (not reimplementing) `extract_meta_phases`,
  `extract_all_terminal_statuses`, `divergence_log.is_approved`, and `render_claude_adapter`'s
  existing write-guard/containment discipline.

---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST
artifact_type: test_plan
tags: [testing, ai, architecture]
---

# Test Plan — TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST

## Regression Surface

**Unit / contract structure:**
- `tests/agent_orchestration/test_contract_structure.py` — this ticket adds new field(s) to
  `contract.yaml`/`workflows/implement-ticket.yaml`/`roles/*.yaml` (whatever shape Plan picks for
  `gate_policy`) and/or a new sibling file for `artifact_requirements`; every existing structural
  assertion here (required-key checks, role count, phase count) must stay green — this file has
  drifted before (`TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH`,
  `TCK-20260804-DOC-UPDATER-ROLE-FILE`'s `== 10` → `== 11` fix) so it is the single most
  regression-sensitive file for this ticket's own schema change.
- `tests/agent_orchestration/test_bootstrap_vocabulary_equality.py`,
  `tests/agent_orchestration/test_skills_catalog.py`,
  `tests/agent_orchestration/test_validator_errors.py`,
  `tests/agent_orchestration/test_validator_no_network_calls.py` — `load_contract()`'s existing
  validated shape and no-network-call guarantee must not regress.
- `tests/tools/test_workflow_meta_conformance.py` — the live-extraction primitive
  (`extract_meta_phases`) this ticket's gate_policy extractor is expected to sit alongside/reuse
  patterns from; must stay green since it is a real dependency of the existing phase_order test.

**Unit / Claude adapter (existing 2 axes — must not regress while adding the 2 new ones):**
- `tests/agent_orchestration_claude_adapter/test_phase_order_conformance.py`
- `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py`
- `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py`
- `tests/agent_orchestration_claude_adapter/test_terminal_status_schema.py`
- `tests/agent_orchestration_claude_adapter/test_generator_containment.py`
- `tests/agent_orchestration_claude_adapter/test_claude_containment.py` (zero-diff-under-`.claude/`
  proof — this ticket must never write to `.claude/`)

**Unit / Codex adapter (must not regress; this ticket extends `build_agents_md`):**
- `tests/agent_orchestration_codex_adapter/test_agents_md_generation.py`
- `tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py`
- `tests/agent_orchestration_codex_adapter/test_generator_traceability.py`
- `tests/agent_orchestration_codex_adapter/test_generator_write_guard.py`
- `tests/agent_orchestration_codex_adapter/test_legacy_skills_containment.py`
- `tests/agent_orchestration_codex_adapter/test_no_production_hook_enabled.py` — `.codex/config.toml`
  must remain hook-free; this ticket must not add anything there.
- `tests/agent_orchestration_codex_adapter/test_reference_resolution.py`
- `tests/agent_orchestration_codex_adapter/test_requires_valid_contract.py`

**Unit / the live gate-check scripts this ticket's gate_policy extractor reads (must not regress —
this ticket reads, never edits, their logic):**
- any existing `tests/tools/test_done_checker_static.py`-style tests, `tests/tools/test_doc_staleness_check.py`,
  `tests/tools/test_architecture_reviewer_static.py`, `tests/tools/test_parity_updater_static.py`,
  `tests/tools/test_test_scope_coverage_static.py` if present (locate at Plan/Implement time via
  `test-scoper`'s file-to-test mapping; not enumerated here since this investigation did not open
  every one of these files — flag as a Plan-time lookup, not assumed).

**No `src/` regression surface** — this ticket touches no simulation code; `tests/unit/`,
`tests/parity/`, `tests/integration/` outside the domains above are out of scope for this ticket's
own verification pass (per CLAUDE.md's Testing Rule, still covered by CI generally).

## New Tests Required

Per Acceptance Criteria (exact package path is a Plan-phase decision; assume a new
`tools/agent_orchestration_claude_adapter/gate_policy_extractor.py` +
`artifact_requirements_loader.py`-shaped pair, or equivalent, alongside the existing
`terminal_status_extractor.py`/`terminal_status_loader.py` split — mirror that predecessor's
live-extractor-vs-contract-loader naming convention rather than inventing a new one):

1. **`test_gate_policy_conformance_full_match_both_directions`** (AC #1)
   Category: unit / conformance test
   Verifies: a new live extractor (e.g. `extract_gate_policy(workflow_js_path)`) pulls, per
   agent-verdict-gated phase (Review, Architecture-Verify, Security-Review), the verdict enum and
   pass-value from the JS source's `verdict: { type: 'string', enum: [...] }` schema blocks +
   `if (X.verdict !== 'APPROVED')` guards, and per static-check-gated phase (Implement,
   Test ×3 sub-gates, Parity, Verify) the `from gate_checks.<module> import <function>` line +
   resulting `writeMonitoring('STATUS')` value(s) — then diffs this against a new contract-side
   `gate_policy` structured field (whatever sibling file/field Plan lands on), checked against
   `divergence_log.is_approved(axis="gate_policy", value=<phase-or-slug>)` before hard-failing,
   exactly mirroring `test_terminal_status_conformance_full_match_both_directions`'s
   missing-from-contract/missing-from-live set-diff shape.
   Location: `tests/agent_orchestration_claude_adapter/test_gate_policy_conformance.py`.

2. **`test_gate_policy_extractor_covers_all_12_phases_or_explicitly_excludes_a_gateless_phase`**
   Category: unit / architecture guard
   Verifies: every one of the 12 live phases (`Scope` through `Finalize`) is either represented in
   the extracted gate_policy vocabulary or explicitly, documentedly excluded (e.g. `Scope`/`Plan`/
   `Document-Update` may have no hard pass/fail gate today — the test must assert this is a
   deliberate documented omission, not a silent gap), mirroring
   `test_scope_agent_failed_handling_is_an_explicit_documented_decision`'s "explicit inclusion or
   explicit documented exclusion, never silent" pattern from the predecessor ticket.
   Location: same test module.

3. **`test_gate_policy_deliberately_introduced_mismatch_fails_without_approval`** (AC #3, gate_policy
   half)
   Category: unit / negative-fixture conformance
   Verifies: given a fixture contract dict with one phase's gate_policy entry deliberately altered
   (e.g. Review's pass-value changed from `APPROVED` to a wrong value, or Verify's backing check
   module renamed), the conformance test fails when no divergence-log entry approves it, and
   passes once a fully-formed `RATIFIED` entry (`Axis: gate_policy`) is added to a fixture copy of
   `agent-orchestration/intentional-divergences.md` — proves the divergence-approval mechanism is
   genuinely wired for this axis, not just documented. Never mutates the real
   `agent-orchestration/` files — operates on `tmp_path` copies only, per the containment
   discipline `test_claude_containment.py` already establishes.
   Location: same test module.

4. **`test_artifact_requirements_conformance_full_match`** (AC #2)
   Category: unit / conformance test
   Verifies: a new contract-side `artifact_requirements` field (per-tier required staging-artifact
   filename list: `{"standard": ["plan.md","investigation.md","test_plan.md"], "epic": [...],
   "hotfix": []}`) matches `tools.gate_checks.done_checker_static.REQUIRED_ARTIFACT_FILES` and its
   `tier == "hotfix"` branch exactly, for every tier value the live code actually branches on.
   Diffed live-code → contract (never the reverse), routed through
   `divergence_log.is_approved(axis="artifact_requirements", value=<tier>)` before hard-failing.
   Location: `tests/agent_orchestration_claude_adapter/test_artifact_requirements_conformance.py`.

5. **`test_artifact_requirements_deliberately_introduced_mismatch_fails_without_approval`** (AC #3,
   artifact_requirements half)
   Category: unit / negative-fixture conformance
   Verifies: given a fixture contract dict where the `standard` tier's required-file list is
   deliberately missing one of `plan.md`/`investigation.md`/`test_plan.md` (or has an extra bogus
   entry), the test fails without a matching `RATIFIED` divergence entry and passes with one —
   same shape as test #3 above, applied to the simpler axis.
   Location: same test module as #4.

6. **`test_codex_agents_md_reflects_gate_policy_and_artifact_requirements_or_documents_the_gap`**
   (AC #4)
   Category: unit / Codex-side conformance (or explicit documented-gap test if Plan chooses the
   fallback path)
   Verifies EITHER: (a) `AGENTS.md`, regenerated via
   `tools.agent_orchestration_codex_adapter.generator.build_agents_md`, renders sections for the
   new `gate_policy`/`artifact_requirements` contract data (extending `build_agents_md` the same
   way its existing `## Roles`/`## Skills` list-rendering was added) and this rendered content is
   diffed against the same contract data the Claude-side tests #1/#4 check, per-axis approval via
   the same `divergence_log.is_approved()` mechanism; OR (b), if Plan explicitly redirects per
   AC #4's fallback clause, this test instead asserts `.codex/config.toml` contains zero
   gate/artifact content (a `test_no_production_hook_enabled.py`-style negative-content assertion)
   AND that `AGENTS.md`'s generator is the named, correct redirect target in a code comment/doc —
   never silently skip this AC by testing nothing.
   Location: `tests/agent_orchestration_codex_adapter/test_gate_policy_artifact_requirements_conformance.py`.

7. **`test_gate_policy_does_not_duplicate_static_check_internal_logic`**
   Category: architecture guard (anti-drift, per investigation.md's Anti-Drift Hazards)
   Verifies: the new `gate_policy` contract field's schema, as actually implemented, records only
   `{phase, gate_type, check_module/verdict_enum, on_fail_status}`-shaped data (module/function
   names + resulting terminal-status mapping) and does NOT re-encode any of
   `done_checker_static.py`'s ~13 named DoD sub-condition predicates as separate YAML entries — a
   structural assertion on the loaded schema's keys, catching scope creep toward "re-implement
   done-checker's logic in YAML" during Implement.
   Location: `tests/agent_orchestration_claude_adapter/test_gate_policy_conformance.py` (same
   module as #1/#2/#3) or `tests/agent_orchestration/test_contract_structure.py` if Plan judges
   this a general contract-structure guard rather than a Claude-adapter-specific one.

## Scoped Pytest Commands

```
pytest tests/agent_orchestration/ tests/agent_orchestration_claude_adapter/ \
       tests/agent_orchestration_codex_adapter/ tests/tools/test_workflow_meta_conformance.py -v
```

Never `pytest tests/` — scoped to the `agent_orchestration`/`agent_orchestration_claude_adapter`/
`agent_orchestration_codex_adapter` domains per CLAUDE.md's Testing Rule. If Plan's chosen
gate_policy design also touches one or more `tools/gate_checks/*_static.py` modules' public
surface (imports only, never edits, expected) add their existing test modules explicitly once
located at Plan/Implement time.

## Anti-Drift Test Guards

- **Live-code → contract direction guard**: every new test above diffs the live JS/Python source
  against the contract, never the reverse — matching this ticket's own Scope instruction and the
  2 existing tests' direction. A test that instead asserts contract-conforms-to-itself would be a
  false-positive-prone regression.
- **No re-derivation of DoD internals guard** (test #7): the single highest scope-creep risk this
  ticket faces per investigation.md — catches an implementation that quietly turns the new
  gate_policy schema into a second, YAML-shaped copy of `done_checker_static.py`'s condition list.
- **`.codex/config.toml` non-target guard**: a test (or an assertion embedded in test #6) must
  confirm no new test in this ticket's own tree treats `.codex/config.toml` as a diffable
  gate/artifact source — catches accidentally reverting to the ticket's own originally-flagged
  wrong framing.
- **Containment guard reused, not reinvented**: new fixture-mismatch tests (#3, #5) must operate
  on `tmp_path`/in-memory copies only, never mutate the committed
  `agent-orchestration/{contract.yaml,workflows/implement-ticket.yaml,roles/*.yaml,intentional-divergences.md}`
  — reuse the existing `test_claude_containment.py`/`test_generator_write_guard.py` zero-diff
  pattern rather than writing a new one.
- **Version-bump-not-required guard**: a test (or a plain assertion in `test_contract_structure.py`)
  should confirm `contract.yaml`'s `version` and `workflows/implement-ticket.yaml`'s
  `workflow_version` are unchanged after this ticket's schema addition — catches an unnecessary
  breaking-style bump for what investigation.md establishes should be a non-breaking additive
  change (per the README's own bump rule and the `TCK-20260730-PROVIDER-HOOK-POLICY` precedent).
- **`condition`/`if_false` vs. `gate_policy` non-conflation guard**: a structural test asserting
  the new `gate_policy` field is a distinct key from the existing `condition`/`if_false` phase
  fields (not merged into or overloaded onto them) — catches the two axes' semantics (tier
  applicability vs. pass/fail condition) being silently collapsed together.

---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST
artifact_type: plan
tags: [testing, ai, architecture]
---

# Implementation Plan — TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST

## Summary

`gate_policy` and `artifact_requirements` do not exist as structured, diffable fields anywhere in
`agent-orchestration/` today (confirmed by direct read of `tools/agent_orchestration/loader.py`,
`agent-orchestration/contract.yaml`, `agent-orchestration/workflows/implement-ticket.yaml` — see
Step 1/2 citations). This plan adds both as **non-breaking, optional-or-newly-created** contract
data — `gate_policy` as a brand-new sibling file (`agent-orchestration/gate-policy.yaml`, own
independent version counter, mirroring `terminal-statuses.yaml`'s precedent exactly), and
`artifact_requirements` as a new **optional** field inline on `contract.yaml` (mirroring
`continuation_policy`'s existing optional-field-on-an-existing-file precedent) — then writes two
new Claude-adapter conformance tests and one Codex-adapter conformance test that diff live code
against this new contract data, exactly reusing the existing `divergence_log.py` approval
mechanism and the existing `extract_meta_phases`/`extract_all_terminal_statuses` static-text-scan
convention. `gate_policy`'s schema records **which mechanism backs each phase's gate and which
terminal-status value(s) result** — never re-deriving `done_checker_static.py`'s ~13 internal DoD
sub-conditions into YAML. No version bump is required anywhere (see Step 1/2's citations of the
README's own bump rule and the `hook-surface-policy.yaml`/`continuation_policy` precedents this
design copies exactly). Fresh evidence gathered while writing this plan surfaced one genuine,
previously-uncaught divergence in the *existing* `terminal_status` axis (`NEEDS_HUMAN_INPUT`'s
`phases: [Investigate]` in `terminal-statuses.yaml` does not match the live code, which gates it in
the **Plan** phase) — this plan does not fix that (out of scope; flagged under Anti-Drift Notes and
as a candidate follow-up hotfix ticket), and the new `gate_policy` extractor is designed to derive
phase attribution from live text position so it does not repeat this class of staleness for the new
axis.

## Steps

### Step 1 — Add `agent-orchestration/gate-policy.yaml` (new sibling file)

**Files:** `agent-orchestration/gate-policy.yaml` (new), `agent-orchestration/contract.yaml`

**Change:** Create a new sibling file exactly analogous to `agent-orchestration/terminal-statuses.yaml`
(read in full — its own header explicitly says "Added by TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER;
per the README's versioning note, a new sibling file needs no `workflow_version` bump", lines 1-6).
Content, derived from direct re-reading of `.claude/workflows/implement-ticket.js` at the line
numbers below (grepped fresh this session — cite these, not investigation.md's slightly older
numbers, since the file's own header convention documents line drift as expected):

```yaml
gate_policy_version: 1
workflow_id: implement-ticket

# gate_type vocabulary:
#   agent_verdict      — an agent's own schema-declared `verdict` enum gates the phase; pass_value
#                        is the one enum value that lets the phase continue past `if (X.verdict
#                        !== pass_value)`.
#   static_check       — an orchestrator-run Python check (no agent judgment) gates the phase.
#     invocation: import — `from gate_checks.<module> import <function>` (or, for the one
#                 non-gate_checks case, `from tag_registry import <function>`), after
#                 `sys.path.insert(0, 'tools')`.
#     invocation: cli    — invoked as `python3 tools/gate_checks/<module>.py <args>`, a standalone
#                 script entry point never imported by name — currently only doc_staleness_check.
#   agent_result_field — a non-verdict field on an agent's own output schema (boolean or array)
#                        gates the phase — no enum, just one pass/fail-shaped field.
#
# Deliberately does NOT re-derive any static_check module's own internal pass/fail predicate (e.g.
# done_checker_static.py's ~13 named DoD sub-conditions) — records only which module/function backs
# the gate and which terminal-status value(s) result on failure. See
# staging_artifacts/TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST/investigation.md's
# Anti-Drift Hazards for why.
gates:
  - phase: Scope
    gate_type: agent_result_field
    result_field: conflicts          # ticket-scoper's own SCOPE_SCHEMA field, implement-ticket.js:86
    pass_value: []                   # empty array passes (implement-ticket.js:444)
    on_fail_status: [CONFLICTS_DETECTED]
  - phase: Scope
    gate_type: static_check
    invocation: import
    check_module: tag_registry       # NOT gate_checks.tag_registry — tools/tag_registry.py directly
    check_function: check_tags_registered   # implement-ticket.js:411, tools/tag_registry.py:187
    on_fail_status: [TAGS_NOT_REGISTERED]
  - phase: Plan
    gate_type: static_check
    invocation: import
    check_module: gate_checks.plan_gate_static
    check_function: plan_has_unresolved_questions_heading   # implement-ticket.js:658, gate_checks/plan_gate_static.py:29
    on_fail_status: [NEEDS_HUMAN_INPUT]
    # NOTE: terminal-statuses.yaml (line 48-50) records NEEDS_HUMAN_INPUT's `phases: [Investigate]`.
    # This is stale relative to live code: phase('Plan') is called at implement-ticket.js:618 and
    # this gate's check (line 654-679, pushEvent('Plan', ...) at :671) sits textually inside the
    # Plan block, well after phase('Investigate') at :499 and before phase('Review') at :686.
    # Do NOT copy terminal-statuses.yaml's `phases` value here — this is a genuine, independently
    # re-derived correction for the gate_policy axis only. Not fixed in terminal-statuses.yaml
    # itself (out of scope — see Anti-Drift Notes).
  - phase: Review
    gate_type: agent_verdict
    verdict_enum: [APPROVED, NEEDS_CHANGES, BLOCKED]   # implement-ticket.js:692
    pass_value: APPROVED                                # implement-ticket.js:729
    on_fail_status: [NEEDS_CHANGES, BLOCKED]            # writeMonitoring(review.verdict), :735 — verdict passthrough
  - phase: Implement
    gate_type: static_check
    invocation: cli
    check_module: gate_checks.doc_staleness_check
    check_function: check_doc_staleness    # implement-ticket.js:892 (CLI, not import); gate_checks/doc_staleness_check.py:39
    on_fail_status: [DOC_STALENESS_BLOCKED]
  - phase: Architecture-Verify
    gate_type: agent_verdict
    verdict_enum: [APPROVED, NEEDS_CHANGES, BLOCKED]   # implement-ticket.js:982
    pass_value: APPROVED                                # implement-ticket.js:1011
    on_fail_status: [NEEDS_CHANGES, BLOCKED]            # writeMonitoring(archVerify.verdict), :1017 — verdict passthrough
  - phase: Test
    gate_type: static_check
    invocation: import
    check_module: gate_checks.test_scope_coverage_static
    check_function: check_test_scope_coverage   # implement-ticket.js:1093, gate_checks/test_scope_coverage_static.py:151
    on_fail_status: [TEST_SCOPE_COVERAGE_FAILED]
  - phase: Test
    gate_type: agent_result_field
    result_field: passed             # test-scoper's own TEST_SCHEMA field, implement-ticket.js:1041
    pass_value: true
    on_fail_status: [TESTS_FAILED]    # implement-ticket.js:1119-1122
  - phase: Test
    gate_type: static_check
    invocation: import
    check_module: gate_checks.done_checker_static
    check_function: clean_data_runs_early   # implement-ticket.js:1157, gate_checks/done_checker_static.py:209
    on_fail_status: [DATA_RUNS_CLEAN_FAILED]
  - phase: Parity
    gate_type: static_check
    invocation: import
    check_module: gate_checks.parity_updater_static
    check_function: cross_reference_touched   # implement-ticket.js:1303, gate_checks/parity_updater_static.py:96
    on_fail_status: [PARITY_INCOMPLETE]
    # Parity's separate skip-eligibility condition (paritySkipEligible, implement-ticket.js:1192-1222)
    # is a conditional-trigger, not a pass/fail gate — already fully covered by
    # workflows/implement-ticket.yaml's `condition: src_change_and_behavior_changed` /
    # `if_false: skipped_event` fields on the Parity phase entry. Do NOT add a second gate_policy
    # row for it.
  - phase: Security-Review
    gate_type: agent_verdict
    verdict_enum: [APPROVED, NEEDS_CHANGES, BLOCKED]   # implement-ticket.js:1355
    pass_value: APPROVED                                # implement-ticket.js:1378
    on_fail_status: [SECURITY_BLOCKED]    # implement-ticket.js:1384 — fixed literal, NOT verdict passthrough
    # (both NEEDS_CHANGES and BLOCKED verdicts collapse to the single SECURITY_BLOCKED status —
    # unlike Review/Architecture-Verify above, this is a `kind: literal` result in
    # terminal-statuses.yaml, not `verdict_derived`. Distinguishable structurally: on_fail_status
    # here does not equal verdict_enum minus pass_value.)
  - phase: Verify
    gate_type: agent_verdict
    verdict_enum: [READY_TO_CLOSE, BLOCKED]   # done-checker's own DONE_SCHEMA, implement-ticket.js:1405
    pass_value: READY_TO_CLOSE                 # implement-ticket.js:1465
    on_fail_status: [DOD_BLOCKED]    # implement-ticket.js:1470 — fixed literal (not "BLOCKED"), informationally
    # backed by gate_checks.done_checker_static.run_static_precheck (implement-ticket.js:1452) as
    # cited evidence for the agent's own verdict — run_static_precheck does NOT itself branch the
    # gate (the JS branches on doneCheck.verdict, the agent's own field, not the script's return
    # value directly). Do NOT add check_module/check_function keys here — that would misrepresent
    # this as a static_check gate when it is actually agent_verdict backed by evidence. Do NOT
    # enumerate run_static_precheck's ~13 named DoD sub-conditions as separate rows — this is the
    # single highest scope-creep risk this ticket faces (see investigation.md Anti-Drift Hazards).
  - phase: Finalize
    gate_type: static_check
    invocation: import
    check_module: gate_checks.done_checker_static
    check_function: run_finalize_selfcheck   # implement-ticket.js:1544, gate_checks/done_checker_static.py:950
    on_fail_status: [FINALIZE_INCOMPLETE]

gateless_phases:
  - phase: Investigate
    reason: >
      No hard pass/fail gate of its own in the live code. NEEDS_HUMAN_INPUT is gated in the Plan
      phase (see the `gates:` entry above and its note) — terminal-statuses.yaml's `phases:
      [Investigate]` attribution for that value is stale relative to current code; not corrected
      here (out of scope for this ticket — see Anti-Drift Notes).
  - phase: Document-Update
    reason: >
      doc-updater's `blocker` field only ever produces an 'ok'/'failed' *event*
      (implement-ticket.js:858-863) — it never calls writeMonitoring() and never returns early.
      Advisory only; the workflow always continues regardless of `blocker`.

excluded_outcomes:
  - value: EPIC_SCOPED
    phase: Scope
    reason: >
      A tier-routing exit (`tier === 'epic'`, implement-ticket.js:472-479), not a pass/fail gate
      condition — already fully covered by the phase_order/tier-applicability axis
      (workflows/implement-ticket.yaml). Recording it here would conflate the two axes, which
      investigation.md's Anti-Drift Hazards explicitly forbids.
```

Add a new `governs:` entry to `agent-orchestration/contract.yaml` (after the existing
`hook-surface-policy.yaml` entry, before `terminal-statuses.yaml`, matching the file's existing
one-entry-per-sibling-file convention seen at lines 12-33):

```yaml
  - path: gate-policy.yaml
    version_field: gate_policy_version
    description: Per-phase gate mechanism (agent_verdict/static_check/agent_result_field), pass condition, and resulting terminal-status mapping for implement-ticket.
```

`contract.yaml`'s own top-level `version: 1` (line 5) is **not** bumped — adding a new `governs:`
list entry is a non-breaking addition to `contract.yaml`'s own schema (it does not add a new
required top-level key; `_REQUIRED_CONTRACT_KEYS = ("version", "name")` at
`tools/agent_orchestration/loader.py:22` is unchanged), exactly mirroring how
`TCK-20260730-PROVIDER-HOOK-POLICY` added `hook-surface-policy.yaml` without bumping
`contract.yaml`'s version (confirmed: `contract.yaml`'s `version` field reads `1` today, and its
`governs:` list already has 7 entries including that file). `gate-policy.yaml`'s own
`gate_policy_version: 1` is a brand-new file's initial version, not a "bump" of anything.

**Do NOT touch:** `agent-orchestration/terminal-statuses.yaml` (a different, already-covered axis —
do not "fix" its stale `phases: [Investigate]` value as part of this ticket, even though Step 1
discovered it). Do not add a `check_module`/`check_function` key to the Verify-phase entry (see
inline note above — it is `agent_verdict`, not `static_check`, despite being evidence-backed by a
static script).

**Verify:** New structural test (Step 4) asserting `gate-policy.yaml` parses, has exactly 12 `gates`
entries's worth of phase coverage across `gates`/`gateless_phases`/`excluded_outcomes` (12 phases
total, matching `test_live_phase_order_has_the_expected_12_phases`'s list), and that `contract.yaml`'s
`version` is unchanged at `1`.

### Step 2 — Add `artifact_requirements` as a new optional field on `contract.yaml`

**Files:** `agent-orchestration/contract.yaml`

**Change:** `tools/gate_checks/done_checker_static.py:53` defines
`REQUIRED_ARTIFACT_FILES = ("plan.md", "investigation.md", "test_plan.md")`, and
`check_staging_artifacts_complete` (lines 148-158) branches on exactly one condition:
`if tier == "hotfix": return ("NA", ...)` (line 151-152) — every other `tier` value (including
`"epic"`, per `tools/ticket_field_values.py`'s `TIER_VALUES`) applies `REQUIRED_ARTIFACT_FILES`
identically. Note: in the live workflow, an `epic`-tier ticket never actually reaches this check —
`implement-ticket.js:472-479` returns `EPIC_SCOPED` at Scope, before Investigate/Plan/.../Verify
ever run — but the function's own branch condition (the only thing this axis's conformance test can
honestly diff against) is `tier == "hotfix"` vs. everything else, not a per-tier enumerated list.
Model the schema after that literal branch, not after CLAUDE.md's prose ("standard/epic only"),
since the two are consistent in outcome but the function's actual shape is a single exempt value:

```yaml
# Added directly below `description:` on contract.yaml, as a new OPTIONAL field — mirrors
# workflows/implement-ticket.yaml's existing optional `continuation_policy` field
# (tools/agent_orchestration/loader.py:118-133 validates it only when present, no version bump
# needed for its addition — same treatment here).
artifact_requirements:
  required_files: [plan.md, investigation.md, test_plan.md]
  exempt_tier: hotfix
```

**Do NOT touch:** `_REQUIRED_CONTRACT_KEYS` in `loader.py` (do not add `artifact_requirements` to
it — that would make it a *required* field, which the README's bump rule (`agent-orchestration/README.md:33-36`)
classifies as a breaking change requiring a version bump; this ticket's own investigation
explicitly concluded no bump is needed, so this field must stay optional-but-validated, exactly
like `continuation_policy`).

**Verify:** Step 4's new structural test asserts `contract.yaml`'s `artifact_requirements.required_files`
== `["plan.md", "investigation.md", "test_plan.md"]` and `contract.yaml["version"] == 1` unchanged.

### Step 3 — Extend `tools/agent_orchestration/loader.py`

**Files:** `tools/agent_orchestration/loader.py`

**Change:** Following the exact existing pattern for `hook-surface-policy.yaml` (lines 222-320,
which is the most structurally similar precedent — a new required sibling file with heterogeneous
per-entry keys) and `continuation_policy` (lines 100-133, the existing optional-field-on-an-existing-file
precedent):

1. Add new key tuples near the existing ones (loader.py:22-40):
   ```python
   _REQUIRED_GATE_POLICY_KEYS = ("gate_policy_version", "workflow_id", "gates")
   _REQUIRED_GATE_ENTRY_KEYS = ("phase", "gate_type", "on_fail_status")
   _GATE_TYPE_EXTRA_KEYS = {
       "agent_verdict": ("verdict_enum", "pass_value"),
       "static_check": ("invocation", "check_module", "check_function"),
       "agent_result_field": ("result_field", "pass_value"),
   }
   _REQUIRED_ARTIFACT_REQUIREMENTS_KEYS = ("required_files", "exempt_tier")
   ```
2. Add `gate_policy: dict[str, Any]` and `artifact_requirements: dict[str, Any] | None` fields to
   the `ContractBundle` frozen dataclass (loader.py:54-64) — `gate_policy` is never `None` (the file
   is always required, like `hook_surface_policy`); `artifact_requirements` defaults to `None` when
   absent from `contract.yaml` (like `continuation_policy`).
3. Add a validation step inside `_load_contract_yaml` (loader.py:88-93) that, if
   `data.get("artifact_requirements") is not None`, validates it's a mapping with
   `_REQUIRED_ARTIFACT_REQUIREMENTS_KEYS` present, `required_files` is a non-empty list of strings,
   and `exempt_tier` is a non-empty string. Do not raise if the field is absent entirely.
4. Add `_load_gate_policy_yaml(path: Path) -> dict[str, Any]`, mirroring
   `_load_hook_surface_policy_yaml`'s shape (loader.py:222-320): validates
   `_REQUIRED_GATE_POLICY_KEYS`, that `gate_policy_version` is an int, that `gates` is a non-empty
   list of mappings each carrying `_REQUIRED_GATE_ENTRY_KEYS` plus exactly the extra keys named by
   `_GATE_TYPE_EXTRA_KEYS[entry["gate_type"]]` (reject an unrecognized `gate_type` value), and that
   `on_fail_status` is a non-empty list of strings. Validate `gateless_phases`/`excluded_outcomes`
   loosely (non-empty list of mappings if present; not required keys, since their shape is simpler
   and less likely to need strict enforcement).
5. Wire into `load_contract()` (loader.py:323-360): add
   `gate_policy = _load_gate_policy_yaml(contract_dir / "gate-policy.yaml")` alongside the existing
   `hook_surface_policy` load, and pass `gate_policy=gate_policy,
   artifact_requirements=contract.get("artifact_requirements")` into the returned `ContractBundle`.

**Do NOT touch:** `_load_workflow_yaml`, `_load_role_yaml`, `_load_skills_yaml`, or any other
existing `_load_*` function — this is purely additive. Do not add `gate_policy`/`artifact_requirements`
to `_REQUIRED_CONTRACT_KEYS` (see Step 2's Do NOT touch note).

**Verify:** `tests/agent_orchestration/test_load_contract_succeeds_against_the_real_contract`-style
new assertion (Step 4) that `load_contract(repo_root).gate_policy["gates"]` has 12 phase-covering
entries and `.artifact_requirements["required_files"]` matches `REQUIRED_ARTIFACT_FILES`. Existing
`tests/agent_orchestration/test_contract_structure.py`, `test_bootstrap_vocabulary_equality.py`,
`test_skills_catalog.py`, `test_validator_errors.py`, `test_validator_no_network_calls.py` must all
stay green (no existing `_load_*` function signature changes).

### Step 4 — Extend `tests/agent_orchestration/test_contract_structure.py`

**Files:** `tests/agent_orchestration/test_contract_structure.py`

**Change:** Add 2-3 new test functions mirroring the existing
`test_new_contract_file_wired_into_readme_and_manifest` (lines 171-179) and
`test_load_contract_includes_hook_surface_policy` (lines 150-155) shapes:
- `test_new_gate_policy_file_wired_into_readme_and_manifest`: asserts `"gate-policy.yaml"` is in
  `contract.yaml`'s `governs:` paths with `version_field == "gate_policy_version"`, and that
  `"gate-policy.yaml"` / `"gate_policy_version"` both appear in `agent-orchestration/README.md`'s text
  (Step 7 adds that row).
- `test_load_contract_includes_gate_policy`: asserts `bundle.gate_policy["gate_policy_version"] == 1`
  and `len(bundle.gate_policy["gates"]) >= 12` (matches the phase count minus gateless phases, plus
  the 3 Test-phase sub-rows — exact count is whatever Step 1's real file ends up with; assert `>= 12`
  rather than a brittle exact count, since 3 phases have multiple gate rows).
- `test_contract_yaml_artifact_requirements_optional_field`: asserts
  `contract["artifact_requirements"]["required_files"] == ["plan.md", "investigation.md", "test_plan.md"]`
  and `contract["artifact_requirements"]["exempt_tier"] == "hotfix"`.
- `test_contract_and_workflow_versions_unchanged_by_this_ticket`: asserts
  `contract["version"] == 1` and `workflow["workflow_version"] == 2` (both already-asserted
  elsewhere individually — this test states the invariant explicitly as the version-bump-not-required
  guard test_plan.md calls for).

**Do NOT touch:** `_EXPECTED_TIER_MATRIX`, any existing test function body, or the 11-role-file
count assertion (line 81) — none of those are affected by this ticket.

**Verify:** `pytest tests/agent_orchestration/test_contract_structure.py -v` — all new + all
existing tests green.

### Step 5 — Write the gate_policy live extractor

**Files:** `tools/agent_orchestration_claude_adapter/gate_policy_extractor.py` (new)

**Change:** Mirrors `terminal_status_extractor.py`'s module docstring convention and
`_CONTEXT_WINDOW_CHARS`/window-based-context-matching technique (terminal_status_extractor.py:26-51)
exactly — no JS parser, `Path.read_text()` + regex only. Three extraction functions matching the 3
`gate_type` values, plus a phase-attribution pass and an aggregator:

- `extract_agent_verdict_gates(workflow_js_path)`: regex
  `verdict:\s*\{\s*type:\s*'string',\s*enum:\s*\[([^\]]+)\]\s*\}` for the enum block, paired with
  the nearest following `if\s*\(\w+\.verdict\s*!==\s*'(\w+)'\)` (pass_value) and the nearest
  following `writeMonitoring\(...\)` call(s) within the existing `_CONTEXT_WINDOW_CHARS`-shaped
  window — reuse that constant from `terminal_status_extractor.py`, import it rather than
  redefining. 4 call sites exist (Review, Architecture-Verify, Security-Review, done-checker/Verify)
  — the extractor must not assume a fixed count of 3 (investigation.md's own count was 3; this plan's
  fresh re-read found 4, including done-checker's `READY_TO_CLOSE`/`BLOCKED` enum at
  implement-ticket.js:1405 — cite this correction explicitly in the module docstring).
- `extract_static_check_gates(workflow_js_path)`: two sub-patterns —
  (a) `invocation: import` — regex `from (tag_registry|gate_checks\.\w+) import (\w+)`, paired with
  the nearest following `writeMonitoring\('([A-Z_]+)'\)` in the same window (reuse
  `_MESSAGE_CONTEXT_RE`-style context capture for FINALIZE_INCOMPLETE's 2 call sites, matching
  `run_finalize_selfcheck`'s existing 2-call-site shape already handled by
  `extract_all_terminal_statuses`);
  (b) `invocation: cli` — regex `python3 tools/gate_checks/(\w+)\.py` mapped through a small, fixed,
  documented constant dict (currently `{"doc_staleness_check": "check_doc_staleness"}`) — a CLI
  invocation line does not name its own function the way an `import` line does, so this one mapping
  is a fixed constant per the same "fixed, documented constant, not scraped" precedent
  `terminal_status_extractor.py:43-51` already establishes for `_VERDICT_DERIVED_STATUSES`.
- `extract_agent_result_field_gates(workflow_js_path)`: a fixed, documented constant list (2 known
  entries: Scope's `conflicts` field / `ticketInfo.conflicts.length > 0` and Test's `passed` field /
  `!testResult.passed`) — these are structural truthiness checks on agent-schema fields, not single
  regex-extractable literals, so (matching the verdict-derived precedent) this is a small constant,
  with a companion `count_agent_result_field_call_sites` sanity-check function (mirrors
  `count_verdict_derived_call_sites`) that greps for `ticketInfo.conflicts.length > 0` and
  `!testResult.passed` literally and asserts both are still found, so a future refactor that removes
  either line is caught as a signal to re-review the constant.
- `extract_gate_policy(workflow_js_path)`: aggregates all three, then attaches `phase` by finding
  the nearest preceding `phase\('([A-Za-z-]+)'\)` call's text offset for each extracted gate's own
  match offset (reuses the same phase-marker literals `extract_meta_phases` already scans for in
  `tools/gate_checks/workflow_meta_conformance.py` — import and reuse its phase-name list rather
  than re-deriving it) — this derives phase attribution from real text position, which is what
  correctly assigns `NEEDS_HUMAN_INPUT`/`plan_has_unresolved_questions_heading` to `Plan` (not
  `Investigate`, unlike `terminal-statuses.yaml`'s stale copy) automatically, without a hardcoded
  phases list.

**Do NOT touch:** `terminal_status_extractor.py` itself — import `_CONTEXT_WINDOW_CHARS`/reuse its
pattern, do not duplicate or modify its regexes.

**Verify:** New unit tests in Step 8 exercise every function above directly against the real
`.claude/workflows/implement-ticket.js`.

### Step 6 — Write the artifact_requirements live extractor

**Files:** `tools/agent_orchestration_claude_adapter/artifact_requirements_extractor.py` (new)

**Change:** Deliberately does **not** follow the JS-text-regex pattern (there is nothing to scan —
`done_checker_static.py` is Python, imported directly, matching investigation.md's own conclusion
that "importing is more robust... already the pattern
`tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py` uses for its
contract-side load"). One function:

```python
def extract_live_artifact_requirements(repo_root: Path) -> dict:
    """Reads tools/gate_checks/done_checker_static.py's REQUIRED_ARTIFACT_FILES constant
    (line 53) and its `tier == "hotfix"` branch (check_staging_artifacts_complete, lines 148-158)
    directly via import — there is no JS text to regex-scan for this axis, unlike gate_policy."""
```
Imports `tools.gate_checks.done_checker_static.REQUIRED_ARTIFACT_FILES` and returns
`{"required_files": list(REQUIRED_ARTIFACT_FILES), "exempt_tier": "hotfix"}` — the `"hotfix"`
string is a documented, hand-verified constant reflecting the function's own literal
`if tier == "hotfix"` branch (line 151), not scraped by regex (there is exactly one branch, so a
regex would be no more robust than stating the constant directly, and the import above already
gives a live, always-fresh read of the file list itself, which is the part that actually changes).

**Do NOT touch:** `tools/gate_checks/done_checker_static.py` — read-only import, no edits. Do not
build a parallel contract-side "artifact_requirements_loader.py" — the contract side is already
returned directly by `load_contract(repo_root).artifact_requirements` (Step 3); adding a second
wrapper file here would be unnecessary indirection for an axis this simple (deliberate asymmetry
vs. `terminal_status_extractor.py`/`terminal_status_loader.py`'s file pair — note this explicitly
in the module docstring so it doesn't read as an oversight).

**Verify:** Step 8's new test imports this function directly and diffs its output against
`load_contract(repo_root).artifact_requirements`.

### Step 7 — Doc updates

**Files:** `agent-orchestration/README.md`, `docs/architecture/agent_orchestration_contract.md`

**Change:**
- `README.md`'s Layout table (lines 14-23): add a row after the `hook-surface-policy.yaml` row:
  `| \`gate-policy.yaml\` | Per-phase gate mechanism, pass condition, and resulting terminal-status
  mapping for \`implement-ticket\`. |`. Also add one sentence to the "Bootstrap vocabulary"/versioning
  section noting `artifact_requirements` is a new optional field on `contract.yaml` itself (not a
  new sibling file), mirroring how `continuation_policy` is already described in the Versioning
  scheme section (lines 38-44).
- `docs/architecture/agent_orchestration_contract.md`'s Conformance Mechanism section (currently
  `**Status: Proposed-pending-implementation-evidence**`, line 125, with a Revisit Trigger noting
  "revisited once the first provider adapter conformance test is actually written" and a Trade-offs
  bullet at lines 209-214/226-229 calling Conformance Mechanism's evidence "thin"): update the status
  line to reflect that all 4 named axes (phases, terminal statuses, gate policy, artifact
  requirements) now have conformance tests — e.g. `**Status: Implemented — all 4 named axes
  (phase_order, terminal_status, gate_policy, artifact_requirements) have conformance tests as of
  TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER (2 axes) and TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST
  (2 axes).**`. Do not remove the Trade-offs bullet's historical framing — append, don't rewrite.

**Do NOT touch:** any other ADR section (Source Ownership, Versioning scheme decisions,
Execution Identity) — none of those are affected by this ticket.

**Verify:** `make knowledge-index-update` after these doc edits (per CLAUDE.md's After Work rule —
docs/ files were modified).

### Step 8 — New Claude-adapter conformance tests

**Files:** `tests/agent_orchestration_claude_adapter/test_gate_policy_conformance.py` (new),
`tests/agent_orchestration_claude_adapter/test_artifact_requirements_conformance.py` (new)

**Change:** Mirror `test_terminal_status_conformance.py`'s exact structure (imports
`is_approved`/`load_divergences` from `divergence_log`, `_REPO_ROOT`/`_WORKFLOW_JS_PATH`/
`_DIVERGENCE_LOG_PATH` module constants). Implements test_plan.md's tests #1, #2, #3, #7 (gate
policy) and #4, #5 (artifact requirements):

- `test_gate_policy_conformance_full_match_both_directions`: diffs
  `extract_gate_policy(_WORKFLOW_JS_PATH)` against `load_contract(_REPO_ROOT).gate_policy["gates"]`
  as a set of `(phase, gate_type, tuple(sorted(on_fail_status)))` triples (order-independent, same
  reasoning as the terminal_status test); any mismatch checked against
  `is_approved(divergences, axis="gate_policy", value=<phase>)` before hard-failing.
- `test_gate_policy_extractor_covers_all_12_phases_or_explicitly_excludes_a_gateless_phase`:
  asserts every one of the 12 live phases (reuse `extract_meta_phases`'s output as ground truth for
  the phase name list) appears in either `gate_policy["gates"]`'s phase set,
  `gate_policy["gateless_phases"]`'s phase set, or (for Scope specifically, given EPIC_SCOPED)
  `gate_policy["excluded_outcomes"]`'s phase set — no phase silently missing from all three.
- `test_gate_policy_deliberately_introduced_mismatch_fails_without_approval`: builds an in-memory
  copy of the loaded `gate_policy` dict with Review's `pass_value` changed to a wrong string, calls
  the same diff logic as test #1 against this mutated copy, asserts it fails without a
  divergence-log entry and passes once a `tmp_path`-copied `intentional-divergences.md` gains a
  `## gate_policy:Review` / `Status: RATIFIED` section — never mutates the real committed
  `agent-orchestration/intentional-divergences.md` (matches `test_claude_containment.py`'s
  containment discipline).
- `test_gate_policy_does_not_duplicate_static_check_internal_logic`: asserts every `gates` entry's
  keys are a subset of `_REQUIRED_GATE_ENTRY_KEYS + _GATE_TYPE_EXTRA_KEYS[entry["gate_type"]]` (from
  Step 3) — i.e. structurally impossible for a `done_checker_static.py`-shaped per-condition
  breakdown to have snuck in, since no such key vocabulary exists in the schema at all.
- `test_artifact_requirements_conformance_full_match`: diffs
  `extract_live_artifact_requirements(_REPO_ROOT)` against
  `load_contract(_REPO_ROOT).artifact_requirements` field-for-field; mismatch checked against
  `is_approved(divergences, axis="artifact_requirements", value="required_files")` before
  hard-failing.
- `test_artifact_requirements_deliberately_introduced_mismatch_fails_without_approval`: same shape
  as the gate_policy mismatch test, applied to a mutated `required_files` list missing
  `investigation.md`.

**Do NOT touch:** `test_phase_order_conformance.py`, `test_terminal_status_conformance.py`, or
either of their backing extractor/loader modules.

**Verify:**
```
pytest tests/agent_orchestration_claude_adapter/test_gate_policy_conformance.py \
       tests/agent_orchestration_claude_adapter/test_artifact_requirements_conformance.py -v
```
plus the full existing suite in that directory to confirm no regression:
```
pytest tests/agent_orchestration_claude_adapter/ -v
```

### Step 9 — Extend `build_agents_md` to render the 2 new axes

**Files:** `tools/agent_orchestration_codex_adapter/generator.py`

**Change:** `build_agents_md` (lines 40-51, read in full) currently builds a flat `lines` list and
appends `## Roles`/`## Skills` sections as list comprehensions. Insert, after the `## Roles` bullets
and before `## Skills` (or after `## Skills`, either position is fine — pick one and keep it
consistent with a new test's fixed expectation):

```python
lines += ['', '## Gate Policy', '']
for g in b.gate_policy['gates']:
    if g['gate_type'] == 'agent_verdict':
        detail = f"pass_value={g['pass_value']}"
    elif g['gate_type'] == 'static_check':
        detail = f"{g['check_module']}.{g['check_function']}"
    else:
        detail = f"{g['result_field']}=={g['pass_value']}"
    lines += [f"- {g['phase']} ({g['gate_type']}): {detail} -> on_fail: {', '.join(g['on_fail_status'])}"]
lines += ['', '## Artifact Requirements', '']
if b.artifact_requirements:
    ar = b.artifact_requirements
    lines += [f"- Required for all tiers except `{ar['exempt_tier']}`: {', '.join(ar['required_files'])}"]
```

`b.gate_policy` is always present (Step 3 makes it a required load); `b.artifact_requirements` may
be `None` in principle (optional field) so guard with `if b.artifact_requirements:` even though
Step 2 always populates it in practice.

**Do NOT touch:** `build_codex_skill_md`, `render_codex_guidance`, `_assert_write_allowed`, or the
existing `## Roles`/`## Workflow Continuation`/`## Skills` rendering — purely additive lines.

**Verify:** Step 11's regenerated `AGENTS.md` contains both new sections; existing
`tests/agent_orchestration_codex_adapter/test_agents_md_generation.py` (which reads the real
committed `AGENTS.md` directly, not a tmp-rendered copy — confirmed by reading that test file)
stays green.

### Step 10 — Regenerate and commit the real `AGENTS.md`

**Files:** `AGENTS.md` (repo root)

**Change:** Run `render_codex_guidance(repo_root, repo_root)` (no `allow_outside_contract` flag
needed for `AGENTS.md` itself — `generator.py`'s `_assert_write_allowed` (line 16-21) already
special-cases `target == root / 'AGENTS.md'` as always-allowed) to regenerate the committed
`AGENTS.md` with the new Gate Policy / Artifact Requirements sections from Step 9. This file is
read directly (not tmp-rendered) by 3 existing tests
(`test_agents_md_generation.py`'s 3 test functions) — it must be regenerated and committed as a
real repo change, not left stale, or those tests silently keep passing against pre-ticket content
while Step 12's new test (below) is the only one that would notice the gap.

**Do NOT touch:** `.agents/skills/*/SKILL.md` companion files — `render_codex_guidance` regenerates
those too as a side effect, but no *content* change is expected there from this ticket; if the
diff shows unrelated skill-file churn, investigate before committing (should be none, since no
`skills.yaml` change is part of this ticket).

**Verify:** `pytest tests/agent_orchestration_codex_adapter/test_agents_md_generation.py -v`.

### Step 11 — New Codex-adapter conformance test (AC #4)

**Files:** `tests/agent_orchestration_codex_adapter/test_gate_policy_artifact_requirements_conformance.py` (new)

**Change:** Implements test_plan.md's test #6, path (a) — feasible per investigation.md's own
conclusion, not the config.toml-redirect fallback:
- `test_agents_md_gate_policy_section_matches_contract`: reads the real committed root
  `AGENTS.md` (mirroring `test_agents_md_generation.py`'s own direct-read convention — confirmed by
  reading that file, it does `(ROOT / "AGENTS.md").read_text()` directly, no tmp_path rendering),
  asserts a `## Gate Policy` heading exists, and that every `bundle.gate_policy["gates"]` phase name
  appears at least once in the section body.
- `test_agents_md_artifact_requirements_section_matches_contract`: same shape, asserts
  `## Artifact Requirements` heading exists and `bundle.artifact_requirements["exempt_tier"]` and
  every filename in `required_files` appear in the section body.
- `test_codex_config_toml_confirmed_not_a_target`: a `test_no_production_hook_enabled.py`-style
  negative assertion that `.codex/config.toml` contains none of the new axes' vocabulary
  (`"gate_policy"`, `"artifact_requirements"`, any phase name) — a structural guard proving this
  ticket's own tests never accidentally started treating `config.toml` as a diffable source (per
  investigation.md's confirmed-inert finding and this ticket's own Out of Scope).

**Do NOT touch:** any existing `tests/agent_orchestration_codex_adapter/*.py` file.

**Verify:**
```
pytest tests/agent_orchestration_codex_adapter/ -v
```

### Step 12 — Parity ledger entry

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Add one new entry. Highest existing `INFRA-*` id as of this reading is `INFRA-407`
(confirmed via `grep -oE "id: INFRA-[0-9]+" docs/parity_ledger/infrastructure.yaml | sort -n |
tail`); re-derive the actual next-available id at Implement time via
`tools/gate_checks/parity_updater_static.py::next_available_id("infrastructure.yaml", ...)` since
other tickets may land first — do not hardcode `INFRA-408` if it's no longer next. Entry shape,
matching sibling agent-orchestration entries (e.g. `INFRA-316`):

```yaml
- id: INFRA-<next>
  text: "gate_policy and artifact_requirements conformance: .claude/ provider translation of implement-ticket's per-phase gate mechanism and per-tier staging-artifact requirement must not silently diverge from agent-orchestration/gate-policy.yaml and contract.yaml's artifact_requirements field."
  status: verified
  priority: P2
  v2_evidence: "tools/agent_orchestration_claude_adapter/gate_policy_extractor.py, tools/agent_orchestration_claude_adapter/artifact_requirements_extractor.py diff live .claude/workflows/implement-ticket.js and tools/gate_checks/done_checker_static.py against agent-orchestration/{gate-policy.yaml,contract.yaml}"
  test_path: "tests/agent_orchestration_claude_adapter/test_gate_policy_conformance.py,tests/agent_orchestration_claude_adapter/test_artifact_requirements_conformance.py,tests/agent_orchestration_codex_adapter/test_gate_policy_artifact_requirements_conformance.py"
  divergence_note: null
  support_boundary: "Agent-orchestration/monitoring-pipeline tooling only — no simulation behavior is involved."
```

**Do NOT touch:** any other `infrastructure.yaml` entry, or any other parity ledger file — this
subsystem has never carried a P0 entry (confirmed via investigation.md), and this ticket does not
change that.

**Verify:** `python3 tools/parity_ledger_scan.py` (or equivalent existing validator) confirms the
new entry parses against `docs/parity_ledger/schema.json`.

## Scope Guards

- Do not rebuild or duplicate the `phase_order`/`terminal_status` axes — `test_phase_order_conformance.py`
  and `test_terminal_status_conformance.py` and their backing extractor/loader modules are untouched.
- Do not "fix" `agent-orchestration/terminal-statuses.yaml`'s stale `NEEDS_HUMAN_INPUT` `phases:
  [Investigate]` value as part of this ticket, even though Step 1 discovered it during this plan's
  own fact-verification pass — that is the terminal_status axis's own file, out of scope here.
  Flag as a candidate follow-up hotfix ticket instead.
- Do not treat `.codex/config.toml` as a diffable source anywhere in this ticket's new tests (Step
  11's negative-assertion test guards this explicitly).
- Do not re-derive `done_checker_static.py`'s ~13 named DoD sub-conditions into
  `gate-policy.yaml` — the Verify-phase entry stays a single `agent_verdict` row, informationally
  noting `run_static_precheck` as evidence, never as a `check_module`/`check_function` pair (Step
  1's inline note is explicit about this).
- Do not add `gate_policy`/`artifact_requirements` to `_REQUIRED_CONTRACT_KEYS` in `loader.py` — both
  must stay structured so no version bump is triggered (`gate-policy.yaml` as a brand-new file with
  its own fresh `gate_policy_version: 1`; `artifact_requirements` as an optional field mirroring
  `continuation_policy`).
- Do not bump `contract.yaml`'s `version` or `workflows/implement-ticket.yaml`'s `workflow_version`
  anywhere in this ticket.
- Do not mutate the real committed `agent-orchestration/intentional-divergences.md` or
  `agent-orchestration/rendered/claude-adapter.yaml` in any new test — mismatch-fixture tests operate
  on `tmp_path`/in-memory copies only.
- Do not touch `docs/guidelines/intentional_divergences.md` (the separate mechanics-bible log) —
  only `agent-orchestration/intentional-divergences.md` is in scope, and only as a read target for
  the real file, never a write target outside `tmp_path`.
- Do not widen scope into `src/` simulation code, `docs/mechanics/`, or `docs/engine/` — none of
  those are implicated (confirmed in investigation.md's Mechanics/Engine Constraints section).

## Dependency Map

- Step 1 and Step 2 are independent of each other (different fields on/near `contract.yaml`) but
  both must land before Step 3 (loader.py reads both).
- Step 3 must land before Step 4 (structural tests import the new loader fields) and before Step 5/6
  (extractors are tested against `load_contract()`'s new output in Step 8).
- Step 5 and Step 6 are independent of each other and of Step 4; both must land before Step 8.
- Step 7 (docs) can happen any time after Step 1/2 land; independent of Steps 3-6/8.
- Step 9 depends on Step 3 (reads `bundle.gate_policy`/`bundle.artifact_requirements`).
- Step 10 depends on Step 9 (regenerates using the extended generator).
- Step 11 depends on Step 10 (reads the regenerated, committed `AGENTS.md`).
- Step 12 (parity ledger) can happen any time after Steps 1-11 are functionally complete — it
  documents the finished state, not a prerequisite for it.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Gate-policy axis test extracts per-phase/per-role gate conditions from implement-ticket.js and asserts match against agent-orchestration/'s per-phase gate representation, adding that representation as a prerequisite | Steps 1, 3, 5, 8 | `test_gate_policy_conformance_full_match_both_directions`, `test_gate_policy_extractor_covers_all_12_phases_or_explicitly_excludes_a_gateless_phase` |
| Artifact-requirements axis test extracts required-artifact set per tier and asserts match against a corresponding agent-orchestration/ field | Steps 2, 3, 6, 8 | `test_artifact_requirements_conformance_full_match` |
| Test suite includes at least one deliberately-introduced-mismatch fixture per new axis | Step 8 | `test_gate_policy_deliberately_introduced_mismatch_fails_without_approval`, `test_artifact_requirements_deliberately_introduced_mismatch_fails_without_approval` |
| Codex-side equivalent test compares AGENTS.md against the same contract data (feasible path chosen over the config.toml-redirect fallback) | Steps 9, 10, 11 | `test_agents_md_gate_policy_section_matches_contract`, `test_agents_md_artifact_requirements_section_matches_contract`, `test_codex_config_toml_confirmed_not_a_target` |

## Anti-Drift Notes

- **`done_checker_static.py` re-derivation risk (highest risk this ticket faces).** The Verify-phase
  `gate_policy` entry must stay a single `agent_verdict` row (`verdict_enum: [READY_TO_CLOSE,
  BLOCKED]`, `pass_value: READY_TO_CLOSE`, `on_fail_status: [DOD_BLOCKED]`) — never expand into a
  per-DoD-condition list. `test_gate_policy_does_not_duplicate_static_check_internal_logic` (Step 8)
  is a structural guard against this, but the real discipline is in Step 1's file content itself;
  review it carefully before committing.
- **`NEEDS_HUMAN_INPUT`'s real phase is Plan, not Investigate.** Confirmed by direct line citation
  (`phase('Plan')` at implement-ticket.js:618, the gate check at :654-679, `phase('Review')` at
  :686) against `terminal-statuses.yaml`'s existing (stale) `phases: [Investigate]` at lines 48-50.
  This plan's `gate_policy` schema is independently derived from live text position (Step 5's
  `extract_gate_policy`), so it gets this right without copying the stale value — but do not let an
  implementer "helpfully" copy `terminal-statuses.yaml`'s phase list as a shortcut when authoring
  Step 1's YAML by hand; it must come from the live-code citations in Step 1 as written here.
- **Security-Review and Verify's gates are `agent_verdict` with a *fixed* `on_fail_status`, not
  verdict-passthrough.** Both collapse a 2-value non-pass verdict space (`NEEDS_CHANGES`/`BLOCKED`
  for Security-Review; the Verify agent's own `BLOCKED` for done-checker) into one fixed status
  (`SECURITY_BLOCKED`, `DOD_BLOCKED` respectively) — structurally distinguishable from
  Review/Architecture-Verify (where `on_fail_status` literally equals `verdict_enum` minus
  `pass_value`) because it does not. Get this distinction right in Step 1's YAML and Step 5's
  extractor — do not assume all `agent_verdict` gates are verdict-passthrough by analogy to Review.
- **`doc_staleness_check` is invoked as a CLI script, not an import line — the one exception to the
  `from gate_checks.X import Y` pattern.** `implement-ticket.js:892` calls
  `python3 tools/gate_checks/doc_staleness_check.py ...` directly; Step 5's extractor needs a
  separate `invocation: cli` regex path plus a fixed function-name lookup for this one case, not a
  blind generalization of the `from ... import ...` regex.
- **`tag_registry` is not under the `gate_checks.` package** — it is `tools/tag_registry.py`,
  imported as bare `tag_registry`, not `gate_checks.tag_registry`. Step 1's YAML and Step 5's
  extractor must both record `check_module: tag_registry` exactly, not `gate_checks.tag_registry`.
- **`artifact_requirements`'s `exempt_tier` is a single string (`"hotfix"`), not a two-list
  `applies_to_tiers`/`exempt_tiers` shape** — `done_checker_static.py`'s own
  `check_staging_artifacts_complete` has exactly one branch condition (`tier == "hotfix"`), and an
  `epic`-tier ticket never actually reaches this check live (it exits at Scope's `EPIC_SCOPED`
  return, implement-ticket.js:472-479) — modeling the schema as a per-tier enumerated list would
  assert something about `epic` this ticket has no live evidence for. Keep the schema honestly
  matching the one real branch.
- **Containment discipline for mismatch fixtures.** Both new mismatch tests (gate_policy,
  artifact_requirements) must mutate an in-memory dict or a `tmp_path` copy of
  `intentional-divergences.md` — never the real committed
  `agent-orchestration/intentional-divergences.md`. Reuse `test_claude_containment.py`'s existing
  zero-diff pattern rather than writing a new one.

## Deviations (recorded at Implement time)

Step 4's own instruction ("empirically verify the context-window size... don't assume the same
window size works without checking against the real file") was followed literally, and the check
itself forced 4 concrete departures from Step 5's exact wording below. Each is evidence-driven, not
a shortcut — the corrected design was verified against the real
`.claude/workflows/implement-ticket.js` before being finalized, and the resulting extractor
produces a byte-for-byte match against Step 1's hand-authored `gate-policy.yaml` (zero divergence
entries needed, confirmed by `test_gate_policy_conformance_full_match_both_directions`).

1. **`_CONTEXT_WINDOW_CHARS` (400) is imported for citation only, never used as an operative
   window.** Measured real distances: enum-block -> guarding if-check spans 1273-3416 chars (large
   agent-prompt text sits in between each schema block and its own `if` guard); if-check ->
   `writeMonitoring(...)` call spans up to 421 chars; static-check import/CLI line ->
   `writeMonitoring('LITERAL')` spans up to 2935 chars (doc-staleness). All of these exceed 400 by
   a wide margin — reusing it verbatim would have silently failed to pair the run_finalize_selfcheck
   gap this step specifically asked to check, and several other gates besides. Three different,
   non-arbitrary pairing strategies were used instead (positional pairing for enum<->if-check, a
   wider 600-char window for if-check<->writeMonitoring, and a structural next-gate-defining-line
   bound for import/CLI<->writeMonitoring) — see `gate_policy_extractor.py`'s module docstring for
   the full, cited rationale.
2. **Phase attribution uses the nearest preceding `pushEvent('<Phase>', ...)` call's literal
   argument, not the nearest preceding `phase('<Phase>')` block marker Step 5 specified.** Direct
   evidence against the literal spec: the doc-staleness gate's `pushEvent`/`writeMonitoring` calls
   sit textually *after* `phase('Document-Update')` but *before* `phase('Architecture-Verify')` —
   a nearest-preceding-`phase()`-marker design would misattribute this gate to Document-Update,
   contradicting both its own inline `pushEvent('Implement', ...)` call and Step 1's own
   `gate_policy: Implement` YAML entry. The `pushEvent`-literal anchor resolves this correctly (and
   also correctly resolves NEEDS_HUMAN_INPUT to Plan, not Investigate) because every gate's failure
   branch emits its own `pushEvent('<Phase>', ...)` call immediately before its `writeMonitoring`
   call, in every one of the 13 gate/status call sites checked.
3. **`extract_static_check_gates` excludes a documented set of "known non-static_check" literal
   status values from its candidate search**, not just a next-import-line structural bound. Direct
   evidence: Scope's phase text has 3 independent literal `writeMonitoring` call sites
   (CONFLICTS_DETECTED, TAGS_NOT_REGISTERED, EPIC_SCOPED) with no import-line boundary between
   them — a plain "nearest literal call in the bounded window" search wrongly paired the
   `tag_registry` import with the closer-but-unrelated CONFLICTS_DETECTED instead of its real
   pairing, TAGS_NOT_REGISTERED (confirmed by running the extractor against the real file before
   finalizing this design). Fixed by excluding literal values already known to belong to
   agent_result_field/agent_verdict gates (plus EPIC_SCOPED/DONE) from static_check's own candidate
   search — see `_static_check_exclusion_values` in `gate_policy_extractor.py`.
4. **`tools/agent_orchestration/generator.py` (not named in Step 3's Files list) gained one new
   block writing `gate-policy.yaml`.** Required to keep the pre-existing
   `test_generated_output_round_trips_through_load_contract` test green (it round-trips
   `generate()`'s output back through `load_contract()`, which now requires `gate-policy.yaml` to
   be present) — the same treatment `hook-surface-policy.yaml` already received in this same
   generator when it was added by TCK-20260730-PROVIDER-HOOK-POLICY.
5. **Module docstrings in `gate_policy_extractor.py` avoid the literal substring
   `"implement-ticket.js"`**, citing line numbers and "the source file" instead. Required by the
   pre-existing `tests/agent_orchestration_claude_adapter/test_no_forbidden_calls_against_implement_ticket_js.py::test_no_forbidden_filename_substring_in_any_string_constant_in_the_file`
   architecture guard, which scans every string constant (including docstrings) in
   `tools/agent_orchestration_claude_adapter/*.py` for that exact substring.
6. **Regenerating `AGENTS.md` (Step 10) incidentally touched 4 unrelated `.agents/skills/*/SKILL.md`
   companion files** (pre-existing staleness: their source `.claude/skills/*/SKILL.md` files
   already referenced the newer `agent-orchestration/data/YYYY-Www/...` monitoring-shard paths, but
   the generated companions had never been regenerated since). These 4 files were reverted
   (`git checkout --`) before landing this ticket — out of scope here, since no `skills.yaml`
   change is part of this ticket, exactly as Step 10's own "if the diff shows unrelated skill-file
   churn, investigate before committing" instruction anticipated. Flagged as a candidate follow-up
   hotfix ticket, not fixed here.

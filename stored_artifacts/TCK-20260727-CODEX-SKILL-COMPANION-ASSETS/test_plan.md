---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260727-CODEX-SKILL-COMPANION-ASSETS
artifact_type: test_plan
tags: [ai, workflows, process-improvement]
---

# Test Plan — TCK-20260727-CODEX-SKILL-COMPANION-ASSETS

## Regression Surface

All existing tests below must keep passing, unmodified in intent, after the generator/loader
extension. Grouped by package (this subsystem has no arena-combat surface — agent-infrastructure
tooling only, confirmed in investigation.md's Mechanics/Engine Constraints).

**`tests/agent_orchestration/` (loader/contract validation — unit):**
- `test_skills_catalog.py::test_skills_yaml_validates_and_has_stable_ids` — ids stay unique,
  identifier-safe, traceable to `.claude/skills/*/SKILL.md`.
- `test_skills_catalog.py::test_skills_yaml_does_not_duplicate_role_fields` — the new
  `companion_assets` field must not collide with `_ROLE_ONLY_FIELDS`; confirm it doesn't (it isn't
  role-shaped) but this test is the structural guard if a future edit ever muddies the two schemas.
- `test_validator_errors.py` (all 3 cases) — missing-required-field and non-mapping-root error
  paths for `contract.yaml`/role YAML must still raise `ContractValidationError` with path+field in
  the message; must not regress when `_load_skills_yaml` gains new logic.
- `test_bootstrap_vocabulary_equality.py`, `test_contract_structure.py`,
  `test_validator_no_network_calls.py` — unrelated axes (vocabulary bootstrap, contract structure,
  AST no-network guard); must stay green as a sign the loader change was additive, not structural.

**`tests/agent_orchestration_codex_adapter/` (generator — unit/integration):**
- `test_generator_traceability.py` (all 4 cases) — frontmatter traceability,
  byte-identical-body-for-frontmatter-having-sources (`brainstorming`, `test-driven-development`),
  byte-identical-full-content-for-frontmatter-less-sources (`create-tickets`, `implement-epic`,
  `implement-ticket`, `simq-audit`), and the 16-entry-not-expanded guard. These directly exercise
  two of the four companion-asset-bearing skills' SKILL.md bodies — must stay byte-identical.
- `test_generator_write_guard.py` (all 4 cases) — external-target refusal without flag,
  external-target allowed with flag, `.claude/`/`.codex/` refusal, and the pre-write path-traversal
  guard (`test_rejects_path_traversal_skill_id_before_writing`, which asserts **nothing** is written
  if any single target fails the guard — the two-pass guard-then-write structure this ticket's
  extension must preserve).
- `test_containment_append_only_monitoring.py`, `test_requires_valid_contract.py`,
  `test_no_production_hook_enabled.py` — unrelated axes (monitoring append-only proof, contract
  validity requirement, no-production-hook guard); confirm generator extension doesn't disturb
  them.
- `test_legacy_skills_containment.py` (all 3 cases) — legacy 18-dir archive hash-check, live
  catalog exclusion, archive-outside-discovery-path. Confirms the companion-asset regeneration
  doesn't touch or reintroduce archived legacy content.

**Scoped `.agents/skills/` regeneration output** — after regenerating, confirm the following
files remain byte-for-byte unchanged from before (i.e., no accidental content drift in the 12
skills with zero companion assets, and no accidental SKILL.md body change in the 4 affected
skills beyond what `test_generator_traceability.py` already checks): re-run
`test_generator_traceability.py` and `test_generator_write_guard.py` against the regenerated tree
as the final regression gate.

## New Tests Required

1. **Test name**: `test_companion_assets_field_defaults_to_empty_list_when_omitted`
   **Category**: unit
   **Verifies**: `load_contract()` on a `skills.yaml` copy with a skill entry lacking
   `companion_assets` does not raise, and the loaded entry exposes `companion_assets == []` (per
   AC: "present, defaults to `[]` if omitted").
   **Location**: `tests/agent_orchestration/test_skills_catalog.py` (new function) or a new
   `tests/agent_orchestration/test_companion_assets_field.py`, following the `_copy_contract_to`
   tmp-path-mutation pattern already used in `test_validator_errors.py`.

2. **Test name**: `test_companion_assets_field_rejects_non_list_value`
   **Category**: unit
   **Verifies**: a `companion_assets` value that is a bare string (not a list) or a non-string-list
   (e.g. a list containing an int) raises `ContractValidationError` naming the file path and field
   — mirrors the existing `FixtureValidationError`/`ContractValidationError` message-shape
   convention (path + field name in the exception string).
   **Location**: same file as test 1.

3. **Test name**: `test_companion_assets_populated_for_the_four_confirmed_skills`
   **Category**: unit
   **Verifies**: `load_contract(ROOT).skills["skills"]` entries for `architecture`,
   `brainstorming`, `test-driven-development`, `api-design-principles` each have a
   `companion_assets` list matching the exact file sets confirmed in investigation.md's Current
   Behavior §4 (5 files; 2 files + 5 `scripts/*` files; 1 file; 5 files across 3 subdirs
   respectively) — a real-data regression test, not just a schema-shape test.
   **Location**: `tests/agent_orchestration/test_skills_catalog.py`.

4. **Test name**: `test_companion_assets_empty_for_the_twelve_unaffected_skills`
   **Category**: unit
   **Verifies**: every other skill id's `companion_assets` is `[]` — an explicit negative
   assertion so a future stray addition to one of the 12 unaffected skills is caught, matching
   this ticket's audit finding that exactly 4 of 16 need entries.
   **Location**: same file as test 3.

5. **Test name**: `test_render_codex_guidance_copies_declared_companion_assets_byte_identical`
   **Category**: integration
   **Verifies**: running `render_codex_guidance(ROOT, tmp_path, allow_outside_contract=True)`
   produces, for each of the 4 affected skills, every file listed in the AC's exact path
   enumeration (`.agents/skills/architecture/{context-discovery.md,...}`,
   `.agents/skills/brainstorming/{spec-document-reviewer-prompt.md,visual-companion.md,scripts/*}`,
   `.agents/skills/test-driven-development/testing-anti-patterns.md`,
   `.agents/skills/api-design-principles/{assets,references,resources}/*`), each byte-identical to
   its `.claude/skills/` source (`sha256` or direct `read_bytes()` comparison), with nested
   directory structure (`scripts/`, `assets/`, `references/`, `resources/`) preserved.
   **Location**: `tests/agent_orchestration_codex_adapter/test_generator_traceability.py` (new
   function, alongside the existing byte-identity tests) or a new
   `test_generator_companion_assets.py` if the file grows too large.

6. **Test name**: `test_companion_asset_copy_respects_write_guard_and_refuses_traversal`
   **Category**: architecture guard
   **Verifies**: (a) a `companion_assets` entry containing a path-traversal string (e.g.
   `../../../etc/passwd`) raises `CodexAdapterWriteGuardError` and writes nothing — mirroring
   `test_generator_write_guard.py::test_rejects_path_traversal_skill_id_before_writing`'s
   nothing-written assertion, but for the companion-asset field instead of the `id` field
   (investigation.md Risks #2, currently uncovered by any existing test); (b) companion-asset
   targets still refuse `.claude/`/`.codex/` destinations, confirming the existing
   `_assert_write_allowed` guard generalizes without modification.
   **Location**: `tests/agent_orchestration_codex_adapter/test_generator_write_guard.py` (new
   functions).

7. **Test name**: `test_missing_companion_asset_source_raises_named_error`
   **Category**: unit
   **Verifies**: if `skills.yaml` declares a `companion_assets` path that does not exist under
   `.claude/skills/<id>/` at generation time, `render_codex_guidance()` raises a named,
   deterministic error (whichever error type Plan/Implement chooses per investigation.md Risks
   #3) rather than a raw `FileNotFoundError` or a partial write.
   **Location**: `tests/agent_orchestration_codex_adapter/test_generator_traceability.py` or
   `test_generator_write_guard.py`, whichever the implementer's error-type choice fits better.

8. **Test name**: `test_reference_resolution_all_sixteen_skills` **(explicitly required by AC)**
   **Category**: integration / regression
   **Verifies**: for every one of the 16 generated `.agents/skills/<id>/SKILL.md` bodies, every
   relative file reference found (markdown-link syntax and `@filename` mentions, matching the
   `@testing-anti-patterns.md` style) resolves to a real file inside that skill's own generated
   `.agents/skills/<id>/` directory. Per investigation.md Current Behavior §6, the detection
   pattern **must** be scoped to avoid two known false-positive classes already found in live
   data: (a) `backend-testing/SKILL.md`'s two pre-existing dead cross-skill links
   (`../api-design/SKILL.md`, `../authentication/SKILL.md`) — these point outside the skill's own
   directory and reference non-existent skill ids; the test must not fail the whole suite over
   read-only, out-of-scope content — and (b) `@example.com`/`@pytest.fixture`/`@pytest.mark.*`
   style non-file `@mentions` in `backend-testing`, `python-performance-optimization`, and
   `python-testing-patterns` — the regex must be scoped to a known companion-file extension set
   (`.md`, `.py`, `.js`, `.cjs`, `.sh`, `.html`, or whatever set Plan settles on) and/or exclude
   matches inside fenced code blocks.
   **AC requirement**: "fails on the pre-fix tree... confirm it fails against a git-stashed
   pre-change `.agents/skills/` before the generator change lands) and passes after the fix, for
   all 16 skills" — write this test first, confirm it fails against the current (pre-fix)
   `.agents/skills/` (where `test-driven-development/SKILL.md`'s `@testing-anti-patterns.md`
   reference has no matching file), then implement the fix, then confirm it passes.
   **Location**: new file, `tests/agent_orchestration_codex_adapter/test_reference_resolution.py`.

## Scoped Pytest Commands

```
pytest tests/agent_orchestration/ tests/agent_orchestration_codex_adapter/ -v
```

If iterating narrowly on the loader-only change first:
```
pytest tests/agent_orchestration/ -v
```

If iterating narrowly on the generator-only change:
```
pytest tests/agent_orchestration_codex_adapter/ -v
```

Never run the full suite (`pytest tests/`) for this ticket — scope stays within these two
directories per this ticket's Related Code Areas; no `src/` simulation test is affected.

## Anti-Drift Test Guards

- `test_skills_yaml_does_not_duplicate_role_fields` (existing, unmodified) already guards against
  `companion_assets` accidentally bleeding role-shaped semantics into `skills.yaml` — no new test
  needed for that axis, but confirm it still passes after the field is added.
- Test 4 (`test_companion_assets_empty_for_the_twelve_unaffected_skills`) is the explicit
  anti-scope-creep guard for the audit step: if a future edit accidentally adds companion assets
  to a skill that shouldn't have them (or the audit was wrong), this test catches it immediately
  rather than silently shipping unreviewed content into the Codex package.
- Test 8's false-positive scoping (backend-testing's dead cross-skill links, `@example.com`/
  `@pytest.fixture` non-file mentions) is itself an anti-drift guard in reverse: it prevents the
  new reference-resolution test from becoming an accidental pressure to hand-edit
  `.claude/skills/backend-testing/SKILL.md` (explicitly Out of Scope, read-only source) just to
  make an overly-broad test pass.
- Re-running `test_legacy_skills_containment.py`'s hash checks after regeneration guards against
  the companion-asset copy path accidentally resurrecting or touching the 18-directory legacy
  archive under `docs/archive/legacy_agents_skills_20260722/`.
- `test_generator_write_guard.py::test_never_targets_dot_claude_or_dot_codex` (existing) plus new
  test 6 together guard against the companion-asset copy path ever writing into `.claude/` or
  `.codex/` — the two failure modes (wrong provider-tree target, and traversal-out-of-package
  target) are covered by separate assertions so a fix for one can't silently regress the other.

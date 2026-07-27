---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260727-CODEX-SKILL-COMPANION-ASSETS
phase: done
date: 2026-07-27
tags: [ai, workflows, process-improvement]
---

# TCK-20260727-CODEX-SKILL-COMPANION-ASSETS

## Title
Codex skill-generation pipeline drops referenced companion asset files (entry-point parity only, not package parity)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`tools/agent_orchestration_codex_adapter/generator.py::render_codex_guidance()` regenerates
`.agents/skills/<id>/SKILL.md` from `.claude/skills/<id>/SKILL.md`'s body (byte-identical body,
per `build_codex_skill_md()`) for all 16 `skills.yaml` entries, but copies nothing else out of the
source `.claude/skills/<id>/` directory. Several of those directories contain companion asset
files — reference docs, a prompt template, a `scripts/` subdirectory, `assets/`/`references/`/
`resources/` subdirectories — that the copied SKILL.md bodies themselves reference by relative
path or `@filename` mention. Confirmed by direct comparison (2026-07-27):

- `architecture`: 5 companion files (`context-discovery.md`, `examples.md`, `pattern-selection.md`,
  `patterns-reference.md`, `trade-off-analysis.md`) exist in `.claude/skills/architecture/` and are
  referenced by filename in the SKILL.md body table (source lines 16-20, carried verbatim into the
  generated `.agents/skills/architecture/SKILL.md`). None exist in `.agents/skills/architecture/`,
  which contains only `SKILL.md`.
- `brainstorming`: `spec-document-reviewer-prompt.md`, `visual-companion.md`, and a `scripts/`
  subdirectory (`server.cjs`, `start-server.sh`, `stop-server.sh`, `helper.js`,
  `frame-template.html`) exist in `.claude/skills/brainstorming/`. None copied to
  `.agents/skills/brainstorming/` (contains only `SKILL.md`).
- `test-driven-development`: `.claude/skills/test-driven-development/testing-anti-patterns.md`
  exists, and the generated `.agents/skills/test-driven-development/SKILL.md` literally instructs
  (line 359 of the generated file, carried from the source body): "read
  @testing-anti-patterns.md to avoid common pitfalls" — a broken reference in the shipped file
  today.
- `api-design-principles`: `.claude/skills/api-design-principles/` has `assets/`, `references/`,
  and `resources/` subdirectories; none copied to `.agents/skills/api-design-principles/` (contains
  only `SKILL.md`). Independently confirmed by Codex's own audit in
  `docs/plans/agent_infrastructure/provider_agnostic_orchestration/final_configuration_parity_verification_response_codex.md`.

The generated Codex skill catalog is entry-point-aligned (SKILL.md bodies match byte-for-byte,
per `tests/agent_orchestration_codex_adapter/test_generator_traceability.py`) but not
skill-package-aligned. A real Codex session following its own generated skill instructions today
would hit missing-file references for at least these 4 of the 16 generated skills.

Both Claude's and Codex's independent audits
(`docs/plans/agent_infrastructure/provider_agnostic_orchestration/final_configuration_parity_verification_claude.md`
and `..._response_codex.md`) converged on the same fix, quoting Codex's own words: "model and
generate only approved companion assets, then add a reference-resolution test. This preserves the
provider-specific boundary while making generated Codex skills self-contained." — i.e. not a blind
copy of every file under every `.claude/skills/<id>/` directory (some Claude-only companion
content, e.g. Claude-Code-specific tooling, may be intentionally excluded), but a deliberate,
contract-declared allowlist of companion assets per skill.

## Scope
- Extend `agent-orchestration/skills.yaml`'s per-skill entry schema (and
  `tools/agent_orchestration/loader.py`'s `_REQUIRED_SKILL_ENTRY_KEYS`/validation, currently
  exactly `id`, `description`, `workflows`, `roles` with no file-list field) with an explicit,
  optional list field naming the approved companion assets to carry alongside `SKILL.md` for that
  skill (relative paths from the skill's own directory, so `scripts/server.cjs` and
  `assets/foo.png`-style nested paths are representable).
- Populate that new field for the 4 confirmed-affected skills (`architecture`, `brainstorming`,
  `test-driven-development`, `api-design-principles`) with the exact companion files/directories
  enumerated in Request Summary above.
- Audit the remaining 12 `skills.yaml` entries' `.claude/skills/<id>/` directories for the same gap
  (companion files referenced by the SKILL.md body but not present in the source directory listing
  used above) and populate the field for any additional skill found to need it.
- Extend `tools/agent_orchestration_codex_adapter/generator.py::render_codex_guidance()` (and
  `build_codex_skill_md()`'s caller loop, generator.py:56-57) to copy each skill's declared
  companion assets from `.claude/skills/<id>/<relative-path>` into
  `.agents/skills/<id>/<relative-path>`, preserving relative directory structure (e.g.
  brainstorming's `scripts/` subdirectory), through the existing `_assert_write_allowed` write-guard
  path (generator.py:12-17) so the containment boundary (`.agents/skills/` only, refuse
  `.claude/`/`.codex/`) still applies to the new copy targets.
- Add a reference-resolution test under `tests/agent_orchestration_codex_adapter/` that parses
  every generated `.agents/skills/<id>/SKILL.md` body for relative file references (markdown-link
  syntax and `@filename` mentions, matching the `@testing-anti-patterns.md` style already present
  in the TDD skill body) and asserts each resolved reference exists as a real file in the generated
  `.agents/skills/<id>/` package.
- Regenerate `.agents/skills/` (via the extended generator) so the 4 confirmed-affected skills'
  companion assets actually land in the committed tree, and confirm via the new test that no other
  skill among the 16 has an unresolved reference.
- Read `docs/architecture/agent_orchestration_contract.md`'s "Contract Representation and Format"
  decision section (source lines 55-79) and either add a short note there describing this schema
  extension, or record in this ticket's Assumptions/Open Questions why no doc update was needed.

## Out of Scope
- Does not modify any file under `.claude/skills/` — that tree is the read-only source of truth for
  both the SKILL.md body content and the companion assets being copied from it.
- Does not enable any live Codex hook, pilot, or production wiring — this ticket only changes what
  static files land in `.agents/skills/` at generation time.
- Does not address the two documented-only gaps already recorded in
  `agent-orchestration/intentional-divergences.md`'s "Known Configuration Gaps (Not
  Conformance-Test Axes)" section (hook-surface policy, execution-identity population) — those are
  separate, deliberately not-yet-ticketed items and this ticket must not fold them in.
- Does not promote or migrate the 6 legacy `.agents/skills/` directories with no `.claude/skills/`
  counterpart (`clean-code`, `codebase-search`, `code-review`, `create-skill`,
  `receiving-code-review`, `requesting-code-review`) — that promotion review was explicitly deferred
  by `docs/ai/agents_dir_disposition.md` to its own future ticket and is unrelated to this
  companion-asset gap on the 16 contract-tracked skills.
- Does not attempt a blanket "copy every file in every `.claude/skills/<id>/` directory" rule — the
  allowlist must be deliberate per skill, per the converged Claude/Codex recommendation.

## Acceptance Criteria
- [x] `agent-orchestration/skills.yaml` has a new field (e.g. `companion_assets: []`) on every skill
  entry, and `tools/agent_orchestration/loader.py` validates it (present, defaults to `[]` if
  omitted, rejects non-list/non-string-list values) without breaking existing skill-entry
  validation tests.
- [x] `architecture`, `brainstorming`, `test-driven-development`, and `api-design-principles` each
  declare the exact companion assets enumerated in Request Summary (5 files; 2 files + 5-file
  `scripts/` dir; 1 file; 3 subdirectories respectively — exact file lists to be confirmed against
  the live directory listing at implementation time).
- [x] Running the extended `render_codex_guidance()` against the current repo produces
  `.agents/skills/architecture/{context-discovery.md,examples.md,pattern-selection.md,patterns-reference.md,trade-off-analysis.md}`,
  `.agents/skills/brainstorming/{spec-document-reviewer-prompt.md,visual-companion.md,scripts/*}`,
  `.agents/skills/test-driven-development/testing-anti-patterns.md`, and
  `.agents/skills/api-design-principles/{assets,references,resources}/*`, each byte-identical to
  its `.claude/skills/` source.
- [x] A new reference-resolution test fails on the pre-fix tree (i.e. it is a real regression test —
  confirm it fails against a git-stashed pre-change `.agents/skills/` before the generator change
  lands) and passes after the fix, for all 16 skills.
- [x] The existing `tests/agent_orchestration_codex_adapter/test_generator_traceability.py` and
  `test_generator_write_guard.py` still pass unmodified in intent (SKILL.md body byte-identity and
  the `.claude/`/`.codex/` write-guard refusal both still hold) after the generator extension.
- [x] `.codex/` and `.claude/` remain untouched by the regeneration run (write-guard still refuses
  those targets for the new companion-asset copy path, not just the existing SKILL.md/AGENTS.md
  path).

## Related Tickets
- `TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE` (DONE) — built
  `tools/agent_orchestration_codex_adapter/generator.py`, the file this ticket extends. Its
  investigation.md Risk #2 explicitly deferred "full parity" between SKILL.md body-only generation
  and complete companion-asset parity as an open design decision — this ticket resolves that
  deferral.
- `TCK-20260721-ORCHESTRATION-CONTRACT-CORE` (DONE) — owns `agent-orchestration/skills.yaml`'s
  schema and `tools/agent_orchestration/loader.py`'s validation, both of which this ticket extends
  with the new `companion_assets` field.
- `TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER` (DONE) — sibling Claude-side adapter; not modified by
  this ticket, referenced only as the "not a template" precedent already noted in the
  fixture-capture ticket's investigation.

## Related Docs
- `docs/architecture/agent_orchestration_contract.md` — "Contract Representation and Format"
  decision section (source lines 55-79); may need a short note about the schema extension.
- `agent-orchestration/intentional-divergences.md` — "Known Configuration Gaps (Not
  Conformance-Test Axes)" section, for context on what is/isn't already tracked as a known gap
  (this companion-asset gap is not currently listed there and should not be conflated with the two
  gaps that are).
- `docs/plans/agent_infrastructure/provider_agnostic_orchestration/final_configuration_parity_verification_claude.md`
  and `..._response_codex.md` — the two independent audits that identified this gap and converged
  on the recommended fix approach.
- `docs/ai/agents_dir_disposition.md` — governs the legacy `.agents/skills/` containment and the
  6-directory promotion deferral referenced in Out of Scope.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE/investigation.md`,
  `plan.md`, `test_plan.md` — original generator design rationale; Risk #2 ("SKILL.md body-content
  source is undefined... deferring full parity to a later ticket") is the direct precursor to this
  ticket's scope.

## Related Code Areas
- `tools/agent_orchestration_codex_adapter/generator.py` (`render_codex_guidance()`,
  `build_codex_skill_md()`, `_assert_write_allowed()`)
- `tools/agent_orchestration_codex_adapter/errors.py`
- `tools/agent_orchestration/loader.py` (`_REQUIRED_SKILL_ENTRY_KEYS`, skill-entry validation)
- `agent-orchestration/skills.yaml`
- `tests/agent_orchestration_codex_adapter/` (`test_generator_traceability.py`,
  `test_generator_write_guard.py`, and the new reference-resolution test)
- `.claude/skills/architecture/`, `.claude/skills/brainstorming/`,
  `.claude/skills/test-driven-development/`, `.claude/skills/api-design-principles/` (read-only
  sources)
- `.agents/skills/` (generated output, regenerated by this ticket)

## Assumptions / Open Questions
- Assumes `companion_assets` as the new field name; Plan may pick a different name if a stronger
  precedent is found, but the shape (list of relative-path strings per skill entry) should hold.
- Assumes the audit of the remaining 12 skills (beyond the 4 confirmed) will find zero or a small
  number of additional cases — if it instead finds most of the 16 need entries, that is still within
  scope (Scope's audit step already accounts for this), it just changes implementation size, not
  ticket boundary.
- `layer: ai` is used per this repo's registered definition ("Claude agent/orchestration tooling")
  — matches every sibling ticket in this same provider-agnostic-orchestration initiative.
- Assumes no `docs/mechanics/`, `docs/engine/`, or `docs/parity_ledger/` entry is affected (verified
  during scoping: this subsystem is agent-infrastructure tooling, not simulation mechanics,
  consistent with every sibling ticket in the batch — `docs/parity_ledger/infrastructure.yaml` has
  no `orchestrat|codex|skills\.yaml|SKILL\.md` hits outside unrelated `CampaignOrchestrator`/
  `LabOrchestrator` simulation-domain entries).

## Implementation Notes
Implemented all 9 plan steps.

1. **`agent-orchestration/skills.yaml`** — added `companion_assets: []` to all 16 entries in a
   single edit (Steps 1+3 combined, see plan.md Deviations #1), populated with the exact curated
   allowlist for `api-design-principles` (5 files), `architecture` (5 files), `brainstorming`
   (2 files + 5-file `scripts/` dir), `test-driven-development` (1 file); all other 12 entries kept
   `companion_assets: []`. Added a one-line header-comment note describing the field.
2. **`tools/agent_orchestration/loader.py::_load_skills_yaml`** — added a separate validation block
   after the existing required-key loop: defaults `companion_assets` to `[]` when absent, raises
   `ContractValidationError` for a non-list value or a non-string list element, and backfills the
   normalized `[]` into the entry dict so downstream callers never need their own `.get(..., [])`.
   Did not add it to `_REQUIRED_SKILL_ENTRY_KEYS` (would break the "defaults to `[]`" requirement).
3. **`tools/agent_orchestration_codex_adapter/errors.py`** — added
   `CodexAdapterMissingCompanionAssetError(Exception): pass`, matching the file's existing bare-class
   convention.
4. **`tools/agent_orchestration_codex_adapter/generator.py::render_codex_guidance()`** — builds a
   parallel `(source, dest)` list for every skill's `companion_assets` entries alongside the
   existing `SKILL.md` path loop, appends every companion `dest` to the same upfront `paths` list
   that already runs through `_assert_write_allowed` (single guard pass, no second pass), then runs
   an upfront `source.is_file()` existence check for every companion pair (raising
   `CodexAdapterMissingCompanionAssetError` if any is missing) before any file is written. Only
   after both checks succeed does it write: unchanged `AGENTS.md` + `SKILL.md` write sequence, then
   a new loop writing companion-asset bytes via `read_bytes()`/`write_bytes()` (binary-safe),
   creating parent directories for nested paths (e.g. `scripts/`).
5. **Tests added**:
   - `tests/agent_orchestration/test_skills_catalog.py` — 4 new tests covering
     defaults-to-`[]`-when-omitted, rejects-non-list, rejects-non-string-element, and the exact
     populated/empty split across all 16 skills.
   - `tests/agent_orchestration_codex_adapter/test_generator_write_guard.py` — 2 new traversal
     tests (see plan.md Deviations #2 for why the invocation shape differs from the plan's literal
     mirror instruction: `../../../etc/passwd` escaping `.agents/skills/`, and a payload resolving
     into `.claude/`), both asserting `CodexAdapterWriteGuardError` with nothing written.
   - `tests/agent_orchestration_codex_adapter/test_generator_traceability.py` — 2 new tests: byte-
     identical companion-asset copy across all 4 skills, and missing-companion-source raises the
     new named error with nothing written.
   - `tests/agent_orchestration_codex_adapter/test_reference_resolution.py` (new file) — one
     reference-resolution test across all 16 generated `SKILL.md` bodies (see plan.md Deviations #3
     for why the detection pattern stayed at exactly markdown-link + `@filename`, no third
     backtick-span pattern). Verified by hand: fails against a `git stash` of the source changes
     (`test-driven-development: unresolved reference 'testing-anti-patterns.md'`), passes after.
6. **Regeneration** — ran `render_codex_guidance(Path('.'), Path('.'))` directly (established
   one-off invocation pattern from `TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE`'s plan.md).
   Verified: all 17 new companion files across the 4 skills are byte-identical (SHA-256) to their
   `.claude/skills/` sources; the other 12 skills' `.agents/skills/<id>/` directories are unchanged
   (`SKILL.md` only); `AGENTS.md` and all `SKILL.md` bodies are unchanged (no `git status` diff);
   `.claude/` and `.codex/` untouched.
7. **`docs/architecture/agent_orchestration_contract.md`** — added a 3-sentence note under
   "Contract Representation and Format" documenting the `companion_assets` field, its validation,
   its consumer, and that it is a curated allowlist not a blind copy. Ran
   `make knowledge-index-update` afterward per project convention.

## Test Summary
`.venv/bin/python3 -m pytest tests/agent_orchestration/ tests/agent_orchestration_codex_adapter/ -q`
→ 50 passed, 1 failed. The 1 failure
(`test_contract_structure.py::test_contract_yaml_has_versioning_field_and_documented_scheme`) is
pre-existing and unrelated: it reads
`staging_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/plan.md`, which no longer exists there
because that unrelated, already-closed ticket's staging artifacts were moved to `stored_artifacts/`
on close per project convention — confirmed failing identically before any of this ticket's edits
were applied (via `git stash`). Not touched, out of scope for this ticket.

Also independently ran `tests/agent_orchestration_codex_adapter/test_legacy_skills_containment.py`,
`test_no_production_hook_enabled.py`, and `test_containment_append_only_monitoring.py` (9 tests,
all passed) to confirm the legacy-skills quarantine and hook-safety gates are undisturbed by the
regeneration.

## Files Changed
- `agent-orchestration/skills.yaml`
- `tools/agent_orchestration/loader.py`
- `tools/agent_orchestration_codex_adapter/errors.py`
- `tools/agent_orchestration_codex_adapter/generator.py`
- `tests/agent_orchestration/test_skills_catalog.py`
- `tests/agent_orchestration_codex_adapter/test_generator_write_guard.py`
- `tests/agent_orchestration_codex_adapter/test_generator_traceability.py`
- `tests/agent_orchestration_codex_adapter/test_reference_resolution.py` (new)
- `docs/architecture/agent_orchestration_contract.md`
- `.agents/skills/architecture/{context-discovery.md,examples.md,pattern-selection.md,patterns-reference.md,trade-off-analysis.md}` (new, generated)
- `.agents/skills/brainstorming/{spec-document-reviewer-prompt.md,visual-companion.md,scripts/*}` (new, generated)
- `.agents/skills/test-driven-development/testing-anti-patterns.md` (new, generated)
- `.agents/skills/api-design-principles/{assets,references,resources}/*` (new, generated)

## Completion Summary
Extended the `agent-orchestration/skills.yaml` contract with an optional, additively-validated
`companion_assets` field and populated it with the curated 4-skill allowlist confirmed by
investigation (no 13th case among the other 12 skills). Extended
`render_codex_guidance()` to copy each skill's declared companion assets into `.agents/skills/<id>/`
through the same single upfront guard-then-write pass already used for `SKILL.md`/`AGENTS.md`, with
a new named error for a missing declared source. Added path-traversal, byte-identity,
missing-source, and one-directional reference-resolution regression coverage (the last one
independently verified to fail pre-fix and pass post-fix via `git stash`). Regenerated the real
`.agents/skills/` tree for the 4 affected skills — byte-identical to source, no other skill or
directory disturbed. All acceptance criteria satisfied; no `src/` runtime behavior changed (tooling
+ generated output + contract data only).

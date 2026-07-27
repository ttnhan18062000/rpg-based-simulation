---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260727-CODEX-SKILL-COMPANION-ASSETS
artifact_type: plan
tags: [ai, workflows, process-improvement]
---

# Implementation Plan — TCK-20260727-CODEX-SKILL-COMPANION-ASSETS

## Summary

Add a new optional `companion_assets: []` field to each `agent-orchestration/skills.yaml` skill
entry, validated additively (not via `_REQUIRED_SKILL_ENTRY_KEYS`) by
`tools/agent_orchestration/loader.py`. Populate it with a curated allowlist (per
investigation.md's falsification of the "textually referenced only" interpretation) for the 4
confirmed skills — `architecture`, `brainstorming`, `test-driven-development`,
`api-design-principles` — leave it `[]` for the other 12 (confirmed by investigation's full
16-skill audit; no 13th case exists). Extend
`tools/agent_orchestration_codex_adapter/generator.py::render_codex_guidance()` to copy each
skill's declared companion assets from `.claude/skills/<id>/<relative>` to
`.agents/skills/<id>/<relative>`, preserving nested structure, through the same upfront
guard-then-write two-pass ordering the existing SKILL.md/AGENTS.md paths already use — extending
`_assert_write_allowed` calls to cover every companion-asset path, including path-traversal
entries, before any file is written. Add a new `CodexAdapterMissingCompanionAssetError` (matching
the existing `CodexAdapterWriteGuardError`/`CodexAdapterMissingSkillSourceError` naming
convention in `errors.py`) for a declared-but-absent source file. Add a one-directional
reference-resolution test across all 16 generated skills, with the detection regex scoped to a
known companion-file extension allowlist and same-skill-relative-path resolution only (no
cross-skill `../` traversal), so it does not spuriously fail on `backend-testing`'s two
pre-existing dead cross-skill links or on `@example.com`/`@pytest.fixture`-style non-file
mentions. Regenerate `.agents/skills/` for the 4 affected skills only, and add a short note to
`docs/architecture/agent_orchestration_contract.md`'s "Contract Representation and Format"
section documenting the schema extension.

## Steps

### Step 1 — Add `companion_assets` field to `skills.yaml` schema (empty everywhere first)

**Files:** `agent-orchestration/skills.yaml`

**Change:** Add `companion_assets: []` to all 16 skill entries as a no-op baseline (every entry
gets the key, all empty at this step) so the schema shape lands before any content is populated
and before loader validation is written. This keeps this step reviewable in isolation: a pure
schema-shape diff with zero behavior content.

**Do NOT touch:** `id`, `description`, `workflows`, `roles` values on any entry. Do not touch
`agent-orchestration/contract.yaml`, `agent-orchestration/roles/*.yaml`, or
`agent-orchestration/workflows/*.yaml` — this field is skill-shaped, not role-shaped or
workflow-shaped (per investigation's Anti-Drift Hazards and
`test_skills_yaml_does_not_duplicate_role_fields`).

**Verify:** `test_companion_assets_field_defaults_to_empty_list_when_omitted` cannot yet exist
meaningfully against this step alone (it needs loader support — see Step 2), but confirm
`test_skills_yaml_validates_and_has_stable_ids` and `test_skills_yaml_does_not_duplicate_role_fields`
still pass unmodified against the edited file (no loader change yet, so the new key is simply
ignored by today's validator, per investigation.md §2).

### Step 2 — Extend `loader.py` to validate `companion_assets` additively

**Files:** `tools/agent_orchestration/loader.py`

**Change:** In `_load_skills_yaml` (currently `loader.py:113-127`), after the existing
`_require_keys(path, data, _REQUIRED_SKILL_ENTRY_KEYS)` / per-entry required-key loop, add a
**separate** block (do not add `companion_assets` to `_REQUIRED_SKILL_ENTRY_KEYS`) that, for each
skill entry:
1. Reads `entry.get("companion_assets", [])` — defaults to `[]` when the key is absent.
2. If the value is not a `list`, raises `ContractValidationError(f"{path}: skills[{idx}]
   'companion_assets' must be a list, got {type(...).__name__}")`.
3. If any element is not a `str`, raises `ContractValidationError(f"{path}: skills[{idx}]
   'companion_assets' must be a list of strings, got {type(elem).__name__} at index {j}")`.
4. Normalizes the entry in the returned `data` structure so `entry["companion_assets"]` is always
   present as a list (mutate the dict in place to backfill `[]` when absent, so downstream callers
   — Step 4's generator — never need their own `.get(..., [])` fallback).

Match the existing `ContractValidationError` message shape (file path + field name) used
throughout this function and `_load_workflow_yaml`/`_load_hook_events_yaml`.

**Do NOT touch:** `_REQUIRED_SKILL_ENTRY_KEYS` tuple (must stay exactly `("id", "description",
"workflows", "roles")` — adding `companion_assets` there would break the "defaults to `[]` when
omitted" AC, since `_require_keys` raises on absence). Do not touch `_load_contract_yaml`,
`_load_workflow_yaml`, `_load_role_yaml`, `_load_monitoring_schema_yaml`,
`_load_hook_events_yaml`, or `ContractBundle`'s dataclass shape.

**Verify:** New tests `test_companion_assets_field_defaults_to_empty_list_when_omitted` and
`test_companion_assets_field_rejects_non_list_value` (test_plan.md items 1-2), written in
`tests/agent_orchestration/test_skills_catalog.py` following the existing `_copy_contract_to`
tmp-path-mutation pattern from `test_validator_errors.py`. Also re-run
`test_validator_errors.py`, `test_bootstrap_vocabulary_equality.py`, `test_contract_structure.py`,
`test_validator_no_network_calls.py` to confirm no regression.

### Step 3 — Populate `companion_assets` for the 4 confirmed skills

**Files:** `agent-orchestration/skills.yaml`

**Change:** Replace the empty `companion_assets: []` placeholders from Step 1 with the exact
curated lists confirmed by investigation.md Current Behavior §4 (relative paths from each skill's
own `.claude/skills/<id>/` directory):

- `api-design-principles`: `[assets/api-design-checklist.md, assets/rest-api-template.py,
  references/graphql-schema-design.md, references/rest-best-practices.md,
  resources/implementation-playbook.md]`
- `architecture`: `[context-discovery.md, examples.md, pattern-selection.md,
  patterns-reference.md, trade-off-analysis.md]`
- `brainstorming`: `[spec-document-reviewer-prompt.md, visual-companion.md,
  scripts/frame-template.html, scripts/helper.js, scripts/server.cjs,
  scripts/start-server.sh, scripts/stop-server.sh]`
- `test-driven-development`: `[testing-anti-patterns.md]`

All other 12 entries keep `companion_assets: []` from Step 1 — this is the audit result, not a
placeholder pending further work (investigation confirmed exactly these 4, no 13th case).

**Do NOT touch:** Any file under `.claude/skills/` (read-only source of truth — this step only
lists paths, never copies or moves anything yet). Do not add entries for any of the 12
zero-companion skills.

**Verify:** New tests `test_companion_assets_populated_for_the_four_confirmed_skills` and
`test_companion_assets_empty_for_the_twelve_unaffected_skills` (test_plan.md items 3-4).

### Step 4 — Add `CodexAdapterMissingCompanionAssetError`

**Files:** `tools/agent_orchestration_codex_adapter/errors.py`

**Change:** Add a new exception class following the file's exact existing convention (bare
`class X(Exception): pass`, `CodexAdapter`-prefixed, `Error`-suffixed name):

```python
class CodexAdapterMissingCompanionAssetError(Exception):
    pass
```

Placed after `CodexAdapterMissingSkillSourceError` (mirrors that class's role: raised when a
declared source file is absent, but scoped to companion assets instead of `SKILL.md` itself).

**Do NOT touch:** `CodexAdapterWriteGuardError`, `CodexAdapterMissingSkillSourceError` — no
renaming, no merging the new case into an existing error type (investigation.md Risk #3
considered reuse and the file's own one-class-per-failure-mode convention favors a distinct type).

**Verify:** Exercised by Step 6's `test_missing_companion_asset_source_raises_named_error`
(test_plan.md item 7) — import succeeds and the class is raisable/catchable.

### Step 5 — Extend `_assert_write_allowed` usage and `render_codex_guidance()` to copy companion assets

**Files:** `tools/agent_orchestration_codex_adapter/generator.py`

**Change:** In `render_codex_guidance()` (`generator.py:44-58`):
1. Import `CodexAdapterMissingCompanionAssetError` from `.errors`.
2. While building the `paths` list (currently lines 50-53, one `SKILL.md` path per skill), also
   build a parallel list of `(source_path, dest_path)` tuples for every `companion_assets` entry
   on every skill: `source = repo_root/'.claude'/'skills'/s['id']/rel`, `dest =
   target/'.agents'/'skills'/s['id']/rel`, for each `rel` in `s.get('companion_assets', [])`
   (loader now guarantees this key is always present as a list per Step 2, but keep `.get(...,
   [])` defensively since `render_codex_guidance` may see contract data from tests that bypass the
   loader).
3. Append every `dest` path to the same upfront `paths` list that already gets guard-checked
   at `generator.py:54` (`for path in paths: _assert_write_allowed(...)`) — do **not** create a
   second guard pass. This preserves the "collect all paths, guard all paths, then write all
   paths" two-pass structure investigation.md's Anti-Drift Hazards require (no interleaved
   per-skill guard-then-write, so a mid-loop failure never leaves partial output).
4. Before any write happens, also validate every companion-asset `source_path.is_file()`; if not,
   raise `CodexAdapterMissingCompanionAssetError(f"{s['id']}: declared companion asset not found:
   {rel}")` — this check must happen in the same upfront pass as the guard checks (step 3 above),
   not lazily during the write loop, so a missing source fails before any file is written (same
   "no partial output" principle).
5. After the existing SKILL.md write loop (`generator.py:56-57`), add a second write loop over the
   companion-asset `(source, dest)` pairs: `dest.parent.mkdir(parents=True, exist_ok=True);
   dest.write_bytes(source.read_bytes())` — use `read_bytes`/`write_bytes` (not text) so binary
   companion files (none currently exist, but the field is declared as general file paths, not
   markdown-only) copy byte-identically without encoding risk.

**Do NOT touch:** `build_codex_skill_md()`, `build_agents_md()`, `_body()` — unrelated to
companion-asset copying. Do not change `_assert_write_allowed`'s own logic (investigation.md
confirmed it already generalizes to companion-asset targets with zero modification — a
`.agents/skills/<id>/<rel>` path already satisfies its existing `is_relative_to(root/'.agents'/
'skills')` check). Do not change the existing SKILL.md-path guard-then-write ordering or the
`AGENTS.md` write at lines 55.

**Verify:** New tests `test_render_codex_guidance_copies_declared_companion_assets_byte_identical`
(test_plan.md item 5), `test_companion_asset_copy_respects_write_guard_and_refuses_traversal`
(test_plan.md item 6), `test_missing_companion_asset_source_raises_named_error` (test_plan.md item
7). Also re-run `test_generator_traceability.py` (all 4 cases) and `test_generator_write_guard.py`
(all 4 cases) to confirm the existing SKILL.md-path behavior is unchanged.

### Step 6 — Add path-traversal test coverage for `companion_assets`

**Files:** `tests/agent_orchestration_codex_adapter/test_generator_write_guard.py`

**Change:** Add `test_companion_asset_copy_respects_write_guard_and_refuses_traversal` (test_plan.md
item 6): construct a temp contract copy where one skill's `companion_assets` contains a
traversal string (e.g. `../../../etc/passwd`) and assert `render_codex_guidance(...)` raises
`CodexAdapterWriteGuardError` with **nothing written** to the temp target directory (mirror
`test_rejects_path_traversal_skill_id_before_writing`'s existing nothing-written assertion
pattern exactly — walk the target tree and assert it's empty, or assert specific expected files
are absent). Also assert a companion-asset `dest` resolving into `.claude/` or `.codex/` (e.g. a
skill's `companion_assets` entry crafted as `../../.claude/skills/other/SKILL.md`-style relative
path that resolves outside `.agents/skills/`) is refused the same way.

**Do NOT touch:** The existing `test_rejects_path_traversal_skill_id_before_writing` test — add a
new function alongside it, do not modify its assertions or the `id`-traversal case it already
covers.

**Verify:** The new test itself is the verification (test_plan.md item 6); also confirms
`test_never_targets_dot_claude_or_dot_codex` (existing) still passes.

### Step 7 — Add reference-resolution test across all 16 skills

**Files:** `tests/agent_orchestration_codex_adapter/test_reference_resolution.py` (new file)

**Change:** Implement `test_reference_resolution_all_sixteen_skills` (test_plan.md item 8),
one-directional only (references found in the generated body must resolve; no inverse check):

1. Run `render_codex_guidance(ROOT, tmp_path, allow_outside_contract=True)` to produce a full
   16-skill `.agents/skills/` tree in a temp directory.
2. For each generated `<tmp>/.agents/skills/<id>/SKILL.md`, extract candidate file references
   using two patterns:
   - Markdown-link syntax `\[[^\]]*\]\(([^)]+)\)`, keeping only link targets that (a) do not start
     with `http://`/`https://`/`#` (skip external links and in-page anchors), and (b) do not
     traverse outside the current skill's own directory — i.e., **reject/skip any target
     containing `../`** (this is the explicit scoping decision that keeps `backend-testing`'s two
     pre-existing dead cross-skill links, `../api-design/SKILL.md` and `../authentication/SKILL.md`,
     out of scope for this test, per investigation.md Current Behavior §6 and the ticket's Out of
     Scope on not touching `.claude/skills/`). A same-skill reference like `context-discovery.md`
     or `scripts/server.cjs` has no `../` and is in scope.
   - `@filename` mentions matching `@([\w./-]+\.(?:md|py|js|cjs|sh|html))\b` — the extension
     allowlist is the explicit false-positive fix for `@example.com`, `@pytest.fixture`,
     `@pytest.mark.*`, `@domain.co.uk` (none of these end in one of the 6 listed extensions, so
     none match).
   - Exclude both patterns from matching inside fenced code blocks (text between ` ``` ` markers)
     — an additional guard against decorator/example noise inside code samples, applied by
     stripping fenced-code-block spans from the body text before running either regex.
3. For each surviving candidate reference on skill `<id>`, assert
   `(<tmp>/.agents/skills/<id>/<reference>).is_file()` is true. Collect all failures and report
   them together (not fail-fast on the first one) so a single test run shows every unresolved
   reference across all 16 skills at once.
4. Per the ticket's AC ("confirm it fails against a git-stashed pre-change `.agents/skills/`
   before the generator change lands"): this must be validated as a real regression test during
   implementation — run the test against the current (pre-Step-5) generator/`.agents/skills/`
   output first (where `test-driven-development/SKILL.md`'s `@testing-anti-patterns.md` reference
   has no matching file) and confirm it fails, then confirm it passes after Steps 1-6 land.

**Do NOT touch:** Any `.claude/skills/<id>/SKILL.md` body content, including
`backend-testing/SKILL.md`'s two dead cross-skill links — this test must observe and skip them via
the `../`-exclusion scoping rule, never "fix" them by editing the read-only source. Do not write an
inverse check ("every shipped companion file must be referenced by name") — investigation.md §5
proves this would incorrectly fail on `api-design-principles` (4 of 5 files unreferenced in body)
and `brainstorming` (5 of 7 files, the whole `scripts/` dir, unreferenced in body).

**Verify:** The test itself, run twice (pre-fix fail, post-fix pass) per the AC's explicit
requirement.

### Step 8 — Regenerate `.agents/skills/` for the 4 affected skills

**Files:** `.agents/skills/architecture/`, `.agents/skills/brainstorming/`,
`.agents/skills/test-driven-development/`, `.agents/skills/api-design-principles/` (generated
output, plus `.agents/AGENTS.md` if the skills catalog listing in `build_agents_md()` changes —
it should not, since that function only reads `id`/`description`, not `companion_assets`).

**Change:** Run the now-extended `render_codex_guidance(repo_root, repo_root)` (real target,
not a tmp path — same invocation pattern the generator's own regeneration entry point already
uses) so the actual committed `.agents/skills/` tree gains:
- `.agents/skills/architecture/{context-discovery.md,examples.md,pattern-selection.md,patterns-reference.md,trade-off-analysis.md}`
- `.agents/skills/brainstorming/{spec-document-reviewer-prompt.md,visual-companion.md,scripts/frame-template.html,scripts/helper.js,scripts/server.cjs,scripts/start-server.sh,scripts/stop-server.sh}`
- `.agents/skills/test-driven-development/testing-anti-patterns.md`
- `.agents/skills/api-design-principles/{assets,references,resources}/*` (5 files across 3
  subdirectories)

Confirm each copied file is byte-identical to its `.claude/skills/` source (`diff` or checksum
comparison) and confirm the other 12 skills' `.agents/skills/<id>/` directories are unchanged
(still `SKILL.md` only).

**Do NOT touch:** `.claude/` or `.codex/` (write-guard already refuses these — confirm the
regeneration run produces no diff under either tree). Do not touch the 6 legacy
`.agents/skills/` directories with no `.claude/skills/` counterpart (`clean-code`,
`codebase-search`, `code-review`, `create-skill`, `receiving-code-review`,
`requesting-code-review`) — out of scope per the ticket and `docs/ai/agents_dir_disposition.md`.

**Verify:** `test_render_codex_guidance_copies_declared_companion_assets_byte_identical` (Step 5),
`test_reference_resolution_all_sixteen_skills` (Step 7) passing against the real regenerated tree,
`test_generator_traceability.py` and `test_generator_write_guard.py` re-run clean against the
real tree (test_plan.md's "Scoped `.agents/skills/` regeneration output" final regression gate),
and `test_legacy_skills_containment.py` (all 3 cases) re-run to confirm the legacy 18-dir archive
and the 6 undecided legacy directories are undisturbed.

### Step 9 — Document the schema extension in the contract ADR

**Files:** `docs/architecture/agent_orchestration_contract.md`

**Change:** Add a short paragraph under the existing "Contract Representation and Format"
decision section (source lines 55-64) noting: `skills.yaml` entries gained an optional
`companion_assets: []` field (list of relative paths from the skill's own `.claude/skills/<id>/`
directory) as of TCK-20260727-CODEX-SKILL-COMPANION-ASSETS, validated additively by
`loader.py` (defaults to `[]`, not part of `_REQUIRED_SKILL_ENTRY_KEYS`), consumed by
`generator.py::render_codex_guidance()` to copy declared companion files into
`.agents/skills/<id>/` alongside the generated `SKILL.md`. Keep it to 3-5 sentences — this is a
documentation-completeness note, not a new ADR decision (the section's existing "YAML +
generated Python validation" decision already covers this; the note just names the field).

**Do NOT touch:** The section's "Status: Decided" line or any other ADR section (Source
Ownership, Versioning, etc.) — this is an additive note, not a re-litigation of the ADR.

**Verify:** No automated test covers doc prose; manual review that the note is present and
accurate is the verification for this step. Per project convention, since this modifies a file
under `docs/`, `make knowledge-index-update` must be run at Finalize.

## Scope Guards

- Never modify any file under `.claude/skills/` — read-only source of truth for both SKILL.md
  body content and companion asset content. All copying in Step 5/8 is one-directional,
  `.claude/` → `.agents/`.
- Never enable any live Codex hook, pilot, or production wiring — this ticket only changes what
  static files land in `.agents/skills/` at generation time. Do not touch
  `test_no_production_hook_enabled.py`'s guarded configuration.
- Never touch `agent-orchestration/intentional-divergences.md`'s "Known Configuration Gaps (Not
  Conformance-Test Axes)" section — hook-surface policy and execution-identity population stay
  out of scope, unrelated to this companion-asset gap.
- Never promote or migrate the 6 legacy `.agents/skills/` directories with no `.claude/skills/`
  counterpart (`clean-code`, `codebase-search`, `code-review`, `create-skill`,
  `receiving-code-review`, `requesting-code-review`) — deferred to a separate future ticket per
  `docs/ai/agents_dir_disposition.md`.
- Never implement a blanket "copy every file in every `.claude/skills/<id>/` directory" rule —
  `companion_assets` must stay a deliberate, curated per-skill allowlist (Step 3), not derived
  mechanically from directory listings or from SKILL.md's own reference syntax.
- Never make the reference-resolution test (Step 7) require the inverse condition ("every shipped
  companion file is referenced in the body") — falsified by real data for `api-design-principles`
  and `brainstorming`.
- Never let the reference-resolution test's detection regex or scoping rule create pressure to
  hand-edit `backend-testing/SKILL.md` (its two dead cross-skill links are explicitly excluded via
  the `../`-traversal scoping rule, not "fixed").
- Never add `companion_assets` to `loader.py`'s `_REQUIRED_SKILL_ENTRY_KEYS` tuple.
- Never interleave per-skill guard-then-write in `render_codex_guidance()` — preserve the
  existing two-pass "collect all paths, guard all paths, then write all paths" structure for both
  SKILL.md paths and the new companion-asset paths.
- Never touch `docs/mechanics/`, `docs/engine/`, or `docs/parity_ledger/` — confirmed by
  investigation as not applicable to this agent-infrastructure-tooling subsystem.

## Dependency Map

- Step 1 → Step 2 (loader validation needs the schema field to exist to validate against, though
  Step 2's test can also construct its own tmp-path fixture independently — Step 1 establishes the
  real `skills.yaml` shape).
- Step 2 → Step 3 (populate real content only after validation logic exists, so a malformed entry
  would be caught immediately).
- Step 3 → Step 5 (generator copy logic needs real `companion_assets` content to copy against in
  its integration tests) and → Step 8 (regeneration needs the populated field).
- Step 4 → Step 5 (generator references the new error class).
- Step 5 → Step 6 (traversal-guard test exercises the extended `render_codex_guidance`).
- Step 5 → Step 7 (reference-resolution test's "post-fix pass" run needs the copy logic to exist;
  the "pre-fix fail" half of the test is validated by running it before Step 5 lands, per Step 7's
  own instructions).
- Step 5, Step 6, Step 7 → Step 8 (regeneration is the real-tree application of the now-tested
  generator extension).
- Step 9 is independent of all other steps (pure documentation) and can be done at any point after
  Step 1-3 establish the final field name/shape, but is listed last since it describes the
  finished feature.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `skills.yaml` has new `companion_assets: []` field on every entry; `loader.py` validates (present, defaults `[]`, rejects non-list/non-string-list) without breaking existing tests | Steps 1, 2 | `test_companion_assets_field_defaults_to_empty_list_when_omitted`, `test_companion_assets_field_rejects_non_list_value`, plus unmodified `test_skills_yaml_validates_and_has_stable_ids`, `test_skills_yaml_does_not_duplicate_role_fields`, `test_validator_errors.py` |
| 4 confirmed skills declare exact companion assets enumerated in Request Summary | Step 3 | `test_companion_assets_populated_for_the_four_confirmed_skills`, `test_companion_assets_empty_for_the_twelve_unaffected_skills` |
| Extended `render_codex_guidance()` produces the exact byte-identical file set for the 4 skills | Steps 4, 5, 8 | `test_render_codex_guidance_copies_declared_companion_assets_byte_identical` |
| New reference-resolution test fails pre-fix, passes post-fix, for all 16 skills | Step 7 | `test_reference_resolution_all_sixteen_skills` (run both pre- and post-Step-5) |
| Existing `test_generator_traceability.py` and `test_generator_write_guard.py` still pass unmodified in intent | Steps 5, 6, 8 (verification) | `test_generator_traceability.py` (all 4 cases), `test_generator_write_guard.py` (all 4 cases) |
| `.codex/` and `.claude/` remain untouched by regeneration, including the new companion-asset copy path | Steps 5, 6, 8 | `test_never_targets_dot_claude_or_dot_codex` (existing), `test_companion_asset_copy_respects_write_guard_and_refuses_traversal` (new) |
| Audit remaining 12 skills for the same gap; populate field for any additional skill found | Step 3 (audit already completed during investigation — result: zero additional skills) | `test_companion_assets_empty_for_the_twelve_unaffected_skills` |
| Read `docs/architecture/agent_orchestration_contract.md`'s "Contract Representation and Format" section and add a note or record why not | Step 9 | Manual review (no automated doc test) |

**Responsible scope expansion beyond the ticket's literal AC text** — the following 4 hazards were
found during investigation, not stated in the ticket's original AC wording, and are addressed
because leaving them unhandled would either break unrelated out-of-scope content or leave a real
security/correctness gap uncovered by any existing test:

1. **Reference-resolution false positives** (`backend-testing`'s dead cross-skill links,
   `@example.com`/`@pytest.fixture`-style non-file mentions) — addressed by Step 7's explicit
   `../`-traversal exclusion and extension-allowlist regex scoping. Without this, the AC's own
   "passes after the fix, for all 16 skills" requirement would be unsatisfiable, since
   `backend-testing` would hard-fail regardless of any companion-asset fix.
2. **`companion_assets` path-traversal attack surface** — addressed by Step 5's inclusion of
   companion-asset destination paths in the existing upfront `_assert_write_allowed` pass, and
   Step 6's dedicated test. Without this, a malformed `companion_assets` entry could write outside
   `.agents/skills/<id>/` with no test ever catching it.
3. **Missing companion-asset source file at generation time** — addressed by Step 4's new
   `CodexAdapterMissingCompanionAssetError` and Step 5's upfront existence check. Without this, a
   typo'd path in `skills.yaml` would surface as a raw `FileNotFoundError` mid-write-loop
   (potentially after some files already written), violating the "guard before write" ordering
   principle the rest of the generator already follows.
4. **Contract doc note** — addressed by Step 9, directly requested by the ticket's own Scope text
   ("either add a short note there... or record... why not") — not a hazard so much as an
   explicit ticket instruction that the plan must not skip.

## Anti-Drift Notes

- The `_body()`/`build_codex_skill_md()` functions and SKILL.md byte-identity guarantees
  (`test_generator_traceability.py`) are completely unaffected by this ticket — companion-asset
  copying is additive, parallel logic, not a modification to how SKILL.md bodies are built.
- `companion_assets` is a curated allowlist, populated by direct comparison against
  investigation.md's Current Behavior §4 table — do not regenerate this list by grepping
  SKILL.md bodies for references at implementation time; that method is proven wrong by real data
  (see investigation.md §5: it would drop 4/5 of `api-design-principles`'s files and 5/7 of
  `brainstorming`'s files).
- The reference-resolution test (Step 7) and the companion-asset allowlist (Step 3) are
  deliberately decoupled mechanisms answering two different questions — "what ships" (Step 3,
  curated) vs. "do the generated bodies' own in-text references resolve" (Step 7, mechanical,
  one-directional). Do not conflate them or try to derive one from the other.
- `read_bytes()`/`write_bytes()` (not `read_text()`/`write_text()`) must be used for companion-
  asset copying in Step 5 to guarantee true byte-identity per the AC, even though all 8 currently
  known companion files happen to be text (`.md`, `.py`, `.js`, `.cjs`, `.sh`, `.html`) —
  `scripts/server.cjs` and `.py`/`.sh` files can carry meaningful line-ending/encoding nuances
  that a text-mode round-trip could silently normalize.
- Confirm `test_legacy_skills_containment.py`'s hash checks (all 3 cases) still pass after Step 8's
  regeneration, even though the archive lives under `docs/archive/`, outside `.agents/skills/` —
  investigation.md flags this as "should be confirmed not to disturb it... explicit at Verify
  time, not assumed."

## Deviations

1. **Steps 1 and 3 combined into one `skills.yaml` edit.** The plan asked for a two-pass edit
   (empty `companion_assets: []` everywhere first, then a second edit populating the 4 confirmed
   skills), reasoned as keeping each step reviewable in isolation as a separate diff. Since this
   entire ticket is implemented in a single uncommitted working session (no intermediate commit
   between Step 1 and Step 3), there is no actual separate reviewable artifact produced by doing
   the edit in two passes — the file on disk only ever reflects its final state at commit time.
   Implemented both steps as one direct edit carrying the final curated content, with the header
   comment update also folded in. No behavior or content difference from the plan's intended
   end-state.

2. **Step 6's traversal test could not literally reuse `test_rejects_path_traversal_skill_id_before_writing`'s
   `repo_root != target_repo_root` + `allow_outside_contract=True` invocation shape.** Investigation
   during implementation showed that existing test only passes because a malformed `id` value fails
   the separate `_ID.fullmatch()` format check *before* any path-resolution guard logic runs — it
   never actually exercises `_assert_write_allowed`'s resolve-based containment check in that
   two-different-roots configuration. A `companion_assets` relative-path entry is not constrained
   by `_ID` (only skill ids are), so the *only* way to make a `../`-payload actually resolve back
   into `root/.claude` or outside `root/.agents/skills` is to call `render_codex_guidance(source,
   source)` with a shared root — the same shape Step 8's real regeneration invocation uses. Wrote
   two tests using this corrected shape:
   `test_companion_asset_copy_respects_write_guard_and_refuses_traversal` (payload
   `../../../etc/passwd`, escapes `.agents/skills/` entirely, caught by the "must be under
   `root/.agents/skills`" branch) and `test_companion_asset_copy_refuses_traversal_into_dot_claude`
   (payload resolves into `root/.claude/...`, caught by the unconditional `.claude`/`.codex`
   branch). Both assert `CodexAdapterWriteGuardError` and nothing written — same guarantee the plan
   asked for, via a corrected test-construction mechanism.

3. **Reference-resolution regex kept to exactly the two patterns specified (markdown-link +
   `@filename`), no third "backtick code-span" pattern added**, despite the plan's prose citing
   `` `context-discovery.md` `` as an "in scope" example (architecture's actual SKILL.md references
   its companion files via backtick-wrapped table cells, not markdown-link or `@`-mention syntax,
   so that specific example is not actually matched by either specified pattern). Verified by
   grepping a candidate third pattern (backtick-wrapped filename with a companion extension) across
   all 16 real `SKILL.md` bodies before deciding: it produces false positives in 9 of 16 skills
   (`agent-monitoring-retro`, `create-tickets`, `implement-epic`, `implement-ticket`, `doc-coauthoring`,
   `prompt-builder`, `simq-audit`, and others) — matches on unrelated repo-relative doc/tool paths
   and generic example output filenames (e.g. `technical-spec.md`, `decision-doc.md`) that are
   never meant to resolve inside the generated skill package. The two specified patterns alone
   correctly detect `test-driven-development`'s real (pre-fix-broken) `@testing-anti-patterns.md`
   reference, correctly exclude `backend-testing`'s two dead cross-skill links and its/other skills'
   `@pytest.fixture`/`@example.com`-style false positives, and satisfy the AC's literal "fails
   pre-fix (confirmed by running the test against a git-stash of the source changes), passes
   post-fix, for all 16 skills" requirement. Not extending the pattern further is consistent with
   the plan's own Anti-Drift Hazards (the reference-resolution test must not become an inverse
   "every companion file must be referenced" check).

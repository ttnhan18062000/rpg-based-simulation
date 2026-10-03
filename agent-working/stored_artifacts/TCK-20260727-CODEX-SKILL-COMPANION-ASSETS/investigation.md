---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260727-CODEX-SKILL-COMPANION-ASSETS
artifact_type: investigation
tags: [ai, workflows, process-improvement]
---

# Investigation — TCK-20260727-CODEX-SKILL-COMPANION-ASSETS

## Current Behavior

### 1. `agent-orchestration/skills.yaml` — 16 entries, exactly 4 fields each

`agent-orchestration/skills.yaml:6-71` — `skills_version: 1`, 16 entries, each with exactly
`id`, `description`, `workflows`, `roles` (confirmed by direct read of the full file). No
file-list/companion-asset field exists today. The header comment (lines 1-5) already documents
the `workflows`/`roles` axis but says nothing about companion files.

### 2. `tools/agent_orchestration/loader.py` — required-key check is presence-only, not exhaustive

`_REQUIRED_SKILL_ENTRY_KEYS = ("id", "description", "workflows", "roles")` (`loader.py:26`).
`_load_skills_yaml` (`loader.py:113-127`) calls `_require_keys` (`loader.py:61-65`), whose entire
logic is `if data.get(key) is None: raise ...`. **There is no allowlist/exhaustive check anywhere
in `loader.py`** — no `set(entry.keys()) <= allowed_keys` assertion exists for skills, roles,
workflow, or contract entries. Confirmed by reading every `_load_*` function in the file (lines
54-188): each one only validates that its *required* keys are non-`None`; none of them reject
unrecognized extra keys. **Answer to the ticket's explicit question**: adding a new
`companion_assets` field to `skills.yaml` entries today would **not** be rejected by the current
validator, with or without a schema-version bump — the validator simply never looks at it. No
schema-version gate needs to be threaded through for the field to be silently accepted; validation
work is additive, not permission-granting.

**However**, also confirmed: **no field in `skills.yaml` has any type validation today** — not
`workflows`, not `roles`, nothing. `_require_keys` only checks non-`None`, never `isinstance`. So
the ticket's AC ("rejects non-list/non-string-list values") requires genuinely new validation
logic, not an extension of an existing type-check pattern (there isn't one to extend). And because
`_require_keys`'s only behavior is "raise if missing," `companion_assets` must **not** be added to
`_REQUIRED_SKILL_ENTRY_KEYS` if the AC's "defaults to `[]` if omitted" is to hold — that tuple's
check trips on the key being absent, which is the exact case the AC wants to tolerate. The new
logic needs its own small block: `entry.get("companion_assets", [])` then type-check the result,
structurally separate from the required-key loop.

### 3. `tools/agent_orchestration_codex_adapter/generator.py` — SKILL.md-only copy, no companion path

`build_codex_skill_md()` (`generator.py:28-34`) reads only
`repo_root/.claude/skills/<id>/SKILL.md`, strips frontmatter via `_body()` (`generator.py:19-26`),
and returns a new Codex-frontmatter + body string. `render_codex_guidance()`
(`generator.py:44-58`) builds a flat `paths` list — `AGENTS.md` plus one `SKILL.md` path per
skill (`generator.py:50-53`) — runs **every** path through `_assert_write_allowed`
(`generator.py:54`) in one upfront pass *before* any file is written (`generator.py:55-57`), then
writes. No companion file is ever read from or written to `.claude/skills/<id>/` /
`.agents/skills/<id>/` beyond the single `SKILL.md`.

The write-guard itself, `_assert_write_allowed` (`generator.py:12-17`), is structurally ready for
companion-asset targets without modification: it refuses `.claude/`/`.codex/` targets
unconditionally, and (absent `allow_outside_contract`) requires every target to be
`root/'AGENTS.md'` or `is_relative_to(root/'.agents'/'skills')` — a companion-asset path like
`.agents/skills/architecture/context-discovery.md` already satisfies that `is_relative_to` check
with zero changes to the guard function itself. The extension work is in building the additional
`Path` entries and running them through the *same* upfront guard-then-write ordering — see Anti-
Drift Hazards.

### 4. Complete 16-skill companion-asset inventory (`.claude/skills/` vs `.agents/skills/`)

Full recursive listing of both trees, cross-checked file-by-file:

| Skill id | `.claude/skills/<id>/` companion files (beyond `SKILL.md`) | `.agents/skills/<id>/` today |
|---|---|---|
| `agent-monitoring-retro` | none | `SKILL.md` only |
| `api-design-principles` | `assets/api-design-checklist.md`, `assets/rest-api-template.py`, `references/graphql-schema-design.md`, `references/rest-best-practices.md`, `resources/implementation-playbook.md` (5 files, 3 subdirs) | `SKILL.md` only |
| `architecture` | `context-discovery.md`, `examples.md`, `pattern-selection.md`, `patterns-reference.md`, `trade-off-analysis.md` (5 files, flat) | `SKILL.md` only |
| `backend-testing` | none | `SKILL.md` only |
| `brainstorming` | `spec-document-reviewer-prompt.md`, `visual-companion.md`, `scripts/frame-template.html`, `scripts/helper.js`, `scripts/server.cjs`, `scripts/start-server.sh`, `scripts/stop-server.sh` (2 files + 5-file `scripts/` dir) | `SKILL.md` only |
| `create-tickets` | none | `SKILL.md` only |
| `debugging-strategies` | none | `SKILL.md` only |
| `doc-coauthoring` | none | `SKILL.md` only |
| `frontend-design` | none | `SKILL.md` only |
| `implement-epic` | none | `SKILL.md` only |
| `implement-ticket` | none | `SKILL.md` only |
| `prompt-builder` | none | `SKILL.md` only |
| `python-performance-optimization` | none | `SKILL.md` only |
| `python-testing-patterns` | none | `SKILL.md` only |
| `simq-audit` | none | `SKILL.md` only |
| `test-driven-development` | `testing-anti-patterns.md` (1 file) | `SKILL.md` only |

**Audit result: exactly the 4 skills named in the ticket's Request Summary have companion
assets; the other 12 have none.** No 13th case was found. This resolves the ticket's own
Assumptions/Open Questions item #2 in the direction of the smaller, already-assumed outcome.

### 5. The "referenced-by-SKILL.md vs. every-file-present" design question — resolved with concrete counter-evidence

Grepped every `.claude/skills/<id>/SKILL.md` for markdown-link syntax and `@filename` mentions,
then manually cross-checked the two skills with subdirectories against their full SKILL.md body
text (read in full, not just grepped):

- **`architecture`** (`SKILL.md:19-23`, a lookup table): all 5 companion filenames
  (`context-discovery.md`, `trade-off-analysis.md`, `pattern-selection.md`, `examples.md`,
  `patterns-reference.md`) are named in the table. Fully consistent with either interpretation.
- **`test-driven-development`** (`SKILL.md:359`): `@testing-anti-patterns.md` — the one companion
  file is referenced. Consistent with either interpretation.
- **`api-design-principles`** (`SKILL.md`, all 40 lines read in full): the body references
  `resources/implementation-playbook.md` twice (lines 36, 40) and **nothing else** — no mention of
  `assets/api-design-checklist.md`, `assets/rest-api-template.py`,
  `references/graphql-schema-design.md`, or `references/rest-best-practices.md` anywhere in the
  body text.
- **`brainstorming`** (`SKILL.md`, 164 lines, grepped for every companion filename): references
  `spec-document-reviewer-prompt.md` (line 122) and `visual-companion.md` (line 164), but **never**
  mentions `scripts/` or any of its 5 files anywhere in the body.

**Finding: interpretation (b) ("only files SKILL.md's own body textually references") is
falsified by the live data** — it would exclude `api-design-principles`'s `assets/` and
`references/` subdirectories (4 of 5 companion files) and `brainstorming`'s entire `scripts/`
subdirectory (5 of 7 companion files). But the ticket's own Acceptance Criteria explicitly
requires shipping `.agents/skills/api-design-principles/{assets,references,resources}/*` and
`.agents/skills/brainstorming/{...,scripts/*}` in full — i.e., the ticket's own AC already commits
to shipping content that is not textually referenced by SKILL.md's body. Interpretation (a)
("every file physically present, no curation") is separately ruled out by the ticket's own Out of
Scope line ("does not attempt a blanket copy-every-file rule") and is consistent with the fact
that all companion files found *are* legitimate (no stray/draft files were found sitting unused in
any of the 4 directories — every present file is either textually referenced or is exactly the
kind of executable/structural support material — `scripts/`, `assets/`, `references/` — the
converged Claude/Codex recommendation names as belonging in an "approved companion assets"
allowlist even without a literal in-body citation).

**Conclusion for Plan**: `companion_assets` must be a **curated allowlist per skill**, populated by
human/agent judgment at Plan/Implement time (matching every file actually found in each of the 4
directories, since none were found to be extraneous), not derived mechanically from parsing
SKILL.md's own reference syntax. The separately-required "reference-resolution test" is a
**different, one-directional check**: it parses the *generated* SKILL.md body for relative
references and asserts each one resolves inside the generated package — it does not (and per the
data above, must not) assert the converse ("every shipped file is referenced by name in the
body"), or it would incorrectly fail on `api-design-principles` and `brainstorming` even after a
correct fix.

### 6. Reference-resolution test hazard — pre-existing broken/false-positive references found

Grepping all 16 `SKILL.md` bodies for markdown-link syntax (`[text](path.ext)`) and `@filename`
mentions surfaced two categories of noise that a naive implementation of the new test would
mishandle:

- **`backend-testing/SKILL.md:840-841`** (pre-existing, unrelated to companion assets):
  ```
  - [api-design](../api-design/SKILL.md): Design APIs alongside tests
  - [authentication-setup](../authentication/SKILL.md): Test authentication systems
  ```
  Both are dead cross-skill links: the real skill id is `api-design-principles`, not `api-design`
  (no `.claude/skills/api-design/` exists), and there is no `authentication`/`authentication-setup`
  skill anywhere in the 16-entry catalog. This is boilerplate carried over from the community skill
  source, confirmed pre-existing and **out of this ticket's scope** (`.claude/skills/` is read-only
  per Out of Scope). A reference-resolution test that treats every markdown-link match as a
  same-package companion-asset reference to be resolved will hard-fail on `backend-testing` the
  moment it runs against the full 16-skill set, for content this ticket must not touch.
- **`@example.com` / `@pytest.fixture` / `@pytest.mark.*` / `@domain.co.uk`** — dozens of hits in
  `backend-testing`, `python-performance-optimization`, and `python-testing-patterns` (email
  addresses in test-data examples, Python decorators in code blocks). A naive `@[\w./-]+\.\w+`
  regex (matching the `@testing-anti-patterns.md` style named in the ticket) will match these as
  false-positive "file references" unless the pattern is scoped to a known companion-file
  extension set (e.g. `.md|.py|.js|.cjs|.sh|.html`) and/or excludes matches inside fenced code
  blocks.

Both are real design constraints for Plan/Implement, not blockers for Investigate — see Risks and
Open Questions and Anti-Drift Hazards below.

## Mechanics / Engine Constraints

Not applicable. Confirmed consistent with every sibling ticket in the provider-agnostic
orchestration batch (`TCK-20260721-ORCHESTRATION-CONTRACT-CORE`,
`TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE`, `TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER`): this
subsystem is agent-infrastructure tooling (`agent-orchestration/`, `tools/agent_orchestration*/`,
`.agents/`), not `src/` simulation code. No `docs/mechanics/` chapter or `docs/engine/` contract
governs `skills.yaml` or the Codex-adapter generator.

## Parity Ledger Overlap

None. Grepped all `docs/parity_ledger/*.yaml` for `codex|skills\.yaml|SKILL\.md|companion` — the
three hits found are unrelated: two are prose uses of the word "companion" inside
`infrastructure.yaml`'s INFRA-256/257/260 support-boundary narrative entries (nothing to do with
skill companion assets), and one (`infrastructure.yaml:5533`) is a citation of
`.claude/skills/simq-audit/SKILL.md` inside an unrelated term-registration entry, not a reference
to this generator or gap. No P0 entry anywhere touches this subsystem. No parity ledger update is
needed for this ticket, consistent with its own Assumptions/Open Questions.

## Prior Work

- **`TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE`** (DONE,
  `stored_artifacts/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE/`) — built
  `tools/agent_orchestration_codex_adapter/generator.py`, this ticket's extension target. Its
  investigation.md Risk #2 ("`SKILL.md` body-content source is undefined... deferring full parity
  to a later ticket") explicitly named this exact gap and deferred it; this ticket is that later
  ticket. That investigation also established the "guard-then-write, all paths checked upfront
  before any write" ordering this ticket's extension must preserve (see Anti-Drift Hazards) and the
  `_assert_write_allowed`/`CodexAdapterWriteGuardError` pattern to reuse rather than reinvent.
- **`TCK-20260721-ORCHESTRATION-CONTRACT-CORE`** (DONE,
  `stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/`) — owns `skills.yaml`'s schema and
  `loader.py`'s validation conventions: single validation entry point returning a frozen dataclass,
  `ContractValidationError`/`FixtureValidationError`-style messages naming the exact file path and
  missing field. Its own Anti-Drift Hazards explicitly warn against letting `skills.yaml` "duplicate
  role obligations" — the new `companion_assets` field is skill-shaped (per-skill file list), not
  role-shaped, so it does not reintroduce that conflation, but `test_skills_yaml_does_not_duplicate_role_fields`
  (see Regression Surface in test_plan.md) is the existing guard that would catch it if it did.
- **`tests/agent_orchestration_codex_adapter/test_legacy_skills_containment.py`** — establishes the
  `docs/archive/legacy_agents_skills_20260722/` archive-hash-check pattern; not directly touched by
  this ticket (it guards the 18-dir legacy quarantine, a different concern from the live 16-skill
  catalog's companion-asset gap) but confirms the `.agents/skills/` tree is otherwise stable and
  this ticket's regeneration will not collide with it.

## Risks and Open Questions

1. **Companion-asset regex/parsing design for the new reference-resolution test is not fully
   specified and has two concrete failure modes already found in live data** (Current Behavior §6):
   pre-existing dead cross-skill links in `backend-testing/SKILL.md` (out of scope to fix), and
   `@example.com`/`@pytest.fixture`-style false positives in three skills' bodies. Plan must decide
   the exact reference-detection pattern (extension allowlist, code-fence exclusion, and/or
   same-directory-only scoping) so the test doesn't fail on content this ticket is not permitted to
   touch. Not blocking Investigate, but must not be left to Implement-time guesswork — a wrong
   choice here either produces a test that's vacuously permissive (misses real dangling refs, defeats
   the AC's "real regression test" requirement) or one that hard-fails on unrelated pre-existing
   content in `backend-testing`.
2. **`companion_assets` path-traversal is a new attack surface `_assert_write_allowed` doesn't yet
   check.** The existing `test_rejects_path_traversal_skill_id_before_writing` test only covers a
   malicious `id` field (`../../etc`); it does not cover a malicious `companion_assets` relative-path
   entry (e.g. `../../../etc/passwd`) that could resolve outside `.agents/skills/<id>/` even though
   the *skill id* itself is clean. `Path.is_relative_to` on the *final joined* path
   (`root/.agents/skills/<id>/<relative>`) would catch this if the guard is invoked per resolved
   companion-asset path (matching the existing SKILL.md-path pattern) — but this needs an explicit
   test, since no existing test exercises it and the AC doesn't call it out by name.
3. **No `CodexAdapterMissingCompanionAssetError` (or similarly named) error type exists yet** for the
   case where `skills.yaml` declares a `companion_assets` path that doesn't exist under
   `.claude/skills/<id>/` at generation time — `errors.py` currently defines only
   `CodexAdapterWriteGuardError` and `CodexAdapterMissingSkillSourceError` (mirroring
   `build_codex_skill_md`'s missing-`SKILL.md` case). Plan should decide whether to add a new named
   error or reuse `CodexAdapterMissingSkillSourceError` with a companion-asset-specific message —
   consistent with this ticket's own predecessor's established "named, deterministic error type"
   convention (`stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/investigation.md`'s
   `FixtureValidationError` precedent).
4. **`docs/architecture/agent_orchestration_contract.md`'s "Contract Representation and Format"
   section (lines 55-64, read in full) is short and general** ("YAML for human-reviewable
   definitions, generated Python validation models") — it does not mention `skills.yaml`'s specific
   fields at all, so a `companion_assets` field addition doesn't contradict it, but the ticket's own
   Scope asks Plan to either add a short note there or record in Assumptions/Open Questions why not.
   This is a documentation-completeness decision, not a technical blocker.

None of these block starting Plan — all are exactly the kind of "Plan must decide" items the
ticket's own Scope/AC text already anticipates.

## Anti-Drift Hazards

- **Do not add `companion_assets` to `_REQUIRED_SKILL_ENTRY_KEYS`.** That tuple's check
  (`entry.get(key) is None`) raises on a genuinely absent key — the AC explicitly wants omission to
  default to `[]`, which requires separate, additive validation logic, not an extension of the
  required-key loop.
- **Do not derive `companion_assets` by parsing SKILL.md for references.** Current Behavior §5
  proves this would under-ship `api-design-principles` (miss `assets/`, `references/`) and
  `brainstorming` (miss `scripts/`) relative to the ticket's own AC. The field is a curated,
  human/agent-authored allowlist, not a mechanically-derived one.
- **Do not let the new reference-resolution test require "every shipped companion file is
  referenced in the body."** That is the inverse of what the test should check and is directly
  falsified by `api-design-principles`/`brainstorming`'s real content (§5). The test's only job is:
  every reference *found in* the generated body resolves to a real file in the generated package —
  one direction only.
- **Do not let the reference-resolution test touch or require fixing `backend-testing/SKILL.md`'s
  two pre-existing dead cross-skill links** (`../api-design/SKILL.md`, `../authentication/SKILL.md`,
  Current Behavior §6) — `.claude/skills/` is explicitly read-only Out of Scope for this ticket.
  Whatever detection pattern Plan picks must not incidentally turn these into new test failures
  this ticket would then be pressured to "fix" by editing the read-only source tree.
- **Do not write any companion-asset file before every target path (SKILL.md paths *and* the new
  companion-asset paths) has passed `_assert_write_allowed`.** The existing write-guard tests
  (`test_generator_write_guard.py::test_rejects_path_traversal_skill_id_before_writing`) assert
  nothing is written if any single target fails the guard — preserve the current "collect all
  paths, guard all paths, then write all paths" two-pass structure (`generator.py:50-57`) rather
  than interleaving per-skill guard-then-write, which could leave partial output on disk on a
  mid-loop failure.
- **Do not silently regenerate `.agents/skills/` without also re-running
  `test_legacy_skills_containment.py`'s hash checks** — that test guards against the *legacy*
  18-directory quarantine leaking back into the live catalog; while this ticket doesn't touch that
  archive, any regeneration of `.agents/skills/` should be confirmed not to disturb it (it shouldn't,
  since the archive lives under `docs/archive/`, outside `.agents/skills/`, but the confirmation
  should be explicit at Verify time, not assumed).
- **Do not scope-creep into promoting the 6 legacy `.agents/skills/` directories** (`clean-code`,
  `codebase-search`, `code-review`, `create-skill`, `receiving-code-review`,
  `requesting-code-review`) — explicitly deferred by a different, not-yet-created ticket per this
  ticket's own Out of Scope and `docs/ai/agents_dir_disposition.md`.

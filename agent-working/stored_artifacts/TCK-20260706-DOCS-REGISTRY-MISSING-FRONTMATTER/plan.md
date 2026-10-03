---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER
artifact_type: plan
tags: [documentation, registry, frontmatter, tagging]
---

# Implementation Plan — TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER

## Summary

Add a minimal, correct YAML frontmatter block to each of the 12 named `docs/` files, using values
derived per-file from sibling doc conventions and each file's own self-declared inline metadata
(never a blind bulk-apply). No code changes: `tools/generate_registry.py`'s hard-error-on-missing-doc-
frontmatter behavior stays exactly as-is (per the ticket's own UQ-1 assumption). Work is grouped into
4 independent per-file-group steps (mirroring the investigation's Group A/B/C/D taxonomy) plus a final
verification step that regenerates `docs/REGISTRY.yaml` and runs the full scoped test suite. Each step
edits only frontmatter — zero body/heading changes to any of the 12 files. The two Group-B/D "report"
files get `status: active` (not `authoritative`) since neither self-declares a certification claim, per
OQ-B. `party_contract.md`'s self-declared `Layer: social` is corrected to `layer: simulation` (the
valid enum value matching its 19 sibling `docs/simulation/domains/*.md` contracts), per the
investigation's Risk #1 finding — its own inline claim is wrong, so it is not literally transcribed.
`demographics_contract.md` uses `last_verified: 2026-07-02` (git-log-last-modified date), per OQ-C.
AC #3 is verified using the 12 explicit per-file `validate_frontmatter.py` invocations listed in
`test_plan.md`, never a whole-tree `docs/` sweep — `docs/simulation/domains/social_memory_contract.md`
is a pre-existing, out-of-scope failure that this ticket must not touch or silently absorb.

## Steps

### Step 1 — Add frontmatter to the 6 Group A `docs/engine/` files

**Files:**
- `docs/engine/legacy_replacement_ledger.md`
- `docs/engine/phase12_entry_package.md`
- `docs/engine/phase13_retirement_manifest.md`
- `docs/engine/engineering_playbook_m10.md`
- `docs/engine/project_lawbook_m10.md`
- `docs/engine/supported_progression_surface_phase5.md`

**Change:** Prepend the following block as the very first bytes of each file (before the existing
leading `# ` heading, no blank line consumed from the existing content — insert the block then a
blank line then the file's existing first line unchanged):

```yaml
---
status: active
layer: engine
authority: P1
audience: developer
---
```

This exactly matches the pattern already used by sibling `docs/engine/*.md` files (`kernel.md`,
`architecture.md`, `known_limitations.md` — confirmed via direct read: `status: active / layer: engine
/ authority: P1 / audience: developer`, no `tags`, no `last_verified`). None of these 6 self-declare a
different status or authority level in their own body text, so the sibling default applies uniformly
to all 6.

**Do NOT touch:**
- Any `## ` heading text in these 6 files (breaks `test_document_structural_compliance` /
  `test_doc_header_compliance`, which regex-match `manifest.json`'s `required_headers` against exact
  heading text).
- `docs/engine/manifest.json`'s `mandatory_documents` or `required_headers` entries.
- `engineering_playbook_m10.md`'s `"## Extension Templates"`, `"### Runtime Profile Template"`,
  `"### Certification Scenario Template"` substrings (asserted verbatim by
  `test_extension_templates_present`).
- Body content of any of the 6 files beyond the new frontmatter block.

**Verify:**
- `python3 tools/validate_frontmatter.py docs/engine/legacy_replacement_ledger.md --content-type doc`
- `python3 tools/validate_frontmatter.py docs/engine/phase12_entry_package.md --content-type doc`
- `python3 tools/validate_frontmatter.py docs/engine/phase13_retirement_manifest.md --content-type doc`
- `python3 tools/validate_frontmatter.py docs/engine/engineering_playbook_m10.md --content-type doc`
- `python3 tools/validate_frontmatter.py docs/engine/project_lawbook_m10.md --content-type doc`
- `python3 tools/validate_frontmatter.py docs/engine/supported_progression_surface_phase5.md --content-type doc`
- `pytest tests/docs/test_doc_integrity.py::test_manifest_file_existence tests/docs/test_doc_integrity.py::test_document_structural_compliance tests/integrity/test_doc_guards.py::test_mandatory_doc_existence tests/integrity/test_doc_guards.py::test_doc_header_compliance tests/docs/test_contributor_guardrails.py::test_extension_templates_present tests/docs/test_contributor_guardrails.py::test_forbidden_terminology -m "not slow"`

---

### Step 2 — Add frontmatter to Group B: `docs/mechanics/content_usage_matrix.md`

**Files:** `docs/mechanics/content_usage_matrix.md`

**Change:** Prepend:

```yaml
---
status: active
layer: mechanics
authority: P1
audience: developer
---
```

Per OQ-B resolution: this is a dynamically-generated report ("This report is generated dynamically...",
per its own opening text), not a certified law chapter — do not use `status: authoritative` even
though sibling `docs/mechanics/01_entity_anatomy.md`-style chapters do, since `authoritative` requires
`last_verified` and no honest verification date exists for a doc that regenerates on demand. `layer:
mechanics` matches its directory placement (a valid `LAYER_VALUES` member, distinct from the chapter
files' P0 authority — this file is not one of the numbered chapters 01–06 per `CLAUDE.md`'s Mechanics
Bible table, so `authority: P1` not `P0`).

**Do NOT touch:**
- The `[!IMPORTANT]` policy-note callout or any body content.
- Any of the numbered Mechanics Bible chapter files (`docs/mechanics/01`–`06`) — not in scope, already
  have frontmatter.

**Verify:**
- `python3 tools/validate_frontmatter.py docs/mechanics/content_usage_matrix.md --content-type doc`
- `pytest tests/tools/test_validate_frontmatter.py -m "not slow"`

---

### Step 3 — Add frontmatter to Group C: the 3 self-declaring "contract" docs

**Files:**
- `docs/systems/faction_contract.md`
- `docs/world/demographics_contract.md`
- `docs/simulation/domains/party_contract.md`

**Change:**

`docs/systems/faction_contract.md` — prepend (mirrors its own `**Status**: AUTHORITATIVE ... Last
verified: 2026-06-23.` line at L3, and sibling `docs/systems/*.md` use `layer: systems, authority: P1,
audience: developer`):
```yaml
---
status: authoritative
layer: systems
authority: P1
audience: developer
last_verified: 2026-06-23
---
```

`docs/world/demographics_contract.md` — prepend (mirrors its own `**Authority:** Certified Level 1
(Authoritative)` / `**Layer:** world` lines; per OQ-C, `last_verified` uses the git-log-last-modified
date 2026-07-02, not the ticket-embedded 2026-06-19, since that is the more-recent confirmed-touched
date and matches this repo's convention of "most recent confirmed-correct date" rather than a proposal
date):
```yaml
---
status: authoritative
layer: world
authority: P1
audience: developer
last_verified: 2026-07-02
tags: [demographics, cohort, population, density-signal, phase-5]
---
```
(The `tags` list is carried over verbatim from the doc's own `**Tags:**` line at L6-7 — this is
transcription of an already-correct self-declared value, not an inference.)

`docs/simulation/domains/party_contract.md` — prepend. Its own `**Layer:** social` (L4) is **not**
transcribed — `social` is not a valid `LAYER_VALUES` member. Use `layer: simulation`, matching all 19
other `docs/simulation/domains/*.md` sibling contracts (e.g. `adventure_contract.md`: `status: active /
layer: simulation / authority: P1 / audience: agent`). The doc's own `**Authority:** P1` (L3) is
transcribed as-is (already valid):
```yaml
---
status: active
layer: simulation
authority: P1
audience: agent
---
```

**Do NOT touch:**
- The `**Authority:** P1` / `**Layer:** social` / `**Status**: AUTHORITATIVE...` inline text lines in
  the file bodies — these are pre-existing self-declarations left as-is; only the new frontmatter block
  is added. (Correcting the inline `Layer: social` text itself, as opposed to the new frontmatter's
  `layer` field, would be a body content change beyond "adding/correcting frontmatter" and is out of
  this ticket's scope.)
- `docs/simulation/domains/social_memory_contract.md` — explicitly out of scope; it already has its own
  (invalid) `layer: social` real frontmatter and already fails `validate_frontmatter.py` today,
  pre-existing and unrelated to this ticket. Do not edit it, do not "fix" it as a drive-by, do not
  include it in any verification command.
- Any other `docs/simulation/domains/*.md` file not in the 12-file list.

**Verify:**
- `python3 tools/validate_frontmatter.py docs/systems/faction_contract.md --content-type doc`
- `python3 tools/validate_frontmatter.py docs/world/demographics_contract.md --content-type doc`
- `python3 tools/validate_frontmatter.py docs/simulation/domains/party_contract.md --content-type doc`
- `pytest tests/tools/test_validate_frontmatter.py -m "not slow"`

---

### Step 4 — Add frontmatter to Group D: the 2 `docs/simulation_quality/` files

**Files:**
- `docs/simulation_quality/event_type_coverage.md`
- `docs/simulation_quality/eval_matrix_results.md`

**Change:**

`docs/simulation_quality/event_type_coverage.md` — prepend (mirrors its own `**Status:** Certified
Level 1 — Authoritative` L3 and `**Last updated:** 2026-07-04` line):
```yaml
---
status: authoritative
layer: simulation
authority: P1
audience: developer
last_verified: 2026-07-04
---
```

`docs/simulation_quality/eval_matrix_results.md` — prepend. Per OQ-B: this is a dated results report
with no self-declared authoritative/certified claim (only `**Date:** 2026-07-02`), analogous to
`content_usage_matrix.md` — use `status: active`, not `authoritative`, to avoid fabricating a
certification claim the doc never makes itself:
```yaml
---
status: active
layer: simulation
authority: P1
audience: developer
---
```

Both use `layer: simulation` matching the directory's sibling template
`docs/simulation_quality/quality_scoring_contract.md` (`status: active / layer: simulation / authority:
P1 / audience: developer / tags: [...]`) — `event_type_coverage.md` additionally carries
`authority: P1` (not P0) since neither file is a Mechanics Bible chapter.

**Do NOT touch:**
- `docs/simulation_quality/quality_scoring_contract.md` or `corpus_tier_taxonomy.md` — already have
  correct frontmatter, not in the 12-file list.
- The `**Audit base:**` / `**Last updated:**` inline provenance text in `event_type_coverage.md` —
  transcribe the date into frontmatter, do not remove or reword the inline text itself.

**Verify:**
- `python3 tools/validate_frontmatter.py docs/simulation_quality/event_type_coverage.md --content-type doc`
- `python3 tools/validate_frontmatter.py docs/simulation_quality/eval_matrix_results.md --content-type doc`
- `pytest tests/tools/test_validate_frontmatter.py -m "not slow"`

---

### Step 5 — Add the two regression-guard tests

**Files:**
- `tests/tools/test_generate_registry.py`
- `tests/tools/test_validate_frontmatter.py`

**Change:**
1. In `tests/tools/test_generate_registry.py`, add `test_registry_exits_zero_on_real_docs_tree` (or
   match the file's existing naming convention) — an integration-style test (not `tmp_path`-synthetic
   like the rest of the file) that invokes `generate_registry()` (or subprocess-runs
   `python3 tools/generate_registry.py`) against the **real** repo root (`Path(".")` /
   `Path(__file__).resolve().parents[2]`, matching however the file already locates repo root if it
   does elsewhere), writing output YAML to a `tmp_path` fixture so the real `docs/REGISTRY.yaml` is
   never touched by the test run, and asserts the return code is `0`. This pins AC #2 as a permanent
   regression guard.
2. In `tests/tools/test_validate_frontmatter.py`, add
   `test_all_previously_frontmatter_missing_docs_now_pass_validation` — iterates the 12 explicit paths
   (hardcode the list, matching the ticket's own enumeration) and asserts
   `validate_file(path, content_type_override="doc", registry=None)` (or whatever the existing
   `validate_file` call signature is in this file — check an existing test in the same file for the
   exact signature before writing) returns `[]` for each, with the file path included in the assertion
   message so a future regression on any one of the 12 fails loudly and specifically.

**Do NOT touch:**
- Any existing test in either file (e.g. `test_registry_exits_nonzero_on_missing_doc_frontmatter`,
  `test_ticket_missing_frontmatter_emits_warning_not_error`) — these guard the doc-hard-error /
  ticket-soft-warn asymmetry that this ticket must preserve, not change.
- `docs/simulation/domains/social_memory_contract.md` must **not** appear in the new
  `test_all_previously_frontmatter_missing_docs_now_pass_validation` test's path list — it is out of
  scope and currently fails; including it would make the new test fail for a reason unrelated to this
  ticket.

**Verify:**
- `pytest tests/tools/test_generate_registry.py tests/tools/test_validate_frontmatter.py -m "not slow" --tb=short`

**Dependency:** Depends on Steps 1–4 being complete (the new tests assert against the post-fix state
of all 12 files).

---

### Step 6 — Regenerate `docs/REGISTRY.yaml` and run full scoped verification

**Files:** `docs/REGISTRY.yaml` (regenerated output, git-tracked)

**Change:**
1. Run `make docs-registry` and confirm exit code `0` (AC #2). This also regenerates
   `docs/REGISTRY.yaml` in place, which will now include real (non-default) `title`/`status`/`layer`
   entries for all 12 previously-absent files (per investigation Risk #5: `collect_docs()` currently
   skips entry creation entirely on error, so these 12 are presently **absent** from the registry, not
   present-with-blank-defaults — post-fix they must newly appear).
2. Run each of the 12 per-file `validate_frontmatter.py` invocations listed in `test_plan.md` (AC #3,
   scoped per OQ-A resolution to exactly these 12 files — do **not** run a whole-tree
   `python3 tools/validate_frontmatter.py docs/` sweep as the AC-passing evidence, since
   `docs/simulation/domains/social_memory_contract.md` — outside this ticket's scope — already fails
   whole-tree validation today and is not this ticket's to fix).
3. Run the full scoped pytest command from `test_plan.md`:
   `pytest tests/tools/test_generate_registry.py tests/tools/test_validate_frontmatter.py tests/docs/ tests/integrity/test_doc_guards.py tests/integrity/test_manifest_guards.py -m "not slow" --tb=short`
4. Stage and include the regenerated `docs/REGISTRY.yaml` in the ticket's commit — a stale registry
   that still shows the 12 files absent would silently reintroduce the exact discovery gap that
   motivated this ticket.

**Do NOT touch:**
- `tools/generate_registry.py` or `tools/validate_frontmatter.py` source — no code changes are in
  scope for this ticket (UQ-1: the hard-error behavior is assumed correct, not relaxed).
- Any `docs/REGISTRY.yaml` entries for files outside the 12-file list (the regeneration is a full
  rewrite by the tool itself, which is expected and fine — just don't hand-edit the output afterward).

**Verify:** All three commands above must pass/exit 0. This step is the final AC gate for AC #1, #2,
and #3 together.

**Dependency:** Depends on Steps 1–5 (all frontmatter added, both new regression tests written and
passing) being complete first.

## Scope Guards

- Do not touch `docs/simulation/domains/social_memory_contract.md` under any circumstance — it is
  explicitly outside the 12-file list, already has a real (invalid `layer: social`) frontmatter block,
  and already fails `validate_frontmatter.py` today. This is a pre-existing, separate defect. Do not
  edit it, do not include it in any new test's path list, do not reference it in any AC-verification
  command.
- Do not modify `tools/generate_registry.py`'s `collect_docs()`/`collect_tickets()` error-vs-warning
  asymmetry, or any other logic in `tools/generate_registry.py` or `tools/validate_frontmatter.py`.
  UQ-1 in the ticket explicitly assumes the current hard-error-on-missing-doc-frontmatter behavior is
  correct.
- Do not archive any of the 6 Group A files (`legacy_replacement_ledger.md`, `phase12_entry_package.md`,
  `phase13_retirement_manifest.md`, `engineering_playbook_m10.md`, `project_lawbook_m10.md`,
  `supported_progression_surface_phase5.md`). Investigation confirmed all 6 remain load-bearing via
  `docs/engine/manifest.json`'s `mandatory_documents` list; archiving any would break
  `test_mandatory_doc_existence`/`test_doc_header_compliance`. The ticket's Scope explicitly requires
  confirming obsolescence first — investigation already did this and found none obsolete.
- Do not edit `docs/engine/manifest.json` (`mandatory_documents`, `required_headers`, or
  `forbidden_terms`).
- Do not reword, remove, or add any `## ` heading in any of the 12 files.
- Do not change body content of any of the 12 files beyond prepending the frontmatter block (the
  inline self-declared metadata lines like `**Status**: AUTHORITATIVE...` or `**Layer:** social` stay
  exactly as they are in the body text — only the new machine-readable frontmatter is corrected/added).
- Do not run or rely on a whole-tree `python3 tools/validate_frontmatter.py docs/` invocation as
  evidence for AC #3 — use the 12 explicit per-file invocations only.
- Do not re-litigate or touch any file from `TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC`'s already-completed
  work.
- Do not use `tools/add_frontmatter_live.py` in bulk-apply mode if it would overwrite the per-file,
  evidence-derived values above with a generic uniform default — if used at all, only as a scaffold
  followed by hand-correction per the values specified in Steps 1–4, never as the final unreviewed
  output.

## Dependency Map

- Steps 1, 2, 3, 4 are independent of each other (different files, no shared state) and may be done in
  any order.
- Step 5 depends on Steps 1–4 (new tests assert against the post-fix content of all 12 files).
- Step 6 depends on Steps 1–5 (final registry regeneration and full verification requires all
  frontmatter added and both new regression tests in place).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — All 12 listed files have valid, correct YAML frontmatter (or confirmed obsolete + archived) | Steps 1, 2, 3, 4 (frontmatter added; investigation confirmed none of the 12 are obsolete, so archiving is not used for any) | Per-file `validate_frontmatter.py` commands in Steps 1–4's Verify blocks; consolidated in Step 6 |
| AC #2 — `make docs-registry` exits 0 | Steps 1–4 (removes the root cause: missing frontmatter) + Step 6 (confirms exit code) | Step 6's `make docs-registry` run; regression-pinned by Step 5's `test_registry_exits_zero_on_real_docs_tree` |
| AC #3 — `validate_frontmatter.py <each file> --content-type doc` passes for every file still under `docs/` after this ticket (scoped per OQ-A to the 12 named files only, consistent with the ticket's Out of Scope section forbidding broader `docs/` auditing) | Steps 1, 2, 3, 4 | The 12 explicit per-file commands in Step 6; regression-pinned by Step 5's `test_all_previously_frontmatter_missing_docs_now_pass_validation` |

## Anti-Drift Notes

- **`social_memory_contract.md` is a trap, not a task.** It shares the same class of defect
  (`layer: social` invalid) as `party_contract.md`'s inline claim, and it is immediately adjacent in
  the same directory (`docs/simulation/domains/`) to a file this ticket does edit
  (`party_contract.md`). This adjacency makes it an easy accidental drive-by fix — do not touch it. It
  is explicitly out of scope and pre-existing.
- **The header-compliance tests (`test_document_structural_compliance`,
  `test_doc_header_compliance`) use `^##\s+...` MULTILINE regex matching against full file content** —
  confirmed frontmatter insertion before the leading `# ` title is safe and doesn't interfere, but this
  must be proven by actually running these tests after each edit (Step 1's Verify), not assumed safe
  from the regex alone.
- **`tests/tools/test_generate_registry.py` is entirely `tmp_path`-synthetic** — passing the existing
  suite gives zero signal about the real `docs/` tree's state. AC #2 can only be verified by actually
  running `make docs-registry` against the real repo (Step 6), which is why Step 5 explicitly adds a
  new *integration*-style test that touches the real filesystem rather than relying on the existing
  synthetic suite.
- **`docs/REGISTRY.yaml` is git-tracked and currently stale for these 12 files** (they are entirely
  absent from it, not present-with-blank-fields, per investigation Risk #5) — forgetting to regenerate
  and commit it in Step 6 would leave the ticket's own Definition of Done incomplete even though all
  ACs might appear to pass locally.
- **`party_contract.md`'s and `social_memory_contract.md`'s shared `layer: social` mistake likely
  originated from the same source pattern** (both under `docs/simulation/domains/`) — this is worth
  noting for a potential future ticket (out of scope here) that could fix `social_memory_contract.md`
  and possibly audit whether other files share the same mistaken inline `Layer:` claim, but that is
  explicitly not this ticket's work.
- **Do not fabricate `last_verified` dates for `status: authoritative` claims where no honest date
  exists** — this is why `content_usage_matrix.md` and `eval_matrix_results.md` use `status: active`
  instead of `authoritative` (OQ-B resolution), avoiding the `last_verified`-required validator rule
  (`validate_frontmatter.py:188-191`) for docs with no natural verification-date anchor.

## Open Questions Status

All resolved — none outstanding. All three open questions surfaced in `investigation.md` (OQ-A, OQ-B,
OQ-C) have clear resolutions already reasoned through and applied directly in Steps 1–6 and the
Acceptance Criteria Map above. No new open question was found during planning that these three
resolutions don't already cover.

## Deviations

- **Step 5's `test_all_previously_frontmatter_missing_docs_now_pass_validation`** was implemented as a
  `pytest.mark.parametrize`d test (one test case per file, 12 total) rather than a single test function
  with an internal `for` loop over the 12 paths. This is a stronger form of the same regression pin —
  each of the 12 files gets its own independently-reportable pass/fail rather than the first failing
  path silently short-circuiting the rest inside one loop — and still satisfies the plan's literal
  requirement ("iterates the 12 explicit paths ... asserts ... returns `[]` for each, with the file path
  included in the assertion message"). No other part of Step 5 changed.
- No other deviations. All 6 steps were executed exactly as specified, including the per-file frontmatter
  values, the Group A/B/C/D scoping, and the Step 6 verification sequence.

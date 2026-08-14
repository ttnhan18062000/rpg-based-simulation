---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER
artifact_type: investigation
tags: [documentation, registry, frontmatter, tagging]
---

# Investigation — TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER

## Current Behavior

`tools/generate_registry.py::collect_docs()` (L179–231) walks `docs/` recursively (skipping
`_SKIP_DOC_SUBDIRS = {"archive", "superpowers", "specs", "parity_ledger", "scenarios", "entity"}`,
L35) and calls `extract_frontmatter()` (imported from `tools/validate_frontmatter.py::L64`) on every
`.md` file. If `extract_frontmatter()` returns `None` (no `---` block matched by `_FM_PATTERN` at
`validate_frontmatter.py:60`), the file's relative path is appended to `errors` (L208) — this is a
**doc** error, distinct from ticket handling. `collect_tickets()` (L239) treats the same condition as
a warning only (prints to stderr, still emits an entry with defaults, L262–267) — this asymmetry is
why 3 `tickets/done/*.md` files with missing frontmatter do not block the exit code but the 12 docs
do.

`generate_registry()` (L408–443) always writes `docs/REGISTRY.yaml` regardless of `doc_errors`
(L410–435 run unconditionally), then returns `1` if `doc_errors` is non-empty (L437–441). `main()`
(L446) calls `sys.exit(generate_registry(...))` (L467), so `make docs-registry` (`Makefile:233-234`,
just `python3 tools/generate_registry.py`) propagates that exit code. Confirmed empirically: running
`make docs-registry` today prints `ERROR: 12 doc file(s) missing frontmatter` for exactly the 12 files
listed in the ticket, writes 1314 entries to `docs/REGISTRY.yaml` anyway, and exits 1 (`make: ***
[Makefile:234: docs-registry] Error 1`).

All 12 files start directly with a markdown `# ` heading — confirmed by direct read, no `---` block
at all (not a malformed block, not a parse error — `extract_frontmatter` cleanly returns `None` for
all 12, no `ValueError` path triggered).

### Per-file findings (grouped by origin)

**Group A — six `docs/engine/` files created as stub docs by `TCK-20260623-FIX-DOCS-INTEGRITY`**
(`docs/engine/legacy_replacement_ledger.md`, `phase12_entry_package.md`,
`phase13_retirement_manifest.md`, `engineering_playbook_m10.md`, `project_lawbook_m10.md`,
`supported_progression_surface_phase5.md`). That ticket's "Files Changed" section
(`tickets/done/TCK-20260623-FIX-DOCS-INTEGRITY.md:94-100`) explicitly lists all six as "created" to
satisfy `docs/engine/manifest.json`'s `mandatory_documents` list (`manifest.json:12-76`), which is
enforced by `tests/integrity/test_doc_guards.py::test_mandatory_doc_existence` and
`::test_doc_header_compliance` (asserts each `required_headers` entry is present as a `## ` heading —
confirmed regex is `^##\s+(?:\d+\.\s+)?{header}\b`, MULTILINE, so a leading frontmatter block does not
interfere). These are **not obsolete** — two of them are still actively cited as canonical by process
docs written after their creation: `CLAUDE.md` calls `project_lawbook_m10.md` "the master index" for
engine contracts, and `CONTRIBUTING.md` + `tests/docs/test_contributor_guardrails.py::
test_extension_templates_present` (L32-40) directly assert against `engineering_playbook_m10.md`'s
content. `phase12_entry_package.md`, `phase13_retirement_manifest.md`, and
`legacy_replacement_ledger.md` are only referenced from `tickets/done/`/`stored_artifacts/` (historical
usage) but remain load-bearing via `manifest.json`'s mandatory-doc gate — removing or archiving any of
the six would break `test_mandatory_doc_existence`/`test_doc_header_compliance`
(`tests/integrity/test_doc_guards.py`), which is out of this ticket's scope to touch. All six sit in
`docs/engine/`, matching sibling files (e.g. `docs/engine/architecture.md`, `kernel.md`,
`known_limitations.md`) that already use `status: active / layer: engine / authority: P1 / audience:
developer` (no `tags`, no `last_verified`).

**Group B — `docs/mechanics/content_usage_matrix.md`.** A generated report (per its own text: "This
report is generated dynamically..."), referenced by name in this project's `CLAUDE.md` under the
Mechanics Bible table's "Also:" line. Sibling `docs/mechanics/*.md` chapter files use `status:
authoritative / layer: mechanics / authority: P0 / audience: developer / last_verified: <date>` (e.g.
`01_entity_anatomy.md`). This file is a live report, not a certified law chapter — treating it as
`authoritative` would trigger the `last_verified`-required rule
(`validate_frontmatter.py:188-191`) for a document with no natural "verified as of" date (it's
"generated dynamically"). Recommend `status: active` (not `authoritative`) to avoid forcing a
fabricated `last_verified` date — this needs a decision, see Risks below.

**Group C — three "contract" docs each already carry inline, self-declared metadata that partially
maps onto the frontmatter schema, but not always correctly:**
- `docs/systems/faction_contract.md:3` — `**Status**: AUTHORITATIVE — E53A–E53D complete. Last
  verified: 2026-06-23.` → maps cleanly to `status: authoritative`, `last_verified: 2026-06-23`.
  Sibling `docs/systems/*.md` all use `layer: systems, authority: P1, audience: developer`.
- `docs/world/demographics_contract.md:3,5` — `**Authority:** Certified Level 1 (Authoritative)` /
  `**Layer:** world` → the doc's own text names layer `world` explicitly and correctly (a valid
  `LAYER_VALUES` member); "Certified Level 1 (Authoritative)" is this repo's phrase for
  `status: authoritative` (used identically in the Mechanics Bible chapters per `CLAUDE.md`'s table).
  `status: authoritative` requires `last_verified` — no explicit "verified" date is in the doc body
  itself; nearest dated signal is the referenced tickets (`E52A`–`E52D`, dated 2026-06-19 per ticket
  IDs) or the file's last git-modified date (2026-07-02, from a batch commit `6e25d4f2` "Engine audit
  documentation, simulation quality (in-progress), test refactor and fixing (#19)" that touched all
  three Group C files without adding frontmatter).
- `docs/simulation/domains/party_contract.md:3-4` — `**Authority:** P1` / `**Layer:** social` →
  **the self-declared `Layer: social` is not a valid `LAYER_VALUES` member** (valid set has no
  `"social"`; see Risks). All 19 other `docs/simulation/domains/*.md` sibling contracts use
  `layer: simulation, status: active, authority: P1, audience: agent` (e.g. `adventure_contract.md`).
  The correct frontmatter `layer` value is `simulation`, not the doc's own inline claim.

**Group D — two `docs/simulation_quality/` files**, explicitly named in the ticket's own Scope item
as having a ready sibling template: `docs/simulation_quality/quality_scoring_contract.md` uses
`status: active / layer: simulation / authority: P1 / audience: developer / tags: [...]`.
`event_type_coverage.md:3` self-declares `**Status:** Certified Level 1 — Authoritative` → maps to
`status: authoritative`, and has an explicit `**Last updated:** 2026-07-04` line usable as
`last_verified`. `eval_matrix_results.md` has no such self-declared status/authority — it is a dated
results report (`**Date:** 2026-07-02`) analogous in kind to `content_usage_matrix.md`; `status:
active` (not `authoritative`) avoids forcing an unfounded certification claim.

## Mechanics / Engine Constraints

None of the affected files are Mechanics Bible chapters (`docs/mechanics/01`–`06`) or Engine Contract
files whose *content* this ticket touches — the ticket is documentation-tooling hygiene (frontmatter
metadata only), not a simulation-law or pipeline change. The frontmatter schema itself
(`docs/guidelines/frontmatter_schema.md`) is the only governing "law" in scope, and it is a docs/tooling
contract, not a `docs/mechanics/`/`docs/engine/` simulation contract. `content_usage_matrix.md` is
listed under `docs/mechanics/` but is explicitly a generated report about content resolution state, not
a law chapter — no mechanics chapter number applies to it.

## Parity Ledger Overlap

Two `docs/parity_ledger/infrastructure.yaml` entries cover the tooling this ticket touches indirectly
(neither requires a *behavior* change — this ticket only adds frontmatter to 12 doc files, it does not
change `generate_registry.py` or `validate_frontmatter.py` logic, per the ticket's own UQ-1 assumption
that the hard-error behavior is correct and should not be relaxed):

- **INFRA-180** (`docs/parity_ledger/infrastructure.yaml:1846-1867`) — "Frontmatter validator
  (`tools/validate_frontmatter.py`) correctly enforces the doc schema..." — `status: verified`,
  `priority: P2`, `test_path: tests/tools/test_validate_frontmatter.py` (exists, confirmed). Not P0 —
  no test_path gate blocks this ticket. No code change expected here, so no update needed unless the
  implementer discovers a genuine validator bug while fixing these 12 files.
- **INFRA-183** (`infrastructure.yaml:1900-1913`) — "`docs/REGISTRY.yaml` generated by
  `tools/generate_registry.py`..." — `status: verified`, `priority: P2`, `test_path:
  tests/tools/test_generate_registry.py` (exists, confirmed). Same: no code change, no update
  strictly required, but `v2_evidence` could optionally be refreshed to note "all `docs/` doc files now
  carry frontmatter; `make docs-registry` exits 0" as a factual improvement — a **nice-to-have**, not
  gated.

No P0 parity entries touch this ticket's scope. No parity ledger entry currently documents "`make
docs-registry` exits 0" as a law — this ticket doesn't need to create one since it's restoring an
already-declared invariant (INFRA-183's text implies a working registry pipeline), not introducing new
behavior.

## Prior Work

- **`tickets/done/TCK-20260623-FIX-DOCS-INTEGRITY.md`** — directly created the 6 Group A stub files to
  satisfy `manifest.json`'s mandatory-doc test gate; never added frontmatter to them (out of that
  ticket's scope at the time — frontmatter enforcement on `docs-registry` may not have existed yet, or
  wasn't the focus). `stored_artifacts/TCK-20260623-FIX-DOCS-INTEGRITY/{investigation,plan,test_plan}.md`
  exist but focus on the `tests/docs/`, `tests/integrity/`, `tests/architecture/` failures being fixed,
  not on registry/frontmatter hygiene — no conflicting guidance found.
- **`tickets/done/TCK-20260606-DOCSITE-REGISTRY.md`** — original ticket that built
  `tools/generate_registry.py` and the `make docs-registry` target; established the hard-error-on-
  missing-doc-frontmatter behavior as intentional (39 tests passing at the time).
- **`tickets/done/TCK-20260606-DOCSITE-FM-ARCHIVE.md`** — applied minimal frontmatter to
  `docs/archive/`, `docs/superpowers/specs/`, `docs/specs/` (173+33+4 files) — establishes the
  "minimal, correct frontmatter" precedent this ticket's Scope explicitly follows, but for `archive`
  content-type, not `doc` content-type (different required fields).
  `tools/add_frontmatter_archive.py` and `tools/add_frontmatter_live.py`
  (`docs/guidelines/frontmatter_schema.md`'s "Related Tools" table) exist as **bulk** frontmatter
  appliers — worth checking during implementation whether `add_frontmatter_live.py` can be safely
  re-run (its docstring per the schema doc says "re-run if adding a new directory") to auto-populate
  these 12 rather than hand-editing each; if its defaults don't match the per-file
  self-declared metadata found above (Group B/C/D), hand-editing after a dry-run comparison is safer.
- No other ticket in `tickets/done/` or `stored_artifacts/` targets these exact 12 files' frontmatter.

## Risks and Open Questions

1. **`docs/simulation/domains/party_contract.md`'s self-declared `Layer: social` is invalid against
   the current schema** (`LAYER_VALUES` has no `"social"` — confirmed via
   `tools/validate_frontmatter.py`'s own enum). A pre-existing sibling file,
   `docs/simulation/domains/social_memory_contract.md`, **already has `layer: social` in its real
   frontmatter today and currently fails `validate_frontmatter.py`** (confirmed: running it directly
   returns `FAIL: 1 violation(s)`, exit 1). This file is **not** one of the 12 in scope, and the
   ticket's Out of Scope explicitly excludes "Auditing docs beyond this specific 12-file list." This
   means **AC #3 as literally worded — "`validate_frontmatter.py <each file>` passes for every file
   still under `docs/` after this ticket" — is already false today for a file outside this ticket's
   12-file list**, and will remain false after this ticket ships unless AC #3 is read as scoped only
   to the 12 named files (which the Scope section implies but AC #3's wording doesn't say explicitly).
   **This needs a decision before implementation**: either (a) AC #3 is understood to mean "the 12
   files, not the whole `docs/` tree" (recommended — consistent with Out of Scope), or (b) the
   `social_memory_contract.md` gap must be fixed too, which would be scope creep beyond what the
   ticket authorized. Do not silently reinterpret AC #3 — flag to the ticket owner/planner.
2. **`content_usage_matrix.md` and `eval_matrix_results.md` have no natural `status: authoritative`
   claim in their own text** (unlike the other 10 files, which either explicitly declare "AUTHORITATIVE"
   / "Certified Level 1" or match an obviously-`active` sibling pattern). Recommend `status: active`
   for both — flagged as an assumption, not a certainty, since `content_usage_matrix.md` is listed
   under `docs/mechanics/` (where every other file is `authoritative`). If a reviewer wants
   `authoritative` instead, a `last_verified` date must be fabricated or derived from git-log — no
   in-doc date exists to anchor it honestly for `content_usage_matrix.md` (it says "generated
   dynamically", implying no fixed verification date is meaningful).
3. **`demographics_contract.md`'s and `faction_contract.md`'s exact `last_verified` source is
   ambiguous.** `faction_contract.md` has an explicit in-body date (`2026-06-23`) — low risk.
   `demographics_contract.md` has no explicit "last verified" date in its own text; only ticket-ID-
   embedded dates (2026-06-19) or git-log last-modified (2026-07-02, a bulk commit that likely touched
   many files, not specifically this one's content) are available as proxies. Pick one convention and
   apply consistently — recommend git-log last-modified date as the more defensible "last verified"
   proxy across all `status: authoritative` files in this batch, unless the doc states its own date.
4. **`docs/engine/manifest.json`'s `mandatory_documents` list is the load-bearing reason none of the
   Group A files can be archived.** Any temptation to archive `phase12_entry_package.md`,
   `phase13_retirement_manifest.md`, or `legacy_replacement_ledger.md` as "milestone-era" (per the
   ticket's own Scope suggestion) must first update `manifest.json` and the two tests that read it
   (`tests/integrity/test_doc_guards.py::test_mandatory_doc_existence`,
   `::test_doc_header_compliance`) — out of this ticket's stated scope ("Content changes to any of the
   12 files beyond adding/correcting frontmatter... is an acceptable alternative to adding frontmatter,
   but this requires confirming obsolescence first"). **Investigation finding: none of the 6 are
   obsolete** — all 6 are still referenced as mandatory by `manifest.json`, and 2 of the 6
   (`project_lawbook_m10.md`, `engineering_playbook_m10.md`) are additionally cited by name in
   `CLAUDE.md`/`CONTRIBUTING.md`/a dedicated test. Recommend: add frontmatter to all 6, archive none.
5. **`docs/REGISTRY.yaml` is git-tracked** (last regenerated 2026-07-06 by
   `TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC`). After this ticket's fix, `make docs-registry` will for the
   first time actually complete a clean run and should be re-run once more at the end of
   implementation to pick up the now-frontmatter-bearing 12 entries (their `title`/`status`/`layer`
   etc. fields currently default to `""` in the registry because `collect_docs()` still emits an entry
   with `fm.get(...)` defaults even on error — confirmed at `generate_registry.py:207-209`, the `errors
   .append(...); continue` skips entry creation entirely for docs, unlike tickets — so these 12 are
   **currently entirely absent from `docs/REGISTRY.yaml`**, not present-with-blank-fields). This is
   worth double-checking: search `docs/REGISTRY.yaml` for any of the 12 paths — none should be found
   pre-fix; all 12 should appear post-fix.

## Anti-Drift Hazards

- **Do not touch `docs/engine/manifest.json`'s `required_headers` or the headers themselves** —
  `test_document_structural_compliance` (`tests/docs/test_doc_integrity.py`) and
  `test_doc_header_compliance` (`tests/integrity/test_doc_guards.py`) both regex-match `^##\s+...`
  against full file content; frontmatter insertion is safe (doesn't match `## `), but any accidental
  rewording of an existing `## Purpose` / `## Cutover Authorization` / etc. heading text would silently
  break these two tests independently of this ticket's frontmatter goal.
- **Do not "fix" `docs/simulation/domains/social_memory_contract.md`'s pre-existing `layer: social`
  violation as a drive-by** — it's outside the 12-file list, and the ticket's Out of Scope explicitly
  forbids broader auditing. Flag it, don't silently absorb it into this ticket's diff.
- **Do not relax `tools/generate_registry.py`'s hard-error behavior** (UQ-1 in the ticket explicitly
  assumes the current behavior is correct) — the fix is entirely in the 12 doc files' content, never in
  `collect_docs()`/`generate_registry()`.
- **Do not let `tools/add_frontmatter_live.py` (if used) overwrite the self-declared inline metadata
  found in Group C/D files** (e.g. `faction_contract.md`'s explicit `Last verified: 2026-06-23`, or
  `party_contract.md`'s `Authority: P1`) with a generic bulk default that ignores those signals — a
  blind bulk-apply would likely assign a uniform `status`/`authority` across all 12, contradicting the
  per-file evidence gathered above (e.g. `content_usage_matrix.md` should not become `authoritative`
  just because it sits in `docs/mechanics/`).
- **`tests/tools/test_generate_registry.py` is entirely `tmp_path`-synthetic** — passing it gives no
  signal about the real `docs/` tree. The only way to verify AC #2 (`make docs-registry` exits 0) is to
  actually run `make docs-registry` against the real repo, not just run the unit test suite.

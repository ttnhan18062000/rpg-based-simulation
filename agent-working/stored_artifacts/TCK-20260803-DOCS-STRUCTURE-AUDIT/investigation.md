---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260803-DOCS-STRUCTURE-AUDIT
artifact_type: investigation
tags: [documentation, registry]
---

# Investigation — TCK-20260803-DOCS-STRUCTURE-AUDIT

## Current Behavior

`tools/generate_registry.py` builds `docs/REGISTRY.yaml` from two sources:

- `collect_docs()` (`tools/generate_registry.py:186-238`) walks `root/docs/` via
  `docs_dir.rglob("*.md")` (line 199) — **it only ever globs `.md` files**, so any
  non-`.md` file (`.yaml`, `.mmd`, `.json`) is excluded from the registry by file-type
  alone, independent of `_SKIP_DOC_SUBDIRS` membership. For each matched `.md` file it
  checks whether `parts[0]` (the first path segment under `docs/`) is in
  `_SKIP_DOC_SUBDIRS` (lines 203-205) and skips the whole subtree if so; otherwise it
  extracts frontmatter and emits a `doc` entry.
- `_SKIP_DOC_SUBDIRS = {"archive", "parity_ledger", "scenarios", "entity"}`
  (`tools/generate_registry.py:42`) is the exclusion set this ticket audits.
- `collect_tickets()` (`tools/generate_registry.py:246-311`) is unrelated to this ticket's
  scope (walks `tickets/done/`, not `docs/`).

`tests/tools/test_generate_registry.py::TestRealDocsTree::test_skip_doc_subdirs_exist_on_disk`
(line 539-550) is the existing regression guard added by `TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES`.
It asserts only that every string in `_SKIP_DOC_SUBDIRS` resolves to an existing
`docs/<name>/` directory on disk — it does **not** check whether the directory contains
any `.md` files, so it cannot by itself distinguish "actively excludes real doc content"
(`archive`, `parity_ledger`) from "currently a no-op because the directory holds no `.md`
files" (`scenarios`, `entity`).

### Full per-folder audit table

`find docs -maxdepth 1 -type d` confirms **26** top-level subfolders exist on disk today,
matching the ticket's enumerated name list exactly (the "24" figure in the original request
was stale; 26 is ground truth — same conclusion the ticket's own Assumptions section reached
at scoping time, now independently re-verified). `find docs -type d -empty` returns
**zero results** — no top-level folder, and no subfolder at any depth, is genuinely empty.

| Folder | `.md` count | Total files | In `_SKIP_DOC_SUBDIRS`? | Notes |
|---|---|---|---|---|
| `agent-monitoring` | 2 | 2 | No | README.md, schema.md — small but populated. |
| `ai` | 19 | 20 | No | +1 non-md: `_category_.json` (Docusaurus sidebar metadata). |
| `architecture` | 10 | 11 | No | +1 non-md: `_category_.json`. |
| `archive` | 439 | 452 | **Yes** | +13 non-md (mostly under `archive/specs/` and legacy dirs). Ticket's scoping text cited "146 files" as already-confirmed; actual on-disk count is 439 md / 452 total — a large discrepancy from the scoping-time figure (see Risks). Exclusion status re-verified correct and unchanged per Out of Scope. |
| `audits` | 21 | 21 | No | All `.md`. |
| `cognition` | 4 | 4 | No | All `.md`, all contract docs. |
| `combat` | 3 | 4 | No | +1 non-md: `_category_.json`. |
| `compliance` | 3 | 4 | No | +1 non-md: `_category_.json`. |
| `content` | 3 | 3 | No | All `.md`. |
| `core` | 7 | 8 | No | +1 non-md: `_category_.json`. |
| `engine` | 79 | 82 | No | +3 non-md: `_category_.json`, `manifest.json`, `capability_registry.yaml`. |
| `entity` | 0 | 1 | **Yes** | 1 file: `entity_aspect_relationship_diagram.mmd`. Zero `.md` files, so already excluded from the registry by the `*.md`-only glob regardless of skip-list membership. Actively referenced (see below) — not dead. |
| `guidelines` | 7 | 8 | No | +1 non-md: `_category_.json`. |
| `guides` | 13 | 13 | No | All `.md`. |
| `mechanics` | 14 | 15 | No | +1 non-md: `_category_.json`. |
| `observability` | 8 | 24 | No | +16 non-md: `_category_.json` + 15 baseline JSON files under `observability/baselines/` (performance baseline snapshots, actively used by perf tooling — not dead). |
| `parity_ledger` | 0 | 10 | **Yes** | 9 `.yaml` subsystem ledgers + `schema.json`. Zero `.md`, so skip-list membership is a genuine, load-bearing exclusion (would be irrelevant anyway given the `*.md`-only glob, but membership is correct/intentional per ticket's own confirmation). |
| `performance` | 3 | 4 | No | +1 non-md: `_category_.json`. |
| `plans` | 52 | 52 | No | All `.md`. |
| `scenarios` | 0 | 5 | **Yes** | 5 `.yaml` files under `scenarios/phase1/`. Zero `.md` files — same no-op situation as `entity`. Actively referenced (see below) — not dead. |
| `simulation` | 27 | 27 | No | All `.md`. |
| `simulation_quality` | 6 | 6 | No | All `.md`. |
| `strategy` | 8 | 9 | No | +1 non-md: `_category_.json`. |
| `systems` | 11 | 12 | No | +1 non-md: `_category_.json`. |
| `testing` | 10 | 11 | No | +1 non-md: `_category_.json`. |
| `world` | 11 | 11 | No | All `.md`. |

No genuinely empty folder (zero files at any depth) exists anywhere under `docs/`. No
top-level item is duplicate-purpose or misnamed relative to its contents. The non-`.md`
files found (`_category_.json` Docusaurus sidebar metadata, `docs/engine/manifest.json` +
`capability_registry.yaml`, `docs/observability/baselines/*.json` perf baselines) are all
tooling-consumed, not orphaned content.

### `docs/scenarios/` and `docs/entity/` — reference check

- `docs/entity/entity_aspect_relationship_diagram.mmd` is actively referenced by
  `docs/strategy/world_capability_design.md` and `docs/guides/diagram_index.md` (diagram
  links), plus cited in multiple `tickets/done/` and `stored_artifacts/` files. **Not dead.**
- `docs/scenarios/phase1/*.yaml` (5 files) are actively loaded by
  `tests/unit/strategic/test_scenario_runner.py` (hardcoded `spec_path =
  "docs/scenarios/phase1/scenario1_growth.yaml"`, lines 8/20) via `ScenarioRunner`. **Not
  dead** — a live test dependency.

Both directories exist on disk, contain zero `.md` files, and hold actively-used non-`.md`
content. Given `collect_docs()`'s `*.md`-only glob, their `_SKIP_DOC_SUBDIRS` membership is
a currently-inert no-op — removing them would change nothing about today's registry output.
The precedent set by `TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES` (which removed `superpowers`/
`specs` from the same set) does **not** transfer directly: that removal was justified because
those two directories **did not exist on disk at all**. `scenarios` and `entity` exist,
contain real active content, and pass `test_skip_doc_subdirs_exist_on_disk` today — they are
a different case (inert-but-real vs. fully dead).

### `docs/specs/` vs. `docs/superpowers/specs/` naming question

No live collision exists. `docs/specs/` (4 files) and `docs/superpowers/specs/` (33 files)
were both already consolidated into `docs/archive/specs/` by the closed
`TCK-20260616-DOCS-ARCHIVE-SPECS-PERF-PLANS` (confirmed: `docs/archive/specs/` currently
holds 37 files = 4 + 33). Neither `docs/specs/` nor `docs/superpowers/` exists as a top-level
`docs/` subfolder today; only `docs/archive/specs/` does, nested one level deeper. The
apparent collision `search_docs` surfaced originates from `TCK-20260606-DOCSITE-FM-ARCHIVE`,
which predates the July consolidation and is describing pre-consolidation state — not a
currently-live ambiguity. See Risks for one adjacent stale-reference observation this
surfaced (out of scope to fix here).

## Mechanics / Engine Constraints

None — this is pure doc-tooling (a registry-generation script and its directory-exclusion
list). No coupling to `docs/mechanics/` simulation laws or `docs/engine/` pipeline contracts.

## Docs Requiring Update

None.

## Parity Ledger Overlap

None. `docs/parity_ledger/infrastructure.yaml` contains INFRA-183 (`generate_registry.py`'s
output shape) and INFRA-264 (CI drift-detection backstop via `--check`) as the only entries
touching this code area, and both remain accurate under this audit's "no functional change"
conclusion. Neither is P0, so no `test_path` gate is triggered by this ticket regardless.

## Prior Work

- **`TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES`** (hotfix, done) — direct precedent. Removed
  `superpowers`/`specs` from `_SKIP_DOC_SUBDIRS` because neither directory existed on disk
  at all, and added `test_skip_doc_subdirs_exist_on_disk`. Its own Implementation Notes state
  the remaining four entries (`archive`, `parity_ledger`, `scenarios`, `entity`) were
  "[c]onfirmed on disk... all exist as real `docs/` subdirectories" — i.e., that ticket
  already validated existence, but not content-relevance, for `scenarios`/`entity`. This
  ticket closes that gap.
- **`TCK-20260606-DOCSITE-FM-ARCHIVE`** (done) — applied frontmatter to `docs/archive/`,
  `docs/superpowers/specs/`, and `docs/specs/` (272 files total) while those were still
  three separate locations, before the July consolidation. Baseline confirmed, not reopened.
- **`TCK-20260616-DOCS-ARCHIVE-SPECS-PERF-PLANS`** (done) — consolidated `docs/specs/` and
  (per its own text, referencing `docs/superpowers/specs/`) into `docs/archive/specs/`,
  resolving the specs/superpowers question this ticket was asked to re-check.
- **`TCK-20260514-DOCS-REORG`** — established the current nested `docs/` hierarchy; not
  independently re-read in depth since this audit's scope is the *current* on-disk state,
  which was gathered directly via `find`, not reconstructed from that ticket's history.

## Risks and Open Questions

- **Why "Docs Requiring Update" is None (rationale).** No documented drift was found:
  `_SKIP_DOC_SUBDIRS`'s four entries are all real, existing `docs/` directories; the two
  currently-inert entries (`scenarios`, `entity`) hold actively referenced content rather
  than being dead, so removing them is not warranted; no folder qualifies for deletion; and
  no other doc (`docs/ai/README.md`, `docs/README.md`, `docs/parity_ledger/infrastructure.yaml`)
  contains a stale folder-count or folder-list claim that this audit's findings would
  invalidate. Because the recommended outcome is "no functional change to `_SKIP_DOC_SUBDIRS`,"
  `docs/parity_ledger/infrastructure.yaml`'s INFRA-183/INFRA-264 entries (which describe
  `generate_registry.py`'s current behavior) do not need re-verification either — nothing
  about that behavior is changing. If the Plan phase instead elects to add an in-code comment
  next to `_SKIP_DOC_SUBDIRS` clarifying the `scenarios`/`entity` no-op-but-retained rationale
  (a code comment in `tools/generate_registry.py`, not a `docs/` file), the "Docs Requiring
  Update" verdict above is unaffected — a code comment is not a `docs/` path.
- **Archive file-count discrepancy (informational, not scope-invalidating).** The ticket's
  scoping text states `archive (146 files)` was "already confirmed correct/out of question
  at scoping time." Direct re-verification (`find docs/archive -type f | wc -l`) returns
  **452** total files (439 `.md`), not 146. Since `Out of Scope` explicitly excludes changing
  `docs/archive/`'s exclusion status, this does not change the recommended outcome — but the
  "146" figure appears to be stale or was measuring something other than total on-disk file
  count (possibly a partial count from an earlier ticket, e.g. the FM-ARCHIVE ticket's
  173-file archive-only baseline before later consolidations added more). Recording the
  correct current count (452 total / 439 `.md`) here for the record; no action taken.
- **Deletion safety was evaluated and found not to apply.** No folder in `docs/` is
  genuinely empty at any depth (`find docs -type d -empty` = no results), so the "is
  removing/renaming an empty or misconfigured folder safe" question raised in the ticket's
  own scoping is moot for this run — there is nothing to safely (or unsafely) delete. Stated
  explicitly here per AC #3's requirement to state this rather than silently doing nothing.
- **Adjacent stale reference (out of scope, flagged for a future ticket).**
  `tools/validate_frontmatter.py`'s `detect_content_type()` (around line 123-127) still
  checks whether the first path segment under `docs/` is `"archive"`, `"superpowers"`, or
  `"specs"` to classify a file as archive-type. Since `docs/specs/` and `docs/superpowers/`
  no longer exist as top-level `docs/` subfolders (both folded into `docs/archive/specs/` by
  `TCK-20260616-DOCS-ARCHIVE-SPECS-PERF-PLANS`), the `"superpowers"` and `"specs"` branches
  of that check are now unreachable dead code — a file under `docs/archive/specs/` is already
  correctly classified via the `"archive"` branch since `archive` is the first path segment,
  not `specs`. This is a different file (`tools/validate_frontmatter.py`) and a different
  function than this ticket's `Related Code Areas` (`tools/generate_registry.py`'s
  `_SKIP_DOC_SUBDIRS`/`collect_docs()`), so fixing it here would be scope creep. Flagging for
  a future small hotfix ticket, following the exact pattern
  `TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES` used for the equivalent dead entries in
  `generate_registry.py`.
- **No open question blocks implementation.** Both reference-check sub-questions the ticket
  posed (is `docs/entity/`'s `.mmd` file used elsewhere? is `docs/scenarios/phase1/`'s YAML
  used elsewhere?) were answered definitively via `grep` — both are actively referenced, so
  the "keep, documented" branch of the ticket's own decision tree applies cleanly with no
  ambiguity left for the Plan phase to resolve.

## Anti-Drift Hazards

- **Do not audit or edit document prose content.** This ticket is structure/naming/existence
  only, per its own scope statement. No individual file's body text was read for accuracy,
  freshness, or correctness in this investigation, and none should be modified during
  Implementation — only `_SKIP_DOC_SUBDIRS` (if the Plan phase elects to add a clarifying
  comment) and, only if a genuinely-empty folder is later found, a `git rm`.
- **Do not fix `tools/validate_frontmatter.py`'s dead `"superpowers"`/`"specs"` check as part
  of this ticket** — it is a real, adjacent finding but belongs to a separate, narrowly
  scoped follow-up ticket (see Risks), not this one's `Related Code Areas`.
- **Do not delete `docs/scenarios/` or `docs/entity/`** — both are confirmed non-dead via
  direct reference checks (a live test dependency and live doc cross-references,
  respectively). Any implementation that removes either directory or its
  `_SKIP_DOC_SUBDIRS` entry without re-confirming those references would silently break
  `tests/unit/strategic/test_scenario_runner.py` and orphan two doc cross-references.
- **Do not touch `docs/archive/` or `docs/parity_ledger/`'s exclusion status** — both are
  explicitly Out of Scope per the ticket, confirmed correct in this investigation, and any
  change to either would exceed this ticket's mandate.
- **Do not widen `collect_docs()`'s `*.md`-only `rglob` to index other file types** — the
  ticket explicitly calls this out as a separate, larger, out-of-scope decision, even though
  this investigation's per-folder table surfaces several non-`.md` files (`_category_.json`,
  baseline JSONs, `capability_registry.yaml`) that a wider glob would newly pick up.

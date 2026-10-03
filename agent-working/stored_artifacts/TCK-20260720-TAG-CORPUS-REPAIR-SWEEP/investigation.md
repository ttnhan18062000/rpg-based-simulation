---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260720-TAG-CORPUS-REPAIR-SWEEP
artifact_type: investigation
tags: [tagging, data-quality, reporting]
---

# Investigation — TCK-20260720-TAG-CORPUS-REPAIR-SWEEP

## Current Behavior

**`tools/validate_frontmatter.py`** (351 lines, read in full) is the enforcement path today, and it
is forward-only and directory-scoped, not corpus-wide:

- `extract_frontmatter(text)` (`tools/validate_frontmatter.py:69-109`) is the single frontmatter
  parser: returns `None` if no `---`-delimited block exists at all, raises `ValueError` on an
  unparseable line (no `:`, empty key, unclosed `[`), otherwise a `dict` of raw string/list values.
  It does not distinguish "no frontmatter" from "frontmatter with no `tags:` key" — both simply
  produce a dict lacking a `"tags"` key (or `None` for the no-block case). Confirmed directly
  against the two fixtures named in this ticket's AC #3 (see Test Plan's Regression Surface).
- `_check_tags(filepath, fm, registry)` (`tools/validate_frontmatter.py:152-181`) is the only place
  tag violations are currently computed, and it is **date-gated**: it reads `fm.get("ticket_id")`,
  computes `_ticket_id_effective_date()`, and returns `[]` immediately (no checking at all) if the
  embedded date is missing or `< TAG_TAXONOMY_EFFECTIVE_DATE` ("20260704"). This is precisely the
  cutoff this ticket's sweep must bypass — the sweep needs the same two checks (`canonical_form_violation`,
  registry membership) but applied unconditionally, plus a third check `_check_tags` does not
  perform at all (`invalid_category`, see below).
- `validate_directory()` (`tools/validate_frontmatter.py:284-292`) walks one directory via
  `path.rglob("*.md")` and returns `{path: [errors]}`. It is invoked today only against
  content-type-homogeneous roots (a single `tickets/` or `stored_artifacts/` tree per CLI
  invocation) — never across all four corpus roots (`tickets/done`, `tickets/inprogress`,
  `tickets/todos`, `stored_artifacts`) in one pass, which is exactly the gap this ticket closes.

**`tools/tag_report.py`** (258 lines, read in full) is the closest existing precedent for a
corpus-walk + tag-row report, but it is intentionally narrower than what this ticket needs:

- `collect_completed_tickets(root)` (`tools/tag_report.py:77-130`) only walks `tickets/done/`
  (`root / "tickets" / "done"`, `.rglob("*.md")`), skips `SEQUENCE.md` by filename
  (`tools/tag_report.py:97-100`), and — critically — applies the exact same
  `pre_taxonomy_or_legacy_ticket_id` date-gate this ticket's sweep must NOT apply
  (`tools/tag_report.py:115-120`, `embedded_date < TAG_TAXONOMY_EFFECTIVE_DATE` skip). It also skips
  any file with no/empty `tags` (`tools/tag_report.py:122-126`) — this behavior (zero rows, not a
  crash) is exactly what this ticket's AC #3 wants preserved.
- `categorize_tag(tag, registry)` (`tools/tag_report.py:55-69`) returns a *display* category
  (`"phase-milestone"`, the registry's recorded category, or `"unclassified"`) — a different
  question from this ticket's `invalid_category` *violation* flag. `categorize_tag` never checks
  the recorded category against `category_values()`; it only checks registry presence. This ticket's
  sweep needs a new check `tag_report.py` does not have.
- `build_tag_rows()` (`tools/tag_report.py:138-164`) aggregates *counts* per tag across all included
  tickets (one row per unique tag) — a different output shape from this ticket's required
  `(file, tag, issue)` row-per-violation-per-file shape. The sweep is a new function, not a
  parameterization of `build_tag_rows`.

**`tools/tag_registry.py`** (432 lines, read in full) is the flagging single source of truth this
ticket's Scope names explicitly (`canonical_form_violation`, `is_tag_registered`,
`check_tags_registered`, `load_registry`), plus the newly-landed category surface from
`TCK-20260720-TAG-CATEGORY-REGISTRY`:

- `load_registry(root)` (`tools/tag_registry.py:156-179`) → `{tag: {"tag", "category", "added_date",
  "note", ["triggers_skill"]}}`. **This is the schema answer the open question below depends on**:
  every registered tag's entry carries its own `"category"` field, written once at `add_tag()` time
  and never updated (append-only). There is no per-file/per-frontmatter-tag category — category is
  a property of the tag's *registration*, looked up by tag string, not stored redundantly on every
  ticket that uses the tag.
- `is_tag_registered(tag, registry)` (`tools/tag_registry.py:182-184`) → `tag in registry or
  is_phase_milestone_tag(tag)`. This is the "is it usable at all" check — it does not distinguish a
  registered-with-valid-category tag from a registered-with-since-invalidated-category tag; both
  return `True`.
- `check_tags_registered(tags, root)` (`tools/tag_registry.py:187-196`) returns only the unregistered
  subset — useful for the `unregistered` row case directly, but says nothing about category
  validity for tags that pass it.
- `category_values(root)` (`tools/tag_registry.py:347-352`, landed by `TCK-20260720-TAG-CATEGORY-REGISTRY`)
  → live `frozenset[str]` read from `registries/tag_category_registry.jsonl`. This is the "current
  valid-category set" the ticket's `invalid_category` case (AC #2/#46 body) refers to.
- `add_tag()` (`tools/tag_registry.py:199-245`) validates `category not in category_values()` **at
  write time** and raises — so under normal registry operation, every entry's recorded `category` is
  guaranteed valid *as of the moment it was added*. `invalid_category` as a sweep check is about
  **drift since then**: because `registries/tag_category_registry.jsonl` is itself append-only
  (categories are never removed, per its own module docstring and `add_category()`'s "cannot be
  re-added or changed" contract), there is currently no code path in this repo that would cause a
  previously-valid recorded category to become invalid later. Confirmed empirically (see below) —
  zero real hits today, exactly as the ticket's Assumptions/Open Questions anticipated.

**Registry data verified directly** (`registries/tag_registry.jsonl`, 53 lines;
`registries/tag_category_registry.jsonl`, 4 lines — `subsystem-topic`, `process-skill-signal`,
`quality-attribute`, `meta-process`; `phase-milestone` deliberately never seeded there, per both
files' own docstrings):

```
$ python3 -c "... categories used in tag_registry.jsonl vs category_values() ..."
valid categories: ['meta-process', 'process-skill-signal', 'quality-attribute', 'subsystem-topic']
categories used in tag_registry.jsonl: ['meta-process', 'process-skill-signal', 'quality-attribute', 'subsystem-topic']
used but not valid: []
```

No literal `phase-N` tag is registered in `tag_registry.jsonl` today (checked directly), and no
entry is missing its `category` field (checked directly) — both would be edge cases the sweep's
`invalid_category` logic must handle defensively even though neither occurs in the live corpus now.

## Mechanics / Engine Constraints

None. This is agent/workflow tooling (`layer: ai`, matching the ticket's own frontmatter and
`docs/guidelines/tag_taxonomy.md`'s Meta-Process disambiguation rule — `layer: ai` in this repo means
the Claude agent-orchestration system, not gameplay cognition), not simulation logic. No
`docs/mechanics/` or `docs/engine/` chapter constrains this work.

## Parity Ledger Overlap

None. Searched all 8 `docs/parity_ledger/*.yaml` files for `tag`/`registry`/`frontmatter` — every
hit is an unrelated gameplay concept that happens to contain the substring "registry" (e.g.
`quest_registry`, `GroupRegistry`, terrain-cost registry, `test_registry_bridge`). No parity ledger
entry concerns the ticket-tagging/frontmatter-registry system at all; this system is pure
repository/workflow tooling, entirely outside the Mechanics Bible's and parity ledger's scope (the
ledger tracks legacy-vs-V2 simulation-behavior parity, not agent-tooling behavior). No entry needs
updating as part of this ticket, and none should be added — this precedent is consistent with
`TCK-20260706-TAG-REPORT-TOOL`'s own Completion Summary ("no parity-ledger entry needed
(agent-orchestration/developer tooling only)").

## Prior Work

Read via `search_docs` (returned as top warm-start candidates) and directly:

- **`TCK-20260706-TAG-REPORT-TOOL`** (`tickets/done/`, hotfix, no staging artifacts): built
  `tools/tag_report.py`'s corpus-walk/skip-rule/frontmatter-reuse pattern this ticket extends. Its
  own Completion Summary confirms "no parity-ledger entry needed" for this subsystem — direct
  precedent for this ticket's own Parity Ledger Overlap finding above.
- **`TCK-20260706-TAG-REGISTRY-DATA`** (`stored_artifacts/`, `tickets/done/`): built the append-only
  `registries/tag_registry.jsonl` (then at `docs/guidelines/`) and the hard-allowlist enforcement in
  `validate_frontmatter.py`. Its investigation.md documents the registry entry schema
  (`{"tag", "category", "added_date", "note"}`) exactly as read directly from
  `tools/tag_registry.py:231-236` above — confirms the schema finding is not a one-off read but
  matches this tool's own design history.
- **`TCK-20260719-TAG-COLLISION-DEDUP`** (`stored_artifacts/`, `tickets/done/`): ran a full-corpus
  (`tickets/{done,inprogress,todos}/` + `stored_artifacts/`) ad-hoc scan for literal-spelling
  duplicate tags — explicitly **not** checked into `tools/`, a one-time manual-fix action. Useful as
  sizing precedent (found 1352 distinct tags as of 2026-07-19) but not reusable code; this ticket's
  sweep is the first *reusable, checked-in* tool to walk all four corpus roots.
- **`TCK-20260720-TAG-CATEGORY-REGISTRY`** (`stored_artifacts/`, `tickets/done/`): landed
  `category_values()`, `load_category_registry()`, `add_category()` — the exact machinery this
  ticket's `invalid_category` flag depends on. Its own investigation.md's precedent (resolving an
  explicit open design question during Investigate rather than deferring it) is the direct template
  followed by this document's own resolution below.
- **`TCK-20260720-TAG-REGISTRY-RELOCATE`** (`stored_artifacts/`, `tickets/done/`): moved
  `docs/guidelines/tag_registry.jsonl` → `registries/tag_registry.jsonl` (and the category registry
  alongside it). Confirmed landed: both files live under `registries/` today. **Gap found**: this
  ticket's own "Related Docs" list and `docs/guides/ticket_reporting.md`'s Pillar 1 section (line 31:
  `[registries/tag_registry.jsonl](../guidelines/tag_registry.jsonl)`) still reference the old
  `docs/guidelines/tag_registry.jsonl` path/link target — stale since the relocation landed. Flagged
  under Anti-Drift Hazards below; the new sweep subsection this ticket adds to
  `ticket_reporting.md` must use the correct `registries/` path, and fixing the pre-existing stale
  link is a reasonable adjacent touch-up if the implementer is already editing that file (not
  required by this ticket's AC, but cheap to fix while present).
- **`TCK-20260706-TICKET-REPORTING-GUIDE`**: established the `docs/guides/ticket_reporting.md`
  "Pillar" documentation pattern this ticket's AC #6 must follow for the new sweep subsection.
- No `stored_artifacts/TCK-20260706-TAG-REPORT-TOOL/` exists (hotfix tier, no staging artifacts per
  project convention — confirmed, not a gap).

`docs/REGISTRY.yaml` exists; the above tickets were located both via `search_docs` (semantic) and by
following this ticket's own "Related Tickets" list (all 8 entries read).

## Risks and Open Questions

**RESOLVED — `invalid_category` operational definition (this ticket's AC #4/#46 mandatory
resolution):**

Tag entries do **not** carry an explicit category field per-usage on a ticket/artifact's own
`tags:` frontmatter list — `tags:` is just a flat list of tag strings (`extract_frontmatter()`
parses it as `list[str]`, nothing more). "Category" is entirely a property of the tag's
*registration record* in `registries/tag_registry.jsonl`, keyed by tag string
(`load_registry()[tag]["category"]`), set once by `add_tag()` and never updated (append-only).

Therefore, for a given `tag` found in a file's `tags:` list, against `registry = load_registry()`
and `valid_categories = category_values()`:

```
if not is_tag_registered(tag, registry):
    emit (file, tag, "unregistered")
elif tag in registry:                                    # registered via a literal entry (not phase-N)
    recorded_category = registry[tag].get("category")    # defensive .get(), see edge case below
    if recorded_category not in valid_categories:
        emit (file, tag, "invalid_category")

if canonical_form_violation(tag) is not None:
    emit (file, tag, "non_canonical_form")               # independent of the two checks above
```

Key properties of this definition, all directly traceable to code read above:

1. **`unregistered` and `invalid_category` are mutually exclusive per tag.** `unregistered` fires
   only when `tag` has no registry entry AND is not a canonical `phase-N` tag (`is_tag_registered`'s
   own definition). `invalid_category` fires only when `tag in registry` — a strictly narrower
   condition than `is_tag_registered` (which also returns `True` for phase-N tags that have no
   registry entry and thus no category to check at all). A tag can never get both in the same sweep
   pass.
2. **`phase-N` tags are exempt from `invalid_category`, by construction, not by a special case.**
   No literal `phase-N` tag is registered today (verified directly), and even if one were, phase
   tags have no category concept (`is_phase_milestone_tag` bypasses the registry entirely in
   `categorize_tag`/`is_tag_registered`) — but if a literal `phase-N` entry *did* exist in the
   registry with an invalid category, this definition would still (correctly) flag it via the
   `tag in registry` branch, since registry presence, not phase-pattern-matching, is what the
   `invalid_category` check keys on. This is a deliberate, code-traceable edge case for the
   implementer to be aware of, not a contradiction.
3. **`non_canonical_form` is a fully independent, third dimension** — checked against the tag's own
   spelling via `canonical_form_violation(tag)` regardless of registration or category state. A tag
   can accumulate `invalid_category` + `non_canonical_form` simultaneously (registered under a
   since-invalidated category AND spelled non-canonically), or `unregistered` +
   `non_canonical_form` simultaneously, but never `unregistered` + `invalid_category` together —
   this matches AC #46's "a tag with multiple issues produces multiple rows" language exactly.
4. **Defensive `.get("category")` matters even though no current entry lacks it** (verified: 0 of 53
   entries missing `category`) — a missing/`None` category should be treated as `invalid_category`
   (since `None not in valid_categories`), not as a `KeyError` crash, per AC #3's "no crash on
   missing data" spirit extended to registry-side malformation, not just file-side.
5. **Zero real hits confirmed today** (registries verified directly above) — this is expected, not a
   bug in the check: `add_category()`'s append-only invariant means no category can currently become
   invalid after a tag was registered under it. The check exists for future drift protection (e.g.
   a hand-edited `tag_registry.jsonl` bypassing `add_tag()`'s validation, or a future policy change
   that deprecates a category without physically removing rows) — the New Tests Required section of
   `test_plan.md` must therefore construct a synthetic fixture (in-memory registry + a
   deliberately-mismatched category-values set) to exercise this branch at all, since the real
   corpus currently offers no positive example.

**Other open items, none blocking:**

- **Performance at ~3954 files.** `tickets/done` (~1199), `tickets/todos` (~20, 4 `SEQUENCE.md`-bearing
  subfolders), `tickets/inprogress` (3 today, will fluctuate), `stored_artifacts` (~2858 `.md` files
  across 853 directories — some directory names are not `TCK-` ticket IDs at all, e.g. UUID-named or
  `D145C3D0-MILESTONE-B`-style folders; the sweep does not need ticket-ID-shaped folder names since
  it walks `stored_artifacts/**/*.md` directly by glob, per AC #1, not by joining through a ticket
  list). Pure Python file-read + regex-based frontmatter parse at this scale is expected to run in
  low single-digit seconds based on `tag_report.py`'s existing ~1200-file `tickets/done/` walk
  precedent; not flagged as a real performance risk, but the CLI should still print progress/summary
  counts (scanned/skipped/flagged) rather than only a final row dump, since a silent multi-thousand
  file scan is a poor debugging experience if something goes wrong mid-run.
- **`stored_artifacts` content type mismatch is not a blocker.** `detect_content_type()` would infer
  `"artifact"` for every `stored_artifacts/**/*.md` file, but the sweep does not call
  `validate_file()`/`_validate_artifact()` at all — it only needs `extract_frontmatter()` (path-
  agnostic) plus the tag-list-specific checks. Full schema validation (required fields, `status`
  enum, etc.) is explicitly out of this ticket's scope (AC only asks for tag/category rows). Do not
  scope-creep into full-schema violations for non-`investigation.md`/`plan.md`/`test_plan.md` files
  in `stored_artifacts/` (many of the 20+ non-standard filenames found, e.g. `design.md`,
  `code_review.md`, `architecture_audit.md`, are not required by `validate_frontmatter.py`'s
  `_validate_artifact` schema either — same principle already applies there).
- **`docs/guides/ticket_reporting.md`'s existing Pillar 1 section references the pre-relocation
  registry path** (see Prior Work above) — a pre-existing doc-drift issue, not caused by this
  ticket, but adjacent to the new subsection this ticket must add.

## Anti-Drift Hazards

- **Do not add a second frontmatter parser.** `extract_frontmatter()` is the sole parser per
  explicit Scope/Out-of-Scope instruction; a fresh regex or YAML-library parse, even a "just for
  this edge case" one, would violate that and risk diverging from `validate_frontmatter.py`'s
  established behavior (e.g. its specific handling of inline `[a, b, c]` lists, quote-stripping,
  comment-skipping).
- **Do not re-derive canonical-form or registry-membership rules.** `canonical_form_violation`,
  `is_tag_registered`, `check_tags_registered`, `load_registry`, `category_values` must be imported
  from `tag_registry.py`, not reimplemented or copy-pasted — this is both explicit Scope and an
  existing repo-wide convention (`tag_report.py` and `validate_frontmatter.py` both already do this;
  see both modules' docstrings on avoiding "second copy" duplication).
- **Do not apply the `TAG_TAXONOMY_EFFECTIVE_DATE`/`pre_taxonomy_or_legacy_ticket_id` date-gate
  anywhere in the new sweep path.** This is the entire point of the ticket (AC #1) — it would be an
  easy, silent mistake to copy `collect_completed_tickets()`'s skip-rule structure wholesale
  (tempting, since 3 of its 4 skip rules — `sequence_index_file`,
  `unparseable_frontmatter`/`no_frontmatter_legacy_format`, `no_tags` — are exactly right to reuse)
  and forget to drop the 4th (date) rule specifically.
- **Do not add a `--fix` flag or any write path.** Explicit Out of Scope and AC #4 (git-diff-clean
  before/after). The function signature itself should make writes structurally impossible (no
  `Path.write_text` call anywhere in the new module), not just "unused today."
- **Do not silently change `tag_report.py`'s or `validate_frontmatter.py`'s existing behavior while
  extending shared code.** Both are actively used elsewhere (`tag_report.py` by `make tag-report`;
  `validate_frontmatter.py` by the Verify gate's `frontmatter_valid` condition and pre-commit-style
  checks). If any shared helper needs a signature change to support the new no-cutoff mode, prefer
  a new optional parameter with the old default preserved (mirrors this codebase's own established
  pattern, e.g. `_check_tags(filepath, fm, registry=None)`'s optional-registry design), not a
  behavior change to the default path. Confirm both modules' existing test suites still pass
  unmodified (see test_plan.md's Regression Surface).
- **`docs/guides/ticket_reporting.md`'s new subsection must link to `registries/tag_registry.jsonl`
  and `registries/tag_category_registry.jsonl`, not the stale `docs/guidelines/` path** already
  present elsewhere in that same file (see Prior Work) — do not copy-paste the stale link pattern
  into new prose.
- **Do not scope-creep into fixing any of the flagged historical violations.** Report-only is the
  entire mandate; even an "obviously right" one-line fix (e.g. a single non-canonical tag spotted
  during manual testing) belongs to a human-reviewed follow-up ticket, per Out of Scope.

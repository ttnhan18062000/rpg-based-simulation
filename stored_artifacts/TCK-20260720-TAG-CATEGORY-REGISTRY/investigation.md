---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260720-TAG-CATEGORY-REGISTRY
artifact_type: investigation
tags: [tagging, frontmatter, taxonomy]
---

# Investigation — TCK-20260720-TAG-CATEGORY-REGISTRY

## Current Behavior

**`tools/tag_registry.py`** (343 lines, read in full) is the sole place `ALL_CATEGORIES` /
`ADDABLE_CATEGORIES` are defined, and the sole place they are actually consumed as Python set
literals today:

- `ALL_CATEGORIES` (lines 66-72): a hardcoded `set` of the 5 taxonomy categories
  (`subsystem-topic`, `phase-milestone`, `process-skill-signal`, `quality-attribute`,
  `meta-process`).
- `ADDABLE_CATEGORIES` (line 76): `ALL_CATEGORIES - {"phase-milestone"}` — the 4 categories a tag
  can actually be registered under.
- `add_tag()` (lines 214-260): validates `category not in ADDABLE_CATEGORIES` at line 233, raising
  `ValueError(f"category must be one of {sorted(ADDABLE_CATEGORIES)}, got {category!r}")`.
- `main()`'s argparse `add` subcommand (line 297): `choices=sorted(ADDABLE_CATEGORIES)`.
- `is_phase_milestone_tag()` (lines 105-107): a **separate, orthogonal** exemption mechanism — a
  regex (`_PHASE_CANONICAL_RE = r"^phase-\d+$"`) that recognizes any `phase-N` tag as
  `phase-milestone` without ever looking it up in a registry or a category set. This is how
  `phase-milestone` membership is actually enforced end-to-end today (`is_tag_registered()` line
  197-199 OR's this in), not via `ALL_CATEGORIES` containing the string.

**`tools/layer_registry.py`** (194 lines, read in full) is the direct template named in the
ticket's own module docstring ("mirrors `tools/tag_registry.py`'s design... read that module first
if this one is unclear, it is the direct template" — layer_registry.py:5-7). Its shape:
`canonical_form_violation()` → `registry_path()`/`load_registry()` (raises on duplicate) →
`add_layer(layer, note, root=None)` (lines 112-141, raises `ValueError` on non-canonical form or
duplicate, writes one `{"layer", "added_date", "note"}` JSON line, `sort_keys=True`) →
`layer_values(root=None)` (lines 144-149, `return frozenset(load_registry(root).keys())` — **no
caching**, no filtering, just every key currently in the file) → CLI `add`/`list` subcommands.
Critically, **layer entries have no `category`-equivalent field at all** — `Layer` "*is* the
subsystem-topic dimension itself" (layer_registry.py:17-19), so there is no addable/non-addable
split to mirror for `add_category()`'s entry shape.

**`tools/validate_frontmatter.py`** (351 lines, read in full) already demonstrates the exact
consumption pattern this ticket wants for categories: line 38 imports `layer_values as
_layer_values` from `layer_registry`, line 53 computes `LAYER_VALUES = _layer_values()` at
module-import time (a live, uncached read, re-evaluated on every process start). **However**,
`validate_frontmatter.py` does not reference tag *categories* anywhere — `_check_tags()` (lines
152-181) only calls `canonical_form_violation()` and `is_tag_registered()`, neither of which takes
or checks a category. This means the ticket's Related Code Areas listing of
`tools/validate_frontmatter.py` as a "hardcoded-category consumer" does not match current code —
see Risks/Gaps below.

**`tools/ticket_stats_report.py`** (304 lines, read in full) contains **zero** references to tag
categories, `ADDABLE_CATEGORIES`, or any category literal — it reports Tier/Type/Priority/Layer
distribution over `tickets/done/`, not tags. Listed in Related Code Areas but has nothing to
change. Confirmed gap (see Risks/Gaps).

**`tools/tag_report.py`** (259 lines, read in full): `categorize_tag()` (lines 55-69) derives a
tag's category by direct registry lookup (`registry.get(tag)["category"]`), falling back to the
literal string `"phase-milestone"` when `is_phase_milestone_tag(tag)` is true, or `"unclassified"`
otherwise. It does **not** import or reference `ALL_CATEGORIES`/`ADDABLE_CATEGORIES` — no set
literal to replace here either; it already reads categories live from the registry per-tag. The
ticket's own Out of Scope section correctly excludes `tag_report.py`'s prose/string-equality
categorization from the "live-import" rework, but Related Code Areas still lists it (reasonable —
it is a categorization *consumer* worth checking, just not one needing an edit).

**`tools/agent-monitoring/generate_retro.py`** (imports `categorize_tag` from `tag_report`, used
at lines 374-378): does two plain string-equality checks (`category == "subsystem-topic"`,
`category == "process-skill-signal"`) — no set literal, correctly excluded from rework scope per
the ticket's own Out of Scope bullet.

**`reviews/src_export.py` / `reviews/test_export.py`**: grepping for `ADDABLE_CATEGORIES`/
`ALL_CATEGORIES` also hits these two files (lines ~204284-204438 and ~56891-57039 respectively).
These are generated code-review export snapshots (concatenated source/test dumps for review
tooling), not real importable source — they are not part of the "7 non-test files" the ticket's
Request Summary refers to and need no edit; they will pick up the change automatically the next
time they are regenerated.

**Tests** — `tests/tools/test_tag_registry.py` (311 lines, read in full) imports `ADDABLE_CATEGORIES`
and `ALL_CATEGORIES` directly (lines 15-16) and asserts on them in
`test_add_tag_rejects_phase_milestone_category` (lines 162-167): `"phase-milestone" not in
ADDABLE_CATEGORIES` and `"phase-milestone" in ALL_CATEGORIES`. This is the one test that must
change shape (the `ALL_CATEGORIES` name goes away per Scope bullet 4), not just get new assertions.
`tests/tools/test_layer_registry.py` (193 lines, read in full) is the exact 9-section structural
template for the new `test_tag_category_registry.py`: canonical-form tests, `is_X_registered`
tests, `load_registry` tests (missing/reads/skips-blanks/duplicate-raises), `add_X` tests
(appends/rejects-non-canonical/rejects-duplicate/append-only), `check_X_registered` tests, and a
`X_values` test pinned against the real seeded repo registry (`test_layer_values_matches_real_
seeded_registry`, layer_registry.py:184-193) — the category equivalent should pin against the real
4 seeded values the same way.

## Mechanics / Engine Constraints

None. This ticket is pure tooling/process infrastructure (`tools/`, `tests/tools/`,
`docs/guidelines/`, `docs/guides/`) — it touches no simulation logic, no `src/` runtime code, and
no `docs/mechanics/` or `docs/engine/` chapter. `layer: guidelines` (matching the ticket's own
frontmatter) is correct; there is no Mechanics Bible or Engine Contract citation applicable here.

## Parity Ledger Overlap

None found. `docs/parity_ledger/infrastructure.yaml` was grepped for `tag_registry`,
`layer_registry`, and `registries/` — all hits are either (a) unrelated coincidental use of the
English word "registries" (e.g. plan-gate static-check module naming), or (b) prior entries for
sibling tickets (`TCK-20260720-DASHBOARD-TAG-FACET-REGISTRY`,
`TCK-20260718-GLOSSARY-REGISTRY`/`GLOSSARY-API`) whose `v2_evidence`/`test_path` already point at
the current, correct `registries/*.jsonl` paths (updated by `TCK-20260720-TAG-REGISTRY-RELOCATE`).
No existing parity ledger entry describes tag-category *validation* mechanics (as opposed to tag
*registration*), and none needs a status change from this ticket's work. **A new entry is not
strictly required** — this ticket doesn't change simulation behavior or observable tool output
(the addable-category set stays the same 4 values, byte-identical before/after) — but if the team
wants tooling-infra changes tracked for consistency with `TCK-20260718-LAYER-REGISTRY-CONVERSION`'s
and `TCK-20260720-TAG-REGISTRY-RELOCATE`'s precedent, `infrastructure.yaml` is the right file
(both those tickets are recorded there, `priority: P2`, `status: verified`/`feature`). Flag this
as a should-decide-at-Parity-phase item, not a blocker for Investigate/Plan.

## Prior Work

- **`TCK-20260718-LAYER-REGISTRY-CONVERSION`** (`stored_artifacts/TCK-20260718-LAYER-REGISTRY-CONVERSION/`,
  `tickets/done/TCK-20260718-LAYER-REGISTRY-CONVERSION.md`) is the direct precedent this ticket
  explicitly mirrors — same conversion shape (hardcoded set literal → append-only JSONL registry +
  live `_values()` reader), same template test file
  (`tests/tools/test_layer_registry.py`), same frontmatter/layer conventions
  (`layer: guidelines`, artifact frontmatter used `authority: P1` there — see Risks below for why
  this investigation uses `P2` instead, per this ticket's own task template and the wider corpus
  norm).
- **`TCK-20260720-TAG-REGISTRY-RELOCATE`** (`stored_artifacts/TCK-20260720-TAG-REGISTRY-RELOCATE/`,
  done) is a hard dependency, already landed: it moved `tag_registry.jsonl`/`layer_registry.jsonl`/
  `glossary_registry.jsonl` from `docs/guidelines/` to `registries/` and updated every
  `_REGISTRY_REL_PATH` constant and doc reference. Confirmed via direct read of
  `registries/tag_registry.jsonl` (53 lines) and `registries/layer_registry.jsonl` (19 lines) —
  both exist at the new path today. **This ticket's own "Related Docs" list
  (`docs/guidelines/layer_registry.jsonl`, `docs/guidelines/tag_registry.jsonl`) is stale** — those
  paths no longer exist; the live paths are `registries/layer_registry.jsonl` and
  `registries/tag_registry.jsonl`. Use the live paths in the new registry file and in any doc
  updates; do not resurrect the old `docs/guidelines/` path.
- **`TCK-20260706-TAG-REGISTRY-DATA`** (`tickets/done/`) originally created `tag_registry.py` /
  `tag_registry.jsonl` and the `ALL_CATEGORIES`/`ADDABLE_CATEGORIES` split being converted here.
- **`TCK-20260704-TAG-TAXONOMY`** (`tickets/done/`) defined the 5-category taxonomy itself
  (`docs/guidelines/tag_taxonomy.md`) — the source of truth for what the 5 category names mean;
  this ticket does not change the taxonomy, only where the *addable subset* is machine-readable.
- **`TCK-20260720-SKILL-MAPPING-DEDUP`** (most recent commit touching `tag_registry.py`, done)
  demonstrates the currently-accepted pattern for `tag_registry.py` growing new
  self-referential/optional-field capability (`triggers_skill`) without breaking existing callers —
  same "additive, backward-compatible" bar `add_category()`/`category_values()` should meet.
- **`docs/guidelines/tag_taxonomy.md`** (Tag Registry section, lines ~130-171) and
  **`docs/guides/ticket_tagging.md`** (Registering a New Tag section, lines ~19-42) both already
  describe categories as **exactly the 4 addable ones** in prose today — `tag_taxonomy.md` line 158:
  "`<category>` must be one of `subsystem-topic`, `process-skill-signal`, `quality-attribute`,
  `meta-process`"; `ticket_tagging.md` line 32 says the same, then explicitly: "`phase-milestone`
  tags like `phase-5` never need registering — they're recognized by pattern." This prose is strong
  independent evidence for the 4-category seeding decision below — it already reflects the
  4-category mental model the tooling should now enforce mechanically instead of just by convention.

## Risks and Open Questions

**RESOLVED — 5-vs-4-category seeding design question (ticket AC requires this be explicitly
resolved here, not assumed):**

**Decision: seed `registries/tag_category_registry.jsonl` with only the 4 currently-addable
categories** (`subsystem-topic`, `process-skill-signal`, `quality-attribute`, `meta-process`).
`phase-milestone` is **not** written to the registry file at all — it remains purely a code-side
concept, exempted via `is_phase_milestone_tag()`'s regex match, exactly as it is exempted from
*tag* registration today (a `phase-N` tag is never written to `tag_registry.jsonl` either — the
same exemption pattern, one level up).

Rationale, grounded directly in how `layer_registry.py` and `tag_registry.py`'s existing exemption
mechanisms actually work (not assumed):

1. **`add_category()` is specified to be "identical shape to `add_layer()`"** (ticket Scope bullet
   2). `add_layer()`'s entry schema is `{"layer", "added_date", "note"}` — no field for
   "registered but not usable." Mirroring that shape exactly gives `add_category()` entries
   `{"category", "added_date", "note"}`, with **no `addable`/`exempt` boolean field**. If
   `phase-milestone` were seeded into this file, every entry would be schema-identical whether or
   not it's actually usable in `add_tag()` — there would be no way to tell them apart from the file
   alone, forcing either (a) a schema deviation (a new boolean field, which is *not* what "identical
   shape to `add_layer()`" asks for), or (b) hardcoding a `- {"phase-milestone"}` subtraction
   *outside* the registry to filter it back out — which is exactly the `ALL_CATEGORIES -
   {"phase-milestone"}` pattern this ticket's Scope bullet 4 says to **remove**, not relocate into a
   different form.
2. **`category_values()` is specified to return a live frozenset "exactly matching
   `layer_values()`'s implementation"** (ticket Scope bullet 3) — i.e. `frozenset(load_registry(root
   ).keys())`, unconditionally, no filtering. Scope bullet 4 then says `add_tag()`'s category
   validation and the CLI `--category` choices should **source directly from `category_values()`**
   with no other logic. For that direct, unfiltered sourcing to correctly reject `phase-milestone`
   as an invalid `add_tag()` category (which `test_add_tag_rejects_phase_milestone_category` in
   `tests/tools/test_tag_registry.py` requires — see Current Behavior), `category_values()` must
   **not** contain `"phase-milestone"` in the first place. If it were seeded and thus present in
   `category_values()`, `add_tag("x", "phase-milestone", ...)` would incorrectly succeed, breaking
   that existing test and the invariant it protects (phase-milestone tags are only ever assigned by
   the numeric-pattern route, never manually chosen at `add_tag()` time).
3. **The existing 3 documented "recognized-but-not-registrable" mechanisms in this codebase all
   work by pattern exemption, never by registering-then-filtering**: `is_phase_milestone_tag()`
   exempts `phase-N` *tags* from `tag_registry.jsonl` membership by regex, not by putting
   `"phase-N"` literal rows in the file; `TAG_SYNONYM_MAP`/`FORBIDDEN_PRIORITY_TAGS` reject
   non-canonical forms before any registry lookup happens at all. Seeding `phase-milestone` into
   `tag_category_registry.jsonl` (only to have it functionally excluded elsewhere) would be the
   first case in the codebase of "register it, then filter it back out" — inconsistent with every
   existing precedent, and reintroducing exactly the two-tier ALL/ADDABLE distinction the ticket
   is trying to collapse into one live source.
4. **`docs/guidelines/tag_taxonomy.md` and `docs/guides/ticket_tagging.md` already describe the
   registrable category set as exactly these 4**, and describe `phase-milestone` as pattern-
   recognized, never registered — the seeding decision matches the existing, already-shipped
   documentation model rather than introducing a new one.
5. **Ticket Acceptance Criterion 1 itself already states this explicitly**: "seeded with exactly
   the current addable categories (subsystem-topic, process-skill-signal, quality-attribute,
   meta-process)" — 4 named categories, and AC 4 says "phase-milestone stays naturally excluded
   since it is never seeded in the registry file." The "Assumptions/Open Questions" framing of this
   as unresolved appears to be a deliberate check that Investigate independently derives and
   confirms this outcome from the mechanism (not merely defers to the AC's own wording) — which
   this section has now done from first principles (points 1-4), arriving at the same answer AC 1
   already states. No conflict, no reason to deviate.

**Other risks / open items:**

- **Gap: `tools/validate_frontmatter.py` has no category-related code to change.** It only checks
  tag canonical-form and registry *membership* (`is_tag_registered`), never a tag's *category* —
  category correctness is enforced entirely inside `add_tag()` at registration time, not re-checked
  at frontmatter-validation time. The ticket's Request Summary implies `validate_frontmatter.py` is
  a "hardcoded-category consumer" that needs updating; it is not, today. Recommend: no change to
  `validate_frontmatter.py` is required by this ticket's actual scope (it doesn't import
  `ADDABLE_CATEGORIES`/`ALL_CATEGORIES` at all, confirmed by direct read of the full file), beyond
  it continuing to work unchanged since it imports unrelated names
  (`FORBIDDEN_PRIORITY_TAGS`, `TAG_SYNONYM_MAP`, `TAG_TAXONOMY_EFFECTIVE_DATE`,
  `canonical_form_violation`, `is_tag_registered`, `load_registry`) from `tag_registry.py`, none of
  which this ticket removes or renames. Flag as a Plan-phase note: verify no edit is made here
  unless a genuine need surfaces; don't invent one to satisfy the Related Code Areas list.
- **Gap: `tools/ticket_stats_report.py` has zero tag-category code.** Confirmed by full read — it
  reports Tier/Type/Priority/Layer distribution, not tags at all. No change needed; likely listed
  in Related Code Areas by analogy/caution rather than an actual dependency. Flag in Plan so it
  isn't force-edited to "use" `category_values()` where there's nothing to wire it to.
- **Self-referential import, resolved as low-risk**: `add_category()`/`category_values()` live in
  `tag_registry.py` itself, and `add_tag()` (also in `tag_registry.py`) will call
  `category_values()`. This is intra-module (same file), not a cross-module import — Python
  resolves both names at *call* time, not *def* time, so their physical order in the file doesn't
  matter as long as both are defined before `add_tag()` is actually invoked (which only happens
  after full module load). No import cycle, no ordering hazard — confirmed by inspecting how
  `layer_values()`/`add_layer()` already coexist in `layer_registry.py` with no special ordering
  needed. `validate_frontmatter.py`'s existing cross-module import chain
  (`validate_frontmatter → tag_registry`, `validate_frontmatter → layer_registry`) is unaffected —
  it doesn't need to import `category_values()` at all (see gap above).
- **The `registries/` path deviation is already real, not aspirational** — `TCK-20260720-TAG-
  REGISTRY-RELOCATE` landed before this ticket started, so `_REGISTRY_REL_PATH =
  Path("registries/tag_category_registry.jsonl")` is correct from day one; no follow-up relocation
  ticket is needed for this new file (unlike what the ticket's own Assumptions section speculates).
- **`reviews/src_export.py` / `reviews/test_export.py`** are stale generated snapshots containing
  copies of the current `ALL_CATEGORIES`/`ADDABLE_CATEGORIES` code and tests. They are not owned by
  this ticket (no regeneration mechanism referenced in Related Code Areas) — leave untouched; note
  in Plan that they will look stale relative to the new code until next regenerated, which is
  expected/pre-existing behavior for that directory, not a regression this ticket causes.

## Anti-Drift Hazards

- **Do not add an `addable`/`exempt` boolean field to the category entry schema.** It would work,
  but it contradicts the ticket's explicit "identical shape to `add_layer()`" requirement and
  reopens exactly the ALL/ADDABLE two-tier distinction the ticket removes. If `phase-milestone` handling
  ever needs to change, the correct lever is `is_phase_milestone_tag()`'s regex, not a registry
  field.
- **Do not let `category_values()` silently diverge from `ADDABLE_CATEGORIES`'s current value.**
  The new registry must be seeded via the *real* `add_category()` API (Scope bullet 1) with exactly
  the same 4 strings currently in `ADDABLE_CATEGORIES` — a hand-written JSONL file, or one seeded
  with different category names/spelling, would silently change what categories are legal without
  any test catching it unless the new `test_tag_category_registry.py` pins against the literal
  set (mirroring `test_layer_values_matches_real_seeded_registry`'s pinning pattern).
- **Do not touch `tag_report.py::categorize_tag()` or `generate_retro.py`'s string-equality
  checks.** Both are explicitly Out of Scope in the ticket, and both were confirmed (by full read)
  to have no set literal to replace — any edit there would be unrequested scope creep with no
  underlying bug to fix.
- **Do not force an edit into `validate_frontmatter.py` or `ticket_stats_report.py`** just because
  they're named in Related Code Areas — both were confirmed to have no actual category-related code
  today (see Risks/Gaps). Editing them to "use" the new registry where nothing currently references
  categories would be inventing behavior, not converting existing behavior.
- **Do not resurrect `docs/guidelines/tag_registry.jsonl` / `docs/guidelines/layer_registry.jsonl`
  paths.** The ticket's own "Related Docs" list is stale post-relocation; any new path references
  (in the new registry file's `_REGISTRY_REL_PATH`, in doc updates) must use `registries/...`.
- **Preserve `test_add_tag_rejects_phase_milestone_category`'s intent, even though its exact
  assertions (`ADDABLE_CATEGORIES`/`ALL_CATEGORIES` names) must change.** The behavior it protects —
  `add_tag(..., "phase-milestone", ...)` must still raise `ValueError` — must keep passing after
  the conversion; only the mechanism proving it (now via `category_values()` not containing
  `"phase-milestone"`) changes.
- **`sort_keys=True` on the written JSON line** (both `add_tag()` and `add_layer()` use it) must be
  preserved in `add_category()` for byte-identical formatting consistency across all three
  registries.

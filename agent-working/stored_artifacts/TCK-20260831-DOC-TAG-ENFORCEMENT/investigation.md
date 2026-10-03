---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260831-DOC-TAG-ENFORCEMENT
artifact_type: investigation
tags: [frontmatter, tagging, taxonomy, documentation, schema]
---

# Investigation — TCK-20260831-DOC-TAG-ENFORCEMENT

## Current Behavior

### `tools/validate_frontmatter.py` — exact code path

Read in full (355 lines). Confirmed structure:

- `_check_enum(filepath, fm, field, valid)` (line 141) — generic enum check, used identically by
  all four `_validate_*` functions.
- `_ticket_id_effective_date(ticket_id)` (line 148) — regex-extracts `YYYYMMDD` from a
  `TCK-YYYYMMDD-...` string via `_TICKET_ID_DATE_PATTERN = re.compile(r"^TCK-(\d{8})-")`. Returns
  `None` if `ticket_id` isn't a string or doesn't match.
- `_check_tags(filepath, fm, registry=None)` (line 156) — the tag-check function:
  ```python
  embedded_date = _ticket_id_effective_date(fm.get("ticket_id"))
  if embedded_date is None or embedded_date < TAG_TAXONOMY_EFFECTIVE_DATE:
      return []   # exempt
  ```
  then canonical-form + registry-membership checks per tag.
- `_validate_doc(filepath, fm, registry=None)` (line 188) — checks `status`/`layer`/`authority`/
  `audience` required + enum, plus the `last_verified`-when-`authoritative` conditional. **Does
  not call `_check_tags` anywhere.** Confirmed by reading the full function body — no reference to
  `_check_tags` or `tags` at all.
- `_validate_ticket` (204) and `_validate_artifact` (218) both end with `errors +=
  _check_tags(filepath, fm, registry)`. `_validate_archive` (232) also never calls it.
- `_VALIDATORS = {"doc": _validate_doc, "ticket": _validate_ticket, "artifact": _validate_artifact,
  "archive": _validate_archive}` (245) — the single dispatch table `validate_file`/
  `validate_directory` use via `detect_content_type()`/`content_type` override.
- `main()` (303) always calls `load_registry()` for real CLI runs and passes it through, so a
  real `python3 tools/validate_frontmatter.py <path>` invocation always has a live registry to
  check against once a doc-side check exists.

**This confirms the ticket's premise exactly**: `_validate_doc` is missing the `_check_tags(...)`
call other validators have. This is a one-line code gap in isolation — but see the "Cutover
mechanism" section below for why a *naive* one-line fix (`errors += _check_tags(filepath, fm,
registry)` added verbatim to `_validate_doc`) would not actually enforce anything.

### The critical architectural finding: `_check_tags`'s cutover logic is `ticket_id`-shaped, and doc frontmatter never has a `ticket_id` field

`_check_tags`'s *entire* in/out-of-scope decision is `_ticket_id_effective_date(fm.get("ticket_id"))`.
Confirmed via `tests/tools/test_validate_frontmatter.py`'s `_doc_fm()` helper (line 64-79): the doc
fixture builder never emits a `ticket_id` key, and no `doc`-type file anywhere in this repo's schema
(`docs/guidelines/frontmatter_schema.md`'s `doc` table, confirmed by reading it) has a `ticket_id`
field — that field is `ticket`/`artifact`-only.

Consequence: `fm.get("ticket_id")` is always `None` for a `doc`-type frontmatter dict, so
`_ticket_id_effective_date(None)` always returns `None`, so `_check_tags`'s exemption branch
(`embedded_date is None or embedded_date < TAG_TAXONOMY_EFFECTIVE_DATE`) is **always true** for
every doc, forever. If `_validate_doc` is wired to call `_check_tags(filepath, fm, registry)`
verbatim (same call shape as `_validate_ticket`/`_validate_artifact`), the call would compile,
run, and always return `[]` — a permanent, silent no-op, never actually enforcing anything on any
doc, ever. This is not a hypothetical edge case; it is the *only* code path `_check_tags` has for
determining scope, and it structurally cannot apply to docs.

**This means "wire `_validate_doc()` to call `_check_tags()`" (ticket Scope, bullet 3) cannot be
implemented as a literal one-line addition mirroring `_validate_ticket`/`_validate_artifact`.**
Either:
1. `_check_tags` must be generalized to accept a caller-supplied `in_scope: bool` (or an
   already-resolved `effective_date`/cutover signal) instead of deriving it internally from
   `ticket_id`, with `_validate_ticket`/`_validate_artifact` computing today's `ticket_id`-based
   value and `_validate_doc` computing a new doc-appropriate value — the *canonical-form and
   registry-membership logic itself* (which is content-type-agnostic) is fully reusable, only the
   scope-determination wrapper differs; or
2. A new doc-specific function (e.g. `_check_doc_tags`) is added that calls the same
   `canonical_form_violation`/`is_tag_registered` primitives from `tag_registry.py` directly (per
   the ticket's Out-of-Scope: "any new doc-side check must call those same functions, not
   reimplement them") but computes its own in-scope decision from whatever cutover mechanism Plan
   selects.

Either shape is a real code decision for Plan/Implement, not a copy-paste. This is the single most
important thing this investigation found beyond what the ticket's own Scope section already
states, and directly informs the "Cutover mechanism options" section below.

### Consumers of `validate_frontmatter.py`'s doc path (confirms Investigation task #5)

Grepped every `validate_frontmatter` reference repo-wide (`.claude/workflows/implement-ticket.js`,
`src/api/agent_ops_dashboard/ingest.py`, `tools/agent-monitoring/done_ticket_monitoring_coverage.py`,
`tools/agent-monitoring/generate_retro.py`, `tools/gate_checks/done_checker_static.py`,
`tools/generate_registry.py`, `tools/hybrid_retrieval.py`, `tools/layer_registry.py`,
`tools/tag_registry.py`, `tools/tag_report.py`, `tools/ticket_field_values.py`,
`tools/ticket_stats_report.py`) and read every import line. Findings:

- Only `tools/gate_checks/done_checker_static.py` imports and calls `validate_file`/
  `validate_directory` (line 41 import; call sites at line 272 `validate_file(ticket_path,
  registry=registry)` — content type inferred from the `tickets/` path — and line 282
  `validate_directory(staging_dir, content_type_override="artifact", registry=registry)` — always
  forced to `artifact`). **Neither call site ever validates `doc` content type.** No other consumer
  calls `validate_file`/`validate_directory` at all.
- Every other consumer only imports narrow, unaffected surface: `extract_frontmatter` (parsing
  only — `src/api/agent_ops_dashboard/ingest.py`, `tools/generate_registry.py`,
  `tools/agent-monitoring/done_ticket_monitoring_coverage.py`, `tools/agent-monitoring/
  generate_retro.py`, `tools/tag_report.py`), `LAYER_VALUES`/`STATUS_VALUES`/`AUTHORITY_VALUES`
  (enum constants — `tools/ticket_field_values.py`, `tools/hybrid_retrieval.py`,
  `tools/layer_registry.py`), or `TAG_TAXONOMY_EFFECTIVE_DATE`/`_ticket_id_effective_date` (also
  imported by `tools/tag_report.py` and `tools/agent-monitoring/generate_retro.py`, but only for
  *ticket*-scoped reporting, never doc-scoped).
- **Conclusion: adding a tag check inside `_validate_doc` cannot break any existing consumer**,
  because no consumer today ever calls the doc validation path at all. `.claude/workflows/
  implement-ticket.js` references `validate_frontmatter.py`/`ARTIFACT_TYPE_VALUES` only in prose
  guidance strings shown to agents, not in executable code. This directly satisfies Investigation
  task #5 and de-risks the "no CI/consumer breakage" half of the ticket's Out-of-Scope claim.

## Mechanics / Engine Constraints

Not applicable — this is tooling/process infrastructure (`docs/guidelines/`), not simulation
mechanics. No `docs/mechanics/` chapter or `docs/engine/` contract governs frontmatter validation
behavior.

## Docs Requiring Update

- `docs/guidelines/tag_taxonomy.md`: its "Enforcement" section (lines 201-224, read in full) states
  "This taxonomy applies to `ticket` and `artifact` content types only. `doc`-type frontmatter's
  `tags` field remains free-form and unvalidated ... the registry does not apply there either." —
  this is the exact sentence this ticket's Scope requires be replaced with the actual new,
  narrower/newly-enforced doc scope once Plan decides the cutover mechanism.
- `docs/guidelines/frontmatter_schema.md`: the `doc` content-type schema table (line 52) currently
  lists `tags` as `no | list of strings | free-form` — must change to describe the new enforcement
  once implemented, consistent with whatever cutover field/mechanism Plan selects (e.g. if a new
  opt-in marker field is chosen, this doc's `doc` schema table needs a new row for it, mirroring
  how the `ticket`/`artifact` rows already read "see `docs/guidelines/tag_taxonomy.md` — controlled
  vocabulary, forward-only enforced from `2026-07-04`").
- `docs/parity_ledger/infrastructure.yaml` entry `INFRA-180`: its `text` field currently reads "On
  ticket/artifact content types, tags additionally carry controlled-vocabulary enforcement ...
  applied forward-only from 2026-07-04" — this sentence is the exact scope statement this ticket
  changes; `status`/`v2_evidence` need updating once implemented (currently `status: verified`,
  `v2_evidence` cites `tools/validate_frontmatter.py + docs/guidelines/frontmatter_schema.md +
  docs/guidelines/tag_taxonomy.md + tests/tools/test_validate_frontmatter.py` — all four still
  apply, evidence just needs the doc-scope addition named).

A doc considered but not requiring a bullet: `docs/guides/ticket_reporting.md` (path:
`docs/guides/ticket_reporting.md`, under `docs/`) documents `tag_report.py`/`tag_corpus_sweep.py`'s
existing ticket/artifact-scoped "Pillar" reporting tools. It is not required to change for *this*
investigation/test_plan pair's own scope — if Plan decides a doc-side sweep tool is needed (see
"Retrofit blast radius" below), a Pillar 4 subsection would be added there, but that is a Plan-time
decision this investigation does not make, so no bullet is written here (would be Format 1 once
Plan confirms it).

A second doc considered but excluded: `docs/guidelines/frontmatter_schema.md`'s `LAYER_VALUES`
"Enum Reference" list (line 159-163) is already stale independent of this ticket — it lists 19
values without `frontend`, while the live registry (`registries/layer_registry.jsonl` via
`layer_values()`) has 20, including `frontend` (added by a prior ticket, confirmed via
`tests/tools/test_validate_frontmatter.py`'s `test_enum_values_layer` which already asserts
`frontend` in `LAYER_VALUES`). This staleness predates this ticket and is not caused by it — fixing
it is optional cleanup Plan may fold into the same `frontmatter_schema.md` edit this ticket already
requires (same file, same section, cheap to fix in passing) but is not itself a required-doc bullet
for this ticket's own scope.

## Parity Ledger Overlap

Only `docs/parity_ledger/infrastructure.yaml` entry `INFRA-180` overlaps (full text quoted above).
`priority: P2` (not P0), so no `test_path` is contractually required by the Authoritative Mechanics
Rule's P0 gate, though the ticket's own Acceptance Criteria already require new/updated tests
regardless. No other parity ledger file (`combat_movement.yaml`, `town_resource.yaml`, etc.)
references `validate_frontmatter.py`, tag/layer enforcement, or `docs/REGISTRY.yaml` — this is
purely an `infrastructure.yaml` concern.

## Prior Work

- `TCK-20260704-TAG-TAXONOMY` — defined the taxonomy and its explicit ticket/artifact-only,
  forward-only-from-2026-07-04 scope. Its own investigation.md's corpus review (1001 tickets, 1273
  distinct tags at the time) is the direct ancestor of this ticket's doc-side equivalent question.
- `TCK-20260706-TAG-REGISTRY-DATA` — built the append-only `registries/tag_registry.jsonl` and its
  `add_tag()`/`load_registry()`/`is_tag_registered()` API, seeded from the live ticket/artifact
  corpus. Any doc-tag backfill (if Plan decides one is needed) reuses this exact registry and API —
  there is no separate "doc tag registry," `tags` is one flat namespace regardless of content type.
- `TCK-20260706-TAG-REPORT-TOOL` — built `tools/tag_report.py`'s corpus-walk/classification pattern
  (`collect_completed_tickets`, `categorize_tag`, `tag_issues` via the later sweep ticket).
- `TCK-20260720-TAG-CATEGORY-REGISTRY` — added `registries/tag_category_registry.jsonl`, the
  4-category (`subsystem-topic`/`process-skill-signal`/`quality-attribute`/`meta-process`)
  allowlist every registered tag's `category` must resolve against.
- `TCK-20260718-LAYER-REGISTRY-CONVERSION` — converted `LAYER_VALUES` from a hardcoded set literal
  to `registries/layer_registry.jsonl` via `tools/layer_registry.py::layer_values()`. This is
  already fully wired for docs (`_validate_doc` already calls `_check_enum(..., "layer",
  LAYER_VALUES)`) — see "Retrofit blast radius" below for why the ticket's premise about a large
  doc-layer gap does not hold up under direct measurement.
- `TCK-20260720-TAG-CORPUS-REPAIR-SWEEP` — read `tools/tag_corpus_sweep.py` (139 lines) and its
  `plan.md`/full 6-step design in full. **This is directly reusable prior art, confirmed by reading
  the actual code, not assumed:** it built a report-only, non-cutoff-gated sweep
  (`collect_sweep_files`, `tag_issues`, `sweep_file_rows` in `tag_report.py`; orchestration/CLI in
  the new `tag_corpus_sweep.py`) walking exactly 4 roots — `tickets/done`, `tickets/inprogress`,
  `tickets/todos`, `stored_artifacts` — **explicitly not `docs/`** (confirmed via
  `collect_sweep_files`'s literal root list, line 192-210 of `tag_report.py`). Its plan.md's Step
  1-5 structure (multi-root collection → pure violation classifier → per-file row builder → sweep
  orchestration → report-only CLI with zero `--fix`/write surface, verified by a
  `git status --porcelain` before/after subprocess test) is a template Plan can point at almost
  unchanged for a `docs/`-scoped sweep, should Plan decide a retrofit report tool is needed — same
  `tag_issues`/`sweep_file_rows` functions in `tag_report.py` are directly callable against a
  `docs/`-rooted file list, no new classification logic required. Its Anti-Drift Notes (do not
  assert exact violation counts against the live corpus since it grows continuously; no `--fix`
  flag ever) apply identically to a doc-side equivalent.
- `TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER` — fixed 12 docs with no frontmatter block at all
  (a `generate_registry.py` hard-error, unrelated tool). Its 12 fixed paths are now pinned as a
  regression test (`tests/tools/test_validate_frontmatter.py`'s `TestPreviouslyFrontmatterMissingDocs`,
  line 712-734, `@pytest.mark.parametrize` over 12 real paths) — useful precedent for how this
  ticket's new tests should pin against real files rather than only synthetic fixtures.

## Risks and Open Questions

**Open question #1 (blocks Plan, per ticket's own framing) — cutover mechanism.** Concretely
evaluated, with feasibility weighed against `_ticket_id_effective_date`'s actual implementation
(read above):

| Option | Feasibility | Notes |
|---|---|---|
| (a) New doc-level opt-in marker field (e.g. a boolean or an embedded-date field analogous to `ticket_id`'s `YYYYMMDD`) | **High** — mirrors the existing mechanism almost exactly: a new frontmatter key, parsed the same way `_ticket_id_effective_date` parses `ticket_id`, feeding the same `_check_tags`-style `embedded_date is None or embedded_date < CUTOFF` comparison. Requires generalizing `_check_tags` per the architectural finding above (accept a resolved in-scope signal rather than deriving it from `ticket_id` internally). Every doc lacking the field is automatically exempt/grandfathered — zero retrofit forced. | Cleanest 1:1 analog to the ticket-side precedent. Downside: requires deliberately adding the field to any doc that should be newly enforced — an opt-in, not automatic, rollout (a doc author must know to add it). |
| (b) Global date cutover via git blame/log on each doc's frontmatter block | **Low-to-moderate, not recommended as primary.** No existing precedent in this codebase does this for a frontmatter check specifically — the only git-log-consuming tool found is `tools/codebase_health_baseline.py` (`git log --shortstat`), a different kind of analysis (change-volume stats, not per-file authorship dates). Concrete risks: git blame on a frontmatter block specifically (not the whole file) requires `git log -L` line-range tracking, which breaks across file moves/renames and squash-merges; is non-deterministic under history rewrites; and is slow to run per-file at directory-scan scale (397+ docs) compared to a pure-frontmatter-string check. Also introduces a git-availability dependency `validate_frontmatter.py` does not have today (it currently only reads file text, no subprocess calls). | Only worth it if Plan explicitly wants "any doc touched after date X" semantics without requiring authors to add anything — but the reliability/performance trade-off is real, not just theoretical. |
| (c) Directory/path-scoped rollout (e.g. only `docs/guidelines/`, `docs/testing/` first) | **High feasibility, but does not by itself satisfy the AC's per-file grandfathering requirement.** Trivial to implement (a path-prefix allowlist checked in `_validate_doc` or the CLI layer before calling the tag check at all). But within an enforced path, every doc — old or new — would either all pass or all newly fail; it doesn't distinguish a legacy doc from a freshly-authored one inside the same directory the way the ticket-side date cutoff does. Would need to be combined with (a) or (b) to get true forward-only semantics, or accepted as a *coarser* grandfathering unit (whole directories grandfathered, not individual files) if Plan is comfortable with that grain. | Good complement/staging strategy (e.g. "(a), rolled out first only in `docs/guidelines/`"), weak as a sole mechanism. |
| (d) Reuse `last_verified` as the cutover signal | **Not viable alone — already correctly ruled out by the ticket itself**, confirmed by direct measurement: only 75/397 `doc`-type entries in `docs/REGISTRY.yaml` carry `last_verified` (not 75/2106 — see "Retrofit blast radius" below for the corrected denominator). It is also semantically conflated: `last_verified` today means "content accuracy re-verified as of this date" (required only when `status: authoritative`), not "tags on this file have been reviewed against the registry." Reusing it for tag-cutover would silently give it a second, unrelated meaning. |

**Recommendation for Plan to weigh (not decided here):** option (a) — a new, purpose-built opt-in
field — is the strongest analog to the existing, working ticket-side mechanism, is deterministic
(no git dependency), and naturally grandfathers every existing doc with zero forced retrofit. It
does require generalizing `_check_tags`'s scope-derivation (see "Current Behavior" above) rather
than a literal one-line wire-in, which should be sized into Plan's estimate.

**Open question #2 (blocks Plan) — retrofit blast radius. Corrected numbers, measured directly
against the live `docs/REGISTRY.yaml` and `registries/tag_registry.jsonl` in this worktree**
(the ticket's own pre-supplied estimates for **layer** conflate two different `docs/REGISTRY.yaml`
row types — see the explicit correction below; the **tag** estimates were directionally right but
mixed doc+ticket rows together):

- `docs/REGISTRY.yaml` has 2106 total entries, but they are **not** all doc entries: 1709 are
  `type: ticket` rows and only 397 are `type: doc` rows (confirmed: `Counter(e['type'] for e in
  data)` → `{'ticket': 1709, 'doc': 397}`).
- **Layer correction:** the ticket's stated "1709/2106 doc registry entries (81%) show `layer:
  <none>`" is not accurate. Direct measurement: **0 of the 397 `type: doc` entries have a
  missing/empty `layer` field** — every doc entry in the registry already carries a real layer
  value. The 1709 figure is the *ticket-type* row count, and `type: ticket` rows in
  `docs/REGISTRY.yaml` structurally never carry a `layer` key at all — confirmed by reading
  `tools/generate_registry.py::collect_tickets()` (line 265-330) directly: its emitted entry dict
  has exactly `type, path, ticket_id, title, tier, ticket_type, date, related_code_areas,
  artifact_files, tags` — no `status`/`layer`/`authority`/`audience` keys, by deliberate design (a
  ticket-workflow-shaped projection, distinct from `collect_docs()`'s frontmatter-mirror shape at
  line 205-263, which explicitly does emit `status`/`layer`/`authority`/`audience` — see also
  `print_summary()`'s own inline comment "`# By layer (docs only).`" at line 394, further
  confirming layer-counting was always doc-scoped by design). This is a registry-projection design
  choice for ticket rows, not a doc-side validation gap — **there is no 1709-doc layer backlog to
  retrofit.**
  - The real, much smaller layer finding: running the live registered-layer allowlist
    (`layer_registry.py::layer_values()`, 20 values) against all 397 doc entries' `layer` values
    finds exactly **1** doc with an invalid value: `docs/simulation/domains/social_memory_contract.md`
    has `layer: social`, which is not a registered layer (closest existing candidates: `strategy`,
    `simulation`, or registering a new `social` layer — `docs/parity_ledger/social_narrative.yaml`
    already exists as a subsystem name, suggesting `social` could be a legitimate future layer
    registration, but that decision belongs to whoever fixes this file, not this investigation).
  - **Consequence for Investigation task #4** ("can layer-comprehensive checking ship
    independently/first?"): yes, trivially — it isn't really a retrofit at all. `_validate_doc`
    already calls `_check_enum(..., "layer", LAYER_VALUES)` (line 194); running
    `python3 tools/validate_frontmatter.py docs/` today would already reject exactly 1 real doc
    over `layer`, not 1709. Wiring this comprehensively (e.g. into a CI step or a doc-close gate)
    is nearly free once that one file is fixed. Plan should treat the "layer" half of this ticket's
    scope as effectively already-solved-and-measured, distinct in size and risk from the "tag"
    half, which is the genuine remaining retrofit question.
- **Tag numbers, doc-only (corrected denominator):** of 397 doc entries, 206 carry at least one
  `tags` entry (191 have none). Doc frontmatter carries **288 unique tag strings** (879 total
  tag occurrences) — not 1381; 1381 is the unique-tag count across the *entire* registry (doc +
  ticket rows combined: `len({t for e in data for t in (e.get('tags') or [])})` == 1381). Of the
  288 doc-only unique tags:
  - **54 tags (covering 517 of the 879 occurrences, ~59%) are already registered** in
    `registries/tag_registry.jsonl` — these would pass a hard-allowlist check with zero changes.
  - **234 tags (362 occurrences, ~41%) are not currently registered.** Of those, **188/234 (80%)
    are used exactly once** — a long tail of one-off, file-specific tags, structurally identical in
    shape to what `docs/guidelines/tag_taxonomy.md`'s own Canonical-Form Rules section already says
    about the original 1273 pre-registry ticket tags ("a large amount of legitimately one-off,
    ticket-specific detail that was never evidence of a missing category"). The highest-frequency
    unregistered doc tags are genuinely reusable subsystem/meta-process candidates, not noise:
    `idea` (28 occurrences — brainstorm-corpus tag), `contract` (16 — the `docs/*/​*_contract.md`
    family, e.g. `assembly_contract.md`, `pipeline_contract.md`, `combat_engagement_contract.md`),
    `agent-infrastructure` (12), `roadmap` (8), `domains` (8 — the `docs/simulation/domains/`
    family), `pipeline` (5), `planning` (5), `guide` (5), `scoring` (4). These read as legitimate
    Subsystem/Topic or Meta-Process candidates worth registering (mirroring how
    `TCK-20260706-TAG-REGISTRY-DATA` seeded the ticket-side registry from live usage), not
    one-off noise — Plan should weigh a small, evidence-based backfill registration pass for this
    high-frequency subset against pure forward-only grandfathering.
  - **Canonical-form violations are rare: only 3 of the 288 doc tags fail canonical form** —
    `'Any'` (uppercase), `'worldmodules'` (known synonym, should be `world-modules`),
    `'simulation_quality'` (underscore, should be `simulation-quality`). These are cheap,
    unambiguous one-line fixes regardless of which cutover/retrofit strategy Plan picks — they are
    not tied to the unregistered-tag question at all (`canonical_form_violation()` and
    `is_tag_registered()` are independent checks, confirmed by reading `_check_tags`'s
    two-stage `if violation: ... elif registry is not None and not is_tag_registered(...)`
    structure).
  - Two doc entries already use `phase-N` tags (`phase-2`, `phase-5`) — automatically exempt from
    registration per the existing `is_phase_milestone_tag()` rule, no special handling needed.

**Open question #3 — `_check_tags` generalization is now a concrete implementation question, not
just a "cutover mechanism" abstraction.** Whichever mechanism Plan picks, the "Current Behavior"
section's architectural finding means Implement must touch `_check_tags`'s signature/internals (or
add a parallel doc-specific function), not just add one call inside `_validate_doc`. This should be
sized explicitly in `plan.md`'s steps, not treated as incidental to "wire `_check_tags` in."

**Risk:** any bulk registration pass for the high-frequency unregistered doc tags (`idea`,
`contract`, `agent-infrastructure`, `roadmap`, `domains`, etc.) is explicitly Out of Scope for
*this* ticket per its own "Out of Scope" section ("Actually performing a bulk backfill/registration
... is large enough to be its own follow-up ticket") — this investigation surfaces the concrete
evidence for that follow-up decision without performing it.

## Anti-Drift Hazards

- **Do not let the doc-tag check reimplement canonical-form or registry-membership logic.**
  `canonical_form_violation()` and `is_tag_registered()` in `tag_registry.py` are the single source
  of truth (per this ticket's own Out-of-Scope) — any new doc-side function must call them
  directly, exactly as `_check_tags` already does for tickets/artifacts.
- **Do not silently change `_check_tags`'s existing ticket/artifact behavior while generalizing
  it.** All of `TestTagRegistryEnforcement`'s 7 existing tests
  (`tests/tools/test_validate_frontmatter.py` lines 559-621) and `TestEnumAntiDrift`'s
  `test_tag_taxonomy_effective_date` must keep passing byte-for-byte — the ticket-side forward-only
  cutoff at `2026-07-04` via `ticket_id` must remain exactly as it is today.
- **Do not conflate `last_verified` with the new cutover signal** — they answer different
  questions (content freshness vs. tag-enforcement scope), as noted in the cutover-mechanism table
  above; reusing the same field for both would be a silent, undocumented semantic overload.
- **Do not let a naive "add `_check_tags(filepath, fm, registry)` to `_validate_doc`" implementation
  ship as if it were real enforcement.** As shown above, that exact line, unmodified, is a
  functional no-op for every doc, forever, because no doc frontmatter carries `ticket_id`. A test
  asserting that a *known-bad* doc tag is actually rejected post-implementation
  (`tests/tools/test_validate_frontmatter.py`'s planned new doc-tag tests) is the concrete guard
  against this exact silent-no-op failure mode landing undetected.
- **The 1-doc invalid-layer finding (`docs/simulation/domains/social_memory_contract.md`,
  `layer: social`) should not be silently "fixed" as a drive-by inside this ticket** without a Plan
  decision on whether `social` should become a registered layer or the file should be remapped to
  an existing one — either choice has downstream effects (a new layer registration is append-only
  and permanent, per `layer_registry.py`'s design).
- **Do not scope-creep into wiring `validate_frontmatter.py` into CI** — explicitly Out of Scope
  per the ticket, confirmed still true (no `.github/workflows/*.yml` references it).

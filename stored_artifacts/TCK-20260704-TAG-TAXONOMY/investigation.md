---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260704-TAG-TAXONOMY
artifact_type: investigation
tags: [tagging, taxonomy, frontmatter, registry, data-quality]
---

# Investigation — TCK-20260704-TAG-TAXONOMY

## Current Behavior (file:line)

`tools/validate_frontmatter.py` defines closed enums for several frontmatter fields and checks
them via a shared `_check_enum()` helper, but `tags` has no equivalent validation at all:

- `STATUS_VALUES` — `tools/validate_frontmatter.py:25`
- `LAYER_VALUES` (19 values: mechanics, engine, testing, simulation, ai, architecture, core,
  ticket, artifact, guidelines, observability, performance, combat, compliance, strategy,
  systems, economy, world, misc) — `tools/validate_frontmatter.py:26-30`
- `AUTHORITY_VALUES` — `tools/validate_frontmatter.py:31`
- `AUDIENCE_VALUES` — `tools/validate_frontmatter.py:32`
- `PHASE_VALUES` — `tools/validate_frontmatter.py:33`
- `ARTIFACT_TYPE_VALUES` — `tools/validate_frontmatter.py:34`
- `_check_enum()` helper — `tools/validate_frontmatter.py:112-116`

`_validate_doc` (`:119-132`), `_validate_ticket` (`:135-145`), `_validate_artifact`
(`:148-158`), and `_validate_archive` (`:161-171`) each call `_check_enum(filepath, fm, "layer",
LAYER_VALUES)` (e.g. `:141`, `:154`) — but **none of them reference `tags` in any way**. There is
no `TAG_VALUES` constant, no format check, no forbidden-value check. A ticket or artifact can put
anything into `tags: [...]` and `validate_file()` (`:182-208`) will pass it silently. Confirmed by
running the four `_validate_*` functions end-to-end: `tags` never appears in any error-producing
branch.

`docs/guidelines/frontmatter_schema.md:52,84,113` documents `tags` as `no | list of strings |
free-form` for the `doc`, `ticket`, and `artifact` content types respectively — i.e. the doc
itself currently states, correctly, that there is no controlled vocabulary. This doc is the
authoritative parity source per `INFRA-180` (see Parity Ledger Overlap below) and will need
updating in lockstep with any validator change.

`.claude/agents/ticket-scoper.md:28` — the agent that authors new ticket frontmatter — instructs
`tags: [<scope words from ticket ID, lowercase>]` with no reference to any taxonomy or canonical
list. This is the write path that produced the current uncontrolled vocabulary and is also the
step where a fix would need to be wired in (AC: "`.claude/agents/ticket-scoper.md` references the
taxonomy doc when generating tags for new tickets").

### Data: Actual Tag Corpus (`docs/REGISTRY.yaml`, re-verified 2026-07-04 this session)

Re-ran the corpus analysis directly against `docs/REGISTRY.yaml` (1251 total entries: 1001
`type: ticket`, 250 `type: doc`) to confirm the numbers cited in the ticket are still accurate:

```
tickets_with_empty_tags = 4 / 1001     # 0.4%  (confirmed)
distinct_tags           = 1273         # confirmed
tags_used_exactly_once  = 730 / 1273   # 57.3% (confirmed)
median_tags_per_ticket  = 3            # confirmed, distribution otherwise healthy
```

Mechanical near-duplicate detection (`re.sub(r'[-_]', '', tag.lower())` — a normalization that
only catches hyphen/underscore/case collisions) found **19 confirmed groups**, matching the
ticket's count. Re-running this check turned up one correction to the prior session's
investigation draft: **4 of the 19 groups are not one-off singleton pairs** — they carry real,
non-trivial counts on both sides, same as `phase-5`/`phase5`:

| Group | Counts | Note |
|---|---|---|
| `phase-5` / `phase5` | 32 / 7 | |
| `simulation_quality` / `simulation-quality` | 11 / 19 | |
| `phase-4` / `phase4` | 17 / 11 | **not a singleton pair** — previously miscategorized in draft notes as one of the "9 more ~1/1" pairs |
| `phase-1` / `phase1` | 14 / 12 | **not a singleton pair** — same correction |
| `phase-3` / `phase3` | 16 / 8 | |
| `p2` / `P2` | 16 / 4 | |
| `phase-2` / `phase2` | 14 / 6 | **not a singleton pair** — same correction |
| `p1` / `P1` | 7 / 7 | |
| `world-modules` / `worldmodules` | 4 / 9 | |
| `phase-6` / `phase6` | 11 / 2 | |
| `phase-0` / `phase0` | 6 / 3 | **not a singleton pair** — same correction |
| `p0` / `P0` | 5 / 2 | |
| `self-model` / `selfmodel` | 3 / 1 | |
| `grand-strategy` / `grand_strategy` | 2 / 1 | |
| `dungeon_crawl` / `dungeon-crawl` | 1 / 1 | true singleton pair |
| `world_spec` / `worldspec` | 1 / 1 | true singleton pair |
| `grade_thresholds` / `grade-thresholds` | 1 / 1 | true singleton pair |
| `feature_flag` / `feature-flag` | 1 / 1 | true singleton pair |
| `data-model` / `datamodel` | 1 / 1 | true singleton pair |

Confirmed `p0`/`p1`/`p2` case variants exactly as the ticket states: `{'p0': 5, 'P0': 2}`,
`{'p1': 7, 'P1': 7}`, `{'p2': 16, 'P2': 4}` — 34 ticket entries total carry a bare priority digit
as a tag, duplicating the dedicated `## Priority` ticket-body field.

Likely additional synonym pairs **not** caught by the mechanical check (confirmed counts, still
requiring human/LLM judgment per the ticket, not resolved here): `obs` (45) vs. `observability`
(43); `cog` (30) vs. `cognition` (24); `sim` (33) vs. `simulation` (3) — the `sim`/`simulation`
gap is much more lopsided than the ticket's framing suggested (33 vs. only 3, not a close split),
which strengthens the case that `sim` is the de facto standard form in practice, if the two are
in fact synonyms and not distinct concepts. This disambiguation is a Plan-phase call, not resolved
here.

### Confirmed: Tags Are Never Queried

```
grep -rn "e\.get('tags')\|tags=\|filter.*tag" .claude/workflows/*.js .claude/agents/*.md
# zero matches (re-confirmed this session)

grep -n "e.get('layer')" .claude/workflows/create-tickets.js
# .claude/workflows/create-tickets.js:343
#   matches = [e for e in entries if e.get('layer') in layers]
```

`layer` is the only `REGISTRY.yaml` field actually filtered on in agent-facing orchestration code
today. Tags remain write-only metadata. Per the 2026-07-04 user decision, wiring tag consumption
is explicitly out of scope for this ticket; recorded here only so Plan doesn't assume any existing
consumer needs to keep working.

## Mechanics/Engine Constraints

None apply. This is repo tooling/process infrastructure (`tools/validate_frontmatter.py`,
`docs/guidelines/`, `.claude/agents/`) — no `docs/mechanics/` chapter or `docs/engine/` contract
governs ticket/doc frontmatter or tag vocabulary. No simulation determinism, authoritative-state,
or mutation-pipeline concern is implicated (consistent with `INFRA-180`'s own
`support_boundary: "Doc tooling only — no simulation behavior is involved."`).

## Parity Ledger Overlap

One entry directly overlaps and **will need a `v2_evidence` review once tag validation lands**:

- **`INFRA-180`** (`docs/parity_ledger/infrastructure.yaml:1846-1862`, status `verified`,
  priority `P2`): asserts `tools/validate_frontmatter.py` "correctly enforces the doc schema
  defined in `docs/guidelines/frontmatter_schema.md`" and that doc + validator + test file stay in
  parity. `v2_evidence` lists exactly the three files this ticket's Scope touches:
  `tools/validate_frontmatter.py`, `docs/guidelines/frontmatter_schema.md`,
  `tests/tools/test_validate_frontmatter.py`. Adding tag validation changes the behavior this
  entry certifies (`frontmatter_schema.md` currently documents `tags` as `free-form` at lines
  52/84/113 — see Current Behavior above), so this entry's `text`/`v2_evidence` must be revisited
  in the same session the validator change lands, per `CLAUDE.md`'s Parity rule ("If logic
  changes, update the corresponding doc AND the parity ledger entry in the same session"). Not
  yet in the ticket's Related Docs/Tickets — should be added during Plan.

No other parity ledger file (`substrate.yaml`, `combat_movement.yaml`,
`strategic_cognition.yaml`, `town_resource.yaml`, `progression.yaml`, `social_narrative.yaml`,
`world_dynamics.yaml`) has any entry referencing tags, taxonomy, or frontmatter — checked via
case-insensitive grep across all six plus `infrastructure.yaml`.

## Prior Work

- **`docs/REGISTRY.yaml`'s doc lineage is directly ancestral to this ticket's problem**:
  `TCK-20260606-DOCSITE-SCHEMA` ("Define frontmatter schema for all documentation content types")
  is where `docs/guidelines/frontmatter_schema.md` and the `_check_enum` pattern originated;
  `TCK-20260606-DOCSITE-FM-LIVE` and `TCK-20260606-DOCSITE-FM-TICKETS` are where the schema was
  first bulk-applied to existing docs/tickets (this is presumably also where the free-text `tags`
  convention took hold, unconstrained from day one); `TCK-20260606-DOCSITE-REGISTRY` is where
  `docs/REGISTRY.yaml` itself was generated. None of these four addressed tag vocabulary control —
  they established the enum pattern for `status`/`layer`/`authority`/`audience` but left `tags`
  deliberately open, which this ticket is now the first to revisit.
- **No prior ticket specifically targets tag taxonomy or synonym control** — searched
  `docs/REGISTRY.yaml`'s 1001 ticket entries for `tag`/`taxonomy`/`frontmatter`/`registry`/
  `validate_frontmatter` in title, path, or tags; the only substantive hits were the four
  DOCSITE-* tickets above plus unrelated uses of "tag(s)" as an ordinary English word (e.g.
  `required_location_tags` quest matching, `event-taxonomy` as a tag on an unrelated resource-
  ecology ticket).
- **This ticket originated from a batch of 5 siblings** filed 2026-07-04 from an agent
  infrastructure audit, recorded in `tickets/todos/agent-infra-followups/SEQUENCE.md`. That
  document explicitly designs this ticket's taxonomy to serve two sibling tickets: `TCK-20260704-
  SKILL-TRIGGER-COVERAGE` (tag-driven skill routing) and `TCK-20260704-RETRO-LOOP-ENFORCEMENT`
  (tag-based retro grouping) — a design-time consideration only, no execution dependency between
  the three. The ticket file is currently duplicated at both
  `tickets/todos/agent-infra-followups/TCK-20260704-TAG-TAXONOMY.md` (source, byte-identical) and
  `tickets/inprogress/TCK-20260704-TAG-TAXONOMY.md` (working copy) — per `CLAUDE.md`'s workflow
  rule, the todos-subfolder source file must be deleted at completion, and once all 5 siblings in
  `agent-infra-followups/` are done, the whole folder moves to `tickets/done/agent-infra-
  followups/`.
- `staging_artifacts/TCK-20260704-TAG-TAXONOMY/investigation.md` (this file) supersedes an earlier
  same-session draft that used non-canonical frontmatter (`phase: open` field present, no `phase`
  key needed for artifacts; `# Investigation` heading without the ticket-id suffix) and slightly
  miscategorized 4 of the 19 duplicate-tag groups as singleton pairs — corrected above.

## Risks and Open Questions

- **Confirmed this session**: `validate_directory()` (`tools/validate_frontmatter.py:211-219`)
  recursively validates every `.md` file under a given root via `path.rglob("*.md")`, and `main()`
  (`:226-266`) dispatches to it whenever the CLI argument is a directory. Nothing in the repo's
  `Makefile`/CI config discovered so far scopes this to "new files only" — if `validate_frontmatter.py`
  is ever invoked as `python3 tools/validate_frontmatter.py tickets/` (whole-directory mode), **all
  1001 historical tickets would be re-validated**, and a hard-reject tag rule would need either a
  grandfather/exemption mechanism or a softer (warn-only) severity. Conversely, if the only real
  invocation path is per-file at ticket-creation time (via `ticket-scoper`), enforcement is
  naturally forward-only and free. **This is not yet fully resolved** — confirming exactly which
  invocation mode(s) are wired into `ticket-scoper`/Make targets/CI (searched but did not find a
  definitive current caller in this pass; this needs one more targeted check in Plan before
  deciding reject-vs-warn) remains the single most consequential open question for the AC about
  "does not newly fail... for tickets that predate this taxonomy."
- Whether "subsystem/topic" tags (combat, economy, cognition, faction, resource, ...) should
  eventually merge into `layer` or stay a deliberately finer-grained complement is a Plan-phase
  design call, not resolved by this investigation (see Design Constraints subsection below for
  the concrete scenario — cross-cutting topics like `faction` — that argues for keeping them
  distinct).
- Reject vs. warn severity: `validate_frontmatter.py` already hard-exits 1 on `layer`/`status`/
  `authority`/`audience`/`phase`/`artifact_type` violations (`main():257-264`) — no existing
  "warn but pass" code path exists anywhere in this file today. Introducing a warn-only severity
  for `tags` alone would be a new pattern in this tool, not a reuse of an existing one; Plan should
  decide explicitly whether to introduce that new pattern or match the existing all-or-nothing
  hard-reject precedent.
- `sim` (33 uses) vs. `simulation` (3 uses) — re-verification found this pairing more lopsided
  than assumed; Plan should treat `sim` as the likely canonical form if these are confirmed
  synonyms, rather than defaulting to the longer spelling the way `observability`/`cognition` are
  probably the intended canonical forms for `obs`/`cog`.

### Design Constraints from Future Usage Scenarios (carried from ticket Request Summary)

The ticket explicitly requires the taxonomy's category design to be validated against five future
scenarios before Plan is considered done (AC: "each scenario should be able to name which category
its routing logic would eventually read"). Recorded here as investigation context, not decided:

1. **Tag-driven skill suggestion** (feeds `TCK-20260704-SKILL-TRIGGER-COVERAGE`) — needs a
   `process/skill-signal` category whose tag spellings line up 1:1 with skill names (e.g.
   `api-design`, `performance`, `debugging`).
2. **Tag-driven process/gate routing** — same category, e.g. a future `security`/`hardening` tag
   triggering an extra review step, analogous to `authority: P0` already getting special handling.
3. **Cross-cutting discovery `layer`'s 19-value enum can't provide** — e.g. `faction` spans `ai`/
   `systems`/`social` layers; a `subsystem/topic` category tag would let one query find "everything
   about factions" where `layer` alone cannot.
4. **Retro/analytics grouping** (feeds `TCK-20260704-RETRO-LOOP-ENFORCEMENT`) — needs tags to be a
   controlled, groupable vocabulary rather than 1273 mostly-singleton strings.
5. **Automatable skill-catalog health check** — same controlled-vocabulary prerequisite as #4,
   applied to a periodic script instead of `tier`/`workflow`-based grouping.

Design implication already reflected in the ticket's Scope: a distinct `process/skill-signal`
category, kept separate from generic `subsystem/topic` and `quality-attribute` tags specifically
so scenarios 1-2 have an unambiguous category to read from later.

## Anti-Drift Hazards

- Do not design the taxonomy as a single frozen list of every currently-observed tag. 1273
  existing tags include a large amount of legitimately one-off, ticket-specific detail
  (`grade_thresholds`, `feature_flag`, `dungeon_crawl`) that is not evidence of a missing category.
  The taxonomy must define **categories and canonical-form rules**, not pre-enumerate every valid
  subsystem tag — over-constraining this would recreate the same problem the 19-value `LAYER_VALUES`
  enum already deliberately avoids by staying coarse.
- Do not let the corrected duplicate-group table (the 4 miscategorized "singleton" pairs above)
  get silently re-copied from an older draft during Plan — `phase-1`/`phase1`,
  `phase-2`/`phase2`, `phase-4`/`phase4`, and `phase-0`/`phase0` all carry substantial counts on
  both sides and are exactly as significant as `phase-5`/`phase5`, `phase-3`/`phase3`, and
  `phase-6`/`phase6`.
- Do not couple this ticket's validator change to a whole-directory re-validation of all 1001
  historical tickets without first confirming (per the open question above) whether that mode is
  ever actually invoked — building an unneeded grandfather/exemption mechanism would be scope
  creep the ticket's Out of Scope section already warns against ("no backfill").
- Do not treat `INFRA-180` as unrelated just because this ticket is "tooling, not simulation
  mechanics" — the parity ledger's own scope explicitly includes doc-tooling parity (`support_boundary:
  "Doc tooling only"` is still a tracked, `verified`-status entry), and `CLAUDE.md`'s Parity rule
  applies to any logic change, not only simulation-behavior changes.

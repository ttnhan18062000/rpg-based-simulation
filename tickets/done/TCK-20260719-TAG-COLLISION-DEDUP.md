---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260719-TAG-COLLISION-DEDUP
phase: done
date: 2026-07-19
tags: [tagging, data-quality]
---

# TCK-20260719-TAG-COLLISION-DEDUP

## Title
Fix duplicate-meaning tags across the ticket/artifact corpus (simulation-quality/simulation_quality and 7 other collision groups)

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Direct user request: "I found that there some duplicated meaning tags, for
example: simulation-quality and simulation_quality, fix them, and also
update all related documents for the recent works." A full corpus scan
found 8 tag collision groups (same real meaning, different literal
spelling) — 5 need renaming to an already-registered or newly-registered
canonical hyphenated form, and 3 (`p0`/`p1`/`p2` as tags, any case) need
removal entirely, since they duplicate the ticket's own dedicated
`## Priority` body field and `tools/tag_registry.py`'s own
`canonical_form_violation()` already says so.

## Scope
- Register 3 missing canonical tag forms (`grand-strategy`,
  `dungeon-crawl`, `grade-thresholds`) via real `tag_registry.py add` calls.
- Rename every occurrence of 5 non-canonical literal tags to their
  canonical form: `simulation_quality`→`simulation-quality`,
  `grand_strategy`→`grand-strategy`, `feature_flag`/`feature-flag`
  (singular)→`feature-flags` (already-registered plural),
  `dungeon_crawl`→`dungeon-crawl`, `grade_thresholds`→`grade-thresholds`.
- Remove `p0`/`P0`/`p1`/`P1`/`p2`/`P2` from every `tags:` list they appear
  in (3 collision groups) — not renamed, removed.
- Fix regardless of ticket date — none of the affected files use the
  pre-TCK-naming legacy format this project's precedent otherwise exempts,
  and a tag-list edit carries none of the structural-retrofit risk that
  motivates that exemption.
- Update `docs/guides/ticket_reporting.md`'s Pillar 1 section, which
  currently describes the `simulation_quality` retag as out-of-scope/
  deferred — no longer true after this ticket.
- Spot-check (not redo) today's three closed epics'
  (`TCK-20260718-CANONICAL-FIELD-ENUMS-EPIC`,
  `TCK-20260718-AGENTOPS-STATS-BOARD-EPIC`,
  `TCK-20260718-GLOSSARY-TOOLTIPS-EPIC`) docs for stale references.
- `make knowledge-index-update` after all `docs/` edits.

## Out of Scope
- Any tag not in one of the 8 identified collision groups.
- `docs/guidelines/tag_taxonomy.md`'s historical "19 confirmed
  format-duplicate groups" claim from the original pre-registry review —
  that's dated context describing a past state, not a live claim to update.
- Redoing any of the three epics' own docs-update work.
- Any change to `tag_registry.py`'s code — the fix is data-only (new
  registry rows + corpus tag-list edits).

## Acceptance Criteria
- [x] `grand-strategy`, `dungeon-crawl`, `grade-thresholds` appear in
      `python3 tools/tag_registry.py list`.
- [x] A fresh corpus-wide collision-group re-scan finds zero remaining
      occurrences of `simulation_quality`, `grand_strategy`,
      `feature_flag`/`feature-flag` (singular), `dungeon_crawl`,
      `grade_thresholds`, or `p0`/`P0`/`p1`/`P1`/`p2`/`P2` as a tag.
- [x] `docs/guides/ticket_reporting.md` no longer describes the
      `simulation_quality` retag as deferred/out-of-scope.
- [x] `make knowledge-index-update` run successfully.

## Related Tickets
None — standalone data-cleanup ticket.

## Related Docs
- docs/guidelines/tag_taxonomy.md
- docs/guides/ticket_reporting.md
- docs/plans/tag_dedup/proposal_tag_corpus_dedup.md

## Related Stored Artifacts
staging_artifacts/TCK-20260719-TAG-COLLISION-DEDUP/ (to be migrated to
stored_artifacts/ on close)

## Related Code Areas
- tools/tag_registry.py (read-only — real API calls only, no code edits)
- docs/guidelines/tag_registry.jsonl (append-only registrations)

## Assumptions / Open Questions
None outstanding — the legacy-scope decision (fix all dated occurrences,
not just post-cutoff ones) is made and documented in investigation.md, not
left open.

## Implementation Notes

Execution-context deviation, self-flagged per this session's established
precedent: this ticket's `implement-ticket.js` pipeline was executed
directly (Read/Edit/Bash/Write) rather than via the specialized
ticket-scoper/investigator/planner/architecture-reviewer/implementer/
test-scoper/parity-updater/done-checker agent roles — this execution
context had no Agent-tool subagent access. All phases were still performed
in full and in order (Scope → Investigate → Plan → Implement → Test →
Finalize; Review/Architecture-Verify skipped in spirit since there is no
architectural surface here — pure ticket/doc metadata, no durable-state or
API-boundary concern).

Registered 3 new canonical tags via real `tools/tag_registry.py add` calls
(`grand-strategy`, `dungeon-crawl`, `grade-thresholds`, all `subsystem-topic`
— category determined by reading each tag's actual usage context in the
corpus, not assumed). Discovered during Investigate that the `feature-flag`
collision group actually had 3 literal spellings, not 2 — the corpus also
already had an already-registered **plural** form, `feature-flags`, that my
initial normalized-grouping scan missed (singular/plural is a different
axis than underscore/hyphen normalization); caught by cross-checking every
planned rename target against the full registry list before implementing,
and folded both `feature-flag` and `feature_flag` into the existing
`feature-flags` instead of registering a redundant new singular form.

Wrote a one-time Python script
(`/tmp/claude-1000/tagdedup_scratch/fix_tags.py`, not committed — scratch
file) that parses each file's frontmatter via the real
`validate_frontmatter.extract_frontmatter`, rewrites only the `tags:` line
(rename or entry-removal per the mapping above), and leaves every other
line byte-identical. Dry-tested on one file first (`git diff` confirmed
exactly one line changed), then ran corpus-wide: 76 files touched across
`tickets/done/`, `tickets/inprogress/`, and `stored_artifacts/` (`tickets/todos/`
had zero hits).

**Legacy-scope decision** (the one open question flagged in investigation.md):
fixed every occurrence regardless of ticket date, including 3 pre-2026-07-04
SIMQ-UPLIFT tickets `ticket_reporting.md` had previously left alone as
"out of scope for the registry ticket." Reasoning: this project's
established legacy-exemption precedent (`STATUS-DRIFT-REPAIR`,
`LAYER-REGISTRY-CONVERSION`) exists to avoid forcing a new section
structure or naming convention onto old-format tickets — a `tags:`
spelling correction is a one-line list edit, not a structural retrofit, so
that risk doesn't apply. The user's request was "fix them," not "fix them
going forward."

**Verification** (genuine before/after comparison, not a single post-hoc
scan, matching this session's established discipline): re-ran the exact
corpus-wide collision-group scan post-fix — zero remaining collision
groups, zero remaining `p0`/`p1`/`p2`/`P0`/`P1`/`P2`-as-tag occurrences,
223 total `simulation-quality` uses (0 `simulation_quality` remaining).
Then ran a genuine `git stash`/`pop` before-after `validate_frontmatter`
comparison across all 77 changed ticket/artifact files: the only diff
between before and after is that 6 pre-existing `tags:`-canonical-form
violations (on the 2 non-legacy `TCK-20260704-SIMQ-*` stored_artifacts
sets my fix targeted) are now gone — every other pre-existing violation
(unrelated `status:`/`phase:`/`ticket_id:` field issues on other legacy
files) is byte-identical before and after, proving zero new violations
introduced.

`docs/REGISTRY.yaml` regenerated (1447 entries, up from 1446 — includes
this ticket's own entry) after the corpus edits, per this project's
Finalize rule. `python3 tools/tag_report.py` re-run directly: 49 unique
tags across 138 post-taxonomy included tickets, `simulation-quality` shows
53 uses there, correctly classified `subsystem-topic`, zero
`unclassified`/non-canonical findings.

Spot-checked (not re-audited) the three epics closed earlier today for
stale doc references per the user's "update all related documents for the
recent works" request: found and fixed one genuine stale claim in
`docs/observability/agent_ops_dashboard_contract.md` (`StatsView.tsx`
section still said "three plain `<table>`s... incomplete artifacts" —
confirmed via direct source read that only 2 tables exist now, the
incomplete-artifacts table was removed by an earlier same-day change;
corrected the count and added a note on where that data still lives).
`docs/guides/agent_ops_dashboard.md` was already correctly updated (no
stale reference found). `docs/parity_ledger/infrastructure.yaml`'s
INFRA-278 entry mentioning Layer's former hardcoded-enum state is
correctly-scoped historical narrative describing the pre-conversion state,
not a live claim — left as-is.

## Test Summary
- `python3 -m pytest tests/tools/test_tag_registry.py
  tests/tools/test_validate_frontmatter.py
  tests/tools/test_generate_registry.py -q` — 157/157 passing (one
  transient failure before `docs/REGISTRY.yaml` regeneration, correctly
  proving the registry drift was real; passing after regeneration).
- `python3 tools/tag_registry.py list` — confirmed `grand-strategy`,
  `dungeon-crawl`, `grade-thresholds` all present.
- `python3 tools/tag_report.py` — 49 unique tags, 0 unclassified, 0
  non-canonical findings.
- Corpus-wide collision-group re-scan (the same technique as
  Investigation's original scan) — 0 remaining collision groups.
- Genuine `git stash`/`pop` before/after `validate_frontmatter` comparison
  across all 77 changed files — proves 0 new violations, exactly the 6
  targeted violations resolved.

## Files Changed
- `docs/guidelines/tag_registry.jsonl` (3 new entries: `grand-strategy`,
  `dungeon-crawl`, `grade-thresholds`)
- 76 ticket/artifact files under `tickets/done/`, `tickets/inprogress/`,
  `stored_artifacts/` — `tags:` frontmatter line only, one rename/removal
  edit per file (full list in `git diff --stat`)
- `docs/guides/ticket_reporting.md` (Pillar 1 Legacy/historical context
  section — resolution note added)
- `docs/observability/agent_ops_dashboard_contract.md` (stale
  incomplete-artifacts table count fixed, spot-check finding)
- `docs/REGISTRY.yaml` (regenerated)

## Completion Summary
Fixed all 8 tag-collision groups found in a full corpus scan: 5 renamed to
their canonical hyphenated form (registering 3 previously-missing forms,
folding a 3-way singular/plural/underscore collision into one existing
registered tag), 3 forbidden-priority-duplicate groups removed entirely
per `tag_registry.py`'s own documented policy. Fixed regardless of ticket
date, closing a gap `docs/guides/ticket_reporting.md` had explicitly left
open since `TCK-20260706-TAG-REPORT-TOOL`. Verified via genuine before/after
comparison (not a single post-hoc scan): 0 new violations introduced, 0
remaining collision groups. Spot-checked today's three closed epics' docs
and fixed one real stale reference found in the process.

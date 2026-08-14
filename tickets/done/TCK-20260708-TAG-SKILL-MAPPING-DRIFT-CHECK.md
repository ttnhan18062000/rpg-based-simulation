---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK
phase: done
date: 2026-07-08
tags: [ai, workflows, tagging, ticket-scoper]
---

# TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK

## Title
Add an automated consistency check for the 4 hand-duplicated tag->skill mapping table copies

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
The `Process/Skill-signal` tag -> suggested-skill mapping (`api-design` -> `/api-design-principles`,
`debugging` -> `/debugging-strategies` or `world-debugger`, `performance` ->
`/python-performance-optimization`, `security` -> `/security-review`) exists as 4 independently
hand-maintained textual copies with no automated consistency check between them:

1. `.claude/agents/ticket-scoper.md` (table rows currently at lines 91-94)
2. `docs/guides/ticket_tagging.md` (table rows currently at lines 52-55)
3. `.claude/workflows/implement-ticket.js` (table rows currently at lines 71-74, inside the "Load
   existing ticket" Scope-phase prompt, Step 3)
4. `.claude/workflows/create-tickets.js` (mapping lines currently at 601-607, inside the Structure-phase
   prompt's `suggested_skills:` block)

This was flagged as an "Anti-Drift Hazard" in `stored_artifacts/TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION/investigation.md`
("Triple-copy mapping table... there is no single source of truth today") but that count is itself
wrong — re-verified during this scoping pass: `tickets/done/TCK-20260705-TAG-SKILL-SUGGEST.md`'s own
Completion Summary and Implementation Notes correctly document **4** independent copies (it names
`create-tickets.js` explicitly as the 4th), and the investigation's own Part 1 section separately lists
all 4 compute sites — only its later "Anti-Drift Hazards" bullet undercounts to 3. This ticket's Scope
and any future check must treat 4 as the correct, current count.

The mapping has not yet actually diverged (all 4 confirmed re-read during this scoping pass, current line
numbers matched what was expected, semantic mapping identical across all 4), but it is unprotected: any
future edit to one copy (e.g. adding a 5th tag, changing `security`'s target skill) has no mechanism to
catch a missed sibling update. This exact failure class — a hand-duplicated table across
`.claude/skills/`/`.claude/workflows/`/`.claude/agents/` going stale — was independently fixed today via
two hotfix tickets (`TCK-20260708-SKILL-CREATE-TICKETS-WORKFLOW-TOOL-STALE`,
`TCK-20260708-SKILL-IMPLEMENT-TICKET-PHASE-DRIFT`), both reactive fixes to already-diverged content. This
ticket is the proactive counterpart: build the detection mechanism before divergence happens, matching
`docs/guidelines/tag_taxonomy.md`'s Purpose section, which explicitly names "Scenario 5: Automatable
skill-catalog health check" (reading the Process/Skill-signal category) as a documented but never-built
future use.

**Important wording caveat found during this scoping pass:** the 4 copies are not currently
word-for-word identical even though they are semantically identical. `.claude/agents/ticket-scoper.md`
and `docs/guides/ticket_tagging.md` carry longer parenthetical commentary (e.g. explaining the
`world-debugger` carve-out's relationship to `src/worldgeneration/`, and noting `security` has no
`CLAUDE.md` precedent row) that `.claude/workflows/implement-ticket.js` and
`.claude/workflows/create-tickets.js`'s terser prompt-template versions omit. Any consistency check built
under this ticket must compare the **extracted (tag -> target) mapping pairs**, not raw table text,
or it will produce false-positive failures against these legitimate, already-existing wording
differences.

## Scope
- Design and implement one automated check (a pytest test under `tests/tools/`, following the existing
  `tests/tools/test_tag_registry.py`/`test_tag_report.py` pattern) that:
  - Extracts the tag -> skill/agent mapping from each of the 4 files listed above (parsing markdown
    tables from the two `.md` files, and the JS template-string table fragments from the two `.js`
    files).
  - Normalizes each extraction down to comparable `{tag: target}` pairs (where `target` for `debugging`
    captures both the default skill and the world-debugger carve-out condition), ignoring prose/wording
    differences that don't change the mapping itself.
  - Asserts all 4 extractions are pairwise equal; fails loudly (a normal pytest failure) with a diff-style
    message identifying which file(s) disagree and on which tag, if not.
- Decide during implementation (record the decision, don't leave it silently assumed) whether the
  extraction logic belongs inline in the test file or as a small reusable helper under `tools/` (mirroring
  `tools/tag_registry.py`'s `check_tags_registered()` pattern of "core logic in `tools/`, test imports
  it") — pick based on whether anything else could plausibly reuse the extractor.
- Update `docs/guidelines/tag_taxonomy.md`'s Scenario 5 row ("Automatable skill-catalog health check") to
  reference the new check's location once built, since that row currently only names the future scenario
  without pointing at an implementation.
- Run the new check against the current (as of this ticket's scoping) state of all 4 files to confirm it
  passes cleanly — i.e., confirm no divergence has occurred since this ticket's Request Summary was
  written.

## Out of Scope
- De-duplicating the 4 copies into one true single source of truth (e.g. via a shared imported constant,
  a generated-from-YAML template, or a build step). These are agent-prompt text blobs spread across
  markdown files and JS template strings, not importable modules sharing a runtime — collapsing them to
  one source is a larger, separate design question. This ticket's job is to make future drift **loud**
  (a failing test), not to make drift **structurally impossible**.
- Expanding the tag->skill mapping itself (adding a 5th `Process/Skill-signal` tag, changing any existing
  tag's target skill). Out of scope per `TCK-20260705-TAG-SKILL-SUGGEST`'s own deferred question; this
  ticket only adds detection over the mapping as it exists today.
- Building any of `TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION`'s other candidate tunings (auto-invoke
  suggested skills, Parity-phase skip on docs-only changes). Candidate 2 (security gate) from that
  investigation was already built separately as `TCK-20260705-WORKFLOW-SECURITY-GATE`; not touched here.
- Wiring the new check into a git pre-commit hook or CI gate — this ticket only adds the pytest-level
  check itself. Whether it should also block commits/CI is a follow-up decision, not assumed here.
- Any change to the mapping's actual content in any of the 4 files (this ticket only reads them to build
  the check; if the check reveals a real, pre-existing divergence, fixing that divergence is a separate
  follow-up ticket, not folded into this one).

## Acceptance Criteria
- [x] A new automated check exists (pytest test under `tests/tools/`, optionally backed by a `tools/`
      helper) that independently extracts the tag->skill mapping from all 4 files
      (`.claude/agents/ticket-scoper.md`, `docs/guides/ticket_tagging.md`,
      `.claude/workflows/implement-ticket.js`, `.claude/workflows/create-tickets.js`) and asserts they
      are pairwise equal on the normalized `{tag: target}` pairs.
- [x] The check passes against the current state of all 4 files (run and confirmed, not assumed).
- [x] The check's failure mode is demonstrated at least once during implementation (e.g. a scratch/local
      mutation of one copy) to confirm it actually fails loudly and identifies the diverging file/tag,
      not just that it passes today.
- [x] The check tolerates the documented legitimate wording differences between the terse JS-prompt
      copies and the more verbose markdown copies (does not false-positive on prose-only differences).
- [x] `docs/guidelines/tag_taxonomy.md`'s Scenario 5 row is updated to reference the new check's file
      location.
- [x] `python3 -m pytest tests/tools/ -q` (or the narrower scoped subset covering the new test file) runs
      clean, including the new test alongside existing `tests/tools/test_tag_registry.py` and
      `test_tag_report.py`.

## Related Tickets
- TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION (done — first flagged the "triple-copy" hazard, itself
  undercounted at 3; this ticket corrects that to 4 and acts on the hazard)
- TCK-20260705-TAG-SKILL-SUGGEST (done — introduced the 4-copy mapping table in the first place; its own
  Implementation Notes correctly document all 4 copies and label the duplication "a disclosed, accepted
  hazard, not a defect")
- TCK-20260708-SKILL-CREATE-TICKETS-WORKFLOW-TOOL-STALE (done — reactive fix for the same failure class,
  stale `Workflow`-tool instructions in `create-tickets/SKILL.md`; precedent this ticket's proactive
  detection work follows)
- TCK-20260708-SKILL-IMPLEMENT-TICKET-PHASE-DRIFT (done — reactive fix for the same failure class, stale
  phase list in `implement-ticket/SKILL.md`; sibling precedent)
- TCK-20260705-WORKFLOW-SECURITY-GATE (done — built Candidate 2 from the tag-tuning investigation
  separately; not touched here, cross-referenced only for context on which candidates from that
  investigation have already shipped)

## Related Docs
- docs/guidelines/tag_taxonomy.md (Purpose section, Scenario 5 row — "Automatable skill-catalog health
  check"; update to reference the new check once built)
- docs/guides/ticket_tagging.md ("Skill Suggestions From Tags" section — one of the 4 copies the check
  reads; not modified beyond what's already tracked as a copy)
- docs/guides/README.md (cross-reference only if it indexes tag/tagging tooling docs; not expected to
  need a change since this ticket adds a test, not a new guide)

## Related Stored Artifacts
- stored_artifacts/TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION/investigation.md (Anti-Drift Hazards
  section — the original, undercounted "triple-copy" flag; Part 1 — the correctly-counted 4-compute-site
  enumeration this ticket's Request Summary cites directly)
- stored_artifacts/TCK-20260705-TAG-SKILL-SUGGEST/ (context on how and why the table was originally
  duplicated across 4 sites rather than centralized)

## Related Code Areas
- .claude/agents/ticket-scoper.md (read + extracted from, not modified unless the check reveals a real
  divergence)
- docs/guides/ticket_tagging.md (read + extracted from; same caveat)
- .claude/workflows/implement-ticket.js (read + extracted from; same caveat)
- .claude/workflows/create-tickets.js (read + extracted from; same caveat)
- tests/tools/ (new test file added here, following test_tag_registry.py/test_tag_report.py conventions)
- tools/ (possible new small helper module, if Plan decides the extraction logic warrants one)

## Assumptions / Open Questions
- This ticket only ADDS a detection/consistency mechanism over the 4 existing copies — it does NOT
  attempt to de-duplicate the table into one true single source of truth via imports/includes, since
  these are agent-prompt text blobs spread across markdown and JS template strings, not importable
  modules sharing a runtime. True dedup (e.g. generating all 4 from one YAML/JSON source at build/lint
  time) is a larger, separate design question, deliberately deferred — this ticket's job is to make
  future drift LOUD (a failing test) rather than silent, matching `tag_taxonomy.md`'s Scenario 5 framing
  exactly, not to solve the harder single-source-of-truth refactor. If this assumption is wrong (i.e. the
  user actually wants the harder dedup-at-source solve now), the scope of this ticket is invalidated and
  should be re-scoped as a larger effort.
- Assumes a pytest-based check (parsing the 4 files' text directly) is an acceptable mechanism, versus a
  standalone `tools/` CLI script run manually or via a hook. Leaning pytest because it matches this
  repo's existing `tests/tools/test_tag_registry.py` precedent for agent-tooling correctness checks and
  runs automatically under the existing "Run relevant existing tests" workflow discipline — but this is
  a Plan-phase call, not fixed here.
- Assumes normalizing away prose/wording differences (see the wording caveat in Request Summary) is the
  correct check semantics, rather than requiring byte-identical table text across all 4 copies. If byte-
  identical text were actually desired, the check would need to also flag the wording differences already
  present today as a pre-existing failure — which would make this ticket's own Acceptance Criterion 2
  ("passes against current state") impossible to satisfy as written, so byte-identical equality is
  treated as the wrong semantics for this check.
- layer is set to `ai` (Claude agent-orchestration domain, per `docs/guidelines/tag_taxonomy.md`'s own
  note that `layer: ai` in this repo means the agent-tooling system, not gameplay AI/cognition),
  consistent with the two 2026-07-08 precedent tickets for this exact failure class. Not defaulting to
  `misc` since this maps cleanly.

## Implementation Notes
Implemented exactly per `staging_artifacts/TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK/plan.md`'s 7
ordered steps, with one discovered-and-fixed parsing bug (see Deviations in plan.md).

- **`tools/tag_skill_mapping_check.py`** (new): `KNOWN_TAGS` allowlist (with the module docstring's
  disclosed "de-facto 5th copy" limitation, verbatim per the plan's Decision); `extract_pairs_markdown`
  (Format A — raw markdown pipe table, header/separator rows skipped naturally since neither cell
  matches the backtick-tag pattern); `extract_pairs_js_escaped` (Format B — same pipe-split approach,
  tag regex tolerates an optional literal backslash before/after the backtick); `extract_pairs_arrow_list`
  (Format C — anchor-bounded line-based state machine, raises `ValueError` on a missing anchor rather
  than silently returning an empty/partial result); `normalize_target` (reduces a raw target string to
  `(primary_skill, carveout_agent, carveout_paths)`); `check_tag_skill_mapping_consistency(root=None)`
  (reads and normalizes all 4 live files, compares pairwise per tag, returns a structured mismatch list
  keyed by tag with each of the 4 files' normalized tuple).
- **`tests/tools/test_tag_skill_mapping_check.py`** (new): 10 tests — one per parser format, two for
  `normalize_target` (prose-only differences, plus one added test for the excluded-path false-positive
  discovered during implementation — see below), one live-repo-passes test, and two
  synthetic-divergence tests (mutate a `tmp_path` fixture copy, confirm the check fails and correctly
  identifies the diverging file/tag).
- **`docs/guidelines/tag_taxonomy.md`**: Scenario 5 row updated to name `tools/tag_skill_mapping_check.py`
  and `tests/tools/test_tag_skill_mapping_check.py` (kept the row's original 2-column shape — appended
  the reference into the existing "Category it reads" cell rather than adding a 3rd column only to this
  row, to avoid misaligning the table).
- **Bug found and fixed during Step 7's live verification run** (not anticipated by the plan/investigation):
  the naive `carveout_paths = re.findall(r'src/[\w./]+', raw_target)` approach specified in the plan's
  Step 4 picked up a false 6th path (`src/worldgeneration/`) from `ticket-scoper.md`'s debugging row —
  that row has a trailing parenthetical explicitly saying `src/worldgeneration/` is *excluded* from the
  carve-out (a pre-existing, separately-flagged oddity the ticket's own Out of Scope names verbatim:
  "Do NOT expand the debugging carve-out path set or touch the pre-existing worldgeneration/ ...
  mismatch"). Reading this excluded mention as an included path caused a false mismatch against the
  other 3 copies on first live run, which would have failed AC2 and AC4. Fixed by bounding path
  extraction to the actual "path under X, Y, or Z" condition clause via a new `_CARVEOUT_LIST_RE` anchor
  regex, so trailing prose (including exclusion parentheticals) is no longer scanned. Verified against
  the real file and covered by a new unit test
  (`test_normalize_target_ignores_excluded_path_mentioned_outside_carveout_list`). No content in any of
  the 4 real source files was touched — this is a fix to the check's own extraction logic only.

## Test Summary
- `python3 -m pytest tests/tools/test_tag_skill_mapping_check.py -v` — 10/10 passed.
- `python3 -m pytest tests/tools/ -q` — 631 passed, 30 failed. All 30 failures are pre-existing and
  unrelated to this ticket: 28 in `tests/tools/test_knowledge_search.py` (knowledge-search build/query
  tests unrelated to tag/skill mapping) and 2 in `tests/tools/test_search_mcp.py`
  (`.mcp.json` command/args assertions — unrelated `.mcp.json` config drift). None touch
  `tag_skill_mapping_check.py`, `tag_skill_mapping_check`-adjacent files, or any of the 4 mapping-table
  source files. Not investigated further per this ticket's scope and the Testing Rule's guidance to
  scope to the domain under modification.
- `make knowledge-index-update` run after the `docs/guidelines/tag_taxonomy.md` edit (11 files
  re-embedded incrementally, including the changed doc).
- `graphify update .` run after adding the new `tools/`/`tests/` files.

## Files Changed
- `tools/tag_skill_mapping_check.py` (new)
- `tests/tools/test_tag_skill_mapping_check.py` (new)
- `docs/guidelines/tag_taxonomy.md` (Scenario 5 row only)

## Completion Summary
Built a proactive drift-detection check for the 4 hand-duplicated `Process/Skill-signal` tag ->
skill mapping table copies (`ticket-scoper.md`, `ticket_tagging.md`, `implement-ticket.js`,
`create-tickets.js`), following `tools/tag_registry.py::check_tags_registered()`'s
tools/-helper-plus-pytest-import precedent. The check extracts each copy's mapping via 3
format-specific parsers, normalizes to comparable `(primary_skill, carveout_agent, carveout_paths)`
tuples (tolerating legitimate prose differences), and asserts pairwise equality — currently passing
against the live, undiverged state of all 4 files. All 6 acceptance criteria met; no mapping content,
git hook, or CI wiring was touched, per Out of Scope.

---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260720-SKILL-MAPPING-DEDUP
artifact_type: investigation
tags: [tagging, workflows, skills]
---

# Investigation — TCK-20260720-SKILL-MAPPING-DEDUP

## Current Behavior

The `Process/Skill-signal` tag -> suggested-skill mapping (4 entries: `api-design`, `debugging`,
`performance`, `security`) is hand-duplicated in **5** places today, not 4 — the ticket's own Request
Summary undercounts by one (it names the drift-checker's `KNOWN_TAGS` as a "5th copy" separately, but
`implement-ticket.js` actually embeds the table **twice**, once per execution branch):

1. `.claude/agents/ticket-scoper.md:89-94` — markdown pipe table, used when `ticket-scoper` drafts a
   brand-new ticket (the `implement-ticket.js` "new ticket" branch delegates to this agent's own
   Output-contract table rather than embedding a second copy itself).
2. `docs/guides/ticket_tagging.md:56-61` — markdown pipe table, human-facing doc copy.
3. `.claude/workflows/implement-ticket.js:112-118` — markdown pipe table inside a JS template
   string (escaped backticks), used **only** on the "load existing ticket" Scope branch (the
   ticket-file-already-exists path at line 96's ternary `ticketId ? ... : ...`).
4. `.claude/workflows/create-tickets.js:511-519` — arrow-list (`tag -> target`) inside a JS template
   string, used by the Structure phase for batch-created tickets; `debugging`'s target wraps across
   3 continuation lines (512-517).
5. `tools/tag_skill_mapping_check.py:41` — `KNOWN_TAGS = frozenset({"api-design", "debugging",
   "performance", "security"})`, the drift-checker's own allowlist, explicitly disclosed in its
   module docstring (lines 29-35) as a de-facto 5th copy of the *tag set* (not the full mapping —
   it has no target-skill values, just tag names).

None of these read `registries/tag_registry.jsonl`'s 4 `process-skill-signal` rows for the mapping
today — `tag_registry.jsonl` entries currently carry only `{tag, category, added_date, note}`
(`tools/tag_registry.py:189-194`, `add_tag()`). The `note` field on each of the 4 rows is free-text
prose that happens to *mention* the target skill (e.g. `"security"`'s note: `"seed: matches
/security-review skill 1:1 per ticket_tagging.md"`) but is not machine-read by anything — it is not
a `triggers_skill`-shaped structured field, and no consumer parses it.

`tools/tag_registry.py`'s `add_tag()` (lines 167-201) is genuinely append-only: it raises
`ValueError` if the tag already exists (lines 182-187) and the CLI (lines 209-242) has no `update`
or `edit` subcommand — text and tests (`tests/tools/test_tag_registry.py:168-183`,
`test_add_tag_is_append_only_existing_entries_unchanged`) both enforce this as a hard invariant, not
an incidental gap. The 4 `process-skill-signal` rows already exist in
`registries/tag_registry.jsonl` (added 2026-07-06, confirmed via direct read) — adding a
`triggers_skill` field to their JSON would require either widening the writer for new rows only
(leaving the 4 existing rows without the field) or literally rewriting those 4 already-committed
lines, which is exactly the invariant conflict the ticket names.

`tools/tag_skill_mapping_check.py` (built by `TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK`, done)
compares the first 4 copies pairwise on a normalized `(primary_skill, carveout_agent,
carveout_paths)` tuple (`normalize_target()`, lines 159-170) and returns a mismatch list
(`check_tag_skill_mapping_consistency()`, lines 180-203). Its own docstring (lines 17-19) states
plainly: "it does not write to any of them, and it is not a single source of truth for the mapping
... deriving KNOWN_TAGS from one of the 4 files would make that file an implicit source of truth for
the other 3, which contradicts this ticket's own Out of Scope (no de-duplication...)." That prior
ticket explicitly declared dedup out of scope — this ticket (per its own Request Summary) reopens
that decision.

10 tests in `tests/tools/test_tag_skill_mapping_check.py` encode real format-specific parsing
knowledge: `extract_pairs_markdown` (Format A, lines 74-95), `extract_pairs_js_escaped` (Format B,
lines 98-120), `extract_pairs_arrow_list` (Format C, lines 123-156, anchor-bounded via
`_ARROW_START_ANCHOR`/`_ARROW_END_ANCHOR` string literals matching `create-tickets.js:511` and
`:519` verbatim — a rename of either anchor string breaks this parser, not just a mapping-content
edit), `normalize_target` (3 tests), and `check_tag_skill_mapping_consistency` (3 tests, one of
which — `test_check_tag_skill_mapping_consistency_passes_against_live_repo_files`,
lines 175-178 — runs against the real repo files with no fixture, so it is a live regression
guard today).

The `debugging` tag's target is not a plain string in any of the 4 copies — it is a conditional:
default `/debugging-strategies`, overridden to `Agent(subagent_type: "world-debugger")` when
`Related Code Areas` includes a path under `src/worldassembly/`, `src/worldbuilding/`,
`src/worldmodules/`, `src/content/`, or `src/core/registries.py`. `ticket-scoper.md:92` additionally
carries a trailing parenthetical stating `src/worldgeneration/` is *excluded* from the carve-out
even though it appears in `world-debugger.md`'s own broader scope list — `normalize_target()`'s
`_CARVEOUT_LIST_RE` (lines 66-68) exists specifically to not misread that excluded mention as a 6th
included path (see Deviations in `stored_artifacts/TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK/plan.md`).
Any single-source encoding of the mapping must preserve this branch (skill + carve-out agent +
carve-out path set + the one explicit exclusion), not flatten it to a string, per this ticket's own
AC2.

`registries/tag_registry.jsonl` is also read by `src/api/agent_ops_dashboard/ingest.py:51-52`
(`import tag_registry`, `sorted(tag_registry.load_registry(self._repo_root).keys())` for the
dashboard's `tags` facet — confirmed via `docs/parity_ledger/infrastructure.yaml:4685-4693`) and by
`tools/tag_report.py:56-68` (`categorize_tag()`, reads `entry["category"]` only). Both consumers
read specific dict keys (`.keys()`, `entry["category"]`) rather than validating the entry's full
shape, so an additive field on new/all rows would not break either — worth confirming empirically in
Plan/Implement, not assumed here.

## Mechanics / Engine Constraints

None. This ticket is entirely agent/workflow tooling (`layer: ai` — Claude agent orchestration, per
`registries/layer_registry.jsonl`'s note distinguishing it from gameplay AI/cognition, which is
tracked under `strategy`/`cognition`). No `docs/mechanics/` chapter or `docs/engine/` contract
governs tag registries, skill routing, or agent-workflow prompt content — this space is governed
instead by `docs/guidelines/tag_taxonomy.md` and `CLAUDE.md`'s own Workflow Rule / Tags-as-hard-
allowlist rules, which this investigation treats as the relevant "constraints" in lieu of Mechanics
Bible chapters.

## Parity Ledger Overlap

None. Searched all 8 `docs/parity_ledger/*.yaml` files for `skill`, `tag_registry`, and
`suggested_skills`. The only hits are incidental token collisions (`skill_silence`/`xp_rate_zero`
progression mechanics in `progression.yaml`, `dataviz` skill usage notes in `infrastructure.yaml`
around the agent-ops dashboard build) or genuinely-unrelated `tag_registry.py` references from
`TCK-20260720-DASHBOARD-TAG-FACET-REGISTRY`'s `v2_evidence` entries
(`infrastructure.yaml:4685-4693`) — that entry documents the dashboard's `tags` facet reading
`tag_registry.load_registry()`, not the skill-mapping table this ticket touches. No parity ledger
entry names the tag->skill mapping, `tag_skill_mapping_check.py`, or the 4 consumer files. No P0
entries are implicated. If the Plan phase's chosen resolution changes what `load_registry()` returns
for the 4 existing rows (e.g. adding a `triggers_skill` key), it is worth a note to the
`TCK-20260720-DASHBOARD-TAG-FACET-REGISTRY` `v2_evidence` entry confirming the facet is unaffected —
not because parity requires it, but because that entry is the nearest existing documentation of a
second `tag_registry.jsonl` consumer.

## Prior Work

- **`TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK`** (done) — built `tools/tag_skill_mapping_check.py`
  and its 10 tests as a read-only pairwise comparator across the 4 (now: 4 mapping copies + 1
  tag-set allowlist) hand-maintained texts. Its plan.md explicitly rejected deriving `KNOWN_TAGS`
  from any one of the 4 files as "making that file an implicit source of truth," and its ticket
  declared true dedup Out of Scope. This ticket's Request Summary explicitly reopens that decision —
  confirmed genuine, not duplicate, work.
- **`TCK-20260705-TAG-SKILL-SUGGEST`** (done) — introduced the mapping as 4 independently
  hand-maintained copies in the first place (`ticket-scoper.md`, `ticket_tagging.md`, and by
  implication the 2 workflow JS files), per its own summary excerpt found via `search_docs`:
  "`docs/guidelines/tag_taxonomy.md`'s `Process/Skill-signal` category was designed specifically to
  serve 'Scenario 1: Tag-driven skill suggestion' — its canonical tag names ... map 1:1 to skill
  invocations."
- **`TCK-20260706-TAG-REGISTRY-DATA`** (done) — built `registries/tag_registry.jsonl` (then at
  `docs/guidelines/`) and `tools/tag_registry.py`'s append-only `add_tag()`/`load_registry()`, the
  exact invariant this ticket's Assumptions/Open Questions section names as the conflict.
- **`TCK-20260720-TAG-REGISTRY-RELOCATE`** (done, most recent, same batch) — moved
  `tag_registry.jsonl`/`layer_registry.jsonl`/`glossary_registry.jsonl` from `docs/guidelines/` to
  `registries/`, updating every active reference including `tools/tag_registry.py:116`'s
  `_REGISTRY_REL_PATH`. Confirmed live: `registries/tag_registry.jsonl` exists,
  `docs/guidelines/tag_registry.jsonl` does not. This ticket's own body text (Related Docs line 61:
  `docs/guidelines/tag_registry.jsonl`) is stale against that relocation — treat
  `registries/tag_registry.jsonl` as the real path throughout Plan/Implement, and correct the ticket
  body's Related Docs line as a drive-by fix when this ticket is next edited.
- **`docs/guidelines/tag_taxonomy.md`'s Purpose section, Scenario 5 row** (line 34, updated by the
  drift-check ticket) already anticipates this exact follow-up under the heading "Automatable
  skill-catalog health check," currently pointing at `tools/tag_skill_mapping_check.py` — this row
  will need another edit once this ticket decides the checker's fate (AC3).
- No prior ticket in `tickets/done/` or `stored_artifacts/` attempted the `triggers_skill`-on-registry-row
  design or any of the 3 candidate schema-conflict resolutions named in this ticket's own Assumptions —
  genuinely new design work for Plan.

## Risks and Open Questions

- **[BLOCKS PLAN, per this ticket's own AC5] Which of the 3 candidate resolutions to the
  append-only-vs-existing-4-rows conflict is chosen.** Per `tickets/todos/tag-registry-redesign/SEQUENCE.md`'s
  "Known Open Decisions" note (verbatim: "which of 3 candidate resolutions closes the conflict
  between `tag_registry.jsonl`'s append-only design and the need to edit 4 already-registered
  rows"), this is explicitly deferred to this ticket's own Investigate/Plan phases. This
  investigation surfaces the options and evidence but does **not** resolve it — that is Plan's
  decision, per the repo's Investigate/Plan boundary:
  - **(a) Widen `add_tag()`'s schema going forward only.** New rows get a `triggers_skill` field;
    the 4 existing rows stay without it, read via a fallback (e.g. a small hardcoded map keyed by
    tag name, scoped to exactly the 4 legacy rows, or a `.get("triggers_skill")` with `None`
    meaning "look up the legacy fallback"). Preserves the append-only invariant literally. Leaves a
    residual hardcoded fallback (arguably a 6th small copy, though bounded to exactly 4 tags with
    no target-skill duplication logic beyond a dict literal).
  - **(b) One-time explicitly-authorized rewrite of the 4 existing lines.** Directly contradicts
    `tag_registry.py`'s current invariant and its test
    `test_add_tag_is_append_only_existing_entries_unchanged`; would need an explicit sign-off
    recorded per the ticket's own AC4 wording ("or the invariant break is explicitly justified and
    recorded"). No prior ticket has ever done this — would be a first, and would need
    `tools/tag_registry.py` and its tests updated to support/permit the rewrite (currently `add_tag()`
    raises on any existing tag, with no code path for legitimate update).
  - **(c) Store the mapping in a location entirely separate from `tag_registry.jsonl` rows** (e.g. a
    small dedicated `registries/skill_mapping.json` or a Python constant module all 4+ consumers
    import/read). Sidesteps the append-only conflict entirely, at the cost of not fulfilling the
    ticket's own "Preferred approach" (Request Summary line 30) of encoding it as a
    `triggers_skill`-style field on the tag row itself — would need explicit justification for
    deviating from the ticket's stated preference.
  - This investigation notes but does not adjudicate: option (a) is the only one that requires zero
    change to `tag_registry.py`'s existing invariant/tests; option (c) is the only one that avoids a
    hardcoded-fallback residual; option (b) is the only one that fully unifies representation but
    breaks a tested invariant. Plan must pick one (or an explicitly justified 4th) and record the
    choice, per AC5.
- **3 different execution contexts need 3 different read mechanisms**, confirmed by reading the
  actual files, not assumed:
  - The 2 Node workflow files (`implement-ticket.js`, `create-tickets.js`) can shell out — a working
    precedent already exists at neither `implement-ticket.js:313-314` nor `create-tickets.js:578-579`
    as literally described in the ticket body (those exact line numbers were not found to contain a
    `python3 -c` subprocess pattern on the current `simulation_quality` branch — this should be
    re-verified in Plan against the current file state, since line numbers drift; a `python3 -c`/JSON-
    stdout-marker pattern does exist elsewhere in these files for other registry reads, e.g. the
    tag-registration check flow, and is the right precedent to reuse, but the exact anchor lines cited
    in the ticket body may be stale).
  - `.claude/agents/ticket-scoper.md` is a pure LLM-interpreted prompt — it cannot execute code. Any
    single source it reads must be either inlined at prompt-authoring time (defeats "single source")
    or read via an instruction telling the agent to run a shell command and use its output (the same
    pattern `implement-ticket.js`'s embedded ticket-scoper-role prompt already uses elsewhere for
    other registry lookups, e.g. `tools/tag_registry.py list` is referenced by name in
    `ticket-scoper.md:33`).
  - `docs/guides/ticket_tagging.md` is a pure human-read doc with no binding/execution mechanism —
    dedup for this file necessarily means "describes the single source and tells the reader to
    consult it live" (per this ticket's own scope line 36), not a runtime read.
- **`tag_skill_mapping_check.py`'s fate (AC3) is coupled to the resolution chosen above.** If the
  4 consumers all read one live source, pairwise-comparing-independent-texts becomes moot for the 2
  files that gain a runtime read (the Node workflows), but `ticket-scoper.md` and
  `ticket_tagging.md` will likely still contain *rendered* text (prompt content an LLM reads, or
  doc prose a human reads) even after pointing at a single source — meaning some form of "does this
  file's rendered text match the live source" check may still have a real job, just reframed from
  "compare 4 peers" to "compare each of N text-only copies against the 1 source." This is a design
  question for Plan, not resolved here.
- **The `KNOWN_TAGS` 5th-copy disclosure in `tag_skill_mapping_check.py`'s docstring (lines 29-35)
  was written under the drift-checker's own explicit "no dedup" scope** — if dedup happens, that
  disclosure's framing ("this is a deliberate, accepted decision... no code-level mitigation is
  planned") becomes stale regardless of which AC3 option is chosen, and needs at minimum a docstring
  edit (if repurposed) or removal (if the module is deleted).
- **Gap flagged, not an error:** the ticket's Assumptions/Open Questions line (body line 83) cites
  specific line numbers (`implement-ticket.js:313-314`, `create-tickets.js:578-579`) for a
  subprocess-JSON-marker precedent that this investigation could not confirm at those exact
  coordinates on the current branch — flagged per the Investigator's "if acceptance criteria
  reference behavior that doesn't exist yet, note it as a gap" instruction. Plan should re-locate the
  actual precedent (it likely exists nearby, e.g. in the tag-registration-check call site) rather
  than trust the cited line numbers verbatim.

## Anti-Drift Hazards

- **Do not let the single-source migration silently drop the `debugging` carve-out's conditional
  structure** (default skill + carve-out agent + carve-out path list + the one explicit
  `src/worldgeneration/` exclusion). This is explicitly named in the ticket's AC2 and is the exact
  shape `tag_skill_mapping_check.py`'s `normalize_target()` was built to compare — any single-source
  schema must be at least as expressive as that 3-tuple, not a flattened string.
- **Do not silently expand or edit the mapping's actual tag-set or target skills while doing this
  refactor.** This ticket's Scope is dedup, not a mapping-content change (mirrors the drift-check
  ticket's own Scope Guard: "Do NOT expand the tag->skill mapping itself"). Any content drift found
  incidentally during the migration should be flagged, not silently fixed inline, unless the ticket
  is explicitly re-scoped.
- **Do not let resolution-(a) (or any option) create a *new* undisclosed 6th copy.** If a hardcoded
  fallback map is used for the 4 legacy rows, it must get the same explicit disclosure treatment
  `tag_skill_mapping_check.py`'s `KNOWN_TAGS` got — an undisclosed shadow copy defeats the entire
  point of this ticket.
- **Do not touch `TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX`'s territory** (`create-tickets.js`'s
  Structure-phase tag-*category* restriction) — that is a separate, already-filed hotfix per this
  ticket's own Out of Scope and `SEQUENCE.md`'s "Related, Not Duplicated" note. This ticket touches
  `create-tickets.js` only for the tag->skill *mapping table*, not its tag-category validation logic.
- **Do not assume `implement-ticket.js`'s two branches (new-ticket vs. existing-ticket) collapse to
  one copy for free.** The "new ticket" branch (line 96 ternary's `false` arm) delegates to the
  `ticket-scoper` agent role and does not itself embed a table — only the "existing ticket" branch
  (lines 110-118) does. A fix that only touches the visible embedded table risks missing that the
  `ticket-scoper.md` delegation is the other de-facto instance already in scope as copy #1.
- **`TAG-TOUCHPOINT-CLEANUP`** (a sibling ticket in this same batch, not yet done) **owns the decision
  on whether `implement-ticket.js`'s "intentionally hand-synced string-match mirror" stays as-is** —
  per `SEQUENCE.md`'s Known Open Decisions. Confirm in Plan whether that note refers to this same
  embedded table (likely) or a different hand-synced mirror elsewhere in `implement-ticket.js`, so
  this ticket and that one do not silently conflict on the same file.

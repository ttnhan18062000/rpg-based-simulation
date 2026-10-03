---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260720-SKILL-MAPPING-DEDUP
artifact_type: plan
tags: [tagging, workflows, skills]
---

# Implementation Plan — TCK-20260720-SKILL-MAPPING-DEDUP

## Summary

Collapse the 5 hand-maintained copies of the `Process/Skill-signal` tag -> skill mapping into one
executable source in `tools/tag_registry.py`, and rewire every consumer to read it live instead of
embedding rendered text. The mechanism is a new `get_skill_mapping(root=None)` function that merges
(a) a `triggers_skill` field newly supported on registry rows going forward, with (b) a small,
explicitly disclosed `_LEGACY_SKILL_TRIGGERS` fallback dict covering exactly the 4 already-registered
`process-skill-signal` rows (`api-design`, `debugging`, `performance`, `security`) — preserving
`tag_registry.py`'s append-only invariant with zero code or test changes to `add_tag()`'s existing
duplicate-rejection behavior. A new `skill-mapping` CLI subcommand
(`python3 tools/tag_registry.py skill-mapping`) prints this merged mapping as JSON. All 3
LLM-interpreted consumers (`ticket-scoper.md`, `implement-ticket.js`'s "existing ticket" branch,
`create-tickets.js`'s Structure phase) already have Bash tool access and this repo already has a
live precedent for telling an agent prompt to `Run: <command>` for a dynamic value
(`create-tickets.js`'s own `Run: date +%Y%m%d` step in the same Structure-phase prompt) — so each
embedded table is replaced with an instruction to run the new CLI subcommand and read its JSON,
rather than requiring new orchestrator-level subprocess plumbing in the two `.js` files. The one pure
human doc (`ticket_tagging.md`) is rewritten to describe and point at the single source instead of
rendering a copy. `tools/tag_skill_mapping_check.py` is repurposed (not removed): since after this
change zero consumer files embed a literal table, its job changes from "compare N independent texts
pairwise" to "assert each of the 4 consumer files references the live single source and does not
contain a re-duplicated table" — a static regression guard against backsliding into a 6th hand copy,
which also resolves the module's own previously-disclosed `KNOWN_TAGS` staleness limitation by
deriving the known-tag set from `get_skill_mapping()` instead of a separate hardcoded frozenset.

## Design Decision

**Question: which of the 3 candidate resolutions closes the append-only-vs-4-existing-rows conflict
in `registries/tag_registry.jsonl`?**

**Chosen: a hybrid of (a) and (c) — schema widened going-forward-only, with a small, explicitly
disclosed fallback constant serving the 4 existing rows, accessed through exactly one function.**

Evidence considered (from `investigation.md` and direct re-verification of the 3 files at
`registries/tag_registry.jsonl:12,39-41`, `tools/tag_registry.py:167-201`,
`tests/tools/test_tag_registry.py:175-189`):

- `add_tag()` is genuinely append-only today: it raises on any existing tag (lines 182-187), the CLI
  has no `update`/`edit` subcommand, and `test_add_tag_is_append_only_existing_entries_unchanged`
  asserts this as a hard invariant, not an incidental gap. The module's own docstring calls this
  "deliberate, not incidental."
- The 4 `process-skill-signal` rows already exist without a `triggers_skill` field
  (`registries/tag_registry.jsonl:12,39-41`, added 2026-07-06). No mechanism in `tag_registry.py`
  today can add a field to an already-written line without rewriting it.
- **Option (b) (rewrite the 4 lines)** would be the first-ever exception to a design the module's own
  docstring calls deliberate, requires building a brand-new "authorized update" code path in
  `add_tag()`/the CLI that doesn't exist today, and forces an explicit, permanent weakening of
  `test_add_tag_is_append_only_existing_entries_unchanged`'s blanket claim — a real, non-trivial cost
  for a design goal (dedup of a 4-row skill-mapping table) that does not require ever touching an
  existing line. Rejected: the cost is disproportionate to the problem, and nothing about this
  ticket's scope forces a rewrite capability into existence.
- **Option (a) pure ("widen forward-only, legacy rows read via fallback")** is exactly right for the
  schema-evolution half of the problem (any *future* 5th `process-skill-signal` tag gets the field
  natively, no fallback needed) but, taken alone, still leaves an undisclosed question: where does the
  data for the 4 *existing* tags actually live? A bare "fallback" without a concrete, disclosed,
  bounded shape is exactly the kind of implicit residual copy `tag_skill_mapping_check.py`'s own
  `KNOWN_TAGS` precedent already warns against repeating silently.
- **Option (c) pure ("separate location entirely")** was rejected on its own by the investigation as
  deviating from the ticket's stated preference (a field-on-row design) with no compelling reason to
  abandon the row-field mechanism for tags that *will* get it once the schema is widened.
- **This plan's resolution takes (a)'s schema-widening literally for new rows, and borrows (c)'s
  "separate but disclosed, bounded location" only for the 4 rows that cannot be widened without a
  rewrite** — exactly the residual the investigation named ("a 6th small copy, though bounded to
  exactly 4 tags with no target-skill duplication logic beyond a dict literal"). Concretely:
  `tools/tag_registry.py` gains `_LEGACY_SKILL_TRIGGERS`, a module-level dict keyed by exactly the 4
  known legacy tags, with a docstring disclosure directly modeled on
  `tag_skill_mapping_check.py`'s own `KNOWN_TAGS` disclosure (see that module's docstring, lines
  29-35, and its plan's "Decision: Allowlist as a Disclosed 5th Copy" —
  `stored_artifacts/TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK/plan.md`). Both callers (the CLI's
  `skill-mapping` subcommand and every consumer instructed to run it) go through **one** function,
  `get_skill_mapping()`, that transparently merges registry-row `triggers_skill` fields with this
  fallback — so from every consumer's point of view there is exactly one thing to run and exactly one
  place to edit, even though its internals are honestly two sources for now.
  A new test (Step 2) locks `_LEGACY_SKILL_TRIGGERS`'s key set to exactly
  `{"api-design", "debugging", "performance", "security"}`, so a future new tag added only to one side
  (registry row without the field, or a hand-added legacy-dict entry that should have been a real row)
  fails loudly — same shape as the anti-drift test guard test_plan.md already specifies for this exact
  risk.

This satisfies AC4 (the append-only invariant is fully preserved — zero code change to `add_tag()`'s
existing raise-on-duplicate behavior, and no line in `registries/tag_registry.jsonl` is ever rewritten
by this ticket) without the disproportionate cost of option (b), and it satisfies AC1 in substance
(one function, one CLI command, one place to edit to change what every consumer computes) without
abandoning the ticket's stated field-on-row preference for anything within reach of it (future tags).

**On Question 2 (`tag_skill_mapping_check.py`'s fate): repurposed, not removed.** Once Steps 5-8 land,
none of the 4 consumer files contains a literal rendered table anymore (see Steps 5-8 below — each is
replaced with a "run the live command" instruction or, for the one human doc, a pointer). That fully
removes the original module's premise (parsing and pairwise-comparing N independently-maintained
texts) — there is nothing left to parse. Its new, real job (Step 10) is a static regression guard:
for each of the 4 consumer files, assert it references the live single source
(`tag_registry.py`'s `skill-mapping` mechanism) and does **not** contain a re-duplicated table. This
is a materially different check, not a cosmetic renaming, so the 10 existing tests (which test the
now-deleted parsers and the now-obsolete pairwise comparison) are explicitly retired, and new tests
are written for the new guard — including an injected-divergence test where a tmp copy of a consumer
file has a table re-added, proving the check can actually fail (the test_plan.md anti-drift guard
against dead-code checks). This also fixes the module's own previously-disclosed `KNOWN_TAGS`
staleness limitation as a side effect: the new check derives its known-tag set from
`get_skill_mapping().keys()` instead of a separately hardcoded frozenset, because now a genuine single
source of truth exists to derive it from (the original objection to doing this — "would make that one
file an implicit source of truth" — no longer applies once dedup is real).

**On Question 3 (disambiguation vs. `TAG-TOUCHPOINT-CLEANUP`): confirmed no conflict — different code
in the same file.** Read both tickets' text directly.
`tickets/todos/tag-registry-redesign/SEQUENCE.md`'s "Known Open Decisions" note about
`implement-ticket.js`'s "intentionally hand-synced string-match mirror" refers to
`TCK-20260720-TAG-TOUCHPOINT-CLEANUP.md`'s own AC4: the `classifyChecklistFailure` function's
`_TAG_REGISTRY_REJECTION_MARKER = 'is not in the tag registry'` string match, confirmed live at
`implement-ticket.js:290-291` — a mirror of `validate_frontmatter.py`'s error *text*, used for
Verify-phase failure classification, kept as an intentional hand-sync per that ticket's own
Assumptions ("passing arbitrary evidence text through a shell command risks quote-corruption"). This
is unrelated to the tag **-> skill** mapping table this ticket touches (lines 110-118, a completely
different Scope-phase concern about the `suggested_skills` field). This plan's Scope Guards state this
disambiguation explicitly and Step 6 touches only lines 110-118, never lines 290-291.

**On Question 4 (stale line-number citation): confirmed and corrected.** The ticket body's cited
`implement-ticket.js:313-314` / `create-tickets.js:578-579` do not contain the subprocess-JSON
precedent on the current branch. The real, current precedent is
`implement-ticket.js:353-360` / `create-tickets.js:578-585` (both: `python3 -c` + `sys.path.insert(0,
'tools')` + `from tag_registry import check_tags_registered` + `print('TAG_CHECK_JSON:' +
json.dumps(...))`, orchestrator-run via `bash()`, MARKER-prefixed parse). This plan does **not**,
however, need to replicate that orchestrator-level subprocess pattern for the skill-mapping mechanism,
because a simpler and equally-established precedent applies directly: `create-tickets.js`'s own
Structure-phase prompt already instructs its LLM agent to `Run: date +%Y%m%d` as a literal step
(confirmed live, near `create-tickets.js:441`) — i.e., agent prompts in this repo already tell the
LLM to run a shell command and use its output mid-reasoning, not only via orchestrator-run `bash()`
calls. Since all 3 LLM-prompt consumers (`ticket-scoper.md`'s agent role, both
`implement-ticket.js` branches via `agentType: 'ticket-scoper'`, and `create-tickets.js`'s
Structure-phase agent) run with full tool access including Bash (see `.claude/agents/ticket-scoper.md`
frontmatter and the agent roster's "Tools: All tools" / "Tools: *" entries), Steps 5-7 use this
simpler "Run: `python3 tools/tag_registry.py skill-mapping`" instruction pattern rather than adding
new orchestrator-level JSON-marker plumbing to the two `.js` files.

## Steps

### Step 1 — Widen `add_tag()`'s schema to optionally accept `triggers_skill` (forward-only)
**Files:** `tools/tag_registry.py`, `tests/tools/test_tag_registry.py`
**Change:** Add an optional `triggers_skill: dict | None = None` parameter to `add_tag()`
(currently `tools/tag_registry.py:167`). When provided, include it as a `triggers_skill` key in the
written JSON entry (line ~189-194's `entry` dict); when `None` (the default), omit the key entirely
so existing entries and any caller that doesn't pass it produce byte-identical output to today. Add
an optional `--triggers-skill <json-string>` flag to the CLI's `add` subparser (`tools/tag_registry.py:215-221`),
parsed with `json.loads` and passed through. Add
`test_add_tag_with_triggers_skill_writes_field` (new row includes the field, structured as a dict, not
a string) and `test_add_tag_without_triggers_skill_omits_field` (default path produces no
`triggers_skill` key — confirms zero behavior change for every existing caller).
**Do NOT touch:** `add_tag()`'s duplicate-rejection logic (lines 181-187), the CLI's `list` subcommand,
or any of the 4 existing lines in `registries/tag_registry.jsonl`.
**Verify:** `test_add_tag_with_triggers_skill_writes_field`,
`test_add_tag_without_triggers_skill_omits_field`; existing `test_add_tag_appends_entry_and_returns_it`,
`test_add_tag_rejects_duplicate_tag`, `test_add_tag_is_append_only_existing_entries_unchanged` still
pass unmodified.

### Step 2 — Add the disclosed `_LEGACY_SKILL_TRIGGERS` fallback for the 4 existing rows
**Files:** `tools/tag_registry.py`, `tests/tools/test_tag_registry.py`
**Change:** Add a module-level `_LEGACY_SKILL_TRIGGERS: dict[str, dict]` constant covering exactly
`api-design`, `debugging`, `performance`, `security`, each value shaped as
`{"skill": <str>, "carveout_agent": <str|None>, "carveout_paths": <tuple[str, ...]>, "carveout_excluded_paths": <tuple[str, ...]>}`
(the `debugging` entry: `skill="/debugging-strategies"`, `carveout_agent="world-debugger"`,
`carveout_paths=("src/worldassembly/", "src/worldbuilding/", "src/worldmodules/", "src/content/",
"src/core/registries.py")`, `carveout_excluded_paths=("src/worldgeneration/",)` — preserving the
existing explicit exclusion note from `ticket-scoper.md:92`/`ticket_tagging.md:59` losslessly; the
other 3 entries have `carveout_agent=None`, empty path tuples). Add a docstring comment directly above
the constant disclosing it as a bounded, deliberate residual — modeled verbatim on
`tag_skill_mapping_check.py`'s `KNOWN_TAGS` disclosure (see Design Decision above). Add
`test_legacy_skill_triggers_covers_exactly_four_known_tags` (keys == the 4-tag frozenset, no more, no
fewer) and `test_legacy_skill_triggers_debugging_preserves_carveout_structure` (asserts the debugging
entry's `carveout_agent`/`carveout_paths`/`carveout_excluded_paths` are non-empty structured values,
not flattened into the `skill` string) — this is the AC2 test.
**Do NOT touch:** any of the 4 existing `registries/tag_registry.jsonl` lines; do not add a 5th entry
to `_LEGACY_SKILL_TRIGGERS` (no new tag, no changed target — mirrors the drift-check ticket's own
"do not expand the mapping" guard).
**Verify:** `test_legacy_skill_triggers_covers_exactly_four_known_tags`,
`test_legacy_skill_triggers_debugging_preserves_carveout_structure`.

### Step 3 — Add `get_skill_mapping(root=None)` — the single-source accessor
**Files:** `tools/tag_registry.py`, `tests/tools/test_tag_registry.py`
**Change:** Add `get_skill_mapping(root: Path | str | None = None) -> dict[str, dict]`: call
`load_registry(root)`; for each tag with a `triggers_skill` field on its row, use that; else, if the
tag is a key in `_LEGACY_SKILL_TRIGGERS`, use that; tags with neither are omitted. Return
`{tag: mapping_dict}`. This is the one function every consumer ultimately depends on (directly, via
the CLI subcommand in Step 4).
Add `test_get_skill_mapping_returns_all_four_known_tags_today` (against the real
`registries/tag_registry.jsonl`, no `root` override, asserts all 4 legacy tags resolve via the
fallback path) and — the literal AC1 test —
`test_get_skill_mapping_single_edit_propagates_with_zero_other_changes`: using `tmp_path`, write a
registry, call `add_tag(..., category="process-skill-signal", triggers_skill={...})` for a synthetic
5th tag, then call `get_skill_mapping(root=tmp_path)` and assert the new tag's mapping appears —
proving one `add_tag()` call (no file edits anywhere else) changes what the accessor returns.
**Do NOT touch:** `load_registry()`'s existing duplicate-detection behavior.
**Verify:** `test_get_skill_mapping_returns_all_four_known_tags_today`,
`test_get_skill_mapping_single_edit_propagates_with_zero_other_changes`.

### Step 4 — Add the `skill-mapping` CLI subcommand
**Files:** `tools/tag_registry.py`
**Change:** Add a `skill-mapping` subparser (alongside `add`/`list` at `tools/tag_registry.py:213-224`)
taking an optional `--root`. In `main()`, on `args.command == "skill-mapping"`, call
`get_skill_mapping(args.root)` and `print(json.dumps(..., sort_keys=True))` — plain JSON to stdout, no
marker prefix needed since this is invoked directly by an agent's own Bash tool call (not parsed by
orchestrator JS), unlike the `check_tags_registered` precedent.
**Do NOT touch:** the `add`/`list` subcommands' existing behavior or output format.
**Verify:** Manual invocation (`python3 tools/tag_registry.py skill-mapping`) confirmed to print valid
JSON matching `get_skill_mapping()`'s return value; no dedicated `main()`-level test needed — this
repo's existing convention (confirmed: `test_tag_registry.py` has no CLI/`main()`-level tests today)
is to test the underlying function (`get_skill_mapping()`, covered by Step 3) rather than argparse
plumbing.

### Step 5 — Rewrite `.claude/agents/ticket-scoper.md`'s Output-contract table (item 5)
**Files:** `.claude/agents/ticket-scoper.md`
**Change:** Replace the embedded markdown table (lines 89-94, and the surrounding instruction at
lines 86-88, 96) with: "Run `python3 tools/tag_registry.py skill-mapping` and match the ticket's
`Process/Skill-signal` tags against its JSON keys. Each value's `skill` field is the suggestion; if
`carveout_agent` is set and `Related Code Areas` includes a path under one of `carveout_paths` (and
is not one of `carveout_excluded_paths`), suggest `Agent(subagent_type: carveout_agent)` instead of
`skill`. Do not hand-copy a table — always read the live command's output. If none of the ticket's
tags appear as a key, `suggested_skills` is an empty array — never omit the field."
**Do NOT touch:** any other Output-contract item (1-4), or any other section of this file.
**Verify:** Manual review — the debugging carve-out's full conditional structure (skill + carveout
agent + carveout paths + the explicit `worldgeneration` exclusion) is present in the instruction, not
flattened (AC2).

### Step 6 — Delete the embedded table in `implement-ticket.js`'s "existing ticket" branch; delegate like the "new ticket" branch already does
**Files:** `.claude/workflows/implement-ticket.js`
**Change:** In the "Load the existing ticket" prompt (lines 96-132), replace Step 3's embedded table
(lines 110-118) with: "Step 3 — read the ticket's frontmatter `tags` field and compute
`suggested_skills` per your Output contract's skill-mapping instructions (the same mapping mechanism
used when scoping a new ticket)." This deletes the 2nd embedded copy in this file entirely (the "new
ticket" branch at line 175 already delegates to ticket-scoper.md's Output contract and needs no
change) — after this step, `implement-ticket.js` contains zero embedded copies, both branches
delegate identically.
**Do NOT touch:** the "new ticket" branch (already correct); `classifyChecklistFailure` /
`_TAG_REGISTRY_REJECTION_MARKER` at lines 290-291 — that is `TAG-TOUCHPOINT-CLEANUP`'s territory, a
different hand-synced mirror unrelated to this mapping table (see Design Decision, Question 3); the
tag-registration check block at lines 347-366 (`check_tags_registered`, a separate mechanism
validating tags are registered, not computing skill suggestions).
**Verify:** Manual review — both branches' prompts now reference the Output contract identically; no
literal table text remains in this file.

### Step 7 — Replace the arrow-list table in `create-tickets.js`'s Structure phase
**Files:** `.claude/workflows/create-tickets.js`
**Change:** Replace the `suggested_skills` arrow-list block (lines 510-519) with a "Run:" step
following the same pattern already used earlier in this exact prompt for `date +%Y%m%d` (confirmed
live near line 441): "suggested_skills: Run `python3 tools/tag_registry.py skill-mapping` and match
each assigned `Process/Skill-signal` tag against its JSON keys the same way (skill field, or
`Agent(subagent_type: carveout_agent)` if a carve-out applies per its `carveout_paths`); empty array
if nothing matches. Do not invent mappings for tags outside this live mapping's keys."
**Do NOT touch:** the tag-registration check block (~lines 577-585, `check_tags_registered` via
orchestrator `bash()`) — a separate, already-correct mechanism for a different purpose (validating
tags are registered, not computing skill suggestions); the Structure phase's other synthesis
instructions (tier, related_docs, assumptions, etc.); `TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX`'s
territory (the Structure phase's tag-*category* restriction, a different closed-list check at line
506, untouched by this step).
**Verify:** Manual review — no literal arrow-list table remains in this file.

### Step 8 — Rewrite `docs/guides/ticket_tagging.md`'s "Skill Suggestions From Tags" section
**Files:** `docs/guides/ticket_tagging.md`
**Change:** Delete the embedded table (lines 56-61). Replace it with prose: "The mapping is defined
once, in `tools/tag_registry.py`'s `get_skill_mapping()` (registry rows' optional `triggers_skill`
field, merged with a small disclosed legacy fallback for the 4 tags registered before this field
existed). Run `python3 tools/tag_registry.py skill-mapping` to see the live mapping as JSON — this doc
does not maintain its own copy; edit `tag_registry.py` (or register a new tag with `--triggers-skill`)
to change or extend it." Keep the surrounding scenario-description prose (lines 45-54, describing when
`suggested_skills` fires and how it relates to `CLAUDE.md`'s auto-invoke triggers, and line 63-64's
"empty array if no match" / "note, not an auto-invoke" framing) — that prose explains *when*
suggestions fire, which this ticket does not change.
**Do NOT touch:** any other section of this file (`## Tags as a Registry Search Filter` and beyond).
**Verify:** Manual review — satisfies AC6 directly (describes the single source, no rendered 4th
copy).

### Step 9 — Review `docs/ai/agents.md`'s ticket-scoper section (AC7)
**Files:** `docs/ai/agents.md` (review only; edit only if needed)
**Change:** Re-read line 44 (`suggested_skills` list description) against the new mechanism. Confirmed
during Plan: the current text ("skill/agent invocations mapped from the ticket's `Process/Skill-signal`
tags — e.g. `debugging` -> `/debugging-strategies` or `world-debugger`; empty if no tag maps") is
generic — it does not name or describe the old 4-copy table mechanism, so it remains accurate under
the new single-source mechanism with no edit required. Implementer should re-confirm this at
Implement time (in case Steps 1-8 shift terminology, e.g. if `carveout_agent`/`carveout_paths` become
the standard vocabulary) and edit only if a genuine mismatch is found.
**Do NOT touch:** any other section of `docs/ai/agents.md`.
**Verify:** Manual review recorded in Implementation Notes — either "no change needed, confirmed
accurate" or the specific edit made and why.

### Step 10 — Repurpose `tools/tag_skill_mapping_check.py` into a live-source reference guard
**Files:** `tools/tag_skill_mapping_check.py`, `tests/tools/test_tag_skill_mapping_check.py`
**Change:** Remove `extract_pairs_markdown`, `extract_pairs_js_escaped`, `extract_pairs_arrow_list`,
`_ARROW_START_ANCHOR`/`_ARROW_END_ANCHOR`, `_CARVEOUT_LIST_RE`, `_SRC_PATH_RE`, `normalize_target`, the
hardcoded `KNOWN_TAGS` frozenset, and `check_tag_skill_mapping_consistency` — all dead once Steps 5-8
land (no consumer embeds a parseable table anymore). Replace with:
- `KNOWN_TAGS` derived live: `frozenset(tag_registry.get_skill_mapping().keys())` (import
  `tag_registry` via the same `sys.path.insert(0, 'tools')` pattern this module already uses)
  — resolves the module's own previously-disclosed staleness limitation (see Design Decision,
  Question 2).
- `check_consumers_reference_live_source(root=None) -> list[str]`: for each of the 4 consumer files
  (`.claude/agents/ticket-scoper.md`, `docs/guides/ticket_tagging.md`,
  `.claude/workflows/implement-ticket.js`, `.claude/workflows/create-tickets.js`), read its text and
  assert (a) it contains a reference to the live mechanism (substring match on `skill-mapping` or
  `get_skill_mapping`), and (b) it does NOT contain a re-duplicated literal table (a regex/heuristic
  guard: no block within a small line window containing 3+ of the known tag names formatted as
  table-row-shaped text, e.g. `` `tag` | ... `` or `tag -> ...` repeated). Return a list of violation
  strings (empty = all 4 consumers correctly reference the live source, none re-duplicate it).
- Update the module docstring to describe this new job in place of the old "compares 4 hand-maintained
  copies" framing, and to state the `KNOWN_TAGS`-staleness limitation is resolved (not just
  re-disclosed) now that it derives from `get_skill_mapping()`.
In `tests/tools/test_tag_skill_mapping_check.py`: delete the 10 existing tests (naming each removed
test and the reason — "parser/comparison premise no longer applies, all 4 consumers now reference a
live source instead of embedding a table" — in a comment block at the top of the file, not a silent
deletion). Add: `test_check_consumers_reference_live_source_passes_against_live_repo_files` (no `root`
override, asserts empty violation list against the real, just-edited 4 files),
`test_check_consumers_reference_live_source_detects_missing_reference` (tmp copy of one consumer file
with the reference instruction stripped out, asserts a violation naming that file), and
`test_check_consumers_reference_live_source_detects_reintroduced_table` (tmp copy of one consumer file
with a literal table re-added, asserts a violation — the anti-drift "must be able to actually fail"
guard).
**Do NOT touch:** any of the 4 real consumer files from this step (they were already finalized in
Steps 5-8) — this step only edits the checker module and its tests.
**Verify:** `test_check_consumers_reference_live_source_passes_against_live_repo_files`,
`test_check_consumers_reference_live_source_detects_missing_reference`,
`test_check_consumers_reference_live_source_detects_reintroduced_table`.

### Step 11 — Update `docs/guidelines/tag_taxonomy.md`'s Scenario 5 row
**Files:** `docs/guidelines/tag_taxonomy.md`
**Change:** Edit the Scenario 5 row (line 34, "Automatable skill-catalog health check") to describe
the repurposed check: still `tools/tag_skill_mapping_check.py`
(`check_consumers_reference_live_source`), run via
`python3 -m pytest tests/tools/test_tag_skill_mapping_check.py -q`, now verifying "each of the 4
consumers references the live single source in `tag_registry.py` and does not re-embed a copy" rather
than "extraction/comparison logic." Keep the edit narrowly scoped to this one row.
**Do NOT touch:** any other row or the Purpose section's framing.
**Verify:** Manual review.

### Step 12 — Full regression run
**Files:** none (verification only)
**Change:** Run the combined scoped command from test_plan.md:
```
python3 -m pytest tests/tools/test_tag_registry.py tests/tools/test_tag_skill_mapping_check.py tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_tag_report.py tests/tools/test_validate_frontmatter.py -q
```
Confirm all pass, including: the 21 pre-existing `test_tag_registry.py` tests unmodified (proving AC4
— the invariant tests were never touched), the new tests from Steps 1-3 and 10, and the 3
`_write_tag_registry_fixture()`-based dashboard tests / `categorize_tag()` tests confirming the
additive `triggers_skill` field doesn't break either downstream consumer. Record the command and
outcome in the ticket's Test Summary.
**Do NOT touch:** do not run `pytest tests/` — stays scoped to `tests/tools/` per the Testing Rule and
this ticket's own test_plan.md.
**Verify:** Exit code 0 on the combined command above.

## Scope Guards

- Do NOT rewrite, delete, or reorder any of the 4 existing lines in
  `registries/tag_registry.jsonl` — the chosen resolution (Steps 1-2) is additive-only by design; any
  edit to those 4 lines is a signal of scope drift toward rejected option (b).
- Do NOT touch `add_tag()`'s duplicate-rejection logic or `test_add_tag_is_append_only_existing_entries_unchanged`
  — that test must pass completely unmodified; any edit to it is itself a sign this plan's resolution
  has drifted.
- Do NOT expand or otherwise change the mapping's actual tag set or target skills (no 5th tag, no
  changed target for `api-design`/`debugging`/`performance`/`security`) — this is dedup, not a content
  change.
- Do NOT touch `implement-ticket.js`'s `classifyChecklistFailure` /
  `_TAG_REGISTRY_REJECTION_MARKER` (lines 290-291) — that is `TCK-20260720-TAG-TOUCHPOINT-CLEANUP`'s
  territory (a different hand-synced mirror: tag-*registration*-rejection error text, not the tag ->
  skill mapping). Confirmed disjoint by direct line-range inspection; the two tickets do not conflict
  because they edit different code in the same file.
- Do NOT touch `create-tickets.js`'s Structure-phase tag-*category* restriction (the closed
  4-tag-name list check near line 506) or anything in `TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX`'s
  territory — this ticket touches `create-tickets.js` only for the `suggested_skills` arrow-list block
  (lines 510-519).
- Do NOT touch either `.js` file's `check_tags_registered` subprocess block (`implement-ticket.js:353-360`,
  `create-tickets.js:~578-585`) — a separate, already-correct mechanism validating tag *registration*,
  not computing skill suggestions.
- Do NOT wire the repurposed `tag_skill_mapping_check.py` into any git hook, CI config, or
  `.claude/settings.json` — pytest-level only, matching the original module's scope.
- Do NOT touch `src/api/agent_ops_dashboard/ingest.py`, `tools/tag_report.py`, or
  `tools/validate_frontmatter.py` beyond confirming (via Step 12's regression run) that the additive
  `triggers_skill` field and new `get_skill_mapping()`/CLI subcommand don't break them — no code change
  to these 3 files is in scope.
- Do NOT edit `docs/ai/agents.md` beyond the single reviewed line unless a genuine mismatch is found
  (Step 9) — no broader rewrite of that doc.

## Dependency Map

- Steps 1 -> 2 -> 3 -> 4 are strictly sequential: each adds one function/constant in
  `tools/tag_registry.py` that the next step calls.
- Steps 5, 6, 7, 8 (consumer rewrites) each depend on Step 4 (the `skill-mapping` CLI subcommand must
  exist for the "Run: ..." instructions to be valid) but are otherwise independent of each other — any
  order among them is fine.
- Step 9 (docs/ai/agents.md review) has no code dependency; sequenced after 5-8 only so the
  implementer reviews it against the finished consumer wording.
- Step 10 depends on Steps 5-8 being complete (the checker asserts against the final text of all 4
  consumer files) and on Step 3 (`get_skill_mapping()` must exist for `KNOWN_TAGS` to derive from it).
- Step 11 depends on Step 10 (describes its final shape).
- Step 12 depends on all prior steps.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — single stored location; editing it changes all 4 consumers' output, zero other file edits | Steps 1-4 (mechanism), 5-8 (consumers wired to it) | `test_get_skill_mapping_single_edit_propagates_with_zero_other_changes`; `test_check_consumers_reference_live_source_passes_against_live_repo_files` |
| AC2 — debugging's conditional carve-out preserved losslessly | Step 2 (structured fallback), Step 5 (ticket-scoper.md prose) | `test_legacy_skill_triggers_debugging_preserves_carveout_structure` |
| AC3 — checker's fate explicitly decided and implemented | Step 10 | `test_check_consumers_reference_live_source_passes_against_live_repo_files`, `test_check_consumers_reference_live_source_detects_missing_reference`, `test_check_consumers_reference_live_source_detects_reintroduced_table` |
| AC4 — append-only invariant preserved (or break justified/recorded) | Steps 1-2 (purely additive) | Existing `test_add_tag_rejects_duplicate_tag`, `test_add_tag_is_append_only_existing_entries_unchanged` pass unmodified |
| AC5 — one of 3 resolutions (or justified 4th) chosen and documented in Investigate/Plan | This plan's Design Decision section | Manual review at Verify/done-checker time |
| AC6 — ticket_tagging.md describes single source, not a 4th copy | Step 8 | Manual review |
| AC7 — agents.md ticket-scoper section reviewed/updated if needed | Step 9 | Manual review |

## Anti-Drift Notes

- **Do not let any of Steps 5-8's replacement instructions flatten the `debugging` carve-out to a
  plain string.** Each replacement instruction must retain the 3-part structure (skill,
  `carveout_agent`, `carveout_paths`) — Step 2's `_LEGACY_SKILL_TRIGGERS` already stores it
  structured; the instructions in Steps 5-7 must tell the reading agent to apply that structure, not
  just "use the mapping."
- **Do not let the `_LEGACY_SKILL_TRIGGERS` fallback become an undisclosed shadow copy.** It must
  carry the same explicit docstring disclosure treatment as `tag_skill_mapping_check.py`'s
  `KNOWN_TAGS` got, and Step 2's key-set test must never be weakened to allow silent growth beyond the
  4 known legacy tags.
- **Do not treat Step 10's checker as optional polish.** AC3 requires it not be left "comparing copies
  that no longer independently exist" — the old module's premise is gone after Steps 5-8, so leaving
  the old parsers/tests in place uncorrected would be worse than removing them: it would be dead code
  silently always passing (vacuously true, since there's nothing left to compare). The 3 new tests in
  Step 10 must include at least one case that can actually fail (the reintroduced-table test).
- **Do not conflate this ticket's `implement-ticket.js` edit (Step 6, lines 110-118, the
  `suggested_skills` table) with `TAG-TOUCHPOINT-CLEANUP`'s edit target (lines 290-291, the tag-
  registration-rejection string match).** Both tickets touch `implement-ticket.js`; they touch
  disjoint line ranges for unrelated reasons. If Step 6's diff touches anything near
  `classifyChecklistFailure` or `_TAG_REGISTRY_REJECTION_MARKER`, that is scope drift — stop and
  reconsider.
- **The `skill-mapping` CLI subcommand's output is consumed by LLM agents reading raw Bash tool
  output, not by orchestrator-parsed JSON markers.** Do not add a `MARKER:`-prefix convention to it
  (Step 4) — that convention exists specifically for orchestrator `bash()` calls that need to parse
  output past log noise; a direct agent-run Bash call has no such noise to filter.

## Deviations

- **Post-implementation, real Test phase (not this plan's own Step 12 self-run) found one failure
  outside the 5 files this plan's Steps 5-8 targeted:**
  `tests/tools/test_create_tickets_tag_scope.py::test_process_skill_signal_mapping_table_still_present_unchanged`.
  That test belonged to a separate, earlier ticket
  (TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX) and asserted the literal old embedded skill-mapping
  table (`"api-design  -> /api-design-principles"` ... `"Do not invent mappings for tags outside
  this 4-entry table"`) was still present verbatim in `create-tickets.js`. It was never updated for
  this ticket's Step 7 removal of that table, so it was testing a premise this ticket's own
  architecture review already approved as intentionally changed.
- **Fix applied (follow-up, not a plan revision):** verified independently by reading the current
  `.claude/workflows/create-tickets.js` (lines ~503-514) that the old table's literal strings are
  genuinely absent and the live-lookup replacement (`python3 tools/tag_registry.py skill-mapping`,
  plus the new guardrail sentence "Do not invent mappings for tags outside this live mapping's
  keys.") is genuinely present, before touching anything. Then renamed the stale test to
  `test_skill_mapping_references_live_source_not_embedded_table` in
  `tests/tools/test_create_tickets_tag_scope.py` and rewrote its assertions to check the new
  reality: old table strings absent, live-lookup reference present. `create-tickets.js` itself was
  not touched (already correct from Step 7). No other test in that file was modified.
- This was caught by the real Test phase running the full regression suite, not silently patched
  around a legitimate gate — the test was factually stale against an already-approved architecture
  change, not a check revealing a real unresolved problem.

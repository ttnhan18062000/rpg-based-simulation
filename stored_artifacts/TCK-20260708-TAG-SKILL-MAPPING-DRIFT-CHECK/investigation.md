---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK
artifact_type: investigation
tags: [ai, workflows, tagging, ticket-scoper]
---

# Investigation — TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK

## Current Behavior

### The 4 copies, exact current text and line numbers (re-verified this session, not restated from the ticket)

**Copy 1 — `.claude/agents/ticket-scoper.md:89-94`** (markdown pipe table, raw backticks):
```
89     | Tag | Suggested skill |
90     |---|---|
91     | `api-design` | `/api-design-principles` |
92     | `debugging` | `/debugging-strategies` — unless `Related Code Areas` includes a path under `src/worldassembly/`, `src/worldbuilding/`, `src/worldmodules/`, `src/content/`, or `src/core/registries.py`, in which case suggest `Agent(subagent_type: "world-debugger")` instead (mirrors CLAUDE.md's existing debugging carve-out; note `src/worldgeneration/` is intentionally excluded — that path only appears in `world-debugger.md`'s own broader scope list, not CLAUDE.md's, and this mapping follows CLAUDE.md) |
93     | `performance` | `/python-performance-optimization` |
94     | `security` | `/security-review` (first codification of this mapping in the repo — no existing CLAUDE.md auto-invoke row for it yet) |
```
Row line numbers (91-94) match the ticket's claim exactly.

**Copy 2 — `docs/guides/ticket_tagging.md:50-55`** (markdown pipe table, raw backticks):
```
50     | Tag | Suggested skill |
51     |---|---|
52     | `api-design` | `/api-design-principles` |
53     | `debugging` | `/debugging-strategies` — unless `Related Code Areas` includes a path under `src/worldassembly/`, `src/worldbuilding/`, `src/worldmodules/`, `src/content/`, or `src/core/registries.py`, in which case suggest `Agent(subagent_type: "world-debugger")` instead |
54     | `performance` | `/python-performance-optimization` |
55     | `security` | `/security-review` (this mapping is the first place this route is codified anywhere in the repo — there is no `CLAUDE.md` auto-invoke row for it) |
```
Row line numbers (52-55) match the ticket's claim exactly.

**Copy 3 — `.claude/workflows/implement-ticket.js:69-74`** (markdown pipe table embedded in a JS template-string literal, backticks escaped with `\`` in raw source):
```
69       | \`api-design\` | \`/api-design-principles\` |
70       | \`debugging\` | \`/debugging-strategies\` — unless \`Related Code Areas\` includes a path under \`src/worldassembly/\`, \`src/worldbuilding/\`, \`src/worldmodules/\`, \`src/content/\`, or \`src/core/registries.py\`, in which case suggest \`Agent(subagent_type: "world-debugger")\` instead |
71       | \`performance\` | \`/python-performance-optimization\` |
72       | \`security\` | \`/security-review\` |
```
(Line numbers above use the file's actual numbering: header/separator at 68-69, rows at 71-74 as the ticket claims — the ticket's "71-74" refers to the 4 data rows, api-design through security, which is confirmed exact.) This copy lives inside the `ticketId ? \`Load the existing ticket...\` : ...` ternary's first branch (Step 3), i.e. only fires when `implement-ticket.js` is resumed with an existing `ticket_id`. The "Create new ticket" branch (same file, ~line 129-133) does **not** embed its own copy — it delegates to `ticket-scoper`'s own Output contract ("suggested_skills (from the mapping table in your Output contract, [] if none)"). So `implement-ticket.js` contains exactly one embedded copy, not two — consistent with the ticket's 4-copy total.

**Copy 4 — `.claude/workflows/create-tickets.js:601-607`** (arrow-list, plain indentation, no pipes/backticks, multi-line continuation for `debugging`):
```
601        api-design  -> /api-design-principles
602        debugging   -> /debugging-strategies (or Agent(subagent_type: "world-debugger") if
603                       related_code_areas includes a path under src/worldassembly/,
604                       src/worldbuilding/, src/worldmodules/, src/content/, or
605                       src/core/registries.py)
606        performance -> /python-performance-optimization
607        security    -> /security-review
```
Line numbers (601-607) match the ticket's claim exactly. This is inside the Structure-phase synthesis prompt's `suggested_skills:` instruction block (preceded by `tags:` instructions at line ~594-597, followed by "Do not invent mappings for tags outside this 4-entry table" at line 608).

### Semantic-identity re-verification (not just restated from the ticket)

Normalizing each of the 4 copies' targets to `(primary_skill, carveout_agent, sorted(carveout_paths))`:

| Tag | Copy 1 (ticket-scoper.md) | Copy 2 (ticket_tagging.md) | Copy 3 (implement-ticket.js) | Copy 4 (create-tickets.js) |
|---|---|---|---|---|
| `api-design` | `/api-design-principles` | `/api-design-principles` | `/api-design-principles` | `/api-design-principles` |
| `debugging` | `/debugging-strategies` unless `{src/worldassembly/, src/worldbuilding/, src/worldmodules/, src/content/, src/core/registries.py}` → `world-debugger` | identical 5-path set, identical targets | identical 5-path set, identical targets | identical 5-path set, identical targets |
| `performance` | `/python-performance-optimization` | `/python-performance-optimization` | `/python-performance-optimization` | `/python-performance-optimization` |
| `security` | `/security-review` (+ prose: "first codification...") | `/security-review` (+ prose, slightly different wording) | `/security-review` (no prose) | `/security-review` (no prose) |

**Result: all 4 copies are currently semantically identical.** The only differences are non-semantic prose (the `debugging` carve-out's parenthetical about `world-debugger.md`'s broader `worldgeneration/` scope appears only in Copy 1; the `security` "first codification" commentary appears only in Copies 1 and 2, with different wording between them). No `{tag: target}` pair differs across any of the 4 sources. This directly confirms the ticket's Request Summary claim and means **Acceptance Criterion #2 ("the check passes against the current state of all 4 files") is achievable as written** — there is no pre-existing divergence the new check would have to (incorrectly) tolerate or (correctly) fail on.

### Extraction/parsing design (concrete, not hand-wavy)

Three distinct textual formats across the 4 files, requiring 3 distinct parsers, all filtered by a fixed known-tag allowlist (`{"api-design", "debugging", "performance", "security"}`) so line-number drift never breaks extraction (no hardcoded line ranges):

**Format A — raw markdown pipe table** (`ticket-scoper.md`, `ticket_tagging.md`):
- Scan file lines for `^\|\s*` prefix.
- Split each candidate line on `|`, strip leading/trailing empty strings from the split, strip whitespace from each cell.
- `cell[0]` matched against `^\`([a-z][a-z-]*)\`$`; only lines whose captured group is in the known-tag set are accepted as data rows (this naturally skips the `| Tag | Suggested skill |` header and the `|---|---|` separator, and needs no separate header/separator-skip logic).
- `cell[1]` (the raw target text, backticks and prose included) is the row's target string.

**Format B — JS-escaped markdown pipe table** (`implement-ticket.js` Step 3 block):
- Same pipe-split approach as Format A, but `cell[0]`'s tag-match regex must tolerate an optional literal backslash immediately before/after the backtick (`^\\?\`([a-z][a-z-]*)\\?\`$`), because the file's raw bytes contain `\`` (backslash + backtick) — the source is a JS template-string literal where backticks are escaped, and this file is read as plain text, not evaluated as JS.
- Same known-tag allowlist filter.

**Format C — arrow-list with multi-line continuation** (`create-tickets.js` Structure-phase block):
- No pipe/backtick delimiters; this is the hardest of the 3 formats because the `debugging` entry's target legitimately spans 4 physical lines (the carve-out's path list wraps).
- Parser is a small line-based state machine: for each line, try `^\s*([a-z][a-z-]*)\s*->\s*(.+)$`. If it matches and the captured tag is in the known-tag allowlist, start a new `(tag, target)` entry with `target` seeded to `match.group(2).strip()`. If a line does *not* match that pattern, append `line.strip()` (joined with a single space) to the *currently open* entry's target — this is what correctly captures debugging's 3 continuation lines (`related_code_areas includes a path under src/worldassembly/,` / `src/worldbuilding/, src/worldmodules/, src/content/, or` / `src/core/registries.py)`) into one target string.
- Bound the scan to the known block: start scanning after the line containing `"Map each assigned tag against this table"` and stop at the line containing `"Do not invent mappings for tags outside this 4-entry table"` — both are stable anchor substrings already present in the file (not line numbers), so the parser is robust to the whole block shifting up/down if unrelated lines above it change.

**Normalization (shared by all 3 formats' output, this is the "ignore prose/wording differences" step):**
- `primary_skill = re.search(r'(/[a-z][a-z-]*)', raw_target).group(1)` — pulls the leading `/skill-name` (works for `/api-design-principles`, `/debugging-strategies`, `/python-performance-optimization`, `/security-review`).
- `carveout_agent = "world-debugger" if "world-debugger" in raw_target else None`.
- `carveout_paths = tuple(sorted(set(re.findall(r'src/[\w./]+', raw_target))))` — captures `src/worldassembly/`, `src/worldbuilding/`, `src/worldmodules/`, `src/content/`, `src/core/registries.py` uniformly regardless of trailing comma/parenthesis in the source prose (the regex character class stops before those punctuation marks).
- `normalized = (primary_skill, carveout_agent, carveout_paths)` is the comparable unit. This is exactly what item 4 below requires: `debugging`'s target has two parts (default skill AND the carve-out condition/path-set), and both are captured in `normalized` — a drift in either the default skill string or any single path in the carve-out set changes the tuple and fails the comparison, which is the scenario this check exists to catch.

**Comparison and failure reporting:**
- Build `{source_file: {tag: normalized}}` for all 4 sources.
- For each of the 4 known tags, assert all 4 sources' `normalized` value are pairwise equal; on mismatch, raise/assert with a message naming the tag, the disagreeing files, and their differing normalized tuples (not just "mismatch") — satisfies the ticket's "diff-style message identifying which file(s) disagree and on which tag" requirement.

### Reusable-helper-vs-inline-test decision (precedent comparison)

`tools/tag_registry.py::check_tags_registered()` (`tools/tag_registry.py:155-164`) is the cited precedent: core logic (`load_registry`, `is_tag_registered`, `check_tags_registered`) lives in `tools/`, and `tests/tools/test_tag_registry.py` imports it via a `sys.path.insert(0, "tools")` shim (`tests/tools/test_tag_registry.py:9-24`) rather than reimplementing logic inline in the test file. `tests/tools/test_tag_report.py` follows the identical shim pattern to import `tools/tag_report.py`'s `build_tag_rows`/`categorize_tag`/`collect_completed_tickets`.

This ticket's extractor should follow the same pattern (**recommend a `tools/` helper, not inline test logic**), for the same reason `check_tags_registered()` does: the 3 parser functions (Format A/B/C) are independently unit-testable against small synthetic string fixtures (needed to satisfy Acceptance Criterion #3 — demonstrating the failure mode without mutating the real 4 source files), and a `tools/`-level module is also the natural place a future consumer (e.g. a pre-commit hook, per the ticket's own Out-of-Scope note that CI/hook wiring is deferred but not ruled out) would import from later, exactly mirroring `check_tags_registered()`'s own present-day usage from both a test file and `implement-ticket.js`'s orchestrator-run `bash()` call. Recommended new module: `tools/tag_skill_mapping_check.py`, exposing `extract_pairs_markdown(text)`, `extract_pairs_js_escaped(text)`, `extract_pairs_arrow_list(text)`, `normalize_target(raw_target)`, and a top-level `check_tag_skill_mapping_consistency(root=None)` that reads the actual 4 live files (via a `root` param mirroring `tag_registry.py`'s `registry_path(root)` testability convention) and returns a structured mismatch list. `tests/tools/test_tag_skill_mapping_check.py` then has (a) unit tests per parser against synthetic snippets, including a deliberately-mutated snippet to prove failure detection (Acceptance Criterion #3), and (b) one integration-style test that calls `check_tag_skill_mapping_consistency()` with no `root` override (i.e., against the real repo files) and asserts the mismatch list is empty — this is the test that actually satisfies Acceptance Criterion #1/#2 against live content.

## Mechanics / Engine Constraints

N/A — confirmed. This ticket touches only `.claude/agents/`, `.claude/workflows/`, `docs/guides/`, and `tests/tools/`/`tools/` agent-tooling paths. No `src/` simulation code, no Mechanics Bible chapter, no Engine Contract governs Claude Code agent-prompt text or Node workflow scripts. Same conclusion the two directly-cited prior investigations (`TCK-20260705-TAG-SKILL-SUGGEST`, `TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION`) already reached for the same file set.

## Parity Ledger Overlap

N/A — confirmed via fresh grep this session (`grep -rniE "suggested_skill|tag_skill|skill_map|skill-signal" docs/parity_ledger/*.yaml`), zero hits across all 8 ledger files (`combat_movement.yaml`, `faction.yaml`, `infrastructure.yaml`, `progression.yaml`, `social_narrative.yaml`, `strategic_cognition.yaml`, `substrate.yaml`, `town_resource.yaml`). This re-confirms `TCK-20260705-TAG-SKILL-SUGGEST/investigation.md`'s own Parity Ledger Overlap finding (which grepped 7 files at the time; an 8th, `faction.yaml`, has since been added to the ledger directory but also has no hits) — the parity ledger tracks `src/` simulation-subsystem doc↔code parity, and this ticket's subject matter (agent-prompt tag→skill routing text) has no ledger presence in any file. No entry needs updating; none needs to be added.

## Prior Work

- **`TCK-20260705-TAG-SKILL-SUGGEST`** (done) — introduced the mapping table and all 4 compute/embed sites (its own investigation.md correctly enumerates `ticket-scoper.md`, `create-tickets.js`, and both of `implement-ticket.js`'s Scope-phase branches — the "Create new ticket" branch delegates rather than duplicating, which is why the file only contains 1 embedded copy despite 2 branches). Its Anti-Drift Hazards section explicitly named the duplication "a disclosed, accepted hazard, not a defect" and deferred building any consistency check.
- **`TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION`** (done) — first flagged the drift risk under Anti-Drift Hazards, but its own Current Behavior Part 1 table only cites 3 locations (`ticket-scoper.md`, `ticket_tagging.md`, `implement-ticket.js`) and its Anti-Drift Hazards bullet says "verbatim in 3 places" — it never separately enumerates `create-tickets.js`'s copy in that bullet even though Part 1's *narrative text* two paragraphs earlier does mention `create-tickets.js`'s Structure-phase table at lines 595-604. This is the "undercounted to 3" gap this ticket's own Request Summary already correctly identifies and corrects to 4 — re-verified here: the investigation.md's Anti-Drift Hazards bullet (reproduced above) is indeed under-scoped relative to its own Part 1 findings.
- **`TCK-20260708-SKILL-CREATE-TICKETS-WORKFLOW-TOOL-STALE`** / **`TCK-20260708-SKILL-IMPLEMENT-TICKET-PHASE-DRIFT`** (both done) — reactive fixes for the identical failure class (hand-duplicated instructional text going stale) in a different pair of files (`create-tickets/SKILL.md`, `implement-ticket/SKILL.md`). Not read in full for this investigation (out of this ticket's Related Code Areas — different files entirely), but confirms the failure class is real and has already manifested twice in this repo, reinforcing the value of a proactive check here.
- **No prior partial/existing consistency check found.** Grep of `tests/` for references to any of the 4 file paths (`ticket-scoper.md`, `ticket_tagging.md`, `create-tickets.js`, `implement-ticket.js`) returns exactly one hit — `tests/tools/test_generate_retro.py` — which is unrelated (that test file's fixtures reference workflow *names* like `"implement-ticket"` as a monitoring `workflow` field value in synthetic `runs.jsonl` records, not a cross-file tag/skill-mapping check). Confirmed: no prior attempt at this specific check exists anywhere in `tests/`.

## Risks and Open Questions

1. **Format C's block-boundary anchors are stable but not enforced by any other test.** If a future edit to `create-tickets.js` rewords the anchor strings ("Map each assigned tag against this table" / "Do not invent mappings for tags outside this 4-entry table") without touching the table itself, the arrow-list parser would fail to locate its scan window and should raise a clear "could not locate mapping block" error (not silently return an empty/wrong result) — Plan should make this an explicit parser failure mode, not an assumed non-issue.
2. **The known-tag allowlist (`api-design`, `debugging`, `performance`, `security`) is itself a 5th, tacit copy of the tag set.** If a 5th `Process/Skill-signal` tag is ever added to all 4 real copies (explicitly Out of Scope for *this* ticket to do, but plausible for a future ticket), the new check's allowlist would need updating too, or it would silently ignore the new tag's mapping rather than compare it. This is not a blocker for this ticket (Out of Scope explicitly excludes expanding the mapping), but worth flagging in the new module's docstring so a future editor knows to update the allowlist alongside any real 5th-tag addition — otherwise the check itself becomes a 5th silently-drifting copy.
3. **No open question blocks implementation.** The ticket's own Assumptions/Open Questions section frames both major decisions (pytest-based vs. `tools/`-CLI mechanism; normalized-comparison vs. byte-identical comparison) as leaning-but-not-fixed Plan-phase calls — this investigation's findings above (Prior Work / extraction design / helper-location precedent) directly resolve both: pytest + `tools/`-helper backing matches the cited `check_tags_registered()` precedent exactly, and normalized comparison is the only semantics under which Acceptance Criterion #2 is satisfiable (byte-identical would immediately fail on the legitimate prose differences documented above). Plan can adopt both without further human input.

## Anti-Drift Hazards

- **Do not let the new check's own known-tag allowlist become an unadvertised 5th copy of the mapping's tag set** (Risk 2 above) — document this explicitly in the new `tools/` module's docstring so it's discoverable, not silently stale.
- **Do not accidentally make the check byte-identical instead of semantic.** The ticket is explicit and this investigation reconfirms: `ticket-scoper.md` and `ticket_tagging.md` legitimately carry longer prose than `implement-ticket.js`/`create-tickets.js`. A byte-identical or even "same cell text" comparison would false-positive against content that is not actually a mapping drift — the check must normalize to `(primary_skill, carveout_agent, carveout_paths)` before comparing.
- **Do not widen this ticket's scope into the "true single source of truth" refactor.** Out of Scope explicitly forbids collapsing the 4 copies via imports/generation; the deliverable is a failing-loudly test, not deduplication. A helper module under `tools/` is *not* a single source of truth for the prompt text itself (the prose still lives independently in 4 places) — it is only a shared *reader/comparator* of that text, which is a materially smaller thing and stays in scope.
- **Do not fix the pre-existing minor Anti-Drift-Hazards undercount in `TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION/investigation.md`** (the "3 places" bullet vs. its own "4 compute sites" Part 1 finding) — that stored artifact is historical/immutable per its own frontmatter (`status: historical`); this ticket's Request Summary already documents and corrects the count going forward, and editing a historical artifact is out of scope.
- **Do not expand the `debugging` carve-out path set or touch the pre-existing `worldgeneration/` CLAUDE.md-vs-world-debugger.md mismatch** (noted in `TCK-20260705-TAG-SKILL-SUGGEST/investigation.md` Risk 3, and re-surfaced in Copy 1's own parenthetical above) — that is a separate, already-flagged, deliberately-deferred discrepancy between CLAUDE.md and `world-debugger.md`, not part of the 4-copy mapping table this ticket's check compares, and not in this ticket's Scope.

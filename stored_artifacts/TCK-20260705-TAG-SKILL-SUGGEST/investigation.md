---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260705-TAG-SKILL-SUGGEST
artifact_type: investigation
tags: [tagging, taxonomy, ticket-scoper, skills]
---

# Investigation — TCK-20260705-TAG-SKILL-SUGGEST

## Current Behavior

### `ticket-scoper.md` has no skill-suggestion concept today
`.claude/agents/ticket-scoper.md:1-81` (full file). The frontmatter template (`:20-29`) requires
a `tags` field sourced from `docs/guidelines/tag_taxonomy.md` (`:28`, already added by
TCK-20260704-TAG-TAXONOMY). The `## Output` section (`:75-81`) currently returns exactly four
things: the ticket markdown, a conflict report, the write path, and a one-sentence `summary`.
There is no `suggested_skills` field, no tag→skill table, and no reference to any skill catalog
anywhere in the file. This is a pure additive change to the Output contract.

### `create-tickets.js`'s Structure phase does not assign tags at all — not just "no skill mapping"
`.claude/workflows/create-tickets.js:441-478` (`TASK_SCHEMA`) has no `tags` property among its
required or optional fields — the Structure-phase synthesis agent is never asked to produce tags.
Then in the Write phase, the frontmatter template written to each batch ticket
(`:673-682`) hardcodes `tags: []` literally, with no substitution token. **Batch-created tickets
today ship with an empty tags array, always** — this is a pre-existing gap, not something this
ticket's scope description accounted for. The ticket's Scope bullet 4 says to add "the same
mapping awareness to `create-tickets.js`'s Structure phase (where tags are assigned for
batch-created tickets)" — but tags are not currently assigned there at all. Implementing skill
suggestion for batch tickets therefore requires two things, not one: (a) make the Structure phase
actually assign `Process/Skill-signal`-aware tags (and ideally `Subsystem/Topic` tags too, though
that's TCK-20260705-TAG-REGISTRY-QUERY's concern, not this ticket's), and (b) add the tag→skill
lookup on top of that. This is a scope-sizing correction Plan needs, not just a "wire it in" task.

### `implement-ticket.js`'s Scope phase has no field to carry a suggestion through — and isn't listed in this ticket's Related Code Areas
`.claude/workflows/implement-ticket.js:27-106`: `phase('Scope')` invokes the `ticket-scoper`
agentType with `TICKET_SCHEMA` (`:31-39`), whose required fields are `ticket_id`, `ticket_path`,
`status`, `conflicts`, `tier`, `summary`, `ts` — no `suggested_skills` field. The conflict-report
surfacing pattern the ticket's Scope bullet 3 asks to mirror lives at `:184-188`:
```
pushEvent('Scope', 'ticket-scoper', ticketInfo.conflicts && ticketInfo.conflicts.length > 0 ? 'failed' : 'ok', ...)
if (ticketInfo.conflicts && ticketInfo.conflicts.length > 0) {
  log(`Conflicts detected: ${ticketInfo.conflicts.join(' | ')}`)
  log('Review conflicts before proceeding. Re-run with ticket_id to continue from existing ticket.')
}
```
For `ticket-scoper`'s new `suggested_skills` field to actually reach a human/orchestrator via
`log(...)` (Scope bullet 3's explicit requirement), `implement-ticket.js`'s `TICKET_SCHEMA` must
gain a `suggested_skills` field and a `log(...)` call analogous to `:186-188` must be added.
**`implement-ticket.js` is not in this ticket's "Related Code Areas" list** even though the
ticket's own Scope text requires changing its Scope-phase surfacing behavior. This is a real gap
in the ticket, not just a documentation nicety — without this edit, `ticket-scoper` would compute
`suggested_skills` but the orchestrating workflow would silently drop the field (schema-driven
agent calls only pass through declared schema properties in this codebase's pattern; every other
sibling field — `conflicts`, `summary` — has matching schema + log-surfacing on both the
subagent's Output contract and the caller's schema/log block).

### CLAUDE.md's auto-invoke table does not have a `security` / `/security-review` row
`CLAUDE.md:311-315` (the "Always auto-invoke" table) has exactly three rows relevant to this
ticket's mapping:
```
| Editing or investigating `src/api/` | `/api-design-principles` ... |
| Investigating a traceback ... | `/debugging-strategies`; ... world-debugger ... |
| Profiling or investigating a slow simulation tick ... | `/python-performance-optimization` |
```
There is **no row for `/security-review`** anywhere in CLAUDE.md. Confirmed via full-file grep —
`security-review` does not appear in CLAUDE.md at all. `/security-review` does exist as a skill:
it is documented in `docs/ai/skills.md`'s "Built-in Skills → Code Quality" section as a
system-level (not project-level, i.e. no `.claude/skills/security-review/` directory exists —
confirmed by directory listing, unlike `api-design-principles`, `debugging-strategies`, and
`python-performance-optimization` which are all real directories under `.claude/skills/`) skill:
"Review for security vulnerabilities across the diff." So the skill itself is real and invocable
as `/security-review`, but the ticket's own wording ("already-established precedent... mirroring
the existing carve-out") overstates the precedent for this specific tag: 3 of the 4 mappings
mirror an existing CLAUDE.md row 1:1, but `security` → `/security-review` does not have a CLAUDE.md
precedent row — only a `docs/ai/skills.md` catalog entry. This does not block the mapping (the
skill exists and is invocable), but Plan/Implementation should not claim CLAUDE.md already has
this row, and per the ticket's own Out-of-Scope ("Changing CLAUDE.md's file-path-based auto-invoke
table itself... this ticket does not modify or replace the existing mechanism"), adding a
CLAUDE.md row for security-review is explicitly not in scope — the mapping in `ticket-scoper.md`
will be the first place `security` → `/security-review` is codified as a routing rule anywhere in
the repo.

### No reusable, structured `Process/Skill-signal` tag list exists in code — a new small map is correctly scoped, not duplicative
`tools/validate_frontmatter.py:36-56` has `TAG_TAXONOMY_EFFECTIVE_DATE`, `FORBIDDEN_PRIORITY_TAGS`,
and `TAG_SYNONYM_MAP` (canonical-form corrections only, e.g. `obs` → `observability`) — none of
these enumerate or categorize tags by taxonomy category (Subsystem/Topic vs. Process/Skill-signal
vs. Quality-attribute). `_check_tags()` (`:152-189`) validates canonical *form* only; it has no
concept of "this tag belongs to category X." `docs/guidelines/tag_taxonomy.md` itself is explicit
that Process/Skill-signal is "not a closed list of every valid tag" (`:96-98`) — by design there is
no authoritative enumeration to import from. This confirms the ticket's own proposed approach (a
small explicit map living in `ticket-scoper.md`) is not duplicating an existing single source of
truth — there isn't one to duplicate. See Risks below for the recommendation on *where* that small
map should live.

### `world-debugger.md`'s carve-out condition, confirmed exact
`.claude/agents/world-debugger.md:5-14` ("System Scope") lists the same five path patterns as
CLAUDE.md's debugging row: `src/worldassembly/`, `src/worldbuilding/`, `src/worldmodules/`,
`src/worldgeneration/` (note: CLAUDE.md's row omits `worldgeneration/`, world-debugger.md includes
it — a pre-existing minor drift between the two, not introduced by this ticket, and out of scope
to fix here), `src/content/`, `src/core/registries.py`. The ticket's Acceptance Criteria 3
("branches to world-debugger when Related Code Areas overlap the world-assembly file set") should
use CLAUDE.md's five-pattern list (the one the ticket cites as "the existing carve-out") as the
literal match set, since that's the version the ticket's Scope text points to; using
world-debugger.md's six-pattern list would silently broaden the carve-out beyond what CLAUDE.md
documents. Flag for Plan to pick one explicitly (recommend: CLAUDE.md's four-path list, since
that's the one users read and the one the ticket cites).

### `docs/ai/agents.md`'s ticket-scoper section — current text
`docs/ai/agents.md` "`ticket-scoper`" section: "**Outputs:** Ticket file at
`tickets/inprogress/{ticket_id}.md`, Staging directory, Conflict report (if any)." No mention of
`suggested_skills`. Needs a new bullet.

### `docs/guides/README.md` — index table structure confirmed
Table has 7 rows (`simulation.md` through `agent_monitoring.md`), each `| [file.md](file.md) |
one-line description |`. Adding a `ticket_tagging.md` row is a one-line, low-risk edit; no test
enforces table completeness (confirmed: no test file references `docs/guides/README.md`).

## Mechanics / Engine Constraints

None. This is a process/tooling ticket (agent prompts, a Node-based workflow script, and
developer-facing docs) — it does not touch `src/`, simulation state, or any authoritative mutation
path. No chapter of the Mechanics Bible or Engine Contracts constrains this work.

## Parity Ledger Overlap

Confirmed no overlap, not merely assumed. Grepped all 7 `docs/parity_ledger/*.yaml` files for
`tag`/`skill` (keyword search, case-insensitive): the only hits are unrelated substring matches —
`progression.yaml:3000` ("`skill_silence`" as one of several XP-plateau *type names*, part of the
progression mechanic's own vocabulary, unrelated to Process/Skill-signal tags) and
`infrastructure.yaml:3350` ("No CLI/skill-level invocation surface is added" — a phrase describing
an unrelated artifact-vs-source-of-truth distinction in a different entry). No parity ledger entry
`text` concerns ticket tagging, skill suggestion, or the `ticket-scoper`/`create-tickets.js`
tooling. No new or updated parity ledger entry is needed for this ticket.

## Prior Work

- **TCK-20260704-TAG-TAXONOMY** (`tickets/done/`, artifacts in `stored_artifacts/`) — shipped the
  `Process/Skill-signal` category this ticket consumes. Its own doc explicitly defers the
  consumption logic ("this document does not build any of that consumption logic itself" —
  `docs/guidelines/tag_taxonomy.md:20`). No overlap risk; this ticket is the deferred follow-through.
- **TCK-20260704-SKILL-TRIGGER-COVERAGE** (`tickets/done/`) — added the three CLAUDE.md
  file-path-based auto-invoke rows this ticket's mapping mirrors (`api-design-principles`,
  `debugging-strategies`/`world-debugger`, `python-performance-optimization`). Its Test Summary
  establishes the precedent that a prompt/doc-only change is verified by manual before/after
  re-reads, not automated tests — directly relevant to this ticket's Test Plan (see
  `test_plan.md`). Confirms this ticket's mapping table is the *first* place `security` appears in
  any routing table anywhere in the repo (see Current Behavior above).
- **TCK-20260705-TAG-REGISTRY-QUERY** (`tickets/todos/tag-taxonomy-followups/`, sibling, filed same
  day, `SEQUENCE.md` confirms no dependency either direction) — consumes the *Subsystem/Topic*
  category instead, touches `create-tickets.js`'s *Investigate* phase (not Structure) and
  `investigator.md` (not `ticket-scoper.md`). No code-path overlap confirmed by reading both
  tickets' Related Code Areas and the SEQUENCE.md's own explicit statement ("Neither depends on
  the other"). Both tickets independently require a `docs/guides/` update — coincidental, not
  coordinated, per SEQUENCE.md's "Dependency Notes."

No `docs/REGISTRY.yaml` entry exists yet for this ticket (it is still `inprogress`, as expected).

## Risks and Open Questions

1. **Mapping location — recommendation, not left unresolved.** The ticket's own Assumptions ask
   whether the mapping should live in `ticket-scoper.md` alone or a shared location (since
   `planner`/`architecture-reviewer` might also want it). Recommendation: **keep it in
   `ticket-scoper.md` for this ticket**, as the ticket's own Scope text proposes as the default.
   Reasoning: (a) no other agent currently reads tags for routing purposes — `planner.md`'s only
   use of `tags` is copying them verbatim into its own frontmatter (`tags: [<scope words from
   ticket ID, lowercase>]`), not routing off them; extending the mapping to `planner` is explicitly
   deferred to Plan by the ticket's own Assumptions bullet 2. (b) `tools/validate_frontmatter.py`
   confirmed has no category-aware structure to extend cheaply (see Current Behavior) — building a
   shared location now (e.g. a new `docs/guidelines/skill_mapping.yaml` or a Python constant) would
   be speculative generality for a 4-entry table with exactly one confirmed reader. (c) If
   `create-tickets.js`'s Structure phase needs the same 4-entry table (which it does, per Scope
   bullet 4), duplicating 4 lines of markdown table into the Structure-phase prompt text is cheap
   and the two consumers (an agent's own `.md` instructions vs. a workflow's inline prompt string)
   don't share an import mechanism today — workflows embed prompt text as JS template literals, not
   as includes of agent `.md` files. A single source of truth would require the workflow to read
   `ticket-scoper.md` at runtime and extract the table, which is a heavier mechanism than the
   ticket's scope warrants for 4 entries. **If a third consumer appears later (Plan's own open
   question), promote to a shared location then** — do not build it preemptively.

2. **`implement-ticket.js` must be edited but is not in the ticket's Related Code Areas.** Flagged
   above under Current Behavior. This should be added to the ticket's Related Code Areas before
   Plan proceeds, or Plan should explicitly decide the suggestion is only surfaced when
   `ticket-scoper` is invoked directly (not via `implement-ticket.js`'s Scope phase) — but that
   would leave Scope bullet 3 ("Ensure the orchestrating session... surfaces this suggestion via
   `log(...)`") unimplemented, which is an explicit Acceptance-Criteria-adjacent requirement in the
   ticket body even though it's not in the AC checklist itself. Recommend: add
   `.claude/workflows/implement-ticket.js` to Related Code Areas; Plan should include a step to add
   `suggested_skills` to `TICKET_SCHEMA` (`:31-39`) and a `log(...)` block mirroring `:186-188`.

3. **World-debugger carve-out file-set mismatch (CLAUDE.md vs. world-debugger.md).** CLAUDE.md's
   debugging row omits `src/worldgeneration/`; `world-debugger.md`'s own System Scope includes it.
   Recommend Plan use CLAUDE.md's four-path list literally (the version the ticket cites), and not
   silently adopt world-debugger.md's broader five-path list, to avoid an undocumented scope
   expansion of "when do we branch to world-debugger" as a side effect of this ticket.

4. **`security` → `/security-review` has no CLAUDE.md precedent row** (see Current Behavior). This
   doesn't block Scope's stated 4-tag mapping — the skill is real and documented in
   `docs/ai/skills.md` — but Plan/Implementation Notes should describe it accurately: 3 of 4 tags
   mirror an existing CLAUDE.md row, 1 of 4 (`security`) is the first codification of that mapping
   anywhere in the repo. This is worth a one-line correction in the ticket's own Scope bullet
   wording during Plan/Implementation, since the ticket's phrasing implies uniform precedent across
   all 4.

5. **`docs/ai/workflows.md`'s `create-tickets` phase table is already stale relative to the actual
   code** (its listed phase names — "Parse" — don't match `create-tickets.js`'s actual phase names
   — Comprehend/Investigate/Structure/Write/Link, confirmed by reading both). This predates this
   ticket and is not introduced by it; not in this ticket's Related Docs, so out of scope to fix,
   but noting so a future editor doesn't assume this ticket caused the drift.

## Anti-Drift Hazards

- Do not let the `suggested_skills` note leak into the *ticket file itself* (durable content) —
  the ticket's Out of Scope and Scope bullet 2 are explicit that this is a runtime/output-only
  suggestion, not a ticket frontmatter/body field. `ticket-scoper.md`'s Output section changes;
  its Ticket Format template (`:15-73`) must not.
- Do not expand the mapping beyond the 4 named tags (`api-design`, `debugging`, `performance`,
  `security`) — Out of Scope explicitly reserves `architecture`, `test-driven-development`, etc.
  for a separate future decision.
- Do not modify CLAUDE.md's auto-invoke table as part of this ticket, even though the
  `security-review` gap (Risk 4) might tempt an implementer to "fix" it by adding a CLAUDE.md row —
  Out of Scope explicitly forbids changing that table in this ticket.
- Do not silently widen the world-debugger carve-out to `worldgeneration/` without an explicit
  Plan decision (Risk 3) — that would be an undocumented behavior change riding along with this
  ticket.
- Keep `docs/guides/ticket_tagging.md` a thin, linking companion — Acceptance Criteria explicitly
  says "Links to `docs/guidelines/tag_taxonomy.md` for the full formal rules rather than
  duplicating them." Do not re-derive the canonical-form rules or the full category list inside
  the new guide.

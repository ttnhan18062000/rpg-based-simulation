---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260720-TAG-RELEVANCE-VERIFY
artifact_type: investigation
tags: [tagging, workflows]
---

# Investigation — TCK-20260720-TAG-RELEVANCE-VERIFY

## Current Behavior

### `validate_frontmatter.py` checks form + registry membership only, never relevance

`tools/validate_frontmatter.py::_check_tags()` (lines 152-181) runs exactly two checks per tag:
`canonical_form_violation()` (spelling/hyphenation) and, if a `registry` dict is passed,
`is_tag_registered()` (does this tag exist at all in `registries/tag_registry.jsonl`). Neither
check reads the ticket's title, scope, or `related_code_areas` — a syntactically valid, registered
tag that has nothing to do with the ticket's actual content passes cleanly. Confirmed by direct
read of the full function; no other function in this file (`_validate_ticket`, `_validate_artifact`,
`validate_file`, `validate_directory`) does semantic/content-based tag checking either.

### `tag_registry.py` has no concept of "relevant to this ticket"

`tools/tag_registry.py` (432 lines, read in full) manages registration (`add_tag`), lookup
(`is_tag_registered`, `check_tags_registered`), and category validity (`category_values`,
`is_category_registered`). Every function operates on a bare tag string against the registry —
none accepts or reasons about ticket content (title/scope/`related_code_areas`). This is a genuine
gap, not an oversight this ticket duplicates: the registry's whole design (per
`docs/guidelines/tag_taxonomy.md`'s "Tag Registry" section) is deliberately about *existence*, not
*fit*.

### `create-tickets.js`'s Structure phase — where batch tags are assigned today

`.claude/workflows/create-tickets.js:503-508` (Step 4's `tags:` rule block, current post-
`TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX` text) instructs the Structure-phase synthesis agent to
follow the full 5-category taxonomy, gated by an evidence guardrail: "Assign a Subsystem/Topic (or
Phase/Milestone, Quality-attribute, Meta-Process) tag only when this concern's investigated
`files_found` or domain clearly indicates one ... Do not guess a tag from the title alone if
`files_found` doesn't support it." This guardrail is prompt-text discipline only — nothing
downstream re-checks that the agent actually followed it. `TASK_SCHEMA` (lines 361-408) has no
field for a relevance self-assessment or confidence score. The only post-hoc code check on
`tags` is the registered-tags-only gate at lines 569-602 (`tag_registry.check_tags_registered`),
which — like `validate_frontmatter.py` — checks existence, not fit.

### `ticket-scoper.md` — where single-ticket tags are assigned today

`.claude/agents/ticket-scoper.md:33` instructs: pick tags per `docs/guidelines/tag_taxonomy.md`,
"ideally from what `python3 tools/tag_registry.py list` already shows registered." No relevance
self-check instruction exists. The `## Output` section (lines 80-93) returns the ticket markdown,
a conflict report, the write path, `summary`, and `suggested_skills` — no relevance/confidence
field.

### The existing narrow precedent: `mistag_warning` (security-only, folded-in, advisory)

`.claude/workflows/implement-ticket.js` already implements a structurally identical but narrower
mechanism for exactly one case (an untagged-`security` ticket whose `Related Code Areas` looks
auth/secret-adjacent):

- `TICKET_SCHEMA` (lines 72-91) carries an optional `mistag_warning: boolean`, with an inline
  comment (lines 84-87) explicitly noting it is "a 4th place in this file independently computing
  tag-related logic ... NOT mirrored in `ticket-scoper.md`."
- Computed **inline**, in the same Scope-phase agent turn that already produces the ticket (both
  the "Load existing ticket" branch, Step 3b at line 117, and the "Create new ticket" branch,
  Step 8 at line 163) — a keyword substring match (`credential`, `secret`, `password`, `api_key`,
  `private_key`, `.env`, `oauth`, `jwt`) against `Related Code Areas`, checked against whether
  `tags` includes `security`.
- Surfaced via `log(...)` only (line 394-396), never `pushEvent`, never a blocking branch, never a
  `reason_code`. `scopeReasonCode` (lines 383-385) is keyed off `conflicts`/`unregisteredTags`
  only — `mistag_warning` contributes nothing to it.
- Confirmed by direct read of `stored_artifacts/TCK-20260705-WORKFLOW-SECURITY-GATE/investigation.md:196`
  that this design was chosen specifically because a second agent call was rejected: "[the design]
  must not add a second agent call."

This is a real, already-shipped instance of the exact pattern this ticket's own Assumptions/Open
Questions section asks about (see Risks and Open Questions below) — for a semantically narrower
question (one hardcoded keyword-vs-tag check) than this ticket's (open-ended "does this tag
plausibly fit the ticket").

### `done_checker_static.py` — current state, post-`TCK-20260720-TAG-TOUCHPOINT-CLEANUP`

Read in full at its current (already-modified) state. Two structural facts matter for this
ticket's drift-check placement:

1. **Part A / Part B split is real and load-bearing.** Part A (`run_static_precheck`, lines
   290-306) aggregates 6 checks that feed `done-checker`'s pre-Finalize `DOD_BLOCKED` gate — every
   entry in its `checks` tuple is a blocking PASS/FAIL/NA condition. Part B
   (`run_finalize_selfcheck`, lines 522-533) aggregates 4 checks that feed the post-Finalize
   `FINALIZE_INCOMPLETE` gate — same blocking shape. **Neither tuple is a safe home for an
   advisory-only check** — anything added to either `checks` tuple becomes part of the
   PASS/FAIL/NA grid that `classify_checklist_failure` and the two blocking statuses
   (`DOD_BLOCKED`, `FINALIZE_INCOMPLETE`) consume.
2. **A precedent for a genuinely non-blocking Finalize-time check already exists and is fully
   documented as the intended shape**: `check_monitoring_write_recorded()` (lines 437-467). Its
   own docstring states it "Deliberately has no `tier` parameter and no NA branch ... Built ...
   as a loud-but-non-blocking warning (a FAIL here never changes `status` away from `'DONE'` ...
   not as a 4th condition in `run_finalize_selfcheck` ... see that ticket's plan.md Design
   Decision 2 for why it is wired in separately, at a later call site." `implement-ticket.js`
   confirms the wiring: called via its own `bash()` block (lines 1356-1364) **after**
   `writeMonitoring('DONE')` and the final blocking-checks return (lines 1290-1347) — its result
   only ever produces a `log(...)` WARNING (line 1376) and a `pushEvent(..., 'failed', ...)` event
   (line 1375), never altering the `status: 'DONE'` in the final `return` (lines 1379+).

This is the exact mechanical shape AC #2's drift check needs, and it is already built, tested, and
running in production for a different (but structurally identical: "advisory Finalize-time
check, never gates ticket close") concern.

`classify_checklist_failure()` (lines 339-382) and `_frontmatter_has_unregistered_tags()` (lines
309-337) — the two functions `TCK-20260720-TAG-TOUCHPOINT-CLEANUP` just touched — are unrelated to
this ticket's scope: they classify an *already-failing* `frontmatter_valid` condition's cause
(canonical-form/registry-membership), not tag *relevance*, and they are not being extended or
duplicated by anything recommended below. No conflict, no overlap requiring coordination.

### `registry_query.py` — already has the primitive the drift check needs

Post-`TCK-20260720-TAG-TOUCHPOINT-CLEANUP`, `tools/registry_query.py::candidate_tags_from_text(*texts, root=None)`
(lines 17-30) returns the subset of live `subsystem-topic` registry tags present as a
case-insensitive substring anywhere in the concatenation of its text arguments. This is exactly
the "derive candidate tags from text" primitive AC #2 needs (given `Files Changed`/
`related_code_areas` text, derive plausible tags), already registry-backed (no hardcoded seed
list — that was this same swap's own point), already tested
(`tests/tools/test_registry_query.py`), and already imported by `.claude/agents/
concern-investigator.md`. No new tag-matching logic needs to be invented for the drift check —
only a new caller.

### `security-reviewer.md` and `mechanics-auditor.md` — the "second independent agent look" pattern's actual cost profile

Both read in full.

- **`security-reviewer`**: a full subagent (`.claude/agents/security-reviewer.md`, 36 lines) with
  its own registry lookup step, a fixed 6-category checklist (injection, deserialization, path
  traversal, subprocess, secrets, raw-domain-model exposure), and a structured
  `APPROVED`/`NEEDS_CHANGES`/`BLOCKED` verdict. Per `docs/ai/agents.md:328-357`, it is wired as a
  **conditional blocking gate** — `implement-ticket.js`'s Security-Review phase fires only when
  `tags` includes `security`, and halts the whole workflow (`SECURITY_BLOCKED`) on
  `NEEDS_CHANGES`/`BLOCKED`, never proceeding to Verify/Finalize. It exists as a dedicated agent
  because (a) its checklist is domain-expert-shaped (injection/deserialization/etc. are not
  generic judgment calls), and (b) its verdict is load-bearing — it stops the pipeline.
- **`mechanics-auditor`**: a full subagent (`.claude/agents/mechanics-auditor.md`, 81 lines) that
  reads an entire Mechanics Bible chapter, extracts every formula, and does bit-identical
  comparison against source — a genuinely large read/compare task across up to 6 chapters. Per
  `docs/ai/agents.md:291-320`, it is explicitly **not** wired into any blocking pipeline call
  site ("mechanics-auditor has no pipeline call site — so compliance depends entirely on this
  agent actually running the script"); it is invoked on demand. It exists as a dedicated agent
  because the *task size* (full-chapter formula extraction and comparison) genuinely exceeds what
  another agent's turn could absorb as a side task.

Neither agent's dedicated-agent shape is justified by "this is judgment-based, so it needs
independence" alone — `security-reviewer`'s justification is blocking-gate correctness for a
domain-expert checklist; `mechanics-auditor`'s is raw task size. Both conditions are explicitly
absent in this ticket's advisory relevance/drift checks: neither is blocking (per Out of Scope),
and both operate on data (a ticket's own title/scope/`related_code_areas`/`tags`) already fully
present in the same turn that produces or closes the ticket — there is no "read a whole
chapter/diff nobody else has seen" task-size justification for a second cold agent call.

## Mechanics / Engine Constraints

None. This ticket, like all of its sibling tag-tooling tickets (`TCK-20260720-TAG-TOUCHPOINT-CLEANUP`,
`TCK-20260720-TAG-CORPUS-REPAIR-SWEEP`, `TCK-20260705-TAG-SKILL-SUGGEST`,
`TCK-20260706-CREATE-TICKETS-TAG-CHECK`), touches only agent/workflow tooling
(`.claude/workflows/`, `.claude/agents/`, `tools/gate_checks/`, `tools/tag_registry.py`,
`tools/registry_query.py`) — no `docs/mechanics/` chapter or `docs/engine/` contract governs
ticket-tagging or gate-check internals. `layer: ai` per `docs/guidelines/tag_taxonomy.md`'s own
Meta-Process disambiguation rule (`layer: ai` names the Claude agent-orchestration system, not
gameplay cognition) — consistent with the ticket's own frontmatter and every sibling ticket's
choice.

## Parity Ledger Overlap

None found, and none expected. Grepped all `docs/parity_ledger/*.yaml` for
`tag-relevance|tag-drift|hallucinat` — zero hits. Broader `tag`/`registry` greps (run by the three
directly-preceding sibling tickets — `TCK-20260720-TAG-TOUCHPOINT-CLEANUP`,
`TCK-20260720-TAG-CORPUS-REPAIR-SWEEP`, `TCK-20260705-TAG-SKILL-SUGGEST`, each independently
re-confirming the same conclusion) only ever match unrelated gameplay concepts that happen to
contain the substring "registry" (`quest_registry`, `GroupRegistry`, terrain-cost registry,
`test_registry_bridge`) or unrelated XP-plateau vocabulary (`skill_silence`). The Parity Ledger's
stated scope (`docs/parity_ledger/schema.json`, CLAUDE.md's Authoritative Mechanics Rule) is
legacy-vs-V2 simulation-behavior parity — agent-tooling/ticket-workflow behavior is categorically
outside it, matching every sibling tagging ticket's own identical finding. **No parity ledger
entry needs updating for this ticket, and none should be added.** No P0 entries are touched.

## Prior Work

- **`TCK-20260705-WORKFLOW-SECURITY-GATE`** (`stored_artifacts/`, read in full) — built
  `mistag_warning`, the direct structural precedent analyzed above. Its own investigation.md
  explicitly rejected a second agent call for a narrower tag-mismatch problem ("it must not add a
  second agent call") — directly on point for this ticket's own open design question.
- **`TCK-20260720-TAG-TOUCHPOINT-CLEANUP`** (`stored_artifacts/`, read in full, just landed) —
  most recent modifier of `done_checker_static.py` and `registry_query.py`, the two files this
  ticket's drift-check recommendation touches. Confirmed no overlap: that ticket's
  `classify_checklist_failure`/`_frontmatter_has_unregistered_tags` work classifies an
  already-FAILing canonical-form/registry-membership condition; this ticket's drift check is a
  wholly separate, always-advisory function that must not be folded into either. That ticket also
  removed `registry_query.py`'s hardcoded `SEED_TAGS`, which is exactly what makes
  `candidate_tags_from_text()` usable as this ticket's drift-detection primitive without
  reintroducing a second hand-maintained word list.
- **`TCK-20260720-TAG-CORPUS-REPAIR-SWEEP`** (`stored_artifacts/`, read in full) — built a
  report-only, non-blocking, corpus-wide sweep for a *different* tag-quality dimension
  (registry-membership/canonical-form/category-validity, explicitly not relevance — this ticket's
  own Out of Scope confirms the two are deliberately not merged). Directly useful precedent for
  this ticket's drift check nonetheless: it establishes the "report-only, no write path, no `--fix`
  flag" convention (`tools/tag_corpus_sweep.py`) this ticket's own AC #2 wording ("flags ... for
  human review, without auto-adding or auto-removing any tag") matches almost verbatim.
- **`TCK-20260705-TAG-SKILL-SUGGEST`** (`stored_artifacts/`, read in full) — built the
  `suggested_skills` note pattern (computed inline in `ticket-scoper`'s existing Output turn,
  surfaced via `log(...)`, no second agent call) that this ticket's Out of Scope explicitly wants
  followed as precedent ("matching this repo's existing practice for soft/judgment-based
  signals"). Its own Risk #1 resolution ("no other agent currently reads tags for routing
  purposes ... building a shared location now would be speculative generality for a 4-entry
  table") is directly analogous reasoning to this ticket's own dedicated-agent-vs-folded-in
  question.
- **`TCK-20260706-CREATE-TICKETS-TAG-CHECK`** (`stored_artifacts/`, read in full) — built the
  orchestrator-side (not agent-side) `check_tags_registered` gate in `create-tickets.js`'s
  Structure phase, including the "skip the task, continue the batch, log a WARNING" precedent
  (`droppedScopes`/`tasksWithUnregisteredTags`) this ticket's relevance flag should structurally
  mirror if/when it needs a per-task, non-fatal signal in the same phase.
- **`TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX`** (`tickets/done/`, read in full, explicitly named
  Out of Scope by this ticket — confirmed non-overlapping, not duplicated or absorbed) — most
  recently touched exactly the Structure-phase `tags:` prompt block (lines 503-508) this ticket's
  relevance-check recommendation (see below) would also need to extend. The evidence guardrail
  that ticket added ("only assign ... when `files_found`/domain clearly indicates one ... Do not
  guess a tag from the title alone if `files_found` doesn't support it") is itself already a
  primitive form of relevance-checking — this ticket's AC #1 for the Structure-phase path is
  naturally an *extension* of that existing guardrail (asking the same agent turn to also flag an
  already-assigned tag that doesn't fit), not a parallel new mechanism.

## Risks and Open Questions

### RESOLVED — dedicated new agent vs. folded-in check (ticket's own named open question)

**Recommendation: fold the relevance check into `ticket-scoper`'s and `create-tickets.js`'s
existing output — do not add a dedicated new agent.**

Evidence, all code-traceable:

1. **A structurally identical mechanism already ships in this exact shape for a narrower case**
   (`mistag_warning`, analyzed above) — computed inline, in the same agent turn, surfaced via
   `log(...)` only, explicitly chosen over a second agent call
   (`stored_artifacts/TCK-20260705-WORKFLOW-SECURITY-GATE/investigation.md:196`). This ticket's
   relevance check is the general form of the same problem `mistag_warning` solves for one
   hardcoded case (security). Reusing the shipped pattern is lower-risk than introducing a second
   pattern for the same problem class in the same file.
2. **The advisory/non-blocking constraint (this ticket's own Out of Scope) removes the strongest
   justification a dedicated agent would otherwise have.** `security-reviewer` is a dedicated
   agent because its verdict is load-bearing (it halts the pipeline) and its checklist is
   domain-expert-shaped. `mechanics-auditor` is a dedicated agent because its task (full-chapter
   formula extraction) is too large to absorb as a side task in another agent's turn. Neither
   condition holds here: the relevance check never blocks anything, and its input (a ticket's own
   title/scope/`related_code_areas`/tags — already fully present in the same turn that assigns
   the tags) requires no additional reading a fresh agent would need to re-derive from cold
   context.
3. **Cost asymmetry is concrete, not abstract.** A dedicated agent call means: a new
   `.claude/agents/*.md` file, a new schema, a new wiring point in both `create-tickets.js`'s
   Structure phase (parallel `pipeline()` call, one per task) and `implement-ticket.js`'s Scope
   phase, a new `docs/ai/agents.md` entry, and — per this repo's own established convention (every
   `agent()` call in this codebase produces a monitoring event) — a new event per ticket, purely
   for a warn-only signal. The folded-in alternative costs zero additional agent calls: the same
   turn that already reads the ticket's own title/scope/`related_code_areas` (because it is
   producing or has just produced them) adds one more self-check instruction and one more output
   field.
4. **`TCK-20260705-TAG-SKILL-SUGGEST`'s own Risk #1 resolution reasoned identically** for a
   different tag-output feature in the same two call sites (`ticket-scoper`/`create-tickets.js`):
   "no other agent currently reads tags for routing purposes ... building a shared location now
   would be speculative generality." The same "don't build machinery for a signal with exactly
   two known consumers" logic applies here.

**Concrete recommendation for Plan:**
- `ticket-scoper.md`: extend the `## Output` section with a `tag_relevance_flags` (or similarly
  named) list — for each assigned tag, a one-line self-assessment of whether the tag's registered
  category/description plausibly matches the ticket's own title/scope/`related_code_areas`; empty
  list if no flag. Computed as part of the same agent turn that already picks the tags (Ticket
  Format section, `tags:` line, `.claude/agents/ticket-scoper.md:33`) — not a second read of the
  ticket.
- `create-tickets.js`'s Structure phase: extend `TASK_SCHEMA` (currently lines 361-408) with the
  same field, and extend the existing Step 4 `tags:` prompt rule block (lines 503-508) — which
  already asks the agent to ground Subsystem/Topic tags in `files_found` evidence — with a
  parallel self-check instruction: for each tag ultimately assigned, note if it does *not* clearly
  match the investigated `files_found`/domain. This is additive to an existing, already-evidence-
  gated instruction block, not a new prompt section.
- Both surfaced via `log(...)` only in the orchestrator (mirroring `mistag_warning`'s line
  394-396 and `create-tickets.js`'s existing `tasksWithSkills` logging at lines 604-607) — never a
  `pushEvent` field of its own, never a `reason_code`, never a blocking branch.

### RESOLVED — where the drift check (AC #2) lives mechanically

**Recommendation: a new function in `tools/gate_checks/done_checker_static.py`'s Part B section
(near `check_monitoring_write_recorded`), called directly from `implement-ticket.js`'s Finalize
phase via its own `bash()` block, positioned *after* `writeMonitoring('DONE')` and the blocking
`run_finalize_selfcheck` return — explicitly NOT added to `run_finalize_selfcheck`'s `checks`
tuple.**

Evidence:

1. `run_static_precheck` and `run_finalize_selfcheck`'s `checks` tuples (lines 295-302, 524-529)
   are exclusively blocking PASS/FAIL/NA conditions feeding `DOD_BLOCKED`/`FINALIZE_INCOMPLETE`.
   Adding the drift check to either risks it being (mis)treated as a 7th/5th blocking condition —
   directly contradicting AC #3 ("Neither mechanism blocks or fails the ticket pipeline
   outright").
2. `check_monitoring_write_recorded()` is the *exact* precedent for "a genuinely non-blocking
   Finalize-time check, deliberately wired outside the blocking-checks aggregation, at its own
   later call site" — its own docstring states this design rationale in almost the same words
   AC #3 uses. `implement-ticket.js`'s wiring (lines 1356-1377) shows precisely how to surface a
   FAIL/flag as a `log(...)` WARNING plus a `pushEvent(..., 'failed', ...)` event without ever
   touching the final `status: 'DONE'`.
3. The drift check's actual detection primitive already exists:
   `registry_query.py::candidate_tags_from_text(*texts, root=None)` — call it with the closing
   ticket's `Files Changed` + `Related Code Areas` section text, and compare the resulting
   candidate `subsystem-topic` tag set against the ticket's declared `tags:` frontmatter. If
   `candidate_tags` is non-empty and disjoint from declared tags, flag for human review (evidence
   string names the specific candidate tag(s) missing). No new tag-matching logic needs
   inventing — only a new function that reads a ticket's `Files Changed`/`Related Code Areas`
   body text (a new small parse, since `extract_frontmatter()` only parses the YAML block, not
   body sections — see Anti-Drift Hazards) and calls the existing primitive.
4. Concrete shape, modeled directly on `check_monitoring_write_recorded`'s own signature
   convention (no `tier` parameter, no NA branch — same reasoning: AC #2 applies to any tier that
   has declared tags at all, not gated on staging-artifact tier the way Part A/B's other checks
   are):
   ```python
   def check_tag_drift(
       ticket_id: str, ticket_path: Path = None
   ) -> tuple[str, str]:
       """Advisory-only: flags a possible mismatch between the closing ticket's declared `tags:`
       and tags its own `Files Changed`/`Related Code Areas` body sections would suggest. Never
       returns a status that should gate ticket close — callers must not add this to
       run_finalize_selfcheck's checks tuple. Mirrors check_monitoring_write_recorded's
       deliberate placement outside the blocking-checks aggregation."""
   ```
5. `implement-ticket.js` wiring: a new `bash()` block placed immediately after the existing
   `check_monitoring_write_recorded` block (after line 1377, before the final `return`), following
   the identical parse-marker/try-catch/log-WARNING pattern already used twice in that same region
   (`finalizeCheckOutput`, `monitoringCheckOutput`) — never altering `status: 'DONE'` in the final
   `return`.

### Open, non-blocking: body-section text extraction has no existing shared parser

`extract_frontmatter()` (`validate_frontmatter.py:69-109`) only parses the YAML frontmatter block
— it explicitly stops at the closing `---` and never reads `## Files Changed`/`## Related Code
Areas` body text. No function anywhere in `tools/` currently extracts a named `##`-section's body
text from a ticket markdown file. The drift check needs one. This is a small, new, single-purpose
helper (find the `## Files Changed` / `## Related Code Areas` headings, return the text between
each and the next `## ` heading) — flagged here so Plan scopes it explicitly rather than
discovering it mid-implementation. Not blocking: this is a straightforward, bounded addition with
no architectural ambiguity, just not something to assume already exists.

### Not an open question: this ticket's own precedent citation is confirmed accurate

The ticket's Out of Scope cites `mistag_warning` as "warns rather than blocks" precedent — this is
confirmed accurate by direct code read (see Current Behavior above), not merely restated from the
ticket text.

## Anti-Drift Hazards

- **Do not add a second agent call for either mechanism.** Both this investigation's evidence and
  `TCK-20260705-WORKFLOW-SECURITY-GATE`'s own explicit design rejection point the same direction.
  A future implementer proposing "just spawn a quick relevance-checker agent" should be pointed
  back to this investigation's cost-asymmetry analysis, not re-litigate it from scratch.
- **Do not add either flag to `run_static_precheck`'s or `run_finalize_selfcheck`'s `checks`
  tuple**, and do not let either flag's status use the `PASS`/`FAIL`/`NA` vocabulary those tuples'
  consumers (`classify_checklist_failure`, the two blocking gate statuses) interpret as
  blocking-relevant. Use a distinct status vocabulary (e.g. `CLEAN`/`FLAGGED`) so no downstream
  consumer can misclassify an advisory flag as a DoD failure.
- **Do not let the relevance/drift check reimplement tag-matching logic.** The drift check must
  call `registry_query.py::candidate_tags_from_text()` — never hand-roll a second substring/seed-
  word matcher, which is exactly the duplication `TCK-20260720-TAG-TOUCHPOINT-CLEANUP` just spent
  an entire ticket removing (the old hardcoded `SEED_TAGS` tuple).
- **Do not conflate this ticket's relevance/drift checks with `TCK-20260720-TAG-CORPUS-REPAIR-
  SWEEP`'s registry-membership/canonical-form/category-validity sweep.** Both this ticket's own
  Out of Scope and that ticket's own investigation.md are explicit that the two are deliberately
  separate, non-merged tools answering different questions ("is this tag validly formed and
  registered" vs. "does this tag actually describe what the ticket is about").
- **Do not let the Structure-phase relevance self-check regress the evidence guardrail
  `TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX` just added** (files_found-grounded Subsystem/Topic
  assignment). The relevance flag is additive to that guardrail, not a replacement — removing or
  weakening the "do not guess from the title alone" instruction while adding the new flag would be
  a silent scope-creep regression of a very recently landed, separately-scoped fix.
- **Keep both mechanisms genuinely advisory end-to-end.** It would be an easy, incremental drift
  for a future ticket to add a `pushEvent`/`reason_code` for either flag "for visibility," which
  would start making them participate in monitoring-based automation (retro reports, dashboards)
  as if they were meaningful pass/fail signals — matching neither this ticket's own AC #3 nor
  `mistag_warning`'s established precedent (log-only, no `pushEvent`, no `reason_code`).

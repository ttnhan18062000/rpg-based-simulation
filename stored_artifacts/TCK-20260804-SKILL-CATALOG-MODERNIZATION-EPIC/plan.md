---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC
artifact_type: plan
tags: [skills, workflows, process-improvement]
---

# Implementation Plan — TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC

## Summary

This epic implements nothing directly. This plan is a child-ticket breakdown: it converts
investigation.md's 5 scope items (plus the 4 explicitly-flagged open judgment calls) into 10
concrete, independently-sized child tickets, each with a proposed ID, tier, one-paragraph scope,
an explicit "must not duplicate" citation to the specific prior ticket it builds on, and a
sequencing note. Two of the epic's original scope items (Item 2 "ticket-metadata triggering" and
Item 1's "mechanism-1 fix direction") are merged into one child ticket per investigation.md's own
finding that they are the same underlying design decision, not two independent pieces of work.
The "popular/community skill sourcing" item is split into three child tickets (disclosed-community
pair, undisclosed-fingerprint quartet, and the smaller dangling-cross-reference cleanup) per the
distinct remediation shapes investigation.md documented. The two open judgment calls flagged in
investigation.md's Risks section (frontend-design reopening, CODEX event-trace gap) each become
their own small, explicitly-scoped child ticket rather than being silently folded in or dropped.
One genuinely unresolved design question (the pass/fail-verdict asymmetry risk of converting
api-design/debugging/performance to hard gates) is deliberately NOT decided here — it is the core
investigation deliverable of child ticket 3 itself, per the Planning Rule against unilaterally
resolving open questions that change implementation approach.

## Steps

### Step 1 — File TCK-20260805-SECURITY-REVIEW-HOTFIX-GAP
**Tier:** hotfix
**Scope:** Fix `.claude/skills/implement-ticket/SKILL.md:70`'s "Hotfix tier skips..." summary
paragraph, which currently omits `Security-Review` from its "still runs for hotfix" enumeration
even though the same file's step 11 states "not tier-gated" two paragraphs earlier
(investigation.md Item 1, citing direct read of `SKILL.md:70` and cross-referencing
`implement-ticket.js:1227-1279`'s tier-unconditional gate placement). Add `Security-Review` to the
enumeration (or restructure the paragraph so it no longer contradicts step 11). Extend
`tools/gate_checks/workflow_meta_conformance.py` / `tests/tools/test_workflow_meta_conformance.py`
per test_plan.md item 1's first New Test entry — a static assertion that the SKILL.md enumeration
includes every `meta.phases` entry the JS itself marks tier-unconditional, cross-referenced against
actual gate placement, not just phase-name string matching.
**Must not duplicate:** `TCK-20260804-SKILL-JS-PHASE-SYNC` and `TCK-20260804-SKILL-DRIFT-DETECTION`
already fixed this exact bug class (documented-but-silently-skipped phase enumeration) in other
paragraphs of SKILL.md today — this ticket applies the identical, narrow, one-paragraph-scope
discipline to the specific location those two tickets' scopes did not cover (the hotfix-summary
paragraph, not the phase list itself). Do not fold into a broader SKILL.md rewrite.
**Verify:** `tests/tools/test_workflow_meta_conformance.py` (extended); manual re-read of the
corrected paragraph against `implement-ticket.js` lines 470, 914, and 1227-1279 to confirm no new
mismatch is introduced in the other direction (e.g. implying Architecture-Verify also runs for
hotfix, which it does not) — test_plan.md's Anti-Drift Test Guards, final bullet.
**Sequencing:** No dependencies. Land first — it is the smallest, most self-evident fix and the one
already confirmed to have caused a real miss (`TCK-20260731-GATE-BYPASS-HARDENING`).

### Step 2 — File TCK-20260805-SECURITY-GATE-FIRING-MONITOR
**Tier:** standard
**Scope:** Build a data-quality check (per test_plan.md item 1's second New Test entry) that reads
real `agent-monitoring/events.jsonl` history and confirms every `security`-tagged,
post-`WORKFLOW-SECURITY-GATE`-dated ticket's events actually contain a `Security-Review` phase
entry — closing the gap between "code says unconditional" (already proven by
`WORKFLOW-SECURITY-GATE`'s existing tests) and "real runs show it happened" (which
`TCK-20260731-GATE-BYPASS-HARDENING` proves is not always true). Follow
`tools/agent-monitoring/retrieval_baseline_metrics.py:1-90`'s pattern (frozen constant with a
load-bearing comment, a `build_*_section()`-style function with a `derivation` string, per-run
grouping via `defaultdict`), per investigation.md Item 4's citation of that file as the house style
for this class of tool. This reads live historical JSONL data, not a fixture — it is an integration
/ data-quality guard, not a pytest unit test in the usual sense.
**Must not duplicate:** `TCK-20260708-RETRO-TAG-BREAKDOWN`'s existing `## Tag Breakdown —
Process/Skill-signal` section in `generate_retro.py:876-900` already checks `security`-tagged runs
against `Security-Review`/`SECURITY_BLOCKED` hits for its own reporting purpose — this ticket's tool
is a stricter pass/fail assertion suitable for a gate check, not a rebuild of that reporting
section. Coordinate: both read the same `tools.jsonl`/`events.jsonl` source; do not let this
ticket's tool re-implement `RETRO-TAG-BREAKDOWN`'s JSONL-loading helpers — import them.
**Verify:** New test(s) in `tests/tools/` (or a dedicated `tools/gate_checks/` module + matching
test file) confirming the checker correctly flags the known `GATE-BYPASS-HARDENING` historical miss
and passes clean for `CODEX-LIVE-TRANSPORT`/`CODEX-PILOT-ORCHESTRATION`.
**Sequencing:** No hard dependency on Step 1, but land after it — the monitor's purpose (catching
future misses) is most meaningful once the root-cause paragraph is fixed; sequencing them in
parallel risks the monitor being written against a not-yet-corrected mental model of "what should
have fired."

### Step 3 — File TCK-20260805-SKILLS-DOC-STALENESS-FIX
**Tier:** hotfix
**Scope:** Correct `docs/ai/skills.md`'s "Tag-Based Skill Suggestions" section, which still
describes the mechanism as purely advisory with no mention of (a) the `security` tag's hard-gate
exception (`TCK-20260705-WORKFLOW-SECURITY-GATE`) or (b) the live single-source mapping mechanism
(`triggers_skill` field on `tag_registry.jsonl` rows, read via
`tools/tag_registry.py::get_skill_mapping()`, per `TCK-20260720-SKILL-MAPPING-DEDUP`). Both
postdate this doc's last edit per investigation.md's Docs Requiring Update section. This is a
factual correction of the CURRENT state, independent of any future gate-conversion decision.
**Must not duplicate:** Do not re-describe or re-build `SKILL-MAPPING-DEDUP`'s dedup mechanism or
`WORKFLOW-SECURITY-GATE`'s gate — this ticket only updates prose to accurately describe what those
two tickets already shipped.
**Verify:** `python3 -m pytest tests/tools/test_validate_frontmatter.py -q` (regression, universal
precedent per test_plan.md item 6) plus a manual diff-read confirming only the "Tag-Based Skill
Suggestions" section changed.
**Sequencing:** No dependencies; can land any time. Recommend landing before Step 4
(SKILL-GATE-CONVERSION-DECISION) so that ticket edits an already-accurate doc rather than a stale
one — Step 4 must still touch this same section again if it decides to add new gates (a follow-on
edit within Step 4's own scope, not a duplicate ticket).

### Step 4 — File TCK-20260805-SKILL-GATE-CONVERSION-DECISION
**Tier:** standard (investigation-heavy)
**Scope:** Merges the epic's Item 1 "mechanism-1 fix direction" and Item 2 "ticket-metadata-driven
triggering re-evaluation" into one ticket, per investigation.md Item 2's own conclusion (citing
`ticket-scoper.md:86-93`'s live `tag_registry.py skill-mapping` read and the 2-clean-fires-vs.-0
evidence): "the real lever is advisory→binding conversion for the mapped tags that don't yet have a
gate (`api-design`, `debugging`, `performance`), not raising the count of mapped tags." This ticket
investigates, per-skill (not blanket), whether `api-design-principles`, `debugging-strategies`, and
`python-performance-optimization` should each be converted from CLAUDE.md's situational file-path
row into a binding `implement-ticket.js` gate mirroring `security`'s pattern
(`implement-ticket.js:1227-1279`), a tag-mapping-driven advisory→gate conversion, or neither. It
must explicitly address the asymmetry risk investigation.md's Risk #4 flags: unlike `security`
(clean APPROVED/NEEDS_CHANGES/BLOCKED verdict shape), these 3 skills have no obvious pass/fail
verdict shape — "did you follow API design principles" is a soft judgment. This is a genuinely
unresolved question this plan does NOT decide (see Unresolved Questions below).
**Must not duplicate:** Do not rebuild `tools/tag_registry.py::get_skill_mapping()` or the
`skill-mapping` CLI subcommand (`SKILL-MAPPING-DEDUP`, 2026-07-20) — any mapping expansion adds a
`triggers_skill` field via `add_tag()` to a registry row, never hand-edits 4 files. Do not
re-litigate `TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION`'s finding that mechanism 2 (tag
suggestion) is advisory-by-design and correctly wired — that finding stands; this ticket only
decides whether specific already-mapped tags should gain a gate. Other writers to
`tag_registry.jsonl` this ticket must coordinate with if it adds a `triggers_skill` field: the
append-only `add_tag()` writer itself (`SKILL-MAPPING-DEDUP`), `TAG-RELEVANCE-VERIFY`'s
`tag_relevance_flags` consumer (reads the same registry rows for a different self-check), and
`tests/tools/test_tag_skill_mapping_check.py`'s drift check (must keep passing, per test_plan.md's
Regression Surface). If it adds a new `implement-ticket.js` gate block, it must include a
zero-added-latency negative test per test_plan.md's Anti-Drift Test Guards (a ticket without the
triggering tag produces zero new events) — `WORKFLOW-SECURITY-GATE`'s own AC3 established this as
mandatory for any new gate.
**Verify:** Per test_plan.md item 3: `test_get_skill_mapping_includes_new_tag_<name>` in
`tests/tools/test_tag_registry.py`, plus (if any gate is added) the full
`WORKFLOW-SECURITY-GATE`-mirrored set (trigger case, clean-pass case, zero-latency negative case,
explicitly including a hotfix-tier trigger case since Step 1 found tier-independence was not
perfectly followed in practice for the existing gate). `node -c .claude/workflows/implement-ticket.js`
for any JS edit.
**Sequencing:** Depends on Step 3 landing first (edits the same `docs/ai/skills.md` section; must
edit the corrected version, not the stale one). Independent of Steps 5-9. If this ticket decides to
reinstate a CLAUDE.md file-path row (unlikely per investigation.md's finding that situational rows
are unreliable regardless of wording, but not foreclosed), coordinate with Step 9
(FRONTEND-DESIGN-TRIGGER-REOPEN) since both would touch CLAUDE.md's "Proactive Tool Use" table —
disjoint skill sets, no direct conflict, but same table.

### Step 5 — File TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED
**Tier:** standard
**Scope:** Research whether current, well-maintained popular alternatives exist for
`api-design-principles` and `architecture` — the 2 skills with explicit, disclosed
`source: community` / `risk: unknown` frontmatter (investigation.md Item 3, confirmed via direct
grep of all 16 `SKILL.md` files). `architecture` additionally references 3 sibling skills
(`@[skills/database-design]`, `@[skills/api-patterns]`, `@[skills/deployment-procedures]`) that do
not exist in this repo — confirm whether a swap or a targeted edit (removing the dangling
references) is the right fix. Produce a per-skill assessment (keep as-is / swap / adapt) with
reasoning, per AC3.
**Must not duplicate:** Do not decide the swap unilaterally in this Plan — investigation.md's Anti-
Drift Hazards explicitly reserves the actual research and swap decision for this child ticket's own
Plan/Implement phases. Do not touch `backend-testing`, `python-performance-optimization`,
`python-testing-patterns`, or `debugging-strategies` — those are Step 6's scope (different
disclosure status, same remediation shape internally, kept in one ticket together).
**Verify:** Per test_plan.md item 4: no pytest surface exists for `SKILL.md` content; verification is
a manual before/after diff read plus `python3 tools/validate_frontmatter.py .claude/skills/<name>/SKILL.md`
if frontmatter changes.
**Sequencing:** No dependency on Steps 1-4. Independent of Step 6 (may run in parallel).

### Step 6 — File TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED
**Tier:** standard
**Scope:** Research whether current, well-maintained popular alternatives exist for the 4 skills
investigation.md classified as "strong community candidate (undisclosed)" — `backend-testing`,
`python-performance-optimization`, `python-testing-patterns`, `debugging-strategies` — sharing an
identical structural fingerprint ("Master X... comprehensive guide", "When to Use This Skill" bullet
list, "Quick Start" code block; `backend-testing` additionally declares
`metadata.platforms: Claude, ChatGPT, Gemini`, confirming cross-platform non-Claude-specific origin)
but lacking `api-design-principles`/`architecture`'s disclosed frontmatter. Kept as one ticket
(not 4) because all 4 share the same remediation shape and the same undisclosed-fingerprint finding
— splitting further would not change the work, only the ticket count. Within the ticket, assessment
must still be per-skill, not blanket, per AC3's wording. If a swap is adopted, add honest
`source: community, risk: ...` disclosure frontmatter matching `api-design-principles`/
`architecture`'s existing pattern (test_plan.md item 4).
**Must not duplicate:** Do not fold `test-driven-development` into this ticket — investigation.md
classifies it as only a "moderate candidate" with a distinct, punchier tone (different community
family) and notes `SIX-SKILLS-INVESTIGATION` already scored it "correctly redundant, deliberately
diverging" — a content-quality swap would not change that usage verdict, so it is out of scope here
per the epic's own Out of Scope (do not re-litigate `SIX-SKILLS-INVESTIGATION`).
**Verify:** Same as Step 5 — manual diff read + `validate_frontmatter.py` if frontmatter changes.
**Sequencing:** No dependency on Steps 1-4. Independent of Step 5. If Step 4 decides to convert
`api-design-principles` or `python-performance-optimization`'s CLAUDE.md row to a gate, that is an
orchestration-level change (CLAUDE.md / `implement-ticket.js`) distinct from this ticket's
content-level change (`SKILL.md` body) — no hard dependency, but coordinate to avoid a frontmatter
edit (this ticket) landing concurrently with a gate-wiring edit (Step 4) touching the same skill
name in unrelated files.

### Step 7 — File TCK-20260805-SKILL-DANGLING-CROSSREF-CLEANUP
**Tier:** hotfix
**Scope:** Reconcile the dangling cross-references investigation.md's Item 3 found in
`frontend-design`, `doc-coauthoring`, and `brainstorming` — these reference sibling
first-party-style conventions (a `spec-document-reviewer` subagent, a `writing-plans` skill) that do
not exist as actual files/agents in this repo, reading as copied from an example skill set rather
than a third-party community pack. Distinct remediation shape from Steps 5-6: not "swap for a
popular alternative," but "remove or correct references to skills/agents this repo doesn't
actually have." Small, self-evident once each dangling reference is located (find each reference,
either remove it or replace it with the actual in-repo equivalent if one exists).
**Must not duplicate:** Do not touch `architecture`'s dangling references to `@[skills/database-design]`
etc. — those are Step 5's scope (disclosed-community classification, different remediation
category per investigation.md's explicit split between "community paradigm swap" and "reconcile
references" categories). Do not re-open the `frontend-design` exclusion question here — that is
Step 9's separate scope; this ticket only cleans up dangling text references, regardless of
whether `frontend-design`'s trigger condition is later reinstated.
**Verify:** `python3 -m pytest tests/tools/test_validate_frontmatter.py -q` (regression) plus manual
diff-read confirming each dangling reference was either removed or correctly repointed.
**Sequencing:** No dependencies. Independent of all other steps.

### Step 8 — File TCK-20260805-SKILL-USAGE-METRIC
**Tier:** standard
**Scope:** Add a new agent-monitoring metric: raw `Skill`-tool-invocation counts by skill name,
answering "was `/api-design-principles` ever actually invoked" — a question
`RETRO-TAG-BREAKDOWN`'s existing tag-based gate-hit breakdown cannot answer for a tag with no gate
(investigation.md Item 4, citing `generate_retro.py:876-900`'s `_TAG_GATE_PHASE`/
`_TAG_GATE_FINAL_STATUS` dicts, which render `"N/A — no gate implemented"` for the 3 ungated tags).
Follow `tools/agent-monitoring/retrieval_baseline_metrics.py:1-90`'s exact pattern: a frozen
`*_TOOL_NAMES`-style constant with a load-bearing comment, a `build_*_section()` function returning
a `derivation` string, per-run grouping via `defaultdict(int)` keyed by `run_id` with a documented
`"unattributed"` bucket for `run_id=None` (a bare `None` dict key breaks
`json.dumps(sort_keys=True)`). Must extract the skill name from `tools.jsonl`'s `input_summary`
field via regex (`re.search(r"'skill':\s*'([^']*)'", input_summary)`) — confirmed by investigation.md
direct inspection that this field is a Python-dict-repr string, not JSON; a naive `json.loads` will
crash. Plan (this ticket's own plan.md) decides the exact shape: a new `generate_retro.py` section
(recurring, alongside the existing Tag Breakdown sections) vs. a new standalone
`skill_usage_metrics.py` script (one-off/periodic, `retrieval_baseline_metrics.py`'s own shape) —
both are acceptable per the epic's Scope text.
**Must not duplicate:** Do not rebuild or modify `generate_retro.py`'s existing `## Tag Breakdown —
Subsystem/Topic` or `## Tag Breakdown — Process/Skill-signal` sections (`RETRO-TAG-BREAKDOWN`,
2026-07-08) — this metric must be additive, in its own clearly-distinguished section heading and
`derivation` string. Other writers to `agent-monitoring/` this ticket must not collide with:
`generate_retro.py`'s existing Reason Codes and Tag Breakdown section builders (same file, if the
new-section shape is chosen — must be a new function, not an edit to the existing ones);
`retrieval_baseline_metrics.py` (separate script, if the standalone shape is chosen — must not
import from or mutate it, only mirror its pattern). Output must never write outside
`agent-monitoring/` — confirmed `docs/`, `data/`, `config/` all serve unrelated concerns
(investigation.md Item 4 output-location constraint).
**Verify:** Per test_plan.md item 5: `test_skill_usage_section_counts_by_tool_name`,
`test_skill_usage_section_handles_python_dict_repr_input_summary`,
`test_skill_usage_section_omitted_when_no_skill_calls` (section-level omit-when-empty, but `0`
rendered per-skill-row for a skill invoked elsewhere but not in the current range — not omitted at
the row level).
**Sequencing:** No dependencies on any other step. Fully independent — can run in parallel with
everything else.

### Step 9 — File TCK-20260805-FRONTEND-DESIGN-TRIGGER-REOPEN
**Tier:** standard (small, decision-focused)
**Scope:** Resolve investigation.md's Risk #3 explicitly rather than carrying forward the stale
"zero evidence" framing either way: decide whether `frontend-design`'s CLAUDE.md exclusion
(`SKILL-TRIGGER-COVERAGE`) should be reopened given the 4 real frontend tickets found since 07-17
(CSS cascade fix, pagination, dropdown fix, tooltip wiring — investigation.md notes these are
maintenance/bugfix-shaped, not "build a new distinctive interface," which is `frontend-design`'s own
stated trigger condition per its `SKILL.md`). This ticket must read `frontend-design`'s actual
trigger wording and each of the 4 tickets' scope before deciding — not assume maintenance work
qualifies. Output: either a CLAUDE.md row change (if reopened) or an explicit written decision not
to reopen, with reasoning, recorded in this ticket's own `investigation.md`.
**Must not duplicate:** Do not re-litigate `SKILL-TRIGGER-COVERAGE`'s original exclusion decision
wholesale — only assess whether the new evidence (4 tickets) changes it. Do not conflate with Step
4's api-design/debugging/performance gate-conversion question — `frontend-design` is a "was it
wrongly excluded" question, disjoint from the "should an already-included skill become a hard gate"
question Step 4 answers.
**Verify:** No pytest surface (CLAUDE.md is prose); manual diff-read verification if changed, plus
`test_tag_skill_mapping_check.py` regression run if the change touches any tag-mapping-adjacent
text.
**Sequencing:** No dependency on Steps 1-8. If it reinstates a CLAUDE.md row, coordinate (not
depend) with Step 4, which may also touch CLAUDE.md's "Proactive Tool Use" table for a different
skill set.

### Step 10 — File TCK-20260805-CODEX-EVENT-TRACE-GAP-INVESTIGATION
**Tier:** standard (investigation-only)
**Priority:** P3 (deferred, non-blocking)
**Scope:** Diagnose whether `TCK-20260804-CODEX-PILOT-ENTRYPOINT`'s truncated event trace and
`TCK-20260804-CODEX-POSTTOOL-HOOK-COMMAND`'s complete absence of events (both DONE, both
`security`-tagged) reflect a monitoring-write gap unrelated to Security-Review specifically, or the
same hand-orchestration-skip pattern found for `GATE-BYPASS-HARDENING` (Step 1). Explicitly flagged
by the epic's own Out of Scope section as needing "its own targeted investigation (full session
history, not available from `tools.jsonl`/`events.jsonl` alone)" — this ticket is that targeted
investigation, deliberately deferred and not sequenced with the others since it requires different
evidence sources.
**Must not duplicate:** Do not re-run this epic's own investigation.md's `tools.jsonl`/`events.jsonl`
analysis — it already established these 2 tickets' traces are incomplete/absent; this ticket's job
is root-causing why, using session history this epic's investigation explicitly did not have access
to.
**Verify:** No pytest surface at investigation stage; any fix that results (if a real monitoring-
write bug is found) gets its own child ticket at that point, not decided here.
**Sequencing:** No dependency on Steps 1-9. Explicitly deferred/low-priority — file it so the
question is tracked, not silently dropped, but do not block any other child ticket's landing on it.

## Scope Guards

- No child ticket may re-litigate `TCK-20260705-SIX-SKILLS-INVESTIGATION`'s 6 "correctly redundant"
  verdicts (`test-driven-development`, `python-testing-patterns`, `backend-testing`, `architecture`
  content-vs-usage question is separate from Step 5/6's content-swap question, `doc-coauthoring`) —
  usage-count verdicts stand; only content (Steps 5-6-7) is in scope.
- No child ticket may rebuild `tools/tag_registry.py::get_skill_mapping()`, the `skill-mapping` CLI
  subcommand, or `generate_retro.py`'s existing `## Tag Breakdown` sections — all already exist
  (`SKILL-MAPPING-DEDUP`, `RETRO-TAG-BREAKDOWN`).
- No child ticket may remove a skill outright — user's explicit framing is improve, not prune.
- No child ticket may touch `prompt-builder` — Copilot-specific, correctly excluded, no new
  evidence changes this.
- Step 10 (CODEX event-trace gap) must not be diagnosed inside this epic or folded into Step 1/2 —
  it needs full session history this epic's evidence base does not have.
- No child ticket may decide the Step 4 gate-conversion asymmetry question in advance — that
  decision belongs entirely to Step 4's own investigation.

## Dependency Map

- Step 1 → independent, land first.
- Step 2 → soft-depends on Step 1 (sequencing preference, not a hard block).
- Step 3 → independent.
- Step 4 → depends on Step 3 (edits the same doc section Step 3 corrects first).
- Step 5 → independent.
- Step 6 → independent; soft-coordinate with Step 4 if `python-performance-optimization`'s trigger
  mechanism changes concurrently with its content.
- Step 7 → independent.
- Step 8 → independent.
- Step 9 → independent; soft-coordinate with Step 4 (both may touch CLAUDE.md's table, disjoint
  skill sets).
- Step 10 → independent, deferred/non-blocking.

All other pairs are independent and may be filed/executed in any order or in parallel.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Root cause of the 3-skill dual-mechanism non-firing identified with real evidence | Already satisfied by investigation.md itself (mechanism 1 vs. mechanism 2 root-caused with citations); no child ticket needed for this AC specifically | N/A — evidence-based finding, not a code change |
| Decision on expanding ticket-metadata-driven triggering | Step 4 | `test_get_skill_mapping_includes_new_tag_<name>` + WORKFLOW-SECURITY-GATE-mirrored gate test set (test_plan.md item 3) |
| Per-skill assessment of popular/community swap | Steps 5, 6, 7 | Manual diff-read + `validate_frontmatter.py` per skill (test_plan.md item 4) |
| Real agent-monitoring skill-usage metric exists | Step 8 | `test_skill_usage_section_*` set (test_plan.md item 5) |
| Child tickets created for each distinct, evidenced piece of work | This plan.md (Steps 1-10) | Ticket files exist in `tickets/inprogress/` once filed |
| docs/ai/skills.md (and CLAUDE.md if changed) updated | Step 3 (baseline fix); Step 4 (gate-decision follow-on); Step 9 (CLAUDE.md, conditional) | `test_validate_frontmatter.py` + manual diff-read |
| (Scope-mandated, not a numbered AC) Fix Security-Review-skipped-on-hotfix bug | Step 1 | `test_workflow_meta_conformance.py` (extended) |

## Anti-Drift Notes

- `tools.jsonl`'s `input_summary` field is a Python-dict-repr string, not JSON — Step 8 must use
  regex extraction (`re.search(r"'skill':\s*'([^']*)'", input_summary)`), never `json.loads` on
  that sub-field, per investigation.md's direct-inspection finding.
- Step 4 is the ticket where the genuinely unresolved asymmetry question lives (security's clean
  pass/fail verdict shape vs. api-design/debugging/performance's soft judgment shape) — do not let
  that child ticket's own Plan phase skip past this by assuming "convert all 3 to gates" is
  self-evidently correct just because `security`'s conversion worked well.
- Steps 5 and 6 must not collapse into a single ticket — investigation.md explicitly distinguishes
  disclosed-community (2 skills, already flagged with `source: community` frontmatter) from
  undisclosed-fingerprint (4 skills, same remediation shape internally but no existing disclosure)
  as different starting states, even though the destination (assess + possibly swap + disclose) is
  similar.
- Step 7's dangling-cross-reference cleanup is categorically different from Steps 5/6's
  community-paradigm-swap work — do not merge them; investigation.md classifies
  `frontend-design`/`doc-coauthoring`/`brainstorming` as "likely first-party (Anthropic) pattern,
  adapted," not community-sourced.
- Step 10 is deferred by design (P3, non-blocking) — this is a deliberate sequencing decision per
  the epic's own Out of Scope section, not an oversight; do not silently drop it from the child-
  ticket list even though it is not landing soon.

## Unresolved Questions

- **Step 4's core question (not decided here, by design):** should `api-design-principles`,
  `debugging-strategies`, and `python-performance-optimization` each be converted to a binding
  `implement-ticket.js` gate (mirroring `security`), given none of the 3 has `security`'s clean
  pass/fail verdict shape? Per the Planning Rule against unilaterally deciding open questions that
  change implementation approach, this is left entirely to Step 4's own investigation.md/plan.md —
  it may conclude "convert all 3," "convert none," or a per-skill split, and must justify whichever
  outcome against the asymmetry risk investigation.md's Risk #4 raises.

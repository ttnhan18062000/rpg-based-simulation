---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC
artifact_type: investigation
tags: [skills, workflows, process-improvement]
---

# Investigation — TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC

## Current Behavior

### Headline finding: the epic's own premise is significantly stale

The epic ticket cites 3 prior tickets (`SKILL-TRIGGER-COVERAGE`, `TAG-SKILL-SUGGEST`,
`SIX-SKILLS-INVESTIGATION`) as "what none of the three prior tickets resolved." Semantic search
(`search_docs`, mandatory Context Scan step 1) immediately surfaced **6 more done tickets the epic
never mentions**, all directly on-topic, all dated between the epic's cited tickets and today:

| Ticket | Date | What it already did |
|---|---|---|
| `TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION` | 07-05 | Already root-caused "why doesn't suggested_skills fire": confirmed it is computed at 3 sites and **purely advisory — logged, never consumed** by any later phase. Assessed 4 candidate tunings (auto-invoke: defer; security hard gate: build now; Parity-skip: build now; Test-skip: reject). |
| `TCK-20260705-WORKFLOW-SECURITY-GATE` | 07-05 | Built exactly the "build now" recommendation above: a mandatory `Security-Review` phase gate in `implement-ticket.js`, triggered by `tags.includes('security')` OR `suggested_skills.includes('/security-review')` — turning the `security` tag's suggestion from advisory into consumed/binding. |
| `TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK` | 07-08 | Added a pytest drift-check across the (then-)4 hand-duplicated mapping copies. |
| `TCK-20260708-RETRO-TAG-BREAKDOWN` | 07-08 | Added two new `generate_retro.py` sections: `## Tag Breakdown — Subsystem/Topic` and `## Tag Breakdown — Process/Skill-signal` — the latter cross-references `security`-tagged runs against `Security-Review` phase/`SECURITY_BLOCKED` hits. This is a **real, already-shipped agent-monitoring metric** adjacent to (but distinct from) the epic's Scope item 4. |
| `TCK-20260720-SKILL-MAPPING-DEDUP` | 07-20 | **Already resolved** the "4 independent hand-copies, no shared import mechanism" hazard the epic's Request Summary implicitly still assumes. The mapping now lives as `triggers_skill` data on `tag_registry.jsonl` rows, read live via `tools/tag_registry.py::get_skill_mapping()` / `python3 tools/tag_registry.py skill-mapping`. All 4 consumers (`ticket-scoper.md`, `ticket_tagging.md`, `implement-ticket.js`, `create-tickets.js`) now read this single source — confirmed by direct read of the current `.claude/agents/ticket-scoper.md:86-93`, which instructs running the live CLI command, not a hand-copied table. |
| `TCK-20260720-TAG-RELEVANCE-VERIFY` | 07-20 | Added `tag_relevance_flags` (Output item 6 in `ticket-scoper.md:94-100`) and a Finalize-time `check_tag_drift()` — advisory tag-quality checks, not skill-invocation checks, but relevant context for item 2 (whether other fields carry signal). |

**Implication for every scope item below:** the epic's Scope/Related-Tickets sections must be
corrected before any child ticket is filed, or child tickets will re-litigate/re-build things that
already exist. This is itself the single most important finding — flagged again in Risks.

### Item 1 — Root-cause the dual-mechanism non-firing

**Confirmed via `agent-monitoring/tools.jsonl` (all-time, 205 total `Skill` tool calls, `input_summary`
regex-extracted):** 14 distinct skill names ever invoked — `implement-ticket` 71, `graphify` 66,
`create-tickets` 26, `implement-epic` 11, `agent-monitoring-retro` 9, `simq-audit` 5, `dataviz` 3,
`brainstorming` 3, `claude-in-chrome` 3, `update-config` 2, `fewer-permission-prompts` 2, `run` 2,
`artifact-design` 1, `claude-api` 1. Zero for `api-design-principles`, `debugging-strategies`,
`python-performance-optimization` (matches epic's claim) — and zero for all 10 other project
`.claude/skills/*` entries too (`architecture`, `backend-testing`, `doc-coauthoring`, `frontend-design`,
`prompt-builder`, `python-testing-patterns`, `test-driven-development`) except `brainstorming`
(3) and `simq-audit` (5).

**Mechanism 2 (tag-based `suggested_skills`, `implement-ticket.js` Scope phase) — root cause is
CONFIRMED, and it is NOT the "silently-skipped hand-orchestration step" bug class the epic
hypothesizes:**
- `.claude/skills/implement-ticket/SKILL.md:34` explicitly documents `log(msg)` → "Output the message
  to the user." This is unlike the shadow-context-packet-probe bug class (a `bash()` block embedded
  only in prose, flagged at `SKILL.md:38` as observed to silently not execute) — the log line is
  correctly wired to reach the user/orchestrating agent's visible output. So mechanism 2's log line
  does surface.
- `WORKFLOW-TAG-TUNING-INVESTIGATION` (07-05) already found the real cause: the field is **advisory
  by design** — `TAG-SKILL-SUGGEST`'s own Out of Scope says "Auto-invoking a skill without a
  suggestion step... is out of scope." Candidate 1 (auto-invoke) was explicitly **deferred**, citing
  "no JS-callable skill-invocation primitive exists yet."
- **Real opportunity check (epic's own explicit ask):** grepped every `TCK-2026*.md` ticket dated
  `>= 20260705` for a frontmatter `tags:` line containing `api-design`, `debugging`, `performance`,
  or `security`. Found **20 tickets** carrying a mapped tag since the mechanism shipped (8
  `api-design`, 6 `debugging`, 1 `performance`, 6 `security` — full list kept in this session's scratch
  output, spot-checked below). This conclusively rules out "no opportunity" as the root cause for
  mechanism 2 — the suggestion had 20 real chances to be acted on and was acted on zero times.
- Two of those `api-design`-tagged tickets (`TCK-20260716-AGENTOPS-DASHBOARD-BACKEND`,
  `TCK-20260718-GLOSSARY-API`) directly confirm real applicable work: `Related Code Areas` includes
  `src/api/read_model_cache.py` and `src/api/agent_ops_dashboard/{models,ingest,main}.py`
  respectively — literal `src/api/` paths, the exact condition CLAUDE.md's row already names.
- **Conclusion for mechanism 2:** correctly wired, correctly surfaced, genuinely had opportunities —
  and still never converted to an invocation, because it is advisory-only by explicit design
  decision, not a wiring bug. The root cause is "advisory suggestions get ignored," which is a
  known, already-documented finding (`WORKFLOW-TAG-TUNING-INVESTIGATION`), not a new discovery this
  epic makes. The one place this pattern *was* converted from advisory to binding
  (`security` → mandatory `Security-Review` gate) is evidence for what actually works: see below.

**Mechanism 1 (CLAUDE.md file-path auto-invoke table, `SKILL-TRIGGER-COVERAGE`) — root cause is
genuinely still open and evidenced as a real gap, unlike mechanism 2:**
- CLAUDE.md's row for `src/api/` exists and is correctly worded (confirmed unedited since
  `SKILL-TRIGGER-COVERAGE`). Real, unambiguous `src/api/` edits occurred at least twice since
  2026-07-04 (see above) with zero `/api-design-principles` invocation.
- This is a standing self-directed instruction (not a single JS phase log line an orchestrator
  might miss) — every session is independently supposed to notice and comply. The evidence (302+
  `search_docs` calls, 66 `graphify` calls, vs. 0 for `api-design-principles`) suggests a
  distinction: **unconditional, every-task rules get followed reliably; conditional, situational
  auto-invoke rows (fires only if editing a specific path) do not**, even when correctly worded and
  present in CLAUDE.md. `search_docs`/`graphify` are invoked because the Context Scan rule fires
  at the start of literally every task, not because an agent notices a file-path match mid-session.
  This is a plausible, evidenced mechanism-level explanation, not just "the row exists but nobody
  reads it" — it is closer to "situational self-monitoring across a long session is unreliable,"
  a different, harder problem than a simple doc/code sync bug.

**A concretely-evidenced NEW gap this investigation found, in the SAME bug class the epic
hypothesizes (documented-but-silently-skipped hand-orchestration), that none of the 3 cited
tickets or today's 3 sibling tickets caught:**
- `agent-monitoring/events.jsonl` shows only **2** `Security-Review` phase events recorded, ever.
- Of the 6 `security`-tagged tickets since the gate shipped, `TCK-20260731-GATE-BYPASS-HARDENING`
  (tier `hotfix`) shows event sequence `Scope → Implement → Test → Verify → Finalize` — **no
  `Security-Review` phase at all**, despite `implement-ticket.js:1227-1279` placing the
  `Security-Review` gate structurally outside every `tier !== 'hotfix'` conditional (confirmed by
  grep — the gate's code block has no tier guard).
- **Likely root cause, found by reading `.claude/skills/implement-ticket/SKILL.md:70` directly:** the
  "Hotfix tier skips..." summary paragraph explicitly re-enumerates which phases "still run for
  hotfix" — "Document-Update, the doc-staleness gate, the post-Test cleanup checkpoint, Parity (with
  its gate), and the post-Finalize steps" — and **omits `Security-Review` from that list**, even
  though the file's own Pipeline section (step 11) correctly states "not tier-gated" two paragraphs
  earlier. An agent hand-orchestrating a hotfix ticket who anchors on the summary paragraph (a
  plausible reading path — it is the paragraph that directly answers "what still runs for hotfix")
  would skip a phase the same file's own step 11 says is unconditional. This is a genuine,
  newly-found instance of the exact SKILL.md self-inconsistency bug class `SKILL-JS-PHASE-SYNC` /
  `SKILL-DRIFT-DETECTION` fixed today — just in a location those tickets' scopes didn't cover
  (the hotfix-summary paragraph vs. the phase list itself).
- The other 4 post-gate security-tagged tickets show mixed results: `CODEX-LIVE-TRANSPORT` (standard
  tier) fired `Security-Review` correctly; `CODEX-PILOT-ORCHESTRATION` fired it correctly;
  `CODEX-PILOT-ENTRYPOINT` and `CODEX-POSTTOOL-HOOK-COMMAND` show incomplete/absent event traces
  (plausibly a different, unrelated monitoring-write gap, not re-investigated further here — flagged
  as an open question, not resolved).

### Item 2 — Ticket-metadata-driven triggering expansion

`.claude/agents/ticket-scoper.md`'s current Output section (`:80-100`, read directly) has **already
moved past** the 4-tag hand-copied table the epic describes:
- Item 5 (`:86-93`): computes `suggested_skills` by running `python3 tools/tag_registry.py
  skill-mapping` live and matching against its JSON keys — not a hand-copied table. Expanding the
  mapping today means adding a `triggers_skill` field to a new tag's registry row (via
  `tag_registry.py::add_tag(triggers_skill=...)`), not editing 4 files by hand. **This materially
  changes the epic's own cost/risk framing** — `TAG-SKILL-SUGGEST`'s "4 independent copies, no
  shared import mechanism" hazard, which the epic's Scope text still cites as a live constraint, was
  resolved on 2026-07-20.
- Item 6 (`:94-100`, `tag_relevance_flags`, shipped by `TAG-RELEVANCE-VERIFY`): a self-check that a
  tag plausibly fits a ticket's own title/scope — already gives `ticket-scoper` a mechanism for
  judging tag fit, orthogonal to (not the same as) skill-suggestion expansion, but relevant context
  for "does another ticket field carry signal" — it demonstrates the repo's established pattern for
  *advisory* self-checks (never a hard block) which any new triggering mechanism should match.
- `layer`/`type`/`tier` are **not** read for routing purposes anywhere in `ticket-scoper.md`,
  `create-tickets.js`, or `implement-ticket.js` — confirmed by the same investigation
  (`WORKFLOW-TAG-TUNING-INVESTIGATION`) the epic itself cites as prior work but doesn't fully credit:
  "no tag, type, priority, or Related Code Areas content changes phase execution anywhere today"
  except the `tier` short-circuit itself. No new evidence surfaced in this investigation to
  contradict that finding for `type`/`layer`. `tier` already IS the one field with real behavioral
  effect (hotfix short-circuit), and per Item 1's finding above, even that field's effect
  (Security-Review "not tier-gated") is currently violated in practice for at least one real ticket
  — an argument for hardening what already exists before adding a new signal dimension.
- Given the mapping is now cheap to extend (one registry row, not 4 file edits), and the security
  tag's hard-gate conversion is evidenced to work far better than advisory logging (2 real
  `Security-Review` fires with clean events, vs. 0 real invocations across every advisory-only tag),
  the balance of evidence favors: **the real lever is advisory→binding conversion for the mapped
  tags that don't yet have a gate (`api-design`, `debugging`, `performance`), not raising the count
  of mapped tags.** `SIX-SKILLS-INVESTIGATION`'s 6 "correctly redundant" verdicts are not
  re-litigated here (out of scope, confirmed no new evidence found that would change them —
  `tools.jsonl` still shows 0 invocations for `test-driven-development`/`python-testing-patterns`/
  `backend-testing`/`architecture`/`doc-coauthoring` and 3 for `brainstorming`, consistent with the
  fresher-still investigation).

### Item 3 — Popular/community skill sourcing audit

Two skills carry **explicit, machine-readable** `source: community` / `risk: unknown` /
`date_added: "2026-02-27"` frontmatter: `api-design-principles` and `architecture`. No other
`.claude/skills/*/SKILL.md` has this frontmatter shape (checked all 16 via direct grep). `architecture`
additionally contains a "Related Skills" table referencing `@[skills/database-design]`,
`@[skills/api-patterns]`, `@[skills/deployment-procedures]` — **none of which exist anywhere in this
repo's `.claude/skills/`** — a strong signal of unmodified, pasted-in community content, not
project-adapted.

Per-skill classification (read each `SKILL.md`'s opening + structure directly):

| Skill | Classification | Reasoning |
|---|---|---|
| `api-design-principles` | Community (disclosed) | `source: community` frontmatter; generic REST/GraphQL guidance, `resources/implementation-playbook.md` sub-file structure typical of a marketplace skill pack. |
| `architecture` | Community (disclosed) | `source: community` frontmatter; references 3 sibling skills that don't exist in this repo — unmistakably unadapted. |
| `backend-testing` | Strong community candidate (undisclosed) | `metadata.platforms: Claude, ChatGPT, Gemini` — explicitly cross-platform, not Claude-specific; generic Jest/Django/Spring Boot framework menu, zero project-specific content. |
| `python-performance-optimization` | Strong community candidate (undisclosed) | Identical structural fingerprint to `api-design-principles` ("Master X... comprehensive guide", "When to Use This Skill" bullet list, "Quick Start" code block) but missing the frontmatter tag — same source family, untagged. |
| `python-testing-patterns` | Strong community candidate (undisclosed) | Same fingerprint as above; generic pytest/fixtures/AAA-pattern content with zero reference to this repo's actual test layout (`tests/tools/`, `conftest.py` conventions). |
| `debugging-strategies` | Strong community candidate (undisclosed) | Same fingerprint; "Scientific Method"/"Rubber Duck Debugging" generic content, no reference to this repo's `world-debugger` agent or `docs/combat/observability_rulebook.md`. |
| `test-driven-development` | Moderate candidate | Terser, punchier tone ("Iron Law", Red-Green-Refactor dot diagram) than the "Master X" family above — plausibly a different, well-known community pack (the style matches widely-circulated strict-TDD skill templates), but not disclosed. Already scored "correctly redundant, deliberately diverging" by `SIX-SKILLS-INVESTIGATION" — content-quality swap would not change that usage verdict. |
| `frontend-design` | Likely first-party (Anthropic), not "popular OSS" | Has a `LICENSE.txt` reference and prose style ("avoids generic AI slop") matching Anthropic's own published frontend-design skill, distinct in kind from the "Master X" community-pack family — not a case of "swap for a popular alternative," since this already effectively is a maintained first-party skill. |
| `doc-coauthoring`, `brainstorming` | Likely first-party (Anthropic) pattern, adapted | References sibling first-party conventions (`spec-document-reviewer` subagent, `writing-plans` skill) not present as actual files in this repo — reads as copied from Anthropic's own example skill set rather than a third-party community pack. Different remediation shape than the "Master X" family: not "swap for popular," more "reconcile references to skills/agents this repo doesn't actually have" (see Anti-Drift Hazards). |
| `prompt-builder` | Community, out of scope | Explicitly VS Code/GitHub-Copilot-specific — already correctly excluded by `SKILL-TRIGGER-COVERAGE`; re-confirmed no new evidence changes this. |
| `simq-audit` | Clearly project-original | Wraps this repo's own `.claude/workflows/simq-audit.js`, `tools/simq_audit_gaps.py`, `grade_anchors.json` — no meaningful "popular equivalent" could exist; explicitly named by the epic itself as the canonical negative example. |
| `create-tickets`, `implement-ticket`, `implement-epic`, `agent-monitoring-retro` | Clearly project-original | All wrap this repo's own `.claude/workflows/*.js` / `tools/agent-monitoring/*.py` machinery — the entire ticket/monitoring pipeline is bespoke; there is no "popular ticket pipeline skill" this could be swapped for. |

**Summary for Plan:** 5 skills (`api-design-principles`, `architecture`, `backend-testing`,
`python-performance-optimization`, `python-testing-patterns`, `debugging-strategies` — 6, correcting
count) are the strongest, best-evidenced candidates for a "check against a popular/maintained
alternative" pass — notably these overlap heavily with the same skills already flagged as
zero-invocation gaps in Item 1, meaning a content-quality swap and a triggering fix could land
together for the same skill. `frontend-design`/`doc-coauthoring`/`brainstorming` are a different,
smaller-risk category (first-party-style content with some dangling cross-references, not "wrong
paradigm" community content). `test-driven-development` is ambiguous. The rest are correctly
project-original and this ticket's own out-of-scope framing (do not prune, do not swap
project-original content) should exclude them explicitly in any child ticket.

### Item 4 — Agent-monitoring usage tracking survey

Confirmed via grep across `tools/agent-monitoring/*.py` and `tools/*.py`: **no existing script or
`generate_retro.py` section filters on `tool == 'Skill'`** — zero hits for a literal `"Skill"` tool-name
comparison anywhere. What DOES exist (`TCK-20260708-RETRO-TAG-BREAKDOWN`, already shipped) is a
**different** metric: two `## Tag Breakdown` sections in `generate_retro.py` (`:876-900`) that group
runs by ticket *tag* (not by `Skill` tool invocation) and, for `Process/Skill-signal` tags, check
whether the run's events hit the tag's corresponding *gate/phase* (currently only meaningful for
`security` → `Security-Review`, since that is the only mapped tag with a real gate — the other 3
render `"N/A — no gate implemented"` by design, per `_TAG_GATE_PHASE`/`_TAG_GATE_FINAL_STATUS`
dicts in `generate_retro.py`). This is a genuinely useful, already-built metric, but it is *not* the
epic's Item-4 ask: it cannot answer "was `/api-design-principles` ever actually invoked as a Skill
tool call" for a tag with no gate — that requires reading `tools.jsonl`'s `tool == 'Skill'` records
and extracting the skill name from `input_summary` (a Python-dict-repr string, not JSON — confirmed
by direct inspection; needs a small regex, `re.search(r"'skill':\s*'([^']*)'", input_summary)`, not a
`json.loads` on that sub-field).

`tools/agent-monitoring/retrieval_baseline_metrics.py`'s exact pattern to follow (confirmed by direct
read, `:1-90`): a frozen `*_TOOL_NAMES`-style constant with a load-bearing comment explaining
precisely what it includes/excludes and why (`SEARCH_TOOL_NAMES`, `:36-43`); a `build_*_section()`
function returning a dict with a `derivation` string describing exactly how the number was computed
(never a fabricated/silent number, matching this session's own convention); per-run grouping via
`defaultdict(int)` keyed by `run_id`, with a documented `"unattributed"` bucket for `run_id=None`
records (since a `None` dict key breaks `json.dumps(sort_keys=True)`); imports composed from
`generate_retro.py`'s existing helpers rather than reimplementing JSONL loading. This module is a
one-off/periodic snapshot tool (its own docstring: "Distinct from generate_retro.py's own recurring
weekly RETRO-*.md cadence"), separate from `generate_retro.py`'s section-based recurring reports —
Plan should decide which shape (a new `generate_retro.py` section, following `_build_tag_breakdown`'s
pattern, vs. a new one-off script following `retrieval_baseline_metrics.py`'s pattern) fits a
per-skill-name usage count best; the epic's own Scope text names both as acceptable options.

**Output location constraint, confirmed correct:** `generate_retro.py`'s `RETRO_DIR =
Path("agent-monitoring/retro")` (referenced, not re-quoted verbatim here) and
`retrieval_baseline_metrics.py`'s own docstring ("never writes into agent-monitoring/ itself" — it
prints JSON to stdout) both confirm the two acceptable shapes the epic names. `docs/`, `data/`, and
`config/` are confirmed unrelated: `docs/` has zero generated-report precedent (it is
authored-documentation only per every sibling ticket's Out of Scope), `data/` is
simulation-content/calibration/world data (`data/runs/`, `data/calibration/`), and `config/` is
observability/simulation_quality settings — none of the 6 newly-found related tickets touched any of
those 3 directories for monitoring output.

### Item 5 — Related agents/workflows

Given Item 1's actual root causes:
- **Mechanism 2 (advisory tag suggestion):** no wiring gap to fix — it works as designed. Any child
  ticket here is a *design* decision (convert more tags to hard gates, following
  `WORKFLOW-SECURITY-GATE`'s exact pattern in `.claude/workflows/implement-ticket.js`), not a bug fix.
  Touches: `.claude/workflows/implement-ticket.js` (new conditional gate blocks, mirroring
  `:1227-1279`), possibly new `.claude/agents/*-reviewer.md` files (mirroring
  `.claude/agents/security-reviewer.md`), `docs/ai/workflows.md` / `docs/ai/system_overview.md` /
  `docs/ai/ticket-lifecycle.md` (mirroring `WORKFLOW-SECURITY-GATE`'s doc updates).
- **Mechanism 1 (CLAUDE.md file-path row):** genuinely unresolved; no single file to "sync" — the
  evidenced pattern (situational instructions are unreliable regardless of correct wording) suggests
  the more promising fix is converting `api-design-principles`/`debugging-strategies`/
  `python-performance-optimization` into gate-checks or Item-1's tag-based binding mechanism (which
  *can* be enforced by the orchestrating workflow) rather than relying on a CLAUDE.md table row a
  session must self-notice mid-task.
- **The newly-found `Security-Review`-skipped-on-hotfix gap:** `.claude/skills/implement-ticket/SKILL.md`
  line 70's "Hotfix tier skips..." summary paragraph — add `Security-Review` explicitly to the "still
  run for hotfix" enumeration, or restructure the paragraph so step 11's "not tier-gated" note is not
  contradicted by the summary's omission. This is a small, well-scoped fix in the same file/bug class
  `SKILL-JS-PHASE-SYNC` already touched today, just a different paragraph. Also worth a
  `tools/gate_checks/workflow_meta_conformance.py`-style static check (that module already exists and
  runs as `tests/tools/test_workflow_meta_conformance.py`, per `.claude/skills/implement-ticket/SKILL.md:68`)
  extended to verify a `security`-tagged/`SECURITY_BLOCKED`-eligible ticket's events actually contain a
  `Security-Review` phase — a natural extension of the drift-detection pattern already established
  today, not a new pattern.

## Mechanics / Engine Constraints

None. This epic and every candidate child ticket are agent-orchestration/tooling work
(`.claude/`, `.claude/workflows/*.js`, `tools/agent-monitoring/`, `docs/ai/`) — no `src/`, simulation
state, or authoritative mutation path is touched. No Mechanics Bible chapter or Engine Contract
constrains this work, consistent with every one of the 9 prior tickets read for this investigation.

## Docs Requiring Update

- `docs/ai/skills.md`: epic's own Related Docs names this file; its "Tag-Based Skill Suggestions"
  section (added by `TAG-DOCS-CROSSREF`) still describes the mechanism as advisory-only with no
  mention of the `security` tag's hard-gate exception (`WORKFLOW-SECURITY-GATE`) or the live
  `tools/tag_registry.py skill-mapping` single-source mechanism (`SKILL-MAPPING-DEDUP`) — both
  postdate this doc's last edit and are not reflected.
- `docs/ai/agents.md`: `ticket-scoper` section should be checked against the now-3-item Output list
  (`suggested_skills`, `tag_relevance_flags`) for accuracy once a child ticket decides whether to add
  a 4th output field for any new triggering mechanism.
- `.claude/skills/implement-ticket/SKILL.md`: the hotfix-summary paragraph (line 70) inconsistency
  found in Item 1 needs a direct fix regardless of which child ticket carries it — flagging here so it
  is not lost if the epic's breakdown doesn't otherwise capture it verbatim.
- CLAUDE.md ("Proactive Tool Use" table): only if a child ticket decides mechanism-1's fix is a new
  row (e.g. reinstating `frontend-design` given Item 3's finding of real, repeated frontend work since
  07-17) — not a certain outcome, a candidate.

## Parity Ledger Overlap

None. Grepped all 7 `docs/parity_ledger/*.yaml` files for `suggested_skills`/`skill catalog`/skill-
suggestion vocabulary — zero hits beyond unrelated substring collisions (same conclusion every one of
the 9 prior/sibling tickets read for this investigation independently reached). This is pure
agent-tooling work; no `P0` entry is implicated.

## Prior Work

Full list (see Current Behavior's table for the 6 the epic itself omits, plus the 3 it cites):
`TCK-20260704-SKILL-TRIGGER-COVERAGE`, `TCK-20260705-TAG-SKILL-SUGGEST` (+ its `plan.md`/
`investigation.md`, read in full), `TCK-20260705-SIX-SKILLS-INVESTIGATION`,
`TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION`, `TCK-20260705-WORKFLOW-SECURITY-GATE`,
`TCK-20260705-TAG-DOCS-CROSSREF`, `TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK`,
`TCK-20260708-RETRO-TAG-BREAKDOWN`, `TCK-20260720-SKILL-MAPPING-DEDUP`,
`TCK-20260720-TAG-RELEVANCE-VERIFY`. `docs/REGISTRY.yaml` exists and was available but not needed as
the primary index here — `search_docs` (mandatory Context Scan step 1) surfaced all 6 missing
tickets directly on the first two queries, which is itself worth noting: the Context Scan rule
worked exactly as intended and is the reason this staleness was caught before any child ticket was
filed.

## Risks and Open Questions

1. **Blocking, must be resolved before child tickets are filed:** the epic's Request Summary,
   Scope, and Related Tickets sections describe a current state (4 hand-copied mapping tables, purely
   advisory suggestion with no example of it being converted to a gate, no agent-monitoring tag
   breakdown) that is **factually out of date** as of 2026-07-20/07-08 respectively. Any child ticket
   that inherits this framing verbatim will mis-scope real work as already-done work, or propose
   re-building `SKILL-MAPPING-DEDUP`'s dedup or `RETRO-TAG-BREAKDOWN`'s tag-breakdown section a second
   time. Recommend: the epic ticket itself (or Plan, before child-ticket creation) should be updated
   to reference these 6 tickets and correct the stale claims, not just this investigation.md.
2. **Open, not resolved here:** whether `CODEX-PILOT-ENTRYPOINT`'s truncated event trace and
   `CODEX-POSTTOOL-HOOK-COMMAND`'s complete absence of events (both DONE, both `security`-tagged)
   reflect a monitoring-write gap unrelated to Security-Review specifically, or the same
   hand-orchestration-skip pattern found for `GATE-BYPASS-HARDENING`. Flagged, not diagnosed — would
   need its own targeted investigation (reading those 2 tickets' full session history, not available
   from `tools.jsonl`/`events.jsonl` alone) before a child ticket claims a specific root cause for
   them.
3. **Open, judgment call for Plan:** whether `frontend-design`'s renewed real-work evidence (Item 3)
   is strong enough to reopen `SKILL-TRIGGER-COVERAGE`'s exclusion, given the 4 tickets found are
   maintenance/bugfix-shaped (CSS cascade fix, pagination, dropdown fix, tooltip wiring) rather than
   "build a new distinctive interface" — `frontend-design`'s own trigger condition may still not
   literally match maintenance work on an existing dashboard. Recommend Plan decide explicitly rather
   than silently carry forward the stale "zero evidence" framing either way.
4. **Open:** whether converting `api-design`/`debugging`/`performance` from advisory suggestions to
   hard gates (mirroring `security`'s pattern) is actually desirable — unlike `security`, none of
   these 3 have an obvious pass/fail verdict shape (a security review has a clear
   APPROVED/NEEDS_CHANGES/BLOCKED outcome; "did you follow API design principles" or "did you profile
   performance" are much softer judgments). This is a real design risk if a child ticket proposes a
   blanket "convert all 4 to gates" without addressing this asymmetry — flagged for Plan, not decided
   here.

## Anti-Drift Hazards

- Do not let a child ticket re-build `tools/tag_registry.py::get_skill_mapping()` /
  the `skill-mapping` CLI subcommand — it already exists (`SKILL-MAPPING-DEDUP`, 2026-07-20). Any
  mapping-expansion child ticket should add a `triggers_skill` field to a tag's registry row via
  `add_tag()`, not touch 4 files by hand.
- Do not let a child ticket re-build the `## Tag Breakdown — Process/Skill-signal` section in
  `generate_retro.py` — it already exists (`RETRO-TAG-BREAKDOWN`, 2026-07-08). A new Item-4 metric
  must be additive (raw `Skill`-tool-invocation counts by name) and clearly distinguished from the
  existing tag/gate-hit breakdown in its own section heading and `derivation` string.
  `tools.jsonl`'s `input_summary` field is a Python-dict-repr string, not JSON — a naive `json.loads`
  on it will crash; use a regex extraction as this investigation did, or document an equivalent safe
  parse.
- Do not fold the `implement-ticket/SKILL.md:70` hotfix-summary-paragraph fix into a broader,
  unrelated rewrite of that file — it is a precise, one-paragraph correction (same discipline
  `SKILL-JS-PHASE-SYNC` applied today).
- Do not treat this investigation's Item 3 skill classifications as a decision to swap any skill's
  content — Scope explicitly reserves the actual popular-alternative research and swap decision for
  Plan/Implement of a future child ticket, per the epic's own instruction.
- Do not re-litigate `SIX-SKILLS-INVESTIGATION`'s 6 verdicts — this investigation found no new
  evidence that would change them (usage counts re-confirmed at the same 0/0/0/0/0/3 split).

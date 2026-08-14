---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS
artifact_type: investigation
tags: [dashboard, observability, workflows]
---

# Investigation — TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS

## Current Behavior

**Canonical phase list** — `tools/agent-monitoring/vocabulary.py:20-31` (`WORKFLOW_PHASES`), live-verified
by direct execution against the module itself. Deduplicated union across all 4 workflows is
**21 distinct phase strings**:

```
Architecture-Verify, Classify Drift, Comprehend, Finalize, Implement, Investigate, Link, Parity,
Parity Check, Plan, Recalibrate, Report, Review, Scope, Security-Review, Structure, Sync Docs,
Test, Update Anchors, Verify, Write
```

Per-workflow breakdown:
- `implement-ticket` (11): Scope, Investigate, Plan, Review, Implement, Architecture-Verify, Test,
  Parity, Security-Review, Verify, Finalize
- `create-tickets` (5): Comprehend, Investigate, Structure, Write, Link
- `implement-epic` (1): Implement
- `simq-audit` (7): Recalibrate, Classify Drift, Update Anchors, Sync Docs, Parity Check, Verify,
  Report

Three strings recur across workflows and must resolve to exactly **one** glossary entry each
(confirmed via direct count — `Investigate`×2, `Verify`×2, `Implement`×2): `Investigate`
(implement-ticket + create-tickets — same investigation-and-write-artifacts meaning in both),
`Verify` (implement-ticket's DoD check + simq-audit's regression/anchor-coverage check — both are
"confirm the work is actually complete and correct" checks, different subject matter, compatible
generalization), `Implement` (implement-ticket's own phase + implement-epic's single per-child-ticket
delegation phase — implement-epic's `Implement` phase literally *is* one call to the
`implement-ticket` workflow per child, so the same word is doing the same job at a different
granularity, not a different meaning). `Parity` (implement-ticket) and `Parity Check` (simq-audit)
are **not** the same string — verified distinct literals, register as two separate terms, not one.

**`Review`/`Architecture Review` naming mismatch, verified directly** — `docs/ai/ticket-lifecycle.md:210`
has section heading `### Architecture Review`, but the doc's own body text at line 221 says "The
workflow resumes from the Review phase," and `vocabulary.py:22`'s literal set member is `"Review"`
(not `"Architecture Review"`). The doc's heading is a more-descriptive display label; the actual
event/vocabulary value everywhere else (including `dashboard-frontend`'s Phase Status Distribution
table, which renders `agent_status_distribution`/`phase_status_distribution` keys straight from
`agent-monitoring/events.jsonl`'s literal `phase` field) is `Review`. The registered glossary term
must be `Review` — confirmed, not assumed.

**`tools/glossary_registry.py`** (`tools/glossary_registry.py:49-57`) — `GLOSSARY_CATEGORIES` is
currently exactly `{"ticket-status", "run-status", "reason-code", "event-status", "tier",
"priority", "type"}` (7 entries, live-counted against `docs/guidelines/glossary_registry.jsonl`:
35 lines, category counts `{'ticket-status': 5, 'tier': 3, 'priority': 4, 'type': 5, 'run-status':
11, 'reason-code': 3, 'event-status': 4}`). `add_term(term, category, description, root=None)`
(`tools/glossary_registry.py:108-144`) raises `ValueError` if `category` isn't in
`GLOSSARY_CATEGORIES`, if `description` is blank, or if `term` is already registered — append-only,
case-sensitive, no canonical-form check (module docstring explicitly rejects lowercase-hyphenation
normalization for glossary terms, since they're existing fixed strings this repo's code already
emits verbatim, not freely-chosen labels — directly relevant here since phase strings like
`Architecture-Verify` and `Classify Drift` must be registered byte-for-byte as `vocabulary.py`
emits them). CLI: `python3 tools/glossary_registry.py add <term> --category <category>
--description "..."`.

**Architectural fork point, confirmed by reading `DashboardCache.get_glossary()` in full
(`src/api/agent_ops_dashboard/ingest.py:833-882`) — this is the one judgment call this ticket's own
Scope section gets slightly imprecise about, worth flagging explicitly for Plan:**

`get_glossary()` currently merges **three** sources, and only the first is `glossary_registry.py`'s
own registry:
1. `load_glossary_registry()` → `docs/guidelines/glossary_registry.jsonl` (the 7-category registry,
   `add_term()`-populated, content freshly authored at registration time).
2. `layer_registry.load_registry()` → `docs/guidelines/layer_registry.jsonl`, re-exposed under a
   **hardcoded `category="layer"` string in `ingest.py:870`** — `"layer"` is *not* and has never been
   a member of `GLOSSARY_CATEGORIES`; it is a literal string assigned directly at merge time.
3. `_load_agent_role_descriptions()` → `.claude/agents/*.md` frontmatter, re-exposed under a
   **hardcoded `category="agent"` string in `ingest.py:879`** — same pattern, also never added to
   `GLOSSARY_CATEGORIES`.

Both existing precedents (Layer, Agent) share one property this ticket's target domain does *not*
have: an **existing field, already authored, living in another file**, that the merge purely
extracts (layer's `note`, agent's frontmatter `description:`). This ticket's own Scope section
states plainly that no such existing text exists for phases anywhere in the repo — every phase
description must be freshly composed prose, distilled from `docs/ai/ticket-lifecycle.md` and
`.claude/skills/simq-audit/SKILL.md` (and `.claude/skills/create-tickets/SKILL.md` for
Comprehend/Structure/Write/Link). Freshly-authored, registry-owned description text for a small,
fixed enum-like domain is *exactly* what `glossary_registry.py`'s own 7-category registry already
exists for (every one of its current 35 entries is also freshly-authored prose for a fixed enum
value, not extracted from anywhere else) — so the ticket's literal instruction ("extend
`GLOSSARY_CATEGORIES` with a `phase` category," i.e. go through `add_term()` into
`glossary_registry.jsonl`) is the pattern-consistent choice, not a fourth `ingest.py`-hardcoded
merge source shaped like Layer/Agent. **This reasoning should be treated as confirmed, not an open
question** — flagging it here because the ticket's own "outside the original two-category scope"
phrasing could be misread as "add a fourth merge source" when the actual precedent match is
"populate the registry itself, same as the original 7 categories."

**Frontend wiring, confirmed by direct read of `dashboard-frontend/src/views/StatsView.tsx`:**
- Phase Status Distribution table (`phaseStatusRows()`, `StatsView.tsx:78-90`; table markup
  `StatsView.tsx:253-302`): the `ok`/`failed`/`blocked`/`skipped` `<th>` headers are already wrapped
  in `<GlossaryTooltip term="ok" glossary={glossary}>` etc. (`StatsView.tsx:260-279`). The `row.phase`
  `<td>` cell (`StatsView.tsx:285`) is plain `{row.phase}` — no `GlossaryTooltip`, confirmed gap.
- Top Agents table's `Agent` column cell (`StatsView.tsx:238-240`) is the direct precedent pattern
  to mirror: `<GlossaryTooltip term={row.agent} glossary={glossary}>{row.agent}</GlossaryTooltip>`
  inside a plain `<td>` — added by `TCK-20260719-AGENT-ROLE-GLOSSARY`. Phase wiring is the
  byte-identical shape: `<GlossaryTooltip term={row.phase} glossary={glossary}>{row.phase}</GlossaryTooltip>`.

`GlossaryTooltip` itself (`dashboard-frontend/src/components/GlossaryTooltip.tsx:22-50`) needs no
changes — it already looks up `glossary[term]` generically and degrades gracefully (renders
`children` unwrapped) when there's no matching entry, regardless of what `category` the entry
carries.

**Real, non-speculative analogous gap found elsewhere in the dashboard** (per the ticket's Out-of-
Scope instruction to check but not speculatively extend): `dashboard-frontend/src/views/ReplayTimelineView.tsx`
also renders `phase` as plain text, in **two** places — the phase-timeline button strip
(`entry.phase ?? '—'`, line 99) and the detail-area header (`entry.phase ?? '—'`, line 108). Line
108 additionally renders `entry.agent ?? '—'` plainly, immediately next to a **already-wired**
`<GlossaryTooltip term={entry.status} ...>` for `entry.status` on the same line (line 109-111) —
i.e. this file already has the `GlossaryTooltip`/`glossary` plumbing in scope and already uses it
for one field on that exact line, but not for `phase` or `agent`. This is a real, concrete,
already-half-wired gap, not a speculative one — Plan should decide whether it's in this ticket's
scope (the ticket's Out of Scope section explicitly reserves this decision for
Investigate/Plan: "extend elsewhere only if a real, analogous gap is found, not speculatively").
Line 99's `phase` is inside a `<button>` (`Tooltip.Trigger asChild` requires a single child element —
wrapping a `<button>`'s inner text fragment needs care, unlike the `<td>` cell case in StatsView).

## Mechanics / Engine Constraints

None. This is dashboard/observability tooling over `tickets/**` and `agent-monitoring/*.jsonl` —
no `docs/mechanics/` or `docs/engine/` chapter governs it, consistent with every prior
glossary-chain ticket's own investigation (`TCK-20260719-AGENT-ROLE-GLOSSARY`'s investigation.md
states the same finding for the Agent merge).

## Parity Ledger Overlap

None. Searched all of `docs/parity_ledger/*.yaml` for `glossary`/`phase.*tooltip`/`dashboard` —
the only hits are `infrastructure.yaml`'s existing Agent Ops Dashboard backend entries (covering
`GET /api/tickets`/`/api/runs`/`/api/runs/{run_id}` and `DashboardCache`/model shapes generally),
none of which reference the glossary endpoint's category set or phase-specific content. No P0
entries touch this scope. No parity ledger entry needs a `status`/`v2_evidence` update — this is
consistent with `TCK-20260719-AGENT-ROLE-GLOSSARY` (its own Parity phase made no ledger edit for
the same reason: dashboard tooling, not a simulation-law behavior change).

## Prior Work

- **`TCK-20260719-AGENT-ROLE-GLOSSARY`** (`stored_artifacts/TCK-20260719-AGENT-ROLE-GLOSSARY/`) —
  direct precedent this ticket mirrors. Added the third (`agent`) merge source to `get_glossary()`,
  wired `StatsView.tsx`'s Top Agents `Agent` column cell in `GlossaryTooltip`, extended
  `docs/observability/agent_ops_dashboard_contract.md`'s existing `get_glossary()` paragraph in
  place. Its plan.md's Anti-Drift Notes section documents a genuine `useGlossary()` module-level
  cache bug found and fixed along the way (`_resetGlossaryCacheForTests()` / `StatsView.test.tsx`
  `afterEach` wiring) — that fix is already landed and does not need repeating, but any new
  frontend test file that calls `useGlossary()` more than once with different mocked glossary
  content must call `_resetGlossaryCacheForTests()` in `afterEach`, or it will silently reuse a
  prior test's resolved glossary value.
- **`TCK-20260718-GLOSSARY-REGISTRY`** — built `tools/glossary_registry.py` and seeded the initial
  35-term/7-category registry.
- **`TCK-20260718-GLOSSARY-API`** — built `GET /api/glossary` / `DashboardCache.get_glossary()` /
  `GlossaryEntry`/`GlossaryResponse` models, merging registry + layer (2 sources at that point).
- **`TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND`** — built `GlossaryTooltip`/`GlossaryHintIcon`
  components and `useGlossary()` fetch-once hook; wired the original chart/table glossary usages.
- **`TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE`** — added the Phase Status Distribution table
  (`phaseStatusRows()`, `StatsView.tsx:78-90`) this ticket wires `row.phase` into. Confirmed its
  `ok`/`failed`/`blocked`/`skipped` headers already use `GlossaryTooltip`; `row.phase` was left
  unwired, which is the exact gap this ticket exists to close.
- **`TCK-20260719-PHASE-AGENT-CASE-FOLD`** — established `vocabulary.py`'s phase-string
  canonicalization (casing) this ticket's dedup logic reuses as-is; not re-investigated further
  since this ticket makes no change to `vocabulary.py` itself (explicitly Out of Scope).
- `docs/plans/archive/agent_ops_dashboard/proposal_agent_glossary.md` — the archived proposal doc
  behind `TCK-20260719-AGENT-ROLE-GLOSSARY`; its "Architectural constraints (carry forward from
  yesterday's glossary epic)" section is the same lineage of reasoning this investigation's
  "Architectural fork point" section above extends one step further for the Phase domain.

## Risks and Open Questions

- **Coverage scope (the ticket's own flagged open question) — recommend resolving as: cover all 21
  phases in one pass.** The ticket's `## Assumptions / Open Questions` section already recommends
  this, citing the Agent merge's own precedent (covered all 13 real role files in one pass rather
  than staging it). Marginal cost per phase is low once the `phase` category + wiring exist, and
  splitting `implement-ticket`'s 11 phases from the other 10 would leave `simq-audit`,
  `create-tickets`, and `implement-epic` phases silently unwired in the same
  `WORKFLOW_PHASES`-sourced dedup set the AC's "term count grows by the real deduplicated phase
  count" language implies covering fully. Not blocking — Plan should confirm this in its own
  Acceptance Criteria Map, but there is no genuine ambiguity in the evidence gathered here.
- **`Implement`/`Investigate`/`Verify` cross-workflow description wording** — each description must
  read correctly for both contexts it appears in (e.g. `Verify`'s description must generalize
  across implement-ticket's 13-condition DoD check and simq-audit's regression/anchor-coverage
  check). This is a content-authorship judgment call for whoever writes the final one-sentence text
  (Plan or Implement, per this ticket's own Scope section) — flagging so the sentence isn't drafted
  narrowly against only one workflow's meaning and then found wrong for the other at review time.
- **ReplayTimelineView.tsx's `phase`/`agent` gap** (see Current Behavior above) — a real,
  non-speculative analogous gap exists. This investigation surfaces it; whether it's in this
  ticket's scope or deferred to a follow-up ticket is a Plan-level decision the ticket's own Out of
  Scope section explicitly reserves, not decided here.
- **No functional risk identified for the `GLOSSARY_CATEGORIES` extension itself** — `add_term()`'s
  validation is purely a `category in GLOSSARY_CATEGORIES` membership check; adding `"phase"` to the
  set doesn't perturb the other 7 categories' existing entries. The load-bearing risk is entirely in
  the **hardcoded exact-set assertion test** flagged below (Anti-Drift Hazards).

## Anti-Drift Hazards

- **`tests/tools/test_glossary_registry.py::test_glossary_categories_is_the_expected_fixed_set`
  (lines 163-172) hardcodes the exact current 7-element `GLOSSARY_CATEGORIES` set with a bare `==`
  comparison.** Adding `"phase"` to `GLOSSARY_CATEGORIES` will make this test fail as written — it
  is not an incidental regression to avoid, it is an **expected, required update**: this test must
  be updated to include `"phase"` in the same commit that extends `GLOSSARY_CATEGORIES`, or the
  Test phase will report a false regression. Flagging explicitly so Plan schedules it as a required
  file touch, not a surprise test failure.
- **Case-sensitive, byte-exact term registration.** `glossary_registry.py` has no canonical-form
  normalization (by design). Every phase term must be registered with the exact casing/spacing
  `vocabulary.py` emits — `"Architecture-Verify"` (hyphenated), `"Classify Drift"` (space,
  title-case both words), `"Sync Docs"`, `"Parity Check"`, `"Update Anchors"` — a typo here (e.g.
  `"architecture-verify"` or `"Architecture Verify"`) registers a dead term that never matches any
  real `phase_status_distribution` key and silently never shows a tooltip, with no test catching it
  unless a test asserts the literal `vocabulary.py` strings round-trip.
- **Do not touch `vocabulary.py`'s `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` sets** — explicitly Out of
  Scope on the ticket; this ticket only reads that module, never edits it.
- **Do not duplicate the "same-first-registered-wins" shadow-guard pattern incorrectly.** Because
  `phase` (per the "Architectural fork point" finding above) is going into `glossary_registry.py`'s
  own registry via `add_term()`, not a fourth `ingest.py` merge loop, there is **no `if term in
  terms: continue` shadow-guard to add** — `load_glossary_registry()` already raises `ValueError` on
  any duplicate term across the whole `glossary_registry.jsonl` file (`load_registry()`,
  `tools/glossary_registry.py:75-100`), which already protects against a phase term colliding with
  an existing ticket-status/tier/priority/type/run-status/reason-code/event-status term. Live-check
  before registering: none of the 21 phase strings match any of the 35 existing registry terms or
  19 layer names or 13 agent names (informal scan — no `Scope`/`Plan`/`Test`/`Review`/`Verify`/
  `Finalize`/`Implement` collision found against the existing registry's `run-status`/`event-status`
  values like `DONE`/`ok`/`failed`/`blocked`/`skipped`/`hotfix`/`standard`/`epic`).
- **`docs/observability/agent_ops_dashboard_contract.md`'s `get_glossary()` paragraph
  (lines ~100-124) must be extended in place**, following the exact convention the Layer and Agent
  additions already used there ("extend the existing paragraph," not a new section) — and its
  term-count sentence ("35 glossary terms, 19 layer names, 13 agent names ... 67 total") needs
  updating to include the new phase count once the real number is known post-implementation.
- **Do not write new descriptions for `Investigate`/`Verify`/`Implement` twice** (once per workflow
  each appears in) — one glossary entry per literal string, matching this registry's own documented
  precedent for the same class of ambiguity (`DONE` meaning both ticket-status and run-status,
  documented in `glossary_registry.py`'s own module docstring).

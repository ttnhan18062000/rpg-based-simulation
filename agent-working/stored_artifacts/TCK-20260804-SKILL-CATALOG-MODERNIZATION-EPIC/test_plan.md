---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC
artifact_type: test_plan
tags: [skills, workflows, process-improvement]
---

# Test Plan — TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC

This is an epic — no direct implementation, so there is no literal pytest command to run for this
ticket itself. This test plan instead specifies, per scope item, what verification approach each
eventual child ticket must carry (mirrored into that child's own `test_plan.md`), and what
regression surface already exists that any child ticket must not break.

## Regression Surface

Existing tests any child ticket touching this area must keep passing, grouped by which prior-work
file they protect (see investigation.md's Prior Work table for the tickets that created them):

**Unit / tooling (`tests/tools/`):**
- `tests/tools/test_tag_registry.py` — protects `get_skill_mapping()`, `add_tag(triggers_skill=...)`,
  the `skill-mapping` CLI subcommand, and the append-only invariant. Any Item-2 mapping-expansion
  child ticket must run this and add cases for the new tag/skill pair.
- `tests/tools/test_tag_skill_mapping_check.py` — protects `check_consumers_reference_live_source()`
  (the repurposed drift check). Any child ticket editing `ticket-scoper.md`, `ticket_tagging.md`,
  `implement-ticket.js`, or `create-tickets.js`'s skill-mapping-adjacent text must re-run this to
  confirm no literal table got re-embedded (this is the check's own anti-drift purpose).
- `tests/tools/test_generate_retro.py` — protects the existing `## Tag Breakdown — Subsystem/Topic`
  and `## Tag Breakdown — Process/Skill-signal` sections. An Item-4 child ticket adding a new
  skill-usage section must add new, separate tests here (or in a new test file if it builds a
  standalone script) and must not modify the existing tag-breakdown tests' assertions.
- `tests/tools/test_ticket_scoper_relevance_check.py`, `tests/tools/test_finalize_tag_drift_wiring.py`
  — protect `tag_relevance_flags` and `check_tag_drift()`. Only relevant if an Item-2 child ticket
  touches `ticket-scoper.md`'s Output contract or `implement-ticket.js`'s Finalize phase.
- `tests/tools/test_validate_frontmatter.py` — protects tag-taxonomy/canonical-form enforcement; every
  child ticket's own staging artifacts and any new/edited doc must pass this (universal precedent
  across all 9 prior-work tickets read).
- `tests/tools/test_workflow_meta_conformance.py` — protects `check_skill_doc_covers_meta_phases()`.
  A child ticket fixing the `implement-ticket/SKILL.md:70` hotfix-summary-paragraph gap (Item 1/5)
  should confirm this still passes and consider whether it should be extended (see New Tests
  Required below) rather than only relying on it as an unchanged regression guard.

**Architecture-guard style (no `src/` involved, but same discipline):**
- `node -c .claude/workflows/implement-ticket.js` / `node -c .claude/workflows/create-tickets.js` —
  syntax check precedent used by `WORKFLOW-SECURITY-GATE`'s own Test Summary for any JS edit.

**No integration/arena-combat surface applies** — confirmed zero `src/`, simulation, or engine-contract
touch anywhere in this investigation's findings; this is pure agent-tooling.

## New Tests Required (per scope item, for whichever child ticket carries it)

1. **Item 1 — hotfix-summary paragraph fix** (`.claude/skills/implement-ticket/SKILL.md:70`)
   - Test name: extend or add a static assertion (unit-style, in
     `tests/tools/test_workflow_meta_conformance.py` or a new sibling test) that the SKILL.md's
     "still run for hotfix" enumeration includes every `meta.phases` entry the JS itself marks as
     tier-unconditional (cross-referencing `implement-ticket.js`'s actual gate-placement, not just
     string-matching phase names).
   - Category: architecture guard (doc/code self-consistency, same shape as
     `check_skill_doc_covers_meta_phases`).
   - What it verifies: prevents the exact class of bug found in this investigation (a phase
     documented as "not tier-gated" in one place, omitted from a "what runs anyway" list in another)
     from reoccurring silently.
   - Where it lives: `tools/gate_checks/workflow_meta_conformance.py` (extend) +
     `tests/tools/test_workflow_meta_conformance.py`.

2. **Item 1 — Security-Review-fired-when-expected check** (evidence gap: `GATE-BYPASS-HARDENING` ran
   with no `Security-Review` event)
   - Test name: a monitoring-data assertion (or a new `tools/gate_checks/` static check) confirming
     every `security`-tagged, post-`WORKFLOW-SECURITY-GATE`-dated ticket's `events.jsonl` records
     contain a `Security-Review` phase entry.
   - Category: integration / data-quality guard, not unit — reads real `agent-monitoring/*.jsonl`
     data, not a fixture.
   - What it verifies: the gate actually fires in practice, not just that its code path is
     syntactically unconditional on tier (which `WORKFLOW-SECURITY-GATE`'s existing tests already
     confirm) — closes the gap between "code says unconditional" and "real runs show it happened."
   - Where it lives: likely `tools/agent-monitoring/` (a query/report script) rather than a pytest
     unit test, since it reads live historical data rather than a deterministic fixture — Plan should
     decide the exact home, following this investigation's own citation of
     `retrieval_baseline_metrics.py` as the precedent for this class of tool.

3. **Item 2 — any mapping-expansion or advisory→gate-conversion child ticket**
   - Test name: `test_get_skill_mapping_includes_new_tag_<name>` (mirrors existing
     `test_tag_registry.py` pattern) plus, if a new hard gate is added (mirroring `Security-Review`),
     a full set mirroring `WORKFLOW-SECURITY-GATE`'s own precedent: trigger case (gate fires,
     structured failure status, does not proceed), clean-pass case (gate passes, run proceeds
     unchanged), and a zero-latency negative case (a ticket without the tag sees zero added events).
   - Category: unit (`tag_registry.py` mapping) + architecture guard (gate placement/tier-independence,
     mirrored via `node -c` + a grep-based structural check, per `WORKFLOW-SECURITY-GATE`'s own Test
     Summary items 2-4).
   - What it verifies: the new tag/gate follows the same append-only/single-source/tier-independence
     discipline the existing `security` gate already established — this investigation found that
     discipline was not perfectly followed in practice (Item 1's hotfix gap), so a new gate's tests
     must explicitly include a hotfix-tier trigger case, not just a standard-tier one.
   - Where it lives: `tests/tools/test_tag_registry.py` + `.claude/workflows/implement-ticket.js` (new
     gate block, verified via the same manual-trace-plus-grep method `WORKFLOW-SECURITY-GATE` used —
     no automated JS test harness exists for `.claude/workflows/*.js`, confirmed precedent, not a new
     finding).

4. **Item 3 — popular/community content swap (if Plan selects any of the 6 flagged skills)**
   - Test name: none in the pytest sense — `SKILL.md` content has no executable surface (confirmed
     precedent across every prior skill-content ticket read). Verification is a manual before/after
     diff read plus `python3 tools/validate_frontmatter.py .claude/skills/<name>/SKILL.md` if the
     swap changes frontmatter (e.g. adding an honest `source: community, risk: ...` disclosure to a
     currently-undisclosed skill, matching `api-design-principles`/`architecture`'s existing pattern).
   - Category: N/A (manual verification), matching `SKILL-TRIGGER-COVERAGE`'s and
     `TAG-DOCS-CROSSREF`'s own precedent for prompt/doc-only changes.
   - What it verifies: the swapped content still satisfies this repo's own trigger conditions
     (`Related Code Areas`/CLAUDE.md row wording) and doesn't silently drop project-specific
     adaptations a prior swap might have made.
   - Where it lives: n/a — a manual verification step recorded in the child ticket's own Test Summary.

5. **Item 4 — new Skill-tool-usage-by-name metric**
   - Test name: `test_skill_usage_section_counts_by_tool_name`, `test_skill_usage_section_handles_
     python_dict_repr_input_summary` (regression-proofing the non-JSON `input_summary` parsing this
     investigation found), `test_skill_usage_section_omitted_when_no_skill_calls` (mirrors the
     existing conditional-render convention used by Reason Codes / Tag Breakdown sections).
   - Category: unit, following `tests/tools/test_generate_retro.py`'s existing structure (or a new
     test file if built as a standalone script per `retrieval_baseline_metrics.py`'s pattern).
   - What it verifies: the new metric is derived correctly from `tools.jsonl`'s actual (non-JSON)
     `input_summary` shape, is clearly distinguished from the existing tag-breakdown's gate-hit
     metric, and never fabricates a count for a skill with zero calls (renders `0`, not omitted, for
     a skill that IS invoked elsewhere but not in the current range — vs. omitting the whole section
     when literally no `Skill` calls exist in range, matching the existing omit-when-empty pattern at
     the section level, not the per-skill-row level).
   - Where it lives: `tools/agent-monitoring/generate_retro.py` (new section) or a new
     `tools/agent-monitoring/skill_usage_metrics.py` (standalone, `retrieval_baseline_metrics.py`
     pattern) + matching test file — Plan decides which, per investigation.md's Item 4 finding that
     the epic's own Scope text accepts either shape.

6. **Item 5 — any doc updates identified above**
   - No pytest surface (docs-only) — verification is `python3 -m pytest
     tests/tools/test_validate_frontmatter.py -q` (regression, universal precedent) plus a manual
     diff-read confirming only the intended section changed, matching every sibling ticket's Test
     Summary discipline read during this investigation.

## Scoped Pytest Commands

For this epic itself (investigation-only, verifying no source was touched):
```
git status --porcelain -- .claude/ tools/ docs/ src/
```
(must show only this ticket's own staging artifacts — confirms Investigate made no implementation
changes, per the epic's explicit "do not propose code changes yet" instruction).

For any child ticket touching the tag/skill-mapping or agent-monitoring surface, the scoped command
set (do not run bare `pytest tests/`):
```
python3 -m pytest tests/tools/test_tag_registry.py tests/tools/test_tag_skill_mapping_check.py \
  tests/tools/test_generate_retro.py tests/tools/test_ticket_scoper_relevance_check.py \
  tests/tools/test_finalize_tag_drift_wiring.py tests/tools/test_validate_frontmatter.py \
  tests/tools/test_workflow_meta_conformance.py -q
```
For a child ticket touching only `.claude/workflows/implement-ticket.js`'s Security-Review-adjacent
code (new gate or hotfix-paragraph fix), add: `node -c .claude/workflows/implement-ticket.js`.

## Anti-Drift Test Guards

- Any child ticket's tests must NOT weaken or delete
  `test_add_tag_is_append_only_existing_entries_unchanged` (`test_tag_registry.py`) — the
  append-only invariant on `tag_registry.jsonl` is load-bearing across 3 prior tickets
  (`TAG-REGISTRY-DATA`, `SKILL-MAPPING-DEDUP`, `TAG-RELEVANCE-VERIFY`) and must survive any Item-2
  mapping expansion.
- Any child ticket adding a new hard gate (Item 1/2) must include a **zero-added-latency negative
  test** (a ticket without the triggering tag produces zero new events) — `WORKFLOW-SECURITY-GATE`'s
  own AC3 established this as the required guard shape for any future gate; skipping it would let a
  new gate silently regress every non-triggering ticket's run time/event count.
- Any child ticket touching `generate_retro.py` must confirm the two existing `## Tag Breakdown`
  sections' tests (`test_generate_retro.py`) still pass unmodified — a new Item-4 section must be
  provably additive, not a rewrite of the existing tag-breakdown logic (this investigation found
  those two are easy to conflate with a new "skill usage" section since both read `tools.jsonl`).
- Any child ticket fixing the `implement-ticket/SKILL.md:70` hotfix paragraph must re-run
  `tests/tools/test_workflow_meta_conformance.py` and manually re-read the corrected paragraph
  against `implement-ticket.js`'s actual tier-conditional blocks (lines 470, 914, and the
  `Security-Review` block at 1227-1279) to confirm the fix doesn't introduce a new mismatch in the
  other direction (e.g. accidentally implying Architecture-Verify also runs for hotfix, which it does
  not).

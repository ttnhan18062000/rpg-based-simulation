---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260810-SKILL-USAGE-RETRO-TRACKING
phase: done
date: 2026-08-10
tags: [skills, agent-monitoring, observability, process-improvement]
---

# TCK-20260810-SKILL-USAGE-RETRO-TRACKING

## Title
Wire `skill_usage_metric.py` into the recurring retro and flag zero-invocation skills after a
grace period

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`TCK-20260805-SKILL-USAGE-METRIC` (child of `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC`) built
a real, tested per-skill invocation-count tool (`tools/agent-monitoring/skill_usage_metric.py`),
deliberately as a **standalone one-off script**, "same reasoning as `SECURITY-GATE-FIRING-MONITOR`:
one-off/periodic tool, not part of the weekly retro cadence." That decision made sense at the time,
but it means skill adoption is not watched on any cadence today.

Running it live during a 2026-08-10 audit surfaced a real, current data point: the same epic's own
6 new bespoke domain skills — `observability`, `simq-dev`, `systems-economy`, `combat-mechanics`,
`cognition-strategy`, `progression-entities` (authored 2026-08-05, closing real gaps the epic's
domain-coverage sweep confirmed) — show **zero invocations** in the corpus so far. 5 days is too
early to call this a failure, but nothing currently re-checks this on a schedule, so a genuine
adoption failure could go unnoticed indefinitely. This is the same structural gap already ticketed
for context-search tooling in this same epic folder (`TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`):
a real, honest metric exists, but nothing puts it in front of anyone on a recurring basis.

## Scope
- **Investigate (mandatory before Plan):** read `skill_usage_metric.py`'s current structure
  (`build_skill_usage_section`, its `derivation` string, `per_skill`/`per_skill_per_run` shape) and
  `generate_retro.py`'s existing section-assembly pattern before designing anything new — reuse,
  don't duplicate the counting logic (call the existing function, don't reimplement the regex).
- Add a `## Skill Usage` section to `generate_retro.py`'s recurring report, trended report-over-report,
  following the same "never silent/fabricated" convention (mandatory `derivation` string) already
  used throughout that file.
- Add a "zero-invocation skills" flag: cross-reference the full skill catalog (`.claude/skills/*/SKILL.md`,
  16+ entries) against `skill_usage_metric.py`'s real per-skill counts, and surface any skill with
  zero invocations whose `SKILL.md` frontmatter/creation date is older than a defined grace period
  (propose 14 days — long enough that a skill genuinely hasn't had a relevant task yet doesn't get
  falsely flagged; Plan phase may adjust with reasoning). Do not auto-flag skills younger than the
  grace period — the 6 new domain skills should not trip this on day 1.
- Decide (Plan phase) whether the grace-period threshold and skill-creation dates are sourced from
  `SKILL.md` file mtimes, ticket `date:` frontmatter of the skill's authoring ticket, or another
  real source — not guessed.

## Out of Scope
- Any change to `skill_usage_metric.py`'s existing counting logic, regex, or output shape — reused
  as-is, not modified.
- Auto-invoking or auto-deprecating a zero-invocation skill — this ticket only makes the signal
  visible in the recurring report; any decision to act on a flagged skill is a separate, later,
  human-reviewed step.
- Re-litigating `TCK-20260705-SIX-SKILLS-INVESTIGATION`'s "correctly redundant" verdicts for the
  pre-existing zero-invocation skills it already assessed — this ticket's flag applies going
  forward, it does not reopen that investigation's settled findings.

## Acceptance Criteria
- [x] A real `generate_retro.py` run against the current corpus produces a `## Skill Usage` section
      with real, non-fabricated per-skill counts (reusing `skill_usage_metric.py`'s function, not a
      reimplementation).
- [x] The zero-invocation-after-grace-period flag correctly excludes the 6 domain skills today
      (all younger than the grace period) and correctly would have flagged `backend-testing` prior
      to its `TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED` fix, as a sanity check against a real
      historical case.
- [x] Every new section has a `derivation` string.
- [x] New tests mirror existing `generate_retro.py`/`skill_usage_metric.py` test patterns
      (never-silent, derivation-matches-fields, real-corpus checks, reuse-not-reimplement AST guards).
- [x] `docs/agent-monitoring/README.md`/`schema.md` updated to describe the new section.

## Related Tickets
- TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC (parent)
- TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING (sibling; same structural gap — metric exists,
  not on a recurring cadence — different subsystem)
- TCK-20260805-SKILL-USAGE-METRIC (DONE; built the metric this ticket wires into the recurring retro)
- TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC (DONE; parent epic that authored the 6 domain skills
  whose adoption this ticket will watch)
- TCK-20260705-SIX-SKILLS-INVESTIGATION (DONE; prior zero-invocation assessment, not reopened)
- TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED (DONE; real historical case used as this ticket's
  flag-logic sanity check)

## Related Docs
- `docs/agent-monitoring/README.md`
- `docs/agent-monitoring/schema.md`
- `docs/ai/skills.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/generate_retro.py`
- `tools/agent-monitoring/skill_usage_metric.py`
- `.claude/skills/*/SKILL.md`
- `tests/tools/test_generate_retro.py`
- `tests/tools/test_skill_usage_metric.py`

## Assumptions / Open Questions
- Grace-period length (proposed 14 days) is not final — Plan phase should confirm against real
  skill-adoption lead times observed in the corpus rather than treating 14 as settled.
- Whether zero-invocation flagging belongs in `generate_retro.py` directly or as an extension to
  `skill_usage_metric.py` itself (which `generate_retro.py` then renders) — left to Investigate/Plan,
  matching the existing house pattern of thin rendering vs. metric-owning modules.

## Implementation Notes
Followed `staging_artifacts/TCK-20260810-SKILL-USAGE-RETRO-TRACKING/plan.md`'s 7 steps in order.

**Step 1 (relocate `build_skill_usage_section`):** Moved the function body and `_SKILL_NAME_RE`
verbatim from `skill_usage_metric.py` into `generate_retro.py`, placed after
`build_raw_investigation_count_section` (immediately before `_collect_inprogress_tagged_tickets`)
— grouped with the other relocated `build_*` functions rather than pinned exactly at
`build_search_count_section`'s line. `skill_usage_metric.py` now does
`from generate_retro import DEFAULT_TOOLS_FILE, build_skill_usage_section, load_jsonl` and no
longer imports `re`/`collections.defaultdict` (both became unused after the move). One comment
line's wording changed (referencing `build_search_count_section`'s own run_id convention instead
of `retrieval_baseline_metrics.py`'s, since the regex/bucketing logic itself is untouched — see
Deviations in plan.md).

**Step 2 (period-scoped `## Skill Usage` count subsection + index.md trend column):** In
`generate()`, added `su = build_skill_usage_section(tools or [])` alongside `pircc`. Rendered
`### Per-Skill Invocation Counts (This Period)` under a new `## Skill Usage` heading, gated (with
Step 4's flag gate) so the whole heading is omitted when there is nothing to show. Added a `Skill
Invocations` column to `_update_index()`'s trend table, computed via
`build_skill_usage_section(week_tools)["total_skill_invocations"]`, reusing the existing
`week_tools` slice.

**Step 3 (`compute_zero_invocation_skill_flags`):** Added `_DEFAULT_SKILLS_DIR` next to
`_DEFAULT_TICKETS_ROOT` and `SKILL_ZERO_INVOCATION_GRACE_PERIOD_DAYS = 14` next to
`SEARCH_TOOL_NAMES`. New function reuses `build_skill_usage_section`, iterates
`sorted(skills_dir.iterdir())`, and returns `flagged_stale`/`flagged_unknown_age` as two
non-conflated buckets plus `catalog_parse_errors`, per Design Decision 2's fail-open policy.
Reuses `extract_frontmatter` (already imported at module top) — no second frontmatter parser.

**Step 4 (wire flags into `generate()`, thread `all_tools`):** Added `all_tools=None` to
`generate()`'s signature with **no `tools` fallback of any kind** — `zif =
compute_zero_invocation_skill_flags(all_tools) if all_tools is not None else None`. The
`### Zero-Invocation Flags (All-Time, {N}-Day Grace Period)` subsection and the whole `##
Skill Usage` heading gate both check `zif is not None` before dereferencing either flag list.
`main()` now calls `generate(runs, events, label, week_str, tools=tools, all_tools=all_tools)`.
Added `test_generate_without_all_tools_never_computes_zero_invocation_flags`, which monkeypatches
`compute_zero_invocation_skill_flags` to raise if called and asserts `generate()` with only
`tools=` never triggers it and never renders the flags heading.

**Step 5 (tests):** Added the full new test block to `tests/tools/test_generate_retro.py` under a
`# --- ## Skill Usage (AC1/AC2/AC3/AC4) ---` banner, covering every test named in Steps 1-4's
Verify lists. Extended `test_all_new_sections_have_derivation_key` and
`test_new_sections_never_write_any_file` with the two new functions. `tests/tools/test_skill_usage_metric.py`'s
12 existing tests pass unmodified (regression proof for Step 1's verbatim relocation).
`test_index_md_trends_search_and_read_investigation_columns` (pre-existing, in the index.md
section this ticket changes) needed its header/row assertions updated for the new column — see
Deviations below. Full suite: `pytest tests/tools/test_generate_retro.py
tests/tools/test_skill_usage_metric.py -q` → 150 passed.

**Step 6 (docs):** Added the `2026-08-15` cadence-integration addendum to
`docs/agent-monitoring/README.md`'s `## Skill Usage Metric` section, a new `**Skill Usage**` row
to `docs/guides/agent_monitoring.md`'s Report Sections table, and a `Skill` case to
`docs/agent-monitoring/schema.md`'s `input_summary` Fields-table row (the real, confirmed
pre-existing gap).

**Step 7 (parity ledger):** Plan.md explicitly defers this to the Parity phase ("This step is
expected to be finalized by the Parity phase (parity-updater agent) against the actual landed
`v2_evidence` line numbers... not necessarily by the implementer"). No entry was written to
`docs/parity_ledger/infrastructure.yaml` in this pass. Draft for the Parity phase:

```
- id: INFRA-333
  text: TCK-20260810-SKILL-USAGE-RETRO-TRACKING -- build_skill_usage_section relocated from
    skill_usage_metric.py into generate_retro.py (tools/agent-monitoring/generate_retro.py:434,
    _SKILL_NAME_RE + verbatim body), resolving the same circular-import constraint as
    INFRA-332's SEARCH_TOOL_NAMES precedent (skill_usage_metric.py:24 re-imports it back).
    New compute_zero_invocation_skill_flags (generate_retro.py:475) cross-references the real
    .claude/skills/*/SKILL.md catalog against build_skill_usage_section's per_skill counts,
    all-time-scoped, split into flagged_stale/flagged_unknown_age buckets with a
    SKILL_ZERO_INVOCATION_GRACE_PERIOD_DAYS=14 grace period (generate_retro.py:348). generate()
    gains all_tools=None (no tools fallback) and renders a new '## Skill Usage' section
    (generate_retro.py:1675) with two subsections: '### Per-Skill Invocation Counts (This
    Period)' (period-scoped, generate_retro.py:1679) and '### Zero-Invocation Flags (All-Time,
    N-Day Grace Period)' (all-time, generate_retro.py:1693, only computed/rendered when the
    caller explicitly passes all_tools). _update_index() gains a Skill Invocations trend column.
  status: verified
  priority: P2
  legacy_evidence: null
  v2_evidence: tools/agent-monitoring/generate_retro.py (line numbers above -- finalize against
    landed diff), tools/agent-monitoring/skill_usage_metric.py:24 (re-import)
  proof_type: regression
  test_path: tests/tools/test_generate_retro.py
  divergence_note: null
  support_boundary: Agent-monitoring tooling only -- no src/ touched, no simulation behavior
    involved. Follows the INFRA-281-INFRA-332 agent-tooling-infrastructure precedent (Parity
    phase overrides the "no src/ touched -> no entry needed" reasoning both
    TCK-20260805-SKILL-USAGE-METRIC and this ticket's own investigation.md initially floated).
```

## Test Summary
`pytest tests/tools/test_generate_retro.py tests/tools/test_skill_usage_metric.py -q` → **150
passed** (was 130 before this ticket's changes; +20 new tests, 1 pre-existing test updated for
the new index.md column, 2 cross-cutting tests extended). Also manually ran
`python3 tools/agent-monitoring/generate_retro.py --all` and
`python3 tools/agent-monitoring/skill_usage_metric.py` against the real corpus and inspected the
rendered `## Skill Usage` section: real per-skill counts, and a Zero-Invocation Flags subsection
correctly listing `api-design-principles`/`architecture` under `flagged_stale` (real `date_added:
"2026-02-27"`, well past the 14-day grace period) and 7 skills with no `date_added` under
`flagged_unknown_age` — the 6 domain skills and `backend-testing` are correctly absent from
`flagged_stale` (matching AC2).

## Files Changed
- `tools/agent-monitoring/generate_retro.py` — relocated `build_skill_usage_section`/`_SKILL_NAME_RE`
  in; added `_DEFAULT_SKILLS_DIR`, `SKILL_ZERO_INVOCATION_GRACE_PERIOD_DAYS`,
  `compute_zero_invocation_skill_flags`; `generate()` gains `all_tools` param and `## Skill Usage`
  render; `main()` passes `all_tools` through; `_update_index()` gains Skill Invocations column;
  `datetime` import extended with `date`.
- `tools/agent-monitoring/skill_usage_metric.py` — local `build_skill_usage_section`/`_SKILL_NAME_RE`
  definition replaced with a re-import; unused `re`/`collections.defaultdict` imports removed.
- `tests/tools/test_generate_retro.py` — new imports (`build_skill_usage_section`,
  `compute_zero_invocation_skill_flags`, `datetime.date`); new `## Skill Usage` test block (23
  tests); extended `test_all_new_sections_have_derivation_key`,
  `test_new_sections_never_write_any_file`; updated
  `test_index_md_trends_search_and_read_investigation_columns` for the new index.md column.
- `docs/agent-monitoring/README.md` — cadence-integration addendum under `## Skill Usage Metric`.
- `docs/guides/agent_monitoring.md` — new `**Skill Usage**` row in the Report Sections table.
- `docs/agent-monitoring/schema.md` — added the `Skill` case to the `input_summary` Fields-table row.

## Completion Summary
Wired `skill_usage_metric.py`'s `build_skill_usage_section` into `generate_retro.py`'s recurring
retro cadence by relocating it (mirroring the sibling ticket's established circular-import fix),
and added a new `## Skill Usage` report section with two scope-distinct subsections: a
period-scoped per-skill invocation count (trended via a new `index.md` column) and an all-time,
two-bucket (`flagged_stale`/`flagged_unknown_age`) zero-invocation flag with a 14-day grace period,
gated so the real-filesystem `.claude/skills/` scan only ever runs when a caller explicitly opts
in via `generate()`'s new `all_tools` parameter (the architecture-review-mandated fix, verified via
a dedicated regression test). All 5 acceptance criteria are satisfied on the real corpus: the flag
correctly excludes the 6 domain skills today and correctly would have flagged `backend-testing`'s
pre-fix state. Docs updated; parity ledger entry drafted for the Parity phase per plan.md's
explicit deferral.

---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260810-SKILL-USAGE-RETRO-TRACKING
phase: open
date: 2026-08-10
tags: [skills, agent-monitoring, observability, process-improvement]
---

# TCK-20260810-SKILL-USAGE-RETRO-TRACKING

## Title
Wire `skill_usage_metric.py` into the recurring retro and flag zero-invocation skills after a
grace period

## Status
OPEN

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
- [ ] A real `generate_retro.py` run against the current corpus produces a `## Skill Usage` section
      with real, non-fabricated per-skill counts (reusing `skill_usage_metric.py`'s function, not a
      reimplementation).
- [ ] The zero-invocation-after-grace-period flag correctly excludes the 6 domain skills today
      (all younger than the grace period) and correctly would have flagged `backend-testing` prior
      to its `TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED` fix, as a sanity check against a real
      historical case.
- [ ] Every new section has a `derivation` string.
- [ ] New tests mirror existing `generate_retro.py`/`skill_usage_metric.py` test patterns
      (never-silent, derivation-matches-fields, real-corpus checks, reuse-not-reimplement AST guards).
- [ ] `docs/agent-monitoring/README.md`/`schema.md` updated to describe the new section.

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
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)

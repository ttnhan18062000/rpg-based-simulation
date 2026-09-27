---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260927-RETRO-SKILL-FLAG-BLIND-TO-OTHER-CHANNELS
artifact_type: investigation
tags: [agent-monitoring, retro, data-quality]
---

# Investigation: TCK-20260927-RETRO-SKILL-FLAG-BLIND-TO-OTHER-CHANNELS

## Root cause, confirmed by direct source read

`compute_zero_invocation_skill_flags()` (`tools/agent-monitoring/generate_retro.py`) cross-
references the real `.claude/skills/*/SKILL.md` catalog against
`build_skill_usage_section(tools)["per_skill"]`, which is derived **solely** from `tools.jsonl`
rows where `tool == "Skill"`. Confirmed by direct read of both functions: there is no code path
anywhere in this cross-reference that considers an agent dispatch, a phase-prompt enrichment, or
a test-guard file as evidence of use.

## Re-ran the live function before touching anything

```
python3 -c "... compute_zero_invocation_skill_flags(real tools) ..."
```
Result (2026-09-27, `.venv` on u24desktop):
```
flagged_stale: api-design-principles, architecture, backend-testing, observability,
               progression-entities, simq-dev, systems-economy
flagged_unknown_age: debugging-strategies, doc-coauthoring, frontend-design, prompt-builder,
                     python-performance-optimization, python-testing-patterns,
                     test-driven-development
```
14 total, matching the retro report's own count.

## A discrepancy in the ticket's own premise, checked before trusting it

The ticket's Request Summary cites `/security-review` as an example of a currently-flagged skill.
**Direct check: no `.claude/skills/security-review/` directory has ever existed in this repo**
(`git log --all -- ".claude/skills/security-review"` returns nothing). `compute_zero_invocation_
skill_flags()` only iterates real `skills_dir.iterdir()` entries — a name with no matching
directory can never appear in `flagged_stale`/`flagged_unknown_age` at all, confirmed by the live
run above (neither list contains `security-review`).

Re-read `agent-monitoring/retro/RETRO-2026-W39.md`'s own "Skill zero-invocation flags" section
(the source of this ticket): it uses `/security-review` as an **illustrative** measurement (17
agent events + 24 phase events + 0 literal `Skill`-tool calls for that name), not a literal member
of "the 14 flags" — the report's own wording ("At least 4 of the 14 flags...") groups it with the
3 real catalog flags it names earlier (`api-design-principles`, `debugging-strategies`,
`python-performance-optimization`) as the same *class* of problem, not a 4th catalog entry.

This does not invalidate the ticket: `tag_registry.py::get_skill_mapping()` (the durable source
this ticket's Scope points to) genuinely maps `"security"` -> `{"skill": "/security-review", ...}`
— it is a real, registered mapping, just one with no corresponding skill directory. AC1's
"demonstrated on /security-review" is satisfied via a fixture (a synthetic `.claude/skills/
security-review/` directory in a temp `skills_dir`), the same fixture style every other test in
this suite already uses for skills that don't exist in the real catalog (e.g.
`test_backend_testing_pre_fix_state_would_have_been_flagged`).

## Durable source chosen for AC4 (resolving the ticket's own Open Question)

`tag_registry.py::get_skill_mapping()` alone — covers all 4 tag-mapped skills
(`security` -> `/security-review`, `api-design` -> `/api-design-principles`, `debugging` ->
`/debugging-strategies`, `performance` -> `/python-performance-optimization`). Confirmed via
direct call: every one of the 3 that has a real catalog directory
(`api-design-principles`, `debugging-strategies`, `python-performance-optimization`) is
CURRENTLY zero-invocation and CURRENTLY flagged before this fix — a live, real demonstration of
the exact defect, not a hypothetical.

**Decided NOT to add a second, parallel channel source** (e.g. a new `SKILL.md` frontmatter field
naming an enforcement channel), even though the ticket's own Assumptions section left this open
and leaned toward it. `get_skill_mapping()` already durably covers every skill this ticket names
as a concrete example — adding a second annotation surface for the same fact
(`api-design-principles`'s test-guard enforcement is *additional* detail about the same tag-mapped
skill, not a different skill needing a different mechanism) would duplicate information this repo
already defines once, which this project's own standing convention rejects
([[feedback_define_information_once_never_repeat]]). If a future skill needs coverage with no tag
mapping at all, that is new evidence for a second mechanism then — not assumed now.

## Second defect: none found

Unlike the sibling ticket (`TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS`), this ticket's Scope
names only the one detector fix plus a derivation-note update — no second defect to investigate.

## Existing test coverage read

`tests/tools/test_generate_retro.py` (171 tests before this ticket) — the `compute_
zero_invocation_skill_flags` section (`_write_skill()` fixture helper, real-corpus soft-checked
assertions via `skill_staleness_check()`) is the direct precedent for this ticket's own new tests.
`test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus` and
`test_backend_testing_post_fix_state_not_currently_flagged` both re-ran and passed unmodified
after the fix — confirming the new `covered_by_other_channel` bucket is additive, not disruptive,
to the pre-existing real-corpus assertions (their own `flagged_stale`/`flagged_unknown_age` counts
shrank as a side effect — `api-design-principles` dropped out of the `flagged_stale` list in the
warning text, exactly as expected — but neither test's own pass/fail assertion depends on the
count, only on absence of specific domain-skill names, so both still pass).

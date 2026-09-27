---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260927-RETRO-SKILL-FLAG-BLIND-TO-OTHER-CHANNELS
phase: done
date: 2026-09-27
tags: [agent-monitoring, retro, data-quality]
---

# TCK-20260927-RETRO-SKILL-FLAG-BLIND-TO-OTHER-CHANNELS

## Title

The retro's zero-invocation skill flag counts only `tool == "Skill"` rows, so a capability delivered
by agent dispatch, phase enrichment or an unconditional test guard reads as permanently dead — it
flagged `/security-review` while that capability ran 17 times.

## Status

DONE

## Tier

standard

## Type

bug

## Priority

P2

## Request Summary

Found while reviewing the W39 retro (`agent-monitoring/retro/RETRO-2026-W39.md`). The report's
zero-invocation flag named 14 skills. I wrote that up as a finding — "a mandated routing rule that
has never fired" — and **it was wrong**, because three of the named skills had already been decided
per-skill by `TCK-20260805-SKILL-GATE-CONVERSION-DECISION` and the zero-invocation fact is recorded in
that ticket's own Request Summary. That retraction had to be applied to a report already committed.

What survives is the detector. `build_zero_invocation_flags()` cross-references the
`.claude/skills/*/SKILL.md` catalog against `build_skill_usage_section(tools)["per_skill"]`, which is
derived **solely** from `tools.jsonl` rows where `tool == "Skill"`. That is one of several channels a
capability can actually be delivered through in this repo:

| Capability | Real delivery channel | `Skill` rows |
|---|---|---|
| `/security-review` | `security-reviewer` **agent** (17 events all-time) + `Security-Review` **phase** (24 events) | **0** |
| `/python-performance-optimization` | tag-driven **Test-phase prompt enrichment** (`ticketInfo.tags.includes('performance')`) | **0** |
| `/api-design-principles` | unconditional test guard `tests/architecture/test_api_read_model_guard.py` | **0** |

So at least 3 of the 14 flags can never clear no matter how heavily the capability is used, and one
of them flags a gate that is actively firing. The flag's wording ("Zero-Invocation Flags",
"flagged_stale") invites exactly the reading I gave it.

The existing derivation note is honest about *how* it counts but not about *what a zero means* — it
explains the `date_added` grace period and the fail-open policy in detail, and says nothing about
capabilities that never route through the `Skill` tool at all.

## Scope

- Make a zero mean something checkable. Either teach the flag the other delivery channels (agent
  events, phase enrichment, a named enforcing test) so a covered capability is not flagged, or narrow
  the flag's claim and wording to "not invoked as a skill," which is all the data supports.
- Suppress or annotate a flag for any skill whose capability has a known non-`Skill` delivery channel,
  sourced from something durable — `tag_registry.get_skill_mapping()` already names the tag→skill
  relationships, and `TCK-20260805-SKILL-GATE-CONVERSION-DECISION`'s outcomes are recorded in
  `docs/guidelines/tag_taxonomy.md`.
- Extend the section's derivation note to state what a zero does and does not imply, in the same
  disclosed-limitation style the report already uses elsewhere (e.g. the Search-Before-Grep section's
  own sub-agent-attribution caveat, which is the right precedent).

## Out of Scope

- **Re-deciding whether any of those 3 skills should become a gate.**
  `TCK-20260805-SKILL-GATE-CONVERSION-DECISION` settled that per-skill with evidence and its outcome
  stands. This ticket does not touch that decision, the `suggested_skills` advisory design, or
  CLAUDE.md's auto-invoke table.
- Deleting skills. Whether a genuinely unused skill should be removed is a separate judgment, and
  this ticket's whole point is that the current signal cannot identify one.
- Changing how `tools.jsonl` records `Skill` invocations. The recording works; `input_summary`'s
  Python-repr shape parses correctly via the production regex on 311 of 311 all-time rows (I
  confirmed this after my own ad-hoc parser wrongly suggested otherwise).

## Acceptance Criteria

1. A skill whose capability is delivered through a non-`Skill` channel is either not flagged, or
   flagged with that channel named — demonstrated on `/security-review`, whose agent and phase both
   have real all-time event counts.
2. A skill with genuinely no delivery channel and no invocations is still flagged. The change must not
   silence the signal wholesale.
3. The derivation note states what a zero implies and what it does not, naming the non-`Skill`
   channels that exist.
4. The suppression/annotation source is durable and cited (registry or recorded decision), never a
   hardcoded list of skill names in the generator.
5. Regenerating an existing report still preserves hand-authored `## Notes`
   (`TCK-20260915-RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES` behavior unchanged).
6. Tests cover: a covered-capability skill, a genuinely-unused skill, and a skill with nonzero `Skill`
   invocations (never flagged, unchanged).

## Related Tickets

- `TCK-20260805-SKILL-GATE-CONVERSION-DECISION` — the decision this flag's output caused me to
  re-litigate. Out of Scope here.
- `TCK-20260810-SKILL-USAGE-RETRO-TRACKING` — built the flag and its `date_added` grace period.
- `TCK-20260720-SKILL-MAPPING-DEDUP` — owns `get_skill_mapping()`, a candidate durable source for AC4.
- `TCK-20260915-RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES` — the notes-preservation behavior AC5 pins.

## Related Docs

- `docs/agent-monitoring/README.md`
- `docs/guidelines/tag_taxonomy.md` — records the per-skill outcomes AC4 can source from.
- `agent-monitoring/retro/RETRO-2026-W39.md` — the report where this surfaced, including the
  retraction.

## Related Stored Artifacts

None yet.

## Related Code Areas

- `tools/agent-monitoring/generate_retro.py` — `build_skill_usage_section()`,
  `build_zero_invocation_flags()` and the Skill Usage section renderer.
- `tools/tag_registry.py` — `get_skill_mapping()`.

## Assumptions / Open Questions

- Which durable source should drive AC4? `get_skill_mapping()` covers the 4 tag-mapped skills but not
  the test-guard channel (`api-design`'s real enforcement). A per-skill field in the skill's own
  `SKILL.md` frontmatter naming its enforcement channel may be the better home, since it keeps the
  fact next to the thing it describes — worth settling in `plan.md` rather than assumed here.
- Open: should the flag distinguish "covered by another channel" from "genuinely unused" as two
  separate lists, or one list with an annotation column? Two lists is clearer to read but doubles the
  section; leaning annotation.

## Implementation Notes
Before trusting the Request Summary's `/security-review` example, confirmed directly: no
`.claude/skills/security-review/` directory has ever existed in this repo's git history. The
retro report's own text uses it as an illustrative measurement (agent/phase event counts), not a
literal member of the current 14 catalog flags — this does not invalidate the ticket, since
`tag_registry.py::get_skill_mapping()` genuinely maps `security` -> `/security-review`, but AC1's
demonstration is necessarily fixture-based for this specific name (same style every other test in
this suite already uses for skills without a real catalog entry).

Resolved AC4's Open Question toward `get_skill_mapping()` alone (no new `SKILL.md` frontmatter
field) — it already durably covers every skill this ticket names, confirmed by a live real-corpus
run showing `api-design-principles`, `debugging-strategies`, and `python-performance-optimization`
all currently zero-invocation and currently misflagged before this fix.

## Test Summary
- `python3 -m pytest tests/tools/test_generate_retro.py -v -k "covered or alternate_channel"` — new
  tests pass individually; full file run below is the authoritative count.
- `python3 -m pytest tests/tools/test_generate_retro.py -q` — **178 passed** (171 pre-existing + 7
  new, none removed/modified). Real-corpus checks
  (`test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus`,
  `test_backend_testing_post_fix_state_not_currently_flagged`) both still pass unmodified — their
  own `flagged_stale` warning text shrank by one entry (`api-design-principles` dropped out), as
  expected, without needing any assertion change.
- Live real-corpus confirmation: `compute_zero_invocation_skill_flags()` against the real
  `tools.jsonl` now reports `covered_by_other_channel` = `api-design-principles` (tag `api-design`),
  `debugging-strategies` (tag `debugging`), `python-performance-optimization` (tag `performance`) —
  all three correctly removed from `flagged_stale`/`flagged_unknown_age`.
- `pytest tests/tools/ -m "not slow"` (full scoped regression) — **3111 passed, 25 skipped, 28
  deselected, 1 xfailed, 0 failed.**

## Files Changed
- `tools/agent-monitoring/generate_retro.py` — added `_skill_alternate_channels()`; widened
  `compute_zero_invocation_skill_flags()` with a `covered_by_other_channel` bucket checked before
  the stale/unknown-age branches; updated its docstring and `derivation` string; updated the
  `### Zero-Invocation Flags` report renderer to surface the new bucket and gate the subsection on
  it too.
- `tests/tools/test_generate_retro.py` — 7 new tests (AC1, AC2, AC3, AC4, AC6 covered/uncovered/
  nonzero-invocation cases, real-corpus confirmation).
- `staging_artifacts/TCK-20260927-RETRO-SKILL-FLAG-BLIND-TO-OTHER-CHANNELS/` —
  `investigation.md`/`plan.md`/`test_plan.md`.

## Completion Summary
Taught `compute_zero_invocation_skill_flags()` about `tag_registry.py::get_skill_mapping()`'s
already-recorded tag-driven routing: a skill named there is reported in a new
`covered_by_other_channel` bucket (with the covering channel named) instead of `flagged_stale`/
`flagged_unknown_age`, since a zero `Skill`-tool count proves nothing about disuse for a capability
delivered through tag-driven prompt enrichment. On the real corpus this immediately corrects 3
misflagged skills (`api-design-principles`, `debugging-strategies`,
`python-performance-optimization`). A skill with genuinely no channel and no invocations is still
flagged, unchanged (AC2). Chose the single existing tag registry as the sole durable source (AC4)
rather than adding a second, parallel `SKILL.md` frontmatter field, since it already covers every
example this ticket names — resisting the scope creep the ticket's own Assumptions section left
open as a live decision. Confirmed and documented (rather than silently accepted) that the
ticket's own `/security-review` example has no matching skill directory in this repo, so AC1 is
demonstrated via fixture, same as the suite's existing precedent for that shape of case.

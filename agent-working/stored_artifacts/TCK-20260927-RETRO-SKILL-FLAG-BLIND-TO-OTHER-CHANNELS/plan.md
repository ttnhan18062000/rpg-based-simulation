---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260927-RETRO-SKILL-FLAG-BLIND-TO-OTHER-CHANNELS
artifact_type: plan
tags: [agent-monitoring, retro, data-quality]
---

# Plan: TCK-20260927-RETRO-SKILL-FLAG-BLIND-TO-OTHER-CHANNELS

## Resolved Open Questions
1. Durable source for AC4: `tag_registry.py::get_skill_mapping()` alone (see investigation.md) —
   no new `SKILL.md` frontmatter field.
2. Annotation shape: one list with a `channel` field per entry (`covered_by_other_channel`), not
   two lists plus an annotation column — simpler, and the ticket's own leaning ("leaning
   annotation") is satisfied by a single list whose entries carry the annotation inline.

## Implementation steps — `tools/agent-monitoring/generate_retro.py`

1. `_skill_alternate_channels(root=None) -> dict[str, str]` — new helper. Builds
   `{bare_skill_name: channel_description}` from `get_skill_mapping()`'s `skill` values
   (`/`-stripped).
2. `compute_zero_invocation_skill_flags()`: for each zero-invocation catalog skill, check
   `_skill_alternate_channels()` **before** the `date_added` grace-period logic. A covered skill
   is appended to a new `covered_by_other_channel` list (`{"skill": name, "channel": text}`) and
   `continue`s — never reaches the stale/unknown-age branches, so it can never double-count.
3. Update the function's own docstring and `derivation` string to state the three-bucket split
   and what a zero does/does not imply (AC3).
4. Report renderer (`### Zero-Invocation Flags` section, ~line 1929): gate the whole subsection on
   `covered_by_other_channel` too (not just the two flag lists), and render a new "Covered by
   another channel" bullet list above the existing two, each entry naming its channel.

## Scope guards
- `TCK-20260805-SKILL-GATE-CONVERSION-DECISION` is not reopened, referenced, or re-derived.
- No `SKILL.md` frontmatter schema change.
- `AGENT_DRIFT_CEILING`/vocabulary.py/monitoring_anomaly_validator.py — untouched, unrelated.
- `## Notes` preservation behavior (`TCK-20260915-RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES`) —
  untouched code path; existing tests re-run as a regression guard, not modified.

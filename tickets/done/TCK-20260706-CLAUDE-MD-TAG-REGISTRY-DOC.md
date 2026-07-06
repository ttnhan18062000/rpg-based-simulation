---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260706-CLAUDE-MD-TAG-REGISTRY-DOC
phase: done
date: 2026-07-06
tags: [tagging, documentation, claude-md]
---

# TCK-20260706-CLAUDE-MD-TAG-REGISTRY-DOC

## Title
Reference the tag registry in CLAUDE.md's Ticket Format section

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Found while answering whether the ticket/working-log formats needed updating after
`TCK-20260706-TAG-REGISTRY-DATA`: `CLAUDE.md`'s Ticket Format section — the single most
authoritative, most-read instructions surface in this repo — still says only "Fill `layer` and
`tags` based on scope; leave `tags: []` if uncertain," with zero mention that tags are now a hard
allowlist gated by `docs/guidelines/tag_registry.jsonl`. This is exactly the blind spot that caused
two tags (`reporting`, `diagrams`) to need after-the-fact registration earlier this same session.

## Scope
- `CLAUDE.md`'s Ticket Format section: add one sentence after the existing
  "Fill `layer` and `tags`..." line, referencing `docs/guidelines/tag_taxonomy.md` and
  `tools/tag_registry.py add` as the way to introduce a genuinely new tag.

## Out of Scope
- Any change to the actual enforcement behavior (`validate_frontmatter.py`,
  `tools/tag_registry.py`) — this ticket is documentation-only.
- The related but separate gap (ticket-scoper/create-tickets not proactively checking the
  registry at Scope/Structure time) — tracked in `TCK-20260706-SCOPE-TAG-REGISTRY-CHECK`.

## Acceptance Criteria
- [ ] `CLAUDE.md`'s Ticket Format section mentions the tag registry and how to add a new tag.
- [ ] `validate_frontmatter.py` still passes on `CLAUDE.md` — n/a (not frontmatter-validated, it's
      a root project-instructions file, but confirm no accidental breakage of its own structure).

## Related Tickets
- TCK-20260706-TAG-REGISTRY-DATA (the feature this doc gap was about)
- TCK-20260706-SCOPE-TAG-REGISTRY-CHECK (the related functional gap, fixed separately)

## Related Docs
- CLAUDE.md
- docs/guidelines/tag_taxonomy.md

## Related Stored Artifacts
None (hotfix tier — no staging artifacts).

## Related Code Areas
None — documentation-only.

## Assumptions / Open Questions
None.

## Implementation Notes
Added one paragraph to `CLAUDE.md`'s Ticket Format section, directly after the existing
"Fill `layer` and `tags`..." sentence: states plainly that tags are a hard allowlist (not free
text), gives the exact `list`/`add` CLI commands and the 4 addable categories, and links to
`tag_taxonomy.md`/`ticket_tagging.md` for detail rather than duplicating their content.

## Test Summary
Documentation-only change to a root project-instructions file (not itself frontmatter-validated).
Manually re-read the edited section for accuracy against the live `tools/tag_registry.py` CLI
(command names, category list) — confirmed correct.

## Files Changed
- `CLAUDE.md` (Ticket Format section)
- `tickets/inprogress/TCK-20260706-CLAUDE-MD-TAG-REGISTRY-DOC.md` → `tickets/done/...`

## Completion Summary
Closed the documentation gap found while reviewing whether ticket/working-log formats needed
updating for the new tag registry: `CLAUDE.md`'s Ticket Format section now tells every future
session that tags are a hard allowlist and exactly how to register a new one, instead of silently
letting an agent invent a plausible tag that only fails 6+ phases later at Verify.

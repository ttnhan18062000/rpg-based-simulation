---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED
artifact_type: test_plan
tags: [skills, workflows]
---

# Test Plan — TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED

## Normal Flow
- `backend-testing/SKILL.md` reads as valid frontmatter + Markdown, zero Node/Express/Jest
  fingerprint strings remain, real repo pattern citations present.
- The 3 adapted skills each contain their new `## In This Repo` section.

## Edge Cases
- `.agents/` mirror regeneration covers all 4 skills without partial writes.
- `backend-testing`'s frontmatter change (`source: community`-style field addition) doesn't
  conflict with the disclosed-pair's existing `risk`/`source`/`date_added` shape — uses
  `source: project` specifically, a distinct, honest value, not a copy-paste of `community`.

## Failure Modes
- If the bespoke `backend-testing` replacement accidentally reintroduces a `../` reference or a
  Jest/Node string, a regression is caught by the same negative-string-check test that verified
  their removal.

## Regression-Prone Paths
- `tests/agent_orchestration_codex_adapter/` full suite re-run — confirms mirror regeneration for
  all 4 skills didn't break the contract mechanism.
- The 3 adapted skills' pre-existing content must not shrink — confirms the `## In This Repo`
  addition was additive, not an accidental content-destroying edit.

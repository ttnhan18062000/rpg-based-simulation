---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20261015-PROCESS-TEXT-PLANNER-CARD-TLS-MERGE-TREE
phase: done
date: 2026-10-15
tags: [documentation, delivery, process-improvement]
---

# TCK-20261015-PROCESS-TEXT-PLANNER-CARD-TLS-MERGE-TREE

## Title
Correct three process texts: the planner card commit line, the TLS paragraph, and what a local merge-tree with the REGISTRY driver can tell you

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Source: RETRO-2026-W41 final note (PR #605), W41/W42 deep investigation 2026-10-15, finding 8 and the delivery findings. (a) The planner card line "commit only on your own leased branch"
(#590, `docs/guidelines/session_roles/functions/planner.md` around L14, and every generated `.claude/agents/session-*-planner.md`)
is wrong. Leases are per worktree (`tools/sessions/state.py` lease_path), main-checkout seats hold none by design
(`registries/session_roles.yaml`), and `tools/sessions/card.py` already prints "Launches from the main checkout, no lease".
So the line reads as banning main-checkout planners from committing. The owner approved the replacement on 2026-10-15.
(b) `docs/guides/delivery_process.md`'s TLS paragraph describes a Fortiguard block page, but on u24desktop api.github.com
and the Actions hosts present certificates from a corporate intercepting CA (`DC=vn, DC=com, DC=tma, CN=tma-ADCA-CA`), with
intermittent handshake timeouts and 502s. (c) "Local merge-tree with the driver reads clean" proves nothing: the driver is
`merge.registry-regen.driver true` (keeps our side) and GitHub never runs it (shown on #589).

## Scope
1. Replace the card sentence with exactly: "Review PRs by comment; commit only on your own branch: in your own worktree,
   or, if you launch from the main checkout, on a small doc/ticket branch you cut there. Never commit in another role's
   worktree." Regenerate the cards (`tools/sessions/generate_agents.py`) and stay within the card budget (test_session_cards).
2. delivery_process.md TLS paragraph: name both patterns (block page; intercepting CA with timeouts/502s) and the check
   (`openssl s_client -connect api.github.com:443 -showcerts | grep issuer`).
3. delivery_process.md (CI/PR lifecycle, merge-driver note): predict GitHub mergeability with a driverless
   `git merge-tree --write-tree origin/main HEAD`, never with the driver.

## Out of Scope
- CLAUDE.md (owner's file); if its wording needs the same correction, put the literal diff in the PR body.
- pr_status.py retry behaviour.

## Acceptance Criteria
- The planner card and all generated planner session cards carry the new sentence; test_session_cards passes.
- delivery_process.md has both corrections; `make knowledge-index-update` was run (docs changed).
- The owner confirms the literal card diff in the PR (governing text).

## Related Tickets
- PR #590 (added the card line)
- TCK-20261015-REGISTRY-DETERMINISTIC-OUTPUT

## Related Docs
- docs/guidelines/session_roles/functions/planner.md
- docs/guides/delivery_process.md

## Related Stored Artifacts
- agent-working/agent-monitoring/retro/RETRO-2026-W41.md (final note, runs=281)

## Related Code Areas
- tools/sessions/generate_agents.py, .claude/agents/session-*-planner.md (generated)

## Assumptions / Open Questions
- none

## Implementation Notes
(a) Planner card: the owner-approved sentence of 2026-10-15 was "Review PRs by comment; commit only on your own branch: in your own worktree, or, if you launch from the main checkout, on a small doc/ticket branch you cut there. Never commit in another role's worktree." It does not fit the card budget (eight planner cards went over 400: agent-working-planner 439, asset 421, lead 421, perf 417, rpg 415, codebase 413, lead-u24 413, testing 407). The owner AMENDED the wording on 2026-10-16 (decided in agent-working-planner's terminal): "Review PRs by comment; commit only on your own branch: your worktree's, or a small doc/ticket branch if you launch from the main checkout." and dropped "See cross_session_messages guide." and "Designer briefs: handoffs once confirmed." from the card; both are kept in a new non-injected `## Reference` section of planner.md. After regeneration every planner card is within 400: agent-working-planner 399, lead-planner 380, asset-planner 381, perf-planner 377, rpg-planner 375, codebase-planner 373, lead-planner-u24 373, testing-planner 367, platform-planner 328. (b) delivery_process.md TLS paragraph names both patterns (a block page; on u24desktop the corporate intercepting CA `DC=vn, DC=com, DC=tma, CN=tma-ADCA-CA` with handshake timeouts and 502s) and the check `openssl s_client -connect api.github.com:443 -showcerts | grep issuer`. (c) delivery_process.md gets a bullet: predict GitHub mergeability with a driverless `git merge-tree --write-tree origin/main HEAD`, never with the registry driver (`merge.registry-regen.driver true` keeps our side; shown on #589).

## Test Summary
`tests/tools/test_session_cards.py`, `test_session_agent_generator.py`, `test_session_roster.py`, `test_session_platform_domain.py`: 106 passed; `python -m tools.sessions.validate`: 0 findings.

## Files Changed
docs/guidelines/session_roles/functions/planner.md, .claude/agents/session-*-planner.md (9 generated cards), docs/guides/delivery_process.md

## Completion Summary
The card wording, the TLS paragraph and the merge-tree rule are corrected. The planner card carries the amended (shorter) wording; the owner confirms the literal card diff in the PR (governing text).

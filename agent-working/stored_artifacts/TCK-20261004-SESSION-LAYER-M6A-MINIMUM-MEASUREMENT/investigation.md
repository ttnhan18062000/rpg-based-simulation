---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261004-SESSION-LAYER-M6A-MINIMUM-MEASUREMENT
date: 2026-10-05
tags: [ai, process-improvement, governance]
---

# Investigation: TCK-20261004-SESSION-LAYER-M6A-MINIMUM-MEASUREMENT

- M0j (`TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE`, row j): `UserPromptSubmit` carries `prompt`, `prompt_id`, `permission_mode`, `session_title`; sampling is possible. A semantic classifier is out of scope, so the tagger is phrase-based and conservative; the owner tally is the authoritative fallback.
- `tools.jsonl` rows have an exact-field pin (`test_post_tool_hook`); the plan asks for runs and events only, so tool rows are not stamped (tried, reverted).
- Closing a ticket happens inside the PR, so `finalized` cannot be the done-move; `mergedAt` is when the ticket reaches the default branch.
- No repo artifact records the dispatch message; first commit of the PR is the proxy, overridable.
- Real batch for AC4: PR 346 via `gh pr view 346`: first commit 2026-10-05T07:11:27Z, last check completed 07:53:13Z, merged 07:56:20Z. Hand computation: 41m46s, 3m07s, 44m53s; the reporter prints the same.
- No existing `UserPromptSubmit` hook; a new top-level key (owner confirmed).

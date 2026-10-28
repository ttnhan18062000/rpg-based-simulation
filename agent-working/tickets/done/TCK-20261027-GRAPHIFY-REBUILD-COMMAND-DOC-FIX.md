---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20261027-GRAPHIFY-REBUILD-COMMAND-DOC-FIX
phase: done
date: 2026-10-27
tags: [documentation, ai]
---

# TCK-20261027-GRAPHIFY-REBUILD-COMMAND-DOC-FIX

## Title
agent_working_environment.md: the shared-graph rebuild command is `graphify update . --force`, not `graphify extract --force`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
lead-planner-u24 found that `docs/guidelines/agent_working_environment.md` line 70 on origin/main (added in #754 by
`TCK-20261024-GRAPHIFY-ON-PATH-IS-NOT-THE-PINNED-VERSION`) gives the one-time shared-graph rebuild as
`graphify extract --force`. agent-working-designer-u24 checked it against graphifyy 0.9.70 (`graphify --help`):
- `extract` requires a path. Given one (`extract .`) and run without `--code-only`, it also runs paid semantic LLM
  extraction over every doc through whichever API key is set.
- The command that actually works, which the owner ran on u24 on 2026-10-27, is
  `graphify update . --force && python3 tools/graphify_prune.py`. That gave 58,389 nodes, 167,562 links and a
  97.9 MB graph.json.
- CLAUDE.md's Graphify section already uses `graphify update .` followed by `graphify_prune.py`. The doc line is the
  only place that disagrees.
- The doc's skill-version note ("from 0.6.7") was true only on ubuntu. On u24desktop the skill is 0.8.39.

Owner decision on #715 (6442823787), option A: agent-working-planner-u24 files this hotfix and lands the drafted
fix by agent-working-designer-u24 (main checkout
`.claude/handover/drafts/graphify-rebuild-command-doc-fix-2026-10-27.md`). The `.hcl` files stay out of the graph, so
there is no `graphifyy[terraform]` extra and the draft's "the extra is not needed" sentence stands. The doc's path
is unowned (`route`: unowned), and the owner chose to land it here without adding an owner.

## Scope
- `docs/guidelines/agent_working_environment.md`: in line 70, replace the two sentences starting at "The one-time
  shared-graph rebuild" with the draft's **After** text, verbatim:

  > The one-time shared-graph rebuild under the pin is run from the main checkout on `main` (`graphify update . --force`, then `python3 tools/graphify_prune.py`) after the batch merges: AST only, no API key, and `--force` lets the rebuilt graph replace one with more nodes (u24desktop, 2026-10-27: 58,389 nodes, 167,562 links, 97.9 MB graph.json). Do not use `graphify extract` for this: it needs a path, and without `--code-only` it also runs semantic LLM extraction over every doc through whichever API key is set. graphify also warns when its agent skills (`~/.claude`, `~/.copilot`, `~/.agents` under `skills/graphify`) are older than the package (0.6.7 on ubuntu and 0.8.39 on u24desktop when the pin was 0.9.70): `graphify install --platform <name>` refreshes one; the shim does not touch them. `graphify watch` also warns that the repo's `.hcl` files add nothing to the graph without the `graphifyy[terraform]` extra. That is expected, and the extra is not needed.

- `make knowledge-index-update` (a docs/ file changes).

## Out of Scope
- Any other text in the doc, and any other doc.
- `requirements-knowledge.txt` (no `graphifyy[terraform]` extra, per the owner).
- Giving the doc an owner in `registries/session_roles.yaml` (the owner chose option A, not the owns add).
- Running the rebuild itself; the owner already did that on u24.
- CLAUDE.md and `.claude/settings.json`.

## Acceptance Criteria
1. Line 70 of the doc carries the After text exactly as written above. `git diff` touches only those two sentences.
2. `graphify extract --force` no longer appears anywhere in `docs/` (grep).
3. `python3 tools/validate_frontmatter.py docs/guidelines/agent_working_environment.md` passes.
4. The PR body quotes the before/after.

## Related Tickets
- TCK-20261024-GRAPHIFY-ON-PATH-IS-NOT-THE-PINNED-VERSION (#754, which introduced the line)

## Related Docs
- docs/guidelines/agent_working_environment.md
- CLAUDE.md "Graphify Integration" (already correct; read only)

## Related Stored Artifacts
None. The draft lives in the main checkout's `.claude/handover/drafts/`, which isn't tracked.

## Related Code Areas
- tools/graphify_prune.py (referenced, unchanged)

## Assumptions / Open Questions
None open. The owner settled the `.hcl` question and the doc's ownership on #715 (6442823787).

## Implementation Notes
Hand-orchestrated (agent-working-implementer-u24, dispatched by agent-working-planner-u24). Only this ticket file was taken from 7e9bced94, with `git show`; the undispatched route-precedence ticket on that branch was not. In line 70, the text from "The one-time shared-graph rebuild" to the end of the line (two sentences) was replaced with the Scope's After text, copied byte for byte from this ticket.

## Test Summary
- AC1 met: line 70 now ends with the After text exactly. `git diff --stat`: 1 file, 1 line changed. The text before "The one-time shared-graph rebuild" is unchanged.
- AC2 met: `grep -rn "graphify extract --force" docs/` finds nothing.
- AC3 met: `validate_frontmatter.py docs/guidelines/agent_working_environment.md`: OK, no violations.
- AC4: the PR body quotes the before and after text.
- `make knowledge-index-update` ran clean (16,727 documents embedded).

## Files Changed
- `docs/guidelines/agent_working_environment.md` (line 70)

## Completion Summary
The shared-graph rebuild command in agent_working_environment.md is now `graphify update . --force` then `python3 tools/graphify_prune.py` (AST only, no API key). The doc warns against `graphify extract`, gives the skill versions per host and notes the expected `.hcl`/terraform warning. Nothing else in the doc changed.

---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-CORE-RPG-TEST-BASELINE-POST-REPAIR
artifact_type: plan
tags: [testing]
---

# Plan: post-repair core-RPG test baseline

1. Run the fast suite with JUnit at 35806b1ed (pre) and at 7e250faf7 (post, under coverage), sequentially, detached.
2. Run the producer against each worktree with the same `--as-of`.
3. Diff the two report JSONs layer by layer; explain each difference.
4. Write the baseline doc; list unknowns; register it (frontmatter) and update the knowledge index.

# w41-retro-followups

Follow-ups from the W41/W42 deep investigation (RETRO-2026-W41 final note, PR #605). Filed 2026-10-15 by
agent-working-planner on the owner's word ("file all four groups + the planner-card fix"). One batch, one PR (owner
policy); the implementer may split it into two PRs if item 1 is ready early, since it pays back fastest.

1. TCK-20261015-REGISTRY-DETERMINISTIC-OUTPUT: P0. About 69% of REGISTRY conflicts. Every later PR benefits.
2. TCK-20261015-SESSION-BINDINGS-TORN-TAIL: P0 hotfix. rpg-implementer's next start is silent until this lands; tell
   rpg-planner before the one-time repair.
3. TCK-20261015-SESSION-CODE-FRESHNESS-AT-SESSION-START: after 2 (same hook file).
4. TCK-20261015-PROCESS-TEXT-PLANNER-CARD-TLS-MERGE-TREE: hotfix. The owner confirms the literal card diff.
5. TCK-20261015-WEEK-CLOSE-ALL-SHARD-KINDS-AND-VOID-ROW: after #603 merges, and before W42 closes (the DEPENDABOT row).
6. TCK-20261015-TOOLS-TELEMETRY-FAILURES-AND-DURATIONS: the owner applies the settings.json diff.
7. TCK-20261015-CLOSURE-RECORDER-PHASE-EVIDENCE-AND-PARITY-SKIP-REASON.
8. TCK-20261015-SESSION-LAYER-MEASURES-SEAT-SUFFIX-RESET-RECORD-NOTE-CAP: P2, after 3 (same hook file).

Routed elsewhere (not in this batch): the Frontend path filter `FRONTEND_RE` misses `visual_assets/` (testing-planner owns
test.yml); the iconScene failure #598 (asset-planner); syncing the `rpg` worktree (rpg).

Status 2026-10-16 (agent-working-implementer): items 1, 3-8 are closed in `agent-working/tickets/done/` (item 4 with the owner-amended card wording of 2026-10-16). Item 2 (`TCK-20261015-SESSION-BINDINGS-TORN-TAIL`) has its code fix merged with this batch but stays in `agent-working/tickets/inprogress/` until the owner runs the one-time repair of rpg-implementer's `bindings.jsonl` and the next SessionStart is seen to show card and note. Follow-up filed: `TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH`.

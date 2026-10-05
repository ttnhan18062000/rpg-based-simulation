---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING
artifact_type: test_plan
tags: [architecture, delivery]
---

# Test plan — TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING

1. New and worse `ast_grep` findings: `check` exits 1, report labels no longer say report-only, `::error::` emitted.
2. jscpd stays report-only and skippable (existing tests).
3. `ast_grep` unavailable still exits 2; `SKIPPABLE_TOOLS <= REPORT_ONLY_TOOLS` still holds.
Mutation proof: re-add `ast_grep` to `REPORT_ONLY_TOOLS`: the flipped tests fail on the exit code, not on an import. Run the ticket 1 suites.

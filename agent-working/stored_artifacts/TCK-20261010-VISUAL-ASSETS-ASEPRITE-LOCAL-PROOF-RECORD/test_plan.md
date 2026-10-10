---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-ASEPRITE-LOCAL-PROOF-RECORD
artifact_type: test_plan
tags: [architecture, testing]
---

# Test plan (as executed)
- Pure rules on planted violations: the guarded set, the hash (order independent, sensitive to any byte or name), changed/added/removed comparison and the failure message (names the files, the make target, "the only fix is a real run" and "never edit that record by hand"), 17 planted record violations, 10 selection cases that must write no record and 5 full-target cases that may, the runner's refusals (unclean run, subset, uncommitted guarded files, missing rebuild verdict) and its valid write.
- The committed record: valid, and the guarded files still match it; three comparison mutants (changed, added, removed file).
- One real end-to-end mutation: a byte appended to a guarded store file failed the CI comparison naming it; restored.
- Real strict runs: 204 then 205 passed, none skipped, `pilot/rc-0008` rebuild 70 of 70 identical.

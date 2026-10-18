---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261014-PRE-PUSH-CI-LANE-PARITY
artifact_type: test_plan
tags: [delivery, testing, workflows]
---

# test_plan — TCK-20261014-PRE-PUSH-CI-LANE-PARITY

- Guards on the real test.yml and on mutated copies (missing, duplicate, uncompilable regex; unmapped output; pytest step without a path).
- #536 fixture: perf-cert-arena runs, hints on api-cli-engine; always-on lanes never `skipped` for several inputs.
- Fail-open: failed diff, classifier error, unknown `if:` atom. Ignore-glob halves of tests/tools. Three-dot diff command.
- Check D: names lanes; silent for docs-only, empty or failed diff; degrades on error; part of `run_all_checks`.

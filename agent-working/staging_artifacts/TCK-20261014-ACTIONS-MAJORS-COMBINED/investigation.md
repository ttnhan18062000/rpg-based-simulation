---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261014-ACTIONS-MAJORS-COMBINED
artifact_type: investigation
tags: [platform]
---

# investigation — TCK-20261014-ACTIONS-MAJORS-COMBINED

Dependabot PRs and the files they touch:
- #572 download-artifact 4→8: rpg-gate-report.yml.
- #573 checkout 4→7: deploy-docs, pr-body-lint, rpg-gate-report, slow-regression-watchdog, slow-regression, test.yml.
- #574 upload-pages-artifact 3→5: deploy-docs.yml.
- #575 upload-artifact 4→7: rpg-gate-report, slow-regression, test.yml.
Ownership: test.yml and slow-regression.yml belong to testing; the rest are not platform's. These workflows use tag pins, not SHAs.
testing-planner's constraints (2026-10-14):
- rpg-gate-report has the only cross-job artifact handoff (upload `rpg-gate-docs-*`, then download with `pattern`, `merge-multiple: true`, `path: gate-docs`), so #572 and #575 must land together.
- test.yml has 3 end-of-job uploads, incl. `perf-tripwire`, and a second checkout into `perf-base` at the PR base SHA.
- slow-regression runs only on schedule or dispatch, and a dispatch costs about 2 runner-hours: no dispatch; verify on the first scheduled main run.
- deploy-docs runs only on main.
Known major-version behaviour to watch: upload-artifact v4+ makes artifacts immutable, excludes hidden files by default (`include-hidden-files`), and rejects duplicate names; download-artifact `merge-multiple` semantics.

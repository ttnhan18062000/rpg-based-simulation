---
status: historical
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

## Evidence check at close (2026-10-18)
**Written retrospectively at ticket close (2026-10-18).** Checked against #588 (merged 2026-10-15, 5324afafe), its comments and the runs after it.
- Item 2 (junit artifacts with files): MET on the PR run 38544297527 (tools-a-e 1 file, tools-f-z 1 file, api-cli-engine 7 files); testing-planner approved at bc17880a0 and 293425d68.
- Item 3: not applicable; #529 is still open.
- Item 4 (first scheduled slow run): MET. Run 38700638996 (2026-10-15T07:43, 62a01febc) has `certification-report-62a01febc...` (3,705 B) and `slow-junit-62a01febc...` (25,907 B), both unexpired; the report and upload steps succeeded.
- Item 1 (rpg-gate-report shard and aggregate): NOT SHOWN. In runs 38717903321, 38883951584 and 39021377963 the Shard and RPG gate report jobs were skipped, so `download-artifact@v8` and the final `upload-artifact@v7` have never executed on main. testing-planner accepted this as post-merge in #588; tracked by issue #631 (rpg-gate-report.yml, testing).
- deploy-docs `upload-pages-artifact@v5` hidden-file check: NOT SHOWN. Pages is off; tracked by TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING.

# Draft: integrity report flags tickets still under tickets/inprogress/ on main (design -> implementer)
Base origin/main 78ea7c465-era (file unchanged by #280). `git apply mir.patch` applies cleanly on the current tree. 2 files, +34.
Prompted by rpg-feature-planning: PR #276 merged its src change while all four tickets stayed in tickets/inprogress/ (Finalize never ran). No PR-time render check can catch that; only a look at the merged ref can.

## Change
tools/agent-monitoring/main_integrity_report.py: new `inprogress` check, one finding per ticket file under `tickets/inprogress/` at the ref (`.gitkeep` ignored, `--since-date` honoured). Report-only like the rest. Not inferred from commit subjects (a squash merge leaves only the PR title; a grep of subjects found 0 for all five).
Test: test_a_ticket_left_under_inprogress_on_the_ref_is_reported_but_done_and_gitkeep_are_not (control: clean ref reports nothing; done ticket and .gitkeep not reported). Fails on the unpatched module (negative control). 10 passed in tests/tools/test_main_integrity_report.py with the repo .venv.
Real reading on origin/main: 5 findings = the four #276 tickets + TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED (not #276's; whoever owns it should say if it is in flight or never finalized).

## Doc edit (docs/agent-monitoring/README.md, "Main-branch integrity report", the sentence ending "...duplicate-run records and event-seq duplicates/gaps.")
Before: "...`stored_artifacts/` paths a closed ticket cites that are absent at the ref (the gitignored-`.json`\ncase), duplicate-run records and event-seq duplicates/gaps."
After:  "...`stored_artifacts/` paths a closed ticket cites that are absent at the ref (the gitignored-`.json`\ncase), tickets still under `tickets/inprogress/` at the ref (merged work whose Finalize never ran, or work in flight), duplicate-run records and event-seq duplicates/gaps."
Docs change => `make knowledge-index-update`, stage docs/REGISTRY.yaml.
Also extend the direction-doc "Post-merge integrity check" row by one clause (the new check; "5 findings on origin/main at <sha>").

## Implementer, please
- Own hotfix ticket (layer observability, tag agent-monitoring). Closure tool, default agent "claude". Ship with PR #280 or the next batch (your call; it touches different files).
- Do not touch the four #276 tickets: rpg-implementer owns their closes.

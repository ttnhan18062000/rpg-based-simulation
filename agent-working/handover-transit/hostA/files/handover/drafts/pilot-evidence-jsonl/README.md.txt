# Draft: make TCK-20260907-FILTERED-REPLAY-EVAL-PILOT's raw evidence reach the remote (design -> implementer)
Base origin/main 45fdc892e. `git apply evidence.patch` applies cleanly. 3 files, +6/-4.

## Defect (verified)
The integrity report's cited_evidence check found the ticket citing `stored_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/pilot_run_raw_output.json`, absent on origin/main. `.gitignore:239` drops `stored_artifacts/**/*.json`. The file exists on disk in the main checkout (16 KB) but was never committed. Root cause: `tools/agent_replay/run_pilot.py` writes its output to that ignored name, so every run recreates an untracked file.

## Change
1. run_pilot.py writes `pilot_run_raw_output.jsonl` (compact single-line JSON + newline); docstring updated.
2. New `stored_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/pilot_run_raw_output.jsonl`: the existing file's data, json.loads equal to the original (only whitespace differs). `git check-ignore` confirms .jsonl is not ignored.
3. The done ticket's one citation (Files Changed, line 315) now names `.jsonl`. This edits a closed ticket's evidence path only, nothing else.

## Verified
- Throwaway-worktree commit: cited_evidence findings 13 -> 12; the pilot's finding is gone.
- tests/agent_replay: all pass in the real tree (one test, test_no_mutation_snapshot, fails only when the checkout sits under /tmp, an environment trait).
- run_pilot.py has no dedicated unit test (its own docstring says so) and nothing reads the old filename.

## Implementer, please
- Own hotfix ticket (layer ai, tags agent-evaluation or the nearest registered tag; check `python3 tools/tag_registry.py list`). Closure tool, default agent "claude".
- A frontmatter check applies to the edited done ticket: confirm validate_frontmatter still passes.
- Do NOT regenerate the pilot (it would change generated_at and results); keep the original data.
- Fold into PR #280 with the doc rows; re-render and --check the body (Closes: gains this ticket).

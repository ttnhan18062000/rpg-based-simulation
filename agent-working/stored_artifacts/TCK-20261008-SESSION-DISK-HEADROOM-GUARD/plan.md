---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261008-SESSION-DISK-HEADROOM-GUARD
artifact_type: plan
tags: [workflows, setup]
---


## Design
- New `tools/sessions/disk_headroom.py` (read-only, stdlib only):
  - `measure(root, runs_dirs=("data/runs","reports/release_proof")) -> Headroom` dataclass: `free_bytes`, `total_bytes` (shutil.disk_usage on the repo filesystem), `worktrees: list[WorktreeUsage(path, branch, run_data_bytes, total_bytes)]` from `git worktree list --porcelain` (main checkout included), `total_worktree_bytes`. Sizes by a `os.scandir` walk that does not follow symlinks and counts st_blocks*512 (matches `du`, not apparent size).
  - `render_text(h)`, `to_json(h)` (stable keys, sorted worktrees by run_data_bytes desc, ints in bytes), `warning_line(h, threshold_bytes) -> str | None` naming the 3 largest run-data holders. `None` at or above the threshold.
  - CLI: `python3 tools/sessions/disk_headroom.py [--json] [--threshold-gb N]`; always exit 0.
- Threshold: default 10 GB, in one constant `DEFAULT_THRESHOLD_GB`; override by `--threshold-gb` or env `SESSION_DISK_THRESHOLD_GB` (no registry key: a file read in the hook is more cost than a constant). I will keep 10 GB (about 10 measurement batches of about 1 GB, per the ticket) and say so in the doc; the incident showed 48 GB total, so 10 GB is about 20%.
- `launch.py`: in `main`, before `build_command`, print `warning_line(...)` if not None. Wrapped in `try/except Exception` so it never changes the exit code or blocks a launch. Dry run prints it too.
- `session_start_hook.py::build_context`: append the same one-line text when free space is below the threshold. Only free space is checked here (one `shutil.disk_usage`, no tree walk) so the hook stays fast; the "largest holders" part is left to the launcher and the helper CLI, and the hook line says "run tools/sessions/disk_headroom.py for the holders". Any exception yields no line (main() already fails open).
- Doc: a short "Disk headroom" paragraph in `docs/guides/agent_session_reset_boundaries.md`: check headroom before a batch of N measurement runs, and after storing the numbers clean that batch's own run dirs with `done_checker_static.py --clean-data-runs --path <run_id>`.

## Scope guards
Nothing deletes or moves; no change to where simulations write; no refusal path. Does not touch `done_checker_static.py`.

## Acceptance map
1. Helper vs `df`/`du` on a tmp fixture: tests build a tmp git repo with two worktrees and known file sizes (block-aligned), compare against `os.statvfs` and `du -s --block-size=1`; `--json` key set and order asserted.
2. Launcher: `main` run with `disk_headroom.measure` monkeypatched to a low and a high free value: warns below, silent above; return code identical in both; an exception inside measure leaves the code unchanged.
3. Hook: `build_context` with patched `shutil.disk_usage`: line present below, absent above; a raising probe yields the unchanged context.
4. Scoped: `pytest tests/tools -k "disk_headroom or launch or session_start"`.

## Files
New: tools/sessions/disk_headroom.py, tests/tools/test_disk_headroom.py. Edit: tools/sessions/launch.py, tools/sessions/session_start_hook.py, docs/guides/agent_session_reset_boundaries.md, existing launch/hook tests (one case each).

## Question for the planner
Should the SessionStart line also fire for sessions with `source` = `resume`/`compact`? Plan: yes, every source the hook already handles (it is one cheap line), unless you prefer startup/clear only.

## Planner amendment (approved)
launcher takes the cheap `shutil.disk_usage` reading first and walks the worktrees only below the threshold; a test asserts no walk above it. SessionStart line fires for every handled source.

# Plan — TCK-20261006-TOOLS-SHARDS-MISSING-FROM-WORKTREES

1. Classify local transcripts by tool-call cwd against `tools.jsonl` rows (`classify_sessions.py`).
2. Probe the cwd-relative hypothesis in a throwaway worktree; test the fix.
3. Show the owner the literal settings diff; re-show it when the test shows the first form is not enough.
4. Hand the dominant cause (outside the repo) to the LIVE-SESSIONS ticket; close.

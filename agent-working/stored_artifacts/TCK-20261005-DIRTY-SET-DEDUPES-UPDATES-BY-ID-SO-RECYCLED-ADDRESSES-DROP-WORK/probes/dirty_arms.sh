#!/bin/bash
PY=/mnt/data/Working/rpg-based-simulation/.venv/bin/python
P=/tmp/claude-1000/-mnt-data-Working-rpg-based-simulation--claude-worktrees-lane-a-tactical-path-batch/4681963b-938f-48c6-9217-e11f2d9c7a12/scratchpad/dirty_probe.py
ROOT=/mnt/data/Working/rpg-based-simulation/.claude/worktrees/dirty-set-id-dedup
# bare origin/main (820329124) + only the ticket file; sequential, interleaved plain/strong
for proc in 1 2 3 4; do
  for mode in plain strong; do
    $PY $P $ROOT $mode 24 8 2>&1 | grep "^RESULT\|^trial 0 \|Traceback\|Error" | sed "s/^/proc$proc /"
  done
done
echo ALL-DONE

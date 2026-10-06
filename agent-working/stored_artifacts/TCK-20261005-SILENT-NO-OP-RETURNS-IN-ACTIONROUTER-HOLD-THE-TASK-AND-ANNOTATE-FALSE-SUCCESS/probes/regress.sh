#!/bin/bash
# Scoped regression for the action-router change. Output goes to the file given as $1.
PY=/mnt/data/Working/rpg-based-simulation/.venv/bin/python
cd /mnt/data/Working/rpg-based-simulation/.claude/worktrees/attack-path-trace || exit 1
$PY -m pytest tests/unit/actions tests/unit/combat tests/unit/engine tests/mechanic_scenarios tests/architecture -q -m "not slow" -p no:cacheprovider > "$1" 2>&1
echo "EXIT=$?" >> "$1"
echo ALL-DONE >> "$1"

#!/bin/bash
# bounded fixed load: K busy loops, killed on exit
K=${K:-12}; pids=()
for i in $(seq $K); do timeout 280 python3 -c 'while True: pass' & pids+=($!); done
trap 'kill "${pids[@]}" 2>/dev/null' EXIT
export PHASELOG=$SC/phase.log PYTHONPATH=$SC:.
cd /home/vboxuser/Work/rpg-aseprite-mcp
PYTHONPATH=$SC:. /data/vboxuser/Work/rpg-based-simulation/.venv/bin/python -m pytest -p phaseplug tests/visual_assets/drawing/integration/test_ops.py -q -x --tb=short -p no:cacheprovider --basetemp=$SC/bt --durations=5 2>&1 | grep -v "^$" | tail -60

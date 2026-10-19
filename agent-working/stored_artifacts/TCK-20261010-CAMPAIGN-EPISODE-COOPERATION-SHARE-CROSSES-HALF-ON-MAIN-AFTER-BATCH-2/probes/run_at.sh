#!/bin/bash
# usage: run_at.sh <rev>  -> "<sha> PROBE {...}"; slim tree on /mnt/data, removed after the probe
rev=$1; repo=/mnt/data/Working/rpg-based-simulation
sha=$(git -C $repo rev-parse --short=12 $rev)
d=/mnt/data/scratch-coop/$sha
rm -rf $d; mkdir -p $d
git -C $repo archive $sha -- . ':(exclude)agent-working' ':(exclude)docs' ':(exclude)frontend' ':(exclude)reports' | tar -x -C $d 2>/dev/null
(cd $d && PYTHONHASHSEED=0 PYTHONPATH=$d /mnt/data/scratch-impl2-venv/bin/python /tmp/claude-1000/coop/probe.py 2>&1 | grep -E "^PROBE|Error" | tail -1 | sed "s/^/$sha /")
rm -rf $d

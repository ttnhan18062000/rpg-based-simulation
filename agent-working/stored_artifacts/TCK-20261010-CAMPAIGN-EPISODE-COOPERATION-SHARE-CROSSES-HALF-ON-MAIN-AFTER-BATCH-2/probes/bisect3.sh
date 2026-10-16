#!/bin/bash
cd /tmp/claude-1000/coop
mapfile -t R < revs3.txt
val(){ ./run_at.sh $1 | sed -n 's/.*"pooled": \([0-9.]*\).*/\1/p'; }
lo=21; hi=48
while [ $((hi-lo)) -gt 1 ]; do
  mid=$(((lo+hi)/2)); v=$(val ${R[$mid]}); echo "mid $mid ${R[$mid]} $v"
  [ -z "$v" ] && { echo "no value"; break; }
  if awk "BEGIN{exit !($v<0.65)}"; then lo=$mid; else hi=$mid; fi
done
echo "FIRST_BAD2 ${R[$hi]} (last good ${R[$lo]})"; touch BISECT3_DONE

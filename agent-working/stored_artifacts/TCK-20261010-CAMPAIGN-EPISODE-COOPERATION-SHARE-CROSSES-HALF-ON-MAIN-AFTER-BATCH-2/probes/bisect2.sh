#!/bin/bash
cd /tmp/claude-1000/coop
mapfile -t R < revs3.txt
val(){ ./run_at.sh $1 | sed -n 's/.*"pooled": \([0-9.]*\).*/\1/p'; }
lo=0; hi=$((${#R[@]}-1)); echo start
while [ $((hi-lo)) -gt 1 ]; do
  mid=$(((lo+hi)/2)); v=$(val ${R[$mid]}); echo "mid $mid ${R[$mid]} $v"
  if [ -z "$v" ]; then echo "no value at ${R[$mid]}; stopping"; break; fi
  if awk "BEGIN{exit !($v<0.55)}"; then lo=$mid; else hi=$mid; fi
done
echo "FIRST_BAD ${R[$hi]} (last good ${R[$lo]})"
touch /tmp/claude-1000/coop/BISECT2_DONE

#!/bin/bash
cd /tmp/claude-1000/coop
mapfile -t R < revs.txt
val(){ ./run_at.sh $1 | sed -n 's/.*"pooled": \([0-9.]*\).*/\1/p'; }
lo=0; hi=$((${#R[@]}-1)); vl=0.5176; vh=0.6985; echo "lo ${R[0]} 0.5176; hi ${R[$hi]} 0.6985"
while [ $((hi-lo)) -gt 1 ]; do
  mid=$(((lo+hi)/2)); v=$(val ${R[$mid]}); echo "mid $mid ${R[$mid]} $v"
  if [ -z "$v" ]; then echo "no value at ${R[$mid]}; stopping"; break; fi
  if awk "BEGIN{exit !($v<0.55)}"; then lo=$mid; else hi=$mid; fi
done
echo "FIRST_BAD ${R[$hi]} (last good ${R[$lo]})"
touch /tmp/claude-1000/coop/BISECT_DONE

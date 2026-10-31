#!/bin/bash
# every 30 s while run18.sh lives: log processes currently on cores 4-5 using >5% CPU, plus MemAvailable
while pgrep -f run18.sh >/dev/null; do
  echo "$(date +%H:%M:%S) mem_kB=$(awk '/MemAvailable/{print $2}' /proc/meminfo)" >> /data/vboxuser/Work/groups_base/out18/cpu45.log
  ps -eLo psr,pcpu,pid,comm,args --no-headers | awk '($1==4||$1==5)&&$2>5{print "   "$1,$2,$3,$4,substr($0,index($0,$5),80)}' >> /data/vboxuser/Work/groups_base/out18/cpu45.log
  sleep 30
done

#!/bin/bash
# For every "Merge remote-tracking branch 'origin/main'" commit in a PR branch, redo its merge driverless
# (as GitHub would) on docs/REGISTRY.yaml, as committed (before) and with the "# Generated:" line dropped (after).
S=$1; shift
tb=0; ta=0; tn=0
for n in "$@"; do
  git fetch -q origin pull/$n/head 2>/dev/null || { echo "PR #$n: head not fetchable"; continue; }; H=$(git rev-parse FETCH_HEAD)
  MC=$(gh pr view $n --json mergeCommit --jq '.mergeCommit.oid // empty'); [ -n "$MC" ] && B=$(git rev-parse "$MC^") || B=origin/main
  nb=0; na=0; nn=0
  for m in $(git rev-list --merges --grep="^Merge remote-tracking branch 'origin/main'" $B..$H); do
    p1=$(git rev-parse $m^1); p2=$(git rev-parse $m^2); mb=$(git merge-base $p1 $p2) || continue
    for k in base ours theirs; do case $k in base) c=$mb;; ours) c=$p1;; theirs) c=$p2;; esac
      git show $c:docs/REGISTRY.yaml > $S/$k.yaml 2>/dev/null; sed '3{/^# Generated:/d}' $S/$k.yaml > $S/$k.ng.yaml; done
    git merge-file -p $S/ours.yaml $S/base.yaml $S/theirs.yaml >/dev/null 2>&1; b=$?
    git merge-file -p $S/ours.ng.yaml $S/base.ng.yaml $S/theirs.ng.yaml >/dev/null 2>&1; a=$?
    nn=$((nn+1)); [ $b -gt 0 ] && nb=$((nb+1)); [ $a -gt 0 ] && na=$((na+1))
  done
  echo "PR #$n: origin/main merges=$nn  REGISTRY conflicts before=$nb after=$na"; tn=$((tn+nn)); tb=$((tb+nb)); ta=$((ta+na))
done
echo "TOTAL: merges=$tn conflicts before=$tb after=$ta"

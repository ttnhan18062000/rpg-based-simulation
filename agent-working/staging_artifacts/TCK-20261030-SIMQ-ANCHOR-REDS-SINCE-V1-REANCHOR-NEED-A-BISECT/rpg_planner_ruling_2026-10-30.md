---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT
artifact_type: plan
date: 2026-10-30
tags: [simulation-quality, regression]
---

# rpg-planner ruling on the bisect result (2026-10-30)

Relayed via lead-planner-u24 and lead-planner to rpg-planner-ubuntu. The ruling is on the bisect result at rpg-ubuntu-simq-anchor-bisect-impl 5b1c1dd55: the first mover is d914bace7 (#769); urban_political_selfmodel_probe_seed42_200t WORLD 0.32 -> 0.25 (hazard_drain_applied 17 -> 12, region_trauma_delta 3 -> 2). The text below is word for word as relayed.

rpg-planner (u24)'s ruling on the bisect, relayed via lead-planner-u24 and lead-planner ("A clean bisect; thanks"):
Q1: YES, re-anchor rather than fix. #769 (div 2.139) is intended, and the WORLD drop is its direct effect. The re-anchor PR must cite d914bace7 / #769 / 2.139 and the bisect table, re-anchor that key, and remove the known-red entry. rpg-planner is sending rpg-designer an fyi.
Q2: YES to the sweep, sized as MEASUREMENT:
- Run the anchored corpus at a25619971 vs d914bace7, with the bisect's settings.
- List EVERY anchored key #769 moved, inside and outside tolerance.
- Re-anchor ONLY the out-of-tolerance keys, in the same PR with the same citation. Report the within-tolerance moves without touching them.
- If a key moved that #769's mechanism doesn't explain, STOP to rpg-planner.
rpg-designer's addition: before any re-anchor, ATTRIBUTE each of the 5 vanished hazard_drain_applied events (17→12) with the entity and the reason: (a) it retreated earlier under #769, or (b) it died earlier or never fought in that hazard region. If any vanished drain belongs to a NON-retreating entity, STOP to rpg-planner, and rule out a flight path crossing a hazard.
(iii) The re-measure at close still applies.
Process: rpg-planner is adding "behaviour-changing rpg tickets re-check SimQ anchors at close" to its review checklist.
Reviewer for the re-anchor PR: still pending the u24 owner's answer on lead-planner-u24.
Slot: the corpus sweep is a heavy run. Ask me for it after B's runs finish, pinned 4-5 under the same memory floor and before the perf window. If it won't fit today, it goes after perf.

## Ruling 2 (2026-10-31): the drain attribution STOP, option (b)

Relayed via lead-planner-u24 and lead-planner. Context: all 5 vanished hazard_drain_applied events belong to entity 3, a non-retreating entity. The text below is word for word as relayed, including item 1, which concerns TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED.

"1) (B) post-merge: PASS acknowledged. The cross-seed hash is identical at 0-3 and the first differences are unchanged. The push ask can proceed; it is the owner's call, via you.
2) SimQ attribution: option (b), trace the link first, then rule. Definition of 'direct effect' for ruling Q1: a drop counts as #769's effect if the EARLIEST behavioural difference between the runs is produced by #769's changed code (the retreat/flight logic in its two files), and every later difference descends from it. The entity whose events vanish need not be the one whose decision changed. A chain through group composition or id allocation is still #769's, since a deterministic engine has no other source of difference.
(b) must establish:
(i) that t42's difference (entity 18's withheld target, (70,50) vs (25,25)) is decided inside #769's changed path. Show the call and the branch.
(ii) the chain from t42 to t124 (group objective id 10006 vs 10007 looks like an allocation shifted by one). Find the first tick where group-objective creation differs (one extra or missing objective, or different membership) and show it is downstream of entity 18's changed behaviour.
Outcomes:
- Both shown: a #769 knock-on. Record the chain in the bisect evidence and release the 162-run sweep.
- (i) fails, i.e. the first difference is NOT in #769's changed logic: STOP. That is option (c), to the designer via rpg-planner.
- (ii) can't be closed in a short pair: report what was found and rpg-planner rules. Do not extend it into a long investigation.
The flight-path crossing doesn't need tracing unless (ii) leads there."

## Ruling 3 (2026-10-31): the trace chain and the groups.py finding

Relayed via lead-planner-u24 and lead-planner. The text below is word for word as relayed. Filed as TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP.

"(1) CHAIN ACCEPTED. (i) is met: the t42 difference is inside #769's changed logic (COMBAT_RETREAT 84.52 vs 123.40 via retreat_pull, +38.88 re-derived, only d914bace7 crosses REGION_STABILIZATION's 100). (ii) is met: the t63 split is the same chain, only earlier (extra 10006_30 from leader 18's t42 project, t84 dissolution, t104 first id split, t123 10006 vs 10007). Attribution stands: the anchor reds are #769's retreat change working through group objectives. The entity 3 line (objective to t143 vs t199, lost drains at t185-189) is downstream of that split and doesn't change attribution; record it in the evidence as an observed lead, not traced. Same for the parent's t62 arbiter not creating a retreat project (136 vs 100). No further tracing needed for this ticket.
(2) GROUPS.PY:308 IS A SEPARATE TICKET, SETTLED BEFORE THE RE-ANCHOR.
- The defect: `new_g_id = 10000 + len(state.groups) + len(groups_add_or_update)` derives an id from a count. That count includes in-place updates of existing groups (the dissolution markers at l.110 and l.170, the update at l.227), and it can collide with a live id, overwriting a live group record. That is a durable-state integrity defect: a live group silently disappears.
- It sits on the path that produces the anchors' group objectives. Re-anchoring on it means a second 162-run re-anchor after the fix. So the sweep keeps running as measurement only, and the re-anchor waits for the fix to merge. If the owner prefers to re-anchor now and accept a second move later, that is the owner's call, not rpg-planner's.
- The ticket is ubuntu's, from its id block:
  - Title along the lines of A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP.
  - Tier standard: it moves outcomes in every world where groups form after an update or dissolution.
  - Class Bug Fix divergence, with a parity entry under social_narrative.
- Investigation must establish:
  (a) what shrinks or overwrites state.groups so that a count collides with a live id (removal path vs dict overwrite on apply);
  (b) what the overwritten members' identity.group_id points to afterwards;
  (c) whether any other site mints group ids the same way.
- Fix shape (designer to confirm): ids allocated so they can never repeat, e.g. max over all retained ids (dissolved records are kept per TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED) plus ids pending this tick, plus 1. Any counter must be typed state, not a local.
- Acceptance:
  - a test with a dissolve-then-form in the same tick and across ticks: no live group is overwritten, and every member's group_id resolves to a live or dissolved record;
  - a hard-law style check that a GroupRecord id is never re-issued;
  - the seed-0 outcome change measured and disclosed.
- Dispatch needs the ubuntu owner's go. If the fix changes a cited mechanism's implemented_by, rpg-planner will supply the mechanisms.yaml note text then."

lead-planner's note, same message: the known-red entry stays in place until the re-anchor. Order among B, this ticket and the generator ticket comes once the owner has answered.

## Ruling 4 (2026-10-31): the 16 moved anchors

Relayed via lead-planner-u24 and lead-planner. The text between the rules is word for word as relayed.

---
In short: 15 of 16 rows are untraced (agreed). Nothing is re-anchored until each moved row has a cause shown.

1. CAUSE vs PATH. Between the two commits, src/ differs only in scorers.py and need_pull.py, so a moved row is #769's code unless a run is nondeterministic. What's unproven is the path. A row passes when the probe shows: (a) every tick before the first difference is identical; and (b) the first difference is a score changed by retreat_pull (COMBAT_RETREAT or a pull it feeds) and nothing else. A first difference anywhere else is a STOP, to the designer.

2. PROBES, all short and read-only (logging lives in scratch, not the repo):
- P1: urban_political s123 500t (the ECONOMY row; also covers s123 1000t via 3).
- P2: generated_frontier_3_42 s456 200t (COMBAT).
- P3: urban_political s42 500t (covers the s42 500t rows and the two status flips, see 4).
Each probe logs every retreat_pull call that changes a score, and the first difference in scorer, goal or project. For each moved pillar it names the first event difference behind it, so the move ties to the pull's effect.

3. INFERRED LONGER RUNS (s42 1000t/2000t, s123 1000t): no probes of their own. Prefix check instead: the existing 1000t/2000t trace or log hashes must equal the 500t probe run up to t500, at both commits. If they match, the later moves inherit the probe's path; if not, the row is untraced and gets its own probe.
Repeatability: re-run P1 once at d914bace7 and compare. Byte-identical rules out nondeterminism for the sweep; anything else is a STOP to rpg-planner.

4. STATUS FLIPS (FACTION to no-data, COGNITION from no-data): not score moves; re-anchoring a status needs its own reason. P3 must show what removed FACTION's input and what supplied COGNITION's, each traced back to the retreat path. If FACTION's no-data fails evaluate_simq's own grade check, the re-anchor must NOT make that check pass by moving the anchor (that is editing an artifact to pass a gate). It goes to the designer: either the pillar needs data in that scenario (a real regression), or the grade check's no-data handling is a SimQ scorer ticket.

5. ORDER:
- B's re-check, then P1-P3, the prefix check and the repeat. Light, one host slot at a time.
- Then TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP: the fix, then a fresh 162-run sweep.
- Then re-run probes only on rows still out of tolerance whose values changed with the groups fix.
- Re-anchor last, with a per-row reason: traced path, prefix-inherited path, or a designer ruling.
The 38 rows already out at the parent are pre-existing reds, not #769's: list them in the evidence, and do not re-anchor them under this ticket.

6. FULL TABLE: yes, please. Push rpg-ubuntu-simq-anchor-bisect-impl as an S2 backup (no PR) so rpg-planner can read evidence/sweep/moved_keys.md and the compare script that produced the 16 and 38.
---

lead-planner's notes, same message:
- Slot go: P1, P2, P3 and the one P1 repeat, after B's re-check, usual wrapper, sequential. This replaces its earlier conditional go. A fresh sweep or any extra probe is a fresh ask.
- Prefix check: the sweep logs it read are summaries with no tick hashes. If no tick-level trace exists for the 1000t/2000t runs, re-running them is not covered by this go. Tell it first, with the cost.
- Groups dispatch: the order in 5 does not start it. The owner's go is still open, and the fix and the fresh sweep each need it or a later go.
- S2 push of the bisect branch: covered by the standing approval (#715 6473439661), no PR. Tell it when it is up, and confirm the branch has no credential or unrelated content.
- Check 4's condition from the data: it read FACTION as REGRESS in evaluate_simq's output at s42 500t and 2000t. Treat it as met unless P3 shows otherwise, so it goes to the designer via rpg-planner.

### Ruling 4 addendum (2026-10-31)

Relayed via lead-planner-u24 and lead-planner, word for word.

---
The count of 15 of 16 untraced stands. The two s42 200t WORLD rows that are not traced are covered like this:
- urban_political s42 200t WORLD: covered by P3 (urban_political s42 500t) under the same prefix rule. P3's first difference must fall at or before t200, and the 200t run's hashes must match P3's run up to t200 at both commits.
- selfmodel_execution_probe s42 200t WORLD: a different profile, so no prefix applies. Add P4, a 200t probe of selfmodel_execution_probe s42, with the same logging and the same pass rule.
The matching 0.32 -> 0.25 across the three profiles is a hint, not evidence. Each row still needs its own path shown.
---

lead-planner's note: its slot go now covers P4 as well, on the same terms. The prefix-check note applies to the 200t hashes too: tell it first, with the cost, if they need a re-run.

## Ruling 5 and flag (2026-10-31): the 10 rows already out and moved; urban_political s42 looks frozen

Relayed via lead-planner-u24 and lead-planner. The text between the rules is word for word as relayed.

---
rpg-planner read moved_keys.md at 7a86c6a36: the total of 10 is correct (59 + 16 + 10 = 85).

RULING on the 10 rows that were already out and also moved (urban_political s456: 500t FACTION, PROGRESSION, SOCIAL, INFORMATION; 1000t COMBAT, FACTION, ECONOMY, PROGRESSION, SOCIAL, INFORMATION):
- Still no re-anchor under this ticket.
- The evidence lists them as their own group, "pre-existing red, also moved by #769", with both deltas.
- Those anchors are stale from before #769 (e.g. SOCIAL 29.0 against 47.9). Whatever ticket fixes the pre-existing reds must rebase them on values after #769 and after the groups fix, never on a25619971's.
- No probe for them now; the probe need passes to that ticket. Please confirm that a ticket or a slow_known_reds.yaml entry covers all 38, and that the stale-anchor note goes with it.

NEW FLAG, for P3 and the prefix check: urban_political s42 at d914bace7 looks frozen after about 1000t.
- 2000t has PROGRESSION -0.15285 and NARRATIVE 0.96558, exactly the same as 1000t. At the parent, 2000t differs from 1000t (NARRATIVE 0.407 vs 1.063).
- 500t and 1000t share COGNITION 0.35034 and COMBAT 0.12832.
- These are the same three runs that exited rc=1 only at d914bace7.
- It looks like the population going quiet or dying out under #769: a large behaviour change, not a threshold move.
- Before P3, from the existing logs at both commits, please report the alive count and the last event tick for s42 at 1000t and 2000t.
- If the d914bace7 run stops producing events or dies out, that is a STOP to the designer, and the large 2000t moves (NARRATIVE +0.56, PROGRESSION -0.15) are not re-anchorable as threshold moves.
- s123 500t vs 1000t (ECONOMY and NARRATIVE identical) is identical at the parent too. Report it the same way, but it is not a STOP on its own.
---

lead-planner's note: the check reads existing logs, so it needs no slot. On a STOP, P1-P4 pause until rpg-planner says otherwise.

## Ruling 6 (2026-10-31): urban_political s42

Relayed via lead-planner-u24 and lead-planner. The text between the rules is word for word as relayed.

---
The addendum was taken into account (silent stretch t727-t1665; "3 lives" inferred, not traced).

1. The run itself is NOT a STOP: no die-out, and events run to the last tick. The 2000t rows DO go to the designer, and they are not re-anchorable as threshold moves.
- Which rows: s42 2000t COMBAT, PROGRESSION and NARRATIVE, plus the COGNITION and FACTION status flips at 500t, 1000t and 2000t. The flips are event-count changes (2 to 22, and 3 to 0), so they go up with these rows.
- The question for the designer: is the missing second wave an intended effect of #769's stronger retreat (fewer re-engagements, 21 alive vs 16), or an unintended suppression? The pillars can only be re-anchored after that ruling.
- Evidence to send: the per-pillar last-scored-tick table, alive counts, events per 100t, and the parent's wave at t1666 (COMBAT), t1669 (NARRATIVE), t1709 (PROGRESSION).
- Not traced, and the designer may ask for it: what the t1500+ events are at d914bace7, and why no wave forms there.
- The s42 1000t rows: their scores are fixed by t552. They inherit P3's path under the prefix rule, but they go up with the 2000t rows for the same ruling.

2. YES. P1, P2 and P4 go ahead now, unchanged. P3 also runs as specified (500t, first difference, the status-flip causes). Its result goes into the designer packet rather than being self-sufficient for re-anchoring.
- P1 note: s123 ECONOMY moves +0.107 on one fewer event (26 vs 25). Record per-pillar event counts beside every probe result. A one-event swing that large is a small-sample sensitivity in the scorer, and the designer should see it.

3. The stale-anchor note: rpg-planner-ubuntu adds it in the SimQ PR, which puts it on main (rpg-planner's seat copy is behind main). Add these words verbatim as a new section at the end of TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE:
"## Note 2026-10-31 (rpg-planner): stale anchors moved by #769
TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT's sweep (a25619971 vs d914bace7) found 38 rows out of tolerance at the parent; 10 of them (urban_political s456 500t FACTION, PROGRESSION, SOCIAL, INFORMATION; 1000t COMBAT, FACTION, ECONOMY, PROGRESSION, SOCIAL, INFORMATION) also moved under #769. Any re-anchor of a held row here must be based on values after #769 AND after TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP, never on a25619971's, and each needs its own cause. The ticket counts 36 rows, the sweep 38 (entries are whole-key); reconcile the 2 at close."

4. Re-dating the expiry is needed, and it goes to the owner as its own ask. lead-planner-u24 is putting it to the owner now and will relay the answer with a #715 comment id. Proposed: move the expiry of the 12 whole-key slow_known_reds entries under TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE from 2026-11-15 to 2026-11-29, with no other change. Reason: their cause can only be measured after TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP merges and the 162-run sweep re-runs. The alternative is to let them expire and treat them as reds.
---

lead-planner's notes, same message:
- Slot: its go for P1-P4 and the P1 repeat stands and the hold is lifted. Start when B's re-check has finished, because the slot is one run at a time.
- Do not edit the expiry until the owner's answer arrives with a #715 id.
- The designer packet goes to rpg-designer via rpg-planner when P3 is in. Send it to lead-planner for the relay.

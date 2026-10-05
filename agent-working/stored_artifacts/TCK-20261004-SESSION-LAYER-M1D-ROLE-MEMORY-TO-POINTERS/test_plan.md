---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-SESSION-LAYER-M1D-ROLE-MEMORY-TO-POINTERS
artifact_type: test_plan
tags: [ai, process-improvement, governance]
---

# Test plan (retroactive)

**Written after the fact**, from the ticket's acceptance criteria, `migration_map.md` and the ticket's Implementation Notes. "Implementer-recorded" means the ticket or map states it and it was not re-run; "re-run 2026-10-05" means checked by the implementer session while writing this file.

## Proof Plan

| AC | Check | Result | Source |
|---|---|---|---|
| 1 | `migration_map.md` lists every role-defining memory file with a repo home; each cited path exists | map lists the ten candidates; 3 rules GAP and 3 PARTIAL are stated openly, not dropped. The gaps were then homed or accepted (branch-recovery subsection at `docs/guides/delivery_process.md` "Recovering when a commit lands on a branch an implementer holds", present on main; two accepted with no new text) | implementer-recorded; existence of the `delivery_process.md` subsection re-run 2026-10-05; the map's other cited paths not individually re-checked |
| 2 | Repo homes merged before any memory file shortened | map records PR #314, squash `242d8920e89bff578a83ab31d2366a215af3d2dc`; owner confirmation and shortening are dated 2026-10-04 in the ticket after that merge. Memory edits have no git timestamp | implementer-recorded; order rests on the ticket's notes |
| 3 | Each shortened file keeps frontmatter, links and a pointer; `MEMORY.md` hooks updated | re-run 2026-10-05: all six shortened files have frontmatter, a `Pointer (M1d, 2026-10-04)` line and `Related:` links; the six `MEMORY.md` lines say `POINTER →`. **One deviation:** `feedback_route_work_via_rpg_feature_planning.md` also carries a "Reinforced 2026-10-05" paragraph added after the shortening ("handoff to the rpg-feature-planning, don't contact directly to implementers"), so it is more than a pointer; that sentence appears in no repo home (`domains/rpg.md` does not state it) | re-run 2026-10-05 |
| 4 | Grep of the memory directory shows no role definition left stated twice (define-once) | command and output below, run 2026-10-05. No role rule is stated in both a pointer file and another memory file: the hits in other files are mentions of `mechanisms.yaml` in unrelated notes. The "Reinforced" paragraph above is memory-only, so it is not duplicated either, but it is a rule with no repo home | re-run 2026-10-05; the original close never recorded a grep result |
| 5 | Owner confirms the list before shortening | `migration_map.md` "Owner confirmation (2026-10-04)": owner confirmed ("confirm the memory list"), relayed by the `agent-working-design` session. Not directly observable by the implementer | implementer-recorded; relayed, not independently checkable |

## AC4 command and output (2026-10-05)

```
cd ~/.claude/projects/-home-u24desktop-Working-rpg-based-simulation/memory && grep -n -i -E "never (message|contact)[^.]*implementer|epic tickets only|rpg-planner owns|only its tooling|mechanisms\.yaml" *.md | cut -c1-120

feedback_planner_creates_epic_tickets_only.md:3:description: "Pointer: a roadmap session files epic tickets only; child 
feedback_planner_creates_epic_tickets_only.md:8:Pointer (M1d, 2026-10-04): this rule now lives in `docs/guidelines/sessi
feedback_registry_edit_run_full_tools_dir_and_all_views.md:3:description: "After any registries/mechanisms.yaml edit, re
feedback_registry_edit_run_full_tools_dir_and_all_views.md:11:After editing `registries/mechanisms.yaml`, do two things 
feedback_route_work_via_rpg_feature_planning.md:13:when the work is detailed, I never message rpg implementer lanes. The
feedback_verify_with_the_command_ci_runs_not_the_authors_filter.md:16:**Confirmed 2026-10-03, PR #292.** `world-rule-cat
MEMORY.md:27:- [Semantic control plane role division](project_semantic_control_plane_role_division.md) — POINTER → d
MEMORY.md:32:- [Mechanism registry ownership split](project_mechanism_registry_ownership_split.md) — POINTER → sessi
MEMORY.md:34:- [Planner creates epic tickets only](feedback_planner_creates_epic_tickets_only.md) — POINTER → functi
MEMORY.md:125:- [mechanisms.yaml verdict is not evidence](project_mechanisms_yaml_verdict_not_evidence.md) — re-verify
project_investigation_forks_ignore_readonly.md:3:description: "Dispatched investigation forks wrote to registries/mechan
project_investigation_forks_ignore_readonly.md:12:directly to `registries/mechanisms.yaml`** despite explicit read-only 
project_mechanism_registry_ownership_split.md:3:description: "Pointer: mechanisms.yaml content is rpg-owned; only its to
project_mechanism_registry_ownership_split.md:8:Pointer (M1d, 2026-10-04): this rule now lives in `registries/session_ro
project_mechanisms_yaml_verdict_not_evidence.md:3:description: "A registries/mechanisms.yaml verdict is a claim, not evi
project_mechanisms_yaml_verdict_not_evidence.md:8:A `verdict:`/`verified.verdict:` field in `registries/mechanisms.yaml`
project_mechanisms_yaml_verdict_not_evidence.md:12:filed on 2026-09-20 on the strength of a `mechanisms.yaml` verdict da
project_mechanisms_yaml_verdict_not_evidence.md:23:- Before filing or grouping a ticket that cites a `mechanisms.yaml` v
project_semantic_control_plane_role_division.md:3:description: "Pointer: rpg-planner owns the Semantic Control Plane epi
```

Reading of the output: hits are in `MEMORY.md` (index lines), the pointer files' own descriptions and pointer lines, `feedback_planner_creates_epic_tickets_only` and `feedback_route_work_via_rpg_feature_planning` (their pointers and the reinforcement paragraph), and four unrelated notes that mention `registries/mechanisms.yaml` as a file (`project_mechanisms_yaml_verdict_not_evidence`, `feedback_registry_edit_run_full_tools_dir_and_all_views`, `feedback_verify_with_the_command_ci_runs_not_the_authors_filter`, `project_investigation_forks_ignore_readonly`). The grep is a phrase probe over the six shortened files' rule wording, not a proof of absence.

## Regression-prone path

A later session adding rule text back into a pointer file (as the 2026-10-05 reinforcement did) reopens the define-once gap; nothing mechanical checks it.

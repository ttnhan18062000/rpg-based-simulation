---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION
phase: open
date: 2026-09-17
tags: [architecture, documentation, investigation]
---

# TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION

## Title
Derive candidate systems by hand against the real graph and report whether the tier design survives
contact — investigate, build nothing

## Status
INPROGRESS — investigation complete, findings reported to peer, held for review before final
closure per explicit request

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
The tier model proposes that a **system** declares a root and derives its membership from that
root's transitive ancestors in `depends_on`. That design has never been run against the real graph.

Before writing any schema, find out whether it produces sensible sets — and answer the three
questions the implementation tickets cannot be drafted without.

**Build nothing.** No schema, no field, no generator. Derive by hand or with a throwaway script and
report.

## Scope

### 1. Derive 4 candidate systems against the current 89-node graph

Suggested, adjust if the graph says otherwise: **combat**, **progression**, **economy/trade**,
**social**. For each, pick a plausible root, compute its transitive ancestors, and record the
resulting membership set.

### 2. Judge each set against one question

**Would a person who knows this simulation call that set "the combat system"?**

Report what is missing that should be there, and what is included that should not be. That judgement
is the finding — a set that needs heavy explanation is evidence the derivation does not work, not
evidence the reader is wrong.

### 3. Answer the three blocking questions

- **How many systems are there?** Nobody has counted. The design assumes a tractable number; if the
  89 nodes decompose into 30 systems the tier adds noise rather than structure.
- **Does one root per system suffice?** `combat` plausibly works from `combat_resolution`.
  `economy` may need several. If multiple roots are needed, the schema changes.
- **Do axes attach to mechanisms or to systems?** Fewer declarations versus more precision. Decide
  against a real case — take one axis from the existing proposals (knowledge-belief,
  social-relationship, legacy-memory, temporal) and try both.

### 4. Report how much the result depends on untrusted edges

`TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY` removed `tactical_decision →
combat_resolution` as a caller rather than a prerequisite. ~64 edges predate that rule.

For each derived set, state how many of its edges have been validated against the stated definition
and how many have not. **If membership rests mostly on unaudited edges, that is the headline finding**
and `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` becomes a hard precondition rather than
a related ticket.

## Out of Scope
- **Any schema, field, or generator.** Investigation only.
- **Running the edge audit.** Report dependence on it; don't do it here.
- **Declaring real systems in the registry.** Candidates are for judgement, not for committing.
- **Axes beyond the single test case** in §3.

## Acceptance Criteria
1. Four candidate systems derived, with membership sets recorded in full.
2. Each set judged explicitly — what is missing, what is wrongly included — not merely listed.
3. All three blocking questions answered with data.
4. Edge-trust reported per set as a count, not an impression.
5. A stated recommendation: **proceed, proceed-with-changes, or do not build this tier.** "Do not
   build" is a legitimate and useful outcome — the epic exists to find that out cheaply if true.

## Related Tickets
- `TCK-20260917-EPIC-MECHANISM-TIER-MODEL` — parent
- `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` — the precondition this measures
- `TCK-20260917-MECHANISM-THREE-TIER-AXIS-SYSTEM-MECHANISM` — the design being tested

## Related Docs
- `docs/plans/mechanism_tier_model_initiative.md` §3, §7
- `docs/brainstorm/2026-09-02-core-rpg-knowledge-belief-axis-proposal.md` and siblings — real axes
  for the §3 test

## Related Stored Artifacts
None yet.

## Related Code Areas
- `registries/mechanisms.yaml`
- `tools/mechanism_registry/generate_mechanism_priority_view.py` — the ancestors-of traversal exists
  here already; call it rather than reimplementing

## Assumptions / Open Questions
1. Derived membership reflects **declared** edges, not real traffic. Combat is reached mostly via
   movement's opportunity-attack path while the declared decision route fires 0–2 times per 1000
   ticks. The `combat` candidate is the sharpest test of whether that gap makes derivation useless
   or merely imperfect.
2. Roots may not be unique — two plausible roots could derive overlapping-but-different sets for the
   same intuitive system. If so, say which and how much they differ.
3. This investigation can conclude the tier is not worth building. That outcome saves the three
   implementation tickets and is a success, not a failure.

## Implementation Notes
The pattern that has worked repeatedly in this arc: measure the cheapest discriminating thing before
committing to a design. This is that step for the tier model.

**Run 2026-09-17.** Derived via `tools.mechanism_registry.registry.transitive_dependencies_of()`
(the existing ancestors-of traversal, reused directly, not reimplemented) against the real,
committed 93-mechanism graph. Full membership sets, per-mechanism state/verified status, and the
throwaway script are in `stored_artifacts/TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION/investigation.md`.

### 1–2. Candidate systems, derived and judged

| Domain | Root tried | n | Judgment |
|---|---|---|---|
| combat | `combat_resolution` | 8 | **Partial fit.** `combat_engagement`, `status_effects`, `skill_unlocks`, `action_pacing_readiness` all clearly belong. But `tactical_decision` — the actual decision-making mechanism, and the one a knowledgeable person would name first — is **absent**, because this same investigation arc's own identity-rules ticket correctly removed `tactical_decision → combat_resolution` as a caller edge, not a functional dependency. Correctly fixing that edge, as a direct side effect, removed the derived set's own most intuitive member. `entity_role`/`personality` are also included on thin grounds (they feed tactical role/style, not combat resolution's own core logic) — borderline, not clearly wrong. |
| progression | `xp_leveling` | 9 | **Poor fit.** The set is combat's own set plus `xp_leveling` on top — 8 of 9 members are combat mechanisms. Missing `attributes`, `derived_stats`, `evolution`, `readiness_speed_scaling`, `succession`/`aging_death` (lifecycle progression) — none of which are `depends_on` ancestors of `xp_leveling`, because progression's own real inputs (attribute point spending, aging) aren't declared as things `xp_leveling` requires to exist. A person who knows this simulation would not call this set "the progression system" — they'd call it "combat, plus leveling." |
| economy/trade | `crafting` (or `equipment_scoring`) | 2 | **Poor fit, too small.** `{crafting, inventory_trade_conservation}` (or `{equipment_scoring, inventory_trade_conservation}`) — missing trade, town services, harvesting, gold sinks, buildings. `inventory_trade_conservation` itself declares no dependencies and only these two mechanisms depend on it; the real economy domain is far larger than what a single root's own ancestors reach. |
| social | `reputation` | 4 | **Plausible but narrow.** `{reputation, affection_relationship_bonds, interaction_channeling, action_pacing_readiness}` — a believable small core, but misses `commitment_betrayal`/`commitment_pressure_consequences` (promise-keeping) and `emotion`, which most people would call social too. |
| social | `goal_hierarchy` | 17 | **Badly over-inclusive.** Pulls in `combat_resolution`, `combat_engagement`, `perception`, `belief_cycle`, `self_model`, `trauma` — this is closer to "the entire strategic-cognition layer" than "the social system." A set this size, for a domain this specific, needs heavy explanation — exactly the signal this ticket's own §2 test is built to catch. |

**Two roots for "social" gave a 4-member set and a 17-member set with almost no overlap in what a
reader would call the domain's core** — direct evidence for Assumption #2 (roots are not unique,
and the difference between candidate roots for the same intuitive system can be enormous, not a
minor variation).

### 3. The three blocking questions, answered

**How many systems are there?** Not a small, tractable number the way the design hoped. Of 4
candidates tried, only `combat` produced a set most people would recognize without heavy caveats,
and even that one has a real, load-bearing omission. `progression` and `economy` both failed
outright from a single root. The likely real shape is either a handful of large, impure systems
(muddying "combat" with "progression" the way `xp_leveling`'s own ancestors do) or dozens of small,
precise clusters that don't map onto genre-level names like "combat"/"progression"/"economy"/
"social" at all. Neither answer is "a tractable handful of clean systems."

**Does one root per system suffice?** **No — falsified, not just for `economy` as originally
suspected, but for `progression` too.** A single root's own ancestor set either captures too little
(`economy`, n=2) or drags in an unrelated adjacent domain wholesale (`progression` inheriting all of
`combat`). Multi-root aggregation (union of several roots' own ancestor sets) looks like it should
be the *default* schema primitive, not a special case reserved for "economy may need several."

**Do axes attach to mechanisms or to systems?** **To mechanisms.** Tested against the temporal axis
proposal (`docs/brainstorm/codex/2026-08-28-core-rpg-temporal-axis-proposal.md`): its own real
concerns — succession, aging/lifecycle, demographic cycles, institutional/commitment continuity —
name mechanisms (`succession`, `aging_death`, `demographic_cohort_cycle`, `commitment_betrayal`)
that live in *different* candidate systems above (progression, social, world), not one. Attaching
"temporal" to a single system would either miss most of what the axis actually needs to tag, or
force an artificial merge of unrelated systems. Given systems themselves are shown above to be
unstable derived sets (not a settled, validated primitive the way mechanisms now are, post
identity-rules), stacking an axis on top of that instability compounds rather than isolates the
problem. Mechanisms — bound to code, identity-validated — are the more defensible attachment point.

### 4. Edge trust per set, as counts

| Set | Internal `depends_on` edges | Audited under the new definition | Unaudited (predate the rule) |
|---|---|---|---|
| combat (`combat_resolution`) | 8 | 5 | 3 |
| progression (`xp_leveling`) | 9 | 5 | 4 |
| economy (`crafting`) | 1 | 0 | 1 |
| social (`reputation`) | 3 | 0 | 3 |
| social (`goal_hierarchy`) | 18 | 5 | 13 |

**Headline: even `combat`, the single best-fitting candidate, rests on unaudited edges for 3 of its
8 (37.5%).** `economy` and the narrow `social` candidate rest on **zero** audited edges — every
single edge in those derived sets predates the identity-rules definition and has not been checked
against it. `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` is not merely related work —
on this evidence it is a **hard precondition** for trusting any derived system's own membership,
not an independent, deferrable improvement.

### Recommendation

**Do not build the `system` tier as currently designed (single declared root, derive membership by
ancestor traversal).** Three separate, independent problems, each sufficient on its own:

1. Single-root derivation fails for 2 of 4 candidates outright (`progression`, `economy`), and is
   only a *partial* fit for the best case (`combat`) because a recent, *correct* edge removal
   silently deleted the set's own most intuitive member.
2. Membership rests substantially on unaudited `depends_on` edges (0–37.5% audited across the 5
   sets tried) — the tier would be built on ground not yet confirmed solid.
3. The two `social` roots tried differ by more than 4x in membership size with almost no shared
   core, meaning "pick a root" is not a well-posed instruction as currently stated — a design that
   requires picking the *right* root, with no stated method for choosing between plausible
   candidates, isn't yet a design.

**If this tier is pursued at all, it should be re-scoped as proceed-with-changes, not proceed:**
multi-root aggregation as the schema's own default (not a special case), sequenced strictly after
`TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` lands (not merely related to it), and with
a stated, checkable method for choosing/validating roots before any system is declared in the
registry. Axes should attach to mechanisms, not systems, independent of whichever system design (if
any) is eventually built.

## Test Summary
Investigation only — no code, schema, field, or generator built, per this ticket's own explicit
scope. The throwaway derivation script and its full output are preserved in
`stored_artifacts/TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION/investigation.md`.

## Files Changed
- `stored_artifacts/TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION/` — this ticket's
  own investigation.md/plan.md/test_plan.md.

## Completion Summary
**Investigation complete, held for peer/user review before final closure** — reported per explicit
request to read the findings against the design conversation while it's still live context.
Recommendation: do not build the `system` tier as designed; if pursued, proceed-with-changes
(multi-root default, edge-audit precondition, a stated root-selection method) rather than proceed
as-is.

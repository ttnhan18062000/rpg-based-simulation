# Implementation Sequence — skill-catalog-modernization

Tickets must be implemented in this order. Generated from intra-batch
dependency analysis. `implement-epic` reads this file to override
alphabetical order.

## Order

1. TCK-20260805-SECURITY-REVIEW-HOTFIX-GAP  (no deps in this batch — smallest, most self-evident, already caused a real miss)
2. TCK-20260805-SKILL-DANGLING-CROSSREF-CLEANUP  (no deps in this batch — small, independent hotfix)
3. TCK-20260805-SECURITY-GATE-FIRING-MONITOR  (depends on: TCK-20260805-SECURITY-REVIEW-HOTFIX-GAP)
4. TCK-20260805-SKILL-GATE-CONVERSION-DECISION  (no hard deps in this batch — its cited dependency, TCK-20260805-SKILLS-DOC-STALENESS-FIX, already landed DONE before this batch was filed)
5. TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED  (no deps in this batch)
6. TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED  (no deps in this batch; soft-coordinate with #4 if debugging-strategies' gate-conversion and content-swap land close together)
7. TCK-20260805-SKILL-USAGE-METRIC  (no deps in this batch)
8. TCK-20260805-OBSERVABILITY-SKILL  (no deps in this batch)
9. TCK-20260805-SIMQ-DEV-SKILL  (no deps in this batch)
10. TCK-20260805-SYSTEMS-SKILL  (no deps in this batch)
11. TCK-20260805-COMBAT-SKILL  (no deps in this batch)
12. TCK-20260805-COGNITION-STRATEGY-SKILL  (no deps in this batch — highest-value gap, but no hard ordering constraint)
13. TCK-20260805-PROGRESSION-ENTITIES-SKILL  (no deps in this batch — 6th domain-gap skill, accidentally omitted from the original numbered list; grouped with #8-#12 by domain-skill-cluster reasoning, no hard ordering constraint)
14. TCK-20260805-FRONTEND-DESIGN-TRIGGER-REOPEN  (no deps in this batch; soft-coordinate with #4 if both touch CLAUDE.md's Proactive Tool Use table)
15. TCK-20260805-CODEX-EVENT-TRACE-GAP-INVESTIGATION  (no deps in this batch — explicitly deferred/P3, lands last by design)

## Why This Order Matters

The two hotfix-tier tickets (#1, #2) land first — smallest, most self-evident, no staging
artifacts required, and #1 already caused a real, confirmed miss (`TCK-20260731-GATE-BYPASS-HARDENING`)
so it has the highest urgency-to-effort ratio in the batch. #3 (the firing monitor) explicitly
depends on #1's fix landing first, since the monitor's purpose — catching future misses — is most
meaningful once the root-cause paragraph is actually corrected; running them in parallel risks the
monitor being written against a not-yet-corrected mental model of "what should have fired."

#4 (the gate-conversion decision) is the most consequential design ticket in the batch — it
decides whether 3 skills convert to binding gates — but has no hard blocking dependency within
this batch (its cited prerequisite, the `docs/ai/skills.md` staleness fix, already landed before
this batch was filed). It's sequenced early-ish since its outcome could inform naming/scope
decisions for later tickets touching the same trigger mechanisms.

#5–#7 (community-swap and usage-metric tickets) are fully independent research/tooling work and
can run in any order or in parallel.

#8–#13 (the 6 domain-gap bespoke skills — observability, simq-dev, systems, combat,
cognition/strategy, progression/entities) are all independent of each other and of everything
else in this batch; ordered here roughly by domain size/urgency (observability and simq-dev first
since they build on already-partially-covered subsystems, cognition/strategy and
progression/entities last among the domain skills despite cognition/strategy being flagged
highest-value, since both benefit from having the other domain skills' authoring pattern already
established as precedent).

#14 (frontend-design reopening) and #15 (Codex event-trace investigation, explicitly P3/deferred)
land last — both are smaller, lower-urgency investigations that don't block or get blocked by
anything else in the batch.

Re-run `/implement-epic` with the same epic_id after any gate failure — already-done tickets are
skipped automatically.

# Plan — TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION

## Disposition (peer-reviewed and approved before closing)
Close on the narrower true claim: there is no live preemption to resolve today, because the two
mechanisms' shared precondition (`len(entity.strategic.leads) > profile.max_leads`) never holds in
a real run — `entity.strategic.leads` is empty for every entity at every tick, confirmed via real
500-tick instrumentation, three independent ways. None of the ticket's three original candidate
dispositions (supersedes / genuinely complementary / sequencing bug) fits, because all three
presuppose the preemption is actually happening in real play. Reconciling two mechanisms that never
fire would be a fix with no observable effect — not a defensible use of implementation work.

## Steps
1. Document the instrumented evidence in `investigation.md` (done) — three independent measurement
   angles, all agreeing the collection is always empty; call counts proving both mechanisms are
   live, not dead; the one-level-deeper trace of why leads are never created (four real creation
   paths, all unreachable under real defaults, for four different reasons).
2. Leave `enforce_bandwidth()` and `CapacityEnforcementPhase.enforce()` untouched — no code change.
   Note the unreconciled ordering explicitly in this ticket's Completion Summary so it is
   recoverable if leads ever start being created for real (at that point the original three-way
   question becomes live again and should be re-asked with real data).
3. Spin the lead-creation-reachability gap out as its own, separate, standard-tier investigation
   ticket, sized correctly per peer review: not "leads aren't created" alone, but combined with the
   already-closed knowledge-fact finding into one framing — **the entire knowledge/investigation
   layer produces nothing in a real run** (facts never written/read; leads never created). This is
   a nameable missing behaviour (characters never investigate, chase a rumor, or follow up on what
   they heard) in a way the knowledge-fact finding alone wasn't, since that finding was "a fact
   that never existed to be ignored" while this is "an entire category of behaviour never occurs."
   Cross-reference `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION`.
   List the four creation paths individually with their distinct root causes (dead code with zero
   callers; flag-gated off by an existing flag; update-only, never seeds from empty; requires a
   provider type with zero real construction sites anywhere) since each needs its own answer.
4. Amend `docs/simulation/belief_and_detour_contract.md` (last touched by PR #173) — its current
   text frames `KnowledgeFact` as provenance while leads "own decision influence." That framing is
   now incomplete: leads are also never created under real defaults, so the division of labour it
   describes is design intent, not live behaviour. State plainly that both halves of the
   knowledge/investigation layer are inert under real defaults. Carried in this ticket's own PR
   rather than opened separately, per peer review's explicit instruction.
5. Close this ticket.

## Guardrails
- Do not modify `enforce_bandwidth()`, `CapacityEnforcementPhase.enforce()`, or their call sites in
  `intelligence.py`/`pipeline.py` — there is nothing to fix given real conditions, and touching
  either risks introducing an untested behavior change to code that, while currently inert on this
  one axis, is real and load-bearing for its other responsibilities (concerns, hypotheses,
  projects, candidate zones — all out of this ticket's scope).
- Do not fold the lead-creation-reachability gap into this ticket's own implementation — file it
  separately, sized and scoped per peer review's explicit framing, not decided unilaterally here.
- Do not flip `ENABLE_GUILD_QUEST_GENERATION` or otherwise attempt a fix for any of the four
  creation-path gaps as a side effect of this ticket.

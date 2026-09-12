# Plan — TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION

## Disposition (peer-reviewed and approved before closing)
Document the real state; build nothing. Neither of the ticket's own original two framings applies
cleanly, and peer review's own "two competing memory models" reframe doesn't apply either —
`KnowledgeFact` and `LeadState` aren't competing for the same decisions; one simply never reaches a
decision at all. The honest finding is that the information-assimilation subsystem is inert end to
end, for reasons owned by other, already-filed tickets, and there is no currently-observable
missing behaviour a player would notice — the "name the missing behaviour" test's own honest answer,
not a way around it.

## Steps
1. Update `docs/simulation/belief_and_detour_contract.md` to state the finding at its real size —
   not "no reader" (undersells it) but "inert end to end": facts almost never written (two gates,
   both owned elsewhere), never read when they are, and the one decision-time structure shaped to
   receive this kind of data is empty from every source. Explicitly note the downstream
   consequence for whoever eventually revisits `ENABLE_INFORMATION_INTENT_EXECUTION`.
2. File `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` as its own, independent,
   P2 ticket for the `CapabilityContext.region_data`/`.enemy_data` always-empty finding — strictly
   as the finding (a decision-time input that is always empty), not as a proposal to wire
   `KnowledgeFact` into it. The shape-match is recorded as an explicitly unproven observation only.
3. Close this ticket on the "document, don't build" disposition, with the full real-density
   instrumented evidence (assimilate() called zero times in a real run) as the primary support for
   why building a reader is not the right next step regardless of what the static code shape
   suggests.

## Guardrails
- Do not wire `KnowledgeFact` into `CapabilityContext` or any other decision — no design doc
  declares that correspondence, unlike `JOIN_PARTY`'s own explicit `intent_mapping`. Building it
  would be inventing gameplay design, not completing a declared one.
- Do not flip `ENABLE_INFORMATION_INTENT_EXECUTION` or thread `pending_information_responses` as a
  side effect of this ticket — both are explicitly owned by other tickets
  (`TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE`'s own deferral;
  `TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH`).

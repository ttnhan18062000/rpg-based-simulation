# Plan — TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION

**Blocked — investigation complete, no implementation without peer/user review.** A real design
exists (`DiplomaticStateMachine.compute_transitions()`) but is unreachable behind three structurally
blocking, partly-circular preconditions (see investigation.md). Unlike the sibling maturity-gate
ticket, fixing this cleanly likely needs at least one new mechanism (a real pre-war producer for
military-strength divergence and/or territory/tension), not just reachable numbers — that is a real
design decision, not this investigation's call. This file will be filled in once a direction is
confirmed.

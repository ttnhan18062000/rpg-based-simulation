# Investigation - Phase 1 Performance Budgets

Investigated the provider hot-paths.
`ResourceOpportunityProvider.get_opportunities`, `ServiceOpportunityProvider.get_opportunities`, and `RequirementEvaluator.evaluate` are highly repetitive.
Adding lightweight local state counters/metrics inside a metric container will easily protect execution loops from processing limits.

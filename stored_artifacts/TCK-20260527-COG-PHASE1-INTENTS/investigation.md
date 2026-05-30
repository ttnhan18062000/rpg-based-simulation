# Investigation - Phase 1 ActionIntent Adapter

Investigated how the existing action surfaces are designed in the codebase.
The existing engine uses action systems (e.g. `ActionRouter` or custom resolvers) to transition entity states.
`ActionIntent` will act as a thin adapter layer mapping strategic options to actual updates/executions.

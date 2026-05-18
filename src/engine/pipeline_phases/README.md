# Pipeline Phases

Internal implementation modules for `AuthoritativeApplyPipeline.refine()`.

Rules:
- Each phase accepts `(state, update)`.
- Each phase returns a new `StateUpdate`.
- Phases must not mutate `AuthoritativeState` in place.
- Public compatibility wrappers stay in `src.engine.pipeline`.

# Phase 3 Investigation Notes

We need to review `src/worldbuilding/compiler.py` around lines 128-220 to see exactly where defaults are used and how to pass down `CompileContext`.
- We can pass `context: Optional[CompileContext] = None` to `WorldCompiler.compile`.
- Inside the entity, resource, building, and faction loops, we will look up resolved properties by checking the context.

# Plan — TCK-20260619-E53Dc-COMPILER-INTEGRATION

## Step 1: compiler.py
Add `faction_names: dict[str, str] | None = None` and `region_names: dict[str, str] | None = None`
to `compile()`. Pass them to `render_markdown()` and `render_json()`.

## Step 2: renderer.py
Add the same two params to `render_markdown()` and `render_json()`. Pass them to
`ChronicleNamer.name_milestone(entry, names, faction_names=fn, region_names=rn)`.

## Step 3: tests/unit/chronicle/test_faction_chronicle.py
Write 4 tests as specified in the ticket scope.

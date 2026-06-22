# Investigation — TCK-20260619-E53Dc-COMPILER-INTEGRATION

## Findings

- `ChronicleCompiler.compile()` in `src/domains/chronicle/compiler.py` accepts `entity_names: dict[int, str]` but NOT `faction_names` or `region_names` — must be added.
- `ChronicleRenderer.render_markdown()` and `render_json()` both accept `entity_names` and call `ChronicleNamer.name_milestone(entry, names)` with only two args — must be updated to pass `faction_names` and `region_names`.
- `ChronicleNamer.name_milestone()` already accepts all four params from E53Da: `entity_names`, `faction_names=None`, `region_names=None`.
- `named_milestones` array key is confirmed in `render_json()` output — this is what the tests assert.
- `chronicle.json` written to `output_dir`; tests should use `tmp_path` fixture.
- E53Da confirmed: `war_declared`, `territory_transferred` both in `BASE_SIGNIFICANCE` and `TEMPLATES`.

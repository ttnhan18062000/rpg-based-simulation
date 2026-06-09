# Investigation
ResolvedEntityArchetype has nested profile objects (stat_profile, inventory_profile, etc.) with CatalogBaseDefinition.id.
TraitDefinition.id and ThemeDefinition.id are the string IDs for traits/themes.
legacy_engine_role/bucket are uppercase enum names (e.g. "HERO", "HERO_GUILD") mappable via EntityRole[name].
hungry_wolf archetype is REDESIGNED-CORE and fully resolved in catalog.
EntityArchetypeResolver.resolve(archetype_id) returns ResolvedEntityArchetype.

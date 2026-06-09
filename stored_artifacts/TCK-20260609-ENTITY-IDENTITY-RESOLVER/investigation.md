# Investigation
EntityIdentityResolver resolves from clean_metadata → runtime_identity_extension → compatibility_projection → legacy_enum.
EntityRole/Faction are IntEnums in src/core/enums.py with values 0-5 and 0-3 respectively.
IdentityComponent.properties (Dict[str,Any]) is the clean metadata store (set by ArchetypeEntityFactory).

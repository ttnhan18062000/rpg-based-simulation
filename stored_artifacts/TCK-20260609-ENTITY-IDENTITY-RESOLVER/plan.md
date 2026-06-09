# Plan
1. Create src/entities/identity_resolver.py with ResolvedEntityIdentity + EntityIdentityResolver
2. Implement 4-path resolution: clean_metadata → runtime_identity_extension → compatibility_projection → legacy_enum
3. Raise IdentityResolutionError on no resolvable identity
4. Write 8 tests

## Deviations
None.

# Test Plan — TCK-20260619-E63C-REGISTRY-LOADER

## test_registry.py
- register + lookup round-trip
- lookup unknown key raises KeyError
- list_all with no enum_class returns only pack-registered keys
- list_all with enum_class returns canonical first, then pack-registered
- duplicate register overwrites

## test_loader.py
- load with empty profile skips all packs
- load discovers demo_escort_pack and registers ESCORT_DIGNITARY
- load skips pack not in active_pack_names
- returned registry has ESCORT_DIGNITARY key in adventure_routing domain

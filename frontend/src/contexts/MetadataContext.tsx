import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import type {
  GameMetadata, EnumsData, ItemsData, ClassesData, TraitsData,
  AttributesData, BuildingsData, ResourcesData, RecipesData,
} from '@/types/metadata';

// Fallback when /api/v1/metadata/* is unavailable (currently unimplemented backend-side --
// see TCK-20260825-METADATA-API-BACKEND-MISSING). All-empty, correctly-shaped GameMetadata so
// consuming panels (BuildingPanel, LootPanel, ClassHallPanel, InspectPanel) render with no
// item/class/trait names looked up rather than crashing on `useMetadata()`'s null-context throw.
// Deliberately does not block the rest of the app (the live map, sidebar, controls) from
// rendering just because this optional detail-lookup data isn't available.
const EMPTY_METADATA: GameMetadata = {
  enums: {
    materials: [], ai_states: [], tiers: [], rarities: [], item_types: [],
    damage_types: [], elements: [], entity_roles: [], factions: [],
    faction_relations: [], entity_kinds: [],
  },
  items: { items: [] },
  classes: {
    classes: [], skills: [], race_skills: {}, scaling_grades: [],
    mastery_tiers: [], skill_targets: [],
  },
  traits: { traits: [] },
  attributes: { attributes: [] },
  buildings: { building_types: [] },
  resources: { resource_types: [] },
  recipes: { recipes: [] },
  itemMap: {}, traitMap: {}, skillMap: {}, classMap: {}, aiStateMap: {}, buildingTypeMap: {},
  attrKeys: [], attrLabels: [],
};

const API = import.meta.env.VITE_API_URL || '';
// Dev-only: when set (frontend/.env.development), sent as X-API-Key -- mirrors
// useSimulation.ts's own API_KEY/authHeaders() convention exactly. Without this, every
// /api/v1/metadata/* call 401s against the real backend (TCK-20260825-METADATA-API-BACKEND-MISSING
// mounted these routes with the same require_admission auth every other REST route already uses,
// no special-casing) -- confirmed by live-testing against a real running backend + frontend dev
// server, not assumed.
const API_KEY = import.meta.env.VITE_API_KEY as string | undefined;

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API}/api/v1/metadata${path}`, {
    headers: API_KEY ? { 'X-API-Key': API_KEY } : undefined,
  });
  if (!res.ok) throw new Error(`metadata ${path}: ${res.status}`);
  return res.json();
}

function buildMetadata(
  enums: EnumsData,
  items: ItemsData,
  classes: ClassesData,
  traits: TraitsData,
  attributes: AttributesData,
  buildings: BuildingsData,
  resources: ResourcesData,
  recipes: RecipesData,
): GameMetadata {
  const itemMap: Record<string, typeof items.items[0]> = {};
  for (const it of items.items) itemMap[it.item_id] = it;

  const traitMap: Record<number, typeof traits.traits[0]> = {};
  for (const t of traits.traits) traitMap[t.trait_type] = t;

  const skillMap: Record<string, typeof classes.skills[0]> = {};
  for (const s of classes.skills) skillMap[s.skill_id] = s;

  const classMap: Record<string, typeof classes.classes[0]> = {};
  for (const c of classes.classes) classMap[c.id] = c;

  const aiStateMap: Record<string, typeof enums.ai_states[0]> = {};
  for (const s of enums.ai_states) aiStateMap[s.name] = s;

  const buildingTypeMap: Record<string, typeof buildings.building_types[0]> = {};
  for (const b of buildings.building_types) buildingTypeMap[b.building_type] = b;

  const attrKeys = attributes.attributes.map(a => a.key);
  const attrLabels = attributes.attributes.map(a => a.label);

  return {
    enums, items, classes, traits, attributes, buildings, resources, recipes,
    itemMap, traitMap, skillMap, classMap, aiStateMap, buildingTypeMap,
    attrKeys, attrLabels,
  };
}

const MetadataContext = createContext<GameMetadata | null>(null);

export function MetadataProvider({ children }: { children: ReactNode }) {
  const [metadata, setMetadata] = useState<GameMetadata | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      fetchJson<EnumsData>('/enums'),
      fetchJson<ItemsData>('/items'),
      fetchJson<ClassesData>('/classes'),
      fetchJson<TraitsData>('/traits'),
      fetchJson<AttributesData>('/attributes'),
      fetchJson<BuildingsData>('/buildings'),
      fetchJson<ResourcesData>('/resources'),
      fetchJson<RecipesData>('/recipes'),
    ])
      .then(([enums, items, classes, traits, attributes, buildings, resources, recipes]) => {
        if (!cancelled) {
          setMetadata(buildMetadata(enums, items, classes, traits, attributes, buildings, resources, recipes));
        }
      })
      .catch(err => {
        // Non-blocking: log for visibility, but never prevent the rest of the app (live map,
        // sidebar, controls) from rendering just because this optional detail-lookup data isn't
        // available. See EMPTY_METADATA's comment for why.
        console.error('Failed to load game metadata, continuing with empty metadata:', err);
        if (!cancelled) setMetadata(EMPTY_METADATA);
      });
    return () => { cancelled = true; };
  }, []);

  if (!metadata) {
    return (
      <div style={{ color: '#888', padding: 24, fontFamily: 'monospace' }}>
        Loading game data…
      </div>
    );
  }

  return (
    <MetadataContext.Provider value={metadata}>
      {children}
    </MetadataContext.Provider>
  );
}

export function useMetadata(): GameMetadata {
  const ctx = useContext(MetadataContext);
  if (!ctx) throw new Error('useMetadata must be used within MetadataProvider');
  return ctx;
}

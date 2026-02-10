import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import type {
  GameMetadata, EnumsData, ItemsData, ClassesData, TraitsData,
  AttributesData, BuildingsData, ResourcesData, RecipesData,
} from '@/types/metadata';

const API = import.meta.env.VITE_API_URL || '';

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API}/api/v1/metadata${path}`);
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
  const [error, setError] = useState<string | null>(null);

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
        if (!cancelled) setError(String(err));
      });
    return () => { cancelled = true; };
  }, []);

  if (error) {
    return (
      <div style={{ color: '#f87171', padding: 24, fontFamily: 'monospace' }}>
        Failed to load game metadata: {error}
      </div>
    );
  }

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

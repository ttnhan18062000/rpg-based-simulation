import { useState } from 'react';
import { X, ChevronDown, ChevronRight, Swords, BookOpen, ScrollText, Brain, BarChart3 } from 'lucide-react';
import type { Entity, GameEvent, MapData } from '@/types/api';
import { KIND_COLORS, STATE_COLORS, TIER_NAMES, itemName, hpColor, ITEM_STATS, RARITY_COLORS } from '@/constants/colors';

const HERO_CLASS_NAMES: Record<string, string> = {
  none: 'None', warrior: 'Warrior', ranger: 'Ranger', mage: 'Mage', rogue: 'Rogue',
  champion: 'Champion', sharpshooter: 'Sharpshooter', archmage: 'Archmage', assassin: 'Assassin',
};
const HERO_CLASS_COLORS: Record<string, string> = {
  none: '#888', warrior: '#f87171', ranger: '#34d399', mage: '#818cf8', rogue: '#fbbf24',
  champion: '#ff4444', sharpshooter: '#22c55e', archmage: '#a78bfa', assassin: '#f59e0b',
};
const HERO_CLASS_DESC: Record<string, string> = {
  none: 'No class assigned.',
  warrior: 'A frontline fighter specializing in strength and vitality.',
  ranger: 'A swift scout with deadly precision and keen awareness.',
  mage: 'A scholar of arcane arts, wielding intelligence and wisdom.',
  rogue: 'A cunning fighter blending agility and strength for lethal strikes.',
  champion: 'An elite warrior who has mastered the art of war.',
  sharpshooter: 'A legendary marksman with unmatched precision.',
  archmage: 'A supreme mage who commands arcane forces at will.',
  assassin: 'A lethal shadow, striking with perfect precision.',
};

const MASTERY_TIERS = ['Novice', 'Apprentice', 'Adept', 'Expert', 'Master'];
function masteryTier(m: number) {
  if (m >= 100) return 4;
  if (m >= 75) return 3;
  if (m >= 50) return 2;
  if (m >= 25) return 1;
  return 0;
}

const SKILL_TARGET_LABELS: Record<string, string> = {
  self: 'Self', single_enemy: 'Enemy', area_enemies: 'AoE Enemies', single_ally: 'Ally', area_allies: 'AoE Allies',
};

type InspectTab = 'stats' | 'class' | 'quests' | 'events' | 'ai';

interface InspectPanelProps {
  entity: Entity | undefined;
  mapData: MapData | null;
  events?: GameEvent[];
  onClose: () => void;
}

export function InspectPanel({ entity, mapData, events, onClose }: InspectPanelProps) {
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const [activeTab, setActiveTab] = useState<InspectTab>('stats');

  if (!entity) {
    return (
      <div className="flex-1 flex items-center justify-center text-text-secondary text-xs p-8 text-center">
        Click an entity on the map or list to inspect it
      </div>
    );
  }

  const toggle = (key: string) => setCollapsed(prev => ({ ...prev, [key]: !prev[key] }));

  const color = KIND_COLORS[entity.kind] || '#888';
  const stateColor = STATE_COLORS[entity.state] || '#888';
  const hpRatio = Math.max(0, entity.hp / entity.max_hp);
  const hpCol = hpColor(hpRatio);
  const xpRatio = entity.xp_to_next > 0 ? Math.min(1, entity.xp / entity.xp_to_next) : 0;
  const staminaRatio = entity.max_stamina > 0 ? Math.min(1, entity.stamina / entity.max_stamina) : 0;
  const tierName = entity.kind === 'hero' ? '' : ` [${TIER_NAMES[entity.tier] || 'Basic'}]`;
  const classColor = HERO_CLASS_COLORS[entity.hero_class] || '#888';
  const terrainCount = entity.terrain_memory ? Object.keys(entity.terrain_memory).length : 0;
  const totalTiles = mapData ? mapData.width * mapData.height : 1024;
  const explorePercent = ((terrainCount / totalTiles) * 100).toFixed(1);

  const activeQuestCount = entity.quests ? entity.quests.filter(q => !q.completed).length : 0;
  const eventCount = events ? events.length : 0;

  const tabs: { id: InspectTab; label: string; icon: React.ReactNode; badge?: number }[] = [
    { id: 'stats', label: 'Stats', icon: <BarChart3 className="w-3.5 h-3.5" /> },
    { id: 'class', label: 'Class', icon: <Swords className="w-3.5 h-3.5" /> },
    { id: 'quests', label: 'Quests', icon: <BookOpen className="w-3.5 h-3.5" />, badge: activeQuestCount },
    { id: 'events', label: 'Events', icon: <ScrollText className="w-3.5 h-3.5" />, badge: eventCount },
    { id: 'ai', label: 'AI', icon: <Brain className="w-3.5 h-3.5" /> },
  ];

  return (
    <div className="flex-1 flex flex-col overflow-hidden min-h-0">
      {/* Header (always visible) */}
      <div className="p-3 border-b border-border shrink-0">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-bold">
            <span style={{ color }}>#{entity.id}</span> {entity.kind}{tierName}
            <span className="text-[#aaa] text-xs ml-1">Lv{entity.level}</span>
          </span>
          <button onClick={onClose} className="text-text-secondary hover:text-text-primary p-0.5 cursor-pointer">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-x-3.5 gap-y-1.5">
          <StatField label="Position" value={`(${entity.x}, ${entity.y})`} />
          <StatField label="State" value={entity.state} valueColor={stateColor} />
          <StatField label="ATK / DEF" value={`${entity.atk} / ${entity.def || 0}`} />
          <StatField label="SPD / LUCK" value={`${entity.spd} / ${entity.luck}`} />
          <StatField label="CRIT / EVA" value={`${(entity.crit_rate * 100).toFixed(0)}% / ${(entity.evasion * 100).toFixed(0)}%`} />
          <StatField label="Gold" value={`${entity.gold}`} valueColor="#fbbf24" />

          {/* HP Bar */}
          <div className="col-span-2 mt-1">
            <div className="flex justify-between mb-0.5">
              <span className="text-[10px] uppercase tracking-wider text-text-secondary">HP</span>
              <span className="text-[11px] font-semibold tabular-nums">{entity.hp} / {entity.max_hp}</span>
            </div>
            <div className="w-full h-1.5 bg-bg-primary rounded-full overflow-hidden">
              <div className="h-full rounded-full transition-[width] duration-200" style={{ width: `${hpRatio * 100}%`, background: hpCol }} />
            </div>
          </div>

          {/* XP Bar */}
          <div className="col-span-2 mt-0.5">
            <div className="flex justify-between mb-0.5">
              <span className="text-[10px] uppercase tracking-wider text-text-secondary">XP</span>
              <span className="text-[11px] font-semibold tabular-nums">{entity.xp} / {entity.xp_to_next}</span>
            </div>
            <div className="w-full h-1 bg-bg-primary rounded-full overflow-hidden">
              <div className="h-full rounded-full bg-accent-purple" style={{ width: `${xpRatio * 100}%` }} />
            </div>
          </div>

          {/* Stamina Bar */}
          {entity.max_stamina > 0 && (
            <div className="col-span-2 mt-0.5">
              <div className="flex justify-between mb-0.5">
                <span className="text-[10px] uppercase tracking-wider text-text-secondary">Stamina</span>
                <span className="text-[11px] font-semibold tabular-nums">{entity.stamina} / {entity.max_stamina}</span>
              </div>
              <div className="w-full h-1 bg-bg-primary rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-[width] duration-200" style={{ width: `${staminaRatio * 100}%`, background: '#fbbf24' }} />
              </div>
            </div>
          )}

          {/* Loot Progress Bar */}
          {entity.state === 'LOOTING' && entity.loot_progress > 0 && (
            <div className="col-span-2 mt-0.5">
              <div className="flex justify-between mb-0.5">
                <span className="text-[10px] uppercase tracking-wider text-text-secondary">Looting</span>
                <span className="text-[11px] font-semibold tabular-nums">{entity.loot_progress} / {entity.loot_duration}</span>
              </div>
              <div className="w-full h-1 bg-bg-primary rounded-full overflow-hidden">
                <div className="h-full rounded-full bg-accent-green" style={{ width: `${(entity.loot_progress / entity.loot_duration) * 100}%` }} />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tab Bar */}
      <div className="flex bg-bg-tertiary border-b border-border px-1 gap-0.5 py-1 shrink-0">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex items-center justify-center gap-1 py-1.5 text-[9px] font-semibold uppercase tracking-wider
                        rounded transition-colors cursor-pointer relative
                        ${activeTab === tab.id
                          ? 'text-accent-blue bg-bg-secondary shadow-sm'
                          : 'text-text-secondary hover:text-text-primary hover:bg-white/[0.03]'
                        }`}
          >
            {tab.icon}
            {tab.label}
            {tab.badge != null && tab.badge > 0 && (
              <span className="absolute -top-0.5 -right-0.5 bg-accent-red text-white text-[7px] font-bold rounded-full w-3.5 h-3.5 flex items-center justify-center">
                {tab.badge > 9 ? '9+' : tab.badge}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {activeTab === 'stats' && <StatsTab entity={entity} collapsed={collapsed} toggle={toggle} />}
        {activeTab === 'class' && <ClassTab entity={entity} classColor={classColor} collapsed={collapsed} toggle={toggle} />}
        {activeTab === 'quests' && <QuestsTab entity={entity} />}
        {activeTab === 'events' && <EventsTab events={events} />}
        {activeTab === 'ai' && <AITab entity={entity} terrainCount={terrainCount} totalTiles={totalTiles} explorePercent={explorePercent} collapsed={collapsed} toggle={toggle} />}
      </div>
    </div>
  );
}

/* ========================================================================= */
/* Tab: Stats                                                                 */
/* ========================================================================= */

function StatsTab({ entity, collapsed, toggle }: { entity: Entity; collapsed: Record<string, boolean>; toggle: (k: string) => void }) {
  return (
    <>
      {/* Attributes */}
      {entity.attributes && (
        <CollapsibleSection title="Attributes" sectionKey="attributes" collapsed={collapsed} toggle={toggle}>
          <div className="grid grid-cols-3 gap-x-3 gap-y-1">
            <AttrField label="STR" value={entity.attributes.str} cap={entity.attribute_caps?.str_cap} frac={entity.attributes.str_frac} color="#f87171" />
            <AttrField label="AGI" value={entity.attributes.agi} cap={entity.attribute_caps?.agi_cap} frac={entity.attributes.agi_frac} color="#34d399" />
            <AttrField label="VIT" value={entity.attributes.vit} cap={entity.attribute_caps?.vit_cap} frac={entity.attributes.vit_frac} color="#fb923c" />
            <AttrField label="INT" value={entity.attributes.int} cap={entity.attribute_caps?.int_cap} frac={entity.attributes.int_frac} color="#818cf8" />
            <AttrField label="SPI" value={entity.attributes.spi} cap={entity.attribute_caps?.spi_cap} frac={entity.attributes.spi_frac} color="#c084fc" />
            <AttrField label="WIS" value={entity.attributes.wis} cap={entity.attribute_caps?.wis_cap} frac={entity.attributes.wis_frac} color="#a78bfa" />
            <AttrField label="END" value={entity.attributes.end} cap={entity.attribute_caps?.end_cap} frac={entity.attributes.end_frac} color="#fbbf24" />
            <AttrField label="PER" value={entity.attributes.per} cap={entity.attribute_caps?.per_cap} frac={entity.attributes.per_frac} color="#2dd4bf" />
            <AttrField label="CHA" value={entity.attributes.cha} cap={entity.attribute_caps?.cha_cap} frac={entity.attributes.cha_frac} color="#f472b6" />
          </div>
        </CollapsibleSection>
      )}

      {/* Active Effects */}
      {entity.active_effects && entity.active_effects.length > 0 && (
        <CollapsibleSection title={`Effects (${entity.active_effects.length})`} sectionKey="effects" collapsed={collapsed} toggle={toggle}>
          {entity.active_effects.map((eff, i) => {
            const isBuff = eff.effect_type === 'SKILL_BUFF' || eff.effect_type === 'TERRITORY_BUFF';
            const mods: string[] = [];
            if (eff.atk_mult !== 1.0) mods.push(`ATK ${eff.atk_mult > 1 ? '+' : ''}${Math.round((eff.atk_mult - 1) * 100)}%`);
            if (eff.def_mult !== 1.0) mods.push(`DEF ${eff.def_mult > 1 ? '+' : ''}${Math.round((eff.def_mult - 1) * 100)}%`);
            if (eff.spd_mult !== 1.0) mods.push(`SPD ${eff.spd_mult > 1 ? '+' : ''}${Math.round((eff.spd_mult - 1) * 100)}%`);
            return (
              <div key={i} className="flex items-center justify-between py-1 text-[11px] border-b border-border/30 last:border-0">
                <div className="flex flex-col">
                  <span className={`font-semibold ${isBuff ? 'text-accent-green' : 'text-accent-red'}`}>
                    {isBuff ? '\u25B2' : '\u25BC'} {eff.source || eff.effect_type.replace(/_/g, ' ')}
                  </span>
                  {mods.length > 0 && (
                    <span className="text-[9px] text-text-secondary">{mods.join(' \u00B7 ')}</span>
                  )}
                </div>
                <span className="text-[10px] text-text-secondary font-mono">{eff.remaining_ticks}t</span>
              </div>
            );
          })}
        </CollapsibleSection>
      )}

      {/* Equipment */}
      <CollapsibleSection title="Equipment" sectionKey="equipment" collapsed={collapsed} toggle={toggle}>
        <EquipSlot label="Weapon" value={entity.weapon} />
        <EquipSlot label="Armor" value={entity.armor} />
        <EquipSlot label="Accessory" value={entity.accessory} />

        {entity.inventory_items && entity.inventory_items.length > 0 ? (
          <div className="mt-2">
            <span className="text-[10px] uppercase tracking-wider text-text-secondary">
              Bag ({entity.inventory_count} items)
            </span>
            <div className="mt-1 flex flex-wrap gap-1">
              {entity.inventory_items.map((iid, i) => (
                <span key={i} className="inline-block text-[10px] bg-bg-tertiary border border-border rounded px-1.5 py-0.5">
                  <ItemWithTooltip itemId={iid} />
                </span>
              ))}
            </div>
          </div>
        ) : (
          <div className="mt-1 text-[11px] text-text-secondary">Bag is empty</div>
        )}
      </CollapsibleSection>
    </>
  );
}

/* ========================================================================= */
/* Tab: Class                                                                 */
/* ========================================================================= */

function ClassTab({ entity, classColor, collapsed, toggle }: { entity: Entity; classColor: string; collapsed: Record<string, boolean>; toggle: (k: string) => void }) {
  const className = HERO_CLASS_NAMES[entity.hero_class] || entity.kind;
  const classDesc = HERO_CLASS_DESC[entity.hero_class] || `A wild ${entity.kind}.`;
  const hasClass = entity.hero_class !== 'none' && !!entity.hero_class;

  return (
    <>
      {/* Class Header */}
      <div className="p-3 border-b border-border">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-bold" style={{ color: classColor }}>
            {hasClass ? className : entity.kind}
          </span>
          <span className="text-[10px] text-text-secondary">Lv {entity.level}</span>
        </div>
        <p className="text-[10px] text-text-secondary leading-relaxed">{classDesc}</p>

        {/* Class Mastery */}
        {entity.class_mastery > 0 && (
          <div className="mt-2">
            <div className="flex justify-between mb-0.5">
              <span className="text-[10px] uppercase tracking-wider text-text-secondary">Class Mastery</span>
              <span className="text-[11px] font-semibold tabular-nums">{entity.class_mastery.toFixed(1)}%</span>
            </div>
            <div className="w-full h-1 bg-bg-primary rounded-full overflow-hidden">
              <div className="h-full rounded-full" style={{ width: `${entity.class_mastery}%`, background: classColor }} />
            </div>
          </div>
        )}
      </div>

      {/* Skills */}
      {entity.skills && entity.skills.length > 0 && (
        <CollapsibleSection title={`Skills (${entity.skills.length})`} sectionKey="skills" collapsed={collapsed} toggle={toggle}>
          {entity.skills.map((sk, i) => {
            const tier = masteryTier(sk.mastery);
            const tierLabel = MASTERY_TIERS[tier];
            const isPassive = sk.skill_type === 'passive';
            return (
              <SkillRow key={i} sk={sk} tier={tier} tierLabel={tierLabel} isPassive={isPassive} />
            );
          })}
        </CollapsibleSection>
      )}

      {entity.skills.length === 0 && (
        <div className="p-3 text-[11px] text-text-secondary">No skills learned yet.</div>
      )}
    </>
  );
}

function SkillRow({ sk, tier, tierLabel, isPassive }: { sk: Entity['skills'][0]; tier: number; tierLabel: string; isPassive: boolean }) {
  const [hover, setHover] = useState(false);
  const tierColors = ['#888', '#60a5fa', '#34d399', '#fbbf24', '#f87171'];

  return (
    <div
      className="relative py-1.5 text-[11px] border-b border-border/30 last:border-0"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      <div className="flex items-center justify-between">
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-text-primary">{sk.name || sk.skill_id.replace(/_/g, ' ')}</span>
            {isPassive && <span className="text-[8px] px-1 py-px rounded bg-bg-tertiary text-text-secondary uppercase">passive</span>}
          </div>
          <div className="flex items-center gap-1 mt-0.5">
            <span className="text-[9px] font-semibold" style={{ color: tierColors[tier] }}>{tierLabel}</span>
            <span className="text-[9px] text-text-secondary">{sk.mastery.toFixed(1)}%</span>
            {!isPassive && <span className="text-[9px] text-text-secondary">&middot; {sk.stamina_cost} sta &middot; CD {sk.cooldown}</span>}
          </div>
        </div>
        <div className="text-right">
          {!isPassive && (
            sk.cooldown_remaining > 0 ? (
              <span className="text-[10px] text-accent-red font-semibold">CD: {sk.cooldown_remaining}</span>
            ) : (
              <span className="text-[10px] text-accent-green font-semibold">Ready</span>
            )
          )}
          <div className="text-[9px] text-text-secondary">{sk.times_used}x used</div>
        </div>
      </div>
      {/* Mastery bar */}
      <div className="w-full h-0.5 bg-bg-primary rounded-full overflow-hidden mt-1">
        <div className="h-full rounded-full" style={{ width: `${sk.mastery}%`, background: tierColors[tier] }} />
      </div>
      {/* Hover tooltip */}
      {hover && sk.description && (
        <div className="absolute left-0 bottom-full mb-1 z-50 w-56 p-2 rounded-md border border-border bg-bg-primary shadow-xl text-[10px] leading-relaxed pointer-events-none">
          <div className="font-bold text-[11px] text-text-primary mb-0.5">{sk.name}</div>
          <div className="text-text-secondary mb-1">{sk.description}</div>
          <div className="flex gap-2 text-text-secondary">
            <span>Target: {SKILL_TARGET_LABELS[sk.target] || sk.target}</span>
            {!isPassive && <span>Power: {sk.power.toFixed(1)}x</span>}
          </div>
        </div>
      )}
    </div>
  );
}

/* ========================================================================= */
/* Tab: Quests                                                                */
/* ========================================================================= */

function QuestsTab({ entity }: { entity: Entity }) {
  const quests = entity.quests || [];
  const active = quests.filter(q => !q.completed);
  const completed = quests.filter(q => q.completed);

  if (quests.length === 0) {
    return <div className="p-3 text-[11px] text-text-secondary">No quests. Visit the Adventurer's Guild to pick up quests.</div>;
  }

  return (
    <div className="p-3">
      {active.length > 0 && (
        <div className="mb-3">
          <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-1.5">Active ({active.length})</div>
          {active.map((q, i) => <QuestCard key={i} quest={q} />)}
        </div>
      )}
      {completed.length > 0 && (
        <div>
          <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-1.5">Completed ({completed.length})</div>
          {completed.map((q, i) => <QuestCard key={i} quest={q} />)}
        </div>
      )}
    </div>
  );
}

function QuestCard({ quest: q }: { quest: Entity['quests'][0] }) {
  const pct = q.target_count > 0 ? Math.min(q.progress / q.target_count, 1.0) * 100 : 100;
  const typeColors: Record<string, string> = { HUNT: '#f87171', GATHER: '#34d399', EXPLORE: '#60a5fa' };
  const typeColor = typeColors[q.quest_type] || '#888';

  return (
    <div className={`rounded-md border border-border/40 p-2 mb-1.5 text-[11px] ${q.completed ? 'opacity-50' : ''}`}>
      <div className="flex items-center justify-between mb-0.5">
        <span className={`font-semibold ${q.completed ? 'text-accent-green line-through' : 'text-text-primary'}`}>
          {q.completed ? '\u2713 ' : ''}{q.title}
        </span>
        <span className="text-[8px] px-1.5 py-px rounded-full font-bold uppercase" style={{ color: typeColor, border: `1px solid ${typeColor}40` }}>{q.quest_type}</span>
      </div>
      {q.description && <p className="text-[9px] text-text-secondary mb-1">{q.description}</p>}
      {!q.completed && (
        <div className="mt-1">
          <div className="flex justify-between mb-0.5">
            <span className="text-[9px] text-text-secondary">{q.progress}/{q.target_count}</span>
            <span className="text-[9px] text-text-secondary">{q.gold_reward}g &middot; {q.xp_reward}xp</span>
          </div>
          <div className="w-full h-1 bg-bg-primary rounded-full overflow-hidden">
            <div className="h-full rounded-full bg-accent-yellow" style={{ width: `${pct}%` }} />
          </div>
        </div>
      )}
      {q.completed && (
        <div className="text-[9px] text-accent-green mt-0.5">Rewards: {q.gold_reward}g &middot; {q.xp_reward}xp</div>
      )}
    </div>
  );
}

/* ========================================================================= */
/* Tab: Events                                                                */
/* ========================================================================= */

function EventsTab({ events }: { events?: GameEvent[] }) {
  if (!events || events.length === 0) {
    return <div className="p-3 text-[11px] text-text-secondary">No events recorded for this entity yet.</div>;
  }

  return (
    <div className="p-3">
      <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-1.5">
        Event History ({events.length})
      </div>
      <div className="space-y-0">
        {[...events].reverse().map((ev, i) => {
          const catColors: Record<string, string> = { combat: '#f87171', loot: '#fbbf24', movement: '#60a5fa', skill: '#a78bfa', quest: '#34d399' };
          const catColor = catColors[ev.category] || '#888';
          return (
            <div key={i} className="py-1 text-[10px] border-b border-border/30 last:border-0">
              <div className="flex items-center gap-1.5">
                <span className="text-text-secondary font-mono shrink-0">T{ev.tick}</span>
                <span className="text-[8px] px-1 py-px rounded font-bold uppercase shrink-0" style={{ color: catColor }}>{ev.category}</span>
              </div>
              <div className="text-text-primary mt-0.5 leading-relaxed">{ev.message}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ========================================================================= */
/* Tab: AI                                                                    */
/* ========================================================================= */

function AITab({ entity, terrainCount, totalTiles, explorePercent, collapsed, toggle }: {
  entity: Entity; terrainCount: number; totalTiles: number; explorePercent: string;
  collapsed: Record<string, boolean>; toggle: (k: string) => void;
}) {
  return (
    <>
      {/* Goals & Thoughts */}
      {entity.goals && entity.goals.length > 0 && (
        <CollapsibleSection title="Goals & Thoughts" sectionKey="goals" collapsed={collapsed} toggle={toggle}>
          {entity.goals.map((g, i) => (
            <GoalRow key={i} goal={g} />
          ))}
        </CollapsibleSection>
      )}

      {/* Craft Target */}
      {entity.kind === 'hero' && entity.craft_target && (
        <CollapsibleSection title="Craft Target" sectionKey="craft" collapsed={collapsed} toggle={toggle}>
          <div className="text-[11px] text-text-primary">
            Working toward: <span className="font-semibold text-accent-yellow">{itemName(entity.craft_target.replace('craft_', ''))}</span>
          </div>
          {entity.known_recipes && entity.known_recipes.length > 0 && (
            <div className="mt-1 text-[10px] text-text-secondary">
              Known recipes: {entity.known_recipes.length}
            </div>
          )}
        </CollapsibleSection>
      )}

      {/* Memory & Vision */}
      <CollapsibleSection title="Memory & Vision" sectionKey="memory" collapsed={collapsed} toggle={toggle}>
        <MemoryStat label="Vision Range" value={`${entity.vision_range} tiles`} />
        <MemoryStat label="Tiles Explored" value={`${terrainCount} / ${totalTiles} (${explorePercent}%)`} />
        <MemoryStat label="Entities Remembered" value={`${entity.entity_memory ? entity.entity_memory.length : 0}`} />

        {entity.entity_memory && entity.entity_memory.length > 0 && (
          <div className="mt-2">
            {[...entity.entity_memory]
              .sort((a, b) => b.tick - a.tick)
              .slice(0, 8)
              .map((em) => {
                const emColor = KIND_COLORS[em.kind] || '#888';
                return (
                  <div key={em.id} className={`flex items-center gap-2 py-0.5 text-[11px] ${!em.visible ? 'opacity-50' : ''}`}>
                    <div className="w-2 h-2 rounded-full shrink-0" style={{ background: emColor }} />
                    <span>#{em.id} {em.kind} Lv{em.level || '?'}</span>
                    <span className="text-[10px] text-text-secondary">ATK:{em.atk || '?'}</span>
                    <span className="text-text-secondary text-[10px] ml-auto">
                      {em.visible ? 'visible' : `last @${em.tick}`}
                    </span>
                  </div>
                );
              })}
            {entity.entity_memory.length > 8 && (
              <div className="text-[10px] text-text-secondary py-0.5">
                ...and {entity.entity_memory.length - 8} more
              </div>
            )}
          </div>
        )}
      </CollapsibleSection>
    </>
  );
}

/* ========================================================================= */
/* Goal row with hover tooltip                                                */
/* ========================================================================= */

const GOAL_PATTERNS: { pattern: RegExp; category: string; desc: string }[] = [
  { pattern: /hunt|kill|attack|fight/i, category: 'Combat', desc: 'Seeking enemies to defeat in battle.' },
  { pattern: /gather|collect|harvest|loot/i, category: 'Gathering', desc: 'Collecting items and resources.' },
  { pattern: /explore|scout|travel|visit/i, category: 'Exploration', desc: 'Discovering new areas of the world.' },
  { pattern: /rest|heal|recover|inn/i, category: 'Recovery', desc: 'Resting to restore health and stamina.' },
  { pattern: /guild|quest/i, category: 'Guild', desc: 'Interacting with the Adventurer\'s Guild.' },
  { pattern: /shop|buy|sell|trade/i, category: 'Commerce', desc: 'Trading items and equipment.' },
  { pattern: /craft|forge|blacksmith/i, category: 'Crafting', desc: 'Creating new items at the Blacksmith.' },
  { pattern: /class|skill|learn|train/i, category: 'Training', desc: 'Improving skills and abilities.' },
  { pattern: /flee|retreat|escape|danger/i, category: 'Survival', desc: 'Avoiding danger and staying alive.' },
  { pattern: /guard|patrol|camp/i, category: 'Guarding', desc: 'Defending a position or camp.' },
  { pattern: /wander|idle|roam/i, category: 'Wandering', desc: 'Moving around without a specific goal.' },
];

function GoalRow({ goal }: { goal: string }) {
  const [hover, setHover] = useState(false);
  const match = GOAL_PATTERNS.find(p => p.pattern.test(goal));
  const category = match?.category || 'General';
  const desc = match?.desc || 'An AI decision or thought.';
  const catColors: Record<string, string> = {
    Combat: '#f87171', Gathering: '#34d399', Exploration: '#60a5fa', Recovery: '#fbbf24',
    Guild: '#a78bfa', Commerce: '#fbbf24', Crafting: '#fb923c', Training: '#c084fc',
    Survival: '#f87171', Guarding: '#6b7280', Wandering: '#9ca3af', General: '#888',
  };

  return (
    <div
      className="relative flex items-baseline gap-1.5 py-0.5 text-[11px] text-text-primary cursor-help"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      <span className="text-[9px] shrink-0" style={{ color: catColors[category] }}>{'\u25C6'}</span>
      <span className="leading-relaxed">{goal}</span>
      {hover && (
        <div className="absolute left-0 bottom-full mb-1 z-50 w-52 p-2 rounded-md border border-border bg-bg-primary shadow-xl text-[10px] leading-relaxed pointer-events-none">
          <div className="font-bold text-[11px] mb-0.5" style={{ color: catColors[category] }}>{category}</div>
          <div className="text-text-secondary">{desc}</div>
        </div>
      )}
    </div>
  );
}

/* ========================================================================= */
/* Shared sub-components                                                      */
/* ========================================================================= */

function CollapsibleSection({
  title, sectionKey, collapsed, toggle, children,
}: {
  title: string;
  sectionKey: string;
  collapsed: Record<string, boolean>;
  toggle: (key: string) => void;
  children: React.ReactNode;
}) {
  const isCollapsed = collapsed[sectionKey] ?? false;
  return (
    <div className="border-b border-border">
      <button
        onClick={() => toggle(sectionKey)}
        className="w-full flex items-center gap-1.5 p-3 pb-1.5 cursor-pointer hover:bg-white/[0.02] transition-colors"
      >
        {isCollapsed
          ? <ChevronRight className="w-3 h-3 text-text-secondary shrink-0" />
          : <ChevronDown className="w-3 h-3 text-text-secondary shrink-0" />
        }
        <span className="text-[10px] font-bold uppercase tracking-wider text-text-secondary">
          {title}
        </span>
      </button>
      {!isCollapsed && <div className="px-3 pb-3">{children}</div>}
    </div>
  );
}

function StatField({ label, value, valueColor }: { label: string; value: string; valueColor?: string }) {
  return (
    <div className="flex flex-col gap-px">
      <span className="text-[10px] uppercase tracking-wider text-text-secondary">{label}</span>
      <span className="text-xs font-semibold tabular-nums" style={valueColor ? { color: valueColor } : undefined}>
        {value}
      </span>
    </div>
  );
}

function EquipSlot({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="flex items-center gap-2 py-1 text-xs">
      <span className="w-[60px] text-[10px] uppercase tracking-wider text-text-secondary shrink-0">{label}</span>
      {value ? (
        <ItemWithTooltip itemId={value} />
      ) : (
        <span className="text-text-secondary italic">-- empty --</span>
      )}
    </div>
  );
}

function ItemWithTooltip({ itemId }: { itemId: string }) {
  const [show, setShow] = useState(false);
  const stats = ITEM_STATS[itemId];
  const rarityColor = stats ? RARITY_COLORS[stats.rarity] || '#9ca3af' : '#9ca3af';

  return (
    <span
      className="relative font-semibold text-text-primary cursor-help"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {itemName(itemId)}
      {show && stats && (
        <span className="absolute left-0 bottom-full mb-1 z-50 w-48 p-2 rounded-md border border-border
                         bg-bg-primary shadow-xl text-[10px] leading-relaxed pointer-events-none">
          <span className="block font-bold text-[11px] mb-1" style={{ color: rarityColor }}>
            {stats.name}
          </span>
          <span className="block text-text-secondary capitalize mb-1">
            {stats.type} &middot; <span style={{ color: rarityColor }}>{stats.rarity}</span>
          </span>
          {stats.atk ? <span className="block text-accent-red">ATK +{stats.atk}</span> : null}
          {stats.def ? <span className="block text-accent-blue">DEF +{stats.def}</span> : null}
          {stats.spd ? <span className="block text-accent-green">SPD {stats.spd > 0 ? '+' : ''}{stats.spd}</span> : null}
          {stats.maxHp ? <span className="block text-accent-green">HP +{stats.maxHp}</span> : null}
          {stats.crit ? <span className="block text-accent-yellow">CRIT +{stats.crit}%</span> : null}
          {stats.evasion ? <span className="block text-accent-purple">EVA +{stats.evasion}%</span> : null}
          {stats.luck ? <span className="block text-accent-yellow">LUCK +{stats.luck}</span> : null}
          {stats.heal ? <span className="block text-accent-green">Heals {stats.heal} HP</span> : null}
          {stats.gold ? <span className="block text-accent-yellow">Worth {stats.gold} gold</span> : null}
        </span>
      )}
    </span>
  );
}

function AttrField({ label, value, cap, frac, color }: { label: string; value: number; cap?: number; frac?: number; color: string }) {
  const [hover, setHover] = useState(false);
  const ratio = cap && cap > 0 ? Math.min(1, value / cap) : 0;
  const fracPct = frac != null ? Math.min(frac, 1.0) * 100 : 0;
  const atCap = cap != null && value >= cap;

  return (
    <div
      className="relative flex flex-col gap-px cursor-help"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      <div className="flex justify-between">
        <span className="text-[10px] uppercase tracking-wider font-bold" style={{ color }}>{label}</span>
        <span className="text-[10px] font-semibold tabular-nums text-text-primary">
          {value}{cap ? <span className="text-text-secondary">/{cap}</span> : null}
        </span>
      </div>
      {cap && cap > 0 && (
        <div className="w-full h-1 bg-bg-primary rounded-full overflow-hidden">
          <div className="h-full rounded-full" style={{ width: `${ratio * 100}%`, background: color }} />
        </div>
      )}
      {/* Hover tooltip showing training progression */}
      {hover && (
        <div className="absolute left-0 bottom-full mb-1 z-50 w-40 p-2 rounded-md border border-border bg-bg-primary shadow-xl text-[10px] leading-relaxed pointer-events-none">
          <div className="font-bold text-[11px] mb-1" style={{ color }}>{label}</div>
          <div className="text-text-secondary mb-1">
            {value}{cap ? ` / ${cap}` : ''} {atCap ? <span className="text-accent-yellow">(MAX)</span> : ''}
          </div>
          {!atCap && (
            <>
              <div className="text-text-secondary mb-0.5">Training: {(fracPct).toFixed(0)}%</div>
              <div className="w-full h-1 bg-bg-tertiary rounded-full overflow-hidden">
                <div className="h-full rounded-full" style={{ width: `${fracPct}%`, background: color, opacity: 0.7 }} />
              </div>
              <div className="text-[9px] text-text-secondary mt-0.5">
                {fracPct > 0 ? `${(100 - fracPct).toFixed(0)}% to next +1` : 'No training progress yet'}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

function MemoryStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between py-0.5 text-[11px]">
      <span className="text-text-secondary">{label}</span>
      <span className="font-semibold tabular-nums">{value}</span>
    </div>
  );
}

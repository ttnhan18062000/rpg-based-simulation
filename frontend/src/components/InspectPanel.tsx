import { useState, useRef } from 'react';
import { X, ChevronDown, ChevronRight, Swords, BookOpen, ScrollText, Brain, BarChart3, Sparkles } from 'lucide-react';
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

type InspectTab = 'stats' | 'class' | 'quests' | 'events' | 'ai' | 'effects';

const ATTR_DESCRIPTIONS: Record<string, { full: string; scaling: string }> = {
  STR: { full: 'Strength', scaling: 'ATK +0.5/pt, carry weight' },
  AGI: { full: 'Agility', scaling: 'SPD +0.4, Crit +0.4%, Eva +0.3%' },
  VIT: { full: 'Vitality', scaling: 'HP +2, DEF +0.3/pt' },
  INT: { full: 'Intelligence', scaling: 'Skill power, XP gain +1%/pt, CD reduction' },
  SPI: { full: 'Spirit', scaling: 'MATK +0.5/pt, mana scaling' },
  WIS: { full: 'Wisdom', scaling: 'MDEF +0.3/pt, Luck +0.3, CD reduction' },
  END: { full: 'Endurance', scaling: 'Stamina +2, HP regen' },
  PER: { full: 'Perception', scaling: 'Vision range, detection, loot quality' },
  CHA: { full: 'Charisma', scaling: 'Trade prices, morale, recruitment' },
};

const ELEMENT_COLORS: Record<string, string> = {
  none: '#9ca3af', fire: '#f87171', ice: '#60a5fa', lightning: '#fbbf24', dark: '#a78bfa', holy: '#fde68a',
};
const ELEMENT_LABELS: Record<string, string> = {
  none: 'None', fire: 'Fire', ice: 'Ice', lightning: 'Lightning', dark: 'Dark', holy: 'Holy',
};
const DMG_TYPE_COLORS: Record<string, string> = {
  physical: '#f87171', magical: '#818cf8',
};

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

  const effectCount = entity.active_effects ? entity.active_effects.length : 0;

  const tabs: { id: InspectTab; label: string; icon: React.ReactNode; badge?: number }[] = [
    { id: 'stats', label: 'Stats', icon: <BarChart3 className="w-3.5 h-3.5" /> },
    { id: 'class', label: 'Class', icon: <Swords className="w-3.5 h-3.5" /> },
    { id: 'effects', label: 'Effects', icon: <Sparkles className="w-3.5 h-3.5" />, badge: effectCount },
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
          <StatField label="ATK" value={`${entity.atk}`} valueColor="#f87171" />
          <StatField label="DEF" value={`${entity.def || 0}`} valueColor="#60a5fa" />
          <StatField label="MATK" value={`${entity.matk}`} valueColor="#c084fc" />
          <StatField label="MDEF" value={`${entity.mdef}`} valueColor="#a78bfa" />
          <StatField label="SPD / LUCK" value={`${entity.spd} / ${entity.luck}`} />
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
        {activeTab === 'effects' && <EffectsTab entity={entity} />}
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
  // Compute equipment bonuses from item stats
  const equipAtk = (entity.weapon ? ITEM_STATS[entity.weapon]?.atk || 0 : 0)
    + (entity.armor ? ITEM_STATS[entity.armor]?.atk || 0 : 0)
    + (entity.accessory ? ITEM_STATS[entity.accessory]?.atk || 0 : 0);
  const equipDef = (entity.weapon ? ITEM_STATS[entity.weapon]?.def || 0 : 0)
    + (entity.armor ? ITEM_STATS[entity.armor]?.def || 0 : 0)
    + (entity.accessory ? ITEM_STATS[entity.accessory]?.def || 0 : 0);
  const equipSpd = (entity.weapon ? ITEM_STATS[entity.weapon]?.spd || 0 : 0)
    + (entity.armor ? ITEM_STATS[entity.armor]?.spd || 0 : 0)
    + (entity.accessory ? ITEM_STATS[entity.accessory]?.spd || 0 : 0);

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

      {/* Primary Derived Stats (Combat) */}
      <CollapsibleSection title="Combat Stats" sectionKey="combat_stats" collapsed={collapsed} toggle={toggle}>
        <div className="space-y-1 text-[10px]">
          <DetailStatRow label="ATK" total={entity.atk} base={entity.base_atk} equip={equipAtk} color="#f87171" />
          <DetailStatRow label="DEF" total={entity.def} base={entity.base_def} equip={equipDef} color="#60a5fa" />
          <DetailStatRow label="MATK" total={entity.matk} base={entity.base_matk} equip={0} color="#c084fc" />
          <DetailStatRow label="MDEF" total={entity.mdef} base={entity.base_mdef} equip={0} color="#a78bfa" />
          <DetailStatRow label="SPD" total={entity.spd} base={entity.base_spd} equip={equipSpd} color="#34d399" />
          <div className="flex justify-between py-0.5 border-b border-border/30">
            <span className="text-text-secondary">CRIT</span>
            <span className="font-semibold text-accent-yellow">{(entity.crit_rate * 100).toFixed(1)}%</span>
          </div>
          <div className="flex justify-between py-0.5 border-b border-border/30">
            <span className="text-text-secondary">EVA</span>
            <span className="font-semibold text-accent-purple">{(entity.evasion * 100).toFixed(1)}%</span>
          </div>
          <div className="flex justify-between py-0.5">
            <span className="text-text-secondary">LUCK</span>
            <span className="font-semibold text-text-primary">{entity.luck}</span>
          </div>
        </div>
      </CollapsibleSection>

      {/* Secondary Derived Stats (Non-Combat) */}
      <CollapsibleSection title="Non-Combat Stats" sectionKey="noncombat_stats" collapsed={collapsed} toggle={toggle}>
        <div className="space-y-1 text-[10px]">
          <SecondaryStatRow label="HP Regen" value={entity.hp_regen} suffix="/tick" color="#34d399" />
          <SecondaryStatRow label="CD Reduction" value={entity.cooldown_reduction} suffix="x" color="#818cf8" isLowerBetter />
          <SecondaryStatRow label="Vision Range" value={entity.vision_range} suffix=" tiles" color="#2dd4bf" isRaw />
          <SecondaryStatRow label="Loot Bonus" value={entity.loot_bonus} suffix="x" color="#fbbf24" />
          <SecondaryStatRow label="Trade Bonus" value={entity.trade_bonus} suffix="x" color="#f472b6" />
          <SecondaryStatRow label="Interact Speed" value={entity.interaction_speed} suffix="x" color="#fb923c" />
          <SecondaryStatRow label="Rest Efficiency" value={entity.rest_efficiency} suffix="x" color="#60a5fa" />
        </div>
      </CollapsibleSection>

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

function DetailStatRow({ label, total, base, equip, color }: { label: string; total: number; base: number; equip: number; color: string }) {
  const buff = total - base - equip;
  return (
    <div className="flex items-center justify-between py-0.5 border-b border-border/30">
      <span className="font-semibold" style={{ color }}>{label}</span>
      <div className="flex items-center gap-1.5">
        <span className="text-text-secondary">{base}</span>
        {equip !== 0 && (
          <span className={equip > 0 ? 'text-accent-blue' : 'text-accent-red'}>
            {equip > 0 ? '+' : ''}{equip}
          </span>
        )}
        {buff !== 0 && (
          <span className={buff > 0 ? 'text-accent-green' : 'text-accent-red'}>
            {buff > 0 ? '+' : ''}{buff}
          </span>
        )}
        <span className="font-bold text-text-primary ml-0.5">= {total}</span>
      </div>
    </div>
  );
}

function SecondaryStatRow({ label, value, suffix, color, isLowerBetter, isRaw }: {
  label: string; value: number; suffix: string; color: string; isLowerBetter?: boolean; isRaw?: boolean;
}) {
  const displayVal = isRaw ? `${value}` : value.toFixed(2);
  const isModified = isRaw ? false : (isLowerBetter ? value < 1.0 : value > 1.0);
  return (
    <div className="flex items-center justify-between py-0.5 border-b border-border/30 last:border-0">
      <span className="text-text-secondary">{label}</span>
      <span className="font-semibold" style={{ color: isModified ? color : undefined }}>
        {displayVal}{suffix}
      </span>
    </div>
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
  const ref = useRef<HTMLDivElement>(null);
  const tierColors = ['#888', '#60a5fa', '#34d399', '#fbbf24', '#f87171'];
  const dmgColor = DMG_TYPE_COLORS[sk.damage_type] || '#888';
  const elemColor = ELEMENT_COLORS[sk.element] || '#9ca3af';
  const elemLabel = ELEMENT_LABELS[sk.element] || 'None';

  return (
    <div
      ref={ref}
      className="relative py-1.5 text-[11px] border-b border-border/30 last:border-0"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      <div className="flex items-center justify-between">
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-text-primary">{sk.name || sk.skill_id.replace(/_/g, ' ')}</span>
            {isPassive && <span className="text-[8px] px-1 py-px rounded bg-bg-tertiary text-text-secondary uppercase">passive</span>}
            {!isPassive && (
              <span className="text-[7px] px-1 py-px rounded font-bold uppercase" style={{ color: dmgColor, background: `${dmgColor}15` }}>
                {sk.damage_type === 'magical' ? 'MAG' : 'PHY'}
              </span>
            )}
            {sk.element && sk.element !== 'none' && (
              <span className="text-[7px] px-1 py-px rounded font-bold uppercase" style={{ color: elemColor, background: `${elemColor}15` }}>
                {elemLabel}
              </span>
            )}
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
      <FixedTooltip triggerRef={ref} show={hover && !!sk.description} width="224px">
        <div className="font-bold text-[11px] text-text-primary mb-0.5">{sk.name}</div>
        <div className="text-text-secondary mb-1">{sk.description}</div>
        <div className="flex flex-wrap gap-2 text-text-secondary">
          <span>Target: {SKILL_TARGET_LABELS[sk.target] || sk.target}</span>
          {!isPassive && <span>Power: {sk.power.toFixed(1)}x</span>}
          <span style={{ color: dmgColor }}>{sk.damage_type === 'magical' ? 'Magical' : 'Physical'}</span>
          {sk.element !== 'none' && <span style={{ color: elemColor }}>{elemLabel}</span>}
        </div>
      </FixedTooltip>
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
/* Tab: Effects                                                               */
/* ========================================================================= */

function EffectsTab({ entity }: { entity: Entity }) {
  const effects = entity.active_effects || [];

  if (effects.length === 0) {
    return <div className="p-3 text-[11px] text-text-secondary">No active effects. Effects come from skills, territory, and environmental sources.</div>;
  }

  return (
    <div className="p-3">
      <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">
        Active Effects ({effects.length})
      </div>
      {effects.map((eff, i) => {
        const isBuff = eff.effect_type === 'SKILL_BUFF' || eff.effect_type === 'TERRITORY_BUFF';
        const mods: { label: string; value: number; color: string }[] = [];
        if (eff.atk_mult !== 1.0) mods.push({ label: 'ATK', value: eff.atk_mult, color: '#f87171' });
        if (eff.def_mult !== 1.0) mods.push({ label: 'DEF', value: eff.def_mult, color: '#60a5fa' });
        if (eff.spd_mult !== 1.0) mods.push({ label: 'SPD', value: eff.spd_mult, color: '#34d399' });
        if (eff.crit_mult !== 1.0) mods.push({ label: 'CRIT', value: eff.crit_mult, color: '#fbbf24' });
        if (eff.evasion_mult !== 1.0) mods.push({ label: 'EVA', value: eff.evasion_mult, color: '#a78bfa' });

        return (
          <div key={i} className="rounded-md border border-border/40 p-2.5 mb-1.5">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1.5">
                <span className={`text-xs font-bold ${isBuff ? 'text-accent-green' : 'text-accent-red'}`}>
                  {isBuff ? '\u25B2' : '\u25BC'} {eff.source || eff.effect_type.replace(/_/g, ' ')}
                </span>
                <span className="text-[8px] px-1.5 py-px rounded-full font-bold uppercase border"
                  style={{ color: isBuff ? '#34d399' : '#f87171', borderColor: isBuff ? '#34d39940' : '#f8717140' }}>
                  {isBuff ? 'Buff' : 'Debuff'}
                </span>
              </div>
              <span className="text-[10px] text-text-secondary font-mono">
                {eff.remaining_ticks < 0 ? 'Permanent' : `${eff.remaining_ticks} ticks`}
              </span>
            </div>

            {/* Stat modifiers */}
            {mods.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-1">
                {mods.map((m) => {
                  const pct = Math.round((m.value - 1) * 100);
                  const isPos = pct > 0;
                  return (
                    <span key={m.label} className="text-[9px] px-1.5 py-0.5 rounded font-bold"
                      style={{ color: isPos ? '#34d399' : '#f87171', background: isPos ? 'rgba(52,211,153,0.1)' : 'rgba(248,113,113,0.1)' }}>
                      {m.label} {isPos ? '+' : ''}{pct}%
                    </span>
                  );
                })}
              </div>
            )}

            {/* HP per tick */}
            {eff.hp_per_tick !== 0 && (
              <div className="mt-1 text-[9px]">
                <span className={eff.hp_per_tick > 0 ? 'text-accent-green' : 'text-accent-red'}>
                  {eff.hp_per_tick > 0 ? '+' : ''}{eff.hp_per_tick} HP/tick
                </span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ========================================================================= */
/* Tab: AI                                                                    */
/* ========================================================================= */

const TRAIT_NAMES: Record<number, { name: string; desc: string; color: string }> = {
  0: { name: 'Aggressive', desc: 'Higher combat utility, lower flee threshold', color: '#f87171' },
  1: { name: 'Cautious', desc: 'Higher flee utility, prefers safe routes', color: '#60a5fa' },
  2: { name: 'Brave', desc: 'Resists fleeing even at low HP', color: '#fbbf24' },
  3: { name: 'Cowardly', desc: 'Flees earlier, avoids strong enemies', color: '#9ca3af' },
  4: { name: 'Bloodthirsty', desc: 'Seeks combat, bonus crit chance', color: '#dc2626' },
  5: { name: 'Greedy', desc: 'Prioritises loot and gold', color: '#fbbf24' },
  6: { name: 'Generous', desc: 'Shares loot, lower sell threshold', color: '#34d399' },
  7: { name: 'Charismatic', desc: 'Better trade prices, higher recruitment', color: '#f472b6' },
  8: { name: 'Loner', desc: 'Avoids allies, prefers solo exploration', color: '#6b7280' },
  9: { name: 'Diligent', desc: 'Faster interactions, lower rest need', color: '#34d399' },
  10: { name: 'Lazy', desc: 'Slower interaction, higher rest utility', color: '#fb923c' },
  11: { name: 'Curious', desc: 'Explores unknown areas more eagerly', color: '#60a5fa' },
  12: { name: 'Berserker', desc: 'Bonus damage at low HP', color: '#dc2626' },
  13: { name: 'Tactical', desc: 'Prefers skills over basic attacks', color: '#818cf8' },
  14: { name: 'Resilient', desc: 'Faster HP regen, higher effective VIT', color: '#34d399' },
  15: { name: 'Arcane Gifted', desc: 'Bonus MATK, higher skill utility', color: '#c084fc' },
  16: { name: 'Spirit Touched', desc: 'Bonus MDEF, resist dark/holy elements', color: '#a78bfa' },
  17: { name: 'Elementalist', desc: 'Bonus elemental damage', color: '#fb923c' },
  18: { name: 'Keen-Eyed', desc: 'Bonus vision range, detects hidden enemies', color: '#2dd4bf' },
  19: { name: 'Oblivious', desc: 'Reduced vision, higher focus on current task', color: '#9ca3af' },
};

const AI_STATE_DESCRIPTIONS: Record<string, string> = {
  IDLE: 'Not doing anything. Waiting for the AI evaluator to pick a new goal.',
  EXPLORING: 'Moving toward unexplored tiles to map the world.',
  HUNTING: 'Seeking and engaging enemies in combat.',
  FLEEING: 'Running away from danger due to low HP or overwhelming enemies.',
  RESTING: 'Recovering HP and stamina at a safe location.',
  LOOTING: 'Picking up items from the ground.',
  TRADING: 'Buying or selling items at the shop.',
  CRAFTING: 'Visiting the blacksmith to craft equipment.',
  SOCIALIZING: 'Interacting with the guild or class hall.',
  GUARDING: 'Defending territory or patrolling near home position.',
  DEAD: 'This entity has been defeated.',
};

function AITab({ entity, terrainCount, totalTiles, explorePercent, collapsed, toggle }: {
  entity: Entity; terrainCount: number; totalTiles: number; explorePercent: string;
  collapsed: Record<string, boolean>; toggle: (k: string) => void;
}) {
  const stateDesc = AI_STATE_DESCRIPTIONS[entity.state] || 'Unknown AI state.';

  return (
    <>
      {/* Current AI State */}
      <CollapsibleSection title="AI State" sectionKey="ai_state" collapsed={collapsed} toggle={toggle}>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold" style={{ color: STATE_COLORS[entity.state] || '#888' }}>
            {entity.state}
          </span>
        </div>
        <p className="text-[10px] text-text-secondary leading-relaxed">{stateDesc}</p>
      </CollapsibleSection>

      {/* Personality Traits */}
      {entity.traits && entity.traits.length > 0 && (
        <CollapsibleSection title={`Traits (${entity.traits.length})`} sectionKey="traits" collapsed={collapsed} toggle={toggle}>
          <div className="text-[9px] text-text-secondary mb-1.5">
            Personality traits influence AI goal evaluation, modifying how this entity prioritizes different actions.
          </div>
          {entity.traits.map((t, i) => {
            const info = TRAIT_NAMES[t] || { name: `Trait #${t}`, desc: 'Unknown trait.', color: '#888' };
            return (
              <div key={i} className="flex items-center gap-2 py-1 text-[11px] border-b border-border/30 last:border-0">
                <span className="w-2 h-2 rounded-full shrink-0" style={{ background: info.color }} />
                <div className="flex flex-col">
                  <span className="font-semibold" style={{ color: info.color }}>{info.name}</span>
                  <span className="text-[9px] text-text-secondary">{info.desc}</span>
                </div>
              </div>
            );
          })}
        </CollapsibleSection>
      )}

      {/* Goals & Thoughts */}
      {entity.goals && entity.goals.length > 0 && (
        <CollapsibleSection title="Goals & Thoughts" sectionKey="goals" collapsed={collapsed} toggle={toggle}>
          <div className="text-[9px] text-text-secondary mb-1.5">
            The Utility AI evaluates all goals each tick. Goals are scored based on context, traits, and environment. The highest-scored goal is selected with weighted randomness.
          </div>
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
  const ref = useRef<HTMLDivElement>(null);
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
      ref={ref}
      className="relative flex items-baseline gap-1.5 py-0.5 text-[11px] text-text-primary cursor-help"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      <span className="text-[9px] shrink-0" style={{ color: catColors[category] }}>{'\u25C6'}</span>
      <span className="leading-relaxed">{goal}</span>
      <FixedTooltip triggerRef={ref} show={hover} width="208px">
        <div className="font-bold text-[11px] mb-0.5" style={{ color: catColors[category] }}>{category}</div>
        <div className="text-text-secondary">{desc}</div>
      </FixedTooltip>
    </div>
  );
}

/* ========================================================================= */
/* Fixed-position tooltip (escapes overflow containers)                        */
/* ========================================================================= */

function FixedTooltip({ triggerRef, show, width, children }: {
  triggerRef: React.RefObject<HTMLElement | null>;
  show: boolean;
  width?: string;
  children: React.ReactNode;
}) {
  if (!show || !triggerRef.current) return null;
  const rect = triggerRef.current.getBoundingClientRect();
  const tooltipWidth = parseInt(width || '200', 10);
  let left = rect.left;
  if (left + tooltipWidth > window.innerWidth) {
    left = window.innerWidth - tooltipWidth - 8;
  }
  if (left < 4) left = 4;
  return (
    <div
      className="fixed p-2 rounded-md border border-border bg-bg-primary shadow-xl text-[10px] leading-relaxed pointer-events-none"
      style={{ top: rect.top - 4, left, width: width || '200px', transform: 'translateY(-100%)', zIndex: 9999 }}
    >
      {children}
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
  const ref = useRef<HTMLSpanElement>(null);
  const stats = ITEM_STATS[itemId];
  const rarityColor = stats ? RARITY_COLORS[stats.rarity] || '#9ca3af' : '#9ca3af';

  return (
    <span
      ref={ref}
      className="relative font-semibold text-text-primary cursor-help"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {itemName(itemId)}
      <FixedTooltip triggerRef={ref} show={show && !!stats} width="192px">
        <span className="block font-bold text-[11px] mb-1" style={{ color: rarityColor }}>
          {stats?.name}
        </span>
        <span className="block text-text-secondary capitalize mb-1">
          {stats?.type} &middot; <span style={{ color: rarityColor }}>{stats?.rarity}</span>
        </span>
        {stats?.atk ? <span className="block text-accent-red">ATK +{stats.atk}</span> : null}
        {stats?.def ? <span className="block text-accent-blue">DEF +{stats.def}</span> : null}
        {stats?.spd ? <span className="block text-accent-green">SPD {stats.spd > 0 ? '+' : ''}{stats.spd}</span> : null}
        {stats?.maxHp ? <span className="block text-accent-green">HP +{stats.maxHp}</span> : null}
        {stats?.crit ? <span className="block text-accent-yellow">CRIT +{stats.crit}%</span> : null}
        {stats?.evasion ? <span className="block text-accent-purple">EVA +{stats.evasion}%</span> : null}
        {stats?.luck ? <span className="block text-accent-yellow">LUCK +{stats.luck}</span> : null}
        {stats?.heal ? <span className="block text-accent-green">Heals {stats.heal} HP</span> : null}
        {stats?.gold ? <span className="block text-accent-yellow">Worth {stats.gold} gold</span> : null}
      </FixedTooltip>
    </span>
  );
}

function AttrField({ label, value, cap, frac, color }: { label: string; value: number; cap?: number; frac?: number; color: string }) {
  const [hover, setHover] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const ratio = cap && cap > 0 ? Math.min(1, value / cap) : 0;
  const fracPct = frac != null ? Math.min(frac, 1.0) * 100 : 0;
  const atCap = cap != null && value >= cap;
  const attrDesc = ATTR_DESCRIPTIONS[label];

  return (
    <div
      ref={ref}
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
      {/* Hover tooltip showing description and training progression */}
      <FixedTooltip triggerRef={ref} show={hover} width="192px">
        <div className="font-bold text-[11px] mb-0.5" style={{ color }}>
          {attrDesc ? attrDesc.full : label}
        </div>
        {attrDesc && (
          <div className="text-[9px] text-accent-blue mb-1">{attrDesc.scaling}</div>
        )}
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
      </FixedTooltip>
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

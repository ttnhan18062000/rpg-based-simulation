import { useState } from 'react';
import { X, ChevronDown, ChevronRight, Swords, Shield, Crosshair, Wand2, Sword, ArrowRight, Lock, Star } from 'lucide-react';
import type { Building } from '@/types/api';
import { useMetadata } from '@/contexts/MetadataContext';
import type { ClassEntry, SkillDefEntry } from '@/types/metadata';

/* ========================================================================= */
/* Visual constants — colors and icons stay in frontend                       */
/* ========================================================================= */

const CLASS_ORDER = ['warrior', 'ranger', 'mage', 'rogue'] as const;

const CLASS_COLORS: Record<string, string> = {
  warrior: '#f87171', ranger: '#34d399', mage: '#818cf8', rogue: '#fbbf24',
  champion: '#ff4444', sharpshooter: '#22c55e', archmage: '#a78bfa', assassin: '#f59e0b',
};

const CLASS_ICONS: Record<string, React.ReactNode> = {
  warrior: <Shield className="w-4 h-4" />,
  ranger: <Crosshair className="w-4 h-4" />,
  mage: <Wand2 className="w-4 h-4" />,
  rogue: <Sword className="w-4 h-4" />,
};

const GRADE_COLORS: Record<string, string> = {
  'E': '#6b7280', 'D': '#94a3b8', 'C': '#34d399', 'B': '#60a5fa',
  'A': '#fb923c', 'S': '#f87171', 'SS': '#f59e0b', 'SSS': '#ffd700',
};

const GRADE_BG: Record<string, string> = {
  'E': 'rgba(107,114,128,0.15)', 'D': 'rgba(148,163,184,0.15)', 'C': 'rgba(52,211,153,0.15)', 'B': 'rgba(96,165,250,0.15)',
  'A': 'rgba(251,146,60,0.15)', 'S': 'rgba(248,113,113,0.2)', 'SS': 'rgba(245,158,11,0.2)', 'SSS': 'rgba(255,215,0,0.25)',
};

const ATTR_COLORS: Record<string, string> = {
  str: '#f87171', agi: '#34d399', vit: '#fb923c', int: '#818cf8',
  spi: '#c084fc', wis: '#a78bfa', end: '#fbbf24', per: '#2dd4bf', cha: '#f472b6',
};

/* ========================================================================= */
/* Component                                                                  */
/* ========================================================================= */

interface ClassHallPanelProps {
  building: Building;
  onClose: () => void;
}

export function ClassHallPanel({ building, onClose }: ClassHallPanelProps) {
  const [selectedClass, setSelectedClass] = useState<string>('warrior');
  const [expandedSkills, setExpandedSkills] = useState<Record<string, boolean>>({});
  const [showBreakthroughClass, setShowBreakthroughClass] = useState(false);

  const metadata = useMetadata();
  const { classMap, skillMap, classes, attributes } = metadata;

  const ATTR_KEYS = attributes.attributes.map(a => a.key);
  const ATTR_LABELS = attributes.attributes.map(a => a.label);

  const scalingMultMap: Record<string, number> = {};
  for (const sg of classes.scaling_grades) scalingMultMap[sg.grade] = sg.multiplier;

  const cls = classMap[selectedClass];
  const btCls = cls?.breakthrough ? classMap[cls.breakthrough.to_class] : null;
  const displayCls = showBreakthroughClass && btCls ? btCls : cls;
  const color = CLASS_COLORS[displayCls?.id ?? ''] || '#888';

  const classSkillDefs = (displayCls?.skill_ids ?? []).map(sid => skillMap[sid]).filter(Boolean) as SkillDefEntry[];
  const heroRaceSkillIds = classes.race_skills['hero'] ?? [];
  const raceSkillDefs = heroRaceSkillIds.map(sid => skillMap[sid]).filter(Boolean) as SkillDefEntry[];

  const toggleSkill = (id: string) => setExpandedSkills(prev => ({ ...prev, [id]: !prev[id] }));

  if (!cls) return <div className="p-4 text-text-secondary text-xs">Loading class data…</div>;

  return (
    <div className="flex-1 flex flex-col overflow-hidden min-h-0">
      {/* Header */}
      <div className="p-3 border-b border-border shrink-0">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <Swords className="w-5 h-5 text-[#c084fc]" />
            <span className="text-sm font-bold text-[#c084fc]">{building.name}</span>
          </div>
          <button onClick={onClose} className="text-text-secondary hover:text-text-primary p-0.5 cursor-pointer">
            <X className="w-4 h-4" />
          </button>
        </div>
        <p className="text-[10px] text-text-secondary leading-relaxed">
          The hall of heroes. Study the path of each class, learn their skills, and pursue mastery through breakthrough.
        </p>
      </div>

      {/* Class Tab Bar */}
      <div className="flex bg-bg-tertiary border-b border-border px-1 gap-0.5 py-1 shrink-0">
        {CLASS_ORDER.map((cid) => {
          const c = classMap[cid];
          const cColor = CLASS_COLORS[cid];
          return (
            <button
              key={cid}
              onClick={() => { setSelectedClass(cid); setShowBreakthroughClass(false); }}
              className={`flex-1 flex items-center justify-center gap-1 py-1.5 text-[9px] font-semibold uppercase tracking-wider
                          rounded transition-colors cursor-pointer
                          ${selectedClass === cid
                            ? 'bg-bg-secondary shadow-sm'
                            : 'text-text-secondary hover:text-text-primary hover:bg-white/[0.03]'
                          }`}
              style={selectedClass === cid ? { color: cColor } : undefined}
            >
              {CLASS_ICONS[cid]}
              {c?.name ?? cid}
            </button>
          );
        })}
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {/* Class Progression Tree */}
        <ProgressionTree cls={cls} btCls={btCls} showBreakthrough={showBreakthroughClass} onToggle={setShowBreakthroughClass} />

        {/* Class Overview */}
        <div className="p-3 border-b border-border">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-bold" style={{ color }}>{displayCls.name}</span>
            <span className="text-[8px] px-1.5 py-0.5 rounded-full font-bold uppercase border" style={{ color, borderColor: `${color}40` }}>
              Tier {displayCls.tier}
            </span>
            <span className="text-[9px] text-text-secondary">{displayCls.role}</span>
          </div>
          <p className="text-[10px] text-text-secondary leading-relaxed mb-2">{displayCls.description}</p>
          <p className="text-[10px] text-text-primary leading-relaxed italic">{displayCls.lore}</p>
        </div>

        {/* Playstyle */}
        <div className="p-3 border-b border-border">
          <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-1.5">Playstyle</div>
          <p className="text-[10px] text-text-primary leading-relaxed">{displayCls.playstyle}</p>
        </div>

        {/* Attribute Scaling */}
        <div className="p-3 border-b border-border">
          <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">Attribute Scaling</div>
          <div className="grid grid-cols-9 gap-1">
            {ATTR_KEYS.map((key, i) => {
              const grade = displayCls.scaling[key] ?? 'E';
              const gradeColor = GRADE_COLORS[grade];
              const gradeBg = GRADE_BG[grade];
              const mult = scalingMultMap[grade] ?? 1.0;
              return (
                <div key={key} className="flex flex-col items-center gap-0.5">
                  <span className="text-[9px] font-bold uppercase" style={{ color: ATTR_COLORS[key] }}>{ATTR_LABELS[i]}</span>
                  <div
                    className="w-full py-1.5 rounded text-center text-xs font-black tracking-wide"
                    style={{ color: gradeColor, background: gradeBg }}
                  >
                    {grade}
                  </div>
                  <span className="text-[8px] text-text-secondary">{Math.round(mult * 100)}%</span>
                </div>
              );
            })}
          </div>
          <div className="mt-2 text-[9px] text-text-secondary leading-relaxed">
            Scaling determines how effectively this class benefits from each attribute.
            <span className="font-semibold" style={{ color: GRADE_COLORS['S'] }}> S</span>=130%,
            <span className="font-semibold" style={{ color: GRADE_COLORS['SS'] }}> SS</span>=150%,
            <span className="font-semibold" style={{ color: GRADE_COLORS['A'] }}> A</span>=115%,
            <span className="font-semibold" style={{ color: GRADE_COLORS['B'] }}> B</span>=100% (baseline).
          </div>
        </div>

        {/* Attribute Bonuses */}
        <div className="p-3 border-b border-border">
          <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">Base Attribute Bonuses</div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            {ATTR_KEYS.map((key, i) => {
              const bonus = displayCls.attr_bonuses[key] ?? 0;
              const capBonus = displayCls.cap_bonuses[key] ?? 0;
              if (bonus === 0 && capBonus === 0) return null;
              return (
                <div key={key} className="flex items-center justify-between text-[10px]">
                  <span className="font-semibold" style={{ color: ATTR_COLORS[key] }}>{ATTR_LABELS[i]}</span>
                  <span className="text-text-primary">
                    {bonus > 0 && <span className="text-accent-green">+{bonus}</span>}
                    {capBonus > 0 && <span className="text-text-secondary ml-1">(cap +{capBonus})</span>}
                  </span>
                </div>
              );
            })}
          </div>
          <div className="mt-1.5 text-[9px] text-text-secondary">
            Bonuses applied when this class is chosen or upon breakthrough.
          </div>
        </div>

        {/* Attribute Effect Reference */}
        <div className="p-3 border-b border-border">
          <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">Attribute Effects</div>
          <div className="space-y-0.5">
            {attributes.attributes.map((attr) => (
              <div key={attr.key} className="flex items-center gap-2 text-[10px]">
                <span className="w-7 font-bold" style={{ color: ATTR_COLORS[attr.key] }}>{attr.label}</span>
                <span className="text-text-secondary">{attr.description}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Class Skills */}
        <div className="p-3 border-b border-border">
          <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">
            Class Skills ({classSkillDefs.length})
          </div>
          {classSkillDefs.map((sk) => (
            <SkillCard key={sk.skill_id} skill={sk} expanded={!!expandedSkills[sk.skill_id]} onToggle={() => toggleSkill(sk.skill_id)} color={color} />
          ))}
        </div>

        {/* Race Skills */}
        <div className="p-3 border-b border-border">
          <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">
            Race Skills (Hero &#x2014; Innate)
          </div>
          <div className="text-[9px] text-text-secondary mb-1.5">
            All heroes learn these skills automatically. No gold cost required.
          </div>
          {raceSkillDefs.map((sk) => (
            <SkillCard key={sk.skill_id} skill={sk} expanded={!!expandedSkills[sk.skill_id]} onToggle={() => toggleSkill(sk.skill_id)} color="#888" />
          ))}
        </div>

        {/* Breakthrough Details */}
        {cls.breakthrough && (
          <div className="p-3 border-b border-border">
            <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">
              Breakthrough: {cls.name} &#x2192; {btCls?.name ?? cls.breakthrough.to_class}
            </div>
            <div className="rounded-md border border-border/50 p-2.5 bg-bg-primary">
              <div className="flex items-center gap-2 mb-2">
                <Star className="w-4 h-4" style={{ color: CLASS_COLORS[cls.breakthrough.to_class] || color }} />
                <span className="text-xs font-bold" style={{ color: CLASS_COLORS[cls.breakthrough.to_class] || color }}>
                  {btCls?.name ?? cls.breakthrough.to_class}
                </span>
              </div>

              <div className="text-[10px] font-bold text-text-secondary uppercase tracking-wider mb-1">Requirements</div>
              <div className="flex gap-3 mb-2 text-[10px]">
                <span className="text-text-primary">Level <span className="font-bold text-accent-yellow">{cls.breakthrough.level_req}+</span></span>
                <span className="text-text-primary">{cls.breakthrough.attr_req.toUpperCase()} <span className="font-bold text-accent-yellow">{'\u2265'} {cls.breakthrough.attr_threshold}</span></span>
              </div>

              <div className="text-[10px] font-bold text-text-secondary uppercase tracking-wider mb-1">Breakthrough Bonuses</div>
              <div className="flex flex-wrap gap-x-3 gap-y-0.5 mb-2">
                {ATTR_KEYS.map((key, i) => {
                  const b = cls.breakthrough!.bonuses[key] ?? 0;
                  const cb = cls.breakthrough!.cap_bonuses[key] ?? 0;
                  if (b === 0 && cb === 0) return null;
                  return (
                    <span key={key} className="text-[10px]">
                      <span className="font-semibold" style={{ color: ATTR_COLORS[key] }}>{ATTR_LABELS[i]}</span>
                      {b > 0 && <span className="text-accent-green"> +{b}</span>}
                      {cb > 0 && <span className="text-text-secondary"> (cap +{cb})</span>}
                    </span>
                  );
                })}
              </div>

              <div className="text-[10px] font-bold text-text-secondary uppercase tracking-wider mb-1">Special Talent</div>
              <div className="rounded border border-border/40 p-2 bg-bg-tertiary">
                <div className="font-bold text-[11px] mb-0.5" style={{ color: CLASS_COLORS[cls.breakthrough.to_class] || color }}>
                  {cls.breakthrough.talent}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Mastery Tier Reference */}
        <div className="p-3 border-b border-border">
          <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">Skill Mastery Tiers</div>
          <div className="text-[9px] text-text-secondary mb-2">
            Using skills builds mastery. Higher mastery tiers unlock power bonuses, stamina reductions, and cooldown improvements.
          </div>
          <table className="w-full text-[9px]">
            <thead>
              <tr className="text-text-secondary uppercase">
                <th className="text-left py-0.5 font-bold">Tier</th>
                <th className="text-left py-0.5 font-bold">Mastery</th>
                <th className="text-center py-0.5 font-bold">Power</th>
                <th className="text-center py-0.5 font-bold">Stamina</th>
                <th className="text-center py-0.5 font-bold">CD</th>
              </tr>
            </thead>
            <tbody>
              {classes.mastery_tiers.map((t, i) => {
                const tierColors = ['#6b7280', '#60a5fa', '#34d399', '#fbbf24', '#f87171'];
                return (
                  <tr key={i} className="border-t border-border/30">
                    <td className="py-1 font-semibold" style={{ color: tierColors[i] }}>{t.name}</td>
                    <td className="py-1 text-text-secondary">{t.min_mastery}%+</td>
                    <td className="py-1 text-center text-text-primary">{t.power_bonus}</td>
                    <td className="py-1 text-center text-text-primary">{t.stamina_reduction}</td>
                    <td className="py-1 text-center text-text-primary">{t.cooldown_reduction}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="p-3 text-[9px] text-text-secondary leading-relaxed">
          Heroes visit the Class Hall to learn new class skills (costs gold) and attempt breakthroughs when they meet the level and attribute requirements.
          Breakthrough classes inherit all skills from the base class and gain improved attribute scaling.
        </div>
      </div>
    </div>
  );
}

/* ========================================================================= */
/* Progression Tree                                                           */
/* ========================================================================= */

function ProgressionTree({ cls, btCls, showBreakthrough, onToggle }: {
  cls: ClassEntry;
  btCls: ClassEntry | null;
  showBreakthrough: boolean;
  onToggle: (v: boolean) => void;
}) {
  const baseColor = CLASS_COLORS[cls.id];
  const btColor = btCls ? CLASS_COLORS[btCls.id] || '#888' : '#888';

  return (
    <div className="p-3 border-b border-border">
      <div className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-2">Class Progression</div>
      <div className="flex items-center gap-1.5">
        {/* Base class node */}
        <button
          onClick={() => onToggle(false)}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border text-[10px] font-bold transition-all cursor-pointer
                      ${!showBreakthrough ? 'shadow-md' : 'opacity-70 hover:opacity-100'}`}
          style={{
            color: baseColor,
            borderColor: !showBreakthrough ? baseColor : `${baseColor}40`,
            background: !showBreakthrough ? `${baseColor}15` : 'transparent',
          }}
        >
          {CLASS_ICONS[cls.id]}
          {cls.name}
          <span className="text-[8px] text-text-secondary font-normal">Lv1</span>
        </button>

        {/* Arrow */}
        <ArrowRight className="w-3.5 h-3.5 text-text-secondary shrink-0" />

        {/* Breakthrough class node */}
        {btCls ? (
          <button
            onClick={() => onToggle(true)}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border text-[10px] font-bold transition-all cursor-pointer
                        ${showBreakthrough ? 'shadow-md' : 'opacity-70 hover:opacity-100'}`}
            style={{
              color: btColor,
              borderColor: showBreakthrough ? btColor : `${btColor}40`,
              background: showBreakthrough ? `${btColor}15` : 'transparent',
            }}
          >
            <Star className="w-3.5 h-3.5" />
            {btCls.name}
            <span className="text-[8px] text-text-secondary font-normal">Lv{cls.breakthrough?.level_req || 10}+</span>
          </button>
        ) : (
          <span className="flex items-center gap-1 px-2.5 py-1.5 rounded-md border border-border/30 text-[10px] text-text-secondary">
            <Lock className="w-3 h-3" /> ???
          </span>
        )}

        {/* Future tier 3 (locked) */}
        <ArrowRight className="w-3.5 h-3.5 text-text-secondary/40 shrink-0" />
        <span className="flex items-center gap-1 px-2.5 py-1.5 rounded-md border border-border/20 text-[10px] text-text-secondary/40">
          <Lock className="w-3 h-3" /> Transcendence
        </span>
      </div>
    </div>
  );
}

/* ========================================================================= */
/* Skill Card                                                                 */
/* ========================================================================= */

function SkillCard({ skill: sk, expanded, onToggle, color }: {
  skill: SkillDefEntry; expanded: boolean; onToggle: () => void; color: string;
}) {
  const isPassive = sk.skill_type === 'passive';

  return (
    <div className="rounded-md border border-border/40 mb-1.5 overflow-hidden">
      {/* Skill header (always visible) */}
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-2 p-2 text-left cursor-pointer hover:bg-white/[0.02] transition-colors"
      >
        {expanded
          ? <ChevronDown className="w-3 h-3 text-text-secondary shrink-0" />
          : <ChevronRight className="w-3 h-3 text-text-secondary shrink-0" />
        }
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-bold text-text-primary">{sk.name}</span>
            {isPassive && <span className="text-[7px] px-1 py-px rounded bg-bg-tertiary text-text-secondary uppercase font-bold">passive</span>}
            {!isPassive && <span className="text-[7px] px-1 py-px rounded uppercase font-bold" style={{ color, background: `${color}15` }}>{sk.target.replace(/_/g, ' ')}</span>}
          </div>
          <div className="text-[9px] text-text-secondary mt-0.5 flex gap-2">
            <span>Lv {sk.level_req}</span>
            {sk.gold_cost > 0 && <span className="text-accent-yellow">{sk.gold_cost}g</span>}
            {!isPassive && <span>CD {sk.cooldown}</span>}
            {!isPassive && <span>{sk.stamina_cost} sta</span>}
            {!isPassive && sk.power !== 1.0 && <span className="text-accent-red">{sk.power}x</span>}
          </div>
        </div>
      </button>

      {/* Expanded details */}
      {expanded && (
        <div className="px-3 pb-2.5 border-t border-border/30">
          <p className="text-[10px] text-text-primary leading-relaxed mt-2 mb-2">{sk.description}</p>

          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[9px]">
            <DetailRow label="Type" value={isPassive ? 'Passive' : 'Active'} />
            <DetailRow label="Target" value={sk.target.replace(/_/g, ' ')} />
            <DetailRow label="Level Req" value={`${sk.level_req}`} />
            <DetailRow label="Gold Cost" value={sk.gold_cost > 0 ? `${sk.gold_cost}g` : 'Free'} valueColor={sk.gold_cost > 0 ? '#fbbf24' : '#34d399'} />
            {!isPassive && <DetailRow label="Cooldown" value={`${sk.cooldown} ticks`} />}
            {!isPassive && <DetailRow label="Stamina" value={`${sk.stamina_cost}`} />}
            {!isPassive && sk.power !== 1.0 && <DetailRow label="Power" value={`${sk.power}x`} valueColor="#f87171" />}
            {sk.range > 0 && <DetailRow label="Range" value={`${sk.range} tiles`} />}
            {sk.duration > 0 && <DetailRow label="Duration" value={`${sk.duration} ticks`} />}
          </div>

          {/* Modifiers */}
          {(sk.atk_mod !== 0 || sk.def_mod !== 0 || sk.spd_mod !== 0 || sk.crit_mod !== 0 || sk.evasion_mod !== 0 || sk.hp_mod !== 0) && (
            <div className="mt-2">
              <div className="text-[9px] font-bold text-text-secondary uppercase mb-0.5">Modifiers</div>
              <div className="flex flex-wrap gap-1.5 text-[9px]">
                {sk.atk_mod !== 0 && <ModBadge label="ATK" value={sk.atk_mod} />}
                {sk.def_mod !== 0 && <ModBadge label="DEF" value={sk.def_mod} />}
                {sk.spd_mod !== 0 && <ModBadge label="SPD" value={sk.spd_mod} />}
                {sk.crit_mod !== 0 && <ModBadge label="CRIT" value={sk.crit_mod} />}
                {sk.evasion_mod !== 0 && <ModBadge label="EVA" value={sk.evasion_mod} />}
                {sk.hp_mod !== 0 && <ModBadge label="HP" value={sk.hp_mod} />}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function DetailRow({ label, value, valueColor }: { label: string; value: string; valueColor?: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-text-secondary">{label}</span>
      <span className="font-semibold" style={valueColor ? { color: valueColor } : undefined}>{value}</span>
    </div>
  );
}

function ModBadge({ label, value }: { label: string; value: number }) {
  const isPositive = value > 0;
  const pct = Math.round(value * 100);
  return (
    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${isPositive ? 'text-accent-green bg-accent-green/10' : 'text-accent-red bg-accent-red/10'}`}>
      {label} {isPositive ? '+' : ''}{pct}%
    </span>
  );
}

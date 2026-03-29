import { LEGEND_ITEMS } from '@/constants/colors';

export function Legend() {
  return (
    <div className="flex gap-3 flex-wrap px-4 py-2 border-b border-border">
      {LEGEND_ITEMS.map((item) => (
        <div key={item.label} className="flex items-center gap-1.5 text-[10px] text-text-secondary">
          <div className="w-2.5 h-2.5 rounded-sm" style={{ background: item.color }} />
          {item.label}
        </div>
      ))}
    </div>
  );
}

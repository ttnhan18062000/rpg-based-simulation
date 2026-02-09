import { Swords } from 'lucide-react';
import type { SimStatus } from '@/hooks/useSimulation';

interface HeaderProps {
  tick: number;
  aliveCount: number;
  totalSpawned: number;
  totalDeaths: number;
  status: SimStatus;
}

const STATUS_COLORS: Record<SimStatus, string> = {
  CONNECTING: 'text-accent-yellow',
  RUNNING: 'text-accent-green',
  PAUSED: 'text-accent-yellow',
  STOPPED: 'text-accent-red',
};

export function Header({ tick, aliveCount, totalSpawned, totalDeaths, status }: HeaderProps) {
  return (
    <header className="col-span-full bg-bg-secondary border-b border-border flex items-center justify-between px-5 h-14 shrink-0">
      <h1 className="text-base font-semibold tracking-wide flex items-center gap-2">
        <Swords className="w-5 h-5 text-accent-blue" />
        <span>RPG Simulation <span className="text-accent-blue">Engine</span></span>
      </h1>
      <div className="flex gap-6 text-[13px] text-text-secondary">
        <div>Tick: <span className="text-text-primary font-semibold tabular-nums">{tick}</span></div>
        <div>Alive: <span className="text-text-primary font-semibold tabular-nums">{aliveCount}</span></div>
        <div>Spawned: <span className="text-text-primary font-semibold tabular-nums">{totalSpawned}</span></div>
        <div>Deaths: <span className="text-text-primary font-semibold tabular-nums">{totalDeaths}</span></div>
        <div className={STATUS_COLORS[status]}>{status}</div>
      </div>
    </header>
  );
}

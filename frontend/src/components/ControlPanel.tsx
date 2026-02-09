import { useState } from 'react';
import { Play, Pause, SkipForward, RotateCcw, Zap } from 'lucide-react';

interface ControlPanelProps {
  sendControl: (action: string) => Promise<void>;
  setSpeed: (tps: number) => Promise<void>;
}

export function ControlPanel({ sendControl, setSpeed }: ControlPanelProps) {
  const [tps, setTps] = useState(20);

  const handleSpeedChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value);
    setTps(val);
    setSpeed(val);
  };

  return (
    <div className="p-3.5 border-b border-border bg-bg-secondary">
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => sendControl('start')}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold
                     bg-accent-blue text-white hover:bg-accent-blue/80 transition-colors cursor-pointer"
        >
          <Zap className="w-4 h-4" /> Start
        </button>
        <button
          onClick={() => sendControl('pause')}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold
                     bg-bg-tertiary text-text-primary border border-border hover:bg-border transition-colors cursor-pointer"
        >
          <Pause className="w-4 h-4" /> Pause
        </button>
        <button
          onClick={() => sendControl('resume')}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold
                     bg-bg-tertiary text-text-primary border border-border hover:bg-border transition-colors cursor-pointer"
        >
          <Play className="w-4 h-4" /> Resume
        </button>
        <button
          onClick={() => sendControl('step')}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold
                     bg-bg-tertiary text-text-primary border border-border hover:bg-border transition-colors cursor-pointer"
        >
          <SkipForward className="w-4 h-4" /> Step
        </button>
        <button
          onClick={() => sendControl('reset')}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold
                     bg-bg-tertiary text-accent-red border border-accent-red/40 hover:bg-accent-red/15 transition-colors cursor-pointer"
        >
          <RotateCcw className="w-4 h-4" /> Reset
        </button>
      </div>
      <div className="flex items-center gap-3 mt-3">
        <label className="text-xs text-text-secondary whitespace-nowrap">Speed</label>
        <input
          type="range"
          min={1}
          max={60}
          value={tps}
          onChange={handleSpeedChange}
          className="flex-1 accent-accent-blue h-1.5"
        />
        <span className="text-xs font-semibold tabular-nums min-w-[48px] text-right">
          {tps} tps
        </span>
      </div>
    </div>
  );
}

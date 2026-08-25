import type { ReactNode } from 'react';
import type { SimStatus } from '@/hooks/useSimulation';

interface SimulationLoadingGateProps {
  status: SimStatus;
  children: ReactNode;
}

type LoadingPhase = 'INITIALIZING' | 'FETCHING_WORLD_DATA' | 'CONNECTING_LIVE' | 'SYNCING';

const PHASE_LABELS: Record<LoadingPhase, string> = {
  INITIALIZING: 'Initializing...',
  FETCHING_WORLD_DATA: 'Fetching world data...',
  CONNECTING_LIVE: 'Connecting to live stream...',
  SYNCING: 'Syncing world state...',
};

const LOADING_STATUSES = new Set<string>(Object.keys(PHASE_LABELS));

export function SimulationLoadingGate({ status, children }: SimulationLoadingGateProps) {
  if (status === 'LOAD_ERROR') {
    return (
      <div className="flex items-center justify-center h-full text-accent-red text-sm">
        Failed to load simulation data. Please reload the page.
      </div>
    );
  }
  if (LOADING_STATUSES.has(status)) {
    return (
      <div className="flex items-center justify-center h-full text-text-secondary text-sm animate-pulse">
        {PHASE_LABELS[status as LoadingPhase]}
      </div>
    );
  }
  return <>{children}</>;
}

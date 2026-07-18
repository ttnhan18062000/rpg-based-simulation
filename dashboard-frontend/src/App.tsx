import { useState } from 'react'
import { RecentActivityGantt } from '@/views/RecentActivityGantt'
import { ReplayTimelineView } from '@/views/ReplayTimelineView'
import { StatsView } from '@/views/StatsView'
import { TicketsView } from '@/views/TicketsView'

type PageView = 'activity' | 'tickets' | 'replay' | 'stats'

const NAV_ITEMS: Array<{ view: PageView; label: string }> = [
  { view: 'activity', label: 'Recent Activity' },
  { view: 'tickets', label: 'Tickets' },
  { view: 'replay', label: 'Replay' },
  { view: 'stats', label: 'Stats' },
]

function App() {
  const [currentView, setCurrentView] = useState<PageView>('activity')
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)

  function handleSelectRun(runId: string) {
    setSelectedRunId(runId)
    setCurrentView('replay')
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <header className="flex flex-wrap items-center gap-y-2 px-5 py-2 sm:py-0 sm:h-14 border-b border-border shrink-0">
        <h1 className="text-base font-semibold mr-4">Agent Ops Dashboard</h1>
        <nav className="flex items-center gap-1">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.view}
              onClick={() => setCurrentView(item.view)}
              className={`px-3 py-1.5 rounded-md text-[11px] font-semibold transition-colors ${
                currentView === item.view
                  ? 'bg-accent-blue/15 text-accent-blue'
                  : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary'
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </header>
      <div className="flex-1 min-h-0 overflow-auto">
        {currentView === 'activity' && <RecentActivityGantt onSelectRun={handleSelectRun} />}
        {currentView === 'tickets' && <TicketsView onSelectRun={handleSelectRun} />}
        {currentView === 'stats' && <StatsView />}
        {currentView === 'replay' &&
          (selectedRunId !== null ? (
            <ReplayTimelineView runId={selectedRunId} />
          ) : (
            <div className="p-6 text-text-secondary">
              Select a run from Recent Activity to view its replay.
            </div>
          ))}
      </div>
    </div>
  )
}

export default App

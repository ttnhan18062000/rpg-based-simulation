import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { SimulationLoadingGate } from '../components/SimulationLoadingGate'
import type { SimStatus } from '../hooks/useSimulation'

const CHILD_TEST_ID = 'canvas-child'

function renderGate(status: SimStatus) {
  return render(
    <SimulationLoadingGate status={status}>
      <div data-testid={CHILD_TEST_ID}>canvas</div>
    </SimulationLoadingGate>
  )
}

describe('SimulationLoadingGate', () => {
  const loadingPhases: { status: SimStatus; label: string }[] = [
    { status: 'INITIALIZING', label: 'Initializing...' },
    { status: 'FETCHING_WORLD_DATA', label: 'Fetching world data...' },
    { status: 'CONNECTING_LIVE', label: 'Connecting to live stream...' },
    { status: 'SYNCING', label: 'Syncing world state...' },
  ]

  for (const { status, label } of loadingPhases) {
    it(`renders phase-specific text for ${status} and does not render children`, () => {
      renderGate(status)

      expect(screen.getByText(label)).toBeInTheDocument()
      expect(screen.queryByTestId(CHILD_TEST_ID)).not.toBeInTheDocument()
    })
  }

  it('renders a distinct error UI for LOAD_ERROR and does not render children', () => {
    renderGate('LOAD_ERROR')

    expect(screen.getByText('Failed to load simulation data. Please reload the page.')).toBeInTheDocument()
    expect(screen.queryByTestId(CHILD_TEST_ID)).not.toBeInTheDocument()

    for (const { label } of loadingPhases) {
      expect(screen.queryByText(label)).not.toBeInTheDocument()
    }
  })

  const passThroughStatuses: SimStatus[] = ['READY', 'RUNNING', 'PAUSED', 'STOPPED']

  for (const status of passThroughStatuses) {
    it(`renders children for ${status} (not gated on literal READY equality)`, () => {
      renderGate(status)

      expect(screen.getByTestId(CHILD_TEST_ID)).toBeInTheDocument()
    })
  }
})

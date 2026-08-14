import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { BarChart } from '../components/BarChart'

describe('BarChart', () => {
  it('renders an empty-state message when data is empty', () => {
    render(<BarChart data={[]} emptyLabel="Nothing here" />)
    expect(screen.getByTestId('bar-chart-empty')).toHaveTextContent('Nothing here')
    expect(screen.queryByTestId('bar-chart')).not.toBeInTheDocument()
  })

  it('sorts by value descending and caps to maxBars, noting the truncated count', () => {
    render(
      <BarChart
        data={[
          { label: 'a', value: 1 },
          { label: 'b', value: 5 },
          { label: 'c', value: 3 },
        ]}
        maxBars={2}
      />,
    )
    const rows = screen.getAllByTestId(/^bar-chart-row-/)
    expect(rows).toHaveLength(2)
    expect(rows[0]).toHaveTextContent('b')
    expect(rows[1]).toHaveTextContent('c')
    expect(screen.getByTestId('bar-chart-truncation-note')).toHaveTextContent('+1 more')
  })

  it('preserves caller order when sortByValue is false, with no truncation note', () => {
    render(
      <BarChart
        data={[
          { label: '2026-07-01', value: 5 },
          { label: '2026-07-02', value: 1 },
        ]}
        sortByValue={false}
      />,
    )
    const rows = screen.getAllByTestId(/^bar-chart-row-/)
    expect(rows[0]).toHaveTextContent('2026-07-01')
    expect(rows[1]).toHaveTextContent('2026-07-02')
    expect(screen.queryByTestId('bar-chart-truncation-note')).not.toBeInTheDocument()
  })

  it('appends a glossary description as a second line in the existing tooltip, on hover, when descriptions matches the row label', async () => {
    render(
      <BarChart
        data={[{ label: 'DOD_BLOCKED', value: 3 }]}
        descriptions={{ DOD_BLOCKED: 'Verify phase found a failing Definition-of-Done condition.' }}
      />,
    )

    const trigger = screen.getByTestId('bar-chart-row-DOD_BLOCKED')
    trigger.dispatchEvent(new MouseEvent('pointerenter', { bubbles: true }))
    trigger.dispatchEvent(new MouseEvent('pointermove', { bubbles: true }))
    ;(trigger as HTMLElement).focus()

    const tooltips = await screen.findAllByText(
      (_, element) => element?.textContent === 'DOD_BLOCKED · 3Verify phase found a failing Definition-of-Done condition.',
    )
    expect(tooltips.length).toBeGreaterThan(0)
  })

  it('renders a "?" hint icon next to the label when descriptions matches the row label', () => {
    render(
      <BarChart
        data={[{ label: 'DOD_BLOCKED', value: 3 }]}
        descriptions={{ DOD_BLOCKED: 'Verify phase found a failing Definition-of-Done condition.' }}
      />,
    )
    expect(screen.getByTestId('bar-chart-row-DOD_BLOCKED')).toContainElement(
      screen.getByTestId('glossary-hint-icon'),
    )
  })

  it('never renders the hint icon when no description matches', () => {
    render(<BarChart data={[{ label: 'unmapped_label', value: 1 }]} />)
    expect(screen.queryByTestId('glossary-hint-icon')).not.toBeInTheDocument()
  })

  it('renders the original label-only tooltip content, unchanged, when no description matches', async () => {
    render(<BarChart data={[{ label: 'unmapped_label', value: 1 }]} />)

    const trigger = screen.getByTestId('bar-chart-row-unmapped_label')
    trigger.dispatchEvent(new MouseEvent('pointerenter', { bubbles: true }))
    trigger.dispatchEvent(new MouseEvent('pointermove', { bubbles: true }))
    ;(trigger as HTMLElement).focus()

    const tooltips = await screen.findAllByText(
      (_, element) => element?.textContent === 'unmapped_label · 1',
    )
    expect(tooltips.length).toBeGreaterThan(0)
  })
})

import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { GroupedBarChart } from '../components/GroupedBarChart'

describe('GroupedBarChart', () => {
  it('renders an empty-state message when data is empty', () => {
    render(<GroupedBarChart data={[]} series1Label="Count" series2Label="Done" emptyLabel="Nothing here" />)
    expect(screen.getByTestId('grouped-bar-chart-empty')).toHaveTextContent('Nothing here')
  })

  it('renders a legend for both series and a row per data point', () => {
    render(
      <GroupedBarChart
        data={[
          { label: 'standard', series1: 10, series2: 4 },
          { label: 'hotfix', series1: 3, series2: 3 },
        ]}
        series1Label="Count"
        series2Label="Done"
      />,
    )
    const legend = screen.getByTestId('grouped-bar-chart-legend')
    expect(legend).toHaveTextContent('Count')
    expect(legend).toHaveTextContent('Done')
    expect(screen.getByTestId('grouped-bar-chart-row-standard')).toBeInTheDocument()
    expect(screen.getByTestId('grouped-bar-chart-row-hotfix')).toBeInTheDocument()
  })

  it('renders a "?" hint icon next to the label when descriptions matches, none when it does not', () => {
    render(
      <GroupedBarChart
        data={[
          { label: 'standard', series1: 10, series2: 4 },
          { label: 'n/a', series1: 1, series2: 0 },
        ]}
        series1Label="Count"
        series2Label="Done"
        descriptions={{ standard: 'Any new feature, refactor, or substantive repair.' }}
      />,
    )
    const standardRow = screen.getByTestId('grouped-bar-chart-row-standard')
    const naRow = screen.getByTestId('grouped-bar-chart-row-n/a')
    expect(standardRow.querySelector('[data-testid="glossary-hint-icon"]')).not.toBeNull()
    expect(naRow.querySelector('[data-testid="glossary-hint-icon"]')).toBeNull()
  })

  it('shows the glossary description on hover over the LABEL itself, not only the bar underneath — regression guard for the label-not-hoverable bug', async () => {
    render(
      <GroupedBarChart
        data={[{ label: 'standard', series1: 10, series2: 4 }]}
        series1Label="Count"
        series2Label="Done"
        descriptions={{ standard: 'Any new feature, refactor, or substantive repair.' }}
      />,
    )

    // Hover the label text directly (not a bar) — this is exactly what a user does when they see
    // the "?" icon next to the label and hover it, expecting a description.
    const labelTrigger = screen.getByText('standard')
    labelTrigger.dispatchEvent(new MouseEvent('pointerenter', { bubbles: true }))
    labelTrigger.dispatchEvent(new MouseEvent('pointermove', { bubbles: true }))
    labelTrigger.parentElement?.focus()

    const tooltips = await screen.findAllByText('Any new feature, refactor, or substantive repair.')
    expect(tooltips.length).toBeGreaterThan(0)
  })
})

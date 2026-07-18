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
})

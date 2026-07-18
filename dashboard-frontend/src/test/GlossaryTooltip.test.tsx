import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import * as Tooltip from '@radix-ui/react-tooltip'
import { GlossaryTooltip } from '../components/GlossaryTooltip'
import type { GlossaryTerms } from '../api'

// Matches src/test/RecentActivityGantt.test.tsx's own established pattern for asserting a
// Radix Tooltip's on-hover content in jsdom (pointerenter + pointermove + focus, since jsdom does
// not simulate real pointer hover timing the way a browser does).
function hoverTrigger(trigger: Element) {
  trigger.dispatchEvent(new MouseEvent('pointerenter', { bubbles: true }))
  trigger.dispatchEvent(new MouseEvent('pointermove', { bubbles: true }))
  ;(trigger as HTMLElement).focus()
}

const GLOSSARY: GlossaryTerms = {
  DONE: { term: 'DONE', category: 'ticket-status', description: 'Work is complete and closed.' },
}

function renderWithProvider(children: React.ReactNode) {
  return render(<Tooltip.Provider delayDuration={0}>{children}</Tooltip.Provider>)
}

describe('GlossaryTooltip', () => {
  it('renders children plainly, with no tooltip trigger, when the glossary has no matching entry', () => {
    renderWithProvider(
      <GlossaryTooltip term="NOT_A_REAL_TERM" glossary={GLOSSARY}>
        NOT_A_REAL_TERM
      </GlossaryTooltip>,
    )
    expect(screen.getByText('NOT_A_REAL_TERM')).toBeInTheDocument()
    // No underline/cursor-help styling class applied — proves no Tooltip.Trigger wrapper exists,
    // not just that the text happens to render.
    expect(screen.getByText('NOT_A_REAL_TERM')).not.toHaveClass('cursor-help')
  })

  it('renders children plainly when term is null (graceful degradation, never crashes)', () => {
    renderWithProvider(
      <GlossaryTooltip term={null} glossary={GLOSSARY}>
        —
      </GlossaryTooltip>,
    )
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('renders children plainly when the glossary itself is empty (still loading), never crashes', () => {
    renderWithProvider(
      <GlossaryTooltip term="DONE" glossary={{}}>
        DONE
      </GlossaryTooltip>,
    )
    expect(screen.getByText('DONE')).toBeInTheDocument()
  })

  it('wraps children in a hoverable trigger when the glossary has a matching entry', () => {
    renderWithProvider(
      <GlossaryTooltip term="DONE" glossary={GLOSSARY}>
        DONE
      </GlossaryTooltip>,
    )
    expect(screen.getByText('DONE')).toHaveClass('cursor-help')
  })

  it('shows the real backend-sourced description text on hover — never a hardcoded string', async () => {
    renderWithProvider(
      <GlossaryTooltip term="DONE" glossary={GLOSSARY}>
        DONE
      </GlossaryTooltip>,
    )

    const trigger = screen.getByText('DONE')
    hoverTrigger(trigger)

    // Radix mirrors the tooltip text into a visually-hidden accessibility span alongside the
    // visible content div, so more than one element matches the same text — mirrors
    // src/test/RecentActivityGantt.test.tsx's own established workaround for this exact Radix
    // behavior (findAllByText + take the first, rather than a getByText that throws on multiple
    // matches).
    const tooltips = await screen.findAllByText('Work is complete and closed.')
    expect(tooltips.length).toBeGreaterThan(0)
    expect(tooltips[0]).not.toBe(trigger)
  })
})

import * as Tooltip from '@radix-ui/react-tooltip'
import type { ReactNode } from 'react'
import type { GlossaryTerms } from '@/api'

export interface GlossaryTooltipProps {
  term: string | null
  glossary: GlossaryTerms
  children: ReactNode
}

// Shared wrapper so every call site looks up its description from the fetched glossary the same
// way, rather than four separate ad-hoc Radix Tooltip wirings (this repo's own established
// precedent — FilterSelect/StatTile/BarChart are all exactly this "one shared component" pattern
// already). Description text always comes from `glossary` (backend-fetched) — this component
// itself never contains a single hardcoded description string.
//
// Graceful degradation (required by this ticket's architectural constraint): if `term` is null/
// empty, or the glossary has no entry for it (registry genuinely has no entry, or the glossary
// hasn't finished loading yet), renders `children` completely unwrapped — no tooltip trigger, no
// broken/empty popover, never blocks the label itself from rendering.
export function GlossaryTooltip({ term, glossary, children }: GlossaryTooltipProps) {
  // `glossary` should always be a real object (useGlossary() defaults to {} on any fetch
  // failure/malformed response), but a direct caller could still pass something else — never
  // trust the shape blindly, since a crash here would break the label's own rendering too.
  const entry = term && glossary ? glossary[term] : undefined

  if (!entry) {
    return <>{children}</>
  }

  return (
    <Tooltip.Root>
      <Tooltip.Trigger asChild>
        <span className="cursor-help underline decoration-dotted decoration-text-secondary underline-offset-2">
          {children}
        </span>
      </Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content
          collisionPadding={8}
          className="rounded-md bg-bg-tertiary px-2 py-1 text-[11px] text-text-primary border border-border max-w-[280px] whitespace-normal"
        >
          {entry.description}
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  )
}

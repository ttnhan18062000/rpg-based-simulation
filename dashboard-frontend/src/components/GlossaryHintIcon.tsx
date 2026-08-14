// Shared small "?" affordance marking a label as hoverable for a glossary description — used by
// GlossaryTooltip (Tickets/Replay/Stats table cells) and BarChart/GroupedBarChart (chart row
// labels), which each wire their own Radix Tooltip.Trigger/Content directly rather than wrapping
// in GlossaryTooltip (their tooltip content already carries chart-specific text — value, series —
// alongside the optional description, which GlossaryTooltip's single-purpose API doesn't support).
// Purely decorative: the icon itself carries no description text and is never a tooltip trigger
// on its own — the caller's existing Tooltip.Trigger covers the whole row/cell already.
export function GlossaryHintIcon() {
  return (
    <span
      aria-hidden="true"
      data-testid="glossary-hint-icon"
      className="inline-flex h-3 w-3 shrink-0 items-center justify-center rounded-full border border-text-secondary text-[8px] leading-none text-text-secondary select-none"
    >
      ?
    </span>
  )
}

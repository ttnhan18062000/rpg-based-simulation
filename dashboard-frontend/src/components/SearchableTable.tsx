import { useMemo, useState } from 'react'

export interface SearchableTableColumn<T> {
  key: string
  header: React.ReactNode
  /** Value used for both sorting and search matching. Numbers sort numerically, strings via localeCompare. */
  accessor: (row: T) => string | number
  /** Display override — defaults to String(accessor(row)). */
  render?: (row: T) => React.ReactNode
  sortable?: boolean
  numeric?: boolean
}

export interface SearchableTableProps<T> {
  testId: string
  columns: SearchableTableColumn<T>[]
  rows: T[]
  rowKey: (row: T) => string
  /** Overrides the auto-generated `${testId}-row-${rowKey(row)}` data-testid — pass this when a
   * table is replacing a pre-existing one whose row testid convention other tests already assert
   * against. */
  rowTestId?: (row: T) => string
  defaultSortKey?: string
  defaultSortDir?: 'asc' | 'desc'
  emptyLabel?: string
  pageSizeOptions?: number[]
  searchPlaceholder?: string
}

const DEFAULT_PAGE_SIZE_OPTIONS = [10, 25, 50, 100]

/** Client-side search + sort + pagination over an already-fetched row array. Reusable across the
 * Agent Ops Dashboard's Stats tab tables (top agents, phase status, slow runs, duration outliers,
 * KGMCP per-ticket/per-agent breakdowns) — one implementation instead of bespoke pagination logic
 * per section. */
export function SearchableTable<T>({
  testId,
  columns,
  rows,
  rowKey,
  rowTestId,
  defaultSortKey,
  defaultSortDir = 'desc',
  emptyLabel = 'No data',
  pageSizeOptions = DEFAULT_PAGE_SIZE_OPTIONS,
  searchPlaceholder = 'Search…',
}: SearchableTableProps<T>) {
  const [query, setQuery] = useState('')
  const [sortKey, setSortKey] = useState<string | undefined>(defaultSortKey)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>(defaultSortDir)
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(pageSizeOptions[0])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return rows
    return rows.filter((row) => columns.some((col) => String(col.accessor(row)).toLowerCase().includes(q)))
  }, [rows, columns, query])

  const sorted = useMemo(() => {
    const col = columns.find((c) => c.key === sortKey)
    if (!col) return filtered
    const dir = sortDir === 'asc' ? 1 : -1
    return [...filtered].sort((a, b) => {
      const av = col.accessor(a)
      const bv = col.accessor(b)
      if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * dir
      return String(av).localeCompare(String(bv)) * dir
    })
  }, [filtered, columns, sortKey, sortDir])

  const pageCount = Math.max(1, Math.ceil(sorted.length / pageSize))
  const clampedPage = Math.min(page, pageCount - 1)
  const pageRows = sorted.slice(clampedPage * pageSize, clampedPage * pageSize + pageSize)

  function toggleSort(key: string) {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
    setPage(0)
  }

  return (
    <div className="flex flex-col gap-2" data-testid={`${testId}-container`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setPage(0)
          }}
          placeholder={searchPlaceholder}
          data-testid={`${testId}-search`}
          className="bg-bg-tertiary border border-border rounded-md px-2 py-1 text-text-primary text-[11px] min-w-[160px]"
        />
        <div className="flex items-center gap-2 text-[11px] text-text-secondary">
          <span data-testid={`${testId}-count`}>
            {sorted.length === rows.length
              ? `${rows.length} total`
              : `${sorted.length} of ${rows.length}`}
          </span>
          <label className="flex items-center gap-1">
            Rows per page
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value))
                setPage(0)
              }}
              data-testid={`${testId}-page-size`}
              className="bg-bg-tertiary border border-border rounded-md px-1 py-0.5 text-text-primary"
            >
              {pageSizeOptions.map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <table className="text-[11px] w-full border-collapse" data-testid={testId}>
        <thead>
          <tr className="text-left text-text-secondary border-b border-border">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`py-1 pr-3 ${col.sortable !== false ? 'cursor-pointer select-none' : ''}`}
                data-testid={`${testId}-col-header-${col.key}`}
                onClick={col.sortable !== false ? () => toggleSort(col.key) : undefined}
              >
                {col.header}
                {sortKey === col.key ? (sortDir === 'asc' ? ' ▲' : ' ▼') : ''}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {pageRows.map((row) => (
            <tr
              key={rowKey(row)}
              data-testid={rowTestId ? rowTestId(row) : `${testId}-row-${rowKey(row)}`}
              className="border-b border-border"
            >
              {columns.map((col) => (
                <td key={col.key} className={`py-1 pr-3 ${col.numeric ? 'tabular-nums' : ''}`}>
                  {col.render ? col.render(row) : String(col.accessor(row))}
                </td>
              ))}
            </tr>
          ))}
          {pageRows.length === 0 && (
            <tr>
              <td className="py-1 pr-3 text-text-secondary" colSpan={columns.length}>
                {rows.length === 0 ? emptyLabel : 'No rows match this search'}
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {pageCount > 1 && (
        <div className="flex items-center justify-end gap-2 text-[11px] text-text-secondary">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={clampedPage === 0}
            data-testid={`${testId}-prev-page`}
            className="border border-border rounded-md px-2 py-0.5 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Prev
          </button>
          <span data-testid={`${testId}-page-indicator`}>
            Page {clampedPage + 1} of {pageCount}
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
            disabled={clampedPage >= pageCount - 1}
            data-testid={`${testId}-next-page`}
            className="border border-border rounded-md px-2 py-0.5 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}

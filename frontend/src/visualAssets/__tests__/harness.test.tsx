import { render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { RehearsalHarness } from '../RehearsalHarness'
import { fixtureManifestText, fixtureUrlFor } from '../fixtureSource'
import { bitmap, manifestWith, RecordingContext } from './helpers'
import type { Decode } from '../loader'

let contexts: RecordingContext[]

beforeEach(() => {
  contexts = []
  vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockImplementation(() => {
    const ctx = new RecordingContext()
    contexts.push(ctx)
    return ctx as unknown as CanvasRenderingContext2D
  })
})
afterEach(() => vi.restoreAllMocks())

const okDecode: Decode = async () => bitmap()

async function settled() {
  await waitFor(() => expect(screen.getByTestId('rehearsal').getAttribute('data-settled')).toBe('true'))
}
const texts = () => screen.getAllByTestId('cell-text').map((n) => n.textContent ?? '')

describe('RehearsalHarness', () => {
  it('draws one native cell per key and the crowded scene from the fixture release', async () => {
    render(<RehearsalHarness manifestText={fixtureManifestText} urlFor={fixtureUrlFor} decode={okDecode} />)
    await settled()
    expect(screen.getByTestId('rehearsal').getAttribute('data-generation')).toMatch(/^sha256:/)
    expect(texts().map((t) => t.split(':')[0])).toEqual([
      'fixture.rehearsal.gem (item)', 'fixture.rehearsal.rock (terrain)', 'fixture.rehearsal.frame (ui)', 'fixture.rehearsal.absent (unknown visual)',
    ])
    expect(texts()[0]).toContain('image 16x16')
    expect(texts()[3]).toContain('not in this release')
    const canvases = [...document.querySelectorAll('canvas')]
    expect(canvases.map((c) => [c.width, c.height])).toEqual([[16, 16], [16, 16], [16, 16], [16, 16], [192, 128]])
    expect(canvases.every((c) => c.style.imageRendering === 'pixelated')).toBe(true)
    expect(contexts.every((c) => c.imageSmoothingEnabled === false || c.calls.length === 0)).toBe(true)
  })

  it('shows the manifest_invalid fallback everywhere, with an alert, for an invalid manifest', async () => {
    render(<RehearsalHarness manifestText={manifestWith((r) => { r.schema_version = 2 })} urlFor={fixtureUrlFor} decode={okDecode} />)
    await settled()
    expect(screen.getByRole('alert').textContent).toContain('unsupported_version')
    expect(texts().every((t) => t.includes('manifest invalid'))).toBe(true)
  })

  it('shows decode_failed for a corrupt image and missing_image for one the build lacks', async () => {
    const corrupt: Decode = async () => { throw new Error('corrupt') }
    const { unmount } = render(<RehearsalHarness manifestText={fixtureManifestText} urlFor={fixtureUrlFor} decode={corrupt} />)
    await settled()
    expect(texts().slice(0, 3).every((t) => t.includes('could not be decoded'))).toBe(true)
    unmount()
    render(<RehearsalHarness manifestText={fixtureManifestText} urlFor={() => undefined} decode={okDecode} />)
    await waitFor(() => expect(screen.getAllByTestId('cell-text').slice(0, 3).every((n) => n.textContent?.includes('image missing'))).toBe(true))
  })

  it('does not touch the network or the simulation: no fetch is made', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch')
    render(<RehearsalHarness manifestText={fixtureManifestText} urlFor={fixtureUrlFor} decode={okDecode} />)
    await settled()
    expect(fetchSpy).not.toHaveBeenCalled()
  })
})

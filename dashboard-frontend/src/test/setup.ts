import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// jsdom has no ResizeObserver; @radix-ui/react-slider's useSize hook requires
// one to measure the track, so every test that renders PlaybackScrubber needs
// this stub regardless of whether it asserts on layout.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver

// Run cleanup after each test case (e.g. clearing jsdom)
afterEach(() => {
  cleanup()
})

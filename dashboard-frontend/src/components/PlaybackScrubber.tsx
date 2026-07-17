import { useEffect, useState } from 'react'
import * as Slider from '@radix-ui/react-slider'

type PlaybackSpeed = 1 | 5 | 20

const SPEED_OPTIONS: PlaybackSpeed[] = [1, 5, 20]

export interface PlaybackScrubberProps {
  maxIndex: number
  index: number
  onIndexChange: (index: number) => void
}

// Deliberately ignorant of RunTimeline/TimelineEntry/RawToolCall — operates
// on a bare integer index range so "scrub never fetches" is structural, not
// just tested (see plan.md Step 2).
export function PlaybackScrubber({ maxIndex, index, onIndexChange }: PlaybackScrubberProps) {
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState<PlaybackSpeed>(1)

  useEffect(() => {
    if (!playing) {
      return
    }
    if (index >= maxIndex) {
      setPlaying(false)
      return
    }
    const intervalId = setInterval(() => {
      onIndexChange(Math.min(index + 1, maxIndex))
    }, 1000 / speed)
    return () => clearInterval(intervalId)
  }, [playing, speed, index, maxIndex, onIndexChange])

  return (
    <div className="flex items-center gap-3" data-testid="playback-scrubber">
      <button
        type="button"
        onClick={() => setPlaying((prev) => !prev)}
        disabled={maxIndex <= 0}
        className="px-2.5 py-1 rounded-md text-[11px] font-semibold text-text-secondary hover:text-text-primary hover:bg-bg-tertiary disabled:opacity-40"
      >
        {playing ? 'Pause' : 'Play'}
      </button>
      {maxIndex > 0 ? (
        <Slider.Root
          className="relative flex items-center flex-1 h-4 select-none touch-none"
          value={[index]}
          min={0}
          max={maxIndex}
          step={1}
          onValueChange={([value]) => onIndexChange(value)}
        >
          <Slider.Track className="relative h-1 flex-1 rounded-full bg-bg-tertiary">
            <Slider.Range className="absolute h-full rounded-full bg-accent-blue" />
          </Slider.Track>
          <Slider.Thumb className="block w-3 h-3 rounded-full bg-accent-blue" aria-label="Playback position" />
        </Slider.Root>
      ) : (
        // Radix Slider divides by (max - min); a single-entry timeline has
        // maxIndex === 0, which would make min === max and produce a NaN
        // percentage. Nothing to scrub across in that case anyway.
        <div className="relative flex-1 h-4" />
      )}
      <div className="flex items-center gap-1">
        {SPEED_OPTIONS.map((option) => (
          <button
            key={option}
            type="button"
            onClick={() => setSpeed(option)}
            className={`px-2 py-1 rounded-md text-[11px] font-semibold ${
              speed === option
                ? 'bg-accent-blue/15 text-accent-blue'
                : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary'
            }`}
          >
            {option}x
          </button>
        ))}
      </div>
    </div>
  )
}

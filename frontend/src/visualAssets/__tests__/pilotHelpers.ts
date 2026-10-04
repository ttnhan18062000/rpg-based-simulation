import type { PilotCtx } from '../pilotScene'

// A recording 2D context for the pilot scene (every call the scene may make), shared by the pilot tests.
export class Recorder {
  calls: [string, ...unknown[]][] = []
  fills: string[] = []
  fillStyle: string | CanvasGradient | CanvasPattern = ''
  strokeStyle: string | CanvasGradient | CanvasPattern = ''
  lineWidth = 1
  globalAlpha = 1
  font = ''
  textAlign: CanvasTextAlign = 'start'
  textBaseline: CanvasTextBaseline = 'alphabetic'
  imageSmoothingEnabled = true
  shadowColor = ''
  shadowBlur = 0
  fillRect(...a: number[]) { this.fills.push(String(this.fillStyle)); this.calls.push(['fillRect', ...a]) }
  strokeRect(...a: number[]) { this.calls.push(['strokeRect', ...a]) }
  clearRect(...a: number[]) { this.calls.push(['clearRect', ...a]) }
  drawImage(...a: unknown[]) { this.calls.push(['drawImage', ...a]) }
  fillText(...a: unknown[]) { this.calls.push(['fillText', ...a]) }
  save() { this.calls.push(['save']) }
  restore() { this.calls.push(['restore']) }
  beginPath() { this.calls.push(['beginPath']) }
  moveTo(...a: number[]) { this.calls.push(['moveTo', ...a]) }
  lineTo(...a: number[]) { this.calls.push(['lineTo', ...a]) }
  closePath() { this.calls.push(['closePath']) }
  arc(...a: number[]) { this.calls.push(['arc', ...a]) }
  fill() { this.calls.push(['fill']) }
  stroke() { this.calls.push(['stroke']) }
  of(name: string) { return this.calls.filter((c) => c[0] === name) }
  asCtx(): PilotCtx { return this as unknown as PilotCtx }
}

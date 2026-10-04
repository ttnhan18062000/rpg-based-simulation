// The browser's decoder for the loader: fetch the build's own URL, decode with createImageBitmap. A failure of either throws.
import type { Bitmap } from './loader'

export async function browserDecode(url: string): Promise<Bitmap> {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return createImageBitmap(await response.blob())
}

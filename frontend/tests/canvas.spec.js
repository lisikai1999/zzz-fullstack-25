import { describe, it, expect } from 'vitest'
import { screenToImage, imageToScreen, distance, bboxFromPoints } from '../src/utils/geometry'

describe('geometry utilities', () => {
  describe('screenToImage / imageToScreen roundtrip', () => {
    it('round-trips at scale=1, no offset', () => {
      const transform = { scale: 1, offsetX: 0, offsetY: 0 }
      const img = screenToImage(100, 200, transform)
      expect(img.x).toBe(100)
      expect(img.y).toBe(200)
      const screen = imageToScreen(img.x, img.y, transform)
      expect(screen.x).toBe(100)
      expect(screen.y).toBe(200)
    })

    it('round-trips with scale and offset', () => {
      const transform = { scale: 2, offsetX: 50, offsetY: 30 }
      const screen = { x: 150, y: 130 }
      const img = screenToImage(screen.x, screen.y, transform)
      expect(img.x).toBeCloseTo(50)
      expect(img.y).toBeCloseTo(50)
      const backToScreen = imageToScreen(img.x, img.y, transform)
      expect(backToScreen.x).toBeCloseTo(screen.x)
      expect(backToScreen.y).toBeCloseTo(screen.y)
    })

    it('handles fractional scale', () => {
      const transform = { scale: 0.5, offsetX: 10, offsetY: 20 }
      const img = screenToImage(60, 70, transform)
      expect(img.x).toBeCloseTo(100)
      expect(img.y).toBeCloseTo(100)
    })
  })

  describe('distance', () => {
    it('calculates distance between two points', () => {
      expect(distance({ x: 0, y: 0 }, { x: 3, y: 4 })).toBeCloseTo(5)
    })

    it('returns 0 for same point', () => {
      expect(distance({ x: 5, y: 5 }, { x: 5, y: 5 })).toBe(0)
    })
  })

  describe('bboxFromPoints', () => {
    it('creates bbox from top-left to bottom-right drag', () => {
      const bbox = bboxFromPoints({ x: 10, y: 20 }, { x: 100, y: 80 })
      expect(bbox.x).toBe(10)
      expect(bbox.y).toBe(20)
      expect(bbox.w).toBe(90)
      expect(bbox.h).toBe(60)
    })

    it('handles reverse direction drag (bottom-right to top-left)', () => {
      const bbox = bboxFromPoints({ x: 100, y: 80 }, { x: 10, y: 20 })
      expect(bbox.x).toBe(10)
      expect(bbox.y).toBe(20)
      expect(bbox.w).toBe(90)
      expect(bbox.h).toBe(60)
    })
  })
})

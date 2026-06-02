import { screenToImage, bboxFromPoints } from '../../utils/geometry'

export default {
  name: 'bbox',
  cursor: 'crosshair',
  state: { startPoint: null, currentRect: null, isDrawing: false },

  onMouseDown(point) {
    this.state.startPoint = point
    this.state.isDrawing = true
    this.state.currentRect = null
  },

  onMouseMove(point) {
    if (!this.state.isDrawing) return
    this.state.currentRect = bboxFromPoints(this.state.startPoint, point)
  },

  onMouseUp(point) {
    if (!this.state.isDrawing) return
    this.state.isDrawing = false
    const rect = bboxFromPoints(this.state.startPoint, point)
    this.state.currentRect = null

    if (rect.w < 3 || rect.h < 3) return null

    return {
      type: 'bbox',
      coords: [rect.x, rect.y, rect.x + rect.w, rect.y + rect.h],
    }
  },

  render(ctx, color = '#FF6B6B') {
    if (!this.state.currentRect) return
    const r = this.state.currentRect
    ctx.strokeStyle = color
    ctx.lineWidth = 2
    ctx.setLineDash([5, 3])
    ctx.strokeRect(r.x, r.y, r.w, r.h)
    ctx.setLineDash([])
    ctx.fillStyle = color + '15'
    ctx.fillRect(r.x, r.y, r.w, r.h)
  },

  reset() {
    this.state = { startPoint: null, currentRect: null, isDrawing: false }
  },
}

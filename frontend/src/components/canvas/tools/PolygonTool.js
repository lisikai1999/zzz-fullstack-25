import { distance } from '../../utils/geometry'

export default {
  name: 'polygon',
  cursor: 'crosshair',
  state: { points: [], isDrawing: false, hoverPoint: null },

  onMouseDown(point) {
    if (!this.state.isDrawing) {
      this.state.isDrawing = true
      this.state.points = [point]
    } else {
      if (this.state.points.length > 2 && distance(point, this.state.points[0]) < 10) {
        return this.finish()
      }
      this.state.points.push(point)
    }
    return null
  },

  onMouseMove(point) {
    this.state.hoverPoint = point
  },

  onMouseUp() {
    return null
  },

  onDblClick() {
    if (this.state.points.length >= 3) {
      return this.finish()
    }
    return null
  },

  finish() {
    const points = [...this.state.points]
    this.reset()
    if (points.length < 3) return null
    return {
      type: 'polygon',
      points: points.map(p => [Math.round(p.x), Math.round(p.y)]),
    }
  },

  render(ctx, color = '#4ECDC4') {
    const pts = this.state.points
    if (pts.length === 0) return

    ctx.strokeStyle = color
    ctx.lineWidth = 2
    ctx.fillStyle = color + '20'

    ctx.beginPath()
    ctx.moveTo(pts[0].x, pts[0].y)
    for (let i = 1; i < pts.length; i++) {
      ctx.lineTo(pts[i].x, pts[i].y)
    }
    if (this.state.hoverPoint && this.state.isDrawing) {
      ctx.lineTo(this.state.hoverPoint.x, this.state.hoverPoint.y)
    }
    ctx.stroke()

    if (pts.length >= 3) {
      ctx.closePath()
      ctx.fill()
    }

    for (const p of pts) {
      ctx.fillStyle = color
      ctx.beginPath()
      ctx.arc(p.x, p.y, 4, 0, Math.PI * 2)
      ctx.fill()
    }

    // Highlight close-to-first-point indicator
    if (pts.length > 2 && this.state.hoverPoint && distance(this.state.hoverPoint, pts[0]) < 10) {
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.arc(pts[0].x, pts[0].y, 8, 0, Math.PI * 2)
      ctx.stroke()
    }
  },

  reset() {
    this.state = { points: [], isDrawing: false, hoverPoint: null }
  },
}

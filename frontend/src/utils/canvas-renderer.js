const ANNOTATION_COLORS = [
  '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
  '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F',
]

export function getColorForUser(index) {
  return ANNOTATION_COLORS[index % ANNOTATION_COLORS.length]
}

export function renderBbox(ctx, coords, color, lineWidth = 2) {
  const [x1, y1, x2, y2] = coords
  ctx.strokeStyle = color
  ctx.lineWidth = lineWidth
  ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)

  ctx.fillStyle = color + '20'
  ctx.fillRect(x1, y1, x2 - x1, y2 - y1)
}

export function renderPolygon(ctx, points, color, lineWidth = 2) {
  if (points.length < 2) return

  ctx.strokeStyle = color
  ctx.lineWidth = lineWidth
  ctx.fillStyle = color + '30'

  ctx.beginPath()
  ctx.moveTo(points[0][0], points[0][1])
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(points[i][0], points[i][1])
  }
  ctx.closePath()
  ctx.fill()
  ctx.stroke()

  for (const p of points) {
    ctx.fillStyle = color
    ctx.beginPath()
    ctx.arc(p[0], p[1], 3, 0, Math.PI * 2)
    ctx.fill()
  }
}

export function renderMask(ctx, maskCanvas, color) {
  ctx.globalAlpha = 0.4
  ctx.drawImage(maskCanvas, 0, 0)
  ctx.globalAlpha = 1.0
}

export function renderLabel(ctx, text, x, y, color) {
  ctx.font = '12px sans-serif'
  const metrics = ctx.measureText(text)
  const padding = 4

  ctx.fillStyle = color
  ctx.fillRect(x, y - 14, metrics.width + padding * 2, 18)

  ctx.fillStyle = 'white'
  ctx.fillText(text, x + padding, y)
}

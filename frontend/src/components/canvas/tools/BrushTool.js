export default {
  name: 'brush',
  cursor: 'none',
  state: { isPainting: false, brushSize: 15, isEraser: false, maskCanvas: null, maskCtx: null },

  init(width, height) {
    if (typeof OffscreenCanvas !== 'undefined') {
      this.state.maskCanvas = new OffscreenCanvas(width, height)
    } else {
      this.state.maskCanvas = document.createElement('canvas')
      this.state.maskCanvas.width = width
      this.state.maskCanvas.height = height
    }
    this.state.maskCtx = this.state.maskCanvas.getContext('2d')
  },

  onMouseDown(point) {
    this.state.isPainting = true
    this.paint(point)
  },

  onMouseMove(point) {
    if (this.state.isPainting) {
      this.paint(point)
    }
  },

  onMouseUp() {
    this.state.isPainting = false
    return null
  },

  paint(point) {
    const ctx = this.state.maskCtx
    if (!ctx) return

    if (this.state.isEraser) {
      ctx.globalCompositeOperation = 'destination-out'
    } else {
      ctx.globalCompositeOperation = 'source-over'
      ctx.fillStyle = 'rgba(255, 100, 100, 1)'
    }
    ctx.beginPath()
    ctx.arc(point.x, point.y, this.state.brushSize / 2, 0, Math.PI * 2)
    ctx.fill()
  },

  getMaskData() {
    if (!this.state.maskCanvas) return null
    const width = this.state.maskCanvas.width
    const height = this.state.maskCanvas.height
    const imageData = this.state.maskCtx.getImageData(0, 0, width, height)
    const data = imageData.data

    const counts = []
    let currentIsOn = false
    let currentCount = 0

    for (let i = 0; i < width * height; i++) {
      const isOn = data[i * 4 + 3] > 0
      if (isOn === currentIsOn) {
        currentCount++
      } else {
        counts.push(currentCount)
        currentIsOn = isOn
        currentCount = 1
      }
    }
    counts.push(currentCount)

    return { type: 'mask', rle: { counts, size: [height, width] } }
  },

  render(ctx, color = '#FF6B6B') {
    if (!this.state.maskCanvas) return
    ctx.globalAlpha = 0.4
    ctx.drawImage(this.state.maskCanvas, 0, 0)
    ctx.globalAlpha = 1.0
  },

  reset() {
    if (this.state.maskCtx) {
      const w = this.state.maskCanvas.width
      const h = this.state.maskCanvas.height
      this.state.maskCtx.clearRect(0, 0, w, h)
    }
    this.state.isPainting = false
  },
}

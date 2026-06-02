export default {
  name: 'panzoom',
  cursor: 'grab',
  state: { isPanning: false, lastPoint: null },

  onMouseDown(point, e, transform) {
    this.state.isPanning = true
    this.state.lastPoint = { x: e.clientX, y: e.clientY }
    this.cursor = 'grabbing'
  },

  onMouseMove(point, e, transform) {
    if (!this.state.isPanning) return
    const dx = e.clientX - this.state.lastPoint.x
    const dy = e.clientY - this.state.lastPoint.y
    transform.offsetX += dx
    transform.offsetY += dy
    this.state.lastPoint = { x: e.clientX, y: e.clientY }
  },

  onMouseUp() {
    this.state.isPanning = false
    this.cursor = 'grab'
    return null
  },

  handleWheel(e, transform, canvasRect) {
    e.preventDefault()
    const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1
    const mouseX = e.clientX - canvasRect.left
    const mouseY = e.clientY - canvasRect.top

    transform.offsetX = mouseX - (mouseX - transform.offsetX) * zoomFactor
    transform.offsetY = mouseY - (mouseY - transform.offsetY) * zoomFactor
    transform.scale *= zoomFactor
  },

  render() {},
  reset() {
    this.state = { isPanning: false, lastPoint: null }
  },
}

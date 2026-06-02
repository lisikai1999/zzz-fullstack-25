<template>
  <div class="annotation-canvas-wrapper" ref="wrapperRef">
    <canvas
      ref="canvasRef"
      @mousedown="handleMouseDown"
      @mousemove="handleMouseMove"
      @mouseup="handleMouseUp"
      @dblclick="handleDblClick"
      @wheel="handleWheel"
      @contextmenu.prevent
      :style="{ cursor: activeTool?.cursor || 'default' }"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { screenToImage } from '../../utils/geometry'
import { renderBbox, renderPolygon, renderLabel, getColorForUser } from '../../utils/canvas-renderer'
import BoundingBoxTool from './tools/BoundingBoxTool'
import PolygonTool from './tools/PolygonTool'
import BrushTool from './tools/BrushTool'
import PanZoomTool from './tools/PanZoomTool'

const props = defineProps({
  imageUrl: { type: String, default: null },
  imageWidth: { type: Number, default: 512 },
  imageHeight: { type: Number, default: 512 },
  annotations: { type: Array, default: () => [] },
  layers: { type: Array, default: () => [] },
  activeToolName: { type: String, default: 'bbox' },
  readOnly: { type: Boolean, default: false },
})

const emit = defineEmits(['annotation-created', 'annotation-updated'])

const canvasRef = ref(null)
const wrapperRef = ref(null)
const transform = ref({ scale: 1, offsetX: 0, offsetY: 0 })
const image = ref(null)
let animFrameId = null

const tools = { bbox: BoundingBoxTool, polygon: PolygonTool, brush: BrushTool, panzoom: PanZoomTool }
const activeTool = computed(() => tools[props.activeToolName])

function getCanvasPoint(e) {
  const rect = canvasRef.value.getBoundingClientRect()
  const screenX = e.clientX - rect.left
  const screenY = e.clientY - rect.top
  return screenToImage(screenX, screenY, transform.value)
}

function handleMouseDown(e) {
  if (props.readOnly) return
  const point = getCanvasPoint(e)
  const tool = activeTool.value
  if (!tool) return

  if (tool.name === 'panzoom') {
    tool.onMouseDown(point, e, transform.value)
  } else {
    const result = tool.onMouseDown(point)
    if (result) emit('annotation-created', result)
  }
}

function handleMouseMove(e) {
  if (props.readOnly) return
  const point = getCanvasPoint(e)
  const tool = activeTool.value
  if (!tool) return

  if (tool.name === 'panzoom') {
    tool.onMouseMove(point, e, transform.value)
  } else {
    tool.onMouseMove(point)
  }
}

function handleMouseUp(e) {
  if (props.readOnly) return
  const point = getCanvasPoint(e)
  const tool = activeTool.value
  if (!tool) return

  if (tool.name === 'panzoom') {
    tool.onMouseUp()
  } else {
    const result = tool.onMouseUp(point)
    if (result) emit('annotation-created', result)
  }
}

function handleDblClick(e) {
  if (props.readOnly) return
  const tool = activeTool.value
  if (tool && tool.onDblClick) {
    const result = tool.onDblClick()
    if (result) emit('annotation-created', result)
  }
}

function handleWheel(e) {
  PanZoomTool.handleWheel(e, transform.value, canvasRef.value.getBoundingClientRect())
}

function render() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')

  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.save()
  ctx.translate(transform.value.offsetX, transform.value.offsetY)
  ctx.scale(transform.value.scale, transform.value.scale)

  // Draw background
  ctx.fillStyle = '#1a1a2e'
  ctx.fillRect(0, 0, props.imageWidth, props.imageHeight)

  // Draw image
  if (image.value) {
    ctx.drawImage(image.value, 0, 0, props.imageWidth, props.imageHeight)
  } else {
    // Placeholder grid
    ctx.strokeStyle = '#333'
    ctx.lineWidth = 0.5
    for (let x = 0; x < props.imageWidth; x += 32) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, props.imageHeight); ctx.stroke()
    }
    for (let y = 0; y < props.imageHeight; y += 32) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(props.imageWidth, y); ctx.stroke()
    }
  }

  // Draw annotations from layers
  const layerData = props.layers.length > 0 ? props.layers : [{ annotations: props.annotations, visible: true, opacity: 1, color: '#FF6B6B' }]

  for (const layer of layerData) {
    if (!layer.visible) continue
    ctx.globalAlpha = layer.opacity ?? 1

    for (const ann of (layer.annotations || [])) {
      const color = layer.color || getColorForUser(ann.user_id || 0)
      const data = typeof ann.data_json === 'string' ? JSON.parse(ann.data_json) : ann.data_json || ann

      if (ann.annotation_type === 'bbox' || data.type === 'bbox') {
        renderBbox(ctx, data.coords, color)
        if (ann.label) renderLabel(ctx, ann.label, data.coords[0], data.coords[1], color)
      } else if (ann.annotation_type === 'polygon' || data.type === 'polygon') {
        renderPolygon(ctx, data.points, color)
        if (ann.label && data.points.length > 0) renderLabel(ctx, ann.label, data.points[0][0], data.points[0][1], color)
      }
    }
  }
  ctx.globalAlpha = 1

  // Draw active tool preview
  const tool = activeTool.value
  if (tool && tool.render && !props.readOnly) {
    tool.render(ctx)
  }

  ctx.restore()
  animFrameId = requestAnimationFrame(render)
}

function resizeCanvas() {
  const canvas = canvasRef.value
  const wrapper = wrapperRef.value
  if (!canvas || !wrapper) return
  canvas.width = wrapper.clientWidth
  canvas.height = wrapper.clientHeight
}

onMounted(() => {
  resizeCanvas()
  window.addEventListener('resize', resizeCanvas)

  if (props.imageUrl) {
    const img = new Image()
    img.onload = () => { image.value = img }
    img.src = props.imageUrl
  }

  BrushTool.init(props.imageWidth, props.imageHeight)
  render()
})

onUnmounted(() => {
  if (animFrameId) cancelAnimationFrame(animFrameId)
  window.removeEventListener('resize', resizeCanvas)
})

watch(() => props.imageUrl, (url) => {
  if (url) {
    const img = new Image()
    img.onload = () => { image.value = img }
    img.src = url
  }
})
</script>

<style scoped>
.annotation-canvas-wrapper {
  width: 100%;
  height: 100%;
  min-height: 500px;
  position: relative;
  background: #0d0d1a;
  border-radius: 8px;
  overflow: hidden;
}

canvas {
  display: block;
  width: 100%;
  height: 100%;
}
</style>

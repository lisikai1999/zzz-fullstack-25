<template>
  <div class="overlay-diff">
    <h4>重叠对比视图</h4>
    <div class="overlay-canvas-wrapper">
      <canvas ref="overlayCanvas" width="512" height="512" />
    </div>
    <div class="overlay-legend">
      <div v-for="(annotator, idx) in annotators" :key="annotator.user_id" class="legend-item">
        <span class="legend-color" :style="{ background: colors[idx] }"></span>
        <span>{{ annotator.username }}</span>
      </div>
      <div class="legend-item">
        <span class="legend-color" style="background: rgba(255,0,0,0.5)"></span>
        <span>差异区域</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { renderBbox, renderPolygon } from '../../utils/canvas-renderer'

const props = defineProps({
  annotators: { type: Array, default: () => [] },
  image: { type: Object, default: () => ({}) },
})

const overlayCanvas = ref(null)
const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']

function drawOverlay() {
  const canvas = overlayCanvas.value
  if (!canvas || !props.annotators.length) return
  const ctx = canvas.getContext('2d')
  const w = props.image.width || 512
  const h = props.image.height || 512
  canvas.width = w
  canvas.height = h

  ctx.fillStyle = '#1a1a2e'
  ctx.fillRect(0, 0, w, h)

  // Draw grid
  ctx.strokeStyle = '#333'
  ctx.lineWidth = 0.5
  for (let x = 0; x < w; x += 32) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke()
  }
  for (let y = 0; y < h; y += 32) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke()
  }

  // Draw each annotator's annotations with their color
  props.annotators.forEach((annotator, idx) => {
    const color = colors[idx % colors.length]
    ctx.globalAlpha = 0.5

    for (const ann of annotator.annotations) {
      const data = typeof ann.data_json === 'string' ? JSON.parse(ann.data_json) : ann.data_json

      if (ann.annotation_type === 'bbox' && data.coords) {
        renderBbox(ctx, data.coords, color, 3)
      } else if (ann.annotation_type === 'polygon' && data.points) {
        renderPolygon(ctx, data.points, color, 3)
      }
    }
  })

  ctx.globalAlpha = 1.0
}

onMounted(drawOverlay)
watch(() => props.annotators, drawOverlay, { deep: true })
</script>

<style scoped>
.overlay-diff {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.overlay-diff h4 {
  font-size: 14px;
  margin-bottom: 12px;
  color: #333;
}

.overlay-canvas-wrapper {
  border-radius: 6px;
  overflow: hidden;
  background: #0d0d1a;
}

.overlay-canvas-wrapper canvas {
  display: block;
  width: 100%;
  height: auto;
}

.overlay-legend {
  display: flex;
  gap: 16px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #666;
}

.legend-color {
  width: 14px;
  height: 14px;
  border-radius: 3px;
}
</style>

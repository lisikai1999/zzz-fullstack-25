<template>
  <div class="qc-view">
    <div class="qc-header">
      <h2>质控对比</h2>
      <div class="qc-controls">
        <label>
          影像ID:
          <input v-model.number="imageId" type="number" min="1" />
        </label>
        <button class="btn btn-primary" @click="loadComparison">加载对比</button>
        <button class="btn btn-secondary" @click="loadFlagged">查看待仲裁</button>
      </div>
    </div>

    <div v-if="comparison" class="qc-content">
      <MetricsPanel :results="comparison.consistency_results" />

      <div class="comparison-panels">
        <div
          v-for="(annotator, idx) in comparison.annotators"
          :key="annotator.user_id"
          class="annotator-panel"
        >
          <div class="panel-header">
            <span class="annotator-name">{{ annotator.username }}</span>
            <span class="annotation-count">{{ annotator.annotations.length }} 个标注</span>
          </div>
          <AnnotationCanvas
            :image-width="comparison.image.width"
            :image-height="comparison.image.height"
            :annotations="annotator.annotations"
            :read-only="true"
          />
        </div>
      </div>

      <OverlayDiff
        v-if="comparison.annotators.length >= 2"
        :annotators="comparison.annotators"
        :image="comparison.image"
      />
    </div>

    <div v-if="flaggedItems.length > 0" class="flagged-section">
      <h3>低一致性项目 (需仲裁)</h3>
      <div class="flagged-list">
        <div v-for="item in flaggedItems" :key="item.id" class="flagged-item">
          <span class="flagged-metric">{{ item.metric_type.toUpperCase() }}</span>
          <span class="flagged-score" :class="scoreClass(item.score)">{{ item.score.toFixed(3) }}</span>
          <span class="flagged-image">影像 #{{ item.image_id }}</span>
          <span class="flagged-status">{{ item.arbitration_status || 'pending' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../api'
import AnnotationCanvas from '../components/canvas/AnnotationCanvas.vue'
import MetricsPanel from '../components/qc/MetricsPanel.vue'
import OverlayDiff from '../components/qc/OverlayDiff.vue'

const imageId = ref(1)
const comparison = ref(null)
const flaggedItems = ref([])

async function loadComparison() {
  try {
    // Trigger consistency computation first
    await api.getConsistency(imageId.value)
    const resp = await api.getComparison(imageId.value)
    comparison.value = resp.data
  } catch (e) {
    alert('无法加载对比数据: ' + (e.response?.data?.detail || e.message))
  }
}

async function loadFlagged() {
  try {
    const resp = await api.getFlagged()
    flaggedItems.value = resp.data
  } catch (e) {
    console.error(e)
  }
}

function scoreClass(score) {
  if (score >= 0.7) return 'good'
  if (score >= 0.4) return 'warn'
  return 'bad'
}
</script>

<style scoped>
.qc-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.qc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.qc-header h2 {
  font-size: 20px;
  color: #1a1a2e;
}

.qc-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.qc-controls label {
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.qc-controls input {
  width: 70px;
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
}

.btn-primary { background: #1a1a2e; color: white; }
.btn-secondary { background: #e8e8e8; color: #333; }

.comparison-panels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 16px;
}

.annotator-panel {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: #f8f9fa;
  border-bottom: 1px solid #eee;
}

.annotator-name {
  font-weight: 600;
  font-size: 14px;
}

.annotation-count {
  font-size: 12px;
  color: #666;
}

.flagged-section {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.flagged-section h3 {
  font-size: 16px;
  color: #e74c3c;
  margin-bottom: 12px;
}

.flagged-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.flagged-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: #fff5f5;
  border-radius: 6px;
  border-left: 3px solid #e74c3c;
  font-size: 13px;
}

.flagged-metric {
  font-weight: 600;
  min-width: 50px;
}

.flagged-score.good { color: #27ae60; }
.flagged-score.warn { color: #f39c12; }
.flagged-score.bad { color: #e74c3c; font-weight: 600; }

.flagged-image { color: #666; }
.flagged-status {
  margin-left: auto;
  font-size: 11px;
  padding: 2px 8px;
  background: #f0f0f0;
  border-radius: 10px;
}
</style>

<template>
  <div class="arbitration-view">
    <div class="arb-header">
      <h2>仲裁工作台</h2>
      <div class="arb-summary">
        <span class="summary-badge">{{ pendingItems.length }} 项待仲裁</span>
        <button class="btn btn-secondary" @click="loadPendingItems">刷新</button>
      </div>
    </div>

    <!-- Pending arbitration list -->
    <div v-if="!activeCase" class="arb-list-section">
      <div v-if="pendingItems.length === 0" class="empty-state">
        <div class="empty-icon">✓</div>
        <p>所有仲裁已处理完毕</p>
      </div>
      <div v-else class="arb-list">
        <div
          v-for="item in pendingItems"
          :key="item.arbitration_id"
          class="arb-list-item"
          @click="openCase(item)"
        >
          <div class="item-left">
            <span class="item-metric" :class="metricSeverity(item.score)">
              {{ item.metric_type.toUpperCase() }}: {{ item.score.toFixed(3) }}
            </span>
            <span class="item-image">{{ item.filename }} (影像 #{{ item.image_id }})</span>
          </div>
          <div class="item-right">
            <span class="item-annotators">
              {{ item.annotation_a?.username }} vs {{ item.annotation_b?.username }}
            </span>
            <span class="item-arrow">→</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Active arbitration case -->
    <div v-if="activeCase" class="arb-workspace">
      <div class="arb-case-header">
        <button class="btn btn-back" @click="closeCase">← 返回列表</button>
        <div class="case-info">
          <span class="case-metric" :class="metricSeverity(activeCase.score)">
            {{ activeCase.metric_type.toUpperCase() }}: {{ activeCase.score.toFixed(4) }}
          </span>
          <span class="case-image">{{ activeCase.filename }}</span>
          <span class="case-threshold">阈值: {{ getThreshold(activeCase.metric_type) }}</span>
        </div>
      </div>

      <!-- Side-by-side comparison -->
      <div class="comparison-area">
        <div class="comparison-panel panel-a" :class="{ selected: selectedResolution === 'a' }">
          <div class="panel-label">
            <input type="radio" v-model="selectedResolution" value="a" name="resolution" />
            <span class="panel-user">{{ activeCase.annotation_a?.username }}</span>
            <span class="panel-type">{{ activeCase.annotation_a?.annotation_type }}</span>
          </div>
          <div class="panel-canvas">
            <AnnotationCanvas
              :image-width="activeCase.width"
              :image-height="activeCase.height"
              :annotations="[activeCase.annotation_a]"
              :read-only="true"
            />
          </div>
          <div class="panel-data">
            <pre>{{ formatAnnotationData(activeCase.annotation_a) }}</pre>
          </div>
        </div>

        <div class="comparison-divider">
          <div class="vs-badge">VS</div>
        </div>

        <div class="comparison-panel panel-b" :class="{ selected: selectedResolution === 'b' }">
          <div class="panel-label">
            <input type="radio" v-model="selectedResolution" value="b" name="resolution" />
            <span class="panel-user">{{ activeCase.annotation_b?.username }}</span>
            <span class="panel-type">{{ activeCase.annotation_b?.annotation_type }}</span>
          </div>
          <div class="panel-canvas">
            <AnnotationCanvas
              :image-width="activeCase.width"
              :image-height="activeCase.height"
              :annotations="[activeCase.annotation_b]"
              :read-only="true"
            />
          </div>
          <div class="panel-data">
            <pre>{{ formatAnnotationData(activeCase.annotation_b) }}</pre>
          </div>
        </div>
      </div>

      <!-- Overlay comparison -->
      <div class="overlay-section">
        <h4>叠加对比</h4>
        <div class="overlay-canvas">
          <AnnotationCanvas
            :image-width="activeCase.width"
            :image-height="activeCase.height"
            :annotations="[activeCase.annotation_a, activeCase.annotation_b]"
            :layers="overlayLayers"
            :read-only="true"
          />
        </div>
        <div class="overlay-legend">
          <span class="legend-a">■ {{ activeCase.annotation_a?.username }}</span>
          <span class="legend-b">■ {{ activeCase.annotation_b?.username }}</span>
        </div>
      </div>

      <!-- Resolution form -->
      <div class="resolution-section">
        <h4>仲裁裁决</h4>
        <div class="resolution-options">
          <label class="resolution-option" :class="{ active: selectedResolution === 'a' }">
            <input type="radio" v-model="selectedResolution" value="a" />
            <span>采纳 {{ activeCase.annotation_a?.username }} 的标注</span>
          </label>
          <label class="resolution-option" :class="{ active: selectedResolution === 'b' }">
            <input type="radio" v-model="selectedResolution" value="b" />
            <span>采纳 {{ activeCase.annotation_b?.username }} 的标注</span>
          </label>
          <label class="resolution-option" :class="{ active: selectedResolution === 'neither' }">
            <input type="radio" v-model="selectedResolution" value="neither" />
            <span>两者均不采纳（需重新标注）</span>
          </label>
        </div>

        <div class="resolution-comment">
          <label>仲裁备注:</label>
          <textarea v-model="resolutionComment" placeholder="说明裁决理由..." rows="3"></textarea>
        </div>

        <div class="resolution-actions">
          <button
            class="btn btn-primary btn-lg"
            :disabled="!selectedResolution || submitting"
            @click="submitResolution"
          >
            {{ submitting ? '提交中...' : '提交裁决' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import api from '../api'
import AnnotationCanvas from '../components/canvas/AnnotationCanvas.vue'

const userStore = useUserStore()

const pendingItems = ref([])
const activeCase = ref(null)
const selectedResolution = ref(null)
const resolutionComment = ref('')
const submitting = ref(false)

const overlayLayers = computed(() => {
  if (!activeCase.value) return []
  return [
    {
      visible: true,
      opacity: 0.6,
      color: '#FF6B6B',
      annotations: [activeCase.value.annotation_a],
    },
    {
      visible: true,
      opacity: 0.6,
      color: '#4ECDC4',
      annotations: [activeCase.value.annotation_b],
    },
  ]
})

async function loadPendingItems() {
  try {
    const resp = await api.getPendingArbitrations()
    pendingItems.value = resp.data
  } catch (e) {
    console.error('Failed to load arbitrations:', e)
  }
}

function openCase(item) {
  activeCase.value = item
  selectedResolution.value = null
  resolutionComment.value = ''
}

function closeCase() {
  activeCase.value = null
  selectedResolution.value = null
  resolutionComment.value = ''
}

async function submitResolution() {
  if (!selectedResolution.value || !activeCase.value) return
  submitting.value = true

  let resolutionData
  if (selectedResolution.value === 'a') {
    resolutionData = {
      chosen: 'annotation_a',
      annotation_id: activeCase.value.annotation_id_a,
      data_json: activeCase.value.annotation_a?.data_json,
      comment: resolutionComment.value,
    }
  } else if (selectedResolution.value === 'b') {
    resolutionData = {
      chosen: 'annotation_b',
      annotation_id: activeCase.value.annotation_id_b,
      data_json: activeCase.value.annotation_b?.data_json,
      comment: resolutionComment.value,
    }
  } else {
    resolutionData = {
      chosen: 'neither',
      annotation_id: null,
      data_json: null,
      comment: resolutionComment.value,
    }
  }

  try {
    await api.submitArbitration({
      image_id: activeCase.value.image_id,
      consistency_result_id: activeCase.value.consistency_result_id,
      reviewer_id: userStore.currentUserId,
      resolution_json: JSON.stringify(resolutionData),
    })
    // Remove from pending list and close case
    pendingItems.value = pendingItems.value.filter(
      i => i.arbitration_id !== activeCase.value.arbitration_id
    )
    activeCase.value = null
    selectedResolution.value = null
    resolutionComment.value = ''
  } catch (e) {
    alert('提交失败: ' + (e.response?.data?.detail || e.message))
  }
  submitting.value = false
}

function formatAnnotationData(annotation) {
  if (!annotation) return ''
  try {
    const data = JSON.parse(annotation.data_json)
    return JSON.stringify(data, null, 2)
  } catch {
    return annotation.data_json
  }
}

function metricSeverity(score) {
  if (score >= 0.6) return 'severity-low'
  if (score >= 0.4) return 'severity-medium'
  return 'severity-high'
}

function getThreshold(metricType) {
  if (metricType === 'kappa') return '0.6'
  return '0.7'
}

onMounted(loadPendingItems)
</script>

<style scoped>
.arbitration-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.arb-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 16px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.arb-header h2 {
  font-size: 20px;
  color: #1a1a2e;
}

.arb-summary {
  display: flex;
  align-items: center;
  gap: 12px;
}

.summary-badge {
  background: #fff3cd;
  color: #856404;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 8px;
}

.empty-icon {
  font-size: 48px;
  color: #27ae60;
  margin-bottom: 12px;
}

.empty-state p {
  color: #666;
  font-size: 15px;
}

/* List */
.arb-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.arb-list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  background: white;
  border-radius: 8px;
  border-left: 4px solid #e74c3c;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  cursor: pointer;
  transition: all 0.15s;
}

.arb-list-item:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateX(2px);
}

.item-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.item-metric {
  font-weight: 700;
  font-size: 14px;
}

.item-metric.severity-high { color: #e74c3c; }
.item-metric.severity-medium { color: #f39c12; }
.item-metric.severity-low { color: #e67e22; }

.item-image {
  font-size: 12px;
  color: #888;
}

.item-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-annotators {
  font-size: 13px;
  color: #555;
}

.item-arrow {
  font-size: 18px;
  color: #ccc;
}

/* Workspace */
.arb-workspace {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.arb-case-header {
  display: flex;
  align-items: center;
  gap: 16px;
  background: white;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.btn-back {
  padding: 8px 14px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 13px;
}

.btn-back:hover { background: #f5f5f5; }

.case-info {
  display: flex;
  gap: 16px;
  align-items: center;
}

.case-metric {
  font-weight: 700;
  font-size: 15px;
}

.case-metric.severity-high { color: #e74c3c; }
.case-metric.severity-medium { color: #f39c12; }
.case-metric.severity-low { color: #e67e22; }

.case-image {
  font-size: 13px;
  color: #666;
}

.case-threshold {
  font-size: 12px;
  color: #999;
  background: #f0f0f0;
  padding: 2px 8px;
  border-radius: 4px;
}

/* Comparison */
.comparison-area {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 0;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.comparison-panel {
  padding: 16px;
  transition: background 0.15s;
}

.comparison-panel.selected {
  background: #f0faf0;
  box-shadow: inset 0 0 0 2px #27ae60;
}

.panel-a { border-right: 1px solid #eee; }

.comparison-divider {
  display: flex;
  align-items: center;
  padding: 0 12px;
  background: #f8f9fa;
}

.vs-badge {
  font-weight: 700;
  font-size: 16px;
  color: #999;
  background: white;
  padding: 8px 12px;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.panel-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.panel-user {
  font-weight: 600;
  font-size: 14px;
}

.panel-type {
  font-size: 11px;
  background: #e8f0fe;
  color: #1a73e8;
  padding: 2px 6px;
  border-radius: 4px;
}

.panel-canvas {
  height: 280px;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 8px;
}

.panel-data pre {
  font-size: 11px;
  background: #f8f9fa;
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
  max-height: 80px;
  color: #555;
}

/* Overlay */
.overlay-section {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.overlay-section h4 {
  margin-bottom: 10px;
  font-size: 14px;
  color: #333;
}

.overlay-canvas {
  height: 300px;
  border-radius: 6px;
  overflow: hidden;
}

.overlay-legend {
  display: flex;
  gap: 20px;
  margin-top: 8px;
  font-size: 12px;
}

.legend-a { color: #FF6B6B; }
.legend-b { color: #4ECDC4; }

/* Resolution */
.resolution-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.resolution-section h4 {
  margin-bottom: 14px;
  font-size: 16px;
  color: #333;
}

.resolution-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.resolution-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
  font-size: 14px;
}

.resolution-option:hover {
  border-color: #bbb;
  background: #fafafa;
}

.resolution-option.active {
  border-color: #27ae60;
  background: #f0faf0;
}

.resolution-option input {
  accent-color: #27ae60;
}

.resolution-comment {
  margin-bottom: 16px;
}

.resolution-comment label {
  display: block;
  font-size: 13px;
  color: #666;
  margin-bottom: 6px;
}

.resolution-comment textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  resize: vertical;
  font-family: inherit;
}

.resolution-comment textarea:focus {
  outline: none;
  border-color: #1a1a2e;
}

.resolution-actions {
  display: flex;
  justify-content: flex-end;
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
.btn-primary:hover { background: #2a2a4e; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { background: #e8e8e8; color: #333; }
.btn-lg { padding: 12px 28px; font-size: 14px; }
</style>

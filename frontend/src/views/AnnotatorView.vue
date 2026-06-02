<template>
  <div class="annotator-view">
    <div class="annotator-header">
      <div class="task-info" v-if="currentTask">
        <span class="task-badge">任务 #{{ currentTask.id }}</span>
        <span class="task-image">影像 #{{ currentTask.image_id }}</span>
        <span class="task-priority">优先级: {{ currentTask.priority?.toFixed(2) }}</span>
      </div>
      <div class="task-actions">
        <button class="btn btn-primary" @click="getNextTask" :disabled="loading">
          {{ currentTask ? '下一张' : '获取任务' }}
        </button>
        <label class="label-input">
          标签:
          <input v-model="currentLabel" placeholder="如: tumor, nodule" />
        </label>
      </div>
    </div>

    <div class="annotator-workspace">
      <div class="canvas-area">
        <ToolBar :active-tool="activeTool" @tool-change="activeTool = $event" @submit="submitAnnotation" @clear="clearCurrent" />
        <AnnotationCanvas
          :image-width="512"
          :image-height="512"
          :active-tool-name="activeTool"
          :annotations="annotations"
          @annotation-created="onAnnotationCreated"
        />
      </div>
      <div class="side-panel">
        <LayerManager
          :layers="layers"
          :active-layer="activeLayer"
          @select-layer="activeLayer = $event"
          @toggle-layer="toggleLayer($event)"
          @add-layer="addLayer"
        />
        <div class="annotations-list">
          <h4>当前标注</h4>
          <div v-for="(ann, idx) in pendingAnnotations" :key="idx" class="ann-item">
            <span class="ann-type">{{ ann.type }}</span>
            <span class="ann-label">{{ currentLabel || '未命名' }}</span>
            <button class="btn-sm" @click="removeAnnotation(idx)">✕</button>
          </div>
          <p v-if="pendingAnnotations.length === 0" class="empty-hint">暂无标注，请在画布上绘制</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useTaskStore } from '../stores/task'
import { useUserStore } from '../stores/user'
import { useAnnotationStore } from '../stores/annotation'
import AnnotationCanvas from '../components/canvas/AnnotationCanvas.vue'
import ToolBar from '../components/canvas/ToolBar.vue'
import LayerManager from '../components/canvas/LayerManager.vue'
import api from '../api'

const taskStore = useTaskStore()
const userStore = useUserStore()
const annotationStore = useAnnotationStore()

const currentTask = ref(null)
const activeTool = ref('bbox')
const currentLabel = ref('tumor')
const loading = ref(false)
const annotations = ref([])
const pendingAnnotations = ref([])
const activeLayer = ref(0)
const layers = ref([
  { name: '默认图层', visible: true, opacity: 1, color: '#FF6B6B', annotations: [] },
])

async function getNextTask() {
  loading.value = true
  try {
    const task = await taskStore.assignNext(userStore.currentUserId)
    currentTask.value = task
    pendingAnnotations.value = []
    annotations.value = []
  } catch (e) {
    alert('没有可分配的任务')
  }
  loading.value = false
}

function onAnnotationCreated(ann) {
  pendingAnnotations.value.push(ann)
  annotations.value.push({
    annotation_type: ann.type,
    label: currentLabel.value,
    data_json: JSON.stringify(ann),
    user_id: userStore.currentUserId,
  })
}

function removeAnnotation(idx) {
  pendingAnnotations.value.splice(idx, 1)
  annotations.value.splice(idx, 1)
}

async function submitAnnotation() {
  if (!currentTask.value || pendingAnnotations.value.length === 0) return
  for (const ann of pendingAnnotations.value) {
    await annotationStore.submit({
      task_id: currentTask.value.id,
      image_id: currentTask.value.image_id,
      user_id: userStore.currentUserId,
      annotation_type: ann.type,
      label: currentLabel.value,
      data_json: JSON.stringify(ann),
      layer_index: activeLayer.value,
    })
  }
  await api.updateTaskStatus(currentTask.value.id, 'completed')
  pendingAnnotations.value = []
  alert('标注已提交！')
}

function clearCurrent() {
  pendingAnnotations.value = []
  annotations.value = []
}

function toggleLayer(idx) {
  layers.value[idx].visible = !layers.value[idx].visible
}

function addLayer() {
  const colors = ['#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
  layers.value.push({
    name: `图层 ${layers.value.length + 1}`,
    visible: true,
    opacity: 1,
    color: colors[layers.value.length % colors.length],
    annotations: [],
  })
}
</script>

<style scoped>
.annotator-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: calc(100vh - 104px);
}

.annotator-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.task-info {
  display: flex;
  gap: 12px;
  align-items: center;
}

.task-badge {
  background: #1a1a2e;
  color: white;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.task-image, .task-priority {
  font-size: 13px;
  color: #666;
}

.task-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.label-input {
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.label-input input {
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
  width: 140px;
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.15s;
}

.btn-primary {
  background: #1a1a2e;
  color: white;
}

.btn-primary:hover {
  background: #2a2a4e;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.annotator-workspace {
  display: grid;
  grid-template-columns: 1fr 260px;
  gap: 16px;
  flex: 1;
  min-height: 0;
}

.canvas-area {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.side-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.annotations-list {
  background: white;
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.annotations-list h4 {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.ann-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  background: #f9f9f9;
  margin-bottom: 4px;
  font-size: 12px;
}

.ann-type {
  background: #e8f0fe;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
  color: #1a73e8;
}

.ann-label {
  flex: 1;
  color: #555;
}

.btn-sm {
  border: none;
  background: #ff4444;
  color: white;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-hint {
  font-size: 12px;
  color: #999;
  text-align: center;
  padding: 16px 0;
}
</style>

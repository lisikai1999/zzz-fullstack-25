<template>
  <div class="task-card">
    <div class="card-header">
      <span class="card-id">#{{ task.id }}</span>
      <span class="card-priority" :class="priorityClass">{{ priorityLabel }}</span>
    </div>
    <div class="card-body">
      <div class="card-image">影像 #{{ task.image_id }}</div>
      <div class="card-assignee" v-if="task.assignee_id">
        标注员 #{{ task.assignee_id }}
      </div>
    </div>
    <div class="card-footer" v-if="task.redundancy_group">
      <span class="redundancy-badge">多人标注</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  task: { type: Object, required: true },
})

const priorityClass = computed(() => {
  const p = props.task.priority
  if (p >= 0.7) return 'high'
  if (p >= 0.4) return 'medium'
  return 'low'
})

const priorityLabel = computed(() => {
  const p = props.task.priority
  if (p >= 0.7) return '高'
  if (p >= 0.4) return '中'
  return '低'
})
</script>

<style scoped>
.task-card {
  background: white;
  border-radius: 6px;
  padding: 10px 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  transition: box-shadow 0.15s;
}

.task-card:hover {
  box-shadow: 0 3px 8px rgba(0,0,0,0.12);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.card-id {
  font-weight: 600;
  font-size: 12px;
  color: #555;
}

.card-priority {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.card-priority.high { background: #ffe0e0; color: #c0392b; }
.card-priority.medium { background: #fff3cd; color: #856404; }
.card-priority.low { background: #d4edda; color: #155724; }

.card-body {
  font-size: 12px;
  color: #666;
}

.card-image {
  margin-bottom: 4px;
}

.card-footer {
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid #f0f0f0;
}

.redundancy-badge {
  font-size: 10px;
  background: #e8f0fe;
  color: #1a73e8;
  padding: 2px 6px;
  border-radius: 4px;
}
</style>

<template>
  <div class="kanban-column">
    <div class="column-header" :style="{ borderTopColor: color }">
      <span class="column-title">{{ title }}</span>
      <span class="column-count">{{ tasks.length }}</span>
    </div>
    <div class="column-body">
      <TaskCard v-for="task in tasks" :key="task.id" :task="task" />
      <div v-if="tasks.length === 0" class="empty-column">暂无任务</div>
    </div>
  </div>
</template>

<script setup>
import TaskCard from './TaskCard.vue'

defineProps({
  title: { type: String, required: true },
  tasks: { type: Array, default: () => [] },
  color: { type: String, default: '#999' },
})
</script>

<style scoped>
.kanban-column {
  background: #f8f9fa;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.column-header {
  padding: 12px 16px;
  border-top: 3px solid;
  border-radius: 8px 8px 0 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
}

.column-title {
  font-weight: 600;
  font-size: 14px;
  color: #333;
}

.column-count {
  background: #e8e8e8;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  color: #666;
}

.column-body {
  flex: 1;
  padding: 8px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.empty-column {
  text-align: center;
  color: #999;
  font-size: 13px;
  padding: 24px 0;
}
</style>

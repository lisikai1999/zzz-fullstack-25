<template>
  <div class="kanban-view">
    <div class="kanban-header">
      <h2>任务看板</h2>
      <button class="btn btn-primary" @click="refreshKanban">刷新</button>
    </div>
    <div class="kanban-board">
      <KanbanColumn
        v-for="col in columns"
        :key="col.key"
        :title="col.title"
        :tasks="kanban[col.key] || []"
        :color="col.color"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useTaskStore } from '../stores/task'
import KanbanColumn from '../components/kanban/KanbanColumn.vue'

const taskStore = useTaskStore()
const kanban = ref({ pending: [], assigned: [], in_progress: [], completed: [], arbitration: [] })

const columns = [
  { key: 'pending', title: '待分配', color: '#95a5a6' },
  { key: 'assigned', title: '已分配', color: '#3498db' },
  { key: 'in_progress', title: '进行中', color: '#f39c12' },
  { key: 'completed', title: '已完成', color: '#27ae60' },
  { key: 'arbitration', title: '待仲裁', color: '#e74c3c' },
]

async function refreshKanban() {
  try {
    await taskStore.fetchKanban()
    kanban.value = taskStore.kanban
  } catch (e) {
    console.error('Failed to fetch kanban:', e)
  }
}

onMounted(refreshKanban)
</script>

<style scoped>
.kanban-view {
  height: calc(100vh - 104px);
  display: flex;
  flex-direction: column;
}

.kanban-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.kanban-header h2 {
  font-size: 20px;
  color: #1a1a2e;
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
}

.btn-primary {
  background: #1a1a2e;
  color: white;
}

.kanban-board {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  flex: 1;
  min-height: 0;
  overflow-x: auto;
}
</style>

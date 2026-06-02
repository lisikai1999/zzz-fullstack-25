import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref([])
  const kanban = ref({ pending: [], assigned: [], in_progress: [], completed: [], arbitration: [] })
  const currentTask = ref(null)

  async function fetchTasks(params = {}) {
    const resp = await api.getTasks(params)
    tasks.value = resp.data
  }

  async function fetchKanban() {
    const resp = await api.getKanban()
    kanban.value = resp.data
  }

  async function assignNext(userId) {
    const resp = await api.assignTask(userId)
    currentTask.value = resp.data
    return resp.data
  }

  async function updateStatus(taskId, status) {
    await api.updateTaskStatus(taskId, status)
    await fetchKanban()
  }

  return { tasks, kanban, currentTask, fetchTasks, fetchKanban, assignNext, updateStatus }
})

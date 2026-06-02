import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useUserStore = defineStore('user', () => {
  const users = ref([])
  const currentUserId = ref(null)

  async function fetchUsers() {
    // For demo, create some users if none exist
    users.value = [
      { id: 1, username: 'alice', role: 'annotator' },
      { id: 2, username: 'bob', role: 'annotator' },
      { id: 3, username: 'reviewer1', role: 'reviewer' },
    ]
    if (!currentUserId.value) {
      currentUserId.value = 1
    }
  }

  function switchUser(id) {
    currentUserId.value = Number(id)
  }

  return { users, currentUserId, fetchUsers, switchUser }
})

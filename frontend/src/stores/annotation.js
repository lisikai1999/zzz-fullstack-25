import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useAnnotationStore = defineStore('annotation', () => {
  const annotations = ref([])
  const currentAnnotations = ref([])

  async function fetchForTask(taskId) {
    const resp = await api.getAnnotationsForTask(taskId)
    currentAnnotations.value = resp.data
  }

  async function fetchForImage(imageId) {
    const resp = await api.getAnnotationsForImage(imageId)
    annotations.value = resp.data
  }

  async function submit(data) {
    const resp = await api.createAnnotation(data)
    currentAnnotations.value.push(resp.data)
    return resp.data
  }

  async function remove(id) {
    await api.deleteAnnotation(id)
    currentAnnotations.value = currentAnnotations.value.filter(a => a.id !== id)
  }

  return { annotations, currentAnnotations, fetchForTask, fetchForImage, submit, remove }
})

import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

export default {
  // Tasks
  getTasks(params) { return api.get('/tasks', { params }) },
  getKanban() { return api.get('/tasks/kanban') },
  assignTask(userId) { return api.post('/tasks/assign', { user_id: userId }) },
  bulkCreateTasks(imageIds, redundancy) {
    return api.post('/tasks/bulk-create', { image_ids: imageIds, redundancy })
  },
  updateTaskStatus(taskId, status) {
    return api.patch(`/tasks/${taskId}/status`, { status })
  },

  // Annotations
  createAnnotation(data) { return api.post('/annotations', data) },
  getAnnotationsForTask(taskId) { return api.get(`/annotations/${taskId}`) },
  getAnnotationsForImage(imageId) { return api.get(`/annotations/image/${imageId}`) },
  updateAnnotation(id, data) { return api.put(`/annotations/${id}`, data) },
  deleteAnnotation(id) { return api.delete(`/annotations/${id}`) },

  // QC
  getConsistency(imageId) { return api.get(`/qc/consistency/${imageId}`) },
  getComparison(imageId) { return api.get(`/qc/comparison/${imageId}`) },
  submitArbitration(data) { return api.post('/qc/arbitrate', data) },
  getFlagged() { return api.get('/qc/flagged') },
  getPendingArbitrations() { return api.get('/qc/pending-arbitrations') },
  getArbitrationDetail(id) { return api.get(`/qc/arbitration/${id}`) },

  // Stats
  getAnnotators() { return api.get('/stats/annotators') },
  getAnnotatorStats(userId) { return api.get(`/stats/annotator/${userId}`) },
  getOverview() { return api.get('/stats/overview') },

  // Images
  getImage(imageId) { return api.get(`/images/${imageId}`) },
  updateUncertainty(imageId, score) {
    return api.patch(`/images/${imageId}/uncertainty`, { uncertainty_score: score })
  },
}

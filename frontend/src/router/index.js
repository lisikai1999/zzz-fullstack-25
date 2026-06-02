import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'annotator', component: () => import('../views/AnnotatorView.vue') },
  { path: '/kanban', name: 'kanban', component: () => import('../views/KanbanView.vue') },
  { path: '/qc', name: 'qc', component: () => import('../views/QCView.vue') },
  { path: '/arbitration', name: 'arbitration', component: () => import('../views/ArbitrationView.vue') },
  { path: '/stats', name: 'stats', component: () => import('../views/StatsView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

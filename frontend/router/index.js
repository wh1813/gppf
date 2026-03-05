import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/chart/000001'
  },
  {
    path: '/chart/:symbol',
    name: 'ChartAnalysis',
    component: () => import('@/views/chart/ChartAnalysis.vue')
  },
  {
    path: '/pool',
    name: 'PoolManager',
    component: () => import('@/views/pool/PoolManager.vue')
  },
  {
    path: '/console',
    name: 'AnalysisConsole',
    component: () => import('@/views/analysis/AnalysisConsole.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router